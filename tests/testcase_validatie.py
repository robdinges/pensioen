"""Testcase validatie: bereken belasting voor 1 jaar en vergelijk met verwachte waarde.

Dit module biedt functies om een testcase te valideren door de belasting
te berekenen en te vergelijken met de verwachte belasting uit de testcase.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from pensioen.tax.belasting_loader import laad_tarieven
from pensioen.tax import belasting_engine, heffingskorting
from tests.models.testcase import TestCase
from tests.scenario_generator import genereer_personen, genereer_testcase_scenario

# Import accountant helper (internal function)
from pensioen.ui.pagina_accountant import _bereken_jaar_detail


def bereken_belasting_testcase(testcase: TestCase) -> dict:
    """Bereken belasting voor testcase (1 jaar).
    
    Args:
        testcase: TestCase om te berekenen
        
    Returns:
        Dict met berekeningsdetails (zoals van _bereken_jaar_detail)
    """
    # Genereer scenario
    personen, scenario = genereer_testcase_scenario(testcase)
    
    persoon1 = personen[0]
    persoon2 = personen[1] if len(personen) > 1 else None
    
    # Laad belastingtarieven
    config, aanname = laad_tarieven(testcase.jaar)
    
    # Geen pensioenrecords (allemaal via componenten)
    records1 = []
    records2 = []
    
    # Beginsaldo
    saldo_begin_jaar = testcase.vermogen.totaal
    
    # Bereken met accountant logica
    resultaat = _bereken_jaar_detail(
        jaar=testcase.jaar,
        persoon1=persoon1,
        persoon2=persoon2,
        records1=records1,
        records2=records2,
        scenario=scenario,
        config=config,
        aanname=aanname,
        saldo_begin_jaar=saldo_begin_jaar,
    )
    
    return resultaat


def extract_totaal_verschuldigd(resultaat: dict, config, heeft_partner: bool) -> Decimal:
    """Extract totaal verschuldigd uit berekeningsresultaat.
    
    Args:
        resultaat: Dict van _bereken_jaar_detail
        config: BelastingConfig voor het jaar
        heeft_partner: Of huishouden een partner heeft
        
    Returns:
        Totaal verschuldigd bedrag (Box 1 IB + premies - kortingen + Box 3)
    """
    # Box 1 IB (inkomstenbelasting alleen, zonder premies)
    box1_ib_p1 = resultaat.get("bel_voor_korting_p1", Decimal("0"))
    box1_ib_p2 = resultaat.get("bel_voor_korting_p2", Decimal("0"))
    
    # Bruto inkomens voor premieberekening
    bruto_p1 = resultaat.get("bruto_p1", Decimal("0"))
    bruto_p2 = resultaat.get("bruto_p2", Decimal("0"))
    
    # AOW status
    is_aow_p1 = resultaat.get("is_aow_p1", False)
    is_aow_p2 = resultaat.get("is_aow_p2", False)
    
    # Bereken premies volksverzekeringen
    premie_aow_p1, premie_anw_p1, premie_wlz_p1, totaal_premies_p1 = (
        belasting_engine.bereken_premies_volksverzekeringen(bruto_p1, config, is_aow_p1)
    )
    premie_aow_p2, premie_anw_p2, premie_wlz_p2, totaal_premies_p2 = (
        belasting_engine.bereken_premies_volksverzekeringen(bruto_p2, config, is_aow_p2)
    )
    
    # Heffingskortingen (AHK, arbeidskorting, ouderenkorting)
    totale_hk_p1 = resultaat.get("totale_hk_p1", Decimal("0"))
    totale_hk_p2 = resultaat.get("totale_hk_p2", Decimal("0"))
    
    # Alleenstaandeouderenkorting (aparte korting voor alleenstaande 65+)
    alleenstaandeouderenkorting = heffingskorting.bereken_alleenstaandeouderenkorting(
        bruto_p1, config, is_aow_p1, is_alleenstaand=not heeft_partner
    )
    
    # Box 3
    box3_heffing = resultaat.get("box3_heffing", Decimal("0"))
    
    # Totaal verschuldigd = IB + premies - kortingen + Box 3
    totaal_ib_en_premies = (
        box1_ib_p1 + totaal_premies_p1 +
        box1_ib_p2 + totaal_premies_p2
    )
    
    totaal_kortingen = totale_hk_p1 + totale_hk_p2 + alleenstaandeouderenkorting
    
    totaal_verschuldigd = totaal_ib_en_premies - totaal_kortingen + box3_heffing
    
    return totaal_verschuldigd


def valideer_testcase(testcase: TestCase, tolerantie: Decimal = Decimal("5")) -> dict:
    """Valideer testcase: bereken belasting en vergelijk met verwachte waarde.
    
    Args:
        testcase: TestCase om te valideren
        tolerantie: Maximaal toegestane afwijking in euros
        
    Returns:
        Dict met validatieresultaat:
        {
            "testcase_id": str,
            "verwacht": Decimal,
            "berekend": Decimal,
            "verschil": Decimal,
            "verschil_pct": Decimal,
            "pass": bool,
            "status": str,  # "PASS", "WARN", "FAIL"
            "details": dict,  # volledige berekeningsdetails
        }
    """
    # Laad config
    config, _ = laad_tarieven(testcase.jaar)
    
    # Bepaal of huishouden een partner heeft
    heeft_partner = testcase.is_paar
    
    # Bereken
    details = bereken_belasting_testcase(testcase)
    berekend = extract_totaal_verschuldigd(details, config, heeft_partner)
    
    # Verwacht
    verwacht = testcase.verwachte_belasting.totaal_verschuldigd
    
    # Verschil
    verschil = berekend - verwacht
    verschil_pct = (verschil / verwacht * 100) if verwacht > 0 else Decimal("0")
    
    # Status
    abs_verschil = abs(verschil)
    if abs_verschil <= tolerantie:
        status = "PASS"
        is_pass = True
    elif abs_verschil <= 50:
        status = "WARN"
        is_pass = False
    else:
        status = "FAIL"
        is_pass = False
    
    return {
        "testcase_id": testcase.testcase_id,
        "naam": testcase.naam,
        "jaar": testcase.jaar,
        "verwacht": verwacht,
        "berekend": berekend,
        "verschil": verschil,
        "verschil_pct": verschil_pct,
        "pass": is_pass,
        "status": status,
        "details": details,
    }
