"""Strikte configuratie- en broncontracten voor gewone IH2025-huishoudens."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator

OLA_HOST = 'opleiding-ola.belastingdienst.nl'
CATALOGUS_URL = f'https://{OLA_HOST}/ola-simulatie/casussen?1'
Geld = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid')


class PersoonCase(Model):
    naam: str = Field(min_length=1)
    geboortedatum: date
    bruto_arbeid: Geld = Decimal('0')
    bruto_pensioen: Geld = Decimal('0')
    bruto_aow: Geld = Decimal('0')


class VermogenCase(Model):
    spaargeld: Geld = Decimal('0')
    beleggingen: Geld = Decimal('0')


class WoningCase(Model):
    woz_waarde: Geld
    betaalde_hypotheekrente: Geld
    eigenwoningschuld: Geld
    verdeling_p1_pct: Literal[50, 100]


class Locator(Model):
    soort: Literal['label', 'role', 'text', 'css']
    waarde: str = Field(min_length=1)
    rol: str | None = None

    @model_validator(mode='after')
    def controleer(self) -> Locator:
        if (self.soort == 'role') != bool(self.rol):
            raise ValueError('Alleen een role-locator vereist rol.')
        return self


class Stap(Model):
    actie: Literal['klik', 'vul', 'selecteer', 'vink', 'lees', 'wacht_tekst']
    locator: Locator
    waarde_pad: str | None = None
    waarde: str | None = None
    veld: str | None = None
    formaat: Literal['tekst', 'datum_nl', 'dag', 'maand', 'jaar', 'euro_nl'] = 'tekst'

    @model_validator(mode='after')
    def controleer(self) -> Stap:
        invoer = self.actie in {'vul', 'selecteer', 'vink'}
        if invoer and (self.waarde_pad is None) == (self.waarde is None):
            raise ValueError('Invoerstap vereist precies één waarde_pad of waarde.')
        if not invoer and (self.waarde_pad is not None or self.waarde is not None):
            raise ValueError('Deze actie heeft geen invoerwaarde.')
        if (self.actie == 'lees') != bool(self.veld):
            raise ValueError('Alleen lees vereist een resultaatveld.')
        if self.veld and self.veld not in RESULTAATVELDEN:
            raise ValueError(f'Onbekend resultaatveld: {self.veld}')
        return self


class OlaConfig(Model):
    formulier: Literal['IH2025 versie 1'] = 'IH2025 versie 1'
    casus: Literal['Blanco'] = 'Blanco'
    keuzes: dict[str, str] = Field(default_factory=dict)
    stappen: list[Stap] = Field(default_factory=list)
    timeout_ms: int = Field(default=15000, ge=1000, le=60000)


class Case(Model):
    versie: Literal[1] = 1
    case_id: str = Field(pattern=r'^ola_2025_[a-z0-9_]+$')
    naam: str = Field(min_length=1)
    jaar: Literal[2025] = 2025
    fictieve_gegevens: Literal[True]
    huishouden: Literal['alleenstaand', 'fiscaal_partners_heel_jaar']
    personen: list[PersoonCase] = Field(min_length=1, max_length=2)
    vermogen: VermogenCase = Field(default_factory=VermogenCase)
    woning: WoningCase | None = None
    uitgangspunten: list[str] = Field(min_length=1)
    tolerantie: Geld = Decimal('1.00')
    ola: OlaConfig = Field(default_factory=OlaConfig)

    @model_validator(mode='after')
    def controleer(self) -> Case:
        aantal = 1 if self.huishouden == 'alleenstaand' else 2
        if len(self.personen) != aantal:
            raise ValueError('Aantal personen past niet bij huishouden.')
        if self.woning and self.woning.verdeling_p1_pct != (100 if aantal == 1 else 50):
            raise ValueError('Eerste versie ondersteunt woningverdeling 100% alleen / 50-50 partners.')
        for p in self.personen:
            if not date(1930, 1, 1) <= p.geboortedatum <= date(2007, 1, 1):
                raise ValueError('Deze tool ondersteunt volwassen personen, geboorte 1930–2007.')
        velden = [s.veld for s in self.ola.stappen if s.veld]
        if len(velden) != len(set(velden)):
            raise ValueError('Een resultaatveld mag maar eenmaal worden vastgelegd.')
        for s in self.ola.stappen:
            if s.waarde_pad:
                waarde_op_pad(self.model_dump(mode='json'), s.waarde_pad)
            if aantal == 1 and s.veld and s.veld.endswith('_p2'):
                raise ValueError('P2-resultaat bij eenpersoonshuishouden.')
        return self

    def vereiste_velden(self) -> set[str]:
        return {f'verschuldigd_ib_pvv_p{i + 1}' for i in range(len(self.personen))}

    def vereiste_invoer(self) -> set[str]:
        velden = {f'personen.{i}.geboortedatum' for i in range(len(self.personen))}
        for i, p in enumerate(self.personen):
            for veld in ('bruto_arbeid', 'bruto_pensioen', 'bruto_aow'):
                if getattr(p, veld):
                    velden.add(f'personen.{i}.{veld}')
        for veld in ('spaargeld', 'beleggingen'):
            if getattr(self.vermogen, veld):
                velden.add(f'vermogen.{veld}')
        if self.woning:
            velden |= {f'woning.{v}' for v in ('woz_waarde', 'betaalde_hypotheekrente', 'eigenwoningschuld')}
        return velden


# Geen fiscale formules: expliciete projectie uit accountant_detail.
DETAIL_MAPPING = {
    'bruto_arbeid': 'jaar_arbeid', 'bruto_pensioen': 'jaar_pen', 'bruto_aow': 'jaar_aow',
    'box1_ib_voor_kortingen': 'bel_voor_korting',
    'premie_aow': 'premie_aow', 'premie_anw': 'premie_anw', 'premie_wlz': 'premie_wlz',
    'ib_pvv_box1_voor_kortingen': 'totaal_ib_en_premies',
    'algemene_heffingskorting': 'ahk', 'arbeidskorting': 'ak',
    'ouderenkorting': 'ok', 'alleenstaandeouderenkorting': 'aok',
    'verrekende_heffingskortingen': 'verrekende_hk',
    'box1_na_kortingen': 'netto_bel',
}
RESULTAATVELDEN = {
    f'{veld}_p{i}' for veld in DETAIL_MAPPING for i in (1, 2)
} | {'verschuldigd_ib_pvv_p1', 'verschuldigd_ib_pvv_p2', 'box3_heffing'}


def waarde_op_pad(data: dict[str, Any], pad: str) -> str:
    waarde: Any = data
    try:
        for deel in pad.split('.'):
            waarde = waarde[int(deel)] if isinstance(waarde, list) else waarde[deel]
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise ValueError(f'Onbekend invoerpad: {pad}') from exc
    if not isinstance(waarde, (str, int, Decimal)) or isinstance(waarde, bool):
        raise ValueError(f'Invoerpad is geen tekst/getal: {pad}')
    return str(waarde)


def laad_case(pad: Path) -> Case:
    return Case.model_validate_json(pad.read_text(encoding='utf-8'))


def hash_json(data: Any) -> str:
    tekst = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=str)
    return hashlib.sha256(tekst.encode()).hexdigest()


def case_hash(case: Case) -> str:
    return hash_json(case.model_dump(mode='json'))


def controleer_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname != OLA_HOST or parsed.port not in (None, 443):
        raise ValueError('Alleen de openbare OLA-opleidingsomgeving is toegestaan.')
    if parsed.username or parsed.password:
        raise ValueError('Credentials in URL zijn niet toegestaan.')
