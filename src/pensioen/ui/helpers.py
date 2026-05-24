"""Gedeelde UI-hulpfuncties: formattering, badges en statusindicatoren."""

from __future__ import annotations

from decimal import Decimal

import streamlit as st


# ---------------------------------------------------------------------------
# Formattering
# ---------------------------------------------------------------------------

def fmt_eur(bedrag: Decimal | float | int | None, decimalen: int = 0) -> str:
    """Formatteer als euro: € 1.234 of € 1.234,56."""
    if bedrag is None:
        return "—"
    fmt = f"€ {{:,.{decimalen}f}}"
    return fmt.format(float(bedrag)).replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(waarde: Decimal | float, decimalen: int = 2) -> str:
    """Formatteer als percentage: 36,00%."""
    return f"{float(waarde) * 100:.{decimalen}f}%".replace(".", ",")


# ---------------------------------------------------------------------------
# Persoon ID mapping (P1/P2 ↔ echte namen)
# ---------------------------------------------------------------------------

def get_persoon_display_naam(persoon_id: str) -> str:
    """
    Converteer persoon ID (P1, P2, Huishouden) naar echte naam voor weergave.
    
    Args:
        persoon_id: Intern ID ("P1", "P2", of "Huishouden")
    
    Returns:
        Echte naam of het ID zelf als niet gevonden.
    """
    if persoon_id == "Huishouden":
        return "Huishouden"
    
    # Haal personen op uit session_state
    persoon1 = st.session_state.get("persoon1")
    persoon2 = st.session_state.get("persoon2")
    
    if persoon_id == "P1" and persoon1:
        return persoon1.naam
    elif persoon_id == "P2" and persoon2:
        return persoon2.naam
    
    # Fallback naar ID zelf
    return persoon_id


def get_persoon_display_mapping() -> dict[str, str]:
    """
    Bouw mapping van intern ID naar weergave naam.
    
    Returns:
        Dict met keys "P1", "P2", "Huishouden" en echte namen als values.
    """
    persoon1 = st.session_state.get("persoon1")
    persoon2 = st.session_state.get("persoon2")
    
    return {
        "P1": persoon1.naam if persoon1 else "Persoon 1",
        "P2": persoon2.naam if persoon2 else "Persoon 2",
        "Huishouden": "Huishouden",
    }


def get_persoon_reverse_mapping() -> dict[str | None, str]:
    """
    Bouw mapping van echte naam naar intern ID.
    
    Gebruikt voor migratie van oude data die echte namen bevat.
    
    Returns:
        Dict met echte namen als keys en "P1"/"P2" als values.
    """
    persoon1 = st.session_state.get("persoon1")
    persoon2 = st.session_state.get("persoon2")
    
    return {
        persoon1.naam if persoon1 else None: "P1",
        persoon2.naam if persoon2 else None: "P2",
    }


# ---------------------------------------------------------------------------
# Statusindicatoren / badges
# ---------------------------------------------------------------------------

def toon_gap_badge(ontbrekende_jaren: list[int]) -> None:
    """Toon een oranje waarschuwing voor jaarlopen zonder eigen tariefbestand."""
    if not ontbrekende_jaren:
        return
    jaren_str = ", ".join(str(j) for j in sorted(ontbrekende_jaren))
    st.warning(
        f"⚠️ **Tariefhiaat**: voor {jaren_str} zijn geen eigen tarieven beschikbaar. "
        "De prognose gebruikt de tarieven van het meest recente beschikbare jaar als aanname."
    )


def toon_overlap_badge(overlappende_jaren: list[int]) -> None:
    """Toon een rode foutmelding bij dubbele tariefbestanden (zou niet moeten voorkomen)."""
    if not overlappende_jaren:
        return
    jaren_str = ", ".join(str(j) for j in sorted(overlappende_jaren))
    st.error(
        f"❌ **Tariefoverlap**: meerdere bestanden gevonden voor {jaren_str}. "
        "Verwijder duplicaten in de config-map."
    )


def toon_tarieven_status(jaar_van: int, jaar_tot: int, beschikbaar: set[int]) -> None:
    """
    Toon een gegroepeerde statusbalk voor het tariefbereik van de prognose.
    Groene vinkjes voor jaren met eigen config, oranje voor fallback-jaren.
    """
    kolommen = min(jaar_tot - jaar_van + 1, 10)
    cols = st.columns(kolommen)
    for i, jaar in enumerate(range(jaar_van, jaar_tot + 1)):
        col_idx = i % kolommen
        if jaar in beschikbaar:
            cols[col_idx].success(f"✅ {jaar}")
        else:
            cols[col_idx].warning(f"⚠️ {jaar}")
