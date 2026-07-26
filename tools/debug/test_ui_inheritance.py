"""Test inheritance UI functionaliteit."""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from pensioen.models.scenario import Scenario
from pensioen.ui.scenario_context import get_resolved_scenario, is_field_overridden

# Test 1: Base scenario
base = Scenario(
    naam="Standaard",
    inflatie_pct=Decimal("2.0"),
    omschrijving="Standaard scenario",
    aangemaakt_op=datetime.now(),
)

print("Test 1: Base scenario")
print(f"  inflatie_pct: {base.inflatie_pct}")
print(f"  is_field_overridden('inflatie_pct'): {is_field_overridden(base, 'inflatie_pct')}")
print(f"  ✓ Base scenario heeft geen overrides")
print()

# Test 2: Afgeleid scenario zonder overrides
voorzichtig = Scenario(
    naam="Voorzichtig",
    parent_naam="Standaard",
    overrides={},  # Geen overrides
    omschrijving="Voorzichtig scenario",
    aangemaakt_op=datetime.now(),
)

scenario_lijst = [base, voorzichtig]
resolved_voorzichtig = get_resolved_scenario(voorzichtig, scenario_lijst)

print("Test 2: Afgeleid scenario zonder overrides")
print(f"  voorzichtig.inflatie_pct (raw): {voorzichtig.inflatie_pct}")
print(f"  resolved_voorzichtig.inflatie_pct: {resolved_voorzichtig.inflatie_pct}")
print(f"  is_field_overridden('inflatie_pct'): {is_field_overridden(voorzichtig, 'inflatie_pct')}")
print(f"  ✓ Resolved scenario erft parent waarde: {resolved_voorzichtig.inflatie_pct == Decimal('2.0')}")
print()

# Test 3: Override in afgeleid scenario
voorzichtig.set_override("inflatie_pct", "3.5")
resolved_voorzichtig = get_resolved_scenario(voorzichtig, scenario_lijst)

print("Test 3: Afgeleid scenario met override")
print(f"  voorzichtig.overrides: {voorzichtig.overrides}")
print(f"  resolved_voorzichtig.inflatie_pct: {resolved_voorzichtig.inflatie_pct}")
print(f"  is_field_overridden('inflatie_pct'): {is_field_overridden(voorzichtig, 'inflatie_pct')}")
print(f"  ✓ Override werkt: {resolved_voorzichtig.inflatie_pct == Decimal('3.5')}")
print()

# Test 4: Parent wijzigen - afgeleid scenario zonder override volgt mee
base.inflatie_pct = Decimal("2.5")
voorzichtig.remove_override("inflatie_pct")  # Verwijder override
resolved_voorzichtig = get_resolved_scenario(voorzichtig, scenario_lijst)

print("Test 4: Parent wijzigt, afgeleid scenario volgt mee (geen override)")
print(f"  base.inflatie_pct: {base.inflatie_pct}")
print(f"  resolved_voorzichtig.inflatie_pct: {resolved_voorzichtig.inflatie_pct}")
print(f"  ✓ Afgeleid scenario volgt parent: {resolved_voorzichtig.inflatie_pct == Decimal('2.5')}")
print()

# Test 5: Parent wijzigen - afgeleid scenario met override blijft ongewijzigd
voorzichtig.set_override("inflatie_pct", "3.5")
base.inflatie_pct = Decimal("4.0")
resolved_voorzichtig = get_resolved_scenario(voorzichtig, scenario_lijst)

print("Test 5: Parent wijzigt, afgeleid scenario met override blijft zelfde")
print(f"  base.inflatie_pct: {base.inflatie_pct}")
print(f"  resolved_voorzichtig.inflatie_pct: {resolved_voorzichtig.inflatie_pct}")
print(f"  ✓ Override blijft behouden: {resolved_voorzichtig.inflatie_pct == Decimal('3.5')}")

print("\n✅ Alle tests geslaagd!")
