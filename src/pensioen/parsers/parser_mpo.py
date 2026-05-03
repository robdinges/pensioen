"""Parser voor MijnPensioenoverzicht exports (CSV, Excel, JSON, optioneel PDF)."""

from __future__ import annotations

import calendar
import json
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd

from pensioen.models.pensioen_record import PensioenRecord, TypePensioen

logger = logging.getLogger(__name__)

# Kolomnamen die we herkennen vanuit de export (case-insensitief)
_KOLOM_MAP = {
    "uitvoerder": "uitvoerder",
    "regeling": "regeling",
    "type_pensioen": "type_pensioen",
    "type": "type_pensioen",
    "ingangsdatum": "ingangsdatum",
    "einddatum": "einddatum",
    "bruto_per_jaar": "bruto_per_jaar",
    "bruto per jaar": "bruto_per_jaar",
    "bruto jaarbedrag": "bruto_per_jaar",
    "partnerpensioen_pct": "partnerpensioen_pct",
    "partnerpensioen %": "partnerpensioen_pct",
    "indexatie_verwacht_pct": "indexatie_verwacht_pct",
    "indexatie verwacht %": "indexatie_verwacht_pct",
    "indexatie_gegarandeerd_pct": "indexatie_gegarandeerd_pct",
    "indexatie gegarandeerd %": "indexatie_gegarandeerd_pct",
}

_VERPLICHTE_KOLOMMEN = {"uitvoerder", "regeling", "type_pensioen", "ingangsdatum", "bruto_per_jaar"}


