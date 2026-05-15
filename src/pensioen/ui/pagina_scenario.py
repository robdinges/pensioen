"""Streamlit-pagina: scenario-beheer met tabel-layout."""

from __future__ import annotations

from datetime import datetime
import streamlit as st

from pensioen.models.scenario import Scenario
from pensioen.ui.flow_context import Stap, set_huidge_stap
from pensioen.ui.scenario_context import (
    SCENARIO_DEFAULT_KEY,
    get_actief_scenario_naam,
    set_actief_scenario_naam,
)
from pensioen.ui.sessie_persistentie import sla_sessie_op


def toon_scenario_pagina() -> None:
    """Toon scenario's in tabel met CRUD-acties en volgende-knop."""
    st.header("Scenario's")

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

    # ─── Scenario lijst ──────────────────────────────────────────────────────
    if not scenario_lijst:
        st.info("Geen scenario's beschikbaar. Maak een nieuw scenario aan.")
    else:
        st.subheader("Beschikbare scenario's")

        scenario_namen = [s.naam for s in scenario_lijst]
        default_index = scenario_namen.index(default_naam) if default_naam in scenario_namen else 0

        gekozen_default = st.radio(
            "Standaard scenario",
            options=scenario_namen,
            index=default_index,
            key="scenario_default_radio",
            horizontal=True,
        )
        if gekozen_default != default_naam:
            st.session_state[SCENARIO_DEFAULT_KEY] = gekozen_default
            default_naam = gekozen_default
            sla_sessie_op()

        st.divider()

        header_cols = st.columns([0.7, 2.2, 4.2, 1.3, 0.8, 0.8, 0.8])
        header_cols[0].markdown("**Actief**")
        header_cols[1].markdown("**Scenario**")
        header_cols[2].markdown("**Beschrijving**")
        header_cols[3].markdown("**Standaard**")
        header_cols[4].markdown("**Ga**")
        header_cols[5].markdown("**Bewerk**")
        header_cols[6].markdown("**Verwijder**")

        for s in scenario_lijst:
            is_actief = s.naam == actief_naam
            is_default = s.naam == default_naam

            cols = st.columns([0.7, 2.2, 4.2, 1.3, 0.8, 0.8, 0.8])

            with cols[0]:
                st.markdown("🟢" if is_actief else "⚪")

            with cols[1]:
                st.write(s.naam)

            with cols[2]:
                st.write(s.omschrijving or "—")

            with cols[3]:
                st.write("Ja" if is_default else "Nee")

            with cols[4]:
                if st.button("➡", key=f"select_{s.naam}", help="Maak actief"):
                    set_actief_scenario_naam(s.naam)
                    sla_sessie_op()
                    st.rerun()

            with cols[5]:
                if st.button("✏", key=f"edit_{s.naam}", help="Bewerk scenario"):
                    st.session_state["_edit_scenario_naam"] = s.naam
                    st.session_state["_toon_edit_dialog"] = True
                    st.rerun()

            with cols[6]:
                if st.button(
                    "🗑",
                    key=f"delete_{s.naam}",
                    help="Verwijder scenario",
                    disabled=len(scenario_lijst) == 1,
                ):
                    scenario_lijst = [sc for sc in scenario_lijst if sc.naam != s.naam]
                    st.session_state["scenario_lijst"] = scenario_lijst

                    if actief_naam == s.naam and scenario_lijst:
                        set_actief_scenario_naam(scenario_lijst[0].naam)

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
                        st.success("Scenario bijgewerkt")
                        st.rerun()
            
            with col_cancel:
                if st.button("❌ Annuleren", key="cancel_edit_scenario"):
                    st.session_state["_toon_edit_dialog"] = False
                    st.rerun()

    # ─── Volgende knop ──────────────────────────────────────────────────────
    st.divider()
    col_vorige, col_volgende = st.columns(2)
    
    with col_vorige:
        if st.button("← Vorige"):
            set_huidge_stap(Stap.PENSIOENGEGEVENS, validatie_ok=False)
            st.rerun()
    
    with col_volgende:
        if st.button("Volgende →", use_container_width=True):
            set_huidge_stap(Stap.COMPONENTEN, validatie_ok=True)
            st.rerun()
