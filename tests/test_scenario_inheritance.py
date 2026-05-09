"""Tests voor scenario-inheritance (parent-child overerving)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from pensioen.models.component import BedragType, CategorieComponent, FinancieelComponent, Frequentie
from pensioen.models.scenario import Scenario


def _maak_component(omschrijving: str, bedrag: Decimal) -> FinancieelComponent:
    return FinancieelComponent(
        omschrijving=omschrijving,
        categorie=CategorieComponent.ARBEIDSINKOMEN,
        persoon="P1",
        bedrag_type=BedragType.BRUTO,
        bedrag=bedrag,
        frequentie=Frequentie.MAANDELIJKS,
    )


# ---------------------------------------------------------------------------
# Scenario zonder parent
# ---------------------------------------------------------------------------

class TestZonderParent:
    def test_effectief_is_zichzelf(self) -> None:
        s = Scenario(naam="Basis", spaargeld_start=Decimal("100000"))
        assert s.effectief_scenario([s]) is s

    def test_onbekende_parent_geeft_zichzelf(self) -> None:
        s = Scenario(naam="Kind", parent_naam="Bestaat Niet")
        effectief = s.effectief_scenario([s])
        assert effectief is s


# ---------------------------------------------------------------------------
# Enkelvoudige overerving
# ---------------------------------------------------------------------------

class TestEnkelvoudigeOvererving:
    @pytest.fixture()
    def parent(self) -> Scenario:
        return Scenario(
            naam="Basis",
            spaargeld_start=Decimal("200000"),
            rendement_pct=Decimal("4"),
            componenten=[_maak_component("Salaris", Decimal("3000"))],
        )

    def test_kind_erft_spaargeld_als_niet_overschreven(self, parent: Scenario) -> None:
        """Kind zonder overschreven_velden erft alles van de parent."""
        kind = Scenario(naam="Kind", parent_naam="Basis")
        effectief = kind.effectief_scenario([parent, kind])
        assert effectief.spaargeld_start == Decimal("200000")
        assert effectief.rendement_pct == Decimal("4")

    def test_kind_erft_componenten(self, parent: Scenario) -> None:
        kind = Scenario(naam="Kind", parent_naam="Basis")
        effectief = kind.effectief_scenario([parent, kind])
        assert len(effectief.componenten) == 1
        assert effectief.componenten[0].omschrijving == "Salaris"

    def test_kind_overschrijft_spaargeld(self, parent: Scenario) -> None:
        kind = Scenario(
            naam="Kind",
            parent_naam="Basis",
            spaargeld_start=Decimal("50000"),
            overschreven_velden=["spaargeld_start"],
        )
        effectief = kind.effectief_scenario([parent, kind])
        assert effectief.spaargeld_start == Decimal("50000")
        # Niet-overschreven veld is geërfd
        assert effectief.rendement_pct == Decimal("4")

    def test_kind_overschrijft_componenten(self, parent: Scenario) -> None:
        extra_comp = _maak_component("Freelance", Decimal("1500"))
        kind = Scenario(
            naam="Kind",
            parent_naam="Basis",
            componenten=[extra_comp],
            overschreven_velden=["componenten"],
        )
        effectief = kind.effectief_scenario([parent, kind])
        assert len(effectief.componenten) == 1
        assert effectief.componenten[0].omschrijving == "Freelance"

    def test_kind_naam_blijft_bewaard(self, parent: Scenario) -> None:
        kind = Scenario(naam="Afgeleid", parent_naam="Basis")
        effectief = kind.effectief_scenario([parent, kind])
        assert effectief.naam == "Afgeleid"


# ---------------------------------------------------------------------------
# Ketens (grootouder → ouder → kind)
# ---------------------------------------------------------------------------

class TestKetting:
    def test_ketting_twee_niveaus(self) -> None:
        grootouder = Scenario(
            naam="Grootouder",
            spaargeld_start=Decimal("300000"),
            rendement_pct=Decimal("5"),
        )
        ouder = Scenario(
            naam="Ouder",
            parent_naam="Grootouder",
            rendement_pct=Decimal("3"),
            overschreven_velden=["rendement_pct"],
        )
        kind = Scenario(naam="Kind", parent_naam="Ouder")
        lijst = [grootouder, ouder, kind]

        effectief = kind.effectief_scenario(lijst)
        # Rendement: ouder heeft overschreven (3%), kind erft dat
        assert effectief.rendement_pct == Decimal("3")
        # Spaargeld: kind erft van ouder, ouder erft van grootouder
        assert effectief.spaargeld_start == Decimal("300000")


# ---------------------------------------------------------------------------
# JSON round-trip: overschreven_velden blijven bewaard
# ---------------------------------------------------------------------------

class TestJsonRoundTrip:
    def test_overschreven_velden_persisteren(self) -> None:
        scenario = Scenario(
            naam="Test",
            parent_naam="Basis",
            overschreven_velden=["spaargeld_start", "rendement_pct"],
            spaargeld_start=Decimal("75000"),
            rendement_pct=Decimal("2.5"),
        )
        data = scenario.model_dump(mode="json")
        herladen = Scenario.model_validate(data)
        assert herladen.overschreven_velden == ["spaargeld_start", "rendement_pct"]
        assert herladen.parent_naam == "Basis"
        assert herladen.spaargeld_start == Decimal("75000")