def _normaliseer_kolommen(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliseer kolomnamen: lowercase, spaties trim, vertaal naar standaard."""
    df.columns = [str(k).strip().lower() for k in df.columns]
    vertaling = {}
    for kolom in df.columns:
        if kolom in _KOLOM_MAP:
            vertaling[kolom] = _KOLOM_MAP[kolom]
    return df.rename(columns=vertaling)


def _parse_datum(waarde: str | None) -> date | None:
    """Parseer een datumstring naar een date-object; geeft None bij leeg/ongeldig."""
    if pd.isna(waarde) or waarde == "" or waarde is None:
        return None
    if isinstance(waarde, date):
        return waarde
    try:
        return pd.to_datetime(str(waarde)).date()
    except (ValueError, TypeError):
        logger.warning("Ongeldige datum: '%s' — wordt als leeg beschouwd.", waarde)
        return None


def _parse_decimal(waarde, standaard: Decimal = Decimal("0")) -> Decimal:
    """Parseer een getal naar Decimal; geeft standaardwaarde bij leeg/ongeldig."""
    if pd.isna(waarde) or waarde == "":
        return standaard
    try:
        return Decimal(str(waarde))
    except Exception:
        logger.warning("Ongeldige decimale waarde: '%s' — gebruik standaard %s.", waarde, standaard)
        return standaard


def _parse_type_pensioen(waarde: str) -> TypePensioen:
    """Zet een string om naar TypePensioen-enum (case-insensitief, diacritieken-tolerant)."""
    genormaliseerd = str(waarde).strip().lower().replace("ë", "e").replace("é", "e")
    for lid in TypePensioen:
        if lid.value == genormaliseerd:
            return lid
    # Fallback: probeer gedeeltelijke match
    for lid in TypePensioen:
        if lid.value in genormaliseerd or genormaliseerd in lid.value:
            return lid
    logger.warning(
        "Onbekend type pensioen: '%s' — standaard 'ouderdoms' gebruikt.", waarde
    )
    return TypePensioen.OUDERDOMS


def _rij_naar_record(rij: pd.Series, bronbestand: str, peildatum: date | None) -> PensioenRecord:
    """Zet één DataFrame-rij om naar een PensioenRecord."""
    return PensioenRecord(
        uitvoerder=str(rij.get("uitvoerder", "")).strip(),
        regeling=str(rij.get("regeling", "")).strip(),
        type_pensioen=_parse_type_pensioen(rij.get("type_pensioen", "ouderdoms")),
        ingangsdatum=_parse_datum(rij.get("ingangsdatum")),  # type: ignore[arg-type]
        einddatum=_parse_datum(rij.get("einddatum")),
        bruto_per_jaar=_parse_decimal(rij.get("bruto_per_jaar"), Decimal("0")),
        partnerpensioen_pct=_parse_decimal(rij.get("partnerpensioen_pct"), Decimal("0")),
        indexatie_verwacht_pct=_parse_decimal(
            rij.get("indexatie_verwacht_pct"), Decimal("0")
        ),
        indexatie_gegarandeerd_pct=_parse_decimal(
            rij.get("indexatie_gegarandeerd_pct"), Decimal("0")
        ),
        bronbestand=bronbestand,
        peildatum=peildatum,
    )


def _df_naar_records(
    df: pd.DataFrame, bronbestand: str, peildatum: date | None = None
) -> list[PensioenRecord]:
    """Zet een DataFrame om naar een lijst van PensioenRecord."""
    df = _normaliseer_kolommen(df)

    records = []
    for _, rij in df.iterrows():
        try:
            record = _rij_naar_record(rij, bronbestand, peildatum)
            records.append(record)
        except Exception as exc:
            logger.error("Rij overgeslagen vanwege fout: %s | Rij: %s", exc, rij.to_dict())

    return records


def _leeftijd_blok_naar_datum(blok: dict, geboortedatum: date | None) -> date | None:
    """
    Zet een Van/Tot-blok (met Leeftijd.Jaren en Leeftijd.Maanden) om naar een date.

    Zonder geboortedatum kan de conversie niet worden gemaakt en wordt None teruggegeven.
    De datum is de eerste dag van de maand die correspondeert met de leeftijd.
    """
    leeftijd = blok.get("Leeftijd")
    if not leeftijd or geboortedatum is None:
        return None
    jaren = int(leeftijd.get("Jaren", 0))
    maanden = int(leeftijd.get("Maanden", 0))
    # Tel jaren en maanden op bij geboortedatum
    doelmaand = geboortedatum.month + maanden + jaren * 12
    doeljaar = geboortedatum.year + (doelmaand - 1) // 12
    doelmaand = (doelmaand - 1) % 12 + 1
    # Gebruik de eerste dag van die maand als ingangsdatum
    return date(doeljaar, doelmaand, 1)


class MPOParser:
    """Parser voor MijnPensioenoverzicht-exports."""

    @staticmethod
    def parse_csv(pad: Path, peildatum: date | None = None) -> list[PensioenRecord]:
        """
        Parseer een CSV-export van mijnpensioenoverzicht.nl.

        Args:
            pad: Pad naar het CSV-bestand.
            peildatum: Peildatum van de export (optioneel, voor transparantie).

        Returns:
            Lijst van PensioenRecord-objecten.
        """
        df = pd.read_csv(pad, dtype=str, encoding="utf-8-sig")
        return _df_naar_records(df, str(pad), peildatum)

    @staticmethod
    def parse_excel(pad: Path, peildatum: date | None = None) -> list[PensioenRecord]:
        """
        Parseer een Excel-export van mijnpensioenoverzicht.nl.

        Args:
            pad: Pad naar het Excel-bestand (.xlsx of .xls).
            peildatum: Peildatum van de export.

        Returns:
            Lijst van PensioenRecord-objecten.
        """
        df = pd.read_excel(pad, dtype=str)
        return _df_naar_records(df, str(pad), peildatum)

    @staticmethod
    def parse_pdf(pad: Path, peildatum: date | None = None) -> list[PensioenRecord]:
        """
        Best-effort PDF-parsing via pdfplumber.

        Let op: PDF-parsing is niet gegarandeerd correct. Valideer het resultaat
        altijd via de validator.

        Args:
            pad: Pad naar het PDF-bestand.
            peildatum: Peildatum van de export.

        Returns:
            Lijst van PensioenRecord-objecten (kan onvolledig zijn).

        Raises:
            ImportError: Als pdfplumber niet geïnstalleerd is.
        """
        try:
            import pdfplumber
        except ImportError as exc:
            raise ImportError(
                "pdfplumber is niet geïnstalleerd. Installeer via: pip install pdfplumber"
            ) from exc

        rijen: list[dict] = []
        with pdfplumber.open(pad) as pdf:
            for pagina in pdf.pages:
                tabellen = pagina.extract_tables()
                for tabel in tabellen:
                    if not tabel:
                        continue
                    headers = [str(h).strip().lower() for h in tabel[0]]
                    for rij in tabel[1:]:
                        rijen.append(dict(zip(headers, rij)))

        if not rijen:
            logger.warning("Geen tabeldata gevonden in PDF: %s", pad)
            return []

        df = pd.DataFrame(rijen)
        return _df_naar_records(df, str(pad), peildatum)

    @staticmethod
    def parse_json(
        pad: Path,
        peildatum: date | None = None,
        geboortedatum: date | None = None,
    ) -> list[PensioenRecord]:
        """
        Parseer een JSON-export van mijnpensioenoverzicht.nl (Stichting Pensioenregister).

        Het JSON-formaat bevat tijdvakken per leeftijdsperiode. Per uitvoerder en
        regelingscode worden records gedupeerd tot één PensioenRecord per aanspraak:
        - ingangsdatum: afgeleid van de vroegste Van.Leeftijd (vereist geboortedatum).
        - bruto_per_jaar: TeBereiken uit het laatste (hoogste leeftijd) tijdvak.
        - einddatum: None als het tijdvak eindigt met 'Overlijden'.

        Args:
            pad: Pad naar het .json-bestand.
            peildatum: Peildatum van de export; wordt afgeleid uit TijdstipAanmakenBericht
                als niet opgegeven.
            geboortedatum: Geboortedatum van de deelnemer. Nodig om leeftijden om te zetten
                naar kalenderdatums. Zonder geboortedatum blijft ingangsdatum None.

        Returns:
            Lijst van PensioenRecord-objecten (OUDERDOMS en PARTNER).
        """
        with open(pad, encoding="utf-8") as f:
            data = json.load(f)

        bronbestand = str(pad)

        # Peildatum uit bericht afleiden als niet opgegeven
        if peildatum is None:
            tijdstip = data.get("TijdstipAanmakenBericht", "")
            if tijdstip:
                try:
                    peildatum = date.fromisoformat(tijdstip[:10])
                except ValueError:
                    pass

        records: list[PensioenRecord] = []
        details = data.get("Details", {})

        # --- Ouderdomspensioen ---
        # Dedupliceer per (HerkenningsNummer, type_sleutel): neem de vroegste ingangsdatum
        # en het TeBereiken-bedrag uit het laatste (meest volledige) tijdvak.
        ouderdoms_tijdvakken = (
            details.get("OuderdomsPensioenDetails", {}).get("OuderdomsPensioen", []) or []
        )
        # Gesorteerd op Van.Leeftijd.Jaren zodat iteratievolgorde altijd vroeg→laat is
        ouderdoms_tijdvakken = sorted(
            ouderdoms_tijdvakken,
            key=lambda t: (
                t.get("Van", {}).get("Leeftijd", {}).get("Jaren", 999),
                t.get("Van", {}).get("Leeftijd", {}).get("Maanden", 0),
            ),
        )

        # Bijhouden per (herkenning, sleutel): {ingangsdatum, einddatum, item_data}
        ouderdoms_map: dict[tuple[str, str], dict] = {}

        for tijdvak in ouderdoms_tijdvakken:
            van_blok = tijdvak.get("Van", {})
            tot_blok = tijdvak.get("Tot", {})

            ingangsdatum = _leeftijd_blok_naar_datum(van_blok, geboortedatum)
            # einddatum is None als Tot een OuderdomsPensioenEvent (bijv. "Overlijden") bevat
            einddatum = (
                _leeftijd_blok_naar_datum(tot_blok, geboortedatum)
                if "Leeftijd" in tot_blok
                else None
            )

            for type_sleutel in ("Pensioen", "IndicatiefPensioen"):
                for item in tijdvak.get(type_sleutel, []) or []:
                    herkenning = item.get("HerkenningsNummer", "")
                    sleutel = (herkenning, type_sleutel)

                    if sleutel not in ouderdoms_map:
                        # Eerste (vroegste) tijdvak: sla ingangsdatum op
                        ouderdoms_map[sleutel] = {
                            "ingangsdatum": ingangsdatum,
                            "einddatum": einddatum,
                            "item": item,
                        }
                    else:
                        # Later tijdvak: werk einddatum en item (TeBereiken) bij
                        ouderdoms_map[sleutel]["einddatum"] = einddatum
                        ouderdoms_map[sleutel]["item"] = item

        for (herkenning, type_sleutel), entry in ouderdoms_map.items():
            item = entry["item"]
            uitvoerder = item.get("PensioenUitvoerder", "")
            stand_per = item.get("StandPer")
            item_peildatum = peildatum
            if stand_per and item_peildatum is None:
                try:
                    item_peildatum = date.fromisoformat(stand_per)
                except ValueError:
                    pass

            te_bereiken = Decimal(str(item.get("TeBereiken") or 0))
            opgebouwd = Decimal(str(item.get("Opgebouwd") or 0))

            try:
                record = PensioenRecord(
                    uitvoerder=uitvoerder,
                    regeling=herkenning,
                    type_pensioen=TypePensioen.OUDERDOMS,
                    ingangsdatum=entry["ingangsdatum"],
                    einddatum=entry["einddatum"],
                    bruto_per_jaar=te_bereiken,
                    bronbestand=bronbestand,
                    peildatum=item_peildatum,
                    scenario_bedragen={"opgebouwd": opgebouwd},
                )
                records.append(record)
            except Exception as exc:
                logger.error(
                    "Ouderdomspensioen-item overgeslagen: %s | herkenning=%s",
                    exc,
                    herkenning,
                )

        # --- Partnerpensioen ---
        # Partnerpensioen heeft geen leeftijdsbasis voor de ingangsdatum (ingaat na overlijden).
        # Dedupliceer op HerkenningsNummer; gebruik VerzekerdBedrag als bruto_per_jaar.
        partner_tijdvakken = (
            details.get("PartnerPensioenDetails", {}).get("PartnerPensioen", []) or []
        )
        partner_map: dict[tuple[str, str], dict] = {}

        for tijdvak in partner_tijdvakken:
            for type_sleutel in ("Pensioen", "IndicatiefPensioen"):
                for item in tijdvak.get(type_sleutel, []) or []:
                    herkenning = item.get("HerkenningsNummer", "")
                    sleutel = (herkenning, type_sleutel)
                    if sleutel not in partner_map:
                        partner_map[sleutel] = {"item": item}

        for (herkenning, type_sleutel), entry in partner_map.items():
            item = entry["item"]
            uitvoerder = item.get("PensioenUitvoerder", "")
            stand_per = item.get("StandPer")
            item_peildatum = peildatum
            if stand_per and item_peildatum is None:
                try:
                    item_peildatum = date.fromisoformat(stand_per)
                except ValueError:
                    pass

            bedragen = item.get("Bedragen", {}) or {}
            # VerzekerdBedragNaPens is het meest relevant voor langetermijnplanning
            te_bereiken = Decimal(
                str(
                    bedragen.get("VerzekerdBedragNaPens")
                    or bedragen.get("VerzekerdBedrag")
                    or 0
                )
            )

            try:
                record = PensioenRecord(
                    uitvoerder=uitvoerder,
                    regeling=herkenning,
                    type_pensioen=TypePensioen.PARTNER,
                    ingangsdatum=None,
                    einddatum=None,
                    bruto_per_jaar=te_bereiken,
                    bronbestand=bronbestand,
                    peildatum=item_peildatum,
                )
                records.append(record)
            except Exception as exc:
                logger.error(
                    "Partnerpensioen-item overgeslagen: %s | herkenning=%s",
                    exc,
                    herkenning,
                )

        return records

    @classmethod
    def parse(
        cls,
        pad: Path,
        peildatum: date | None = None,
        geboortedatum: date | None = None,
    ) -> list[PensioenRecord]:
        """
        Parseer automatisch op basis van de bestandsextensie.

        Ondersteunde extensies: .csv, .xlsx, .xls, .pdf, .json

        Args:
            pad: Pad naar het bestand.
            peildatum: Peildatum van de export (optioneel).
            geboortedatum: Geboortedatum van de deelnemer; alleen nodig voor .json
                om leeftijden naar datums te vertalen.
        """
        extensie = pad.suffix.lower()
        if extensie == ".csv":
            return cls.parse_csv(pad, peildatum)
        if extensie in (".xlsx", ".xls"):
            return cls.parse_excel(pad, peildatum)
        if extensie == ".pdf":
            return cls.parse_pdf(pad, peildatum)
        if extensie == ".json":
            return cls.parse_json(pad, peildatum, geboortedatum)
        raise ValueError(
            f"Onbekende bestandsextensie: '{extensie}'. "
            "Ondersteunde formaten: .csv, .xlsx, .xls, .pdf, .json"
        )
