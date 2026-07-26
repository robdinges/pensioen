"""Governancetest voor expliciet geregistreerde externe afwijkingen."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from tests.testcase_loader import vind_testcase_by_id
from tests.testcase_validatie import valideer_testcase


REGISTER_PAD = Path(
    "tests/fixtures/belasting_testcases/bekende_afwijkingen.json"
)
with open(REGISTER_PAD, encoding="utf-8") as register_bestand:
    REGISTER = json.load(register_bestand)


@pytest.mark.referentie
@pytest.mark.parametrize(
    ("testcase_id", "verwachting"),
    REGISTER["afwijkingen"].items(),
    ids=REGISTER["afwijkingen"].keys(),
)
def test_bekende_externe_afwijking_blijft_expliciet(
    testcase_id: str,
    verwachting: dict[str, str],
) -> None:
    """Een verandering in bekende afwijking vereist bewuste herclassificatie."""
    resultaat = valideer_testcase(vind_testcase_by_id(testcase_id))
    tolerantie = Decimal(REGISTER["tolerantie_verschil"])

    assert resultaat["status"] == verwachting["status"]
    assert abs(resultaat["verschil"] - Decimal(verwachting["verschil"])) <= tolerantie
    assert verwachting["classificatie"] in {
        "codebug",
        "bronconflict",
        "referentieschuld",
        "tolerantieverschil",
        "nog_te_onderzoeken",
    }
    assert verwachting["eigenaar"]
    assert verwachting["vervolgstap"]
