"""Tests voor inheritance resolution engine."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from pensioen.calculations.inheritance_engine import (
    InheritanceError,
    get_override_chain,
    get_parent_chain,
    resolve_scenario,
    validate_inheritance_tree,
)
from pensioen.models.scenario import Scenario


@pytest.fixture
def base_scenario() -> Scenario:
    """Base scenario zonder parent."""
    return Scenario(
        naam="Base",
        omschrijving="Basis scenario",
        rendement_sparen_pct=Decimal("3"),
        rendement_beleggen_pct=Decimal("5"),
        inflatie_pct=Decimal("2"),
        spaargeld_start=Decimal("50000"),
        beleggingen_start=Decimal("100000"),
    )


@pytest.fixture
def derived_scenario_1level(base_scenario: Scenario) -> Scenario:
    """1-level afgeleid scenario (parent = Base)."""
    return Scenario(
        naam="Optimistisch",
        omschrijving="Optimistisch scenario",
        parent_naam="Base",
        overrides={
            "rendement_sparen_pct": "5.0",  # Override naar 5%
            "inflatie_pct": "1.5",  # Override naar 1.5%
        },
        # Andere velden worden geërfd van Base
        rendement_sparen_pct=Decimal("5"),
        rendement_beleggen_pct=Decimal("5"),  # Dezelfde als Base (geen override)
        inflatie_pct=Decimal("1.5"),
        spaargeld_start=Decimal("50000"),  # Geërfd
        beleggingen_start=Decimal("100000"),  # Geërfd
    )


@pytest.fixture
def derived_scenario_2level(derived_scenario_1level: Scenario) -> Scenario:
    """2-level afgeleid scenario (parent = Optimistisch)."""
    return Scenario(
        naam="Ultra-Optimistisch",
        omschrijving="Ultra-optimistisch scenario",
        parent_naam="Optimistisch",
        overrides={
            "rendement_beleggen_pct": "7.0",  # Nieuw override
        },
        rendement_sparen_pct=Decimal("5"),  # Geërfd van Optimistisch
        rendement_beleggen_pct=Decimal("7"),  # Override
        inflatie_pct=Decimal("1.5"),  # Geërfd van Optimistisch
        spaargeld_start=Decimal("50000"),
        beleggingen_start=Decimal("100000"),
    )


def test_base_scenario_is_base(base_scenario: Scenario) -> None:
    """Test dat base scenario correct geïdentificeerd wordt."""
    assert base_scenario.is_base_scenario()
    assert not base_scenario.is_derived_scenario()
    assert base_scenario.parent_naam is None
    assert base_scenario.get_override_count() == 0


def test_derived_scenario_is_derived(derived_scenario_1level: Scenario) -> None:
    """Test dat afgeleid scenario correct geïdentificeerd wordt."""
    assert not derived_scenario_1level.is_base_scenario()
    assert derived_scenario_1level.is_derived_scenario()
    assert derived_scenario_1level.parent_naam == "Base"
    assert derived_scenario_1level.get_override_count() == 2


def test_resolve_base_scenario(base_scenario: Scenario) -> None:
    """Test dat resolve van base scenario het origineel teruggeeft."""
    resolved = resolve_scenario(base_scenario, [base_scenario])
    assert resolved.naam == base_scenario.naam
    assert resolved.rendement_sparen_pct == Decimal("3")
    assert resolved.inflatie_pct == Decimal("2")


def test_resolve_1level_inheritance(
    base_scenario: Scenario, derived_scenario_1level: Scenario
) -> None:
    """Test 1-level inheritance resolution."""
    scenario_lijst = [base_scenario, derived_scenario_1level]
    resolved = resolve_scenario(derived_scenario_1level, scenario_lijst)

    # Check overridden values
    assert resolved.rendement_sparen_pct == Decimal("5")  # Overridden
    assert resolved.inflatie_pct == Decimal("1.5")  # Overridden

    # Check inherited values
    assert resolved.rendement_beleggen_pct == Decimal("5")  # Inherited from Base
    assert resolved.spaargeld_start == Decimal("50000")  # Inherited from Base
    assert resolved.beleggingen_start == Decimal("100000")  # Inherited from Base

    # Metadata should remain from derived scenario
    assert resolved.naam == "Optimistisch"


def test_resolve_2level_inheritance(
    base_scenario: Scenario,
    derived_scenario_1level: Scenario,
    derived_scenario_2level: Scenario,
) -> None:
    """Test 2-level inheritance chain (Base → Optimistisch → Ultra-Optimistisch)."""
    scenario_lijst = [base_scenario, derived_scenario_1level, derived_scenario_2level]
    resolved = resolve_scenario(derived_scenario_2level, scenario_lijst)

    # rendement_sparen_pct: geërfd van Optimistisch (die override van Base)
    assert resolved.rendement_sparen_pct == Decimal("5")

    # rendement_beleggen_pct: override in Ultra-Optimistisch
    assert resolved.rendement_beleggen_pct == Decimal("7")

    # inflatie_pct: geërfd van Optimistisch (die override van Base)
    assert resolved.inflatie_pct == Decimal("1.5")

    # spaargeld_start: geërfd van Base (via chain)
    assert resolved.spaargeld_start == Decimal("50000")

    assert resolved.naam == "Ultra-Optimistisch"


def test_get_parent_chain_base(base_scenario: Scenario) -> None:
    """Test parent chain voor base scenario."""
    chain = get_parent_chain(base_scenario, [base_scenario])
    assert chain == ["Base"]


def test_get_parent_chain_1level(
    base_scenario: Scenario, derived_scenario_1level: Scenario
) -> None:
    """Test parent chain voor 1-level derived scenario."""
    scenario_lijst = [base_scenario, derived_scenario_1level]
    chain = get_parent_chain(derived_scenario_1level, scenario_lijst)
    assert chain == ["Optimistisch", "Base"]


def test_get_parent_chain_2level(
    base_scenario: Scenario,
    derived_scenario_1level: Scenario,
    derived_scenario_2level: Scenario,
) -> None:
    """Test parent chain voor 2-level derived scenario."""
    scenario_lijst = [base_scenario, derived_scenario_1level, derived_scenario_2level]
    chain = get_parent_chain(derived_scenario_2level, scenario_lijst)
    assert chain == ["Ultra-Optimistisch", "Optimistisch", "Base"]


def test_get_override_chain(
    base_scenario: Scenario, derived_scenario_1level: Scenario
) -> None:
    """Test override chain voor specifiek veld."""
    scenario_lijst = [base_scenario, derived_scenario_1level]
    
    # rendement_sparen_pct is overridden in Optimistisch
    chain = get_override_chain(derived_scenario_1level, "rendement_sparen_pct", scenario_lijst)
    assert len(chain) == 2
    assert chain[0] == ("Optimistisch", "5.0")  # Override value uit overrides dict
    assert chain[1][0] == "Base"

    # rendement_beleggen_pct is NIET overridden, wordt geërfd
    chain_inherited = get_override_chain(derived_scenario_1level, "rendement_beleggen_pct", scenario_lijst)
    assert len(chain_inherited) >= 1  # Minstens Base scenario


def test_validate_no_warnings_valid_tree(
    base_scenario: Scenario, derived_scenario_1level: Scenario
) -> None:
    """Test validatie voor geldige inheritance tree."""
    scenario_lijst = [base_scenario, derived_scenario_1level]
    warnings = validate_inheritance_tree(scenario_lijst)
    assert len(warnings) == 0


def test_validate_orphaned_scenario() -> None:
    """Test detectie van orphaned scenario (parent bestaat niet)."""
    orphaned = Scenario(
        naam="Orphan",
        parent_naam="NonExistent",
        rendement_sparen_pct=Decimal("3"),
    )
    warnings = validate_inheritance_tree([orphaned])
    assert len(warnings) == 1
    assert "niet-bestaande parent" in warnings[0]
    assert "NonExistent" in warnings[0]


def test_validate_circular_dependency() -> None:
    """Test detectie van circulaire parent chain."""
    scenario_a = Scenario(
        naam="A",
        parent_naam="B",
        rendement_sparen_pct=Decimal("3"),
    )
    scenario_b = Scenario(
        naam="B",
        parent_naam="A",
        rendement_sparen_pct=Decimal("3"),
    )
    warnings = validate_inheritance_tree([scenario_a, scenario_b])
    assert len(warnings) >= 1
    assert "Circulaire" in warnings[0] or "circulaire" in warnings[0].lower()


def test_self_parenting_prevented_in_model() -> None:
    """Test dat self-parenting wordt afgevangen door Pydantic validator."""
    with pytest.raises(ValueError, match="self-parenting"):
        Scenario(
            naam="SelfParent",
            parent_naam="SelfParent",
            rendement_sparen_pct=Decimal("3"),
        )


def test_override_helpers() -> None:
    """Test helper methods voor overrides."""
    scenario = Scenario(
        naam="Test",
        parent_naam="Base",
        rendement_sparen_pct=Decimal("3"),
    )

    # Initieel geen overrides
    assert scenario.get_override_count() == 0
    assert not scenario.is_override("rendement_sparen_pct")

    # Voeg override toe
    scenario.set_override("rendement_sparen_pct", "5.0")
    assert scenario.get_override_count() == 1
    assert scenario.is_override("rendement_sparen_pct")
    assert scenario.overrides["rendement_sparen_pct"] == "5.0"

    # Verwijder override
    scenario.remove_override("rendement_sparen_pct")
    assert scenario.get_override_count() == 0
    assert not scenario.is_override("rendement_sparen_pct")


def test_resolve_orphaned_scenario_gracefully() -> None:
    """Test dat resolve van orphaned scenario geen crash geeft."""
    orphaned = Scenario(
        naam="Orphan",
        parent_naam="NonExistent",
        rendement_sparen_pct=Decimal("3"),
    )
    # Moet het originele scenario teruggeven zonder parent resolve
    resolved = resolve_scenario(orphaned, [orphaned])
    assert resolved.naam == "Orphan"
