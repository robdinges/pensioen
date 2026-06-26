"""Scenario generator: converteer TestCase naar Persoon + Scenario objecten.

Dit module converteert testcase data naar de pensioen models
die door de cashflow engine gebruikt kunnen worden.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pensioen.models.component import (
    BedragType,
    CategorieComponent,
    FinancieelComponent,
    Frequentie,
)
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import EigenWoningData, Scenario
from pensioen.models.vermogensitem import VermogensItem, VermogensType
from tests.models.testcase import TestCase, TestPersoon


def genereer_personen(testcase: TestCase) -> list[Persoon]:
    """Genereer Persoon objecten uit TestCase.
    
    Args:
        testcase: TestCase met personen data
        
    Returns:
        List van Persoon objecten (1 of 2)
    """
    personen = []
    
    for idx, test_persoon in enumerate(testcase.personen):
        # Bepaal partner relatie
        heeft_partner = testcase.is_paar
        partner_id = None
        
        if heeft_partner:
            # P1 heeft P2 als partner en vice versa
            partner_id = f"P{2 if idx == 0 else 1}"
        
        persoon = Persoon(
            naam=test_persoon.naam or f"Persoon {idx + 1}",
            geboortedatum=test_persoon.geboortedatum,
            heeft_partner=heeft_partner,
            partner_id=partner_id,
        )
        
        personen.append(persoon)
    
    return personen


def genereer_financiele_componenten(
    testcase: TestCase,
    jaar: int,
) -> list[FinancieelComponent]:
    """Genereer FinancieelComponent objecten voor inkomens.
    
    Args:
        testcase: TestCase met inkomens data
        jaar: Jaar waarvoor componenten gegenereerd worden
        
    Returns:
        List van FinancieelComponent objecten
    """
    componenten = []
    startdatum = date(jaar, 1, 1)
    einddatum = date(jaar, 12, 31)
    
    for idx, persoon in enumerate(testcase.personen):
        persoon_id = f"P{idx + 1}"
        
        # Arbeidsinkomen
        if persoon.bruto_arbeid > 0:
            componenten.append(
                FinancieelComponent(
                    omschrijving=f"Arbeidsinkomen {persoon.naam}",
                    categorie=CategorieComponent.ARBEIDSINKOMEN,
                    bedrag_type=BedragType.BRUTO,
                    bedrag=persoon.bruto_arbeid,
                    frequentie=Frequentie.JAARLIJKS,
                    startdatum=startdatum,
                    einddatum=einddatum,
                    persoon=persoon_id,
                )
            )
        
        # Pensioeninkomen
        if persoon.bruto_pensioen > 0:
            componenten.append(
                FinancieelComponent(
                    omschrijving=f"Pensioen {persoon.naam}",
                    categorie=CategorieComponent.PENSIOEN_INKOMEN,
                    bedrag_type=BedragType.BRUTO,
                    bedrag=persoon.bruto_pensioen,
                    frequentie=Frequentie.JAARLIJKS,
                    startdatum=startdatum,
                    einddatum=einddatum,
                    persoon=persoon_id,
                )
            )
        
        # AOW: SKIP - wordt automatisch berekend door accountant engine via aow_engine
        # Als bruto_aow is opgegeven in testcase, is dit alleen voor validatie van
        # de verwachte waarde, niet om als component toe te voegen.
        
        # Overig inkomen
        if persoon.bruto_overig > 0:
            componenten.append(
                FinancieelComponent(
                    omschrijving=f"Overig inkomen {persoon.naam}",
                    categorie=CategorieComponent.OVERIG_INKOMEN,
                    bedrag_type=BedragType.BRUTO,
                    bedrag=persoon.bruto_overig,
                    frequentie=Frequentie.JAARLIJKS,
                    startdatum=startdatum,
                    einddatum=einddatum,
                    persoon=persoon_id,
                )
            )
    
    return componenten


def genereer_vermogensitems(testcase: TestCase) -> list[VermogensItem]:
    """Genereer VermogensItem objecten voor spaargeld en beleggingen.
    
    Args:
        testcase: TestCase met vermogen data
        
    Returns:
        List van VermogensItem objecten
    """
    items = []
    
    # Spaargeld
    spaargeld = testcase.vermogen.spaargeld_berekend
    if spaargeld > 0:
        items.append(
            VermogensItem(
                omschrijving="Spaargeld",
                type=VermogensType.SPAARGELD,
                persoon="Huishouden",  # verdeling wordt door engine bepaald
                aanschafwaarde=spaargeld,
                groei_pct=Decimal("0"),  # wordt via scenario.rendement_sparen_pct bepaald
                box3_belast=True,
            )
        )
    
    # Beleggingen
    beleggingen = testcase.vermogen.beleggingen_berekend
    if beleggingen > 0:
        items.append(
            VermogensItem(
                omschrijving="Beleggingen",
                type=VermogensType.BELEGGINGEN,
                persoon="Huishouden",
                aanschafwaarde=beleggingen,
                groei_pct=Decimal("0"),  # wordt via scenario.rendement_beleggen_pct bepaald
                box3_belast=True,
            )
        )
    
    return items


def genereer_scenario(
    testcase: TestCase,
    rendement_sparen_pct: Decimal = Decimal("0"),
    rendement_beleggen_pct: Decimal = Decimal("0"),
    inflatie_pct: Decimal = Decimal("0"),
) -> Scenario:
    """Genereer Scenario object uit TestCase.
    
    Args:
        testcase: TestCase met scenario data
        rendement_sparen_pct: Jaarlijks rendement spaargeld (default: 0%)
        rendement_beleggen_pct: Jaarlijks rendement beleggingen (default: 0%)
        inflatie_pct: Jaarlijkse inflatie (default: 0%)
        
    Returns:
        Scenario object met componenten en vermogensitems
    """
    jaar = testcase.jaar
    
    # Genereer componenten
    componenten = genereer_financiele_componenten(testcase, jaar)
    vermogensitems = genereer_vermogensitems(testcase)
    
    # Bereken spaargeld en beleggingen bedragen
    spaargeld_bedrag = testcase.vermogen.spaargeld_berekend
    beleggingen_bedrag = testcase.vermogen.beleggingen_berekend
    
    # Bouw scenario
    scenario = Scenario(
        naam=testcase.naam,
        omschrijving=testcase.metadata.opmerkingen,
        
        # Rendement
        rendement_sparen_pct=rendement_sparen_pct,
        rendement_beleggen_pct=rendement_beleggen_pct,
        inflatie_pct=inflatie_pct,
        
        # Componenten
        componenten=componenten,
        vermogensitems=vermogensitems,
        
        # Legacy velden (voor Box 3 berekening in accountant)
        spaargeld_start=spaargeld_bedrag,
        beleggingen_start=beleggingen_bedrag,
        jaarlijkse_inleg=Decimal("0"),
        box3_spaargeld_fractie=testcase.vermogen.spaargeld_fractie,

        # Eigen woning (box 1)
        heeft_eigen_woning=(testcase.heeft_eigen_huis and testcase.eigen_woning is not None),
        eigen_woning=(
            EigenWoningData(
                woz_waarde=testcase.eigen_woning.woz_waarde,
                betaalde_hypotheekrente=testcase.eigen_woning.betaalde_hypotheekrente,
                overige_aftrekbare_kosten=testcase.eigen_woning.overige_aftrekbare_kosten,
                eigenwoningschuld_begin=testcase.eigen_woning.eigenwoningschuld_begin,
                eigenwoningschuld_eind=testcase.eigen_woning.eigenwoningschuld_eind,
            )
            if testcase.heeft_eigen_huis and testcase.eigen_woning is not None
            else EigenWoningData()
        ),
    )
    
    return scenario


def genereer_testcase_scenario(
    testcase: TestCase,
    rendement_sparen_pct: Decimal = Decimal("0"),
    rendement_beleggen_pct: Decimal = Decimal("0"),
    inflatie_pct: Decimal = Decimal("0"),
) -> tuple[list[Persoon], Scenario]:
    """Genereer complete scenario setup uit TestCase.
    
    Dit is de hoofdfunctie die alle conversie doet.
    
    Args:
        testcase: TestCase om te converteren
        rendement_sparen_pct: Jaarlijks rendement spaargeld
        rendement_beleggen_pct: Jaarlijks rendement beleggingen
        inflatie_pct: Jaarlijkse inflatie
        
    Returns:
        Tuple van (personen, scenario)
        
    Example:
        >>> from tests.testcase_loader import laad_testcase
        >>> tc = laad_testcase(Path("tests/fixtures/belasting_testcases/normalized/tc_2025_001_normalized.json"))
        >>> personen, scenario = genereer_testcase_scenario(tc)
        >>> # Nu kunnen we cashflow berekenen
        >>> from pensioen.calculations.cashflow_engine import bereken_huishouden
        >>> resultaat = bereken_huishouden(personen, scenario)
    """
    personen = genereer_personen(testcase)
    scenario = genereer_scenario(
        testcase,
        rendement_sparen_pct=rendement_sparen_pct,
        rendement_beleggen_pct=rendement_beleggen_pct,
        inflatie_pct=inflatie_pct,
    )
    
    return personen, scenario
