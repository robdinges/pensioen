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
- Gebruik `round(waarde, 2)` voor geldbedragen (€)
- Documenteer eenheden in de docstring: `"""Geeft jaarlijks pensioen terug in euro's."""`
- Valideer invoer aan de grenzen: `assert 18 <= leeftijd <= 100`

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
