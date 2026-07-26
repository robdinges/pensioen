"""Diagnostic tool om scenario componenten te inspecteren."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

# Zoek sessiebestand
project_root = Path(__file__).resolve().parents[2]
mogelijke_paden = [
    project_root / ".sessie.json",
    Path.cwd() / ".sessie.json",
]

sessie_pad = None
for pad in mogelijke_paden:
    if pad.exists():
        sessie_pad = pad
        break

if not sessie_pad:
    print("❌ Geen .sessie.json bestand gevonden")
    print(f"Gezocht op: {[str(p) for p in mogelijke_paden]}")
    exit(1)

print(f"✓ Sessiebestand gevonden: {sessie_pad}")
print()

with open(sessie_pad) as f:
    data = json.load(f)

if "scenario_lijst" not in data:
    print("❌ Geen scenario_lijst in sessie")
    exit(1)

print(f"Aantal scenario's: {len(data['scenario_lijst'])}\n")

for idx, scenario in enumerate(data["scenario_lijst"]):
    naam = scenario.get("naam", "Onbekend")
    is_actief = scenario.get("is_actief", False)
    print(f"{'[ACTIEF]' if is_actief else '[-----]'} Scenario {idx+1}: {naam}")
    
    if "componenten" not in scenario:
        print("  ⚠️ Geen componenten")
        continue
    
    print(f"  Aantal componenten: {len(scenario['componenten'])}")
    
    for comp_idx, comp in enumerate(scenario["componenten"]):
        cat = comp.get("categorie", "?")
        omschr = comp.get("omschrijving", "?")
        persoon = comp.get("persoon", "?")
        bedrag = comp.get("bedrag", "?")
        freq = comp.get("frequentie", "?")
        begindatum = comp.get("begindatum")
        einddatum = comp.get("einddatum")
        
        print(f"    [{comp_idx+1}] {omschr}")
        print(f"        Categorie: {cat}")
        print(f"        Persoon: {persoon}")
        print(f"        Bedrag: €{bedrag} ({freq})")
        print(f"        Begindatum: {begindatum or 'geen'}")
        print(f"        Einddatum: {einddatum or 'geen'}")
        
        # Controleer of component actief zou moeten zijn in 2026
        if begindatum and einddatum:
            try:
                begin = date.fromisoformat(begindatum)
                eind = date.fromisoformat(einddatum)
                test_2026_jan = date(2026, 1, 1)
                test_2026_dec = date(2026, 12, 31)
                
                # Component is actief in 2026 als:
                # - einddatum >= 2026-01-01 EN
                # - begindatum <= 2026-12-31
                actief_2026 = eind >= test_2026_jan and begin <= test_2026_dec
                
                print(f"        ✓ Actief in 2026: {'JA' if actief_2026 else 'NEE'}")
                
                if not actief_2026 and eind.year < 2026:
                    print(f"        ⚠️ Einddatum ({eind}) ligt VOOR 2026!")
                elif not actief_2026 and begin.year > 2026:
                    print(f"        ⚠️ Begindatum ({begin}) ligt NA 2026!")
            except (ValueError, TypeError) as e:
                print(f"        ⚠️ Ongeldige datum: {e}")
        print()

print("\n" + "="*60)
print("DIAGNOSE VOLTOOID")
print("="*60)
print("\nAls een component 'Actief in 2026: NEE' toont terwijl je dat wel verwacht,")
print("controleer dan de begin- en einddatum van dat component in de UI.")
