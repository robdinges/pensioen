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


def bereken_rente_maand(
    saldo: Decimal,
    jaarrendement_pct: Decimal,
    jaarrendement_sparen_pct: Decimal | None = None,
    jaarrendement_beleggen_pct: Decimal | None = None,
    spaargeld_fractie: Decimal = Decimal("1"),
) -> Decimal:
    """
    Bereken de rente/rendement voor één maand op basis van het beginsaldo.

    Als jaarrendement_sparen_pct en jaarrendement_beleggen_pct ingesteld zijn, wordt het
    saldo opgesplitst: spaargeld_fractie * saldo draagt jaarrendement_sparen_pct,
    (1 - spaargeld_fractie) * saldo draagt jaarrendement_beleggen_pct.

    Args:
        saldo: Beginsaldo van de maand.
        jaarrendement_pct: Verwacht jaarrendement in % (bijv. 3.0 voor 3%).
            Gebruikt als fallback als aparte rendementen niet ingesteld zijn.
        jaarrendement_sparen_pct: Rendement op spaargeld deel (optioneel).
        jaarrendement_beleggen_pct: Rendement op beleggelingen deel (optioneel).
        spaargeld_fractie: Fractie van saldo dat als spaargeld telt (0-1). Default 1 (alles spaargeld).

    Returns:
        Rentetoevoeging voor de maand.
    """
    if saldo <= Decimal("0"):
        return Decimal("0")
    
    # Als aparte rendementen ingesteld zijn, bereken met opgesplitst saldo
    if jaarrendement_sparen_pct is not None and jaarrendement_beleggen_pct is not None:
        saldo_sparen = saldo * spaargeld_fractie
        saldo_beleggen = saldo * (Decimal("1") - spaargeld_fractie)
        
        rente_sparen = Decimal("0")
        if saldo_sparen > Decimal("0") and jaarrendement_sparen_pct > Decimal("0"):
            maand_rente = maandrendement(jaarrendement_sparen_pct)
            rente_sparen = _rond_af(saldo_sparen * maand_rente)
        
        rente_beleggen = Decimal("0")
        if saldo_beleggen > Decimal("0") and jaarrendement_beleggen_pct > Decimal("0"):
            maand_rente = maandrendement(jaarrendement_beleggen_pct)
            rente_beleggen = _rond_af(saldo_beleggen * maand_rente)
        
        return rente_sparen + rente_beleggen
    
    # Fallback: gebruik enkel jaarrendement_pct
    if jaarrendement_pct == Decimal("0"):
        return Decimal("0")
    maand_rente = maandrendement(jaarrendement_pct)
    return _rond_af(saldo * maand_rente)


def bereken_vermogensontwikkeling(
    beginsaldo: Decimal,
    jaarrendement_pct: Decimal,
    mutaties: list[tuple[date, Decimal]],
    jaar_van: int,
    jaar_tot: int,
    jaarrendement_sparen_pct: Decimal | None = None,
    jaarrendement_beleggen_pct: Decimal | None = None,
    spaargeld_fractie: Decimal = Decimal("1"),
) -> list[tuple[date, Decimal]]:
    """
    Bereken het verloop van het vermogen over een reeks jaren.

    Args:
        beginsaldo: Beginsaldo op 1 januari van jaar_van.
        jaarrendement_pct: Verwacht jaarrendement in %.
            Gebruikt als fallback als aparte rendementen niet ingesteld zijn.
        mutaties: Lijst van (datum, bedrag) voor stortingen (+) en onttrekkingen (-).
            Worden pro-rata verwerkt in de juiste kalendermaand.
        jaar_van: Eerste jaar van de prognose.
        jaar_tot: Laatste jaar van de prognose (inclusief).
        jaarrendement_sparen_pct: Rendement op spaargeld deel (optioneel).
        jaarrendement_beleggen_pct: Rendement op beleggelingen deel (optioneel).
        spaargeld_fractie: Fractie van saldo dat als spaargeld telt (0-1). Default 1 (alles spaargeld).

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
            rente = bereken_rente_maand(
                saldo,
                jaarrendement_pct,
                jaarrendement_sparen_pct,
                jaarrendement_beleggen_pct,
                spaargeld_fractie,
            )
            saldo = _rond_af(saldo + rente)

            # Saldo kan niet negatief worden (geen rood staan)
            saldo = max(Decimal("0"), saldo)

            # Einde-maand datum
            dag = calendar.monthrange(jaar, maand)[1]
            resultaten.append((date(jaar, maand, dag), saldo))

    return resultaten
