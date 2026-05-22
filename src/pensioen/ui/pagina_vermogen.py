"""Streamlit-pagina: vermogensitems beheer per actief scenario."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import streamlit as st

from pensioen.models.vermogensitem import VermogensItem, VermogensType
from pensioen.ui.scenario_context import get_actief_scenario
from pensioen.ui.sessie_persistentie import sla_sessie_op


def _update_scenario(scenario, scenario_lijst):
    """Update scenario in lijst en sla op."""
    scenario.laatst_gewijzigd_op = datetime.now()
    for i, sc in enumerate(scenario_lijst):
        if sc.naam == scenario.naam:
            scenario_lijst[i] = scenario
            break
    st.session_state["scenario_lijst"] = scenario_lijst
    sla_sessie_op()


def toon_vermogen_pagina() -> None:
    """Beheer vermogensitems voor het actieve scenario."""
    st.header("💰 Vermogensitems")

    scenario_lijst = st.session_state.get("scenario_lijst", [])
    actief = get_actief_scenario(scenario_lijst)
    if actief is None:
        st.warning("⚠️ Kies eerst een actief scenario.")
        return

    scenario = actief
    st.caption(f"Actief scenario: {scenario.naam}")
    
    # Migreer legacy vermogen indien nodig
    if not scenario.vermogensitems and (scenario.spaargeld_start > Decimal("0") or scenario.beleggingen_start > Decimal("0")):
        scenario.migreer_legacy_vermogen()
        _update_scenario(scenario, scenario_lijst)
        st.rerun()
    
    # Tabs per vermogenstype
    tab_liquide, tab_bezit, tab_overzicht = st.tabs([
        "💵 Liquide middelen", 
        "🏠 Bezittingen",
        "📊 Overzicht"
    ])
    
    with tab_liquide:
        st.markdown("### Spaargeld en beleggingen")
        
        liquide_items = [
            item for item in scenario.vermogensitems 
            if item.type in (VermogensType.SPAARGELD, VermogensType.BELEGGINGEN)
        ]
        
        if not liquide_items:
            st.info("Nog geen spaargeld of beleggingen toegevoegd.")
        else:
            for idx, item in enumerate(liquide_items):
                render_vermogensitem_card(item, idx, scenario, scenario_lijst, "liquide")
        
        st.divider()
        if st.button("➕ Nieuwe liquide middelen", key="liquide_nieuwe"):
            st.session_state["vermogen_active_mode"] = "add_liquide"
            st.rerun()
        
        # Formulier voor toevoegen
        if st.session_state.get("vermogen_active_mode") == "add_liquide":
            render_vermogensitem_form("liquide", None, scenario, scenario_lijst)
    
    with tab_bezit:
        st.markdown("### Fysieke bezittingen")
        
        bezit_items = [
            item for item in scenario.vermogensitems 
            if item.type not in (VermogensType.SPAARGELD, VermogensType.BELEGGINGEN)
        ]
        
        if not bezit_items:
            st.info("Nog geen fysieke bezittingen toegevoegd.")
        else:
            for idx, item in enumerate(bezit_items):
                render_vermogensitem_card(item, idx, scenario, scenario_lijst, "bezit")
        
        st.divider()
        if st.button("➕ Nieuwe bezitting", key="bezit_nieuwe"):
            st.session_state["vermogen_active_mode"] = "add_bezit"
            st.rerun()
        
        # Formulier voor toevoegen
        if st.session_state.get("vermogen_active_mode") == "add_bezit":
            render_vermogensitem_form("bezit", None, scenario, scenario_lijst)
    
    with tab_overzicht:
        st.markdown("### Totaal vermogensoverzicht")
        
        peildatum = date.today()
        totaal = scenario.totaal_vermogen_op_datum(peildatum)
        box3_belast = sum(
            item.waarde_op_datum(peildatum) 
            for item in scenario.vermogensitems 
            if item.box3_belast and item.is_actief_op(peildatum)
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Totaal vermogen", f"€ {totaal:,.0f}")
        with col2:
            st.metric("📊 Box 3 belast", f"€ {box3_belast:,.0f}")
        with col3:
            vrijgesteld = totaal - box3_belast
            st.metric("🏠 Vrijgesteld", f"€ {vrijgesteld:,.0f}")
        
        st.divider()
        
        # Tabel met alle items
        if scenario.vermogensitems:
            st.markdown("#### Alle vermogensitems")
            
            for item in scenario.vermogensitems:
                if item.is_actief_op(peildatum):
                    waarde = item.waarde_op_datum(peildatum)
                    box3_status = "✅ Ja" if item.box3_belast else "❌ Nee"
                    
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    with col1:
                        st.write(f"**{item.omschrijving}**")
                        st.caption(f"{item.type.value.title()} • {item.persoon}")
                    with col2:
                        st.write(f"€ {waarde:,.0f}")
                    with col3:
                        st.write(box3_status)
                    with col4:
                        if item.groei_pct != Decimal("0"):
                            st.caption(f"{float(item.groei_pct):+.1f}%")


def render_vermogensitem_card(
    item: VermogensItem,
    idx: int,
    scenario,
    scenario_lijst,
    prefix: str
) -> None:
    """Toon een vermogensitem als card met acties."""
    with st.container(border=True):
        col1, col2, col3 = st.columns([4, 2, 1])
        
        with col1:
            st.markdown(f"**{item.omschrijving}**")
            st.caption(f"{item.type.value.title()} • {item.persoon}")
        
        with col2:
            peildatum = date.today()
            waarde = item.waarde_op_datum(peildatum)
            st.metric("Waarde", f"€ {waarde:,.0f}")
        
        with col3:
            col_edit, col_del = st.columns(2)
            with col_edit:
                if st.button("✏️", key=f"{prefix}_edit_{idx}", help="Bewerken"):
                    st.session_state["vermogen_active_mode"] = f"edit_{prefix}"
                    st.session_state["vermogen_active_idx"] = idx
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"{prefix}_del_{idx}", help="Verwijderen"):
                    scenario.vermogensitems.remove(item)
                    _update_scenario(scenario, scenario_lijst)
                    st.rerun()
        
        # Details
        cols = st.columns(4)
        with cols[0]:
            st.caption(f"Aanschafwaarde: € {item.aanschafwaarde:,.0f}")
        with cols[1]:
            st.caption(f"Groei: {float(item.groei_pct):+.1f}%/jaar")
        with cols[2]:
            st.caption(f"Box 3: {'Ja' if item.box3_belast else 'Nee'}")
        with cols[3]:
            if item.verkoopdatum:
                st.caption(f"Verkoop: {item.verkoopdatum.strftime('%d-%m-%Y')}")


def render_vermogensitem_form(
    form_type: str,
    edit_idx: int | None,
    scenario,
    scenario_lijst
) -> None:
    """Toon formulier om vermogensitem toe te voegen of te bewerken."""
    is_edit = edit_idx is not None
    title = "Bewerk" if is_edit else "Nieuw"
    
    if is_edit and edit_idx < len(scenario.vermogensitems):
        item = scenario.vermogensitems[edit_idx]
    else:
        item = None
    
    with st.form(f"vermogen_form_{form_type}"):
        st.markdown(f"### {title} vermogensitem")
        
        # Type selectie
        if form_type == "liquide":
            type_opties = [VermogensType.SPAARGELD, VermogensType.BELEGGINGEN]
        else:
            type_opties = [
                VermogensType.EIGEN_WONING,
                VermogensType.AUTO,
                VermogensType.KUNST,
                VermogensType.BOOT,
                VermogensType.OVERIG,
            ]
        
        default_type_idx = 0
        if item and item.type in type_opties:
            default_type_idx = type_opties.index(item.type)
        
        vermogenstype = st.selectbox(
            "Type",
            type_opties,
            format_func=lambda x: x.value.title(),
            index=default_type_idx,
        )
        
        omschrijving = st.text_input(
            "Omschrijving",
            value=item.omschrijving if item else "",
            placeholder="bijv. 'Spaarrekening ING' of 'Tesla Model 3'"
        )
        
        persoon = st.selectbox(
            "Eigenaar",
            ["Huishouden", "P1", "P2"],
            index=["Huishouden", "P1", "P2"].index(item.persoon) if item else 0,
        )
        
        col1, col2 = st.columns(2)
        with col1:
            aanschafwaarde = st.number_input(
                "Aanschafwaarde (€)",
                min_value=0,
                value=int(item.aanschafwaarde) if item else 0,
                step=1000,
            )
        
        with col2:
            groei_pct = st.number_input(
                "Groei/afschrijving (%/jaar)",
                min_value=-100.0,
                max_value=100.0,
                value=float(item.groei_pct) if item else 0.0,
                step=0.5,
                help="Positief = waardestijging, negatief = afschrijving"
            )
        
        # Datums
        col1, col2 = st.columns(2)
        with col1:
            aanschafdatum = st.date_input(
                "Aanschafdatum",
                value=item.aanschafdatum if item and item.aanschafdatum else None,
                help="Laat leeg als item al in bezit is bij start planning"
            )
        
        with col2:
            verkoopdatum = st.date_input(
                "Verkoopdatum (optioneel)",
                value=item.verkoopdatum if item and item.verkoopdatum else None,
                help="Laat leeg als item niet verkocht wordt"
            )
        
        # Verkoopprijs (alleen als verkoopdatum is ingevuld)
        verkoopprijs = None
        if verkoopdatum:
            verkoopprijs = st.number_input(
                "Verkoopprijs (€)",
                min_value=0,
                value=int(item.verkoopprijs) if item and item.verkoopprijs else 0,
                step=1000,
                help="Laat op 0 voor automatische berekening op basis van waardering"
            )
            if verkoopprijs == 0:
                verkoopprijs = None
        
        # Box 3
        if vermogenstype != VermogensType.EIGEN_WONING:
            box3_belast = st.checkbox(
                "Box 3 belast",
                value=item.box3_belast if item else True,
                help="Vink uit voor vrijgestelde items (bijv. recreatievaartuig)"
            )
        else:
            box3_belast = False
            st.info("ℹ️ Eigen woning is vrijgesteld van box 3 (eigenwoningforfait box 1)")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Opslaan", type="primary", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Annuleren", use_container_width=True)
        
        if submit:
            if not omschrijving:
                st.error("Omschrijving is verplicht")
                return
            
            try:
                nieuw_item = VermogensItem(
                    omschrijving=omschrijving,
                    type=vermogenstype,
                    persoon=persoon,
                    aanschafwaarde=Decimal(str(aanschafwaarde)),
                    aanschafdatum=aanschafdatum if aanschafdatum else None,
                    groei_pct=Decimal(str(groei_pct)),
                    verkoopdatum=verkoopdatum if verkoopdatum else None,
                    verkoopprijs=Decimal(str(verkoopprijs)) if verkoopprijs else None,
                    box3_belast=box3_belast,
                )
                
                if is_edit:
                    scenario.vermogensitems[edit_idx] = nieuw_item
                else:
                    scenario.vermogensitems.append(nieuw_item)
                
                _update_scenario(scenario, scenario_lijst)
                st.session_state["vermogen_active_mode"] = None
                st.session_state["vermogen_active_idx"] = None
                st.success("✅ Vermogensitem opgeslagen")
                st.rerun()
                
            except ValueError as e:
                st.error(f"❌ Validatiefout: {e}")
        
        if cancel:
            st.session_state["vermogen_active_mode"] = None
            st.session_state["vermogen_active_idx"] = None
            st.rerun()
