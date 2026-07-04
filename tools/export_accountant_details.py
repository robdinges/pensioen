from __future__ import annotations

"""Exporteer uitgebreide accountant-berekeningen voor testcase-validatie.

Dit script gebruikt dezelfde interne detailberekening als de accountantspagina
(`_bereken_jaar_detail`) en schrijft per testcase:
- een volledige JSON dump met alle tussenwaarden
- een compacte Markdown samenvatting

Daarnaast wordt een batchsamenvatting in Markdown geschreven.
"""

import argparse
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from pensioen.tax.belasting_loader import laad_tarieven
from pensioen.ui.pagina_accountant import _bereken_jaar_detail
from tests.scenario_generator import genereer_testcase_scenario
from tests.testcase_validatie import _pas_aow_bedrag_aan_voor_testcase
from tests.testcase_loader import vind_testcase_by_id


IB2025_DEFAULT_CASE_IDS = [
    "tc_2025_006",
    "tc_2025_007",
    "tc_2025_008",
    "tc_2025_009",
    "tc_2025_010",
    "tc_2025_011",
]


def _serialize(obj: Any) -> Any:
    """Serialiseer helper voor JSON-export."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Niet serialiseerbaar: {type(obj)}")


def _berekend_totaal_verschuldigd(detail: dict[str, Any]) -> Decimal:
    """Bepaal totaal verschuldigd op basis van detaildict."""
    return (
        detail.get("netto_bel_p1", Decimal("0"))
        + detail.get("netto_bel_p2", Decimal("0"))
        + detail.get("box3_heffing", Decimal("0"))
    )


def _status(abs_verschil: Decimal) -> str:
    """Classificeer verschil volgens testcase-drempels."""
    if abs_verschil <= Decimal("5"):
        return "PASS"
    if abs_verschil <= Decimal("50"):
        return "WARN"
    return "FAIL"


def exporteer_testcase_detail(
    testcase_id: str,
    output_dir: Path,
) -> tuple[str, Decimal, Decimal, Decimal, str]:
    """Exporteer detailrapporten voor 1 testcase.

    Returns:
        tuple(testcase_id, verwacht, berekend, verschil, status)
    """
    testcase = vind_testcase_by_id(testcase_id)
    personen, scenario = genereer_testcase_scenario(testcase)

    persoon1 = personen[0]
    persoon2 = personen[1] if len(personen) > 1 else None
    config, aanname = laad_tarieven(testcase.jaar)
    config = _pas_aow_bedrag_aan_voor_testcase(testcase, config)

    detail = _bereken_jaar_detail(
        jaar=testcase.jaar,
        persoon1=persoon1,
        persoon2=persoon2,
        records1=[],
        records2=[],
        scenario=scenario,
        config=config,
        aanname=aanname,
        saldo_begin_jaar=testcase.vermogen.totaal,
    )

    verwacht = testcase.verwachte_belasting.totaal_verschuldigd
    berekend = _berekend_totaal_verschuldigd(detail)
    verschil = berekend - verwacht
    status = _status(abs(verschil))

    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"{testcase_id}_accountant_detail.json"
    md_path = output_dir / f"{testcase_id}_accountant_detail.md"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(detail, handle, ensure_ascii=False, indent=2, default=_serialize)

    md_regels = [
        f"## Accountant detail export - {testcase_id}",
        "",
        f"- Jaar: {testcase.jaar}",
        f"- Aanname tariefjaar: {aanname or 'geen'}",
        f"- Verwacht totaal verschuldigd: {verwacht}",
        f"- Berekend totaal verschuldigd: {berekend}",
        f"- Verschil: {verschil}",
        f"- Status: {status}",
        "",
        "## Kernwaarden",
        "",
        f"- bruto_p1: {detail.get('bruto_p1')}",
        f"- bruto_p2: {detail.get('bruto_p2')}",
        f"- box1_grondslag_p1: {detail.get('box1_grondslag_p1')}",
        f"- box1_grondslag_p2: {detail.get('box1_grondslag_p2')}",
        f"- bel_voor_korting_p1: {detail.get('bel_voor_korting_p1')}",
        f"- bel_voor_korting_p2: {detail.get('bel_voor_korting_p2')}",
        f"- totaal_premies_p1: {detail.get('totaal_premies_p1')}",
        f"- totaal_premies_p2: {detail.get('totaal_premies_p2')}",
        f"- totale_hk_p1: {detail.get('totale_hk_p1')}",
        f"- totale_hk_p2: {detail.get('totale_hk_p2')}",
        f"- box3_heffing: {detail.get('box3_heffing')}",
        f"- saldo_begin_jaar: {detail.get('saldo_begin_jaar')}",
        f"- saldo_einde_jaar: {detail.get('saldo_einde_jaar')}",
        "",
        f"Volledige dump staat in: {json_path}",
    ]

    md_path.write_text("\n".join(md_regels) + "\n", encoding="utf-8")

    return testcase_id, verwacht, berekend, verschil, status


def _bouw_argumenten() -> argparse.Namespace:
    """Lees CLI-argumenten."""
    parser = argparse.ArgumentParser(
        description="Exporteer uitgebreide accountant-berekeningen per testcase",
    )
    parser.add_argument(
        "testcase_ids",
        nargs="*",
        help=(
            "Optionele lijst testcase IDs. Laat leeg voor standaardset "
            "tc_2025_006 t/m tc_2025_011."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="tests/fixtures/belasting_testcases/accountant_exports",
        help="Output directory voor JSON/Markdown exportbestanden.",
    )
    parser.add_argument(
        "--summary-name",
        default="batch_summary.md",
        help="Bestandsnaam voor de batchsamenvatting (Markdown).",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    args = _bouw_argumenten()

    testcase_ids = args.testcase_ids if args.testcase_ids else IB2025_DEFAULT_CASE_IDS
    output_dir = Path(args.output_dir)

    samenvatting = [
        "## Batch accountant export",
        "",
        "| testcase | verwacht | berekend | verschil | status |",
        "|---|---:|---:|---:|---|",
    ]

    for testcase_id in testcase_ids:
        testcase_id, verwacht, berekend, verschil, status = exporteer_testcase_detail(
            testcase_id=testcase_id,
            output_dir=output_dir,
        )
        samenvatting.append(
            f"| {testcase_id} | {verwacht} | {berekend} | {verschil} | {status} |"
        )
        print(f"Export klaar voor {testcase_id} ({status})")

    summary_path = output_dir / args.summary_name
    summary_path.write_text("\n".join(samenvatting) + "\n", encoding="utf-8")
    print(f"Batchsamenvatting geschreven: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
