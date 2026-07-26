---
archived: true
post_title: "Epic 5 Issues Backlog"
author1: "GitHub Copilot"
post_slug: "epic-5-issues-backlog"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "epic-5"
  - "backlog"
  - "issues"
ai_note: "AI-assisted backlog structuring based on the approved Epic 5 work package; no application code was modified."
summary: "Concrete issue-level backlog for Epic 5 with small implementation slices, dependencies, and acceptance criteria for UI/API decoupling and pure engine-output consumption."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel

Deze backlog vertaalt Epic 5 naar kleine, uitvoerbare issues.

## Implementatiestatus 2026-07-26

Status: **issues 1-14 geïmplementeerd; functionele UI-validatie open**.

Consumptiecontract:

| Pad | Toegestane bron | Presentatie-afleiding |
| --- | --- | --- |
| Streamlit resultaten | `JaarResultaat.jaar_samenvatting` en expliciete enginevelden | formattering, grafiekvorm en koopkrachtlabel |
| Streamlit accountant | `JaarResultaat.accountant_detail` | formattering en zichtbaarheid van nulregels |
| Streamlit/Excel rapport | `HuishoudCashflow`, `jaar_samenvatting`, `accountant_detail` | werkblad- en kolomopmaak |
| React resultaten | `cashflow.jaren[].jaar_samenvatting` | formattering en niet-fiscale KPI-statistiek |
| React accountant | `cashflow.jaren[].accountant_detail` | formattering en tabelgroepering |
| `app_api_client.py` | `cashflow.jaren[].jaar_samenvatting` | DataFrame- en grafiekopmaak |

Technische borging:

- API-response bevat outputcontract versie `1.0`.
- React en de API-client accepteren geen ontbrekende centrale jaarsamenvatting.
- De maand-naar-jaar fiscale fallbacks zijn verwijderd.
- `resultaat_service.py` is de gedeelde voorbereidingslaag voor Streamlit en API.
- Tariefconfiguratie en tariefbronnen worden centraal eenmaal voorbereid.
- Presentatiecontract- en enginegelijkheidstests bewaken regressie.
- De bestaande IB-2025-validatiestatus blijft afzonderlijk zichtbaar en wordt
  niet in deze presentatiemigratie gerebaselined.

Epic 5 draait om één hoofdvraag:

```text
Hoe maken we van Streamlit, React, API en API-client pure consumenten van engine-output?
```

## Volgorde

De aanbevolen uitvoervolgorde is:

1. consumptiecontracten per presentatiepad vastleggen
2. Streamlit hoofdpad opschonen
3. React en API-client herleiding minimaliseren
4. API- en tariefvoorbereiding harmoniseren
5. contract- en regressiebewaking toevoegen

## Epic 5-A — Consumptiecontracten per pad

### Issue 1

Titel:

`Leg consumptiecontract vast voor Streamlit resultaten, accountant en rapport`

Scope:

- bepaal per Streamlit-scherm welke engine-output gelezen mag worden

Acceptatiecriteria:

- voor elk Streamlit-presentatiepad is de toegestane outputbron expliciet

### Issue 2

Titel:

`Leg consumptiecontract vast voor React resultaten, accountant en plannerCore`

Scope:

- bepaal welke API-output React direct mag consumeren
- markeer welke client-afleidingen tijdelijk zijn en welke niet meer mogen

Acceptatiecriteria:

- voor elk React-presentatiepad is de toegestane outputbron expliciet

### Issue 3

Titel:

`Leg consumptiecontract vast voor app_api_client`

Scope:

- bepaal welke outputvelden nog client-side geïnterpreteerd mogen worden en welke
  via engine-output expliciet geleverd moeten worden

Acceptatiecriteria:

- `app_api_client.py` heeft een expliciet consumptiecontract

## Epic 5-B — Streamlit hoofdpad opschonen

### Issue 4

Titel:

`Beperk app.py tot orchestration en statebeheer`

Scope:

- verwijder of markeer logica die meer doet dan orchestration, state en
  doorroep naar engine

Betrokken bestanden:

- `app.py`

Acceptatiecriteria:

- `app.py` bevat geen zelfstandige fiscale interpretatielaag meer

### Issue 5

Titel:

`Minimaliseer resultaat-afleiding in Streamlit resultatenpagina`

Scope:

- zorg dat `pagina_resultaten.py` engine-output presenteert en geen eigen
  inhoudelijke herleiding toevoegt die beter in de engine thuishoort

Betrokken bestanden:

- `src/pensioen/ui/pagina_resultaten.py`

Acceptatiecriteria:

- resultaatpagina voegt geen zelfstandige fiscale logica toe

### Issue 6

Titel:

`Minimaliseer rapportafleiding buiten de engine`

Scope:

- controleer of rapportage alleen engine- en detailoutput consumeert

