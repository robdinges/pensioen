"""2025-bronregels en OLA-regressies voor volledig gepensioneerden."""
from decimal import Decimal
from pathlib import Path

import pytest

from pensioen.tax.belasting_loader import laad_tarieven
from pensioen.tax.heffingskorting import bereken_ouderenkorting
from tools.ola.modellen import laad_case, DETAIL_MAPPING
from tests.testcase_loader import vind_testcase_by_id
from tests.testcase_validatie import bereken_belasting_testcase
from tools.ola.vergelijking import engine_resultaat


@pytest.mark.bouwsteen
@pytest.mark.parametrize(('inkomen', 'korting'), [
    ('41752', '2035'), ('45308', '2035'), ('45309', '2035'),
    ('46308', '1885'), ('58875', '0'),
])
def test_ouderenkorting_2025_official_threshold(inkomen: str, korting: str) -> None:
    # Fiscale informatie 2025, paragraaf 21.4.1; OLA bevestigt €2035 bij €41752.
    config, _ = laad_tarieven(2025)
    assert bereken_ouderenkorting(Decimal(inkomen), config, True) == Decimal(korting)


@pytest.mark.engine
def test_single_retirement_ola_source() -> None:
    case = laad_case(Path('config/ola/historisch/alleen_pensioen.json'))
    waarden = _historische_fiscale_waarden('tc_2025_016')
    assert Decimal(waarden['bruto_aow_p1']) == case.personen[0].bruto_aow
    assert Decimal(waarden['bruto_pensioen_p1']) == case.personen[0].bruto_pensioen
    assert Decimal(waarden['ouderenkorting_p1']) == Decimal('2035')
    assert Decimal(waarden['alleenstaandeouderenkorting_p1']) == Decimal('531')
    # OLA-AHK €1114 versus tabelberekening €1113; bestaande €1-tolerantie.
    assert abs(Decimal(waarden['totaal_verschuldigd']) - Decimal('4447')) <= case.tolerantie


@pytest.mark.engine
def test_partner_retirement_ola_source() -> None:
    case = laad_case(Path('config/ola/historisch/paar_pensioen.json'))
    waarden = _historische_fiscale_waarden('tc_2025_017')
    for i, (ib, voor_kortingen, ahk, netto) in enumerate([
        ('2987', '6552', '1277', '3240'), ('2170', '4760', '1536', '1189'),
    ], 1):
        assert Decimal(waarden[f'bruto_aow_p{i}']) == case.personen[i - 1].bruto_aow
        assert Decimal(waarden[f'bruto_pensioen_p{i}']) == case.personen[i - 1].bruto_pensioen
        assert Decimal(waarden[f'box1_ib_voor_kortingen_p{i}']) == Decimal(ib)
        assert Decimal(waarden[f'ib_pvv_box1_voor_kortingen_p{i}']) == Decimal(voor_kortingen)
        assert Decimal(waarden[f'premie_aow_p{i}']) == 0
        assert Decimal(waarden[f'ouderenkorting_p{i}']) == Decimal('2035')
        assert Decimal(waarden[f'alleenstaandeouderenkorting_p{i}']) == 0
        assert abs(Decimal(waarden[f'algemene_heffingskorting_p{i}']) - Decimal(ahk)) <= case.tolerantie
        assert abs(Decimal(waarden[f'box1_na_kortingen_p{i}']) - Decimal(netto)) <= case.tolerantie
    assert abs(Decimal(waarden['totaal_verschuldigd']) - Decimal('4429')) <= case.tolerantie


def _historische_fiscale_waarden(case_id: str) -> dict[str, Decimal]:
    """Bevries oude OLA-bruto invoer; de SVB-cashflow heeft eigen regressies."""
    case = vind_testcase_by_id(case_id)
    detail = bereken_belasting_testcase(case)
    waarden = {f'{veld}_p{i}': detail[f'{bron}_p{i}']
               for i in range(1, len(case.personen) + 1) for veld, bron in DETAIL_MAPPING.items()}
    waarden['totaal_verschuldigd'] = detail['totaal_netto_belasting_box1'] + detail['box3_heffing']
    return waarden


@pytest.mark.engine
@pytest.mark.parametrize(('naam', 'verwacht'), [('alleen_pensioen_svb', '5847'), ('paar_pensioen_svb', '5411')])
def test_current_svb_cashflow_against_live_ola(naam: str, verwacht: str) -> None:
    case = laad_case(Path('config/ola/verified') / f'{naam}.json')
    waarden = engine_resultaat(case)['waarden']
    for i, p in enumerate(case.personen, 1):
        assert Decimal(waarden[f'bruto_aow_p{i}']) == p.bruto_aow
    assert abs(Decimal(waarden['totaal_verschuldigd']) - Decimal(verwacht)) <= case.tolerantie
