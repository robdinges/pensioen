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
from pensioen.ui.scenario_context import (
    ensure_scenario_context,
    get_actief_scenario_naam,
    set_actief_scenario_naam,
)

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
st.sidebar.title("🏦 Pensioenplanner")

# Render steps bar in sidebar (vertical)
st.sidebar.markdown("**Voortgang**")
huidig_stap = get_huidge_stap()

for i, stap in enumerate(STAPPEN_VOLGORDE):
    status = stap_status(stap)
    label = STAP_LABELS[stap]
    stap_nr = str(i + 1)

    # Maak stappen klikbaar voor teruggaan (maar niet forward)
    if status == "voltooid" or status == "opnieuw_nodig":
        # Klikbare knop voor eerdere stappen
        if st.sidebar.button(
            f"{stap_nr}. {label}" if status == "voltooid" else f"🔴 {stap_nr}. {label}",
            key=f"stap_btn_{stap.value}",
            use_container_width=True,
        ):
            set_huidge_stap(stap, validatie_ok=False)
            st.rerun()
    elif status == "huidig":
        st.sidebar.markdown(f"**🟦 {stap_nr}. {label}**")
    else:  # toekomstig
        st.sidebar.markdown(f"⚪ {stap_nr}. {label}")
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
st.sidebar.markdown("**⚙️ Instellingen**")
if st.sidebar.button("Open Instellingen", key="goto_instellingen_from_sidebar"):
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
