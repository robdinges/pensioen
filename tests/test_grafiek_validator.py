"""Test grafiek validator tegen rendement inclusie."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.models.component import (
    BedragType,
    CategorieComponent,
    FinancieelComponent,
    Frequentie,
)
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.models.vermogensitem import VermogensItem, VermogensType
from pensioen.tax.belasting_loader import laad_tarieven
from pensioen.validators.grafiek_validator import valideer_cashflow_consistency


@pytest.fixture
def scenario_met_rendement():
    """Simpel scenario met vermogen dat rendement genereert."""
    persoon = Persoon(
        naam="Jan",
        geboortedatum=date(1970, 1, 1),
        heeft_partner=False,
    )
    
    scenario = Scenario(
        naam="Test met rendement",
        persoon1=persoon,
        persoon2=None,
        rendement_pct=Decimal("5"),
        rendement_sparen_pct=Decimal("2"),
        rendement_beleggen_pct=Decimal("6"),
        componenten=[
            # Basisinkomen
            FinancieelComponent(
                omschrijving="Salaris",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="P1",
                bedrag_type=BedragType.BRUTO,
                bedrag=Decimal("3000"),
                frequentie=Frequentie.MAANDELIJKS,
                begindatum=date(2026, 1, 1),
                einddatum=date(2030, 12, 31),
            ),
        ],
        vermogensitems=[
            # Spaargeld met rendement
            VermogensItem(
                omschrijving="Spaarrekening",
                type=VermogensType.SPAARGELD,
                persoon="P1",
                aanschafwaarde=Decimal("50000"),
                groei_pct=Decimal("2"),
                box3_belast=True,
            ),
            # Beleggingen met hoger rendement
            VermogensItem(
                omschrijving="Beleggingsportefeuille",
                type=VermogensType.BELEGGINGEN,
                persoon="P1",
                aanschafwaarde=Decimal("100000"),
                groei_pct=Decimal("6"),
                box3_belast=True,
            ),
        ],
    )
    
    return persoon, scenario


def test_validator_accepteert_rendement_in_totaal_bruto(scenario_met_rendement):
    """
    Test dat de validator correct omgaat met rendement in totaal_bruto.
    
    Voorheen foutief: bruto_som = arbeid + aow + pensioen + overig (geen rendement)
    Correct: bruto_som = arbeid + aow + pensioen + overig + rendement
    """
    persoon, scenario = scenario_met_rendement
    
    belasting_configs = {
        jaar: laad_tarieven(jaar)
        for jaar in range(2026, 2031)
    }
    cashflow = bereken_huishouden(
        scenario=scenario,
        persoon1=persoon,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2026,
        jaar_tot=2030,
        belasting_configs=belasting_configs,
    )
    
    # Validator moet geen fouten vinden
    resultaat = valideer_cashflow_consistency(cashflow)
    
    # Debug output als er fouten zijn
    if not resultaat.is_geldig:
        print("\n❌ Validatiefouten gevonden:")
        for fout in resultaat.fouten:
            print(f"  • {fout}")
    
    assert resultaat.is_geldig, f"Validator vond fouten: {resultaat.fouten}"
    
    # Controleer dat er daadwerkelijk rendement is gegenereerd
    rendement_totaal = sum(
        sum(m.rente_bruto for m in jr.maanden)
        for jr in cashflow.jaren
    )
    assert rendement_totaal > Decimal("0"), "Er moet rendement zijn gegenereerd"

