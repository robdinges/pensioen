"""Parser voor MijnPensioenoverzicht exports (CSV, Excel, optioneel PDF)."""

from __future__ import annotations

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

    @classmethod
    def parse(cls, pad: Path, peildatum: date | None = None) -> list[PensioenRecord]:
        """
        Parseer automatisch op basis van de bestandsextensie.

        Ondersteunde extensies: .csv, .xlsx, .xls, .pdf
        """
        extensie = pad.suffix.lower()
        if extensie == ".csv":
            return cls.parse_csv(pad, peildatum)
        if extensie in (".xlsx", ".xls"):
            return cls.parse_excel(pad, peildatum)
        if extensie == ".pdf":
            return cls.parse_pdf(pad, peildatum)
        raise ValueError(
            f"Onbekende bestandsextensie: '{extensie}'. "
            "Ondersteunde formaten: .csv, .xlsx, .xls, .pdf"
        )
