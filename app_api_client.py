"""Eenvoudige Streamlit UI die de FastAPI endpoints aanroept."""

from __future__ import annotations

import json
from datetime import date
from urllib import error, request

import streamlit as st


def _voorbeeld_payload() -> dict:
    huidig_jaar = date.today().year
    return {
        "scenario": {
            "naam": "API Demo Scenario",
            "spaargeld_start": "50000",
            "beleggingen_start": "0",
            "jaarlijkse_inleg": "0",
            "jaarlijkse_inleg_sparen": "1200",
            "jaarlijkse_inleg_beleggen": "0",
            "inflatie_pct": "2",
            "box3_meenemen": True,
            "componenten": [
                {
                    "omschrijving": "Salaris P1",
                    "categorie": "arbeidsinkomen",
                    "persoon": "P1",
                    "bedrag": "4000",
                    "bedrag_type": "bruto",
                    "frequentie": "maandelijks",
                    "groei_pct": "0",
                },
                {
                    "omschrijving": "Vaste lasten",
                    "categorie": "uitgave",
                    "persoon": "Huishouden",
                    "bedrag": "1500",
                    "bedrag_type": "netto",
                    "frequentie": "maandelijks",
                    "groei_pct": "0",
                },
            ],
            "incidentele_items": [],
        },
        "persoon1": {
            "naam": "Jan Jansen",
            "geboortedatum": "1963-03-15",
            "heeft_partner": False,
        },
        "persoon2": None,
        "records1": [],
        "records2": [],
        "jaar_van": huidig_jaar,
        "jaar_tot": huidig_jaar + 5,
        "scenario_lijst": [],
    }


def _api_post(url: str, payload: dict) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            inhoud = response.read().decode("utf-8")
            return response.status, json.loads(inhoud)
    except error.HTTPError as exc:
        inhoud = exc.read().decode("utf-8")
        try:
            data = json.loads(inhoud)
        except json.JSONDecodeError:
            data = {"detail": inhoud}
        return exc.code, data


st.set_page_config(page_title="Pensioenplanner API Client", layout="wide")
st.title("Pensioenplanner API Client (MVP)")

if "payload_json" not in st.session_state:
    st.session_state.payload_json = json.dumps(_voorbeeld_payload(), indent=2)
if "laatste_payload_hash" not in st.session_state:
    st.session_state.laatste_payload_hash = None
if "laatste_resultaat" not in st.session_state:
    st.session_state.laatste_resultaat = None

api_basis = st.text_input(
    "API basis URL",
    value="http://127.0.0.1:8000/api/v1",
)

payload_json = st.text_area(
    "Berekening payload (JSON)",
    key="payload_json",
    height=420,
)

huidige_hash = hash(payload_json)
is_verouderd = st.session_state.laatste_payload_hash != huidige_hash

if is_verouderd:
    st.warning("Gegevens gewijzigd sinds laatste berekening.")
else:
    st.success("Resultaten zijn actueel.")

if st.button("Berekenen via API", type="primary"):
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        st.error(f"Ongeldige JSON: {exc}")
    else:
        status, data = _api_post(f"{api_basis}/berekeningen", payload)
        if status >= 400:
            st.error(f"API fout ({status})")
            st.json(data)
        else:
            st.session_state.laatste_resultaat = data
            st.session_state.laatste_payload_hash = huidige_hash
            st.success("Berekening uitgevoerd.")

resultaat = st.session_state.laatste_resultaat
if resultaat:
    jaren = resultaat.get("cashflow", {}).get("jaren", [])
    if jaren:
        eerste_jaar = jaren[0]
        laatste_jaar = jaren[-1]
        kol1, kol2, kol3 = st.columns(3)
        with kol1:
            st.metric("Aantal jaren", len(jaren))
        with kol2:
            st.metric("Netto eerste jaar", eerste_jaar.get("netto", "n.v.t."))
        with kol3:
            st.metric("Vermogen eind laatste jaar", laatste_jaar.get("vermogen_einde_jaar", "n.v.t."))

    st.subheader("API response")
    st.json(resultaat)
