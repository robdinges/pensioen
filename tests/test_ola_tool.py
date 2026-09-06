"""Contracttests voor OLA-invoer, bronvastlegging en vergelijking (offline)."""
from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from tools.ola.__main__ import controleer_bewijs, main
from tools.ola.browser import controleer_recept, stap_waarde
from tools.ola.catalogus import CatalogusParser
from tools.ola.modellen import Case, Locator, Stap, case_hash, controleer_url, laad_case
from tools.ola.vergelijking import engine_resultaat, lees_euro, vergelijk


@pytest.fixture
def case() -> Case:
    return laad_case(Path('config/ola/cases/alleen_werkend.json'))


def bron(case: Case, totaal: str = '1234') -> dict:
    # Testdubbel; dit zijn geen Belastingdienst-referentiewaarden.
    return {'jaar': 2025, 'status': 'vastgelegd', 'case_hash': case_hash(case),
            'controleur': 'offline test', 'waarnemingen': {
                f'verschuldigd_ib_pvv_p{i+1}': {'tekst': totaal, 'bedrag': totaal}
                for i in range(len(case.personen))}}


def test_only_2025_and_matching_household(case: Case) -> None:
    for update in [{'jaar':2026}, {'personen':case.model_dump()['personen'] * 2}, {'fictieve_gegevens':False}]:
        with pytest.raises(ValidationError):
            Case.model_validate({**case.model_dump(), **update})


@pytest.mark.parametrize(('tekst', 'verwacht'), [('€ 1.234,56', '1234.56'), ('0', '0'), ('−31,29', '-31.29'), ('1.826', '1826')])
def test_dutch_amounts(tekst: str, verwacht: str) -> None:
    assert lees_euro(tekst) == Decimal(verwacht)


@pytest.mark.parametrize('tekst', ['', '€ -', '€ 10 en € 20', '1,234.56', 'NaN', '12.34', 'Totaal 123'])
def test_ambiguous_amounts_fail_closed(tekst: str) -> None:
    with pytest.raises(ValueError):
        lees_euro(tekst)


def test_catalogue_discovers_current_ids_without_hardcoding() -> None:
    parser = CatalogusParser()
    parser.feed('''<form action="./casussen?9-1.IFormSubmitListener-formulierPanel-formulierenForm">
      <input type="hidden" name="token" value="test"><select>
      <option value="999">2025| IH2025 versie 1</option></select></form>
      <tr id="Blanco_openen" onclick="window.open(&#039;https://opleiding-ola.belastingdienst.nl/onlineaangifte/ib/aangifte/2025/?casusid=888&#039;)"></tr>''')
    assert parser.waarde_2025 == '999'
    assert parser.form_data == {'token':'test'}
    assert parser.casussen['Blanco'].endswith('casusid=888')


@pytest.mark.parametrize('url', ['http://opleiding-ola.belastingdienst.nl/', 'https://belastingdienst.nl/',
                                  'https://opleiding-ola.belastingdienst.nl.evil.test/', 'https://user:pw@opleiding-ola.belastingdienst.nl/'])
def test_only_training_domain(url: str) -> None:
    with pytest.raises(ValueError):
        controleer_url(url)


def test_all_examples_build_real_engine_output() -> None:
    for pad in Path('config/ola/cases').glob('*.json'):
        case = laad_case(pad)
        result = engine_resultaat(case)
        assert result['accountant_detail']['config_jaar'] == 2025
        assert result['waarden']['bruto_arbeid_p1'] == str(case.personen[0].bruto_arbeid)
        assert Decimal(result['waarden']['totaal_verschuldigd']).is_finite()
        assert result['tarieven_hash']
        assert bool(result['accountant_detail']['heeft_partner']) == (len(case.personen) == 2)


def test_aow_input_difference_is_not_a_tax_fail() -> None:
    case = laad_case(Path('config/ola/cases/alleen_pensioen.json'))
    engine = engine_resultaat(case)
    assert vergelijk(case, bron(case), engine)['status'] == 'INVOER_VERSCHIL'


def test_comparison_preserves_zero_and_reports_delta(case: Case) -> None:
    engine = engine_resultaat(case)
    reference = bron(case, '0')
    result = vergelijk(case, reference, engine)
    assert result['status'] == 'FAIL'
    assert result['verschillen'][0]['ola'] == '0'
    assert result['verschillen'][0]['verschil'] == engine['waarden']['totaal_verschuldigd']
    assert result['dekking'] == 'alleen huishoudtotaal'


