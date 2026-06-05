"""Vergelijk dutch_tax berekening met pensioen-app berekening.

Analyseert verschillen en genereert hypotheses over oorzaken.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

from .dutch_tax_adapter import DutchTaxData, laad_dutch_tax_submission
from .pensioen_adapter import (
    HuishoudBelastingResultaat,
    PensioenBelastingResultaat,
    bereken_via_pensioen_engine,
)


@dataclass
class VerschilAnalyse:
    """Analyse van één verschil tussen twee berekeningen."""

    categorie: str
    onderdeel: str
    dutch_tax_waarde: Decimal
    pensioen_app_waarde: Decimal
    verschil_absoluut: Decimal
    verschil_procent: Decimal | None
    oorzaak_hypothese: str
    ernst: str = ""  # "KRITIEK", "SIGNIFICANT", "KLEIN", "VERWAARLOOSBAAR"

    def __post_init__(self):
        """Bepaal ernst op basis van absolute waarde."""
        if not self.ernst:  # Alleen bepalen als niet al ingevuld
            abs_verschil = abs(self.verschil_absoluut)
            if abs_verschil >= Decimal("1000"):
                self.ernst = "KRITIEK"
            elif abs_verschil >= Decimal("100"):
                self.ernst = "SIGNIFICANT"
            elif abs_verschil >= Decimal("10"):
                self.ernst = "KLEIN"
            else:
                self.ernst = "VERWAARLOOSBAAR"


@dataclass
class VergelijkingsResultaat:
    """Volledig resultaat van vergelijking tussen beide systemen."""

    huishouden_id: str
    jaar: int
    submission_jaar: int  # Origineel jaar van de submission
    
    # Data
    dutch_tax_data: DutchTaxData
    pensioen_resultaat: HuishoudBelastingResultaat
    
    # Verschillen
    verschillen: list[VerschilAnalyse] = field(default_factory=list)
    
    # Samenvattingen
    totaal_verschil_te_betalen: Decimal = Decimal("0")
    aantal_kritieke_verschillen: int = 0
    aantal_significante_verschillen: int = 0
    
    # Conclusies & aanbevelingen
    conclusies: list[str] = field(default_factory=list)
    aanbevelingen: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Bereken samenvattingen."""
        self.aantal_kritieke_verschillen = sum(
            1 for v in self.verschillen if v.ernst == "KRITIEK"
        )
        self.aantal_significante_verschillen = sum(
            1 for v in self.verschillen if v.ernst == "SIGNIFICANT"
        )


def vergelijk_berekeningen(
    json_pad: Path,
    doel_jaar: int,
    geboortedatum_p1: date,
    geboortedatum_p2: date | None = None,
) -> VergelijkingsResultaat:
    """
    Vergelijk dutch_tax submission met pensioen-app berekening.
    
    Args:
        json_pad: Pad naar dutch_tax submission JSON
        doel_jaar: Jaar voor de berekening (meestal 2026)
        geboortedatum_p1: Geboortedatum persoon 1
        geboortedatum_p2: Geboortedatum persoon 2 (indien partner)
    
    Returns:
        VergelijkingsResultaat met alle verschillen en analyses
    """
    # Laad dutch_tax data
    dutch_data = laad_dutch_tax_submission(json_pad)
    
    # Bereken via pensioen-app
    pensioen_resultaat = bereken_via_pensioen_engine(
        dutch_data, doel_jaar, geboortedatum_p1, geboortedatum_p2
    )
    
    # Verzamel verschillen
    verschillen: list[VerschilAnalyse] = []
    
    # Vergelijk per persoon
    for idx, pensioen_persoon in enumerate(pensioen_resultaat.personen):
        if idx >= len(dutch_data.personen):
            break
        
        dutch_persoon = dutch_data.personen[idx]
        verschillen.extend(
            _vergelijk_persoon(dutch_persoon, pensioen_persoon, dutch_data, doel_jaar)
        )
    
    # Vergelijk Box 3 huishoudniveau
    verschillen.extend(
        _vergelijk_box3_huishoud(dutch_data, pensioen_resultaat)
    )
    
    # Vergelijk totaal
    verschillen.extend(
        _vergelijk_totaal(dutch_data, pensioen_resultaat)
    )
    
    # Genereer conclusies en aanbevelingen
    conclusies, aanbevelingen = _genereer_conclusies_aanbevelingen(
        verschillen, dutch_data, pensioen_resultaat
    )
    
    # Bereken totaal verschil
    totaal_verschil = pensioen_resultaat.totaal_te_betalen_terug - _bereken_dutch_tax_totaal(
        dutch_data
    )
    
    return VergelijkingsResultaat(
        huishouden_id=dutch_data.huishouden_id,
        jaar=doel_jaar,
        submission_jaar=dutch_data.jaar,
        dutch_tax_data=dutch_data,
        pensioen_resultaat=pensioen_resultaat,
        verschillen=verschillen,
        totaal_verschil_te_betalen=totaal_verschil,
        conclusies=conclusies,
        aanbevelingen=aanbevelingen,
    )


