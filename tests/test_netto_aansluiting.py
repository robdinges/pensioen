"""Resultaatopbouw sluit exact aan op de maandengine."""
from datetime import date
from decimal import Decimal

import pytest
import json
from pathlib import Path
from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.models.component import FinancieelComponent
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.tax.belasting_loader import laad_tarieven_bereik


@pytest.mark.engine
def test_net_income_keeps_person_ownership_and_reconciles() -> None:
    fixture = json.loads(Path('tests/fixtures/belasting_testcases/normalized/tc_2025_018_normalized.json').read_text())
    data = next(v['regressies_netto'] for v in fixture.values() if isinstance(v, dict) and 'regressies_netto' in v)
    scenario = Scenario(naam='Aansluiting', box3_meenemen=False, spaargeld_start=Decimal('10000'),
        rendement_pct=Decimal('3'), componenten=[
            FinancieelComponent(omschrijving=p, categorie='arbeidsinkomen', persoon=p,
                                bedrag=bedrag, bedrag_type='netto')
            for p, bedrag in [('P1', data['netto_maand_p1']), ('P2', data['netto_maand_p2'])]
        ])
    result = bereken_huishouden(scenario,
        Persoon(naam='Een', geboortedatum=date(1990, 1, 1)),
        Persoon(naam='Twee', geboortedatum=date(1990, 1, 1)),
        [], [], 2025, 2025, laad_tarieven_bereik(2025, 2025))
    year = result.jaren[0]
    detail = year.accountant_detail
    assert detail['jaar_arbeid_netto_p1'] == Decimal('12000')
    assert detail['jaar_arbeid_netto_p2'] == Decimal('24000')
    rows = detail['netto_aansluiting']
    assert sum((r['huishouden'] for r in rows[:-1]), Decimal('0')) == rows[-1]['huishouden']
    assert rows[-1]['huishouden'] == year.netto_inkomen
    assert rows[-1]['p1'] == Decimal('12000')
    assert rows[-1]['p2'] == Decimal('24000')
    assert rows[-1]['gezamenlijk'] > 0


@pytest.mark.bouwsteen
def test_detail_reconciles_tax_return_and_deductions() -> None:
    from pensioen.models.cashflow import MaandResultaat
    from pensioen.calculations.detail_output_engine import bouw_netto_aansluiting
    month = MaandResultaat(jaar=2025, maand=1, pensioen_p1_bruto=Decimal('1000'),
        belasting_p1=Decimal('200'), heffingskorting_p1=Decimal('50'),
        inkomen_componenten_netto=Decimal('500'), rente_bruto=Decimal('-20'),
        inhoudingen=Decimal('10'))
    rows = bouw_netto_aansluiting([month])
    assert rows[-1]['huishouden'] == month.netto_inkomen == Decimal('1320')
    for row in rows:
        assert row['p1'] + row['p2'] + row['gezamenlijk'] == row['huishouden']
