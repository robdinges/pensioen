"""Box 1 belastingberekening inclusief heffingskortingen en AOW-breuk."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, ROUND_FLOOR, Decimal

from pensioen.tax import aow_engine, heffingskorting
from pensioen.tax.belasting_loader import BelastingConfig, SchijfConfig

CENT = Decimal("0.01")


def _naar_float(waarde: Decimal | None) -> float | None:
    if waarde is None:
        return None
    return float(waarde)


def _serializeer_schijven(schijven: list[SchijfConfig]) -> list[dict[str, float | None]]:
    return [
        {
            "tot": _naar_float(schijf.tot),
            "tarief": float(schijf.tarief),
        }
        for schijf in schijven
    ]


def rond_af(bedrag: Decimal) -> Decimal:
    """Rond een geldbedrag af op centen (ROUND_HALF_UP)."""
    return bedrag.quantize(CENT, rounding=ROUND_HALF_UP)


def rond_heffing_af(bedrag: Decimal, config: BelastingConfig) -> Decimal:
    """Aanslagafronding pas na de volledige heffing; opslag blijft Decimal."""
    if config.afronding_aanslag:
        return bedrag.quantize(Decimal('1'), rounding=ROUND_FLOOR).quantize(CENT)
    return rond_af(bedrag)


def begrens_verrekenbare_heffingskorting(
    berekende_heffingskorting: Decimal,
    verschuldigde_ib_en_premies: Decimal,
) -> tuple[Decimal, Decimal]:
    """
    Splits de berekende heffingskorting in een verrekend en niet-verrekend deel.

    Functioneel contract:
    - source of truth voor de stap Heffingskortingen -> Netto inkomen;
    - verrekening is begrensd op de verschuldigde inkomstenbelasting en premies;
    - negatieve invoer wordt voor de begrenzing als nul behandeld;
    - de bedragen worden op eurocenten afgerond.

    Uitbetaling van algemene heffingskorting aan een minstverdienende fiscale
    partner is een afzonderlijke huishoudregel en valt buiten deze functie.
    """
    korting = max(Decimal("0"), rond_af(berekende_heffingskorting))
    verschuldigd = max(Decimal("0"), rond_af(verschuldigde_ib_en_premies))
    verrekend = min(korting, verschuldigd)
    niet_verrekend = korting - verrekend
    return verrekend, niet_verrekend


@dataclass
class BelastingResultaat:
    """Uitgebreid resultaat van een belastingberekening inclusief transparantie."""

    bruto: Decimal
    
    # Opsplitsing belasting en premies (vanaf 2025)
    inkomstenbelasting: Decimal  # Pure inkomstenbelasting (box 1)
    premie_aow: Decimal  # AOW-premie
    premie_anw: Decimal  # Nabestaandenwet premie
    premie_wlz: Decimal  # Wet langdurige zorg premie
    totaal_premies: Decimal  # Afgeronde ongeronde som bij aanslagafronding; kan van getoonde delen afwijken
    
    # Legacy veld voor backward compatibility
    belasting: Decimal  # Totaal IB + premies (voor oude code)
    
    # Kortingen en netto
    heffingskorting: Decimal
    netto: Decimal
    
    # Metadata
    effectief_tarief: Decimal  # percentage
    gebruikte_tarieven: dict = field(default_factory=dict)
    aannames: list[str] = field(default_factory=list)


def _bereken_schijven(inkomen: Decimal, schijven: list[SchijfConfig], afronding_aanslag: bool = False) -> Decimal:
    """
    Bereken belasting per schijf, bij aanslagafronding elke voltooide schijf omlaag.

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
            schijfbelasting = max(inkomen - vorig_tot, Decimal("0")) * schijf.tarief
            belasting += (schijfbelasting.quantize(Decimal('1'), rounding=ROUND_FLOOR)
                          if afronding_aanslag else schijfbelasting)
        else:
            schijf_inkomen = max(
                Decimal("0"), min(inkomen, schijf.tot) - vorig_tot
            )
            schijfbelasting = schijf_inkomen * schijf.tarief
            belasting += (schijfbelasting.quantize(Decimal('1'), rounding=ROUND_FLOOR)
                          if afronding_aanslag else schijfbelasting)
            vorig_tot = schijf.tot
            if inkomen <= schijf.tot:
                break

    return belasting