def _vergelijk_persoon(
    dutch_persoon,
    pensioen_persoon: PensioenBelastingResultaat,
    dutch_data: DutchTaxData,
    jaar: int,
) -> list[VerschilAnalyse]:
    """Vergelijk één persoon tussen beide systemen."""
    verschillen = []
    naam = dutch_persoon.naam
    
    # Bruto inkomen (zou gelijk moeten zijn)
    dutch_bruto = sum(
        (ink.bruto_bedrag for ink in dutch_persoon.inkomsten), Decimal("0")
    )
    verschil_bruto = pensioen_persoon.bruto_inkomen - dutch_bruto
    if abs(verschil_bruto) > Decimal("0.01"):
        verschillen.append(
            VerschilAnalyse(
                categorie=f"Box 1 - {naam}",
                onderdeel="Bruto inkomen",
                dutch_tax_waarde=dutch_bruto,
                pensioen_app_waarde=pensioen_persoon.bruto_inkomen,
                verschil_absoluut=verschil_bruto,
                verschil_procent=_bereken_procent(verschil_bruto, dutch_bruto),
                oorzaak_hypothese="Data mapping verschil",
            )
        )
    
    # Heffingskortingen vergelijken (complex!)
    # dutch_tax heeft totale tax credits, pensioen-app splits ze op
    dutch_totale_credits = sum(
        (hk.bedrag for hk in dutch_persoon.heffingskortingen), Decimal("0")
    )
    verschil_credits = pensioen_persoon.totale_heffingskorting - dutch_totale_credits
    
    if abs(verschil_credits) > Decimal("10"):
        hypothese = "Tariefverschil 2025→2026 én berekeningsverschil "
        hypothese += f"(dutch_tax: algemene korting, pensioen-app: AHK+arbeidskorting+ouderen)"
        
        verschillen.append(
            VerschilAnalyse(
                categorie=f"Heffingskortingen - {naam}",
                onderdeel="Totale heffingskorting",
                dutch_tax_waarde=dutch_totale_credits,
                pensioen_app_waarde=pensioen_persoon.totale_heffingskorting,
                verschil_absoluut=verschil_credits,
                verschil_procent=_bereken_procent(verschil_credits, dutch_totale_credits),
                oorzaak_hypothese=hypothese,
            )
        )
    
    # Eigenwoningforfait impact (indien aanwezig in dutch_tax)
    if dutch_persoon.eigen_woning:
        # Schatting: 0.25% van WOZ (conservatief gemiddelde)
        geschat_forfait = dutch_persoon.eigen_woning.woz_waarde * Decimal("0.0025")
        # Bij 35% belasting schijf = ca 0.09% WOZ aan extra belasting
        geschatte_impact = geschat_forfait * Decimal("0.35")
        
        verschillen.append(
            VerschilAnalyse(
                categorie=f"Box 1 - {naam}",
                onderdeel="Eigenwoningforfait (ONTBREEKT)",
                dutch_tax_waarde=geschatte_impact,
                pensioen_app_waarde=Decimal("0"),
                verschil_absoluut=-geschatte_impact,
                verschil_procent=Decimal("-100"),
                oorzaak_hypothese=(
                    f"Pensioen-app ondersteunt geen eigenwoningforfait. "
                    f"WOZ €{dutch_persoon.eigen_woning.woz_waarde:,.0f} → "
                    f"geschat forfait €{geschat_forfait:,.0f} → "
                    f"extra belasting ~€{geschatte_impact:,.0f} (indicatief)"
                ),
            )
        )
    
    # Aftrekposten impact (indien aanwezig)
    if dutch_persoon.aftrekposten:
        totaal_aftrek = sum((a.bedrag for a in dutch_persoon.aftrekposten), Decimal("0"))
        # Bij 35% belasting schijf
        geschatte_impact = totaal_aftrek * Decimal("0.35")
        
        verschillen.append(
            VerschilAnalyse(
                categorie=f"Box 1 - {naam}",
                onderdeel="Aftrekposten (ONTBREKEN)",
                dutch_tax_waarde=geschatte_impact,
                pensioen_app_waarde=Decimal("0"),
                verschil_absoluut=-geschatte_impact,
                verschil_procent=Decimal("-100"),
                oorzaak_hypothese=(
                    f"Pensioen-app ondersteunt geen aftrekposten. "
                    f"{len(dutch_persoon.aftrekposten)} aftrekpost(en) "
                    f"totaal €{totaal_aftrek:,.0f} → "
                    f"belastingvoordeel ~€{geschatte_impact:,.0f} (indicatief)"
                ),
            )
        )
    
    return verschillen


