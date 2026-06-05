"""Inheritance resolution engine voor scenario's met parent-child relaties."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from pensioen.models.scenario import Scenario

logger = logging.getLogger(__name__)


class InheritanceError(Exception):
    """Exception voor inheritance-gerelateerde fouten (cycles, orphans, etc.)."""


def validate_inheritance_tree(scenario_lijst: list[Scenario]) -> list[str]:
    """
    Valideer de inheritance tree en retourneer lijst van waarschuwingen.

    Detecteert:
    - Circulaire parent chains (A → B → C → A)
    - Orphaned scenarios (parent bestaat niet)
    - Self-parenting (scenario wijst naar zichzelf)

    Args:
        scenario_lijst: Lijst van alle scenario's.

    Returns:
        Lijst van waarschuwingen (lege lijst = geen problemen).
    """
    warnings: list[str] = []
    scenario_namen = {s.naam for s in scenario_lijst}

    for scenario in scenario_lijst:
        if scenario.parent_naam is None:
            continue  # Base scenario, geen validatie nodig

        # Check 1: Self-parenting
        if scenario.parent_naam == scenario.naam:
            warnings.append(
                f"Scenario '{scenario.naam}' wijst naar zichzelf als parent (self-parenting)"
            )
            continue

        # Check 2: Orphaned scenario (parent bestaat niet)
        if scenario.parent_naam not in scenario_namen:
            warnings.append(
                f"Scenario '{scenario.naam}' wijst naar niet-bestaande parent '{scenario.parent_naam}'"
            )
            continue

        # Check 3: Circular dependency
        try:
            _detect_circular_chain(scenario.naam, scenario_lijst, set())
        except InheritanceError as e:
            warnings.append(str(e))

    return warnings


def _detect_circular_chain(
    naam: str, scenario_lijst: list[Scenario], visited: set[str]
) -> None:
    """
    Detecteer circulaire parent chains recursief.

    Raises:
        InheritanceError: Als circulaire keten gedetecteerd wordt.
    """
    if naam in visited:
        chain = " → ".join(visited) + f" → {naam}"
        raise InheritanceError(
            f"Circulaire parent chain gedetecteerd: {chain}"
        )

    visited.add(naam)

    scenario = next((s for s in scenario_lijst if s.naam == naam), None)
    if scenario is None or scenario.parent_naam is None:
        return  # Einde van chain bereikt

    _detect_circular_chain(scenario.parent_naam, scenario_lijst, visited)


def get_parent_chain(scenario: Scenario, scenario_lijst: list[Scenario]) -> list[str]:
    """
    Geef de volledige parent chain voor een scenario.

    Args:
        scenario: Het scenario waarvoor de chain bepaald wordt.
        scenario_lijst: Lijst van alle scenario's.

    Returns:
        Lijst van scenario namen van kind naar root, bijv. ["Kind", "Parent", "Base"].
        Voor een base scenario: [scenario.naam].
    """
    chain = [scenario.naam]
    current = scenario

    while current.parent_naam is not None:
        parent_naam = current.parent_naam
        if parent_naam in chain:
            # Circulaire chain gedetecteerd (zou niet mogen voorkomen na validatie)
            logger.warning(
                f"Circulaire chain gedetecteerd in get_parent_chain: {chain}"
            )
            break

        chain.append(parent_naam)
        current = next((s for s in scenario_lijst if s.naam == parent_naam), None)
        if current is None:
            # Orphaned scenario (parent niet gevonden)
            logger.warning(
                f"Parent '{parent_naam}' niet gevonden voor scenario '{scenario.naam}'"
            )
            break

    return chain


def resolve_scenario(
    scenario: Scenario, scenario_lijst: list[Scenario]
) -> Scenario:
    """
    Resolveer een scenario door parent waarden recursief te mergen.

    Voor een scenario met parent: merge alle parent velden in volgorde van
    root → child. Overrides in het child scenario hebben voorrang.

    Args:
        scenario: Het scenario dat geresolveerd moet worden.
        scenario_lijst: Lijst van alle scenario's (voor parent lookup).

    Returns:
        Volledig geresolveerd scenario met alle geërfde waarden ingevuld.
        Voor base scenarios (parent_naam=None) wordt het originele scenario teruggegeven.
    """
    if scenario.parent_naam is None:
        return scenario  # Base scenario, geen resolutie nodig

    # Haal parent chain op in volgorde root → child
    chain = get_parent_chain(scenario, scenario_lijst)
    if len(chain) == 1:
        return scenario  # Alleen het scenario zelf, geen parent gevonden

    # Reverse chain zodat we van root naar child mergen
    chain_scenarios = []
    for naam in reversed(chain):
        s = next((sc for sc in scenario_lijst if sc.naam == naam), None)
        if s is not None:
            chain_scenarios.append(s)

    # Start met root (base scenario) en merge elk child
    base = chain_scenarios[0]
    resolved_data = base.model_dump(mode="json")

    # Merge elk volgend scenario in de chain
    for child in chain_scenarios[1:]:
        child_overrides = child.overrides
        if not child_overrides:
            continue  # Geen overrides in dit child

        # Apply overrides
        for field_path, value in child_overrides.items():
            _set_nested_value(resolved_data, field_path, value)

    # Creëer nieuw scenario met gemerged data
    # Behoud metadata van originele scenario (naam, timestamps, etc.)
    resolved_data["naam"] = scenario.naam
    resolved_data["aangemaakt_op"] = scenario.aangemaakt_op.isoformat()
    resolved_data["laatst_gewijzigd_op"] = scenario.laatst_gewijzigd_op.isoformat()
    resolved_data["is_default"] = scenario.is_default

    # Verwijder parent_naam en overrides uit resolved scenario
    resolved_data.pop("parent_naam", None)
    resolved_data.pop("overrides", None)

    return Scenario.model_validate(resolved_data)


def get_override_chain(
    scenario: Scenario, field_path: str, scenario_lijst: list[Scenario]
) -> list[tuple[str, Any]]:
    """
    Trace de inheritance chain voor een specifiek veld.

    Geeft terug welke scenario's deze waarde beïnvloeden en wat hun waarde is.

    Args:
        scenario: Het scenario waarvoor de chain bepaald wordt.
        field_path: Dotted path naar veld, bijv. "rendement_pct" of "componenten.0.bedrag".
        scenario_lijst: Lijst van alle scenario's.

    Returns:
        Lijst van (scenario_naam, waarde) tuples van child naar root.
        Bijv. [("Kind", 5.0), ("Parent", 3.0), ("Base", 3.0)] betekent
        dat Kind override heeft naar 5.0, Parent en Base hebben 3.0.
    """
    chain_namen = get_parent_chain(scenario, scenario_lijst)
    chain: list[tuple[str, Any]] = []

    for naam in chain_namen:
        s = next((sc for sc in scenario_lijst if sc.naam == naam), None)
        if s is None:
            continue

        # Check of dit scenario een override heeft voor dit veld
        if s.overrides and field_path in s.overrides:
            chain.append((naam, s.overrides[field_path]))
        else:
            # Haal waarde op uit scenario data
            try:
                scenario_data = s.model_dump(mode="json")
                value = _get_nested_value(scenario_data, field_path)
                chain.append((naam, value))
            except (KeyError, IndexError):
                # Veld bestaat niet in dit scenario
                pass

    return chain


def _get_nested_value(data: dict[str, Any], path: str) -> Any:
    """
    Haal nested waarde op uit dictionary via dotted path.

    Bijv. "componenten.0.bedrag" → data["componenten"][0]["bedrag"]
    """
    parts = path.split(".")
    current = data

    for part in parts:
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            index = int(part)
            current = current[index]
        else:
            raise KeyError(f"Cannot navigate to '{part}' in path '{path}'")

    return current


def _set_nested_value(data: dict[str, Any], path: str, value: Any) -> None:
    """
    Zet nested waarde in dictionary via dotted path.

    Bijv. "componenten.0.bedrag" met value=1000 → data["componenten"][0]["bedrag"] = 1000
    """
    parts = path.split(".")
    current = data

    for i, part in enumerate(parts[:-1]):
        if isinstance(current, dict):
            if part not in current:
                # Maak nested dict/list aan indien nodig
                next_part = parts[i + 1]
                current[part] = [] if next_part.isdigit() else {}
            current = current[part]
        elif isinstance(current, list):
            index = int(part)
            current = current[index]
        else:
            raise KeyError(f"Cannot navigate to '{part}' in path '{path}'")

    # Zet finale waarde
    final_key = parts[-1]
    if isinstance(current, dict):
        current[final_key] = value
    elif isinstance(current, list):
        index = int(final_key)
        current[index] = value
    else:
        raise KeyError(f"Cannot set value at '{final_key}' in path '{path}'")


def clear_cache() -> None:
    """Clear de LRU cache van resolve_scenario (gebruik na scenario wijzigingen)."""
    resolve_scenario.cache_clear()  # type: ignore