Betrokken bestanden:

- `src/pensioen/ui/pagina_rapport.py`
- `src/pensioen/reports/rapport_engine.py`

Acceptatiecriteria:

- rapportpad reconstrueert geen fiscale waarheid buiten de engine

## Epic 5-C — React en API-client herleiding minimaliseren

### Issue 7

Titel:

`Beoordeel en reduceer client-side jaaraggregatie in plannerCore`

Scope:

- evalueer `aggregateYearRows()`
- verplaats waar wenselijk jaarsamenvatting naar engine-output of maak de
  client-afleiding expliciet tijdelijk

Betrokken bestanden:

- `frontend-react/src/planner/plannerCore.js`
- `frontend-react/src/components/ResultsSection.jsx`

Acceptatiecriteria:

- client-side jaaraggregatie is minimaal of expliciet contractueel verantwoord

### Issue 8

Titel:

`Beoordeel en reduceer accountant-interpretatie in React`

Scope:

- zorg dat React-accountantweergave vooral detailoutput leest, niet zelf
  betekenis toevoegt aan fiscale velden

Betrokken bestanden:

- `frontend-react/src/components/AccountantSection.jsx`

Acceptatiecriteria:

- React-accountantpad is een presentatiepad en geen impliciete rekenschil

### Issue 9

Titel:

`Beoordeel en reduceer netto-herleiding in app_api_client`

Scope:

- evalueer `_bereken_maand_netto()`
- verplaats waar mogelijk benodigde output naar de engine of markeer het pad als
  tijdelijke compatibiliteitslaag

Betrokken bestanden:

- `app_api_client.py`

Acceptatiecriteria:

- API-client reconstrueert geen vermijdbare fiscale logica client-side

## Epic 5-D — API- en voorbereidingslogica harmoniseren

### Issue 10

Titel:

`Inventariseer dubbele tarief- en requestvoorbereiding tussen app.py en API`

Scope:

- vergelijk `app.py`, `api/main.py` en `api/schemas.py`

Acceptatiecriteria:

- de dubbele voorbereidingslogica is expliciet geïnventariseerd

### Issue 11

Titel:

`Harmoniseer voorbereidingslogica waar inhoudelijke duplicatie aantoonbaar is`

Scope:

- harmoniseer alleen waar dat werkelijk logische duplicatie vermindert

Betrokken bestanden:

- `app.py`
- `src/pensioen/api/main.py`
- `src/pensioen/api/schemas.py`

Acceptatiecriteria:

- voorbereidingslogica is aantoonbaar minder dubbel of bewust verantwoord dubbel

## Epic 5-E — Contract- en regressiebewaking

### Issue 12

Titel:

`Voeg outputcontracttests toe voor API-consumenten`

Scope:

- borg relevante responsevelden voor React, Streamlit en API-client

Betrokken tests:

- `tests/test_api_main.py`
- `tests/test_api_regressie_normalized.py`

Acceptatiecriteria:

- wijzigingen in outputstructuur breken contracttests direct

### Issue 13

Titel:

`Voeg regressietests toe die bewaken dat presentatielagen geen afwijkende businessuitkomst tonen`

Scope:

- controleer dat presentatielagen geen inhoudelijk afwijkende interpretatie
  opleveren ten opzichte van engine-output

Acceptatiecriteria:

- outputdrift tussen engine en consumptiepaden veroorzaakt testfalen

## Epic 5-F — Integratiepoort

### Issue 14

Titel:

`Verifieer dat Epic 5 geen nieuw presentatiespoor met eigen fiscaliteit introduceert`

Scope:

- controle op Streamlit, React, API-client en rapportage

Acceptatiecriteria:

- Epic 5 vermindert client- en presentatielogica aantoonbaar

## Afhankelijkheden tussen issues

| Issue | Blokkeert |
| --- | --- |
| 1, 2, 3 | 4, 5, 6, 7, 8, 9 |
| 4, 5, 6 | 10, 11, 13 |
| 7, 8, 9 | 12, 13 |
| 10 | 11 |
| 11, 12, 13 | 14 |

## Definition of Done voor Epic 5 als geheel

Epic 5 is klaar als:

1. issues 1 tot en met 14 afgerond zijn
2. consumptiecontracten per presentatiepad zijn vastgelegd
3. Streamlit, React en API-client geen zelfstandige fiscale waarheid meer
   reconstrueren waar dat vermijdbaar is
4. dubbele voorbereidingslogica aantoonbaar is verminderd of expliciet verantwoord
5. contract- en regressietests de consumptiepaden bewaken

## Samenvatting

Deze backlog maakt van Epic 5 een serie kleine stappen om UI, API en
clientpaden terug te brengen tot wat ze horen te zijn: contract- en
presentatielagen boven één rekenengine.
