"""Cashflowberekening per maand en jaar voor het huishouden."""

from __future__ import annotations

import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from pensioen.calculations import pensioen_engine, vermogen_engine
from pensioen.calculations.detail_output_engine import bouw_accountant_detail, bouw_jaar_samenvatting
from pensioen.calculations.inheritance_engine import resolve_scenario
from pensioen.models.cashflow import (
    BrutoInkomenJaar,
    BrutoInkomenPersoon,
    HuishoudCashflow,
    JaarResultaat,
    MaandResultaat,
)
from pensioen.models.component import BedragType, CategorieComponent, is_handmatige_aow_component
from pensioen.models.pensioen_record import PensioenRecord
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.tax import aow_engine, belasting_engine, heffingskorting
from pensioen.tax.belasting_loader import BelastingConfig
from pensioen.tax.eigen_woning_engine import EigenWoningInvoer, bereken_eigen_woning

logger = logging.getLogger(__name__)

CENT = Decimal("0.01")


def _naar_float(waarde: Decimal | None) -> float | None:
    if waarde is None:
        return None
    return float(waarde)


def _rond_af(bedrag: Decimal) -> Decimal:
    return bedrag.quantize(CENT, rounding=ROUND_HALF_UP)


def _incidentele_items_voor_maand(
    scenario: Scenario, jaar: int, maand: int
) -> tuple[Decimal, Decimal]:
    """Retourneer (ontvangsten, uitgaven) voor incidentele items in de gegeven maand."""
    ontvangst = Decimal("0")
    uitgave = Decimal("0")
    for item in scenario.incidentele_items:
        if item.datum.year == jaar and item.datum.month == maand:
            if item.bedrag >= Decimal("0"):
                ontvangst += item.bedrag
            else:
                uitgave += abs(item.bedrag)
    return ontvangst, uitgave


def _component_som_maand(
    scenario: Scenario,
    categorie: CategorieComponent,
    persoon: str | None,
    jaar: int,
    maand: int,
    bedrag_type: BedragType | None = None,
    negeer_handmatige_aow: bool = False,
) -> Decimal:
    """Som van alle component-maandbedragen voor een categorie en optioneel persoon."""
    totaal = Decimal("0")
    for c in scenario.componenten:
        if c.categorie != categorie:
            continue
        if negeer_handmatige_aow and is_handmatige_aow_component(c):
            continue
        if persoon is not None and c.persoon != persoon:
            continue
        if bedrag_type is not None and c.bedrag_type != bedrag_type:
            continue
        totaal += c.bedrag_per_maand_actief(jaar, maand)
    return totaal


def _heeft_handmatige_aow_componenten(scenario: Scenario) -> bool:
    """Bepaal of het scenario handmatig ingevoerde AOW-componenten bevat."""

    return any(is_handmatige_aow_component(component) for component in scenario.componenten)


