"""Testcase loader: laad en valideer genormaliseerde testcase JSONs.

Dit module biedt functies om testcase JSON files in te lezen,
te valideren via Pydantic, en beschikbaar te maken voor validatie.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from tests.models.testcase import TestCase


# Default directory voor genormaliseerde testcases
DEFAULT_TESTCASE_DIR = Path("tests/fixtures/belasting_testcases/normalized")


class TestCaseLoadError(Exception):
    """Error bij laden van testcase."""
    
    def __init__(self, filepath: Path, message: str, original_error: Exception | None = None):
        self.filepath = filepath
        self.message = message
        self.original_error = original_error
        super().__init__(f"Error loading {filepath.name}: {message}")


def laad_testcase(filepath: Path) -> TestCase:
    """Laad één testcase JSON en valideer met Pydantic.
    
    Args:
        filepath: Pad naar genormaliseerde JSON file
        
    Returns:
        Gevalideerde TestCase object
        
    Raises:
        TestCaseLoadError: Als JSON invalid is of validatie faalt
    """
    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise TestCaseLoadError(filepath, f"Invalid JSON: {e}", e)
    except FileNotFoundError as e:
        raise TestCaseLoadError(filepath, "File not found", e)
    except Exception as e:
        raise TestCaseLoadError(filepath, f"Unexpected error reading file: {e}", e)
    
    try:
        return TestCase(**data)
    except Exception as e:
        raise TestCaseLoadError(filepath, f"Validation error: {e}", e)


def laad_alle_testcases(
    directory: Path = DEFAULT_TESTCASE_DIR,
    pattern: str = "*_normalized.json",
) -> dict[str, TestCase]:
    """Laad alle testcases uit directory.
    
    Args:
        directory: Directory met genormaliseerde JSONs
        pattern: Glob pattern voor files (default: *_normalized.json)
        
    Returns:
        Dict met testcase_id → TestCase mapping
        
    Raises:
        TestCaseLoadError: Als één van de testcases niet geladen kan worden
    """
    testcases = {}
    errors = []
    
    # Vind alle matching files
    files = sorted(directory.glob(pattern))
    
    if not files:
        raise ValueError(f"Geen testcase files gevonden in {directory} met pattern '{pattern}'")
    
    for filepath in files:
        try:
            testcase = laad_testcase(filepath)
            testcases[testcase.testcase_id] = testcase
        except TestCaseLoadError as e:
            errors.append(e)
    
    # Als er errors waren, raise eerste error
    if errors:
        raise errors[0]
    
    return testcases


def iter_testcases(
    directory: Path = DEFAULT_TESTCASE_DIR,
    pattern: str = "*_normalized.json",
) -> Iterator[tuple[Path, TestCase]]:
    """Itereer over testcases (lazy loading).
    
    Args:
        directory: Directory met genormaliseerde JSONs
        pattern: Glob pattern voor files
        
    Yields:
        (filepath, TestCase) tuples
    """
    files = sorted(directory.glob(pattern))
    
    for filepath in files:
        try:
            testcase = laad_testcase(filepath)
            yield filepath, testcase
        except TestCaseLoadError as e:
            # Log error maar ga door
            print(f"⚠️  Skipping {filepath.name}: {e.message}")
            continue


def vind_testcase_by_id(
    testcase_id: str,
    directory: Path = DEFAULT_TESTCASE_DIR,
) -> TestCase:
    """Zoek testcase op ID.
    
    Args:
        testcase_id: ID van gewenste testcase
        directory: Directory om te zoeken
        
    Returns:
        TestCase object
        
    Raises:
        ValueError: Als testcase niet gevonden
        TestCaseLoadError: Als testcase niet geladen kan worden
    """
    # Probeer direct bestand
    filepath = directory / f"{testcase_id}_normalized.json"
    if filepath.exists():
        return laad_testcase(filepath)
    
    # Zoek in alle testcases
    for filepath, testcase in iter_testcases(directory):
        if testcase.testcase_id == testcase_id:
            return testcase
    
    raise ValueError(f"Testcase '{testcase_id}' niet gevonden in {directory}")


def filter_testcases(
    testcases: dict[str, TestCase],
    jaar: int | None = None,
    huishoud_type: str | None = None,
    min_inkomen: int | None = None,
    max_inkomen: int | None = None,
    heeft_eigen_huis: bool | None = None,
) -> dict[str, TestCase]:
    """Filter testcases op criteria.
    
    Args:
        testcases: Dict met alle testcases
        jaar: Filter op jaar (optioneel)
        huishoud_type: Filter op huishoud type (optioneel)
        min_inkomen: Minimum totaal inkomen (optioneel)
        max_inkomen: Maximum totaal inkomen (optioneel)
        heeft_eigen_huis: Filter op eigen huis (optioneel)
        
    Returns:
        Gefilterde dict met testcases
    """
    result = {}
    
    for tc_id, tc in testcases.items():
        # Filter op jaar
        if jaar is not None and tc.jaar != jaar:
            continue
        
        # Filter op huishoud type
        if huishoud_type is not None and tc.huishouden.type.value != huishoud_type.upper():
            continue
        
        # Filter op inkomen
        totaal_inkomen = float(tc.totaal_bruto_inkomen_huishouden)
        if min_inkomen is not None and totaal_inkomen < min_inkomen:
            continue
        if max_inkomen is not None and totaal_inkomen > max_inkomen:
            continue
        
        # Filter op eigen huis
        if heeft_eigen_huis is not None and tc.heeft_eigen_huis != heeft_eigen_huis:
            continue
        
        result[tc_id] = tc
    
    return result
