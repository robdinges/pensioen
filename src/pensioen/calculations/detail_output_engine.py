"""Detailoutput-assembler voor accountant, rapportage en API-consumenten."""

from __future__ import annotations

from decimal import Decimal

from pensioen.models.cashflow import JaarResultaat, MaandResultaat
from pensioen.tax.eigen_woning_engine import EigenWoningResultaat


CENT = Decimal("0.01")


def _d(waarde) -> Decimal:
    if isinstance(waarde, Decimal):
        return waarde
    if waarde is None:
        return Decimal("0")
    return Decimal(str(waarde))


def _som_maanden(maanden: list[MaandResultaat], selector) -> Decimal:
    return sum((_d(selector(maand)) for maand in maanden), Decimal("0"))


def bouw_jaar_samenvatting(jaar_resultaat: JaarResultaat) -> dict[str, Decimal | int]:
    """Bouw een compacte jaarsamenvatting uit maandoutput van de engine."""
    maanden = jaar_resultaat.maanden
    if not maanden:
        return {
            "jaar": jaar_resultaat.jaar,
            "bruto": Decimal("0"),
            "belasting": Decimal("0"),
            "netto": Decimal("0"),
            "netto_per_maand": Decimal("0"),
            "vermogen_einde_jaar": Decimal("0"),
        }

    bruto = _som_maanden(maanden, lambda m: m.totaal_bruto)
    belasting = _som_maanden(maanden, lambda m: m.totaal_belasting)
    netto = _som_maanden(maanden, lambda m: m.netto)
    netto_per_maand = (netto / Decimal(str(len(maanden)))).quantize(CENT)
    vermogen_einde_jaar = _d(maanden[-1].vermogen_einde_maand)

    return {
        "jaar": jaar_resultaat.jaar,
        "bruto": bruto,
        "belasting": belasting,
        "netto": netto,
        "netto_per_maand": netto_per_maand,
        "vermogen_einde_jaar": vermogen_einde_jaar,
        "arbeid_p1": _som_maanden(maanden, lambda m: m.arbeid_p1_bruto),
        "arbeid_p2": _som_maanden(maanden, lambda m: m.arbeid_p2_bruto),
        "aow_p1": _som_maanden(maanden, lambda m: m.aow_p1_bruto),
        "aow_p2": _som_maanden(maanden, lambda m: m.aow_p2_bruto),
        "pensioen_p1": _som_maanden(maanden, lambda m: m.pensioen_p1_bruto),
        "pensioen_p2": _som_maanden(maanden, lambda m: m.pensioen_p2_bruto),
        "overig": _som_maanden(maanden, lambda m: m.overig_bruto),
        "rendement": _som_maanden(maanden, lambda m: m.rente_bruto),
        "inhoudingen": _som_maanden(maanden, lambda m: m.inhoudingen),
        "huishoudelijke_uitgaven": _som_maanden(maanden, lambda m: m.huishoudelijke_uitgaven),
        "eenmalig_ontvangst": _som_maanden(maanden, lambda m: m.eenmalig_ontvangst),
        "eenmalig_uitgave": _som_maanden(maanden, lambda m: m.eenmalig_uitgave),
    }


def _bouw_eigen_woning_resultaat(payload: dict | None) -> EigenWoningResultaat:
    payload = payload or {}
    return EigenWoningResultaat(
        eigenwoningforfait=_d(payload.get("eigenwoningforfait")),
        aftrekbare_hypotheekrente=_d(payload.get("aftrekbare_hypotheekrente")),
        overige_aftrekbare_kosten=_d(payload.get("overige_aftrekbare_kosten")),
        totaal_aftrek=_d(payload.get("totaal_aftrek")),
        saldo_eigen_woning=_d(payload.get("saldo_eigen_woning")),
        hillen_correctie=_d(payload.get("hillen_correctie")),
        box1_mutatie=_d(payload.get("box1_mutatie")),
        tariefsaanpassing=_d(payload.get("tariefsaanpassing")),
        box3_bezittingen=Decimal("0"),
        box3_schulden=Decimal("0"),
        toelichting=list(payload.get("toelichting") or []),
    )


