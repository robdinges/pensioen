"""Streamlit-pagina: berekening uitvoeren."""

from __future__ import annotations

from datetime import date

import streamlit as st

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.calculations.scenario_engine import vergelijk_scenarios
from pensioen.ui.flow_context import Stap, set_huidge_stap
from pensioen.ui.scenario_context import get_actief_scenario
from pensioen.tax.belasting_loader import laad_tarieven_bereik, resolve_tariefwaarden_voor_jaar
from pensioen.ui.sessie_persistentie import sla_sessie_op


def toon_bereken_pagina() -> None:
    """Streamlit-pagina voor het uitvoeren van berekeningen."""
    st.header("Berekening uitvoeren")

    # Valideer vereiste invoer
    persoon1 = st.session_state.get("persoon1")
    scenario_lijst = st.session_state.get("scenario_lijst", [])
    actief = get_actief_scenario(scenario_lijst)

    if not persoon1:
        st.warning("⚠️ Vul eerst de persoonsgegevens in (stap: Personen).")
        return
    if not scenario_lijst:
        st.warning("⚠️ Definieer eerst minstens één scenario (stap: Scenario).")
        return
    if actief is None:
        st.warning("⚠️ Kies eerst een actief scenario.")
        return

    persoon2 = st.session_state.get("persoon2")
    records1 = st.session_state.get("records_p1", [])
    records2 = st.session_state.get("records_p2", [])

    # Prognosehorizon
    st.subheader("Prognosehorizon")
    col1, col2 = st.columns(2)
    with col1:
        jaar_van = st.number_input("Prognose van jaar", value=date.today().year, step=1, key="bereken_jaar_van")
    with col2:
        jaar_tot = st.number_input("Prognose tot jaar", value=date.today().year + 35, step=1, key="bereken_jaar_tot")

    if jaar_tot <= jaar_van:
        st.error("'Tot jaar' moet na 'Van jaar' liggen.")
        return

    st.divider()

    # Berekening uitvoeren
    if st.button("▶ Berekening uitvoeren", type="primary", key="bereken_btn", use_container_width=True):
        with st.spinner("Bezig met berekenen..."):
            try:
                configs = laad_tarieven_bereik(int(jaar_van), int(jaar_tot))
                _voer_berekening_uit(
                    persoon1,
                    persoon2,
                    records1,
                    records2,
                    actief,
                    scenario_lijst,
                    int(jaar_van),
                    int(jaar_tot),
                    configs,
                )
                st.success("✅ Berekening voltooid. Ga naar Resultaten om de grafiek en tabel te zien.")
                set_huidge_stap(Stap.RESULTATEN, validatie_ok=True)
                st.rerun()
            except (TypeError, ValueError) as exc:
                st.error(f"Berekeningsfout: {exc}")
                return

    # Info
    st.divider()
    st.info(
        "Klik op '▶ Berekening uitvoeren' om de pensioenprognose voor alle scenario's te berekenen. "
        "Dit kan enkele seconden duren."
    )

    # ─── Vorige/Volgende knoppen ────────────────────────────────────────────
    st.divider()
    col_vorige, col_volgende = st.columns(2)

    with col_vorige:
        if st.button("← Vorige"):
            set_huidge_stap(Stap.COMPONENTEN, validatie_ok=False)
            st.rerun()

    with col_volgende:
        st.info("⏭️ Berekening wordt automatisch uitgevoerd")


def _voer_berekening_uit(
    persoon1,
    persoon2,
    records1,
    records2,
    actief_scenario,
    scenario_lijst,
    jaar_van,
    jaar_tot,
    configs,
):
    """Bereken en sla op in session_state."""
    configs_override = {
        y: (
            resolve_tariefwaarden_voor_jaar(cfg, y, actief_scenario.tarief_periodes)[0],
            melding,
        )
        for y, (cfg, melding) in configs.items()
    }

    cashflow = bereken_huishouden(
        scenario=actief_scenario,
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

    sla_sessie_op()
