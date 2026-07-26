"""Gedeelde voorbereidingslaag voor resultaatconsumenten."""

from __future__ import annotations

from dataclasses import dataclass

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.models.cashflow import HuishoudCashflow
from pensioen.models.pensioen_record import PensioenRecord
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.tax.belasting_loader import (
    BelastingConfig,
    laad_tarieven_bereik,
    resolve_tariefwaarden_voor_jaar,
)


@dataclass(frozen=True)
class ResultaatVoorbereiding:
    """Centraal voorbereide tarieven en herkomstmetadata per jaar."""

    configs: dict[int, tuple[BelastingConfig, str]]
    tarief_bronnen: dict[int, dict[str, str]]


def bouw_resultaat_voorbereiding(
    scenario: Scenario,
    jaar_van: int,
    jaar_tot: int,
) -> ResultaatVoorbereiding:
    """Bereid tarieven en bronmetadata eenmaal voor alle resultaatpaden voor."""
    basis_configs = laad_tarieven_bereik(jaar_van, jaar_tot)
    configs: dict[int, tuple[BelastingConfig, str]] = {}
    tarief_bronnen: dict[int, dict[str, str]] = {}
    for jaar, (config, melding) in basis_configs.items():
        opgelost, bronnen = resolve_tariefwaarden_voor_jaar(
            config,
            jaar,
            scenario.tarief_periodes,
        )
        configs[jaar] = (opgelost, melding)
        tarief_bronnen[jaar] = bronnen
    return ResultaatVoorbereiding(
        configs=configs,
        tarief_bronnen=tarief_bronnen,
    )


def bouw_belasting_configs_voor_scenario(
    scenario: Scenario,
    jaar_van: int,
    jaar_tot: int,
) -> dict[int, tuple[BelastingConfig, str]]:
    """Bouw resolved tariefconfiguratie voor één scenario en periode."""
    return bouw_resultaat_voorbereiding(
        scenario,
        jaar_van,
        jaar_tot,
    ).configs


def bereken_resultaten(
    scenario: Scenario,
    persoon1: Persoon,
    persoon2: Persoon | None,
    records1: list[PensioenRecord],
    records2: list[PensioenRecord],
    jaar_van: int,
    jaar_tot: int,
    scenario_lijst: list[Scenario] | None = None,
    voorbereiding: ResultaatVoorbereiding | None = None,
) -> HuishoudCashflow:
    """Bereken resultaatoutput met centraal voorbereide tariefconfiguratie."""
    return bereken_huishouden(
        scenario=scenario,
        persoon1=persoon1,
        persoon2=persoon2,
        records1=records1,
        records2=records2,
        jaar_van=jaar_van,
        jaar_tot=jaar_tot,
        belasting_configs=(
            voorbereiding
            or bouw_resultaat_voorbereiding(scenario, jaar_van, jaar_tot)
        ).configs,
        scenario_lijst=scenario_lijst,
    )
