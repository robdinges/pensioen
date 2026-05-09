"""Streamlit-pagina: gedetailleerde accountantsberekening (2026-2030)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import streamlit as st

from pensioen.calculations import pensioen_engine, vermogen_engine
from pensioen.models.component import BedragType, CategorieComponent
from pensioen.tax import aow_engine, belasting_engine, heffingskorting
from pensioen.tax.belasting_loader import BelastingConfig, laad_tarieven


def _fmt(bedrag: Decimal | float | int) -> str:
    """Formatteer als euro met 2 decimalen."""
    return f"€ {float(bedrag):>12,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(waarde: Decimal | float) -> str:
    return f"{float(waarde) * 100:.4f}%"


def _incidentele_items_voor_maand(scenario, jaar: int, maand: int) -> tuple[Decimal, Decimal]:
    """Retourneer (ontvangst, uitgave) voor incidentele items in de maand."""
    ontvangst = Decimal("0")
    uitgave = Decimal("0")
    for item in scenario.incidentele_items:
        if item.datum.year == jaar and item.datum.month == maand:
            if item.bedrag >= Decimal("0"):
                ontvangst += item.bedrag
            else:
                uitgave += abs(item.bedrag)
    return ontvangst, uitgave


def _component_som_maand(scenario, categorie, persoon, jaar: int, maand: int, bedrag_type: BedragType | None = None) -> Decimal:
    """Som van component-maandbedragen voor categorie en optioneel persoon."""
    return sum(
        (c.bedrag_per_maand_actief(jaar, maand) for c in scenario.componenten
         if c.categorie == categorie
         and (persoon is None or c.persoon == persoon)
         and (bedrag_type is None or c.bedrag_type == bedrag_type)),
        Decimal("0"),
    )


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

    # Maandbruto ophalen via componenten + records
    maand_data = []
    for maand in range(1, 13):
        arbeid_p1 = _component_som_maand(
            scenario, CategorieComponent.ARBEIDSINKOMEN, "P1", jaar, maand, BedragType.BRUTO
        )
        arbeid_p2 = (
            _component_som_maand(
                scenario, CategorieComponent.ARBEIDSINKOMEN, "P2", jaar, maand, BedragType.BRUTO
            )
            if persoon2 else Decimal("0")
        )
        arbeid_netto_p1 = _component_som_maand(
            scenario, CategorieComponent.ARBEIDSINKOMEN, "P1", jaar, maand, BedragType.NETTO
        )
        arbeid_netto_p2 = (
            _component_som_maand(
                scenario, CategorieComponent.ARBEIDSINKOMEN, "P2", jaar, maand, BedragType.NETTO
            )
            if persoon2 else Decimal("0")
        )
        overig_p1 = (
            _component_som_maand(
                scenario, CategorieComponent.PENSIOEN_INKOMEN, "P1", jaar, maand, BedragType.BRUTO
            )
            + _component_som_maand(
                scenario, CategorieComponent.OVERIG_INKOMEN, "P1", jaar, maand, BedragType.BRUTO
            )
        )
        overig_p2 = Decimal("0")
        if persoon2:
            overig_p2 = (
                _component_som_maand(
                    scenario, CategorieComponent.PENSIOEN_INKOMEN, "P2", jaar, maand, BedragType.BRUTO
                )
                + _component_som_maand(
                    scenario, CategorieComponent.OVERIG_INKOMEN, "P2", jaar, maand, BedragType.BRUTO
                )
            )
        overig_netto_p1 = (
            _component_som_maand(
                scenario, CategorieComponent.PENSIOEN_INKOMEN, "P1", jaar, maand, BedragType.NETTO
            )
            + _component_som_maand(
                scenario, CategorieComponent.OVERIG_INKOMEN, "P1", jaar, maand, BedragType.NETTO
            )
        )
        overig_netto_p2 = Decimal("0")
        if persoon2:
            overig_netto_p2 = (
                _component_som_maand(
                    scenario, CategorieComponent.PENSIOEN_INKOMEN, "P2", jaar, maand, BedragType.NETTO
                )
                + _component_som_maand(
                    scenario, CategorieComponent.OVERIG_INKOMEN, "P2", jaar, maand, BedragType.NETTO
                )
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
        ontvangst, uitgave_inc = _incidentele_items_voor_maand(scenario, jaar, maand)
        uitgaven_maand = _component_som_maand(scenario, CategorieComponent.UITGAVE, None, jaar, maand)
        inhoudingen_maand = _component_som_maand(scenario, CategorieComponent.INHOUDING, None, jaar, maand)
        maand_data.append({
            "maand": maand,
            "arbeid_p1": arbeid_p1, "arbeid_p2": arbeid_p2,
            "arbeid_netto_p1": arbeid_netto_p1, "arbeid_netto_p2": arbeid_netto_p2,
            "overig_p1": overig_p1, "overig_p2": overig_p2,
            "overig_netto_p1": overig_netto_p1, "overig_netto_p2": overig_netto_p2,
            "aow_p1": aow_p1, "aow_p2": aow_p2,
            "pen_p1": pen_p1, "pen_p2": pen_p2,
            "ontvangst": ontvangst, "uitgave": uitgave_inc,
            "uitgaven": uitgaven_maand, "inhoudingen": inhoudingen_maand,
        })

    # Jaartotalen bruto
    jaar_arbeid_p1 = sum(m["arbeid_p1"] for m in maand_data)
    jaar_arbeid_p2 = sum(m["arbeid_p2"] for m in maand_data)
    jaar_overig_p1 = sum(m["overig_p1"] for m in maand_data)
    jaar_overig_p2 = sum(m["overig_p2"] for m in maand_data)
    jaar_arbeid_netto_p1 = sum(m["arbeid_netto_p1"] for m in maand_data)
    jaar_arbeid_netto_p2 = sum(m["arbeid_netto_p2"] for m in maand_data)
    jaar_overig_netto_p1 = sum(m["overig_netto_p1"] for m in maand_data)
    jaar_overig_netto_p2 = sum(m["overig_netto_p2"] for m in maand_data)
    jaar_aow_p1 = sum(m["aow_p1"] for m in maand_data)
    jaar_aow_p2 = sum(m["aow_p2"] for m in maand_data)
    jaar_pen_p1 = sum(m["pen_p1"] for m in maand_data)
    jaar_pen_p2 = sum(m["pen_p2"] for m in maand_data)
    jaar_netto_component_inkomen = sum(
        m["arbeid_netto_p1"] + m["arbeid_netto_p2"] + m["overig_netto_p1"] + m["overig_netto_p2"]
        for m in maand_data
    )
    jaar_incidenteel_ontvangst = sum(m["ontvangst"] for m in maand_data)
    jaar_incidenteel_uitgave = sum(m["uitgave"] for m in maand_data)
    jaar_inhoudingen = sum(m["inhoudingen"] for m in maand_data)
    jaar_huishoud_uitgaven = sum(m["uitgaven"] for m in maand_data)

    bruto_p1 = jaar_arbeid_p1 + jaar_overig_p1 + jaar_aow_p1 + jaar_pen_p1
    bruto_p2 = jaar_arbeid_p2 + jaar_overig_p2 + jaar_aow_p2 + jaar_pen_p2

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
            saldo_begin_jaar, config, heeft_partner,
            spaargeld_fractie=scenario.box3_spaargeld_fractie,
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
            + mb["overig_p1"] + mb["overig_p2"]
            + mb["arbeid_netto_p1"] + mb["arbeid_netto_p2"]
            + mb["overig_netto_p1"] + mb["overig_netto_p2"]
            + mb["aow_p1"] + mb["aow_p2"]
            + mb["pen_p1"] + mb["pen_p2"]
            - maand_bel_p1 - maand_bel_p2
            + maand_hk_p1 + maand_hk_p2
            - box3_per_maand
            - mb["inhoudingen"]
            - mb["uitgaven"]
            + mb["ontvangst"] - mb["uitgave"]
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
        "jaar_arbeid_p1": Decimal(str(jaar_arbeid_p1)),
        "jaar_arbeid_p2": Decimal(str(jaar_arbeid_p2)),
        "jaar_overig_p1": Decimal(str(jaar_overig_p1)),
        "jaar_overig_p2": Decimal(str(jaar_overig_p2)),
        "jaar_arbeid_netto_p1": Decimal(str(jaar_arbeid_netto_p1)),
        "jaar_arbeid_netto_p2": Decimal(str(jaar_arbeid_netto_p2)),
        "jaar_overig_netto_p1": Decimal(str(jaar_overig_netto_p1)),
        "jaar_overig_netto_p2": Decimal(str(jaar_overig_netto_p2)),
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
        "jaar_netto_component_inkomen": Decimal(str(jaar_netto_component_inkomen)),
        "jaar_incidenteel_ontvangst": Decimal(str(jaar_incidenteel_ontvangst)),
        "jaar_incidenteel_uitgave": Decimal(str(jaar_incidenteel_uitgave)),
        "jaar_inhoudingen": jaar_inhoudingen,
        "jaar_huishoudelijke_uitgaven": jaar_huishoud_uitgaven,
        "box3_vrijstelling": config.box3.vrijstelling_per_persoon * (2 if heeft_partner else 1),
        "box3_belastbaar": max(Decimal("0"), saldo_begin_jaar - config.box3.vrijstelling_per_persoon * (2 if heeft_partner else 1)),
        "box3_spaargeld_fractie": scenario.box3_spaargeld_fractie,
        "box3_forfait_spaargeld": config.box3.forfaitair_spaargeld,
        "box3_forfait_overig": config.box3.forfaitair_overig,
        "box3_tarief": config.box3.tarief,
        "box3_heffing": box3_heffing,
        "ouderenkorting_max": config.ouderenkorting.max_bedrag,
        "ouderenkorting_afbouw_van": config.ouderenkorting.afbouw_inkomen_van,
        "box3_info": box3_info,
        "saldo_begin_jaar": saldo_begin_jaar,
        "maandrendement": maandrendement,
        "inleg_per_jaar": scenario.jaarlijkse_inleg,
        "saldo_einde_jaar": saldo_einde_jaar,
        "jaar_rendement": sum(r["rente"] for r in vermogen_rijen),
        "jaar_netto_cashflow": sum(r["netto_cashflow"] for r in vermogen_rijen),
        "vermogen_rijen": vermogen_rijen,
        "maand_data": maand_data,
    }


def _toon_inkomen_detail(d: dict, naam_p1: str, naam_p2: str | None) -> None:
    """Toon de bruto → netto berekening als genummerde stappen."""
    heeft_p2 = naam_p2 is not None and d["bruto_p2"] > Decimal("0")

    st.markdown("#### A. Bruto inkomsten")
    cols = ["Post", naam_p1] + ([naam_p2] if heeft_p2 else []) + ["Huishouden"]
    rijen = [
        ["Arbeidsinkomen (componenten)",
         _fmt(d["jaar_arbeid_p1"]),
         *([_fmt(d["jaar_arbeid_p2"])] if heeft_p2 else []),
         _fmt(d["jaar_arbeid_p1"] + d["jaar_arbeid_p2"])],
        ["Overig inkomen (componenten)",
         _fmt(d["jaar_overig_p1"]),
         *([_fmt(d["jaar_overig_p2"])] if heeft_p2 else []),
         _fmt(d["jaar_overig_p1"] + d["jaar_overig_p2"])],
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

    # Toelichting ouderenkorting
    ouderenkorting_max = d.get("ouderenkorting_max", Decimal("0"))
    ouderenkorting_afbouw_van = d.get("ouderenkorting_afbouw_van", Decimal("0"))
    if not d["is_aow_p1"] and d["ok_p1"] == Decimal("0"):
        st.caption(
            f"ℹ️ **{naam_p1}**: ouderenkorting = € 0,00 omdat AOW-leeftijd nog niet bereikt is "
            f"(AOW-breuk dit jaar: {float(d['aow_breuk_p1']):.0%}). "
            "Ouderenkorting geldt uitsluitend voor AOW-gerechtigden."
        )
    elif d["is_aow_p1"] and d["ok_p1"] == Decimal("0"):
        st.caption(
            f"ℹ️ **{naam_p1}**: ouderenkorting = € 0,00 omdat bruto inkomen "
            f"({_fmt(d['bruto_p1'])}) boven de afbouwgrens van "
            f"€ {float(ouderenkorting_afbouw_van):,.0f} + max-korting/15% uitkomt. "
            "De korting bouwt volledig af boven dit inkomensniveau."
        )
    if heeft_p2 and not d["is_aow_p2"] and d["ok_p2"] == Decimal("0"):
        st.caption(
            f"ℹ️ **{naam_p2}**: ouderenkorting = € 0,00 omdat AOW-leeftijd nog niet bereikt is."
        )
    elif heeft_p2 and d["is_aow_p2"] and d["ok_p2"] == Decimal("0"):
        st.caption(
            f"ℹ️ **{naam_p2}**: ouderenkorting = € 0,00 door inkomen boven afbouwgrens."
        )

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
        ["Netto componentinkomen (onbelast)",
         _fmt(d["jaar_arbeid_netto_p1"] + d["jaar_overig_netto_p1"]),
         *([_fmt(d["jaar_arbeid_netto_p2"] + d["jaar_overig_netto_p2"])] if heeft_p2 else []),
         _fmt(d["jaar_netto_component_inkomen"])],
        ["**= Totaal netto incl. netto componenten**",
         f"**{_fmt(d['netto_p1'] + d['jaar_arbeid_netto_p1'] + d['jaar_overig_netto_p1'])}**",
         *([
             f"**{_fmt(d['netto_p2'] + d['jaar_arbeid_netto_p2'] + d['jaar_overig_netto_p2'])}**"
         ] if heeft_p2 else []),
         f"**{_fmt(d['totaal_netto_inkomen'] + d['jaar_netto_component_inkomen'])}**"],
    ]
    st.table(_maak_tabel(cols, rijen_d))


def _toon_vermogen_detail(d: dict) -> None:
    """Toon de vermogensberekening: box 3 + maandopbouw."""
    st.markdown("#### E. Box 3 heffing")
    belastbaar = d["box3_belastbaar"]
    fractie_s = d["box3_spaargeld_fractie"]
    fractie_o = Decimal("1") - fractie_s
    deel_spaargeld = (belastbaar * fractie_s).quantize(Decimal("0.01"))
    deel_overig = (belastbaar * fractie_o).quantize(Decimal("0.01"))
    fictief_s = (deel_spaargeld * d["box3_forfait_spaargeld"]).quantize(Decimal("0.01"))
    fictief_o = (deel_overig * d["box3_forfait_overig"]).quantize(Decimal("0.01"))
    fictief_totaal = fictief_s + fictief_o
    rijen_e = [
        ["Vermogen begin jaar", _fmt(d["saldo_begin_jaar"]), ""],
        ["Af: belastingvrije vrijstelling", _fmt(d["box3_vrijstelling"]), ""],
        ["**= Belastbaar vermogen**", f"**{_fmt(belastbaar)}**", ""],
        ["", "", ""],
        [f"Spaargeld ({float(fractie_s)*100:.0f}% × belastbaar)",
         _fmt(deel_spaargeld),
         f"× forfait {float(d['box3_forfait_spaargeld'])*100:.2f}%"],
        ["= Fictief rendement spaargeld", _fmt(fictief_s), ""],
        [f"Beleggingen/overig ({float(fractie_o)*100:.0f}% × belastbaar)",
         _fmt(deel_overig),
         f"× forfait {float(d['box3_forfait_overig'])*100:.2f}%"],
        ["= Fictief rendement beleggingen", _fmt(fictief_o), ""],
        ["**= Totaal fictief rendement**", f"**{_fmt(fictief_totaal)}**", ""],
        ["", "", ""],
        ["× Box 3 belastingtarief", f"{float(d['box3_tarief'])*100:.0f}%", ""],
        ["**= Box 3 heffing (jaar)**", f"**{_fmt(d['box3_heffing'])}**", ""],
    ]
    st.table(_maak_tabel(["Post", "Bedrag", "Toelichting"], rijen_e))
    if d["box3_info"]:
        st.caption(f"⚠️ {d['box3_info']}")

    st.markdown("#### F. Netto cashflow opgebouwd uit losse componenten (jaar)")
    netto_inkomen = d["totaal_netto_inkomen"]
    netto_component_inkomen = d["jaar_netto_component_inkomen"]
    box3 = d["box3_heffing"]
    rendement = d["jaar_rendement"]
    inleg = d["inleg_per_jaar"]
    opname = d["jaar_incidenteel_uitgave"]
    incidentele_ontvangst = d["jaar_incidenteel_ontvangst"]
    inhoudingen = d["jaar_inhoudingen"]
    huishoud_uitgaven = d["jaar_huishoudelijke_uitgaven"]
    netto_cashflow = (
        netto_inkomen
        + netto_component_inkomen
        - inhoudingen
        - box3
        - huishoud_uitgaven
        + rendement
        + inleg
        + incidentele_ontvangst
        - opname
    )

    rijen_f = [
        ["Netto inkomen uit loon/pensioen/AOW (na box 1)", _fmt(netto_inkomen), "Inkomen"],
        ["Netto inkomenscomponenten (onbelast)", _fmt(netto_component_inkomen), "Inkomen"],
        ["Af: inhoudingen", _fmt(inhoudingen), "Inkomen"],
        ["Af: box 3 heffing (belasting over fictief rendement)", _fmt(box3), "Inkomen"],
        ["Af: verwachte huishoudelijke uitgaven", _fmt(huishoud_uitgaven), "Uitgaven"],
        ["Rendement op vermogen", _fmt(rendement), "Vermogen"],
        ["Jaarlijkse inleg", _fmt(inleg), "Inleg/Opname"],
        ["Incidentele ontvangst", _fmt(incidentele_ontvangst), "Inleg/Opname"],
        ["Af: incidentele opname/uitgave", _fmt(opname), "Inleg/Opname"],
        ["**= Netto cashflow jaar**", f"**{_fmt(netto_cashflow)}**", "Controle"],
        ["Mutatie saldo (eind - begin)", _fmt(d["saldo_einde_jaar"] - d["saldo_begin_jaar"]), "Controle"],
    ]
    st.table(_maak_tabel(["Component", "Bedrag", "Deel"], rijen_f))
    st.caption(
        "Formule: Netto cashflow = netto inkomen - inhoudingen - box 3 "
        "- huishouduitgaven + rendement + inleg + incidentele ontvangst - opname "
        "+ netto inkomenscomponenten."
    )

    st.markdown("#### G. Vermogensopbouw per maand")
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
    scenario_namen = [s.naam for s in scenario_lijst]
    default_index = 0
    huidige_keuze = st.session_state.get("acc_scenario_naam")
    if huidige_keuze in scenario_namen:
        default_index = scenario_namen.index(huidige_keuze)
    gekozen_scenario_naam = st.selectbox(
        "Scenario",
        options=scenario_namen,
        index=default_index,
        key="acc_scenario_naam",
    )
    scenario = next((s for s in scenario_lijst if s.naam == gekozen_scenario_naam), scenario_lijst[0])
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
