# Pensioen Project — Agent Instructions

<!-- markdownlint-disable MD007 MD012 MD022 MD032 MD040 -->

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
│   │   ├── component.py            # FinancieelComponent + BeleggingsType (sparen/beleggen)
│   │   ├── scenario.py             # Scenario + IncidenteelItem; rendement_sparen_pct + rendement_beleggen_pct
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
│   │   ├── vermogen_engine.py      # Vermogensontwikkeling met maandrendement; ondersteunt sparen/beleggen split
│   │   ├── cashflow_engine.py      # bereken_huishouden() — hoofdengine; doet rendement_sparen/beleggen door
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

### Veilige Git-werkwijze voor Codex
- Lees voor iedere wijziging eerst de bestaande architectuur, `AGENTS.md`, de relevante `.github`-instructies en de betrokken bestanden.
- Werk voor iedere Codex-opdracht op een aparte branch met de naam `codex/<korte-beschrijving>`; wijzig nooit rechtstreeks `main`.
- Controleer voor iedere wijziging de actieve branch en `git status`. Leg bestaande wijzigingen duidelijk vast en overschrijf ze niet.
- Werk `main` alleen bij wanneer de werkmap schoon is en dit veilig kan. Voer geen `pull` uit zonder uitdrukkelijke toestemming.
- Maak nooit automatisch een commit, push, merge of pull request. Doe dit uitsluitend na uitdrukkelijke toestemming.
- Gebruik geen destructieve Git-commando's, waaronder `git reset --hard`, `git clean -fd`, force-push of het verwijderen van branches, tenzij daar expliciet opdracht voor is gegeven.

### Wijzigingsdiscipline
- Houd bestaande API-contracten en gegevensmodellen intact, tenzij de opdracht expliciet vraagt deze te wijzigen.
- Voer alleen wijzigingen uit die noodzakelijk zijn voor de gegeven opdracht en vermijd ongerelateerde refactoring.
- Pas dependencies niet aan zonder dit vooraf te melden.
- Voeg waar relevant tests toe of pas bestaande tests aan.
- Voer na wijzigingen de relevante tests, linters en typecontroles uit en meld duidelijk welke controles niet uitgevoerd konden worden.
- Toon na iedere opdracht de gewijzigde bestanden, een samenvatting van de wijzigingen, testresultaten, eventuele risico's en de relevante `git diff`.
- Commit, push en merge uitsluitend na uitdrukkelijke toestemming.

### Calculation Ownership (Single Source Of Truth)
- `src/pensioen/calculations/cashflow_engine.py` orkestreert maand/jaar-flow en roept fiscale modules aan.
- `src/pensioen/tax/belasting_engine.py` bevat box 1/box 3/premie-kernberekeningen.
- `src/pensioen/tax/heffingskorting.py` bevat alle heffingskortingformules.
- `src/pensioen/tax/eigen_woning_engine.py` bevat eigen-woninglogica en tariefsaanpassing.
- `src/pensioen/tax/aow_engine.py` bevat AOW-datum en AOW-breukregels.
- UI, API-serialisatie en exports presenteren resultaten maar bevatten geen fiscale herberekeningen.

### Functional Calculation Governance
- Behandel wijzigingen aan berekeningen eerst als wijzigingen in de **functionele berekenarchitectuur**, niet als losse code-edits.
- Map iedere wijziging eerst op precies één functionele stap uit de keten: `Scenario -> Persoonsgegevens -> Pensioen -> AOW -> Arbeid -> Bruto inkomen -> Eigen woning -> Box 1 -> Heffingskortingen -> Netto inkomen -> Box 3 -> Vermogen -> Resultaten`.
- Leg per wijziging expliciet vast: source of truth, invoer, uitvoer, gebruikte tarieven, gebruikte tests en afhankelijke vervolgstappen.
- Als een taak niet eenduidig op één berekenstap past, is de taak nog niet scherp genoeg en moet eerst het contract worden verduidelijkt.
- Nieuwe of aangepaste UI-, API- of rapportagelogica mag geen zelfstandige fiscale herberekening introduceren.
- Accountantoutput moet uiteindelijk volledig uit engine-output worden opgebouwd; tijdelijke afwijkingen moeten expliciet als migratieschuld benoemd blijven.
- Gebruik de documenten `MASTERPLAN_PENSIOENAPPLICATIE.md`, `UITVOERINGSPLAN_HERSTRUCTURERING.md` en `EPIC1_WERKPAKKET_FISCALE_BOUWSTENEN.md` als leidraad voor calculation-affecting werk.

### Delivery Discipline For Calculation Work
- Werk bij calculation-affecting changes in kleine slices per bouwsteen of berekenstap, niet in brede refactors over meerdere domeinstappen tegelijk.
- Voeg of wijzig eerst directe tests voor de betrokken bouwsteen voordat bredere engine- of UI-aanpassingen worden gedaan, tenzij de taak expliciet alleen analyse/documentatie is.
- Verwijder geen legacy bron of parallel rekenpad voordat de nieuwe source of truth aantoonbaar dezelfde functionele uitkomst levert en regressietests aanwezig zijn.
- Bij fiscale bugs moet het eindresultaat van de fix minimaal opleveren: één herleidbare oorzaak, één directe test op de betrokken bouwsteen en één regressietest op het hogere pad dat de bug zichtbaar maakte.

### Definition Of Done (Rekenwijzigingen)
- Elke wijziging aan berekeningen bevat minimaal:
    - testcase-update in `tests/fixtures/belasting_testcases/raw/`
    - regeneratie van `tests/fixtures/belasting_testcases/normalized/`
    - regressietest of validatierapport-update in `tests/` of `tests/fixtures/belasting_testcases/`
- Geen feature is functioneel gereed zonder bijgewerkte testartefacten en expliciete borging van regels in instructies waar nodig.
- Geen calculation-affecting wijziging is gereed zonder expliciete koppeling aan één functionele berekenstap en bevestiging van de source of truth voor die stap.
- Geen wijziging aan accountant-, rapportage- of resultaatweergave is gereed als die een eigen fiscale herberekening toevoegt of in stand houdt zonder expliciete migratiereden.

### Interne Verslaglegging En Tokens
- Houd interne verslaglegging compact en taakgericht; geen uitgebreide recaps tenzij expliciet gevraagd.
- Voeg alleen documentatie/rapportage-artefacten toe als deze functioneel nodig zijn voor beheer, validatie of compliance.
- Geef bij voortgang alleen delta-informatie (wat is veranderd sinds vorige update).

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
