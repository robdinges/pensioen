"""Datamodel voor een planningsscenario."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, model_validator


class IncidenteelItem(BaseModel):
    """Een eenmalige ontvangst (positief) of uitgave (negatief) op een specifieke datum."""

    datum: date
    bedrag: Decimal  # positief = ontvangst, negatief = uitgave
    omschrijving: str


class Scenario(BaseModel):
    """Een planningsscenario met parameters voor cashflowberekeningen."""

    naam: str

    # Stopdatum werk per persoon
    persoon1_stopdatum_werk: date
    persoon2_stopdatum_werk: date | None = None

    # Bruto jaarsalaris op het moment van aanmaken van het scenario
    persoon1_bruto_jaarsalaris: Decimal = Decimal("0")
    persoon2_bruto_jaarsalaris: Decimal = Decimal("0")

    # Jaarlijkse salarisgroei (percentage)
    salarisgroei_pct: Decimal = Decimal("0")

    # Spaargeld en rendement
    spaargeld_start: Decimal = Decimal("0")  # beginsaldo in euro's
    jaarlijkse_inleg: Decimal = Decimal("0")  # jaarlijkse toevoeging terwijl men werkt
    rendement_pct: Decimal = Decimal("3")  # verwacht jaarlijks rendement in %

    # Incidentele cashflows
    incidentele_items: list[IncidenteelItem] = []

    # Opties
    box3_meenemen: bool = True
    box3_spaargeld_fractie: Decimal = Decimal("1")  # 0=volledig beleggingen, 1=volledig spaargeld
    partner_heffingskorting_overdracht: bool = False

    @model_validator(mode="after")
    def valideer_bedragen(self) -> Scenario:
        if self.spaargeld_start < Decimal("0"):
            raise ValueError("spaargeld_start mag niet negatief zijn.")
        if not (Decimal("0") <= self.rendement_pct <= Decimal("30")):
            raise ValueError("rendement_pct moet tussen 0% en 30% liggen.")
        if not (Decimal("0") <= self.salarisgroei_pct <= Decimal("20")):
            raise ValueError("salarisgroei_pct moet tussen 0% en 20% liggen.")
        return self
