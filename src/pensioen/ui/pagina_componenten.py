"""Streamlit-pagina: financiële componenten, vermogen en eenmalige posten (unified view)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import streamlit as st

from pensioen.models.component import CategorieComponent, FinancieelComponent, BeleggingsType
from pensioen.models.vermogensitem import VermogensItem, VermogensType
from pensioen.models.scenario import IncidenteelItem
from pensioen.ui.flow_context import set_huidge_stap
from pensioen.ui.scenario_context import get_actief_scenario
from pensioen.ui.sessie_persistentie import sla_sessie_op
from pensioen.ui import helpers
from pensioen.ui.component_helpers import (
    render_component_form,
    render_incidenteel_form,
    CATEGORIE_LABELS,
)
from pensioen.ui.tile_renderers import (
    render_component_tile,
    render_vermogensitem_tile,
    render_incidenteel_tile,
    render_type_filters,
)
from pensioen.ui.style import format_bedrag


def _injecteer_componenten_stijl() -> None:
    """Voeg een zakelijke, consistente presentatiestijl voor deze pagina toe."""
    st.markdown(
        """
        <style>
        .fin-tegelkop {
            align-items: center;
            display: flex;
            gap: 0.625rem;
            min-height: 2rem;
        }
        .fin-tegelicoon {
            color: #52606d;
            display: inline-flex;
            flex: 0 0 1.5rem;
        }
        .fin-tegelicoon svg {
            height: 1.5rem;
            width: 1.5rem;
        }
        .fin-tegeltitel {
            color: #17212b;
            font-size: 0.95rem;
            font-weight: 650;
            line-height: 1.3;
        }
        .fin-bedrag {
            color: #17212b;
            font-size: 1.45rem;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1.2;
            margin: 0.9rem 0 0.1rem;
        }
        .fin-kerngegeven {
            border-left: 2px solid #6a7b8c;
            color: #344454;
            font-size: 0.85rem;
            font-weight: 600;
            margin: 0.75rem 0;
            padding: 0.2rem 0 0.2rem 0.6rem;
        }
        [class*="st-key-fin_tegel_"],
        [class*="st-key-fin_tegel_"] [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important;
            border-color: #b8c5d1 !important;
            border-radius: 3px !important;
            box-shadow: none !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] {
            color: #52606d;
            line-height: 1.4;
        }
        .st-key-comp_inkuit_pills button,
        .st-key-vermogen_pills button,
        .st-key-eenmalig_pills button {
            background: #edf2f6 !important;
            border: 1px solid #c7d2dc !important;
            border-radius: 3px !important;
            color: #52606d !important;
            font-weight: 550 !important;
            min-height: 2rem !important;
            padding: 0.25rem 0.7rem !important;
        }
        .st-key-comp_inkuit_pills button[aria-selected="true"],
        .st-key-vermogen_pills button[aria-selected="true"],
        .st-key-eenmalig_pills button[aria-selected="true"],
        .st-key-comp_inkuit_pills button[aria-pressed="true"],
        .st-key-vermogen_pills button[aria-pressed="true"],
        .st-key-eenmalig_pills button[aria-pressed="true"] {
            background: #6a89a7 !important;
            border-color: #5c7892 !important;
            color: #ffffff !important;
            font-weight: 650 !important;
        }
        .st-key-comp_inkuit_pills button:hover,
        .st-key-vermogen_pills button:hover,
        .st-key-eenmalig_pills button:hover {
            border-color: #8299ad !important;
        }
        [data-testid="stPopoverBody"] {
            border: 1px solid #c9d2dc !important;
            border-radius: 3px !important;
            box-shadow: 0 4px 12px rgba(23, 33, 43, 0.12) !important;
            padding: 0.25rem !important;
        }
        [data-testid="stPopoverBody"] .stButton > button {
            background: transparent !important;
            border: 0 !important;
            border-radius: 2px !important;
            color: #344454 !important;
            font-size: 0.82rem !important;
            justify-content: flex-start !important;
            min-height: 1.9rem !important;
            padding: 0.25rem 0.5rem !important;
        }
        [data-testid="stPopoverBody"] .stButton > button:hover {
            background: #edf2f6 !important;
            color: #17212b !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


LAYOUT_OPTIES = {
    "1 · Kleur": "kleur",
    "2 · Compact": "compact",
    "3 · Werkblad": "werkblad",
}


def _aantal_tegelkolommen(layout: str) -> int:
    """Geef de informatiedichtheid van de gekozen ontwerpvariant."""
    return 4 if layout == "compact" else 3


def _injecteer_variant_stijl(layout: str) -> None:
    """Pas ook de Streamlit-zijbalk en hoofdindeling zichtbaar aan."""
    variant_css = {
        "kleur": """
            [data-testid="stSidebar"] { background: #123c34 !important; }
            [data-testid="stMainBlockContainer"] { max-width: 1380px; }
            [class*="st-key-fin_tegel_comp_"] {
                border-left: 5px solid #1b8a70 !important;
            }
            [class*="st-key-fin_tegel_verm_"] {
                border-left: 5px solid #3977c3 !important;
            }
            [class*="st-key-fin_tegel_inc_"] {
                border-left: 5px solid #b87520 !important;
            }
        """,
        "compact": """
            [data-testid="stSidebar"] {
                min-width: 13.5rem !important;
                max-width: 13.5rem !important;
                background: #17212b !important;
            }
            [data-testid="stMainBlockContainer"] {
                max-width: 1600px;
                padding-left: 1.25rem;
                padding-right: 1.25rem;
            }
            [class*="st-key-fin_tegel_"] .fin-bedrag {
                font-size: 1.15rem;
                margin-top: 0.45rem;
            }
            [class*="st-key-fin_tegel_"] [data-testid="stVerticalBlock"] {
                gap: 0.35rem !important;
            }
        """,
        "werkblad": """
            [data-testid="stSidebar"] {
                min-width: 15.5rem !important;
                max-width: 15.5rem !important;
                background: #102d29 !important;
                border-right: 1px solid #294943;
            }
            [data-testid="stMainBlockContainer"] {
                max-width: 1500px;
                padding-top: 1.4rem;
            }
            [data-testid="stMetric"] {
                background: #f7faf8;
                border: 1px solid #d9e4df;
                border-radius: 8px;
                padding: 0.75rem 1rem;
            }
            [data-testid="stTabs"] [data-baseweb="tab-list"] {
                gap: 0.35rem;
                border-bottom: 1px solid #d7e1dc;
            }
            [data-testid="stTabs"] button[role="tab"] {
                min-height: 3rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            [data-testid="stTabs"] button[aria-selected="true"] {
                color: #126a58 !important;
                font-weight: 700;
            }
            [class*="st-key-fin_tegel_"] {
                box-shadow: 0 5px 16px rgba(20, 48, 41, 0.06) !important;
            }
        """,
    }
    st.markdown(f"<style>{variant_css[layout]}</style>", unsafe_allow_html=True)


def _update_scenario(scenario, scenario_lijst):
    """Update scenario in lijst en sla op."""
    scenario.laatst_gewijzigd_op = datetime.now()
    for i, sc in enumerate(scenario_lijst):
        if sc.naam == scenario.naam:
            scenario_lijst[i] = scenario
            break
    st.session_state["scenario_lijst"] = scenario_lijst
    sla_sessie_op()


def _plus_jaren(brondatum: date, jaren: int) -> date:
    """Geef een datum n jaren later terug, met veilige fallback op 28 februari."""
    try:
        return brondatum.replace(year=brondatum.year + jaren)
    except ValueError:
        return brondatum.replace(month=2, day=28, year=brondatum.year + jaren)


def toon_componenten_pagina() -> None:
    """Financiële componenten, vermogen en eenmalige posten in één overzichtelijke pagina."""
    _injecteer_componenten_stijl()
    kop_col, keuze_col = st.columns([1.35, 1])
    with kop_col:
        st.header("Financiële planning")
        st.caption("Leg inkomsten, vermogen en eenmalige gebeurtenissen vast.")
    with keuze_col:
        gekozen_layout = st.radio(
            "Vergelijk ontwerp",
            options=list(LAYOUT_OPTIES),
            horizontal=True,
            key="componenten_layout_variant",
        )
    layout = LAYOUT_OPTIES[gekozen_layout]
    _injecteer_variant_stijl(layout)
    
    scenario_lijst = st.session_state.get("scenario_lijst", [])
    actief = get_actief_scenario(scenario_lijst)
    if actief is None:
        st.warning("⚠️ Kies eerst een actief scenario.")
        return
    
    scenario = actief
    st.caption(f"Actief scenario: **{scenario.naam}**")
    
    # Toon info bij afgeleid scenario
    if scenario.parent_naam:
        st.info(
            f"🔗 **Afgeleid scenario** (parent: {scenario.parent_naam})\n\n"
            f"ℹ️ Componenten en vermogensitems worden gekopieerd bij aanmaak. "
            f"Wijzigingen in de parent worden niet automatisch doorgevoerd. "
            f"Voor scenario-parameters (inflatie) werkt inheritance wel automatisch."
        )
    
    heeft_partner = "persoon2" in st.session_state
    persoon2 = st.session_state.get("persoon2")
    
    # Bouw persoon opties - ALTIJD P1/P2/Huishouden gebruiken (niet echte namen)
    # De echte namen worden alleen gebruikt voor weergave in de UI
    persoon_display = helpers.get_persoon_display_mapping()
    
    # Persoon opties: altijd P1, optioneel P2, en Huishouden
    persoon_opties = ["P1"]
    if persoon2:
        persoon_opties.append("P2")
    persoon_opties.append("Huishouden")
    
    # MIGRATIE: Converteer oude persoon namen naar P1/P2/Huishouden
    # Dit zorgt ervoor dat bestaande data werkt met het nieuwe systeem
    migratie_nodig = False
    reverse_mapping = helpers.get_persoon_reverse_mapping()
    
    for comp in scenario.componenten:
        if comp.persoon not in ["P1", "P2", "Huishouden"]:
            # Dit is een oude naam, converteer naar P1/P2
            nieuwe_persoon = reverse_mapping.get(comp.persoon, "P1")
            comp.persoon = nieuwe_persoon
            migratie_nodig = True
    
    for item in scenario.vermogensitems:
        if item.persoon not in ["P1", "P2", "Huishouden"]:
            nieuwe_persoon = reverse_mapping.get(item.persoon, "P1")
            item.persoon = nieuwe_persoon
            migratie_nodig = True
    
    if migratie_nodig:
        _update_scenario(scenario, scenario_lijst)
        st.info("ℹ️ Persoonsgegevens zijn gemigreerd naar het nieuwe formaat (P1/P2).")
        st.rerun()
    
    # Migreer legacy vermogen indien nodig
    if not scenario.vermogensitems and (scenario.spaargeld_start > Decimal("0") or scenario.beleggingen_start > Decimal("0")):
        scenario.migreer_legacy_vermogen()
        _update_scenario(scenario, scenario_lijst)
        st.rerun()
    
    if layout == "werkblad":
        st.markdown("### Financieel overzicht")
        metric_cols = st.columns(3)
        metric_cols[0].metric("Periodieke posten", len(scenario.componenten))
        metric_cols[1].metric("Vermogensonderdelen", len(scenario.vermogensitems))
        metric_cols[2].metric("Eenmalige posten", len(scenario.incidentele_items))
        st.caption(
            "Kies hieronder het onderdeel waaraan je wilt werken. "
            "Zo blijft alleen de informatie voor die taak in beeld."
        )
        tab_inkomen, tab_vermogen, tab_eenmalig = st.tabs(
            ["Inkomsten & uitgaven", "Vermogen", "Eenmalige posten"]
        )
        with tab_inkomen:
            _render_inkomsten_uitgaven_sectie(
                scenario, scenario_lijst, persoon_opties, persoon_display, layout
            )
        with tab_vermogen:
            _render_vermogen_sectie(
                scenario, scenario_lijst, persoon_opties, persoon_display, layout
            )
        with tab_eenmalig:
            _render_eenmalige_posten_sectie(scenario, scenario_lijst, layout)
        return

    st.divider()
    st.subheader("Inkomsten en uitgaven")
    _render_inkomsten_uitgaven_sectie(
        scenario, scenario_lijst, persoon_opties, persoon_display, layout
    )

    st.divider()
    st.subheader("Vermogen en bezittingen")
    _render_vermogen_sectie(
        scenario, scenario_lijst, persoon_opties, persoon_display, layout
    )

    st.divider()
    st.subheader("Eenmalige ontvangsten en uitgaven")
    _render_eenmalige_posten_sectie(scenario, scenario_lijst, layout)


# ==============================================================================
# SECTIE 1: INKOMSTEN & UITGAVEN
# ==============================================================================

def _render_inkomsten_uitgaven_sectie(
    scenario, scenario_lijst, persoon_opties, persoon_display, layout: str = "kleur"
):
    """Render inkomsten & uitgaven sectie met AOW info en filters."""
    
    # AOW automatische berekening info
    st.markdown("### AOW (automatisch berekend)")
    _render_aow_info()
    
    st.markdown("---")
    st.markdown("### Periodieke inkomsten en uitgaven")
    
    # Filters: categorie en persoon
    col_filter_cat, col_filter_pers = st.columns(2)
    
    with col_filter_cat:
        categorie_filter = [
            ("arbeidsinkomen", "Arbeidsinkomen"),
            ("pensioen", "Pensioen"),
            ("overig_inkomen", "Overig inkomen"),
            ("uitgave", "Uitgaven"),
            ("inhouding", "Inhoudingen"),
        ]
        active_filters = render_type_filters(categorie_filter, "comp_inkuit")
    
    with col_filter_pers:
        # Persoonfilter - toon echte namen maar gebruik P1/P2 intern
        persoon_filter_display = ["Alle personen"] + [persoon_display[p] for p in persoon_opties]
        persoon_filter_selectie = st.multiselect(
            "Filter op persoon:",
            options=persoon_filter_display,
            default=["Alle personen"],
            key="comp_persoon_filter"
        )
        # Map terug naar interne IDs
        if "Alle personen" in persoon_filter_selectie:
            persoon_filter_actief = []
        else:
            # Reverse mapping: echte naam → P1/P2
            reverse_display = {v: k for k, v in persoon_display.items()}
            persoon_filter_actief = [reverse_display.get(naam, naam) for naam in persoon_filter_selectie]
    
    # Maak gefilterde lijsten
    componenten_gefilterd = []
    for comp in scenario.componenten:
        # Check categorie filter
        cat_match = False
        if comp.categorie == CategorieComponent.ARBEIDSINKOMEN and "arbeidsinkomen" in active_filters:
            cat_match = True
            cat_key = "arbeidsinkomen"
        elif comp.categorie == CategorieComponent.PENSIOEN_INKOMEN and "pensioen" in active_filters:
            cat_match = True
            cat_key = "pensioen"
        elif comp.categorie == CategorieComponent.OVERIG_INKOMEN and "overig_inkomen" in active_filters:
            cat_match = True
            cat_key = "overig_inkomen"
        elif comp.categorie == CategorieComponent.UITGAVE and "uitgave" in active_filters:
            cat_match = True
            cat_key = "uitgave"
        elif comp.categorie == CategorieComponent.INHOUDING and "inhouding" in active_filters:
            cat_match = True
            cat_key = "inhouding"
        else:
            continue
        
        # Check persoonfilter
        if persoon_filter_actief and comp.persoon not in persoon_filter_actief:
            continue
        
        if cat_match:
            componenten_gefilterd.append((cat_key, comp))
    
    # Toevoeg-knop
    if st.button("➕ Nieuwe component", key="comp_nieuwe"):
        st.session_state["comp_active_mode"] = "add"
        st.session_state["comp_active_idx"] = None
        st.rerun()
    
    # Formulier indien actief
    active_mode = st.session_state.get("comp_active_mode")
    active_idx = st.session_state.get("comp_active_idx")
    
    if active_mode == "add":
        nieuwe_comp = render_component_form(
            section_key="comp",
            mode="add",
            initial=None,
            persoon_opties=persoon_opties,
            persoon_display=persoon_display,
        )
        if nieuwe_comp:
            scenario.componenten.append(nieuwe_comp)
            st.session_state["comp_active_mode"] = None
            _update_scenario(scenario, scenario_lijst)
            st.rerun()
    elif active_mode == "edit" and active_idx is not None:
        gewijzigde_comp = render_component_form(
            section_key="comp",
            mode="edit",
            initial=scenario.componenten[active_idx],
            persoon_opties=persoon_opties,
            persoon_display=persoon_display,
        )
        if gewijzigde_comp:
            scenario.componenten[active_idx] = gewijzigde_comp
            st.session_state["comp_active_mode"] = None
            st.session_state["comp_active_idx"] = None
            _update_scenario(scenario, scenario_lijst)
            st.rerun()
    
    # Verwijder-logica
    if "comp_delete_idx" in st.session_state:
        del_idx = st.session_state["comp_delete_idx"]
        scenario.componenten.pop(del_idx)
        del st.session_state["comp_delete_idx"]
        _update_scenario(scenario, scenario_lijst)
        st.rerun()
    
    # Toon tegels in grid van 3 kolommen
    st.markdown("---")
    if not componenten_gefilterd:
        st.info("Geen componenten gevonden. Klik 'Nieuwe component' om er een toe te voegen.")
    else:
        aantal_kolommen = _aantal_tegelkolommen(layout)
        for row_start in range(0, len(componenten_gefilterd), aantal_kolommen):
            cols = st.columns(aantal_kolommen)
            for col_idx in range(aantal_kolommen):
                i = row_start + col_idx
                if i < len(componenten_gefilterd):
                    cat_key, comp = componenten_gefilterd[i]
                    # Find original index in scenario.componenten
                    orig_idx = scenario.componenten.index(comp)
                    with cols[col_idx]:
                        with st.container(border=True, key=f"fin_tegel_comp_{orig_idx}"):
                            render_component_tile(comp, orig_idx, "comp")


def _laad_aow_bedragen(jaar: int) -> tuple[Decimal | None, Decimal | None]:
    """Laad de maandbedragen voor gehuwden en alleenstaanden uit de jaarconfig."""
    from pensioen.tax.belasting_loader import laad_tarieven

    try:
        config, _ = laad_tarieven(jaar)
        return (
            config.aow_bedrag.gehuwd_of_samenwonend_per_maand,
            config.aow_bedrag.alleenstaande_per_maand,
        )
    except (FileNotFoundError, KeyError, TypeError, ValueError):
        return None, None


def _render_aow_info():
    """Render AOW info sectie."""
    from pensioen.tax.aow_engine import bereken_aow_datum
    
    persoon1 = st.session_state.get("persoon1")
    persoon2 = st.session_state.get("persoon2")
    aow_gehuwd, aow_alleenstaand = _laad_aow_bedragen(date.today().year)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if persoon1:
            aow_datum_p1 = bereken_aow_datum(persoon1.geboortedatum)
            aow_leeftijd_p1 = (aow_datum_p1.year - persoon1.geboortedatum.year)
            
            aow_bedrag = aow_gehuwd if persoon2 else aow_alleenstaand
            bedrag_tekst = f"€ {float(aow_bedrag):,.0f}/maand" if aow_bedrag else "Config niet beschikbaar"
            
            with st.container(border=True):
                st.markdown(f"**{persoon1.naam}**")
                st.caption(
                    f"AOW vanaf {aow_datum_p1.strftime('%d-%m-%Y')} "
                    f"(leeftijd {aow_leeftijd_p1})"
                )
                st.markdown(f"**{bedrag_tekst}**")
                st.caption("Bruto, indicatief")
        else:
            st.caption("Persoon 1 niet ingevuld")
    
    with col2:
        if persoon2:
            aow_datum_p2 = bereken_aow_datum(persoon2.geboortedatum)
            aow_leeftijd_p2 = (aow_datum_p2.year - persoon2.geboortedatum.year)
            
            aow_bedrag = aow_gehuwd
            bedrag_tekst = f"€ {float(aow_bedrag):,.0f}/maand" if aow_bedrag else "Config niet beschikbaar"
            
            with st.container(border=True):
                st.markdown(f"**{persoon2.naam}**")
                st.caption(
                    f"AOW vanaf {aow_datum_p2.strftime('%d-%m-%Y')} "
                    f"(leeftijd {aow_leeftijd_p2})"
                )
                st.markdown(f"**{bedrag_tekst}**")
                st.caption("Bruto, indicatief")
        else:
            st.caption("Partner niet ingevuld")
    
    st.caption("AOW wordt automatisch berekend op basis van geboortedatum. Het bedrag is een indicatie en kan jaarlijks wijzigen.")


# ==============================================================================
# SECTIE 2: VERMOGEN & BEZITTINGEN
# ==============================================================================

def _render_vermogen_sectie(
    scenario, scenario_lijst, persoon_opties, persoon_display, layout: str = "kleur"
):
    """Render vermogen & bezittingen sectie met filters."""
    
    # Filter vermogensitems
    vermogen_filter = [
        ("spaargeld", "Spaargeld"),
        ("beleggingen", "Beleggingen"),
        ("eigen_woning", "Eigen woning"),
        ("hypotheek", "Hypotheek"),
        ("auto", "Auto"),
        ("kunst", "Kunst & Antiek"),
        ("boot", "Boot"),
        ("overig", "Overig"),
    ]
    
    active_filters = render_type_filters(vermogen_filter, "vermogen")
    
    # Filter items
    items_gefilterd = []
    type_mapping = {
        "spaargeld": VermogensType.SPAARGELD,
        "beleggingen": VermogensType.BELEGGINGEN,
        "eigen_woning": VermogensType.EIGEN_WONING,
        "hypotheek": VermogensType.HYPOTHEEK,
        "auto": VermogensType.AUTO,
        "kunst": VermogensType.KUNST,
        "boot": VermogensType.BOOT,
        "overig": VermogensType.OVERIG,
    }
    
    for item in scenario.vermogensitems:
        for filter_key, vtype in type_mapping.items():
            if filter_key in active_filters and item.type == vtype:
                items_gefilterd.append((filter_key, item))
                break
    
    # Toevoeg-knop
    if st.button("➕ Nieuw vermogensitem", key="verm_nieuwe"):
        st.session_state["verm_active_mode"] = "add"
        st.session_state["verm_active_idx"] = None
        st.rerun()

    # Fiscale eigen woning synchroniseren vanuit vermogensitems voor de accountant
    scenario.sync_eigen_woning_uit_vermogensitems()
    
    # Formulier indien actief
    active_mode = st.session_state.get("verm_active_mode")
    active_idx = st.session_state.get("verm_active_idx")
    
    if active_mode == "add":
        _render_vermogensitem_form("add", None, scenario, scenario_lijst)
    elif active_mode == "edit" and active_idx is not None:
        _render_vermogensitem_form("edit", active_idx, scenario, scenario_lijst)
    
    # Verwijder-logica
    if "verm_delete_idx" in st.session_state:
        del_idx = st.session_state["verm_delete_idx"]
        scenario.vermogensitems.pop(del_idx)
        del st.session_state["verm_delete_idx"]
        _update_scenario(scenario, scenario_lijst)
        st.rerun()
    
    # Toon tegels in grid van 3 kolommen
    st.markdown("---")
    if not items_gefilterd:
        st.info("Geen vermogensitems gevonden. Klik 'Nieuw vermogensitem' om er een toe te voegen.")
    else:
        aantal_kolommen = _aantal_tegelkolommen(layout)
        for row_start in range(0, len(items_gefilterd), aantal_kolommen):
            cols = st.columns(aantal_kolommen)
            for col_idx in range(aantal_kolommen):
                i = row_start + col_idx
                if i < len(items_gefilterd):
                    filter_key, item = items_gefilterd[i]
                    # Find original index
                    orig_idx = scenario.vermogensitems.index(item)
                    with cols[col_idx]:
                        with st.container(border=True, key=f"fin_tegel_verm_{orig_idx}"):
                            render_vermogensitem_tile(item, orig_idx, "verm")


def _render_vermogensitem_form(mode: str, edit_idx: int | None, scenario, scenario_lijst):
    """Render formulier voor vermogensitem toevoegen/bewerken."""
    is_edit = edit_idx is not None
    title = "Bewerk vermogensitem" if is_edit else "Nieuw vermogensitem"
    
    if is_edit and edit_idx < len(scenario.vermogensitems):
        item = scenario.vermogensitems[edit_idx]
    else:
        item = None
    
    with st.form(f"verm_form_{mode}"):
        st.markdown(f"### {title}")
        
        # Type selectie
        type_opties = list(VermogensType)
        default_type_idx = 0
        if item and item.type in type_opties:
            default_type_idx = type_opties.index(item.type)
        
        vermogenstype = st.selectbox(
            "Type",
            type_opties,
            format_func=lambda x: x.value.replace("_", " ").title(),
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
            if vermogenstype == VermogensType.EIGEN_WONING:
                aanschafwaarde = st.number_input(
                    "WOZ-waarde (€)",
                    min_value=0,
                    value=int(item.woz_waarde if item and item.woz_waarde is not None else (item.aanschafwaarde if item else 0)),
                    step=5000,
                    help="WOZ-waarde per 1 januari",
                )
            elif vermogenstype == VermogensType.HYPOTHEEK:
                aanschafwaarde = st.number_input(
                    "Resterende schuld (€)",
                    min_value=0,
                    value=int(item.aanschafwaarde) if item else 0,
                    step=1000,
                    help="Resterende hypotheekschuld per 1 januari",
                )
            else:
                aanschafwaarde = st.number_input(
                    "Aanschafwaarde / Huidige waarde (€)",
                    min_value=0,
                    value=int(item.aanschafwaarde) if item else 0,
                    step=1000,
                )
        
        with col2:
            # Label aanpassen voor liquide middelen
            if vermogenstype in (VermogensType.SPAARGELD, VermogensType.BELEGGINGEN):
                groei_label = "Rendement (%/jaar)"
                groei_help = "Verwacht jaarlijks rendement op dit vermogen. Dit wordt ook gebruikt voor cashflow berekeningen."
            elif vermogenstype == VermogensType.HYPOTHEEK:
                groei_label = "Schuldontwikkeling (%/jaar)"
                groei_help = "Negatief = aflossing, positief = schuldtoename"
            else:
                groei_label = "Groei/afschrijving (%/jaar)"
                groei_help = "Positief = waardestijging, negatief = afschrijving"
            
            groei_pct = st.number_input(
                groei_label,
                min_value=-100.0,
                max_value=100.0,
                value=float(item.groei_pct) if item else 0.0,
                step=0.5,
                help=groei_help
            )
            
            # Waarschuwing voor spaargeld/beleggingen
            if vermogenstype in (VermogensType.SPAARGELD, VermogensType.BELEGGINGEN):
                type_label = "sparen" if vermogenstype == VermogensType.SPAARGELD else "beleggen"
                st.caption(f"⚠️ Dit rendement wordt ook gebruikt voor alle cashflow berekeningen van {type_label}")
        
        # Datums
        col1, col2 = st.columns(2)
        with col1:
            aanschafdatum = st.date_input(
                "Aanschafdatum (optioneel)",
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
        
        # Type-specifieke velden
        if vermogenstype == VermogensType.EIGEN_WONING:
            woz_jaarlijkse_stijging_pct = st.number_input(
                "Jaarlijkse waardestijging (%/jaar)",
                min_value=-100.0,
                max_value=100.0,
                value=float(item.woz_jaarlijkse_stijging_pct) if item else 2.0,
                step=0.5,
                help="Verwachte jaarlijkse stijging van de WOZ-waarde",
            )
            st.info("ℹ️ Eigen woning is vrijgesteld van box 3 (eigenwoningforfait box 1)")
            box3_belast = False
        elif vermogenstype == VermogensType.HYPOTHEEK:
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                is_primaire_woning = st.checkbox(
                    "Primaire woning",
                    value=item.is_primaire_woning if item and item.is_primaire_woning is not None else True,
                    help="Vink aan als dit de primaire woning betreft",
                )
            with col_h2:
                hypotheekrente_pct = st.number_input(
                    "Hypotheekrente (%/jaar)",
                    min_value=0.0,
                    max_value=20.0,
                    value=float(item.hypotheekrente_pct) if item and item.hypotheekrente_pct is not None else 3.5,
                    step=0.1,
                    help="Jaarlijkse hypotheekrente",
                )
            einddatum_aftrekbaarheid = st.date_input(
                "Einddatum renteaftrek",
                value=item.einddatum_aftrekbaarheid if item and item.einddatum_aftrekbaarheid else _plus_jaren(date.today(), 30),
                help="Datum waarna rente niet langer aftrekbaar is",
            )
            box3_belast = False
            st.info("ℹ️ Hypotheekschuld is fiscale invoer voor box 1 en telt niet mee in box 3")
        else:
            box3_belast = st.checkbox(
                "Box 3 belast",
                value=item.box3_belast if item else True,
                help="Vink uit voor vrijgestelde items (bijv. recreatievaartuig)"
            )
        
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
                extra_kwargs = {}
                if vermogenstype == VermogensType.EIGEN_WONING:
                    extra_kwargs["woz_waarde"] = Decimal(str(aanschafwaarde))
                    extra_kwargs["woz_jaarlijkse_stijging_pct"] = Decimal(str(woz_jaarlijkse_stijging_pct))
                elif vermogenstype == VermogensType.HYPOTHEEK:
                    extra_kwargs["is_primaire_woning"] = is_primaire_woning
                    extra_kwargs["hypotheekrente_pct"] = Decimal(str(hypotheekrente_pct))
                    extra_kwargs["einddatum_aftrekbaarheid"] = einddatum_aftrekbaarheid

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
                    **extra_kwargs,
                )
                
                if is_edit:
                    scenario.vermogensitems[edit_idx] = nieuw_item
                else:
                    scenario.vermogensitems.append(nieuw_item)
                
                _update_scenario(scenario, scenario_lijst)
                st.session_state["verm_active_mode"] = None
                st.session_state["verm_active_idx"] = None
                st.success("✅ Vermogensitem opgeslagen")
                st.rerun()
                
            except ValueError as e:
                st.error(f"❌ Validatiefout: {e}")
        
        if cancel:
            st.session_state["verm_active_mode"] = None
            st.session_state["verm_active_idx"] = None
            st.rerun()


# ==============================================================================
# SECTIE 3: EENMALIGE POSTEN
# ==============================================================================

def _render_eenmalige_posten_sectie(
    scenario, scenario_lijst, layout: str = "kleur"
):
    """Render eenmalige ontvangsten & uitgaven sectie."""
    
    # Filter
    eenmalig_filter = [
        ("ontvangst", "Ontvangsten"),
        ("uitgave", "Uitgaven"),
    ]
    
    active_filters = render_type_filters(eenmalig_filter, "eenmalig")
    
    # Filter items
    items_gefilterd = []
    for item in scenario.incidentele_items:
        if item.bedrag >= 0 and "ontvangst" in active_filters:
            items_gefilterd.append(("ontvangst", item))
        elif item.bedrag < 0 and "uitgave" in active_filters:
            items_gefilterd.append(("uitgave", item))
    
    # Sorteer op datum
    items_gefilterd.sort(key=lambda x: x[1].datum)
    
    # Toevoeg-knop
    if st.button("➕ Nieuwe eenmalige post", key="inc_nieuwe"):
        st.session_state["inc_active_mode"] = "add"
        st.session_state["inc_active_idx"] = None
        st.rerun()
    
    # Formulier indien actief
    active_mode = st.session_state.get("inc_active_mode")
    active_idx = st.session_state.get("inc_active_idx")
    
    if active_mode == "add":
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
    elif active_mode == "edit" and active_idx is not None:
        gewijzigd_item = render_incidenteel_form(
            section_key="inc",
            mode="edit",
            initial=scenario.incidentele_items[active_idx],
        )
        if gewijzigd_item:
            scenario.incidentele_items[active_idx] = gewijzigd_item
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
    
    # Toon tegels in grid van 3 kolommen
    st.markdown("---")
    if not items_gefilterd:
        st.info("Geen eenmalige posten gevonden. Klik 'Nieuwe eenmalige post' om er een toe te voegen.")
    else:
        aantal_kolommen = _aantal_tegelkolommen(layout)
        for row_start in range(0, len(items_gefilterd), aantal_kolommen):
            cols = st.columns(aantal_kolommen)
            for col_idx in range(aantal_kolommen):
                i = row_start + col_idx
                if i < len(items_gefilterd):
                    filter_key, item = items_gefilterd[i]
                    # Find original index
                    orig_idx = scenario.incidentele_items.index(item)
                    with cols[col_idx]:
                        with st.container(border=True, key=f"fin_tegel_inc_{orig_idx}"):
                            render_incidenteel_tile(item, orig_idx, "inc")