def test_missing_reference_does_not_become_zero(case: Case) -> None:
    reference = bron(case)
    reference['waarnemingen'].clear()
    with pytest.raises(ValueError, match='Ontbrekende'):
        vergelijk(case, reference, engine_resultaat(case))


def test_changed_case_and_changed_raw_text_rejected(case: Case) -> None:
    reference = bron(case)
    edited = case.model_copy(deep=True)
    edited.personen[0].bruto_arbeid += Decimal('1')
    with pytest.raises(ValueError, match='andere invoer'):
        vergelijk(edited, reference, engine_resultaat(edited))
    reference['waarnemingen']['verschuldigd_ib_pvv_p1']['bedrag'] = '999'
    with pytest.raises(ValueError, match='Brontekst'):
        vergelijk(case, reference, engine_resultaat(case))


def test_partner_results_are_aggregated_not_imputed(case: Case) -> None:
    pair = Case.model_validate({**case.model_dump(), 'huishouden':'fiscaal_partners_heel_jaar',
                              'personen':case.model_dump()['personen'] * 2})
    result = vergelijk(pair, bron(pair, '500'), engine_resultaat(pair))
    assert result['verschillen'][0]['ola'] == '1000'
    assert len(result['verschillen']) == 1


def test_recipe_requires_bound_inputs_and_both_partner_outputs(case: Case) -> None:
    with pytest.raises(ValueError, match='onvolledig'):
        controleer_recept(case)
    steps = [Stap(actie='vul', locator=Locator(soort='css', waarde='#test'), waarde_pad=p)
             for p in case.vereiste_invoer()]
    steps.append(Stap(actie='lees', locator=Locator(soort='css', waarde='#amount'), veld='verschuldigd_ib_pvv_p1'))
    case.ola.stappen = steps
    controleer_recept(case)


def test_date_formatting_keeps_case_input(case: Case) -> None:
    step = Stap(actie='vul', locator=Locator(soort='css', waarde='#date'),
                waarde_pad='personen.0.geboortedatum', formaat='datum_nl')
    assert stap_waarde(case, step) == '12-04-1970'


def test_evidence_tampering_rejected(tmp_path: Path) -> None:
    (tmp_path/'a.png').write_bytes(b'fixture image')
    (tmp_path/'a.txt').write_text('1234')
    url = 'https://opleiding-ola.belastingdienst.nl/onlineaangifte/ib/aangifte/2025/?casusid=260'
    reference = {'bron_url':url, 'formulier':'IH2025 versie 1', 'waarnemingen':{'total': {
        'url':url, 'bewijs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.iterdir()}}}}
    controleer_bewijs(tmp_path, reference)
    (tmp_path/'a.txt').write_text('999')
    with pytest.raises(ValueError, match='Gewijzigd'):
        controleer_bewijs(tmp_path, reference)


def test_prepare_creates_separate_runs_without_reference(tmp_path: Path) -> None:
    args = ['voorbereiden', 'config/ola/cases/alleen_werkend.json', '--output', str(tmp_path)]
    assert main(args) == main(args) == 0
    runs = list((tmp_path/'ola_2025_alleen_werkend').iterdir())
    assert len(runs) == 2
    for run in runs:
        assert (run/'pensioen.json').exists()
        assert (run/'invulblad.md').exists()
        assert not (run/'ola.json').exists()


def test_export_uses_external_amount_and_loads_in_existing_contract(case: Case) -> None:
    from tests.models.testcase import TestCase
    from tools.ola.vergelijking import raw_kandidaat
    candidate = raw_kandidaat(case, bron(case, '1234'), engine_resultaat(case))
    parsed = TestCase.model_validate(candidate)
    assert parsed.verwachte_belasting.totaal_verschuldigd == Decimal('1234')
    assert parsed.jaar == 2025
    assert 'box3_heffing' not in candidate['verwachte_belasting']


def test_export_refuses_input_source_conflict() -> None:
    from tools.ola.vergelijking import raw_kandidaat
    case = laad_case(Path('config/ola/cases/alleen_pensioen.json'))
    with pytest.raises(ValueError, match='bronverschil'):
        raw_kandidaat(case, bron(case), engine_resultaat(case))
