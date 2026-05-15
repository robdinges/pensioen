"""Hulpen voor de centrale actieve-scenarioselectie."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import streamlit as st

from pensioen.models.scenario import Scenario

NIEUW_SCENARIO_LABEL = "— Nieuw scenario —"
SCENARIO_SELECTIE_KEY = "scenario_selectie"
SCENARIO_ACTIEF_KEY = "scenario_selectie_actief"
SCENARIO_DEFAULT_KEY = "scenario_default_naam"
DEFAULT_SCENARIO_NAAM = "Default"


def _geldige_scenario_namen(scenario_lijst: Sequence[Scenario]) -> list[str]:
    return [s.naam for s in scenario_lijst if isinstance(s.naam, str) and s.naam.strip()]


def _bepaal_default_uit_scenarios(scenario_lijst: Sequence[Scenario]) -> str | None:
    kandidaten = [s for s in scenario_lijst if s.is_default]
    if not kandidaten:
        return None
    kandidaten.sort(key=lambda s: s.laatst_gewijzigd_op)
    return kandidaten[-1].naam


def ensure_scenario_context() -> list[Scenario]:
    """Initialiseer actieve/default scenario-context en zorg voor een bruikbaar scenario."""
    scenario_lijst = st.session_state.get("scenario_lijst", [])
    if not isinstance(scenario_lijst, list):
        scenario_lijst = []

    if not scenario_lijst:
        scenario_lijst = [Scenario(naam=DEFAULT_SCENARIO_NAAM)]
        st.session_state["scenario_lijst"] = scenario_lijst

    namen = _geldige_scenario_namen(scenario_lijst)
    if not namen:
        scenario_lijst = [Scenario(naam=DEFAULT_SCENARIO_NAAM)]
        st.session_state["scenario_lijst"] = scenario_lijst
        namen = [DEFAULT_SCENARIO_NAAM]

    default_uit_model = _bepaal_default_uit_scenarios(scenario_lijst)
    default_naam = default_uit_model or st.session_state.get(SCENARIO_DEFAULT_KEY)
    if not isinstance(default_naam, str) or default_naam not in namen:
        oud_actief = st.session_state.get(SCENARIO_ACTIEF_KEY)
        oud_widget = st.session_state.get(SCENARIO_SELECTIE_KEY)
        kandidaat = (
            oud_actief if isinstance(oud_actief, str) and oud_actief in namen
            else oud_widget if isinstance(oud_widget, str) and oud_widget in namen
            else DEFAULT_SCENARIO_NAAM if DEFAULT_SCENARIO_NAAM in namen
            else namen[0]
        )
        st.session_state[SCENARIO_DEFAULT_KEY] = kandidaat
        default_naam = kandidaat

    actief_naam = st.session_state.get(SCENARIO_ACTIEF_KEY)
    init_gedaan = bool(st.session_state.get("_scenario_context_init"))
    if not init_gedaan:
        # Bij app-start: gebruik actief_naam uit geladen sessie als dat geldig is,
        # anders terugvallen op het standaardscenario.
        if not isinstance(actief_naam, str) or actief_naam not in namen:
            st.session_state[SCENARIO_ACTIEF_KEY] = default_naam
        st.session_state["_scenario_context_init"] = True
    elif not isinstance(actief_naam, str) or actief_naam not in namen:
        st.session_state[SCENARIO_ACTIEF_KEY] = default_naam

    # Legacy-key alleen initialiseren als deze nog ontbreekt.
    if SCENARIO_SELECTIE_KEY not in st.session_state:
        st.session_state[SCENARIO_SELECTIE_KEY] = st.session_state.get(SCENARIO_ACTIEF_KEY)
    return scenario_lijst


def set_actief_scenario_naam(naam: str) -> None:
    """Stel het actieve scenario in wanneer de naam bestaat."""
    scenario_lijst = st.session_state.get("scenario_lijst", [])
    namen = _geldige_scenario_namen(scenario_lijst)
    if naam in namen:
        st.session_state[SCENARIO_ACTIEF_KEY] = naam


def set_default_scenario_naam(naam: str, maak_ook_actief: bool = False) -> None:
    """Stel het standaardscenario in en optioneel ook het actieve scenario."""
    scenario_lijst = st.session_state.get("scenario_lijst", [])
    namen = _geldige_scenario_namen(scenario_lijst)
    if naam in namen:
        st.session_state[SCENARIO_DEFAULT_KEY] = naam
        if maak_ook_actief:
            set_actief_scenario_naam(naam)


def get_actief_scenario_naam(session_state: Mapping[str, object] | None = None) -> str | None:
    """Geef de huidige actieve scenario-naam terug, of None."""
    bron = st.session_state if session_state is None else session_state
    waarde = bron.get(SCENARIO_ACTIEF_KEY)
    if not isinstance(waarde, str) or waarde == NIEUW_SCENARIO_LABEL:
        waarde = bron.get(SCENARIO_SELECTIE_KEY)
    if not isinstance(waarde, str) or waarde == NIEUW_SCENARIO_LABEL:
        return None
    return waarde


def get_default_scenario_naam(session_state: Mapping[str, object] | None = None) -> str | None:
    """Geef de standaardscenario-naam terug, of None."""
    bron = st.session_state if session_state is None else session_state
    waarde = bron.get(SCENARIO_DEFAULT_KEY)
    return waarde if isinstance(waarde, str) else None


def get_actief_scenario(
    scenario_lijst: Sequence[Scenario],
    session_state: Mapping[str, object] | None = None,
) -> Scenario | None:
    """Geef het actieve scenario terug als dat geselecteerd is."""
    actieve_naam = get_actief_scenario_naam(session_state=session_state)
    if actieve_naam is None:
        return None
    return next((scenario for scenario in scenario_lijst if scenario.naam == actieve_naam), None)