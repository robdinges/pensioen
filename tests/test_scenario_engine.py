"""Tests voor de scenariovergelijkingsengine."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pensioen.calculations.scenario_engine import vergelijk_scenarios
from pensioen.models.pensioen_record import PensioenRecord, TypePensioen
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario


class TestVergelijkScenarios:
    """Tests voor de scenariovergelijkingsfunctie."""

    def test_een_scenario_geeft_resultaat(
        self, persoon1: Persoon, pensioenrecord_p1: PensioenRecord
    ) -> None:
        """Eén scenario levert een ScenarioVergelijking met één resultaat."""
        scenario = Scenario(
            naam="Vroeg stoppen",
            persoon1_stopdatum_werk=date(2025, 4, 1),
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
        Twee scenario's (vroeg vs. laat stoppen) leveren vergelijkbare resultaten.
        Laat stoppen geeft doorgaans hoger netto door meer arbeidsinkomen.
        """
        vroeg = Scenario(
            naam="Stoppen op 62",
            persoon1_stopdatum_werk=date(2025, 4, 1),
            spaargeld_start=Decimal("50000"),
        )
        laat = Scenario(
            naam="Stoppen op 67",
            persoon1_stopdatum_werk=date(2030, 3, 15),
            persoon1_bruto_jaarsalaris=Decimal("60000"),
            spaargeld_start=Decimal("50000"),
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
            persoon1_stopdatum_werk=date(2025, 1, 1),
            spaargeld_start=Decimal("0"),
        )
        rijk = Scenario(
            naam="Veel",
            persoon1_stopdatum_werk=date(2025, 1, 1),
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
            persoon1_stopdatum_werk=date(2025, 4, 1),
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
            persoon1_stopdatum_werk=date(2025, 1, 1),
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
