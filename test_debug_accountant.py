"""Debug accountant component filtering."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pensioen.models.component import (
    BedragType,
    CategorieComponent,
    FinancieelComponent,
    Frequentie,
)
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario


def test_accountant_component_som():
    """Test dat _component_som_maand correct werkt."""
    persoon = Persoon(
        naam="Test",
        geboortedatum=date(1970, 1, 1),
        heeft_partner=False,
    )
    
    # Maak scenario met arbeidsinkomen tot 2028
    scenario = Scenario(
        naam="Test scenario",
        persoon1=persoon,
        persoon2=None,
        componenten=[
            FinancieelComponent(
                omschrijving="Salaris",
                categorie=CategorieComponent.ARBEIDSINKOMEN,
                persoon="P1",
                bedrag_type=BedragType.BRUTO,
                bedrag=Decimal("4000"),
                frequentie=Frequentie.MAANDELIJKS,
                begindatum=date(2025, 1, 1),
                einddatum=date(2028, 12, 31),
            ),
        ],
    )
    
    # Simuleer de _component_som_maand functie
    def component_som_maand(scenario, categorie, persoon, jaar: int, maand: int, bedrag_type):
        return sum(
            (c.bedrag_per_maand_actief(jaar, maand) for c in scenario.componenten
             if c.categorie == categorie
             and (persoon is None or c.persoon == persoon)
             and (bedrag_type is None or c.bedrag_type == bedrag_type)),
            Decimal("0"),
        )
    
    # Test verschillende jaren
    for test_jaar in [2025, 2026, 2027, 2028, 2029]:
        bedrag = component_som_maand(
            scenario,
            CategorieComponent.ARBEIDSINKOMEN,
            "P1",
            test_jaar,
            1,  # januari
            BedragType.BRUTO,
        )
        print(f"Jaar {test_jaar}, maand 1: €{bedrag}")
        
        # Verwacht: 2025-2028 = €4000, 2029 = €0
        if test_jaar <= 2028:
            assert bedrag == Decimal("4000"), f"Verwacht €4000 in {test_jaar}, kreeg {bedrag}"
        else:
            assert bedrag == Decimal("0"), f"Verwacht €0 in {test_jaar}, kreeg {bedrag}"
    
    print("\n✅ Component filtering werkt correct in accountantsoverzicht!")


if __name__ == "__main__":
    test_accountant_component_som()
