"""Streamlit-pagina: belastingtarieven per jaar inzien en aanpassen."""

from __future__ import annotations

import streamlit as st

from pensioen.tax.belasting_loader import laad_tarieven


def toon_instellingen_pagina() -> None:
    """Streamlit-pagina voor het inzien en overschrijven van belastingtarieven."""
    st.header("⚙️ Instellingen")

    st.subheader("Belastingtarieven per jaar")
    jaar = st.selectbox("Jaar", [2025, 2026], key="tarieven_jaar_select")

    config, melding = laad_tarieven(jaar)
    if melding:
        st.warning(f"⚠️ {melding}")

    st.write(f"**Box 1 – Niet-AOW (schijven voor {jaar})**")
    for i, schijf in enumerate(config.box1_niet_aow, 1):
        tot_str = f"t/m €{schijf.tot:,.0f}" if schijf.tot else "daarboven"
        st.write(f"  Schijf {i}: {float(schijf.tarief) * 100:.2f}% — {tot_str}")

    st.write(f"**Box 1 – AOW-gerechtigd (schijf 1)**")
    schijf1_aow = config.box1_aow[0]
    st.write(f"  Schijf 1: {float(schijf1_aow.tarief) * 100:.2f}%")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("AHK max", f"€ {float(config.ahk.max_bedrag):,.0f}")
    with col2:
        st.metric("Arbeidskorting max", f"€ {float(config.arbeidskorting.max_bedrag):,.0f}")
    with col3:
        st.metric("Ouderenkorting max", f"€ {float(config.ouderenkorting.max_bedrag):,.0f}")

    st.divider()
    st.subheader("Box 3")
    st.info(
        f"**Disclaimer**: {config.box3.disclaimer}\n\n"
        f"Vrijstelling per persoon: €{float(config.box3.vrijstelling_per_persoon):,.0f} | "
        f"Tarief: {float(config.box3.tarief) * 100:.0f}%"
    )

    st.divider()
    st.subheader("AOW-bedragen")
    col4, col5 = st.columns(2)
    with col4:
        st.metric("Alleenstaand (p/m)", f"€ {float(config.aow_bedrag.alleenstaande_per_maand):,.0f}")
    with col5:
        st.metric(
            "Gehuwd/samenwonend (p/m)",
            f"€ {float(config.aow_bedrag.gehuwd_of_samenwonend_per_maand):,.0f}",
        )

    st.caption(
        "ℹ️ Tarieven worden ingelezen uit `config/belasting_YYYY.json`. "
        "Voor onbekende jaren wordt het meest recente beschikbare jaar gebruikt."
    )
