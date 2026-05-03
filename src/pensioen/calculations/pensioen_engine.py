"""Pro-rata pensioenberekening per kalendermaand."""

from __future__ import annotations

import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from pensioen.models.pensioen_record import PensioenRecord, TypePensioen

CENT = Decimal("0.01")


def _rond_af(bedrag: Decimal) -> Decimal:
    return bedrag.quantize(CENT, rounding=ROUND_HALF_UP)


def _bruto_per_maand(record: PensioenRecord, jaar: int) -> Decimal:
    """
    Bereken het bruto maandbedrag voor een pensioenjaar, inclusief indexatie.

    Indexatie wordt samengesteld berekend per jaar since de ingangsdatum.
    Er wordt altijd de verwachte (niet gegarandeerde) indexatie toegepast.
    """
    if record.ingangsdatum is None:
        return Decimal("0")

    bruto_jaar = record.bruto_per_jaar
    indexatie = record.indexatie_verwacht_pct / Decimal("100")

    if indexatie > Decimal("0"):
        jaren_na_ingang = max(0, jaar - record.ingangsdatum.year)
        groeifactor = (Decimal("1") + indexatie) ** jaren_na_ingang
        bruto_jaar = _rond_af(bruto_jaar * groeifactor)

    return bruto_jaar / Decimal("12")


def bereken_pensioen_maand(
    record: PensioenRecord,
    jaar: int,
    maand: int,
) -> Decimal:
    """
    Bereken het bruto pensioenbedrag voor één kalendermaand.

    Houdt rekening met:
    - Ingangsdatum (pro-rata voor de eerste maand)
    - Einddatum (pro-rata voor de laatste maand)
    - Indexatie (samengesteld, jaarlijks)

    Voor type PARTNER en NABESTAANDEN geeft deze functie 0 terug (aparte logica).

    Returns:
        Bruto pensioenbedrag voor de maand in euro's.
    """
    if record.ingangsdatum is None:
        return Decimal("0")

    # Typen die niet als regulier inkomen meetellen
    if record.type_pensioen in (TypePensioen.PARTNER, TypePensioen.NABESTAANDEN):
        return Decimal("0")

    maand_begin = date(jaar, maand, 1)
    dagen_in_maand = calendar.monthrange(jaar, maand)[1]
    maand_eind = date(jaar, maand, dagen_in_maand)

    # Pensioen nog niet ingegaan
    if record.ingangsdatum > maand_eind:
        return Decimal("0")

    # Pensioen al geëindigd
    if record.einddatum and record.einddatum < maand_begin:
        return Decimal("0")

    maand_bedrag = _bruto_per_maand(record, jaar)

    # Pro-rata voor de eerste maand
    if record.ingangsdatum > maand_begin:
        resterende_dagen = dagen_in_maand - record.ingangsdatum.day + 1
        maand_bedrag = _rond_af(
            maand_bedrag * Decimal(str(resterende_dagen)) / Decimal(str(dagen_in_maand))
        )

    # Pro-rata voor de laatste maand
    elif record.einddatum and record.einddatum < maand_eind:
        gelopen_dagen = record.einddatum.day
        maand_bedrag = _rond_af(
            maand_bedrag * Decimal(str(gelopen_dagen)) / Decimal(str(dagen_in_maand))
        )

    return maand_bedrag


def bereken_aow_maand(
    geboortedatum: date,
    aow_datum: date,
    bedrag_per_maand: Decimal,
    jaar: int,
    maand: int,
) -> Decimal:
    """
    Bereken het bruto AOW-bedrag voor één kalendermaand.

    Houdt rekening met de exacte AOW-ingangsdatum (pro-rata voor de eerste maand).

    Args:
        geboortedatum: Geboortedatum (niet direct gebruikt, voor context).
        aow_datum: Exacte AOW-ingangsdatum uit aow_engine.bereken_aow_datum().
        bedrag_per_maand: Bruto maandbedrag uit belastingconfig.
        jaar: Kalenderjaar.
        maand: Kalendermaand (1–12).

    Returns:
        Bruto AOW-bedrag voor de maand.
    """
    maand_begin = date(jaar, maand, 1)
    dagen_in_maand = calendar.monthrange(jaar, maand)[1]
    maand_eind = date(jaar, maand, dagen_in_maand)

    # AOW nog niet ingegaan
    if aow_datum > maand_eind:
        return Decimal("0")

    # AOW al volledig lopend
    if aow_datum <= maand_begin:
        return bedrag_per_maand

    # Pro-rata eerste maand
    resterende_dagen = dagen_in_maand - aow_datum.day + 1
    return _rond_af(
        bedrag_per_maand * Decimal(str(resterende_dagen)) / Decimal(str(dagen_in_maand))
    )


def bereken_arbeid_maand(
    bruto_jaarsalaris: Decimal,
    stopdatum: date,
    jaar: int,
    maand: int,
) -> Decimal:
    """
    Bereken het bruto arbeidsinkomen voor één kalendermaand.

    Pro-rata voor de stopmaand (werkt t/m de stopdatum).

    Args:
        bruto_jaarsalaris: Bruto jaarsalaris voor dit jaar.
        stopdatum: Datum van laatste werkdag.
        jaar: Kalenderjaar.
        maand: Kalendermaand (1–12).

    Returns:
        Bruto arbeidsinkomen voor de maand.
    """
    maand_begin = date(jaar, maand, 1)
    dagen_in_maand = calendar.monthrange(jaar, maand)[1]
    maand_eind = date(jaar, maand, dagen_in_maand)

    # Werk al gestopt vóór deze maand
    if stopdatum < maand_begin:
        return Decimal("0")

    # Werk duurt heel de maand door
    if stopdatum >= maand_eind:
        return bruto_jaarsalaris / Decimal("12")

    # Pro-rata: werkt t/m stopdatum.day in deze maand
    gewerkte_dagen = stopdatum.day
    return _rond_af(
        (bruto_jaarsalaris / Decimal("12"))
        * Decimal(str(gewerkte_dagen))
        / Decimal(str(dagen_in_maand))
    )
