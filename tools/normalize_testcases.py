#!/usr/bin/env python3
"""
Normaliseer raw testcase JSONs naar uniform schema.

Dit script leest alle raw/*.json files, uniformeert de structuur naar het
gestandaardiseerde schema (zie schema.md), vult defaults in, en schrijft
genormaliseerde JSONs naar normalized/.

Gebruik: python tools/normalize_testcases.py

Output:
- normalized/tc_*.json files
- normalization_report.md
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from typing import Any


RAW_DIR = Path("tests/fixtures/belasting_testcases/raw")
NORMALIZED_DIR = Path("tests/fixtures/belasting_testcases/normalized")
REPORT_PATH = Path("tests/fixtures/belasting_testcases/normalization_report.md")

# Defaults
DEFAULT_SPAARGELD_FRACTIE = 0.4
DEFAULT_EIGEN_HUIS = False


class NormalizationWarning:
    """Track warnings during normalization."""
    
    def __init__(self, testcase_id: str, message: str, field: str = ""):
        self.testcase_id = testcase_id
        self.message = message
        self.field = field
    
    def __str__(self):
        return f"[{self.testcase_id}] {self.message}" + (f" (veld: {self.field})" if self.field else "")


class NormalizationReport:
    """Verzamel normalisatie-resultaten."""
    
    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.warnings: list[NormalizationWarning] = []
        self.testcases_processed: list[str] = []
        self.testcases_failed: list[tuple[str, str]] = []  # (id, error)
    
    def add_success(self, testcase_id: str):
        self.success_count += 1
        self.testcases_processed.append(testcase_id)
    
    def add_error(self, testcase_id: str, error: str):
        self.error_count += 1
        self.testcases_failed.append((testcase_id, error))
    
    def add_warning(self, warning: NormalizationWarning):
        self.warnings.append(warning)


def normalize_datum(datum_str: Any) -> str:
    """Converteer datum naar ISO formaat (YYYY-MM-DD)."""
    if isinstance(datum_str, str):
        # Probeer verschillende formaten
        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"]:
            try:
                dt = datetime.strptime(datum_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        # Als geen formaat werkt, return as-is en laat validatie falen
        return datum_str
    return str(datum_str)


def normalize_huishouden(data: dict, report: NormalizationReport, testcase_id: str) -> dict:
    """Normaliseer huishouden-veld."""
    huishouden = data.get("huishouden", {})
    
    result = {
        "type": huishouden.get("type", "UNKNOWN"),
        "aantal_personen": huishouden.get("aantal_personen", len(data.get("personen", []))),
    }
    
    # Optionele velden
    if "is_gehuwd" in huishouden:
        result["is_gehuwd"] = huishouden["is_gehuwd"]
    
    if "eigen_huis" in huishouden:
        result["eigen_huis"] = huishouden["eigen_huis"]
    else:
        result["eigen_huis"] = DEFAULT_EIGEN_HUIS
        report.add_warning(NormalizationWarning(
            testcase_id, 
            f"Geen 'eigen_huis' gevonden, default {DEFAULT_EIGEN_HUIS} gebruikt",
            "huishouden.eigen_huis"
        ))
    
    return result


def normalize_persoon(persoon: dict, report: NormalizationReport, testcase_id: str, persoon_idx: int) -> dict:
    """Normaliseer persoon-veld."""
    result = {
        "naam": persoon.get("naam", f"Persoon {persoon_idx + 1}"),
        "geboortedatum": normalize_datum(persoon.get("geboortedatum", "1900-01-01")),
    }
    
    # Inkomens (defaults naar 0)
    for inkomen_type in ["bruto_arbeid", "bruto_pensioen", "bruto_aow", "bruto_overig"]:
        result[inkomen_type] = persoon.get(inkomen_type, 0)
    
    # Optioneel: AOW-status
    if "is_aow_heel_jaar" in persoon:
        result["is_aow_heel_jaar"] = persoon["is_aow_heel_jaar"]
    
    return result


def normalize_vermogen(data: dict, report: NormalizationReport, testcase_id: str) -> dict:
    """Normaliseer vermogen-veld."""
    vermogen = data.get("vermogen", {})
    
    result = {
        "totaal": vermogen.get("totaal", 0),
    }
    
    # Bepaal spaargeld_fractie
    if "spaargeld_fractie" in vermogen:
        result["spaargeld_fractie"] = vermogen["spaargeld_fractie"]
    elif "spaargeld" in vermogen and "totaal" in vermogen and vermogen["totaal"] > 0:
        # Bereken uit absolute bedragen
        spaargeld = vermogen["spaargeld"]
        totaal = vermogen["totaal"]
        result["spaargeld_fractie"] = round(spaargeld / totaal, 2)
        report.add_warning(NormalizationWarning(
            testcase_id,
            f"spaargeld_fractie berekend uit absolute bedragen: {result['spaargeld_fractie']}",
            "vermogen.spaargeld_fractie"
        ))
    else:
        result["spaargeld_fractie"] = DEFAULT_SPAARGELD_FRACTIE
        report.add_warning(NormalizationWarning(
            testcase_id,
            f"Geen spaargeld_fractie gevonden, default {DEFAULT_SPAARGELD_FRACTIE} gebruikt",
            "vermogen.spaargeld_fractie"
        ))
    
    # Optionele velden bewaren
    if "spaargeld" in vermogen:
        result["spaargeld"] = vermogen["spaargeld"]
    if "beleggingen" in vermogen:
        result["beleggingen"] = vermogen["beleggingen"]
    if "verdeling_personen" in vermogen:
        result["verdeling_personen"] = vermogen["verdeling_personen"]
    
    return result


def normalize_verwachte_belasting(data: dict, report: NormalizationReport, testcase_id: str) -> dict:
    """Normaliseer verwachte_belasting-veld."""
    verwacht = data.get("verwachte_belasting", {})
    
    # Vind totaal verschuldigd (verschillende keys mogelijk)
    totaal = (
        verwacht.get("totaal_verschuldigd") or
        verwacht.get("totaal_verschuldigd_huishouden") or
        0
    )
    
    if totaal == 0:
        report.add_warning(NormalizationWarning(
            testcase_id,
            "Geen totaal_verschuldigd gevonden!",
            "verwachte_belasting.totaal_verschuldigd"
        ))
    
    # Bewaar alles (flexibel schema)
    result = dict(verwacht)
    
    # Zorg dat totaal_verschuldigd altijd aanwezig is
    if "totaal_verschuldigd" not in result:
        result["totaal_verschuldigd"] = totaal

    _valideer_interne_consistentie_verwachte_belasting(result, report, testcase_id)
    
    return result


def _decimal_uit_waarde(waarde: Any) -> Decimal | None:
    """Converteer naar Decimal of None bij ongeldige waarden."""
    if waarde is None:
        return None
    try:
        return Decimal(str(waarde))
    except Exception:
        return None


def _valideer_interne_consistentie_verwachte_belasting(
    verwacht: dict,
    report: NormalizationReport,
    testcase_id: str,
) -> None:
    """Voeg warnings toe bij intern-inconsistente verwachtingsvelden."""
    # Controle 1: totaal_kortingen per persoon = som van onderliggende kortingen.
    for suffix in ["p1", "p2"]:
        totaal = _decimal_uit_waarde(verwacht.get(f"totaal_kortingen_{suffix}"))
        if totaal is None:
            continue

        componenten = [
            _decimal_uit_waarde(verwacht.get(f"ahk_{suffix}")),
            _decimal_uit_waarde(verwacht.get(f"arbeidskorting_{suffix}")),
            _decimal_uit_waarde(verwacht.get(f"ouderenkorting_{suffix}")),
            _decimal_uit_waarde(verwacht.get(f"alleenstaandeouderenkorting_{suffix}")),
        ]
        componenten = [c for c in componenten if c is not None]
        if not componenten:
            continue

        som_componenten = sum(componenten, Decimal("0"))
        if abs(totaal - som_componenten) > Decimal("0.01"):
            report.add_warning(NormalizationWarning(
                testcase_id,
                (
                    f"totaal_kortingen_{suffix} ({totaal}) is niet gelijk aan "
                    f"som kortingen ({som_componenten})"
                ),
                f"verwachte_belasting.totaal_kortingen_{suffix}",
            ))

    # Controle 2: box1_ib per persoon moet optellen met schijven als beide aanwezig zijn.
    for suffix in ["p1", "p2"]:
        box1 = _decimal_uit_waarde(verwacht.get(f"box1_ib_{suffix}"))
        schijf1 = _decimal_uit_waarde(verwacht.get(f"box1_schijf1_{suffix}"))
        schijf2 = _decimal_uit_waarde(verwacht.get(f"box1_schijf2_{suffix}"))
        if box1 is None or schijf1 is None or schijf2 is None:
            continue

        som_schijven = schijf1 + schijf2
        if abs(box1 - som_schijven) > Decimal("0.01"):
            report.add_warning(NormalizationWarning(
                testcase_id,
                (
                    f"box1_ib_{suffix} ({box1}) is niet gelijk aan "
                    f"box1_schijf1_{suffix}+box1_schijf2_{suffix} ({som_schijven})"
                ),
                f"verwachte_belasting.box1_ib_{suffix}",
            ))


def normalize_metadata(data: dict, report: NormalizationReport, testcase_id: str) -> dict:
    """Normaliseer metadata-veld."""
    metadata = data.get("metadata", {})
    
    result = {}
    
    # Bewaar bestaande velden
    for key in ["uitgangspunten", "opmerkingen", "data_kwaliteit", "bron", "_incomplete"]:
        if key in metadata:
            result[key] = metadata[key]
    
    # Defaults
    if "data_kwaliteit" not in result:
        # Schat kwaliteit op basis van aanwezigheid tussenresultaten
        verwacht = data.get("verwachte_belasting", {})
        if any(k.startswith("box1_") for k in verwacht.keys()):
            result["data_kwaliteit"] = "volledig"
        elif len(verwacht) > 2:
            result["data_kwaliteit"] = "gedeeltelijk"
        else:
            result["data_kwaliteit"] = "minimaal"
    
    if "_incomplete" not in result:
        result["_incomplete"] = False
    
    return result


def normalize_eigen_woning(data: dict, report: NormalizationReport, testcase_id: str) -> dict | None:
    """Normaliseer eigen_woning-veld als aanwezig."""
    eigen_woning = data.get("eigen_woning")
    if not isinstance(eigen_woning, dict):
        if data.get("huishouden", {}).get("eigen_huis"):
            report.add_warning(NormalizationWarning(
                testcase_id,
                "huishouden.eigen_huis is true maar geen eigen_woning details gevonden",
                "eigen_woning"
            ))
        return None

    result = {
        "woz_waarde": eigen_woning.get("woz_waarde", 0),
        "betaalde_hypotheekrente": eigen_woning.get("betaalde_hypotheekrente", 0),
        "overige_aftrekbare_kosten": eigen_woning.get("overige_aftrekbare_kosten", 0),
        "eigenwoningschuld_begin": eigen_woning.get("eigenwoningschuld_begin", 0),
        "eigenwoningschuld_eind": eigen_woning.get("eigenwoningschuld_eind", 0),
    }
    return result


def normalize_testcase(filepath: Path, report: NormalizationReport) -> dict | None:
    """Normaliseer één testcase JSON."""
    try:
        with open(filepath) as f:
            data = json.load(f)
        
        testcase_id = data.get("testcase_id", filepath.stem)
        
        # Bouw genormaliseerde structuur
        normalized = {
            "testcase_id": testcase_id,
            "naam": data.get("naam", "Unnamed"),
            "jaar": data.get("jaar", 2025),
        }
        
        # Optionele root velden
        if "datum_aangeleverd" in data:
            normalized["datum_aangeleverd"] = data["datum_aangeleverd"]
        if "bron_formaat" in data:
            normalized["bron_formaat"] = data["bron_formaat"]
        
        # Geneste velden
        normalized["huishouden"] = normalize_huishouden(data, report, testcase_id)
        normalized["personen"] = [
            normalize_persoon(p, report, testcase_id, idx)
            for idx, p in enumerate(data.get("personen", []))
        ]
        normalized["vermogen"] = normalize_vermogen(data, report, testcase_id)
        normalized["verwachte_belasting"] = normalize_verwachte_belasting(data, report, testcase_id)
        eigen_woning = normalize_eigen_woning(data, report, testcase_id)
        if eigen_woning is not None:
            normalized["eigen_woning"] = eigen_woning
        normalized["metadata"] = normalize_metadata(data, report, testcase_id)
        
        report.add_success(testcase_id)
        return normalized
        
    except Exception as e:
        report.add_error(filepath.stem, str(e))
        return None


def generate_report(report: NormalizationReport) -> str:
    """Genereer Markdown rapport."""
    lines = [
        "# Normalization Report",
        "",
        f"**Datum**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Samenvatting",
        "",
        f"- **Totaal testcases verwerkt**: {report.success_count + report.error_count}",
        f"- **✅ Succesvol genormaliseerd**: {report.success_count}",
        f"- **❌ Errors**: {report.error_count}",
        f"- **⚠️  Warnings**: {len(report.warnings)}",
        "",
    ]
    
    if report.testcases_processed:
        lines.extend([
            "## Verwerkte Testcases",
            "",
        ])
        for tc_id in report.testcases_processed:
            lines.append(f"- ✅ {tc_id}")
        lines.append("")
    
    if report.testcases_failed:
        lines.extend([
            "## Errors",
            "",
        ])
        for tc_id, error in report.testcases_failed:
            lines.append(f"### ❌ {tc_id}")
            lines.append(f"```\n{error}\n```")
            lines.append("")
    
    if report.warnings:
        lines.extend([
            "## Warnings",
            "",
            "Aannames gemaakt tijdens normalisatie:",
            "",
        ])
        
        # Groepeer warnings per testcase
        warnings_by_tc = {}
        for warning in report.warnings:
            if warning.testcase_id not in warnings_by_tc:
                warnings_by_tc[warning.testcase_id] = []
            warnings_by_tc[warning.testcase_id].append(warning)
        
        for tc_id in sorted(warnings_by_tc.keys()):
            lines.append(f"### {tc_id}")
            lines.append("")
            for warning in warnings_by_tc[tc_id]:
                lines.append(f"- {warning.message}")
            lines.append("")
    
    lines.extend([
        "## Actie Vereist",
        "",
    ])
    
    if report.error_count > 0:
        lines.append("❌ **Errors gevonden**: Controleer errors hierboven en corrigeer raw JSONs.")
    
    incomplete_warnings = [w for w in report.warnings if "_incomplete" in w.message.lower()]
    if incomplete_warnings:
        lines.append("⚠️  **Incomplete testcases**: Handmatige review nodig voor complete validatie.")
    
    if report.error_count == 0 and len(report.warnings) == 0:
        lines.append("✅ **Alles OK**: Alle testcases succesvol genormaliseerd zonder warnings.")
    elif report.error_count == 0:
        lines.append("⚠️  **Review warnings**: Normalisatie is gelukt, maar controleer de waarschuwingen hierboven.")
    
    lines.append("")
    
    return "\n".join(lines)


def main():
    """Hoofdfunctie: normaliseer alle raw testcases."""
    print("=" * 80)
    print("TESTCASE NORMALISATIE")
    print("=" * 80)
    print()
    
    # Vind alle testcase JSONs (skip templates)
    json_files = sorted(RAW_DIR.glob("tc_*.json"))
    
    if not json_files:
        print(f"❌ Geen testcase JSONs gevonden in {RAW_DIR}")
        return
    
    print(f"📁 Input: {RAW_DIR}")
    print(f"📁 Output: {NORMALIZED_DIR}")
    print(f"📊 Aantal testcases: {len(json_files)}")
    print()
    
    # Zorg dat output directory bestaat
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Normaliseer alle testcases
    report = NormalizationReport()
    
    for filepath in json_files:
        print(f"Processing {filepath.name}...", end=" ")
        normalized = normalize_testcase(filepath, report)
        
        if normalized:
            # Schrijf genormaliseerde JSON
            output_path = NORMALIZED_DIR / f"{normalized['testcase_id']}_normalized.json"
            with open(output_path, "w") as f:
                json.dump(normalized, f, indent=2, ensure_ascii=False)
            print(f"✅ → {output_path.name}")
        else:
            print("❌ FAILED")
    
    print()
    print("=" * 80)
    print("RESULTAAT")
    print("=" * 80)
    print()
    print(f"✅ Succesvol: {report.success_count}")
    print(f"❌ Errors: {report.error_count}")
    print(f"⚠️  Warnings: {len(report.warnings)}")
    print()
    
    # Genereer rapport
    report_content = generate_report(report)
    with open(REPORT_PATH, "w") as f:
        f.write(report_content)
    
    print(f"📝 Rapport opgeslagen: {REPORT_PATH}")
    print()
    
    if report.error_count == 0:
        print("✅ Normalisatie succesvol afgerond!")
        print(f"📁 {report.success_count} genormaliseerde testcases in {NORMALIZED_DIR}")
    else:
        print("⚠️  Normalisatie afgerond met errors. Controleer het rapport.")
    
    print()


if __name__ == "__main__":
    main()
