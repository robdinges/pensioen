"""API-regressietest op genormaliseerde IB-testcases."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pensioen.api.main import app
from tests.scenario_generator import genereer_testcase_scenario
from tests.testcase_loader import iter_testcases


client = TestClient(app)
BASELINE_BESTAND = Path("tests/fixtures/belasting_testcases/api_regressie_baseline.json")


def _laad_baseline() -> tuple[dict[str, Decimal], Decimal]:
    with open(BASELINE_BESTAND, encoding="utf-8") as bestand:
        data = json.load(bestand)

    per_case_raw = data.get("baseline_afwijking", {})
    per_case = {
        testcase_id: Decimal(str(waarde))
        for testcase_id, waarde in per_case_raw.items()
    }
    tolerantie = Decimal(str(data.get("tolerantie", "0.01")))
    return per_case, tolerantie


BASELINE_AFWIJKING, TOLERANTIE_BASELINE = _laad_baseline()


BEKENDE_AFWIJKINGEN = {
    "tc_2025_013": "OLA afrondingsschuld: centenberekening versus hele euro's; bron blijft ongewijzigd",
    "tc_2025_014": "OLA afrondingsschuld: centenberekening versus hele euro's; bron blijft ongewijzigd",
    "tc_2025_010": (
        "E6-AFW-002: automatische AOW-bron wijkt af van het bruto AOW-bedrag "
        "in de externe testcase; bronkeuze vereist productvalidatie"
    ),
}


TESTCASE_DATA = list(iter_testcases())
TESTCASES = [
    pytest.param(
        pad,
        testcase,
        marks=(
            pytest.mark.xfail(
                strict=True,
                reason=BEKENDE_AFWIJKINGEN[testcase.testcase_id],
            )
            if testcase.testcase_id in BEKENDE_AFWIJKINGEN
            else ()
        ),
    )
    for pad, testcase in TESTCASE_DATA
]
TESTCASE_IDS = [testcase.testcase_id for _, testcase in TESTCASE_DATA]


@pytest.mark.parametrize(
    ("testcase_pad", "testcase"),
    TESTCASES,
    ids=TESTCASE_IDS,
)
def test_api_berekeningen_regressie_genormaliseerde_cases(testcase_pad, testcase) -> None:
    """Bewak dat API-afwijking t.o.v. testcaseverwachting niet verslechtert."""
    personen, scenario = genereer_testcase_scenario(testcase)
    persoon1 = personen[0]
    persoon2 = personen[1] if len(personen) > 1 else None

    payload = {
        "scenario": scenario.model_dump(mode="json"),
        "persoon1": persoon1.model_dump(mode="json"),
        "persoon2": persoon2.model_dump(mode="json") if persoon2 else None,
        "records1": [],
        "records2": [],
        "jaar_van": testcase.jaar,
        "jaar_tot": testcase.jaar,
        "scenario_lijst": [scenario.model_dump(mode="json")],
    }

    response = client.post("/api/v1/berekeningen", json=payload)
    assert response.status_code == 200, f"{testcase.testcase_id} uit {testcase_pad.name}"

    data = response.json()["cashflow"]
    jaren = data["jaren"]
    assert len(jaren) == 1

    maanden = jaren[0]["maanden"]
    assert len(maanden) == 12

    totaal_verschuldigd_api = sum(
        (
            Decimal(str(maand["belasting_p1"]))
            + Decimal(str(maand["belasting_p2"]))
            + Decimal(str(maand["box3_heffing"]))
            - Decimal(str(maand["heffingskorting_p1"]))
            - Decimal(str(maand["heffingskorting_p2"]))
        )
        for maand in maanden
    )

    verwacht = testcase.verwachte_belasting.totaal_verschuldigd
    afwijking = abs(totaal_verschuldigd_api - verwacht)

    baseline = BASELINE_AFWIJKING.get(testcase.testcase_id)
    if testcase.testcase_id in {"tc_2025_013", "tc_2025_014"}:
        baseline = Decimal("1")  # De oorspronkelijke OLA-tolerantie blijft intact.
    assert baseline is not None, f"Geen baseline-afwijking geconfigureerd voor {testcase.testcase_id}"
    assert afwijking <= baseline + TOLERANTIE_BASELINE, (
        f"{testcase.testcase_id}: afwijking verslechterd naar {afwijking} "
        f"(baseline={baseline}, api={totaal_verschuldigd_api}, verwacht={verwacht})"
    )
