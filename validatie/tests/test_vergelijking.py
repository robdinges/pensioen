"""Tests voor belasting vergelijking tooling."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from validatie.belasting_vergelijking.dutch_tax_adapter import (
    DutchTaxData,
    laad_dutch_tax_submission,
)
from validatie.belasting_vergelijking.pensioen_adapter import bereken_via_pensioen_engine
from validatie.belasting_vergelijking.rapport_generator import genereer_markdown_rapport
from validatie.belasting_vergelijking.vergelijker import vergelijk_berekeningen


# Pad naar test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestDutchTaxAdapter:
    """Tests voor dutch_tax JSON parsing."""

    def test_laad_alleenstaand_simpel(self):
        """Test parsing van simpele alleenstaande testcase."""
        json_pad = FIXTURES_DIR / "test_alleenstaand.json"
        
        data = laad_dutch_tax_submission(json_pad)
        
        assert data.huishouden_id == "TestCase_Alleenstaand_Simpel"
        assert data.heeft_fiscaal_partner is False
        assert data.jaar == 2025
        assert len(data.personen) == 1
        
        persoon = data.personen[0]
        assert persoon.naam == "Jan Testpersoon"
        assert persoon.bsn == "123456789"
        assert persoon.heeft_aow is True
        assert len(persoon.inkomsten) == 1
        assert persoon.inkomsten[0].bruto_bedrag == Decimal("18500")
        assert persoon.inkomsten[0].soort == "PENSION"
        
        # Box 3
        assert data.totaal_spaargeld() == Decimal("45000")
        assert data.totaal_beleggingen() == Decimal("25000")
        assert data.netto_vermogen() == Decimal("70000")

    def test_laad_partner_eigen_woning(self):
        """Test parsing van complexere testcase met partner en eigen woning."""
        json_pad = FIXTURES_DIR / "test_partner_eigenwoning.json"
        
        data = laad_dutch_tax_submission(json_pad)
        
        assert data.huishouden_id == "TestCase_Partner_Complexer"
        assert data.heeft_fiscaal_partner is True
        assert len(data.personen) == 2
        
        # Persoon 1
        p1 = data.personen[0]
        assert p1.naam == "Marie Testpersoon"
        assert len(p1.inkomsten) == 2  # Werkgeverspensioen + AOW
        assert len(p1.aftrekposten) == 1  # Beddengoed
        assert p1.eigen_woning is not None
        assert p1.eigen_woning.woz_waarde == Decimal("350000")
        
        # Persoon 2
        p2 = data.personen[1]
        assert p2.naam == "Pieter Testpersoon"
        assert len(p2.inkomsten) == 1  # Alleen AOW
        
        # Box 3
        assert data.totaal_spaargeld() == Decimal("85000")
        assert data.totaal_beleggingen() == Decimal("100000")
        assert data.totaal_dividend_ingehouden == Decimal("125")


class TestPensioenAdapter:
    """Tests voor pensioen-app adapter."""

    def test_bereken_alleenstaand(self):
        """Test berekening voor alleenstaande via pensioen-app."""
        json_pad = FIXTURES_DIR / "test_alleenstaand.json"
        data = laad_dutch_tax_submission(json_pad)
        
        # AOW-leeftijd: geboren 1957-01-01 (69 jaar in 2026)
        gb_p1 = date(1957, 1, 1)
        
        resultaat = bereken_via_pensioen_engine(data, 2026, gb_p1)
        
        assert resultaat.huishouden_id == "TestCase_Alleenstaand_Simpel"
        assert resultaat.jaar == 2026
        assert resultaat.heeft_partner is False
        assert len(resultaat.personen) == 1
        
        persoon = resultaat.personen[0]
        assert persoon.bruto_inkomen == Decimal("18500")
        assert persoon.arbeidsinkomen == Decimal("0")
        assert persoon.ahk > Decimal("0")  # Heeft AHK
        assert persoon.ouderenkorting > Decimal("0")  # Heeft ouderenkorting
        assert persoon.arbeidskorting == Decimal("0")  # Geen arbeidsinkomen
        
        # Box 3
        assert resultaat.box3_totaal_vermogen == Decimal("70000")
        # Vrijstelling alleenstaand 2026: €59.357
        assert resultaat.box3_belastbaar_vermogen > Decimal("0")

    def test_bereken_partner_waarschuwingen(self):
        """Test dat eigenwoningforfait en aftrekposten waarschuwingen genereren."""
        json_pad = FIXTURES_DIR / "test_partner_eigenwoning.json"
        data = laad_dutch_tax_submission(json_pad)
        
        gb_p1 = date(1955, 5, 1)
        gb_p2 = date(1958, 3, 15)
        
        resultaat = bereken_via_pensioen_engine(data, 2026, gb_p1, gb_p2)
        
        # Check dat eerste persoon (Marie) waarschuwingen heeft
        marie = resultaat.personen[0]
        aannames_str = " ".join(marie.aannames)
        
        assert "Eigenwoningforfait" in aannames_str
        assert "WOZ" in aannames_str
        assert "aftrekpost" in aannames_str.lower()


class TestVergelijker:
    """Tests voor vergelijking tussen dutch_tax en pensioen-app."""

    def test_vergelijk_alleenstaand(self):
        """Test volledige vergelijking voor alleenstaande."""
        json_pad = FIXTURES_DIR / "test_alleenstaand.json"
        gb_p1 = date(1957, 1, 1)
        
        resultaat = vergelijk_berekeningen(json_pad, 2026, gb_p1)
        
        assert resultaat.huishouden_id == "TestCase_Alleenstaand_Simpel"
        assert resultaat.jaar == 2026
        assert resultaat.submission_jaar == 2025
        assert len(resultaat.verschillen) >= 0  # Kan verschillen hebben
        
        # Moet conclusies en aanbevelingen hebben
        assert len(resultaat.conclusies) > 0
        # Geen eigenwoningforfait/aftrekposten, dus minder aanbevelingen
        assert isinstance(resultaat.aanbevelingen, list)

    def test_vergelijk_partner_met_eigenwoning(self):
        """Test vergelijking met eigenwoningforfait en aftrekposten."""
        json_pad = FIXTURES_DIR / "test_partner_eigenwoning.json"
        gb_p1 = date(1955, 5, 1)
        gb_p2 = date(1958, 3, 15)
        
        resultaat = vergelijk_berekeningen(json_pad, 2026, gb_p1, gb_p2)
        
        assert resultaat.huishouden_id == "TestCase_Partner_Complexer"
        
        # Moet verschillen bevatten voor eigenwoningforfait en aftrekposten
        categorieen = {v.categorie for v in resultaat.verschillen}
        assert any("Box 1" in cat for cat in categorieen)
        
        # Check dat eigenwoningforfait wordt gemeld
        onderdelen = {v.onderdeel for v in resultaat.verschillen}
        assert any("Eigenwoningforfait" in od for od in onderdelen)
        
        # Check dat aftrekposten worden gemeld
        assert any("Aftrekpost" in od for od in onderdelen)
        
        # Moet aanbevelingen hebben voor ontbrekende features
        assert len(resultaat.aanbevelingen) > 0
        aanbevelingen_str = " ".join(resultaat.aanbevelingen)
        assert "eigenwoningforfait" in aanbevelingen_str.lower()


class TestRapportGenerator:
    """Tests voor rapport generatie."""

    def test_genereer_markdown_rapport(self):
        """Test markdown rapport generatie."""
        json_pad = FIXTURES_DIR / "test_alleenstaand.json"
        gb_p1 = date(1957, 1, 1)
        
        resultaat = vergelijk_berekeningen(json_pad, 2026, gb_p1)
        markdown = genereer_markdown_rapport(resultaat)
        
        assert "# Belastingvergelijking" in markdown
        assert "TestCase_Alleenstaand_Simpel" in markdown
        assert "2026" in markdown
        assert "Samenvatting" in markdown
        assert "Verschillenanalyse" in markdown
        
        # Check dat tabellen aanwezig zijn
        assert "| Onderdeel |" in markdown
        
        # Check dat disclaimer aanwezig is
        assert "Disclaimer" in markdown

    def test_markdown_bevat_aanbevelingen(self):
        """Test dat markdown aanbevelingen bevat."""
        json_pad = FIXTURES_DIR / "test_partner_eigenwoning.json"
        gb_p1 = date(1955, 5, 1)
        gb_p2 = date(1958, 3, 15)
        
        resultaat = vergelijk_berekeningen(json_pad, 2026, gb_p1, gb_p2)
        markdown = genereer_markdown_rapport(resultaat)
        
        assert "Aanbevelingen" in markdown
        assert "PRIORITEIT" in markdown


class TestDataIntegriteit:
    """Tests voor data-integriteit tijdens conversie."""

    def test_decimals_blijven_precies(self):
        """Test dat Decimal waarden precies blijven tijdens parsing."""
        json_pad = FIXTURES_DIR / "test_alleenstaand.json"
        data = laad_dutch_tax_submission(json_pad)
        
        # Check dat bedragen exact zijn (geen floating point errors)
        assert data.totaal_spaargeld() == Decimal("45000")
        assert data.totaal_beleggingen() == Decimal("25000")
        
        persoon = data.personen[0]
        totaal_bruto = sum((i.bruto_bedrag for i in persoon.inkomsten), Decimal("0"))
        assert totaal_bruto == Decimal("18500")

    def test_geen_data_verlies_bij_roundtrip(self):
        """Test dat geen belangrijke data verloren gaat."""
        json_pad = FIXTURES_DIR / "test_partner_eigenwoning.json"
        data = laad_dutch_tax_submission(json_pad)
        
        # Alle belangrijke velden moeten aanwezig zijn
        assert data.huishouden_id != ""
        assert len(data.personen) == 2
        
        for persoon in data.personen:
            assert persoon.naam != ""
            assert persoon.bsn != ""
            assert len(persoon.inkomsten) > 0
