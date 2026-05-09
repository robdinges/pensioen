"""Streamlit-pagina: berekeningsresultaten en grafieken."""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.calculations.scenario_engine import vergelijk_scenarios
from pensioen.models.cashflow import HuishoudCashflow
from pensioen.ui.scenario_context import get_actief_scenario
from pensioen.tax.belasting_loader import laad_tarieven_bereik


def toon_resultaten_pagina() -> None:
    """Streamlit-pagina voor het berekenen en weergeven van de prognose."""
    st.header("📊 Resultaten")

    actieve_scenario_raw = get_actief_scenario(st.session_state.get("scenario_lijst", []))
    if actieve_scenario_raw is not None:
        actieve_scenario = actieve_scenario_raw.effectief_scenario(
            st.session_state.get("scenario_lijst", [])
        )
        label = actieve_scenario_raw.naam
        if actieve_scenario_raw.parent_naam:
            label += f" (erft van {actieve_scenario_raw.parent_naam})"
        st.caption(f"Actief scenario: {label}")
    else:
        actieve_scenario = None

    # Valideer dat vereiste invoer aanwezig is
    persoon1 = st.session_state.get("persoon1")
    scenario_lijst = st.session_state.get("scenario_lijst", [])

    if not persoon1:
        st.warning("⚠️ Vul eerst de persoonsgegevens in (stap: Personen).")
        return
    if not scenario_lijst:
        st.warning("⚠️ Definieer eerst minstens één scenario (stap: Scenario).")
        return
    if actieve_scenario is None:
        st.warning("⚠️ Kies eerst een actief scenario in de scenario-pagina.")
        return

    persoon2 = st.session_state.get("persoon2")
    records1 = st.session_state.get("records_p1", [])
    records2 = st.session_state.get("records_p2", [])

    # Prognosehorizon
    col1, col2 = st.columns(2)
    with col1:
        jaar_van = st.number_input("Prognose van jaar", value=date.today().year, step=1, key="jaar_van")
    with col2:
        jaar_tot = st.number_input("Prognose tot jaar", value=date.today().year + 35, step=1, key="jaar_tot")

    if jaar_tot <= jaar_van:
        st.error("'Tot jaar' moet na 'Van jaar' liggen.")
        return

    if st.button("▶ Berekening uitvoeren", type="primary", key="bereken"):
        with st.spinner("Bezig met berekenen..."):
            try:
                configs = laad_tarieven_bereik(int(jaar_van), int(jaar_tot))
                _voer_berekening_uit(
                    persoon1,
                    persoon2,
                    records1,
                    records2,
                    actieve_scenario,
                    scenario_lijst,
                    int(jaar_van),
                    int(jaar_tot),
                    configs,
                )
            except (TypeError, ValueError) as exc:
                st.error(f"Berekeningsfout: {exc}")
                return

    # Resultaten tonen (indien beschikbaar)
    cashflow_hoofd = st.session_state.get("cashflow_hoofd")
    vergelijking = st.session_state.get("vergelijking")

    if cashflow_hoofd:
        _toon_tarieven_banner(cashflow_hoofd)
        _toon_inkomensgrafiek(cashflow_hoofd)
        _toon_vermogensgrafiek(cashflow_hoofd)
        _toon_jaaroverzicht_tabel(cashflow_hoofd)
        if vergelijking and len(vergelijking.scenario_resultaten) > 1:
            _toon_vergelijking(vergelijking)


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
    cashflow = bereken_huishouden(
        scenario=actief_scenario,
        persoon1=persoon1,
        persoon2=persoon2,
        records1=records1,
        records2=records2,
        jaar_van=jaar_van,
        jaar_tot=jaar_tot,
        belasting_configs=configs,
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

    st.success("✅ Berekening klaar")


def _toon_tarieven_banner(cashflow: HuishoudCashflow) -> None:
    """Toon een waarschuwingsbanner als er tariefassumpties zijn gemaakt."""
    aannames = [a for a in cashflow.aannames if a]
    if aannames:
        st.warning(
            "**Tarievenassumptie**: Er zijn geen tarieven gevonden, dus we gaan uit "
            "van default-waarden."
        )

        # Detailmeldingen blijven beschikbaar op verzoek van de gebruiker.
        detailregels = sorted(
            {
                jr.tarieven_aanname
                for jr in cashflow.jaren
                if jr.tarieven_aanname
            }
        )
        if detailregels:
            with st.expander("Bekijk detail-log belastingaannames"):
                for regel in detailregels:
                    st.write(f"- {regel}")


def _toon_inkomensgrafiek(cashflow: HuishoudCashflow) -> None:
    """Gestapeld staafdiagram van inkomstenbronnen per jaar."""
    st.subheader("Bruto inkomen per jaar")
    data = []
    for jr in cashflow.jaren:
        data.append({
            "Jaar": jr.jaar,
            "Arbeidsinkomen": float(jr.arbeid_bruto),
            "AOW": float(jr.aow_bruto),
            "Pensioen": float(jr.pensioen_bruto),
            "Netto": float(jr.netto),
        })
    df = pd.DataFrame(data)

    fig = go.Figure()
    for bron in ["Arbeidsinkomen", "AOW", "Pensioen"]:
        fig.add_trace(go.Bar(name=bron, x=df["Jaar"], y=df[bron]))
    fig.add_trace(
        go.Scatter(
            name="Netto",
            x=df["Jaar"],
            y=df["Netto"],
            mode="lines+markers",
            line=dict(color="darkgreen", width=2),
            yaxis="y",
        )
    )
    fig.update_layout(
        barmode="stack",
        xaxis_title="Jaar",
        yaxis_title="Bedrag (€)",
        legend_title="Inkomstenbron",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


def _toon_vermogensgrafiek(cashflow: HuishoudCashflow) -> None:
    """Lijndiagram van het vermogen per jaar."""
    st.subheader("Vermogensontwikkeling")
    data = [
        {"Jaar": jr.jaar, "Vermogen (€)": float(jr.vermogen_einde_jaar)}
        for jr in cashflow.jaren
    ]
    df = pd.DataFrame(data)
    fig = px.area(df, x="Jaar", y="Vermogen (€)", title="Vermogen einde jaar")
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


def _toon_jaaroverzicht_tabel(cashflow: HuishoudCashflow) -> None:
    """Tabel met jaaroverzicht."""
    st.subheader("Jaaroverzicht")
    data = [
        {
            "Jaar": jr.jaar,
            "Bruto (€)": float(jr.totaal_bruto),
            "Belasting (€)": float(jr.totaal_belasting),
            "Heffingskorting (€)": float(jr.totaal_heffingskorting),
            "Netto (€)": float(jr.netto),
            "Netto p/m (€)": float(jr.netto_per_maand),
            "Eff. tarief (%)": float(jr.effectief_tarief),
            "Vermogen (€)": float(jr.vermogen_einde_jaar),
            "Tekortjaar": "⚠️" if jr.is_tekortjaar else "",
        }
        for jr in cashflow.jaren
    ]
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _toon_vergelijking(vergelijking) -> None:
    """Vergelijkingstabel voor meerdere scenario's."""
    st.subheader("Scenariovergelijking")
    data = [
        {
            "Scenario": sr.scenario_naam,
            "Stopdatum": sr.stopdatum_werk,
            "Mediaan netto p/m (€)": float(sr.netto_per_maand_mediaan),
            "Laagste jaar netto (€)": float(sr.netto_laagste_jaar),
            "Vermogen op 70 (€)": float(sr.vermogen_op_70),
            "Vermogen op 80 (€)": float(sr.vermogen_op_80),
            "Eff. tarief (%)": float(sr.gemiddelde_belastingdruk),
            "Tekortjaren": sr.aantal_tekortjaren,
        }
        for sr in vergelijking.scenario_resultaten
    ]
    df = pd.DataFrame(data)
    beste = vergelijking.beste_scenario_netto
    if beste:
        st.success(
            f"✅ Beste scenario op basis van mediaan netto: **{beste.scenario_naam}**"
        )
    st.dataframe(df, use_container_width=True, hide_index=True)