def _bouw_accountant_tarieven_payload(
    belasting_p1,
    belasting_p2_resultaat,
    belasting_config: BelastingConfig,
    saldo_begin_jaar: Decimal,
    box3_grondslag_begin_jaar: Decimal,
    scenario: Scenario,
    heeft_partner: bool,
    box3_jaar: Decimal,
    spaargeld_fractie_box3: Decimal,
    box3_bron: str,
    inleg_per_jaar: Decimal,
    maandrendement: Decimal,
    aow_breuk_p1: Decimal,
    aow_breuk_p2: Decimal,
    ew_bron: str,
    ew_woz_waarde: Decimal,
    ew_betaalde_hypotheekrente: Decimal,
    ew_eigenwoningschuld_begin: Decimal,
    ew_woning_items: list,
    ew_hypotheek_items: list,
    ew_p1,
    ew_p2,
    box1_grondslag_p1: Decimal,
    box1_grondslag_p2: Decimal,
    jaar_belasting_p1: Decimal,
    jaar_belasting_p2: Decimal,
    jaar_heffingskorting_p1: Decimal,
    jaar_heffingskorting_p2: Decimal,
) -> dict:
    vrijstelling = belasting_config.box3.vrijstelling_per_persoon * Decimal("2" if heeft_partner else "1")
    belastbaar_vermogen = max(Decimal("0"), box3_grondslag_begin_jaar - vrijstelling)
    gewogen_forfait = (
        spaargeld_fractie_box3 * belasting_config.box3.forfaitair_spaargeld
        + (Decimal("1") - spaargeld_fractie_box3) * belasting_config.box3.forfaitair_overig
    )
    fictief_rendement = belastbaar_vermogen * gewogen_forfait
    verrekende_hk_p1, niet_verrekende_hk_p1 = (
        belasting_engine.begrens_verrekenbare_heffingskorting(
            jaar_heffingskorting_p1,
            jaar_belasting_p1,
        )
    )
    verrekende_hk_p2, niet_verrekende_hk_p2 = (
        belasting_engine.begrens_verrekenbare_heffingskorting(
            jaar_heffingskorting_p2,
            jaar_belasting_p2,
        )
    )

    return {
        "belastingjaar": belasting_config.jaar,
        "persoon1": belasting_p1.gebruikte_tarieven,
        "persoon2": (
            belasting_p2_resultaat.gebruikte_tarieven if belasting_p2_resultaat is not None else None
        ),
        "box3": {
            "box3_meenemen": scenario.box3_meenemen,
            "grondslag_start_vermogen": _naar_float(box3_grondslag_begin_jaar),
            "grondslag_bron": box3_bron,
            "rendement_grondslag_start": _naar_float(saldo_begin_jaar),
            "vrijstelling": _naar_float(vrijstelling),
            "belastbaar_vermogen": _naar_float(belastbaar_vermogen),
            "spaargeld_fractie": _naar_float(spaargeld_fractie_box3),
            "forfaitair_spaargeld": float(belasting_config.box3.forfaitair_spaargeld),
            "forfaitair_overig": float(belasting_config.box3.forfaitair_overig),
            "gewogen_forfait": _naar_float(gewogen_forfait),
            "fictief_rendement": _naar_float(fictief_rendement),
            "tarief": float(belasting_config.box3.tarief),
            "heffing_jaar": _naar_float(box3_jaar),
            "disclaimer": belasting_config.box3.disclaimer,
        },
        "aow": {
            "p1_breuk": _naar_float(aow_breuk_p1),
            "p2_breuk": _naar_float(aow_breuk_p2),
            "p1_is_aow": bool(aow_breuk_p1 > Decimal("0")),
            "p2_is_aow": bool(aow_breuk_p2 > Decimal("0")),
        },
        "eigen_woning": {
            "heeft_invoer": ew_bron != "geen",
            "bron": ew_bron,
            "woz_waarde": _naar_float(ew_woz_waarde),
            "betaalde_hypotheekrente": _naar_float(ew_betaalde_hypotheekrente),
            "eigenwoningschuld_begin": _naar_float(ew_eigenwoningschuld_begin),
            "woning_items": ew_woning_items,
            "hypotheek_items": ew_hypotheek_items,
            "p1": {
                "eigenwoningforfait": _naar_float(ew_p1.eigenwoningforfait),
                "aftrekbare_hypotheekrente": _naar_float(ew_p1.aftrekbare_hypotheekrente),
                "overige_aftrekbare_kosten": _naar_float(ew_p1.overige_aftrekbare_kosten),
                "totaal_aftrek": _naar_float(ew_p1.totaal_aftrek),
                "saldo_eigen_woning": _naar_float(ew_p1.saldo_eigen_woning),
                "hillen_correctie": _naar_float(ew_p1.hillen_correctie),
                "box1_mutatie": _naar_float(ew_p1.box1_mutatie),
                "tariefsaanpassing": _naar_float(ew_p1.tariefsaanpassing),
                "toelichting": ew_p1.toelichting,
            },
            "p2": (
                {
                    "eigenwoningforfait": _naar_float(ew_p2.eigenwoningforfait),
                    "aftrekbare_hypotheekrente": _naar_float(ew_p2.aftrekbare_hypotheekrente),
                    "overige_aftrekbare_kosten": _naar_float(ew_p2.overige_aftrekbare_kosten),
                    "totaal_aftrek": _naar_float(ew_p2.totaal_aftrek),
                    "saldo_eigen_woning": _naar_float(ew_p2.saldo_eigen_woning),
                    "hillen_correctie": _naar_float(ew_p2.hillen_correctie),
                    "box1_mutatie": _naar_float(ew_p2.box1_mutatie),
                    "tariefsaanpassing": _naar_float(ew_p2.tariefsaanpassing),
                    "toelichting": ew_p2.toelichting,
                }
                if ew_p2 is not None
                else None
            ),
        },
        "box1": {
            "grondslag_p1": _naar_float(box1_grondslag_p1),
            "grondslag_p2": _naar_float(box1_grondslag_p2),
            "belasting_voor_korting_p1": _naar_float(belasting_p1.inkomstenbelasting),
            "belasting_voor_korting_p2": (
                _naar_float(belasting_p2_resultaat.inkomstenbelasting)
                if belasting_p2_resultaat is not None
                else _naar_float(Decimal("0"))
            ),
            "premie_aow_p1": _naar_float(belasting_p1.premie_aow),
            "premie_anw_p1": _naar_float(belasting_p1.premie_anw),
            "premie_wlz_p1": _naar_float(belasting_p1.premie_wlz),
            "totaal_premies_p1": _naar_float(belasting_p1.totaal_premies),
            "premie_aow_p2": (
                _naar_float(belasting_p2_resultaat.premie_aow)
                if belasting_p2_resultaat is not None
                else _naar_float(Decimal("0"))
            ),
            "premie_anw_p2": (
                _naar_float(belasting_p2_resultaat.premie_anw)
                if belasting_p2_resultaat is not None
                else _naar_float(Decimal("0"))
            ),
            "premie_wlz_p2": (
                _naar_float(belasting_p2_resultaat.premie_wlz)
                if belasting_p2_resultaat is not None
                else _naar_float(Decimal("0"))
            ),
            "totaal_premies_p2": (
                _naar_float(belasting_p2_resultaat.totaal_premies)
                if belasting_p2_resultaat is not None
                else _naar_float(Decimal("0"))
            ),
            "totale_hk_p1": _naar_float(jaar_heffingskorting_p1),
            "totale_hk_p2": _naar_float(jaar_heffingskorting_p2),
            "verrekende_hk_p1": _naar_float(verrekende_hk_p1),
            "verrekende_hk_p2": _naar_float(verrekende_hk_p2),
            "niet_verrekende_hk_p1": _naar_float(niet_verrekende_hk_p1),
            "niet_verrekende_hk_p2": _naar_float(niet_verrekende_hk_p2),
            "totaal_ib_en_premies_p1": _naar_float(jaar_belasting_p1),
            "totaal_ib_en_premies_p2": _naar_float(jaar_belasting_p2),
            "netto_bel_p1": _naar_float(max(Decimal("0"), jaar_belasting_p1 - jaar_heffingskorting_p1)),
            "netto_bel_p2": _naar_float(max(Decimal("0"), jaar_belasting_p2 - jaar_heffingskorting_p2)),
            "netto_p1": _naar_float(max(Decimal("0"), box1_grondslag_p1 - max(Decimal("0"), jaar_belasting_p1 - jaar_heffingskorting_p1))),
            "netto_p2": _naar_float(max(Decimal("0"), box1_grondslag_p2 - max(Decimal("0"), jaar_belasting_p2 - jaar_heffingskorting_p2))),
            "totaal_netto_inkomen": _naar_float(
                max(Decimal("0"), box1_grondslag_p1 - max(Decimal("0"), jaar_belasting_p1 - jaar_heffingskorting_p1))
                + max(Decimal("0"), box1_grondslag_p2 - max(Decimal("0"), jaar_belasting_p2 - jaar_heffingskorting_p2))
            ),
        },
        "vermogen": {
            "saldo_begin_jaar": _naar_float(saldo_begin_jaar),
            "inleg_per_jaar": _naar_float(inleg_per_jaar),
            "maandrendement": _naar_float(maandrendement),
        },
    }


