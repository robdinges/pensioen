"""Test grafiek consistentie en scenario kopiëren."""
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
from pensioen.tax.belasting_loader import laad_tarieven_bereik


def test_grafiek_toont_alle_inkomenscategorieen():
    """
    Regression test: grafiek moet ALLE inkomensbronnen tonen.
    
    Bug: De grafiek "Bruto inkomen per jaar" toonde alleen Arbeidsinkomen, AOW, 
    en Pensioen, maar niet "Overig inkomen". Dit zorgde voor verschil tussen 
    de grafiek (105k) en de waterfall chart (114k) wanneer er een overig inkomen 
    component was van 9k.
    
    Deze test zorgt ervoor dat overig_bruto in de cashflow resultaten wordt 
    meegenomen en dat het verschil tussen de som van alle bronnen en totaal_bruto 
    alleen uit rendement bestaat.
    """
    # Setup
    persoon1 = Persoon(naam="Rob", geboortedatum=date(1963, 1, 13), heeft_partner=False)
    
    scenario = Scenario(
        naam="Test",
        componenten=[
            FinancieelComponent(
                omschrijving="Salaris",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="P1",
                bedrag=Decimal("85000"),
                bedrag_type=BedragType.BRUTO,
                frequentie=Frequentie.JAARLIJKS,
                begindatum=date(2026, 1, 1),
                einddatum=date(2030, 1, 13),
            ),
            FinancieelComponent(
                omschrijving="WIA uitkering",
                categorie=CategorieComponent.OVERIG_INKOMEN,
                persoon="P1",
                bedrag=Decimal("9000"),
                bedrag_type=BedragType.BRUTO,
                frequentie=Frequentie.JAARLIJKS,
                einddatum=date(2033, 3, 14),
            ),
        ],
    )
    
    configs = laad_tarieven_bereik(2026, 2030)
    
    # Execute
    cashflow = bereken_huishouden(
        scenario=scenario,
        persoon1=persoon1,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2026,
        jaar_tot=2030,
        belasting_configs=configs,
    )
    
    # Verify: voor elk jaar moet gelden:
    # totaal_bruto = inkomen_bruto + rendement_bruto
    # Dit test dat de nieuwe centrale properties correct werken
    for jr in cashflow.jaren:
        # Test centrale property inkomen_bruto
        inkomen_verwacht = jr.arbeid_bruto + jr.aow_bruto + jr.pensioen_bruto + jr.overig_bruto
        assert jr.inkomen_bruto == inkomen_verwacht, (
            f"Jaar {jr.jaar}: inkomen_bruto property incorrect"
        )
        
        # Test centrale property rendement_bruto
        rendement_verwacht = sum(m.rente_bruto for m in jr.maanden)
        assert float(jr.rendement_bruto) == pytest.approx(float(rendement_verwacht), abs=0.01), (
            f"Jaar {jr.jaar}: rendement_bruto property incorrect"
        )
        
        # Test dat totaal = inkomen + rendement
        assert float(jr.totaal_bruto) == pytest.approx(float(jr.inkomen_bruto + jr.rendement_bruto), abs=0.01), (
            f"Jaar {jr.jaar}: totaal_bruto != inkomen_bruto + rendement_bruto"
        )
        
        # Verify dat overig inkomen daadwerkelijk wordt meegenomen
        if jr.jaar <= 2033:  # WIA loopt tot 2033
            assert jr.overig_bruto > Decimal("0"), (
                f"Jaar {jr.jaar}: overig_bruto zou > 0 moeten zijn (WIA uitkering)"
            )
        
        # Test inkomen_bronnen dict property
        bronnen = jr.inkomen_bronnen
        assert set(bronnen.keys()) == {"Arbeidsinkomen", "AOW", "Pensioen", "Overig inkomen"}
        assert bronnen["Arbeidsinkomen"] == jr.arbeid_bruto
        assert bronnen["AOW"] == jr.aow_bruto
        assert bronnen["Pensioen"] == jr.pensioen_bruto
        assert bronnen["Overig inkomen"] == jr.overig_bruto


