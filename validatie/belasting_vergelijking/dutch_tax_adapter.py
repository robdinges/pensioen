"""Adapter voor dutch_tax JSON submissions (2025) naar standaard tussenformaat.

Parse submission JSON handmatig zonder dependencies op dutch_tax codebase.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass
class InkomstenItem:
    """Een inkomstenbron uit Box 1."""

    bron: str
    soort: str  # PENSION, EMPLOYMENT, RENTAL, etc.
    bruto_bedrag: Decimal
    arbeidsinkomen_bedrag: Decimal = Decimal("0")  # Voor arbeidskorting
    beschrijving: str = ""


@dataclass
class AftrekItem:
    """Een aftrekpost uit Box 1."""

    naam: str
    soort: str  # PERSONAL_ALLOWANCE, PROFESSIONAL, etc.
    bedrag: Decimal


@dataclass
class VermogensItem:
    """Een vermogensbestanddeel voor Box 3."""

    naam: str
    soort: str  # SAVINGS, INVESTMENT, OTHER_ASSETS, DEBT
    waarde: Decimal
    dividend_ingehouden: Decimal = Decimal("0")
    is_groen: bool = False


@dataclass
class Heffingskorting:
    """Een heffingskorting."""

    naam: str
    bedrag: Decimal


@dataclass
class EigenWoning:
    """Eigen woning voor eigenwoningforfait."""

    woz_waarde: Decimal
    periode_fractie: Decimal = Decimal("1.0")


@dataclass
class PersoonData:
    """Persoonlijke gegevens en belastinggegevens voor één persoon."""

    persoon_id: str
    naam: str
    bsn: str
    
    # Box 1
    inkomsten: list[InkomstenItem] = field(default_factory=list)
    aftrekposten: list[AftrekItem] = field(default_factory=list)
    eigen_woning: EigenWoning | None = None
    heeft_aow: bool = False
    
    # Heffingskortingen (zoals opgegeven in submission)
    heffingskortingen: list[Heffingskorting] = field(default_factory=list)
    
    # Vooraf betaald
    loonheffing_ingehouden: Decimal = Decimal("0")
    
    # Box 2
    heeft_aanmerkelijk_belang: bool = False
    dividend_inkomen_box2: Decimal = Decimal("0")
    verkoopwinst_box2: Decimal = Decimal("0")


@dataclass
class DutchTaxData:
    """Volledige dutch_tax submission data voor een huishouden."""

    huishouden_id: str
    heeft_fiscaal_partner: bool
    aantal_kinderen: int
    jaar: int  # Belastingjaar (meestal 2025 voor de submissions)
    
    personen: list[PersoonData] = field(default_factory=list)
    
    # Box 3 (huishoudniveau)
    vermogen_items: list[VermogensItem] = field(default_factory=list)
    totaal_dividend_ingehouden: Decimal = Decimal("0")
    buitenlands_dividend_ingehouden: Decimal = Decimal("0")
    
    # Verdeling Box 3 grondslag per persoon (indien opgegeven)
    box3_verdeling: dict[str, Decimal] = field(default_factory=dict)

    def totaal_spaargeld(self) -> Decimal:
        """Totaal spaargeld (voor Box 3 forfait berekening)."""
        return sum(
            (item.waarde for item in self.vermogen_items if item.soort == "SAVINGS"),
            Decimal("0"),
        )

    def totaal_beleggingen(self) -> Decimal:
        """Totaal beleggingen + overige bezittingen (voor Box 3 forfait berekening)."""
        return sum(
            (item.waarde for item in self.vermogen_items 
             if item.soort in ("INVESTMENT", "OTHER_ASSETS")),
            Decimal("0"),
        )

    def totaal_schulden(self) -> Decimal:
        """Totaal schulden (aftrekbaar van Box 3 vermogen)."""
        return sum(
            (item.waarde for item in self.vermogen_items if item.soort == "DEBT"),
            Decimal("0"),
        )

    def netto_vermogen(self) -> Decimal:
        """Netto vermogen (bezittingen - schulden) voor Box 3."""
        bezittingen = self.totaal_spaargeld() + self.totaal_beleggingen()
        return bezittingen - self.totaal_schulden()


def _parse_decimal(waarde: Any) -> Decimal:
    """Parse een waarde naar Decimal (veilig voor int/float/str)."""
    if isinstance(waarde, Decimal):
        return waarde
    if isinstance(waarde, (int, float)):
        return Decimal(str(waarde))
    if isinstance(waarde, str):
        return Decimal(waarde)
    return Decimal("0")


def laad_dutch_tax_submission(json_pad: Path) -> DutchTaxData:
    """
    Laad een dutch_tax submission JSON bestand.
    
    Args:
        json_pad: Pad naar het submission JSON bestand (bijv. frits.json)
    
    Returns:
        DutchTaxData object met alle belastinggegevens
    
    Raises:
        FileNotFoundError: Als het bestand niet bestaat
        ValueError: Als JSON structuur ongeldig is
    """
    if not json_pad.exists():
        raise FileNotFoundError(f"Submission bestand niet gevonden: {json_pad}")
    
    with open(json_pad, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Haal hoofdgegevens op
    data_section = data.get("data", {})
    huishouden_id = data_section.get("household_id", "ONBEKEND")
    heeft_partner = data_section.get("fiscal_partner", False)
    aantal_kinderen = data_section.get("children_count", 0)
    
    # Belastingjaar: submissions zijn 2025, we passen later aan naar 2026
    jaar = 2025
    
    # Parse personen
    personen: list[PersoonData] = []
    for member_data in data_section.get("members", []):
        persoon = _parse_persoon(member_data)
        personen.append(persoon)
    
    # Parse Box 3 (huishoudniveau)
    box3_data = data_section.get("box3_household", {})
    vermogen_items = _parse_box3_vermogen(box3_data)
    
    totaal_dividend = _parse_decimal(data_section.get("dividend_withholding_total", 0))
    buitenlands_dividend = _parse_decimal(
        data_section.get("foreign_dividend_withholding_total", 0)
    )
    
    # Box 3 verdeling per persoon
    box3_verdeling: dict[str, Decimal] = {}
    joint_dist = data_section.get("joint_distribution", {})
    grondslag_dist = joint_dist.get("grondslag_voordeel_sparen_beleggen", {})
    for persoon_id, grondslag in grondslag_dist.items():
        box3_verdeling[persoon_id] = _parse_decimal(grondslag)
    
    return DutchTaxData(
        huishouden_id=huishouden_id,
        heeft_fiscaal_partner=heeft_partner,
        aantal_kinderen=aantal_kinderen,
        jaar=jaar,
        personen=personen,
        vermogen_items=vermogen_items,
        totaal_dividend_ingehouden=totaal_dividend,
        buitenlands_dividend_ingehouden=buitenlands_dividend,
        box3_verdeling=box3_verdeling,
    )


def _parse_persoon(member_data: dict) -> PersoonData:
    """Parse één persoon uit member data."""
    persoon_id = member_data.get("member_id", "ONBEKEND")
    naam = member_data.get("full_name", "Onbekend")
    bsn = member_data.get("bsn", "000000000")
    
    loonheffing = _parse_decimal(member_data.get("wage_withholding", 0))
    
    # Box 1 data
    box1_data = member_data.get("box1", {})
    inkomsten = _parse_inkomsten(box1_data.get("incomes", []))
    aftrekposten = _parse_aftrekposten(box1_data.get("deductions", []))
    
    # Eigen woning
    eigen_woning_data = box1_data.get("own_home", {})
    eigen_woning = None
    if eigen_woning_data.get("has_own_home", False):
        woz = _parse_decimal(eigen_woning_data.get("woz_value", 0))
        fractie = _parse_decimal(eigen_woning_data.get("period_fraction", 1))
        if woz > Decimal("0"):
            eigen_woning = EigenWoning(woz_waarde=woz, periode_fractie=fractie)
    
    heeft_aow = box1_data.get("has_aow", False)
    
    # Heffingskortingen
    heffingskortingen = _parse_heffingskortingen(box1_data.get("tax_credits", []))
    
    # Box 2
    box2_data = member_data.get("box2", {})
    heeft_ab = box2_data.get("has_substantial_interest", False)
    dividend_box2 = _parse_decimal(box2_data.get("dividend_income", 0))
    verkoopwinst = _parse_decimal(box2_data.get("sale_gain", 0))
    
    return PersoonData(
        persoon_id=persoon_id,
        naam=naam,
        bsn=bsn,
        inkomsten=inkomsten,
        aftrekposten=aftrekposten,
        eigen_woning=eigen_woning,
        heeft_aow=heeft_aow,
        heffingskortingen=heffingskortingen,
        loonheffing_ingehouden=loonheffing,
        heeft_aanmerkelijk_belang=heeft_ab,
        dividend_inkomen_box2=dividend_box2,
        verkoopwinst_box2=verkoopwinst,
    )


def _parse_inkomsten(incomes: list[dict]) -> list[InkomstenItem]:
    """Parse lijst van inkomsten."""
    result = []
    for income in incomes:
        soort = income.get("type", "OTHER")
        bedrag = _parse_decimal(income.get("amount", 0))
        arbeidsinkomen = _parse_decimal(income.get("labor_credit", 0))
        bron = income.get("source", "Onbekend")
        beschrijving = income.get("description", "")
        
        result.append(
            InkomstenItem(
                bron=bron,
                soort=soort,
                bruto_bedrag=bedrag,
                arbeidsinkomen_bedrag=arbeidsinkomen,
                beschrijving=beschrijving,
            )
        )
    return result


def _parse_aftrekposten(deductions: list[dict]) -> list[AftrekItem]:
    """Parse lijst van aftrekposten."""
    result = []
    for ded in deductions:
        soort = ded.get("type", "OTHER")
        naam = ded.get("name", "Aftrekpost")
        bedrag = _parse_decimal(ded.get("amount", 0))
        
        result.append(AftrekItem(naam=naam, soort=soort, bedrag=bedrag))
    return result


def _parse_heffingskortingen(tax_credits: list[dict]) -> list[Heffingskorting]:
    """Parse lijst van heffingskortingen."""
    result = []
    for credit in tax_credits:
        naam = credit.get("name", "Heffingskorting")
        bedrag = _parse_decimal(credit.get("amount", 0))
        result.append(Heffingskorting(naam=naam, bedrag=bedrag))
    return result


def _parse_box3_vermogen(box3_data: dict) -> list[VermogensItem]:
    """Parse Box 3 vermogensitems."""
    result = []
    
    # Spaarrekeningen
    for acc in box3_data.get("savings_accounts", []):
        naam = acc.get("name", "Spaarrekening")
        bedrag = _parse_decimal(acc.get("amount", 0))
        is_groen = acc.get("is_green", False)
        result.append(
            VermogensItem(
                naam=naam,
                soort="SAVINGS",
                waarde=bedrag,
                is_groen=is_groen,
            )
        )
    
    # Beleggingsrekeningen
    for acc in box3_data.get("investment_accounts", []):
        naam = acc.get("name", "Beleggingsrekening")
        bedrag = _parse_decimal(acc.get("amount", 0))
        is_groen = acc.get("is_green", False)
        dividend = _parse_decimal(acc.get("dividend_withholding", 0))
        result.append(
            VermogensItem(
                naam=naam,
                soort="INVESTMENT",
                waarde=bedrag,
                dividend_ingehouden=dividend,
                is_groen=is_groen,
            )
        )
    
    # Overige bezittingen
    for item in box3_data.get("other_assets_items", []):
        naam = item.get("name", "Overige bezitting")
        bedrag = _parse_decimal(item.get("amount", 0))
        if bedrag > Decimal("0"):
            result.append(
                VermogensItem(naam=naam, soort="OTHER_ASSETS", waarde=bedrag)
            )
    
    # Schulden
    for item in box3_data.get("debt_items", []):
        naam = item.get("name", "Schuld")
        bedrag = _parse_decimal(item.get("amount", 0))
        if bedrag > Decimal("0"):
            result.append(VermogensItem(naam=naam, soort="DEBT", waarde=bedrag))
    
    return result
