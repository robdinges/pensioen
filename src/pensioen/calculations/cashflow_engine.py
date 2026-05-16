"""Cashflowberekening per maand en jaar voor het huishouden."""

from __future__ import annotations

import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from pensioen.calculations import pensioen_engine, vermogen_engine
from pensioen.models.cashflow import HuishoudCashflow, JaarResultaat, MaandResultaat
from pensioen.models.component import BedragType, CategorieComponent
from pensioen.models.pensioen_record import PensioenRecord
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.tax import aow_engine, belasting_engine
from pensioen.tax.belasting_loader import BelastingConfig

logger = logging.getLogger(__name__)

CENT = Decimal("0.01")


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
) -> Decimal:
    """Som van alle component-maandbedragen voor een categorie en optioneel persoon."""
    totaal = Decimal("0")
    for c in scenario.componenten:
        if c.categorie != categorie:
            continue
        if persoon is not None and c.persoon != persoon:
            continue
        if bedrag_type is not None and c.bedrag_type != bedrag_type:
            continue
        totaal += c.bedrag_per_maand_actief(jaar, maand)
    return totaal


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

    # Accumuleer jaarlijkse totalen voor belastingberekening
    jaar_arbeid_p1 = Decimal("0")
    jaar_arbeid_p2 = Decimal("0")
    jaar_overig_p1 = Decimal("0")
    jaar_overig_p2 = Decimal("0")
    jaar_aow_p1 = Decimal("0")
    jaar_aow_p2 = Decimal("0")
    jaar_pensioen_p1 = Decimal("0")
    jaar_pensioen_p2 = Decimal("0")

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

        # Overig inkomen (pensioen_inkomen + overig_inkomen)
        overig_bruto_p1 = (
            _component_som_maand(
                scenario, CategorieComponent.PENSIOEN_INKOMEN, "P1", jaar, maand, BedragType.BRUTO
            )
            + _component_som_maand(
                scenario, CategorieComponent.OVERIG_INKOMEN, "P1", jaar, maand, BedragType.BRUTO
            )
        )
        overig_bruto_p2 = Decimal("0")
        if persoon2:
            overig_bruto_p2 = (
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

        # AOW
        aow_p1 = pensioen_engine.bereken_aow_maand(
            persoon1.geboortedatum, aow_datum_p1, aow_maandbedrag_p1, jaar, maand
        )
        aow_p2 = Decimal("0")
        if persoon2 and aow_datum_p2:
            aow_p2 = pensioen_engine.bereken_aow_maand(
                persoon2.geboortedatum, aow_datum_p2, aow_maandbedrag_p2, jaar, maand
            )

        # Pensioen uit records (MPO import)
        pen_p1 = sum(
            pensioen_engine.bereken_pensioen_maand(r, jaar, maand)
            for r in records1
        )
        pen_p2 = sum(
            pensioen_engine.bereken_pensioen_maand(r, jaar, maand)
            for r in records2
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

    belasting_p1 = belasting_engine.netto_uit_bruto(
        bruto=bruto_jaar_p1,
        arbeidsinkomen=jaar_arbeid_p1,
        config=belasting_config,
        geboortedatum=persoon1.geboortedatum,
        jaar=jaar,
    )
    belasting_p2_resultaat = None
    if persoon2:
        belasting_p2_resultaat = belasting_engine.netto_uit_bruto(
            bruto=bruto_jaar_p2,
            arbeidsinkomen=jaar_arbeid_p2,
            config=belasting_config,
            geboortedatum=persoon2.geboortedatum,
            jaar=jaar,
        )

    # Maandelijkse belasting = jaarbelasting / 12
    maand_bel_p1 = _rond_af(belasting_p1.belasting / Decimal("12"))
    maand_hk_p1 = _rond_af(belasting_p1.heffingskorting / Decimal("12"))
    maand_bel_p2 = (
        _rond_af(belasting_p2_resultaat.belasting / Decimal("12"))
        if belasting_p2_resultaat else Decimal("0")
    )
    maand_hk_p2 = (
        _rond_af(belasting_p2_resultaat.heffingskorting / Decimal("12"))
        if belasting_p2_resultaat else Decimal("0")
    )

    # --- Stap 3: Box 3 heffing ---
    box3_maand = Decimal("0")
    box3_disclaimer = ""
    if scenario.box3_meenemen and saldo_begin_jaar > Decimal("0"):
        # Bereken dynamische split op basis van actieve componenten aan het begin van het jaar
        peildatum_box3 = date(jaar, 1, 1)
        spaargeld_fractie_box3 = scenario.bereken_spaargeld_fractie_op_datum(peildatum_box3)
        
        box3_jaar, box3_disclaimer = belasting_engine.bereken_box3_heffing(
            saldo_begin_jaar, belasting_config, heeft_partner,
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
            gebruikte_tarieven=belasting_p1.gebruikte_tarieven,
        )
        maandresultaten.append(resultaat)

    jaar_resultaat = JaarResultaat(
        jaar=jaar,
        maanden=maandresultaten,
        tarieven_jaar=belasting_config.jaar,
        tarieven_aanname=aanname_melding,
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
) -> HuishoudCashflow:
    """
    Bereken de volledige cashflowprognose voor het huishouden.

    Args:
        scenario: Planningsscenario met financiële componenten.
        persoon1: Eerste persoon (hoofd).
        persoon2: Tweede persoon (partner), of None.
        records1: Pensioenrecords van persoon1 (uit MPO).
        records2: Pensioenrecords van persoon2 (uit MPO).
        jaar_van: Eerste prognosejaar.
        jaar_tot: Laatste prognosejaar (inclusief).
        belasting_configs: Dict van {jaar: (BelastingConfig, aanname_melding)}.

    Returns:
        HuishoudCashflow met resultaten per jaar en aannames.
    """
    cashflow = HuishoudCashflow(scenario_naam=scenario.naam)
    saldo = scenario.totaal_vermogen_start()

    for jaar in range(jaar_van, jaar_tot + 1):
        config, aanname_melding = belasting_configs[jaar]

        jaar_resultaat = _bereken_jaar(
            jaar=jaar,
            persoon1=persoon1,
            persoon2=persoon2,
            records1=records1,
            records2=records2,
            scenario=scenario,
            belasting_config=config,
            aanname_melding=aanname_melding,
            saldo_begin_jaar=saldo,
        )
        cashflow.jaren.append(jaar_resultaat)
        saldo = jaar_resultaat.vermogen_einde_jaar

    alle_aannames: set[str] = set()
    for jr in cashflow.jaren:
        if jr.tarieven_aanname:
            alle_aannames.add(jr.tarieven_aanname)
    cashflow.aannames = sorted(alle_aannames)

    return cashflow



