"""Tests voor autosave en atomische schrijfoperaties in sessie_persistentie."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _maak_mock_session_state(data: dict) -> MagicMock:
    """Geeft een MagicMock terug die .get() en 'in'-checks ondersteunt."""
    mock = MagicMock()
    mock.get = lambda key, default=None: data.get(key, default)
    mock.__contains__ = lambda self, key: key in data
    mock.__getitem__ = lambda self, key: data[key]
    mock.__setitem__ = lambda self, key, value: data.__setitem__(key, value)
    return mock


# ---------------------------------------------------------------------------
# autosla_sessie_op: hash-deduplicatie
# ---------------------------------------------------------------------------

class TestAutoslaDeduplicatie:
    """Autosave slaat niet opnieuw op als de inhoud niet is gewijzigd."""

    def test_geen_schrijven_bij_ongewijzigde_data(self, tmp_path: Path) -> None:
        persoon = Persoon(naam="Test", geboortedatum=date(1963, 1, 1), heeft_partner=False)
        session_data: dict = {
            "persoon1": persoon,
            "persoon2": None,
            "records_p1": [],
            "records_p2": [],
            "scenario_lijst": [],
        }

        sessie_pad = tmp_path / ".sessie.json"

        with (
            patch("pensioen.ui.sessie_persistentie.st") as mock_st,
            patch("pensioen.ui.sessie_persistentie.SESSIE_PAD", sessie_pad),
        ):
            mock_st.session_state = session_data

            from pensioen.ui.sessie_persistentie import autosla_sessie_op

            autosla_sessie_op()
            assert sessie_pad.exists()
            eerste_mtime = sessie_pad.stat().st_mtime

            # Tweede aanroep — zelfde data, hash al opgeslagen
            autosla_sessie_op()
            tweede_mtime = sessie_pad.stat().st_mtime

            assert eerste_mtime == tweede_mtime, "Bestand mag niet herschreven worden bij ongewijzigde data"

    def test_schrijft_bij_gewijzigde_data(self, tmp_path: Path) -> None:
        persoon = Persoon(naam="Test", geboortedatum=date(1963, 1, 1), heeft_partner=False)
        session_data: dict = {
            "persoon1": persoon,
            "persoon2": None,
            "records_p1": [],
            "records_p2": [],
            "scenario_lijst": [],
        }

        sessie_pad = tmp_path / ".sessie.json"

        with (
            patch("pensioen.ui.sessie_persistentie.st") as mock_st,
            patch("pensioen.ui.sessie_persistentie.SESSIE_PAD", sessie_pad),
        ):
            mock_st.session_state = session_data

            from pensioen.ui.sessie_persistentie import autosla_sessie_op

            autosla_sessie_op()
            assert sessie_pad.exists()

            # Wijzig data en sla opnieuw op
            persoon2 = Persoon(naam="Partner", geboortedatum=date(1965, 6, 1), heeft_partner=True)
            session_data["persoon2"] = persoon2
            # Verwijder hash zodat herberekening plaatsvindt
            session_data.pop("_sessie_hash", None)

            autosla_sessie_op()
            inhoud = json.loads(sessie_pad.read_text())
            assert inhoud.get("persoon2", {}).get("naam") == "Partner"


# ---------------------------------------------------------------------------
# sla_sessie_op: atomische schrijfoperatie
# ---------------------------------------------------------------------------

class TestAtomischeSchrijfOperatie:
    """sla_sessie_op schrijft atomisch via tijdelijk bestand."""

    def test_tmp_bestand_verwijderd_na_schrijven(self, tmp_path: Path) -> None:
        session_data: dict = {
            "persoon1": None,
            "persoon2": None,
            "records_p1": [],
            "records_p2": [],
            "scenario_lijst": [],
        }
        sessie_pad = tmp_path / ".sessie.json"
        tmp_pad = sessie_pad.with_suffix(".tmp.json")

        with (
            patch("pensioen.ui.sessie_persistentie.st") as mock_st,
            patch("pensioen.ui.sessie_persistentie.SESSIE_PAD", sessie_pad),
        ):
            mock_st.session_state = session_data
            from pensioen.ui.sessie_persistentie import sla_sessie_op

            sla_sessie_op()

            assert sessie_pad.exists()
            assert not tmp_pad.exists(), "Tijdelijk bestand moet na schrijven verwijderd zijn"

    def test_json_valide_na_schrijven(self, tmp_path: Path) -> None:
        scenario = Scenario(
            naam="Test Scenario",
            spaargeld_start=Decimal("100000"),
            jaarlijkse_inleg=Decimal("5000"),
            rendement_pct=Decimal("3.5"),
        )
        session_data: dict = {
            "persoon1": None,
            "persoon2": None,
            "records_p1": [],
            "records_p2": [],
            "scenario_lijst": [scenario],
        }
        sessie_pad = tmp_path / ".sessie.json"

        with (
            patch("pensioen.ui.sessie_persistentie.st") as mock_st,
            patch("pensioen.ui.sessie_persistentie.SESSIE_PAD", sessie_pad),
        ):
            mock_st.session_state = session_data
            from pensioen.ui.sessie_persistentie import sla_sessie_op

            sla_sessie_op()

            inhoud = json.loads(sessie_pad.read_text(encoding="utf-8"))
            assert len(inhoud["scenario_lijst"]) == 1
            assert inhoud["scenario_lijst"][0]["naam"] == "Test Scenario"


# ---------------------------------------------------------------------------
# laad_sessie: herstel van opgeslagen JSON
# ---------------------------------------------------------------------------

class TestLaadSessie:
    """laad_sessie herstelt Persoon- en Scenario-objecten correct."""

    def test_herstel_persoon_en_scenario(self, tmp_path: Path) -> None:
        persoon = Persoon(naam="Geladen", geboortedatum=date(1960, 3, 1), heeft_partner=False)
        scenario = Scenario(naam="Geladen Scenario", spaargeld_start=Decimal("50000"))
        data = {
            "persoon1": persoon.model_dump(mode="json"),
            "records_p1": [],
            "records_p2": [],
            "scenario_lijst": [scenario.model_dump(mode="json")],
        }
        sessie_pad = tmp_path / ".sessie.json"
        sessie_pad.write_text(json.dumps(data), encoding="utf-8")

        session_data: dict = {}

        with (
            patch("pensioen.ui.sessie_persistentie.st") as mock_st,
            patch("pensioen.ui.sessie_persistentie.SESSIE_PAD", sessie_pad),
        ):
            mock_st.session_state = session_data
            from pensioen.ui.sessie_persistentie import laad_sessie

            laad_sessie()

            assert "persoon1" in session_data
            assert session_data["persoon1"].naam == "Geladen"
            assert len(session_data["scenario_lijst"]) == 1
            assert session_data["scenario_lijst"][0].naam == "Geladen Scenario"

    def test_eenmalig_laden(self, tmp_path: Path) -> None:
        """laad_sessie mag slechts eenmalig per sessie uitvoeren."""
        sessie_pad = tmp_path / ".sessie.json"
        session_data: dict = {"_sessie_geladen": True}

        with (
            patch("pensioen.ui.sessie_persistentie.st") as mock_st,
            patch("pensioen.ui.sessie_persistentie.SESSIE_PAD", sessie_pad),
        ):
            mock_st.session_state = session_data
            from pensioen.ui.sessie_persistentie import laad_sessie

            laad_sessie()  # Zou niks mogen doen want _sessie_geladen=True
            assert "persoon1" not in session_data
