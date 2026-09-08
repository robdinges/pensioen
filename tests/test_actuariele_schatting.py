"""Actuariële gelijkwaardigheid en afzonderlijke opbouwkorting."""
from datetime import date
from decimal import Decimal

import pytest

from pensioen.calculations.actuariele_schatting import waardefactoren, schat_regeling


@pytest.mark.bouwsteen
def test_same_start_date_has_no_early_retirement_discount() -> None:
    f=waardefactoren(date(1960,1,1),date(2027,1,1),date(2027,1,1),Decimal('3'),Decimal('0'))
    assert f['vervroegingsfactor']==Decimal('1')
    assert f['premie_factor']==0


@pytest.mark.bouwsteen
def test_present_values_match_and_reduction_is_not_a_fixed_percentage() -> None:
    f=waardefactoren(date(1960,1,1),date(2025,1,1),date(2027,1,1),Decimal('3'),Decimal('0'))
    assert Decimal('0.7')<f['vervroegingsfactor']<1
    assert abs(f['direct_factor']*f['vervroegingsfactor']-f['uitgesteld_factor'])<Decimal('.00000001')
    result=schat_regeling(Decimal('1000'),date(1960,1,1),date(2025,1,1),date(2027,1,1),Decimal('3'),Decimal('0'),25,True,Decimal('10'))
    assert result['opbouwfactor']==Decimal(40)/Decimal(42)
    assert result['direct_bruto_maand']<result['wachten_bruto_maand']<1000
    assert result['premie_bruto_maand']>0


@pytest.mark.bouwsteen
def test_paid_up_pension_is_not_reduced_for_missing_contributions() -> None:
    result=schat_regeling(Decimal('1000'),date(1960,1,1),date(2025,1,1),date(2027,1,1),Decimal('3'),Decimal('0'),25,False,Decimal('10'))
    assert result['wachten_bruto_maand']==1000
    assert result['premie_bruto_maand']==0
    assert result['direct_bruto_maand']<1000


@pytest.mark.engine
def test_api_uses_existing_scenario_dates_and_generates_three_variants() -> None:
    from fastapi.testclient import TestClient
    from pensioen.api.main import app
    from pensioen.models.scenario import Scenario
    from pensioen.models.component import FinancieelComponent
    scenario=Scenario(naam='Stop op 65',box3_meenemen=False,componenten=[
        FinancieelComponent(omschrijving='Loon',categorie='arbeidsinkomen',persoon='P1',bedrag='2000',einddatum=date(2024,12,31)),
        FinancieelComponent(omschrijving='Fonds',categorie='pensioen_inkomen',persoon='P1',bedrag='12000',frequentie='jaarlijks',begindatum=date(2027,1,1)),
    ])
    response=TestClient(app).post('/api/v1/simulaties/actuarieel',json={'berekening':{
        'scenario':scenario.model_dump(mode='json'),'persoon1':{'naam':'Test','geboortedatum':'1960-01-01'},
        'persoon2':None,'jaar_van':2025,'jaar_tot':2030}})
    assert response.status_code==200,response.text
    data=response.json(); r=data['raming']
    assert r['vanaf_stoppen']=='2025-01-01'
    assert Decimal(r['totaal_direct_bruto_maand'])<Decimal(r['totaal_wachten_bruto_maand'])<Decimal('1000')
    assert Decimal(r['totaal_doorbetalen_bruto_maand'])==1000
    assert len(data['vergelijking']['scenario_resultaten'])==3
    direct,wachten,met=data['vergelijking']['scenario_resultaten']
    first=lambda s:s['cashflow']['jaren'][0]['maanden'][0]
    assert Decimal(first(direct)['pensioen_p1_bruto'])>0
    assert Decimal(first(wachten)['pensioen_p1_bruto'])==0
    assert Decimal(first(met)['huishoudelijke_uitgaven'])==Decimal(r['premie_per_maand_bij_start'])
    assert Decimal(r['totale_premie'])==Decimal(r['premie_per_maand_bij_start'])*24


@pytest.mark.bouwsteen
def test_normalized_regression_preserves_accrual_and_premium_period() -> None:
    import json
    from pathlib import Path
    fixture = json.loads((Path(__file__).parent / 'fixtures/belasting_testcases/normalized/tc_2025_018_normalized.json').read_text())
    case = fixture['metadata']['regressies_actuarieel']
    from pensioen.calculations.actuariele_schatting import maanden_tussen
    stop, normaal = date.fromisoformat(case['stop']), date.fromisoformat(case['normaal'])
    result = schat_regeling(Decimal(case['bruto_maand']), date.fromisoformat(case['geboortedatum']),
                           stop, normaal, Decimal('3'), Decimal('0'), 25, True, Decimal('10'))
    assert result['opbouwfactor'] == Decimal(case['opbouw_maanden']) / Decimal(case['totaal_maanden'])
    assert maanden_tussen(stop, normaal) == case['premiemaanden']


