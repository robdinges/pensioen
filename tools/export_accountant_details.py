from __future__ import annotations

"""Genereer herhaalbare, uitgebreide validatierapporten per testcase.

Per testcase schrijft dit script:
- een volledige JSON dump met invoer, validatie-uitkomst en detailberekening
- een uitgebreid Markdown rapport met stap-voor-stap opbouw en vergelijking
    met Belastingdienst-verwachtingen

Daarnaast wordt een batchsamenvatting geschreven zodat dezelfde vergelijking
eenvoudig voor andere cases uitgevoerd kan worden.
"""

import argparse
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from tests.testcase_loader import DEFAULT_TESTCASE_DIR, laad_alle_testcases, vind_testcase_by_id
from tests.testcase_validatie import valideer_testcase


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


def _naar_decimal(waarde: Any) -> Decimal:
    """Converteer naar Decimal met veilige default."""
    if waarde is None:
        return Decimal("0")
    if isinstance(waarde, Decimal):
        return waarde
    return Decimal(str(waarde))


def _fmt_eur(waarde: Decimal | None) -> str:
    """Formatteer bedrag als euro-tekst."""
    if waarde is None:
        return "n.v.t."
    afgerond = Decimal(waarde).quantize(Decimal("0.01"))
    return f"EUR {afgerond:,.2f}"


def _fmt_num(waarde: Decimal) -> str:
    """Formatteer getal met 2 decimalen zonder valuta-prefix."""
    return f"{Decimal(waarde).quantize(Decimal('0.01'))}"


def _status_en_verschil(verwacht: Decimal | None, berekend: Decimal | None) -> tuple[str, Decimal | None]:
    """Bepaal status op basis van standaard validatiedrempels."""
    if verwacht is None or berekend is None:
        return "NVT", None

    verschil = berekend - verwacht
    abs_verschil = abs(verschil)
    if abs_verschil <= Decimal("5"):
        return "PASS", verschil
    if abs_verschil <= Decimal("50"):
        return "WARN", verschil
    return "FAIL", verschil


def _bereken_box3_verdeling(testcase, detail: dict[str, Any]) -> tuple[Decimal, Decimal]:
    """Bepaal box 3 heffing per persoon voor rapportvergelijking."""
    totaal_box3 = _naar_decimal(detail.get("box3_heffing", Decimal("0")))
    verwacht = testcase.verwachte_belasting

    if verwacht.box3_heffing_p1 is not None and verwacht.box3_heffing_p2 is not None:
        return _naar_decimal(verwacht.box3_heffing_p1), _naar_decimal(verwacht.box3_heffing_p2)

    if testcase.is_paar:
        helft = (totaal_box3 / Decimal("2")).quantize(Decimal("0.01"))
        return helft, totaal_box3 - helft

    return totaal_box3, Decimal("0")


def _componentvergelijking(testcase, detail: dict[str, Any]) -> list[dict[str, Any]]:
    """Bouw componentvergelijking verwacht versus applicatie."""
    verwacht = testcase.verwachte_belasting

    def _verwacht(naam: str) -> Decimal | None:
        waarde = getattr(verwacht, naam, None)
        return _naar_decimal(waarde) if waarde is not None else None

    def _ew_aanpassing(sleutel: str) -> Decimal:
        ew = detail.get(sleutel)
        if ew is None:
            return Decimal("0")
        if isinstance(ew, dict):
            return _naar_decimal(ew.get("tariefsaanpassing", Decimal("0")))
        return _naar_decimal(getattr(ew, "tariefsaanpassing", Decimal("0")))

    box1_ib_p1_app = _naar_decimal(detail.get("bel_voor_korting_p1")) + _ew_aanpassing("ew_p1")

    componenten: list[tuple[str, Decimal | None, Decimal | None]] = [
        ("box1_ib_p1", _verwacht("box1_ib_p1"), box1_ib_p1_app),
        ("totaal_premies_p1", _verwacht("totaal_premies_p1"), _naar_decimal(detail.get("totaal_premies_p1"))),
        ("totaal_kortingen_p1", _verwacht("totaal_kortingen_p1"), _naar_decimal(detail.get("totale_hk_p1"))),
        ("box3_heffing", _verwacht("box3_heffing"), _naar_decimal(detail.get("box3_heffing"))),
    ]

    if testcase.is_paar:
        box1_ib_p2_app = _naar_decimal(detail.get("bel_voor_korting_p2")) + _ew_aanpassing("ew_p2")
        componenten.extend(
            [
                ("box1_ib_p2", _verwacht("box1_ib_p2"), box1_ib_p2_app),
                ("totaal_premies_p2", _verwacht("totaal_premies_p2"), _naar_decimal(detail.get("totaal_premies_p2"))),
                ("totaal_kortingen_p2", _verwacht("totaal_kortingen_p2"), _naar_decimal(detail.get("totale_hk_p2"))),
            ]
        )

    resultaat: list[dict[str, Any]] = []
    for naam, verwacht_waarde, app_waarde in componenten:
        status, verschil = _status_en_verschil(verwacht_waarde, app_waarde)
        resultaat.append(
            {
                "naam": naam,
                "verwacht": verwacht_waarde,
                "applicatie": app_waarde,
                "verschil": verschil,
                "status": status,
            }
        )
    return resultaat


