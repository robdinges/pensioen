"""Streamlit-pagina: scenario-beheer met tabel-layout."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pandas as pd
import streamlit as st

from pensioen.models.scenario import Scenario
from pensioen.ui.flow_context import Stap, set_huidge_stap
from pensioen.ui.helpers import fmt_eur
from pensioen.ui.scenario_context import (
    SCENARIO_ACTIEF_KEY,
    SCENARIO_DEFAULT_KEY,
    get_actief_scenario_naam,
    set_actief_scenario_naam,
)
from pensioen.ui.sessie_persistentie import sla_sessie_op


def toon_scenario_pagina() -> None:
    """Toon scenario's in tabel met CRUD-acties en volgende-knop."""
    st.header("📋 Scenario's")

    scenario_lijst: list[Scenario] = st.session_state.get("scenario_lijst", [])
    actief_naam = get_actief_scenario_naam()
    default_naam = st.session_state.get(SCENARIO_DEFAULT_KEY)

    # ─── Nieuw scenario dialog ───────────────────────────────────────────────
    st.subheader("Scenario beheren")
    col_nieuw, col_info = st.columns([1, 4])
    
    with col_nieuw:
        if st.button("➕ Nieuw scenario"):
            st.session_state["_toon_nieuw_scenario_dialog"] = True

    with col_info:
        st.caption(f"{len(scenario_lijst)} scenario's beschikbaar")

    # Dialog: Nieuw scenario
    if st.session_state.get("_toon_nieuw_scenario_dialog"):
        st.divider()
        st.subheader("Nieuw scenario")
        
        col_form, col_kopie = st.columns([2, 1])
        
        with col_form:
            naam = st.text_input("Naam", placeholder="Bijv. Voorzichtig", key="nieuw_scenario_naam")
            beschrijving = st.text_area("Beschrijving", placeholder="Bijv. Met voorzichtige aannames...", key="nieuw_scenario_beschrijving", height=80)
        
        with col_kopie:
            st.write("**Kopie van:**")
            kopie_opties = ["— Leeg —"] + [s.naam for s in scenario_lijst]
            kopie_van = st.selectbox("Basisscenario", options=kopie_opties, key="nieuw_scenario_kopie_van")

        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("✅ Opslaan", key="save_nieuw_scenario"):
                if not naam or not naam.strip():
                    st.error("Naam mag niet leeg zijn")
                elif any(s.naam == naam for s in scenario_lijst):
                    st.error(f"Scenario '{naam}' bestaat al")
                else:
                    if kopie_van == "— Leeg —":
                        # Nieuw leeg scenario
                        nieuw = Scenario(
                            naam=naam.strip(),
                            omschrijving=beschrijving.strip(),
                            aangemaakt_op=datetime.now(),
                            laatst_gewijzigd_op=datetime.now(),
                            is_default=False,
                        )
                    else:
                        # Kopie van bestaand
                        bron = next(s for s in scenario_lijst if s.naam == kopie_van)
                        nieuw = bron.model_copy(deep=True)
                        nieuw.naam = naam.strip()
                        nieuw.omschrijving = beschrijving.strip()
                        nieuw.is_default = False
                        nieuw.aangemaakt_op = datetime.now()
                        nieuw.laatst_gewijzigd_op = datetime.now()
                    
                    scenario_lijst.append(nieuw)
                    st.session_state["scenario_lijst"] = scenario_lijst
                    set_actief_scenario_naam(nieuw.naam)
                    sla_sessie_op()
                    st.session_state["_toon_nieuw_scenario_dialog"] = False
                    st.success(f"✅ Scenario '{naam}' aangemaakt")
                    st.rerun()
        
        with col_cancel:
            if st.button("❌ Annuleren", key="cancel_nieuw_scenario"):
                st.session_state["_toon_nieuw_scenario_dialog"] = False
                st.rerun()

    st.divider()

    # ─── Scenario tabel ──────────────────────────────────────────────────────
    if not scenario_lijst:
        st.info("Geen scenario's beschikbaar. Maak een nieuw scenario aan.")
    else:
        st.subheader("Beschikbare scenario's")
        
        # Build table data
        tabel_data = []
        for s in scenario_lijst:
            is_actief = s.naam == actief_naam
            is_default = s.naam == default_naam
            
            status = ""
            if is_actief:
                status += "🟢 Actief"
            if is_default:
                status += " ⭐ Standaard"
            
            n_componenten = len(s.componenten)
            n_incidenteel = len(s.incidentele_items)
            
            tabel_data.append({
                "Scenario": s.naam,
                "Beschrijving": s.omschrijving or "—",
                "Status": status,
                "Componenten": n_componenten,
                "Eenmalig": n_incidenteel,
                "Spaargeld": fmt_eur(s.spaargeld_start),
            })
        
        # Display as table
        df = pd.DataFrame(tabel_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()

        # ─── Acties per scenario ─────────────────────────────────────────────
        st.subheader("Acties")
        
        for s in scenario_lijst:
            col_select, col_default, col_edit, col_delete = st.columns(4)
            
            with col_select:
                if st.button(
                    f"Selecteer: {s.naam}",
                    key=f"select_{s.naam}",
                    use_container_width=True,
                ):
                    set_actief_scenario_naam(s.naam)
                    sla_sessie_op()
                    st.rerun()
            
            with col_default:
                is_default = s.naam == default_naam
                if st.button(
                    f"{'✅ Is standaard' if is_default else '⭐ Maak standaard'}",
                    key=f"default_{s.naam}",
                    use_container_width=True,
                ):
                    if not is_default:
                        st.session_state[SCENARIO_DEFAULT_KEY] = s.naam
                        sla_sessie_op()
                        st.success(f"{s.naam} is nu standaard")
                        st.rerun()
            
            with col_edit:
                if st.button(
                    "✏️ Bewerk",
                    key=f"edit_{s.naam}",
                    use_container_width=True,
                ):
                    st.session_state["_edit_scenario_naam"] = s.naam
                    st.session_state["_toon_edit_dialog"] = True
                    st.rerun()
            
            with col_delete:
                if st.button(
                    "🗑️ Verwijder",
                    key=f"delete_{s.naam}",
                    use_container_width=True,
                    disabled=len(scenario_lijst) == 1,  # Altijd minimaal 1 scenario
                ):
                    scenario_lijst = [sc for sc in scenario_lijst if sc.naam != s.naam]
                    st.session_state["scenario_lijst"] = scenario_lijst
                    
                    # Update active if deleted
                    if actief_naam == s.naam and scenario_lijst:
                        set_actief_scenario_naam(scenario_lijst[0].naam)
                    
                    # Update default if deleted
                    if default_naam == s.naam and scenario_lijst:
                        st.session_state[SCENARIO_DEFAULT_KEY] = scenario_lijst[0].naam
                    
                    sla_sessie_op()
                    st.success(f"Scenario '{s.naam}' verwijderd")
                    st.rerun()

    # ─── Edit scenario dialog ────────────────────────────────────────────────
    if st.session_state.get("_toon_edit_dialog"):
        edit_naam = st.session_state.get("_edit_scenario_naam")
        edit_scenario = next((s for s in scenario_lijst if s.naam == edit_naam), None)
        
        if edit_scenario:
            st.divider()
            st.subheader(f"Bewerk: {edit_naam}")
            
            col_form, _ = st.columns([2, 1])
            
            with col_form:
                nieuwe_naam = st.text_input(
                    "Naam",
                    value=edit_scenario.naam,
                    key="edit_scenario_naam",
                )
                nieuwe_beschrijving = st.text_area(
                    "Beschrijving",
                    value=edit_scenario.omschrijving,
                    key="edit_scenario_beschrijving",
                    height=80,
                )
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("✅ Opslaan", key="save_edit_scenario"):
                    if not nieuwe_naam or not nieuwe_naam.strip():
                        st.error("Naam mag niet leeg zijn")
                    elif nieuwe_naam != edit_naam and any(s.naam == nieuwe_naam for s in scenario_lijst):
                        st.error(f"Scenario '{nieuwe_naam}' bestaat al")
                    else:
                        # Update scenario
                        edit_scenario.naam = nieuwe_naam.strip()
                        edit_scenario.omschrijving = nieuwe_beschrijving.strip()
                        edit_scenario.laatst_gewijzigd_op = datetime.now()
                        
                        # Replace in list
                        scenario_lijst = [s for s in scenario_lijst if s.naam != edit_naam]
                        scenario_lijst.append(edit_scenario)
                        st.session_state["scenario_lijst"] = scenario_lijst
                        
                        # Update active/default names if renamed
                        if actief_naam == edit_naam:
                            set_actief_scenario_naam(nieuwe_naam)
                        if default_naam == edit_naam:
                            st.session_state[SCENARIO_DEFAULT_KEY] = nieuwe_naam
                        
                        sla_sessie_op()
                        st.session_state["_toon_edit_dialog"] = False
                        st.success(f"Scenario bijgewerkt")
                        st.rerun()
            
            with col_cancel:
                if st.button("❌ Annuleren", key="cancel_edit_scenario"):
                    st.session_state["_toon_edit_dialog"] = False
                    st.rerun()

    # ─── Volgende knop ──────────────────────────────────────────────────────
    st.divider()
    col_vorige, col_volgende = st.columns(2)
    
    with col_vorige:
        if st.button("⬅️ Vorige"):
            set_huidge_stap(Stap.PENSIOENGEGEVENS, validatie_ok=False)
            st.rerun()
    
    with col_volgende:
        if st.button("Volgende ➡️", use_container_width=True):
            set_huidge_stap(Stap.COMPONENTEN, validatie_ok=True)
            st.rerun()
