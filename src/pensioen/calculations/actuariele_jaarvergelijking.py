"""Resultaten: presenteer jaarlijkse engine-uitvoer, zonder fiscale herberekening."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from pensioen.calculations.scenario_engine import ScenarioVergelijking
from pensioen.models.persoon import Persoon
from pensioen.tax.aow_engine import bereken_aow_datum


def bouw_actuariele_jaarvergelijking(
    vergelijking: ScenarioVergelijking, persoon: Persoon,
) -> dict[str, Any]:
    """Verschillen t.o.v. wachten zonder premie, alle bedragen per huishouden."""
    aow_datum = bereken_aow_datum(persoon.geboortedatum)
    basis = vergelijking.scenario_resultaten[1].cashflow.jaren
    varianten = []
    for index, resultaat in enumerate(vergelijking.scenario_resultaten):
        jaren = []
        for jaar, referentie in zip(resultaat.cashflow.jaren, basis):
            box1 = jaar.box1_belasting - jaar.totaal_heffingskorting
            belasting = box1 + jaar.box3_heffing
            belasting_basis = referentie.totaal_belasting - referentie.totaal_heffingskorting
            jaren.append({
                "jaar": jaar.jaar,
                "aow_fase": "Vóór AOW" if jaar.jaar < aow_datum.year else
                            "AOW-overgangsjaar" if jaar.jaar == aow_datum.year else "Na AOW",
                "bruto_inkomen": jaar.inkomen_bruto,
                "box1_na_kortingen": box1,
                "box3": jaar.box3_heffing,
                "belasting_totaal": belasting,
                "belastingverschil": belasting - belasting_basis,
                "belastingdruk": jaar.effectief_tarief,
                "belastingdrukverschil_pp": jaar.effectief_tarief - referentie.effectief_tarief,
                "netto_inkomen": jaar.netto_inkomen,
                "voortzettingspremie": jaar.huishoudelijke_uitgaven - referentie.huishoudelijke_uitgaven
                    if index == 2 else Decimal("0"),
                "over_na_uitgaven": jaar.netto,
                "vermogen": jaar.vermogen_einde_jaar,
                "netto_verschil": jaar.netto_inkomen - referentie.netto_inkomen,
            })
        varianten.append({"naam": resultaat.scenario_naam, "jaren": jaren})
    return {"referentie": vergelijking.scenario_resultaten[1].scenario_naam,
            "aow_datum": aow_datum, "persoon": persoon.naam, "varianten": varianten}
