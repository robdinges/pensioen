"""Modern tile-based renderers for components, vermogensitems and incidentele items."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import streamlit as st

from pensioen.models.component import FinancieelComponent, CategorieComponent
from pensioen.models.vermogensitem import VermogensItem, VermogensType
from pensioen.models.scenario import IncidenteelItem
from pensioen.ui.style import COLORS, ICONS, badge_html, format_bedrag
from pensioen.ui.component_helpers import (
    CATEGORIE_LABELS,
    FREQUENTIE_LABELS,
    BEDRAG_TYPE_LABELS,
    BELEGGINGS_TYPE_LABELS,
)


# ==============================================================================
# Tile Rendering Functions (Modern 4-koloms layout met kebab menu)
# ==============================================================================

def render_component_tile(
    comp: FinancieelComponent,
    idx: int,
    section_key: str,
) -> None:
    """
    Render één FinancieelComponent als moderne tile met kebab menu.
    
    Tile bevat:
    - Omschrijving (bold)
    - Bedrag / frequentie
    - Persoon • Type badges
    - Extra details (datum, groei)
    - Kebab menu (⋮) met bewerken/verwijderen
    
    Args:
        comp: FinancieelComponent object.
        idx: Index in de lijst.
        section_key: Unieke sectie-identifier voor state keys.
    """
    # Bepaal badge type
    if comp.categorie.value in ("arbeidsinkomen", "pensioen_inkomen", "overig_inkomen"):
        badge_type = "inkomen"
    elif comp.categorie.value in ("uitgave", "inhouding"):
        badge_type = "uitgave"
    else:
        badge_type = "neutraal"
    
    # Container met tile styling
    with st.container():
        # Header met titel en kebab menu
        col_title, col_menu = st.columns([4, 1])
        
        with col_title:
            st.markdown(f"**{comp.omschrijving}**")
        
        with col_menu:
            with st.popover("⋮", use_container_width=False):
                if st.button("✏️ Bewerken", key=f"{section_key}_edit_{idx}", use_container_width=True):
                    st.session_state[f"{section_key}_active_idx"] = idx
                    st.session_state[f"{section_key}_active_mode"] = "edit"
                    st.rerun()
                if st.button("🗑️ Verwijderen", key=f"{section_key}_del_{idx}", use_container_width=True, type="secondary"):
                    st.session_state[f"{section_key}_delete_idx"] = idx
                    st.rerun()
        
        # Bedrag en frequentie
        bedrag_str = format_bedrag(float(comp.bedrag))
        freq_label = FREQUENTIE_LABELS[comp.frequentie]
        st.markdown(f"### {bedrag_str}")
        st.caption(f"per {freq_label.lower()}")
        
        # Badges
        type_badge = badge_html(BEDRAG_TYPE_LABELS[comp.bedrag_type], badge_type="neutraal", small=True)
        cat_badge = badge_html(CATEGORIE_LABELS[comp.categorie], badge_type=badge_type, small=True)
        belegg_badge = badge_html(BELEGGINGS_TYPE_LABELS[comp.beleggings_type], badge_type="vermogen", small=True)
        
        st.markdown(
            f"{comp.persoon} • {type_badge} {cat_badge} {belegg_badge}",
            unsafe_allow_html=True
        )
        
        # Extra details
        details = []
        if comp.begindatum:
            details.append(f"📅 Vanaf {comp.begindatum.strftime('%d-%m-%Y')}")
        if comp.einddatum:
            details.append(f"Tot {comp.einddatum.strftime('%d-%m-%Y')}")
        if comp.groei_pct and comp.groei_pct > 0:
            details.append(f"📈 Groei {float(comp.groei_pct):.1f}%/jr")
        
        if details:
            st.caption(" • ".join(details))


def render_vermogensitem_tile(
    item: VermogensItem,
    idx: int,
    section_key: str,
) -> None:
    """
    Render één VermogensItem als moderne tile met kebab menu.
    
    Tile bevat:
    - Omschrijving (bold)
    - Huidige waarde (groot)
    - Type • Persoon
    - Rendement/groei percentage (PROMINENT voor SPAARGELD/BELEGGINGEN)
    - Box 3 status
    - Kebab menu (⋮) met bewerken/verwijderen
    
    Args:
        item: VermogensItem object.
        idx: Index in de lijst.
        section_key: Unieke sectie-identifier voor state keys.
    """
    peildatum = date.today()
    waarde = item.waarde_op_datum(peildatum)
    
    # Container met tile styling
    with st.container():
        # Header met titel en kebab menu
        col_title, col_menu = st.columns([4, 1])
        
        with col_title:
            st.markdown(f"**{item.omschrijving}**")
        
        with col_menu:
            with st.popover("⋮", use_container_width=False):
                if st.button("✏️ Bewerken", key=f"{section_key}_edit_{idx}", use_container_width=True):
                    st.session_state[f"{section_key}_active_idx"] = idx
                    st.session_state[f"{section_key}_active_mode"] = "edit"
                    st.rerun()
                if st.button("🗑️ Verwijderen", key=f"{section_key}_del_{idx}", use_container_width=True, type="secondary"):
                    st.session_state[f"{section_key}_delete_idx"] = idx
                    st.rerun()
        
        # Waarde (groot en prominent)
        st.markdown(f"### {format_bedrag(float(waarde))}")
        
        # Type en persoon
        type_label = item.type.value.replace("_", " ").title()
        st.caption(f"{type_label} • {item.persoon}")
        
        # RENDEMENT/GROEI - PROMINENT voor liquide middelen
        if item.type in (VermogensType.SPAARGELD, VermogensType.BELEGGINGEN):
            # Rendement prominent tonen voor spaargeld en beleggingen
            rendement_kleur = COLORS["vermogen"].primary
            st.markdown(
                f"<div style='background-color: {COLORS['vermogen'].bg}; padding: 0.5rem; border-radius: 0.375rem; margin: 0.5rem 0;'>"
                f"<span style='color: {rendement_kleur}; font-weight: 600;'>📊 Rendement: {float(item.groei_pct):.1f}% /jaar</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        elif item.groei_pct != Decimal("0"):
            # Groei/afschrijving voor andere items
            groei_label = "📈 Waardestijging" if item.groei_pct > 0 else "📉 Afschrijving"
            st.caption(f"{groei_label}: {float(item.groei_pct):+.1f}% /jaar")
        
        # Box 3 status
        box3_icon = "✅" if item.box3_belast else "❌"
        box3_label = "Box 3 belast" if item.box3_belast else "Box 3 vrijgesteld"
        st.caption(f"{box3_icon} {box3_label}")
        
        # Verkoopdatum indien aanwezig
        if item.verkoopdatum:
            st.caption(f"🔚 Verkoop: {item.verkoopdatum.strftime('%d-%m-%Y')}")


def render_incidenteel_tile(
    item: IncidenteelItem,
    idx: int,
    section_key: str,
) -> None:
    """
    Render één IncidenteelItem als moderne tile met kebab menu.
    
    Tile bevat:
    - Omschrijving (bold)
    - Bedrag (groot, groen voor ontvangst, rood voor uitgave)
    - Datum
    - Type badge (ontvangst/uitgave)
    - Kebab menu (⋮) met bewerken/verwijderen
    
    Args:
        item: IncidenteelItem object.
        idx: Index in de lijst.
        section_key: Unieke sectie-identifier voor state keys.
    """
    is_ontvangst = item.bedrag >= 0
    badge_type = "ontvangst" if is_ontvangst else "uitgave_eenmalig"
    
    # Container met tile styling
    with st.container():
        # Header met titel en kebab menu
        col_title, col_menu = st.columns([4, 1])
        
        with col_title:
            st.markdown(f"**{item.omschrijving or '(geen omschrijving)'}**")
        
        with col_menu:
            with st.popover("⋮", use_container_width=False):
                if st.button("✏️ Bewerken", key=f"{section_key}_edit_{idx}", use_container_width=True):
                    st.session_state[f"{section_key}_active_idx"] = idx
                    st.session_state[f"{section_key}_active_mode"] = "edit"
                    st.rerun()
                if st.button("🗑️ Verwijderen", key=f"{section_key}_del_{idx}", use_container_width=True, type="secondary"):
                    st.session_state[f"{section_key}_delete_idx"] = idx
                    st.rerun()
        
        # Bedrag (met kleur)
        bedrag_str = format_bedrag(float(item.bedrag))
        bedrag_kleur = COLORS["ontvangst"].primary if is_ontvangst else COLORS["uitgave_eenmalig"].primary
        st.markdown(f"<h3 style='color: {bedrag_kleur}; margin: 0;'>{bedrag_str}</h3>", unsafe_allow_html=True)
        
        # Datum
        st.caption(f"📅 {item.datum.strftime('%d-%m-%Y')}")
        
        # Type badge
        type_label = "Ontvangst" if is_ontvangst else "Uitgave"
        type_badge_html = badge_html(type_label, badge_type=badge_type, small=True)
        st.markdown(type_badge_html, unsafe_allow_html=True)


# ==============================================================================
# Filter Button Helpers
# ==============================================================================

def render_type_filters(
    filter_types: list[tuple[str, str]],
    section_key: str,
    default_active: list[str] | None = None,
) -> list[str]:
    """
    Render filter buttons voor component types met pills interface.
    
    Args:
        filter_types: List van (internal_key, display_label) tuples.
        section_key: Unieke sectie-identifier voor state persistence.
        default_active: Standaard actieve filters (None = allemaal actief).
    
    Returns:
        Lijst van actieve filter keys.
    """
    state_key = f"{section_key}_active_filters"
    
    # Initialize state
    if state_key not in st.session_state:
        st.session_state[state_key] = default_active or [k for k, _ in filter_types]
    
    # Render pills
    labels = [label for _, label in filter_types]
    selected_labels = st.pills(
        "Filter:",
        labels,
        selection_mode="multi",
        default=labels,
        key=f"{section_key}_pills",
        label_visibility="collapsed"
    )
    
    # Convert labels back to keys
    label_to_key = {label: key for key, label in filter_types}
    active_keys = [label_to_key[label] for label in selected_labels if label in label_to_key]
    
    # Update state
    st.session_state[state_key] = active_keys
    
    return active_keys
