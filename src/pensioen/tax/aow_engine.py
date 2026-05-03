"""AOW-leeftijdberekeningen op basis van de SVB-tabel."""

from __future__ import annotations

import calendar
import json
import logging
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_DIR = Path(__file__).parents[3] / "config"
CONFIG_DIR = Path(os.environ.get("PENSIOEN_CONFIG_DIR", _DEFAULT_CONFIG_DIR))


def _laad_aow_tabel() -> list[dict]:
    """Laad de SVB AOW-leeftijdentabel uit JSON."""
    bestand = CONFIG_DIR / "aow_leeftijden.json"
    if not bestand.exists():
        raise FileNotFoundError(
            f"AOW-leeftijdentabel niet gevonden: {bestand}. "
            "Zorg dat config/aow_leeftijden.json aanwezig is."
        )
    with bestand.open(encoding="utf-8") as f:
        data = json.load(f)
    return data["tabel"]


def _zoek_aow_leeftijd(geboortejaar: int, tabel: list[dict]) -> tuple[int, int]:
    """
    Zoek de AOW-leeftijd (jaren, maanden) op voor het gegeven geboortejaar.

    Raises:
        ValueError: als het geboortejaar niet in de tabel gevonden wordt.
    """
    for rij in tabel:
        if "max_geboortejaar" in rij and geboortejaar <= rij["max_geboortejaar"]:
            return rij["jaren"], rij["maanden"]
        if "geboortejaar" in rij and geboortejaar == rij["geboortejaar"]:
            return rij["jaren"], rij["maanden"]
        if "min_geboortejaar" in rij and geboortejaar >= rij["min_geboortejaar"]:
            return rij["jaren"], rij["maanden"]

    raise ValueError(
        f"AOW-leeftijd voor geboortejaar {geboortejaar} niet gevonden in tabel. "
        "Voeg het geboortejaar toe aan config/aow_leeftijden.json."
    )


def _voeg_jaren_toe(d: date, jaren: int) -> date:
    """Voeg jaren toe aan een datum; behandel 29-feb edge case."""
    try:
        return d.replace(year=d.year + jaren)
    except ValueError:
        # 29 februari in niet-schrikkeljaar → 28 februari
        return d.replace(year=d.year + jaren, day=28)


def _voeg_maanden_toe(d: date, maanden: int) -> date:
    """Voeg maanden toe aan een datum; behandel kortere maanden correct."""
    totale_maanden = d.month - 1 + maanden
    nieuw_jaar = d.year + totale_maanden // 12
    nieuwe_maand = (totale_maanden % 12) + 1
    max_dag = calendar.monthrange(nieuw_jaar, nieuwe_maand)[1]
    return date(nieuw_jaar, nieuwe_maand, min(d.day, max_dag))


def bereken_aow_datum(geboortedatum: date) -> date:
    """
    Bereken de exacte AOW-ingangsdatum op basis van de geboortedatum.

    Gebruikt de officiële SVB-tabel uit config/aow_leeftijden.json.
    AOW gaat in op de dag van de verjaardag in het AOW-leeftijdjaar.
    """
    tabel = _laad_aow_tabel()
    jaren, maanden = _zoek_aow_leeftijd(geboortedatum.year, tabel)
    datum_na_jaren = _voeg_jaren_toe(geboortedatum, jaren)
    return _voeg_maanden_toe(datum_na_jaren, maanden)


def is_aow_gerechtigd(geboortedatum: date, peildatum: date) -> bool:
    """Geeft True als de persoon op de peildatum AOW-gerechtigd is."""
    aow_datum = bereken_aow_datum(geboortedatum)
    return peildatum >= aow_datum


def aow_breuk_jaar(geboortedatum: date, jaar: int) -> Decimal:
    """
    Bereken het deel van het jaar dat een persoon AOW-gerechtigd is (0.0–1.0).

    Voor maandmodel-belastingberekening: de breuk bepaalt de weging tussen
    het AOW- en niet-AOW-belastingtarief.

    Voorbeelden:
    - Heel jaar AOW (aow-datum vóór 1 jan) → 1.0
    - Heel jaar geen AOW (aow-datum na 31 dec) → 0.0
    - AOW ingaat op 1 juli → 0.5 (6 volledige maanden / 12)
    - AOW ingaat op 17 september → (rest-sept pro-rata + 3 volle maanden) / 12

    Returns:
        Decimal breuk van het jaar als AOW-gerechtigd.
    """
    aow_datum = bereken_aow_datum(geboortedatum)

    # Heel jaar AOW
    if aow_datum <= date(jaar, 1, 1):
        return Decimal("1")

    # Heel jaar geen AOW
    if aow_datum > date(jaar, 12, 31):
        return Decimal("0")

    # Gedeeltelijk jaar: AOW start in dit jaar
    aow_maand = aow_datum.month

    # Pro-rata voor de startmaand op basis van dagentelling
    dagen_in_maand = calendar.monthrange(jaar, aow_maand)[1]
    resterende_dagen = Decimal(str(dagen_in_maand - aow_datum.day + 1))
    aow_breuk_startmaand = resterende_dagen / Decimal(str(dagen_in_maand))

    # Volledige maanden na de startmaand
    volledige_aow_maanden = Decimal(str(12 - aow_maand))

    totaal_aow_maanden = volledige_aow_maanden + aow_breuk_startmaand
    return totaal_aow_maanden / Decimal("12")
