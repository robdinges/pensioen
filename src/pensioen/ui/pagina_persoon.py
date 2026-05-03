"""Streamlit-pagina: persoonsgegevens invoeren."""

from __future__ import annotations

from datetime import date

import streamlit as st

from pensioen.models.persoon import Persoon
from pensioen.tax.aow_engine import bereken_aow_datum
from pensioen.ui.sessie_persistentie import sla_sessie_op


def toon_persoon_pagina() -> None:
    """Streamlit-pagina voor het invoeren van persoonsgegevens."""
    st.header("👤 Persoonsgegevens")

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
    except Exception:
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
        except Exception:
            pass

    if st.button("Opslaan", key="opslaan_personen"):
        try:
            p1 = Persoon(
                naam=naam1,
                geboortedatum=geboortedatum1,
                heeft_partner=heeft_partner,
            )
            st.session_state["persoon1"] = p1

            if heeft_partner and geboortedatum2:
                p2 = Persoon(
                    naam=naam2,
                    geboortedatum=geboortedatum2,
                    heeft_partner=True,
                    partner_id=naam1,
                )
                st.session_state["persoon2"] = p2
            else:
                st.session_state.pop("persoon2", None)

            st.success("✅ Persoonsgegevens opgeslagen")
            sla_sessie_op()
        except Exception as exc:
            st.error(f"Fout: {exc}")
