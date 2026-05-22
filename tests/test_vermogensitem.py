"""Tests voor VermogensItem model."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pensioen.models.vermogensitem import VermogensItem, VermogensType


class TestVermogensItem:
    """Tests voor VermogensItem datamodel."""

    def test_spaargeld_aanmaken(self):
        """Test aanmaken van spaargeld item."""
        item = VermogensItem(
            omschrijving="Spaarrekening ING",
            type=VermogensType.SPAARGELD,
            aanschafwaarde=Decimal("50000"),
            groei_pct=Decimal("2.5"),
        )
        
        assert item.omschrijving == "Spaarrekening ING"
        assert item.type == VermogensType.SPAARGELD
        assert item.aanschafwaarde == Decimal("50000")
        assert item.groei_pct == Decimal("2.5")
        assert item.box3_belast is True
        assert item.persoon == "Huishouden"
    
    def test_auto_met_afschrijving(self):
        """Test auto met negatieve groei (afschrijving)."""
        item = VermogensItem(
            omschrijving="Tesla Model 3",
            type=VermogensType.AUTO,
            aanschafwaarde=Decimal("45000"),
            aanschafdatum=date(2024, 1, 1),
            groei_pct=Decimal("-15"),  # 15% afschrijving per jaar
            verkoopdatum=date(2029, 1, 1),
            verkoopprijs=Decimal("15000"),
        )
        
        assert item.type == VermogensType.AUTO
        assert item.groei_pct == Decimal("-15")
        assert item.verkoopdatum == date(2029, 1, 1)
        assert item.verkoopprijs == Decimal("15000")
    
    def test_kunst_met_waardestijging(self):
        """Test kunstobject met positieve groei."""
        item = VermogensItem(
            omschrijving="Schilderij Rembrandt",
            type=VermogensType.KUNST,
            aanschafwaarde=Decimal("100000"),
            groei_pct=Decimal("3"),  # 3% waardestijging per jaar
        )
        
        assert item.type == VermogensType.KUNST
        assert item.groei_pct == Decimal("3")
    
    def test_eigen_woning_box3_vrijstelling(self):
        """Test dat eigen woning automatisch box3_belast op False zet."""
        item = VermogensItem(
            omschrijving="Eigen woning Hoofdstraat 1",
            type=VermogensType.EIGEN_WONING,
            aanschafwaarde=Decimal("400000"),
            box3_belast=True,  # Expliciet op True, maar wordt automatisch False
        )
        
        # Na validatie moet box3_belast False zijn
        assert item.box3_belast is False
    
    def test_waarde_op_datum_zonder_groei(self):
        """Test waardebepaling zonder groei."""
        item = VermogensItem(
            omschrijving="Spaargeld",
            type=VermogensType.SPAARGELD,
            aanschafwaarde=Decimal("10000"),
            groei_pct=Decimal("0"),
        )
        
        # Waarde blijft gelijk
        assert item.waarde_op_datum(date(2026, 1, 1)) == Decimal("10000")
        assert item.waarde_op_datum(date(2030, 1, 1)) == Decimal("10000")
    
    def test_waarde_op_datum_met_groei(self):
        """Test waardebepaling met groei over meerdere jaren."""
        item = VermogensItem(
            omschrijving="Beleggingen",
            type=VermogensType.BELEGGINGEN,
            aanschafwaarde=Decimal("100000"),
            aanschafdatum=date(2020, 1, 1),
            groei_pct=Decimal("5"),  # 5% per jaar
        )
        
        # Na 6 jaar (2020 -> 2026): 100000 * 1.05^6 ≈ 134009.56
        waarde_2026 = item.waarde_op_datum(date(2026, 1, 1))
        assert abs(waarde_2026 - Decimal("134009.56")) < Decimal("20")  # Binnen €20 marge (float conversie)
    
    def test_waarde_op_datum_met_afschrijving(self):
        """Test waardebepaling met afschrijving."""
        item = VermogensItem(
            omschrijving="Auto",
            type=VermogensType.AUTO,
            aanschafwaarde=Decimal("30000"),
            aanschafdatum=date(2024, 1, 1),
            groei_pct=Decimal("-20"),  # 20% afschrijving per jaar
        )
        
        # Na 1 jaar: 30000 * 0.8 = 24000
        waarde_2025 = item.waarde_op_datum(date(2025, 1, 1))
        assert abs(waarde_2025 - Decimal("24000")) < Decimal("20")
        
        # Na 2 jaar: 30000 * 0.8^2 = 19200
        waarde_2026 = item.waarde_op_datum(date(2026, 1, 1))
        assert abs(waarde_2026 - Decimal("19200")) < Decimal("20")
    
    def test_waarde_voor_aanschafdatum(self):
        """Test dat waarde 0 is vóór aanschafdatum."""
        item = VermogensItem(
            omschrijving="Auto",
            type=VermogensType.AUTO,
            aanschafwaarde=Decimal("30000"),
            aanschafdatum=date(2025, 6, 1),
        )
        
        assert item.waarde_op_datum(date(2025, 1, 1)) == Decimal("0")
        assert item.waarde_op_datum(date(2025, 5, 31)) == Decimal("0")
        assert item.waarde_op_datum(date(2025, 6, 1)) == Decimal("30000")
    
    def test_waarde_na_verkoop(self):
        """Test dat waarde 0 is na verkoopdatum."""
        item = VermogensItem(
            omschrijving="Auto",
            type=VermogensType.AUTO,
            aanschafwaarde=Decimal("30000"),
            aanschafdatum=date(2024, 1, 1),
            verkoopdatum=date(2028, 12, 31),
            verkoopprijs=Decimal("10000"),
        )
        
        assert item.waarde_op_datum(date(2029, 1, 1)) == Decimal("0")
        assert item.waarde_op_datum(date(2030, 1, 1)) == Decimal("0")
    
    def test_verkoopprijs_op_verkoopdatum(self):
        """Test dat verkoopprijs wordt gebruikt op verkoopdatum."""
        item = VermogensItem(
            omschrijving="Auto",
            type=VermogensType.AUTO,
            aanschafwaarde=Decimal("30000"),
            aanschafdatum=date(2024, 1, 1),
            groei_pct=Decimal("-15"),
            verkoopdatum=date(2028, 1, 1),
            verkoopprijs=Decimal("12000"),
        )
        
        # Op verkoopdatum: gebruik verkoopprijs
        assert item.waarde_op_datum(date(2028, 1, 1)) == Decimal("12000")
    
    def test_is_actief_op(self):
        """Test actief-status op verschillende datums."""
        item = VermogensItem(
            omschrijving="Auto",
            type=VermogensType.AUTO,
            aanschafwaarde=Decimal("30000"),
            aanschafdatum=date(2024, 1, 1),
            verkoopdatum=date(2028, 12, 31),
        )
        
        assert item.is_actief_op(date(2023, 12, 31)) is False  # Voor aankoop
        assert item.is_actief_op(date(2024, 1, 1)) is True     # Op aankoopdatum
        assert item.is_actief_op(date(2026, 6, 15)) is True    # Tijdens bezit
        assert item.is_actief_op(date(2028, 12, 31)) is True   # Op verkoopdatum
        assert item.is_actief_op(date(2029, 1, 1)) is False    # Na verkoop
    
    def test_validatie_negatieve_aanschafwaarde(self):
        """Test dat negatieve aanschafwaarde wordt afgewezen."""
        with pytest.raises(ValueError, match="aanschafwaarde mag niet negatief"):
            VermogensItem(
                omschrijving="Test",
                type=VermogensType.AUTO,
                aanschafwaarde=Decimal("-10000"),
            )
    
    def test_validatie_groei_pct_te_hoog(self):
        """Test dat onrealistische groei wordt afgewezen."""
        with pytest.raises(ValueError, match="groei_pct moet tussen"):
            VermogensItem(
                omschrijving="Test",
                type=VermogensType.BELEGGINGEN,
                aanschafwaarde=Decimal("10000"),
                groei_pct=Decimal("150"),  # 150% groei is onrealistisch
            )
    
    def test_validatie_groei_pct_te_laag(self):
        """Test dat te sterke afschrijving wordt afgewezen."""
        with pytest.raises(ValueError, match="groei_pct moet tussen"):
            VermogensItem(
                omschrijving="Test",
                type=VermogensType.AUTO,
                aanschafwaarde=Decimal("10000"),
                groei_pct=Decimal("-150"),  # -150% afschrijving is onrealistisch
            )
    
    def test_validatie_verkoopprijs_zonder_datum(self):
        """Test dat verkoopprijs zonder verkoopdatum wordt afgewezen."""
        with pytest.raises(ValueError, match="verkoopprijs vereist een verkoopdatum"):
            VermogensItem(
                omschrijving="Auto",
                type=VermogensType.AUTO,
                aanschafwaarde=Decimal("30000"),
                verkoopprijs=Decimal("10000"),
            )
    
    def test_validatie_negatieve_verkoopprijs(self):
        """Test dat negatieve verkoopprijs wordt afgewezen."""
        with pytest.raises(ValueError, match="verkoopprijs mag niet negatief"):
            VermogensItem(
                omschrijving="Auto",
                type=VermogensType.AUTO,
                aanschafwaarde=Decimal("30000"),
                verkoopdatum=date(2028, 1, 1),
                verkoopprijs=Decimal("-5000"),
            )
    
    def test_validatie_verkoop_voor_aankoop(self):
        """Test dat verkoop vóór aankoop wordt afgewezen."""
        with pytest.raises(ValueError, match="verkoopdatum mag niet vóór aanschafdatum"):
            VermogensItem(
                omschrijving="Auto",
                type=VermogensType.AUTO,
                aanschafwaarde=Decimal("30000"),
                aanschafdatum=date(2025, 1, 1),
                verkoopdatum=date(2024, 1, 1),
            )
    
    def test_boot_met_afschrijving(self):
        """Test boot scenario uit backlog."""
        item = VermogensItem(
            omschrijving="Zeilboot Bavaria 46",
            type=VermogensType.BOOT,
            aanschafwaarde=Decimal("80000"),
            aanschafdatum=date(2024, 1, 1),
            groei_pct=Decimal("-10"),  # 10% afschrijving
            box3_belast=False,  # Vrijgesteld voor recreatie
        )
        
        assert item.type == VermogensType.BOOT
        assert item.box3_belast is False
        
        # Na 1 jaar: 80000 * 0.9 = 72000
        waarde_2025 = item.waarde_op_datum(date(2025, 1, 1))
        assert abs(waarde_2025 - Decimal("72000")) < Decimal("20")
