"""Persistentie van sessie-invoer naar lokaal JSON-bestand.

Slaat persoonsgegevens, pensioenrecords, scenario's en tabelwaarden op in
.sessie.json in de projectmap. Bij herstart van de applicatie worden deze
automatisch hersteld in session_state.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from pensioen.models.pensioen_record import PensioenRecord
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario

# Sla op in de projectroot (twee niveaus boven src/pensioen/ui/)
SESSIE_PAD = Path(__file__).parents[4] / ".sessie.json"

# Widget-sleutels die direct als primitieve waarden worden opgeslagen
_DATUM_SLEUTELS = {"geboortedatum_p1", "geboortedatum_p2", "stopdatum_p1", "stopdatum_p2"}
_WIDGET_SLEUTELS = [
    "naam_p1", "geboortedatum_p1", "heeft_partner",
    "naam_p2", "geboortedatum_p2",
    "scenario_naam",
    "stopdatum_p1", "salaris_p1",
    "stopdatum_p2", "salaris_p2",
    "salarisgroei", "spaargeld", "inleg", "rendement", "box3",
    "jaar_van", "jaar_tot",
]


def _serialiseerbaar(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Niet-serialiseerbaar type: {type(obj)}")


def sla_sessie_op() -> None:
    """Sla de huidige sessie-invoer op naar .sessie.json."""
    data: dict[str, Any] = {}

    # Pydantic-modellen
    if p1 := st.session_state.get("persoon1"):
        data["persoon1"] = p1.model_dump(mode="json")
    if p2 := st.session_state.get("persoon2"):
        data["persoon2"] = p2.model_dump(mode="json")

    data["records_p1"] = [
        r.model_dump(mode="json")
        for r in st.session_state.get("records_p1", [])
    ]
    data["records_p2"] = [
        r.model_dump(mode="json")
        for r in st.session_state.get("records_p2", [])
    ]
    data["scenario_lijst"] = [
        s.model_dump(mode="json")
        for s in st.session_state.get("scenario_lijst", [])
    ]

    # Incidentele tabel
    df: pd.DataFrame | None = st.session_state.get("incidenteel_tabel")
    if df is not None and not df.empty:
        data["incidenteel_tabel"] = json.loads(
            df.to_json(orient="records", date_format="iso")
        )

    # Widget-primitieven
    widgets: dict[str, Any] = {}
    for sleutel in _WIDGET_SLEUTELS:
        waarde = st.session_state.get(sleutel)
        if waarde is not None:
            if isinstance(waarde, (date, datetime)):
                widgets[sleutel] = waarde.isoformat()
            elif isinstance(waarde, Decimal):
                widgets[sleutel] = str(waarde)
            else:
                widgets[sleutel] = waarde
    data["widgets"] = widgets

    try:
        SESSIE_PAD.write_text(
            json.dumps(data, default=_serialiseerbaar, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        st.warning(f"⚠️ Sessie kon niet opgeslagen worden: {exc}")


def laad_sessie() -> None:
    """Herstel een eerder opgeslagen sessie in session_state (eenmalig per startup)."""
    if st.session_state.get("_sessie_geladen"):
        return
    st.session_state["_sessie_geladen"] = True

    if not SESSIE_PAD.exists():
        return

    try:
        data = json.loads(SESSIE_PAD.read_text(encoding="utf-8"))
    except Exception:
        return

    # Personen
    if p1_dict := data.get("persoon1"):
        try:
            st.session_state["persoon1"] = Persoon.model_validate(p1_dict)
        except Exception:
            pass
    if p2_dict := data.get("persoon2"):
        try:
            st.session_state["persoon2"] = Persoon.model_validate(p2_dict)
        except Exception:
            pass

    # Pensioenrecords
    records1 = []
    for r in data.get("records_p1", []):
        try:
            records1.append(PensioenRecord.model_validate(r))
        except Exception:
            pass
    if records1:
        st.session_state["records_p1"] = records1

    records2 = []
    for r in data.get("records_p2", []):
        try:
            records2.append(PensioenRecord.model_validate(r))
        except Exception:
            pass
    if records2:
        st.session_state["records_p2"] = records2

    # Scenario's
    scenarios = []
    for s in data.get("scenario_lijst", []):
        try:
            scenarios.append(Scenario.model_validate(s))
        except Exception:
            pass
    if scenarios:
        st.session_state["scenario_lijst"] = scenarios

    # Incidentele tabel
    if rijen := data.get("incidenteel_tabel"):
        try:
            df = pd.DataFrame(rijen)
            if "datum" in df.columns:
                df["datum"] = pd.to_datetime(df["datum"])
            st.session_state["incidenteel_tabel"] = df
        except Exception:
            pass

    # Widget-waarden voor pre-fill van formulieren
    widgets = data.get("widgets", {})
    for sleutel, waarde in widgets.items():
        if sleutel in st.session_state:
            continue  # widget is al actief, niet overschrijven
        if sleutel in _DATUM_SLEUTELS and isinstance(waarde, str):
            try:
                waarde = date.fromisoformat(waarde)
            except Exception:
                continue
        st.session_state[sleutel] = waarde
