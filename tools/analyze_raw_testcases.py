#!/usr/bin/env python3
"""
Analyseer raw testcase JSONs en toon overzicht van velden.

Dit script scant alle raw/*.json files en rapporteert:
- Welke velden aanwezig zijn per testcase
- Datatypes per veld
- Ontbrekende verplichte velden
- Voorgesteld uniform schema

Gebruik: python tools/analyze_raw_testcases.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from collections import defaultdict


RAW_DIR = Path("tests/fixtures/belasting_testcases/raw")
VERPLICHTE_VELDEN = {
    "testcase_id",
    "naam",
    "jaar",
    "huishouden.type",
    "personen[0].geboortedatum",
    "verwachte_belasting.totaal_verschuldigd",
}


def get_nested_keys(data: dict, prefix: str = "") -> set[str]:
    """Recursief alle keys ophalen uit geneste dict."""
    keys = set()
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            keys.add(full_key)
            keys.update(get_nested_keys(value, full_key))
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            keys.add(f"{full_key}[]")
            keys.update(get_nested_keys(value[0], f"{full_key}[0]"))
        else:
            keys.add(full_key)
    
    return keys


def analyze_testcase(filepath: Path) -> dict[str, Any]:
    """Analyseer één testcase JSON."""
    try:
        with open(filepath) as f:
            data = json.load(f)
        
        # Vind alle keys
        keys = get_nested_keys(data)
        
        # Check verplichte velden
        missing = []
        for veld in VERPLICHTE_VELDEN:
            # Simpele check (geen echte path parsing)
            if veld not in str(keys):
                missing.append(veld)
        
        return {
            "filepath": filepath,
            "testcase_id": data.get("testcase_id", "UNKNOWN"),
            "naam": data.get("naam", "UNKNOWN"),
            "jaar": data.get("jaar", 0),
            "keys": keys,
            "missing_required": missing,
            "data": data,
            "success": True,
        }
    except Exception as e:
        return {
            "filepath": filepath,
            "testcase_id": "ERROR",
            "naam": str(e),
            "keys": set(),
            "missing_required": list(VERPLICHTE_VELDEN),
            "success": False,
            "error": str(e),
        }


def main():
    """Hoofdfunctie: analyseer alle raw testcases."""
    # Vind alle testcase JSONs (skip templates)
    json_files = sorted(RAW_DIR.glob("tc_*.json"))
    
    if not json_files:
        print("❌ Geen testcase JSONs gevonden in", RAW_DIR)
        return
    
    print("=" * 80)
    print("ANALYSE RAW TESTCASE JSONs")
    print("=" * 80)
    print(f"\n📁 Directory: {RAW_DIR}")
    print(f"📊 Aantal testcases: {len(json_files)}\n")
    
    # Analyseer elke testcase
    analyses = [analyze_testcase(f) for f in json_files]
    
    # Verzamel statistieken
    all_keys = set()
    key_counts = defaultdict(int)
    
    for analysis in analyses:
        all_keys.update(analysis["keys"])
        for key in analysis["keys"]:
            key_counts[key] += 1
    
    # Toon per testcase
    print("=" * 80)
    print("PER TESTCASE OVERZICHT")
    print("=" * 80)
    
    for analysis in analyses:
        if analysis["success"]:
            print(f"\n✅ {analysis['testcase_id']} - {analysis['naam']}")
            print(f"   Jaar: {analysis['jaar']}")
            print(f"   Aantal keys: {len(analysis['keys'])}")
            
            if analysis["missing_required"]:
                print(f"   ⚠️  Ontbrekende verplichte velden: {', '.join(analysis['missing_required'])}")
            else:
                print(f"   ✅ Alle verplichte velden aanwezig")
        else:
            print(f"\n❌ {analysis['filepath'].name}")
            print(f"   Error: {analysis.get('error', 'Unknown error')}")
    
    # Toon verzamelde keys
    print("\n" + "=" * 80)
    print("ALLE GEVONDEN KEYS (UNION)")
    print("=" * 80)
    print(f"\nTotaal {len(all_keys)} unieke keys:\n")
    
    # Groepeer keys per top-level
    grouped_keys = defaultdict(list)
    for key in sorted(all_keys):
        top_level = key.split('.')[0] if '.' in key else key
        grouped_keys[top_level].append(key)
    
    for top_level in sorted(grouped_keys.keys()):
        keys_in_group = grouped_keys[top_level]
        print(f"\n{top_level}:")
        for key in sorted(keys_in_group):
            count = key_counts[key]
            coverage = f"({count}/{len(json_files)})"
            print(f"  - {key:<60} {coverage}")
    
    # Toon coverage
    print("\n" + "=" * 80)
    print("FIELD COVERAGE")
    print("=" * 80)
    
    universal_keys = [k for k in all_keys if key_counts[k] == len(json_files)]
    partial_keys = [k for k in all_keys if 0 < key_counts[k] < len(json_files)]
    
    print(f"\n✅ Universeel (in alle {len(json_files)} testcases): {len(universal_keys)} keys")
    print(f"⚠️  Gedeeltelijk: {len(partial_keys)} keys")
    
    if partial_keys:
        print("\nGedeeltelijke coverage keys:")
        for key in sorted(partial_keys):
            count = key_counts[key]
            print(f"  - {key:<60} {count}/{len(json_files)}")
    
    # Aanbevelingen
    print("\n" + "=" * 80)
    print("AANBEVELINGEN VOOR NORMALISATIE")
    print("=" * 80)
    
    problems = []
    
    for analysis in analyses:
        if analysis["missing_required"]:
            problems.append(f"{analysis['testcase_id']}: Ontbrekende verplichte velden")
    
    if problems:
        print("\n⚠️  Problemen gevonden:")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print("\n✅ Alle testcases hebben verplichte velden")
    
    print(f"\n📝 Normalisatie zal {len(partial_keys)} optionele velden standaardiseren")
    print(f"📝 Verwachte output: {len(json_files)} normalized JSONs")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
