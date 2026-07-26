"""Contracttests voor pure resultaatconsumenten uit Epic 5."""

from __future__ import annotations

from pathlib import Path

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.calculations.resultaat_service import (
    bereken_resultaten,
    bouw_belasting_configs_voor_scenario,
    bouw_resultaat_voorbereiding,
)


def test_resultaat_service_levert_dezelfde_engine_output(
    persoon1,
    persoon2,
    scenario_standaard,
) -> None:
    configs = bouw_belasting_configs_voor_scenario(
        scenario_standaard,
        2026,
        2027,
    )
    voorbereiding = bouw_resultaat_voorbereiding(
        scenario_standaard,
        2026,
        2027,
    )
    assert configs == voorbereiding.configs
    assert set(voorbereiding.tarief_bronnen) == {2026, 2027}
    direct = bereken_huishouden(
        scenario=scenario_standaard,
        persoon1=persoon1,
        persoon2=persoon2,
        records1=[],
        records2=[],
        jaar_van=2026,
        jaar_tot=2027,
        belasting_configs=configs,
    )
    via_service = bereken_resultaten(
        scenario=scenario_standaard,
        persoon1=persoon1,
        persoon2=persoon2,
        records1=[],
        records2=[],
        jaar_van=2026,
        jaar_tot=2027,
    )

    assert [jaar.jaar_samenvatting for jaar in via_service.jaren] == [
        jaar.jaar_samenvatting for jaar in direct.jaren
    ]
    for via_jaar, direct_jaar in zip(via_service.jaren, direct.jaren, strict=True):
        assert via_jaar.accountant_detail["totaal_netto_inkomen"] == (
            direct_jaar.accountant_detail["totaal_netto_inkomen"]
        )
        assert via_jaar.accountant_detail["saldo_einde_jaar"] == (
            direct_jaar.accountant_detail["saldo_einde_jaar"]
        )
        assert via_jaar.accountant_detail["tarief_bronnen"]


def test_presentatiepaden_bevatten_geen_fiscale_fallbacks() -> None:
    projectroot = Path(__file__).parents[1]
    api_client = (projectroot / "app_api_client.py").read_text(encoding="utf-8")
    planner_core = (
        projectroot / "frontend-react/src/planner/plannerCore.js"
    ).read_text(encoding="utf-8")

    assert "_bereken_maand_netto" not in api_client
    assert "belastingMaand" not in planner_core
    assert "nettoMaand" not in planner_core
    assert "jaar_samenvatting ontbreekt" in api_client
    assert "jaar_samenvatting ontbreekt" in planner_core
