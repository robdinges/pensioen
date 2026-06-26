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
from pensioen.models.vermogensitem import VermogensItem, VermogensType
from pensioen.tax.belasting_loader import laad_tarieven_bereik
from pensioen.tax.eigen_woning_engine import EigenWoningResultaat


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


def test_accountant_eigen_woning_blok_bij_effect_partner2():
    """Eigen woning sectie moet zichtbaar zijn als alleen partner 2 effect heeft."""
    from pensioen.ui.pagina_accountant import _heeft_eigen_woning_effect

    partner1 = EigenWoningResultaat(
        eigenwoningforfait=Decimal("0"),
        aftrekbare_hypotheekrente=Decimal("0"),
        overige_aftrekbare_kosten=Decimal("0"),
        totaal_aftrek=Decimal("0"),
        saldo_eigen_woning=Decimal("0"),
        hillen_correctie=Decimal("0"),
        box1_mutatie=Decimal("0"),
        tariefsaanpassing=Decimal("0"),
        box3_bezittingen=Decimal("0"),
        box3_schulden=Decimal("0"),
    )
    partner2 = EigenWoningResultaat(
        eigenwoningforfait=Decimal("875"),
        aftrekbare_hypotheekrente=Decimal("3000"),
        overige_aftrekbare_kosten=Decimal("0"),
        totaal_aftrek=Decimal("3000"),
        saldo_eigen_woning=Decimal("-2125"),
        hillen_correctie=Decimal("0"),
        box1_mutatie=Decimal("-2125"),
        tariefsaanpassing=Decimal("0"),
        box3_bezittingen=Decimal("0"),
        box3_schulden=Decimal("0"),
    )

    assert not _heeft_eigen_woning_effect(partner1)
    assert _heeft_eigen_woning_effect(partner2)


def test_accountant_gebruikt_vermogensitem_bron_voor_eigen_woning() -> None:
    """Accountantdetail moet de vermogensitem-bron gebruiken voor eigen woning en hypotheek."""
    from pensioen.tax.belasting_loader import laad_tarieven
    from pensioen.ui.pagina_accountant import _bereken_jaar_detail

    scenario = Scenario(
        naam="Eigen woning",
        vermogensitems=[
            VermogensItem(
                omschrijving="Woning",
                type=VermogensType.EIGEN_WONING,
                persoon="Huishouden",
                aanschafwaarde=Decimal("500000"),
                woz_waarde=Decimal("500000"),
                box3_belast=False,
            ),
            VermogensItem(
                omschrijving="Hypotheek",
                type=VermogensType.HYPOTHEEK,
                persoon="Huishouden",
                aanschafwaarde=Decimal("150000"),
                is_primaire_woning=True,
                hypotheekrente_pct=Decimal("4.0"),
                einddatum_aftrekbaarheid=date(2056, 1, 1),
                box3_belast=False,
            ),
        ],
    )
    persoon1 = Persoon(naam="P1", geboortedatum=date(1980, 1, 1), heeft_partner=True)
    persoon2 = Persoon(naam="P2", geboortedatum=date(1982, 1, 1), heeft_partner=True)
    config, aanname = laad_tarieven(2026)

    detail = _bereken_jaar_detail(
        jaar=2026,
        persoon1=persoon1,
        persoon2=persoon2,
        records1=[],
        records2=[],
        scenario=scenario,
        config=config,
        aanname=aanname,
        saldo_begin_jaar=Decimal("0"),
    )

    assert detail["ew_woz_waarde"] == Decimal("500000")
    assert detail["ew_betaalde_hypotheekrente"] == Decimal("6000")
    assert detail["ew_p1"].eigenwoningforfait == Decimal("875.00")
    assert detail["ew_p1"].aftrekbare_hypotheekrente == Decimal("3000.00")
    assert detail["ew_p2"].eigenwoningforfait == Decimal("875.00")
    assert detail["ew_p2"].aftrekbare_hypotheekrente == Decimal("3000.00")
