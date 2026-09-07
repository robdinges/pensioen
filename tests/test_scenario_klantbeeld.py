"""Begrijpelijke KPI's komen uit maandoutput en gebruiken één vergelijkingsperiode."""
from datetime import date
from decimal import Decimal

import pytest
import json
from pathlib import Path

from pensioen.calculations.scenario_klantbeeld import bouw_klantbeeld, vergelijkingsperiode
from pensioen.models.cashflow import HuishoudCashflow, JaarResultaat, MaandResultaat
from pensioen.models.component import FinancieelComponent
from pensioen.models.scenario import Scenario


def employment(end: date | None, person: str = 'P1') -> FinancieelComponent:
    return FinancieelComponent(omschrijving='Werk',categorie='arbeidsinkomen',persoon=person,
                              bedrag=Decimal('1000'),einddatum=end)


@pytest.mark.bouwsteen
def test_common_period_starts_after_latest_partner_stop() -> None:
    scenarios = [Scenario(naam='A',componenten=[employment(date(2025,3,15))]),
                 Scenario(naam='B',componenten=[employment(date(2025,6,30)),employment(date(2025,8,1),'P2')])]
    start, end, after = vergelijkingsperiode(scenarios,2025,2026)
    assert (start,end,after)==(date(2025,9,1),date(2026,12,31),True)
    scenarios[0].componenten.append(employment(None))
    assert vergelijkingsperiode(scenarios,2025,2026)==(date(2025,1,1),date(2026,12,31),False)


@pytest.mark.bouwsteen
def test_average_is_not_median_and_buffer_uses_months() -> None:
    fixture=json.loads(Path('tests/fixtures/belasting_testcases/normalized/tc_2025_018_normalized.json').read_text())['metadata']['regressies_scenariokaarten']
    months=[MaandResultaat(jaar=2025,maand=i+1,inkomen_componenten_netto=Decimal(amount),
                          vermogen_einde_maand=Decimal(balance))
            for i,(amount,balance) in enumerate((row['over'],row['saldo']) for row in fixture['maanden'])]
    flow=HuishoudCashflow(scenario_naam='Test',jaren=[JaarResultaat(jaar=2025,maanden=months)])
    result=bouw_klantbeeld(flow,date(2025,1,1),date(2025,12,31),date(1945,1,1))
    assert result['gemiddeld_over_per_maand']==Decimal(fixture['gemiddelde'])
    assert result['laagste_buffer']==Decimal(fixture['laagste_buffer'])
    assert result['laagste_buffer_maand']=='2025-02'
    assert result['jaren_interen']==0
    assert result['jaren_negatief_vermogen']==1
    assert result['jaarregels'][0]['over_na_uitgaven']==Decimal('900')
    assert result['vermogen_op_80']==Decimal('2000')


@pytest.mark.bouwsteen
def test_no_post_stop_months_is_unknown_not_zero() -> None:
    flow=HuishoudCashflow(scenario_naam='Leeg',jaren=[])
    result=bouw_klantbeeld(flow,date(2027,1,1),date(2026,12,31),date(1990,1,1))
    assert result['gemiddeld_over_per_maand'] is None
    assert result['laagste_buffer'] is None
    assert result['vermogen_op_80'] is None


@pytest.mark.engine
def test_api_average_after_stopping_and_deltas_use_same_months() -> None:
    from fastapi.testclient import TestClient
    from pensioen.api.main import app
    scenarios=[]
    for name, stop, income in [('A',date(2025,3,31),'1000'),('B',date(2025,6,30),'1200'),('C',date(2025,5,31),'900')]:
        scenarios.append(Scenario(naam=name,box3_meenemen=False,componenten=[
            employment(stop),
            FinancieelComponent(omschrijving='Netto uitkering',categorie='overig_inkomen',persoon='P1',
                                bedrag=Decimal(income),bedrag_type='netto',begindatum=date(2025,7,1)),
            FinancieelComponent(omschrijving='Uitgaven',categorie='uitgave',persoon='Huishouden',
                                bedrag=Decimal('500'),bedrag_type='netto'),
        ]).model_dump(mode='json'))
    response=TestClient(app).post('/api/v1/vergelijkingen',json={
        'scenarios':scenarios,'persoon1':{'naam':'Test','geboortedatum':'1990-01-01'},
        'persoon2':None,'records1':[],'records2':[],'jaar_van':2025,'jaar_tot':2025,
    })
    assert response.status_code==200
    comparison=response.json()['vergelijking']
    assert comparison['klantvergelijking']['gemiddelde_van']=='2025-07-01'
    for row, average, delta in zip(comparison['scenario_resultaten'],['500','700','400'],['0','200','-100']):
        kpi=row['klantbeeld']
        assert kpi['aantal_maanden_gemiddelde']==6
        assert Decimal(kpi['gemiddeld_over_per_maand'])==Decimal(average)
        assert Decimal(kpi['verschil_gemiddeld_over_per_maand'])==Decimal(delta)
        assert kpi['vermogen_op_80'] is None
        assert kpi['jaren_interen']==sum(Decimal(r['over_na_uitgaven'])<0 for r in kpi['jaarregels'])
        expected=min(Decimal(m['vermogen_einde_maand']) for j in row['cashflow']['jaren'] for m in j['maanden'])
        assert Decimal(kpi['laagste_buffer'])==expected


@pytest.mark.bouwsteen
def test_last_stop_beyond_horizon_does_not_invent_an_average() -> None:
    scenario=Scenario(naam='Later',componenten=[employment(date(2026,12,31))])
    assert vergelijkingsperiode([scenario],2025,2025)==(date(2027,1,1),date(2025,12,31),True)
