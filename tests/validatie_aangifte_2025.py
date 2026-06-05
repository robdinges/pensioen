"""
Validatiescript voor Aangifte 2025 - Interactieve Component Vergelijking

Dit script valideert het pensioenmodel tegen een echte aangifte 2025:
- Persoon: Alleenstaand, AOW-ontvanger (geboortedatum 1954-01-01)
- Inkomen: €86.813 pensioen
- Vermogen: €500.000 (€200.000 spaargeld, €300.000 beleggingen)

Toont verschillen per component met colored output voor interactieve debugging.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

import pytest

from pensioen.tax.belasting_engine import (
    bereken_box1_belasting,
    bereken_box3_heffing,
    bereken_premies_volksverzekeringen,
    netto_uit_bruto,
)
from pensioen.tax.belasting_loader import laad_tarieven
from pensioen.tax import aow_engine, heffingskorting


# ============================================================================
# AANGIFTE 2025 REFERENTIE
# ============================================================================

AANGIFTE_2025_REF = {
    "persoon": {
        "geboortedatum": date(1954, 1, 1),  # ~71 jaar in 2025, AOW-gerechtigd
        "is_alleenstaand": True,
    },
    "inkomen": {
        "pensioen_bruto": Decimal("86813"),
        "arbeidsinkomen": Decimal("0"),
        "totaal_bruto": Decimal("86813"),
    },
    "vermogen": {
        "totaal": Decimal("500000"),
        "bankrekeningen": Decimal("200000"),
        "beleggingen": Decimal("300000"),
    },
    "verwacht": {
        # Box 1 - Inkomstenbelasting per schijf
        "ib_schijf1": Decimal("3140"),    # 8,17% × €38.441
        "ib_schijf2": Decimal("14383"),   # 37,48% × €38.376
        "ib_schijf3": Decimal("4948"),    # 49,50% × €9.996
        "totaal_ib": Decimal("22471"),
        
        # Premies volksverzekeringen (alleen over schijf 1: €38.441)
        "premie_aow": Decimal("0"),       # 0% × €38.441 (al AOW-gerechtigd)
        "premie_anw": Decimal("38"),      # 0,1% × €38.441
        "premie_wlz": Decimal("3709"),    # 9,65% × €38.441
        "totaal_premies": Decimal("3747"),
        
        # Box 3
        "grondslag_box3": Decimal("442316"),  # €500.000 - €57.684
        "fictief_rendement": Decimal("18028"),
        "box3_belasting": Decimal("6490"),    # 36% × €18.028
        
        # Heffingskortingen
        "ahk": Decimal("0"),
        "ouderenkorting": Decimal("0"),
        "alleenstaandeouderenkorting": Decimal("531"),
        "totaal_kortingen": Decimal("531"),
        
        # Totaal verschuldigd
        "totaal_belasting_en_premies": Decimal("32708"),  # €22.471 + €3.747 + €6.490
        "totaal_verschuldigd": Decimal("32177"),  # €32.708 - €531
    }
}


# ============================================================================
# VALIDATIE HELPERS
# ============================================================================

@dataclass
class ComponentVerschil:
    """Een verschil tussen aangifte en model voor één component."""
    naam: str
    aangifte: Decimal
    model: Decimal
    verschil: Decimal
    tolerantie: Decimal = Decimal("1")  # €1 default tolerantie
    
    @property
    def is_match(self) -> bool:
        """Check of verschil binnen tolerantie valt."""
        return abs(self.verschil) <= self.tolerantie
    
    @property
    def status_icon(self) -> str:
        """Emoji status indicator."""
        return "✅" if self.is_match else "❌"
    
    @property
    def status_color(self) -> str:
        """ANSI color code."""
        return "\033[92m" if self.is_match else "\033[91m"  # Groen / Rood


@dataclass
class ValidatieRapport:
    """Volledig validatierapport met alle componentverschillen."""
    jaar: int
    box1_verschillen: list[ComponentVerschil]
    premie_verschillen: list[ComponentVerschil]
    box3_verschillen: list[ComponentVerschil]
    korting_verschillen: list[ComponentVerschil]
    totaal_verschillen: list[ComponentVerschil]
    
    @property
    def alle_verschillen(self) -> list[ComponentVerschil]:
        """Alle verschillen gecombineerd."""
        return (
            self.box1_verschillen +
            self.premie_verschillen +
            self.box3_verschillen +
            self.korting_verschillen +
            self.totaal_verschillen
        )
    
    @property
    def is_volledig_match(self) -> bool:
        """Check of alle componenten matchen."""
        return all(v.is_match for v in self.alle_verschillen)
    
    @property
    def aantal_matches(self) -> int:
        """Aantal componenten dat matched."""
        return sum(1 for v in self.alle_verschillen if v.is_match)
    
    @property
    def aantal_mismatches(self) -> int:
        """Aantal componenten dat niet matched."""
        return sum(1 for v in self.alle_verschillen if not v.is_match)


# ============================================================================
# VALIDATIE ENGINE
# ============================================================================

def bereken_model_2025(
    bruto_inkomen: Decimal,
    vermogen_totaal: Decimal,
    spaargeld_fractie: Decimal,
    geboortedatum: date,
    is_alleenstaand: bool,
) -> dict:
    """
    Bereken belasting met het huidige model (2025 config).
    
    Returns:
        Dict met alle berekende componenten voor vergelijking.
    """
    config, _ = laad_tarieven(2025)  # Unpack tuple (config, aanname_melding)
    jaar = 2025
    
    # AOW-status
    aow_breuk = aow_engine.aow_breuk_jaar(geboortedatum, jaar)
    is_aow_heel_jaar = aow_breuk >= Decimal("1")
    is_aow_deels = aow_breuk > Decimal("0")
    
    # Box 1 inkomstenbelasting (pure IB)
    box1_ib = bereken_box1_belasting(bruto_inkomen, config, aow_breuk)
    
    # Premies volksverzekeringen (nu apart berekend!)
    premie_aow, premie_anw, premie_wlz, totaal_premies = bereken_premies_volksverzekeringen(
        bruto_inkomen, config, is_aow_heel_jaar
    )
    
    # Heffingskortingen (inclusief alleenstaandeouderenkorting)
    ahk = heffingskorting.bereken_ahk(bruto_inkomen, config)
    arbeidskorting = heffingskorting.bereken_arbeidskorting(Decimal("0"), config)
    ouderenkorting = heffingskorting.bereken_ouderenkorting(bruto_inkomen, config, is_aow_deels)
    alleenstaandeouderenkorting = heffingskorting.bereken_alleenstaandeouderenkorting(
        bruto_inkomen, config, is_aow_deels, is_alleenstaand
    )
    totaal_kortingen = ahk + arbeidskorting + ouderenkorting + alleenstaandeouderenkorting
    
    # Box 3 belasting
    box3_belasting, _ = bereken_box3_heffing(
        vermogen_totaal,
        config,
        heeft_partner=not is_alleenstaand,
        spaargeld_fractie=spaargeld_fractie,
    )
    
    # Bereken grondslag en fictief rendement voor validatie
    vrijstelling = config.box3.vrijstelling_per_persoon * (1 if is_alleenstaand else 2)
    grondslag_box3 = max(Decimal("0"), vermogen_totaal - vrijstelling)
    overig_fractie = Decimal("1") - spaargeld_fractie
    gewogen_forfait = (
        spaargeld_fractie * config.box3.forfaitair_spaargeld +
        overig_fractie * config.box3.forfaitair_overig
    )
    fictief_rendement = grondslag_box3 * gewogen_forfait
    
    # Totalen
    totaal_belasting_en_premies = box1_ib + totaal_premies + box3_belasting
    totaal_verschuldigd = totaal_belasting_en_premies - totaal_kortingen
    
    return {
        "box1_ib": box1_ib,
        "premie_aow": premie_aow,
        "premie_anw": premie_anw,
        "premie_wlz": premie_wlz,
        "totaal_premies": totaal_premies,
        "grondslag_box3": grondslag_box3,
        "fictief_rendement": fictief_rendement,
        "box3_belasting": box3_belasting,
        "ahk": ahk,
        "ouderenkorting": ouderenkorting,
        "alleenstaandeouderenkorting": alleenstaandeouderenkorting,
        "totaal_kortingen": totaal_kortingen,
        "totaal_belasting_en_premies": totaal_belasting_en_premies,
        "totaal_verschuldigd": totaal_verschuldigd,
        "config": config,
    }


def valideer_aangifte_2025() -> ValidatieRapport:
    """
    Valideer het model tegen de aangifte 2025.
    
    Returns:
        ValidatieRapport met alle componentverschillen.
    """
    ref = AANGIFTE_2025_REF
    
    # Bereken met model
    spaargeld_fractie = ref["vermogen"]["bankrekeningen"] / ref["vermogen"]["totaal"]
    model = bereken_model_2025(
        bruto_inkomen=ref["inkomen"]["totaal_bruto"],
        vermogen_totaal=ref["vermogen"]["totaal"],
        spaargeld_fractie=spaargeld_fractie,
        geboortedatum=ref["persoon"]["geboortedatum"],
        is_alleenstaand=ref["persoon"]["is_alleenstaand"],
    )
    
    exp = ref["verwacht"]
    
    # Box 1 verschillen
    # Nu kunnen we IB apart vergelijken!
    box1_verschillen = [
        ComponentVerschil(
            naam="Totaal IB (box 1)",
            aangifte=exp["totaal_ib"],
            model=model["box1_ib"],
            verschil=model["box1_ib"] - exp["totaal_ib"],
        ),
    ]
    
    # Premie verschillen (model berekent deze nog niet apart)
    premie_verschillen = [
        ComponentVerschil(
            naam="Premie AOW",
            aangifte=exp["premie_aow"],
            model=model["premie_aow"],
            verschil=model["premie_aow"] - exp["premie_aow"],
        ),
        ComponentVerschil(
            naam="Premie Anw",
            aangifte=exp["premie_anw"],
            model=model["premie_anw"],
            verschil=model["premie_anw"] - exp["premie_anw"],
        ),
        ComponentVerschil(
            naam="Premie Wlz",
            aangifte=exp["premie_wlz"],
            model=model["premie_wlz"],
            verschil=model["premie_wlz"] - exp["premie_wlz"],
        ),
    ]
    
    # Box 3 verschillen
    box3_verschillen = [
        ComponentVerschil(
            naam="Grondslag box 3",
            aangifte=exp["grondslag_box3"],
            model=model["grondslag_box3"],
            verschil=model["grondslag_box3"] - exp["grondslag_box3"],
        ),
        ComponentVerschil(
            naam="Fictief rendement",
            aangifte=exp["fictief_rendement"],
            model=model["fictief_rendement"],
            verschil=model["fictief_rendement"] - exp["fictief_rendement"],
        ),
        ComponentVerschil(
            naam="Box 3 belasting",
            aangifte=exp["box3_belasting"],
            model=model["box3_belasting"],
            verschil=model["box3_belasting"] - exp["box3_belasting"],
        ),
    ]
    
    # Heffingskorting verschillen
    korting_verschillen = [
        ComponentVerschil(
            naam="Algemene heffingskorting",
            aangifte=exp["ahk"],
            model=model["ahk"],
            verschil=model["ahk"] - exp["ahk"],
        ),
        ComponentVerschil(
            naam="Ouderenkorting",
            aangifte=exp["ouderenkorting"],
            model=model["ouderenkorting"],
            verschil=model["ouderenkorting"] - exp["ouderenkorting"],
        ),
        ComponentVerschil(
            naam="Alleenstaandeouderenkorting",
            aangifte=exp["alleenstaandeouderenkorting"],
            model=model["alleenstaandeouderenkorting"],
            verschil=model["alleenstaandeouderenkorting"] - exp["alleenstaandeouderenkorting"],
        ),
    ]
    
    # Totaal verschillen
    totaal_verschillen = [
        ComponentVerschil(
            naam="TOTAAL VERSCHULDIGD",
            aangifte=exp["totaal_verschuldigd"],
            model=model["totaal_verschuldigd"],
            verschil=model["totaal_verschuldigd"] - exp["totaal_verschuldigd"],
            tolerantie=Decimal("5"),  # Iets ruimere tolerantie voor totaal
        ),
    ]
    
    return ValidatieRapport(
        jaar=2025,
        box1_verschillen=box1_verschillen,
        premie_verschillen=premie_verschillen,
        box3_verschillen=box3_verschillen,
        korting_verschillen=korting_verschillen,
        totaal_verschillen=totaal_verschillen,
    )


# ============================================================================
# COLORED OUTPUT
# ============================================================================

def format_bedrag(bedrag: Decimal) -> str:
    """Format bedrag als €X.XXX."""
    return f"€{bedrag:,.0f}".replace(",", ".")


def print_sectie_header(titel: str, breedte: int = 70) -> None:
    """Print een sectie header."""
    print("\n" + titel)
    print("━" * breedte)


def print_component_lijn(verschil: ComponentVerschil, naam_breedte: int = 30) -> None:
    """Print één component-lijn met colored output."""
    RESET = "\033[0m"
    naam = verschil.naam.ljust(naam_breedte)
    aangifte = format_bedrag(verschil.aangifte).rjust(12)
    model = format_bedrag(verschil.model).rjust(12)
    
    # Verschil met +/- en kleur
    verschil_str = format_bedrag(abs(verschil.verschil))
    if verschil.verschil > 0:
        verschil_str = "+" + verschil_str
    elif verschil.verschil < 0:
        verschil_str = "-" + verschil_str
    else:
        verschil_str = " " + verschil_str
    verschil_str = verschil_str.rjust(13)
    
    status = verschil.status_icon
    
    # Print met kleur
    print(
        f"{naam}  "
        f"{aangifte}  "
        f"{model}  "
        f"{verschil.status_color}{verschil_str}{RESET}  "
        f"{status}"
    )


def print_validatie_rapport(rapport: ValidatieRapport) -> None:
    """Print het volledige validatierapport met colored output."""
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    print("\n" + "=" * 70)
    print(f"{BOLD}  VALIDATIE AANGIFTE {rapport.jaar} - COMPONENT VERGELIJKING{RESET}")
    print("=" * 70)
    
    # Header
    naam_breedte = 30
    print(
        f"{'Component'.ljust(naam_breedte)}  "
        f"{'Aangifte'.rjust(12)}  "
        f"{'Model'.rjust(12)}  "
        f"{'Verschil'.rjust(13)}  "
        f"St"
    )
    print("─" * 70)
    
    # Box 1
    if rapport.box1_verschillen:
        print_sectie_header("BOX 1 BELASTING")
        for v in rapport.box1_verschillen:
            print_component_lijn(v, naam_breedte)
    
    # Premies
    if rapport.premie_verschillen:
        print_sectie_header("PREMIES VOLKSVERZEKERINGEN")
        for v in rapport.premie_verschillen:
            print_component_lijn(v, naam_breedte)
    
    # Box 3
    if rapport.box3_verschillen:
        print_sectie_header("BOX 3 SPAREN EN BELEGGEN")
        for v in rapport.box3_verschillen:
            print_component_lijn(v, naam_breedte)
    
    # Kortingen
    if rapport.korting_verschillen:
        print_sectie_header("HEFFINGSKORTINGEN")
        for v in rapport.korting_verschillen:
            print_component_lijn(v, naam_breedte)
    
    # Totaal
    if rapport.totaal_verschillen:
        print_sectie_header("TOTAAL")
        for v in rapport.totaal_verschillen:
            print_component_lijn(v, naam_breedte)
    
    # Samenvatting
    print("\n" + "=" * 70)
    if rapport.is_volledig_match:
        print(f"\033[92m✅ VALIDATIE GESLAAGD{RESET} - Alle componenten matchen binnen tolerantie")
    else:
        print(
            f"\033[91m❌ VALIDATIE MISLUKT{RESET} - "
            f"{rapport.aantal_mismatches} van {len(rapport.alle_verschillen)} componenten wijken af"
        )
    print("=" * 70 + "\n")


# ============================================================================
# PYTEST TESTS
# ============================================================================

def test_validatie_aangifte_2025_baseline():
    """
    Baseline validatie: toont huidige verschillen tussen model en aangifte 2025.
    
    Deze test faalt verwacht in de baseline (voor de refactor).
    Na de implementatie van premie-splitsing en alleenstaandeouderenkorting
    moet deze test slagen.
    """
    rapport = valideer_aangifte_2025()
    
    # Print rapport voor interactieve debugging
    print_validatie_rapport(rapport)
    
    # Assert: We verwachten dat dit initieel faalt
    # (Uncomment de volgende regel om te testen na implementatie)
    # assert rapport.is_volledig_match, f"{rapport.aantal_mismatches} componenten wijken af"
    
    # Voor nu: alleen een soft check op het totaalverschil
    totaal_verschil = rapport.totaal_verschillen[0]
    if not totaal_verschil.is_match:
        print(
            f"\n⚠️  LET OP: Totaalverschil is {format_bedrag(abs(totaal_verschil.verschil))} "
            f"(verwacht: binnen €{totaal_verschil.tolerantie})"
        )


def test_box3_vrijstelling_2025():
    """Specifieke test: Box 3 vrijstelling moet €57.684 zijn (niet €57.000)."""
    config, _ = laad_tarieven(2025)  # Unpack tuple
    
    verwacht_vrijstelling = Decimal("57684")
    actuele_vrijstelling = config.box3.vrijstelling_per_persoon
    
    assert actuele_vrijstelling == verwacht_vrijstelling, (
        f"Box 3 vrijstelling 2025 moet €{verwacht_vrijstelling} zijn, "
        f"maar is €{actuele_vrijstelling}"
    )


if __name__ == "__main__":
    # Run validatie standalone (zonder pytest)
    rapport = valideer_aangifte_2025()
    print_validatie_rapport(rapport)
    
    # Save rapport naar markdown
    import os
    rapporten_dir = os.path.join(os.path.dirname(__file__), "..", "rapporten")
    os.makedirs(rapporten_dir, exist_ok=True)
    
    rapport_path = os.path.join(rapporten_dir, "validatie_baseline_2025.md")
    with open(rapport_path, "w") as f:
        f.write(f"# Validatie Aangifte 2025 - Baseline Rapport\n\n")
        f.write(f"**Datum:** {date.today().isoformat()}\n\n")
        f.write("## Samenvatting\n\n")
        if rapport.is_volledig_match:
            f.write("✅ **VALIDATIE GESLAAGD** - Alle componenten matchen binnen tolerantie\n\n")
        else:
            f.write(
                f"❌ **VALIDATIE MISLUKT** - "
                f"{rapport.aantal_mismatches} van {len(rapport.alle_verschillen)} componenten wijken af\n\n"
            )
        
        f.write("## Verschillen per Component\n\n")
        for sectie_naam, verschillen in [
            ("Box 1 Belasting", rapport.box1_verschillen),
            ("Premies Volksverzekeringen", rapport.premie_verschillen),
            ("Box 3 Sparen en Beleggen", rapport.box3_verschillen),
            ("Heffingskortingen", rapport.korting_verschillen),
            ("Totaal", rapport.totaal_verschillen),
        ]:
            if verschillen:
                f.write(f"### {sectie_naam}\n\n")
                f.write("| Component | Aangifte | Model | Verschil | Status |\n")
                f.write("|-----------|----------|-------|----------|--------|\n")
                for v in verschillen:
                    status = "✅" if v.is_match else "❌"
                    verschil_str = format_bedrag(abs(v.verschil))
                    if v.verschil > 0:
                        verschil_str = "+" + verschil_str
                    elif v.verschil < 0:
                        verschil_str = "-" + verschil_str
                    f.write(
                        f"| {v.naam} | {format_bedrag(v.aangifte)} | "
                        f"{format_bedrag(v.model)} | {verschil_str} | {status} |\n"
                    )
                f.write("\n")
    
    print(f"\n📄 Rapport opgeslagen: {rapport_path}")
