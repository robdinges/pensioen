"""Streamlit-pagina: financiële componenten per actief scenario."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import streamlit as st

from pensioen.ui.flow_context import Stap, set_huidge_stap
from pensioen.ui.scenario_context import get_actief_scenario
from pensioen.ui.sessie_persistentie import sla_sessie_op
from pensioen.ui.component_helpers import (
    render_component_card,
    render_component_form,
    render_incidenteel_card,
    render_incidenteel_form,
)


def toon_componenten_pagina() -> None:
    """Bewerk financiële componenten voor het actieve scenario."""
    st.header("Financiële componenten")

    scenario_lijst = st.session_state.get("scenario_lijst", [])
    actief = get_actief_scenario(scenario_lijst)
    if actief is None:
        st.warning("⚠️ Kies eerst een actief scenario.")
        return

    def _update_scenario(scenario, scenario_lijst):
        """Update scenario in lijst en sla op."""
        scenario.laatst_gewijzigd_op = datetime.now()
        for i, sc in enumerate(scenario_lijst):
            if sc.naam == scenario.naam:
                scenario_lijst[i] = scenario
                break
        st.session_state["scenario_lijst"] = scenario_lijst
        sla_sessie_op()

    scenario = actief
    st.caption(f"Actief scenario: {scenario.naam}")

    heeft_partner = "persoon2" in st.session_state
    persoon_opties = ["P1", "P2", "Huishouden"] if heeft_partner else ["P1", "Huishouden"]

    # Reset vermogenwidgets zodat ze de waarden van het nieuwe scenario tonen
    if st.session_state.get("_comp_geladen") != scenario.naam:
        st.session_state["_comp_geladen"] = scenario.naam
        st.session_state["comp_spaargeld"] = int(scenario.spaargeld_start)
        st.session_state["comp_beleggingen"] = int(scenario.beleggingen_start)
        # Backward compatibility: gebruik oude jaarlijkse_inleg als nieuwe velden leeg zijn
        if scenario.jaarlijkse_inleg > 0 and scenario.jaarlijkse_inleg_sparen == 0 and scenario.jaarlijkse_inleg_beleggen == 0:
            st.session_state["comp_inleg_sparen"] = int(scenario.jaarlijkse_inleg)
            st.session_state["comp_inleg_beleggen"] = 0
        else:
            st.session_state["comp_inleg_sparen"] = int(scenario.jaarlijkse_inleg_sparen)
            st.session_state["comp_inleg_beleggen"] = int(scenario.jaarlijkse_inleg_beleggen)
        st.session_state["comp_rendement"] = float(scenario.rendement_pct)
        st.session_state["comp_inflatie"] = float(scenario.inflatie_pct)
        st.session_state["comp_box3"] = scenario.box3_meenemen
        st.session_state["comp_box3_spaargeld"] = int(scenario.box3_spaargeld_fractie * 100)
    
    # ========== PERIODIEKE INKOMSTEN EN UITGAVEN ==========
    st.divider()
    st.markdown("### 📊 Periodieke inkomsten en uitgaven")
    
    # Zoekbalk
    zoek_query = st.text_input("🔍 Zoek component", key="comp_zoek", placeholder="Typ om te filteren op omschrijving...")
    
    # Filter componenten op categorie
    from pensioen.models.component import CategorieComponent
    
    categorie_inkomen = [CategorieComponent.ARBEIDSINKOMEN, CategorieComponent.OVERIG_INKOMEN]
    categorie_uitgave = [CategorieComponent.UITGAVE, CategorieComponent.INHOUDING]
    categorie_pensioen = [CategorieComponent.PENSIOEN_INKOMEN]
    
    inkomsten = [c for c in scenario.componenten if c.categorie in categorie_inkomen]
    uitgaven = [c for c in scenario.componenten if c.categorie in categorie_uitgave]
    pensioenen = [c for c in scenario.componenten if c.categorie in categorie_pensioen]
    
    # Toepassen zoekfilter
    if zoek_query:
        inkomsten = [c for c in inkomsten if zoek_query.lower() in c.omschrijving.lower()]
        uitgaven = [c for c in uitgaven if zoek_query.lower() in c.omschrijving.lower()]
        pensioenen = [c for c in pensioenen if zoek_query.lower() in c.omschrijving.lower()]
    
    tab_ink, tab_uitg, tab_pens = st.tabs([f"💰 Inkomsten ({len(inkomsten)})", f"🧾 Uitgaven ({len(uitgaven)})", f"🏦 Pensioenen ({len(pensioenen)})"])
    
    with tab_ink:
        # Toevoeg-knop
        if st.button("➕ Nieuwe inkomst", key="ink_nieuwe"):
            st.session_state["ink_active_mode"] = "add"
            st.session_state["ink_active_idx"] = None
            st.rerun()
        
        # Formulier indien actief
        active_mode = st.session_state.get("ink_active_mode")
        active_idx = st.session_state.get("ink_active_idx")
        
        if active_mode == "add":
            nieuwe_comp = render_component_form(
                section_key="ink",
                mode="add",
                initial=None,
                persoon_opties=persoon_opties,
            )
            if nieuwe_comp:
                scenario.componenten.append(nieuwe_comp)
                st.session_state["ink_active_mode"] = None
                _update_scenario(scenario, scenario_lijst)
                st.rerun()
        elif active_mode == "edit" and active_idx is not None:
            gewijzigde_comp = render_component_form(
                section_key="ink",
                mode="edit",
                initial=inkomsten[active_idx],
                persoon_opties=persoon_opties,
            )
            if gewijzigde_comp:
                # Vervang in scenario.componenten
                orig_idx = scenario.componenten.index(inkomsten[active_idx])
                scenario.componenten[orig_idx] = gewijzigde_comp
                st.session_state["ink_active_mode"] = None
                st.session_state["ink_active_idx"] = None
                _update_scenario(scenario, scenario_lijst)
                st.rerun()
        
        # Verwijder-logica
        if "ink_delete_idx" in st.session_state:
            del_idx = st.session_state["ink_delete_idx"]
            orig_idx = scenario.componenten.index(inkomsten[del_idx])
            scenario.componenten.pop(orig_idx)
            del st.session_state["ink_delete_idx"]
            _update_scenario(scenario, scenario_lijst)
            st.rerun()
        
        # Toon cards in grid van 3 kolommen
        st.markdown("---")
        if not inkomsten:
            st.info("Geen periodieke inkomsten ingesteld. Klik 'Nieuwe inkomst' om er een toe te voegen.")
        else:
            # Render in groepen van 3
            for row_start in range(0, len(inkomsten), 3):
                cols = st.columns(3)
                for col_idx in range(3):
                    i = row_start + col_idx
                    if i < len(inkomsten):
                        with cols[col_idx]:
                            render_component_card(inkomsten[i], i, "ink")
    
    with tab_uitg:
        # Toevoeg-knop
        if st.button("➕ Nieuwe uitgave", key="uitg_nieuwe"):
            st.session_state["uitg_active_mode"] = "add"
            st.session_state["uitg_active_idx"] = None
            st.rerun()
        
        # Formulier indien actief
        active_mode_uitg = st.session_state.get("uitg_active_mode")
        active_idx_uitg = st.session_state.get("uitg_active_idx")
        
        if active_mode_uitg == "add":
            nieuwe_comp = render_component_form(
                section_key="uitg",
                mode="add",
                initial=None,
                persoon_opties=persoon_opties,
            )
            if nieuwe_comp:
                scenario.componenten.append(nieuwe_comp)
                st.session_state["uitg_active_mode"] = None
                _update_scenario(scenario, scenario_lijst)
                st.rerun()
        elif active_mode_uitg == "edit" and active_idx_uitg is not None:
            gewijzigde_comp = render_component_form(
                section_key="uitg",
                mode="edit",
                initial=uitgaven[active_idx_uitg],
                persoon_opties=persoon_opties,
            )
            if gewijzigde_comp:
                # Vervang in scenario.componenten
                orig_idx = scenario.componenten.index(uitgaven[active_idx_uitg])
                scenario.componenten[orig_idx] = gewijzigde_comp
                st.session_state["uitg_active_mode"] = None
                st.session_state["uitg_active_idx"] = None
                _update_scenario(scenario, scenario_lijst)
                st.rerun()
        
        # Verwijder-logica
        if "uitg_delete_idx" in st.session_state:
            del_idx = st.session_state["uitg_delete_idx"]
            orig_idx = scenario.componenten.index(uitgaven[del_idx])
            scenario.componenten.pop(orig_idx)
            del st.session_state["uitg_delete_idx"]
            _update_scenario(scenario, scenario_lijst)
            st.rerun()
        
        # Toon cards in grid van 3 kolommen
        st.markdown("---")
        if not uitgaven:
            st.info("Geen periodieke uitgaven ingesteld. Klik 'Nieuwe uitgave' om er een toe te voegen.")
        else:
            # Render in groepen van 3
            for row_start in range(0, len(uitgaven), 3):
                cols = st.columns(3)
                for col_idx in range(3):
                    i = row_start + col_idx
                    if i < len(uitgaven):
                        with cols[col_idx]:
                            render_component_card(uitgaven[i], i, "uitg")
    
    with tab_pens:
        # Toevoeg-knop
        if st.button("➕ Nieuw pensioen", key="pens_nieuwe"):
            st.session_state["pens_active_mode"] = "add"
            st.session_state["pens_active_idx"] = None
            st.rerun()
        
        # Formulier indien actief
        active_mode_pens = st.session_state.get("pens_active_mode")
        active_idx_pens = st.session_state.get("pens_active_idx")
        
        if active_mode_pens == "add":
            nieuwe_comp = render_component_form(
                section_key="pens",
                mode="add",
                initial=None,
                persoon_opties=persoon_opties,
            )
            if nieuwe_comp:
                scenario.componenten.append(nieuwe_comp)
                st.session_state["pens_active_mode"] = None
                _update_scenario(scenario, scenario_lijst)
                st.rerun()
        elif active_mode_pens == "edit" and active_idx_pens is not None:
            gewijzigde_comp = render_component_form(
                section_key="pens",
                mode="edit",
                initial=pensioenen[active_idx_pens],
                persoon_opties=persoon_opties,
            )
            if gewijzigde_comp:
                # Vervang in scenario.componenten
                orig_idx = scenario.componenten.index(pensioenen[active_idx_pens])
                scenario.componenten[orig_idx] = gewijzigde_comp
                st.session_state["pens_active_mode"] = None
                st.session_state["pens_active_idx"] = None
                _update_scenario(scenario, scenario_lijst)
                st.rerun()
        
        # Verwijder-logica
        if "pens_delete_idx" in st.session_state:
            del_idx = st.session_state["pens_delete_idx"]
            orig_idx = scenario.componenten.index(pensioenen[del_idx])
            scenario.componenten.pop(orig_idx)
            del st.session_state["pens_delete_idx"]
            _update_scenario(scenario, scenario_lijst)
            st.rerun()
        
        # Toon cards in grid van 3 kolommen
        st.markdown("---")
        if not pensioenen:
            st.info("Geen pensioenen ingesteld. Klik 'Nieuw pensioen' om er een toe te voegen, of importeer vanaf Mijn Pensioen Overzicht.")
        else:
            # Render in groepen van 3
            for row_start in range(0, len(pensioenen), 3):
                cols = st.columns(3)
                for col_idx in range(3):
                    i = row_start + col_idx
                    if i < len(pensioenen):
                        with cols[col_idx]:
                            render_component_card(pensioenen[i], i, "pens")

    st.divider()
    st.subheader("💸 Eenmalige ontvangsten en uitgaven")
    
    # Toevoeg-knop
    if st.button("➕ Nieuwe eenmalige cashflow", key="inc_nieuwe"):
        st.session_state["inc_active_mode"] = "add"
        st.session_state["inc_active_idx"] = None
        st.rerun()
    
    # Formulier indien actief
    active_mode_inc = st.session_state.get("inc_active_mode")
    active_idx_inc = st.session_state.get("inc_active_idx")
    
    if active_mode_inc == "add":
        nieuw_item = render_incidenteel_form(
            section_key="inc",
            mode="add",
            initial=None,
        )
        if nieuw_item:
            scenario.incidentele_items.append(nieuw_item)
            st.session_state["inc_active_mode"] = None
            _update_scenario(scenario, scenario_lijst)
            st.rerun()
    elif active_mode_inc == "edit" and active_idx_inc is not None:
        gewijzigd_item = render_incidenteel_form(
            section_key="inc",
            mode="edit",
            initial=scenario.incidentele_items[active_idx_inc],
        )
        if gewijzigd_item:
            scenario.incidentele_items[active_idx_inc] = gewijzigd_item
            st.session_state["inc_active_mode"] = None
            st.session_state["inc_active_idx"] = None
            _update_scenario(scenario, scenario_lijst)
            st.rerun()
    
    # Verwijder-logica
    if "inc_delete_idx" in st.session_state:
        del_idx = st.session_state["inc_delete_idx"]
        scenario.incidentele_items.pop(del_idx)
        del st.session_state["inc_delete_idx"]
        _update_scenario(scenario, scenario_lijst)
        st.rerun()
    
    # Toon cards in grid van 3 kolommen
    st.markdown("---")
    if not scenario.incidentele_items:
        st.info("Geen eenmalige cashflows ingesteld. Klik 'Nieuwe eenmalige cashflow' om er een toe te voegen.")
    else:
        # Sorteer op datum
        sorted_items = sorted(scenario.incidentele_items, key=lambda x: x.datum)
        # Render in groepen van 3
        for row_start in range(0, len(sorted_items), 3):
            cols = st.columns(3)
            for col_idx in range(3):
                i = row_start + col_idx
                if i < len(sorted_items):
                    with cols[col_idx]:
                        render_incidenteel_card(sorted_items[i], i, "inc")

    st.divider()
    st.markdown("### 💼 Vermogen & rendement")
    
    from pensioen.ui.style import section_header_html, COLORS, format_bedrag
    
    # Header met icoon
    st.markdown(section_header_html("Startpositie vermogen", "💰", COLORS["vermogen"]), unsafe_allow_html=True)
    
    peildatum = date.today().replace(day=1)
    fractie_sparen = scenario.bereken_spaargeld_fractie_op_datum(peildatum)
    fractie_beleggen = Decimal("1") - fractie_sparen
    
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        spaargeld = st.number_input(
            "🏦 Spaargeld nu (€)",
            min_value=0,
            value=int(scenario.spaargeld_start),
            step=1000,
            key="comp_spaargeld",
            help="Bedrag op spaarrekeningen per vandaag.",
        )
    with col_v2:
        beleggingen = st.number_input(
            "📈 Beleggingen nu (€)",
            min_value=0,
            value=int(scenario.beleggingen_start),
            step=1000,
            key="comp_beleggingen",
            help="Waarde van beleggingsportefeuille per vandaag.",
        )
    with col_v3:
        totaal = spaargeld + beleggingen
        st.metric(
            "Totaal vermogen",
            format_bedrag(totaal),
            help="Som van spaargeld en beleggingen.",
        )
        # Toon split alleen als beide types aanwezig zijn
        if fractie_sparen > 0 and fractie_beleggen > 0:
            st.metric(
                "Huidige split",
                f"{float(fractie_sparen * 100):.0f}% / {float(fractie_beleggen * 100):.0f}%",
                help="Sparen / Beleggen (incl. actieve componenten deze maand).",
            )
    
    st.markdown(section_header_html("Rendement & inflatie", "📊", COLORS["vermogen"]), unsafe_allow_html=True)
    
    # Toggle voor afzonderlijke rendementen
    gebruik_aparte_rendementen = st.checkbox(
        "Gebruik afzonderlijke rendementen voor sparen en beleggen",
        value=scenario.rendement_sparen_pct is not None or scenario.rendement_beleggen_pct is not None,
        key="comp_aparte_rendementen",
        help="Schakel in om verschillende rendementen in te stellen voor spaargeld en beleggingen.",
    )
    
    col_r1, col_r2, col_r3 = st.columns(3)
    
    if gebruik_aparte_rendementen:
        with col_r1:
            rendement_sparen = st.slider(
                "Rendement sparen (%)",
                0.0, 10.0,
                float(scenario.get_rendement_sparen()),
                0.1,
                key="comp_rendement_sparen",
                help="Verwacht jaarrendement op spaargeld (bijv. 0,5-2%).",
            )
        with col_r2:
            rendement_beleggen = st.slider(
                "Rendement beleggen (%)",
                0.0, 10.0,
                float(scenario.get_rendement_beleggen()),
                0.1,
                key="comp_rendement_beleggen",
                help="Verwacht jaarrendement op beleggingen (bijv. 4-7%).",
            )
        with col_r3:
            inflatie = st.slider(
                "Inflatie (%)",
                0.0, 10.0,
                float(scenario.inflatie_pct),
                0.1,
                key="comp_inflatie",
                help="Gebruikt voor koopkrachtberekening.",
            )
        # Gemiddelde voor backward compat
        rendement_avg = (Decimal(str(rendement_sparen)) + Decimal(str(rendement_beleggen))) / 2
    else:
        with col_r1:
            rendement_avg = st.slider(
                "Rendement (gem.) (%)",
                0.0, 10.0,
                float(scenario.rendement_pct),
                0.1,
                key="comp_rendement",
                help="Gemiddeld jaarrendement (gebruikt als aparte rendementen niet ingesteld).",
            )
        with col_r2:
            inflatie = st.slider(
                "Inflatie (%)",
                0.0, 10.0,
                float(scenario.inflatie_pct),
                0.1,
                key="comp_inflatie",
                help="Gebruikt voor koopkrachtberekening.",
            )
        rendement_sparen = rendement_avg
        rendement_beleggen = rendement_avg
        rendement_avg = Decimal(str(rendement_avg))
    
    # Aparte inleg velden voor sparen en beleggen
    st.markdown(section_header_html("Jaarlijkse inleg", "💶", COLORS["vermogen"]), unsafe_allow_html=True)
    col_i1, col_i2, col_i3 = st.columns(3)
    with col_i1:
        jaarlijkse_inleg_sparen = st.number_input(
            "Inleg sparen per jaar (€)",
            min_value=0,
            value=int(scenario.jaarlijkse_inleg_sparen) if scenario.jaarlijkse_inleg_sparen > 0 else int(scenario.jaarlijkse_inleg),
            step=500,
            key="comp_inleg_sparen",
            help="Jaarlijkse storting op spaargeld (naast componenten).",
        )
    with col_i2:
        jaarlijkse_inleg_beleggen = st.number_input(
            "Inleg beleggen per jaar (€)",
            min_value=0,
            value=int(scenario.jaarlijkse_inleg_beleggen),
            step=500,
            key="comp_inleg_beleggen",
            help="Jaarlijkse storting op beleggingen (naast componenten).",
        )
    with col_i3:
        totaal_inleg = jaarlijkse_inleg_sparen + jaarlijkse_inleg_beleggen
        st.metric(
            "Totale inleg",
            format_bedrag(totaal_inleg),
            help="Som van inleg sparen en beleggen.",
        )
    
    # Box 3 opties
    st.markdown(section_header_html("Box 3 vermogensrendementsheffing", "🏛️", COLORS["vermogen"]), unsafe_allow_html=True)
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        box3_meenemen = st.checkbox(
            "Box 3 heffing meenemen (indicatief)",
            value=scenario.box3_meenemen,
            key="comp_box3",
            help="Indicatieve berekening o.b.v. forfaitaire rendementen.",
        )
    with col_b2:
        if box3_meenemen:
            box3_spaargeld_pct = st.slider(
                "% vermogen op spaarrekening (Box 3)",
                min_value=0,
                max_value=100,
                value=int(scenario.box3_spaargeld_fractie * 100),
                step=5,
                key="comp_box3_spaargeld",
                help="100% = spaargeld (forfait ~1,5%); 0% = beleggingen (forfait ~6%). "
                     "Belasting = 36% over fictief rendement.",
            )
        else:
            box3_spaargeld_pct = 100


    st.divider()
    st.caption("Wijzigingen in componenten worden automatisch opgeslagen.")

    # Sla vermogen en rendementsparameters op
    nieuwe_spaargeld = Decimal(str(spaargeld))
    nieuwe_beleggingen = Decimal(str(beleggingen))
    nieuwe_inleg_sparen = Decimal(str(jaarlijkse_inleg_sparen))
    nieuwe_inleg_beleggen = Decimal(str(jaarlijkse_inleg_beleggen))
    nieuwe_inflatie = Decimal(str(inflatie))
    nieuwe_box3_fractie = Decimal(str(box3_spaargeld_pct)) / Decimal("100")
    
    # Rendement: sla beide op als deze ingesteld zijn
    if gebruik_aparte_rendementen:
        nieuwe_rendement = rendement_avg  # fallback gemiddelde
        nieuwe_rendement_sparen = Decimal(str(rendement_sparen))
        nieuwe_rendement_beleggen = Decimal(str(rendement_beleggen))
    else:
        nieuwe_rendement = Decimal(str(rendement_avg))
        nieuwe_rendement_sparen = None
        nieuwe_rendement_beleggen = None

    gewijzigd = (
        scenario.spaargeld_start != nieuwe_spaargeld
        or scenario.beleggingen_start != nieuwe_beleggingen
        or scenario.jaarlijkse_inleg_sparen != nieuwe_inleg_sparen
        or scenario.jaarlijkse_inleg_beleggen != nieuwe_inleg_beleggen
        or scenario.rendement_pct != nieuwe_rendement
        or scenario.rendement_sparen_pct != nieuwe_rendement_sparen
        or scenario.rendement_beleggen_pct != nieuwe_rendement_beleggen
        or scenario.inflatie_pct != nieuwe_inflatie
        or scenario.box3_meenemen != box3_meenemen
        or scenario.box3_spaargeld_fractie != nieuwe_box3_fractie
    )
    
    if gewijzigd:
        scenario.spaargeld_start = nieuwe_spaargeld
        scenario.beleggingen_start = nieuwe_beleggingen
        scenario.jaarlijkse_inleg_sparen = nieuwe_inleg_sparen
        scenario.jaarlijkse_inleg_beleggen = nieuwe_inleg_beleggen
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

        sla_sessie_op()
        st.caption(f"Automatisch opgeslagen: {scenario.naam}")

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
