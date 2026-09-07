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
    if not jaarrendement_pct.is_finite() or jaarrendement_pct < Decimal("-100"):
        raise ValueError("Jaarrendement moet eindig zijn en minimaal -100% bedragen.")
    if jaarrendement_pct == Decimal("-100"):
        return Decimal("-1")
    return (Decimal("1") + jaarrendement_pct / Decimal("100")) ** (Decimal("1") / Decimal("12")) - Decimal("1")



def bereken_rente_maand(
    saldo: Decimal,
    jaarrendement_pct: Decimal | None = None,
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
            DEPRECATED: rendement wordt nu per vermogensitem ingesteld.
        jaarrendement_sparen_pct: Rendement op spaargeld deel (optioneel). DEPRECATED.
        jaarrendement_beleggen_pct: Rendement op beleggelingen deel (optioneel). DEPRECATED.
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
        if saldo_sparen > Decimal("0"):
            maand_rente = maandrendement(jaarrendement_sparen_pct)
            rente_sparen = _rond_af(saldo_sparen * maand_rente)
        
        rente_beleggen = Decimal("0")
        if saldo_beleggen > Decimal("0"):
            maand_rente = maandrendement(jaarrendement_beleggen_pct)
            rente_beleggen = _rond_af(saldo_beleggen * maand_rente)
        
        return rente_sparen + rente_beleggen
    
    # Fallback: gebruik jaarrendement_pct indien beschikbaar
    if jaarrendement_pct is None or jaarrendement_pct == Decimal("0"):
        return Decimal("0")
    maand_rente = maandrendement(jaarrendement_pct)
    return _rond_af(saldo * maand_rente)


def bereken_vermogensontwikkeling(
    beginsaldo: Decimal,
    jaarrendement_pct: Decimal | None = None,
    mutaties: list[tuple[date, Decimal]] = None,
    jaar_van: int = 2025,
    jaar_tot: int = 2050,
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

    if mutaties is None:
        mutaties = []
    
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
        if item.type in (VermogensType.EIGEN_WONING, VermogensType.HYPOTHEEK):
            continue
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
        if item.box3_belast and item.is_actief_op(peildatum) and item.type not in (VermogensType.EIGEN_WONING, VermogensType.HYPOTHEEK):
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


class LiquidePortefeuille:
    """Rekenstaat per liquide post; bronitems blijven ongewijzigd.

    Openingen zijn externe toevoegingen. Sluitingen gaan naar renteloos kasgeld.
    Inleg en huishoudcashflow vallen aan het maandeinde. Algemene cashflow wordt
    naar rato verdeeld; ongedekte tekorten blijven negatief kasgeld. Dit is de
    eigenaar van de saldi; herwaardering van aanschafwaarde tijdens de prognose
    zou rendement dubbel tellen.
    """

    def __init__(
        self, items: list[VermogensItem], start: date,
        inleg_sparen: Decimal = Decimal('0'), inleg_beleggen: Decimal = Decimal('0'),
    ) -> None:
        self.items = [i.model_copy(deep=True) for i in items
                      if i.type in (VermogensType.SPAARGELD, VermogensType.BELEGGINGEN)]
        self.saldis = [Decimal('0') for _ in self.items]
        self.geopend = [False for _ in self.items]
        self.gesloten = [False for _ in self.items]
        self.kas = Decimal('0')
        self.peildatum = start
        self.inleg_legacy = {VermogensType.SPAARGELD: inleg_sparen,
                            VermogensType.BELEGGINGEN: inleg_beleggen}
        self.rentes = [Decimal('0') for _ in self.items]
        self.inleggen = [Decimal('0') for _ in self.items]
        for n, item in enumerate(self.items):
            if item.verkoopdatum and item.verkoopdatum < start:
                self.geopend[n] = self.gesloten[n] = True
            elif not item.aanschafdatum or item.aanschafdatum <= start:
                self.geopend[n] = True
                waarde = item.aanschafwaarde
                if item.aanschafdatum and item.aanschafdatum < start:
                    dagen = Decimal((start - item.aanschafdatum).days)
                    waarde *= (Decimal('1') + item.groei_pct / Decimal('100')) ** (dagen / Decimal('365.25'))
                self.saldis[n] = _rond_af(waarde)

    @property
    def saldo(self) -> Decimal:
        return self.kas + sum(self.saldis, Decimal('0'))

    def _verdeel(self, bedrag: Decimal, indices: list[int]) -> None:
        """Centennauwkeurig, naar positieve saldi; sluitrest op laatste post."""
        if not indices:
            self.kas += bedrag
            return
        totaal = sum((self.saldis[n] for n in indices), Decimal('0'))
        rest = bedrag
        for n in indices[:-1]:
            deel = _rond_af(bedrag * self.saldis[n] / totaal) if totaal else _rond_af(bedrag / len(indices))
            # Een onttrekking mag geen afzonderlijke post negatief maken.
            deel = max(-self.saldis[n], deel)
            self.saldis[n] += deel
            rest -= deel
        laatste = indices[-1]
        deel = max(-self.saldis[laatste], rest)
        self.saldis[laatste] += deel
        self.kas += rest - deel

    def _stort(self, n: int, bedrag: Decimal) -> None:
        # Nieuwe inleg vult eerst een eerder ongedekt tekort aan.
        herstel = min(bedrag, max(Decimal('0'), -self.kas))
        self.kas += herstel
        self.saldis[n] += bedrag - herstel

    def begin_maand(self, jaar: int, maand: int) -> tuple[Decimal, Decimal, Decimal]:
        """Verwerk actieve dagen; geef rendement, inleg en externe openingen."""
        import calendar
        eerste = date(jaar, maand, 1)
        laatste = date(jaar, maand, calendar.monthrange(jaar, maand)[1])
        self.peildatum = laatste
        opening = Decimal('0')
        self.rentes = [Decimal('0') for _ in self.items]
        self.inleggen = [Decimal('0') for _ in self.items]
        for n, item in enumerate(self.items):
            if self.gesloten[n] or (item.aanschafdatum and item.aanschafdatum > laatste):
                continue
            if not self.geopend[n]:
                self.geopend[n] = True
                opening += item.aanschafwaarde
                self._stort(n, item.aanschafwaarde)
            vanaf = max(eerste, item.aanschafdatum or eerste)
            tot = min(laatste, item.verkoopdatum or laatste)
            if tot < vanaf:
                continue
            aandeel = Decimal((tot - vanaf).days + 1) / Decimal(laatste.day)
            factor = (Decimal('1') + maandrendement(item.groei_pct)) ** aandeel - Decimal('1')
            self.rentes[n] = _rond_af(self.saldis[n] * factor)
            self.saldis[n] += self.rentes[n]
            self.inleggen[n] = _rond_af((item.jaarlijkse_inleg or Decimal('0')) / Decimal('12') * aandeel)
            self._stort(n, self.inleggen[n])

        # Oude clients hebben alleen scenario-inleg; expliciete post-inleg is
        # per type leidend, ook als die nul is. Zo wordt niets dubbel ingelegd.
        legacy_totaal = Decimal('0')
        for soort, jaarbedrag in self.inleg_legacy.items():
            if any(i.type == soort and i.jaarlijkse_inleg is not None for i in self.items):
                continue
            bedrag = _rond_af(jaarbedrag / Decimal('12'))
            indices = [n for n, i in enumerate(self.items)
                       if i.type == soort and self.geopend[n] and not self.gesloten[n]
                       and i.is_actief_op(laatste)]
            herstel = min(bedrag, max(Decimal('0'), -self.kas))
            self.kas += herstel
            self._verdeel(bedrag - herstel, indices)
            legacy_totaal += bedrag
        return sum(self.rentes, Decimal('0')), sum(self.inleggen, Decimal('0')) + legacy_totaal, opening

    def sluit_maand(self, cashflow: Decimal) -> None:
        """Verwerk vrij besteedbare cashflow en sluit aflopende posten."""
        indices = [n for n in range(len(self.items)) if self.geopend[n] and not self.gesloten[n]]
        bedrag = _rond_af(cashflow)
        if bedrag < 0:
            uit_kas = min(max(self.kas, Decimal('0')), -bedrag)
            self.kas -= uit_kas
            bedrag += uit_kas
            te_onttrekken = min(-bedrag, sum((self.saldis[n] for n in indices), Decimal('0')))
            self._verdeel(-te_onttrekken, indices)
            self.kas += bedrag + te_onttrekken
        else:
            herstel = min(bedrag, max(-self.kas, Decimal('0')))
            self.kas += herstel
            self._verdeel(bedrag - herstel, [n for n in indices if self.items[n].is_actief_op(self.peildatum)])
        for n in indices:
            item = self.items[n]
            if item.verkoopdatum and item.verkoopdatum <= self.peildatum:
                self.kas += self.saldis[n]
                self.saldis[n] = Decimal('0')
                self.gesloten[n] = True

    def box3_saldi(self, peildatum: date) -> tuple[Decimal, Decimal]:
        """Projecteer actuele belaste saldi: sparen en beleggingen, geen formule."""
        sparen, beleggen = max(self.kas, Decimal('0')), Decimal('0')
        for n, item in enumerate(self.items):
            if not item.box3_belast or self.gesloten[n]:
                continue
            waarde = self.saldis[n]
            if not self.geopend[n] and item.aanschafdatum == peildatum:
                waarde = item.aanschafwaarde
            if item.type == VermogensType.SPAARGELD:
                sparen += waarde
            else:
                beleggen += waarde
        return sparen, beleggen

    def detail(self) -> dict:
        """Alleen bestaande rekenstaat voor API en accountantoutput."""
        return {'bron': 'vermogensitems', 'kas': self.kas, 'posten': [
            {'omschrijving': i.omschrijving, 'type': i.type.value,
             'saldo': self.saldis[n], 'rendement_pct': i.groei_pct,
             'rente': self.rentes[n], 'inleg': self.inleggen[n]}
            for n, i in enumerate(self.items)]}
