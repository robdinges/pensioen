"""Scenario-recept voor doorwerken en vrijwillige pensioenopbouw."""
from datetime import date
from decimal import Decimal

import pytest

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
    data=dict(pensioen_index=1,laatste_werkdag='2025-03-31',doorwerken_tot='2025-12-31',
              pensioen_vanaf='2026-01-01',premie_per_maand='800',pensioen_doorwerken='1200',
              pensioen_zonder='1000',pensioen_met='1200',modus='aannames')
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
