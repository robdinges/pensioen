# Testmatrix functionele berekenstappen

Laatste inventarisatie: 26 juli 2026.

De primaire stap is de eigenaar van de regel. De testlaag bepaalt de
pytest-marker; een module kan daarnaast een hoger contract- of presentatiepad
afdekken.

| Testmodule | Primaire stap | Laag/marker | Hoger pad |
| --- | --- | --- | --- |
| `test_aow_engine.py` | AOW | `bouwsteen` | Box 1 |
| `test_api_main.py` | Resultaten | `contract` | API |
| `test_api_regressie_normalized.py` | Resultaten | `contract`, `referentie` | API en externe cases |
| `test_audit.py` | Scenario | `bouwsteen` | Governance |
| `test_belasting_engine.py` | Box 1/Box 3 | `bouwsteen` | Netto inkomen |
| `test_cashflow_engine.py` | Resultaten | `engine` | Volledige keten |
| `test_eigen_woning_engine.py` | Eigen woning | `bouwsteen` | Box 1 |
| `test_epic4_detailoutput.py` | Resultaten | `engine`, `contract` | Accountant en rapport |
| `test_epic5_consumptiecontract.py` | Resultaten | `contract`, `presentatie` | UI/API |
| `test_fiscale_bouwstenen.py` | Heffingskortingen | `bouwsteen` | Box 1 |
| `test_grafiek_consistency.py` | Resultaten | `engine`, `presentatie` | Grafieken/accountant |
| `test_grafiek_validator.py` | Resultaten | `presentatie` | Grafieken |
| `test_inheritance_engine.py` | Scenario | `engine` | API |
| `test_parser_mpo.py` | Pensioen | `bouwsteen`, `contract` | Import |
| `test_pensioen_engine.py` | Pensioen | `bouwsteen` | Bruto inkomen |
| `test_periodieke_waarde.py` | Scenario | `bouwsteen` | Inkomenscomponenten |
| `test_referentie_governance.py` | Resultaten | `referentie` | Externe cases |
| `test_regression_bugs.py` | Resultaten | `engine`, `referentie` | Volledige keten |
| `test_rendement_split.py` | Vermogen | `engine` | Resultaten |
| `test_scenario_engine.py` | Scenario | `engine` | Resultaten |
| `test_vermogen_engine.py` | Vermogen | `engine` | Box 3/resultaten |
| `test_vermogensitem.py` | Vermogen | `bouwsteen` | Scenario |

## Verplichte scenario’s

| Scenario | Primaire dekking |
| --- | --- |
| Alleenstaand werkend | `test_cashflow_engine.py`, `tc_2025_006/007` |
| Alleenstaand AOW/pensioen | `test_cashflow_engine.py`, `tc_2025_008` |
| Partners met verschillende AOW-status | `tc_2025_010` |
| Eigen woning met/zonder aftrek | `test_eigen_woning_engine.py`, `tc_2025_006/007` |
| Box 3 onder/boven vrijstelling | `test_belasting_engine.py`, `test_cashflow_engine.py` |
| Gemengd sparen/beleggen | `test_rendement_split.py` |
| Incidentele ontvangst/uitgave | `test_cashflow_engine.py` |
| Meerjarige vermogensdoorloop | `test_epic4_detailoutput.py`, `test_vermogen_engine.py` |
| Tarieffallback/periodeoverride | `test_belasting_engine.py`, `test_cashflow_engine.py` |

## Bekende dekkingsgaten

1. Streamlitpagina’s hebben grotendeels geen directe UI-tests.
2. React heeft een productiebuildpoort, maar nog geen component- of
   end-to-end-tests.
3. De externe IB-2025-set bevat zes handmatig getranscribeerde cases en is nog
   geen volledige fiscale waarheidstabel.
4. AOW-bronbedragen voor fiscaal partnerschap vereisen productvalidatie.
5. Typecontrole is nog geen verplichte CI-poort.

Integratiedekking mag deze gaten niet als directe bouwsteendekking presenteren.
