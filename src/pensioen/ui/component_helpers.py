"""Helper functions for component and pensioen record management."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from pensioen.models.component import BedragType, BeleggingsType, CategorieComponent, FinancieelComponent, Frequentie
from pensioen.models.pensioen_record import PensioenRecord


# Component category and type labels
CATEGORIE_LABELS = {
    CategorieComponent.ARBEIDSINKOMEN: "Arbeidsinkomen",
    CategorieComponent.PENSIOEN_INKOMEN: "Pensioen inkomen",
    CategorieComponent.OVERIG_INKOMEN: "Overig inkomen",
    CategorieComponent.UITGAVE: "Uitgave",
    CategorieComponent.INHOUDING: "Inhouding",
}
CATEGORIE_OPTIES = list(CATEGORIE_LABELS.values())

FREQUENTIE_LABELS = {
    Frequentie.MAANDELIJKS: "Maandelijks",
    Frequentie.KWARTAAL: "Per kwartaal",
    Frequentie.HALFJAARLIJKS: "Halfjaarlijks",
    Frequentie.JAARLIJKS: "Jaarlijks",
    Frequentie.EENMALIG: "Eenmalig",
}
FREQUENTIE_OPTIES = list(FREQUENTIE_LABELS.values())

BEDRAG_TYPE_LABELS = {
    BedragType.BRUTO: "Bruto",
    BedragType.NETTO: "Netto",
}
BEDRAG_TYPE_OPTIES = list(BEDRAG_TYPE_LABELS.values())

BELEGGINGS_TYPE_LABELS = {
    BeleggingsType.SPAREN: "Sparen",
    BeleggingsType.BELEGGEN: "Beleggen",
}
BELEGGINGS_TYPE_OPTIES = list(BELEGGINGS_TYPE_LABELS.values())


def maak_lege_component_df() -> pd.DataFrame:
    """Create an empty component DataFrame."""
    return pd.DataFrame({
        "omschrijving": pd.Series(dtype="object"),
        "categorie": pd.Series(dtype="object"),
        "persoon": pd.Series(dtype="object"),
        "bedrag_type": pd.Series(dtype="object"),
        "bedrag": pd.Series(dtype="float64"),
        "frequentie": pd.Series(dtype="object"),
        "begindatum": pd.Series(dtype="object"),
        "einddatum": pd.Series(dtype="object"),
        "groei_pct": pd.Series(dtype="float64"),
        "beleggings_type": pd.Series(dtype="object"),
    })


def componenten_naar_df(componenten: list[FinancieelComponent]) -> pd.DataFrame:
    """Convert a list of components to an editable DataFrame."""
    rijen = []
    for c in componenten:
        rijen.append({
            "omschrijving": c.omschrijving,
            "categorie": CATEGORIE_LABELS[c.categorie],
            "persoon": c.persoon,
            "bedrag_type": BEDRAG_TYPE_LABELS[c.bedrag_type],
            "bedrag": float(c.bedrag),
            "frequentie": FREQUENTIE_LABELS[c.frequentie],
            "begindatum": c.begindatum.strftime("%d-%m-%Y") if c.begindatum else "",
            "einddatum": c.einddatum.strftime("%d-%m-%Y") if c.einddatum else "",
            "groei_pct": float(c.groei_pct),
            "beleggings_type": BELEGGINGS_TYPE_LABELS[c.beleggings_type],
        })
    if not rijen:
        return maak_lege_component_df()
    return pd.DataFrame(rijen)


def df_naar_componenten(df: pd.DataFrame) -> list[FinancieelComponent]:
    """Convert a DataFrame back to FinancieelComponent objects."""
    cat_inv = {v: k for k, v in CATEGORIE_LABELS.items()}
    freq_inv = {v: k for k, v in FREQUENTIE_LABELS.items()}
    bedrag_type_inv = {v: k for k, v in BEDRAG_TYPE_LABELS.items()}
    beleggings_type_inv = {v: k for k, v in BELEGGINGS_TYPE_LABELS.items()}

    componenten = []
    for _, rij in df.iterrows():
        omschrijving = str(rij.get("omschrijving", "")).strip()
        if not omschrijving:
            continue
        bedrag_raw = rij.get("bedrag", 0)
        try:
            bedrag = Decimal(str(bedrag_raw))
        except (InvalidOperation, TypeError):
            bedrag = Decimal("0")

        cat_label = str(rij.get("categorie", "Arbeidsinkomen"))
        freq_label = str(rij.get("frequentie", "Maandelijks"))
        categorie = cat_inv.get(cat_label, CategorieComponent.ARBEIDSINKOMEN)
        frequentie = freq_inv.get(freq_label, Frequentie.MAANDELIJKS)
        bedrag_type_label = str(rij.get("bedrag_type", "Bruto"))
        bedrag_type = bedrag_type_inv.get(bedrag_type_label, BedragType.BRUTO)

        beleggings_type_label = str(rij.get("beleggings_type", "Sparen"))
        beleggings_type = beleggings_type_inv.get(beleggings_type_label, BeleggingsType.SPAREN)

        persoon = str(rij.get("persoon", "P1"))

        def parse_datum(waarde: str | None) -> date | None:
            """Parse dd-mm-yyyy or ISO date."""
            if not waarde or str(waarde).strip() == "":
                return None
            s = str(waarde).strip()
            for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
                try:
                    return date.fromisoformat(s) if fmt == "%Y-%m-%d" else datetime.strptime(s, fmt).date()
                except ValueError:
                    continue
            return None

        begindatum = parse_datum(rij.get("begindatum"))
        einddatum = parse_datum(rij.get("einddatum"))

        try:
            groei_pct = Decimal(str(rij.get("groei_pct", 0)))
        except (InvalidOperation, TypeError):
            groei_pct = Decimal("0")

        try:
            comp = FinancieelComponent(
                omschrijving=omschrijving,
                categorie=categorie,
                persoon=persoon,
                bedrag_type=bedrag_type,
                bedrag=bedrag,
                frequentie=frequentie,
                begindatum=begindatum,
                einddatum=einddatum,
                groei_pct=groei_pct,
                beleggings_type=beleggings_type,
            )
            componenten.append(comp)
        except (ValueError, TypeError):
            pass
    return componenten


# ============================================================================
# Card en Form Renderers (herbruikbaar voor nieuwe UI)
# ============================================================================

def render_component_card(
    comp: FinancieelComponent,
    idx: int,
    section_key: str,
) -> None:
    """
    Render één component als compacte card met inline actieknoppen.
    Deze functie rendert binnen een bestaande kolom (geen st.container).
    
    Args:
        comp: FinancieelComponent object.
        idx: Index in de lijst.
        section_key: Unieke sectie-identifier voor state keys.
    """
    from pensioen.ui.style import badge_html, format_bedrag, ICONS
    
    # Bepaal type voor badge-kleur
    if comp.categorie.value in ("arbeidsinkomen", "pensioen_inkomen", "overig_inkomen"):
        badge_type = "inkomen"
    elif comp.categorie.value in ("uitgave", "inhouding"):
        badge_type = "uitgave"
    else:
        badge_type = "neutraal"
    
    # Bedrag formatteren
    bedrag_str = format_bedrag(float(comp.bedrag))
    freq_label = FREQUENTIE_LABELS[comp.frequentie]
    
    # Bruto/netto badge
    type_badge = badge_html(BEDRAG_TYPE_LABELS[comp.bedrag_type], badge_type="neutraal", small=True)
    cat_badge = badge_html(CATEGORIE_LABELS[comp.categorie], badge_type=badge_type, small=True)
    
    # Card inhoud (binnen bestaande kolom)
    st.markdown(f"**{comp.omschrijving}**")
    st.markdown(
        f"{bedrag_str} / {freq_label}",
        unsafe_allow_html=True,
    )
    st.caption(f"{comp.persoon} • {type_badge} {cat_badge}", unsafe_allow_html=True)
    
    # Extra details indien aanwezig
    details = []
    if comp.begindatum:
        details.append(f"Vanaf {comp.begindatum.strftime('%d-%m-%Y')}")
    if comp.einddatum:
        details.append(f"Tot {comp.einddatum.strftime('%d-%m-%Y')}")
    if comp.groei_pct and comp.groei_pct > 0:
        details.append(f"Groei {float(comp.groei_pct):.1f}%/jr")
    if details:
        st.caption(" | ".join(details))
    
    # Actieknoppen
    edit_key = f"{section_key}_edit_{idx}"
    del_key = f"{section_key}_del_{idx}"
    
    col_edit, col_del = st.columns(2)
    with col_edit:
        if st.button(f"{ICONS['bewerken']} Bewerk", key=edit_key, use_container_width=True):
            st.session_state[f"{section_key}_active_idx"] = idx
            st.session_state[f"{section_key}_active_mode"] = "edit"
            st.rerun()
    with col_del:
        if st.button(f"{ICONS['verwijderen']} Verw.", key=del_key, use_container_width=True, type="secondary"):
            st.session_state[f"{section_key}_delete_idx"] = idx
            st.rerun()
    
    st.markdown("---")


def render_component_form(
    section_key: str,
    mode: str,
    initial: FinancieelComponent | None,
    persoon_opties: list[str],
) -> FinancieelComponent | None:
    """
    Render herbruikbaar formulier voor toevoegen of wijzigen van een component.
    
    Args:
        section_key: Unieke sectie-identifier.
        mode: "add" of "edit".
        initial: Initiële data (None bij add).
        persoon_opties: Lijst van mogelijke personen.
    
    Returns:
        FinancieelComponent indien opgeslagen, anders None.
    """
    from pensioen.ui.style import ICONS
    
    form_key = f"{section_key}_form_{mode}"
    
    # Initiële waarden
    if initial:
        omschr = initial.omschrijving
        cat = CATEGORIE_LABELS[initial.categorie]
        pers = initial.persoon
        bedrag = float(initial.bedrag)
        btype = BEDRAG_TYPE_LABELS[initial.bedrag_type]
        freq = FREQUENTIE_LABELS[initial.frequentie]
        belegg = BELEGGINGS_TYPE_LABELS[initial.beleggings_type]
        begindatum_val = initial.begindatum
        einddatum_val = initial.einddatum
        groei = float(initial.groei_pct)
    else:
        omschr = ""
        cat = CATEGORIE_OPTIES[0]
        pers = persoon_opties[0]
        bedrag = 0.0
        btype = BEDRAG_TYPE_OPTIES[0]
        freq = FREQUENTIE_OPTIES[0]
        belegg = BELEGGINGS_TYPE_OPTIES[0]
        begindatum_val = None
        einddatum_val = None
        groei = 0.0
    
    st.markdown(f"### {ICONS['toevoegen'] if mode == 'add' else ICONS['bewerken']} {'Nieuw component' if mode == 'add' else 'Component wijzigen'}")
    
    col1, col2 = st.columns(2)
    with col1:
        omschrijving = st.text_input("Omschrijving", value=omschr, key=f"{form_key}_omschr")
        categorie_label = st.selectbox("Categorie", options=CATEGORIE_OPTIES, index=CATEGORIE_OPTIES.index(cat), key=f"{form_key}_cat")
        bedrag_inp = st.number_input("Bedrag (€)", min_value=0, value=int(bedrag), step=100, key=f"{form_key}_bedrag")
        frequentie_label = st.selectbox("Frequentie", options=FREQUENTIE_OPTIES, index=FREQUENTIE_OPTIES.index(freq), key=f"{form_key}_freq")
    
    with col2:
        persoon = st.selectbox("Persoon", options=persoon_opties, index=persoon_opties.index(pers) if pers in persoon_opties else 0, key=f"{form_key}_pers")
        bedrag_type_label = st.selectbox("Type bedrag", options=BEDRAG_TYPE_OPTIES, index=BEDRAG_TYPE_OPTIES.index(btype), key=f"{form_key}_btype")
        groei_inp = st.number_input("Groei % per jaar", min_value=0.0, max_value=20.0, value=groei, step=0.1, key=f"{form_key}_groei")
    
    # Geavanceerde opties (ingeklapt)
    with st.expander("⚙️ Geavanceerde opties", expanded=False):
        st.caption("Deze opties bepalen naar welk vermogenstype (spaargeld of beleggingen) dit component bijdraagt. Dit beïnvloedt de dynamische split voor Box 3 en rendementsberekeningen.")
        belegg_type_label = st.selectbox(
            "Soort vermogen",
            options=BELEGGINGS_TYPE_OPTIES,
            index=BELEGGINGS_TYPE_OPTIES.index(belegg),
            key=f"{form_key}_belegg",
            help="Bepaalt of dit component naar spaargeld of beleggingen gaat.",
        )
    
    st.markdown("**Optionele datumrange**")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        begindatum = st.date_input("Vanaf (leeg = altijd)", value=begindatum_val, key=f"{form_key}_start", format="DD-MM-YYYY")
    with col_d2:
        einddatum = st.date_input("Tot (leeg = onbepaald)", value=einddatum_val, key=f"{form_key}_eind", format="DD-MM-YYYY")
    
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 Bewaren", key=f"{form_key}_save", type="primary", use_container_width=True):
            # Validatie
            if not omschrijving.strip():
                st.error("Omschrijving is verplicht.")
                return None
            
            # Mapping terug naar enums
            cat_inv = {v: k for k, v in CATEGORIE_LABELS.items()}
            freq_inv = {v: k for k, v in FREQUENTIE_LABELS.items()}
            btype_inv = {v: k for k, v in BEDRAG_TYPE_LABELS.items()}
            belegg_inv = {v: k for k, v in BELEGGINGS_TYPE_LABELS.items()}
            
            try:
                return FinancieelComponent(
                    omschrijving=omschrijving.strip(),
                    categorie=cat_inv[categorie_label],
                    persoon=persoon,
                    bedrag=Decimal(str(bedrag_inp)),
                    bedrag_type=btype_inv[bedrag_type_label],
                    frequentie=freq_inv[frequentie_label],
                    beleggings_type=belegg_inv[belegg_type_label],
                    begindatum=begindatum if begindatum else None,
                    einddatum=einddatum if einddatum else None,
                    groei_pct=Decimal(str(groei_inp)),
                )
            except (ValueError, TypeError) as e:
                st.error(f"Ongeldige invoer: {e}")
                return None
    
    with col_cancel:
        if st.button("❌ Annuleren", key=f"{form_key}_cancel", use_container_width=True):
            st.session_state[f"{section_key}_active_mode"] = None
            st.session_state[f"{section_key}_active_idx"] = None
            st.rerun()
    
    return None


def render_incidenteel_card(
    item: "IncidenteelItem",
    idx: int,
    section_key: str,
) -> None:
    """
    Render één eenmalige cashflow als compacte card met inline actieknoppen.
    Deze functie rendert binnen een bestaande kolom (geen st.container).
    
    Args:
        item: IncidenteelItem object.
        idx: Index in de lijst.
        section_key: Unieke sectie-identifier voor state keys.
    """
    from pensioen.ui.style import badge_html, format_bedrag, ICONS
    
    is_ontvangst = item.bedrag >= 0
    badge_type = "ontvangst" if is_ontvangst else "uitgave_eenmalig"
    bedrag_str = format_bedrag(float(item.bedrag))
    
    type_badge = badge_html("Ontvangst" if is_ontvangst else "Uitgave", badge_type=badge_type, small=True)
    
    # Card inhoud (binnen bestaande kolom)
    st.markdown(f"**{item.omschrijving or '(geen omschrijving)'}**")
    st.markdown(
        f"{bedrag_str}",
        unsafe_allow_html=True,
    )
    st.caption(f"{item.datum.strftime('%d-%m-%Y')} • {type_badge}", unsafe_allow_html=True)
    
    # Actieknoppen
    edit_key = f"{section_key}_edit_{idx}"
    del_key = f"{section_key}_del_{idx}"
    
    col_edit, col_del = st.columns(2)
    with col_edit:
        if st.button(f"{ICONS['bewerken']} Bewerk", key=edit_key, use_container_width=True):
            st.session_state[f"{section_key}_active_idx"] = idx
            st.session_state[f"{section_key}_active_mode"] = "edit"
            st.rerun()
    with col_del:
        if st.button(f"{ICONS['verwijderen']} Verw.", key=del_key, use_container_width=True, type="secondary"):
            st.session_state[f"{section_key}_delete_idx"] = idx
            st.rerun()
    
    st.markdown("---")


def render_incidenteel_form(
    section_key: str,
    mode: str,
    initial: "IncidenteelItem | None",
) -> "IncidenteelItem | None":
    """
    Render formulier voor toevoegen of wijzigen van eenmalige cashflow.
    
    Args:
        section_key: Unieke sectie-identifier.
        mode: "add" of "edit".
        initial: Initiële data (None bij add).
    
    Returns:
        IncidenteelItem indien opgeslagen, anders None.
    """
    from pensioen.models.scenario import IncidenteelItem
    from pensioen.ui.style import ICONS
    
    form_key = f"{section_key}_form_{mode}"
    
    if initial:
        omschr = initial.omschrijving or ""
        bedrag_val = float(initial.bedrag)
        datum_val = initial.datum
    else:
        omschr = ""
        bedrag_val = 0.0
        datum_val = date.today()
    
    st.markdown(f"### {ICONS['toevoegen'] if mode == 'add' else ICONS['bewerken']} {'Nieuwe eenmalige cashflow' if mode == 'add' else 'Cashflow wijzigen'}")
    
    col1, col2 = st.columns(2)
    with col1:
        omschrijving = st.text_input("Omschrijving", value=omschr, key=f"{form_key}_omschr")
        datum = st.date_input("Datum", value=datum_val, key=f"{form_key}_datum", format="DD-MM-YYYY")
    with col2:
        bedrag_inp = st.number_input(
            "Bedrag (€, negatief = uitgave)",
            value=int(bedrag_val),
            step=100,
            key=f"{form_key}_bedrag",
            help="Positief = ontvangst, negatief = uitgave.",
        )
    
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 Bewaren", key=f"{form_key}_save", type="primary", use_container_width=True):
            if not omschrijving.strip():
                st.error("Omschrijving is verplicht.")
                return None
            
            try:
                return IncidenteelItem(
                    datum=datum,
                    bedrag=Decimal(str(bedrag_inp)),
                    omschrijving=omschrijving.strip(),
                )
            except (ValueError, TypeError) as e:
                st.error(f"Ongeldige invoer: {e}")
                return None
    
    with col_cancel:
        if st.button("❌ Annuleren", key=f"{form_key}_cancel", use_container_width=True):
            st.session_state[f"{section_key}_active_mode"] = None
            st.session_state[f"{section_key}_active_idx"] = None
            st.rerun()
    
    return None


