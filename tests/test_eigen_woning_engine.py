"""Unit tests voor eigen_woning_engine.

Testscenario's zijn gebaseerd op de Belastingdienst aangiftesimulator 2025.
Referentiecase: tc_2025_004 (echtpaar, WOZ €500.000, rente €6.000).
"""

from __future__ import annotations

import pytest
from decimal import Decimal

from pensioen.tax.belasting_loader import laad_tarieven
from pensioen.tax.eigen_woning_engine import (
    EigenWoningInvoer,
    bereken_eigen_woning,
)


@pytest.fixture
def config_2025():
    config, _ = laad_tarieven(2025)
    return config


class TestEigenwoningforfait:
    """Tests voor forfait-berekening op basis van WOZ-waarde."""

    def test_forfait_woz_500k(self, config_2025):
        """WOZ €500.000 volledig: forfait = 0,35% = €1.750."""
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("500000"),
            betaalde_hypotheekrente=Decimal("0"),
        )
        resultaat = bereken_eigen_woning(invoer, config_2025)
        assert resultaat.eigenwoningforfait == Decimal("1750.00")

    def test_forfait_woz_onder_75k(self, config_2025):
        """WOZ ≤ €75.000: forfait = €0."""
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("75000"),
            betaalde_hypotheekrente=Decimal("0"),
        )
        resultaat = bereken_eigen_woning(invoer, config_2025)
        assert resultaat.eigenwoningforfait == Decimal("0.00")

    def test_forfait_woz_hoog_boven_1200k(self, config_2025):
        """WOZ €1.500.000: basis 0,35% × €1.200.000 + 2,35% × €300.000 = €4.200 + €7.050 = €11.250."""
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("1500000"),
            betaalde_hypotheekrente=Decimal("0"),
        )
        resultaat = bereken_eigen_woning(invoer, config_2025)
        verwacht = Decimal("4200.00") + Decimal("7050.00")
        assert resultaat.eigenwoningforfait == verwacht


class TestSaldoEigenWoning:
    """Tests voor saldo-berekening (forfait minus aftrek)."""

    def test_saldo_negatief_aftrekpost(self, config_2025):
        """Rente > forfait → negatief saldo = aftrekpost (per persoon, 50/50 split).

        Simulatorcase 004: WOZ €500.000 total, per persoon woz=250.000.
        Per persoon: forfait = 250.000 × 0,35% = €875, rente = €3.000, saldo -€2.125.
        """
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("250000"),  # per persoon (helft van €500.000)
            betaalde_hypotheekrente=Decimal("3000"),  # per persoon
        )
        resultaat = bereken_eigen_woning(invoer, config_2025)
        assert resultaat.eigenwoningforfait == Decimal("875.00")
        assert resultaat.aftrekbare_hypotheekrente == Decimal("3000.00")
        assert resultaat.saldo_eigen_woning == Decimal("-2125.00")
        assert resultaat.box1_mutatie == Decimal("-2125.00")

    def test_saldo_positief_bijtelling(self, config_2025):
        """Forfait > 0 en geen rente → positief saldo; Wet Hillen vermindert."""
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("200000"),
            betaalde_hypotheekrente=Decimal("0"),
        )
        resultaat = bereken_eigen_woning(invoer, config_2025)
        assert resultaat.saldo_eigen_woning > Decimal("0")
        assert resultaat.hillen_correctie > Decimal("0")
        # box1_mutatie moet kleiner zijn dan saldo door Wet Hillen
        assert resultaat.box1_mutatie < resultaat.saldo_eigen_woning


class TestTariefsaanpassing:
    """Tests voor tariefsaanpassing aftrekposten bij hoog inkomen."""

    def test_tariefsaanpassing_hoog_inkomen(self, config_2025):
        """Inkomen in schijf 3 (€100.000): tariefsaanpassing = 12,02% × aftrek in schijf 3.

        Referentie: simulator tc_2025_004 persoon 1.
        Per persoon: woz=250.000, forfait=875, rente=3.000, saldo=-2.125.
        bruto_inkomen=100.000, schijf3-grens=76.817.
        aftrek_in_schijf3 = min(2125, 100000 - 76817) = min(2125, 23183) = 2125
        aanpassing = 2125 × 0.1202 = 255.43
        """
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("250000"),  # per persoon
            betaalde_hypotheekrente=Decimal("3000"),
            bruto_inkomen_box1=Decimal("100000"),
        )
        resultaat = bereken_eigen_woning(invoer, config_2025)
        # 2125 × 0.1202 = 255.425 → afgerond ROUND_HALF_UP = 255.43
        assert resultaat.tariefsaanpassing == Decimal("255.43")

    def test_tariefsaanpassing_laag_inkomen(self, config_2025):
        """Inkomen beneden schijf 3: geen tariefsaanpassing.

        Referentie: simulator tc_2025_004 persoon 2 (box1 grondslag €37.875 < schijf3-grens).
        """
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("250000"),  # per persoon
            betaalde_hypotheekrente=Decimal("3000"),
            bruto_inkomen_box1=Decimal("37875"),
        )
        resultaat = bereken_eigen_woning(invoer, config_2025)
        assert resultaat.tariefsaanpassing == Decimal("0")

    def test_geen_tariefsaanpassing_positief_saldo(self, config_2025):
        """Positief saldo (bijtelling): geen tariefsaanpassing."""
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("100000"),
            betaalde_hypotheekrente=Decimal("0"),
            bruto_inkomen_box1=Decimal("150000"),
        )
        resultaat = bereken_eigen_woning(invoer, config_2025)
        assert resultaat.tariefsaanpassing == Decimal("0")


