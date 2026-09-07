"""Projectie van engine-output en verschillen, zonder fiscale herberekening."""
from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from pensioen.api.serialisatie import naar_json_compatibel
from pensioen.calculations.resultaat_service import bereken_resultaten
from pensioen.models.component import FinancieelComponent
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import EigenWoningData, Scenario
from pensioen.models.vermogensitem import VermogensItem
from pensioen.tax.belasting_loader import laad_tarieven
from tools.ola.modellen import Case, DETAIL_MAPPING, RESULTAATVELDEN, case_hash, hash_json


def lees_euro(tekst: str) -> Decimal:
    """Eén Nederlands geldbedrag; geen stille nul, jaartalextractie of float."""
    schoon = tekst.strip().replace('\u00a0', ' ').replace('€', '').strip().replace('−', '-')
    if not re.fullmatch(r'-?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{1,2})?', schoon):
        raise ValueError(f'Geen eenduidig Nederlands bedrag: {tekst!r}; selecteer alleen de waarde.')
    return Decimal(schoon.replace('.', '').replace(',', '.'))


def bouw_engine_invoer(case: Case) -> tuple[list[Persoon], Scenario]:
    personen = [Persoon(naam=p.naam, geboortedatum=p.geboortedatum, heeft_partner=len(case.personen) == 2)
                for p in case.personen]
    componenten = []
    for i, persoon in enumerate(case.personen, 1):
        for veld, categorie in [('bruto_arbeid', 'arbeidsinkomen'), ('bruto_pensioen', 'pensioen_inkomen')]:
            bedrag = getattr(persoon, veld)
            if bedrag:
                componenten.append(FinancieelComponent(
                    omschrijving=f'OLA {veld} P{i}', persoon=f'P{i}', categorie=categorie,
                    bedrag=bedrag, bedrag_type='bruto', frequentie='jaarlijks',
                    begindatum='2025-01-01', einddatum='2025-12-31', groei_pct=Decimal('0'),
                ))
    items = [VermogensItem(omschrijving=f'OLA {naam}', type=soort, aanschafwaarde=bedrag,
                          persoon='Huishouden', box3_belast=True, groei_pct=Decimal('0'))
             for naam, soort, bedrag in [('sparen', 'spaargeld', case.vermogen.spaargeld),
                                        ('beleggen', 'beleggingen', case.vermogen.beleggingen)] if bedrag]
    woning = case.woning
    scenario = Scenario(
        naam=case.case_id, componenten=componenten, vermogensitems=items,
        rendement_sparen_pct=Decimal('0'), rendement_beleggen_pct=Decimal('0'),
        inflatie_pct=Decimal('0'), heeft_eigen_woning=woning is not None,
        # De bestaande fiscale woninginput is een gedocumenteerd compatibiliteitscontract.
        eigen_woning=EigenWoningData(
            woz_waarde=woning.woz_waarde,
            betaalde_hypotheekrente=woning.betaalde_hypotheekrente,
            eigenwoningschuld_begin=woning.eigenwoningschuld,
            eigenwoningschuld_eind=woning.eigenwoningschuld,
        ) if woning else EigenWoningData(),
    )
    return personen, scenario


def engine_resultaat(case: Case) -> dict[str, Any]:
    tarieven, aanname = laad_tarieven(2025)
    if tarieven.jaar != 2025 or aanname:
        raise ValueError('Validatie vereist een eigen 2025-config, zonder tarieffallback.')
    personen, scenario = bouw_engine_invoer(case)
    cashflow = bereken_resultaten(scenario, personen[0], personen[1] if len(personen) == 2 else None,
                                  [], [], 2025, 2025)
    detail = cashflow.jaren[0].accountant_detail
    waarden = {'box3_heffing': detail['box3_heffing']}
    for i in range(1, len(personen) + 1):
        for veld, bron in DETAIL_MAPPING.items():
            waarden[f'{veld}_p{i}'] = detail[f'{bron}_p{i}']
    # Alleen aggregatie van de bestaande engine-eindbedragen; geen belastingformule.
    waarden['totaal_verschuldigd'] = detail['totaal_netto_belasting_box1'] + detail['box3_heffing']
    return naar_json_compatibel({
        'waarden': waarden, 'accountant_detail': detail,
        'request': {'scenario': scenario, 'personen': personen, 'jaar_van': 2025, 'jaar_tot': 2025},
        'tarieven': tarieven, 'tarieven_hash': hash_json(naar_json_compatibel(tarieven)),
    })


