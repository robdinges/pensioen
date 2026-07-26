# Validatie-index

Laatste volledige lokale uitvoering: 26 juli 2026.

| Onderdeel | Bewijs | Status |
| --- | --- | --- |
| Testclassificatie | `TESTMATRIX_BEREKENSTAPPEN.md` | gereed |
| Bouwstenen en contracten | `pytest -m "bouwsteen or contract"` | groen |
| Volledige Python-suite | `pytest tests/` | groen met 2 geregistreerde xfails |
| Raw/normalized lifecycle | `normalize_testcases.py --check` | groen |
| Externe IB-2025-referentie | `validatie_rapport_ib2025.md` | 2 WARN, 4 FAIL |
| Bekende afwijkingen | `bekende_afwijkingen.json`, `AFWIJKINGENREGISTER.md` | geregistreerd |
| Resultaat/detailconsistentie | `test_epic4_detailoutput.py` | blokkerende test |
| API/presentatiecontract | `test_api_main.py`, `test_epic5_consumptiecontract.py` | blokkerende tests |
| React | `npm run build` | groen |

## Bronnen per functionele stap

| Stap | Source of truth | Tarief-/databron | Primaire tests |
| --- | --- | --- | --- |
| Scenario | Pydantic-modellen en inheritance-engine | gebruikersinvoer | scenario-, periode- en persistentietests |
| Persoonsgegevens | `Persoon` | gebruikersinvoer | model- en cashflowtests |
| Pensioen | `Scenario.componenten` na MPO-transformatie | MPO/import | parser- en pensioenenginetests |
| AOW | `aow_engine.py` | `config/aow_leeftijden.json`, belastingconfig | AOW-tests |
| Arbeid/bruto | `cashflow_engine.py` | scenario-componenten | cashflowtests |
| Eigen woning | `eigen_woning_engine.py` | belastingconfig | eigen-woningtests |
| Box 1 | `belasting_engine.py` | `config/belasting_YYYY.json` | belasting- en bouwsteentests |
| Heffingskortingen | `heffingskorting.py` | belastingconfig | fiscale bouwsteentests |
| Box 3 | `belasting_engine.py` | belastingconfig en peildatumvermogen | belasting- en cashflowtests |
| Vermogen | `vermogen_engine.py` | scenario/vermogensitems | vermogen- en rendementtests |
| Resultaten | engine-output | alle voorgaande stappen | detail-, API- en referentietests |

## Open besluit

Epic 7 krijgt pas een definitieve go/no-go nadat de producteigenaar de drie
bron- en tolerantievragen uit het afwijkingenregister heeft beantwoord.