def test_scenario_kopie_behoudt_persoon_velden():
    """
    Test dat scenario.model_copy(deep=True) de persoon velden correct kopieert.
    
    Bug: Bij het kopiëren van een scenario zou de persoon-verdeling verloren kunnen 
    gaan, waardoor alle componenten bij P1 terechtkomen in plaats van correct 
    verdeeld over P1/P2.
    """
    # Setup: scenario met P1 en P2 componenten
    origineel = Scenario(
        naam="Origineel",
        componenten=[
            FinancieelComponent(
                omschrijving="Salaris P1",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="P1",
                bedrag=Decimal("85000"),
                bedrag_type=BedragType.BRUTO,
                frequentie=Frequentie.JAARLIJKS,
            ),
            FinancieelComponent(
                omschrijving="Salaris P2",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="P2",
                bedrag=Decimal("29000"),
                bedrag_type=BedragType.BRUTO,
                frequentie=Frequentie.JAARLIJKS,
            ),
            FinancieelComponent(
                omschrijving="Uitkering P1",
                categorie=CategorieComponent.OVERIG_INKOMEN,
                persoon="P1",
                bedrag=Decimal("9000"),
                bedrag_type=BedragType.BRUTO,
                frequentie=Frequentie.JAARLIJKS,
            ),
        ],
    )
    
    # Execute: kopieer het scenario (zoals pagina_scenario.py doet)
    kopie = origineel.model_copy(deep=True)
    kopie.naam = "Kopie"
    
    # Verify: persoon velden moeten identiek zijn
    assert len(kopie.componenten) == 3
    assert kopie.componenten[0].persoon == "P1"
    assert kopie.componenten[0].omschrijving == "Salaris P1"
    assert kopie.componenten[1].persoon == "P2"
    assert kopie.componenten[1].omschrijving == "Salaris P2"
    assert kopie.componenten[2].persoon == "P1"
    assert kopie.componenten[2].omschrijving == "Uitkering P1"
    
    # Verify: mutatie van kopie heeft geen effect op origineel (deep copy)
    kopie.componenten[0].persoon = "Huishouden"
    assert origineel.componenten[0].persoon == "P1"


def test_accountant_p1_p2_breakdown():
    """
    Test dat accountantsoverzicht correct P1/P2 breakdown toont.
    
    Verificatie dat _component_som_maand correct filtert op persoon en dat
    de accountant detail tabel P1 en P2 kolommen correct toont wanneer beide
    personen inkomen hebben.
    """
    from pensioen.ui.pagina_accountant import _component_som_maand
    
    scenario = Scenario(
        naam="Test",
        componenten=[
            FinancieelComponent(
                omschrijving="Salaris P1",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="P1",
                bedrag=Decimal("7000"),  # €7000/maand
                bedrag_type=BedragType.BRUTO,
                frequentie=Frequentie.MAANDELIJKS,
            ),
            FinancieelComponent(
                omschrijving="Salaris P2",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="P2",
                bedrag=Decimal("2500"),  # €2500/maand
                bedrag_type=BedragType.BRUTO,
                frequentie=Frequentie.MAANDELIJKS,
            ),
            FinancieelComponent(
                omschrijving="WIA P1",
                categorie=CategorieComponent.OVERIG_INKOMEN,
                persoon="P1",
                bedrag=Decimal("750"),  # €750/maand
                bedrag_type=BedragType.BRUTO,
                frequentie=Frequentie.MAANDELIJKS,
            ),
        ],
    )
    
    # Verify P1 arbeidsinkomen
    arbeid_p1 = _component_som_maand(
        scenario, CategorieComponent.ARBEIDSINKOMEN, "P1", 2026, 1, BedragType.BRUTO
    )
    assert arbeid_p1 == Decimal("7000")
    
    # Verify P2 arbeidsinkomen
    arbeid_p2 = _component_som_maand(
        scenario, CategorieComponent.ARBEIDSINKOMEN, "P2", 2026, 1, BedragType.BRUTO
    )
    assert arbeid_p2 == Decimal("2500")
    
    # Verify P1 overig inkomen
    overig_p1 = _component_som_maand(
        scenario, CategorieComponent.OVERIG_INKOMEN, "P1", 2026, 1, BedragType.BRUTO
    )
    assert overig_p1 == Decimal("750")
    
    # Verify P2 overig inkomen (moet 0 zijn)
    overig_p2 = _component_som_maand(
        scenario, CategorieComponent.OVERIG_INKOMEN, "P2", 2026, 1, BedragType.BRUTO
    )
    assert overig_p2 == Decimal("0")
    
    # Verify totaal zonder persoon filter
    arbeid_totaal = _component_som_maand(
        scenario, CategorieComponent.ARBEIDSINKOMEN, None, 2026, 1, BedragType.BRUTO
    )
    assert arbeid_totaal == Decimal("9500")  # 7000 + 2500
