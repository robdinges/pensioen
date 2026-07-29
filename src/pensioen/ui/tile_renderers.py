"""Modern tile-based renderers for components, vermogensitems and incidentele items."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from html import escape
from pathlib import Path

import streamlit as st

from pensioen.models.component import FinancieelComponent, CategorieComponent
from pensioen.models.vermogensitem import VermogensItem, VermogensType
from pensioen.models.scenario import IncidenteelItem
from pensioen.ui.style import badge_html, format_bedrag
from pensioen.ui.helpers import get_persoon_display_naam
from pensioen.ui.component_helpers import (
    CATEGORIE_LABELS,
    FREQUENTIE_LABELS,
    BEDRAG_TYPE_LABELS,
)

_TEGELICOON_MAP = Path(__file__).resolve().parents[3] / "docs" / "assets" / "icons" / "financiele-tegels"
_TEGELICOON_BESTANDEN = {
    "arbeidsinkomen": "arbeidsinkomen.svg",
    "pensioen_inkomen": "pensioeninkomen.svg",
    "overig_inkomen": "overig_inkomen.svg",
    "uitgave": "uitgave.svg",
    "inhouding": "inhouding.svg",
    "spaargeld": "sparen.svg",
    "beleggingen": "beleggen.svg",
    "eigen_woning": "eigen_woning.svg",
    "hypotheek": "hypotheek.svg",
    "auto": "auto.svg",
    "kunst": "kunst.svg",
    "boot": "boot.svg",
    "overig": "overig.svg",
}


def tegelicoon_pad(sleutel: str) -> Path:
    """Geef het icoonpad voor een financiële tegel, met een generieke fallback."""
    bestandsnaam = _TEGELICOON_BESTANDEN.get(sleutel, "overig.svg")
    return _TEGELICOON_MAP / bestandsnaam


def _render_tegelkop(titel: str, icoonsleutel: str) -> None:
    """Render een rustig, monochroom icoon naast de titel van een tegel."""
    icoon = tegelicoon_pad(icoonsleutel).read_text(encoding="utf-8")
    st.markdown(
        f'<div class="fin-tegelkop">'
        f'<span class="fin-tegelicoon">{icoon}</span>'
        f'<span class="fin-tegeltitel">{escape(titel)}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )


# ==============================================================================
# Tile Rendering Functions (zakelijke tegels met kebabmenu)
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
    # Container met tile styling
    with st.container():
        # Header met titel en kebab menu
        col_title, col_menu = st.columns([4, 1])
        
        with col_title:
            _render_tegelkop(comp.omschrijving, comp.categorie.value)
        
        with col_menu:
            with st.popover("⋮", use_container_width=False):
                if st.button("Bewerken", key=f"{section_key}_edit_{idx}", use_container_width=True):
                    st.session_state[f"{section_key}_active_idx"] = idx
                    st.session_state[f"{section_key}_active_mode"] = "edit"
                    st.rerun()
                if st.button("Verwijderen", key=f"{section_key}_del_{idx}", use_container_width=True, type="secondary"):
                    st.session_state[f"{section_key}_delete_idx"] = idx
                    st.rerun()
        
        # Bedrag en frequentie
        bedrag_str = format_bedrag(float(comp.bedrag))
        freq_label = FREQUENTIE_LABELS[comp.frequentie]
        st.markdown(f'<p class="fin-bedrag">{bedrag_str}</p>', unsafe_allow_html=True)
        st.caption(
            f"{CATEGORIE_LABELS[comp.categorie]} • "
            f"{get_persoon_display_naam(comp.persoon)}"
        )
        st.caption(f"{freq_label} • {BEDRAG_TYPE_LABELS[comp.bedrag_type]}")
        
        # Extra details
        details = []
        if comp.begindatum:
            details.append(f"Vanaf {comp.begindatum.strftime('%d-%m-%Y')}")
        if comp.einddatum:
            details.append(f"Tot {comp.einddatum.strftime('%d-%m-%Y')}")
        if comp.groei_pct and comp.groei_pct > 0:
            details.append(f"Groei {float(comp.groei_pct):.1f}% per jaar")
        
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
            _render_tegelkop(item.omschrijving, item.type.value)
        
        with col_menu:
            with st.popover("⋮", use_container_width=False):
                if st.button("Bewerken", key=f"{section_key}_edit_{idx}", use_container_width=True):
                    st.session_state[f"{section_key}_active_idx"] = idx
                    st.session_state[f"{section_key}_active_mode"] = "edit"
                    st.rerun()
                if st.button("Verwijderen", key=f"{section_key}_del_{idx}", use_container_width=True, type="secondary"):
                    st.session_state[f"{section_key}_delete_idx"] = idx
                    st.rerun()
        
        # Waarde (groot en prominent)
        st.markdown(
            f'<p class="fin-bedrag">{format_bedrag(float(waarde))}</p>',
            unsafe_allow_html=True,
        )
        
        # Type en persoon
        type_label = item.type.value.replace("_", " ").title()
        st.caption(f"{type_label} • {get_persoon_display_naam(item.persoon)}")

        if item.type == VermogensType.EIGEN_WONING:
            st.caption(f"WOZ {format_bedrag(float(item.woz_waarde or item.aanschafwaarde))}")
            if item.woz_jaarlijkse_stijging_pct != Decimal("0"):
                st.caption(f"WOZ-stijging {float(item.woz_jaarlijkse_stijging_pct):.1f}% per jaar")
        elif item.type == VermogensType.HYPOTHEEK:
            st.caption(f"Schuld {format_bedrag(float(abs(waarde)))}")
            if item.hypotheekrente_pct is not None:
                st.caption(f"Rente {float(item.hypotheekrente_pct):.2f}% per jaar")
            if item.einddatum_aftrekbaarheid is not None:
                st.caption(f"Aftrek t/m {item.einddatum_aftrekbaarheid.strftime('%d-%m-%Y')}")
        
        # RENDEMENT/GROEI - PROMINENT voor liquide middelen
        if item.type in (VermogensType.SPAARGELD, VermogensType.BELEGGINGEN):
            st.markdown(
                f'<p class="fin-kerngegeven">Rendement '
                f"{float(item.groei_pct):.1f}% per jaar</p>",
                unsafe_allow_html=True,
            )
        elif item.groei_pct != Decimal("0"):
            groei_label = "Waardestijging" if item.groei_pct > 0 else "Afschrijving"
            st.caption(f"{groei_label}: {float(item.groei_pct):+.1f}% per jaar")
        
        # Box 3 status
        box3_label = "Box 3 belast" if item.box3_belast else "Box 3 vrijgesteld"
        st.caption(box3_label)
        
        # Verkoopdatum indien aanwezig
        if item.verkoopdatum:
            st.caption(f"Verkoop: {item.verkoopdatum.strftime('%d-%m-%Y')}")


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
            icoonsleutel = "overig" if is_ontvangst else "uitgave"
            _render_tegelkop(item.omschrijving or "(geen omschrijving)", icoonsleutel)
        
        with col_menu:
            with st.popover("⋮", use_container_width=False):
                if st.button("Bewerken", key=f"{section_key}_edit_{idx}", use_container_width=True):
                    st.session_state[f"{section_key}_active_idx"] = idx
                    st.session_state[f"{section_key}_active_mode"] = "edit"
                    st.rerun()
                if st.button("Verwijderen", key=f"{section_key}_del_{idx}", use_container_width=True, type="secondary"):
                    st.session_state[f"{section_key}_delete_idx"] = idx
                    st.rerun()
        
        # Bedrag (met kleur)
        bedrag_str = format_bedrag(float(item.bedrag))
        st.markdown(f'<p class="fin-bedrag">{bedrag_str}</p>', unsafe_allow_html=True)
        
        # Datum
        st.caption(item.datum.strftime("%d-%m-%Y"))
        
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
