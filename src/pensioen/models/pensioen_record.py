"""Datamodel voor een pensioenrecord afkomstig van mijnpensioenoverzicht.nl."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, field_validator, model_validator


class TypePensioen(str, Enum):
    """Type pensioenuitkering."""

    OUDERDOMS = "ouderdoms"
    PARTNER = "partner"
    NABESTAANDEN = "nabestaanden"
    ARBEIDSONGESCHIKTHEID = "arbeidsongeschiktheid"
    LIJFRENTE = "lijfrente"


class PensioenRecord(BaseModel):
    """Een pensioenregeling zoals geëxporteerd vanuit mijnpensioenoverzicht.nl."""

    uitvoerder: str
    regeling: str
    type_pensioen: TypePensioen
    ingangsdatum: date | None = None
    einddatum: date | None = None
    bruto_per_jaar: Decimal  # in euro's per jaar
    partnerpensioen_pct: Decimal = Decimal("0")  # percentage (0–100)
    indexatie_verwacht_pct: Decimal = Decimal("0")  # verwacht jaarlijks %
    indexatie_gegarandeerd_pct: Decimal = Decimal("0")  # gegarandeerd jaarlijks %
    scenario_bedragen: dict[str, Decimal] = {}  # bijv. {"pessimistisch": 17000}
    bronbestand: str = ""
    peildatum: date | None = None

    @field_validator("bruto_per_jaar")
    @classmethod
    def valideer_bruto(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("bruto_per_jaar mag niet negatief zijn.")
        return v

    @field_validator("partnerpensioen_pct")
    @classmethod
    def valideer_partnerpensioen(cls, v: Decimal) -> Decimal:
        if not (Decimal("0") <= v <= Decimal("100")):
            raise ValueError("partnerpensioen_pct moet tussen 0 en 100 liggen.")
        return v

    @field_validator("indexatie_verwacht_pct", "indexatie_gegarandeerd_pct")
    @classmethod
    def valideer_indexatie(cls, v: Decimal) -> Decimal:
        if not (Decimal("-5") <= v <= Decimal("20")):
            raise ValueError(
                "Indexatiepercentage moet tussen -5% en 20% liggen."
            )
        return v

    @model_validator(mode="after")
    def valideer_datums(self) -> PensioenRecord:
        if self.einddatum and self.ingangsdatum and self.einddatum <= self.ingangsdatum:
            raise ValueError("einddatum moet na ingangsdatum liggen.")
        return self
