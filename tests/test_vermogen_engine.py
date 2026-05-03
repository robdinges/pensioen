"""Tests voor de vermogensontwikkelingsberekening."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pensioen.calculations.vermogen_engine import (
    bereken_rente_maand,
    bereken_vermogensontwikkeling,
    maandrendement,
)


class TestMaandrendement:
    def test_nul_rendement(self) -> None:
        assert maandrendement(Decimal("0")) == Decimal("0")

    def test_positief_rendement(self) -> None:
        """3% jaarrendement geeft klein maandrendement."""
        mr = maandrendement(Decimal("3"))
        # (1.03)^(1/12) - 1 ≈ 0.002466
        assert float(mr) == pytest.approx(0.002466, rel=1e-3)

    def test_samengesteld_rendement_klopt(self) -> None:
        """12 × maandrendement samengesteld ≈ jaarrendement."""
        jaarrendement = Decimal("5")
        mr = maandrendement(jaarrendement)
        samengesteld = (Decimal("1") + mr) ** 12 - Decimal("1")
        assert float(samengesteld) == pytest.approx(0.05, rel=1e-4)


class TestBerekenRenteMaand:
    def test_geen_saldo_geen_rente(self) -> None:
        assert bereken_rente_maand(Decimal("0"), Decimal("3")) == Decimal("0")

    def test_negatief_saldo_geen_rente(self) -> None:
        assert bereken_rente_maand(Decimal("-1000"), Decimal("3")) == Decimal("0")

    def test_rente_positief_bij_positief_saldo(self) -> None:
        rente = bereken_rente_maand(Decimal("10000"), Decimal("3"))
        assert rente > Decimal("0")


class TestBerekenVermogensontwikkeling:
    def test_saldo_groeit_zonder_mutaties(self) -> None:
        """Zonder mutaties groeit het saldo via rendement."""
        resultaten = bereken_vermogensontwikkeling(
            beginsaldo=Decimal("100000"),
            jaarrendement_pct=Decimal("3"),
            mutaties=[],
            jaar_van=2026,
            jaar_tot=2027,
        )
        # Na 2 jaar: saldo > beginsaldo
        eindwaarde = resultaten[-1][1]
        assert eindwaarde > Decimal("100000")

    def test_aantal_resultaten_klopt(self) -> None:
        """2 jaar × 12 maanden = 24 resultaten."""
        resultaten = bereken_vermogensontwikkeling(
            beginsaldo=Decimal("50000"),
            jaarrendement_pct=Decimal("3"),
            mutaties=[],
            jaar_van=2026,
            jaar_tot=2027,
        )
        assert len(resultaten) == 24

    def test_stortingen_verhogen_saldo(self) -> None:
        """Een storting in januari verhoogt het saldo."""
        resultaten_geen_storting = bereken_vermogensontwikkeling(
            Decimal("100000"), Decimal("3"), [], 2026, 2026
        )
        resultaten_met_storting = bereken_vermogensontwikkeling(
            Decimal("100000"),
            Decimal("3"),
            [(date(2026, 1, 1), Decimal("10000"))],
            2026,
            2026,
        )
        assert resultaten_met_storting[-1][1] > resultaten_geen_storting[-1][1]

    def test_hoog_vermogen_box3_indicatie(self) -> None:
        """Saldo van €300.000 is boven box 3 vrijstelling van €59.357 (single)."""
        resultaten = bereken_vermogensontwikkeling(
            Decimal("300000"), Decimal("3"), [], 2026, 2026
        )
        eindsaldo = resultaten[-1][1]
        from pensioen.tax.belasting_loader import laad_tarieven

        config, _ = laad_tarieven(2026)
        assert eindsaldo > config.box3.vrijstelling_per_persoon

    def test_nul_rendement_saldo_stabiel(self) -> None:
        """Bij 0% rendement en geen mutaties blijft het saldo gelijk."""
        resultaten = bereken_vermogensontwikkeling(
            Decimal("50000"), Decimal("0"), [], 2026, 2026
        )
        for _, saldo in resultaten:
            assert float(saldo) == pytest.approx(50000, rel=1e-4)
