"""Tests voor gesplitst rendement (sparen vs beleggen)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.calculations.vermogen_engine import bereken_rente_maand
from pensioen.models.component import (
    BedragType,
    CategorieComponent,
    FinancieelComponent,
    Frequentie,
)
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.tax.belasting_loader import laad_tarieven


def test_rendement_sparen_vs_beleggen_verschil():
    """Test dat verschillende rendementen voor sparen/beleggen impact hebben."""
    persoon = Persoon(
        naam="Test",
        geboortedatum=date(1970, 1, 1),
        heeft_partner=False,
    )
    
    # Scenario met €60k inkomen en €30k uitgaven = substantieel overschot per jaar
    # Start met €50.000 vermogen om direct rendement te hebben
    scenario_basis = Scenario(
        naam="Basis 3% rendement",
        rendement_pct=Decimal("3"),  # 3% uniform
        vermogensitems=[],  # Geen vermogensitems, maar wel startvermogen via jaarlijkse_inleg
        componenten=[
            FinancieelComponent(
                omschrijving="Salaris",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="Test",
                bedrag_type=BedragType.BRUTO,
                bedrag=Decimal("5000"),  # €5000/maand = €60k/jaar
                frequentie=Frequentie.MAANDELIJKS,
                begindatum=date(2025, 1, 1),
                einddatum=date(2030, 12, 31),
            ),
            FinancieelComponent(
                omschrijving="Uitgaven",
                categorie=CategorieComponent.UITGAVE,
                persoon="Huishouden",
                bedrag_type=BedragType.BRUTO,
                bedrag=Decimal("2500"),  # €2500/maand = €30k/jaar
                frequentie=Frequentie.MAANDELIJKS,
                begindatum=date(2025, 1, 1),
                einddatum=date(2030, 12, 31),
            ),
        ],
        jaarlijkse_inleg=Decimal("50000"),  # Start vermogen van €50k
    )
    
    # Scenario met gesplitst rendement: 1% sparen, 6% beleggen
    scenario_split = Scenario(
        naam="Split rendement",
        rendement_pct=Decimal("3"),  # fallback (niet gebruikt)
        rendement_sparen_pct=Decimal("1"),  # laag rendement op spaargeld
        rendement_beleggen_pct=Decimal("6"),  # hoog rendement op beleggingen
        box3_spaargeld_fractie=Decimal("0.5"),  # 50/50 split
        vermogensitems=[],
        componenten=[
            FinancieelComponent(
                omschrijving="Salaris",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="Test",
                bedrag_type=BedragType.BRUTO,
                bedrag=Decimal("5000"),
                frequentie=Frequentie.MAANDELIJKS,
                begindatum=date(2025, 1, 1),
                einddatum=date(2030, 12, 31),
            ),
            FinancieelComponent(
                omschrijving="Uitgaven",
                categorie=CategorieComponent.UITGAVE,
                persoon="Huishouden",
                bedrag_type=BedragType.BRUTO,
                bedrag=Decimal("2500"),
                frequentie=Frequentie.MAANDELIJKS,
                begindatum=date(2025, 1, 1),
                einddatum=date(2030, 12, 31),
            ),
        ],
        jaarlijkse_inleg=Decimal("50000"),  # Start vermogen van €50k
    )
    
    belasting_configs = {jaar: laad_tarieven(jaar) for jaar in range(2025, 2031)}
    
    # Bereken beide scenarios
    cashflow_basis = bereken_huishouden(
        scenario=scenario_basis,
        persoon1=persoon,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2025,
        jaar_tot=2030,
        belasting_configs=belasting_configs,
    )
    
    cashflow_split = bereken_huishouden(
        scenario=scenario_split,
        persoon1=persoon,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2025,
        jaar_tot=2030,
        belasting_configs=belasting_configs,
    )
    
    # Vergelijk eindvermogen
    eindvermogen_basis = cashflow_basis.jaren[-1].vermogen_einde_jaar
    eindvermogen_split = cashflow_split.jaren[-1].vermogen_einde_jaar
    
    # De split van 50/50 tussen 1% en 6% geeft gemiddeld 3.5%
    # MAAR: de werkelijke spaargeld_fractie kan afwijken door cashflows en box3
    # We testen hier dat er een meetbaar verschil is tussen uniform en split
    verschil = abs(eindvermogen_split - eindvermogen_basis)
    
    # Verschil moet substantieel zijn (minimaal €5000 na 6 jaar met €50k start)
    assert verschil > Decimal("5000"), (
        f"Verschil tussen gesplitst en uniform rendement te klein: €{verschil:,.2f}. "
        f"Basis (3%): €{eindvermogen_basis:,.2f}, Split (1%/6% 50/50): €{eindvermogen_split:,.2f}"
    )
    
    # Ook controleren dat beide eindvermogens positief en realistisch zijn
    assert eindvermogen_basis > Decimal("100000"), (
        f"Basis eindvermogen te laag: €{eindvermogen_basis:,.2f}"
    )
    assert eindvermogen_split > Decimal("100000"), (
        f"Split eindvermogen te laag: €{eindvermogen_split:,.2f}"
    )


def test_rendement_sparen_100_procent():
    """Test dat 100% spaargeld het juiste rendement krijgt."""
    # 100% spaargeld met 1% rendement
    # rendement_pct wordt alleen gebruikt als fallback, dus zet op 3% (realistische waarde)
    scenario = Scenario(
        naam="100% sparen",
        rendement_pct=Decimal("3"),  # fallback, niet gebruikt bij split
        rendement_sparen_pct=Decimal("1"),
        rendement_beleggen_pct=Decimal("6"),
        box3_spaargeld_fractie=Decimal("1"),  # 100% spaargeld
    )
    
    # Bereken rendement op €10.000
    rente = bereken_rente_maand(
        saldo=Decimal("10000"),
        jaarrendement_pct=scenario.rendement_pct,
        jaarrendement_sparen_pct=scenario.rendement_sparen_pct,
        jaarrendement_beleggen_pct=scenario.rendement_beleggen_pct,
        spaargeld_fractie=scenario.box3_spaargeld_fractie,
    )
    
    # Bij 1% jaarrendement op €10.000 verwacht je ~€8,33 per maand
    # (€10.000 * 0.01 / 12 ≈ €8,33, maar compound interest iets meer)
    assert Decimal("8") < rente < Decimal("9"), (
        f"Rente op €10.000 bij 1% moet ~€8,33/maand zijn, kreeg: €{rente}"
    )


def test_rendement_beleggen_100_procent():
    """Test dat 100% beleggingen het juiste rendement krijgt."""
    # 100% beleggingen met 6% rendement
    # rendement_pct wordt alleen gebruikt als fallback, dus zet op 3% (realistische waarde)
    scenario = Scenario(
        naam="100% beleggen",
        rendement_pct=Decimal("3"),  # fallback, niet gebruikt bij split
        rendement_sparen_pct=Decimal("1"),
        rendement_beleggen_pct=Decimal("6"),
        box3_spaargeld_fractie=Decimal("0"),  # 0% spaargeld = 100% beleggen
    )
    
    # Bereken rendement op €10.000
    rente = bereken_rente_maand(
        saldo=Decimal("10000"),
        jaarrendement_pct=scenario.rendement_pct,
        jaarrendement_sparen_pct=scenario.rendement_sparen_pct,
        jaarrendement_beleggen_pct=scenario.rendement_beleggen_pct,
        spaargeld_fractie=scenario.box3_spaargeld_fractie,
    )
    
    # Bij 6% jaarrendement op €10.000 verwacht je ~€50 per maand
    # (€10.000 * 0.06 / 12 = €50, maar compound interest iets meer)
    assert Decimal("48") < rente < Decimal("52"), (
        f"Rente op €10.000 bij 6% moet ~€50/maand zijn, kreeg: €{rente}"
    )


def test_rendement_50_50_split():
    """Test dat 50/50 split het gemiddelde rendement geeft."""
    # rendement_pct wordt alleen gebruikt als fallback, dus zet op 3% (realistische waarde)
    scenario = Scenario(
        naam="50/50 split",
        rendement_pct=Decimal("3"),  # fallback, niet gebruikt bij split
        rendement_sparen_pct=Decimal("2"),
        rendement_beleggen_pct=Decimal("8"),
        box3_spaargeld_fractie=Decimal("0.5"),  # 50/50 split
    )
    
    # Bereken rendement op €10.000
    rente = bereken_rente_maand(
        saldo=Decimal("10000"),
        jaarrendement_pct=scenario.rendement_pct,
        jaarrendement_sparen_pct=scenario.rendement_sparen_pct,
        jaarrendement_beleggen_pct=scenario.rendement_beleggen_pct,
        spaargeld_fractie=scenario.box3_spaargeld_fractie,
    )
    
    # Bij 50/50 split van 2% en 8% = gemiddeld 5%
    # €10.000 * 0.05 / 12 ≈ €41,67 per maand (compound iets meer)
    assert Decimal("40") < rente < Decimal("44"), (
        f"Rente op €10.000 bij 50/50 split (2%/8%) moet ~€41,67/maand zijn, kreeg: €{rente}"
    )
