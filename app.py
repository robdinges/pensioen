"""Streamlit-applicatie: pensioenprognose huishouden."""

from __future__ import annotations

from datetime import date


import streamlit as st

st.set_page_config(
    page_title="Pensioenplanner",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.calculations.scenario_engine import vergelijk_scenarios
from pensioen.tax.belasting_loader import laad_tarieven_bereik, resolve_tariefwaarden_voor_jaar
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
    Stap.COMPONENTEN: toon_componenten_pagina,
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
    # Bij scenario-wissel: herbereken als er al resultaten zijn
    if st.session_state.get("cashflow_hoofd") is not None:
        persoon1 = st.session_state.get("persoon1")
        persoon2 = st.session_state.get("persoon2")
        if persoon1 and scenario_lijst:
            from pensioen.ui.scenario_context import get_actief_scenario
            actief = get_actief_scenario(scenario_lijst)
            if actief is not None:
                try:
                    jaar_van = st.session_state.get("jaar_van", date.today().year)
                    jaar_tot = st.session_state.get("jaar_tot", date.today().year + 30)
                    
                    configs = laad_tarieven_bereik(int(jaar_van), int(jaar_tot))
                    configs_override = {
                        y: (
                            resolve_tariefwaarden_voor_jaar(cfg, y, actief.tarief_periodes)[0],
                            melding,
                        )
                        for y, (cfg, melding) in configs.items()
                    }
                    
                    cashflow = bereken_huishouden(
                        scenario=actief,
                        persoon1=persoon1,
                        persoon2=persoon2,
                        records1=[],
                        records2=[],
                        jaar_van=jaar_van,
                        jaar_tot=jaar_tot,
                        belasting_configs=configs_override,
                    )
                    st.session_state["cashflow_hoofd"] = cashflow
                    
                    if len(scenario_lijst) > 1:
                        vergelijking = vergelijk_scenarios(
                            scenarios=scenario_lijst,
                            persoon1=persoon1,
                            persoon2=persoon2,
                            records1=[],
                            records2=[],
                            jaar_van=jaar_van,
                            jaar_tot=jaar_tot,
                        )
                        st.session_state["vergelijking"] = vergelijking
                    else:
                        st.session_state.pop("vergelijking", None)
                except Exception:
                    # Stille fallback: clear cashflow bij fout
                    st.session_state.pop("cashflow_hoofd", None)
                    st.session_state.pop("vergelijking", None)
    st.rerun()
st.sidebar.markdown("---")

# --- Render huidge pagina op basis van flow ---
pagina_func = STAP_NAAR_PAGINA.get(huidig_stap)
if pagina_func:
    pagina_func()

# Bereken knop in sidebar
st.sidebar.markdown("---")

# Berekeningsperiode defaults
if "jaar_van" not in st.session_state:
    st.session_state["jaar_van"] = date.today().year
if "jaar_tot" not in st.session_state:
    st.session_state["jaar_tot"] = date.today().year + 30

# Bereken knop
if st.sidebar.button("▶ Berekenen", key="sidebar_bereken_btn", type="primary", use_container_width=True):
    persoon1 = st.session_state.get("persoon1")
    persoon2 = st.session_state.get("persoon2")
    
    if not persoon1:
        st.sidebar.error("⚠️ Vul eerst de persoonsgegevens in")
    elif not scenario_lijst:
        st.sidebar.error("⚠️ Definieer eerst een scenario")
    else:
        # Haal actief scenario op
        from pensioen.ui.scenario_context import get_actief_scenario
        actief = get_actief_scenario(scenario_lijst)
        
        if actief is None:
            st.sidebar.error("⚠️ Kies eerst een actief scenario")
        else:
            # Pensioenen zijn nu componenten
            records1 = []
            records2 = []
            
            try:
                jaar_van = st.session_state["jaar_van"]
                jaar_tot = st.session_state["jaar_tot"]
                
                with st.sidebar:
                    with st.spinner("Bezig met berekenen..."):
                        configs = laad_tarieven_bereik(int(jaar_van), int(jaar_tot))
                        
                        # Bereken met tariefoverrides
                        configs_override = {
                            y: (
                                resolve_tariefwaarden_voor_jaar(cfg, y, actief.tarief_periodes)[0],
                                melding,
                            )
                            for y, (cfg, melding) in configs.items()
                        }
                        
                        cashflow = bereken_huishouden(
                            scenario=actief,
                            persoon1=persoon1,
                            persoon2=persoon2,
                            records1=records1,
                            records2=records2,
                            jaar_van=jaar_van,
                            jaar_tot=jaar_tot,
                            belasting_configs=configs_override,
                        )
                        st.session_state["cashflow_hoofd"] = cashflow
                        
                        if len(scenario_lijst) > 1:
                            vergelijking = vergelijk_scenarios(
                                scenarios=scenario_lijst,
                                persoon1=persoon1,
                                persoon2=persoon2,
                                records1=records1,
                                records2=records2,
                                jaar_van=jaar_van,
                                jaar_tot=jaar_tot,
                            )
                            st.session_state["vergelijking"] = vergelijking
                        else:
                            st.session_state.pop("vergelijking", None)
                        
                        from pensioen.ui.sessie_persistentie import sla_sessie_op
                        sla_sessie_op()
                
                st.sidebar.success("✅ Berekening voltooid!")
                set_huidge_stap(Stap.RESULTATEN, validatie_ok=True)
                st.rerun()
            except (TypeError, ValueError) as exc:
                st.sidebar.error(f"Berekeningsfout: {exc}")

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
