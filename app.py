"""Streamlit-applicatie: pensioenprognose huishouden."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Pensioenplanner",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

from pensioen.ui.pagina_import import toon_import_pagina
from pensioen.ui.pagina_instellingen import toon_instellingen_pagina
from pensioen.ui.pagina_persoon import toon_persoon_pagina
from pensioen.ui.pagina_rapport import toon_rapport_pagina
from pensioen.ui.pagina_resultaten import toon_resultaten_pagina
from pensioen.ui.pagina_scenario import toon_scenario_pagina
from pensioen.ui.pagina_accountant import toon_accountant_pagina
from pensioen.ui.sessie_persistentie import autosla_sessie_op, laad_sessie, sla_sessie_op
from pensioen.ui.scenario_context import get_actief_scenario_naam

# Herstel sessie bij (her)start (eenmalig per serversessie)
laad_sessie()

# --- Sidebar navigatie ---
PAGINAS = {
    "👤 Personen": "personen",
    "📂 Pensioengegevens": "import",
    "📋 Scenario": "scenario",
    "📊 Resultaten": "resultaten",
    "� Accountantsoverzicht": "accountant",
    "�📥 Rapport": "rapport",
    "⚙️ Instellingen": "instellingen",
}

st.sidebar.title("🏦 Pensioenplanner")
actieve_scenario_naam = get_actief_scenario_naam()
if actieve_scenario_naam is None:
    st.sidebar.warning("Geen actief scenario")
else:
    st.sidebar.success(f"Actief: {actieve_scenario_naam}")
st.sidebar.markdown("---")

geselecteerde_pagina = st.sidebar.radio(
    "Navigatie",
    list(PAGINAS.keys()),
    key="navigatie",
)

st.sidebar.markdown("---")
if st.sidebar.button("💾 Sessie opslaan", use_container_width=True):
    sla_sessie_op()
    st.sidebar.success("✅ Sessie opgeslagen")
st.sidebar.markdown("---")
st.sidebar.caption(
    "Alle berekeningen zijn indicatief. "
    "Raadpleeg een financieel adviseur voor persoonlijk advies."
)

# --- Pagina renderen ---
pagina_sleutel = PAGINAS[geselecteerde_pagina]

if pagina_sleutel == "personen":
    toon_persoon_pagina()
elif pagina_sleutel == "import":
    toon_import_pagina()
elif pagina_sleutel == "scenario":
    toon_scenario_pagina()
elif pagina_sleutel == "resultaten":
    toon_resultaten_pagina()
elif pagina_sleutel == "accountant":
    toon_accountant_pagina()
elif pagina_sleutel == "rapport":
    toon_rapport_pagina()
elif pagina_sleutel == "instellingen":
    toon_instellingen_pagina()

# Autosave na iedere render — stil, atomisch, alleen bij wijzigingen
autosla_sessie_op()
