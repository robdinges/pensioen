"""CLI: python3 -m tools.ola --help."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from tools.ola.catalogus import ontdek_casussen
from tools.ola.modellen import Case, case_hash, controleer_url, laad_case, formulierafrondingen
from tools.ola.vergelijking import engine_resultaat, raw_kandidaat, vergelijk


def schrijf_json(pad: Path, inhoud: Any) -> None:
    pad.write_text(json.dumps(inhoud, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


def nieuwe_run(root: Path, case: Case) -> Path:
    naam = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
    directory = root / case.case_id / naam
    directory.mkdir(parents=True, exist_ok=False)
    return directory


def invulblad(case: Case) -> str:
    regels = [f'# {case.naam}', '', '**Uitsluitend fictieve IH2025-simulatiegegevens.**', '',
              'Volledig jaar Nederlands inwoner en verzekerd. Geen onderneming, buitenland,',
              'migratie, bijzondere aftrekposten of wijziging fiscaal partnerschap.',
              'Geen werkelijk-rendementroute; deze cases vergelijken het forfaitaire box-3-pad.',
              '', '## Invoerbindingen', '', '| Pad | Waarde |', '| --- | --- |']
    data = case.model_dump(mode='json')
    for i, p in enumerate(data['personen']):
        regels += [f'| personen.{i}.{k} | {v} |' for k, v in p.items()]
    regels += [f'| vermogen.{k} | {v} |' for k, v in data['vermogen'].items()]
    if case.woning:
        regels += [f'| woning.{k} | {v} |' for k, v in data['woning'].items()]
    regels += [f'| ola.keuzes.{k} | {v} |' for k, v in case.ola.keuzes.items()]
    for rij in formulierafrondingen(case):
        regels.append(f'| Formulier: {rij["pad"]} ({rij["regel"]}) | {rij["formulier"]} |')
    regels += ['', '## Uitgangspunten', ''] + [f'- {s}' for s in case.uitgangspunten]
    regels += ['', '## Resultaatbetekenis', '',
               '`verschuldigd_ib_pvv_p1` (en P2): inkomstenbelasting box 1 + box 3 en',
               'premies volksverzekeringen NA toegepaste heffingskortingen, VOOR verrekening',
               'van loonheffing en voorlopige aanslagen. NIET het bedrag te betalen/ontvangen.',
               'Zvw hoort niet in dit veld. Leg bij partners beide persoonsuitkomsten vast.',
               'Detailvelden zijn optioneel; ontbrekend betekent onbekend, nooit nul.',
               'Woningverdeling 100% bij alleenstaanden, 50/50 bij partners. Leg ook de',
               'box-3-verdelingskeuze expliciet vast; de vergelijking gebruikt het huishoudtotaal.',
               'Bevestig bij afronden dat alle OLA-invoer en keuzes overeenkomen met dit blad.']
    return '\n'.join(regels) + '\n'


def controleer_bewijs(directory: Path, bron: dict[str, Any]) -> None:
    controleer_url(bron['bron_url'])
    if '/ib/aangifte/2025/' not in bron['bron_url'] or bron.get('formulier') != 'IH2025 versie 1':
        raise ValueError('Bron is geen IH2025-simulatie.')
    for veld, waarneming in bron.get('waarnemingen', {}).items():
        controleer_url(waarneming['url'])
        bewijs = waarneming.get('bewijs', {})
        if not bewijs or not any(naam.endswith('.png') for naam in bewijs) or not any(naam.endswith('.txt') for naam in bewijs):
            raise ValueError(f'Ontbrekend bronbewijs voor {veld}.')
        for naam, verwacht in bewijs.items():
            pad = directory / naam
            if Path(naam).name != naam or pad.is_symlink():
                raise ValueError('Bewijspad moet een lokaal bestand in deze run zijn.')
            if hashlib.sha256(pad.read_bytes()).hexdigest() != verwacht:
                raise ValueError(f'Gewijzigd bronbewijs: {naam}')


def schrijf_vergelijking(directory: Path, case: Case, bron: dict[str, Any], engine: dict[str, Any]) -> dict[str, Any]:
    controleer_bewijs(directory, bron)
    resultaat = vergelijk(case, bron, engine)
    schrijf_json(directory / 'vergelijking.json', resultaat)
    with (directory / 'verschillen.csv').open('w', newline='', encoding='utf-8') as bestand:
        writer = csv.DictWriter(bestand, fieldnames=['veld', 'ola', 'pensioen', 'verschil', 'status'])
        writer.writeheader()
        writer.writerows(resultaat['verschillen'])
    regels = [f'# {case.case_id}: {resultaat["status"]}', '',
              f'Tolerantie per vergelijking: € {case.tolerantie}. Dekking: {resultaat["dekking"]}.',
              '', '| Veld | OLA | Pensioen | Verschil | Status |', '| --- | ---: | ---: | ---: | --- |']
    regels += ['| ' + ' | '.join(str(r[k]) for k in ['veld', 'ola', 'pensioen', 'verschil', 'status']) + ' |'
               for r in resultaat['verschillen']]
    if resultaat['formulierafrondingen']:
        regels += ['', '## Expliciete formulierafronding', '',
                   'Engine en case behouden centen; OLA ontvangt de hieronder vermelde hele euro’s.',
                   '| Invoerpad | Case/engine | Formulier |', '| --- | ---: | ---: |']
        regels += [f'| {r["pad"]} | {r["case"]} | {r["formulier"]} |' for r in resultaat['formulierafrondingen']]
    if resultaat['invoerverschillen']:
        regels += ['', '## Invoer niet gelijk', '',
                   'Eerst de bronkeuze onderzoeken; fiscale verschillen zijn nog niet vergelijkbaar.',
                   '```json', json.dumps(resultaat['invoerverschillen'], indent=2), '```']
    regels += ['', 'PASS geldt alleen voor de vastgelegde velden en deze tolerantie.',
               'Dit rapport wijzigt geen belastingtarieven of referentiebaselines.']
    (directory / 'rapport.md').write_text('\n'.join(regels) + '\n', encoding='utf-8')
    return resultaat


def run_case(case: Case, root: Path, actie: str, controleur: str, headless: bool, terminal: bool = False) -> int:
    directory = nieuwe_run(root, case)
    schrijf_json(directory / 'case.json', case.model_dump(mode='json'))
    (directory / 'invulblad.md').write_text(invulblad(case), encoding='utf-8')
    print(directory)
    try:
        engine = engine_resultaat(case)
        schrijf_json(directory / 'pensioen.json', engine)
        revision = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=False)
        schrijf_json(directory / 'run.json', {'status': 'voorbereid', 'case_hash': case_hash(case),
                     'git_head': revision.stdout.strip(), 'tarieven_hash': engine['tarieven_hash'],
                     'opmerking': 'pensioen.json bevat de exacte engine-output; git_head kan lokale wijzigingen uitsluiten.'})
        if actie == 'voorbereiden':
            return 0
        from tools.ola.browser import simuleer
        catalogus = ontdek_casussen()
        if case.ola.casus not in catalogus:
            raise ValueError('Gekozen 2025-casus niet beschikbaar.')
        case, bron = simuleer(case, catalogus[case.ola.casus], directory,
                             opname=actie == 'opnemen', controleur=controleur, headless=headless, terminal=terminal)
        schrijf_json(directory / 'case.json', case.model_dump(mode='json'))
        schrijf_json(directory / 'ola.json', bron)
        resultaat = schrijf_vergelijking(directory, case, bron, engine)
        schrijf_json(directory / 'run.json', {'status': resultaat['status'], 'case_hash': case_hash(case),
                     'git_head': revision.stdout.strip(), 'tarieven_hash': engine['tarieven_hash']})
        print(resultaat['status'])
        return 0 if resultaat['status'] == 'PASS' else 1
    except (Exception, KeyboardInterrupt) as exc:
        schrijf_json(directory / 'run.json', {'status': 'ONVOLLEDIG', 'fout': str(exc) or 'Afgebroken',
                     'case_hash': case_hash(case)})
        print(f'ONVOLLEDIG: {exc}', file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='OLA IH2025: caseconfig → simulatiebewijs → enginevergelijking')
    subs = parser.add_subparsers(dest='actie', required=True)
    subs.add_parser('catalogus', help='Ontdek beschikbare IH2025-casussen op de officiële website')
    for actie in ('voorbereiden', 'opnemen', 'uitvoeren'):
        sub = subs.add_parser(actie)
        sub.add_argument('case', type=Path)
        sub.add_argument('--output', type=Path, default=Path('validatie/ola/runs'))
        if actie == 'opnemen':
            sub.add_argument('--terminal', action='store_true', help='Stappen als JSON en zichtbare scherminspectie')
            sub.add_argument('--headless', action='store_true')
        if actie == 'uitvoeren':
            sub.add_argument('--controleur', required=True, help='Wie heeft het recept en de veldbetekenis gecontroleerd?')
            sub.add_argument('--headless', action='store_true')
    sub = subs.add_parser('batch', help='Herhaal alle opgenomen case-configs in een map')
    sub.add_argument('map', type=Path)
    sub.add_argument('--output', type=Path, default=Path('validatie/ola/runs'))
    sub.add_argument('--controleur', required=True)
    sub.add_argument('--headless', action='store_true')
    sub = subs.add_parser('vergelijken', help='Vergelijk bewaarde OLA-referentie met de huidige engine')
    sub.add_argument('run', type=Path)
    sub = subs.add_parser('exporteren', help='Maak een kandidaat voor bestaande raw-testcases; overschrijft geen baseline')
    sub.add_argument('run', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.actie == 'catalogus':
            print(json.dumps(ontdek_casussen(), ensure_ascii=False, indent=2))
            return 0
        if args.actie in {'vergelijken', 'exporteren'}:
            case = laad_case(args.run / 'case.json')
            bron = json.loads((args.run / 'ola.json').read_text(encoding='utf-8'))
            controleer_bewijs(args.run, bron)
            # Elke hervergelijking krijgt een eigen submap; originele engine-output blijft behouden.
            doel = args.run / ('vergelijking-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8])
            doel.mkdir()
            engine = engine_resultaat(case)
            resultaat = vergelijk(case, bron, engine)
            if args.actie == 'exporteren':
                schrijf_json(doel / (case.case_id + '.json'), raw_kandidaat(case, bron, engine))
            schrijf_json(doel / 'pensioen.json', engine)
            schrijf_json(doel / 'vergelijking.json', resultaat)
            print(f'{resultaat["status"]}: {doel}')
            return 0 if resultaat['status'] == 'PASS' else 1
        if args.actie == 'batch':
            bestanden = sorted(args.map.glob('*.json'))
            if not bestanden:
                raise ValueError('Geen case-configuraties gevonden.')
            return max(run_case(laad_case(p), args.output, 'uitvoeren', args.controleur, args.headless) for p in bestanden)
        return run_case(laad_case(args.case), args.output, args.actie,
                        getattr(args, 'controleur', ''), getattr(args, 'headless', False), getattr(args, 'terminal', False))
    except Exception as exc:
        print(f'FOUT: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
