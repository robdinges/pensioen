"""Hulpen voor de centrale actieve-scenarioselectie."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import streamlit as st

from pensioen.models.scenario import Scenario

NIEUW_SCENARIO_LABEL = "— Nieuw scenario —"
SCENARIO_SELECTIE_KEY = "scenario_selectie"


def get_actief_scenario_naam(session_state: Mapping[str, object] | None = None) -> str | None:
    """Geef de huidige actieve scenario-naam terug, of None."""
    bron = st.session_state if session_state is None else session_state
    waarde = bron.get(SCENARIO_SELECTIE_KEY)
    if not isinstance(waarde, str) or waarde == NIEUW_SCENARIO_LABEL:
        return None
    return waarde


def get_actief_scenario(
    scenario_lijst: Sequence[Scenario],
    session_state: Mapping[str, object] | None = None,
) -> Scenario | None:
    """Geef het actieve scenario terug als dat geselecteerd is."""
    actieve_naam = get_actief_scenario_naam(session_state=session_state)
    if actieve_naam is None:
        return None
    return next((scenario for scenario in scenario_lijst if scenario.naam == actieve_naam), None)