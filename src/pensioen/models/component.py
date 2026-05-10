"""Financieel component: een periodieke of eenmalige cashflow in een scenario."""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import cast

from pydantic import BaseModel, Field, field_validator, model_validator

from pensioen.models.periodieke_waarde import PeriodiekeWaarde, selecteer_periodieke_waarde


class Frequentie(str, Enum):
    """Betalingsfrequentie van een financieel component."""

    EENMALIG = "eenmalig"
    MAANDELIJKS = "maandelijks"
    KWARTAAL = "kwartaal"
    HALFJAARLIJKS = "halfjaarlijks"
    JAARLIJKS = "jaarlijks"

    def maanden_per_periode(self) -> int:
        """Aantal maanden per betalingsperiode (voor spreiding naar maandbedrag)."""
        return {
            Frequentie.EENMALIG: 1,
            Frequentie.MAANDELIJKS: 1,
            Frequentie.KWARTAAL: 3,
            Frequentie.HALFJAARLIJKS: 6,
            Frequentie.JAARLIJKS: 12,
        }[self]


class CategorieComponent(str, Enum):
    """Categorie van het financieel component (bepaalt belasting- en cashflowbehandeling)."""

    ARBEIDSINKOMEN = "arbeidsinkomen"        # bruto, telt mee voor arbeidskorting
    PENSIOEN_INKOMEN = "pensioen_inkomen"    # bruto pensioen (handmatig, naast MPO)
    OVERIG_INKOMEN = "overig_inkomen"        # bruto overig inkomen (uitkering etc.)
    UITGAVE = "uitgave"                      # huishoudelijke uitgave (na belasting)
    INHOUDING = "inhouding"                  # netto inhouding (na belasting)


class BedragType(str, Enum):
    """Type bedrag voor inkomenscomponenten: bruto (belast) of netto (onbelast)."""

    BRUTO = "bruto"
    NETTO = "netto"


