"""Datamodel voor een planningsscenario."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from pensioen.models.component import CategorieComponent, FinancieelComponent


class IncidenteelItem(BaseModel):
    """Een eenmalige ontvangst (positief) of uitgave (negatief) op een specifieke datum."""

    datum: date
    bedrag: Decimal  # positief = ontvangst, negatief = uitgave
    omschrijving: str


class TariefPeriodeItem(BaseModel):
    """Periode-override voor één tariefsleutel."""

    sleutel: str
    startjaar: int | None = None
    eindjaar: int | None = None
    waarde: Decimal
    inflatie_pct: Decimal = Decimal("0")


class Scenario(BaseModel):
    """Een planningsscenario met parameters voor cashflowberekeningen."""

    naam: str  # korte naam voor keuzelijsten
    omschrijving: str = ""
    aangemaakt_op: datetime = Field(default_factory=datetime.now)
    laatst_gewijzigd_op: datetime = Field(default_factory=datetime.now)
    is_default: bool = False

    # Spaargeld en rendement
    spaargeld_start: Decimal = Decimal("0")   # beginsaldo in euro's
    jaarlijkse_inleg: Decimal = Decimal("0")  # jaarlijkse toevoeging aan vermogen
    rendement_pct: Decimal = Decimal("3")     # verwacht jaarlijks rendement in %

    # Financiële componenten (inkomsten, uitgaven, inhoudingen)
    componenten: list[FinancieelComponent] = []

    # Incidentele eenmalige cashflows (niet belastbaar)
    incidentele_items: list[IncidenteelItem] = []

    # Inflatie
    inflatie_pct: Decimal = Decimal("2")  # verwachte jaarlijkse inflatie in %

    # Box 3
    box3_meenemen: bool = True
    box3_spaargeld_fractie: Decimal = Decimal("1")  # 0=beleggingen, 1=spaargeld

    # Periodegebaseerde tariefoverrides
    tarief_periodes: list[TariefPeriodeItem] = []

    @model_validator(mode="after")
    def valideer_bedragen(self) -> Scenario:
        if self.spaargeld_start < Decimal("0"):
            raise ValueError("spaargeld_start mag niet negatief zijn.")
        if not (Decimal("0") <= self.rendement_pct <= Decimal("30")):
            raise ValueError("rendement_pct moet tussen 0% en 30% liggen.")
        if not (Decimal("0") <= self.inflatie_pct <= Decimal("20")):
            raise ValueError("inflatie_pct moet tussen 0% en 20% liggen.")
        for p in self.tarief_periodes:
            if p.startjaar is not None and p.eindjaar is not None and p.eindjaar < p.startjaar:
                raise ValueError("Bij tarief_periodes moet eindjaar >= startjaar zijn.")
            if not (Decimal("0") <= p.inflatie_pct <= Decimal("20")):
                raise ValueError("inflatie_pct in tarief_periodes moet tussen 0% en 20% liggen.")
        return self

    # --- Hulpeigenschappen voor terugwaartse compatibiliteit in rapportages ---
    def arbeidsinkomen_componenten(self, persoon: str) -> list[FinancieelComponent]:
        return [c for c in self.componenten
                if c.categorie == CategorieComponent.ARBEIDSINKOMEN and c.persoon == persoon]

    def inkomen_componenten(self, persoon: str) -> list[FinancieelComponent]:
        """Alle inkomenscategorieën voor een persoon (arbeid + pensioen + overig)."""
        return [c for c in self.componenten
                if c.categorie in (
                    CategorieComponent.ARBEIDSINKOMEN,
                    CategorieComponent.PENSIOEN_INKOMEN,
                    CategorieComponent.OVERIG_INKOMEN,
                ) and c.persoon == persoon]

    def uitgave_componenten(self) -> list[FinancieelComponent]:
        return [c for c in self.componenten if c.categorie == CategorieComponent.UITGAVE]

    def inhouding_componenten(self) -> list[FinancieelComponent]:
        return [c for c in self.componenten if c.categorie == CategorieComponent.INHOUDING]
