#!/usr/bin/env python3
"""Test de testcase-validatiepipeline en genereer optioneel een IB-rapport.

Dit script test de volledige flow:
1. Laad genormaliseerde JSON -> TestCase (Pydantic validatie)
2. Converteer TestCase -> Persoon + Scenario
3. Bereken cashflow en vergelijk met verwachte belasting
4. Schrijf een samenvattend validatierapport voor alle IB 2025-cases

Gebruik:
    - Alle cases + rapport: python tools/test_validatie_pipeline.py
    - Enkele case zonder rapport: python tools/test_validatie_pipeline.py tc_2025_010
    - Enkele case met rapport: python tools/test_validatie_pipeline.py tc_2025_010 --schrijf-rapport
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from tests.testcase_loader import laad_alle_testcases, laad_testcase
from tests.testcase_validatie import valideer_testcase

RAPPORT_PATH = Path("tests/fixtures/belasting_testcases/validatie_rapport_ib2025.md")


def format_bedrag(bedrag: Decimal | None) -> str:
    """Format bedrag als EUR met 2 decimalen."""
    if bedrag is None:
        return "n.v.t."
    afgerond = Decimal(bedrag).quantize(Decimal("0.01"))
    return f"EUR {afgerond:,.2f}"


def _verwacht_get(testcase, veld: str) -> Decimal | None:
    """Lees optioneel veld uit verwachte_belasting."""
    return getattr(testcase.verwachte_belasting, veld, None)


def _bereken_box3_verdeling(testcase, details: dict) -> tuple[Decimal, Decimal]:
    """Bepaal box 3 heffing per persoon voor vergelijking."""
    totaal_box3 = Decimal(details.get("box3_heffing", Decimal("0")))

    verwacht_box3_p1 = _verwacht_get(testcase, "box3_heffing_p1")
    verwacht_box3_p2 = _verwacht_get(testcase, "box3_heffing_p2")

    if verwacht_box3_p1 is not None and verwacht_box3_p2 is not None:
        return Decimal(verwacht_box3_p1), Decimal(verwacht_box3_p2)

    if testcase.is_paar:
        helft = (totaal_box3 / Decimal("2")).quantize(Decimal("0.01"))
        return helft, totaal_box3 - helft

    return totaal_box3, Decimal("0")


def _component_vergelijkingen(testcase, details: dict) -> list[tuple[str, Decimal | None, Decimal | None]]:
    """Bouw componentvergelijking verwacht versus berekend."""
    def _ew_tariefsaanpassing(sleutel: str) -> Decimal:
        ew = details.get(sleutel)
        if ew is None:
            return Decimal("0")
        if isinstance(ew, dict):
            return Decimal(ew.get("tariefsaanpassing", Decimal("0")))
        return Decimal(getattr(ew, "tariefsaanpassing", Decimal("0")))

    box1_ib_p1_berekend = (
        Decimal(details.get("bel_voor_korting_p1", Decimal("0")))
        + _ew_tariefsaanpassing("ew_p1")
    )

    componenten = [
        ("box1_ib_p1", _verwacht_get(testcase, "box1_ib_p1"), box1_ib_p1_berekend),
        ("totaal_premies_p1", _verwacht_get(testcase, "totaal_premies_p1"), details.get("totaal_premies_p1")),
        ("totaal_kortingen_p1", _verwacht_get(testcase, "totaal_kortingen_p1"), details.get("totale_hk_p1")),
        ("box3_heffing", _verwacht_get(testcase, "box3_heffing"), details.get("box3_heffing")),
    ]

    if testcase.is_paar:
        box1_ib_p2_berekend = (
            Decimal(details.get("bel_voor_korting_p2", Decimal("0")))
            + _ew_tariefsaanpassing("ew_p2")
        )
        componenten.extend(
            [
                ("box1_ib_p2", _verwacht_get(testcase, "box1_ib_p2"), box1_ib_p2_berekend),
                (
                    "totaal_premies_p2",
                    _verwacht_get(testcase, "totaal_premies_p2"),
                    details.get("totaal_premies_p2"),
                ),
                (
                    "totaal_kortingen_p2",
                    _verwacht_get(testcase, "totaal_kortingen_p2"),
                    details.get("totale_hk_p2"),
                ),
            ]
        )

    return componenten


def _vergelijk_regel(verwacht: Decimal | None, berekend: Decimal | None) -> tuple[str, Decimal | None]:
    """Maak statusregel voor een vergelijkingspaar."""
    if verwacht is None or berekend is None:
        return "NVT", None

    verschil = Decimal(berekend) - Decimal(verwacht)
    if abs(verschil) <= Decimal("5"):
        return "PASS", verschil
    if abs(verschil) <= Decimal("50"):
        return "WARN", verschil
    return "FAIL", verschil


def _print_vergelijkingsblok(testcase, resultaat: dict) -> dict:
    """Print gestructureerde vergelijking en retourneer rapportdata."""
    details = resultaat["details"]
    box3_p1, box3_p2 = _bereken_box3_verdeling(testcase, details)

    verwacht_huishouden = Decimal(resultaat["verwacht"])
    berekend_huishouden = Decimal(resultaat["berekend"])
    status_hh, verschil_hh = _vergelijk_regel(verwacht_huishouden, berekend_huishouden)

    verwacht_p1 = _verwacht_get(testcase, "totaal_verschuldigd_p1")
    berekend_p1 = Decimal(details.get("netto_bel_p1", Decimal("0"))) + box3_p1
    status_p1, verschil_p1 = _vergelijk_regel(verwacht_p1, berekend_p1)

    verwacht_p2 = _verwacht_get(testcase, "totaal_verschuldigd_p2")
    berekend_p2 = Decimal(details.get("netto_bel_p2", Decimal("0"))) + box3_p2
    status_p2, verschil_p2 = _vergelijk_regel(verwacht_p2, berekend_p2)

    print("\n3) GESTRUCTUREERDE VERGELIJKING")
    print("   Huishouden")
    print(f"      Verwacht: {format_bedrag(verwacht_huishouden)}")
    print(f"      Berekend: {format_bedrag(berekend_huishouden)}")
    print(f"      Verschil: {format_bedrag(verschil_hh or Decimal('0'))}  Status: {status_hh}")

    print("   Per persoon")
    print(
        f"      P1 verwacht/berekend: {format_bedrag(verwacht_p1)} / {format_bedrag(berekend_p1)}"
        f"  Verschil: {format_bedrag(verschil_p1 or Decimal('0'))}  Status: {status_p1}"
    )
    if testcase.is_paar:
        print(
            f"      P2 verwacht/berekend: {format_bedrag(verwacht_p2)} / {format_bedrag(berekend_p2)}"
            f"  Verschil: {format_bedrag(verschil_p2 or Decimal('0'))}  Status: {status_p2}"
        )

    componenten_uitvoer = []
    print("   Componentniveau")
    for naam, verwacht, berekend in _component_vergelijkingen(testcase, details):
        status, verschil = _vergelijk_regel(verwacht, berekend)
        componenten_uitvoer.append(
            {
                "naam": naam,
                "verwacht": verwacht,
                "berekend": Decimal(berekend) if berekend is not None else None,
                "verschil": verschil,
                "status": status,
            }
        )
        if status == "NVT":
            print(f"      - {naam}: verwacht n.v.t., berekend {format_bedrag(berekend)}")
        else:
            print(
                f"      - {naam}: {format_bedrag(verwacht)} vs {format_bedrag(berekend)}"
                f"  Verschil {format_bedrag(verschil or Decimal('0'))}  Status {status}"
            )

    return {
        "testcase_id": testcase.testcase_id,
        "naam": testcase.naam,
        "status": resultaat["status"],
        "huishouden": {
            "verwacht": verwacht_huishouden,
            "berekend": berekend_huishouden,
            "verschil": verschil_hh,
            "status": status_hh,
        },
        "persoon": {
            "p1": {
                "verwacht": verwacht_p1,
                "berekend": berekend_p1,
                "verschil": verschil_p1,
                "status": status_p1,
            },
            "p2": {
                "verwacht": verwacht_p2,
                "berekend": berekend_p2,
                "verschil": verschil_p2,
                "status": status_p2,
            },
        },
        "componenten": componenten_uitvoer,
    }


def _genereer_markdown_rapport(rapport_regels: list[dict]) -> None:
    """Genereer markdown rapport voor IB 2025 testcases."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lijnen = [
        "## IB 2025 Validatierapport",
        "",
        f"- Gegenereerd op: {timestamp}",
        f"- Aantal testcases: {len(rapport_regels)}",
        "",
        "## Samenvatting",
        "",
        "| Testcase | Status | Verwacht huishouden | Berekend huishouden | Verschil |",
        "|---|---|---:|---:|---:|",
    ]

    for regel in rapport_regels:
        hh = regel["huishouden"]
        lijnen.append(
            "| "
            f"{regel['testcase_id']} | {hh['status']} | {format_bedrag(hh['verwacht'])} | "
            f"{format_bedrag(hh['berekend'])} | {format_bedrag(hh['verschil'] or Decimal('0'))} |"
        )

    for regel in rapport_regels:
        lijnen.extend(
            [
                "",
                f"## {regel['testcase_id']} - {regel['naam']}",
                "",
                "### Huishouden",
                "",
                "| Verwacht | Berekend | Verschil | Status |",
                "|---:|---:|---:|---|",
                f"| {format_bedrag(regel['huishouden']['verwacht'])} | {format_bedrag(regel['huishouden']['berekend'])} "
                f"| {format_bedrag(regel['huishouden']['verschil'] or Decimal('0'))} | {regel['huishouden']['status']} |",
                "",
                "### Per persoon",
                "",
                "| Persoon | Verwacht | Berekend | Verschil | Status |",
                "|---|---:|---:|---:|---|",
                f"| P1 | {format_bedrag(regel['persoon']['p1']['verwacht'])} | {format_bedrag(regel['persoon']['p1']['berekend'])} "
                f"| {format_bedrag(regel['persoon']['p1']['verschil'] or Decimal('0'))} | {regel['persoon']['p1']['status']} |",
            ]
        )

        if regel["persoon"]["p2"]["verwacht"] is not None:
            lijnen.append(
                f"| P2 | {format_bedrag(regel['persoon']['p2']['verwacht'])} | {format_bedrag(regel['persoon']['p2']['berekend'])} "
                f"| {format_bedrag(regel['persoon']['p2']['verschil'] or Decimal('0'))} | {regel['persoon']['p2']['status']} |"
            )

        lijnen.extend(
            [
                "",
                "### Componentniveau",
                "",
                "| Component | Verwacht | Berekend | Verschil | Status |",
                "|---|---:|---:|---:|---|",
            ]
        )

        for component in regel["componenten"]:
            lijnen.append(
                f"| {component['naam']} | {format_bedrag(component['verwacht'])} | "
                f"{format_bedrag(component['berekend'])} | {format_bedrag(component['verschil'] or Decimal('0'))} "
                f"| {component['status']} |"
            )

    RAPPORT_PATH.write_text("\n".join(lijnen), encoding="utf-8")


