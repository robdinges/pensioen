"""Test is_actief methode met einddatum."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pensioen.models.component import (
    BedragType,
    CategorieComponent,
    FinancieelComponent,
    Frequentie,
)


def test_component_actief_met_einddatum():
    """Test dat component actief is tot en met de einddatum."""
    comp = FinancieelComponent(
        omschrijving="Salaris",
        categorie=CategorieComponent.ARBEIDSINKOMEN,
        persoon="P1",
        bedrag_type=BedragType.BRUTO,
        bedrag=Decimal("4000"),
        frequentie=Frequentie.MAANDELIJKS,
        begindatum=date(2026, 1, 1),
        einddatum=date(2028, 12, 31),
    )
    
    # 2026 moet actief zijn
    assert comp.is_actief(2026, 1) is True, "Januari 2026 moet actief zijn"
    assert comp.is_actief(2026, 6) is True, "Juni 2026 moet actief zijn"
    assert comp.is_actief(2026, 12) is True, "December 2026 moet actief zijn"
    
    # 2027 moet actief zijn
    assert comp.is_actief(2027, 1) is True, "Januari 2027 moet actief zijn"
    assert comp.is_actief(2027, 12) is True, "December 2027 moet actief zijn"
    
    # 2028 moet actief zijn (tot en met december)
    assert comp.is_actief(2028, 1) is True, "Januari 2028 moet actief zijn"
    assert comp.is_actief(2028, 12) is True, "December 2028 moet actief zijn (einddatum)"
    
    # 2029 moet NIET actief zijn
    assert comp.is_actief(2029, 1) is False, "Januari 2029 mag NIET actief zijn"
    
    # Bedragen moeten ook correct zijn
    bedrag_2026_jan = comp.bedrag_per_maand_actief(2026, 1)
    assert bedrag_2026_jan == Decimal("4000"), f"Verwacht €4000, kreeg {bedrag_2026_jan}"
    
    bedrag_2029_jan = comp.bedrag_per_maand_actief(2029, 1)
    assert bedrag_2029_jan == Decimal("0"), f"Verwacht €0 in 2029, kreeg {bedrag_2029_jan}"
    
    print("✅ Alle tests slagen - is_actief werkt correct met einddatum")


if __name__ == "__main__":
    test_component_actief_met_einddatum()