def _bereken_jaar(
    jaar: int,
    persoon1: Persoon,
    persoon2: Persoon | None,
    records1: list[PensioenRecord],
    records2: list[PensioenRecord],
    scenario: Scenario,
    belasting_config: BelastingConfig,
    aanname_melding: str,
    saldo_begin_jaar: Decimal,
    box3_grondslag_begin_jaar: Decimal,
    box3_bron: str,
) -> JaarResultaat:
    """
    Bereken alle cashflows voor één kalenderjaar voor het huishouden.

    Aanpak:
    1. Bereken maandelijkse bruto inkomsten voor beide personen.
    2. Sommeer tot jaarbedragen voor belastingberekening.
    3. Bereken jaarbelasting per persoon.
    4. Verdeel belasting evenredig over maanden.
    5. Bereken maandelijks vermogen inclusief rendement.
    """
    # --- AOW-datums ---
    aow_datum_p1 = aow_engine.bereken_aow_datum(persoon1.geboortedatum)
    aow_datum_p2 = (
        aow_engine.bereken_aow_datum(persoon2.geboortedatum) if persoon2 else None
    )

    # --- AOW-bedragen per maand ---
    heeft_partner = persoon2 is not None
    aow_maandbedrag_p1 = (
        belasting_config.aow_bedrag.gehuwd_of_samenwonend_per_maand
        if heeft_partner
        else belasting_config.aow_bedrag.alleenstaande_per_maand
    )
    aow_maandbedrag_p2 = (
        belasting_config.aow_bedrag.gehuwd_of_samenwonend_per_maand
        if heeft_partner
        else belasting_config.aow_bedrag.alleenstaande_per_maand
    )

    # --- Stap 1: Maandelijkse bruto berekening ---
    maandresultaten: list[MaandResultaat] = []
    saldo = saldo_begin_jaar
    handmatige_aow_gevonden = _heeft_handmatige_aow_componenten(scenario)

    # Accumuleer jaarlijkse totalen voor belastingberekening
    jaar_arbeid_p1 = Decimal("0")
    jaar_arbeid_p2 = Decimal("0")
    jaar_overig_p1 = Decimal("0")
    jaar_overig_p2 = Decimal("0")
    jaar_aow_p1 = Decimal("0")
    jaar_aow_p2 = Decimal("0")
    jaar_pensioen_p1 = Decimal("0")
    jaar_pensioen_p2 = Decimal("0")
    aow_breuk_p1 = aow_engine.aow_breuk_jaar(persoon1.geboortedatum, jaar)
    aow_breuk_p2 = (
        aow_engine.aow_breuk_jaar(persoon2.geboortedatum, jaar) if persoon2 else Decimal("0")
    )

    maand_bruto: list[dict] = []

    for maand in range(1, 13):
        # Arbeidsinkomen uit componenten (bruto wordt belast, netto niet)
        arbeid_bruto_p1 = _component_som_maand(
            scenario, CategorieComponent.ARBEIDSINKOMEN, "P1", jaar, maand, BedragType.BRUTO
        )
        arbeid_bruto_p2 = (
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

        # Overig inkomen (alleen OVERIG_INKOMEN componenten, PENSIOEN_INKOMEN wordt apart geteld)
        overig_bruto_p1 = _component_som_maand(
            scenario,
            CategorieComponent.OVERIG_INKOMEN,
            "P1",
            jaar,
            maand,
            BedragType.BRUTO,
            negeer_handmatige_aow=True,
        )
        overig_bruto_p2 = Decimal("0")
        if persoon2:
            overig_bruto_p2 = _component_som_maand(
                scenario,
                CategorieComponent.OVERIG_INKOMEN,
                "P2",
                jaar,
                maand,
                BedragType.BRUTO,
                negeer_handmatige_aow=True,
            )
        overig_netto_p1 = _component_som_maand(
            scenario,
            CategorieComponent.OVERIG_INKOMEN,
            "P1",
            jaar,
            maand,
            BedragType.NETTO,
            negeer_handmatige_aow=True,
        )
        overig_netto_p2 = Decimal("0")
        if persoon2:
            overig_netto_p2 = _component_som_maand(
                scenario,
                CategorieComponent.OVERIG_INKOMEN,
                "P2",
                jaar,
                maand,
                BedragType.NETTO,
                negeer_handmatige_aow=True,
            )

        # AOW
        aow_p1 = pensioen_engine.bereken_aow_maand(
            persoon1.geboortedatum, aow_datum_p1, aow_maandbedrag_p1, jaar, maand
        )
        aow_p2 = Decimal("0")
        if persoon2 and aow_datum_p2:
            aow_p2 = pensioen_engine.bereken_aow_maand(
                persoon2.geboortedatum, aow_datum_p2, aow_maandbedrag_p2, jaar, maand
            )

        # Pensioen uit componenten (PENSIOEN_INKOMEN)
        # Deze worden gebruikt voor de grafiekweergave (pensioen_p1_bruto, pensioen_p2_bruto)
        pen_p1 = _component_som_maand(
            scenario, CategorieComponent.PENSIOEN_INKOMEN, "P1", jaar, maand, BedragType.BRUTO
        )
        pen_p2 = Decimal("0")
        if persoon2:
            pen_p2 = _component_som_maand(
                scenario, CategorieComponent.PENSIOEN_INKOMEN, "P2", jaar, maand, BedragType.BRUTO
            )

        # Uitgaven en inhoudingen uit componenten
        uitgaven_maand = (
            _component_som_maand(scenario, CategorieComponent.UITGAVE, None, jaar, maand)
        )
        inhoudingen_maand = (
            _component_som_maand(scenario, CategorieComponent.INHOUDING, None, jaar, maand)
        )

        # Incidenteel
        ontvangst, uitgave = _incidentele_items_voor_maand(scenario, jaar, maand)

        maand_bruto.append({
            "maand": maand,
            "arbeid_p1": arbeid_bruto_p1,
            "arbeid_p2": arbeid_bruto_p2,
            "arbeid_netto_p1": arbeid_netto_p1,
            "arbeid_netto_p2": arbeid_netto_p2,
            "overig_p1": overig_bruto_p1,
            "overig_p2": overig_bruto_p2,
            "overig_netto_p1": overig_netto_p1,
            "overig_netto_p2": overig_netto_p2,
            "aow_p1": aow_p1,
            "aow_p2": aow_p2,
            "pen_p1": Decimal(str(pen_p1)),
            "pen_p2": Decimal(str(pen_p2)),
            "uitgaven": uitgaven_maand,
            "inhoudingen": inhoudingen_maand,
            "ontvangst": ontvangst,
            "uitgave": uitgave,
        })

        jaar_arbeid_p1 += arbeid_bruto_p1
        jaar_arbeid_p2 += arbeid_bruto_p2
        jaar_overig_p1 += overig_bruto_p1
        jaar_overig_p2 += overig_bruto_p2
        jaar_aow_p1 += aow_p1
        jaar_aow_p2 += aow_p2
        jaar_pensioen_p1 += Decimal(str(pen_p1))
        jaar_pensioen_p2 += Decimal(str(pen_p2))

    # --- Stap 2: Jaarbelasting per persoon ---
    bruto_jaar_p1 = jaar_arbeid_p1 + jaar_overig_p1 + jaar_aow_p1 + jaar_pensioen_p1
    bruto_jaar_p2 = jaar_arbeid_p2 + jaar_overig_p2 + jaar_aow_p2 + jaar_pensioen_p2

    eigen_woning_invoer = scenario.verzamel_fiscale_eigen_woning_invoer(
        jaar=jaar,
        heeft_partner=heeft_partner,
    )
    heeft_eigen_woning_invoer = bool(eigen_woning_invoer["heeft_invoer"])

    ew_p1 = bereken_eigen_woning(
        EigenWoningInvoer(
            woz_waarde=eigen_woning_invoer["p1"].woz_waarde if heeft_eigen_woning_invoer else Decimal("0"),
            betaalde_hypotheekrente=(
                eigen_woning_invoer["p1"].betaalde_hypotheekrente if heeft_eigen_woning_invoer else Decimal("0")
            ),
            overige_aftrekbare_kosten=(
                eigen_woning_invoer["p1"].overige_aftrekbare_kosten if heeft_eigen_woning_invoer else Decimal("0")
            ),
            eigenwoningschuld_begin=(
                eigen_woning_invoer["p1"].eigenwoningschuld_begin if heeft_eigen_woning_invoer else Decimal("0")
            ),
            eigenwoningschuld_eind=(
                eigen_woning_invoer["p1"].eigenwoningschuld_eind if heeft_eigen_woning_invoer else Decimal("0")
            ),
            bruto_inkomen_box1=bruto_jaar_p1,
        ),
        belasting_config,
    )
    ew_p2 = None
    if persoon2:
        ew_p2 = bereken_eigen_woning(
            EigenWoningInvoer(
                woz_waarde=(
                    eigen_woning_invoer["p2"].woz_waarde
                    if heeft_eigen_woning_invoer and eigen_woning_invoer["p2"] is not None
                    else Decimal("0")
                ),
                betaalde_hypotheekrente=(
                    eigen_woning_invoer["p2"].betaalde_hypotheekrente
                    if heeft_eigen_woning_invoer and eigen_woning_invoer["p2"] is not None
                    else Decimal("0")
                ),
                overige_aftrekbare_kosten=(
                    eigen_woning_invoer["p2"].overige_aftrekbare_kosten
                    if heeft_eigen_woning_invoer and eigen_woning_invoer["p2"] is not None
                    else Decimal("0")
                ),
                eigenwoningschuld_begin=(
                    eigen_woning_invoer["p2"].eigenwoningschuld_begin
                    if heeft_eigen_woning_invoer and eigen_woning_invoer["p2"] is not None
                    else Decimal("0")
                ),
                eigenwoningschuld_eind=(
                    eigen_woning_invoer["p2"].eigenwoningschuld_eind
                    if heeft_eigen_woning_invoer and eigen_woning_invoer["p2"] is not None
                    else Decimal("0")
                ),
                bruto_inkomen_box1=bruto_jaar_p2,
            ),
            belasting_config,
        )

    box1_grondslag_p1 = max(Decimal("0"), bruto_jaar_p1 + ew_p1.box1_mutatie)
    box1_grondslag_p2 = max(
        Decimal("0"),
        bruto_jaar_p2 + (ew_p2.box1_mutatie if ew_p2 is not None else Decimal("0")),
    )

    belasting_p1 = belasting_engine.netto_uit_bruto(
        bruto=box1_grondslag_p1,
        arbeidsinkomen=jaar_arbeid_p1,
        config=belasting_config,
        geboortedatum=persoon1.geboortedatum,
        jaar=jaar,
        is_alleenstaand=not heeft_partner,
    )
    belasting_p2_resultaat = None
    if persoon2:
        belasting_p2_resultaat = belasting_engine.netto_uit_bruto(
            bruto=box1_grondslag_p2,
            arbeidsinkomen=jaar_arbeid_p2,
            config=belasting_config,
            geboortedatum=persoon2.geboortedatum,
            jaar=jaar,
            is_alleenstaand=False,
        )

    jaar_belasting_p1 = belasting_p1.belasting + ew_p1.tariefsaanpassing
    is_aow_p1 = aow_breuk_p1 > Decimal("0")
    ahk_inkomen_p1 = box1_grondslag_p1 if is_aow_p1 else bruto_jaar_p1
    ahk_p1 = belasting_engine.rond_af(
        heffingskorting.bereken_ahk_met_aow(ahk_inkomen_p1, belasting_config, aow_breuk_p1)
    )
    ak_p1 = belasting_engine.rond_af(heffingskorting.bereken_arbeidskorting(jaar_arbeid_p1, belasting_config))
    ok_p1 = belasting_engine.rond_af(
        heffingskorting.bereken_ouderenkorting(box1_grondslag_p1, belasting_config, is_aow_p1)
    )
    aok_p1 = belasting_engine.rond_af(
        heffingskorting.bereken_alleenstaandeouderenkorting(
            box1_grondslag_p1,
            belasting_config,
            is_aow_p1,
            is_alleenstaand=not heeft_partner,
        )
    )
    jaar_heffingskorting_p1 = ahk_p1 + ak_p1 + ok_p1 + aok_p1
    belasting_p1.heffingskorting = jaar_heffingskorting_p1
    belasting_p1.gebruikte_tarieven.update(
        {
            "ahk": float(ahk_p1),
            "arbeidskorting": float(ak_p1),
            "ouderenkorting": float(ok_p1),
            "alleenstaandeouderenkorting": float(aok_p1),
        }
    )
    jaar_belasting_p2 = Decimal("0")
    jaar_heffingskorting_p2 = Decimal("0")
    if belasting_p2_resultaat is not None:
        jaar_belasting_p2 = belasting_p2_resultaat.belasting + (
            ew_p2.tariefsaanpassing if ew_p2 is not None else Decimal("0")
        )
        is_aow_p2 = aow_breuk_p2 > Decimal("0")
        ahk_inkomen_p2 = box1_grondslag_p2 if is_aow_p2 else bruto_jaar_p2
        ahk_p2 = belasting_engine.rond_af(
            heffingskorting.bereken_ahk_met_aow(ahk_inkomen_p2, belasting_config, aow_breuk_p2)
        )
        ak_p2 = belasting_engine.rond_af(
            heffingskorting.bereken_arbeidskorting(jaar_arbeid_p2, belasting_config)
        )
        ok_p2 = belasting_engine.rond_af(
            heffingskorting.bereken_ouderenkorting(box1_grondslag_p2, belasting_config, is_aow_p2)
        )
        jaar_heffingskorting_p2 = ahk_p2 + ak_p2 + ok_p2
        belasting_p2_resultaat.heffingskorting = jaar_heffingskorting_p2
        belasting_p2_resultaat.gebruikte_tarieven.update(
            {
                "ahk": float(ahk_p2),
                "arbeidskorting": float(ak_p2),
                "ouderenkorting": float(ok_p2),
                "alleenstaandeouderenkorting": float(Decimal("0")),
            }
        )

    # Maandelijkse belasting = jaarbelasting / 12
    maand_bel_p1 = _rond_af(jaar_belasting_p1 / Decimal("12"))
    maand_hk_p1 = _rond_af(jaar_heffingskorting_p1 / Decimal("12"))
    maand_bel_p2 = (
        _rond_af(jaar_belasting_p2 / Decimal("12"))
        if belasting_p2_resultaat else Decimal("0")
    )
    maand_hk_p2 = (
        _rond_af(jaar_heffingskorting_p2 / Decimal("12"))
        if belasting_p2_resultaat else Decimal("0")
    )

    # --- Stap 3: Box 3 heffing ---
    box3_maand = Decimal("0")
    box3_jaar = Decimal("0")
    box3_disclaimer = ""
    spaargeld_fractie_box3 = scenario.bereken_spaargeld_fractie_startvermogen(date(jaar, 1, 1))
    if scenario.box3_meenemen and box3_grondslag_begin_jaar > Decimal("0"):
        # Box 3 peildatum gebruikt startverdeling (1 januari), niet maandcomponenten.
        box3_jaar, box3_disclaimer = belasting_engine.bereken_box3_heffing(
            box3_grondslag_begin_jaar,
            belasting_config,
            heeft_partner,
            spaargeld_fractie=spaargeld_fractie_box3,
        )
        box3_maand = _rond_af(box3_jaar / Decimal("12"))

    # --- Stap 4: Jaarlijkse inleg ---
    inleg_per_maand = Decimal("0")
    totale_inleg = scenario.totaal_jaarlijkse_inleg()
    if totale_inleg > Decimal("0"):
        inleg_per_maand = _rond_af(totale_inleg / Decimal("12"))

    # --- Stap 5: Maandresultaten samenstellen ---
    aannames: list[str] = []
    if aanname_melding:
        aannames.append(aanname_melding)
    if box3_disclaimer and scenario.box3_meenemen:
        aannames.append(box3_disclaimer)
    if handmatige_aow_gevonden and (jaar_aow_p1 > Decimal("0") or jaar_aow_p2 > Decimal("0")):
        aannames.append(
            "Handmatige AOW-component gedetecteerd: automatische AOW blijft leidend en handmatige AOW is uit inkomenssommen gefilterd."
        )
    if records1 or records2:
        aannames.append(
            "PensioenRecord-invoer ontvangen, maar pensioenbron in de engine is Scenario.componenten (PENSIOEN_INKOMEN)."
        )
    if heeft_eigen_woning_invoer:
        aannames.append(
            f"Eigen woning stap actief (bron: {eigen_woning_invoer['bron']}); box-1 grondslag bevat eigen-woningmutatie en tariefsaanpassing."
        )
    if scenario.box3_meenemen:
        aannames.append(
            f"Box 3 grondslag bron: {box3_bron}; rendementsgrondslag start op € {saldo_begin_jaar:,}."
        )

    maandrendement = vermogen_engine.maandrendement(scenario.rendement_pct or Decimal("0"))

    bruto_inkomen = BrutoInkomenJaar(
        p1=BrutoInkomenPersoon(
            arbeid=jaar_arbeid_p1,
            aow=jaar_aow_p1,
            pensioen=jaar_pensioen_p1,
            overig=jaar_overig_p1,
        ),
        p2=BrutoInkomenPersoon(
            arbeid=jaar_arbeid_p2,
            aow=jaar_aow_p2,
            pensioen=jaar_pensioen_p2,
            overig=jaar_overig_p2,
        ),
    )

    for mb in maand_bruto:
        maand = mb["maand"]

        # Bereken dynamische split tussen sparen en beleggen op basis van actieve componenten
        peildatum = date(jaar, maand, 1)
        spaargeld_fractie_dynamisch = scenario.bereken_spaargeld_fractie_op_datum(peildatum)

        rente = vermogen_engine.bereken_rente_maand(
            saldo,
            scenario.rendement_pct,
            scenario.rendement_sparen_pct,
            scenario.rendement_beleggen_pct,
            spaargeld_fractie_dynamisch,
        )

        netto_cashflow = (
            mb["arbeid_p1"] + mb["arbeid_p2"]
            + mb["overig_p1"] + mb["overig_p2"]
            + mb["arbeid_netto_p1"] + mb["arbeid_netto_p2"]
            + mb["overig_netto_p1"] + mb["overig_netto_p2"]
            + mb["aow_p1"] + mb["aow_p2"]
            + mb["pen_p1"] + mb["pen_p2"]
            - maand_bel_p1 - maand_bel_p2
            + maand_hk_p1 + maand_hk_p2
            - box3_maand
            - mb["inhoudingen"]
            - mb["uitgaven"]
            + mb["ontvangst"] - mb["uitgave"]
            + rente
            + inleg_per_maand
        )
        saldo = max(Decimal("0"), _rond_af(saldo + netto_cashflow))

        resultaat = MaandResultaat(
            jaar=jaar,
            maand=maand,
            arbeid_p1_bruto=mb["arbeid_p1"],
            arbeid_p2_bruto=mb["arbeid_p2"],
            aow_p1_bruto=mb["aow_p1"],
            aow_p2_bruto=mb["aow_p2"],
            pensioen_p1_bruto=mb["pen_p1"],
            pensioen_p2_bruto=mb["pen_p2"],
            overig_bruto=mb["overig_p1"] + mb["overig_p2"],
            inkomen_componenten_netto=(
                mb["arbeid_netto_p1"]
                + mb["arbeid_netto_p2"]
                + mb["overig_netto_p1"]
                + mb["overig_netto_p2"]
            ),
            rente_bruto=rente,
            eenmalig_ontvangst=mb["ontvangst"],
            eenmalig_uitgave=mb["uitgave"],
            belasting_p1=maand_bel_p1,
            heffingskorting_p1=maand_hk_p1,
            belasting_p2=maand_bel_p2,
            heffingskorting_p2=maand_hk_p2,
            box3_heffing=box3_maand,
            inhoudingen=mb["inhoudingen"],
            huishoudelijke_uitgaven=mb["uitgaven"],
            vermogen_einde_maand=saldo,
            aannames=list(aannames),
            gebruikte_tarieven=_bouw_accountant_tarieven_payload(
                belasting_p1,
                belasting_p2_resultaat,
                belasting_config,
                saldo_begin_jaar,
                box3_grondslag_begin_jaar,
                scenario,
                heeft_partner,
                box3_jaar,
                spaargeld_fractie_box3,
                box3_bron,
                totale_inleg,
                maandrendement,
                aow_breuk_p1,
                aow_breuk_p2,
                eigen_woning_invoer["bron"],
                eigen_woning_invoer["huishouden"].woz_waarde,
                eigen_woning_invoer["huishouden"].betaalde_hypotheekrente,
                eigen_woning_invoer["huishouden"].eigenwoningschuld_begin,
                eigen_woning_invoer["woning_items"],
                eigen_woning_invoer["hypotheek_items"],
                ew_p1,
                ew_p2,
                box1_grondslag_p1,
                box1_grondslag_p2,
                jaar_belasting_p1,
                jaar_belasting_p2,
                jaar_heffingskorting_p1,
                jaar_heffingskorting_p2,
            ),
        )
        maandresultaten.append(resultaat)

    jaar_resultaat = JaarResultaat(
        jaar=jaar,
        maanden=maandresultaten,
        tarieven_jaar=belasting_config.jaar,
        tarieven_aanname=aanname_melding,
        bruto_inkomen=bruto_inkomen,
    )
    jaar_resultaat.jaar_samenvatting = bouw_jaar_samenvatting(jaar_resultaat)
    jaar_resultaat.accountant_detail = bouw_accountant_detail(
        jaar_resultaat,
        aanname=aanname_melding,
        tarief_bronnen={},
        records_aangeleverd=len(records1) + len(records2),
    )
    return jaar_resultaat


def bereken_huishouden(
    scenario: Scenario,
    persoon1: Persoon,
    persoon2: Persoon | None,
    records1: list[PensioenRecord],
    records2: list[PensioenRecord],
    jaar_van: int,
    jaar_tot: int,
    belasting_configs: dict[int, tuple[BelastingConfig, str]],
    scenario_lijst: list[Scenario] | None = None,
) -> HuishoudCashflow:
    """
    Bereken de volledige cashflowprognose voor het huishouden.

    Args:
        scenario: Planningsscenario met financiële componenten.
        persoon1: Eerste persoon (hoofd).
        persoon2: Tweede persoon (partner), of None.
        records1: Pensioenrecords van persoon1 (uit MPO, niet leidend in berekening).
        records2: Pensioenrecords van persoon2 (uit MPO, niet leidend in berekening).
        jaar_van: Eerste prognosejaar.
        jaar_tot: Laatste prognosejaar (inclusief).
        belasting_configs: Dict van {jaar: (BelastingConfig, aanname_melding)}.
        scenario_lijst: Lijst van alle scenario's (voor inheritance resolution).
            Als None: scenario wordt niet geresolveerd (backward compatible).

    Returns:
        HuishoudCashflow met resultaten per jaar en aannames.
    """
    # Resolve scenario als het een afgeleid scenario is
    if scenario.is_derived_scenario() and scenario_lijst is not None:
        logger.info(
            f"Resolving derived scenario '{scenario.naam}' (parent: {scenario.parent_naam})"
        )
        scenario_resolved = resolve_scenario(scenario, scenario_lijst)
    else:
        scenario_resolved = scenario

    cashflow = HuishoudCashflow(scenario_naam=scenario_resolved.naam)
    startwaarden_vermogen = scenario_resolved.bepaal_vermogen_startwaarden(date(jaar_van, 1, 1))
    saldo = Decimal(str(startwaarden_vermogen["liquide_startvermogen"]))
    box3_grondslag = Decimal(str(startwaarden_vermogen["box3_grondslag"]))
    box3_bron = str(startwaarden_vermogen["bron"])

    for jaar in range(jaar_van, jaar_tot + 1):
        config, aanname_melding = belasting_configs[jaar]

        jaar_resultaat = _bereken_jaar(
            jaar=jaar,
            persoon1=persoon1,
            persoon2=persoon2,
            records1=records1,
            records2=records2,
            scenario=scenario_resolved,  # Use resolved scenario
            belasting_config=config,
            aanname_melding=aanname_melding,
            saldo_begin_jaar=saldo,
            box3_grondslag_begin_jaar=box3_grondslag,
            box3_bron=box3_bron,
        )
        cashflow.jaren.append(jaar_resultaat)
        saldo = jaar_resultaat.vermogen_einde_jaar
        box3_grondslag = saldo
        box3_bron = "prognose_saldo"

    alle_aannames: set[str] = set()
    for jr in cashflow.jaren:
        if jr.tarieven_aanname:
            alle_aannames.add(jr.tarieven_aanname)
    cashflow.aannames = sorted(alle_aannames)

    return cashflow

