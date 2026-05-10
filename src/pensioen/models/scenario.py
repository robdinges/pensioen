"""Datamodel voor een planningsscenario."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, model_validator

from pensioen.models.component import CategorieComponent, FinancieelComponent


class IncidenteelItem(BaseModel):
    """Een eenmalige ontvangst (positief) of uitgave (negatief) op een specifieke datum."""

    datum: date
    bedrag: Decimal  # positief = ontvangst, negatief = uitgave
    omschrijving: str


class Scenario(BaseModel):
    """Een planningsscenario met parameters voor cashflowberekeningen."""

    naam: str

    # Optionele oudernaam voor inheritance
    parent_naam: str | None = None
    # Velden die de gebruiker expliciet heeft ingesteld t.o.v. de parent
    overschreven_velden: list[str] = []

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

    @model_validator(mode="after")
    def valideer_bedragen(self) -> Scenario:
        if self.spaargeld_start < Decimal("0"):
            raise ValueError("spaargeld_start mag niet negatief zijn.")
        if not (Decimal("0") <= self.rendement_pct <= Decimal("30")):
            raise ValueError("rendement_pct moet tussen 0% en 30% liggen.")
        if not (Decimal("0") <= self.inflatie_pct <= Decimal("20")):
            raise ValueError("inflatie_pct moet tussen 0% en 20% liggen.")
        return self

    # ------------------------------------------------------------------
    # Inheritance
    # ------------------------------------------------------------------

    _ERFBARE_VELDEN = frozenset({
        "spaargeld_start", "jaarlijkse_inleg", "rendement_pct", "inflatie_pct",
        "componenten", "incidentele_items", "box3_meenemen", "box3_spaargeld_fractie",
    })

    def effectief_scenario(self, scenario_lijst: list[Scenario]) -> Scenario:
        """Geef het effectieve scenario terug waarbij niet-overschreven velden van de parent worden geërfd.

        Ondersteunt enkelvoudige overerving (geen cyclische ketens).
        """
        if self.parent_naam is None:
            return self

        parent_obj = next((s for s in scenario_lijst if s.naam == self.parent_naam), None)
        if parent_obj is None:
            return self  # Parent niet gevonden — gebruik eigen waarden

        # Recursief ouderscenario ophalen (max één niveau diep in ketens)
        ouder_effectief = parent_obj.effectief_scenario(scenario_lijst)

        # Start met ouderwaarden, overschrijf met eigen expliciete velden
        merged = ouder_effectief.model_dump()
        for veld in self.overschreven_velden:
            if veld in self._ERFBARE_VELDEN:
                merged[veld] = self.model_dump()[veld]

        merged["naam"] = self.naam
        merged["parent_naam"] = self.parent_naam
        merged["overschreven_velden"] = self.overschreven_velden
        return Scenario.model_validate(merged)

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
