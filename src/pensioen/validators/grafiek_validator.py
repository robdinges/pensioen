"""Runtime validatie van consistentie tussen grafieken en accountantsoverzicht."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from pensioen.models.cashflow import HuishoudCashflow, JaarResultaat


@dataclass
class ValidatieResultaat:
    """Resultaat van grafiek-consistentie validatie."""
    
    is_geldig: bool
    fouten: list[str]
    waarschuwingen: list[str]


def valideer_jaar_consistency(jr: JaarResultaat) -> ValidatieResultaat:
    """
    Controleer of een enkel jaar intern consistent is.
    
    Controleert:
    - Som van bruto componenten = totaal_bruto
    - Box1 + Box3 = totaal_belasting
    - Netto berekening klopt
    - Geen dubbeltelling van inkomensbronnen
    """
    fouten = []
    waarschuwingen = []
    
    # Check 1: Bruto componenten (inclusief rendement)
    bruto_inkomen = jr.arbeid_bruto + jr.aow_bruto + jr.pensioen_bruto + jr.overig_bruto
    rendement = sum(m.rente_bruto for m in jr.maanden)
    bruto_som = bruto_inkomen + rendement
    
    if bruto_som != jr.totaal_bruto:
        verschil = abs(bruto_som - jr.totaal_bruto)
        if verschil > Decimal("10"):  # Meer dan €10 verschil is een fout
            fouten.append(
                f"Jaar {jr.jaar}: Som bruto componenten (€{bruto_inkomen:,.0f}) "
                f"+ rendement (€{rendement:,.0f}) = €{bruto_som:,.0f} "
                f"≠ totaal_bruto (€{jr.totaal_bruto:,.0f}), verschil: €{verschil:,.0f}"
            )
        else:
            waarschuwingen.append(
                f"Jaar {jr.jaar}: Klein afrondingsverschil in bruto ({verschil})"
            )
    
    # Check 2: Belastingcomponenten
    if jr.box1_belasting + jr.box3_heffing != jr.totaal_belasting:
        fouten.append(
            f"Jaar {jr.jaar}: Box1 (€{jr.box1_belasting:,.0f}) + "
            f"Box3 (€{jr.box3_heffing:,.0f}) ≠ "
            f"totaal_belasting (€{jr.totaal_belasting:,.0f})"
        )
    
    # Check 3: Netto berekening
    netto_component_inkomen = sum(m.inkomen_componenten_netto for m in jr.maanden)
    # Rendement is al berekend in Check 1
    
    netto_handmatig = (
        jr.totaal_bruto
        + netto_component_inkomen
        - jr.totaal_belasting
        + jr.totaal_heffingskorting
        - jr.inhoudingen
        - jr.huishoudelijke_uitgaven
        - jr.eenmalige_uitgaven
        + jr.eenmalige_ontvangsten
    )
    
    verschil_netto = abs(netto_handmatig - jr.netto)
    if verschil_netto > Decimal("1"):
        fouten.append(
            f"Jaar {jr.jaar}: Netto berekening inconsistent. "
            f"Handmatig: €{netto_handmatig:,.0f}, "
            f"JaarResultaat: €{jr.netto:,.0f}, "
            f"verschil: €{verschil_netto:,.2f}"
        )
    
    # Check 4: Som van maanden
    totaal_bruto_maanden = sum(m.totaal_bruto for m in jr.maanden)
    if totaal_bruto_maanden != jr.totaal_bruto:
        fouten.append(
            f"Jaar {jr.jaar}: Som maanden bruto (€{totaal_bruto_maanden:,.0f}) "
            f"≠ totaal_bruto (€{jr.totaal_bruto:,.0f})"
        )
    
    is_geldig = len(fouten) == 0
    return ValidatieResultaat(is_geldig=is_geldig, fouten=fouten, waarschuwingen=waarschuwingen)


def valideer_cashflow_consistency(cashflow: HuishoudCashflow) -> ValidatieResultaat:
    """
    Valideer alle jaren in een cashflow op consistentie.
    
    Retourneert een ValidatieResultaat met alle gevonden fouten en waarschuwingen.
    """
    alle_fouten = []
    alle_waarschuwingen = []
    
    for jr in cashflow.jaren:
        resultaat = valideer_jaar_consistency(jr)
        alle_fouten.extend(resultaat.fouten)
        alle_waarschuwingen.extend(resultaat.waarschuwingen)
    
    is_geldig = len(alle_fouten) == 0
    return ValidatieResultaat(
        is_geldig=is_geldig,
        fouten=alle_fouten,
        waarschuwingen=alle_waarschuwingen,
    )


def toon_validatie_samenvatting(cashflow: HuishoudCashflow) -> str:
    """
    Genereer een leesbare samenvatting van de validatie voor gebruikersfeedback.
    
    Returns:
        String met validatieresultaat (voor display in UI).
    """
    resultaat = valideer_cashflow_consistency(cashflow)
    
    if resultaat.is_geldig and not resultaat.waarschuwingen:
        return "✅ Alle grafieken en overzichten zijn consistent."
    
    output_lines = []
    
    if resultaat.fouten:
        output_lines.append(f"❌ **{len(resultaat.fouten)} fout(en) gedetecteerd:**")
        for fout in resultaat.fouten[:5]:  # Toon max 5 fouten
            output_lines.append(f"  • {fout}")
        if len(resultaat.fouten) > 5:
            output_lines.append(f"  ... en {len(resultaat.fouten) - 5} meer")
    
    if resultaat.waarschuwingen:
        output_lines.append(f"\n⚠️ **{len(resultaat.waarschuwingen)} waarschuwing(en):**")
        for waarschuwing in resultaat.waarschuwingen[:3]:
            output_lines.append(f"  • {waarschuwing}")
        if len(resultaat.waarschuwingen) > 3:
            output_lines.append(f"  ... en {len(resultaat.waarschuwingen) - 3} meer")
    
    return "\n".join(output_lines)