def _status(abs_verschil: Decimal) -> str:
    """Classificeer verschil volgens testcase-drempels."""
    if abs_verschil <= Decimal("5"):
        return "PASS"
    if abs_verschil <= Decimal("50"):
        return "WARN"
    return "FAIL"


def _bouw_rapport_markdown(testcase, validatie: dict[str, Any], detail: dict[str, Any], json_path: Path) -> str:
    """Bouw uitgebreid Markdown-rapport voor 1 testcase."""
    verwacht = _naar_decimal(validatie["verwacht"])
    berekend = _naar_decimal(validatie["berekend"])
    verschil = _naar_decimal(validatie["verschil"])
    status = str(validatie["status"])
    verwacht_bron = str(validatie.get("verwacht_bron", "huishoudtotaal"))
    data_waarschuwingen = list(validatie.get("data_waarschuwingen", []))

    box3_p1, box3_p2 = _bereken_box3_verdeling(testcase, detail)
    verwacht_p1 = (
        _naar_decimal(testcase.verwachte_belasting.totaal_verschuldigd_p1)
        if testcase.verwachte_belasting.totaal_verschuldigd_p1 is not None
        else None
    )
    verwacht_p2 = (
        _naar_decimal(testcase.verwachte_belasting.totaal_verschuldigd_p2)
        if testcase.verwachte_belasting.totaal_verschuldigd_p2 is not None
        else None
    )
    app_p1 = _naar_decimal(detail.get("netto_bel_p1")) + box3_p1
    app_p2 = _naar_decimal(detail.get("netto_bel_p2")) + box3_p2 if testcase.is_paar else None

    p1_status, p1_verschil = _status_en_verschil(verwacht_p1, app_p1)
    p2_status, p2_verschil = _status_en_verschil(verwacht_p2, app_p2)

    componenten = _componentvergelijking(testcase, detail)

    lines = [
        f"## Uitgebreid validatierapport - {testcase.testcase_id}",
        "",
        f"- Naam testcase: {testcase.naam}",
        f"- Jaar: {testcase.jaar}",
        f"- Tariefjaar gebruikt door engine: {detail.get('config_jaar', testcase.jaar)}",
        f"- Tariefaanname/fallback: {detail.get('aanname', 'geen')}",
        f"- Verwacht-bron voor validatie: {verwacht_bron}",
        f"- Eindstatus: {status}",
        "",
        "## 1. Inkomensopbouw",
        "",
        "| Component | P1 | P2 | Huishouden |",
        "|---|---:|---:|---:|",
        f"| Arbeidsinkomen | {_fmt_eur(_naar_decimal(detail.get('jaar_arbeid_p1')))} | {_fmt_eur(_naar_decimal(detail.get('jaar_arbeid_p2')))} | {_fmt_eur(_naar_decimal(detail.get('jaar_arbeid_p1')) + _naar_decimal(detail.get('jaar_arbeid_p2')))} |",
        f"| Pensioen | {_fmt_eur(_naar_decimal(detail.get('jaar_pen_p1')))} | {_fmt_eur(_naar_decimal(detail.get('jaar_pen_p2')))} | {_fmt_eur(_naar_decimal(detail.get('jaar_pen_p1')) + _naar_decimal(detail.get('jaar_pen_p2')))} |",
        f"| AOW | {_fmt_eur(_naar_decimal(detail.get('jaar_aow_p1')))} | {_fmt_eur(_naar_decimal(detail.get('jaar_aow_p2')))} | {_fmt_eur(_naar_decimal(detail.get('jaar_aow_p1')) + _naar_decimal(detail.get('jaar_aow_p2')))} |",
        f"| Overig inkomen | {_fmt_eur(_naar_decimal(detail.get('jaar_overig_p1')))} | {_fmt_eur(_naar_decimal(detail.get('jaar_overig_p2')))} | {_fmt_eur(_naar_decimal(detail.get('jaar_overig_p1')) + _naar_decimal(detail.get('jaar_overig_p2')))} |",
        f"| **Totaal bruto** | **{_fmt_eur(_naar_decimal(detail.get('bruto_p1')))}** | **{_fmt_eur(_naar_decimal(detail.get('bruto_p2')))}** | **{_fmt_eur(_naar_decimal(detail.get('bruto_p1')) + _naar_decimal(detail.get('bruto_p2')))}** |",
        "",
        "## 2. Berekeningsstappen applicatie",
        "",
        "### Persoon 1",
        "",
        f"- Box 1 grondslag = bruto + eigen woning mutatie = {_fmt_eur(_naar_decimal(detail.get('bruto_p1')))} + {_fmt_eur(_naar_decimal(detail.get('ew_p1').box1_mutatie if detail.get('ew_p1') is not None else Decimal('0')))} = {_fmt_eur(_naar_decimal(detail.get('box1_grondslag_p1')))}",
        f"- IB voor kortingen = {_fmt_eur(_naar_decimal(detail.get('bel_voor_korting_p1')))}",
        f"- Premies totaal = {_fmt_eur(_naar_decimal(detail.get('totaal_premies_p1')))}",
        f"- Tariefsaanpassing eigen woning = {_fmt_eur(_naar_decimal(detail.get('ew_p1').tariefsaanpassing if detail.get('ew_p1') is not None else Decimal('0')))}",
        f"- Heffingskortingen totaal = {_fmt_eur(_naar_decimal(detail.get('totale_hk_p1')))}",
        f"- Netto verschuldigd P1 = max(0, IB + premies + tariefsaanpassing - kortingen) = {_fmt_eur(_naar_decimal(detail.get('netto_bel_p1')))}",
        "",
    ]

    if testcase.is_paar:
        lines.extend(
            [
                "### Persoon 2",
                "",
                f"- Box 1 grondslag = bruto + eigen woning mutatie = {_fmt_eur(_naar_decimal(detail.get('bruto_p2')))} + {_fmt_eur(_naar_decimal(detail.get('ew_p2').box1_mutatie if detail.get('ew_p2') is not None else Decimal('0')))} = {_fmt_eur(_naar_decimal(detail.get('box1_grondslag_p2')))}",
                f"- IB voor kortingen = {_fmt_eur(_naar_decimal(detail.get('bel_voor_korting_p2')))}",
                f"- Premies totaal = {_fmt_eur(_naar_decimal(detail.get('totaal_premies_p2')))}",
                f"- Tariefsaanpassing eigen woning = {_fmt_eur(_naar_decimal(detail.get('ew_p2').tariefsaanpassing if detail.get('ew_p2') is not None else Decimal('0')))}",
                f"- Heffingskortingen totaal = {_fmt_eur(_naar_decimal(detail.get('totale_hk_p2')))}",
                f"- Netto verschuldigd P2 = max(0, IB + premies + tariefsaanpassing - kortingen) = {_fmt_eur(_naar_decimal(detail.get('netto_bel_p2')))}",
                "",
            ]
        )

    lines.extend(
        [
            "## 3. Vergelijking met Belastingdienst",
            "",
            "### Huishouden",
            "",
            "| Maatstaf | Belastingdienst | Applicatie | Verschil | Status |",
            "|---|---:|---:|---:|---|",
            f"| Totaal verschuldigd | {_fmt_eur(verwacht)} | {_fmt_eur(berekend)} | {_fmt_eur(verschil)} | {status} |",
            "",
            "### Per persoon",
            "",
            "| Persoon | Belastingdienst | Applicatie | Verschil | Status |",
            "|---|---:|---:|---:|---|",
            f"| P1 | {_fmt_eur(verwacht_p1)} | {_fmt_eur(app_p1)} | {_fmt_eur(p1_verschil)} | {p1_status} |",
        ]
    )

    if testcase.is_paar:
        lines.append(
            f"| P2 | {_fmt_eur(verwacht_p2)} | {_fmt_eur(app_p2)} | {_fmt_eur(p2_verschil)} | {p2_status} |"
        )

    lines.extend(
        [
            "",
            "### Componentniveau",
            "",
            "| Component | Belastingdienst | Applicatie | Verschil | Status |",
            "|---|---:|---:|---:|---|",
        ]
    )

    for item in componenten:
        lines.append(
            f"| {item['naam']} | {_fmt_eur(item['verwacht'])} | {_fmt_eur(item['applicatie'])} | {_fmt_eur(item['verschil'])} | {item['status']} |"
        )

    lines.extend(
        [
            "",
            "## 4. Box 3 en vermogenskoppeling",
            "",
            f"- Box 3 vrijstelling huishouden: {_fmt_eur(_naar_decimal(detail.get('box3_vrijstelling')))}",
            f"- Box 3 belastbare grondslag: {_fmt_eur(_naar_decimal(detail.get('box3_belastbaar')))}",
            f"- Box 3 heffing totaal: {_fmt_eur(_naar_decimal(detail.get('box3_heffing')))}",
            f"- Box 3 heffing P1: {_fmt_eur(box3_p1)}",
            f"- Box 3 heffing P2: {_fmt_eur(box3_p2 if testcase.is_paar else Decimal('0'))}",
            "",
            "## 5. Datakwaliteit en aandachtspunten",
            "",
        ]
    )

    if data_waarschuwingen:
        for waarschuwing in data_waarschuwingen:
            lines.append(f"- {waarschuwing}")
    else:
        lines.append("- Geen interne inconsistenties gedetecteerd in verwachte velden.")

    lines.extend(
        [
            "",
            "## 6. Reproduceerbaarheid",
            "",
            "Gebruik deze commandostructuur om dezelfde vergelijking opnieuw te draaien:",
            "",
            "- Één testcase: PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_010",
            "- Meerdere testcases: PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_008 tc_2025_010 tc_2025_011",
            "- Alle beschikbare cases in een directory: PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py --input-dir tests/fixtures/belasting_testcases/normalized",
            "",
            f"Volledige JSON dump: {json_path}",
        ]
    )

    return "\n".join(lines) + "\n"