def _vergelijk_box3_huishoud(
    dutch_data: DutchTaxData, pensioen_resultaat: HuishoudBelastingResultaat
) -> list[VerschilAnalyse]:
    """Vergelijk Box 3 op huishoudniveau."""
    verschillen = []
    
    # Totaal vermogen
    dutch_vermogen = dutch_data.netto_vermogen()
    verschil = pensioen_resultaat.box3_totaal_vermogen - dutch_vermogen
    
    if abs(verschil) > Decimal("1"):
        verschillen.append(
            VerschilAnalyse(
                categorie="Box 3",
                onderdeel="Totaal vermogen",
                dutch_tax_waarde=dutch_vermogen,
                pensioen_app_waarde=pensioen_resultaat.box3_totaal_vermogen,
                verschil_absoluut=verschil,
                verschil_procent=_bereken_procent(verschil, dutch_vermogen),
                oorzaak_hypothese="Data mapping verschil",
            )
        )
    
    # Vrijstelling
    aantal = 2 if dutch_data.heeft_fiscaal_partner else 1
    # dutch_tax 2025: €57.684, pensioen-app 2026: €59.357
    # We kunnen dit niet direct vergelijken zonder tarieven, maar melden het
    
    # Box 3 heffing
    # dutch_tax heeft waarschijnlijk een andere berekening
    # We kunnen dit alleen als schatting doen zonder de volledige dutch_tax berekening
    
    # Spaargeld vs beleggingen fractie
    dutch_spaargeld = dutch_data.totaal_spaargeld()
    dutch_beleggingen = dutch_data.totaal_beleggingen()
    dutch_totaal_positief = dutch_spaargeld + dutch_beleggingen
    
    if dutch_totaal_positief > Decimal("0"):
        dutch_fractie = dutch_spaargeld / dutch_totaal_positief
        verschil_fractie = pensioen_resultaat.box3_spaargeld_fractie - dutch_fractie
        
        if abs(verschil_fractie) > Decimal("0.01"):
            verschillen.append(
                VerschilAnalyse(
                    categorie="Box 3",
                    onderdeel="Spaargeld fractie",
                    dutch_tax_waarde=dutch_fractie,
                    pensioen_app_waarde=pensioen_resultaat.box3_spaargeld_fractie,
                    verschil_absoluut=verschil_fractie,
                    verschil_procent=_bereken_procent(verschil_fractie, dutch_fractie),
                    oorzaak_hypothese="Data mapping of categorie-indeling verschil",
                )
            )
    
    return verschillen


def _vergelijk_totaal(
    dutch_data: DutchTaxData, pensioen_resultaat: HuishoudBelastingResultaat
) -> list[VerschilAnalyse]:
    """Vergelijk totalen."""
    verschillen = []
    
    # We kunnen totaal te betalen niet direct vergelijken zonder volledige dutch_tax berekening
    # Maar we kunnen wel de pensioen-app totaal rapporteren
    
    # Vooraf betaald (loonheffing + dividend)
    dutch_vooraf = sum(
        (p.loonheffing_ingehouden for p in dutch_data.personen), Decimal("0")
    )
    dutch_vooraf += dutch_data.totaal_dividend_ingehouden
    
    pensioen_vooraf = sum(
        (p.vooraf_betaald for p in pensioen_resultaat.personen), Decimal("0")
    )
    
    verschil_vooraf = pensioen_vooraf - dutch_vooraf
    if abs(verschil_vooraf) > Decimal("1"):
        oorzaak = "Pensioen-app neemt mogelijk geen dividend ingehouden mee in vooraf betaald"
        if dutch_data.totaal_dividend_ingehouden > Decimal("0"):
            oorzaak += f" (dutch_tax: €{dutch_data.totaal_dividend_ingehouden:,.2f} dividend)"
        
        verschillen.append(
            VerschilAnalyse(
                categorie="Totaal",
                onderdeel="Vooraf betaald (loonheffing + dividend)",
                dutch_tax_waarde=dutch_vooraf,
                pensioen_app_waarde=pensioen_vooraf,
                verschil_absoluut=verschil_vooraf,
                verschil_procent=_bereken_procent(verschil_vooraf, dutch_vooraf),
                oorzaak_hypothese=oorzaak,
            )
        )
    
    return verschillen


