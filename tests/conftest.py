"""Gedeelde pytest-fixtures voor de volledige testsuite."""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

# Zorg dat tests altijd de projectconfigs gebruiken
os.environ.setdefault(
    "PENSIOEN_CONFIG_DIR",
    str(Path(__file__).parent.parent / "config"),
)

from pensioen.models.cashflow import HuishoudCashflow
from pensioen.models.component import CategorieComponent, FinancieelComponent, Frequentie
from pensioen.models.pensioen_record import PensioenRecord, TypePensioen
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import IncidenteelItem, Scenario


TESTLAAG_PER_MODULE: dict[str, tuple[str, ...]] = {
    "test_aow_engine.py": ("bouwsteen",),
    "test_api_main.py": ("contract",),
    "test_api_regressie_normalized.py": ("contract", "referentie"),
    "test_audit.py": ("bouwsteen",),
    "test_belasting_engine.py": ("bouwsteen",),
    "test_cashflow_engine.py": ("engine",),
    "test_eigen_woning_engine.py": ("bouwsteen",),
    "test_epic4_detailoutput.py": ("engine", "contract"),
    "test_epic5_consumptiecontract.py": ("contract", "presentatie"),
    "test_fiscale_bouwstenen.py": ("bouwsteen",),
    "test_grafiek_consistency.py": ("engine", "presentatie"),
    "test_grafiek_validator.py": ("presentatie",),
    "test_inheritance_engine.py": ("engine",),
    "test_parser_mpo.py": ("bouwsteen", "contract"),
    "test_pensioen_engine.py": ("bouwsteen",),
    "test_periodieke_waarde.py": ("bouwsteen",),
    "test_referentie_governance.py": ("referentie",),
    "test_regression_bugs.py": ("engine", "referentie"),
    "test_rendement_split.py": ("engine",),
    "test_scenario_context.py": ("presentatie",),
    "test_scenario_engine.py": ("engine",),
    "test_sessie_persistentie.py": ("contract",),
    "test_vermogen_engine.py": ("engine",),
    "test_vermogensitem.py": ("bouwsteen",),
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Ken de vastgelegde Epic 6-testlagen per module toe."""
    for item in items:
        for marker in TESTLAAG_PER_MODULE.get(item.path.name, ("engine",)):
            item.add_marker(getattr(pytest.mark, marker))


@pytest.fixture()
def persoon1() -> Persoon:
    """Persoon geboren 15 maart 1963 (AOW-leeftijd ≥ 67)."""
    return Persoon(naam="Jan Jansen", geboortedatum=date(1963, 3, 15), heeft_partner=True)


@pytest.fixture()
def persoon2() -> Persoon:
    """Partner geboren 22 juni 1965."""
    return Persoon(naam="Marie Jansen", geboortedatum=date(1965, 6, 22), heeft_partner=True)


@pytest.fixture()
def persoon_alleenstaand() -> Persoon:
    """Alleenstaande persoon geboren 1 oktober 1955 (AOW op 67)."""
    return Persoon(naam="Piet Pietersen", geboortedatum=date(1955, 10, 1), heeft_partner=False)


@pytest.fixture()
def pensioenrecord_p1() -> PensioenRecord:
    """Standaard ouderdomspensioen van €18.400/jaar, start 1 januari 2030."""
    return PensioenRecord(
        uitvoerder="ABP",
        regeling="Ouderdomspensioen Regeling A",
        type_pensioen=TypePensioen.OUDERDOMS,
        ingangsdatum=date(2030, 1, 1),
        bruto_per_jaar=Decimal("18400"),
        partnerpensioen_pct=Decimal("70"),
        indexatie_verwacht_pct=Decimal("2.0"),
        bronbestand="tests/fixtures/mpo_partner1.csv",
        peildatum=date(2026, 5, 1),
    )


@pytest.fixture()
def pensioenrecord_september_start() -> PensioenRecord:
    """Pensioen dat start op 17 september (test pro-rata berekening)."""
    return PensioenRecord(
        uitvoerder="Nationale Nederlanden",
        regeling="Aanvullend OP",
        type_pensioen=TypePensioen.OUDERDOMS,
        ingangsdatum=date(2031, 9, 17),
        bruto_per_jaar=Decimal("12000"),
        bronbestand="tests/fixtures/test",
        peildatum=date(2026, 5, 1),
    )


@pytest.fixture()
def scenario_standaard(persoon1: Persoon, persoon2: Persoon) -> Scenario:
    """Standaardscenario: stoppen op 62, spaargeld €50.000, rendement 3%."""
    return Scenario(
        naam="Stoppen op 62",
        spaargeld_start=Decimal("50000"),
        jaarlijkse_inleg=Decimal("5000"),
        rendement_pct=Decimal("3"),
        componenten=[
            FinancieelComponent(
                omschrijving="Salaris P1",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="P1",
                bedrag=Decimal("5000"),
                frequentie=Frequentie.MAANDELIJKS,
                einddatum=date(2025, 4, 1),
                groei_pct=Decimal("2"),
            ),
            FinancieelComponent(
                omschrijving="Salaris P2",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="P2",
                bedrag=Decimal("3333.33"),
                frequentie=Frequentie.MAANDELIJKS,
                einddatum=date(2027, 6, 30),
            ),
        ],
    )


@pytest.fixture()
def scenario_geen_pensioen() -> Scenario:
    """Scenario voor iemand zonder pensioenrekeningen."""
    return Scenario(
        naam="Geen pensioen",
        spaargeld_start=Decimal("200000"),
        rendement_pct=Decimal("3"),
    )


@pytest.fixture()
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"