def bouw_accountant_detail(
    jaar_resultaat: JaarResultaat,
    aanname: str,
    tarief_bronnen: dict[str, str] | None = None,
    records_aangeleverd: int = 0,
) -> dict:
    """Bouw accountantdetail uitsluitend uit engine-output van het jaarresultaat."""
    maanden = jaar_resultaat.maanden
    if not maanden:
        return {
            "jaar": jaar_resultaat.jaar,
            "aanname": aanname,
            "tarief_bronnen": tarief_bronnen or {},
        }

    eerste_maand = maanden[0]
    tarieven_payload = eerste_maand.gebruikte_tarieven or {}

    p1_payload = tarieven_payload.get("persoon1", {})
    p2_payload = tarieven_payload.get("persoon2") or {}
    box3_payload = tarieven_payload.get("box3", {})
    box1_payload = tarieven_payload.get("box1", {})
    ew_payload = tarieven_payload.get("eigen_woning", {})
    aow_payload = tarieven_payload.get("aow", {})
    vermogen_payload = tarieven_payload.get("vermogen", {})

    jaar_arbeid_p1 = _som_maanden(maanden, lambda m: m.arbeid_p1_bruto)
    jaar_arbeid_p2 = _som_maanden(maanden, lambda m: m.arbeid_p2_bruto)
    jaar_overig = _som_maanden(maanden, lambda m: m.overig_bruto)
    jaar_aow_p1 = _som_maanden(maanden, lambda m: m.aow_p1_bruto)
    jaar_aow_p2 = _som_maanden(maanden, lambda m: m.aow_p2_bruto)
    jaar_pen_p1 = _som_maanden(maanden, lambda m: m.pensioen_p1_bruto)
    jaar_pen_p2 = _som_maanden(maanden, lambda m: m.pensioen_p2_bruto)

    jaar_arbeid_netto = _som_maanden(maanden, lambda m: m.inkomen_componenten_netto)
    jaar_inhoudingen = _som_maanden(maanden, lambda m: m.inhoudingen)
    jaar_huishoud_uitgaven = _som_maanden(maanden, lambda m: m.huishoudelijke_uitgaven)
    jaar_incidenteel_ontvangst = _som_maanden(maanden, lambda m: m.eenmalig_ontvangst)
    jaar_incidenteel_uitgave = _som_maanden(maanden, lambda m: m.eenmalig_uitgave)

    bruto_p1 = jaar_arbeid_p1 + jaar_aow_p1 + jaar_pen_p1
    bruto_p2 = jaar_arbeid_p2 + jaar_aow_p2 + jaar_pen_p2

    ew_p1 = _bouw_eigen_woning_resultaat(ew_payload.get("p1"))
    ew_p2_data = ew_payload.get("p2")
    ew_p2 = _bouw_eigen_woning_resultaat(ew_p2_data) if ew_p2_data else None

    saldo_begin_jaar = _d(vermogen_payload.get("saldo_begin_jaar"))
    inleg_per_jaar = _d(vermogen_payload.get("inleg_per_jaar"))
    inleg_per_maand = (inleg_per_jaar / Decimal("12")).quantize(CENT) if inleg_per_jaar else Decimal("0")

    vermogen_rijen = []
    saldo_begin_maand = saldo_begin_jaar
    for maand in maanden:
        netto_cashflow = maand.netto + inleg_per_maand
        vermogen_rijen.append(
            {
                "maand": maand.maand,
                "saldo_begin": saldo_begin_maand,
                "rente": _d(maand.rente_bruto),
                "netto_cashflow": netto_cashflow,
                "saldo_eind": _d(maand.vermogen_einde_maand),
            }
        )
        saldo_begin_maand = _d(maand.vermogen_einde_maand)

    maand_data = [
        {
            "maand": maand.maand,
            "arbeid_p1": _d(maand.arbeid_p1_bruto),
            "arbeid_p2": _d(maand.arbeid_p2_bruto),
            "arbeid_netto_p1": Decimal("0"),
            "arbeid_netto_p2": Decimal("0"),
            "overig_p1": _d(maand.overig_bruto),
            "overig_p2": Decimal("0"),
            "overig_netto_p1": Decimal("0"),
            "overig_netto_p2": Decimal("0"),
            "aow_p1": _d(maand.aow_p1_bruto),
            "aow_p2": _d(maand.aow_p2_bruto),
            "pen_p1": _d(maand.pensioen_p1_bruto),
            "pen_p2": _d(maand.pensioen_p2_bruto),
            "ontvangst": _d(maand.eenmalig_ontvangst),
            "uitgave": _d(maand.eenmalig_uitgave),
            "uitgaven": _d(maand.huishoudelijke_uitgaven),
            "inhoudingen": _d(maand.inhoudingen),
        }
        for maand in maanden
    ]

    detail = {
        "jaar": jaar_resultaat.jaar,
        "config_jaar": jaar_resultaat.tarieven_jaar,
        "aanname": aanname,
        "pensioenbron": "scenario_componenten",
        "pensioen_records_genegeerd": records_aangeleverd,
        "tarief_bronnen": tarief_bronnen or {},
        "jaar_arbeid_p1": jaar_arbeid_p1,
        "jaar_arbeid_p2": jaar_arbeid_p2,
        "jaar_overig_p1": jaar_overig,
        "jaar_overig_p2": Decimal("0"),
        "jaar_arbeid_netto_p1": jaar_arbeid_netto,
        "jaar_arbeid_netto_p2": Decimal("0"),
        "jaar_overig_netto_p1": Decimal("0"),
        "jaar_overig_netto_p2": Decimal("0"),
        "jaar_aow_p1": jaar_aow_p1,
        "jaar_aow_p2": jaar_aow_p2,
        "jaar_pen_p1": jaar_pen_p1,
        "jaar_pen_p2": jaar_pen_p2,
        "bruto_p1": bruto_p1,
        "bruto_p2": bruto_p2,
        "box1_grondslag_p1": _d(box1_payload.get("grondslag_p1")),
        "box1_grondslag_p2": _d(box1_payload.get("grondslag_p2")),
        "ew_p1": ew_p1,
        "ew_p2": ew_p2,
        "ew_invoer_gevonden": bool(ew_payload.get("heeft_invoer")),
        "ew_bron": ew_payload.get("bron", "geen"),
        "ew_huishouden": ew_payload.get("huishouden", {}),
        "ew_invoer_p1": None,
        "ew_invoer_p2": None,
        "ew_woning_items": ew_payload.get("woning_items") or [],
        "ew_hypotheek_items": ew_payload.get("hypotheek_items") or [],
        "ew_woz_waarde": _d(ew_payload.get("woz_waarde")),
        "ew_betaalde_hypotheekrente": _d(ew_payload.get("betaalde_hypotheekrente")),
        "ew_schuld_begin": _d(ew_payload.get("eigenwoningschuld_begin")),
        "aow_breuk_p1": _d(aow_payload.get("p1_breuk")),
        "aow_breuk_p2": _d(aow_payload.get("p2_breuk")),
        "is_aow_p1": bool(aow_payload.get("p1_is_aow")),
        "is_aow_p2": bool(aow_payload.get("p2_is_aow")),
        "bel_voor_korting_p1": _d(box1_payload.get("belasting_voor_korting_p1")),
        "bel_voor_korting_p2": _d(box1_payload.get("belasting_voor_korting_p2")),
        "premie_aow_p1": _d(box1_payload.get("premie_aow_p1")),
        "premie_anw_p1": _d(box1_payload.get("premie_anw_p1")),
        "premie_wlz_p1": _d(box1_payload.get("premie_wlz_p1")),
        "totaal_premies_p1": _d(box1_payload.get("totaal_premies_p1")),
        "premie_aow_p2": _d(box1_payload.get("premie_aow_p2")),
        "premie_anw_p2": _d(box1_payload.get("premie_anw_p2")),
        "premie_wlz_p2": _d(box1_payload.get("premie_wlz_p2")),
        "totaal_premies_p2": _d(box1_payload.get("totaal_premies_p2")),
        "totaal_ib_en_premies_p1": _d(box1_payload.get("totaal_ib_en_premies_p1")),
        "totaal_ib_en_premies_p2": _d(box1_payload.get("totaal_ib_en_premies_p2")),
        "ahk_p1": _d(p1_payload.get("ahk")),
        "ak_p1": _d(p1_payload.get("arbeidskorting")),
        "ok_p1": _d(p1_payload.get("ouderenkorting")),
        "aok_p1": _d(p1_payload.get("alleenstaandeouderenkorting")),
        "ahk_p2": _d(p2_payload.get("ahk")),
        "ak_p2": _d(p2_payload.get("arbeidskorting")),
        "ok_p2": _d(p2_payload.get("ouderenkorting")),
        "aok_p2": _d(p2_payload.get("alleenstaandeouderenkorting")),
        "totale_hk_p1": _d(box1_payload.get("totale_hk_p1")),
        "totale_hk_p2": _d(box1_payload.get("totale_hk_p2")),
        "verrekende_hk_p1": _d(box1_payload.get("verrekende_hk_p1")),
        "verrekende_hk_p2": _d(box1_payload.get("verrekende_hk_p2")),
        "niet_verrekende_hk_p1": _d(box1_payload.get("niet_verrekende_hk_p1")),
        "niet_verrekende_hk_p2": _d(box1_payload.get("niet_verrekende_hk_p2")),
        "netto_bel_p1": _d(box1_payload.get("netto_bel_p1")),
        "netto_bel_p2": _d(box1_payload.get("netto_bel_p2")),
        "netto_p1": _d(box1_payload.get("netto_p1")),
        "netto_p2": _d(box1_payload.get("netto_p2")),
        "totaal_netto_inkomen": _d(box1_payload.get("totaal_netto_inkomen")),
        "jaar_netto_component_inkomen": jaar_arbeid_netto,
        "jaar_incidenteel_ontvangst": jaar_incidenteel_ontvangst,
        "jaar_incidenteel_uitgave": jaar_incidenteel_uitgave,
        "jaar_inhoudingen": jaar_inhoudingen,
        "jaar_huishoudelijke_uitgaven": jaar_huishoud_uitgaven,
        "box3_vrijstelling": _d(box3_payload.get("vrijstelling")),
        "box3_belastbaar": _d(box3_payload.get("belastbaar_vermogen")),
        "box3_spaargeld_fractie": _d(box3_payload.get("spaargeld_fractie")),
        "box3_forfait_spaargeld": _d(box3_payload.get("forfaitair_spaargeld")),
        "box3_forfait_overig": _d(box3_payload.get("forfaitair_overig")),
        "box3_fictief_rendement": _d(box3_payload.get("fictief_rendement")),
        "box3_tarief": _d(box3_payload.get("tarief")),
        "box3_bron_tarief": (tarief_bronnen or {}).get("box3_tarief", "basisconfig"),
        "box3_bron_forfait_spaargeld": (tarief_bronnen or {}).get("box3_forfait_spaargeld", "basisconfig"),
        "box3_bron_forfait_overig": (tarief_bronnen or {}).get("box3_forfait_overig", "basisconfig"),
        "box3_heffing": _d(box3_payload.get("heffing_jaar")),
        "ouderenkorting_max": Decimal("0"),
        "ouderenkorting_afbouw_van": Decimal("0"),
        "box3_info": box3_payload.get("disclaimer", ""),
        "aow_waarschuwingen": [
            aanname for aanname in eerste_maand.aannames if "Handmatige AOW-component" in aanname
        ],
        "saldo_begin_jaar": saldo_begin_jaar,
        "maandrendement": _d(vermogen_payload.get("maandrendement")),
        "inleg_per_jaar": inleg_per_jaar,
        "saldo_einde_jaar": _d(maanden[-1].vermogen_einde_maand),
        "jaar_rendement": _som_maanden(maanden, lambda m: m.rente_bruto),
        "jaar_netto_cashflow": _som_maanden(maanden, lambda m: m.netto) + inleg_per_jaar,
        "vermogen_rijen": vermogen_rijen,
        "maand_data": maand_data,
    }

    return detail
