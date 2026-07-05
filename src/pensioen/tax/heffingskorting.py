"""Berekening van heffingskortingen op basis van de belastingconfiguratie."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from pensioen.tax.belasting_loader import ArbeidskortingConfig, BelastingConfig, HeffingskortingConfig

CENT = Decimal("0.01")


def _rond_af_cent(bedrag: Decimal) -> Decimal:
    """Rond af op eurocenten met de standaard Decimal quantize-regel."""
    return bedrag.quantize(CENT, rounding=ROUND_HALF_UP)


def _afbouw_korting(
    inkomen: Decimal,
    config: HeffingskortingConfig,
) -> Decimal:
    """
    Bereken een heffingskorting met lineaire afbouw.

    Formule: max(minimum, max_bedrag - max(0, inkomen - afbouw_drempel) * afbouw_pct)
    """
    afbouw = max(Decimal("0"), inkomen - config.afbouw_inkomen_van) * config.afbouw_pct
    korting = config.max_bedrag - afbouw
    return max(config.minimum, korting)


def _afbouw_korting_met_maximum(
    inkomen: Decimal,
    minimum: Decimal,
    maximum: Decimal,
    afbouw_inkomen_van: Decimal,
    afbouw_pct: Decimal,
) -> Decimal:
    """Variant van lineaire afbouw met expliciet maximum."""
    afbouw = max(Decimal("0"), inkomen - afbouw_inkomen_van) * afbouw_pct
    korting = maximum - afbouw
    return max(minimum, korting)


def bereken_ahk(inkomen: Decimal, config: BelastingConfig) -> Decimal:
    """
    Bereken de Algemene Heffingskorting (AHK).

    De AHK bouwt af boven een inkomensdrempel.

    Voor AOW-gerechtigden kan een AOW-factor gelden. Bij een gedeeltelijk
    AOW-jaar passen we een tijdsevenredige weging toe op die factor.
    """
    return _afbouw_korting(inkomen, config.ahk)


def bereken_ahk_met_aow(
    inkomen: Decimal,
    config: BelastingConfig,
    aow_breuk: Decimal,
) -> Decimal:
    """
    Bereken AHK inclusief AOW-factor en tijdsevenredige berekening.

    Belastingdienst-systematiek:
    - AOW-factor werkt op het AHK-maximum (niet op de al afgebouwde uitkomst)
    - Daarna volgt lineaire afbouw over het inkomen

    Bij een gedeeltelijk AOW-jaar wordt het maximum tijdsevenredig gewogen.
    """
    aow_breuk = max(Decimal("0"), min(Decimal("1"), aow_breuk))
    ahk_config = config.ahk

    if aow_breuk == Decimal("0"):
        return _afbouw_korting(inkomen, ahk_config)

    factor = config.ahk_aow_factor
    if aow_breuk == Decimal("1"):
        aangepast_maximum = ahk_config.max_bedrag * factor
    else:
        gewogen_factor = ((Decimal("1") - aow_breuk) * Decimal("1")) + (aow_breuk * factor)
        aangepast_maximum = ahk_config.max_bedrag * gewogen_factor

    return _afbouw_korting_met_maximum(
        inkomen=inkomen,
        minimum=ahk_config.minimum,
        maximum=aangepast_maximum,
        afbouw_inkomen_van=ahk_config.afbouw_inkomen_van,
        afbouw_pct=ahk_config.afbouw_pct,
    )


def bereken_arbeidskorting(arbeidsinkomen: Decimal, config: BelastingConfig) -> Decimal:
    """
    Bereken de arbeidskorting op basis van arbeidsinkomen.

    Vereenvoudigde berekening voor MVP:
    - Geen arbeidsinkomen → 0
    - Arbeidsinkomen aanwezig → min(max, arbeidsinkomen) minus afbouw boven drempel

    Let op: de volledige opbouwfases vereisen nadere parametrisatie in de JSON.
    De huidige implementatie is conservatief: bij laag arbeidsinkomen kan de werkelijke
    korting lager zijn dan berekend.
    """
    if arbeidsinkomen <= Decimal("0"):
        return Decimal("0")

    ak = config.arbeidskorting
    # Benadering: maximale korting bij inkomen ≥ max (opbouw vereenvoudigd)
    korting_voor_afbouw = min(ak.max_bedrag, arbeidsinkomen)

    # Afbouw
    afbouw = max(
        Decimal("0"),
        (arbeidsinkomen - ak.afbouw_drempel) * ak.afbouw_pct,
    )
    korting = korting_voor_afbouw - afbouw
    return max(ak.minimum, korting)


def bereken_ouderenkorting(inkomen: Decimal, config: BelastingConfig, is_aow: bool) -> Decimal:
    """
    Bereken de ouderenkorting.

    Alleen van toepassing op AOW-gerechtigden.
    """
    if not is_aow:
        return Decimal("0")
    return _afbouw_korting(inkomen, config.ouderenkorting)


def bereken_alleenstaandeouderenkorting(
    inkomen: Decimal,
    config: BelastingConfig,
    is_aow: bool,
    is_alleenstaand: bool,
) -> Decimal:
    """
    Bereken de alleenstaandeouderenkorting.

    Alleen van toepassing op alleenstaande AOW-gerechtigden.
    Vanaf belastingjaar 2025.
    """
    if not (is_aow and is_alleenstaand):
        return Decimal("0")
    
    if config.alleenstaandeouderenkorting is None:
        return Decimal("0")
    
    return _afbouw_korting(inkomen, config.alleenstaandeouderenkorting)


def bereken_totale_heffingskortingen(
    bruto_inkomen: Decimal,
    arbeidsinkomen: Decimal,
    config: BelastingConfig,
    is_aow: bool,
    aow_breuk: Decimal = Decimal("0"),
    is_alleenstaand: bool = True,
) -> Decimal:
    """
    Bereken de totale heffingskortingen voor één persoon.

    Args:
        bruto_inkomen: Totaal bruto inkomen voor AHK-afbouw (arbeid + pensioen + AOW).
        arbeidsinkomen: Alleen het deel dat als arbeidsinkomen telt (voor arbeidskorting).
        config: Belastingconfiguratie voor het betreffende jaar.
        is_aow: Of de persoon AOW-gerechtigd is (voor ouderenkorting).
        is_alleenstaand: Of de persoon alleenstaand is (voor alleenstaandeouderenkorting).

    Returns:
        Totale heffingskorting in euro's.
    """
    # Afrondingsregel: eerst volledige formule per component, daarna afronden op centen.
    ahk = _rond_af_cent(bereken_ahk_met_aow(bruto_inkomen, config, aow_breuk))
    ak = _rond_af_cent(bereken_arbeidskorting(arbeidsinkomen, config))
    ok = _rond_af_cent(bereken_ouderenkorting(bruto_inkomen, config, is_aow))
    aok = _rond_af_cent(
        bereken_alleenstaandeouderenkorting(bruto_inkomen, config, is_aow, is_alleenstaand)
    )
    return ahk + ak + ok + aok
