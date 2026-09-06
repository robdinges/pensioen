"""Ontdek IH2025 via het openbare, sessiegebonden Wicket-formulier."""
from __future__ import annotations

import html
import re
import ssl
from pathlib import Path
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from urllib.parse import urlencode, urljoin
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from tools.ola.modellen import CATALOGUS_URL, controleer_url


class VeiligeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        controleer_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class CatalogusParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.form_action: str | None = None
        self.form_data: dict[str, str] = {}
        self.waarde_2025: str | None = None
        self.casussen: dict[str, str] = {}
        self._in_form = False
        self._option: str | None = None
        self._tekst = ''

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == 'form':
            self._in_form = 'formulierenForm' in (a.get('action') or '')
            if self._in_form:
                self.form_action = a.get('action')
        if self._in_form and tag == 'input' and a.get('type') == 'hidden' and a.get('name'):
            self.form_data[a['name']] = a.get('value') or ''
        if self._in_form and tag == 'option':
            self._option, self._tekst = a.get('value'), ''
        if tag == 'tr' and (a.get('id') or '').endswith('_openen'):
            match = re.search(r"window\.open\('([^']+)'", html.unescape(a.get('onclick') or ''))
            if match:
                url = match.group(1)
                controleer_url(url)
                if '/ib/aangifte/2025/' in url:
                    self.casussen[a['id'][:-7]] = url

    def handle_data(self, data: str) -> None:
        if self._option is not None:
            self._tekst += data

    def handle_endtag(self, tag: str) -> None:
        if tag == 'option':
            if self._tekst.strip() == '2025| IH2025 versie 1':
                self.waarde_2025 = self._option
            self._option = None
        if tag == 'form':
            self._in_form = False


def ontdek_casussen() -> dict[str, str]:
    """Maak een verse sessie en selecteer op label, niet op een vast Wicket-ID."""
    context = ssl.create_default_context()
    if ssl.get_default_verify_paths().cafile is None and Path("/etc/ssl/cert.pem").is_file():
        context.load_verify_locations("/etc/ssl/cert.pem")
    opener = build_opener(HTTPCookieProcessor(CookieJar()), VeiligeRedirect(), HTTPSHandler(context=context))
    with opener.open(CATALOGUS_URL, timeout=30) as response:
        basis = response.url
        parser = CatalogusParser()
        parser.feed(response.read(2_000_000).decode('utf-8'))
    if not parser.form_action or parser.waarde_2025 is None:
        raise ValueError('IH2025 versie 1 niet gevonden; catalogusadapter controleren.')
    target = urljoin(basis, parser.form_action)
    controleer_url(target)
    payload = {**parser.form_data, 'formulierenSelect': parser.waarde_2025}
    request = Request(target, data=urlencode(payload).encode(), method='POST')
    with opener.open(request, timeout=30) as response:
        result = CatalogusParser()
        result.feed(response.read(2_000_000).decode('utf-8'))
    if not result.casussen:
        raise ValueError('Geen IH2025-casussen gevonden; geen ander jaar als fallback.')
    return result.casussen