def exporteer_testcase_detail(
    testcase_id: str,
    output_dir: Path,
    input_dir: Path,
) -> tuple[str, Decimal, Decimal, Decimal, str]:
    """Exporteer detailrapporten voor 1 testcase.

    Returns:
        tuple(testcase_id, verwacht, berekend, verschil, status)
    """
    testcase = vind_testcase_by_id(testcase_id, directory=input_dir)
    validatie = valideer_testcase(testcase)
    detail = validatie["details"]
    verwacht = _naar_decimal(validatie["verwacht"])
    berekend = _naar_decimal(validatie["berekend"])
    verschil = _naar_decimal(validatie["verschil"])
    status = str(validatie["status"])

    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"{testcase_id}_accountant_detail.json"
    md_path = output_dir / f"{testcase_id}_accountant_detail.md"

    payload = {
        "testcase": testcase.model_dump(mode="python"),
        "validatie": {
            "verwacht": verwacht,
            "berekend": berekend,
            "verschil": verschil,
            "status": status,
            "verwacht_bron": validatie.get("verwacht_bron"),
            "data_waarschuwingen": validatie.get("data_waarschuwingen", []),
        },
        "detail": detail,
    }
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, default=_serialize)

    md_inhoud = _bouw_rapport_markdown(testcase, validatie, detail, json_path)
    md_path.write_text(md_inhoud, encoding="utf-8")

    return testcase_id, verwacht, berekend, verschil, status


