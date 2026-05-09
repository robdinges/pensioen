"""Scenariovergelijking: vergelijk meerdere planningsscenario's naast elkaar."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from statistics import median

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.models.cashflow import HuishoudCashflow
from pensioen.models.component import CategorieComponent
from pensioen.models.pensioen_record import PensioenRecord
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.tax.belasting_loader import BelastingConfig, laad_tarieven_bereik


def _stopdatum_werk(scenario: Scenario) -> str:
    """Vroegste einddatum van ARBEIDSINKOMEN-P1 componenten, of 'onbepaald'."""
    stops = [
        c.einddatum for c in scenario.componenten
        if c.categorie == CategorieComponent.ARBEIDSINKOMEN
        and c.persoon == "P1"
        and c.einddatum is not None
    ]
    return str(min(stops)) if stops else "onbepaald"


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
    cashflow: HuishoudCashflow = field(repr=False)


@dataclass
class ScenarioVergelijking:
    """Vergelijking van meerdere scenario's."""

    scenario_resultaten: list[ScenarioResultaat] = field(default_factory=list)

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
    cashflow: HuishoudCashflow,
    persoon1: Persoon,
    scenario: Scenario,
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
    belasting_configs = laad_tarieven_bereik(jaar_van, jaar_tot)
    vergelijking = ScenarioVergelijking()

    for scenario in scenarios:
        cashflow = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon1,
            persoon2=persoon2,
            records1=records1,
            records2=records2,
            jaar_van=jaar_van,
            jaar_tot=jaar_tot,
            belasting_configs=belasting_configs,
        )
        samenvatting = _bereken_samenvatting(cashflow, persoon1, scenario)
        vergelijking.scenario_resultaten.append(samenvatting)

    return vergelijking
