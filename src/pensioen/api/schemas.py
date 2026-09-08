"""Pydantic schema's voor API-requests."""

from __future__ import annotations

from pensioen.models.opbouw_simulatie import OpbouwKeuze, ActuarieleKeuze

from typing import Any

from pydantic import BaseModel, Field, model_validator

from pensioen.api.referentietabellen import (
    BEDRAG_TYPE_CODES,
    BELEGGINGS_TYPE_CODES,
    CATEGORIE_CODES,
    FREQUENTIE_CODES,
    VERMOGENS_TYPE_CODES,
    map_code,
)
from pensioen.models.pensioen_record import PensioenRecord
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario


def _normaliseer_component_codes(component: dict[str, Any]) -> dict[str, Any]:
    component["categorie"] = map_code(component.get("categorie"), CATEGORIE_CODES)
    component["frequentie"] = map_code(component.get("frequentie"), FREQUENTIE_CODES)
    component["bedrag_type"] = map_code(component.get("bedrag_type"), BEDRAG_TYPE_CODES)
    component["beleggings_type"] = map_code(component.get("beleggings_type"), BELEGGINGS_TYPE_CODES)
    return component


def _normaliseer_vermogensitem_codes(item: dict[str, Any]) -> dict[str, Any]:
    item["type"] = map_code(item.get("type"), VERMOGENS_TYPE_CODES)
    return item


def _normaliseer_scenario_codes(scenario_data: dict[str, Any]) -> dict[str, Any]:
    componenten = scenario_data.get("componenten")
    if isinstance(componenten, list):
        scenario_data["componenten"] = [
            _normaliseer_component_codes(component)
            if isinstance(component, dict)
            else component
            for component in componenten
        ]

    vermogensitems = scenario_data.get("vermogensitems")
    if isinstance(vermogensitems, list):
        scenario_data["vermogensitems"] = [
            _normaliseer_vermogensitem_codes(item)
            if isinstance(item, dict)
            else item
            for item in vermogensitems
        ]

    return scenario_data


def _normaliseer_payload_codes(payload: dict[str, Any]) -> dict[str, Any]:
    scenario = payload.get("scenario")
    if isinstance(scenario, dict):
        payload["scenario"] = _normaliseer_scenario_codes(scenario)

    scenario_lijst = payload.get("scenario_lijst")
    if isinstance(scenario_lijst, list):
        payload["scenario_lijst"] = [
            _normaliseer_scenario_codes(s)
            if isinstance(s, dict)
            else s
            for s in scenario_lijst
        ]

    scenarios = payload.get("scenarios")
    if isinstance(scenarios, list):
        payload["scenarios"] = [
            _normaliseer_scenario_codes(s)
            if isinstance(s, dict)
            else s
            for s in scenarios
        ]

    berekening = payload.get("berekening")
    if isinstance(berekening, dict):
        payload["berekening"] = _normaliseer_payload_codes(berekening)

    scenarios_vergelijking = payload.get("scenarios_vergelijking")
    if isinstance(scenarios_vergelijking, list):
        payload["scenarios_vergelijking"] = [
            _normaliseer_scenario_codes(s)
            if isinstance(s, dict)
            else s
            for s in scenarios_vergelijking
        ]

    return payload


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

    @model_validator(mode="before")
    @classmethod
    def normaliseer_codes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return _normaliseer_payload_codes(data)
        return data

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

    @model_validator(mode="before")
    @classmethod
    def normaliseer_codes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return _normaliseer_payload_codes(data)
        return data

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

    @model_validator(mode="before")
    @classmethod
    def normaliseer_codes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return _normaliseer_payload_codes(data)
        return data


class PensioenopbouwRequest(BaseModel):
    """Afzonderlijke simulator; de basisinvoer wordt niet overschreven."""
    berekening: BerekeningRequest
    keuze: OpbouwKeuze

    @model_validator(mode="after")
    def valideer_horizon(self) -> "PensioenopbouwRequest":
        if not self.berekening.jaar_van <= self.keuze.laatste_werkdag.year <= self.berekening.jaar_tot:
            raise ValueError("De stopdatum moet binnen de berekeningsperiode liggen, zodat alle premies meetellen.")
        if self.keuze.pensioen_vanaf.year > self.berekening.jaar_tot:
            raise ValueError("Verleng de berekeningsperiode tot minstens het jaar waarin het pensioen ingaat.")
        return self


class ActuarieleSchattingRequest(BaseModel):
    berekening: BerekeningRequest
    keuze: ActuarieleKeuze = Field(default_factory=ActuarieleKeuze)
