"""Testcase validatie: bereken belasting voor 1 jaar en vergelijk met verwachte waarde.

Dit module biedt functies om een testcase te valideren door de belasting
te berekenen en te vergelijken met de verwachte belasting uit de testcase.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from pensioen.calculations.cashflow_engine import bereken_accountant_jaar_detail
from pensioen.tax.belasting_loader import laad_tarieven
from pensioen.tax import belasting_engine, heffingskorting
from tests.models.testcase import TestCase
from tests.scenario_generator import genereer_personen, genereer_testcase_scenario

def _controleer_consistentie_verwachte_belasting(testcase: TestCase) -> list[str]:
    """Controleer interne consistentie van verwachte_belasting-velden."""
    waarschuwingen: list[str] = []
    verwacht = testcase.verwachte_belasting

    # Huishoudtotaal versus per-persoon totalen.
    if testcase.is_paar and verwacht.totaal_verschuldigd_p1 is not None and verwacht.totaal_verschuldigd_p2 is not None:
        som_persoon = verwacht.totaal_verschuldigd_p1 + verwacht.totaal_verschuldigd_p2
        if abs(verwacht.totaal_verschuldigd - som_persoon) > Decimal("5"):
            waarschuwingen.append(
                (
                    "verwachte_belasting.totaal_verschuldigd wijkt af van "
                    "totaal_verschuldigd_p1 + totaal_verschuldigd_p2"
                )
            )

    # Controle kortingen P1/P2 versus componenten.
    for suffix in ("p1", "p2"):
        totaal = getattr(verwacht, f"totaal_kortingen_{suffix}", None)
        if totaal is None:
            continue

        componenten = [
            getattr(verwacht, f"ahk_{suffix}", None),
            getattr(verwacht, f"arbeidskorting_{suffix}", None),
            getattr(verwacht, f"ouderenkorting_{suffix}", None),
        ]

        # Historisch veld zonder suffix blijft ondersteund voor P1.
        if suffix == "p1":
            componenten.append(getattr(verwacht, "alleenstaandeouderenkorting", None))

        componenten = [c for c in componenten if c is not None]
        if not componenten:
            continue

        som_componenten = sum(componenten, Decimal("0"))
        if abs(totaal - som_componenten) > Decimal("0.01"):
            waarschuwingen.append(
                f"verwachte_belasting.totaal_kortingen_{suffix} is niet gelijk aan som kortingen"
            )

    return waarschuwingen


def _bepaal_vergelijkingsverwachting(testcase: TestCase) -> tuple[Decimal, str, list[str]]:
    """Bepaal welk verwacht totaal voor validatie gebruikt wordt."""
    verwacht = testcase.verwachte_belasting
    waarschuwingen = _controleer_consistentie_verwachte_belasting(testcase)

    if testcase.is_paar and verwacht.totaal_verschuldigd_p1 is not None and verwacht.totaal_verschuldigd_p2 is not None:
        som_persoon = verwacht.totaal_verschuldigd_p1 + verwacht.totaal_verschuldigd_p2
        if abs(verwacht.totaal_verschuldigd - som_persoon) > Decimal("5"):
            waarschuwingen.append(
                "huishoudtotaal is intern inconsistent; validatie vergelijkt op som per persoon"
            )
            return som_persoon, "som_per_persoon", waarschuwingen

    return verwacht.totaal_verschuldigd, "huishoudtotaal", waarschuwingen


def _pas_aow_bedrag_aan_voor_testcase(testcase: TestCase, config):
    """Gebruik testcase-specifieke AOW-bedragen i.p.v. generieke jaarconfig.

    Voor validatiecases uit de Belastingdienst simulator kunnen de AOW-bedragen
    afwijken van de standaardwaarden in `config/belasting_YYYY.json`.
    Deze helper overschrijft daarom tijdelijk de relevante maandbedragen.
    """
    aow_bedragen = [
        Decimal(p.bruto_aow)
        for p in testcase.personen
        if Decimal(p.bruto_aow) > Decimal("0")
    ]

    # Nieuwe SVB-referenties toetsen de echte maandcashflow, zonder invoeroverride.
    if testcase.testcase_id in {"tc_2025_018", "tc_2025_019"}:
        return config

    if not aow_bedragen:
        return config

    if testcase.is_paar:
        # Voor partnerhuishoudens gebruikt de engine het partner-AOW maandbedrag.
        # Neem het gemiddelde van de opgegeven jaarlijkse AOW-bedragen voor stabiliteit.
        jaarbedrag = sum(aow_bedragen) / Decimal(str(len(aow_bedragen)))
        maandbedrag = jaarbedrag / Decimal("12")
        nieuwe_aow_bedragen = replace(
            config.aow_bedrag,
            gehuwd_of_samenwonend_per_maand=maandbedrag,
            periodes=[],  # Historische fiscale proef met expliciete bruto broninvoer.
        )
    else:
        jaarbedrag = aow_bedragen[0]
        maandbedrag = jaarbedrag / Decimal("12")
        nieuwe_aow_bedragen = replace(
            config.aow_bedrag,
            alleenstaande_per_maand=maandbedrag,
            periodes=[],  # Geen vakantiegeld bovenop het opgegeven jaarbedrag.
        )

    return replace(config, aow_bedrag=nieuwe_aow_bedragen)


def bereken_belasting_testcase(testcase: TestCase) -> dict:
    """Bereken belasting voor testcase (1 jaar).
    
    Args:
        testcase: TestCase om te berekenen
        
    Returns:
        Centrale accountantdetailoutput van de engine.
    """
    # Genereer scenario
    personen, scenario = genereer_testcase_scenario(testcase)
    
    persoon1 = personen[0]
    persoon2 = personen[1] if len(personen) > 1 else None
    
    # Laad belastingtarieven
    config, aanname = laad_tarieven(testcase.jaar)
    config = _pas_aow_bedrag_aan_voor_testcase(testcase, config)
    
    # Geen pensioenrecords (allemaal via componenten)
    records1 = []
    records2 = []
    
    resultaat = bereken_accountant_jaar_detail(
        jaar=testcase.jaar,
        persoon1=persoon1,
        persoon2=persoon2,
        records1=records1,
        records2=records2,
        scenario=scenario,
        config=config,
        aanname=aanname,
    )
    
    return resultaat


def extract_totaal_verschuldigd(resultaat: dict, config, heeft_partner: bool) -> Decimal:
    """Extract totaal verschuldigd uit berekeningsresultaat.

    Gebruikt de al-correcte waarden uit _bereken_jaar_detail (die rekening houden
    met eigen woning grondslag-correctie, tariefsaanpassing en premies op gecorrigeerde grondslag).

    Args:
        resultaat: Dict van _bereken_jaar_detail
        config: BelastingConfig voor het jaar (niet meer gebruikt, behouden voor backward-compat)
        heeft_partner: Of huishouden een partner heeft (niet meer gebruikt)

    Returns:
        Totaal verschuldigd bedrag
    """
    netto_bel_p1 = resultaat.get("netto_bel_p1", Decimal("0"))
    netto_bel_p2 = resultaat.get("netto_bel_p2", Decimal("0"))
    box3_heffing = resultaat.get("box3_heffing", Decimal("0"))
    return netto_bel_p1 + netto_bel_p2 + box3_heffing


def valideer_testcase(testcase: TestCase, tolerantie: Decimal = Decimal("5")) -> dict:
    """Valideer testcase: bereken belasting en vergelijk met verwachte waarde.
    
    Args:
        testcase: TestCase om te valideren
        tolerantie: Maximaal toegestane afwijking in euros
        
    Returns:
        Dict met validatieresultaat:
        {
            "testcase_id": str,
            "verwacht": Decimal,
            "berekend": Decimal,
            "verschil": Decimal,
            "verschil_pct": Decimal,
            "pass": bool,
            "status": str,  # "PASS", "WARN", "FAIL"
            "details": dict,  # volledige berekeningsdetails
        }
    """
    # Laad config
    config, _ = laad_tarieven(testcase.jaar)
    
    # Bepaal of huishouden een partner heeft
    heeft_partner = testcase.is_paar
    
    # Bereken
    details = bereken_belasting_testcase(testcase)
    berekend = extract_totaal_verschuldigd(details, config, heeft_partner)
    
    # Verwacht (met interne-consistentie fallback)
    verwacht, verwacht_bron, data_waarschuwingen = _bepaal_vergelijkingsverwachting(testcase)
    
    # Verschil
    verschil = berekend - verwacht
    verschil_pct = (verschil / verwacht * 100) if verwacht > 0 else Decimal("0")
    
    # Status
    abs_verschil = abs(verschil)
    if abs_verschil <= tolerantie:
        status = "PASS"
        is_pass = True
    elif abs_verschil <= 50:
        status = "WARN"
        is_pass = False
    else:
        status = "FAIL"
        is_pass = False
    
    return {
        "testcase_id": testcase.testcase_id,
        "naam": testcase.naam,
        "jaar": testcase.jaar,
        "verwacht": verwacht,
        "berekend": berekend,
        "verschil": verschil,
        "verschil_pct": verschil_pct,
        "pass": is_pass,
        "status": status,
        "verwacht_bron": verwacht_bron,
        "data_waarschuwingen": data_waarschuwingen,
        "details": details,
    }