class BedragPeriode(BaseModel):
    """Een afzonderlijke periode binnen een financieel component."""

    bedrag: Decimal
    startdatum: date | None = None
    einddatum: date | None = None

    @field_validator("bedrag")
    @classmethod
    def bedrag_niet_negatief(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("bedrag mag niet negatief zijn.")
        return v


class FinancieelComponent(BaseModel):
    """Een periodieke of eenmalige cashflow binnen een scenario."""

    omschrijving: str
    categorie: CategorieComponent
    persoon: str = "P1"          # "P1", "P2" of "Huishouden"
    bedrag: Decimal              # bedrag per frequentie-periode (positief)
    bedrag_type: BedragType = BedragType.BRUTO
    frequentie: Frequentie = Frequentie.MAANDELIJKS
    begindatum: date | None = None   # None = geen beperking aan het begin
    einddatum: date | None = None    # None = oneindig
    groei_pct: Decimal = Decimal("0")  # groei per kalenderjaar (%)
    waarde_periodes: list[BedragPeriode] = Field(default_factory=list)

    @field_validator("bedrag")
    @classmethod
    def bedrag_niet_negatief(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("bedrag mag niet negatief zijn.")
        return v

    @model_validator(mode="after")
    def valideer_datums(self) -> FinancieelComponent:
        if self.begindatum and self.einddatum and self.einddatum < self.begindatum:
            raise ValueError("einddatum mag niet vóór begindatum liggen.")
        return self

    def is_actief(self, jaar: int, maand: int) -> bool:
        """Is dit component actief in de gegeven kalendermaand?"""
        dag_begin = date(jaar, maand, 1)
        dag_eind = date(jaar, maand, calendar.monthrange(jaar, maand)[1])

        if self.waarde_periodes:
            peildatum = date(jaar, maand, 1)
            periode = selecteer_periodieke_waarde(
                self._waarde_perioden(),
                peildatum,
            )
            return periode is not None

        if self.frequentie == Frequentie.EENMALIG:
            if self.begindatum is None:
                return False
            return self.begindatum.year == jaar and self.begindatum.month == maand

        if self.begindatum and dag_eind < self.begindatum:
            return False
        if self.einddatum and dag_begin > self.einddatum:
            return False
        return True

    def bedrag_per_maand_actief(self, jaar: int, maand: int) -> Decimal:
        """
        Maandelijks equivalent bedrag inclusief groei, of Decimal('0') als niet actief.

        Periodieke bedragen worden gelijkmatig over maanden gespreid:
        - Maandelijks: bedrag × 1
        - Kwartaal: bedrag / 3
        - Halfjaarlijks: bedrag / 6
        - Jaarlijks: bedrag / 12
        - Eenmalig: het volledige bedrag in de maand van begindatum
        """
        peildatum = date(jaar, maand, 1)

        if self.waarde_periodes:
            periode = selecteer_periodieke_waarde(
                self._waarde_perioden(),
                peildatum,
            )
            if periode is None:
                return Decimal("0")
            basis_bedrag = periode.waarde
            startjaar = periode.startdatum.year if periode.startdatum else jaar
        else:
            if not self.is_actief(jaar, maand):
                return Decimal("0")
            basis_bedrag = self.bedrag
            startjaar = self.begindatum.year if self.begindatum else jaar

        jaren_groei = max(0, jaar - startjaar)
        groeifactor = (Decimal("1") + self.groei_pct / Decimal("100")) ** jaren_groei

        if self.frequentie == Frequentie.EENMALIG:
            return basis_bedrag * groeifactor

        return (basis_bedrag * groeifactor) / Decimal(str(self.frequentie.maanden_per_periode()))

    def is_inkomen(self) -> bool:
        """True voor componenten die als inkomsten worden behandeld."""
        return self.categorie in {
            CategorieComponent.ARBEIDSINKOMEN,
            CategorieComponent.PENSIOEN_INKOMEN,
            CategorieComponent.OVERIG_INKOMEN,
        }

    def _waarde_perioden(self) -> list[PeriodiekeWaarde]:
        """Converteer de Pydantic-lijst naar expliciete periodieke waarden."""
        return [
            PeriodiekeWaarde(
                waarde=p.bedrag,
                startdatum=p.startdatum,
                einddatum=p.einddatum,
            )
            for p in cast(list[BedragPeriode], self.waarde_periodes)
        ]


# ---------------------------------------------------------------------------
# Component-sjablonen
# ---------------------------------------------------------------------------

from dataclasses import dataclass  # noqa: E402


@dataclass(frozen=True)
class ComponentSjabloon:
    """Eén sjabloon — waarden zijn aanpasbaar na toevoegen in de UI."""

    label: str
    categorie: CategorieComponent
    bedrag_type: BedragType
    frequentie: Frequentie
    bedrag: Decimal
    groei_pct: Decimal
    persoon: str
    omschrijving: str


COMPONENT_SJABLONEN: list[ComponentSjabloon] = [
    ComponentSjabloon(label="Salaris (bruto, maandelijks)", categorie=CategorieComponent.ARBEIDSINKOMEN, bedrag_type=BedragType.BRUTO, frequentie=Frequentie.MAANDELIJKS, bedrag=Decimal("4000"), groei_pct=Decimal("2"), persoon="P1", omschrijving="Salaris"),
    ComponentSjabloon(label="AOW-aanvulling (netto, maandelijks)", categorie=CategorieComponent.OVERIG_INKOMEN, bedrag_type=BedragType.NETTO, frequentie=Frequentie.MAANDELIJKS, bedrag=Decimal("1000"), groei_pct=Decimal("0"), persoon="P1", omschrijving="AOW-aanvulling"),
    ComponentSjabloon(label="Werkgeverspensioen (bruto, maandelijks)", categorie=CategorieComponent.PENSIOEN_INKOMEN, bedrag_type=BedragType.BRUTO, frequentie=Frequentie.MAANDELIJKS, bedrag=Decimal("1500"), groei_pct=Decimal("0"), persoon="P1", omschrijving="Werkgeverspensioen"),
    ComponentSjabloon(label="Hypotheek (netto, maandelijks)", categorie=CategorieComponent.UITGAVE, bedrag_type=BedragType.NETTO, frequentie=Frequentie.MAANDELIJKS, bedrag=Decimal("1200"), groei_pct=Decimal("0"), persoon="Huishouden", omschrijving="Hypotheek"),
    ComponentSjabloon(label="Vaste lasten (netto, maandelijks)", categorie=CategorieComponent.UITGAVE, bedrag_type=BedragType.NETTO, frequentie=Frequentie.MAANDELIJKS, bedrag=Decimal("800"), groei_pct=Decimal("2"), persoon="Huishouden", omschrijving="Vaste lasten"),
    ComponentSjabloon(label="Freelance / ZZP (bruto, maandelijks)", categorie=CategorieComponent.ARBEIDSINKOMEN, bedrag_type=BedragType.BRUTO, frequentie=Frequentie.MAANDELIJKS, bedrag=Decimal("2000"), groei_pct=Decimal("1"), persoon="P1", omschrijving="Freelance inkomen"),
    ComponentSjabloon(label="Jaarlijkse bonus (bruto, jaarlijks)", categorie=CategorieComponent.ARBEIDSINKOMEN, bedrag_type=BedragType.BRUTO, frequentie=Frequentie.JAARLIJKS, bedrag=Decimal("5000"), groei_pct=Decimal("0"), persoon="P1", omschrijving="Jaarbonus"),
    ComponentSjabloon(label="Lease-bijdrage auto (netto, maandelijks)", categorie=CategorieComponent.INHOUDING, bedrag_type=BedragType.NETTO, frequentie=Frequentie.MAANDELIJKS, bedrag=Decimal("250"), groei_pct=Decimal("0"), persoon="P1", omschrijving="Lease-bijdrage auto"),
    ComponentSjabloon(label="Huurinkomsten (netto, maandelijks)", categorie=CategorieComponent.OVERIG_INKOMEN, bedrag_type=BedragType.NETTO, frequentie=Frequentie.MAANDELIJKS, bedrag=Decimal("600"), groei_pct=Decimal("2"), persoon="Huishouden", omschrijving="Huurinkomsten"),
    ComponentSjabloon(label="Partner-salaris (bruto, maandelijks)", categorie=CategorieComponent.ARBEIDSINKOMEN, bedrag_type=BedragType.BRUTO, frequentie=Frequentie.MAANDELIJKS, bedrag=Decimal("3000"), groei_pct=Decimal("2"), persoon="P2", omschrijving="Salaris partner"),
]
