# Pensioen Project — Agent Instructions

## Project Overview
Professionele Nederlandse pensioenplanner: dag-nauwkeurige cashflowprognoses voor een huishouden op basis van pensioen, AOW, werkinkomen, spaargeld en incidentele cashflows.

- **Taal / Language**: Dutch voor domain-code, variabelenamen en comments; Engels voor infrastructure/tests
- **Domain**: Dutch pension rules (AOW, werkgeverspensioen, Box 1/3, heffingskortingen)
- **UI**: Streamlit (`streamlit run app.py`)

## Tech Stack
- **Python 3.12+** — type hints overal
- **Pydantic v2** — validatie van alle inputmodellen
- **Decimal** — alle geldbedragen (`from decimal import Decimal, ROUND_HALF_UP`)
- **pandas 2.2+** — DataFrames voor tabellen en exports
- **plotly 5.22+** — interactieve grafieken in de UI
- **openpyxl 3.1+** — Excel-rapporten
- **pdfplumber 0.11+** — PDF-parsing van MPO-exports
- **pytest 8.2+ / pytest-cov** — testframework

## Installatie & Gebruik

```bash
# Installeer (inclusief dev-dependencies)
pip install -e ".[dev]"

# Start de applicatie
streamlit run app.py

# Voer tests uit
pytest tests/

# Met coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Project Structuur

```
pensioen/
├── app.py                          # Streamlit entrypunt
├── pyproject.toml                  # Pakketdefinitie (build-backend: setuptools.build_meta)
├── config/
│   ├── belasting_YYYY.json         # Belastingtarieven per jaar
│   └── aow_leeftijden.json         # SVB AOW-leeftijdentabel
├── src/pensioen/
│   ├── models/                     # Pydantic inputmodellen + cashflow dataclasses
│   │   ├── persoon.py              # Persoon
│   │   ├── pensioen_record.py      # PensioenRecord + TypePensioen
│   │   ├── scenario.py             # Scenario + IncidenteelItem
│   │   └── cashflow.py             # MaandResultaat, JaarResultaat, HuishoudCashflow
│   ├── tax/                        # Belastingberekeningen
│   │   ├── belasting_loader.py     # laad_tarieven(jaar), laad_tarieven_bereik()
│   │   ├── aow_engine.py           # bereken_aow_datum(), aow_breuk_jaar()
│   │   ├── heffingskorting.py      # AHK, arbeidskorting, ouderenkorting
│   │   └── belasting_engine.py     # netto_uit_bruto(), bereken_box3_heffing()
│   ├── parsers/
│   │   └── parser_mpo.py           # MPOParser: CSV/Excel/PDF MijnPensioenoverzicht
│   ├── validators/
│   │   └── validator.py            # valideer_records() → ValidationResultaat
│   ├── calculations/
│   │   ├── pensioen_engine.py      # Pro-rata maandberekeningen (pensioen/AOW/arbeid)
│   │   ├── vermogen_engine.py      # Vermogensontwikkeling met maandrendement
│   │   ├── cashflow_engine.py      # bereken_huishouden() — hoofdengine
│   │   └── scenario_engine.py      # vergelijk_scenarios() — multi-scenario vergelijking
│   ├── reports/
│   │   └── rapport_engine.py       # genereer_rapport() → Excel bytes
│   └── ui/
│       ├── pagina_import.py         # Streamlit: MPO-import
│       ├── pagina_persoon.py        # Streamlit: persoonsgegevens
│       ├── pagina_scenario.py       # Streamlit: scenarioparameters
│       ├── pagina_resultaten.py     # Streamlit: grafieken + tabel
│       ├── pagina_instellingen.py   # Streamlit: tarieven inzien
│       └── pagina_rapport.py        # Streamlit: rapport downloaden
└── tests/
    ├── conftest.py                  # Gedeelde fixtures
    ├── fixtures/                    # CSV-testbestanden (mpo_partner1.csv, mpo_partner2.csv)
    └── test_*.py                    # 77 tests, 60% coverage
```

## Project Conventions

### Naamgeving (Naming)
- Dutch namen voor domeinconcepten: `pensioenleeftijd`, `netto_inkomen`, `opbouwpercentage`, `belasting_p1`
- snake_case voor alle identifiers
- Engels voor infrastructure-code (test fixtures, CI config)
- Geen hardgecodeerde belastingtarieven — altijd via `BelastingConfig` (uit JSON)

### Geldbedragen
- Altijd `Decimal`, nooit `float` voor opslag/berekening
- Afronden met `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`
- JSON-loading: `Decimal(str(float_waarde))` (niet `Decimal(float_waarde)` vanwege IEEE 754)

### Belastingconfiguratie
- JSON-bestanden: `config/belasting_YYYY.json`
- Fallback: als jaar niet bestaat → gebruik meest recente beschikbare jaar + toon waarschuwing
- Testbaar via `PENSIOEN_CONFIG_DIR` omgevingsvariabele

### Testing
- `pytest` via `python3 -m pytest tests/` vanuit projectroot
- Fixtures in `tests/conftest.py`
- `test_<module>.py` naamgeving
- `pytest.approx` vergelijkingen: altijd `float(Decimal_waarde)` wrappen

## Common Pitfalls
- **Duplicate file content**: Bij parallel `create_file` kan dubbele content ontstaan. Controleer `wc -l` en gebruik `head -N > tmp && mv tmp bestand` om af te kappen.
- **`from __future__ import annotations`** moet altijd op regel 1 staan (vóór alle andere imports behalve de module-docstring).
- **`setuptools.backends.legacy:build`** werkt niet op Python 3.14; gebruik `setuptools.build_meta` als build-backend in `pyproject.toml`.
- **`.pyc` cache**: Na bestandscorrecties `find . -type d -name __pycache__ -exec rm -rf {} +` uitvoeren.
- Dutch pension rules change yearly — parameterize year-dependent constants, don't hardcode
- AOW-leeftijd is niet vast; altijd ophalen via `aow_engine.bereken_aow_datum()` en `config/aow_leeftijden.json`
- Box 3: grote disclaimers meesturen; wetgeving is nog in beweging (rechtbankvonnissen Hoge Raad)