def vergelijk(case: Case, bron: dict[str, Any], engine: dict[str, Any]) -> dict[str, Any]:
    if bron.get('case_hash') != case_hash(case):
        raise ValueError('Referentie hoort bij andere invoer/keuzes; eerst opnieuw simuleren.')
    if bron.get('jaar') != 2025 or bron.get('status') != 'vastgelegd':
        raise ValueError('Geen voltooide 2025-referentie.')
    if not bron.get('controleur'):
        raise ValueError('OLA-invoer en betekenis van resultaatvelden zijn niet bevestigd.')
    waarnemingen = bron.get('waarnemingen', {})
    ontbreekt = case.vereiste_velden() - waarnemingen.keys()
    if ontbreekt:
        raise ValueError(f'Ontbrekende persoonsuitkomsten: {sorted(ontbreekt)}')
    if set(waarnemingen) - RESULTAATVELDEN:
        raise ValueError('Onbekende OLA-resultaatvelden.')
    if len(case.personen) == 1 and any(v.endswith('_p2') for v in waarnemingen):
        raise ValueError('P2-uitkomsten bij eenpersoonshuishouden.')
    ola = {}
    for veld, waarneming in waarnemingen.items():
        bedrag = lees_euro(waarneming['tekst'])
        if Decimal(waarneming['bedrag']) != bedrag:
            raise ValueError(f'Brontekst en bedrag verschillen voor {veld}.')
        ola[veld] = bedrag
    ola['totaal_verschuldigd'] = sum((ola[v] for v in case.vereiste_velden()), Decimal('0'))
    invoerverschillen = []
    for i, p in enumerate(case.personen, 1):
        for veld in ('bruto_arbeid', 'bruto_pensioen', 'bruto_aow'):
            verwacht = getattr(p, veld)
            werkelijk = Decimal(engine['waarden'][f'{veld}_p{i}'])
            if abs(werkelijk - verwacht) > Decimal('0.01'):
                invoerverschillen.append({'veld': f'{veld}_p{i}', 'case': str(verwacht), 'engine': str(werkelijk)})
    verschillen = []
    for veld, verwacht in sorted(ola.items()):
        if veld.startswith('verschuldigd_ib_pvv_'):
            continue  # Engine heeft geen individuele box-3-toedeling; vergelijk huishoudsom.
        werkelijk = Decimal(engine['waarden'][veld])
        delta = werkelijk - verwacht
        verschillen.append({'veld': veld, 'ola': str(verwacht), 'pensioen': str(werkelijk),
                             'verschil': str(delta), 'status': 'PASS' if abs(delta) <= case.tolerantie else 'FAIL'})
    status = ('INVOER_VERSCHIL' if invoerverschillen else
              'FAIL' if any(v['status'] == 'FAIL' for v in verschillen) else 'PASS')
    return {'case_id': case.case_id, 'jaar': 2025, 'status': status,
            'tolerantie': str(case.tolerantie), 'invoerverschillen': invoerverschillen,
            'verschillen': verschillen, 'case_hash': case_hash(case),
            'tarieven_hash': engine['tarieven_hash'],
            'dekking': 'alleen huishoudtotaal' if len(verschillen) == 1 else 'huishoudtotaal en vastgelegde componenten'}


def raw_kandidaat(case: Case, bron: dict[str, Any], engine: dict[str, Any]) -> dict[str, Any]:
    """Exporteer alleen bronbedragen; nooit de pensioenuitkomst als referentie."""
    resultaat = vergelijk(case, bron, engine)
    if resultaat['status'] == 'INVOER_VERSCHIL':
        raise ValueError('Los eerst het invoer-/AOW-bronverschil op voordat deze case naar de oude testcaseketen gaat.')
    verwacht = {'totaal_verschuldigd': next(r['ola'] for r in resultaat['verschillen'] if r['veld'] == 'totaal_verschuldigd')}
    mapping = {'box1_ib_voor_kortingen':'box1_ib', 'algemene_heffingskorting':'ahk',
               'arbeidskorting':'arbeidskorting', 'ouderenkorting':'ouderenkorting',
               'alleenstaandeouderenkorting':'alleenstaandeouderenkorting',
               'premie_aow':'premie_aow', 'premie_anw':'premie_anw', 'premie_wlz':'premie_wlz'}
    for veld, obs in bron['waarnemingen'].items():
        if veld == 'box3_heffing':
            verwacht[veld] = obs['bedrag']
        for prefix, naam in mapping.items():
            if veld in {f'{prefix}_p1', f'{prefix}_p2'}:
                verwacht[f'{naam}_{veld[-2:]}'] = obs['bedrag']
    vermogen = case.vermogen
    return {'testcase_id': case.case_id, 'naam': case.naam, 'jaar': 2025,
            'bron_formaat': 'OLA IH2025 + schermafbeeldingen',
            'huishouden': {'type': 'ALLEENSTAAND' if len(case.personen) == 1 else 'PAAR',
                          'aantal_personen': len(case.personen), 'eigen_huis': case.woning is not None},
            'personen': [p.model_dump(mode='json') for p in case.personen],
            'vermogen': {'totaal': str(vermogen.spaargeld + vermogen.beleggingen),
                         'spaargeld_fractie': str(vermogen.spaargeld / (vermogen.spaargeld + vermogen.beleggingen))
                         if vermogen.spaargeld + vermogen.beleggingen else '0',
                         'spaargeld': str(vermogen.spaargeld), 'beleggingen': str(vermogen.beleggingen)},
            'eigen_woning': {'woz_waarde': str(case.woning.woz_waarde),
                             'betaalde_hypotheekrente': str(case.woning.betaalde_hypotheekrente),
                             'eigenwoningschuld_begin': str(case.woning.eigenwoningschuld),
                             'eigenwoningschuld_eind': str(case.woning.eigenwoningschuld)} if case.woning else None,
            'verwachte_belasting': verwacht,
            'metadata': {'bron': bron.get('bron_url', ''), 'uitgangspunten': case.uitgangspunten,
                         'data_kwaliteit': 'minimaal' if len(verwacht) == 1 else 'gedeeltelijk',
                         'opmerkingen': f'OLA-kandidaat, inhoudelijk reviewen vóór opname in raw/. Casehash: {case_hash(case)}. Controleur: {bron["controleur"]}',
                         '_incomplete': False}}
