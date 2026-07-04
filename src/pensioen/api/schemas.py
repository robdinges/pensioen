"""Pydantic schema's voor API-requests."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from pensioen.models.pensioen_record import PensioenRecord
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario


class BerekeningRequest(BaseModel):
    """Request voor een enkele huishoudberekening."""

    scenario: Scenario
    persoon1: Persoon
    persoon2: Persoon | None = None
    records1: list[PensioenRecord] = Field(default_factory=list)
    records2: list[PensioenRecord] = Field(default_factory=list)
    jaar_van: int
    jaar_tot: int
    scenario_lijst: list[Scenario] = Field(default_factory=list)

    @model_validator(mode="after")
    def valideer_jaarrange(self) -> "BerekeningRequest":
        if self.jaar_tot < self.jaar_van:
            raise ValueError("jaar_tot moet groter of gelijk zijn aan jaar_van")
        return self


class VergelijkingRequest(BaseModel):
    """Request voor vergelijking van meerdere scenario's."""

    scenarios: list[Scenario]
    persoon1: Persoon
    persoon2: Persoon | None = None
    records1: list[PensioenRecord] = Field(default_factory=list)
    records2: list[PensioenRecord] = Field(default_factory=list)
    jaar_van: int
    jaar_tot: int

    @model_validator(mode="after")
    def valideer_input(self) -> "VergelijkingRequest":
        if not self.scenarios:
            raise ValueError("Minimaal 1 scenario is vereist")
        if self.jaar_tot < self.jaar_van:
            raise ValueError("jaar_tot moet groter of gelijk zijn aan jaar_van")
        return self


class RapportageRequest(BaseModel):
    """Request voor Excel-rapportage."""

    berekening: BerekeningRequest
    include_vergelijking: bool = False
    scenarios_vergelijking: list[Scenario] = Field(default_factory=list)
