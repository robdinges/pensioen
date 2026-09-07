"""Regressies voor verlies en rendement per liquide post."""
from datetime import date
from decimal import Decimal

import pytest

from pensioen.calculations.vermogen_engine import bereken_rente_maand, maandrendement
from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.models.cashflow import HuishoudCashflow
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.models.vermogensitem import VermogensItem
from pensioen.tax.belasting_loader import laad_tarieven_bereik


@pytest.mark.bouwsteen
def test_negative_split_return_is_not_discarded() -> None:
    assert bereken_rente_maand(Decimal('100000'), None, Decimal('0'), Decimal('-10'), Decimal('0')) == Decimal('-874.16')


@pytest.mark.bouwsteen
@pytest.mark.parametrize('rate', ['-101', 'NaN', 'Infinity'])
def test_return_domain_rejects_invalid_rate(rate: str) -> None:
    with pytest.raises(ValueError):
        maandrendement(Decimal(rate))


@pytest.mark.bouwsteen
def test_total_loss_is_bounded_at_balance() -> None:
    assert bereken_rente_maand(Decimal('1000'), Decimal('-100')) == Decimal('-1000.00')


def flow(scenario: Scenario, end: int = 2025) -> HuishoudCashflow:
    return bereken_huishouden(scenario, Persoon(naam='Test', geboortedatum=date(1990, 1, 1)),
                             None, [], [], 2025, end, laad_tarieven_bereik(2025, end))


@pytest.mark.engine
def test_negative_return_reaches_household_balance() -> None:
    result = flow(Scenario(naam='Verlies', beleggingen_start=Decimal('100000'),
                          rendement_sparen_pct=Decimal('0'), rendement_beleggen_pct=Decimal('-10'),
                          box3_meenemen=False))
    assert result.jaren[0].maanden[0].rente_bruto == Decimal('-874.16')
    assert abs(result.jaren[0].vermogen_einde_jaar - Decimal('90000')) < Decimal('.05')


@pytest.mark.engine
def test_distinct_accounts_compound_their_own_rates() -> None:
    result = flow(Scenario(naam='Twee rekeningen', box3_meenemen=False,
        rendement_sparen_pct=Decimal('3'), vermogensitems=[
            VermogensItem(omschrijving='Klein', type='spaargeld', aanschafwaarde='1000', groei_pct='1'),
            VermogensItem(omschrijving='Groot', type='spaargeld', aanschafwaarde='99000', groei_pct='5'),
        ]), 2026)
    assert abs(result.jaren[0].vermogen_einde_jaar - Decimal('104960')) < Decimal('.05')
    assert abs(result.jaren[1].vermogen_einde_jaar - Decimal('110167.60')) < Decimal('.10')


@pytest.mark.bouwsteen
def test_post_contributions_dates_closure_and_cash_shortfall() -> None:
    from pensioen.calculations.vermogen_engine import LiquidePortefeuille
    items = [VermogensItem(omschrijving='Later', type='beleggingen', aanschafwaarde='1000',
                          groei_pct='0', aanschafdatum=date(2025, 7, 16),
                          verkoopdatum=date(2025, 8, 15), jaarlijkse_inleg='1200')]
    p = LiquidePortefeuille(items, date(2025, 1, 1))
    assert p.saldo == 0
    assert p.begin_maand(2025, 6) == (Decimal('0'), Decimal('0'), Decimal('0'))
    p.sluit_maand(Decimal('0'))
    rente, inleg, opening = p.begin_maand(2025, 7)
    assert opening == 1000
    assert inleg == Decimal('51.61')  # 16 / 31 dagen
    p.sluit_maand(Decimal('-100'))
    assert p.saldo == Decimal('951.61')
    p.begin_maand(2025, 8)
    p.sluit_maand(Decimal('0'))
    assert p.saldo == Decimal('1000.00')  # 15 / 31 dagen inleg; sluiting behoudt geld.
    p.begin_maand(2025, 9)
    p.sluit_maand(Decimal('-1100'))
    assert p.saldo == Decimal('-100.00')
    p.begin_maand(2025, 10)
    p.sluit_maand(Decimal('200'))
    assert p.saldo == Decimal('100.00')
    assert items[0].aanschafwaarde == 1000  # Broninvoer wordt niet gemuteerd.


