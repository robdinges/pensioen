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