def _bereken_dutch_tax_totaal(dutch_data: DutchTaxData) -> Decimal:
    """
    Schatting van dutch_tax totaal te betalen.
    
    WAARSCHUWING: Dit is een vereenvoudigde schatting, niet de volledige berekening!
    """
    # We hebben geen volledige dutch_tax berekening, dus retourneren we 0
    # De verschillenanalyse focust op deelonderdelen
    return Decimal("0")


def _bereken_procent(verschil: Decimal, basis: Decimal) -> Decimal | None:
    """Bereken verschil als percentage van basis."""
    if basis == Decimal("0"):
        return None
    return (verschil / basis) * Decimal("100")


def _genereer_conclusies_aanbevelingen(
    verschillen: list[VerschilAnalyse],
    dutch_data: DutchTaxData,
    pensioen_resultaat: HuishoudBelastingResultaat,
) -> tuple[list[str], list[str]]:
    """Genereer conclusies en aanbevelingen op basis van verschillen."""
    conclusies = []
    aanbevelingen = []
    
    # Aantal verschillen per ernst
    kritiek = sum(1 for v in verschillen if v.ernst == "KRITIEK")
    significant = sum(1 for v in verschillen if v.ernst == "SIGNIFICANT")
    
    conclusies.append(
        f"Gevonden: {len(verschillen)} verschillen "
        f"({kritiek} kritiek, {significant} significant)"
    )
    
    # Check voor eigenwoningforfait
    heeft_eigen_woning = any(p.eigen_woning for p in dutch_data.personen)
    if heeft_eigen_woning:
        conclusies.append(
            "⚠️ Eigenwoningforfait aanwezig in dutch_tax, ontbreekt in pensioen-app"
        )
        aanbevelingen.append(
            "PRIORITEIT 1: Implementeer eigenwoningforfait berekening in pensioen-app "
            "(kan €100-500+ impact hebben per jaar)"
        )
    
    # Check voor aftrekposten
    heeft_aftrekposten = any(p.aftrekposten for p in dutch_data.personen)
    if heeft_aftrekposten:
        conclusies.append(
            "⚠️ Aftrekposten aanwezig in dutch_tax, ontbreken in pensioen-app"
        )
        aanbevelingen.append(
            "PRIORITEIT 2: Voeg ondersteuning toe voor veelvoorkomende aftrekposten "
            "(beddengoed, giften, etc.)"
        )
    
    # Check voor dividend ingehouden
    if dutch_data.totaal_dividend_ingehouden > Decimal("0"):
        conclusies.append(
            f"ℹ️ Dividend ingehouden: €{dutch_data.totaal_dividend_ingehouden:,.2f}"
        )
        aanbevelingen.append(
            "PRIORITEIT 3: Controleer of dividend ingehouden correct wordt verrekend "
            "in Box 3 berekening"
        )
    
    # Tariefjaar verschil
    if dutch_data.jaar != pensioen_resultaat.jaar:
        conclusies.append(
            f"ℹ️ Tariefverschil: dutch_tax {dutch_data.jaar} vs "
            f"pensioen-app {pensioen_resultaat.jaar} - "
            f"kleine verschillen in heffingskortingen/schijven zijn normaal"
        )
    
    # Heffingskortingen
    hk_verschillen = [v for v in verschillen if "Heffingskortingen" in v.categorie]
    if hk_verschillen:
        conclusies.append(
            "ℹ️ Heffingskortingen verschillen: dutch_tax gebruikt 'algemene korting', "
            "pensioen-app berekent AHK/arbeidskorting/ouderenkorting apart"
        )
        aanbevelingen.append(
            "VERIFICATIE: Controleer of pensioen-app heffingskortingen formules "
            "up-to-date zijn voor 2026"
        )
    
    return conclusies, aanbevelingen
