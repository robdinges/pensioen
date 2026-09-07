"""Vermogensstanden zijn waarnemingen, geen looptijd of extra inleg."""
from datetime import date
from decimal import Decimal

import pytest

from pensioen.models.vermogensitem import VermogensItem
from pensioen.models.scenario import Scenario
from tests.test_vermogen_rendement_regressie import flow


@pytest.mark.bouwsteen
def test_latest_known_balance_is_authoritative() -> None:
    item = VermogensItem(omschrijving='Rekening', type='spaargeld', aanschafwaarde='999', groei_pct='0',
        saldostanden=[{'peildatum':'2025-01-01','bedrag':'1000'}, {'peildatum':'2025-07-01','bedrag':'500'}])
    assert item.waarde_op_datum(date(2024, 12, 31)) == 0
    assert item.waarde_op_datum(date(2025, 6, 30)) == 1000
    assert item.waarde_op_datum(date(2026, 1, 1)) == 500


@pytest.mark.engine
def test_new_balance_replaces_projection_without_income() -> None:
    result = flow(Scenario(naam='Standen', box3_meenemen=False, vermogensitems=[
        VermogensItem(omschrijving='Rekening', type='spaargeld', aanschafwaarde='0', groei_pct='0',
            saldostanden=[{'peildatum':'2025-01-01','bedrag':'1000'}, {'peildatum':'2025-07-16','bedrag':'500'}])]))
    months = result.jaren[0].maanden
    assert months[5].vermogen_einde_maand == 1000
    assert months[6].vermogen_einde_maand == 500
    assert months[6].eenmalig_ontvangst == 0
    assert months[6].eenmalig_uitgave == 0
    assert months[6].vermogen_correctie == Decimal('-500')
    for row in result.jaren[0].accountant_detail['vermogen_rijen']:
        assert row['saldo_begin'] + row['netto_cashflow'] + row['saldo_correctie'] == row['saldo_eind']


@pytest.mark.engine
def test_mid_month_observation_resets_growth_base() -> None:
    result = flow(Scenario(naam='Groei', box3_meenemen=False, vermogensitems=[
        VermogensItem(omschrijving='Rekening', type='spaargeld', aanschafwaarde='0', groei_pct='12',
            saldostanden=[{'peildatum':'2025-01-01','bedrag':'1000'}, {'peildatum':'2025-01-16','bedrag':'2000'}])]))
    # Vanaf de stand aan begin 16 januari groeit 2000 nog 16/31 van de maand.
    expected = (Decimal('2000') * Decimal('1.12') ** (Decimal(16) / Decimal(31) / Decimal(12))).quantize(Decimal('.01'))
    assert result.jaren[0].maanden[0].vermogen_einde_maand == expected


@pytest.mark.bouwsteen
def test_duplicate_balance_dates_are_rejected() -> None:
    with pytest.raises(ValueError, match='peildatum'):
        VermogensItem(omschrijving='Rekening', type='spaargeld', aanschafwaarde='0',
            saldostanden=[{'peildatum':'2025-01-01','bedrag':'1'}, {'peildatum':'2025-01-01','bedrag':'2'}])