class TestBox3Uitsluiting:
    """Tests voor correcte uitsluiting van eigen woning uit box 3."""

    def test_woning_niet_in_box3(self, config_2025):
        """Eigen woning en schuld zijn altijd €0 in box 3."""
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("500000"),
            betaalde_hypotheekrente=Decimal("3000"),
            eigenwoningschuld_begin=Decimal("150000"),
            eigenwoningschuld_eind=Decimal("148000"),
        )
        resultaat = bereken_eigen_woning(invoer, config_2025)
        assert resultaat.box3_bezittingen == Decimal("0")
        assert resultaat.box3_schulden == Decimal("0")


class TestWetHillen:
    """Tests voor Wet Hillen afbouw 2025 (80%)."""

    def test_hillen_80_pct_2025(self, config_2025):
        """Wet Hillen 2025: 80% vermindering van positief saldo."""
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("200000"),
            betaalde_hypotheekrente=Decimal("0"),
        )
        resultaat = bereken_eigen_woning(invoer, config_2025)
        if resultaat.saldo_eigen_woning > Decimal("0"):
            verwacht_hillen = (resultaat.saldo_eigen_woning * Decimal("0.80")).quantize(
                Decimal("0.01")
            )
            assert resultaat.hillen_correctie == verwacht_hillen

    def test_hillen_niet_van_toepassing_bij_negatief_saldo(self, config_2025):
        """Wet Hillen is alleen voor positief saldo."""
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("500000"),
            betaalde_hypotheekrente=Decimal("10000"),
        )
        resultaat = bereken_eigen_woning(invoer, config_2025)
        assert resultaat.saldo_eigen_woning < Decimal("0")
        assert resultaat.hillen_correctie == Decimal("0")


class TestGeenConfig:
    """Test gedrag zonder eigen_woning config."""

    def test_geen_config_geeft_nul(self):
        """Als config.eigen_woning None is, retourneert de engine altijd nul-waarden."""
        from pensioen.tax.belasting_loader import (
            BelastingConfig, SchijfConfig, HeffingskortingConfig,
            ArbeidskortingConfig, Box3Config, AOWBedragConfig,
        )
        from decimal import Decimal

        # Minimale config zonder eigen_woning
        config = BelastingConfig(
            jaar=2025,
            box1_niet_aow=[SchijfConfig(tot=None, tarief=Decimal("0.495"))],
            box1_aow=[SchijfConfig(tot=None, tarief=Decimal("0.0817"))],
            ahk=HeffingskortingConfig(Decimal("3362"), Decimal("24813"), Decimal("0.06095")),
            arbeidskorting=ArbeidskortingConfig(Decimal("5532"), Decimal("39898"), Decimal("0.0651")),
            ouderenkorting=HeffingskortingConfig(Decimal("1884"), Decimal("40888"), Decimal("0.15")),
            alleenstaandeouderenkorting=None,
            box3=Box3Config(Decimal("57684"), Decimal("0.36"), Decimal("0.015"), Decimal("0.06"), ""),
            aow_bedrag=AOWBedragConfig(Decimal("1396"), Decimal("964")),
            premies=None,
            eigen_woning=None,
        )
        invoer = EigenWoningInvoer(
            woz_waarde=Decimal("500000"),
            betaalde_hypotheekrente=Decimal("6000"),
        )
        resultaat = bereken_eigen_woning(invoer, config)
        assert resultaat.eigenwoningforfait == Decimal("0")
        assert resultaat.box1_mutatie == Decimal("0")
        assert resultaat.tariefsaanpassing == Decimal("0")
