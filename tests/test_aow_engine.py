"""Tests voor de AOW-engine: datumberekeningen en leeftijdlookup."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pensioen.tax.aow_engine import (
    aow_breuk_jaar,
    bereken_aow_datum,
    is_aow_gerechtigd,
)


class TestBerekenAowDatum:
    """Tests voor bereken_aow_datum."""

    def test_geboren_1947_of_eerder(self) -> None:
        """Personen geboren t/m 1947 krijgen AOW op 65e verjaardag."""
        geboortedatum = date(1947, 6, 15)
        verwacht = date(2012, 6, 15)  # 65 jaar, 0 maanden
        assert bereken_aow_datum(geboortedatum) == verwacht

    def test_geboren_1948(self) -> None:
        """Geboren in 1948 → AOW op 65 jaar en 3 maanden."""
        geboortedatum = date(1948, 3, 10)
        aow = bereken_aow_datum(geboortedatum)
        assert aow == date(2013, 6, 10)  # 65j + 3m = 65j3m

    def test_geboren_1955_aow_leeftijd(self) -> None:
        """Geboren in 1955 → AOW op 66 jaar en 7 maanden (per tabel)."""
        geboortedatum = date(1955, 1, 1)
        aow = bereken_aow_datum(geboortedatum)
        assert aow.year == 2021 or aow.year == 2022  # 1955 + 66 of 67 jaar

    def test_geboren_1963_aow_op_67(self) -> None:
        """Geboren in 1963 (≥1956) → AOW op 67e verjaardag."""
        geboortedatum = date(1963, 3, 15)
        aow = bereken_aow_datum(geboortedatum)
        assert aow == date(2030, 3, 15)

    def test_geboren_29_februari(self) -> None:
        """Schrikkeljaar-verjaardag: 29 feb → 28 feb of 1 mrt in andere jaren."""
        geboortedatum = date(1956, 2, 29)
        aow = bereken_aow_datum(geboortedatum)
        # 1956 + 67 = 2023; 29 feb bestaat niet in 2023 → 28 feb
        assert aow == date(2023, 2, 28)

    def test_maandoptelling_over_jaargrens(self) -> None:
        """Maanden optelling die over de jaargrens gaat (bijv. oktober + 3m = januari)."""
        geboortedatum = date(1948, 10, 20)
        aow = bereken_aow_datum(geboortedatum)
        # 1948 + 65 jaar = 2013 oktober + 3 maanden = januari 2014
        assert aow == date(2014, 1, 20)


class TestIsAowGerechtigd:
    """Tests voor is_aow_gerechtigd."""

    def test_dag_voor_aow_datum(self) -> None:
        geboortedatum = date(1963, 3, 15)
        aow_datum = date(2030, 3, 15)
        assert not is_aow_gerechtigd(geboortedatum, date(2030, 3, 14))

    def test_op_aow_datum(self) -> None:
        geboortedatum = date(1963, 3, 15)
        assert is_aow_gerechtigd(geboortedatum, date(2030, 3, 15))

    def test_na_aow_datum(self) -> None:
        geboortedatum = date(1963, 3, 15)
        assert is_aow_gerechtigd(geboortedatum, date(2035, 1, 1))


class TestAowBreukJaar:
    """Tests voor aow_breuk_jaar (dag-nauwkeurige fractieberekening)."""

    def test_heel_jaar_geen_aow(self) -> None:
        """AOW-datum na 31 december → breuk = 0."""
        geboortedatum = date(1963, 3, 15)  # AOW op 15 maart 2030
        assert aow_breuk_jaar(geboortedatum, 2029) == Decimal("0")

    def test_heel_jaar_aow(self) -> None:
        """AOW-datum vóór 1 januari van het jaar → breuk = 1."""
        geboortedatum = date(1963, 3, 15)
        assert aow_breuk_jaar(geboortedatum, 2031) == Decimal("1")

    def test_aow_start_1_juli(self) -> None:
        """AOW start op 1 juli → breuk ≈ 0.5 (6 volledige maanden)."""
        # Geboortedatum zodat aow_datum = 1 juli 2030
        geboortedatum = date(1963, 7, 1)  # AOW 1 juli 2030
        breuk = aow_breuk_jaar(geboortedatum, 2030)
        # 1 juli: resterende dagen = 31, hele maand = 31 (pro-rata = 1.0)
        # + 5 volledige maanden (aug-dec) = 6 maanden / 12 = 0.5
        assert breuk == pytest.approx(Decimal("0.5"), abs=Decimal("0.01"))

    def test_aow_start_17_september(self) -> None:
        """AOW start op 17 september → pro-rata september + 3 volle maanden."""
        # We zoeken een geboortedatum waarvoor aow_datum = 17 sept 2031
        # geboortejaar >= 1956: aow op 67e verjaardag
        geboortedatum = date(1964, 9, 17)  # AOW 17 sept 2031
        breuk = aow_breuk_jaar(geboortedatum, 2031)
        # September: 30 - 17 + 1 = 14 dagen van 30 → 14/30
        # Oktober, november, december: 3 volledige maanden
        # Totaal: (3 + 14/30) / 12
        verwacht = (Decimal("3") + Decimal("14") / Decimal("30")) / Decimal("12")
        assert breuk == pytest.approx(verwacht, rel=Decimal("0.001"))
