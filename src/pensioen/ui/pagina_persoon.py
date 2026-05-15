"""Streamlit-pagina: persoonsgegevens invoeren."""

from __future__ import annotations

from datetime import date

import streamlit as st

from pensioen.models.persoon import Persoon
from pensioen.tax.aow_engine import bereken_aow_datum
from pensioen.ui.flow_context import Stap, set_huidge_stap
from pensioen.ui.sessie_persistentie import sla_sessie_op


def toon_persoon_pagina() -> None:
    """Streamlit-pagina voor het invoeren van persoonsgegevens."""
    st.header("Persoonsgegevens")

    st.subheader("Persoon 1")
    naam1 = st.text_input("Naam persoon 1", value="Persoon 1", key="naam_p1")
    geboortedatum1 = st.date_input(
        "Geboortedatum persoon 1",
        value=date(1963, 1, 1),
        min_value=date(1930, 1, 1),
        max_value=date(2010, 12, 31),
        key="geboortedatum_p1",
    )

    try:
        aow1 = bereken_aow_datum(geboortedatum1)
        st.info(f"🕐 Geschatte AOW-datum persoon 1: **{aow1.strftime('%d %B %Y')}**")
    except ValueError:
        pass

    heeft_partner = st.checkbox("Heeft een partner", value=True, key="heeft_partner")

    naam2 = ""
    geboortedatum2 = None
    if heeft_partner:
        st.divider()
        st.subheader("Persoon 2 (partner)")
        naam2 = st.text_input("Naam persoon 2", value="Partner", key="naam_p2")
        geboortedatum2 = st.date_input(
            "Geboortedatum persoon 2",
            value=date(1965, 1, 1),
            min_value=date(1930, 1, 1),
            max_value=date(2010, 12, 31),
            key="geboortedatum_p2",
        )
        try:
            aow2 = bereken_aow_datum(geboortedatum2)
            st.info(f"🕐 Geschatte AOW-datum persoon 2: **{aow2.strftime('%d %B %Y')}**")
        except ValueError:
            pass

    try:
        p1 = Persoon(
            naam=naam1,
            geboortedatum=geboortedatum1,
            heeft_partner=heeft_partner,
        )
        gewijzigd = st.session_state.get("persoon1") != p1
        st.session_state["persoon1"] = p1

        if heeft_partner and geboortedatum2:
            p2 = Persoon(
                naam=naam2,
                geboortedatum=geboortedatum2,
                heeft_partner=True,
                partner_id=naam1,
            )
            if st.session_state.get("persoon2") != p2:
                gewijzigd = True
            st.session_state["persoon2"] = p2
        else:
            if "persoon2" in st.session_state:
                gewijzigd = True
            st.session_state.pop("persoon2", None)

        if gewijzigd:
            st.session_state.pop("cashflow_hoofd", None)
            st.session_state.pop("vergelijking", None)
            st.session_state.pop("rapport_bytes", None)
            sla_sessie_op()
            st.caption("Wijzigingen automatisch opgeslagen.")
    except (TypeError, ValueError) as exc:
        st.error(f"Fout: {exc}")

    # ─── Volgende knop ──────────────────────────────────────────────────────
    st.divider()
    col_volgende = st.columns(2)[1]
    with col_volgende:
        if st.button("Volgende →", use_container_width=True):
            set_huidge_stap(Stap.PENSIOENGEGEVENS, validatie_ok=True)
            st.rerun()
