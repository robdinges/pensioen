# Doelarchitectuur pensioenplanner

## Besluit

React is de enige gebruikersinterface van de pensioenplanner. Alle presentatie-
en invoerschermen communiceren met de backend via de FastAPI-endpoints.
Streamlit is volledig uit de codebase verwijderd.

Dit frontendbesluit en het compatibiliteitsbeleid zijn door de producteigenaar
goedgekeurd op 26 juli 2026.

## Berekenketen

`Scenario → Persoonsgegevens → Pensioen → AOW → Arbeid → Bruto inkomen → Eigen
woning → Box 1 → Heffingskortingen → Netto inkomen → Box 3 → Vermogen →
Resultaten`

| Laag | Eigenaarschap |
| --- | --- |
| `tax/` | fiscale formules en jaarconfiguratie |
| `calculations/cashflow_engine.py` | interne maand-/jaarorkestratie |
| `calculations/resultaat_service.py` | enige publieke ingang voor volledige resultaten en tariefvoorbereiding |
| `calculations/detail_output_engine.py` | centrale afleiding van jaar- en accountantoutput |
| `models/output_contract.py` | versie en typed publieke resultaatcontracten |
| `api/` | inputvalidatie en serialisatie, geen herberekening |
| React | presentatie en invoer, geen fiscale of cashflowformules |
| `reports/` | export van bestaande engine-output |

## Frontendstrategie

- React: enige planner voor huishoudens, scenario's, import, berekening en rapportage.
- Streamlit: volledig uitgeschakeld en verwijderd.

## Compatibiliteit

Contract `1.0` blijft backward compatible. Nieuwe velden zijn additief.
Verwijderingen of semantische wijzigingen vereisen een nieuwe API-hoofdversie,
release-notitie en migratiepad.
