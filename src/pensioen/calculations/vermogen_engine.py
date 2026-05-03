"""Vermogensontwikkeling berekening met maandelijks samengesteld rendement."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def _rond_af(bedrag: Decimal) -> Decimal:
    return bedrag.quantize(CENT, rounding=ROUND_HALF_UP)


def maandrendement(jaarrendement_pct: Decimal) -> Decimal:
    """
    Bereken het equivalente maandrendement op basis van jaarrendement.

    Formule: (1 + jaar%) ^ (1/12) - 1

    Returns:
        Maandrendement als Decimal (niet als percentage).
    """
    if jaarrendement_pct == Decimal("0"):
        return Decimal("0")
    jaar = jaarrendement_pct / Decimal("100")
    # Python werkt niet direct met Decimal voor machtsverheffing met fractionele exponent;
    # we gebruiken float als tussenstap en converteren terug.
    maand = Decimal(str((1 + float(jaar)) ** (1 / 12) - 1))
    return maand


def bereken_rente_maand(saldo: Decimal, jaarrendement_pct: Decimal) -> Decimal:
    """
    Bereken de rente/rendement voor één maand op basis van het beginsaldo.

    Args:
        saldo: Beginsaldo van de maand.
        jaarrendement_pct: Verwacht jaarrendement in % (bijv. 3.0 voor 3%).

    Returns:
        Rentetoevoeging voor de maand.
    """
    if saldo <= Decimal("0") or jaarrendement_pct == Decimal("0"):
        return Decimal("0")
    maand_rente = maandrendement(jaarrendement_pct)
    return _rond_af(saldo * maand_rente)


def bereken_vermogensontwikkeling(
    beginsaldo: Decimal,
    jaarrendement_pct: Decimal,
    mutaties: list[tuple[date, Decimal]],
    jaar_van: int,
    jaar_tot: int,
) -> list[tuple[date, Decimal]]:
    """
    Bereken het verloop van het vermogen over een reeks jaren.

    Args:
        beginsaldo: Beginsaldo op 1 januari van jaar_van.
        jaarrendement_pct: Verwacht jaarrendement in %.
        mutaties: Lijst van (datum, bedrag) voor stortingen (+) en onttrekkingen (-).
            Worden pro-rata verwerkt in de juiste kalendermaand.
        jaar_van: Eerste jaar van de prognose.
        jaar_tot: Laatste jaar van de prognose (inclusief).

    Returns:
        Lijst van (einde_maand_datum, saldo) per maand.
    """
    import calendar

    saldo = beginsaldo
    resultaten: list[tuple[date, Decimal]] = []

    # Zet mutaties om naar een dict per (jaar, maand)
    mutaties_per_maand: dict[tuple[int, int], Decimal] = {}
    for mutatie_datum, bedrag in mutaties:
        sleutel = (mutatie_datum.year, mutatie_datum.month)
        mutaties_per_maand[sleutel] = mutaties_per_maand.get(sleutel, Decimal("0")) + bedrag

    for jaar in range(jaar_van, jaar_tot + 1):
        for maand in range(1, 13):
            # Verwerk mutaties aan het begin van de maand
            mutatie = mutaties_per_maand.get((jaar, maand), Decimal("0"))
            saldo = saldo + mutatie

            # Rendement over het (gecorrigeerde) saldo
            rente = bereken_rente_maand(saldo, jaarrendement_pct)
            saldo = _rond_af(saldo + rente)

            # Saldo kan niet negatief worden (geen rood staan)
            saldo = max(Decimal("0"), saldo)

            # Einde-maand datum
            dag = calendar.monthrange(jaar, maand)[1]
            resultaten.append((date(jaar, maand, dag), saldo))

    return resultaten
