"""Tests voor de nieuwe FastAPI-laag."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from pensioen.api.main import app
from pensioen.models.pensioen_record import PensioenRecord, TypePensioen
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


def test_referenties_codes_endpoint() -> None:
    response = client.get("/api/v1/referenties/codes")
    assert response.status_code == 200
    data = response.json()["codes"]
    assert "categorieen" in data
    assert data["categorieen"]["arbeidsinkomen"] == "Arbeidsinkomen"
    assert "frequenties" in data
    assert data["frequenties"]["maandelijks"] == "Maandelijks"
    assert "foutcodes" in data
    assert "derived_scenario_requires_list" in data["foutcodes"]


def test_referenties_input_hints_endpoint() -> None:
    response = client.get("/api/v1/referenties/input-hints")
    assert response.status_code == 200
    hints = response.json()["hints"]
    assert "berekening" in hints
    assert "required" in hints["berekening"]
    assert "scenario" in hints
    assert "defaults" in hints["scenario"]
    assert hints["component"]["defaults"]["frequentie"] == "maandelijks"


def test_import_mpo_pdf_endpoint_happy_path(monkeypatch) -> None:
    def fake_parse_pdf(_pad):
        return [
            PensioenRecord(
                uitvoerder="ABP",
                regeling="Ouderdomspensioen",
                type_pensioen=TypePensioen.OUDERDOMS,
                ingangsdatum=date(2030, 1, 1),
                bruto_per_jaar=Decimal("12000"),
            )
        ]

    monkeypatch.setattr("pensioen.api.main.MPOParser.parse_pdf", fake_parse_pdf)

    response = client.post(
        "/api/v1/import/mpo/pdf",
        files={"bestand": ("mpo.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["aantal_records"] == 1
    assert data["records"][0]["uitvoerder"] == "ABP"


def test_import_mpo_pdf_endpoint_rejects_non_pdf() -> None:
    response = client.post(
        "/api/v1/import/mpo/pdf",
        files={"bestand": ("mpo.txt", b"geen pdf", "text/plain")},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "invalid_file_type"


def test_import_mpo_pdf_endpoint_rejects_empty_pdf() -> None:
    response = client.post(
        "/api/v1/import/mpo/pdf",
        files={"bestand": ("leeg.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "empty_file"


def test_berekeningen_endpoint_happy_path(persoon1, scenario_standaard) -> None:
    payload = _payload_berekening(persoon1, scenario_standaard)
    response = client.post("/api/v1/berekeningen", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "cashflow" in data
    assert data["cashflow"]["scenario_naam"] == scenario_standaard.naam
    assert len(data["cashflow"]["jaren"]) == 3


def test_berekeningen_endpoint_normaliseert_codes(persoon1, scenario_standaard) -> None:
    payload = _payload_berekening(persoon1, scenario_standaard)
    payload["scenario"]["componenten"][0]["categorie"] = "ARBEIDS INKOMEN"
    payload["scenario"]["componenten"][0]["frequentie"] = "MAANDELIJKS"
    payload["scenario"]["componenten"][0]["bedrag_type"] = "BRUTO"
    payload["scenario"]["componenten"][0]["beleggings_type"] = "SPAAR"
    payload["scenario"]["vermogensitems"] = [
        {
            "omschrijving": "Eigen woning",
            "type": "EIGEN WONING",
            "persoon": "Huishouden",
            "aanschafwaarde": "400000",
            "groei_pct": "2",
            "box3_belast": False,
        }
    ]

    response = client.post("/api/v1/berekeningen", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "cashflow" in data


def test_berekeningen_endpoint_accepteert_legacy_code_varianten(
    persoon1, scenario_standaard
) -> None:
    payload = _payload_berekening(persoon1, scenario_standaard)
    payload["scenario"]["componenten"][0]["categorie"] = "PENSIOEN INKOMEN"
    payload["scenario"]["componenten"][0]["frequentie"] = "HALF JAARLIJKS"
    payload["scenario"]["componenten"][0]["bedrag_type"] = "NETTO"
    payload["scenario"]["componenten"][0]["beleggings_type"] = "SPAREN"
    payload["scenario"]["vermogensitems"] = [
        {
            "omschrijving": "Woning",
            "type": "EIGENWONING",
            "persoon": "Huishouden",
            "aanschafwaarde": "450000",
            "groei_pct": "2",
            "box3_belast": False,
        }
    ]

    response = client.post("/api/v1/berekeningen", json=payload)

    assert response.status_code == 200


def test_rapportage_endpoint_normaliseert_codes_in_geneste_payload(
    persoon1, scenario_standaard
) -> None:
    payload = {
        "berekening": _payload_berekening(persoon1, scenario_standaard),
        "include_vergelijking": True,
        "scenarios_vergelijking": [scenario_standaard.model_dump(mode="json")],
    }

    payload["berekening"]["scenario"]["componenten"][0]["categorie"] = "OVERIG INKOMEN"
    payload["berekening"]["scenario"]["componenten"][0]["frequentie"] = "KWARTAAL"
    payload["scenarios_vergelijking"][0]["componenten"][0]["categorie"] = "ARBEIDS INKOMEN"

    response = client.post("/api/v1/rapportages/excel", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


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


def test_vergelijkingen_endpoint_inheritance_cycle_returns_422(
    persoon1, scenario_standaard
) -> None:
    scenario_a = scenario_standaard.model_copy(deep=True)
    scenario_a.naam = "Scenario A"
    scenario_a.parent_naam = "Scenario B"

    scenario_b = scenario_standaard.model_copy(deep=True)
    scenario_b.naam = "Scenario B"
    scenario_b.parent_naam = "Scenario A"

    payload = {
        "scenarios": [
            scenario_a.model_dump(mode="json"),
            scenario_b.model_dump(mode="json"),
        ],
        "persoon1": persoon1.model_dump(mode="json"),
        "persoon2": None,
        "records1": [],
        "records2": [],
        "jaar_van": 2026,
        "jaar_tot": 2028,
    }

    response = client.post("/api/v1/vergelijkingen", json=payload)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "inheritance_validation_error"
    assert detail["waarschuwingen"]


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


def test_rapportage_excel_endpoint_derived_requires_scenario_lijst(
    persoon1, scenario_standaard
) -> None:
    afgeleid = Scenario(
        naam="Afgeleid rapportscenario",
        parent_naam=scenario_standaard.naam,
        overrides={"jaarlijkse_inleg_sparen": "2500"},
    )

    payload = {
        "berekening": {
            "scenario": afgeleid.model_dump(mode="json"),
            "persoon1": persoon1.model_dump(mode="json"),
            "persoon2": None,
            "records1": [],
            "records2": [],
            "jaar_van": 2026,
            "jaar_tot": 2028,
            "scenario_lijst": [],
        },
        "include_vergelijking": False,
        "scenarios_vergelijking": [],
    }

    response = client.post("/api/v1/rapportages/excel", json=payload)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "derived_scenario_requires_list"
