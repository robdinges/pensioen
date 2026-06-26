"""Berekening eigen woning (box 1): forfait, renteaftrek, Wet Hillen en box 3-koppeling."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from pensioen.tax.belasting_loader import BelastingConfig

CENT = Decimal("0.01")


def _rond_af(bedrag: Decimal) -> Decimal:
    return bedrag.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass
class EigenWoningInvoer:
    """Invoer voor de eigen-woning-berekening voor één belastingjaar."""

    woz_waarde: Decimal
    betaalde_hypotheekrente: Decimal
    overige_aftrekbare_kosten: Decimal = Decimal("0")
    eigenwoningschuld_begin: Decimal = Decimal("0")
    eigenwoningschuld_eind: Decimal = Decimal("0")
    bruto_inkomen_box1: Decimal = Decimal("0")  # grondslag vóór eigen woning, voor tariefsaanpassing


@dataclass
class EigenWoningResultaat:
    """Resultaat van de eigen-woning-berekening."""

    eigenwoningforfait: Decimal
    aftrekbare_hypotheekrente: Decimal
    overige_aftrekbare_kosten: Decimal
    totaal_aftrek: Decimal
    saldo_eigen_woning: Decimal       # negatief = aftrekpost, positief = bijtelling
    hillen_correctie: Decimal          # vermindering van positief saldo (Wet Hillen)
    box1_mutatie: Decimal              # effectieve correctie op box-1 grondslag (na Hillen)
    tariefsaanpassing: Decimal         # extra belasting door begrenzing aftrek bij hoog inkomen
    box3_bezittingen: Decimal          # = 0: woning behoort niet tot box 3
    box3_schulden: Decimal             # = 0: eigenwoningschuld behoort niet tot box 3
    toelichting: list[str] = field(default_factory=list)


def _bereken_eigenwoningforfait(
    woz_waarde: Decimal,
    config: BelastingConfig,
) -> tuple[Decimal, list[str]]:
    """
    Bereken het eigenwoningforfait op basis van WOZ-waarde.

    Het eigenwoningforfait is GEEN progressieve belasting: het tarief van de schijf
    waarin de WOZ-waarde valt wordt toegepast op de VOLLEDIGE WOZ-waarde.
    Uitzondering: de hoogste (open) schijf is progressief (vast bedrag + meerdere × toptarief).
    """
    if config.eigen_woning is None:
        return Decimal("0"), ["Geen eigen-woning-configuratie beschikbaar voor dit jaar."]

    schijven = config.eigen_woning.forfait_schijven
    toelichting: list[str] = []

    for i, schijf in enumerate(schijven):
        if schijf.tot is None:
            # Laatste (open) schijf: basis op vorige grens + meerdere × toptarief
            vorig_max = schijven[i - 1].tot if i > 0 else Decimal("0")
            vorig_pct = schijven[i - 1].percentage if i > 0 else Decimal("0")
            basis = _rond_af(vorig_max * vorig_pct)
            meerdere = max(Decimal("0"), woz_waarde - vorig_max)
            extra = _rond_af(meerdere * schijf.percentage)
            forfait = basis + extra
            toelichting.append(
                f"Forfait t/m € {int(vorig_max):,}: {float(vorig_pct) * 100:.2f}% × € {int(vorig_max):,} = € {basis:,}"
            )
            toelichting.append(
                f"Forfait boven € {int(vorig_max):,}: {float(schijf.percentage) * 100:.2f}% × € {int(meerdere):,} = € {extra:,}"
            )
            return _rond_af(forfait), toelichting

        if woz_waarde <= schijf.tot:
            # Tarief van toepassing op volledige WOZ-waarde
            forfait = _rond_af(woz_waarde * schijf.percentage)
            if schijf.percentage > Decimal("0"):
                toelichting.append(
                    f"Forfait: {float(schijf.percentage) * 100:.2f}% × € {int(woz_waarde):,} = € {forfait:,}"
                )
            return forfait, toelichting

    return Decimal("0"), toelichting


def _bereken_tariefsaanpassing(
    aftrek: Decimal,
    bruto_inkomen: Decimal,
    config: BelastingConfig,
) -> tuple[Decimal, str]:
    """
    Bereken de tariefsaanpassing aftrekposten eigen woning.

    Aftrekposten in box 1 zijn begrensd: het belastingvoordeel is maximaal het
    schijf-2-tarief. Bij inkomen in schijf 3 geldt een correctie:
      extra_belasting = aftrek_in_schijf3 × tariefsaanpassing_pct.

    Returns:
        Tuple van (extra_belasting, toelichting_tekst)
    """
    if config.eigen_woning is None or aftrek <= Decimal("0"):
        return Decimal("0"), ""

    # Schijf-3-grens = bovengrens van de tweede schijf in box1_niet_aow
    schijf3_grens = Decimal("0")
    for i, schijf in enumerate(config.box1_niet_aow):
        if i == 1 and schijf.tot is not None:
            schijf3_grens = schijf.tot
            break

    if bruto_inkomen <= schijf3_grens:
        return Decimal("0"), ""

    aftrek_in_schijf3 = min(aftrek, bruto_inkomen - schijf3_grens)
    aanpassing = _rond_af(aftrek_in_schijf3 * config.eigen_woning.tariefsaanpassing_pct)

    if aanpassing > Decimal("0"):
        toelichting = (
            f"Tariefsaanpassing aftrekposten: "
            f"{float(config.eigen_woning.tariefsaanpassing_pct) * 100:.2f}% "
            f"× € {int(aftrek_in_schijf3):,} = € {aanpassing:,} "
            f"(aftrek begrensd tot schijf-2-tarief)"
        )
        return aanpassing, toelichting

    return Decimal("0"), ""


def bereken_eigen_woning(
    invoer: EigenWoningInvoer,
    config: BelastingConfig,
) -> EigenWoningResultaat:
    """
    Bereken de fiscale gevolgen van de eigen woning voor box 1 en box 3.

    Args:
        invoer: Invoergegevens (WOZ, rente, schuld, inkomen voor tariefsaanpassing).
        config: Belastingconfiguratie voor het belastingjaar.

    Returns:
        EigenWoningResultaat met alle componenten en toelichting.
    """
    nul = Decimal("0")
    toelichting: list[str] = []

    if config.eigen_woning is None:
        return EigenWoningResultaat(
            eigenwoningforfait=nul,
            aftrekbare_hypotheekrente=nul,
            overige_aftrekbare_kosten=invoer.overige_aftrekbare_kosten,
            totaal_aftrek=nul,
            saldo_eigen_woning=nul,
            hillen_correctie=nul,
            box1_mutatie=nul,
            tariefsaanpassing=nul,
            box3_bezittingen=nul,
            box3_schulden=nul,
            toelichting=["Geen eigen-woning-configuratie beschikbaar voor dit belastingjaar."],
        )

    # 1. Eigenwoningforfait
    forfait, forfait_toelichting = _bereken_eigenwoningforfait(invoer.woz_waarde, config)
    toelichting.append(
        f"Eigenwoningforfait: WOZ € {int(invoer.woz_waarde):,} → € {forfait:,}"
    )
    toelichting.extend(forfait_toelichting)

    # 2. Aftrekbare kosten
    aftrekbare_rente = _rond_af(invoer.betaalde_hypotheekrente)
    overige_kosten = _rond_af(invoer.overige_aftrekbare_kosten)
    totaal_aftrek = aftrekbare_rente + overige_kosten
    if totaal_aftrek > nul:
        toelichting.append(
            f"Aftrekbare kosten: hypotheekrente € {aftrekbare_rente:,}"
            + (f" + overig € {overige_kosten:,}" if overige_kosten > nul else "")
            + f" = € {totaal_aftrek:,}"
        )

    # 3. Saldo eigen woning
    saldo = _rond_af(forfait - totaal_aftrek)
    if saldo < nul:
        toelichting.append(f"Saldo eigen woning: aftrekpost € {abs(saldo):,} (forfait − aftrek)")
    else:
        toelichting.append(f"Saldo eigen woning: bijtelling € {saldo:,} (forfait − aftrek)")

    # 4. Wet Hillen (alleen bij positief saldo)
    hillen_correctie = nul
    if saldo > nul and config.eigen_woning.wet_hillen_pct > nul:
        hillen_correctie = _rond_af(saldo * config.eigen_woning.wet_hillen_pct)
        toelichting.append(
            f"Wet Hillen-vermindering: {float(config.eigen_woning.wet_hillen_pct) * 100:.2f}% "
            f"× € {saldo:,} = € {hillen_correctie:,}"
        )

    saldo_na_hillen = _rond_af(saldo - hillen_correctie)

    # 5. Tariefsaanpassing (op de TOTALE AFTREKBARE KOSTEN, niet op het netto saldo)
    # Art. 3.123a Wet IB 2001: aftrekposten zijn begrensd tot schijf-2-tarief.
    # Grondslag = renteaftrek + overige kosten (vóór netting met forfait).
    tariefsaanpassing = nul
    if totaal_aftrek > nul:
        tariefsaanpassing, aanpassing_toelichting = _bereken_tariefsaanpassing(
            totaal_aftrek, invoer.bruto_inkomen_box1, config
        )
        if aanpassing_toelichting:
            toelichting.append(aanpassing_toelichting)

    # 6. Box 1 mutatie = saldo na Hillen (negatief verlaagt grondslag)
    box1_mutatie = saldo_na_hillen

    # 7. Box 3: woning en eigenwoningschuld zijn uitgesloten
    toelichting.append(
        "Eigen woning en eigenwoningschuld zijn uitgesloten van box 3 "
        "(art. 5.3 lid 2 en art. 5.4 Wet IB 2001)."
    )

    return EigenWoningResultaat(
        eigenwoningforfait=forfait,
        aftrekbare_hypotheekrente=aftrekbare_rente,
        overige_aftrekbare_kosten=overige_kosten,
        totaal_aftrek=totaal_aftrek,
        saldo_eigen_woning=saldo,
        hillen_correctie=hillen_correctie,
        box1_mutatie=box1_mutatie,
        tariefsaanpassing=tariefsaanpassing,
        box3_bezittingen=nul,
        box3_schulden=nul,
        toelichting=toelichting,
    )