def bereken_box1_belasting(
    bruto: Decimal,
    config: BelastingConfig,
    aow_breuk: Decimal,
    geboortedatum: date | None = None,
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

    if (geboortedatum is not None and config.box1_geboortejaar_grens is not None
            and geboortedatum.year < config.box1_geboortejaar_grens and config.box1_ouder_cohort):
        return rond_heffing_af(_bereken_schijven(bruto, config.box1_ouder_cohort, config.afronding_aanslag), config)
    belasting_niet_aow = _bereken_schijven(bruto, config.box1_niet_aow, config.afronding_aanslag)
    belasting_aow = _bereken_schijven(bruto, config.box1_aow, config.afronding_aanslag)

    gewogen = (
        niet_aow_breuk * belasting_niet_aow
        + aow_breuk * belasting_aow
    )
    return rond_heffing_af(gewogen, config)


def bereken_premies_volksverzekeringen(
    bruto_inkomen: Decimal,
    config: BelastingConfig,
    is_aow: bool,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """
        Bereken premies volksverzekeringen (AOW, Anw, Wlz).

        Functioneel contract:
        - Doel: bereken premiecomponenten en totaal voor box-1-premies.
        - Invoer: bruto jaarinkomen, jaarconfig, AOW-status voor het hele jaar.
        - Grondslag: min(bruto_inkomen, premiegrens); geen negatieve correctie.
        - Tarieven:
            - AOW-premie: tarief_niet_aow of tarief_aow (meestal 0 bij volledig AOW).
            - Anw- en Wlz-premie: altijd van toepassing op dezelfde grondslag.
        - Aanslagafronding: componenten omlaag op hele euro's; totaal uit de
            ongeronde componenten, daarna omlaag. Het totaal is leidend.
        - Zonder aanslagafronding: legacy centenafronding per component.
        - Randgeval: ontbrekende premiesconfig geeft (0, 0, 0, 0) voor
            backward compatibility.

    Args:
        bruto_inkomen: Totaal bruto jaarinkomen.
        config: Belastingconfiguratie voor het jaar.
        is_aow: Of de persoon (heel jaar) AOW-gerechtigd is.
    
    Returns:
        Tuple van (premie_aow, premie_anw, premie_wlz, totaal_premies).
        Retourneert (0, 0, 0, 0) als config.premies None is (backward compatibility).
    """
    if config.premies is None:
        # Backward compatibility: oude configs zonder premies-sectie
        return Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0")
    
    # Grondslag: max tot premiegrens (alleen schijf 1)
    grondslag = min(bruto_inkomen, config.premies.premiegrens)
    
    # AOW-premie: 0 als al AOW-gerechtigd, anders tarief_niet_aow
    tarief_aow = config.premies.aow_tarief_aow if is_aow else config.premies.aow_tarief_niet_aow
    premie_aow_raw = grondslag * tarief_aow
    
    # Anw en Wlz: voor iedereen
    premie_anw_raw = grondslag * config.premies.anw_tarief
    premie_wlz_raw = grondslag * config.premies.wlz_tarief
    premie_aow = rond_heffing_af(premie_aow_raw, config)
    premie_anw = rond_heffing_af(premie_anw_raw, config)
    premie_wlz = rond_heffing_af(premie_wlz_raw, config)
    
    totaal = premie_aow + premie_anw + premie_wlz
    if config.afronding_aanslag:
        totaal = rond_heffing_af(premie_aow_raw + premie_anw_raw + premie_wlz_raw, config)
    return premie_aow, premie_anw, premie_wlz, totaal


def netto_uit_bruto(
    bruto: Decimal,
    arbeidsinkomen: Decimal,
    config: BelastingConfig,
    geboortedatum: date,
    jaar: int,
    is_alleenstaand: bool = True,
    aannames: list[str] | None = None,
) -> BelastingResultaat:
    """
    Bereken het netto jaarinkomen vanuit bruto, inclusief heffingskortingen en premies.

        Contract voor samenstelling en afronding:
        - Inkomstenbelasting (box 1) en premies volksverzekeringen worden als
            losse componenten berekend op hun eigen grondslag.
        - Heffingskortingen worden berekend in de heffingskorting-module als som
            van afgeronde componenten.
        - Netto verschuldigd = max(0, inkomstenbelasting + totaal_premies - heffingskorting).
        - Netto inkomen = bruto - netto verschuldigd, afgerond op eurocenten.

    Args:
        bruto: Totaal bruto jaarinkomen (arbeid + pensioen + AOW + overig).
        arbeidsinkomen: Deel dat als arbeidsinkomen telt (voor arbeidskorting).
        config: Belastingconfiguratie voor het jaar.
        geboortedatum: Geboortedatum van de persoon (voor AOW-status).
        jaar: Belastingjaar.
        is_alleenstaand: Of de persoon alleenstaand is (voor alleenstaandeouderenkorting).
        aannames: Eventuele extra aannames voor transparantie.

    Returns:
        BelastingResultaat met bruto, IB, premies, heffingskorting, netto, tarief.
    """
    if aannames is None:
        aannames = []

    bruto = max(Decimal("0"), bruto)

    # AOW-status
    aow_breuk = aow_engine.aow_breuk_jaar(geboortedatum, jaar)
    is_aow_heel_jaar = aow_breuk >= Decimal("1")  # Voor premies: hele jaar AOW?
    is_aow_deels = aow_breuk > Decimal("0")  # Voor kortingen: deels AOW?

    # Box 1 inkomstenbelasting (pure IB, zonder premies)
    ib = bereken_box1_belasting(bruto, config, aow_breuk, geboortedatum=geboortedatum)
    
    # Premies volksverzekeringen (apart berekend, alleen over schijf 1)
    premie_aow, premie_anw, premie_wlz, totaal_premies = bereken_premies_volksverzekeringen(
        bruto, config, is_aow_heel_jaar
    )
    
    # Totaal belasting + premies
    totaal_belasting_en_premies = ib + totaal_premies

    # Heffingskortingen (inclusief alleenstaandeouderenkorting)
    totale_korting = heffingskorting.bereken_totale_heffingskortingen(
        bruto_inkomen=bruto,
        arbeidsinkomen=arbeidsinkomen,
        config=config,
        is_aow=is_aow_deels,
        aow_breuk=aow_breuk,
        is_alleenstaand=is_alleenstaand,
    )

    # Netto belasting (nooit negatief — kortingen kunnen belasting niet overstijgen)
    verrekende_korting, _ = begrens_verrekenbare_heffingskorting(
        totale_korting,
        totaal_belasting_en_premies,
    )
    netto_verschuldigd = totaal_belasting_en_premies - verrekende_korting
    netto = rond_af(bruto - netto_verschuldigd)

    effectief_tarief = (
        netto_verschuldigd / bruto * Decimal("100")
        if bruto > Decimal("0")
        else Decimal("0")
    )

    gebruikte_tarieven = {
        "belastingjaar": config.jaar,
        "aow_breuk": float(aow_breuk),
        "inkomstenbelasting": float(ib),
        "premie_aow": float(premie_aow),
        "premie_anw": float(premie_anw),
        "premie_wlz": float(premie_wlz),
        "totaal_premies": float(totaal_premies),
        "ahk": float(heffingskorting.bereken_ahk_met_aow(bruto, config, aow_breuk)),
        "arbeidskorting": float(heffingskorting.bereken_arbeidskorting(arbeidsinkomen, config)),
        "ouderenkorting": float(
            heffingskorting.bereken_ouderenkorting(bruto, config, is_aow_deels)
        ),
        "alleenstaandeouderenkorting": float(
            heffingskorting.bereken_alleenstaandeouderenkorting(
                bruto, config, is_aow_deels, is_alleenstaand
            )
        ),
        "grondslagen": {
            "bruto_jaarinkomen": float(bruto),
            "arbeidsinkomen": float(arbeidsinkomen),
            "premiegrondslag": float(
                min(bruto, config.premies.premiegrens) if config.premies else Decimal("0")
            ),
        },
        "schijven": {
            "box1_niet_aow": _serializeer_schijven(config.box1_niet_aow),
            "box1_aow": _serializeer_schijven(config.box1_aow),
        },
        "premies_config": (
            {
                "premiegrens": float(config.premies.premiegrens),
                "aow_tarief_niet_aow": float(config.premies.aow_tarief_niet_aow),
                "aow_tarief_aow": float(config.premies.aow_tarief_aow),
                "anw_tarief": float(config.premies.anw_tarief),
                "wlz_tarief": float(config.premies.wlz_tarief),
            }
            if config.premies
            else None
        ),
    }

    if aow_breuk > Decimal("0") and aow_breuk < Decimal("1"):
        aannames.append(
            f"AOW-gerechtigd voor {float(aow_breuk):.1%} van {jaar} "
            f"(gewogen tarief toegepast)."
        )

    return BelastingResultaat(
        bruto=bruto,
        inkomstenbelasting=rond_af(ib),
        premie_aow=premie_aow,
        premie_anw=premie_anw,
        premie_wlz=premie_wlz,
        totaal_premies=totaal_premies,
        belasting=rond_af(totaal_belasting_en_premies),  # Legacy veld
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
    spaargeld_fractie: Decimal = Decimal("1"),
) -> tuple[Decimal, str]:
    """
    Bereken de box 3 heffing op vermogen.

    Correcte berekening: belasting = 36% × fictief rendement.
    Fictief rendement = belastbaar vermogen × gewogen forfaitair rendement.
    Gewogen rendement = spaargeld_fractie × forfaitair_spaargeld
                      + (1 - spaargeld_fractie) × forfaitair_overig.

    WAARSCHUWING: Box 3 wetgeving is in beweging vanwege rechterlijke uitspraken.

    Args:
        spaarsaldo: Totaal spaarsaldo / vermogen in box 3.
        config: Belastingconfiguratie (bevat vrijstelling, tarieven en forfaits).
        heeft_partner: Of er een fiscaal partner is (verdubbelt de vrijstelling).
        spaargeld_fractie: Aandeel van het vermogen dat als spaargeld telt (0.0–1.0).

    Returns:
        Tuple van (belasting, disclaimer_tekst).
    """
    aantallers = 2 if heeft_partner else 1
    vrijstelling = config.box3.vrijstelling_per_persoon * Decimal(str(aantallers))
    belastbaar = max(Decimal("0"), spaarsaldo - vrijstelling)

    spaargeld_fractie = max(Decimal("0"), min(Decimal("1"), spaargeld_fractie))
    overig_fractie = Decimal("1") - spaargeld_fractie

    gewogen_forfait = (
        spaargeld_fractie * config.box3.forfaitair_spaargeld
        + overig_fractie * config.box3.forfaitair_overig
    )
    # Geen tussentijdse afronding: eerst volledig fictief rendement, dan eindheffing afronden.
    fictief_rendement = belastbaar * gewogen_forfait
    heffing = rond_af(fictief_rendement * config.box3.tarief)
    return heffing, config.box3.disclaimer