@pytest.mark.bouwsteen
def test_zero_interest_and_no_cost_loading_remain_valid() -> None:
    args = (Decimal('1000'), date(1960, 1, 1), date(2025, 1, 1), date(2027, 1, 1),
            Decimal('0'), Decimal('0'), 25, True)
    bare = schat_regeling(*args, Decimal('0'))
    loaded = schat_regeling(*args, Decimal('10'))
    assert 0 < bare['direct_bruto_maand'] < bare['wachten_bruto_maand']
    assert abs(loaded['premie_bruto_maand'] - bare['premie_bruto_maand'] * Decimal('1.1')) < Decimal('.02')


@pytest.mark.bouwsteen
def test_adapter_preserves_partner_and_base_and_staggers_premiums() -> None:
    from pensioen.calculations.actuariele_scenarios import bouw_actuariele_scenarios
    from pensioen.models.scenario import Scenario
    from pensioen.models.persoon import Persoon
    from pensioen.models.opbouw_simulatie import ActuarieleKeuze
    basis = Scenario(naam='Test', componenten=[
        {'omschrijving': 'Loon', 'categorie': 'arbeidsinkomen', 'persoon': 'P1', 'bedrag': '2000', 'einddatum': '2024-12-31'},
        {'omschrijving': 'Fonds A', 'categorie': 'pensioen_inkomen', 'persoon': 'P1', 'bedrag': '1000', 'begindatum': '2027-01-01'},
        {'omschrijving': 'Fonds B', 'categorie': 'pensioen_inkomen', 'persoon': 'P1', 'bedrag': '500', 'begindatum': '2028-01-01'},
        {'omschrijving': 'Partner', 'categorie': 'pensioen_inkomen', 'persoon': 'P2', 'bedrag': '900', 'begindatum': '2027-01-01'},
    ])
    original = basis.model_dump()
    persoon = Persoon(naam='Test', geboortedatum=date(1960, 1, 1))
    scenarios, raming = bouw_actuariele_scenarios(basis, persoon, ActuarieleKeuze(), 2025, 2030)
    assert basis.model_dump() == original
    assert all(s.componenten[3] == basis.componenten[3] for s in scenarios)
    assert [c.einddatum for c in scenarios[2].componenten[4:]] == [date(2026, 12, 31), date(2027, 12, 31)]
    assert len(raming['regelingen']) == 2
    with pytest.raises(ValueError, match='hoort niet'):
        bouw_actuariele_scenarios(basis, persoon, ActuarieleKeuze(reeds_opgebouwde_posten=[3]), 2025, 2030)
    basis.componenten[0].einddatum = None
    with pytest.raises(ValueError, match='einddatum'):
        bouw_actuariele_scenarios(basis, persoon, ActuarieleKeuze(), 2025, 2030)


@pytest.mark.parametrize('afwijking,reden', [
    ({'einddatum': '2030-12-31'}, 'Einddatum'),
    ({'waarde_periodes': [{'bedrag': '500', 'startdatum': '2027-01-01'}]}, 'waardeperiode'),
    ({'bedrag_type': 'netto'}, 'netto'),
    ({'frequentie': 'eenmalig'}, 'Eenmalige'),
    ({'begindatum': None}, 'Ingangsdatum'),
])
@pytest.mark.engine
def test_unsupported_pension_does_not_hide_other_estimates(afwijking: dict, reden: str) -> None:
    from fastapi.testclient import TestClient
    from pensioen.api.main import app
    from pensioen.models.scenario import Scenario
    problem = {'omschrijving': 'Afwijkende regeling', 'categorie': 'pensioen_inkomen',
               'persoon': 'P1', 'bedrag': '500', 'begindatum': '2027-01-01', **afwijking}
    scenario = Scenario(naam='Deelraming', componenten=[
        {'omschrijving': 'Loon', 'categorie': 'arbeidsinkomen', 'persoon': 'P1', 'bedrag': '2000', 'einddatum': '2024-12-31'},
        problem,
        {'omschrijving': 'Geldige regeling', 'categorie': 'pensioen_inkomen', 'persoon': 'P1', 'bedrag': '1000', 'begindatum': '2027-01-01'},
        {'omschrijving': 'Lopende regeling', 'categorie': 'pensioen_inkomen', 'persoon': 'P1', 'bedrag': '100', 'begindatum': '2024-01-01'},
    ])
    response = TestClient(app).post('/api/v1/simulaties/actuarieel', json={'berekening': {
        'scenario': scenario.model_dump(mode='json'), 'persoon1': {'naam': 'Test', 'geboortedatum': '1960-01-01'},
        'jaar_van': 2025, 'jaar_tot': 2030}})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['vergelijking'] is None
    assert data['raming']['volledig'] is False
    assert [r['naam'] for r in data['raming']['regelingen']] == ['Geldige regeling']
    posten = data['raming']['posten']
    assert [p['status'] for p in posten] == ['niet_berekend', 'berekend', 'ongewijzigd']
    assert reden in posten[0]['reden']
    assert Decimal(data['raming']['regelingen'][0]['direct_bruto_maand']) > 0
