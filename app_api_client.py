"""Eenvoudige Streamlit UI die de FastAPI endpoints aanroept."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib import error, request

import pandas as pd
import plotly.express as px
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


def _naar_decimal(waarde: object) -> Decimal:
    if isinstance(waarde, Decimal):
        return waarde
    if waarde is None:
        return Decimal("0")
    try:
        return Decimal(str(waarde))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _format_euro(waarde: Decimal) -> str:
    return f"EUR {float(waarde):,.2f}"


def _bereken_maand_netto(maand: dict) -> Decimal:
    totaal_bruto = (
        _naar_decimal(maand.get("arbeid_p1_bruto"))
        + _naar_decimal(maand.get("arbeid_p2_bruto"))
        + _naar_decimal(maand.get("aow_p1_bruto"))
        + _naar_decimal(maand.get("aow_p2_bruto"))
        + _naar_decimal(maand.get("pensioen_p1_bruto"))
        + _naar_decimal(maand.get("pensioen_p2_bruto"))
        + _naar_decimal(maand.get("lijfrente_bruto"))
        + _naar_decimal(maand.get("rente_bruto"))
        + _naar_decimal(maand.get("overig_bruto"))
    )
    totaal_belasting = (
        _naar_decimal(maand.get("belasting_p1"))
        + _naar_decimal(maand.get("belasting_p2"))
        + _naar_decimal(maand.get("box3_heffing"))
    )
    totaal_heffingskorting = (
        _naar_decimal(maand.get("heffingskorting_p1"))
        + _naar_decimal(maand.get("heffingskorting_p2"))
    )

    return (
        totaal_bruto
        + _naar_decimal(maand.get("inkomen_componenten_netto"))
        - totaal_belasting
        + totaal_heffingskorting
        - _naar_decimal(maand.get("inhoudingen"))
        - _naar_decimal(maand.get("huishoudelijke_uitgaven"))
        + _naar_decimal(maand.get("eenmalig_ontvangst"))
        - _naar_decimal(maand.get("eenmalig_uitgave"))
    )


def _bouw_jaar_dataframe(resultaat: dict) -> pd.DataFrame:
    jaren = resultaat.get("cashflow", {}).get("jaren", [])
    if not isinstance(jaren, list) or not jaren:
        return pd.DataFrame()

    rijen: list[dict] = []
    for jaar_data in jaren:
        jaar = int(jaar_data.get("jaar", 0))
        maanden = jaar_data.get("maanden", [])
        if not isinstance(maanden, list):
            maanden = []

        netto_jaar = sum((_bereken_maand_netto(m) for m in maanden), Decimal("0"))
        bruto_jaar = sum(
            (
                _naar_decimal(m.get("arbeid_p1_bruto"))
                + _naar_decimal(m.get("arbeid_p2_bruto"))
                + _naar_decimal(m.get("aow_p1_bruto"))
                + _naar_decimal(m.get("aow_p2_bruto"))
                + _naar_decimal(m.get("pensioen_p1_bruto"))
                + _naar_decimal(m.get("pensioen_p2_bruto"))
                + _naar_decimal(m.get("lijfrente_bruto"))
                + _naar_decimal(m.get("rente_bruto"))
                + _naar_decimal(m.get("overig_bruto"))
            )
            for m in maanden
        )
        belasting_jaar = sum(
            (
                _naar_decimal(m.get("belasting_p1"))
                + _naar_decimal(m.get("belasting_p2"))
                + _naar_decimal(m.get("box3_heffing"))
            )
            for m in maanden
        )

        vermogen_einde_jaar = Decimal("0")
        if maanden:
            laatste_maand = maanden[-1]
            if isinstance(laatste_maand, dict):
                vermogen_einde_jaar = _naar_decimal(laatste_maand.get("vermogen_einde_maand"))

        netto_per_maand = netto_jaar / Decimal(str(len(maanden))) if maanden else Decimal("0")

        rijen.append(
            {
                "jaar": jaar,
                "bruto_jaar": float(bruto_jaar),
                "belasting_jaar": float(belasting_jaar),
                "netto_jaar": float(netto_jaar),
                "netto_per_maand": float(netto_per_maand),
                "vermogen_einde_jaar": float(vermogen_einde_jaar),
                "bruto_jaar_fmt": _format_euro(bruto_jaar),
                "belasting_jaar_fmt": _format_euro(belasting_jaar),
                "netto_jaar_fmt": _format_euro(netto_jaar),
                "netto_per_maand_fmt": _format_euro(netto_per_maand),
                "vermogen_einde_jaar_fmt": _format_euro(vermogen_einde_jaar),
            }
        )

    return pd.DataFrame(rijen).sort_values("jaar")


def _check_api_status(api_basis: str) -> tuple[bool, str]:
    status, data = _api_get(f"{api_basis}/health", timeout=2)
    if status == 200:
        return True, "API online"

    detail = data.get("detail") if isinstance(data, dict) else data
    if isinstance(detail, str) and detail.strip():
        return False, detail
    return False, f"API niet bereikbaar (status {status})"


st.set_page_config(
    page_title="Pensioenplanner API Client",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Pensioenplanner API Client")
st.caption("API-gedreven invoer met jaarresultaten en snelle controle van netto en vermogen.")

if "payload_json" not in st.session_state:
    st.session_state.payload_json = json.dumps(_voorbeeld_payload(), indent=2)
if "laatste_payload_hash" not in st.session_state:
    st.session_state.laatste_payload_hash = None
if "laatste_resultaat" not in st.session_state:
    st.session_state.laatste_resultaat = None
if "builder_componenten" not in st.session_state:
    st.session_state.builder_componenten = [_default_component()]
if "laatste_api_fouten" not in st.session_state:
    st.session_state.laatste_api_fouten = []

with st.sidebar:
    st.subheader("API verbinding")
    api_basis = st.text_input(
        "API basis URL",
        value="http://127.0.0.1:8000/api/v1",
    ).strip()

    api_online, api_status_tekst = _check_api_status(api_basis)
    if api_online:
        st.success(api_status_tekst)
    else:
        st.warning(api_status_tekst)

    if st.button("Referenties verversen", use_container_width=True):
        _laad_referenties_cached.clear()
        st.rerun()

    st.markdown("---")
    st.caption("Werkwijze")
    st.caption("1. Vul of update payload")
    st.caption("2. Bereken via API")
    st.caption("3. Bekijk jaarresultaten")

referenties = _laad_referenties_cached(api_basis)

tab_invoer, tab_resultaten, tab_json = st.tabs([
    "Invoer",
    "Resultaten op Jaarbasis",
    "Ruwe API JSON",
])

with tab_invoer:
    st.subheader("Invoer en Payload")
    st.info("Bewerk via formulier of direct in JSON, en start daarna handmatig de berekening.")

    with st.expander("Payload bouwer (codes uit API)", expanded=True):
        kol1, kol2 = st.columns(2)
        with kol1:
            scenario_naam = st.text_input("Scenario naam", value="API Demo Scenario")
            persoon_naam = st.text_input("Naam persoon", value="Jan Jansen")
            geboortedatum = st.date_input("Geboortedatum", value=date(1963, 3, 15))
        with kol2:
            huidig_jaar = date.today().year
            jaar_van = st.number_input("Jaar van", min_value=2020, max_value=2100, value=huidig_jaar)
            jaar_tot = st.number_input("Jaar tot", min_value=2020, max_value=2100, value=huidig_jaar + 20)
            spaargeld_start = st.number_input("Spaargeld start", min_value=0, value=50000)

        st.caption("Componenten")
        cat_labels = referenties["categorieen"]
        freq_labels = referenties["frequenties"]
        bedragtype_labels = referenties["bedrag_types"]
        beleggings_labels = referenties.get(
            "beleggings_types",
            {
                "sparen": "Sparen",
                "beleggen": "Beleggen",
            },
        )

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

    if st.button("Berekenen via API", type="primary", use_container_width=True):
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

            with st.spinner("Berekening loopt..."):
                status, data = _api_post(f"{api_basis}/berekeningen", payload)

            if status >= 400:
                fouten = _lees_foutmeldingen(data, referenties.get("foutcodes", {}))
                st.session_state.laatste_api_fouten = fouten
                st.error(f"API fout ({status})")
                for melding in fouten:
                    st.warning(melding)
            else:
                st.session_state.laatste_api_fouten = []
                st.session_state.laatste_resultaat = data
                st.session_state.laatste_payload_hash = huidige_hash
                st.success("Berekening uitgevoerd. Bekijk nu de tab 'Resultaten op Jaarbasis'.")

with tab_resultaten:
    st.subheader("Jaaroverzicht")
    resultaat = st.session_state.laatste_resultaat

    if not resultaat:
        st.info("Nog geen berekening beschikbaar. Start eerst een berekening in de tab 'Invoer'.")
    else:
        df_jaar = _bouw_jaar_dataframe(resultaat)
        if df_jaar.empty:
            st.warning("Geen jaarresultaten gevonden in API-response.")
        else:
            eerste_jaar = int(df_jaar["jaar"].min())
            laatste_jaar = int(df_jaar["jaar"].max())
            totaal_netto = Decimal(str(df_jaar["netto_jaar"].sum()))
            gemiddeld_netto = totaal_netto / Decimal(str(len(df_jaar)))
            eindvermogen = Decimal(str(df_jaar.iloc[-1]["vermogen_einde_jaar"]))

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.metric("Periode", f"{eerste_jaar}-{laatste_jaar}")
            with k2:
                st.metric("Aantal jaren", len(df_jaar))
            with k3:
                st.metric("Gem. netto per jaar", _format_euro(gemiddeld_netto))
            with k4:
                st.metric("Vermogen einde periode", _format_euro(eindvermogen))

            st.markdown("### Jaarresultaten")
            st.dataframe(
                df_jaar[
                    [
                        "jaar",
                        "bruto_jaar_fmt",
                        "belasting_jaar_fmt",
                        "netto_jaar_fmt",
                        "netto_per_maand_fmt",
                        "vermogen_einde_jaar_fmt",
                    ]
                ].rename(
                    columns={
                        "jaar": "Jaar",
                        "bruto_jaar_fmt": "Bruto per jaar",
                        "belasting_jaar_fmt": "Belasting per jaar",
                        "netto_jaar_fmt": "Netto per jaar",
                        "netto_per_maand_fmt": "Gem. netto per maand",
                        "vermogen_einde_jaar_fmt": "Vermogen einde jaar",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

            grafiek_k1, grafiek_k2 = st.columns(2)
            with grafiek_k1:
                fig_netto = px.bar(
                    df_jaar,
                    x="jaar",
                    y="netto_jaar",
                    title="Netto kasstroom per jaar",
                    template="plotly_white",
                )
                fig_netto.update_layout(xaxis_title="Jaar", yaxis_title="EUR")
                st.plotly_chart(fig_netto, use_container_width=True)

            with grafiek_k2:
                fig_vermogen = px.line(
                    df_jaar,
                    x="jaar",
                    y="vermogen_einde_jaar",
                    markers=True,
                    title="Vermogen einde jaar",
                    template="plotly_white",
                )
                fig_vermogen.update_layout(xaxis_title="Jaar", yaxis_title="EUR")
                st.plotly_chart(fig_vermogen, use_container_width=True)

        aannames = resultaat.get("aannames", [])
        if isinstance(aannames, list) and aannames:
            with st.expander("Aannames en toelichting", expanded=False):
                for aanname in aannames:
                    st.write(f"- {aanname}")

with tab_json:
    st.subheader("Ruwe API output")
    if st.session_state.laatste_resultaat:
        with st.expander("Volledige API response", expanded=False):
            st.json(st.session_state.laatste_resultaat)
    else:
        st.info("Nog geen API-response beschikbaar.")