def _bouw_argumenten() -> argparse.Namespace:
    """Lees CLI-argumenten."""
    parser = argparse.ArgumentParser(
        description="Exporteer uitgebreide accountant-berekeningen per testcase",
    )
    parser.add_argument(
        "testcase_ids",
        nargs="*",
        help="Optionele lijst testcase IDs. Laat leeg om alle cases uit --input-dir te verwerken.",
    )
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_TESTCASE_DIR),
        help="Directory met genormaliseerde testcase JSON-bestanden.",
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

    input_dir = Path(args.input_dir)
    if args.testcase_ids:
        testcase_ids = args.testcase_ids
    else:
        testcase_ids = sorted(laad_alle_testcases(directory=input_dir).keys())
    output_dir = Path(args.output_dir)

    samenvatting = [
        "## Batch validatierapporten",
        "",
        f"- Input directory: {input_dir}",
        f"- Output directory: {output_dir}",
        f"- Aantal testcases: {len(testcase_ids)}",
        "",
        "| testcase | verwacht | berekend | verschil | status | markdown | json |",
        "|---|---:|---:|---:|---|---|---|",
    ]

    for testcase_id in testcase_ids:
        testcase_id, verwacht, berekend, verschil, status = exporteer_testcase_detail(
            testcase_id=testcase_id,
            output_dir=output_dir,
            input_dir=input_dir,
        )
        md_pad = output_dir / f"{testcase_id}_accountant_detail.md"
        json_pad = output_dir / f"{testcase_id}_accountant_detail.json"
        samenvatting.append(
            f"| {testcase_id} | {_fmt_num(verwacht)} | {_fmt_num(berekend)} | {_fmt_num(verschil)} | {status} | {md_pad} | {json_pad} |"
        )
        print(f"Export klaar voor {testcase_id} ({status})")

    summary_path = output_dir / args.summary_name
    summary_path.write_text("\n".join(samenvatting) + "\n", encoding="utf-8")
    print(f"Batchsamenvatting geschreven: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
