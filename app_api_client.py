"""Eenvoudige Streamlit UI die de FastAPI endpoints aanroept."""

from __future__ import annotations

import json
from datetime import date
from urllib import error, request

import streamlit as st


def _default_component() -> dict:
    return {
        "omschrijving": "Salaris P1",
        "categorie": "arbeidsinkomen",
        "persoon": "P1",
        "bedrag": 4000,
        "bedrag_type": "bruto",
        "frequentie": "maandelijks",
        "beleggings_type": "sparen",
        "groei_pct": 0,
    }


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
                    "beleggings_type": "sparen",
                    "groei_pct": "0",
                },
                {
                    "omschrijving": "Vaste lasten",
                    "categorie": "uitgave",
                    "persoon": "Huishouden",
                    "bedrag": "1500",
                    "bedrag_type": "netto",
                    "frequentie": "maandelijks",
                    "beleggings_type": "sparen",
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
    except error.URLError as exc:
        return 503, {"detail": f"API niet bereikbaar: {exc.reason}"}
    except TimeoutError:
        return 504, {"detail": "Timeout bij verbinden met API"}


def _api_get(url: str, timeout: int = 15) -> tuple[int, dict]:
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            inhoud = response.read().decode("utf-8")
            return response.status, json.loads(inhoud)
    except error.HTTPError as exc:
        inhoud = exc.read().decode("utf-8")
        try:
            data = json.loads(inhoud)
        except json.JSONDecodeError:
            data = {"detail": inhoud}
        return exc.code, data
    except error.URLError as exc:
        return 503, {"detail": f"API niet bereikbaar: {exc.reason}"}
    except TimeoutError:
        return 504, {"detail": "Timeout bij verbinden met API"}


def _laad_referenties(api_basis: str) -> dict[str, dict[str, str]]:
    fallback = {
        "categorieen": {
            "arbeidsinkomen": "Arbeidsinkomen",
            "pensioen_inkomen": "Pensioeninkomen",
            "overig_inkomen": "Overig inkomen",
            "uitgave": "Uitgave",
            "inhouding": "Inhouding",
        },
        "frequenties": {
            "eenmalig": "Eenmalig",
            "maandelijks": "Maandelijks",
            "kwartaal": "Per kwartaal",
            "halfjaarlijks": "Per halfjaar",
            "jaarlijks": "Jaarlijks",
        },
        "bedrag_types": {
            "bruto": "Bruto",
            "netto": "Netto",
        },
        "beleggings_types": {
            "sparen": "Sparen",
            "beleggen": "Beleggen",
        },
        "foutcodes": {
            "derived_scenario_requires_list": "Afgeleid scenario vereist ook een scenario_lijst met het parent scenario.",
            "inheritance_validation_error": "De scenario-relaties bevatten een fout (bijv. cirkel of ontbrekende parent).",
            "berekening_input_error": "De invoer voor de berekening is ongeldig.",
        },
    }
    status, data = _api_get(f"{api_basis}/referenties/codes", timeout=3)
    if status >= 400:
        return fallback
    codes = data.get("codes", {})
    return {
        "categorieen": codes.get("categorieen", fallback["categorieen"]),
        "frequenties": codes.get("frequenties", fallback["frequenties"]),
        "bedrag_types": codes.get("bedrag_types", fallback["bedrag_types"]),
        "beleggings_types": codes.get("beleggings_types", fallback["beleggings_types"]),
        "foutcodes": codes.get("foutcodes", fallback["foutcodes"]),
    }


@st.cache_data(ttl=300, show_spinner=False)
def _laad_referenties_cached(api_basis: str) -> dict[str, dict[str, str]]:
    return _laad_referenties(api_basis)


def _lees_foutmeldingen(data: dict, code_berichten: dict[str, str]) -> list[str]:

    detail = data.get("detail")
    berichten: list[str] = []

    if isinstance(detail, dict):
        code = detail.get("code")
        if isinstance(code, str) and code in code_berichten:
            berichten.append(code_berichten[code])

        message = detail.get("message")
        if isinstance(message, str) and message.strip():
            berichten.append(message)

        waarschuwingen = detail.get("waarschuwingen")
        if isinstance(waarschuwingen, list):
            for waarschuwing in waarschuwingen:
                if isinstance(waarschuwing, str) and waarschuwing.strip():
                    berichten.append(waarschuwing)

    if isinstance(detail, list):
        for item in detail:
            if not isinstance(item, dict):
                continue
            loc = item.get("loc")
            msg = item.get("msg")
            if isinstance(msg, str):
                if isinstance(loc, list) and loc:
                    pad = ".".join(str(stap) for stap in loc)
                    berichten.append(f"{pad}: {msg}")
                else:
                    berichten.append(msg)

    if not berichten and isinstance(detail, str) and detail.strip():
        berichten.append(detail)

    if not berichten:
        berichten.append("Onbekende API-fout. Controleer de invoer en probeer opnieuw.")

    return berichten


st.set_page_config(page_title="Pensioenplanner API Client", layout="wide")
st.title("Pensioenplanner API Client (MVP)")

if "payload_json" not in st.session_state:
    st.session_state.payload_json = json.dumps(_voorbeeld_payload(), indent=2)
if "laatste_payload_hash" not in st.session_state:
    st.session_state.laatste_payload_hash = None
if "laatste_resultaat" not in st.session_state:
    st.session_state.laatste_resultaat = None
if "builder_componenten" not in st.session_state:
    st.session_state.builder_componenten = [_default_component()]

api_basis = st.text_input(
    "API basis URL",
    value="http://127.0.0.1:8000/api/v1",
)

referenties = _laad_referenties_cached(api_basis.strip())

with st.expander("Payload bouwer (codes uit API)", expanded=False):
    kol1, kol2 = st.columns(2)
    with kol1:
        scenario_naam = st.text_input("Scenario naam", value="API Demo Scenario")
        persoon_naam = st.text_input("Naam persoon", value="Jan Jansen")
        geboortedatum = st.date_input("Geboortedatum", value=date(1963, 3, 15))
    with kol2:
        huidig_jaar = date.today().year
        jaar_van = st.number_input("Jaar van", min_value=2020, max_value=2100, value=huidig_jaar)
        jaar_tot = st.number_input("Jaar tot", min_value=2020, max_value=2100, value=huidig_jaar + 5)
        spaargeld_start = st.number_input("Spaargeld start", min_value=0, value=50000)

    st.caption("Componenten")
    cat_labels = referenties["categorieen"]
    freq_labels = referenties["frequenties"]
    bedragtype_labels = referenties["bedrag_types"]
    beleggings_labels = referenties["beleggings_types"]

    categorie_opties = list(cat_labels.keys())
    frequentie_opties = list(freq_labels.keys())
    bedragtype_opties = list(bedragtype_labels.keys())
    beleggings_opties = list(beleggings_labels.keys())

    if st.button("+ Component toevoegen"):
        st.session_state.builder_componenten.append(_default_component())
        st.rerun()

    verwijder_index = None
    persoon_opties = ["P1", "P2", "Huishouden"]

    for idx, component in enumerate(st.session_state.builder_componenten):
        if "beleggings_type" not in component:
            component["beleggings_type"] = "sparen"

        st.markdown(f"Component {idx + 1}")
        comp_k1, comp_k2, comp_k3, comp_k4 = st.columns(4)
        with comp_k1:
            component["omschrijving"] = st.text_input(
                "Omschrijving",
                value=str(component.get("omschrijving", "")),
                key=f"comp_omschrijving_{idx}",
            )
        with comp_k2:
            huidige_cat = component.get("categorie", categorie_opties[0])
            cat_index = categorie_opties.index(huidige_cat) if huidige_cat in categorie_opties else 0
            component["categorie"] = st.selectbox(
                "Categorie",
                options=categorie_opties,
                index=cat_index,
                format_func=lambda code: cat_labels.get(code, code),
                key=f"comp_categorie_{idx}",
            )
        with comp_k3:
            huidige_bedragtype = component.get("bedrag_type", bedragtype_opties[0])
            bedragtype_index = (
                bedragtype_opties.index(huidige_bedragtype)
                if huidige_bedragtype in bedragtype_opties
                else 0
            )
            component["bedrag_type"] = st.selectbox(
                "Bedrag type",
                options=bedragtype_opties,
                index=bedragtype_index,
                format_func=lambda code: bedragtype_labels.get(code, code),
                key=f"comp_bedrag_type_{idx}",
            )
        with comp_k4:
            huidige_freq = component.get("frequentie", frequentie_opties[0])
            freq_index = frequentie_opties.index(huidige_freq) if huidige_freq in frequentie_opties else 0
            component["frequentie"] = st.selectbox(
                "Frequentie",
                options=frequentie_opties,
                index=freq_index,
                format_func=lambda code: freq_labels.get(code, code),
                key=f"comp_frequentie_{idx}",
            )

        comp_k5, comp_k6, comp_k7, comp_k8 = st.columns(4)
        with comp_k5:
            component["persoon"] = st.selectbox(
                "Persoon",
                options=persoon_opties,
                index=(persoon_opties.index(component.get("persoon", "P1")) if component.get("persoon", "P1") in persoon_opties else 0),
                key=f"comp_persoon_{idx}",
            )
        with comp_k6:
            component["bedrag"] = st.number_input(
                "Bedrag",
                min_value=0.0,
                value=float(component.get("bedrag", 0)),
                step=100.0,
                key=f"comp_bedrag_{idx}",
            )
        with comp_k7:
            component["groei_pct"] = st.number_input(
                "Groei %",
                min_value=-100.0,
                max_value=100.0,
                value=float(component.get("groei_pct", 0)),
                step=0.5,
                key=f"comp_groei_{idx}",
            )
        with comp_k8:
            huidige_beleggings_type = component.get("beleggings_type", beleggings_opties[0])
            beleggings_index = (
                beleggings_opties.index(huidige_beleggings_type)
                if huidige_beleggings_type in beleggings_opties
                else 0
            )
            component["beleggings_type"] = st.selectbox(
                "Beleggings type",
                options=beleggings_opties,
                index=beleggings_index,
                format_func=lambda code: beleggings_labels.get(code, code),
                key=f"comp_beleggings_type_{idx}",
            )

        if st.button(f"Verwijder component {idx + 1}", key=f"verwijder_comp_{idx}"):
            verwijder_index = idx

    if verwijder_index is not None:
        st.session_state.builder_componenten.pop(verwijder_index)
        if not st.session_state.builder_componenten:
            st.session_state.builder_componenten = [_default_component()]
        st.rerun()

    if st.button("Vul payload vanuit formulier"):
        componenten_payload = [
            {
                "omschrijving": str(comp.get("omschrijving", "")),
                "categorie": str(comp.get("categorie", "arbeidsinkomen")),
                "persoon": str(comp.get("persoon", "P1")),
                "bedrag": str(comp.get("bedrag", 0)),
                "bedrag_type": str(comp.get("bedrag_type", "bruto")),
                "frequentie": str(comp.get("frequentie", "maandelijks")),
                "beleggings_type": str(comp.get("beleggings_type", "sparen")),
                "groei_pct": str(comp.get("groei_pct", 0)),
            }
            for comp in st.session_state.builder_componenten
        ]

        payload = {
            "scenario": {
                "naam": scenario_naam,
                "spaargeld_start": str(spaargeld_start),
                "beleggingen_start": "0",
                "jaarlijkse_inleg": "0",
                "jaarlijkse_inleg_sparen": "0",
                "jaarlijkse_inleg_beleggen": "0",
                "inflatie_pct": "2",
                "box3_meenemen": True,
                "componenten": componenten_payload,
                "incidentele_items": [],
            },
            "persoon1": {
                "naam": persoon_naam,
                "geboortedatum": geboortedatum.isoformat(),
                "heeft_partner": False,
            },
            "persoon2": None,
            "records1": [],
            "records2": [],
            "jaar_van": int(jaar_van),
            "jaar_tot": int(jaar_tot),
            "scenario_lijst": [],
        }
        st.session_state.payload_json = json.dumps(payload, indent=2)
        st.rerun()

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
        scenario = payload.get("scenario")
        if isinstance(scenario, dict):
            componenten = scenario.get("componenten")
            if isinstance(componenten, list):
                for component in componenten:
                    if isinstance(component, dict) and not component.get("beleggings_type"):
                        component["beleggings_type"] = "sparen"

        status, data = _api_post(f"{api_basis}/berekeningen", payload)
        if status >= 400:
            st.error(f"API fout ({status})")
            for melding in _lees_foutmeldingen(data, referenties.get("foutcodes", {})):
                st.warning(melding)
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

    with st.expander("Volledige API response", expanded=False):
        st.json(resultaat)
