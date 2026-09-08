"""Scenario-recept voor doorwerken en vrijwillige pensioenopbouw."""
from datetime import date
from decimal import Decimal

import pytest
import json
from pathlib import Path

from pensioen.models.scenario import Scenario
from pensioen.models.component import FinancieelComponent
from pensioen.calculations.pensioenopbouw_simulator import OpbouwKeuze, bouw_opbouwscenarios


def base() -> Scenario:
    return Scenario(naam='Basis',componenten=[
        FinancieelComponent(omschrijving='Werk',categorie='arbeidsinkomen',persoon='P1',bedrag='3000'),
        FinancieelComponent(omschrijving='Pensioen',categorie='pensioen_inkomen',persoon='P1',bedrag='1000'),
        FinancieelComponent(omschrijving='Partner',categorie='arbeidsinkomen',persoon='P2',bedrag='2000'),
    ])


def choice(**changes) -> OpbouwKeuze:
    fixture=json.loads(Path('tests/fixtures/belasting_testcases/normalized/tc_2025_018_normalized.json').read_text())
    data=fixture['metadata']['regressies_opbouw']['keuze']
    return OpbouwKeuze(**(data|changes))


@pytest.mark.bouwsteen
def test_variants_replace_only_selected_pension_and_preserve_partner() -> None:
    original=base()
    scenarios=bouw_opbouwscenarios(original,choice())
    assert len(scenarios)==3
    assert [s.componenten[0].einddatum for s in scenarios]==[date(2025,12,31),date(2025,3,31),date(2025,3,31)]
    assert [s.componenten[1].bedrag for s in scenarios]==[Decimal('1200'),Decimal('1000'),Decimal('1200')]
    assert all(s.componenten[2].einddatum is None for s in scenarios)
    premium=scenarios[2].componenten[-1]
    assert premium.bedrag==800
    assert premium.begindatum==date(2025,4,1)
    assert premium.einddatum==date(2025,12,31)
    assert premium.categorie.value=='uitgave'
    assert original.componenten[0].einddatum is None
    assert len(original.componenten)==3


@pytest.mark.bouwsteen
@pytest.mark.parametrize('changes',[
    {'premie_per_maand':'-1'}, {'premie_per_maand':'NaN'},
    {'laatste_werkdag':'2026-01-01'}, {'doorwerken_tot':'2025-01-01'},
    {'modus':'uitvoerder'},
])
def test_invalid_or_unconfirmed_configuration_is_rejected(changes) -> None:
    with pytest.raises(ValueError): choice(**changes)


@pytest.mark.bouwsteen
def test_partial_months_are_explicitly_rejected() -> None:
    with pytest.raises(ValueError,match='hele maanden'):
        choice(laatste_werkdag='2025-03-15')


@pytest.mark.engine
def test_api_counts_premium_once_and_reports_only_engine_cashflows() -> None:
    from fastapi.testclient import TestClient
    from pensioen.api.main import app
    scenario=base()
    scenario.box3_meenemen=False
    scenario.rendement_pct=Decimal('0')
    response=TestClient(app).post('/api/v1/simulaties/pensioenopbouw',json={
        'berekening':{'scenario':scenario.model_dump(mode='json'),
                      'persoon1':{'naam':'Test','geboortedatum':'1990-01-01'},'persoon2':None,
                      'jaar_van':2025,'jaar_tot':2030},
        'keuze':choice().model_dump(mode='json'),
    })
    assert response.status_code==200,response.text
    data=response.json()
    assert Decimal(data['opbouw']['totale_premie'])==Decimal('7200')
    assert len(data['vergelijking']['scenario_resultaten'])==3
    zonder,met=data['vergelijking']['scenario_resultaten'][1:]
    ms=lambda s:[m for j in s['cashflow']['jaren'] for m in j['maanden']]
    assert sum(Decimal(m['huishoudelijke_uitgaven'])-Decimal(z['huishoudelijke_uitgaven']) for m,z in zip(ms(met),ms(zonder)))==Decimal('7200')
    assert all(Decimal(m['huishoudelijke_uitgaven'])==0 for m in ms(met) if m['jaar']>2025)
    assert sum(Decimal(m['belasting_p1']) for m in ms(met) if m['jaar']==2025)==sum(Decimal(m['belasting_p1']) for m in ms(zonder) if m['jaar']==2025)
    assert 'geen belastingaftrek' in ' '.join(data['aannames'])
    assert data['keuze']['modus']=='aannames'


@pytest.mark.bouwsteen
def test_breakeven_stays_nonnegative_and_never_claims_zero_premium_recovery() -> None:
    from types import SimpleNamespace
    from pensioen.models.cashflow import HuishoudCashflow,JaarResultaat,MaandResultaat
    from pensioen.calculations.pensioenopbouw_simulator import bouw_opbouwuitkomst
    def flow(values,premiums):
        return SimpleNamespace(cashflow=HuishoudCashflow(scenario_naam='T',jaren=[
            JaarResultaat(jaar=2025,maanden=[MaandResultaat(jaar=2025,maand=12,huishoudelijke_uitgaven=Decimal(premiums))]),
            JaarResultaat(jaar=2026,maanden=[MaandResultaat(jaar=2026,maand=i+1,inkomen_componenten_netto=Decimal(v)) for i,v in enumerate(values)])]))
    # Eerst herstel, dan terugval: alleen de latere blijvende kruising telt.
    zero=flow(['0','0','0'],'0')
    comparison=SimpleNamespace(scenario_resultaten=[zero,zero,flow(['100','-50','100'],'100')])
    result=bouw_opbouwuitkomst(comparison,choice(),date(1960,3,15))
    assert result['omslag_maand']=='2026-03'
    assert result['omslag_leeftijd']==66
    comparison.scenario_resultaten[2]=flow(['0','0','0'],'0')
    assert bouw_opbouwuitkomst(comparison,choice(premie_per_maand='0'),date(1960,1,1))['omslag_maand'] is None
