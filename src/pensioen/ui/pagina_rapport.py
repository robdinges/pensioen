"""Streamlit-pagina: rapport downloaden."""

from __future__ import annotations

from datetime import date

import streamlit as st

from pensioen.reports.rapport_engine import genereer_rapport
from pensioen.ui.flow_context import Stap, set_huidge_stap
from pensioen.ui.scenario_context import get_actief_scenario_naam


def toon_rapport_pagina() -> None:
    """Streamlit-pagina voor het downloaden van het prognose-rapport."""
    st.header("Rapport downloaden")

    cashflow = st.session_state.get("cashflow_hoofd")
    vergelijking = st.session_state.get("vergelijking")
    actief_scenario_naam = get_actief_scenario_naam() or "Default"
    st.caption(f"Actief scenario: {actief_scenario_naam}")

    if not cashflow:
        st.warning(
            "⚠️ Er zijn nog geen berekeningsresultaten beschikbaar. "
            "Voer eerst een berekening uit (stap: Resultaten)."
        )
        return

    if cashflow.scenario_naam != actief_scenario_naam:
        st.warning(
            "De huidige resultaten zijn berekend voor een ander scenario. "
            "Voer eerst opnieuw een berekening uit in de resultatenpagina."
        )

    st.write("Download het volledige prognose-rapport als Excel-werkmap.")
    st.write("Het rapport bevat de volgende tabbladen:")
    st.markdown(
        """
        - **Jaaroverzicht**: alle jaren met inkomsten, belasting en vermogen
        - **Maanddetail**: uitgesplitst per kalendermaand
        - **Aannames**: gebruikte tarieven en disclaimers
        - **Vergelijking** *(alleen bij meerdere scenario's)*: scenariovergelijking
        """
    )

    bestandsnaam = (
        f"pensioenprognose_{cashflow.scenario_naam.replace(' ', '_')}_{date.today()}.xlsx"
    )

    if st.button("Rapport genereren", type="primary", key="genereer_rapport"):
        with st.spinner("Rapport wordt gegenereerd..."):
            try:
                rapport_bytes = genereer_rapport(cashflow, vergelijking)
                st.session_state["rapport_bytes"] = rapport_bytes
                st.session_state["rapport_bestandsnaam"] = bestandsnaam
                st.success("✅ Rapport gegenereerd")
            except Exception as exc:
                st.error(f"Fout bij genereren rapport: {exc}")

    rapport_bytes = st.session_state.get("rapport_bytes")
    if rapport_bytes:
        st.download_button(
            label="⬇️ Download Excel-rapport",
            data=rapport_bytes,
            file_name=st.session_state.get("rapport_bestandsnaam", bestandsnaam),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel",
        )

    st.divider()
    st.caption(
        "Alle berekeningen zijn indicatief. Raadpleeg een financieel adviseur "
        "voor persoonlijk pensioenadvies."
    )

    # ─── Vorige knop ─────────────────────────────────────────────────────────
    st.divider()
    col_vorige = st.columns(2)[0]
    with col_vorige:
        if st.button("← Vorige"):
            set_huidge_stap(Stap.ACCOUNTANT, validatie_ok=False)
            st.rerun()
