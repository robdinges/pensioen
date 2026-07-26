# Epic 7 legacyregister

Status: actief besluitregister, bijgewerkt 26 juli 2026.

| Kandidaat | Callers/bewijs | Source of truth | Besluit | Verwijdercriterium |
| --- | --- | --- | --- | --- |
| `Scenario.spaargeld_start` en `beleggingen_start` | API-requests, sessies, fixtures, inheritance en beide frontends | `Scenario.vermogensitems` | Behouden als gedocumenteerde inputcompatibiliteit | API v2 plus sessiemigratie en gelijkheidstests |
| `Scenario.eigen_woning` | Streamlit-invoer, testcasegenerator en oude sessies | woning- en hypotheekitems in `vermogensitems` | Behouden als fallback | alle opgeslagen scenario's gemigreerd en API v2 |
| `PensioenRecord` als rekenbron | API-schema en importtests; hoofdengine meldt expliciet dat componenten leidend zijn | `Scenario.componenten` met `PENSIOEN_INKOMEN` | Behouden als import-/compatibiliteits-DTO, niet als rekenpad | apart importcontract zonder records in berekenrequest |
| `_bereken_jaar_detail()` | uitsluitend regressietests en Streamlit-module | `jaar.accountant_detail` uit resultaatservice | Verwijderd in Epic 7 | voldaan |
| directe scenariovergelijking via `bereken_huishouden` | `scenario_engine.py` | `bereken_resultaten()` | Verwijderd in Epic 7 | voldaan |
| detailopbouw in Streamlit | `pagina_accountant.py` | `resultaat_service` + `detail_output_engine` | Verwijderd in Epic 7 | voldaan |
| `bereken_accountant_jaar_detail()` | alleen directe regressietests; geen runtimecaller | volledig resultaat via `bereken_resultaten()` | Tijdelijk behouden als testcompatibiliteitshelper | regressietests migreren naar resultaatservice en externe callercheck bij API v2 |
| `update_vermogensitems_waarde()` | alleen directe unit-tests, geen runtimecaller | maandelijkse vermogensreeks in `cashflow_engine.py` | Behouden als interne kandidaat tot API-breaking akkoord | verwijderen na externe-compatibiliteitsbesluit |

Elke toekomstige verwijdering vereist opnieuw calleronderzoek in Python, React,
API-schema's, fixtures en sessieopslag. Een groen unit-testbestand alleen is geen
bewijs dat opgeslagen gebruikersdata migreerbaar is.
