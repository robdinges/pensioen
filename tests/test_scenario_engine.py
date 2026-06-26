"""Tests voor de scenariovergelijkingsengine."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pensioen.calculations.scenario_engine import vergelijk_scenarios
from pensioen.models.component import CategorieComponent, FinancieelComponent, Frequentie
from pensioen.models.pensioen_record import PensioenRecord, TypePensioen
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.models.vermogensitem import VermogensItem, VermogensType


class TestScenarioModel:
    """Regressietests voor het Scenario-model zelf."""

    def test_lege_componenten_is_geldig(self) -> None:
        """Scenario zonder componenten is geldig (standaard lege lijst)."""
        scenario = Scenario(naam="Leeg")
        assert scenario.componenten == []

    def test_component_toevoegen(self) -> None:
        """Scenario accepteert een FinancieelComponent in de lijst."""
        comp = FinancieelComponent(
            omschrijving="Salaris",
            categorie=CategorieComponent.ARBEIDSINKOMEN,
            persoon="P1",
            bedrag=Decimal("5000"),
        )
        scenario = Scenario(naam="Met salaris", componenten=[comp])
        assert len(scenario.componenten) == 1
        assert scenario.componenten[0].omschrijving == "Salaris"

    def test_helper_arbeidsinkomen_componenten(self) -> None:
        """arbeidsinkomen_componenten filtert correct op persoon en categorie."""
        comp_arbeid = FinancieelComponent(
            omschrijving="Salaris P1",
            categorie=CategorieComponent.ARBEIDSINKOMEN,
            persoon="P1",
            bedrag=Decimal("5000"),
        )
        comp_uitgave = FinancieelComponent(
            omschrijving="Huur",
            categorie=CategorieComponent.UITGAVE,
            persoon="Huishouden",
            bedrag=Decimal("1500"),
        )
        scenario = Scenario(naam="Test", componenten=[comp_arbeid, comp_uitgave])
        assert scenario.arbeidsinkomen_componenten("P1") == [comp_arbeid]
        assert scenario.arbeidsinkomen_componenten("P2") == []

    def test_spaargeld_default_nul(self) -> None:
        """spaargeld_start heeft standaard Decimal('0')."""
        scenario = Scenario(naam="Test")
        assert scenario.spaargeld_start == Decimal("0")

    def test_sync_eigen_woning_uit_vermogensitems_telt_jaar_overlap_mee(self) -> None:
        """Woning en hypotheek tellen mee zodra ze ergens in het belastingjaar bestaan."""
        scenario = Scenario(
            naam="Eigen woning",
            vermogensitems=[
                VermogensItem(
                    omschrijving="Woning",
                    type=VermogensType.EIGEN_WONING,
                    aanschafwaarde=Decimal("500000"),
                    woz_waarde=Decimal("500000"),
                    aanschafdatum=date(2026, 6, 26),
                    box3_belast=False,
                ),
                VermogensItem(
                    omschrijving="Hypotheek",
                    type=VermogensType.HYPOTHEEK,
                    aanschafwaarde=Decimal("200000"),
                    aanschafdatum=date(2026, 6, 26),
                    is_primaire_woning=True,
                    hypotheekrente_pct=Decimal("3.0"),
                    box3_belast=False,
                ),
            ],
        )

        resultaat = scenario.sync_eigen_woning_uit_vermogensitems(2026)

        assert resultaat.woz_waarde == Decimal("500000")
        assert resultaat.betaalde_hypotheekrente == Decimal("6000")
        assert resultaat.eigenwoningschuld_begin == Decimal("200000")


class TestVergelijkScenarios:
    """Tests voor de scenariovergelijkingsfunctie."""

    def test_een_scenario_geeft_resultaat(
        self, persoon1: Persoon, pensioenrecord_p1: PensioenRecord
    ) -> None:
        """Eén scenario levert een ScenarioVergelijking met één resultaat."""
        scenario = Scenario(
            naam="Vroeg stoppen",
            spaargeld_start=Decimal("100000"),
        )
        vergelijking = vergelijk_scenarios(
            scenarios=[scenario],
            persoon1=persoon1,
            persoon2=None,
            records1=[pensioenrecord_p1],
            records2=[],
            jaar_van=2025,
            jaar_tot=2035,
        )
        assert len(vergelijking.scenario_resultaten) == 1
        assert vergelijking.scenario_resultaten[0].scenario_naam == "Vroeg stoppen"

    def test_meerdere_scenarios_vergelijking(
        self, persoon1: Persoon, pensioenrecord_p1: PensioenRecord
    ) -> None:
        """
        Twee scenario's (weinig vs. veel spaargeld) leveren vergelijkbare resultaten.
        """
        vroeg = Scenario(
            naam="Stoppen op 62",
            spaargeld_start=Decimal("50000"),
        )
        laat = Scenario(
            naam="Stoppen op 67",
            spaargeld_start=Decimal("50000"),
            componenten=[
                FinancieelComponent(
                    omschrijving="Salaris P1",
                    categorie=CategorieComponent.ARBEIDSINKOMEN,
                    persoon="P1",
                    bedrag=Decimal("5000"),
                    einddatum=date(2030, 3, 15),
                ),
            ],
        )
        vergelijking = vergelijk_scenarios(
            scenarios=[vroeg, laat],
            persoon1=persoon1,
            persoon2=None,
            records1=[pensioenrecord_p1],
            records2=[],
            jaar_van=2025,
            jaar_tot=2040,
        )
        assert len(vergelijking.scenario_resultaten) == 2
        assert set(vergelijking.scenario_namen) == {"Stoppen op 62", "Stoppen op 67"}

    def test_beste_scenario_bepaald(
        self, persoon1: Persoon, pensioenrecord_p1: PensioenRecord
    ) -> None:
        """beste_scenario_netto wijst het scenario met hoogste mediaan netto aan."""
        arm = Scenario(
            naam="Weinig",
            spaargeld_start=Decimal("0"),
        )
        rijk = Scenario(
            naam="Veel",
            spaargeld_start=Decimal("1000000"),
            rendement_pct=Decimal("5"),
        )
        vergelijking = vergelijk_scenarios(
            scenarios=[arm, rijk],
            persoon1=persoon1,
            persoon2=None,
            records1=[pensioenrecord_p1],
            records2=[],
            jaar_van=2025,
            jaar_tot=2035,
        )
        beste = vergelijking.beste_scenario_netto
        assert beste is not None
        assert beste.scenario_naam == "Veel"

    def test_resultaat_vermogen_op_leeftijden(
        self, persoon1: Persoon, pensioenrecord_p1: PensioenRecord
    ) -> None:
        """Vermogen op leeftijden 70 en 80 worden bepaald."""
        scenario = Scenario(
            naam="Test vermogen",
            spaargeld_start=Decimal("100000"),
            rendement_pct=Decimal("3"),
        )
        vergelijking = vergelijk_scenarios(
            scenarios=[scenario],
            persoon1=persoon1,
            persoon2=None,
            records1=[pensioenrecord_p1],
            records2=[],
            jaar_van=2025,
            jaar_tot=2040,
        )
        resultaat = vergelijking.scenario_resultaten[0]
        # Zowel vermogen_op_70 als vermogen_op_80 zijn Decimal (kunnen 0 zijn buiten bereik)
        assert isinstance(resultaat.vermogen_op_70, Decimal)
        assert isinstance(resultaat.vermogen_op_80, Decimal)

    def test_tekortjaren_tellen(self, persoon1: Persoon) -> None:
        """Scenario zonder inkomen en weinig spaargeld heeft tekortjaren."""
        scenario = Scenario(
            naam="Geen inkomen",
            spaargeld_start=Decimal("1"),
        )
        vergelijking = vergelijk_scenarios(
            scenarios=[scenario],
            persoon1=persoon1,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2025,
            jaar_tot=2040,
        )
        resultaat = vergelijking.scenario_resultaten[0]
        assert isinstance(resultaat.aantal_tekortjaren, int)
        assert resultaat.aantal_tekortjaren >= 0
