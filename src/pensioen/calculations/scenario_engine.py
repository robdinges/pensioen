"""Scenariovergelijking: vergelijk meerdere planningsscenario's naast elkaar."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from decimal import Decimal
from statistics import median

from pensioen.calculations.inheritance_engine import get_parent_chain, resolve_scenario
from pensioen.calculations.scenario_klantbeeld import bouw_klantbeeld, vergelijkingsperiode
from pensioen.calculations.resultaat_service import bereken_resultaten
from pensioen.models.cashflow import HuishoudCashflow
from pensioen.models.component import CategorieComponent
from pensioen.models.pensioen_record import PensioenRecord
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario


def _stopdatum_werk(scenario: Scenario) -> str:
    """Vroegste einddatum van ARBEIDSINKOMEN-P1 componenten, of 'onbepaald'."""
    stops = [
        c.einddatum for c in scenario.componenten
        if c.categorie == CategorieComponent.ARBEIDSINKOMEN
        and c.persoon == "P1"
        and c.einddatum is not None
    ]
    return str(min(stops)) if stops else "onbepaald"


def _leeftijd_op_datum(geboortedatum: date, datum: date | None) -> str | None:
    """Bepaal de leeftijd op een laatste werkdag."""
    if datum is None:
        return None
    jaren = datum.year - geboortedatum.year
    if (datum.month, datum.day) < (geboortedatum.month, geboortedatum.day):
        jaren -= 1
    maanden = (datum.year - (geboortedatum.year + jaren)) * 12 + datum.month - geboortedatum.month
    if datum.day < geboortedatum.day:
        maanden -= 1
    return f"{jaren}j {maanden} m"


@dataclass
class ScenarioResultaat:
    """Samenvatting van één scenario voor vergelijking."""

    scenario_naam: str
    stopdatum_werk: str
    netto_per_maand_mediaan: Decimal
    netto_laagste_jaar: Decimal
    laagste_inkomensjaar: int | None
    vermogen_op_70: Decimal
    vermogen_op_80: Decimal
    gemiddelde_belastingdruk: Decimal  # effectief tarief
    aantal_tekortjaren: int
    cashflow: HuishoudCashflow  # Moved before field with default
    klantbeeld: dict[str, Any] = field(default_factory=dict)
    parent_chain: list[str] = field(default_factory=list)  # inheritance chain


@dataclass
class ScenarioVergelijking:
    """Vergelijking van meerdere scenario's."""

    scenario_resultaten: list[ScenarioResultaat] = field(default_factory=list)
    klantvergelijking: dict[str, Any] = field(default_factory=dict)

    @property
    def beste_scenario_netto(self) -> ScenarioResultaat | None:
        """Scenario met het hoogste mediane netto maandinkomen."""
        if not self.scenario_resultaten:
            return None
        return max(self.scenario_resultaten, key=lambda s: s.netto_per_maand_mediaan)

    @property
    def scenario_namen(self) -> list[str]:
        return [s.scenario_naam for s in self.scenario_resultaten]


def _bereken_samenvatting(
    scenario: Scenario,
    cashflow: HuishoudCashflow,
    persoon1: Persoon,
    scenario_lijst: list[Scenario],
) -> ScenarioResultaat:
    """Bereken de samenvattingsstatistieken voor één scenario."""
    netto_per_maand_alle_jaren = [
        j.netto_per_maand for j in cashflow.jaren
    ]
    mediaan = Decimal(str(median(float(n) for n in netto_per_maand_alle_jaren)))

    laagste = cashflow.laagste_inkomensjaar
    laagste_jaar_netto = laagste.netto if laagste else Decimal("0")
    laagste_jaar_nr = laagste.jaar if laagste else None

    vermogen_70 = cashflow.vermogen_op_leeftijd(persoon1.geboortedatum, 70)
    vermogen_80 = cashflow.vermogen_op_leeftijd(persoon1.geboortedatum, 80)

    gemiddeld_tarief = (
        Decimal(
            str(
                sum(float(j.effectief_tarief) for j in cashflow.jaren)
                / len(cashflow.jaren)
            )
        )
        if cashflow.jaren
        else Decimal("0")
    )

    # Determine parent chain for inheritance tracking
    parent_chain = get_parent_chain(scenario, scenario_lijst)

    return ScenarioResultaat(
        scenario_naam=scenario.naam,
        stopdatum_werk=_stopdatum_werk(scenario),
        netto_per_maand_mediaan=mediaan,
        netto_laagste_jaar=laagste_jaar_netto,
        laagste_inkomensjaar=laagste_jaar_nr,
        vermogen_op_70=vermogen_70,
        vermogen_op_80=vermogen_80,
        gemiddelde_belastingdruk=gemiddeld_tarief,
        aantal_tekortjaren=len(cashflow.tekortjaren),
        parent_chain=parent_chain,
        cashflow=cashflow,
    )


