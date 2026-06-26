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
    Stap.RESULTATEN,
    Stap.ACCOUNTANT,
    Stap.RAPPORT,
]

STAP_LABELS = {
    Stap.PERSONEN: "Personen",
    Stap.PENSIOENGEGEVENS: "Pensioengegevens",
    Stap.SCENARIO: "Scenario",
    Stap.COMPONENTEN: "Componenten",
    Stap.BEREKEN: "Berekenen",  # Verplaatst naar sidebar
    Stap.RESULTATEN: "Resultaten",
    Stap.ACCOUNTANT: "Accountant",
    Stap.RAPPORT: "Rapport",
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
    """Haal huidge stap op."""
    _init_flow()
    waarde = st.session_state.get(HUIDGE_STAP_KEY, Stap.PERSONEN)
    return waarde if isinstance(waarde, Stap) else Stap.PERSONEN


def set_huidge_stap(stap: Stap, validatie_ok: bool = True) -> None:
    """Zet huidge stap en markeer vorige als voltooid."""
    _init_flow()
    
    if validatie_ok:
        st.session_state[VOLTOOIDE_STAPPEN_KEY].add(get_huidge_stap())
    
    huidig = get_huidge_stap()
    huidig_index = STAPPEN_VOLGORDE.index(huidig) if huidig in STAPPEN_VOLGORDE else -1
    stap_index = STAPPEN_VOLGORDE.index(stap) if stap in STAPPEN_VOLGORDE else -1
    
    # Als we vooruit gaan, markeer alles ertussen als voltooid
    if stap_index > huidig_index >= 0:
        volgende_index = huidig_index + 1
        for i in range(volgende_index, len(STAPPEN_VOLGORDE)):
            st.session_state[STAPPEN_OPNIEUW_NODIG_KEY].add(STAPPEN_VOLGORDE[i])
    
    # Markeer als voltooid
    if validatie_ok and huidig in STAPPEN_VOLGORDE:
        st.session_state[VOLTOOIDE_STAPPEN_KEY].add(huidig)
        st.session_state[STAPPEN_OPNIEUW_NODIG_KEY].discard(huidig)
    
    st.session_state[HUIDGE_STAP_KEY] = stap


def stap_voltooid(stap: Stap) -> bool:
    """Check of een stap voltooid is."""
    _init_flow()
    return stap in st.session_state.get(VOLTOOIDE_STAPPEN_KEY, set())


def stap_opnieuw_nodig(stap: Stap) -> bool:
    """Check of een stap opnieuw doorlopen moet worden."""
    _init_flow()
    return stap in st.session_state.get(STAPPEN_OPNIEUW_NODIG_KEY, set())


def voltooi_stap(stap: Stap) -> None:
    """Markeer stap als voltooid."""
    _init_flow()
    st.session_state[VOLTOOIDE_STAPPEN_KEY].add(stap)
    if stap in st.session_state[STAPPEN_OPNIEUW_NODIG_KEY]:
        st.session_state[STAPPEN_OPNIEUW_NODIG_KEY].discard(stap)


def volgende_stap(stap: Stap) -> Stap | None:
    """Haal volgende stap op."""
    if stap not in STAPPEN_VOLGORDE:
        return None
    
    index = STAPPEN_VOLGORDE.index(stap)
    if index + 1 < len(STAPPEN_VOLGORDE):
        return STAPPEN_VOLGORDE[index + 1]
    
    return None


def vorige_stap(stap: Stap) -> Stap | None:
    """Haal vorige stap op."""
    if stap not in STAPPEN_VOLGORDE:
        return None
    
    index = STAPPEN_VOLGORDE.index(stap)
    if index > 0:
        return STAPPEN_VOLGORDE[index - 1]
    
    return None


def invalideer_stappen_na(stap: Stap) -> None:
    """Markeer alle stappen na de gegeven stap als opnieuw nodig."""
    _init_flow()
    
    stap_index = STAPPEN_VOLGORDE.index(stap)
    for i in range(stap_index, len(STAPPEN_VOLGORDE)):
        st.session_state[STAPPEN_OPNIEUW_NODIG_KEY].add(STAPPEN_VOLGORDE[i])


def mark_stap_voltooid(stap: Stap) -> None:
    """Compatibele alias voor voltooi_stap."""
    voltooi_stap(stap)


def is_stap_voltooid(stap: Stap) -> bool:
    """Compatibele alias voor stap_voltooid."""
    return stap_voltooid(stap)


def stap_status(stap: Stap) -> str:
    """Compatibele stapstatus voor oudere callsites."""
    _init_flow()
    huidig = get_huidge_stap()
    if stap_opnieuw_nodig(stap):
        return "opnieuw_nodig"
    if stap == huidig:
        return "huidig"
    if stap_voltooid(stap):
        return "voltooid"
    return "toekomstig"


def get_volgende_stap(stap: Stap | None = None) -> Stap | None:
    """Compatibele alias voor volgende_stap."""
    _init_flow()
    if stap is None:
        stap = get_huidge_stap()
    return volgende_stap(stap)


def get_vorige_stap(stap: Stap | None = None) -> Stap | None:
    """Compatibele alias voor vorige_stap."""
    _init_flow()
    if stap is None:
        stap = get_huidge_stap()
    return vorige_stap(stap)


def invalidate_berekeningen() -> None:
    """Compatibele alias voor het invalideren vanaf de berekenstap."""
    invalideer_stappen_na(Stap.BEREKEN)
