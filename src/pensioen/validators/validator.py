"""Validatie van PensioenRecord-lijsten op volledigheid en consistentie."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal

from pensioen.models.pensioen_record import PensioenRecord, TypePensioen

logger = logging.getLogger(__name__)

Ernst = Literal["FOUT", "WAARSCHUWING", "INFO"]

# Grens boven welke een bedrag als onrealistisch wordt gemarkeerd
MAX_REALISTISCH_BEDRAG = Decimal("500000")
MIN_REALISTISCH_BEDRAG = Decimal("100")


@dataclass
class ValidationFout:
    """Eén validatiebevinding."""

    ernst: Ernst
    veld: str
    bericht: str
    record_index: int | None = None


@dataclass
class ValidationResultaat:
    """Resultaat van de validatie van een lijst pensioenrecords."""

    fouten: list[ValidationFout] = field(default_factory=list)
    waarschuwingen: list[ValidationFout] = field(default_factory=list)
    info: list[ValidationFout] = field(default_factory=list)

    @property
    def is_geldig(self) -> bool:
        """Geldig = geen fouten (waarschuwingen zijn toegestaan)."""
        return len(self.fouten) == 0

    @property
    def heeft_meldingen(self) -> bool:
        return len(self.fouten) > 0 or len(self.waarschuwingen) > 0

    def alle_meldingen(self) -> list[ValidationFout]:
        return self.fouten + self.waarschuwingen + self.info

    def voeg_toe(self, fout: ValidationFout) -> None:
        if fout.ernst == "FOUT":
            self.fouten.append(fout)
        elif fout.ernst == "WAARSCHUWING":
            self.waarschuwingen.append(fout)
        else:
            self.info.append(fout)


def _valideer_record(
    record: PensioenRecord, index: int, resultaat: ValidationResultaat
) -> None:
    """Valideer één record op ontbrekende velden en ongeldige waarden."""

    # Verplichte velden
    if not record.uitvoerder.strip():
        resultaat.voeg_toe(ValidationFout("FOUT", "uitvoerder", "Uitvoerder is verplicht.", index))
    if not record.regeling.strip():
        resultaat.voeg_toe(ValidationFout("FOUT", "regeling", "Regeling is verplicht.", index))
    if record.ingangsdatum is None:
        resultaat.voeg_toe(
            ValidationFout("FOUT", "ingangsdatum", "Ingangsdatum ontbreekt.", index)
        )

    # Negatieve bedragen
    if record.bruto_per_jaar < Decimal("0"):
        resultaat.voeg_toe(
            ValidationFout(
                "FOUT",
                "bruto_per_jaar",
                f"bruto_per_jaar is negatief: €{record.bruto_per_jaar}.",
                index,
            )
        )

    # Onrealistische bedragen
    if record.bruto_per_jaar > MAX_REALISTISCH_BEDRAG:
        resultaat.voeg_toe(
            ValidationFout(
                "WAARSCHUWING",
                "bruto_per_jaar",
                f"bruto_per_jaar van €{record.bruto_per_jaar:,.0f} lijkt onrealistisch hoog "
                f"(> €{MAX_REALISTISCH_BEDRAG:,.0f}). Controleer het bronbestand.",
                index,
            )
        )

    if (
        record.bruto_per_jaar > Decimal("0")
        and record.bruto_per_jaar < MIN_REALISTISCH_BEDRAG
    ):
        resultaat.voeg_toe(
            ValidationFout(
                "WAARSCHUWING",
                "bruto_per_jaar",
                f"bruto_per_jaar van €{record.bruto_per_jaar} is erg laag "
                f"(< €{MIN_REALISTISCH_BEDRAG}). Is het bedrag per jaar (niet per maand)?",
                index,
            )
        )

    # Partnerpensioen percentage
    if record.partnerpensioen_pct > Decimal("100"):
        resultaat.voeg_toe(
            ValidationFout(
                "FOUT",
                "partnerpensioen_pct",
                f"partnerpensioen_pct van {record.partnerpensioen_pct}% overschrijdt 100%.",
                index,
            )
        )

    # Einddatum voor ingangsdatum
    if record.einddatum and record.ingangsdatum and record.einddatum <= record.ingangsdatum:
        resultaat.voeg_toe(
            ValidationFout(
                "FOUT",
                "einddatum",
                f"einddatum ({record.einddatum}) is niet na ingangsdatum ({record.ingangsdatum}).",
                index,
            )
        )

    # Toekomstige peildatum waarschuwing
    if record.peildatum and record.peildatum > date.today():
        resultaat.voeg_toe(
            ValidationFout(
                "WAARSCHUWING",
                "peildatum",
                f"peildatum {record.peildatum} ligt in de toekomst.",
                index,
            )
        )


def _valideer_duplicaten(
    records: list[PensioenRecord], resultaat: ValidationResultaat
) -> None:
    """Waarschuw bij dubbele records (zelfde uitvoerder + regeling + ingangsdatum)."""
    gezien: set[tuple] = set()
    for i, record in enumerate(records):
        sleutel = (
            record.uitvoerder.strip().lower(),
            record.regeling.strip().lower(),
            record.ingangsdatum,
        )
        if sleutel in gezien:
            resultaat.voeg_toe(
                ValidationFout(
                    "WAARSCHUWING",
                    "regeling",
                    f"Duplicaat gevonden: {record.uitvoerder} / {record.regeling} / "
                    f"{record.ingangsdatum}. Controleer op dubbelinvoer.",
                    i,
                )
            )
        gezien.add(sleutel)


def _valideer_overlappende_periodes(
    records: list[PensioenRecord], resultaat: ValidationResultaat
) -> None:
    """
    Detecteer overlappende uitkeringsperiodes voor hetzelfde type pensioen.

    Overlappende ouderdomspensioenen van meerdere uitvoerders zijn normaal
    (meerdere regelingen). Dit is een informatieve melding, geen fout.
    """
    # Groepeer ouderdomspensioenen met einddatum
    ouderdoms = [
        (i, r)
        for i, r in enumerate(records)
        if r.type_pensioen == TypePensioen.OUDERDOMS and r.einddatum is not None
    ]

    for i, (idx_a, a) in enumerate(ouderdoms):
        for idx_b, b in ouderdoms[i + 1 :]:
            # Overlap: a.start < b.eind AND a.eind > b.start
            if a.ingangsdatum < b.einddatum and a.einddatum > b.ingangsdatum:
                resultaat.voeg_toe(
                    ValidationFout(
                        "INFO",
                        "ingangsdatum",
                        f"Overlappende ouderdomspensioenen gevonden: "
                        f"'{a.regeling}' en '{b.regeling}'. Controleer of dit correct is.",
                        idx_a,
                    )
                )


def valideer_records(records: list[PensioenRecord]) -> ValidationResultaat:
    """
    Voer volledige validatie uit op een lijst pensioenrecords.

    Args:
        records: Lijst van geparseerde PensioenRecord-objecten.

    Returns:
        ValidationResultaat met fouten, waarschuwingen en info-meldingen.
    """
    resultaat = ValidationResultaat()

    if not records:
        resultaat.voeg_toe(
            ValidationFout("WAARSCHUWING", "algemeen", "Geen pensioenrecords gevonden.")
        )
        return resultaat

    for i, record in enumerate(records):
        _valideer_record(record, i, resultaat)

    _valideer_duplicaten(records, resultaat)
    _valideer_overlappende_periodes(records, resultaat)

    return resultaat
