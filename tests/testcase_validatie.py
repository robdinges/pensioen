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

    Gebruikt de al-correcte waarden uit _bereken_jaar_detail (die rekening houden
    met eigen woning grondslag-correctie, tariefsaanpassing en premies op gecorrigeerde grondslag).

    Args:
        resultaat: Dict van _bereken_jaar_detail
        config: BelastingConfig voor het jaar (niet meer gebruikt, behouden voor backward-compat)
        heeft_partner: Of huishouden een partner heeft (niet meer gebruikt)

    Returns:
        Totaal verschuldigd bedrag
    """
    netto_bel_p1 = resultaat.get("netto_bel_p1", Decimal("0"))
    netto_bel_p2 = resultaat.get("netto_bel_p2", Decimal("0"))
    box3_heffing = resultaat.get("box3_heffing", Decimal("0"))
    return netto_bel_p1 + netto_bel_p2 + box3_heffing


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
