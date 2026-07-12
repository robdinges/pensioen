"""Streamlit-pagina: gedetailleerde accountantsberekening (2026-2030)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import streamlit as st

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.calculations.detail_output_engine import bouw_accountant_detail
from pensioen.models.component import BedragType, CategorieComponent, is_handmatige_aow_component
from pensioen.tax import belasting_engine
from pensioen.tax.belasting_loader import BelastingConfig, laad_tarieven, resolve_tariefwaarden_voor_jaar
from pensioen.tax.eigen_woning_engine import EigenWoningInvoer, EigenWoningResultaat, bereken_eigen_woning
from pensioen.ui.flow_context import Stap, set_huidge_stap
from pensioen.ui.scenario_context import get_actief_scenario


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


def _heeft_eigen_woning_effect(resultaat: EigenWoningResultaat | None) -> bool:
    """Bepaal of een eigen-woningresultaat zichtbaar moet zijn in het overzicht."""
    if resultaat is None:
        return False

    return any(
        waarde != Decimal("0")
        for waarde in (
            resultaat.eigenwoningforfait,
            resultaat.aftrekbare_hypotheekrente,
            resultaat.overige_aftrekbare_kosten,
            resultaat.saldo_eigen_woning,
            resultaat.hillen_correctie,
            resultaat.box1_mutatie,
            resultaat.tariefsaanpassing,
        )
    )


def _bereken_eigen_woning_voor_weergave(
    d: dict,
    heeft_partner: bool,
    config: BelastingConfig,
) -> tuple[EigenWoningResultaat, EigenWoningResultaat | None]:
    """Bereken eigen-woningregels direct uit de bronwaarden voor de accountantstabel."""
    ew_invoer_p1 = d.get("ew_invoer_p1")
    ew_invoer_p2 = d.get("ew_invoer_p2")
    if ew_invoer_p1 is None:
        factor_p1 = Decimal("0.5") if heeft_partner else Decimal("1")
        ew_invoer_p1 = EigenWoningInvoer(
            woz_waarde=d.get("ew_woz_waarde", Decimal("0")) * factor_p1,
            betaalde_hypotheekrente=d.get("ew_betaalde_hypotheekrente", Decimal("0")) * factor_p1,
            overige_aftrekbare_kosten=Decimal("0") * factor_p1,
            eigenwoningschuld_begin=d.get("ew_schuld_begin", Decimal("0")) * factor_p1,
            eigenwoningschuld_eind=d.get("ew_schuld_begin", Decimal("0")) * factor_p1,
            bruto_inkomen_box1=d.get("bruto_p1", Decimal("0")),
        )

    ew_p1 = bereken_eigen_woning(
        ew_invoer_p1,
        config,
    )

    if not heeft_partner:
        return ew_p1, None

    if ew_invoer_p2 is None:
        factor_p2 = Decimal("0.5")
        ew_invoer_p2 = EigenWoningInvoer(
            woz_waarde=d.get("ew_woz_waarde", Decimal("0")) * factor_p2,
            betaalde_hypotheekrente=d.get("ew_betaalde_hypotheekrente", Decimal("0")) * factor_p2,
            overige_aftrekbare_kosten=Decimal("0") * factor_p2,
            eigenwoningschuld_begin=d.get("ew_schuld_begin", Decimal("0")) * factor_p2,
            eigenwoningschuld_eind=d.get("ew_schuld_begin", Decimal("0")) * factor_p2,
            bruto_inkomen_box1=d.get("bruto_p2", Decimal("0")),
        )

    ew_p2 = bereken_eigen_woning(
        ew_invoer_p2,
        config,
    )
    return ew_p1, ew_p2


def _component_som_maand(scenario, categorie, persoon, jaar: int, maand: int, bedrag_type: BedragType | None = None) -> Decimal:
    """Som van component-maandbedragen voor categorie en optioneel persoon."""
    return sum(
        (c.bedrag_per_maand_actief(jaar, maand) for c in scenario.componenten
         if c.categorie == categorie
         and not is_handmatige_aow_component(c)
         and (persoon is None or c.persoon == persoon)
         and (bedrag_type is None or c.bedrag_type == bedrag_type)),
        Decimal("0"),
    )


def _handmatige_aow_componenten(scenario, jaar: int) -> list[str]:
    """Geef actieve handmatige AOW-componenten terug voor een belastingjaar."""

    gevonden: list[str] = []
    for component in scenario.componenten:
        if not is_handmatige_aow_component(component):
            continue
        if any(component.is_actief(jaar, maand) for maand in range(1, 13)):
            gevonden.append(component.omschrijving)
    return gevonden


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
    tarief_bronnen: dict[str, str] | None = None,
) -> dict:
    """Bouw accountantdetail uit engine-output voor exact één kalenderjaar."""
    eenjaars_cashflow = bereken_huishouden(
        scenario=scenario,
        persoon1=persoon1,
        persoon2=persoon2,
        records1=records1,
        records2=records2,
        jaar_van=jaar,
        jaar_tot=jaar,
        belasting_configs={jaar: (config, aanname)},
    )
    jr = eenjaars_cashflow.jaren[0]
    detail = bouw_accountant_detail(
        jr,
        aanname=aanname,
        tarief_bronnen=tarief_bronnen,
        records_aangeleverd=len(records1) + len(records2),
    )
    detail["aow_waarschuwingen"] = _handmatige_aow_componenten(scenario, jaar)

    # Houd expliciet het externally supplied beginjaar-saldo aan voor accountantcontroles.
    detail["saldo_begin_jaar"] = saldo_begin_jaar
    return detail


def _toon_inkomen_detail(d: dict, naam_p1: str, naam_p2: str | None, config: BelastingConfig) -> None:
    """Toon de bruto → netto berekening als genummerde stappen."""
    heeft_p2 = naam_p2 is not None and d["bruto_p2"] > Decimal("0")

    if d.get("aow_waarschuwingen"):
        st.warning(
            "Handmatige AOW-component(en) gedetecteerd: "
            + ", ".join(d["aow_waarschuwingen"])
            + ". Automatische AOW blijft leidend; deze componenten zijn uit de inkomenssommen gefilterd om dubbeltelling te voorkomen."
        )

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

    # B.0 Eigen woning (optioneel)
    ew1: EigenWoningResultaat = d.get("ew_p1")
    ew2: EigenWoningResultaat = d.get("ew_p2")
    if d.get("ew_invoer_gevonden", False) and not _heeft_eigen_woning_effect(ew1) and not _heeft_eigen_woning_effect(ew2):
        ew1, ew2 = _bereken_eigen_woning_voor_weergave(d, heeft_p2, config)
    heeft_ew = d.get("ew_invoer_gevonden", False) or _heeft_eigen_woning_effect(ew1) or _heeft_eigen_woning_effect(ew2)
    if heeft_ew:
        st.markdown("#### A.1 Eigen woning (saldo box 1)")
        st.caption(
            "Bron: Vermogen & Bezittingen"
            f" • WOZ-waarde: {_fmt(d.get('ew_woz_waarde', Decimal('0')))}"
            f" • Hypotheekrente: {_fmt(d.get('ew_betaalde_hypotheekrente', Decimal('0')))}"
            f" • Hypotheekschuld: {_fmt(d.get('ew_schuld_begin', Decimal('0')))}"
        )
        if d.get("ew_woning_items") or d.get("ew_hypotheek_items"):
            st.caption(
                f"Gevonden invoerregels: {len(d.get('ew_woning_items', []))} woning(en), "
                f"{len(d.get('ew_hypotheek_items', []))} hypotheek(en)"
            )
        rijen_ew = [
            ["Eigenwoningforfait",
             _fmt(ew1.eigenwoningforfait),
             *([_fmt(ew2.eigenwoningforfait)] if heeft_p2 and ew2 else []),
             _fmt((ew1.eigenwoningforfait) + (ew2.eigenwoningforfait if heeft_p2 and ew2 else Decimal("0")))],
            ["Hypotheekrenteaftrek",
             _fmt(-ew1.aftrekbare_hypotheekrente),
             *([_fmt(-ew2.aftrekbare_hypotheekrente)] if heeft_p2 and ew2 else []),
             _fmt(-(ew1.aftrekbare_hypotheekrente + (ew2.aftrekbare_hypotheekrente if heeft_p2 and ew2 else Decimal("0"))))],
            ["Overige aftrekbare kosten",
             _fmt(-ew1.overige_aftrekbare_kosten),
             *([_fmt(-ew2.overige_aftrekbare_kosten)] if heeft_p2 and ew2 else []),
             _fmt(-(ew1.overige_aftrekbare_kosten + (ew2.overige_aftrekbare_kosten if heeft_p2 and ew2 else Decimal("0"))))],
            ["Saldo eigen woning",
             _fmt(ew1.saldo_eigen_woning),
             *([_fmt(ew2.saldo_eigen_woning)] if heeft_p2 and ew2 else []),
             _fmt(ew1.saldo_eigen_woning + (ew2.saldo_eigen_woning if heeft_p2 and ew2 else Decimal("0")))],
            ["Wet Hillen-vermindering",
             _fmt(-ew1.hillen_correctie),
             *([_fmt(-ew2.hillen_correctie)] if heeft_p2 and ew2 else []),
             _fmt(-(ew1.hillen_correctie + (ew2.hillen_correctie if heeft_p2 and ew2 else Decimal("0"))))],
            ["**Box 1-correctie (mutatie grondslag)**",
             f"**{_fmt(ew1.box1_mutatie)}**",
             *([f"**{_fmt(ew2.box1_mutatie)}**"] if heeft_p2 and ew2 else []),
             f"**{_fmt(ew1.box1_mutatie + (ew2.box1_mutatie if heeft_p2 and ew2 else Decimal('0')))}**"],
            ["Tariefsaanpassing aftrekposten",
             _fmt(ew1.tariefsaanpassing),
             *([_fmt(ew2.tariefsaanpassing)] if heeft_p2 and ew2 else []),
             _fmt(ew1.tariefsaanpassing + (ew2.tariefsaanpassing if heeft_p2 and ew2 else Decimal("0")))],
            ["**Belastbaar inkomen box 1**",
             f"**{_fmt(d['box1_grondslag_p1'])}**",
             *([f"**{_fmt(d['box1_grondslag_p2'])}**"] if heeft_p2 else []),
             f"**{_fmt(d['box1_grondslag_p1'] + d['box1_grondslag_p2'])}**"],
        ]
        st.table(_maak_tabel(cols, rijen_ew))
        if ew1.toelichting:
            with st.expander("Toelichting eigen woning berekening"):
                for regel in ew1.toelichting:
                    st.caption(regel)
                if heeft_p2 and ew2 and ew2.toelichting:
                    st.caption("--- partner ---")
                    for regel in ew2.toelichting:
                        st.caption(regel)

    st.markdown("#### B. Box 1 inkomstenbelasting (IB)")
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
        ["Belastbaar inkomen box 1",
         _fmt(d["box1_grondslag_p1"]),
         *([_fmt(d["box1_grondslag_p2"])] if heeft_p2 else []),
         _fmt(d["box1_grondslag_p1"] + d["box1_grondslag_p2"])],
        ["Inkomstenbelasting (IB) schijventarief *",
         _fmt(d["bel_voor_korting_p1"]),
         *([_fmt(d["bel_voor_korting_p2"])] if heeft_p2 else []),
         _fmt(d["bel_voor_korting_p1"] + d["bel_voor_korting_p2"])],
    ]
    st.table(_maak_tabel(cols, rijen_b))
    aow_delen = []
    for i, schijf in enumerate(config.box1_aow, start=1):
        grens = f"≤ €{float(schijf.tot):,.0f}" if schijf.tot is not None else "zonder bovengrens"
        aow_delen.append(f"schijf {i} {grens}: {float(schijf.tarief) * 100:.2f}%")

    niet_aow_delen = []
    for i, schijf in enumerate(config.box1_niet_aow, start=1):
        grens = f"≤ €{float(schijf.tot):,.0f}" if schijf.tot is not None else "zonder bovengrens"
        niet_aow_delen.append(f"schijf {i} {grens}: {float(schijf.tarief) * 100:.2f}%")

    st.caption(
        f"\\* IB-tarieven ({config.jaar}, ZONDER premies) - "
        f"AOW: {' | '.join(aow_delen)}. "
        f"Niet-AOW: {' | '.join(niet_aow_delen)}."
    )

    st.markdown("#### C. Premies volksverzekeringen")
    premiegrens = config.premies.premiegrens if config.premies else Decimal("0")
    rijen_premies = [
        ["AOW-premie (alleen niet-AOW)",
         _fmt(d["premie_aow_p1"]),
         *([_fmt(d["premie_aow_p2"])] if heeft_p2 else []),
         _fmt(d["premie_aow_p1"] + d["premie_aow_p2"])],
        ["Anw-premie",
         _fmt(d["premie_anw_p1"]),
         *([_fmt(d["premie_anw_p2"])] if heeft_p2 else []),
         _fmt(d["premie_anw_p1"] + d["premie_anw_p2"])],
        ["Wlz-premie",
         _fmt(d["premie_wlz_p1"]),
         *([_fmt(d["premie_wlz_p2"])] if heeft_p2 else []),
         _fmt(d["premie_wlz_p1"] + d["premie_wlz_p2"])],
        ["**Totaal premies**",
         f"**{_fmt(d['totaal_premies_p1'])}**",
         *([f"**{_fmt(d['totaal_premies_p2'])}**"] if heeft_p2 else []),
         f"**{_fmt(d['totaal_premies_p1'] + d['totaal_premies_p2'])}**"],
    ]
    st.table(_maak_tabel(cols, rijen_premies))
    st.caption(
        f"ℹ️ Premies worden alleen geheven over inkomen tot de premiegrens "
        f"(€{float(premiegrens):,.0f} in {config.jaar}). "
        f"AOW-premie (17,9%) geldt alleen voor niet-AOW-gerechtigden."
    )

    st.markdown("#### D. Heffingskortingen")
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
        ["Alleenstaandeouderenkorting",
         _fmt(d["aok_p1"]),
         *([_fmt(d["aok_p2"])] if heeft_p2 else []),
         _fmt(d["aok_p1"] + d["aok_p2"])],
        ["**Totaal kortingen**",
         f"**{_fmt(d['totale_hk_p1'])}**",
         *([f"**{_fmt(d['totale_hk_p2'])}**"] if heeft_p2 else []),
         f"**{_fmt(d['totale_hk_p1'] + d['totale_hk_p2'])}**"],
    ]
    st.table(_maak_tabel(cols, rijen_c))

    # Toelichting ouderenkorting
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

    st.markdown("#### E. Totaal verschuldigd belasting en premies")
    rijen_d = [
        ["IB vóór kortingen (B)",
         _fmt(d["bel_voor_korting_p1"]),
         *([_fmt(d["bel_voor_korting_p2"])] if heeft_p2 else []),
         _fmt(d["bel_voor_korting_p1"] + d["bel_voor_korting_p2"])],
        ["Premies volksverzekeringen (C)",
         _fmt(d["totaal_premies_p1"]),
         *([_fmt(d["totaal_premies_p2"])] if heeft_p2 else []),
         _fmt(d["totaal_premies_p1"] + d["totaal_premies_p2"])],
        ["Tariefsaanpassing eigen woning",
         _fmt(d["ew_p1"].tariefsaanpassing if d.get("ew_p1") else Decimal("0")),
         *([_fmt(d["ew_p2"].tariefsaanpassing if d.get("ew_p2") else Decimal("0"))] if heeft_p2 else []),
         _fmt((d["ew_p1"].tariefsaanpassing if d.get("ew_p1") else Decimal("0"))
              + (d["ew_p2"].tariefsaanpassing if heeft_p2 and d.get("ew_p2") else Decimal("0")))],
        ["**= Totaal IB + premies**",
         f"**{_fmt(d['totaal_ib_en_premies_p1'])}**",
         *([f"**{_fmt(d['totaal_ib_en_premies_p2'])}**"] if heeft_p2 else []),
         f"**{_fmt(d['totaal_ib_en_premies_p1'] + d['totaal_ib_en_premies_p2'])}**"],
        ["Af: totaal heffingskortingen (D)",
         _fmt(d["totale_hk_p1"]),
         *([_fmt(d["totale_hk_p2"])] if heeft_p2 else []),
         _fmt(d["totale_hk_p1"] + d["totale_hk_p2"])],
        ["**= Totaal verschuldigd Box 1**",
         f"**{_fmt(d['netto_bel_p1'])}**",
         *([f"**{_fmt(d['netto_bel_p2'])}**"] if heeft_p2 else []),
         f"**{_fmt(d['netto_bel_p1'] + d['netto_bel_p2'])}**"],
    ]
    st.table(_maak_tabel(cols, rijen_d))
    
    st.markdown("#### F. Netto inkomen")
    rijen_f = [
        ["Bruto inkomen (A)",
         _fmt(d["bruto_p1"]),
         *([_fmt(d["bruto_p2"])] if heeft_p2 else []),
         _fmt(d["bruto_p1"] + d["bruto_p2"])],
        ["Af: verschuldigd Box 1 (E)",
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
    st.table(_maak_tabel(cols, rijen_f))


def _toon_vermogen_detail(d: dict) -> None:
    """Toon de vermogensberekening: box 3 + maandopbouw."""
    st.markdown("#### G. Box 3 heffing")
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
    st.caption(
        "Bronnen box 3: "
        f"tarief = {d['box3_bron_tarief']}; "
        f"forfait spaargeld = {d['box3_bron_forfait_spaargeld']}; "
        f"forfait overig = {d['box3_bron_forfait_overig']}."
    )
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
    st.header("Accountantsoverzicht")
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
    # Pensioenen zijn nu componenten, geen records meer
    records1 = []
    records2 = []
    actief = get_actief_scenario(scenario_lijst)
    if actief is None:
        st.warning("⚠️ Geen actief scenario beschikbaar.")
        return

    scenario_ruw = actief
    scenario = scenario_ruw
    st.caption(f"Actief scenario: {scenario_ruw.naam}")
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

    st.caption("Overzicht wordt automatisch herberekend bij wijzigingen in personen of scenario.")
    saldo = scenario.totaal_vermogen_op_datum(date(int(jaar_van), 1, 1))

    for jaar in range(int(jaar_van), int(jaar_tot) + 1):
        config_basis, aanname = laad_tarieven(jaar)
        config, tarief_bronnen = resolve_tariefwaarden_voor_jaar(
            config_basis,
            jaar,
            scenario.tarief_periodes,
        )

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
            tarief_bronnen=tarief_bronnen,
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

            if d.get("tarief_bronnen"):
                st.caption(
                    "Tariefbronnen dit jaar: "
                    f"box1 niet-AOW schijf 1 tarief = {d['tarief_bronnen'].get('box1_niet_aow_s1_tarief', 'basisconfig')}; "
                    f"box1 AOW schijf 1 tarief = {d['tarief_bronnen'].get('box1_aow_s1_tarief', 'basisconfig')}; "
                    f"box3 tarief = {d['tarief_bronnen'].get('box3_tarief', 'basisconfig')}; "
                    f"box3 forfait spaargeld = {d['tarief_bronnen'].get('box3_forfait_spaargeld', 'basisconfig')}; "
                    f"box3 forfait overig = {d['tarief_bronnen'].get('box3_forfait_overig', 'basisconfig')}."
                )

            st.markdown(
                f"**Scenario:** {scenario.naam}  |  "
                f"**Persoon 1:** {persoon1.naam}  |  "
                + (f"**Persoon 2:** {persoon2.naam}  |  " if persoon2 else "")
                + f"**Belastingjaar (tarieven):** {config.jaar}"
            )

            _toon_inkomen_detail(d, persoon1.naam, naam_p2, config)
            st.divider()
            _toon_vermogen_detail(d)

        saldo = d["saldo_einde_jaar"]

    # ─── Vorige/Volgende knoppen ────────────────────────────────────────────
    st.divider()
    col_vorige, col_volgende = st.columns(2)
    
    with col_vorige:
        if st.button("← Vorige"):
            set_huidge_stap(Stap.RESULTATEN, validatie_ok=False)
            st.rerun()
    
    with col_volgende:
        if st.button("Volgende →", use_container_width=True):
            set_huidge_stap(Stap.RAPPORT, validatie_ok=True)
            st.rerun()
