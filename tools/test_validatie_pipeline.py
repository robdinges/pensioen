#!/usr/bin/env python3
"""
Test de testcase validatie pipeline.

Dit script test de volledige flow:
1. Laad genormaliseerde JSON → TestCase (Pydantic validatie)
2. Converteer TestCase → Persoon + Scenario
3. Bereken cashflow voor 2025
4. Vergelijk met verwachte belasting

Gebruik: python tools/test_validatie_pipeline.py
"""

from __future__ import annotations

from pathlib import Path
from decimal import Decimal

# Tests imports
from tests.testcase_loader import laad_testcase, laad_alle_testcases
from tests.testcase_validatie import valideer_testcase


def format_bedrag(bedrag: Decimal) -> str:
    """Format bedrag als €X,XXX."""
    return f"€{int(bedrag):,}"


def test_single_testcase(testcase_id: str):
    """Test één testcase."""
    print("=" * 80)
    print(f"TEST: {testcase_id}")
    print("=" * 80)
    
    # Stap 1: Laad testcase
    print("\n1️⃣  LADEN TESTCASE JSON")
    filepath = Path(f"tests/fixtures/belasting_testcases/normalized/{testcase_id}_normalized.json")
    testcase = laad_testcase(filepath)
    print(f"   ✅ Geladen: {testcase.naam}")
    print(f"   Jaar: {testcase.jaar}")
    print(f"   Huishouden: {testcase.huishouden.type.value} ({testcase.huishouden.aantal_personen} personen)")
    print(f"   Totaal bruto inkomen: {format_bedrag(testcase.totaal_bruto_inkomen_huishouden)}")
    print(f"   Vermogen: {format_bedrag(testcase.vermogen.totaal)}")
    print(f"   Verwacht verschuldigd: {format_bedrag(testcase.verwachte_belasting.totaal_verschuldigd)}")
    
    # Stap 2: Valideer
    print("\n2️⃣  BEREKEN & VALIDEER BELASTING")
    try:
        resultaat = valideer_testcase(testcase)
        
        print(f"   📊 RESULTAAT:")
        print(f"      Verwacht: {format_bedrag(resultaat['verwacht'])}")
        print(f"      Berekend: {format_bedrag(resultaat['berekend'])}")
        print(f"      Verschil: {format_bedrag(resultaat['verschil'])} ({resultaat['verschil_pct']:.1f}%)")
        print(f"      Status:   {resultaat['status']}")
        
        # Details
        details = resultaat['details']
        print(f"\n   📝 DETAILS:")
        print(f"      Bruto P1:        {format_bedrag(details.get('bruto_p1', Decimal('0')))}")
        print(f"      Bruto P2:        {format_bedrag(details.get('bruto_p2', Decimal('0')))}")
        print(f"      Box 1 IB P1:     {format_bedrag(details.get('bel_voor_korting_p1', Decimal('0')))}")
        print(f"      Box 1 IB P2:     {format_bedrag(details.get('bel_voor_korting_p2', Decimal('0')))}")
        print(f"      Kortingen P1:    {format_bedrag(details.get('totale_hk_p1', Decimal('0')))}")
        print(f"      Kortingen P2:    {format_bedrag(details.get('totale_hk_p2', Decimal('0')))}")
        print(f"      Box 3 heffing:   {format_bedrag(details.get('box3_heffing', Decimal('0')))}")
        print(f"      Netto bel P1:    {format_bedrag(details.get('netto_bel_p1', Decimal('0')))}")
        print(f"      Netto bel P2:    {format_bedrag(details.get('netto_bel_p2', Decimal('0')))}")
        
        # Status symbool
        if resultaat['status'] == 'PASS':
            print(f"\n   ✅ PASS - Binnen tolerantie (±€5)")
        elif resultaat['status'] == 'WARN':
            print(f"\n   ⚠️  WARN - Kleine afwijking (€5-€50)")
        else:
            print(f"\n   ❌ FAIL - Grote afwijking (>€50)")
        
    except Exception as e:
        print(f"   ❌ Error bij validatie: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def test_alle_testcases():
    """Test alle testcases."""
    print("=" * 80)
    print("TEST ALLE TESTCASES")
    print("=" * 80)
    print()
    
    # Laad alle testcases
    testcases = laad_alle_testcases()
    print(f"Gevonden: {len(testcases)} testcases\n")
    
    # Test elk testcase
    for tc_id in sorted(testcases.keys()):
        test_single_testcase(tc_id)


def main():
    """Hoofdfunctie."""
    import sys
    
    if len(sys.argv) > 1:
        # Test specifieke testcase
        testcase_id = sys.argv[1]
        test_single_testcase(testcase_id)
    else:
        # Test alle testcases
        test_alle_testcases()


if __name__ == "__main__":
    main()
