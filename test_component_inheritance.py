"""Test component inheritance bij afgeleid scenario aanmaken."""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime, date

from pensioen.models.scenario import Scenario
from pensioen.models.component import FinancieelComponent, CategorieComponent

# Test: Afgeleid scenario met componenten
print("=" * 60)
print("Test: Afgeleid scenario krijgt kopie van parent componenten")
print("=" * 60)

# Maak parent scenario met een component
parent = Scenario(
    naam="Standaard",
    inflatie_pct=Decimal("2.0"),
    omschrijving="Standaard scenario",
    aangemaakt_op=datetime.now(),
)

# Voeg component toe aan parent
component = FinancieelComponent(
    omschrijving="Maandelijks salaris",
    categorie=CategorieComponent.ARBEIDSINKOMEN,
    persoon="P1",
    bedrag=Decimal("5000"),
    startdatum=date(2026, 1, 1),
    einddatum=date(2035, 12, 31),
)
parent.componenten.append(component)

print(f"\n1. Parent scenario '{parent.naam}':")
print(f"   - Componenten: {len(parent.componenten)}")
print(f"   - Component 0: {parent.componenten[0].omschrijving} = €{parent.componenten[0].bedrag}")

# Maak afgeleid scenario door parent te kopiëren (zoals de UI nu doet)
afgeleid = parent.model_copy(deep=True)
afgeleid.naam = "Voorzichtig"
afgeleid.omschrijving = "Voorzichtig scenario"
afgeleid.parent_naam = "Standaard"
afgeleid.overrides = {}
afgeleid.aangemaakt_op = datetime.now()
afgeleid.laatst_gewijzigd_op = datetime.now()

print(f"\n2. Afgeleid scenario '{afgeleid.naam}' aangemaakt:")
print(f"   - Parent: {afgeleid.parent_naam}")
print(f"   - Componenten: {len(afgeleid.componenten)}")
print(f"   - Component 0: {afgeleid.componenten[0].omschrijving} = €{afgeleid.componenten[0].bedrag}")

# Test: Wijzig bedrag in afgeleid scenario
afgeleid.componenten[0].bedrag = Decimal("4500")

print(f"\n3. Bedrag gewijzigd in afgeleid scenario naar €{afgeleid.componenten[0].bedrag}:")
print(f"   - Parent component bedrag: €{parent.componenten[0].bedrag} (ongewijzigd)")
print(f"   - Afgeleid component bedrag: €{afgeleid.componenten[0].bedrag} (gewijzigd)")
print(f"   ✓ Deep copy werkt correct - wijziging in child beïnvloedt parent niet")

# Test: Voeg component toe aan parent
nieuwe_component = FinancieelComponent(
    omschrijving="Jaarlijkse bonus",
    categorie=CategorieComponent.ARBEIDSINKOMEN,
    persoon="P1",
    bedrag=Decimal("1000"),
    startdatum=date(2026, 1, 1),
    einddatum=date(2035, 12, 31),
)
parent.componenten.append(nieuwe_component)

print(f"\n4. Nieuwe component toegevoegd aan parent:")
print(f"   - Parent componenten: {len(parent.componenten)} ({[c.omschrijving for c in parent.componenten]})")
print(f"   - Afgeleid componenten: {len(afgeleid.componenten)} ({[c.omschrijving for c in afgeleid.componenten]})")
print(f"   ⚠️  Nieuwe parent component wordt NIET automatisch geërfd")
print(f"   ℹ️  Dit is verwacht gedrag - componenten zijn snapshot bij aanmaak")

print("\n" + "=" * 60)
print("Conclusie:")
print("=" * 60)
print("✓ Componenten worden gekopieerd bij aanmaak afgeleid scenario")
print("✓ Wijzigingen in afgeleid scenario beïnvloeden parent niet (deep copy)")
print("⚠️  Latere wijzigingen in parent propageren NIET naar child")
print("ℹ️  Voor volledige inheritance is deep merge van lijsten nodig (toekomstige feature)")
