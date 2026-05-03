"""Berekening van heffingskortingen op basis van de belastingconfiguratie."""

from __future__ import annotations

from decimal import Decimal

from pensioen.tax.belasting_loader import ArbeidskortingConfig, BelastingConfig, HeffingskortingConfig


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


def bereken_ahk(inkomen: Decimal, config: BelastingConfig) -> Decimal:
    """
    Bereken de Algemene Heffingskorting (AHK).

    De AHK bouwt af boven een inkomensdrempel.
    """
    return _afbouw_korting(inkomen, config.ahk)


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


def bereken_totale_heffingskortingen(
    bruto_inkomen: Decimal,
    arbeidsinkomen: Decimal,
    config: BelastingConfig,
    is_aow: bool,
) -> Decimal:
    """
    Bereken de totale heffingskortingen voor één persoon.

    Args:
        bruto_inkomen: Totaal bruto inkomen voor AHK-afbouw (arbeid + pensioen + AOW).
        arbeidsinkomen: Alleen het deel dat als arbeidsinkomen telt (voor arbeidskorting).
        config: Belastingconfiguratie voor het betreffende jaar.
        is_aow: Of de persoon AOW-gerechtigd is (voor ouderenkorting).

    Returns:
        Totale heffingskorting in euro's.
    """
    ahk = bereken_ahk(bruto_inkomen, config)
    ak = bereken_arbeidskorting(arbeidsinkomen, config)
    ok = bereken_ouderenkorting(bruto_inkomen, config, is_aow)
    return ahk + ak + ok
