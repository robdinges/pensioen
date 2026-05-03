"""Box 1 belastingberekening inclusief heffingskortingen en AOW-breuk."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from pensioen.tax import aow_engine, heffingskorting
from pensioen.tax.belasting_loader import BelastingConfig, SchijfConfig

CENT = Decimal("0.01")


def rond_af(bedrag: Decimal) -> Decimal:
    """Rond een geldbedrag af op centen (ROUND_HALF_UP)."""
    return bedrag.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass
class BelastingResultaat:
    """Uitgebreid resultaat van een belastingberekening inclusief transparantie."""

    bruto: Decimal
    belasting: Decimal
    heffingskorting: Decimal
    netto: Decimal
    effectief_tarief: Decimal  # percentage
    gebruikte_tarieven: dict = field(default_factory=dict)
    aannames: list[str] = field(default_factory=list)


def _bereken_schijven(inkomen: Decimal, schijven: list[SchijfConfig]) -> Decimal:
    """
    Bereken de ruwe belasting op basis van schijven (voor heffingskortingen).

    Args:
        inkomen: Belastbaar inkomen in euro's.
        schijven: Lijst van SchijfConfig met tarieven.

    Returns:
        Belasting vóór aftrek heffingskortingen.
    """
    belasting = Decimal("0")
    vorig_tot = Decimal("0")

    for schijf in schijven:
        if schijf.tot is None:
            # Laatste (open) schijf
            belasting += max(inkomen - vorig_tot, Decimal("0")) * schijf.tarief
        else:
            schijf_inkomen = max(
                Decimal("0"), min(inkomen, schijf.tot) - vorig_tot
            )
            belasting += schijf_inkomen * schijf.tarief
            vorig_tot = schijf.tot
            if inkomen <= schijf.tot:
                break

    return belasting


def bereken_box1_belasting(
    bruto: Decimal,
    config: BelastingConfig,
    aow_breuk: Decimal,
) -> Decimal:
    """
    Bereken de box 1 belasting voor een jaarinkomen, rekening houdend met AOW-status.

    Voor personen die gedurende het jaar AOW-gerechtigd worden, wordt een gewogen
    gemiddelde toegepast: (1 - aow_breuk) * niet-AOW tarief + aow_breuk * AOW tarief.

    Args:
        bruto: Totaal bruto jaarinkomen.
        config: Belastingconfiguratie voor het jaar.
        aow_breuk: Fractie van het jaar als AOW-gerechtigd (0.0 – 1.0).

    Returns:
        Berekende belasting vóór heffingskortingen.
    """
    bruto = max(Decimal("0"), bruto)
    aow_breuk = max(Decimal("0"), min(Decimal("1"), aow_breuk))
    niet_aow_breuk = Decimal("1") - aow_breuk

    belasting_niet_aow = _bereken_schijven(bruto, config.box1_niet_aow)
    belasting_aow = _bereken_schijven(bruto, config.box1_aow)

    gewogen = (
        niet_aow_breuk * belasting_niet_aow
        + aow_breuk * belasting_aow
    )
    return rond_af(gewogen)


def netto_uit_bruto(
    bruto: Decimal,
    arbeidsinkomen: Decimal,
    config: BelastingConfig,
    geboortedatum: date,
    jaar: int,
    aannames: list[str] | None = None,
) -> BelastingResultaat:
    """
    Bereken het netto jaarinkomen vanuit bruto, inclusief heffingskortingen.

    Args:
        bruto: Totaal bruto jaarinkomen (arbeid + pensioen + AOW + overig).
        arbeidsinkomen: Deel dat als arbeidsinkomen telt (voor arbeidskorting).
        config: Belastingconfiguratie voor het jaar.
        geboortedatum: Geboortedatum van de persoon (voor AOW-status).
        jaar: Belastingjaar.
        aannames: Eventuele extra aannames voor transparantie.

    Returns:
        BelastingResultaat met bruto, belasting, heffingskorting, netto, tarief.
    """
    if aannames is None:
        aannames = []

    bruto = max(Decimal("0"), bruto)

    # AOW-status
    aow_breuk = aow_engine.aow_breuk_jaar(geboortedatum, jaar)
    is_aow = aow_breuk > Decimal("0")

    # Box 1 belasting (vóór heffingskortingen)
    belasting_voor_kortingen = bereken_box1_belasting(bruto, config, aow_breuk)

    # Heffingskortingen
    totale_korting = heffingskorting.bereken_totale_heffingskortingen(
        bruto_inkomen=bruto,
        arbeidsinkomen=arbeidsinkomen,
        config=config,
        is_aow=is_aow,
    )

    # Netto belasting (nooit negatief — kortingen kunnen belasting niet overstijgen)
    netto_belasting = max(Decimal("0"), belasting_voor_kortingen - totale_korting)
    netto = rond_af(bruto - netto_belasting)

    effectief_tarief = (
        netto_belasting / bruto * Decimal("100")
        if bruto > Decimal("0")
        else Decimal("0")
    )

    gebruikte_tarieven = {
        "belastingjaar": config.jaar,
        "aow_breuk": float(aow_breuk),
        "belasting_voor_kortingen": float(belasting_voor_kortingen),
        "ahk": float(heffingskorting.bereken_ahk(bruto, config)),
        "arbeidskorting": float(heffingskorting.bereken_arbeidskorting(arbeidsinkomen, config)),
        "ouderenkorting": float(
            heffingskorting.bereken_ouderenkorting(bruto, config, is_aow)
        ),
    }

    if aow_breuk > Decimal("0") and aow_breuk < Decimal("1"):
        aannames.append(
            f"AOW-gerechtigd voor {float(aow_breuk):.1%} van {jaar} "
            f"(gewogen tarief toegepast)."
        )

    return BelastingResultaat(
        bruto=bruto,
        belasting=rond_af(belasting_voor_kortingen),
        heffingskorting=rond_af(totale_korting),
        netto=netto,
        effectief_tarief=rond_af(effectief_tarief),
        gebruikte_tarieven=gebruikte_tarieven,
        aannames=aannames,
    )


def bereken_box3_heffing(
    spaarsaldo: Decimal,
    config: BelastingConfig,
    heeft_partner: bool,
) -> tuple[Decimal, str]:
    """
    Bereken de box 3 heffing op vermogen.

    WAARSCHUWING: Box 3 wetgeving is in beweging vanwege rechterlijke uitspraken.
    Gebruik de uitkomsten met grote voorzichtigheid.

    Args:
        spaarsaldo: Totaal spaarsaldo / vermogen in box 3.
        config: Belastingconfiguratie (bevat vrijstelling en tarief).
        heeft_partner: Of er een fiscaal partner is (verdubbelt de vrijstelling).

    Returns:
        Tuple van (belasting, disclaimer_tekst).
    """
    aantallers = 2 if heeft_partner else 1
    vrijstelling = config.box3.vrijstelling_per_persoon * Decimal(str(aantallers))
    belastbaar = max(Decimal("0"), spaarsaldo - vrijstelling)
    heffing = rond_af(belastbaar * config.box3.tarief)
    return heffing, config.box3.disclaimer
