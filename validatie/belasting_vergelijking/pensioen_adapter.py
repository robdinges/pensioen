"""Adapter voor pensioen-app belastingengines.

Roept bestaande belastingberekeningen aan (read-only) voor vergelijking.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from pensioen.tax import belasting_engine, heffingskorting
from pensioen.tax.belasting_loader import BelastingConfig, laad_tarieven

from .dutch_tax_adapter import DutchTaxData, PersoonData


@dataclass
class PensioenBelastingResultaat:
    """Resultaat van pensioen-app belastingberekening voor één persoon."""

    persoon_id: str
    naam: str
    jaar: int
    
    # Box 1 details
    bruto_inkomen: Decimal
    arbeidsinkomen: Decimal
    belasting_voor_kortingen: Decimal
    
    # Heffingskortingen (pensioen-app berekening)
    ahk: Decimal
    arbeidskorting: Decimal
    ouderenkorting: Decimal
    totale_heffingskorting: Decimal
    
    # Netto belasting
    netto_belasting_box1: Decimal
    netto_inkomen: Decimal
    
    # Box 3 (per persoon aandeel)
    box3_aandeel_heffing: Decimal
    
    # Totaal
    totale_belasting: Decimal
    vooraf_betaald: Decimal
    te_betalen_terug: Decimal  # Positief = bijbetalen, Negatief = terug
    
    # Metadata
    aow_breuk: Decimal
    effectief_tarief: Decimal
    aannames: list[str]


@dataclass
class HuishoudBelastingResultaat:
    """Resultaat voor heel huishouden."""

    huishouden_id: str
    jaar: int
    heeft_partner: bool
    
    # Per persoon
    personen: list[PensioenBelastingResultaat]
    
    # Box 3 (huishoudniveau)
    box3_totaal_vermogen: Decimal
    box3_vrijstelling: Decimal
    box3_belastbaar_vermogen: Decimal
    box3_totale_heffing: Decimal
    box3_spaargeld_fractie: Decimal
    
    # Totaal huishouden
    totaal_te_betalen_terug: Decimal
    
    config_gebruikt: str  # Welk belastingjaar config


def bereken_via_pensioen_engine(
    data: DutchTaxData,
    doel_jaar: int,
    geboortedatum_p1: date,
    geboortedatum_p2: date | None = None,
) -> HuishoudBelastingResultaat:
    """
    Bereken belasting via pensioen-app engines.
    
    Args:
        data: Dutch tax submission data
        doel_jaar: Jaar voor berekening (meestal 2026)
        geboortedatum_p1: Geboortedatum persoon 1 (voor AOW-status)
        geboortedatum_p2: Geboortedatum persoon 2 (indien partner)
    
    Returns:
        HuishoudBelastingResultaat met alle berekeningen
    """
    # Laad belastingconfiguratie voor doel_jaar
    config, melding = laad_tarieven(doel_jaar)
    
    aannames = []
    if melding:
        aannames.append(f"Tarieven {doel_jaar}: {melding}")
    
    # Bereken Box 3 huishoudniveau
    box3_huishoud = _bereken_box3_huishoud(data, config)
    
    # Bereken per persoon
    personen_resultaten = []
    geboortedatums = [geboortedatum_p1]
    if geboortedatum_p2:
        geboortedatums.append(geboortedatum_p2)
    
    for idx, persoon_data in enumerate(data.personen):
        if idx >= len(geboortedatums):
            # Geen geboortedatum beschikbaar, gebruik standaard (65 jaar geleden)
            gb_datum = date(doel_jaar - 65, 1, 1)
            aannames.append(
                f"Geboortedatum {persoon_data.naam} onbekend, aangenomen: {gb_datum}"
            )
        else:
            gb_datum = geboortedatums[idx]
        
        persoon_resultaat = _bereken_persoon(
            persoon_data,
            config,
            gb_datum,
            doel_jaar,
            box3_huishoud["heffing_per_persoon"][idx],
            aannames.copy(),
        )
        personen_resultaten.append(persoon_resultaat)
    
    # Totaal huishouden
    totaal_te_betalen = sum(
        (p.te_betalen_terug for p in personen_resultaten), Decimal("0")
    )
    
    return HuishoudBelastingResultaat(
        huishouden_id=data.huishouden_id,
        jaar=doel_jaar,
        heeft_partner=data.heeft_fiscaal_partner,
        personen=personen_resultaten,
        box3_totaal_vermogen=box3_huishoud["totaal_vermogen"],
        box3_vrijstelling=box3_huishoud["vrijstelling"],
        box3_belastbaar_vermogen=box3_huishoud["belastbaar"],
        box3_totale_heffing=box3_huishoud["heffing"],
        box3_spaargeld_fractie=box3_huishoud["spaargeld_fractie"],
        totaal_te_betalen_terug=totaal_te_betalen,
        config_gebruikt=f"{config.jaar} ({melding if melding else 'exact'})",
    )


def _bereken_box3_huishoud(data: DutchTaxData, config: BelastingConfig) -> dict:
    """Bereken Box 3 op huishoudniveau via pensioen-app engine."""
    totaal_vermogen = data.netto_vermogen()
    
    # Bereken spaargeld fractie
    spaargeld = data.totaal_spaargeld()
    beleggingen = data.totaal_beleggingen()
    totaal_positief = spaargeld + beleggingen
    
    if totaal_positief > Decimal("0"):
        spaargeld_fractie = spaargeld / totaal_positief
    else:
        spaargeld_fractie = Decimal("1")  # Default: alles sparen
    
    # Bereken Box 3 heffing via pensioen-app engine
    heffing, disclaimer = belasting_engine.bereken_box3_heffing(
        spaarsaldo=totaal_vermogen,
        config=config,
        heeft_partner=data.heeft_fiscaal_partner,
        spaargeld_fractie=spaargeld_fractie,
    )
    
    # Vrijstelling
    aantal = 2 if data.heeft_fiscaal_partner else 1
    vrijstelling = config.box3.vrijstelling_per_persoon * Decimal(str(aantal))
    belastbaar = max(Decimal("0"), totaal_vermogen - vrijstelling)
    
    # Verdeel Box 3 heffing gelijk over personen (pensioen-app aanname)
    aantal_personen = len(data.personen)
    heffing_per_persoon = (
        heffing / Decimal(str(aantal_personen)) if aantal_personen > 0 else Decimal("0")
    )
    
    return {
        "totaal_vermogen": totaal_vermogen,
        "vrijstelling": vrijstelling,
        "belastbaar": belastbaar,
        "heffing": heffing,
        "spaargeld_fractie": spaargeld_fractie,
        "heffing_per_persoon": [heffing_per_persoon] * aantal_personen,
        "disclaimer": disclaimer,
    }


def _bereken_persoon(
    persoon: PersoonData,
    config: BelastingConfig,
    geboortedatum: date,
    jaar: int,
    box3_aandeel: Decimal,
    aannames: list[str],
) -> PensioenBelastingResultaat:
    """Bereken belasting voor één persoon via pensioen-app engines."""
    
    # Som inkomsten
    bruto_inkomen = sum((ink.bruto_bedrag for ink in persoon.inkomsten), Decimal("0"))
    arbeidsinkomen = sum(
        (ink.arbeidsinkomen_bedrag for ink in persoon.inkomsten), Decimal("0")
    )
    
    # WAARSCHUWING: Pensioen-app ondersteunt geen aftrekposten of eigenwoningforfait
    if persoon.aftrekposten:
        totaal_aftrek = sum((a.bedrag for a in persoon.aftrekposten), Decimal("0"))
        aannames.append(
            f"⚠️ {persoon.naam}: {len(persoon.aftrekposten)} aftrekpost(en) "
            f"(totaal €{totaal_aftrek:,.2f}) NIET meegenomen (niet ondersteund)"
        )
    
    if persoon.eigen_woning:
        aannames.append(
            f"⚠️ {persoon.naam}: Eigenwoningforfait (WOZ €{persoon.eigen_woning.woz_waarde:,.0f}) "
            f"NIET meegenomen (niet ondersteund)"
        )
    
    # Bereken via pensioen-app netto_uit_bruto
    resultaat = belasting_engine.netto_uit_bruto(
        bruto=bruto_inkomen,
        arbeidsinkomen=arbeidsinkomen,
        config=config,
        geboortedatum=geboortedatum,
        jaar=jaar,
        aannames=aannames,
    )
    
    # Heffingskortingen (uit pensioen-app berekening)
    from pensioen.tax import aow_engine
    
    aow_breuk = aow_engine.aow_breuk_jaar(geboortedatum, jaar)
    is_aow = aow_breuk > Decimal("0")
    
    ahk = heffingskorting.bereken_ahk(bruto_inkomen, config)
    arbeidskorting = heffingskorting.bereken_arbeidskorting(arbeidsinkomen, config)
    ouderenkorting = heffingskorting.bereken_ouderenkorting(
        bruto_inkomen, config, is_aow
    )
    
    # Totaal belasting (Box 1 + Box 3 aandeel)
    totale_belasting = (
        resultaat.belasting - resultaat.heffingskorting + box3_aandeel
    )
    totale_belasting = max(Decimal("0"), totale_belasting)
    
    # Vooraf betaald (loonheffing + dividend)
    vooraf_betaald = persoon.loonheffing_ingehouden
    # TODO: Dividend ingehouden wordt door pensioen-app niet meegenomen in Box 3 aftrek
    
    te_betalen = totale_belasting - vooraf_betaald
    
    return PensioenBelastingResultaat(
        persoon_id=persoon.persoon_id,
        naam=persoon.naam,
        jaar=jaar,
        bruto_inkomen=bruto_inkomen,
        arbeidsinkomen=arbeidsinkomen,
        belasting_voor_kortingen=resultaat.belasting,
        ahk=ahk,
        arbeidskorting=arbeidskorting,
        ouderenkorting=ouderenkorting,
        totale_heffingskorting=resultaat.heffingskorting,
        netto_belasting_box1=max(
            Decimal("0"), resultaat.belasting - resultaat.heffingskorting
        ),
        netto_inkomen=resultaat.netto,
        box3_aandeel_heffing=box3_aandeel,
        totale_belasting=totale_belasting,
        vooraf_betaald=vooraf_betaald,
        te_betalen_terug=te_betalen,
        aow_breuk=aow_breuk,
        effectief_tarief=resultaat.effectief_tarief,
        aannames=resultaat.aannames,
    )
