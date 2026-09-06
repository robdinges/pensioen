"""Directe brongevallen voor de tijdens OLA-validatie gevonden fouten."""
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from pensioen.tax.belasting_engine import bereken_box1_belasting, bereken_premies_volksverzekeringen
from pensioen.tax.belasting_loader import laad_tarieven
from pensioen.tax.heffingskorting import bereken_arbeidskorting


@pytest.mark.bouwsteen
def test_box1_2025_cohort_and_premium_boundary() -> None:
    config, _ = laad_tarieven(2025)
    assert bereken_box1_belasting(Decimal('45000'), config, Decimal('0')) == Decimal('5598.94')
    assert bereken_box1_belasting(Decimal('45000'), config, Decimal('1'), geboortedatum=date(1945, 12, 31)) == Decimal('4994.86')
    assert bereken_box1_belasting(Decimal('45000'), config, Decimal('1'), geboortedatum=date(1946, 1, 1)) == Decimal('5598.94')
    assert bereken_premies_volksverzekeringen(Decimal('45000'), config, False) == (
        Decimal('6880.94'), Decimal('38.44'), Decimal('3709.56'), Decimal('10628.94'))


@pytest.mark.bouwsteen
@pytest.mark.parametrize(('inkomen', 'korting'), [
    ('0', '0'), ('10000', '805.3'), ('12169', '979.96957'),
    ('12170', '980.30030'), ('26288', '5219.9357'),
    ('26289', '5220.02258'), ('30000', '5303.81696'),
    ('43071', '5598.96014'), ('45000', '5473.4221'), ('130000', '0'),
])
def test_arbeidskorting_2025_official_segments(inkomen: str, korting: str) -> None:
    config, _ = laad_tarieven(2025)
    assert bereken_arbeidskorting(Decimal(inkomen), config) == Decimal(korting)


@pytest.mark.engine
@pytest.mark.parametrize(('naam', 'totaal'), [
    ('alleen_werkend', '8738.02'), ('paar_werkend_zonder_vermogen', '11213.21'),
])
def test_corrected_ola_household_path_keeps_rounding_debt_explicit(naam: str, totaal: str) -> None:
    from tools.ola.modellen import laad_case
    from tools.ola.vergelijking import engine_resultaat
    case = laad_case(Path('config/ola/verified') / f'{naam}.json')
    waarden = engine_resultaat(case)['waarden']
    assert Decimal(waarden['totaal_verschuldigd']) == Decimal(totaal)
    assert Decimal(waarden['box1_ib_voor_kortingen_p1']) == Decimal('5598.94')
    if len(case.personen) == 2:
        assert Decimal(waarden['arbeidskorting_p2']) == Decimal('5303.82')


@pytest.mark.contract
def test_period_resolution_keeps_cohort_and_credit_segments() -> None:
    from pensioen.tax.belasting_loader import resolve_tariefwaarden_voor_jaar
    config, _ = laad_tarieven(2025)
    resolved, _ = resolve_tariefwaarden_voor_jaar(config, 2025, [])
    assert bereken_arbeidskorting(Decimal('30000'), resolved) == Decimal('5303.81696')
    assert bereken_box1_belasting(Decimal('45000'), resolved, Decimal('1'), geboortedatum=date(1945, 1, 1)) == Decimal('4994.86')
