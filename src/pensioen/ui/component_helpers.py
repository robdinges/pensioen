"""Helper functions for component and pensioen record management."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from pensioen.models.component import BedragType, CategorieComponent, FinancieelComponent, Frequentie
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
        })
    if not rijen:
        return maak_lege_component_df()
    return pd.DataFrame(rijen)


def df_naar_componenten(df: pd.DataFrame) -> list[FinancieelComponent]:
    """Convert a DataFrame back to FinancieelComponent objects."""
    cat_inv = {v: k for k, v in CATEGORIE_LABELS.items()}
    freq_inv = {v: k for k, v in FREQUENTIE_LABELS.items()}
    bedrag_type_inv = {v: k for k, v in BEDRAG_TYPE_LABELS.items()}

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

        persoon = str(rij.get("persoon", "P1"))

        def parse_datum(waarde: str | None) -> date | None:
            """Parse dd-mm-yyyy or ISO date."""
            if not waarde or str(waarde).strip() == "":
                return None
            s = str(waarde).strip()
            for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
                try:
                    return date.fromisoformat(s) if fmt == "%Y-%m-%d" else __import__("datetime").datetime.strptime(s, fmt).date()
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
            )
            componenten.append(comp)
        except (ValueError, TypeError):
            pass
    return componenten


def toon_pensioen_editor(records_key: str, persoon_label: str) -> list[PensioenRecord]:
    """Show and allow editing of pension record start/end dates."""
    records: list[PensioenRecord] = st.session_state.get(records_key, [])
    if not records:
        st.caption(f"Geen MPO-records geladen voor {persoon_label}.")
        return records

    gewijzigd = []
    for i, r in enumerate(records):
        with st.expander(f"{r.uitvoerder} — {r.regeling} (€ {float(r.bruto_per_jaar):,.0f}/jr)", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                ingangsdatum = st.date_input(
                    "Ingangsdatum pensioen",
                    value=r.ingangsdatum or date.today(),
                    key=f"{records_key}_ingangsdatum_{i}",
                    format="DD-MM-YYYY",
                )
            with col2:
                einddatum = st.date_input(
                    "Einddatum (leeg = onbepaald)",
                    value=r.einddatum,
                    key=f"{records_key}_einddatum_{i}",
                    format="DD-MM-YYYY",
                )
            gewijzigd.append(r.model_copy(update={
                "ingangsdatum": ingangsdatum,
                "einddatum": einddatum,
            }))
    return gewijzigd
