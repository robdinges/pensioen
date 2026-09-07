---
description: Python code conventions for this pension project (Dutch naming, pandas, pytest)
applyTo: "**/*.py"
---

# Python Conventions — Pensioen Project

## Taal
- Gebruik **Nederlands** voor alle domeinconcepten: variabelen, functies, klassen, docstrings
- Voorbeelden: `bereken_netto_pensioen()`, `opbouwjaren`, `pensioenkapitaal`

## Constanten
Definieer jaar-afhankelijke constanten in één bestand (bijv. `src/pensioen/constanten.py`):
```python
AOW_LEEFTIJD = 67          # leeftijd in jaren
MAX_OPBOUWPERCENTAGE = 0.0175
BELASTINGSCHIJF_1 = 0.3693
```

## Berekeningen
- Gebruik `Decimal` en rond af met `quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`
- Documenteer eenheden in de docstring: `"""Geeft jaarlijks pensioen terug in euro's."""`
- Valideer invoer aan de grenzen: `assert 18 <= leeftijd <= 100`

## Berekeningen - Eigenaarschap
- Plaats fiscale formules uitsluitend in tax-modules onder `src/pensioen/tax/`.
- Houd `src/pensioen/calculations/` beperkt tot orkestratie en aggregatie.
- Voeg geen fiscale herberekeningen toe in UI-, report- of API-serialisatielagen.

## Afrondingsregels Belastingdienst (IB 2025)
- Voer interne berekeningen uit met volledige precisie; geen tussentijdse afronding in formules
- Rond pas af op logische eindniveaus per belastingplichtige (niet op huishoudniveau)
- Rond componenten per persoon af nadat de volledige formule klaar is:
  - box 1 belasting vóór kortingen
  - premies volksverzekeringen
  - heffingskortingen (AHK, ouderenkorting, overige kortingen)
- Tel daarna pas de afgeronde componenten per persoon op tot eindbelasting
- Rond nooit af op inkomens- of grondslagniveau
- Box 3: bereken grondslag en fictief rendement volledig door; rond alleen de eindheffing af

## Uitzondering voor fiscale aanslagafronding 2025

Bij `afronding_aanslag=true` in de jaarconfig geldt de live OLA-bevestigde
afronding: IB per schijf omlaag, premietotaal uit ongeronde premies omlaag,
volledig berekende heffingskortingen omhoog op hele euro's. Geen afronding van
percentages of tussenstappen binnen een schijf/korting. De afgeronde bedragen
blijven Decimal. Centenafronding blijft gelden voor cashflow en maandverdeling.
De fiscale modules bezitten deze regels; zie `docs/OLA_VALIDATIE_2025.md`.

## pandas / numpy
- Geef kolommen Nederlandse namen: `df["bruto_salaris"]`, `df["opbouwjaren"]`
- Gebruik `dtype=float` expliciet voor numerieke kolommen
- Vermijd itereren over DataFrames; gebruik vectorized operaties

## Tests (pytest)
- Elke berekeningsfunctie heeft minstens één happy-path test en één edge-case test
- Gebruik `pytest.approx` voor floating-point vergelijkingen:
  ```python
  assert bereken_pensioen(40000, 35) == pytest.approx(14000.0, rel=1e-3)
  ```
- Testbestandsnamen volgen `test_<modulenaam>.py`
- Elke nieuwe of aangepaste berekenregel vereist:
  - update van testcasebron in `tests/fixtures/belasting_testcases/raw/`
  - regeneratie van `tests/fixtures/belasting_testcases/normalized/`
  - minimaal één regressietest of fixture-validatie-update
