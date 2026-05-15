"""Streamlit-applicatie: pensioenprognose huishouden."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Pensioenplanner",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

from pensioen.ui.flow_context import (
    STAP_LABELS,
    STAPPEN_VOLGORDE,
    Stap,
    get_huidge_stap,
    set_huidge_stap,
    stap_status,
)
from pensioen.ui.pagina_import import toon_import_pagina
from pensioen.ui.pagina_instellingen import toon_instellingen_pagina
from pensioen.ui.pagina_componenten import toon_componenten_pagina
from pensioen.ui.pagina_persoon import toon_persoon_pagina
from pensioen.ui.pagina_rapport import toon_rapport_pagina
from pensioen.ui.pagina_resultaten import toon_resultaten_pagina
from pensioen.ui.pagina_scenario import toon_scenario_pagina
from pensioen.ui.pagina_bereken import toon_bereken_pagina
from pensioen.ui.pagina_accountant import toon_accountant_pagina
from pensioen.ui.sessie_persistentie import autosla_sessie_op, laad_sessie
from pensioen.ui.style import injecteer_stijl
from pensioen.ui.scenario_context import (
    ensure_scenario_context,
    get_actief_scenario_naam,
    set_actief_scenario_naam,
)

# Injecteer professionele huisstijl
injecteer_stijl()

# Herstel sessie bij (her)start (eenmalig per serversessie)
laad_sessie()
scenario_lijst = ensure_scenario_context()

# Flow mapping: Stap → pagina function
STAP_NAAR_PAGINA = {
    Stap.PERSONEN: toon_persoon_pagina,
    Stap.PENSIOENGEGEVENS: toon_import_pagina,
    Stap.SCENARIO: toon_scenario_pagina,
    Stap.COMPONENTEN: toon_componenten_pagina,
    Stap.BEREKEN: toon_bereken_pagina,
    Stap.RESULTATEN: toon_resultaten_pagina,
    Stap.ACCOUNTANT: toon_accountant_pagina,
    Stap.RAPPORT: toon_rapport_pagina,
}

# --- Sidebar setup ---
st.sidebar.markdown(
    '<p style="color:#D0E3F3;font-size:1rem;font-weight:700;'
    'padding:0 0.75rem;margin:0 0 1.25rem 0;letter-spacing:-0.01em">'
    'Pensioenplanner</p>',
    unsafe_allow_html=True,
)

# Voortgangslijst (stappen)
st.sidebar.markdown(
    '<p style="color:rgba(141,173,197,0.5);font-size:0.68rem;font-weight:600;'
    'text-transform:uppercase;letter-spacing:0.08em;padding:0 0.75rem;margin:0 0 0.5rem 0">'
    'Voortgang</p>',
    unsafe_allow_html=True,
)
huidig_stap = get_huidge_stap()

# Verwerk optionele stapnavigatie via query-parameter (vrije navigatie)
doel_stap_waarde = st.query_params.get("ga_naar_stap")
if doel_stap_waarde:
    doel_stap = next((s for s in STAPPEN_VOLGORDE if s.value == doel_stap_waarde), None)
    if doel_stap is not None and doel_stap != huidig_stap:
        st.query_params.clear()
        set_huidge_stap(doel_stap, validatie_ok=False)
        st.rerun()
    st.query_params.clear()

for i, stap in enumerate(STAPPEN_VOLGORDE):
    status = stap_status(stap)
    label = STAP_LABELS[stap]
    nr = f"{i + 1:02d}"

    if status == "huidig":
        nummer_kleur = "#88BDF2"
        label_kleur = "#E8F2FB"
        achtergrond = "rgba(136,189,242,0.1)"
        rand_links = "#88BDF2"
        nummer_gewicht = "700"
        label_gewicht = "600"
    elif status == "toekomstig":
        nummer_kleur = "rgba(136,189,242,0.2)"
        label_kleur = "rgba(141,173,197,0.28)"
        achtergrond = "transparent"
        rand_links = "transparent"
        nummer_gewicht = "600"
        label_gewicht = "400"
    elif status == "opnieuw_nodig":
        nummer_kleur = "rgba(136,189,242,0.25)"
        label_kleur = "rgba(141,173,197,0.38)"
        achtergrond = "transparent"
        rand_links = "transparent"
        nummer_gewicht = "600"
        label_gewicht = "400"
    else:  # voltooid
        nummer_kleur = "rgba(136,189,242,0.3)"
        label_kleur = "rgba(141,173,197,0.55)"
        achtergrond = "transparent"
        rand_links = "transparent"
        nummer_gewicht = "600"
        label_gewicht = "400"

    if i == 0:
        stappen_html = []

    stappen_html.append(
        f'<a href="?ga_naar_stap={stap.value}" target="_self" '
        f'style="display:block;text-decoration:none;margin:0;padding:0;">'
        f'<div style="display:flex;align-items:center;justify-content:flex-start;'
        f'gap:8px;padding:4px 12px;margin:0;line-height:1.2;'
        f'border-left:2px solid {rand_links};background:{achtergrond};">'
        f'<span style="display:inline-block;min-width:1.4rem;'
        f'font-variant-numeric:tabular-nums;font-size:0.67rem;'
        f'font-weight:{nummer_gewicht};color:{nummer_kleur};">{nr}</span>'
        f'<span style="display:inline-block;font-size:0.81rem;'
        f'font-weight:{label_gewicht};letter-spacing:0;'
        f'color:{label_kleur};">{label}</span>'
        f'</div>'
        f'</a>'
    )

if STAPPEN_VOLGORDE:
    st.sidebar.markdown(
        '<div style="display:flex;flex-direction:column;gap:0;margin:0;padding:0">'
        + ''.join(stappen_html)
        + '</div>',
        unsafe_allow_html=True,
    )

st.sidebar.markdown("---")

# Sidebar scenario selectie
st.sidebar.markdown("**Scenario**")
scenario_namen = [s.naam for s in scenario_lijst]
actief_index = 0
actief_naam = get_actief_scenario_naam()
if actief_naam in scenario_namen:
    actief_index = scenario_namen.index(actief_naam)

gekozen_actief = st.sidebar.selectbox(
    "Actief scenario",
    options=scenario_namen,
    index=actief_index,
    key="sidebar_actief_scenario",
)
if gekozen_actief != actief_naam:
    set_actief_scenario_naam(gekozen_actief)
st.sidebar.markdown("---")

# --- Render huidge pagina op basis van flow ---
pagina_func = STAP_NAAR_PAGINA.get(huidig_stap)
if pagina_func:
    pagina_func()

# Instellingen altijd beschikbaar buiten flow
st.sidebar.markdown("---")
if st.sidebar.button("Instellingen", key="goto_instellingen_from_sidebar"):
    set_huidge_stap(Stap.INSTELLINGEN, validatie_ok=False)
    st.rerun()

# Als we op instellingen pagina zijn
if huidig_stap == Stap.INSTELLINGEN:
    toon_instellingen_pagina()

st.sidebar.markdown("---")
st.sidebar.caption("Wijzigingen worden automatisch opgeslagen.")
st.sidebar.markdown("---")
st.sidebar.caption(
    "Alle berekeningen zijn indicatief. "
    "Raadpleeg een financieel adviseur voor persoonlijk advies."
)

# Autosave na iedere render
autosla_sessie_op()
