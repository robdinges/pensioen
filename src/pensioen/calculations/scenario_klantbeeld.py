"""Resultaten: begrijpelijke scenario-KPI's, uitsluitend uit bestaande cashflow."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from pensioen.models.cashflow import HuishoudCashflow
from pensioen.models.component import CategorieComponent
from pensioen.models.scenario import Scenario


def vergelijkingsperiode(scenarios: list[Scenario], jaar_van: int, jaar_tot: int) -> tuple[date, date, bool]:
    """Gelijke maanden na alle stopdatums; bij open arbeid expliciet hele horizon."""
    begin, einde = date(jaar_van, 1, 1), date(jaar_tot, 12, 31)
    arbeid = [c for s in scenarios for c in s.componenten
              if c.categorie == CategorieComponent.ARBEIDSINKOMEN
              and (c.bedrag > 0 or c.waarde_periodes)]
    if not arbeid or any(c.einddatum is None for c in arbeid):
        return begin, einde, False
    laatste = max((c.einddatum for c in arbeid if c.einddatum), default=None)
    if laatste:
        # Einddatum is inclusief. De eerste volledige maand erna is vergelijkbaar.
        volgend = date(laatste.year + (laatste.month == 12), laatste.month % 12 + 1, 1)
        begin = max(begin, volgend)
    return begin, einde, True


def bouw_klantbeeld(cashflow: HuishoudCashflow, begin: date, einde: date,
                    geboortedatum: date) -> dict[str, Any]:
    """Aggregeer maanduitkomsten zonder nieuwe fiscale of vermogensformules."""
    maanden = sorted((m for j in cashflow.jaren for m in j.maanden), key=lambda m: (m.jaar, m.maand))
    selectie = [m for m in maanden if begin <= date(m.jaar, m.maand, 1) <= einde]
    gemiddelde = ((sum((m.netto for m in selectie), Decimal('0')) / Decimal(len(selectie)))
                  .quantize(Decimal('.01'), rounding=ROUND_HALF_UP)) if selectie else None
    laagste = min(maanden, key=lambda m: m.vermogen_einde_maand) if maanden else None
    jaarregels = []
    for jaar in sorted(cashflow.jaren, key=lambda j: j.jaar):
        jaarregels.append({
            'jaar': jaar.jaar,
            'over_na_uitgaven': jaar.netto,
            'interen': max(-jaar.netto, Decimal('0')),
            'vermogen_eind': jaar.vermogen_einde_jaar,
            'negatief_vermogen': any(m.vermogen_einde_maand < 0 for m in jaar.maanden),
        })
    tekorten = [r for r in jaarregels if r['interen'] > 0]
    grootste = max(tekorten, key=lambda r: r['interen']) if tekorten else None
    tachtig = next((r for r in jaarregels if r['jaar'] == geboortedatum.year + 80), None)
    return {
        'gemiddeld_over_per_maand': gemiddelde,
        'aantal_maanden_gemiddelde': len(selectie),
        'grootste_jaartekort': grootste['interen'] if grootste else Decimal('0'),
        'grootste_jaartekort_jaar': grootste['jaar'] if grootste else None,
        'laagste_buffer': laagste.vermogen_einde_maand if laagste else None,
        'laagste_buffer_maand': f'{laagste.jaar:04d}-{laagste.maand:02d}' if laagste else None,
        'vermogen_op_80': tachtig['vermogen_eind'] if tachtig else None,
        'jaren_interen': len(tekorten),
        'jaren_negatief_vermogen': sum(r['negatief_vermogen'] for r in jaarregels),
        'jaarregels': jaarregels,
    }
