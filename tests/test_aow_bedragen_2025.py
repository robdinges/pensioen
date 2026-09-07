"""SVB/SZW-bronregels: halfjaarbedragen en uitbetaling vakantiegeld in mei."""
from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from pensioen.tax import aow_engine
from pensioen.tax.belasting_loader import laad_tarieven, resolve_tariefwaarden_voor_jaar


@pytest.mark.bouwsteen
@pytest.mark.parametrize(('partner', 'januari', 'juli', 'mei', 'jaarbedrag'), [
    (False, '1580.92', '1612.44', '2613.20', '20192.44'),
    (True, '1081.50', '1103.97', '1818.86', '13850.18'),
])
def test_svb_full_year_and_holiday_payment(partner: bool, januari: str, juli: str, mei: str, jaarbedrag: str) -> None:
    config, _ = laad_tarieven(2025)
    bedragen = [aow_engine.bereken_aow_uitkering_maand(date(2022, 1, 1), config, 2025, m, partner)
                for m in range(1, 13)]
    assert bedragen[0] == Decimal(januari)
    assert bedragen[4] == Decimal(mei)
    assert bedragen[6] == Decimal(juli)
    assert sum(bedragen) == Decimal(jaarbedrag)


@pytest.mark.bouwsteen
def test_holiday_only_in_may_and_only_accrued_months() -> None:
    config, _ = laad_tarieven(2025)
    # Start januari: alleen januari-april opbouw, geen twaalf maanden vakantiegeld.
    assert aow_engine.bereken_aow_uitkering_maand(date(2025, 1, 1), config, 2025, 5, False) == Decimal('1990.76')
    assert aow_engine.bereken_aow_uitkering_maand(date(2025, 5, 1), config, 2025, 5, False) == Decimal('1580.92')
    assert aow_engine.bereken_aow_uitkering_maand(date(2025, 7, 1), config, 2025, 5, False) == 0
    assert aow_engine.bereken_aow_uitkering_maand(date(2025, 7, 17), config, 2025, 7, False) == Decimal('780.21')


@pytest.mark.contract
def test_period_resolution_preserves_half_year_and_holiday_rules() -> None:
    config, _ = laad_tarieven(2025)
    resolved, _ = resolve_tariefwaarden_voor_jaar(config, 2025, [])
    assert aow_engine.bereken_aow_uitkering_maand(date(2022, 1, 1), resolved, 2025, 5, False) == Decimal('2613.20')
    assert aow_engine.bereken_aow_uitkering_maand(date(2022, 1, 1), resolved, 2025, 7, False) == Decimal('1612.44')


@pytest.mark.bouwsteen
def test_missing_or_overlapping_source_period_is_rejected() -> None:
    config, _ = laad_tarieven(2025)
    config.aow_bedrag.periodes = config.aow_bedrag.periodes[:-1]
    with pytest.raises(ValueError, match='ontbreekt of overlapt'):
        aow_engine.bereken_aow_uitkering_maand(date(2022, 1, 1), config, 2025, 7, False)
    config.aow_bedrag.periodes.append(config.aow_bedrag.periodes[-1])
    with pytest.raises(ValueError, match='ontbreekt of overlapt'):
        aow_engine.bereken_aow_uitkering_maand(date(2022, 1, 1), config, 2025, 1, False)


@pytest.mark.contract
def test_fallback_year_preserves_flat_amount_without_unavailable_history() -> None:
    config, _ = laad_tarieven(2025)
    assert aow_engine.bereken_aow_uitkering_maand(date(2020, 1, 1), config, 2022, 5, False) == Decimal('1580.92')
    legacy = replace(config, aow_bedrag=replace(config.aow_bedrag, periodes=[]))
    assert aow_engine.bereken_aow_uitkering_maand(date(2020, 1, 1), legacy, 2025, 5, False) == Decimal('1580.92')


@pytest.mark.contract
def test_explicit_monthly_override_retains_holiday_accrual() -> None:
    from pensioen.tax.belasting_loader import pas_tariefwaarden_toe_op_config
    config, _ = laad_tarieven(2025)
    custom = pas_tariefwaarden_toe_op_config(config, {'aow_alleenstaand_pm': Decimal('1700')})
    assert aow_engine.bereken_aow_uitkering_maand(date(2020, 1, 1), custom, 2025, 7, False) == Decimal('1700')
    assert aow_engine.bereken_aow_uitkering_maand(date(2020, 1, 1), custom, 2025, 5, False) == Decimal('2732.28')
    assert config.aow_bedrag.periodes[-1].alleenstaande_per_maand == Decimal('1612.44')


@pytest.mark.engine
@pytest.mark.parametrize('partner', [False, True])
def test_cashflow_and_accountant_use_svb_months(partner: bool) -> None:
    from pensioen.calculations.cashflow_engine import bereken_huishouden
    from pensioen.models.persoon import Persoon
    from pensioen.models.scenario import Scenario
    config, _ = laad_tarieven(2025)
    p1 = Persoon(naam='P1', geboortedatum=date(1955, 3, 15), heeft_partner=partner)
    p2 = Persoon(naam='P2', geboortedatum=date(1956, 5, 15), heeft_partner=True) if partner else None
    flow = bereken_huishouden(Scenario(naam='SVB'), p1, p2, [], [], 2025, 2025, {2025: (config, '')})
    jaar = flow.jaren[0]
    assert jaar.maanden[4].aow_p1_bruto == Decimal('1818.86' if partner else '2613.20')
    assert jaar.maanden[6].aow_p1_bruto == Decimal('1103.97' if partner else '1612.44')
    assert jaar.accountant_detail['jaar_aow_p1'] == sum(m.aow_p1_bruto for m in jaar.maanden)
    assert jaar.accountant_detail['jaar_aow_p1'] == Decimal('13850.18' if partner else '20192.44')
    if partner:
        assert jaar.accountant_detail['jaar_aow_p2'] == Decimal('13850.18')
