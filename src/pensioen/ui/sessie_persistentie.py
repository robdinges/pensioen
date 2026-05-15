"""Persistentie van sessie-invoer naar lokaal JSON-bestand.

Slaat persoonsgegevens, pensioenrecords, scenario's en tabelwaarden op in
.sessie.json in de projectmap. Bij herstart van de applicatie worden deze
automatisch hersteld in session_state.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from pensioen.models.pensioen_record import PensioenRecord
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.ui.scenario_context import (
    DEFAULT_SCENARIO_NAAM,
    SCENARIO_ACTIEF_KEY,
    SCENARIO_DEFAULT_KEY,
)

# Sla op in de projectroot (twee niveaus boven src/pensioen/ui/)
SESSIE_PAD = Path(__file__).parents[4] / ".sessie.json"

# Schema-versienummer: verhoog bij incompatibele wijzigingen in de opslagstructuur
SESSIE_VERSIE = 3


def _serialiseerbaar(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Niet-serialiseerbaar type: {type(obj)}")


def _zet(key: str, waarde: Any) -> None:
    """Stel een session_state-waarde in, maar overschrijf bestaande widget-state niet."""
    if key not in st.session_state and waarde is not None:
        st.session_state[key] = waarde


def sla_sessie_op() -> None:
    """Sla de huidige sessie-invoer op naar .sessie.json."""
    data: dict[str, Any] = {"_versie": SESSIE_VERSIE}

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

    actief_naam = st.session_state.get(SCENARIO_ACTIEF_KEY)
    if isinstance(actief_naam, str):
        data[SCENARIO_ACTIEF_KEY] = actief_naam
    default_naam = st.session_state.get(SCENARIO_DEFAULT_KEY)
    if isinstance(default_naam, str):
        data[SCENARIO_DEFAULT_KEY] = default_naam

    # Incidentele tabel
    df: pd.DataFrame | None = st.session_state.get("incidenteel_tabel")
    if df is not None and not df.empty:
        data["incidenteel_tabel"] = json.loads(
            df.to_json(orient="records", date_format="iso")
        )

    # Losstaande widgets niet in modellen (prognosehorizon)
    for sleutel in ("jaar_van", "jaar_tot"):
        waarde = st.session_state.get(sleutel)
        if waarde is not None:
            data.setdefault("widgets", {})[sleutel] = waarde

    tekst = json.dumps(data, default=_serialiseerbaar, ensure_ascii=False, indent=2)
    nieuw_hash = hashlib.md5(tekst.encode()).hexdigest()
    if st.session_state.get("_sessie_hash") == nieuw_hash:
        return  # Geen wijzigingen — sla schrijven over

    tmp_pad = SESSIE_PAD.with_suffix(".tmp.json")
    try:
        tmp_pad.write_text(tekst, encoding="utf-8")
        os.replace(tmp_pad, SESSIE_PAD)
        st.session_state["_sessie_hash"] = nieuw_hash
    except OSError as exc:
        st.warning(f"⚠️ Sessie kon niet opgeslagen worden: {exc}")
        tmp_pad.unlink(missing_ok=True)


def autosla_sessie_op() -> None:
    """Sla de sessie stilletjes op — geen UI-feedback, geen exceptions naar de gebruiker."""
    tmp_pad = SESSIE_PAD.with_suffix(".tmp.json")
    data: dict[str, Any] = {"_versie": SESSIE_VERSIE}

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

    actief_naam = st.session_state.get(SCENARIO_ACTIEF_KEY)
    if isinstance(actief_naam, str):
        data[SCENARIO_ACTIEF_KEY] = actief_naam
    default_naam = st.session_state.get(SCENARIO_DEFAULT_KEY)
    if isinstance(default_naam, str):
        data[SCENARIO_DEFAULT_KEY] = default_naam

    df: pd.DataFrame | None = st.session_state.get("incidenteel_tabel")
    if df is not None and not df.empty:
        data["incidenteel_tabel"] = json.loads(
            df.to_json(orient="records", date_format="iso")
        )

    for sleutel in ("jaar_van", "jaar_tot"):
        if (waarde := st.session_state.get(sleutel)) is not None:
            data.setdefault("widgets", {})[sleutel] = waarde

    try:
        tekst = json.dumps(data, default=_serialiseerbaar, ensure_ascii=False, indent=2)
        nieuw_hash = hashlib.md5(tekst.encode()).hexdigest()
        if st.session_state.get("_sessie_hash") == nieuw_hash:
            return
        tmp_pad.write_text(tekst, encoding="utf-8")
        os.replace(tmp_pad, SESSIE_PAD)
        st.session_state["_sessie_hash"] = nieuw_hash
    except OSError:
        tmp_pad.unlink(missing_ok=True)


def laad_sessie() -> None:
    """Herstel een eerder opgeslagen sessie in session_state (eenmalig per startup)."""
    if st.session_state.get("_sessie_geladen"):
        return
    st.session_state["_sessie_geladen"] = True

    if not SESSIE_PAD.exists():
        return

    try:
        data = json.loads(SESSIE_PAD.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    # Versiecheck — laad altijd, maar waarschuw bij verouderd schema
    opgeslagen_versie = data.get("_versie", 1)
    if opgeslagen_versie < SESSIE_VERSIE:
        st.info(
            f"ℹ️ Sessiebestand is opgeslagen in schema v{opgeslagen_versie} "
            f"(huidig: v{SESSIE_VERSIE}). Gegevens worden ingelezen; sla daarna opnieuw op."
        )

    # --- Personen ---
    if p1_dict := data.get("persoon1"):
        try:
            p1 = Persoon.model_validate(p1_dict)
            st.session_state["persoon1"] = p1
            # Formulierwaarden afleiden uit het model
            _zet("naam_p1", p1.naam)
            _zet("geboortedatum_p1", p1.geboortedatum)
            _zet("heeft_partner", p1.heeft_partner)
        except (TypeError, ValueError):
            pass

    if p2_dict := data.get("persoon2"):
        try:
            p2 = Persoon.model_validate(p2_dict)
            st.session_state["persoon2"] = p2
            _zet("naam_p2", p2.naam)
            _zet("geboortedatum_p2", p2.geboortedatum)
        except (TypeError, ValueError):
            pass

    # --- Pensioenrecords ---
    records1 = []
    for r in data.get("records_p1", []):
        try:
            records1.append(PensioenRecord.model_validate(r))
        except (TypeError, ValueError):
            pass
    if records1:
        st.session_state["records_p1"] = records1

    records2 = []
    for r in data.get("records_p2", []):
        try:
            records2.append(PensioenRecord.model_validate(r))
        except (TypeError, ValueError):
            pass
    if records2:
        st.session_state["records_p2"] = records2

    # --- Scenario's ---
    scenarios = []
    for s in data.get("scenario_lijst", []):
        try:
            scenarios.append(Scenario.model_validate(s))
        except (TypeError, ValueError):
            pass
    if scenarios:
        st.session_state["scenario_lijst"] = scenarios

    # --- Actief/default scenario ---
    actief_naam = data.get(SCENARIO_ACTIEF_KEY)
    if not isinstance(actief_naam, str):
        # Backward compat met legacy widget-key
        legacy = data.get("scenario_selectie")
        actief_naam = legacy if isinstance(legacy, str) else None
    if isinstance(actief_naam, str):
        st.session_state[SCENARIO_ACTIEF_KEY] = actief_naam

    default_naam = data.get(SCENARIO_DEFAULT_KEY)
    if not isinstance(default_naam, str):
        default_naam = actief_naam or DEFAULT_SCENARIO_NAAM
    st.session_state[SCENARIO_DEFAULT_KEY] = default_naam

    # --- Incidentele tabel ---
    if rijen := data.get("incidenteel_tabel"):
        try:
            df = pd.DataFrame(rijen)
            if "datum" in df.columns:
                df["datum"] = pd.to_datetime(df["datum"])
            _zet("incidenteel_tabel", df)
        except (TypeError, ValueError):
            pass



    # --- Losstaande widgets (prognosehorizon) ---
    for sleutel in ("jaar_van", "jaar_tot"):
        if sleutel not in st.session_state:
            if (waarde := data.get("widgets", {}).get(sleutel)) is not None:
                st.session_state[sleutel] = int(waarde)
