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

    # Losstaande widgets niet in modellen (prognosehorizon)
    for sleutel in ("jaar_van", "jaar_tot"):
        waarde = st.session_state.get(sleutel)
        if waarde is not None:
            data.setdefault("widgets", {})[sleutel] = waarde

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

    # --- Personen ---
    if p1_dict := data.get("persoon1"):
        try:
            p1 = Persoon.model_validate(p1_dict)
            st.session_state["persoon1"] = p1
            # Formulierwaarden afleiden uit het model
            _zet("naam_p1", p1.naam)
            _zet("geboortedatum_p1", p1.geboortedatum)
            _zet("heeft_partner", p1.heeft_partner)
        except Exception:
            pass

    if p2_dict := data.get("persoon2"):
        try:
            p2 = Persoon.model_validate(p2_dict)
            st.session_state["persoon2"] = p2
            _zet("naam_p2", p2.naam)
            _zet("geboortedatum_p2", p2.geboortedatum)
        except Exception:
            pass

    # --- Pensioenrecords ---
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

    # --- Scenario's ---
    scenarios = []
    for s in data.get("scenario_lijst", []):
        try:
            scenarios.append(Scenario.model_validate(s))
        except Exception:
            pass
    if scenarios:
        st.session_state["scenario_lijst"] = scenarios
        # Formulierwaarden pre-fill vanuit het eerste scenario
        s0 = scenarios[0]
        _zet("scenario_naam", s0.naam)
        _zet("stopdatum_p1", s0.persoon1_stopdatum_werk)
        _zet("salaris_p1", int(s0.persoon1_bruto_jaarsalaris))
        if s0.persoon2_stopdatum_werk:
            _zet("stopdatum_p2", s0.persoon2_stopdatum_werk)
        _zet("salaris_p2", int(s0.persoon2_bruto_jaarsalaris))
        _zet("salarisgroei", float(s0.salarisgroei_pct))
        _zet("spaargeld", int(s0.spaargeld_start))
        _zet("inleg", int(s0.jaarlijkse_inleg))
        _zet("rendement", float(s0.rendement_pct))
        _zet("box3", s0.box3_meenemen)
        _zet("box3_spaargeld_pct", int(s0.box3_spaargeld_fractie * 100))

    # --- Incidentele tabel ---
    if rijen := data.get("incidenteel_tabel"):
        try:
            df = pd.DataFrame(rijen)
            if "datum" in df.columns:
                df["datum"] = pd.to_datetime(df["datum"])
            _zet("incidenteel_tabel", df)
        except Exception:
            pass

    # --- Losstaande widgets (prognosehorizon) ---
    for sleutel in ("jaar_van", "jaar_tot"):
        if sleutel not in st.session_state:
            if (waarde := data.get("widgets", {}).get(sleutel)) is not None:
                st.session_state[sleutel] = int(waarde)
