"""Lokale, geïsoleerde Playwright-opname en herhaling van OLA-cases.

De opname bedient alleen expliciet gekozen schermvelden. Geen verborgen
OLA-rekenfuncties; schermselectors worden per case vastgelegd.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Any

from tools.ola.modellen import Case, Locator, RESULTAATVELDEN, Stap, case_hash, controleer_url, waarde_op_pad, hele_euro_omlaag
from tools.ola.vergelijking import lees_euro

PICKER_SCRIPT = r"""
(() => {
  function locator(el) {
    if (el.labels && el.labels.length === 1) {
      const label = el.labels[0].innerText.trim();
      if (label) return {soort:'label', waarde:label};
    }
    const aria = el.getAttribute('aria-label');
    if (aria) return {soort:'label', waarde:aria};
    if (el.tagName === 'BUTTON' || el.tagName === 'A') {
      const text = el.innerText.trim();
      if (text) return {soort:'role', rol:el.tagName === 'A' ? 'link' : 'button', waarde:text};
    }
    const parts = [];
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      if (n.id) {
        parts.unshift('#' + CSS.escape(n.id));
        break;
      }
      const peers = n.parentElement ? Array.from(n.parentElement.children).filter(s => s.tagName === n.tagName) : [n];
      parts.unshift(n.tagName.toLowerCase() + ':nth-of-type(' + (peers.indexOf(n) + 1) + ')');
    }
    return {soort:'css', waarde:parts.join(' > ')};
  }
  document.addEventListener('click', e => {
    if (!e.altKey) return;
    e.preventDefault(); e.stopImmediatePropagation();
    const el = e.target.closest('button, a, input, select, textarea') || e.target;
    window.olaPick({locator:locator(el)});
  }, true);
})();
"""


def browser_dependency() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError('Installeer eerst: pip install -e ".[ola]" en python3 -m playwright install chromium') from exc
    return sync_playwright


def element(page: Any, locator: Locator) -> Any:
    if locator.soort == 'label':
        result = page.get_by_label(locator.waarde, exact=True)
    elif locator.soort == 'role':
        result = page.get_by_role(locator.rol, name=locator.waarde, exact=True)
    elif locator.soort == 'text':
        result = page.get_by_text(locator.waarde, exact=True)
    else:
        result = page.locator(locator.waarde)
    result.wait_for(state='visible')
    if result.count() != 1:
        raise ValueError(f'Locator is niet uniek: {locator.model_dump()}')
    return result


def stap_waarde(case: Case, stap: Stap) -> str:
    waarde = waarde_op_pad(case.model_dump(mode='json'), stap.waarde_pad) if stap.waarde_pad else stap.waarde
    if waarde is None:
        raise ValueError('Ontbrekende stapwaarde.')
    if stap.formaat == 'euro_heel_omlaag':
        return hele_euro_omlaag(waarde)
    if stap.formaat == 'euro_nl':
        return waarde.replace('.', ',')
    if stap.formaat in {'datum_nl', 'dag', 'maand', 'jaar'}:
        datum = date.fromisoformat(waarde)
        return datum.strftime({'datum_nl':'%d-%m-%Y', 'dag':'%d', 'maand':'%m', 'jaar':'%Y'}[stap.formaat])
    return waarde


def bewaar_bewijs(page: Any, directory: Path, naam: str) -> dict[str, str]:
    controleer_url(page.url)
    png = directory / f'{naam}.png'
    tekst = directory / f'{naam}.txt'
    page.screenshot(path=str(png), full_page=True)
    tekst.write_text(page.locator('body').inner_text(), encoding='utf-8')
    (directory / f'{naam}.html').write_text(page.locator('body').inner_html(), encoding='utf-8')
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (png, tekst)}


def voer_stap_uit(page: Any, case: Case, stap: Stap, directory: Path) -> dict[str, Any] | None:
    controleer_url(page.url)
    target = element(page, stap.locator)
    if stap.actie == 'klik':
        target.click()
        if stap.locator.waarde == '#ola-akkoordbutton-screen':
            page.wait_for_timeout(1500)
            page.wait_for_load_state('networkidle')
    elif stap.actie == 'vul':
        target.fill(stap_waarde(case, stap))
        target.press('Tab')
    elif stap.actie == 'selecteer':
        target.select_option(label=stap_waarde(case, stap))
    elif stap.actie == 'vink':
        waarde = stap_waarde(case, stap)
        if waarde not in {'ja', 'nee'}:
            raise ValueError('Vinkkeuze moet ja of nee zijn.')
        target.set_checked(waarde == 'ja')
    elif stap.actie == 'lees':
        tekst = target.inner_text().strip()
        bedrag = lees_euro(tekst)
        return {'tekst': tekst, 'bedrag': str(bedrag), 'url': page.url,
                'locator': stap.locator.model_dump(mode='json'),
                'vastgelegd_op': datetime.now(timezone.utc).isoformat(),
                'bewijs': bewaar_bewijs(page, directory, stap.veld)}
    # OLA bouwt vervolgvragen asynchroon op na wijzigingen en Akkoord.
    # Wacht op de netwerkverwerking voordat een volgend scherm wordt bediend.
    page.wait_for_timeout(250)
    page.wait_for_load_state('networkidle')
    return None


def controleer_recept(case: Case) -> None:
    gelezen = {s.veld for s in case.ola.stappen if s.actie == 'lees'}
    gebonden = {s.waarde_pad for s in case.ola.stappen if s.actie in {'vul', 'selecteer'}}
    ontbreekt = case.vereiste_velden() - gelezen
    invoer = case.vereiste_invoer() - gebonden
    if ontbreekt or invoer:
        raise ValueError(f'Recept onvolledig. Resultaatvelden: {sorted(ontbreekt)}; invoerbindingen: {sorted(invoer)}. Gebruik opnemen.')


def inspecteer_scherm(page: Any) -> dict[str, Any]:
    """Geef uitsluitend zichtbare DOM-elementen voor terminalbediening."""
    controleer_url(page.url)
    page.wait_for_load_state('networkidle')
    return {
        'url': page.url,
        'tekst': page.locator('body').inner_text(),
        'velden': page.locator('input, select, textarea, button, a, [role="button"]').evaluate_all("""els => els
            .filter(el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden')
            .map(el => ({tag: el.tagName, id: el.id, type: el.type,
                tekst: el.innerText, waarde: el.value,
                label: el.getAttribute('aria-label') || (el.labels ? Array.from(el.labels).map(l => l.innerText).join(' ') : ''),
                opties: el.options ? Array.from(el.options).map(o => o.text) : undefined}))"""),
    }


def terminal_opnemen(page: Any, case: Case, directory: Path) -> tuple[Case, dict[str, Any], str]:
    """Bedien dezelfde gevalideerde stappen als JSON, zonder GUI-elementkiezer."""
    stappen: list[Stap] = []
    waarnemingen: dict[str, Any] = {}
    commands: Queue = Queue()
    Thread(target=_terminal, args=(commands,), daemon=True).start()
    print('scherm | JSON Stap | klaar CONTROLEUR | stop', flush=True)
    while True:
        page.wait_for_timeout(100)
        try:
            _, command = commands.get_nowait()
        except Empty:
            continue
        if command == 'stop':
            raise KeyboardInterrupt
        if command == 'scherm':
            print(json.dumps(inspecteer_scherm(page), ensure_ascii=False), flush=True)
            page.screenshot(path=str(directory / 'scherm.png'), full_page=True)
            continue
        if command.startswith('klaar '):
            nieuw = Case.model_validate({**case.model_dump(mode='json'), 'ola': {
                **case.ola.model_dump(mode='json'), 'stappen': [s.model_dump(mode='json') for s in stappen]}})
            controleer_recept(nieuw)
            return nieuw, waarnemingen, command[6:].strip()
        try:
            stap = Stap.model_validate_json(command)
            if stap.veld in waarnemingen:
                raise ValueError('Resultaatveld is al vastgelegd.')
            waarde = voer_stap_uit(page, case, stap, directory)
            stappen.append(stap)
            if waarde:
                waarnemingen[stap.veld] = waarde
            (directory / 'recept-concept.json').write_text(json.dumps(
                [s.model_dump(mode='json') for s in stappen], indent=2), encoding='utf-8')
            print(json.dumps({'stap': len(stappen), 'waarneming': waarde}), flush=True)
        except Exception as exc:
            print(f'Niet vastgelegd: {exc}', flush=True)


def _terminal(queue: Queue) -> None:
    while True:
        try:
            queue.put(('commando', input('ola> ').strip()))
        except EOFError:
            queue.put(('commando', 'stop'))
            return


def opnemen(page: Any, case: Case, directory: Path, events: Queue) -> tuple[Case, dict[str, Any], str]:
    print('Alle handelingen opnemen via de terminal + Alt-klik in de browser.')
    print('k = klik; v PAD [FORMAAT] = vul; s PAD = selecteer; c PAD = vink (ja/nee);')
    print('l RESULTAATVELD = lees bedrag; w TEKST = wacht op tekst; velden = resultaatnamen;')
    print('klaar CONTROLEUR = bevestig invoer/uitkomsten en bewaar; stop = afbreken.')
    print('Gebruik geen normale klikken/handmatige invoer: die worden niet opgenomen.')
    Thread(target=_terminal, args=(events,), daemon=True).start()
    stappen: list[Stap] = []
    waarnemingen: dict[str, Any] = {}
    opdracht: dict[str, Any] | None = None
    while not page.is_closed():
        page.wait_for_timeout(100)  # Pomp browser-events terwijl de terminal op invoer wacht.
        try:
            soort, data = events.get_nowait()
        except Empty:
            continue
        try:
            if soort == 'commando':
                onderdelen = data.split(maxsplit=2)
                if not onderdelen:
                    continue
                cmd = onderdelen[0]
                if cmd == 'stop':
                    raise KeyboardInterrupt
                if cmd == 'velden':
                    print('\n'.join(sorted(RESULTAATVELDEN)))
                elif cmd == 'klaar':
                    controleur = data[len('klaar'):].strip()
                    if not controleur:
                        raise ValueError('Vul een controleurnaam in.')
                    nieuw = Case.model_validate({**case.model_dump(mode='json'), 'ola': {
                        **case.ola.model_dump(mode='json'), 'stappen': [s.model_dump(mode='json') for s in stappen]}})
                    controleer_recept(nieuw)
                    return nieuw, waarnemingen, controleur
                elif cmd == 'w':
                    stap = Stap(actie='wacht_tekst', locator=Locator(soort='text', waarde=data[2:]))
                    voer_stap_uit(page, case, stap, directory)
                    stappen.append(stap)
                elif cmd in {'k', 'v', 's', 'c', 'l'}:
                    opdracht = {'actie': {'k':'klik', 'v':'vul', 's':'selecteer', 'c':'vink', 'l':'lees'}[cmd]}
                    if cmd in {'v', 's', 'c'}:
                        waarde_op_pad(case.model_dump(mode='json'), onderdelen[1])
                        opdracht['waarde_pad'] = onderdelen[1]
                        if len(onderdelen) == 3:
                            opdracht['formaat'] = onderdelen[2]
                    if cmd == 'l':
                        veld = onderdelen[1]
                        if veld not in RESULTAATVELDEN or veld in waarnemingen:
                            raise ValueError('Onbekend of al gelezen resultaatveld.')
                        opdracht['veld'] = veld
                    print('Alt-klik nu precies het bedoelde element; bij lezen alleen het bedrag.')
                else:
                    raise ValueError('Onbekend commando.')
            elif soort == 'pick' and opdracht:
                stap = Stap(**opdracht, locator=Locator.model_validate(data['locator']))
                waarde = voer_stap_uit(page, case, stap, directory)
                stappen.append(stap)
                if waarde:
                    waarnemingen[stap.veld] = waarde
                    print(f'{stap.veld}: {waarde["tekst"]}')
                print(f'Vastgelegd: {stap.actie} ({stap.locator.soort}: {stap.locator.waarde})')
                opdracht = None
        except (ValueError, IndexError) as exc:
            print(f'Niet vastgelegd: {exc}')
    raise RuntimeError('Browser gesloten voordat de opname was afgerond.')


def simuleer(case: Case, start_url: str, directory: Path, *, opname: bool = False,
             controleur: str = '', headless: bool = False, terminal: bool = False) -> tuple[Case, dict[str, Any]]:
    controleer_url(start_url)
    if '/ib/aangifte/2025/' not in start_url:
        raise ValueError('Geen IH2025-startadres.')
    if not opname:
        controleer_recept(case)
    events: Queue = Queue()
    with browser_dependency()() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(locale='nl-NL', timezone_id='Europe/Amsterdam', accept_downloads=False)
        try:
            context.set_default_timeout(case.ola.timeout_ms)
            def beveilig(route: Any) -> None:
                if route.request.is_navigation_request():
                    try:
                        controleer_url(route.request.url)
                    except ValueError:
                        route.abort()
                        return
                route.continue_()
            context.route('**/*', beveilig)
            if opname:
                context.expose_binding('olaPick', lambda source, data: events.put(('pick', data)))
                context.add_init_script(PICKER_SCRIPT)
            page = context.new_page()
            page.goto(start_url, wait_until='networkidle', timeout=60000)
            waarnemingen = {}
            if opname:
                case, waarnemingen, controleur = (terminal_opnemen(page, case, directory) if terminal
                    else opnemen(page, case, directory, events))
            else:
                for nr, stap in enumerate(case.ola.stappen, 1):
                    try:
                        waarde = voer_stap_uit(page, case, stap, directory)
                    except Exception:
                        bewaar_bewijs(page, directory, 'fout')
                        raise
                    if waarde:
                        waarnemingen[stap.veld] = waarde
                    (directory / 'voortgang.json').write_text(json.dumps({'laatste_stap': nr}), encoding='utf-8')
            if not controleur.strip():
                raise ValueError('Controleurnaam vereist: bevestig het eerder opgenomen recept.')
            return case, {'versie': 1, 'jaar': 2025, 'status': 'vastgelegd', 'case_id': case.case_id,
                          'case_hash': case_hash(case), 'bron_url': start_url,
                          'formulier': case.ola.formulier, 'controleur': controleur.strip(),
                          'vastgelegd_op': datetime.now(timezone.utc).isoformat(),
                          'waarnemingen': waarnemingen}
        finally:
            context.close()
            browser.close()
