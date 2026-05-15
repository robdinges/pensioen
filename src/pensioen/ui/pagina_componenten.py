"""Streamlit-pagina: financiële componenten per actief scenario."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from pensioen.models.component import COMPONENT_SJABLONEN
from pensioen.models.scenario import IncidenteelItem
from pensioen.ui.flow_context import Stap, set_huidge_stap
from pensioen.ui.scenario_context import get_actief_scenario
from pensioen.ui.sessie_persistentie import sla_sessie_op
from pensioen.ui.component_helpers import (
    BEDRAG_TYPE_LABELS,
    BEDRAG_TYPE_OPTIES,
    BELEGGINGS_TYPE_LABELS,
    BELEGGINGS_TYPE_OPTIES,
    CATEGORIE_LABELS,
    CATEGORIE_OPTIES,
    FREQUENTIE_LABELS,
    FREQUENTIE_OPTIES,
    componenten_naar_df,
    df_naar_componenten,
    toon_pensioen_editor,
)


def toon_componenten_pagina() -> None:
    """Bewerk financiële componenten voor het actieve scenario."""
    st.header("Financiële componenten")

    scenario_lijst = st.session_state.get("scenario_lijst", [])
    actief = get_actief_scenario(scenario_lijst)
    if actief is None:
        st.warning("⚠️ Kies eerst een actief scenario.")
        return

    scenario = actief
    st.caption(f"Actief scenario: {scenario.naam}")

    heeft_partner = "persoon2" in st.session_state
    persoon_opties = ["P1", "P2", "Huishouden"] if heeft_partner else ["P1", "Huishouden"]

    standaard_comp_df = componenten_naar_df(scenario.componenten)
    if "component_tabel" not in st.session_state or st.session_state.get("_comp_geladen") != scenario.naam:
        st.session_state["component_tabel"] = standaard_comp_df
        st.session_state["_comp_geladen"] = scenario.naam
        # Reset vermogenwidgets zodat ze de waarden van het nieuwe scenario tonen
        st.session_state["comp_spaargeld"] = int(scenario.spaargeld_start)
        st.session_state["comp_inleg"] = int(scenario.jaarlijkse_inleg)
        st.session_state["comp_rendement"] = float(scenario.rendement_pct)
        st.session_state["comp_inflatie"] = float(scenario.inflatie_pct)
        st.session_state["comp_box3"] = scenario.box3_meenemen
        st.session_state["comp_box3_spaargeld"] = int(scenario.box3_spaargeld_fractie * 100)

    with st.expander("➕ Voeg sjabloon toe", expanded=False):
        sj_col, sj_btn_col = st.columns([4, 1])
        with sj_col:
            sj_keuze = st.selectbox(
                "Kies een sjabloon",
                options=[s.label for s in COMPONENT_SJABLONEN],
                key="comp_sj_selectie",
                label_visibility="collapsed",
            )
        with sj_btn_col:
            if st.button("Voeg toe", key="comp_sj_toevoegen"):
                sj = next(s for s in COMPONENT_SJABLONEN if s.label == sj_keuze)
                nieuwe_rij = pd.DataFrame([{
                    "omschrijving": sj.omschrijving,
                    "categorie": CATEGORIE_LABELS[sj.categorie],
                    "persoon": sj.persoon,
                    "bedrag_type": BEDRAG_TYPE_LABELS[sj.bedrag_type],
                    "bedrag": float(sj.bedrag),
                    "frequentie": FREQUENTIE_LABELS[sj.frequentie],
                    "begindatum": "",
                    "einddatum": "",
                    "groei_pct": float(sj.groei_pct),
                    "beleggings_type": BELEGGINGS_TYPE_LABELS[sj.beleggings_type],
                }])
                st.session_state["component_tabel"] = pd.concat(
                    [st.session_state["component_tabel"], nieuwe_rij], ignore_index=True
                )
                st.rerun()

    component_df = st.data_editor(
        st.session_state["component_tabel"],
        num_rows="dynamic",
        column_config={
            "omschrijving": st.column_config.TextColumn("Omschrijving", required=True, width="medium"),
            "categorie": st.column_config.SelectboxColumn("Categorie", options=CATEGORIE_OPTIES, required=True, width="medium"),
            "persoon": st.column_config.SelectboxColumn("Persoon", options=persoon_opties, required=True, width="small"),
            "bedrag_type": st.column_config.SelectboxColumn("Type", options=BEDRAG_TYPE_OPTIES, required=True, width="small"),
            "bedrag": st.column_config.NumberColumn("Bedrag (€)", min_value=0.0, format="%.2f", required=True, width="small"),
            "frequentie": st.column_config.SelectboxColumn("Frequentie", options=FREQUENTIE_OPTIES, required=True, width="medium"),
            "beleggings_type": st.column_config.SelectboxColumn("Soort vermogen", options=BELEGGINGS_TYPE_OPTIES, required=True, width="small"),
            "begindatum": st.column_config.TextColumn("Begindatum (dd-mm-jjjj)", width="medium"),
            "einddatum": st.column_config.TextColumn("Einddatum (dd-mm-jjjj)", width="medium"),
            "groei_pct": st.column_config.NumberColumn("Groei % /jaar", min_value=0.0, max_value=20.0, format="%.1f", width="small"),
        },
        use_container_width=True,
        key="component_editor_v2",
    )

    st.divider()
    st.subheader("Pensioendatums (uit MPO-import)")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("**Persoon 1**")
        records_p1 = toon_pensioen_editor("records_p1", "Persoon 1")
    with col_p2:
        if heeft_partner:
            st.markdown("**Persoon 2**")
            records_p2 = toon_pensioen_editor("records_p2", "Persoon 2")
        else:
            records_p2 = []

    st.divider()
    st.subheader("Eenmalige ontvangsten en uitgaven")
    standaard_inc = pd.DataFrame(
        [{"datum": i.datum.strftime("%d-%m-%Y"), "bedrag": float(i.bedrag), "omschrijving": i.omschrijving}
         for i in scenario.incidentele_items],
        columns=["datum", "bedrag", "omschrijving"],
    ) if scenario.incidentele_items else pd.DataFrame({
        "datum": pd.Series(dtype="object"),
        "bedrag": pd.Series(dtype="float64"),
        "omschrijving": pd.Series(dtype="object"),
    })

    if "incidenteel_tabel" not in st.session_state or st.session_state.get("_inc_geladen") != scenario.naam:
        st.session_state["incidenteel_tabel"] = standaard_inc
        st.session_state["_inc_geladen"] = scenario.naam

    incidenteel_df = st.data_editor(
        st.session_state["incidenteel_tabel"],
        num_rows="dynamic",
        column_config={
            "datum": st.column_config.TextColumn("Datum (dd-mm-jjjj)", required=True),
            "bedrag": st.column_config.NumberColumn("Bedrag (€, negatief = uitgave)", format="%.2f", required=True),
            "omschrijving": st.column_config.TextColumn("Omschrijving"),
        },
        use_container_width=True,
        key="incidenteel_editor_v2",
    )

    st.divider()
    st.subheader("Vermogen en rendement")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        spaargeld = st.number_input(
            "Spaargeld/beleggingen nu (€)",
            min_value=0, value=int(scenario.spaargeld_start),
            step=1000, key="comp_spaargeld",
        )
        jaarlijkse_inleg = st.number_input(
            "Jaarlijkse extra inleg (€)",
            min_value=0, value=int(scenario.jaarlijkse_inleg),
            step=500, key="comp_inleg",
        )
    with col_v2:
        # Toggle voor afzonderlijke rendementen
        gebruik_aparte_rendementen = st.checkbox(
            "Gebruik afzonderlijke rendementen voor sparen en beleggen",
            value=scenario.rendement_sparen_pct is not None or scenario.rendement_beleggen_pct is not None,
            key="comp_aparte_rendementen",
            help="Schakel in om verschillende rendementen in te stellen voor spaargeld en beleggingen.",
        )
        
        if gebruik_aparte_rendementen:
            rendement_sparen = st.slider(
                "Rendement op spaargeld (%)", 0.0, 10.0,
                float(scenario.get_rendement_sparen()), 0.1, key="comp_rendement_sparen",
                help="Verwacht jaarrendement op spaargeld (bijv. 0,5-2%).",
            )
            rendement_beleggen = st.slider(
                "Rendement op beleggingen (%)", 0.0, 10.0,
                float(scenario.get_rendement_beleggen()), 0.1, key="comp_rendement_beleggen",
                help="Verwacht jaarrendement op beleggingen (bijv. 4-7%).",
            )
            # Voor backward compat: gemiddelde als fallback
            rendement_avg = (Decimal(str(rendement_sparen)) + Decimal(str(rendement_beleggen))) / 2
        else:
            rendement_avg = st.slider(
                "Verwacht rendement (%)", 0.0, 10.0,
                float(scenario.rendement_pct), 0.1, key="comp_rendement",
                help="Gemiddeld jaarrendement (gebruikt als aparte rendementen niet ingesteld).",
            )
            rendement_sparen = rendement_avg
            rendement_beleggen = rendement_avg
            rendement_avg = Decimal(str(rendement_avg))
        
        inflatie = st.slider(
            "Verwachte inflatie (%)", 0.0, 10.0,
            float(scenario.inflatie_pct), 0.1, key="comp_inflatie",
            help="Gebruikt voor de reële koopkrachtkolom in de resultaten.",
        )
        box3_meenemen = st.checkbox(
            "Box 3 heffing meenemen (indicatief)",
            value=scenario.box3_meenemen, key="comp_box3",
        )
        if box3_meenemen:
            box3_spaargeld_pct = st.slider(
                "Box 3: % vermogen op spaarrekening",
                min_value=0, max_value=100,
                value=int(scenario.box3_spaargeld_fractie * 100),
                step=5, key="comp_box3_spaargeld",
                help="100% = spaargeld (forfait ~1,5%); 0% = beleggingen (forfait ~6%). "
                     "Belasting = 36% over fictief rendement.",
            )
        else:
            box3_spaargeld_pct = 100

    st.divider()
    st.caption("Wijzigingen in componenten worden automatisch opgeslagen.")

    try:
        componenten = df_naar_componenten(component_df)

        def _datum_uit_tekst(s: str | None) -> date | None:
            if not s or str(s).strip() == "":
                return None
            for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(str(s).strip(), fmt).date()
                except ValueError:
                    continue
            return None

        incidentele_items: list[IncidenteelItem] = []
        for _, rij in incidenteel_df.iterrows():
            d = _datum_uit_tekst(rij.get("datum"))
            b = rij.get("bedrag")
            if d is not None and b is not None:
                try:
                    incidentele_items.append(
                        IncidenteelItem(
                            datum=d,
                            bedrag=Decimal(str(b)),
                            omschrijving=str(rij.get("omschrijving", "")),
                        )
                    )
                except (ValueError, InvalidOperation):
                    pass

        nieuwe_spaargeld = Decimal(str(spaargeld))
        nieuwe_inleg = Decimal(str(jaarlijkse_inleg))
        nieuwe_inflatie = Decimal(str(inflatie))
        nieuwe_box3_fractie = Decimal(str(box3_spaargeld_pct)) / Decimal("100")
        
        # Rendement: sla beide opslag sparen en beleggen op als deze ingesteld zijn
        if gebruik_aparte_rendementen:
            nieuwe_rendement = rendement_avg  # fallback gemiddelde
            nieuwe_rendement_sparen = Decimal(str(rendement_sparen))
            nieuwe_rendement_beleggen = Decimal(str(rendement_beleggen))
        else:
            nieuwe_rendement = Decimal(str(rendement_avg))
            nieuwe_rendement_sparen = None
            nieuwe_rendement_beleggen = None

        gewijzigd = (
            scenario.componenten != componenten
            or scenario.incidentele_items != incidentele_items
            or scenario.spaargeld_start != nieuwe_spaargeld
            or scenario.jaarlijkse_inleg != nieuwe_inleg
            or scenario.rendement_pct != nieuwe_rendement
            or scenario.rendement_sparen_pct != nieuwe_rendement_sparen
            or scenario.rendement_beleggen_pct != nieuwe_rendement_beleggen
            or scenario.inflatie_pct != nieuwe_inflatie
            or scenario.box3_meenemen != box3_meenemen
            or scenario.box3_spaargeld_fractie != nieuwe_box3_fractie
        )
        if gewijzigd:
            scenario.componenten = componenten
            scenario.incidentele_items = incidentele_items
            scenario.spaargeld_start = nieuwe_spaargeld
            scenario.jaarlijkse_inleg = nieuwe_inleg
            scenario.rendement_pct = nieuwe_rendement
            scenario.rendement_sparen_pct = nieuwe_rendement_sparen
            scenario.rendement_beleggen_pct = nieuwe_rendement_beleggen
            scenario.inflatie_pct = nieuwe_inflatie
            scenario.box3_meenemen = box3_meenemen
            scenario.box3_spaargeld_fractie = nieuwe_box3_fractie
            scenario.laatst_gewijzigd_op = datetime.now()

            for i, sc in enumerate(scenario_lijst):
                if sc.naam == scenario.naam:
                    scenario_lijst[i] = scenario
                    break

            st.session_state["scenario_lijst"] = scenario_lijst
            st.session_state["records_p1"] = records_p1
            if heeft_partner:
                st.session_state["records_p2"] = records_p2

            sla_sessie_op()
            st.caption(f"Automatisch opgeslagen: {scenario.naam}")
            st.rerun()

    except (TypeError, ValueError) as exc:
        st.error(f"❌ Ongeldige componentinvoer: {exc}")

    # ─── Vorige/Volgende knoppen ────────────────────────────────────────────
    st.divider()
    col_vorige, col_volgende = st.columns(2)

    with col_vorige:
        if st.button("← Vorige"):
            set_huidge_stap(Stap.SCENARIO, validatie_ok=False)
            st.rerun()

    with col_volgende:
        if st.button("Volgende →", use_container_width=True):
            set_huidge_stap(Stap.BEREKEN, validatie_ok=True)
            st.rerun()
