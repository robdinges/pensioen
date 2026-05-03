# Pensioen Project — Agent Instructions

## Project Overview
Personal retirement calculator and planner written in Python.
- **Taal / Language**: Dutch voor code, comments en variabelenamen
- **Domain**: Dutch pension rules (AOW, werkgeverspensioen, eigen inleg)

## Tech Stack
- Python 3.x
- `pandas` / `numpy` for calculations and projections
- `pytest` for testing

## Project Conventions

### Naamgeving (Naming)
- Use Dutch names for domain concepts: `pensioenleeftijd`, `netto_inkomen`, `opbouwpercentage`
- Use snake_case for all identifiers
- Use English for infrastructure code (test fixtures, CI config)

### Structure (to be established)
```
pensioen/
├── src/
│   └── pensioen/       # main package
├── tests/              # pytest tests
├── data/               # input CSVs or JSON files
└── notebooks/          # exploratory Jupyter notebooks (optional)
```

### Testing
- Use `pytest`; run with `pytest` from project root
- Place tests in `tests/` following `test_<module>.py` naming
- Use `pytest` fixtures for shared setup (e.g. sample pension data)

### Calculations
- Monetary values: use `Decimal` or `float` with explicit rounding; document unit (€, %)
- Years/ages: use `int`; validate ranges at boundaries (e.g. `18 <= leeftijd <= 100`)
- Avoid magic numbers; define constants at module level (e.g. `AOW_LEEFTIJD = 67`)

## Common Pitfalls
- Dutch pension rules change yearly — parameterize year-dependent constants, don't hardcode
- AOW-leeftijd is not fixed; retrieve from configuration or constants file
