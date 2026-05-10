"""Streamlit-pagina: scenarioparameters invoeren en beheren."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from pensioen.models.component import BedragType, CategorieComponent, ComponentSjabloon, COMPONENT_SJABLONEN, FinancieelComponent, Frequentie
from pensioen.models.pensioen_record import PensioenRecord
from pensioen.models.scenario import IncidenteelItem, Scenario
from pensioen.ui.helpers import fmt_eur
from pensioen.ui.sessie_persistentie import sla_sessie_op

_CATEGORIE_LABELS = {
    CategorieComponent.ARBEIDSINKOMEN: "Arbeidsinkomen",
    CategorieComponent.PENSIOEN_INKOMEN: "Pensioen inkomen",
    CategorieComponent.OVERIG_INKOMEN: "Overig inkomen",
    CategorieComponent.UITGAVE: "Uitgave",
    CategorieComponent.INHOUDING: "Inhouding",
}
_CATEGORIE_OPTIES = list(_CATEGORIE_LABELS.values())

_FREQUENTIE_LABELS = {
    Frequentie.MAANDELIJKS: "Maandelijks",
    Frequentie.KWARTAAL: "Per kwartaal",
    Frequentie.HALFJAARLIJKS: "Halfjaarlijks",
    Frequentie.JAARLIJKS: "Jaarlijks",
    Frequentie.EENMALIG: "Eenmalig",
}
_FREQUENTIE_OPTIES = list(_FREQUENTIE_LABELS.values())

_BEDRAG_TYPE_LABELS = {
    BedragType.BRUTO: "Bruto",
    BedragType.NETTO: "Netto",
}
_BEDRAG_TYPE_OPTIES = list(_BEDRAG_TYPE_LABELS.values())


def _fmt_eur(bedrag: Decimal | float | None) -> str:
    """€ 1.234,56 — rechts uitlijnen via vast breedte."""
    if bedrag is None:
        return "€ 0,00"
    return f"€ {float(bedrag):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _parse_decimal(waarde: str | float | None) -> Decimal:
    """Zet string of float om naar Decimal; geeft 0 bij fout."""
    try:
        return Decimal(str(waarde)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        return Decimal("0")


def _maak_lege_component_df() -> pd.DataFrame:
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


def _componenten_naar_df(componenten: list[FinancieelComponent]) -> pd.DataFrame:
    """Zet een lijst componenten om naar een bewerkbaar DataFrame."""
    rijen = []
    for c in componenten:
        rijen.append({
            "omschrijving": c.omschrijving,
            "categorie": _CATEGORIE_LABELS[c.categorie],
            "persoon": c.persoon,
            "bedrag_type": _BEDRAG_TYPE_LABELS[c.bedrag_type],
            "bedrag": float(c.bedrag),
            "frequentie": _FREQUENTIE_LABELS[c.frequentie],
            "begindatum": c.begindatum.strftime("%d-%m-%Y") if c.begindatum else "",
            "einddatum": c.einddatum.strftime("%d-%m-%Y") if c.einddatum else "",
            "groei_pct": float(c.groei_pct),
        })
    if not rijen:
        return _maak_lege_component_df()
    return pd.DataFrame(rijen)


def _df_naar_componenten(df: pd.DataFrame) -> list[FinancieelComponent]:
    """Zet een DataFrame terug naar FinancieelComponent-objecten."""
    _cat_inv = {v: k for k, v in _CATEGORIE_LABELS.items()}
    _freq_inv = {v: k for k, v in _FREQUENTIE_LABELS.items()}
    _bedrag_type_inv = {v: k for k, v in _BEDRAG_TYPE_LABELS.items()}

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
        categorie = _cat_inv.get(cat_label, CategorieComponent.ARBEIDSINKOMEN)
        frequentie = _freq_inv.get(freq_label, Frequentie.MAANDELIJKS)
        bedrag_type_label = str(rij.get("bedrag_type", "Bruto"))
        bedrag_type = _bedrag_type_inv.get(bedrag_type_label, BedragType.BRUTO)

        persoon = str(rij.get("persoon", "P1"))

        def _parse_datum(waarde: str | None) -> date | None:
            """Parseer dd-mm-jjjj of jjjj-mm-dd (ISO) naar date."""
            if not waarde or str(waarde).strip() == "":
                return None
            s = str(waarde).strip()
            for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
                try:
                    return date.fromisoformat(s) if fmt == "%Y-%m-%d" else __import__("datetime").datetime.strptime(s, fmt).date()
                except ValueError:
                    continue
            return None

        begindatum = _parse_datum(rij.get("begindatum"))
        einddatum = _parse_datum(rij.get("einddatum"))

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
        except (ValueError, Exception):
            pass
    return componenten


def _toon_pensioen_editor(records_key: str, persoon_label: str) -> list[PensioenRecord]:
    """Toon en laat ingangsdatum van MPO-records bewerken."""
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


def toon_scenario_pagina() -> None:
    """Streamlit-pagina voor het configureren en beheren van planningsscenario's."""
    st.header("📋 Scenario's")

    scenario_lijst: list[Scenario] = st.session_state.get("scenario_lijst", [])

    # ─── Scenario selecteren of nieuw aanmaken ───────────────────────────────
    st.subheader("Selecteer of maak een scenario")
    namen = [s.naam for s in scenario_lijst]
    opties = ["— Nieuw scenario —"] + namen

    # Streamlit staat niet toe dat je een widget-key overschrijft ná renderen.
    # Daarom gebruiken we een aparte "doelselectie"-key om na opslaan/verwijderen
    # de juiste optie te laten selecteren in de volgende run.
    voorkeur_selectie = st.session_state.get("scenario_selectie_doel")
    huidige_selectie = st.session_state.get("scenario_selectie")
    if voorkeur_selectie in opties:
        default_index = opties.index(voorkeur_selectie)
    elif huidige_selectie in opties:
        default_index = opties.index(huidige_selectie)
    else:
        default_index = 0

    col_sel, col_nieuw = st.columns([3, 1])
    with col_sel:
        scenario_selectie = st.selectbox(
            "Beschikbare scenario's",
            options=opties,
            index=default_index,
            key="scenario_selectie",
        )
        if voorkeur_selectie == scenario_selectie:
            st.session_state["scenario_selectie_doel"] = None
    with col_nieuw:
        st.write("")  # vertical align
        st.write("")
        if st.button("🗑️ Verwijder geselecteerd", key="verwijder_scenario",
                     disabled=scenario_selectie == "— Nieuw scenario —"):
            scenario_lijst = [s for s in scenario_lijst if s.naam != scenario_selectie]
            st.session_state["scenario_lijst"] = scenario_lijst
            st.session_state["scenario_selectie_doel"] = "— Nieuw scenario —"
            sla_sessie_op()
            st.rerun()

    # Laad bestaand scenario in formulier of start leeg
    bestaand: Scenario | None = None
    if scenario_selectie != "— Nieuw scenario —":
        bestaand = next((s for s in scenario_lijst if s.naam == scenario_selectie), None)

    # Houd de naam-widget synchroon met geselecteerd scenario.
    # Zonder dit kan de text_input een oude naam blijven tonen/bewaren.
    if "_naam_geladen_voor" not in st.session_state:
        st.session_state["_naam_geladen_voor"] = None
    if st.session_state["_naam_geladen_voor"] != scenario_selectie:
        st.session_state["sc_naam"] = bestaand.naam if bestaand else "Mijn scenario"
        st.session_state["sc_parent"] = bestaand.parent_naam if bestaand else None
        st.session_state["_naam_geladen_voor"] = scenario_selectie

    st.divider()

    # ─── 1. Scenario naam en parent ───────────────────────────────────────
    col_nm, col_par = st.columns([2, 2])
    with col_nm:
        scenario_naam = st.text_input("Naam van dit scenario", key="sc_naam")
    with col_par:
        parent_opties = ["— Geen parent (zelfstandig) —"] + [
            s.naam for s in scenario_lijst
            if s.naam != (bestaand.naam if bestaand else "")
        ]
        huidig_parent = st.session_state.get("sc_parent")
        parent_default = (
            parent_opties.index(huidig_parent)
            if huidig_parent in parent_opties
            else 0
        )
        parent_selectie = st.selectbox(
            "Basisscenario (erft waarden over)",
            options=parent_opties,
            index=parent_default,
            key="sc_parent_selectie",
            help="Kies een basisscenario om van te erven. Hier ingevulde velden overschrijven de parent.",
        )
        parent_naam_waarde: str | None = (
            None if parent_selectie == "— Geen parent (zelfstandig) —" else parent_selectie
        )
    if parent_naam_waarde:
        parent_effectief = next(
            (s.effectief_scenario(scenario_lijst) for s in scenario_lijst if s.naam == parent_naam_waarde),
            None,
        )
        if parent_effectief:
            st.info(
                f"🔗 Erft van **{parent_naam_waarde}**: "
                f"€ {float(parent_effectief.spaargeld_start):,.0f} spaargeld, "
                f"{float(parent_effectief.rendement_pct):.1f}% rendement, "
                f"{len(parent_effectief.componenten)} componenten"
            )

    # ─── 2. Financiële componenten ───────────────────────────────────────────
    st.subheader("💶 Financiële componenten")
    st.caption(
        "Voeg hier alle periodieke en eenmalige inkomsten, uitgaven en inhoudingen toe. "
        "Begindatum leeg = nu; einddatum leeg = geen einddatum. "
        "Bedrag is per frequentieperiode. Groei % = jaarlijkse groei. "
        "Bruto = meegenomen in belasting; Netto = direct in kasstroom zonder box 1-heffing."
    )

    heeft_partner = "persoon2" in st.session_state
    persoon_opties = ["P1", "P2", "Huishouden"] if heeft_partner else ["P1", "Huishouden"]

    standaard_comp_df = (
        _componenten_naar_df(bestaand.componenten) if bestaand else _maak_lege_component_df()
    )
    if "component_tabel" not in st.session_state or st.session_state.get("_sc_geladen") != scenario_selectie:
        st.session_state["component_tabel"] = standaard_comp_df
        st.session_state["_sc_geladen"] = scenario_selectie

    # Sjabloon toevoegen
    with st.expander("➕ Voeg sjabloon toe", expanded=False):
        sj_col, sj_btn_col = st.columns([4, 1])
        with sj_col:
            sj_keuze = st.selectbox(
                "Kies een sjabloon",
                options=[s.label for s in COMPONENT_SJABLONEN],
                key="sj_selectie",
                label_visibility="collapsed",
            )
        with sj_btn_col:
            if st.button("Voeg toe", key="sj_toevoegen"):
                sj = next(s for s in COMPONENT_SJABLONEN if s.label == sj_keuze)
                nieuwe_rij = pd.DataFrame([{
                    "omschrijving": sj.omschrijving,
                    "categorie": _CATEGORIE_LABELS[sj.categorie],
                    "persoon": sj.persoon,
                    "bedrag_type": _BEDRAG_TYPE_LABELS[sj.bedrag_type],
                    "bedrag": float(sj.bedrag),
                    "frequentie": _FREQUENTIE_LABELS[sj.frequentie],
                    "begindatum": "",
                    "einddatum": "",
                    "groei_pct": float(sj.groei_pct),
                }])
                st.session_state["component_tabel"] = pd.concat(
                    [st.session_state["component_tabel"], nieuwe_rij], ignore_index=True
                )
                st.rerun()

    component_df = st.data_editor(
        st.session_state["component_tabel"],
        num_rows="dynamic",
        column_config={
            "omschrijving": st.column_config.TextColumn("Omschrijving", required=True, width="medium"),
            "categorie": st.column_config.SelectboxColumn(
                "Categorie", options=_CATEGORIE_OPTIES, required=True, width="medium"
            ),
            "persoon": st.column_config.SelectboxColumn(
                "Persoon", options=persoon_opties, required=True, width="small"
            ),
            "bedrag_type": st.column_config.SelectboxColumn(
                "Type", options=_BEDRAG_TYPE_OPTIES, required=True, width="small"
            ),
            "bedrag": st.column_config.NumberColumn(
                "Bedrag (€)", min_value=0.0, format="%.2f", required=True, width="small"
            ),
            "frequentie": st.column_config.SelectboxColumn(
                "Frequentie", options=_FREQUENTIE_OPTIES, required=True, width="medium"
            ),
            "begindatum": st.column_config.TextColumn(
                "Begindatum (dd-mm-jjjj)", width="medium",
                help="Leeg = geen beperking. Formaat: dd-mm-jjjj"
            ),
            "einddatum": st.column_config.TextColumn(
                "Einddatum (dd-mm-jjjj)", width="medium",
                help="Leeg = geen einddatum. Formaat: dd-mm-jjjj"
            ),
            "groei_pct": st.column_config.NumberColumn(
                "Groei % /jaar", min_value=0.0, max_value=20.0,
                format="%.1f", width="small"
            ),
        },
        use_container_width=True,
        key="component_editor",
    )
    st.session_state["component_tabel"] = component_df

    # ─── 3. Pensioen ingangsdatums (MPO-records) ─────────────────────────────
    st.divider()
    st.subheader("🏦 Pensioendatums (uit MPO-import)")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("**Persoon 1**")
        records_p1 = _toon_pensioen_editor("records_p1", "Persoon 1")
    with col_p2:
        if heeft_partner:
            st.markdown("**Persoon 2**")
            records_p2 = _toon_pensioen_editor("records_p2", "Persoon 2")
        else:
            records_p2 = []

    # ─── 4. Vermogen en rendement ─────────────────────────────────────────────
    st.divider()
    st.subheader("💰 Vermogen en rendement")
    col3, col4 = st.columns(2)
    with col3:
        spaargeld = st.number_input(
            "Spaargeld/beleggingen nu (€)",
            min_value=0, value=int(bestaand.spaargeld_start) if bestaand else 50000,
            step=1000, key="sc_spaargeld",
        )
        jaarlijkse_inleg = st.number_input(
            "Jaarlijkse extra inleg (€)",
            min_value=0, value=int(bestaand.jaarlijkse_inleg) if bestaand else 0,
            step=500, key="sc_inleg",
        )
    with col4:
        rendement = st.slider(
            "Verwacht rendement (%)", 0.0, 10.0,
            float(bestaand.rendement_pct) if bestaand else 3.0,
            0.1, key="sc_rendement",
        )
        inflatie = st.slider(
            "Verwachte inflatie (%)", 0.0, 10.0,
            float(bestaand.inflatie_pct) if bestaand else 2.0,
            0.1, key="sc_inflatie",
            help="Gebruikt voor de reële koopkrachtkolom in de resultaten.",
        )
        box3_meenemen = st.checkbox(
            "Box 3 heffing meenemen (indicatief)",
            value=bestaand.box3_meenemen if bestaand else True,
            key="sc_box3",
        )
        if box3_meenemen:
            box3_spaargeld_pct = st.slider(
                "Box 3: % vermogen op spaarrekening",
                min_value=0, max_value=100,
                value=int((bestaand.box3_spaargeld_fractie * 100) if bestaand else 100),
                step=5, key="sc_box3_spaargeld",
                help="100% = spaargeld (forfait ~1,5%); 0% = beleggingen (forfait ~6%). "
                     "Belasting = 36% over fictief rendement.",
            )
        else:
            box3_spaargeld_pct = 100

    # ─── 5. Eenmalige cashflows ───────────────────────────────────────────────
    st.divider()
    st.subheader("⚡ Eenmalige ontvangsten en uitgaven")
    st.caption("Positief bedrag = ontvangst (erfenis, schenking); negatief = uitgave (verbouwing).")

    standaard_inc = pd.DataFrame(
        [{"datum": i.datum.strftime("%d-%m-%Y"), "bedrag": float(i.bedrag), "omschrijving": i.omschrijving}
         for i in bestaand.incidentele_items] if bestaand else [],
        columns=["datum", "bedrag", "omschrijving"],
    ) if bestaand and bestaand.incidentele_items else pd.DataFrame({
        "datum": pd.Series(dtype="object"),
        "bedrag": pd.Series(dtype="float64"),
        "omschrijving": pd.Series(dtype="object"),
    })

    if "incidenteel_tabel" not in st.session_state or st.session_state.get("_sc_geladen") != scenario_selectie:
        st.session_state["incidenteel_tabel"] = standaard_inc

    incidenteel_df = st.data_editor(
        st.session_state["incidenteel_tabel"],
        num_rows="dynamic",
        column_config={
            "datum": st.column_config.TextColumn("Datum (dd-mm-jjjj)", required=True),
            "bedrag": st.column_config.NumberColumn(
                "Bedrag (€, negatief = uitgave)", format="%.2f", required=True
            ),
            "omschrijving": st.column_config.TextColumn("Omschrijving"),
        },
        use_container_width=True,
        key="incidenteel_editor",
    )
    st.session_state["incidenteel_tabel"] = incidenteel_df

    # ─── Opslaan ─────────────────────────────────────────────────────────────
    st.divider()
    col_save, col_info = st.columns([2, 3])
    with col_save:
        opslaan = st.button("💾 Scenario opslaan", key="sc_opslaan", type="primary")

    if opslaan:
        # Vroege validatie — voor Pydantic-constructie
        fouten: list[str] = []
        if not scenario_naam or not scenario_naam.strip():
            fouten.append("Naam mag niet leeg zijn.")
        if scenario_naam.strip() == "— Nieuw scenario —":
            fouten.append("Kies een andere naam dan de standaard.")
        # Controleer of alle rijen in component_df een omschrijving hebben
        if not component_df.empty:
            lege_rijen = component_df[component_df["omschrijving"].astype(str).str.strip() == ""]
            if not lege_rijen.empty:
                fouten.append(f"{len(lege_rijen)} component(en) zonder omschrijving — vul alle rijen in of verwijder ze.")
        if fouten:
            for f in fouten:
                st.error(f"❌ {f}")
        else:
            try:
                componenten = _df_naar_componenten(component_df)

                def _datum_uit_tekst(s: str | None) -> date | None:
                    if not s or str(s).strip() == "":
                        return None
                    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
                        try:
                            return __import__("datetime").datetime.strptime(str(s).strip(), fmt).date()
                        except ValueError:
                            continue
                    return None

                incidentele_items = []
                for _, rij in incidenteel_df.iterrows():
                    d = _datum_uit_tekst(rij.get("datum"))
                    b = rij.get("bedrag")
                    if d is not None and b is not None:
                        try:
                            incidentele_items.append(IncidenteelItem(
                                datum=d,
                                bedrag=Decimal(str(b)),
                                omschrijving=str(rij.get("omschrijving", "")),
                            ))
                        except (ValueError, InvalidOperation):
                            pass

                # Bepaal welke velden expliciet zijn ingevuld t.o.v. de parent
                overschreven: list[str] = []
                if parent_naam_waarde:
                    parent_eff = next(
                        (s.effectief_scenario(scenario_lijst) for s in scenario_lijst if s.naam == parent_naam_waarde),
                        None,
                    )
                    if parent_eff:
                        _veld_waarden = {
                            "spaargeld_start": Decimal(str(spaargeld)),
                            "jaarlijkse_inleg": Decimal(str(jaarlijkse_inleg)),
                            "rendement_pct": Decimal(str(rendement)),
                            "inflatie_pct": Decimal(str(inflatie)),
                            "box3_meenemen": box3_meenemen,
                            "box3_spaargeld_fractie": Decimal(str(box3_spaargeld_pct)) / Decimal("100"),
                        }
                        for veld, waarde in _veld_waarden.items():
                            if waarde != getattr(parent_eff, veld):
                                overschreven.append(veld)
                        # Componenten als overschreven markeren als ze van de parent afwijken
                        if componenten != parent_eff.componenten:
                            overschreven.append("componenten")
                        if incidentele_items != parent_eff.incidentele_items:
                            overschreven.append("incidentele_items")

                scenario = Scenario(
                    naam=scenario_naam,
                    parent_naam=parent_naam_waarde,
                    overschreven_velden=overschreven,
                    spaargeld_start=Decimal(str(spaargeld)),
                    jaarlijkse_inleg=Decimal(str(jaarlijkse_inleg)),
                    rendement_pct=Decimal(str(rendement)),
                    inflatie_pct=Decimal(str(inflatie)),
                    box3_meenemen=box3_meenemen,
                    box3_spaargeld_fractie=Decimal(str(box3_spaargeld_pct)) / Decimal("100"),
                    componenten=componenten,
                    incidentele_items=incidentele_items,
                )

                # Vervang bestaand geselecteerd scenario, ook bij hernoemen.
                oude_naam = bestaand.naam if bestaand else None
                bestaand_lijst = [
                    s for s in scenario_lijst
                    if s.naam != scenario_naam and (oude_naam is None or s.naam != oude_naam)
                ]
                bestaand_lijst.append(scenario)
                st.session_state["scenario_lijst"] = bestaand_lijst
                st.session_state["scenario_selectie_doel"] = scenario_naam
                st.session_state["_naam_geladen_voor"] = scenario_naam

                # Pensioenrecords bijwerken (met gewijzigde ingangsdatums)
                st.session_state["records_p1"] = records_p1
                if heeft_partner:
                    st.session_state["records_p2"] = records_p2

                sla_sessie_op()
                st.success(f"✅ Scenario '{scenario_naam}' opgeslagen ({len(componenten)} componenten)")
                st.rerun()

            except ValueError as exc:
                st.error(f"❌ Ongeldige waarde: {exc}")
            except TypeError as exc:
                st.error(f"❌ Onverwacht gegevenstype: {exc}")

    # ─── Overzicht opgeslagen scenario's ─────────────────────────────────────
    scenario_lijst_actueel: list[Scenario] = st.session_state.get("scenario_lijst", [])
    if scenario_lijst_actueel:
        st.divider()
        st.subheader("📂 Opgeslagen scenario's")
        for s in scenario_lijst_actueel:
            n_ink = sum(1 for c in s.componenten if c.categorie in (
                CategorieComponent.ARBEIDSINKOMEN,
                CategorieComponent.PENSIOEN_INKOMEN,
                CategorieComponent.OVERIG_INKOMEN,
            ))
            n_uit = sum(1 for c in s.componenten if c.categorie in (
                CategorieComponent.UITGAVE, CategorieComponent.INHOUDING
            ))
            n_inc = len(s.incidentele_items)
            parent_info = f" ↳ erft van **{s.parent_naam}**" if s.parent_naam else ""
            actief_marker = " 🟢" if s.naam == st.session_state.get("scenario_selectie") else ""
            st.markdown(
                f"**{s.naam}**{actief_marker}{parent_info} — "
                f"{n_ink} inkomsten, {n_uit} uitgaven/inhoudingen, {n_inc} eenmalig  |  "
                f"Spaargeld: {fmt_eur(s.spaargeld_start)}  |  "
                f"Rendement: {s.rendement_pct}%"
            )