def vergelijk_scenarios(
    scenarios: list[Scenario],
    persoon1: Persoon,
    persoon2: Persoon | None,
    records1: list[PensioenRecord],
    records2: list[PensioenRecord],
    jaar_van: int,
    jaar_tot: int,
) -> ScenarioVergelijking:
    """
    Bereken en vergelijk meerdere scenario's.

    Args:
        scenarios: Lijst van te vergelijken scenario's (max. 4 aanbevolen).
        persoon1: Eerste persoon.
        persoon2: Partner (of None).
        records1: Pensioenrecords persoon1.
        records2: Pensioenrecords persoon2.
        jaar_van: Eerste prognosejaar.
        jaar_tot: Laatste prognosejaar.

    Returns:
        ScenarioVergelijking met resultaten per scenario.
    """
    vergelijking = ScenarioVergelijking()

    for scenario in scenarios:
        cashflow = bereken_resultaten(
            scenario=scenario,
            persoon1=persoon1,
            persoon2=persoon2,
            records1=records1,
            records2=records2,
            jaar_van=jaar_van,
            jaar_tot=jaar_tot,
            scenario_lijst=scenarios,  # Pass full list for inheritance resolution
        )
        samenvatting = _bereken_samenvatting(scenario, cashflow, persoon1, scenarios)
        vergelijking.scenario_resultaten.append(samenvatting)

    opgeloste_scenarios = [resolve_scenario(s, scenarios) for s in scenarios]
    begin, einde, na_stoppen = vergelijkingsperiode(opgeloste_scenarios, jaar_van, jaar_tot)
    vergelijking.klantvergelijking = {
        "gemiddelde_van": begin, "gemiddelde_tot": einde,
        "na_stoppen": na_stoppen, "horizon_van": jaar_van, "horizon_tot": jaar_tot,
        "actief_scenario": scenarios[0].naam if scenarios else None,
    }
    for resultaat, opgelost in zip(vergelijking.scenario_resultaten, opgeloste_scenarios):
        resultaat.klantbeeld = bouw_klantbeeld(resultaat.cashflow, begin, einde, persoon1.geboortedatum)
        resultaat.klantbeeld["laatste_werkdagen"] = {}
        resultaat.klantbeeld["leeftijden_op_laatste_werkdag"] = {}
        for persoon in ("P1", "P2") if persoon2 else ("P1",):
            posten = [c for c in opgelost.componenten if c.categorie == CategorieComponent.ARBEIDSINKOMEN
                      and c.persoon == persoon and (c.bedrag > 0 or c.waarde_periodes)]
            geboortedatum = persoon1.geboortedatum if persoon == "P1" else persoon2.geboortedatum
            if posten:
                laatste_werkdag = max(c.einddatum for c in posten) if all(c.einddatum for c in posten) else None
                resultaat.klantbeeld["laatste_werkdagen"][persoon] = laatste_werkdag
                resultaat.klantbeeld["leeftijden_op_laatste_werkdag"][persoon] = _leeftijd_op_datum(
                    geboortedatum, laatste_werkdag
                )
    if vergelijking.scenario_resultaten:
        basis = vergelijking.scenario_resultaten[0].klantbeeld
        for resultaat in vergelijking.scenario_resultaten:
            beeld = resultaat.klantbeeld
            for veld in ("gemiddeld_over_per_maand", "vermogen_op_80"):
                beeld[f"verschil_{veld}"] = (
                    beeld[veld] - basis[veld] if beeld[veld] is not None and basis[veld] is not None else None
                )
    return vergelijking
