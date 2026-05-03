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
from pensioen.ui.sessie_persistentie import laad_sessie, sla_sessie_op

# Herstel sessie bij (her)start (eenmalig per serversessie)
laad_sessie()

# --- Sidebar navigatie ---
PAGINAS = {
    "👤 Personen": "personen",
    "📂 Pensioengegevens": "import",
    "📋 Scenario": "scenario",
    "📊 Resultaten": "resultaten",
    "📥 Rapport": "rapport",
    "⚙️ Instellingen": "instellingen",
}

st.sidebar.title("🏦 Pensioenplanner")
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
elif pagina_sleutel == "rapport":
    toon_rapport_pagina()
elif pagina_sleutel == "instellingen":
    toon_instellingen_pagina()
