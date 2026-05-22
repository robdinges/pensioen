"""Vermogensontwikkeling berekening met maandelijks samengesteld rendement."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from pensioen.models.vermogensitem import VermogensItem, VermogensType

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


# ===== Nieuwe functionaliteit voor VermogensItems =====


def bereken_vermogen_totaal(vermogensitems: list[VermogensItem], peildatum: date) -> Decimal:
    """
    Bereken totaal vermogen op een specifieke datum uit lijst van VermogensItems.
    
    Args:
        vermogensitems: Lijst van VermogensItems (spaargeld, beleggingen, bezittingen).
        peildatum: Datum waarop vermogen wordt berekend.
    
    Returns:
        Totaal vermogen in euro's.
    """
    totaal = Decimal("0")
    for item in vermogensitems:
        totaal += item.waarde_op_datum(peildatum)
    
    return totaal


def bereken_vermogen_box3_belast(vermogensitems: list[VermogensItem], peildatum: date) -> Decimal:
    """
    Bereken box 3 belast vermogen op een specifieke datum.
    
    Alleen items waarbij box3_belast=True worden meegeteld.
    
    Args:
        vermogensitems: Lijst van VermogensItems.
        peildatum: Datum waarop vermogen wordt berekend.
    
    Returns:
        Box 3 belast vermogen in euro's.
    """
    totaal = Decimal("0")
    for item in vermogensitems:
        if item.box3_belast and item.is_actief_op(peildatum):
            totaal += item.waarde_op_datum(peildatum)
    
    return totaal


def bereken_vermogen_per_type(
    vermogensitems: list[VermogensItem], 
    peildatum: date
) -> dict[VermogensType, Decimal]:
    """
    Bereken vermogen per VermogensType op een specifieke datum.
    
    Args:
        vermogensitems: Lijst van VermogensItems.
        peildatum: Datum waarop vermogen wordt berekend.
    
    Returns:
        Dictionary met per VermogensType het totale vermogen.
    """
    per_type: dict[VermogensType, Decimal] = {}
    
    for item in vermogensitems:
        if item.is_actief_op(peildatum):
            waarde = item.waarde_op_datum(peildatum)
            if item.type in per_type:
                per_type[item.type] += waarde
            else:
                per_type[item.type] = waarde
    
    return per_type


def update_vermogensitems_waarde(
    vermogensitems: list[VermogensItem],
    peildatum: date,
    cashflow_netto: Decimal,
) -> list[VermogensItem]:
    """
    Update de waarde van vermogensitems met netto cashflow.
    
    Voor SPAARGELD en BELEGGINGEN items wordt de aanschafwaarde verhoogd met het
    overschot (positief) of verlaagd met het tekort (negatief).
    
    Voor fysieke bezittingen (AUTO, KUNST, etc.) blijft de aanschafwaarde ongewijzigd;
    deze worden gewaardeerd via groei_pct.
    
    Args:
        vermogensitems: Lijst van VermogensItems (wordt gekopieerd).
        peildatum: Datum waarop cashflow wordt toegevoegd.
        cashflow_netto: Netto cashflow (positief=overschot, negatief=tekort).
    
    Returns:
        Nieuwe lijst VermogensItems met bijgewerkte waarden.
    """
    # Maak kopie van lijst
    nieuwe_items = [item.model_copy(deep=True) for item in vermogensitems]
    
    if cashflow_netto == Decimal("0"):
        return nieuwe_items
    
    # Zoek spaargeld en beleggingen items
    liquide_items = [
        item for item in nieuwe_items 
        if item.type in (VermogensType.SPAARGELD, VermogensType.BELEGGINGEN) 
        and item.is_actief_op(peildatum)
    ]
    
    if not liquide_items:
        # Geen liquide items: maak nieuw spaargeld item
        nieuw_item = VermogensItem(
            omschrijving="Spaargeld (automatisch aangemaakt)",
            type=VermogensType.SPAARGELD,
            persoon="Huishouden",
            aanschafwaarde=cashflow_netto,
            aanschafdatum=peildatum,
            groei_pct=Decimal("0"),  # Groei wordt via rente berekend in cashflow_engine
            box3_belast=True,
        )
        nieuwe_items.append(nieuw_item)
        return nieuwe_items
    
    # Verdeel cashflow over liquide items naar rato huidige waarde
    totaal_liquide = sum(item.waarde_op_datum(peildatum) for item in liquide_items)
    
    for item in liquide_items:
        if totaal_liquide > Decimal("0"):
            # Pro-rata verdeling
            fractie = item.waarde_op_datum(peildatum) / totaal_liquide
            item.aanschafwaarde += cashflow_netto * fractie
        else:
            # Gelijk verdelen over liquide items
            item.aanschafwaarde += cashflow_netto / Decimal(str(len(liquide_items)))
        
        # Aanschafwaarde kan niet negatief
        item.aanschafwaarde = max(Decimal("0"), item.aanschafwaarde)
    
    return nieuwe_items
