"""Scenario-recept; pensioenbedragen zijn expliciete invoer, geen actuariële schatting."""
from __future__ import annotations

from datetime import date, timedelta
import calendar
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from pensioen.models.component import BedragType, CategorieComponent, FinancieelComponent, Frequentie
from pensioen.models.opbouw_simulatie import OpbouwKeuze
from pensioen.models.scenario import Scenario
from pensioen.calculations.scenario_engine import ScenarioVergelijking


def bouw_opbouwscenarios(basis: Scenario, keuze: OpbouwKeuze) -> list[Scenario]:
    if keuze.pensioen_index >= len(basis.componenten):
        raise ValueError('Kies een bestaande pensioenpost.')
    pensioen = basis.componenten[keuze.pensioen_index]
    if pensioen.categorie != CategorieComponent.PENSIOEN_INKOMEN or pensioen.persoon not in ('P1', 'P2'):
        raise ValueError('Kies een pensioenpost van persoon 1 of 2.')
    arbeid = [c for c in basis.componenten if c.categorie == CategorieComponent.ARBEIDSINKOMEN
              and c.persoon == pensioen.persoon]
    if not arbeid:
        raise ValueError('Voeg eerst het werkinkomen van deze persoon toe aan het actieve plan.')
    if not any((c.begindatum is None or c.begindatum <= keuze.laatste_werkdag) and (c.einddatum is None or c.einddatum >= keuze.laatste_werkdag) for c in arbeid):
        raise ValueError('Er is geen werkinkomen actief op de gekozen laatste werkdag.')
    if pensioen.einddatum is not None:
        raise ValueError('Kies een doorlopend ouderdomspensioen; een tijdelijk pensioen is niet geschikt voor deze simulator.')
    if any(c.waarde_periodes for c in arbeid):
        raise ValueError('Werkinkomen met meerdere waardeperiodes: maak voor deze simulatie eerst een aparte eenvoudige loonpost.')
    varianten = [
        ('Doorwerken', keuze.doorwerken_tot, keuze.pensioen_doorwerken),
        ('Stoppen zonder doorbetalen', keuze.laatste_werkdag, keuze.pensioen_zonder),
        ('Stoppen met doorbetalen', keuze.laatste_werkdag, keuze.pensioen_met),
    ]
    result = []
    for naam, werkdag, bedrag in varianten:
        scenario = basis.model_copy(deep=True)
        scenario.naam = naam
        scenario.parent_naam = None
        scenario.overrides = {}
        componenten = []
        for index, component in enumerate(scenario.componenten):
            if index == keuze.pensioen_index:
                component.bedrag = bedrag
                component.frequentie = Frequentie.MAANDELIJKS
                component.bedrag_type = BedragType.BRUTO
                component.begindatum = keuze.pensioen_vanaf
                component.einddatum = None
                component.waarde_periodes = []
            elif component.categorie == CategorieComponent.ARBEIDSINKOMEN and component.persoon == pensioen.persoon:
                # Geen fictief werk hervatten bij eerder beëindigde banen.
                if component.begindatum and component.begindatum > werkdag:
                    continue
                if naam == 'Doorwerken':
                    if component.einddatum is None or component.einddatum >= keuze.laatste_werkdag:
                        component.einddatum = werkdag
                else:
                    component.einddatum = min(component.einddatum, werkdag) if component.einddatum else werkdag
            componenten.append(component)
        if naam == 'Stoppen met doorbetalen':
            componenten.append(FinancieelComponent(
                omschrijving='Vrijwillige pensioenpremie (simulator)', categorie=CategorieComponent.UITGAVE,
                persoon=pensioen.persoon, bedrag=keuze.premie_per_maand, bedrag_type=BedragType.NETTO,
                begindatum=keuze.laatste_werkdag + timedelta(days=1),
                einddatum=keuze.pensioen_vanaf - timedelta(days=1),
            ))
        scenario.componenten = componenten
        result.append(Scenario.model_validate(scenario.model_dump()))
    return result


def bouw_opbouwuitkomst(vergelijking: ScenarioVergelijking, keuze: OpbouwKeuze,
                        geboortedatum: date) -> dict[str, Any]:
    """Resultaten samenvatten uit de bestaande maandengine, zonder fiscale herrekening."""
    doorwerken = {(m.jaar,m.maand): m for j in vergelijking.scenario_resultaten[0].cashflow.jaren for m in j.maanden}
    zonder = vergelijking.scenario_resultaten[1].cashflow
    met = vergelijking.scenario_resultaten[2].cashflow
    m_zonder = {(m.jaar, m.maand): m for j in zonder.jaren for m in j.maanden}
    m_met = sorted((m for j in met.jaren for m in j.maanden), key=lambda m: (m.jaar, m.maand))
    cumulatief = Decimal('0')
    premie = Decimal('0')
    verschil_inkomen = []
    reeks = []
    for maand in m_met:
        ander = m_zonder[(maand.jaar, maand.maand)]
        # Alleen de premie verschilt in deze uitgavencategorie tussen deze twee opties.
        premie += maand.huishoudelijke_uitgaven - ander.huishoudelijke_uitgaven
        cumulatief += maand.netto - ander.netto
        peildatum = date(maand.jaar, maand.maand, 1)
        if peildatum >= keuze.pensioen_vanaf:
            verschil_inkomen.append((maand.netto_inkomen - maand.rente_bruto) - (ander.netto_inkomen - ander.rente_bruto))
        reeks.append({'maand': f'{maand.jaar:04d}-{maand.maand:02d}', 'datum': date(maand.jaar, maand.maand, calendar.monthrange(maand.jaar, maand.maand)[1]),
                      'cumulatief_verschil': cumulatief})
    # Alleen een omslagpunt dat in de resterende berekeningsperiode niet terugvalt.
    omslag = None
    toekomst_min = Decimal('Infinity')
    for punt in reversed(reeks):
        toekomst_min = min(toekomst_min, punt['cumulatief_verschil'])
        if premie > 0 and punt['datum'] >= keuze.pensioen_vanaf and toekomst_min >= 0:
            omslag = punt['datum']
    leeftijd = (omslag.year - geboortedatum.year - ((omslag.month, omslag.day) < (geboortedatum.month, geboortedatum.day))) if omslag else None
    brug_zonder = sum((doorwerken[key].netto - m.netto for key,m in m_zonder.items() if date(m.jaar,m.maand,1) < keuze.pensioen_vanaf), Decimal('0'))
    brug_met = sum((doorwerken[(m.jaar,m.maand)].netto - m.netto for m in m_met if date(m.jaar,m.maand,1) < keuze.pensioen_vanaf), Decimal('0'))
    return {
        'extra_geld_tot_pensioen_zonder': brug_zonder,
        'extra_geld_tot_pensioen_met': brug_met,
        'totale_premie': premie,
        'extra_netto_pensioen_per_maand': (sum(verschil_inkomen, Decimal('0')) / Decimal(len(verschil_inkomen))).quantize(Decimal('.01'), rounding=ROUND_HALF_UP) if verschil_inkomen else None,
        'omslag_maand': omslag.strftime('%Y-%m') if omslag else None,
        'omslag_leeftijd': leeftijd,
        'cumulatief_verschil_einde': cumulatief,
        'maandvergelijking': [{k:v for k,v in punt.items() if k != 'datum'} for punt in reeks],
    }