@pytest.mark.engine
def test_cashflow_changes_next_months_return_and_inleg_is_not_doubled() -> None:
    from pensioen.models.scenario import IncidenteelItem
    scenario = Scenario(naam='Inleg', box3_meenemen=False, jaarlijkse_inleg_sparen='1200',
        incidentele_items=[IncidenteelItem(datum=date(2025, 1, 31), bedrag=Decimal('-500'), omschrijving='Opname')],
        vermogensitems=[VermogensItem(omschrijving='Sparen', type='spaargeld',
                       aanschafwaarde='1000', groei_pct='12', jaarlijkse_inleg='1200')])
    result = flow(scenario)
    jan, feb = result.jaren[0].maanden[:2]
    assert jan.vermogen_einde_maand == Decimal('609.49')
    assert feb.rente_bruto == Decimal('5.78')


@pytest.mark.engine
def test_future_account_does_not_activate_legacy_mirrored_balance_early() -> None:
    result = flow(Scenario(naam='Later', spaargeld_start='1000', box3_meenemen=False,
        vermogensitems=[VermogensItem(omschrijving='Later', type='spaargeld', aanschafwaarde='1000',
                        aanschafdatum=date(2025, 7, 1), groei_pct='0')]))
    assert result.jaren[0].maanden[5].vermogen_einde_maand == 0
    assert result.jaren[0].maanden[6].vermogen_einde_maand == 1000


@pytest.mark.engine
def test_report_reconciles_actual_partial_year_contributions() -> None:
    result = flow(Scenario(naam='Deeljaar', box3_meenemen=False,
        vermogensitems=[VermogensItem(omschrijving='Later', type='spaargeld', aanschafwaarde='1000',
                        aanschafdatum=date(2025, 7, 1), groei_pct='0', jaarlijkse_inleg='1200')]))
    detail = result.jaren[0].accountant_detail
    assert detail['inleg_per_jaar'] == Decimal('600')
    assert detail['jaar_netto_cashflow'] == Decimal('1600')
    for row in detail['vermogen_rijen']:
        assert row['saldo_eind'] - row['saldo_begin'] == row['netto_cashflow']
    assert detail['vermogen_rijen'][6]['inleg'] == Decimal('100')


@pytest.mark.bouwsteen
def test_general_cashflow_and_returns_conserve_money() -> None:
    from pensioen.calculations.vermogen_engine import LiquidePortefeuille
    items = [VermogensItem(omschrijving=str(i), type='spaargeld', aanschafwaarde='0.01', groei_pct='0') for i in range(20)]
    p = LiquidePortefeuille(items, date(2025, 1, 1))
    for amount in ('0.10', '-0.07', '-100', '100', '0.01'):
        before = p.saldo
        p.begin_maand(2025, 1)
        p.sluit_maand(Decimal(amount))
        assert p.saldo == before + Decimal(amount)
        assert all(s >= 0 for s in p.saldis)


@pytest.mark.contract
def test_invalid_legacy_rate_is_input_error() -> None:
    with pytest.raises(ValueError, match='minimaal -100'):
        Scenario(naam='Ongeldig', rendement_beleggen_pct=Decimal('-101'))


@pytest.mark.bouwsteen
def test_interest_stops_at_closing_date_and_money_is_retained() -> None:
    from pensioen.calculations.vermogen_engine import LiquidePortefeuille
    p = LiquidePortefeuille([VermogensItem(omschrijving='Beleggen', type='beleggingen',
                            aanschafwaarde='1000', groei_pct='12', verkoopdatum=date(2025, 1, 15))], date(2025, 1, 1))
    rente, _, _ = p.begin_maand(2025, 1)
    assert rente == Decimal('4.58')
    p.sluit_maand(Decimal('0'))
    assert p.saldo == Decimal('1004.58')
    assert p.begin_maand(2025, 2)[0] == 0


@pytest.mark.engine
def test_box3_next_year_uses_actual_post_balances() -> None:
    scenario = Scenario(naam='Actuele verdeling', box3_meenemen=False, vermogensitems=[
        VermogensItem(omschrijving='Spaar', type='spaargeld', aanschafwaarde='10000', groei_pct='0', jaarlijkse_inleg='12000'),
        VermogensItem(omschrijving='Beleg', type='beleggingen', aanschafwaarde='10000', groei_pct='-10', jaarlijkse_inleg='0'),
    ])
    result = flow(scenario, 2026)
    detail = result.jaren[1].accountant_detail
    assert detail['box3_grondslag'] == result.jaren[0].vermogen_einde_jaar
    assert abs(detail['box3_spaargeld_fractie'] - Decimal('22000') / Decimal('31000')) < Decimal('.00001')
