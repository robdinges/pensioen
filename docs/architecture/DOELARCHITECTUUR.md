# Doelarchitectuur pensioenplanner

## Besluit

React is de primaire gebruikersinterface. Streamlit blijft voorlopig beschikbaar
voor functioneel beheer en validatie. Beide consumeren dezelfde API- en
resultaatcontracten; Streamlit bevat geen zelfstandig rekenpad.

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
| React en Streamlit | presentatie en invoer, geen fiscale of cashflowformules |
| `reports/` | export van bestaande engine-output |

## Frontendstrategie

- React: primaire planner voor huishoudens, scenario's, import, berekening en rapportage.
- Streamlit: beheer- en validatiescherm zolang functionele beheertaken nog niet
  aantoonbaar in React zijn afgedekt.
- Verwijdering van Streamlit vereist pariteitstoets, sessiemigratie en expliciete
  productgoedkeuring.

## Compatibiliteit

Contract `1.0` blijft backward compatible. Nieuwe velden zijn additief.
Verwijderingen of semantische wijzigingen vereisen een nieuwe API-hoofdversie,
release-notitie en migratiepad.