def _is_ib2025_case(testcase_id: str) -> bool:
    """Bepaal of testcase in de IB 2025-rapportset valt."""
    return testcase_id.startswith("tc_2025_")


def test_single_testcase(testcase_id: str) -> dict | None:
    """Test een testcase en geef rapportregel terug."""
    print("=" * 80)
    print(f"TEST: {testcase_id}")
    print("=" * 80)

    print("\n1) LADEN TESTCASE JSON")
    filepath = Path(f"tests/fixtures/belasting_testcases/normalized/{testcase_id}_normalized.json")
    testcase = laad_testcase(filepath)
    print(f"   Geladen: {testcase.naam}")
    print(f"   Jaar: {testcase.jaar}")
    print(f"   Huishouden: {testcase.huishouden.type.value} ({testcase.huishouden.aantal_personen} personen)")
    print(f"   Totaal bruto inkomen: {format_bedrag(testcase.totaal_bruto_inkomen_huishouden)}")
    print(f"   Vermogen: {format_bedrag(testcase.vermogen.totaal)}")
    print(f"   Verwacht verschuldigd: {format_bedrag(testcase.verwachte_belasting.totaal_verschuldigd)}")

    print("\n2) BEREKEN EN VALIDEER BELASTING")
    try:
        resultaat = valideer_testcase(testcase)
        print("   RESULTAAT:")
        print(f"      Verwacht: {format_bedrag(resultaat['verwacht'])}")
        print(f"      Berekend: {format_bedrag(resultaat['berekend'])}")
        print(f"      Verschil: {format_bedrag(resultaat['verschil'])} ({resultaat['verschil_pct']:.1f}%)")
        print(f"      Status:   {resultaat['status']}")
        print(f"      Verwacht-bron: {resultaat.get('verwacht_bron', 'huishoudtotaal')}")

        data_waarschuwingen = resultaat.get("data_waarschuwingen", [])
        if data_waarschuwingen:
            print("\n   DATAWAARSCHUWINGEN:")
            for waarschuwing in data_waarschuwingen:
                print(f"      - {waarschuwing}")

        details = resultaat["details"]
        print("\n   DETAILS:")
        print(f"      Bruto P1:        {format_bedrag(details.get('bruto_p1', Decimal('0')))}")
        print(f"      Bruto P2:        {format_bedrag(details.get('bruto_p2', Decimal('0')))}")
        print(f"      Box 1 IB P1:     {format_bedrag(details.get('bel_voor_korting_p1', Decimal('0')))}")
        print(f"      Box 1 IB P2:     {format_bedrag(details.get('bel_voor_korting_p2', Decimal('0')))}")
        print(f"      Kortingen P1:    {format_bedrag(details.get('totale_hk_p1', Decimal('0')))}")
        print(f"      Kortingen P2:    {format_bedrag(details.get('totale_hk_p2', Decimal('0')))}")
        print(f"      Box 3 heffing:   {format_bedrag(details.get('box3_heffing', Decimal('0')))}")
        print(f"      Netto bel P1:    {format_bedrag(details.get('netto_bel_p1', Decimal('0')))}")
        print(f"      Netto bel P2:    {format_bedrag(details.get('netto_bel_p2', Decimal('0')))}")

        if resultaat["status"] == "PASS":
            print("\n   PASS - Binnen tolerantie (+/- EUR 5)")
        elif resultaat["status"] == "WARN":
            print("\n   WARN - Kleine afwijking (EUR 5 - EUR 50)")
        else:
            print("\n   FAIL - Grote afwijking (> EUR 50)")

        rapport_regel = _print_vergelijkingsblok(testcase, resultaat)
        print()
        return rapport_regel

    except Exception as exc:
        print(f"   Error bij validatie: {exc}")
        print()
        return None


