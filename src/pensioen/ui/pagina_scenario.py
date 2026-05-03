"""Streamlit-pagina: scenarioparameters invoeren."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from pensioen.models.scenario import IncidenteelItem, Scenario


def toon_scenario_pagina() -> None:
    """Streamlit-pagina voor het configureren van planningsscenario's."""
    st.header("📋 Scenario configureren")

    scenario_naam = st.text_input(
        "Naam van dit scenario", value="Mijn scenario", key="scenario_naam"
    )

    # --- Stopdatum werk ---
    st.subheader("Stopdatums werk")
    col1, col2 = st.columns(2)
    with col1:
        stopdatum_p1 = st.date_input(
            "Stopdatum werk persoon 1",
            value=date(2025, 12, 31),
            key="stopdatum_p1",
        )
        salaris_p1 = st.number_input(
            "Bruto jaarsalaris persoon 1 (€)",
            min_value=0,
            value=60000,
            step=1000,
            key="salaris_p1",
        )

    heeft_partner = "persoon2" in st.session_state
    stopdatum_p2 = None
    salaris_p2 = 0
    with col2:
        if heeft_partner:
            stopdatum_p2 = st.date_input(
                "Stopdatum werk persoon 2",
                value=date(2030, 12, 31),
                key="stopdatum_p2",
            )
            salaris_p2 = st.number_input(
                "Bruto jaarsalaris persoon 2 (€)",
                min_value=0,
                value=40000,
                step=1000,
                key="salaris_p2",
            )
        else:
            st.caption("Geen partner ingevuld")

    salarisgroei = st.slider(
        "Verwachte jaarlijkse salarisgroei (%)", 0.0, 5.0, 1.5, 0.1, key="salarisgroei"
    )

    st.divider()
    st.subheader("Spaargeld & rendement")
    col3, col4 = st.columns(2)
    with col3:
        spaargeld = st.number_input(
            "Spaargeld/beleggingen nu (€)", min_value=0, value=50000, step=5000, key="spaargeld"
        )
        jaarlijkse_inleg = st.number_input(
            "Jaarlijkse extra inleg (€)", min_value=0, value=0, step=500, key="inleg"
        )
    with col4:
        rendement = st.slider("Verwacht rendement (%)", 0.0, 10.0, 3.0, 0.1, key="rendement")
        box3_meenemen = st.checkbox(
            "Box 3 heffing meenemen (indicatief)", value=True, key="box3"
        )

    st.divider()
    st.subheader("Incidentele cashflows")
    st.caption(
        "Voeg eenmalige ontvangsten (+) of uitgaven (-) toe, "
        "bijv. erfenis, verbouwing, schenking."
    )

    if "incidenteel_tabel" not in st.session_state:
        st.session_state["incidenteel_tabel"] = pd.DataFrame(
            columns=["datum", "bedrag", "omschrijving"]
        )

    incidenteel_df = st.data_editor(
        st.session_state["incidenteel_tabel"],
        num_rows="dynamic",
        column_config={
            "datum": st.column_config.DateColumn("Datum", required=True),
            "bedrag": st.column_config.NumberColumn(
                "Bedrag (€, negatief = uitgave)", required=True
            ),
            "omschrijving": st.column_config.TextColumn("Omschrijving"),
        },
        key="incidenteel_editor",
        use_container_width=True,
    )
    st.session_state["incidenteel_tabel"] = incidenteel_df

    if st.button("Scenario opslaan", key="opslaan_scenario"):
        try:
            incidentele_items = [
                IncidenteelItem(
                    datum=rij["datum"],
                    bedrag=Decimal(str(rij["bedrag"])),
                    omschrijving=str(rij.get("omschrijving", "")),
                )
                for _, rij in incidenteel_df.iterrows()
                if pd.notna(rij.get("datum")) and pd.notna(rij.get("bedrag"))
            ]

            scenario = Scenario(
                naam=scenario_naam,
                persoon1_stopdatum_werk=stopdatum_p1,
                persoon2_stopdatum_werk=stopdatum_p2,
                persoon1_bruto_jaarsalaris=Decimal(str(salaris_p1)),
                persoon2_bruto_jaarsalaris=Decimal(str(salaris_p2)) if salaris_p2 else None,
                salarisgroei_pct=Decimal(str(salarisgroei)),
                spaargeld_start=Decimal(str(spaargeld)),
                jaarlijkse_inleg=Decimal(str(jaarlijkse_inleg)),
                rendement_pct=Decimal(str(rendement)),
                box3_meenemen=box3_meenemen,
                incidentele_items=incidentele_items,
            )
            if "scenario_lijst" not in st.session_state:
                st.session_state["scenario_lijst"] = []

            # Vervang als scenario met zelfde naam bestaat
            bestaand = [
                s for s in st.session_state["scenario_lijst"]
                if s.naam != scenario.naam
            ]
            bestaand.append(scenario)
            st.session_state["scenario_lijst"] = bestaand
            st.success(f"✅ Scenario '{scenario.naam}' opgeslagen")
        except Exception as exc:
            st.error(f"Fout: {exc}")

    # Overzicht opgeslagen scenario's
    scenario_lijst = st.session_state.get("scenario_lijst", [])
    if scenario_lijst:
        st.divider()
        st.subheader("Opgeslagen scenario's")
        for s in scenario_lijst:
            st.write(
                f"- **{s.naam}**: stopdatum {s.persoon1_stopdatum_werk}, "
                f"spaargeld €{s.spaargeld_start:,.0f}, "
                f"rendement {s.rendement_pct}%"
            )
