"""Streamlit-pagina: berekeningsresultaten en grafieken."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pensioen.models.cashflow import HuishoudCashflow
from pensioen.ui.flow_context import Stap, set_huidge_stap
from pensioen.ui.scenario_context import get_actief_scenario
from pensioen.validators.grafiek_validator import valideer_cashflow_consistency


def toon_resultaten_pagina() -> None:
    """Streamlit-pagina voor het berekenen en weergeven van de prognose."""
    st.header("Resultaten")

    actieve_scenario_raw = get_actief_scenario(st.session_state.get("scenario_lijst", []))
    if actieve_scenario_raw is not None:
        actieve_scenario = actieve_scenario_raw
        label = actieve_scenario_raw.naam
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

    # Resultaten tonen (indien beschikbaar)
    cashflow_hoofd = st.session_state.get("cashflow_hoofd")
    vergelijking = st.session_state.get("vergelijking")

    if not cashflow_hoofd:
        st.info(
            "Noch geen berekeningsresultaten beschikbaar. "
            "Voer eerst een berekening uit via de vorige stap (Bereken)."
        )
        return

    if cashflow_hoofd:
        _toon_tarieven_banner(cashflow_hoofd)
        
        # Valideer consistentie tussen grafieken en accountantsoverzicht
        validatie = valideer_cashflow_consistency(cashflow_hoofd)
        if not validatie.is_geldig:
            st.error("**Data-inconsistentie gedetecteerd**")
            st.error("\n\n".join(validatie.fouten))
            st.warning(
                "⚠️ Er zijn verschillen tussen de grafieken en het accountantsoverzicht. "
                "Dit kan duiden op een bug in de berekeningen. Neem contact op met de ontwikkelaar."
            )
        elif validatie.waarschuwingen:
            with st.expander("⚠️ Kleine afrondingsverschillen gedetecteerd", expanded=False):
                st.info("\n\n".join(validatie.waarschuwingen))
        
        _toon_inkomensgrafiek(cashflow_hoofd)
        _toon_uitgavengrafiek(cashflow_hoofd)
        _toon_vermogensgrafiek(cashflow_hoofd)
        _toon_jaaroverzicht_tabel(cashflow_hoofd, actieve_scenario.inflatie_pct)
        if vergelijking and len(vergelijking.scenario_resultaten) > 1:
            _toon_vergelijking(vergelijking)

    # ─── Vorige/Volgende knoppen ─────────────────────────────────────────────
    st.divider()
    col_vorige, col_volgende = st.columns(2)
    
    with col_vorige:
        if st.button("← Vorige"):
            set_huidge_stap(Stap.COMPONENTEN, validatie_ok=False)
            st.rerun()
    
    with col_volgende:
        if st.button("Volgende →", use_container_width=True):
            set_huidge_stap(Stap.ACCOUNTANT, validatie_ok=True)
            st.rerun()




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
        # Gebruik centrale inkomen_bronnen property voor consistentie
        bronnen = jr.inkomen_bronnen
        data.append({
            "Jaar": jr.jaar,
            **{k: float(v) for k, v in bronnen.items()},
            "Netto": float(jr.netto),
        })
    df = pd.DataFrame(data)

    fig = go.Figure()
    # Gebruik keys uit eerste jaar om consistentie te garanderen
    if cashflow.jaren:
        bron_namen = list(cashflow.jaren[0].inkomen_bronnen.keys())
        for bron in bron_namen:
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


def _toon_uitgavengrafiek(cashflow: HuishoudCashflow) -> None:
    """Waterfall chart die laat zien hoe bruto inkomen wordt omgezet naar netto."""
    st.subheader("Van bruto naar netto per jaar")
    
    if not cashflow.jaren:
        return
    
    # Jaar-selectie slider
    min_jaar = cashflow.jaren[0].jaar
    max_jaar = cashflow.jaren[-1].jaar
    
    # Gebruik een aparte tracking key voor persistentie over scenario-wissels heen
    tracking_key = "waterfall_jaar_tracking"
    slider_key = "waterfall_jaar_selectie"
    
    # Bepaal de slider waarde:
    # - Als slider_key bestaat EN binnen bereik: gebruik die (gebruiker heeft hem verplaatst)
    # - Anders: gebruik tracking_key (persistentie over scenario-wissels)
    # - Als beide niet bestaan of buiten bereik: gebruik min_jaar
    
    slider_waarde = None
    
    # Eerst: check of slider al een waarde heeft (gebruikersinteractie)
    if slider_key in st.session_state:
        slider_bestaand = st.session_state[slider_key]
        if min_jaar <= slider_bestaand <= max_jaar:
            slider_waarde = slider_bestaand
    
    # Tweede: check tracking key (voor scenario-wissels)
    if slider_waarde is None and tracking_key in st.session_state:
        tracking_bestaand = st.session_state[tracking_key]
        if min_jaar <= tracking_bestaand <= max_jaar:
            slider_waarde = tracking_bestaand
    
    # Fallback: eerste jaar
    if slider_waarde is None:
        slider_waarde = min_jaar
    
    # Render slider
    geselecteerd_jaar = st.slider(
        "Selecteer jaar voor gedetailleerde breakdown:",
        min_value=min_jaar,
        max_value=max_jaar,
        value=slider_waarde,
        step=1,
        key=slider_key
    )
    
    # Update tracking key met huidige slider waarde (voor volgende scenario-wissel)
    st.session_state[tracking_key] = geselecteerd_jaar
    
    # Vind het geselecteerde jaar
    jr = next((j for j in cashflow.jaren if j.jaar == geselecteerd_jaar), cashflow.jaren[0])
    
    # Bereken beginvermogen van het geselecteerde jaar
    idx = cashflow.jaren.index(jr)
    if idx > 0:
        verm_begin = cashflow.jaren[idx - 1].vermogen_einde_jaar
    else:
        # Eerste jaar: gebruik scenario startwaarde
        # Haal scenario op uit session state
        scenario_lijst = st.session_state.get("scenario_lijst", [])
        actief = get_actief_scenario(scenario_lijst)
        verm_begin = actief.totaal_vermogen_start() if actief else Decimal("0")
    
    st.caption(
        f"**Jaar {jr.jaar}** — Vermogen begin jaar: €{float(verm_begin):,.0f} | "
        f"Box 3 heffing: €{float(jr.box3_heffing):,.2f}"
    )
    
    # Bereken de componenten
    # BELANGRIJK: gebruik inkomen_bruto (excl. rendement) en rendement_bruto properties
    # Deze zijn centraal gedefinieerd in JaarResultaat voor consistentie
    bruto_inkomen = float(jr.inkomen_bruto)
    rendement = float(jr.rendement_bruto)
    box1_bel = -float(jr.box1_belasting)
    box3_bel = -float(jr.box3_heffing)
    heffingskortingen = float(jr.totaal_heffingskorting)
    inhoudingen = -float(jr.inhoudingen)
    huish_uitgaven = -float(jr.huishoudelijke_uitgaven)
    eenmalige_uit = -float(jr.eenmalige_uitgaven)
    eenmalige_ont = float(jr.eenmalige_ontvangsten)
    netto = float(jr.netto)
    
    # Waterfall chart data
    measure_types = ["relative"] * 9 + ["total"]
    x_labels = [
        "Bruto inkomen",
        "Rendement",
        "Box 1 belasting",
        "Box 3 vermogen",
        "Heffingskortingen",
        "Inhoudingen",
        "Huish. uitgaven",
        "Eenmalige uitg.",
        "Eenmalige ontv.",
        "Netto overschot"
    ]
    y_values = [
        bruto_inkomen,
        rendement,
        box1_bel,
        box3_bel,
        heffingskortingen,
        inhoudingen,
        huish_uitgaven,
        eenmalige_uit,
        eenmalige_ont,
        netto
    ]
    
    fig = go.Figure(go.Waterfall(
        name="Cashflow",
        orientation="v",
        measure=measure_types,
        x=x_labels,
        y=y_values,
        connector={"line": {"color": "#64748b", "width": 1, "dash": "dot"}},
        increasing={"marker": {"color": "#10b981"}},
        decreasing={"marker": {"color": "#dc2626"}},
        totals={"marker": {"color": "#047857"}},
        textposition="outside",
        text=[f"€{v:,.0f}" if v != 0 else "" for v in y_values],
    ))
    
    fig.update_layout(
        title=f"Cashflow-breakdown voor jaar {jr.jaar}",
        xaxis_title="",
        yaxis_title="Bedrag (€)",
        height=450,
        showlegend=False,
        yaxis={"tickformat": ",.0f"},
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Toon extra context over het geselecteerde jaar
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Effectief tarief", f"{float(jr.effectief_tarief):.1f}%")
    with col2:
        st.metric("Netto per maand", f"€{float(jr.netto_per_maand):,.0f}")
    with col3:
        vermogen_label = "🔴 Tekort" if jr.is_tekortjaar else "Vermogen einde jaar"
        st.metric(vermogen_label, f"€{float(jr.vermogen_einde_jaar):,.0f}")


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


def _toon_jaaroverzicht_tabel(cashflow: HuishoudCashflow, inflatie_pct: Decimal = Decimal("2")) -> None:
    """Tabel met jaaroverzicht."""
    st.subheader("Jaaroverzicht")
    startjaar = cashflow.jaren[0].jaar if cashflow.jaren else 0
    data = [
        {
            "Jaar": jr.jaar,
            "Bruto (€)": float(jr.totaal_bruto),
            "Belasting (€)": float(jr.totaal_belasting),
            "Heffingskorting (€)": float(jr.totaal_heffingskorting),
            "Netto (€)": float(jr.netto),
            "Netto p/m (€)": float(jr.netto_per_maand),
            "Reëel netto p/m (€)": float(
                jr.netto_per_maand / (Decimal("1") + inflatie_pct / Decimal("100")) ** (jr.jaar - startjaar)
            ),
            "Eff. tarief (%)": float(jr.effectief_tarief),
            "Vermogen (€)": float(jr.vermogen_einde_jaar),
            "Tekortjaar": "⚠️" if jr.is_tekortjaar else "",
        }
        for jr in cashflow.jaren
    ]
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(
        f"Reëel netto p/m = koopkracht in euro's van {startjaar} bij {float(inflatie_pct):.1f}% jaarlijkse inflatie."
    )


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