def test_alle_testcases() -> None:
    """Test alle testcases en maak rapport voor de IB 2025 set."""
    print("=" * 80)
    print("TEST ALLE TESTCASES")
    print("=" * 80)
    print()

    testcases = laad_alle_testcases()
    print(f"Gevonden: {len(testcases)} testcases\n")

    rapport_regels = []
    for tc_id in sorted(testcases.keys()):
        rapport_regel = test_single_testcase(tc_id)
        if rapport_regel and _is_ib2025_case(rapport_regel["testcase_id"]):
            rapport_regels.append(rapport_regel)

    if rapport_regels:
        _genereer_markdown_rapport(rapport_regels)
        print(f"Markdown rapport opgeslagen: {RAPPORT_PATH}")


def main() -> None:
    """Hoofdfunctie."""
    import sys

    args = sys.argv[1:]
    schrijf_rapport = "--schrijf-rapport" in args
    args = [arg for arg in args if arg != "--schrijf-rapport"]

    if args:
        testcase_id = args[0]
        rapport_regel = test_single_testcase(testcase_id)
        if schrijf_rapport and rapport_regel and _is_ib2025_case(testcase_id):
            _genereer_markdown_rapport([rapport_regel])
            print(f"Markdown rapport opgeslagen: {RAPPORT_PATH}")
        elif schrijf_rapport:
            print("Geen IB 2025-case; rapport niet geschreven.")
    else:
        test_alle_testcases()


if __name__ == "__main__":
    main()
