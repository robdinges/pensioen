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

    def test_aparte_rendementen_sparen_beleggen(self) -> None:
        """Sparen 2%, Beleggen 6%, 50/50 split → gewogen rendement 4%."""
        saldo = Decimal("10000")
        rente = bereken_rente_maand(
            saldo=saldo,
            jaarrendement_pct=Decimal("4"),  # fallback (niet gebruikt)
            jaarrendement_sparen_pct=Decimal("2"),
            jaarrendement_beleggen_pct=Decimal("6"),
            spaargeld_fractie=Decimal("0.5"),
        )
        # Verwacht: 5000 × 2% + 5000 × 6% = 100 + 300 = 400 per jaar
        # Per maand: ≈ 32.74
        assert float(rente) == pytest.approx(32.74, abs=1.0)

    def test_spaargeld_fractie_scenarios(self) -> None:
        """Verschillende fracties geven verschillende rendementen."""
        saldo = Decimal("10000")
        
        # 100% sparen (1% rendement)
        rente_sparen = bereken_rente_maand(
            saldo, Decimal("0"), Decimal("1"), Decimal("7"), Decimal("1.0")
        )
        
        # 100% beleggen (7% rendement)
        rente_beleggen = bereken_rente_maand(
            saldo, Decimal("0"), Decimal("1"), Decimal("7"), Decimal("0.0")
        )
        
        # 50/50
        rente_mix = bereken_rente_maand(
            saldo, Decimal("0"), Decimal("1"), Decimal("7"), Decimal("0.5")
        )
        
        assert rente_sparen < rente_mix < rente_beleggen
