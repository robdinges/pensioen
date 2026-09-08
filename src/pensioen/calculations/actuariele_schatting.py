"""Pensioen: actuariële gelijkwaardigheid met AG2024 en expliciete opbouwaanname."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
import json
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[3] / 'config'
CENT = Decimal('.01')


@lru_cache(maxsize=1)
def grondslagen() -> dict:
    return json.loads((CONFIG/'actuariele_schatting.json').read_text(),parse_float=Decimal)


@lru_cache(maxsize=1)
def sterftetafel() -> dict:
    return json.loads((CONFIG/'actuarieel_ag2024.json').read_text())


def maanden_tussen(vanaf: date, tot: date) -> int:
    return (tot.year-vanaf.year)*12+tot.month-vanaf.month


def maand_plus(vanaf: date, maanden: int) -> date:
    nummer=vanaf.year*12+vanaf.month-1+maanden
    return date(nummer//12,nummer%12+1,1)


@lru_cache(maxsize=128)
def overleving(geboorte: date, start: date) -> tuple[Decimal, ...]:
    """Maandelijkse overleving, 50/50 mix bij start; constante sterfte-intensiteit per qx."""
    tabel=sterftetafel()
    man=vrouw=Decimal('1')
    gewicht=Decimal(grondslagen()['sterftemix_man'])
    kansen=[]
    maand=0
    while True:
        datum=maand_plus(start,maand)
        leeftijd=datum.year-geboorte.year-((datum.month,datum.day)<(geboorte.month,geboorte.day))
        if leeftijd>tabel['leeftijd_tot']:
            break
        if leeftijd<0 or not tabel['jaar_van']<=datum.year<=tabel['jaar_tot']:
            raise ValueError('De leeftijden/datums vallen buiten de beschikbare AG2024-tabel (2025–2200).')
        kansen.append(gewicht*man+(1-gewicht)*vrouw)
        index=datum.year-tabel['jaar_van']
        man *= (1-Decimal(tabel['qx']['man'][leeftijd][index]))**(Decimal(1)/12)
        vrouw *= (1-Decimal(tabel['qx']['vrouw'][leeftijd][index]))**(Decimal(1)/12)
        maand+=1
    return tuple(kansen)


@lru_cache(maxsize=512)
def waardefactoren(geboorte: date, stop: date, normaal: date, rente: Decimal, indexatie: Decimal) -> dict[str, Decimal]:
    """Contante waarde van 1 euro maandpensioen, betaald aan begin van de maand."""
    if normaal<stop or rente<=-100 or indexatie<=-100:
        raise ValueError('Ongeldige pensioenperiode of rekenrente/indexatie.')
    wachttijd=maanden_tussen(stop,normaal)
    disconto=(1+rente/100)**(-Decimal(1)/12)
    groei=(1+indexatie/100)**(Decimal(1)/12)
    direct=uitgesteld=premies=Decimal('0')
    factor=Decimal('1')
    stijging=Decimal('1')
    for maand,kans in enumerate(overleving(geboorte,stop)):
        gewicht=kans*factor
        direct+=gewicht*stijging
        if maand>=wachttijd:
            uitgesteld+=gewicht*(groei**(maand-wachttijd))
        else:
            premies+=gewicht
        factor*=disconto
        stijging*=groei
    if direct<=0 or uitgesteld<=0:
        raise ValueError('Geen levenslange uitkering binnen de sterftetafel te waarderen.')
    return {'direct_factor':direct,'uitgesteld_factor':uitgesteld,'premie_factor':premies,
            'vervroegingsfactor':uitgesteld/direct}


def schat_regeling(bedrag: Decimal, geboorte: date, stop: date, normaal: date,
                   rente: Decimal, indexatie: Decimal, startleeftijd: int,
                   verdere_opbouw: bool, kostenopslag: Decimal) -> dict:
    """Lineaire opbouwproxy apart van actuariële vervroeging; geen fondsrechtenberekening."""
    start_opbouw=date(geboorte.year+startleeftijd,geboorte.month,1)
    totaal=maanden_tussen(start_opbouw,normaal)
    if verdere_opbouw and (totaal<=0 or stop<start_opbouw):
        raise ValueError('De aangenomen startleeftijd voor opbouw ligt na de stop- of pensioendatum.')
    opbouw=min(Decimal('1'),Decimal(maanden_tussen(start_opbouw,stop))/Decimal(totaal)) if verdere_opbouw else Decimal('1')
    factoren=waardefactoren(geboorte,stop,normaal,rente,indexatie)
    wachten=bedrag*opbouw
    direct=wachten*factoren['vervroegingsfactor']
    premie=((bedrag-wachten)*factoren['uitgesteld_factor']/factoren['premie_factor']*(1+kostenopslag/100)) if factoren['premie_factor'] else Decimal('0')
    return {'opbouwfactor':opbouw,**factoren,'direct_bruto_maand':direct.quantize(CENT,rounding=ROUND_HALF_UP),
            'wachten_bruto_maand':wachten.quantize(CENT,rounding=ROUND_HALF_UP),
            'doorbetalen_bruto_maand':bedrag.quantize(CENT,rounding=ROUND_HALF_UP),
            'premie_bruto_maand':premie.quantize(CENT,rounding=ROUND_HALF_UP)}
