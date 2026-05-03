"""Streamlit-pagina: gedetailleerde accountantsberekening (2026-2030)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import streamlit as st

from pensioen.calculations import pensioen_engine, vermogen_engine
from pensioen.tax import aow_engine, belasting_engine, heffingskorting
from pensioen.tax.belasting_loader import BelastingConfig, laad_tarieven


def _fmt(bedrag: Decimal | float | int) -> str:
    """Formatteer als euro met 2 decimalen."""
    return f"€ {float(bedrag):>12,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(waarde: Decimal | float) -> str:
    return f"{float(waarde) * 100:.4f}%"


def _bereken_jaar_detail(
    jaar: int,
    persoon1,
    persoon2,
    records1: list,
    records2: list,
    scenario,
    config: BelastingConfig,
    aanname: str,
    saldo_begin_jaar: Decimal,
    startjaar: int,
) -> dict:
    """
    Herbereken één jaar volledig met alle tussentotalen.
    Retourneert een dict met alle berekeningen voor weergave.
    """
    heeft_partner = persoon2 is not None

    # AOW-datums en bedragen
    aow_datum_p1 = aow_engine.bereken_aow_datum(persoon1.geboortedatum)
    aow_datum_p2 = aow_engine.bereken_aow_datum(persoon2.geboortedatum) if persoon2 else None
    aow_bedrag_p1 = (
        config.aow_bedrag.gehuwd_of_samenwonend_per_maand
        if heeft_partner
        else config.aow_bedrag.alleenstaande_per_maand
    )
    aow_bedrag_p2 = (
        config.aow_bedrag.gehuwd_of_samenwonend_per_maand
        if heeft_partner
        else config.aow_bedrag.alleenstaande_per_maand
    )

    # Jaarsalaris (met salarisgroei)
    basis_p1 = scenario.persoon1_bruto_jaarsalaris
    basis_p2 = scenario.persoon2_bruto_jaarsalaris
    groeifactor = (
        (Decimal("1") + scenario.salarisgroei_pct / Decimal("100"))
        ** max(0, jaar - startjaar)
    )
    salaris_p1 = (basis_p1 * groeifactor).quantize(Decimal("0.01"))
    salaris_p2 = (basis_p2 * groeifactor).quantize(Decimal("0.01")) if persoon2 else Decimal("0")

    # Maandbruto ophalen
    maand_data = []
    for maand in range(1, 13):
        arbeid_p1 = pensioen_engine.bereken_arbeid_maand(
            salaris_p1, scenario.persoon1_stopdatum_werk, jaar, maand
        )
        arbeid_p2 = Decimal("0")
        if persoon2 and scenario.persoon2_stopdatum_werk:
            arbeid_p2 = pensioen_engine.bereken_arbeid_maand(
                salaris_p2, scenario.persoon2_stopdatum_werk, jaar, maand
            )
        aow_p1 = pensioen_engine.bereken_aow_maand(
            persoon1.geboortedatum, aow_datum_p1, aow_bedrag_p1, jaar, maand
        )
        aow_p2 = Decimal("0")
        if persoon2 and aow_datum_p2:
            aow_p2 = pensioen_engine.bereken_aow_maand(
                persoon2.geboortedatum, aow_datum_p2, aow_bedrag_p2, jaar, maand
            )
        pen_p1 = Decimal(str(sum(
            pensioen_engine.bereken_pensioen_maand(r, jaar, maand) for r in records1
        )))
        pen_p2 = Decimal(str(sum(
            pensioen_engine.bereken_pensioen_maand(r, jaar, maand) for r in records2
        )))
        maand_data.append({
            "maand": maand,
            "arbeid_p1": arbeid_p1, "arbeid_p2": arbeid_p2,
            "aow_p1": aow_p1, "aow_p2": aow_p2,
            "pen_p1": pen_p1, "pen_p2": pen_p2,
        })

    # Jaartotalen bruto
    jaar_arbeid_p1 = sum(m["arbeid_p1"] for m in maand_data)
    jaar_arbeid_p2 = sum(m["arbeid_p2"] for m in maand_data)
    jaar_aow_p1 = sum(m["aow_p1"] for m in maand_data)
    jaar_aow_p2 = sum(m["aow_p2"] for m in maand_data)
    jaar_pen_p1 = sum(m["pen_p1"] for m in maand_data)
    jaar_pen_p2 = sum(m["pen_p2"] for m in maand_data)

    bruto_p1 = jaar_arbeid_p1 + jaar_aow_p1 + jaar_pen_p1
    bruto_p2 = jaar_arbeid_p2 + jaar_aow_p2 + jaar_pen_p2

    # Belasting persoon 1 — detailberekening
    aow_breuk_p1 = aow_engine.aow_breuk_jaar(persoon1.geboortedatum, jaar)
    is_aow_p1 = aow_breuk_p1 > Decimal("0")
    bel_voor_korting_p1 = belasting_engine.bereken_box1_belasting(bruto_p1, config, aow_breuk_p1)
    ahk_p1 = heffingskorting.bereken_ahk(bruto_p1, config)
    ak_p1 = heffingskorting.bereken_arbeidskorting(jaar_arbeid_p1, config)
    ok_p1 = heffingskorting.bereken_ouderenkorting(bruto_p1, config, is_aow_p1)
    totale_hk_p1 = ahk_p1 + ak_p1 + ok_p1
    netto_bel_p1 = max(Decimal("0"), bel_voor_korting_p1 - totale_hk_p1)
    netto_p1 = bruto_p1 - netto_bel_p1

    # Belasting persoon 2 — detailberekening
    bel_voor_korting_p2 = Decimal("0")
    ahk_p2 = ak_p2 = ok_p2 = totale_hk_p2 = netto_bel_p2 = Decimal("0")
    aow_breuk_p2 = Decimal("0")
    is_aow_p2 = False
    netto_p2 = Decimal("0")
    if persoon2:
        aow_breuk_p2 = aow_engine.aow_breuk_jaar(persoon2.geboortedatum, jaar)
        is_aow_p2 = aow_breuk_p2 > Decimal("0")
        bel_voor_korting_p2 = belasting_engine.bereken_box1_belasting(bruto_p2, config, aow_breuk_p2)
        ahk_p2 = heffingskorting.bereken_ahk(bruto_p2, config)
        ak_p2 = heffingskorting.bereken_arbeidskorting(jaar_arbeid_p2, config)
        ok_p2 = heffingskorting.bereken_ouderenkorting(bruto_p2, config, is_aow_p2)
        totale_hk_p2 = ahk_p2 + ak_p2 + ok_p2
        netto_bel_p2 = max(Decimal("0"), bel_voor_korting_p2 - totale_hk_p2)
        netto_p2 = bruto_p2 - netto_bel_p2

    totaal_netto_inkomen = netto_p1 + netto_p2

    # Box 3 heffing
    box3_heffing = Decimal("0")
    box3_info = ""
    if scenario.box3_meenemen and saldo_begin_jaar > Decimal("0"):
        box3_heffing, box3_info = belasting_engine.bereken_box3_heffing(
            saldo_begin_jaar, config, heeft_partner
        )

    # Vermogensberekening: saldo maand-voor-maand
    maandrendement = vermogen_engine.maandrendement(scenario.rendement_pct)
    inleg_per_maand = (scenario.jaarlijkse_inleg / Decimal("12")).quantize(Decimal("0.01"))
    box3_per_maand = (box3_heffing / Decimal("12")).quantize(Decimal("0.01"))
    maand_bel_p1 = (bel_voor_korting_p1 / Decimal("12")).quantize(Decimal("0.01"))
    maand_hk_p1 = (totale_hk_p1 / Decimal("12")).quantize(Decimal("0.01"))
    maand_bel_p2 = (bel_voor_korting_p2 / Decimal("12")).quantize(Decimal("0.01"))
    maand_hk_p2 = (totale_hk_p2 / Decimal("12")).quantize(Decimal("0.01"))

    vermogen_rijen = []
    saldo = saldo_begin_jaar
    for mb in maand_data:
        rente = vermogen_engine.bereken_rente_maand(saldo, scenario.rendement_pct)
        netto_cf = (
            mb["arbeid_p1"] + mb["arbeid_p2"]
            + mb["aow_p1"] + mb["aow_p2"]
            + mb["pen_p1"] + mb["pen_p2"]
            - maand_bel_p1 - maand_bel_p2
            + maand_hk_p1 + maand_hk_p2
            - box3_per_maand
            + rente
            + inleg_per_maand
        )
        nieuw_saldo = max(Decimal("0"), (saldo + netto_cf).quantize(Decimal("0.01")))
        vermogen_rijen.append({
            "maand": mb["maand"],
            "saldo_begin": saldo,
            "rente": rente,
            "netto_cashflow": netto_cf,
            "saldo_eind": nieuw_saldo,
        })
        saldo = nieuw_saldo

    saldo_einde_jaar = saldo

    return {
        "jaar": jaar,
        "config_jaar": config.jaar,
        "aanname": aanname,
        "salaris_p1": salaris_p1,
        "salaris_p2": salaris_p2,
        "jaar_arbeid_p1": Decimal(str(jaar_arbeid_p1)),
        "jaar_arbeid_p2": Decimal(str(jaar_arbeid_p2)),
        "jaar_aow_p1": Decimal(str(jaar_aow_p1)),
        "jaar_aow_p2": Decimal(str(jaar_aow_p2)),
        "jaar_pen_p1": Decimal(str(jaar_pen_p1)),
        "jaar_pen_p2": Decimal(str(jaar_pen_p2)),
        "bruto_p1": Decimal(str(bruto_p1)),
        "bruto_p2": Decimal(str(bruto_p2)),
        "aow_breuk_p1": aow_breuk_p1,
        "aow_breuk_p2": aow_breuk_p2,
        "is_aow_p1": is_aow_p1,
        "is_aow_p2": is_aow_p2,
        "bel_voor_korting_p1": bel_voor_korting_p1,
        "bel_voor_korting_p2": bel_voor_korting_p2,
        "ahk_p1": ahk_p1, "ak_p1": ak_p1, "ok_p1": ok_p1,
        "ahk_p2": ahk_p2, "ak_p2": ak_p2, "ok_p2": ok_p2,
        "totale_hk_p1": totale_hk_p1,
        "totale_hk_p2": totale_hk_p2,
        "netto_bel_p1": netto_bel_p1,
        "netto_bel_p2": netto_bel_p2,
        "netto_p1": netto_p1,
        "netto_p2": netto_p2,
        "totaal_netto_inkomen": totaal_netto_inkomen,
        "box3_vrijstelling": config.box3.vrijstelling_per_persoon * (2 if heeft_partner else 1),
        "box3_belastbaar": max(Decimal("0"), saldo_begin_jaar - config.box3.vrijstelling_per_persoon * (2 if heeft_partner else 1)),
        "box3_tarief": config.box3.tarief,
        "box3_heffing": box3_heffing,
        "box3_info": box3_info,
        "saldo_begin_jaar": saldo_begin_jaar,
        "maandrendement": maandrendement,
        "inleg_per_jaar": scenario.jaarlijkse_inleg,
        "saldo_einde_jaar": saldo_einde_jaar,
        "vermogen_rijen": vermogen_rijen,
        "maand_data": maand_data,
    }


def _toon_inkomen_detail(d: dict, naam_p1: str, naam_p2: str | None) -> None:
    """Toon de bruto → netto berekening als genummerde stappen."""
    heeft_p2 = naam_p2 is not None and d["bruto_p2"] > Decimal("0")

    st.markdown("#### A. Bruto inkomsten")
    cols = ["Post", naam_p1] + ([naam_p2] if heeft_p2 else []) + ["Huishouden"]
    rijen = [
        ["Arbeidsinkomen",
         _fmt(d["jaar_arbeid_p1"]),
         *([_fmt(d["jaar_arbeid_p2"])] if heeft_p2 else []),
         _fmt(d["jaar_arbeid_p1"] + d["jaar_arbeid_p2"])],
        ["AOW-uitkering",
         _fmt(d["jaar_aow_p1"]),
         *([_fmt(d["jaar_aow_p2"])] if heeft_p2 else []),
         _fmt(d["jaar_aow_p1"] + d["jaar_aow_p2"])],
        ["Werkgeverspensioen",
         _fmt(d["jaar_pen_p1"]),
         *([_fmt(d["jaar_pen_p2"])] if heeft_p2 else []),
         _fmt(d["jaar_pen_p1"] + d["jaar_pen_p2"])],
        ["**Totaal bruto inkomen**",
         f"**{_fmt(d['bruto_p1'])}**",
         *([f"**{_fmt(d['bruto_p2'])}**"] if heeft_p2 else []),
         f"**{_fmt(d['bruto_p1'] + d['bruto_p2'])}**"],
    ]
    st.table(_maak_tabel(cols, rijen))

    st.markdown("#### B. Box 1 belasting vóór heffingskortingen")
    if d["aow_breuk_p1"] > Decimal("0") and d["aow_breuk_p1"] < Decimal("1"):
        st.caption(
            f"⚠️ {naam_p1} bereikt AOW-leeftijd dit jaar. "
            f"AOW-breuk: {float(d['aow_breuk_p1']):.4f} "
            f"({float(d['aow_breuk_p1'])*100:.1f}% van het jaar AOW-tarief). "
            "Gewogen tarief toegepast."
        )
    if heeft_p2 and d["aow_breuk_p2"] > Decimal("0") and d["aow_breuk_p2"] < Decimal("1"):
        st.caption(
            f"⚠️ {naam_p2} bereikt AOW-leeftijd dit jaar. "
            f"AOW-breuk: {float(d['aow_breuk_p2']):.4f}. "
            "Gewogen tarief toegepast."
        )
    rijen_b = [
        ["Belastbaar inkomen",
         _fmt(d["bruto_p1"]),
         *([_fmt(d["bruto_p2"])] if heeft_p2 else []),
         ""],
        ["Schijventarief (zie noot *)",
         _fmt(d["bel_voor_korting_p1"]),
         *([_fmt(d["bel_voor_korting_p2"])] if heeft_p2 else []),
         _fmt(d["bel_voor_korting_p1"] + d["bel_voor_korting_p2"])],
    ]
    st.table(_maak_tabel(cols, rijen_b))
    st.caption(
        "\\* Schijven 2026: AOW-tarieven: schijf 1 ≤ €38.883 → **17,85%** | "
        "schijf 2 ≤ €78.426 → **37,56%** | schijf 3 → **49,50%**. "
        "Niet-AOW: schijf 1 → **35,75%**."
    )

    st.markdown("#### C. Heffingskortingen")
    rijen_c = [
        ["Algemene heffingskorting (AHK)",
         _fmt(d["ahk_p1"]),
         *([_fmt(d["ahk_p2"])] if heeft_p2 else []),
         _fmt(d["ahk_p1"] + d["ahk_p2"])],
        ["Arbeidskorting",
         _fmt(d["ak_p1"]),
         *([_fmt(d["ak_p2"])] if heeft_p2 else []),
         _fmt(d["ak_p1"] + d["ak_p2"])],
        ["Ouderenkorting",
         _fmt(d["ok_p1"]),
         *([_fmt(d["ok_p2"])] if heeft_p2 else []),
         _fmt(d["ok_p1"] + d["ok_p2"])],
        ["**Totaal kortingen**",
         f"**{_fmt(d['totale_hk_p1'])}**",
         *([f"**{_fmt(d['totale_hk_p2'])}**"] if heeft_p2 else []),
         f"**{_fmt(d['totale_hk_p1'] + d['totale_hk_p2'])}**"],
    ]
    st.table(_maak_tabel(cols, rijen_c))

    st.markdown("#### D. Netto belasting en netto inkomen")
    rijen_d = [
        ["Belasting vóór kortingen (B)",
         _fmt(d["bel_voor_korting_p1"]),
         *([_fmt(d["bel_voor_korting_p2"])] if heeft_p2 else []),
         _fmt(d["bel_voor_korting_p1"] + d["bel_voor_korting_p2"])],
        ["Af: totaal heffingskortingen (C)",
         _fmt(d["totale_hk_p1"]),
         *([_fmt(d["totale_hk_p2"])] if heeft_p2 else []),
         _fmt(d["totale_hk_p1"] + d["totale_hk_p2"])],
        ["**= Netto belasting**",
         f"**{_fmt(d['netto_bel_p1'])}**",
         *([f"**{_fmt(d['netto_bel_p2'])}**"] if heeft_p2 else []),
         f"**{_fmt(d['netto_bel_p1'] + d['netto_bel_p2'])}**"],
        ["Bruto inkomen (A)",
         _fmt(d["bruto_p1"]),
         *([_fmt(d["bruto_p2"])] if heeft_p2 else []),
         _fmt(d["bruto_p1"] + d["bruto_p2"])],
        ["Af: netto belasting",
         _fmt(d["netto_bel_p1"]),
         *([_fmt(d["netto_bel_p2"])] if heeft_p2 else []),
         _fmt(d["netto_bel_p1"] + d["netto_bel_p2"])],
        ["**= Netto inkomen**",
         f"**{_fmt(d['netto_p1'])}**",
         *([f"**{_fmt(d['netto_p2'])}**"] if heeft_p2 else []),
         f"**{_fmt(d['totaal_netto_inkomen'])}**"],
    ]
    st.table(_maak_tabel(cols, rijen_d))


def _toon_vermogen_detail(d: dict) -> None:
    """Toon de vermogensberekening: box 3 + maandopbouw."""
    st.markdown("#### E. Box 3 heffing")
    rijen_e = [
        ["Vermogen begin jaar", _fmt(d["saldo_begin_jaar"])],
        ["Belastingvrij (vrijstelling)", _fmt(d["box3_vrijstelling"])],
        ["Belastbaar vermogen", _fmt(d["box3_belastbaar"])],
        [f"× Box 3 tarief ({float(d['box3_tarief'])*100:.0f}%)", ""],
        ["**= Box 3 heffing (jaar)**", f"**{_fmt(d['box3_heffing'])}**"],
    ]
    st.table(_maak_tabel(["Post", "Bedrag"], rijen_e))
    if d["box3_info"]:
        st.caption(f"⚠️ {d['box3_info']}")

    st.markdown("#### F. Vermogensopbouw per maand")
    st.caption(
        f"Jaarrendement: **{d['maandrendement'] * 100 * 12:.2f}%** (nominaal) → "
        f"maandrendement: **{float(d['maandrendement'])*100:.6f}%**  |  "
        f"Jaarlijkse inleg: **{_fmt(d['inleg_per_jaar'])}**"
    )

    import pandas as pd
    maand_namen = ["jan", "feb", "mrt", "apr", "mei", "jun",
                   "jul", "aug", "sep", "okt", "nov", "dec"]
    rows = []
    for r in d["vermogen_rijen"]:
        rows.append({
            "Maand": maand_namen[r["maand"] - 1],
            "Saldo begin": _fmt(r["saldo_begin"]),
            "Rente": _fmt(r["rente"]),
            "Netto cashflow": _fmt(r["netto_cashflow"]),
            "Saldo eind": _fmt(r["saldo_eind"]),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown(
        f"**Vermogen begin {d['jaar']}:** {_fmt(d['saldo_begin_jaar'])}  \n"
        f"**Vermogen einde {d['jaar']}:** {_fmt(d['saldo_einde_jaar'])}  \n"
        f"**Mutatie:** {_fmt(d['saldo_einde_jaar'] - d['saldo_begin_jaar'])}"
    )


def _maak_tabel(cols: list[str], rijen: list[list]) -> "pd.DataFrame":
    import pandas as pd
    return pd.DataFrame(rijen, columns=cols)


def toon_accountant_pagina() -> None:
    """Streamlit-pagina: gedetailleerde accountantsberekening per jaar."""
    st.header("🔍 Accountantsoverzicht")
    st.write(
        "Exacte doorrekening van bruto → netto inkomen en vermogensontwikkeling "
        "per jaar, met alle tussentotalen."
    )

    persoon1 = st.session_state.get("persoon1")
    scenario_lijst = st.session_state.get("scenario_lijst", [])

    if not persoon1:
        st.warning("⚠️ Vul eerst de persoonsgegevens in (stap: Personen).")
        return
    if not scenario_lijst:
        st.warning("⚠️ Definieer eerst minstens één scenario (stap: Scenario).")
        return

    persoon2 = st.session_state.get("persoon2")
    records1 = st.session_state.get("records_p1", [])
    records2 = st.session_state.get("records_p2", [])
    scenario = scenario_lijst[0]
    naam_p2 = persoon2.naam if persoon2 else None

    col1, col2 = st.columns(2)
    with col1:
        jaar_van = st.number_input("Van jaar", value=date.today().year, step=1, key="acc_jaar_van")
    with col2:
        jaar_tot = st.number_input(
            "Tot en met jaar", value=date.today().year + 4, step=1, key="acc_jaar_tot"
        )

    if jaar_tot < jaar_van:
        st.error("'Tot jaar' moet na 'Van jaar' liggen.")
        return

    if st.button("▶ Berekening uitvoeren", type="primary", key="acc_bereken"):
        startjaar = int(jaar_van)
        saldo = scenario.spaargeld_start

        for jaar in range(int(jaar_van), int(jaar_tot) + 1):
            config, aanname = laad_tarieven(jaar)

            d = _bereken_jaar_detail(
                jaar=jaar,
                persoon1=persoon1,
                persoon2=persoon2,
                records1=records1,
                records2=records2,
                scenario=scenario,
                config=config,
                aanname=aanname,
                saldo_begin_jaar=saldo,
                startjaar=startjaar,
            )

            with st.expander(
                f"**{jaar}**  —  netto inkomen: {_fmt(d['totaal_netto_inkomen'])}  |  "
                f"vermogen einde jaar: {_fmt(d['saldo_einde_jaar'])}",
                expanded=(jaar == int(jaar_van)),
            ):
                if aanname:
                    st.warning(aanname)
                if config.jaar != jaar:
                    st.caption(f"Gebruikte belastingtarieven: {config.jaar}")

                st.markdown(
                    f"**Scenario:** {scenario.naam}  |  "
                    f"**Persoon 1:** {persoon1.naam}  |  "
                    + (f"**Persoon 2:** {persoon2.naam}  |  " if persoon2 else "")
                    + f"**Belastingjaar (tarieven):** {config.jaar}"
                )

                _toon_inkomen_detail(d, persoon1.naam, naam_p2)
                st.divider()
                _toon_vermogen_detail(d)

            saldo = d["saldo_einde_jaar"]
