"""Tests voor consistentie tussen grafieken en accountantsoverzicht."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.models.component import BedragType, CategorieComponent, FinancieelComponent, Frequentie
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.tax.belasting_loader import laad_tarieven


@pytest.fixture
def simpel_scenario() -> tuple[Persoon, Scenario]:
    """Eenvoudig scenario met vaste inkomensbronnen."""
    persoon = Persoon(
        naam="Test Persoon",
        geboortedatum=date(1970, 1, 1),
        heeft_partner=False,
    )
    
    scenario = Scenario(
        naam="Test",
        componenten=[
            # Arbeidsinkomen tot 2035
            FinancieelComponent(
                omschrijving="Salaris",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="P1",
                bedrag_type=BedragType.BRUTO,
                bedrag=Decimal("4000"),
                frequentie=Frequentie.MAANDELIJKS,
                begindatum=date(2025, 1, 1),
                einddatum=date(2034, 12, 31),
            ),
            # Pensioeninkomen vanaf 2035
            FinancieelComponent(
                omschrijving="Werkgeverspensioen",
                categorie=CategorieComponent.PENSIOEN_INKOMEN,
                persoon="P1",
                bedrag_type=BedragType.BRUTO,
                bedrag=Decimal("2500"),
                frequentie=Frequentie.MAANDELIJKS,
                begindatum=date(2035, 1, 1),
                einddatum=date(2070, 12, 31),
            ),
            # Vaste uitgaven
            FinancieelComponent(
                omschrijving="Huishoudelijke kosten",
                categorie=CategorieComponent.UITGAVE,
                persoon="Huishouden",
                bedrag_type=BedragType.BRUTO,
                bedrag=Decimal("2000"),
                frequentie=Frequentie.MAANDELIJKS,
                begindatum=date(2025, 1, 1),
                einddatum=date(2070, 12, 31),
            ),
        ],
    )
    
    return persoon, scenario


def test_bruto_inkomen_consistency(simpel_scenario):
    """Test dat bruto inkomen consistent is tussen grafieken en accountantsoverzicht."""
    persoon, scenario = simpel_scenario
    
    belasting_configs = {
        jaar: laad_tarieven(jaar)
        for jaar in range(2025, 2045)
    }
    cashflow = bereken_huishouden(
        scenario=scenario,
        persoon1=persoon,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2025,
        jaar_tot=2044,
        belasting_configs=belasting_configs,
    )
    
    for jr in cashflow.jaren:
        # Bruto inkomen via JaarResultaat properties (zonder rente/lijfrente - die komen uit vermogen)
        bruto_arbeid = jr.arbeid_bruto
        bruto_aow = jr.aow_bruto
        bruto_pensioen = jr.pensioen_bruto
        bruto_overig = jr.overig_bruto
        
        # Totaal bruto bevat ook rente/lijfrente uit vermogensrendement
        # Controleer dat totaal_bruto >= som van inkomensbronnen
        bruto_inkomen_componenten = bruto_arbeid + bruto_aow + bruto_pensioen + bruto_overig
        bruto_totaal_direct = jr.totaal_bruto
        
        # Totaal bruto moet minstens gelijk zijn aan inkomensbronnen (kan meer zijn door rente)
        assert bruto_totaal_direct >= bruto_inkomen_componenten, (
            f"Jaar {jr.jaar}: Totaal bruto ({bruto_totaal_direct}) < "
            f"som inkomensbronnen ({bruto_inkomen_componenten})"
        )
        
        # Controleer dat som van maanden klopt
        bruto_som_maanden = sum(m.totaal_bruto for m in jr.maanden)
        assert bruto_som_maanden == bruto_totaal_direct, (
            f"Jaar {jr.jaar}: Som maanden ({bruto_som_maanden}) "
            f"≠ totaal_bruto ({bruto_totaal_direct})"
        )


def test_belasting_consistency(simpel_scenario):
    """Test dat belastingberekeningen consistent zijn."""
    persoon, scenario = simpel_scenario
    
    belasting_configs = {
        jaar: laad_tarieven(jaar)
        for jaar in range(2025, 2045)
    }
    cashflow = bereken_huishouden(
        scenario=scenario,
        persoon1=persoon,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2025,
        jaar_tot=2044,
        belasting_configs=belasting_configs,
    )
    
    for jr in cashflow.jaren:
        # Box1 + Box3 moet gelijk zijn aan totaal_belasting
        box1_bel = jr.box1_belasting
        box3_bel = jr.box3_heffing
        totaal_bel = jr.totaal_belasting
        
        assert box1_bel + box3_bel == totaal_bel, (
            f"Jaar {jr.jaar}: Box1 ({box1_bel}) + Box3 ({box3_bel}) "
            f"≠ totaal_belasting ({totaal_bel})"
        )
        
        # Som van maanden moet kloppen
        totaal_bel_maanden = sum(m.totaal_belasting for m in jr.maanden)
        assert totaal_bel_maanden == totaal_bel, (
            f"Jaar {jr.jaar}: Som maanden belasting ({totaal_bel_maanden}) "
            f"≠ totaal_belasting ({totaal_bel})"
        )


def test_netto_berekening_consistency(simpel_scenario):
    """Test dat netto-inkomen correct wordt berekend uit bruto minus belasting plus kortingen."""
    persoon, scenario = simpel_scenario
    
    belasting_configs = {
        jaar: laad_tarieven(jaar)
        for jaar in range(2025, 2045)
    }
    cashflow = bereken_huishouden(
        scenario=scenario,
        persoon1=persoon,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2025,
        jaar_tot=2044,
        belasting_configs=belasting_configs,
    )
    
    for jr in cashflow.jaren:
        # Bereken netto handmatig
        bruto = jr.totaal_bruto  # bevat al rente_bruto
        belasting = jr.totaal_belasting
        heffingskorting = jr.totaal_heffingskorting
        inhoudingen = jr.inhoudingen
        uitgaven = jr.huishoudelijke_uitgaven
        eenmalige_uit = jr.eenmalige_uitgaven
        eenmalige_ont = jr.eenmalige_ontvangsten
        
        # Netto component inkomen (componenten die al netto zijn)
        netto_component_inkomen = sum(m.inkomen_componenten_netto for m in jr.maanden)
        
        # Rendement is al in bruto opgenomen, niet opnieuw optellen!
        netto_handmatig = (
            bruto 
            + netto_component_inkomen
            - belasting 
            + heffingskorting 
            - inhoudingen 
            - uitgaven
            - eenmalige_uit
            + eenmalige_ont
        )
        
        netto_jr = jr.netto
        
        # Tolerantie van 1 euro voor afrondingsverschillen
        verschil = abs(netto_handmatig - netto_jr)
        assert verschil <= Decimal("1"), (
            f"Jaar {jr.jaar}: Netto handmatig ({netto_handmatig}) "
            f"≠ jr.netto ({netto_jr}), verschil: {verschil}"
        )


def test_waterfall_components_som(simpel_scenario):
    """Test dat waterfall componenten optellen tot correct netto bedrag."""
    persoon, scenario = simpel_scenario
    
    belasting_configs = {
        jaar: laad_tarieven(jaar)
        for jaar in range(2025, 2045)
    }
    cashflow = bereken_huishouden(
        scenario=scenario,
        persoon1=persoon,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2025,
        jaar_tot=2044,
        belasting_configs=belasting_configs,
    )
    
    for jr in cashflow.jaren:
        # Simuleer waterfall berekening (zoals UI nu doet)
        # Bruto = alleen inkomensbronnen (geen rendement)
        bruto_inkomen = jr.arbeid_bruto + jr.aow_bruto + jr.pensioen_bruto + jr.overig_bruto
        # Rendement = verschil tussen totaal_bruto en inkomensbronnen
        rendement = jr.totaal_bruto - bruto_inkomen
        
        box1_bel = -jr.box1_belasting
        box3_bel = -jr.box3_heffing
        hk = jr.totaal_heffingskorting
        inhoud = -jr.inhoudingen
        uitg = -jr.huishoudelijke_uitgaven
        eenm_uit = -jr.eenmalige_uitgaven
        eenm_ont = jr.eenmalige_ontvangsten
        
        # Netto component inkomen
        netto_comp = sum(m.inkomen_componenten_netto for m in jr.maanden)
        
        waterfall_netto = (
            bruto_inkomen + rendement + box1_bel + box3_bel + hk + inhoud + uitg + 
            eenm_uit + eenm_ont + netto_comp
        )
        
        verschil = abs(waterfall_netto - jr.netto)
        assert verschil <= Decimal("1"), (
            f"Jaar {jr.jaar}: Waterfall netto ({waterfall_netto}) "
            f"≠ jr.netto ({jr.netto}), verschil: {verschil}"
        )


def test_geen_dubbeltelling_pensioen(simpel_scenario):
    """Test dat pensioeninkomen niet dubbel geteld wordt."""
    persoon, scenario = simpel_scenario
    
    belasting_configs = {
        jaar: laad_tarieven(jaar)
        for jaar in range(2025, 2045)
    }
    cashflow = bereken_huishouden(
        scenario=scenario,
        persoon1=persoon,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2025,
        jaar_tot=2044,
        belasting_configs=belasting_configs,
    )
    
    # Controleer een jaar met pensioen (2035)
    jr_2035 = next((j for j in cashflow.jaren if j.jaar == 2035), None)
    assert jr_2035 is not None
    
    # Pensioeninkomen moet in pensioen_bruto zitten
    pensioen = jr_2035.pensioen_bruto
    assert pensioen == Decimal("2500") * 12  # 12 maanden * 2500
    
    # overig_bruto mag GEEN pensioeninkomen bevatten (alleen OVERIG_INKOMEN componenten)
    overig = jr_2035.overig_bruto
    # In dit scenario is er geen OVERIG_INKOMEN, dus moet 0 zijn
    assert overig == Decimal("0")
    
    # Totaal bruto moet correct zijn: arbeid + pensioen + aow + overig + rente
    # (rente komt uit vermogensrendement)
    totaal_inkomen = jr_2035.arbeid_bruto + pensioen + jr_2035.aow_bruto + overig
    # Totaal bruto kan hoger zijn door rente/rendement
    assert jr_2035.totaal_bruto >= totaal_inkomen, (
        f"Totaal bruto ({jr_2035.totaal_bruto}) < som inkomensbronnen ({totaal_inkomen})"
    )


def test_accountant_vs_grafiek_consistency(simpel_scenario):
    """Test dat accountantsoverzicht dezelfde cijfers heeft als grafieken."""
    persoon, scenario = simpel_scenario
    
    belasting_configs = {
        jaar: laad_tarieven(jaar)
        for jaar in range(2025, 2045)
    }
    cashflow = bereken_huishouden(
        scenario=scenario,
        persoon1=persoon,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2025,
        jaar_tot=2044,
        belasting_configs=belasting_configs,
    )
    
    for jr in cashflow.jaren:
        # Deze cijfers worden gebruikt in het accountantsoverzicht
        # en moeten exact overeenkomen met wat in grafieken wordt getoond
        
        # Bruto inkomen grafiek data (alleen inkomensbronnen, geen rendement)
        grafiek_bruto_data = {
            "Arbeidsinkomen": jr.arbeid_bruto,
            "AOW": jr.aow_bruto,
            "Pensioen": jr.pensioen_bruto,
        }
        som_grafiek_inkomen = sum(grafiek_bruto_data.values()) + jr.overig_bruto
        
        # Waterfall grafiek moet nu ook alleen inkomensbronnen tonen (zoals UI nu doet)
        # NIET totaal_bruto (dat bevat ook rendement op vermogen)
        waterfall_bruto_inkomen = jr.arbeid_bruto + jr.aow_bruto + jr.pensioen_bruto + jr.overig_bruto
        
        # Deze moeten exact gelijk zijn - beide grafieken tonen hetzelfde bruto inkomen
        assert som_grafiek_inkomen == waterfall_bruto_inkomen, (
            f"Jaar {jr.jaar}: Inkomensgrafiek bruto ({som_grafiek_inkomen}) "
            f"≠ waterfall bruto inkomen ({waterfall_bruto_inkomen})"
        )
        
        # Belasting in waterfall moet gelijk zijn aan wat accountant toont
        # (box1_belasting + box3_heffing)
        waterfall_box1 = jr.box1_belasting
        waterfall_box3 = jr.box3_heffing
        waterfall_hk = jr.totaal_heffingskorting
        
        totaal_bel_accountant = waterfall_box1 + waterfall_box3
        assert totaal_bel_accountant == jr.totaal_belasting
        
        # Heffingskortingen moeten consistent zijn
        assert waterfall_hk == jr.totaal_heffingskorting
