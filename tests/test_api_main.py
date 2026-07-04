"""Tests voor de nieuwe FastAPI-laag."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from pensioen.api.main import app
from pensioen.models.scenario import Scenario


client = TestClient(app)


def _payload_berekening(persoon1, scenario_standaard) -> dict:
    return {
        "scenario": scenario_standaard.model_dump(mode="json"),
        "persoon1": persoon1.model_dump(mode="json"),
        "persoon2": None,
        "records1": [],
        "records2": [],
        "jaar_van": 2026,
        "jaar_tot": 2028,
        "scenario_lijst": [scenario_standaard.model_dump(mode="json")],
    }


def test_healthcheck() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_berekeningen_endpoint_happy_path(persoon1, scenario_standaard) -> None:
    payload = _payload_berekening(persoon1, scenario_standaard)
    response = client.post("/api/v1/berekeningen", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "cashflow" in data
    assert data["cashflow"]["scenario_naam"] == scenario_standaard.naam
    assert len(data["cashflow"]["jaren"]) == 3


def test_berekeningen_endpoint_derived_requires_scenario_lijst(persoon1, scenario_standaard) -> None:
    afgeleid = Scenario(
        naam="Afgeleid scenario",
        parent_naam=scenario_standaard.naam,
        overrides={"jaarlijkse_inleg_sparen": "2500"},
    )
    payload = {
        "scenario": afgeleid.model_dump(mode="json"),
        "persoon1": persoon1.model_dump(mode="json"),
        "persoon2": None,
        "records1": [],
        "records2": [],
        "jaar_van": 2026,
        "jaar_tot": 2028,
        "scenario_lijst": [],
    }
    response = client.post("/api/v1/berekeningen", json=payload)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "derived_scenario_requires_list"


def test_vergelijkingen_endpoint_happy_path(persoon1, scenario_standaard) -> None:
    scenario_2 = scenario_standaard.model_copy(deep=True)
    scenario_2.naam = "Alternatief"
    scenario_2.spaargeld_start = Decimal("100000")

    payload = {
        "scenarios": [
            scenario_standaard.model_dump(mode="json"),
            scenario_2.model_dump(mode="json"),
        ],
        "persoon1": persoon1.model_dump(mode="json"),
        "persoon2": None,
        "records1": [],
        "records2": [],
        "jaar_van": 2026,
        "jaar_tot": 2030,
    }

    response = client.post("/api/v1/vergelijkingen", json=payload)

    assert response.status_code == 200
    data = response.json()["vergelijking"]
    assert len(data["scenario_resultaten"]) == 2


def test_rapportage_excel_endpoint(persoon1, scenario_standaard) -> None:
    payload = {
        "berekening": _payload_berekening(persoon1, scenario_standaard),
        "include_vergelijking": False,
        "scenarios_vergelijking": [],
    }

    response = client.post("/api/v1/rapportages/excel", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert len(response.content) > 0
