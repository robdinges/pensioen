"""Streamlit-pagina: rapport downloaden."""

from __future__ import annotations

from datetime import date

import streamlit as st

from pensioen.reports.rapport_engine import genereer_rapport


def toon_rapport_pagina() -> None:
    """Streamlit-pagina voor het downloaden van het prognose-rapport."""
    st.header("📥 Rapport downloaden")

    cashflow = st.session_state.get("cashflow_hoofd")
    vergelijking = st.session_state.get("vergelijking")

    if not cashflow:
        st.warning(
            "⚠️ Er zijn nog geen berekeningsresultaten beschikbaar. "
            "Voer eerst een berekening uit (stap: Resultaten)."
        )
        return

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

    if st.button("📊 Rapport genereren", type="primary", key="genereer_rapport"):
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
