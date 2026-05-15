"""Centraal flow/wizard management voor de stappencirculatie."""

from __future__ import annotations

from enum import Enum

import streamlit as st


class Stap(Enum):
    """Alle stappen in de flow."""

    PERSONEN = "personen"
    PENSIOENGEGEVENS = "pensioengegevens"
    SCENARIO = "scenario"
    COMPONENTEN = "componenten"
    BEREKEN = "bereken"
    RESULTATEN = "resultaten"
    ACCOUNTANT = "accountant"
    RAPPORT = "rapport"
    INSTELLINGEN = "instellingen"  # Buiten flow


# Volgorde van stappen
STAPPEN_VOLGORDE = [
    Stap.PERSONEN,
    Stap.PENSIOENGEGEVENS,
    Stap.SCENARIO,
    Stap.COMPONENTEN,
    Stap.BEREKEN,
    Stap.RESULTATEN,
    Stap.ACCOUNTANT,
    Stap.RAPPORT,
]

STAP_LABELS = {
    Stap.PERSONEN: "👤 Personen",
    Stap.PENSIOENGEGEVENS: "📂 Pensioengegevens",
    Stap.SCENARIO: "📋 Scenario",
    Stap.COMPONENTEN: "💶 Componenten",
    Stap.BEREKEN: "▶ Bereken",
    Stap.RESULTATEN: "📊 Resultaten",
    Stap.ACCOUNTANT: "🔍 Accountant",
    Stap.RAPPORT: "📥 Rapport",
}

# Session state keys
HUIDGE_STAP_KEY = "flow_huidge_stap"
VOLTOOIDE_STAPPEN_KEY = "flow_voltooide_stappen"
STAPPEN_OPNIEUW_NODIG_KEY = "flow_stappen_opnieuw_nodig"


def _init_flow() -> None:
    """Initialiseer flow-state indien nog niet gedaan."""
    if HUIDGE_STAP_KEY not in st.session_state:
        st.session_state[HUIDGE_STAP_KEY] = Stap.PERSONEN
    if VOLTOOIDE_STAPPEN_KEY not in st.session_state:
        st.session_state[VOLTOOIDE_STAPPEN_KEY] = set()
    if STAPPEN_OPNIEUW_NODIG_KEY not in st.session_state:
        st.session_state[STAPPEN_OPNIEUW_NODIG_KEY] = set()


def get_huidge_stap() -> Stap:
    """Geef de huidge stap terug."""
    _init_flow()
    waarde = st.session_state.get(HUIDGE_STAP_KEY, Stap.PERSONEN)
    return waarde if isinstance(waarde, Stap) else Stap.PERSONEN


def set_huidge_stap(stap: Stap, validatie_ok: bool = True) -> None:
    """Stel huidge stap in. Invalideer volgende stappen als we teruggaan."""
    _init_flow()
    huidig = get_huidge_stap()

    if stap == huidig:
        return

    # Bepaal of we teruggaan of vooruitgaan
    huidig_index = STAPPEN_VOLGORDE.index(huidig) if huidig in STAPPEN_VOLGORDE else -1
    stap_index = STAPPEN_VOLGORDE.index(stap) if stap in STAPPEN_VOLGORDE else -1

    if huidig_index > stap_index:
        # Teruggaan: invalideer alles na de vorige stap
        st.session_state[HUIDGE_STAP_KEY] = stap
        volgende_index = stap_index + 1
        for i in range(volgende_index, len(STAPPEN_VOLGORDE)):
            st.session_state[STAPPEN_OPNIEUW_NODIG_KEY].add(STAPPEN_VOLGORDE[i])
    else:
        # Vooruitgaan: markeer huidge als voltooid (als validatie OK)
        st.session_state[HUIDGE_STAP_KEY] = stap
        if validatie_ok and huidig in STAPPEN_VOLGORDE:
            st.session_state[VOLTOOIDE_STAPPEN_KEY].add(huidig)
            # Zorg dat vorige niet meer "opnieuw nodig" is
            if huidig in st.session_state[STAPPEN_OPNIEUW_NODIG_KEY]:
                st.session_state[STAPPEN_OPNIEUW_NODIG_KEY].discard(huidig)


def mark_stap_voltooid(stap: Stap) -> None:
    """Markeer een stap als voltooid."""
    _init_flow()
    st.session_state[VOLTOOIDE_STAPPEN_KEY].add(stap)
    if stap in st.session_state[STAPPEN_OPNIEUW_NODIG_KEY]:
        st.session_state[STAPPEN_OPNIEUW_NODIG_KEY].discard(stap)


def is_stap_voltooid(stap: Stap) -> bool:
    """Controleer of een stap voltooid is."""
    _init_flow()
    return stap in st.session_state.get(VOLTOOIDE_STAPPEN_KEY, set())


def stap_status(stap: Stap) -> str:
    """Geef de status van een stap: 'voltooid', 'huidig', 'opnieuw_nodig', 'toekomstig'."""
    _init_flow()
    huidig = get_huidge_stap()
    opnieuw_nodig = st.session_state.get(STAPPEN_OPNIEUW_NODIG_KEY, set())
    voltooide = st.session_state.get(VOLTOOIDE_STAPPEN_KEY, set())

    if stap in opnieuw_nodig:
        return "opnieuw_nodig"
    elif stap == huidig:
        return "huidig"
    elif stap in voltooide:
        return "voltooid"
    else:
        return "toekomstig"


def get_volgende_stap(stap: Stap | None = None) -> Stap | None:
    """Geef de volgende stap terug."""
    _init_flow()
    if stap is None:
        stap = get_huidge_stap()
    try:
        index = STAPPEN_VOLGORDE.index(stap)
        if index + 1 < len(STAPPEN_VOLGORDE):
            return STAPPEN_VOLGORDE[index + 1]
    except ValueError:
        pass
    return None


def get_vorige_stap(stap: Stap | None = None) -> Stap | None:
    """Geef de vorige stap terug."""
    _init_flow()
    if stap is None:
        stap = get_huidge_stap()
    try:
        index = STAPPEN_VOLGORDE.index(stap)
        if index > 0:
            return STAPPEN_VOLGORDE[index - 1]
    except ValueError:
        pass
    return None


def invalidate_berekeningen() -> None:
    """Invalideer BEREKEN en volgende stappen (gebruikt door instellingen)."""
    _init_flow()
    bereken_index = STAPPEN_VOLGORDE.index(Stap.BEREKEN)
    for i in range(bereken_index, len(STAPPEN_VOLGORDE)):
        st.session_state[STAPPEN_OPNIEUW_NODIG_KEY].add(STAPPEN_VOLGORDE[i])
