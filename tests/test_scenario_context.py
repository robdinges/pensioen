"""Tests voor de centrale scenarioselectie."""

from __future__ import annotations

from decimal import Decimal

from pensioen.models.scenario import Scenario
from pensioen.ui.scenario_context import NIEUW_SCENARIO_LABEL, get_actief_scenario, get_actief_scenario_naam


def test_actieve_scenario_naam_uit_session_state() -> None:
    session_state = {"scenario_selectie": "Scenario A"}

    assert get_actief_scenario_naam(session_state) == "Scenario A"


def test_nieuw_scenario_is_geen_actief_scenario() -> None:
    session_state = {"scenario_selectie": NIEUW_SCENARIO_LABEL}

    assert get_actief_scenario_naam(session_state) is None


def test_actief_scenario_wordt_gevonden_op_naam() -> None:
    scenario_lijst = [
        Scenario(naam="Scenario A", spaargeld_start=Decimal("1000")),
        Scenario(naam="Scenario B", spaargeld_start=Decimal("2000")),
    ]
    session_state = {"scenario_selectie": "Scenario B"}

    actief = get_actief_scenario(scenario_lijst, session_state)
    assert actief is not None
    assert actief.naam == "Scenario B"