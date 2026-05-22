"""Tests voor de vermogensontwikkelingsberekening."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pensioen.calculations.vermogen_engine import (
    bereken_rente_maand,
    bereken_vermogen_box3_belast,
    bereken_vermogen_per_type,
    bereken_vermogen_totaal,
    bereken_vermogensontwikkeling,
    maandrendement,
    update_vermogensitems_waarde,
)
from pensioen.models.vermogensitem import VermogensItem, VermogensType


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


class TestVermogensItems:
    """Tests voor VermogensItems functionaliteit in vermogen_engine."""
    
    def test_bereken_vermogen_totaal_enkelvoudig(self) -> None:
        """Bereken totaal vermogen met één item."""
        items = [
            VermogensItem(
                omschrijving="Spaargeld",
                type=VermogensType.SPAARGELD,
                aanschafwaarde=Decimal("50000"),
            )
        ]
        
        totaal = bereken_vermogen_totaal(items, date(2026, 1, 1))
        assert totaal == Decimal("50000")
    
    def test_bereken_vermogen_totaal_meerdere_items(self) -> None:
        """Bereken totaal vermogen met meerdere items."""
        items = [
            VermogensItem(
                omschrijving="Spaargeld",
                type=VermogensType.SPAARGELD,
                aanschafwaarde=Decimal("30000"),
            ),
            VermogensItem(
                omschrijving="Beleggingen",
                type=VermogensType.BELEGGINGEN,
                aanschafwaarde=Decimal("70000"),
            ),
            VermogensItem(
                omschrijving="Auto",
                type=VermogensType.AUTO,
                aanschafwaarde=Decimal("25000"),
            ),
        ]
        
        totaal = bereken_vermogen_totaal(items, date(2026, 1, 1))
        assert totaal == Decimal("125000")
    
    def test_bereken_vermogen_box3_belast(self) -> None:
        """Bereken alleen box 3 belast vermogen."""
        items = [
            VermogensItem(
                omschrijving="Spaargeld",
                type=VermogensType.SPAARGELD,
                aanschafwaarde=Decimal("50000"),
                box3_belast=True,
            ),
            VermogensItem(
                omschrijving="Eigen woning",
                type=VermogensType.EIGEN_WONING,
                aanschafwaarde=Decimal("400000"),
                box3_belast=False,  # Auto-gezet door validatie
            ),
            VermogensItem(
                omschrijving="Boot",
                type=VermogensType.BOOT,
                aanschafwaarde=Decimal("80000"),
                box3_belast=False,  # Recreatie vrijgesteld
            ),
        ]
        
        box3_vermogen = bereken_vermogen_box3_belast(items, date(2026, 1, 1))
        # Alleen spaargeld telt mee
        assert box3_vermogen == Decimal("50000")
    
    def test_bereken_vermogen_per_type(self) -> None:
        """Bereken vermogen opgesplitst per VermogensType."""
        items = [
            VermogensItem(
                omschrijving="Spaarrekening 1",
                type=VermogensType.SPAARGELD,
                aanschafwaarde=Decimal("30000"),
            ),
            VermogensItem(
                omschrijving="Spaarrekening 2",
                type=VermogensType.SPAARGELD,
                aanschafwaarde=Decimal("20000"),
            ),
            VermogensItem(
                omschrijving="Aandelen",
                type=VermogensType.BELEGGINGEN,
                aanschafwaarde=Decimal("100000"),
            ),
            VermogensItem(
                omschrijving="Tesla",
                type=VermogensType.AUTO,
                aanschafwaarde=Decimal("45000"),
            ),
        ]
        
        per_type = bereken_vermogen_per_type(items, date(2026, 1, 1))
        
        assert per_type[VermogensType.SPAARGELD] == Decimal("50000")
        assert per_type[VermogensType.BELEGGINGEN] == Decimal("100000")
        assert per_type[VermogensType.AUTO] == Decimal("45000")
    
    def test_update_vermogensitems_waarde_overschot(self) -> None:
        """Update vermogensitems met positieve cashflow (overschot)."""
        items = [
            VermogensItem(
                omschrijving="Spaargeld",
                type=VermogensType.SPAARGELD,
                aanschafwaarde=Decimal("10000"),
            ),
        ]
        
        nieuwe_items = update_vermogensitems_waarde(
            items,
            date(2026, 1, 1),
            Decimal("5000"),  # €5000 overschot
        )
        
        # Spaargeld moet verhoogd zijn
        assert nieuwe_items[0].aanschafwaarde == Decimal("15000")
    
    def test_update_vermogensitems_waarde_tekort(self) -> None:
        """Update vermogensitems met negatieve cashflow (tekort)."""
        items = [
            VermogensItem(
                omschrijving="Spaargeld",
                type=VermogensType.SPAARGELD,
                aanschafwaarde=Decimal("10000"),
            ),
        ]
        
        nieuwe_items = update_vermogensitems_waarde(
            items,
            date(2026, 1, 1),
            Decimal("-3000"),  # €3000 tekort
        )
        
        # Spaargeld moet verlaagd zijn
        assert nieuwe_items[0].aanschafwaarde == Decimal("7000")
    
    def test_update_vermogensitems_geen_liquide_items(self) -> None:
        """Update zonder liquide items: maak nieuw spaargeld item."""
        items = [
            VermogensItem(
                omschrijving="Auto",
                type=VermogensType.AUTO,
                aanschafwaarde=Decimal("30000"),
            ),
        ]
        
        nieuwe_items = update_vermogensitems_waarde(
            items,
            date(2026, 1, 1),
            Decimal("2000"),  # €2000 overschot
        )
        
        # Moet nu 2 items hebben: auto + nieuw spaargeld
        assert len(nieuwe_items) == 2
        assert nieuwe_items[1].type == VermogensType.SPAARGELD
        assert nieuwe_items[1].aanschafwaarde == Decimal("2000")
    
    def test_update_vermogensitems_pro_rata_verdeling(self) -> None:
        """Update met meerdere liquide items: pro-rata verdeling."""
        items = [
            VermogensItem(
                omschrijving="Spaarrekening",
                type=VermogensType.SPAARGELD,
                aanschafwaarde=Decimal("30000"),  # 30% van totaal (30k / 100k)
            ),
            VermogensItem(
                omschrijving="Beleggingen",
                type=VermogensType.BELEGGINGEN,
                aanschafwaarde=Decimal("70000"),  # 70% van totaal (70k / 100k)
            ),
        ]
        
        nieuwe_items = update_vermogensitems_waarde(
            items,
            date(2026, 1, 1),
            Decimal("10000"),  # €10000 overschot
        )
        
        # 30% naar spaargeld: 30000 + 3000 = 33000
        # 70% naar beleggingen: 70000 + 7000 = 77000
        assert nieuwe_items[0].aanschafwaarde == Decimal("33000")
        assert nieuwe_items[1].aanschafwaarde == Decimal("77000")
    
    def test_vermogen_met_inactieve_items(self) -> None:
        """Items die niet actief zijn tellen niet mee."""
        items = [
            VermogensItem(
                omschrijving="Auto (verkocht)",
                type=VermogensType.AUTO,
                aanschafwaarde=Decimal("30000"),
                aanschafdatum=date(2020, 1, 1),
                verkoopdatum=date(2025, 12, 31),  # Al verkocht
            ),
            VermogensItem(
                omschrijving="Spaargeld",
                type=VermogensType.SPAARGELD,
                aanschafwaarde=Decimal("50000"),
            ),
        ]
        
        totaal = bereken_vermogen_totaal(items, date(2026, 1, 1))
        # Alleen spaargeld telt mee
        assert totaal == Decimal("50000")

