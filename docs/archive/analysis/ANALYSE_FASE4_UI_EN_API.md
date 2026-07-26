---
post_title: "Analyse Fase 4 UI en API"
author1: "GitHub Copilot"
post_slug: "analyse-fase-4-ui-en-api"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "analysis"
  - "ui"
  - "api"
  - "streamlit"
  - "react"
ai_note: "AI-assisted UI and API analysis based on repository inspection; no application code was modified."
summary: "Fase 4 analyse van Streamlit, React, API en accountantspagina met focus op dubbele berekeningen, afwijkende logica en verschillende databronnen."
post_date: "2026-07-12"
archived: true
---

<!-- markdownlint-disable MD041 -->

## Doel en afbakening

Deze fase analyseert uitsluitend:

- Streamlit
- React
- FastAPI
- accountantspagina

met focus op:

- dubbele berekeningen
- afwijkende logica
- verschillende databronnen
- inconsistenties tussen schermen en paden

## 1. Overzicht van de vier relevante paden

| Pad | Ingang | Rekent zelf? | Leest hoofdengine-output? | Opmerking |
| --- | --- | --- | --- | --- |
| Streamlit hoofdpad | `app.py` + resultaatpagina | nee, roept hoofdengine aan | ja | standaard pad voor resultaten |
| FastAPI-pad | `src/pensioen/api/main.py` | nee, roept hoofdengine aan | ja | contractlaag boven core |
| React-pad | `frontend-react/src/App.jsx` | niet fiscaal, wel payloadmapping en aggregatie | ja | presentatielaag plus requestbuilder |
| Streamlit accountantpad | `src/pensioen/ui/pagina_accountant.py` | ja | nee, niet als bron van waarheid | tweede rekensysteem |

## 2. Streamlit hoofdpad

### Datastroom Streamlit hoofdpad

```text
gebruiker
  -> session_state
  -> laad_tarieven_bereik
  -> resolve_tariefwaarden_voor_jaar
  -> bereken_huishouden
  -> cashflow_hoofd in session_state
  -> pagina_resultaten / pagina_rapport
```

### Eigenschappen Streamlit hoofdpad

- de Streamlit hoofdapp roept direct `bereken_huishouden()` aan
- scenario-switch in `app.py` kan direct herberekenen
- tariefoverrides worden al in `app.py` toegepast vóór de enginecall

### Risico’s Streamlit hoofdpad

- `app.py` bevat eigen orchestration- en herberekenlogica
- `STAP_NAAR_PAGINA` bevat geen route voor `Stap.SCENARIO`, terwijl die stap wel
  in de flow bestaat
- session state is zowel inputstore als resultstore

## 3. FastAPI-pad

### Datastroom FastAPI-pad

```text
request
  -> BerekeningRequest.normaliseer_codes
  -> _bouw_belasting_configs
  -> bereken_huishouden
  -> naar_json_compatibel
  -> response
```

### Eigenschappen FastAPI-pad

- de API is relatief dun
- codes worden genormaliseerd in `schemas.py`
- inheritance-validatie gebeurt voor berekeningen en vergelijkingen

### Risico’s FastAPI-pad

- API bouwt zelf tariefconfigs op met `_bouw_belasting_configs`
- dat lijkt op orchestration uit `app.py`; er zijn dus twee plaatsen waar
  dezelfde preparatiestap leeft

## 4. React-pad

### Datastroom React-pad

```text
React state
  -> buildRequestPayload()
  -> POST /api/v1/berekeningen
  -> cashflow response
  -> aggregateYearRows()
  -> ResultsSection / AccountantSection / ReportSection
```

### Wat React wel doet

- payloads samenstellen
- types mappen naar API-codes
- gemiddelden van rendementen bepalen uit posts
- jaarresultaten client-side aggregeren uit maanddata
- accountantweergave opbouwen uit API-response

### Wat React niet doet

- geen fiscale herberekening
- geen box 1/box 3/own-woning-engine lokaal

### Concrete afwijkingen ten opzichte van Streamlit

| Onderwerp | React | Streamlit |
| --- | --- | --- |
| pensioenimport | vooral preview + state | zet records direct om naar scenario-componenten |
| `records1/records2` in request | standaard leeg | hoofd-Streamlit gebruikt ook effectief geen records in berekening |
| resultaataggregatie | `aggregateYearRows()` client-side | `JaarResultaat` properties en grafiekpagina |
| accountantdetail | leest API-output | rekent zelfstandig opnieuw |

### Concrete risico’s

- `buildRequestPayload()` is handmatige modelvertaling en dus foutgevoelig
- React berekent gemiddelde sparen/beleggen-rendementen uit posts, terwijl de
  backend ook eigen logica heeft rond legacy velden en dynamische fracties
- `aggregateYearRows()` berekent netto client-side uit maandvelden, dus er is
  een extra interpretatielaag buiten de backend

## 5. Streamlit accountantpad

### Datastroom accountantpad

```text
session_state
  -> laad_tarieven(jaar)
  -> resolve_tariefwaarden_voor_jaar
  -> _bereken_jaar_detail
  -> tabellen en toelichtingen
```

### Wat deze pagina zelf doet

- AOW-datums bepalen
- maanddata opnieuw opbouwen
- bruto jaarinkomen opnieuw samenstellen
- eigen woning berekenen
- box 1-belasting opnieuw berekenen
- premies opnieuw berekenen
- heffingskortingen opnieuw berekenen
- box 3 opnieuw berekenen
- vermogensopbouw opnieuw berekenen

### Waarom dit het grootste afwijkingspunt is

Deze pagina is geen presentatielaag op basis van een bestaande
`HuishoudCashflow`-detailstructuur.

Het is een tweede rekensysteem dat naast de hoofdengine bestaat.

## 6. Exacte verschilpunten tussen schermen en processen

### Verschilpunt 1: pensioenbron

| Pad | Bron |
| --- | --- |
| hoofdengine | `Scenario.componenten` |
| accountantpad | `records1` / `records2` via `bereken_pensioen_maand()` |
| Streamlit import | zet records om naar componenten |
| React import | houdt vooral preview/state bij en stuurt lege `records1/records2` |

### Verschilpunt 2: eigen woning

| Pad | Eigen woning in berekening? |
| --- | --- |
| hoofdengine | nee |
| accountantpad | ja |
| React accountantweergave | alleen wat in API-output zit |
| resultaatpagina | geen zelfstandige detailberekening |

### Verschilpunt 3: resultaatbron

| Scherm | Gebruikt welke bron? |
| --- | --- |
| Streamlit resultaten | `cashflow_hoofd` |
| Streamlit rapport | `cashflow_hoofd` |
| React resultaten | API-response + client-aggregatie |
| React accountant | API-response + `gebruikte_tarieven` uit maanddata |
| Streamlit accountant | eigen `_bereken_jaar_detail()` |

### Verschilpunt 4: netto-herleiding

| Pad | Nettoafleiding |
| --- | --- |
| hoofdengine | backend in `MaandResultaat` en `JaarResultaat` |
| app_api_client | `_bereken_maand_netto()` client-side uit JSON-velden |
| React | `aggregateYearRows()` client-side uit JSON-velden |
| accountantpad | zelfstandige detailformule |

Gevolg:

- er bestaan meerdere interpretaties van hetzelfde resultaatmodel

## 7. Waar kunnen verschillen ontstaan?

### Tussen Streamlit resultaten en Streamlit accountant

- eigen woning wel versus niet
- pensioen uit componenten versus records
- AHK-special case in accountantpad
- black-box `netto_uit_bruto()` versus uitgesplitste herberekening

### Tussen React en Streamlit hoofdpad

- React payloadmapping kan anders zijn dan wat Streamlit in session state heeft
- React aggregeert jaarwaarden client-side
- React gebruikt lege `records1/records2`

### Tussen API en Streamlit orchestration

- beide bouwen tariefconfigs op, maar op verschillende plekken
- beide moeten scenario-overrides consistent toepassen

### Tussen app_api_client en de hoofdengine

- `app_api_client.py` berekent netto cliënt-side opnieuw uit de responsevelden
- dat is geen fiscale engine, maar wel een extra interpretatielaag

## 8. Welke onderdelen zijn puur presentatie en welke niet

### Vrijwel alleen presentatie

- `ResultsSection.jsx`
- `ReportSection.jsx`
- `WizardSidebar.jsx`
- `ContextTopBar.jsx`
- delen van `pagina_resultaten.py`

### Presentatie plus business-achtige logic glue

- `frontend-react/src/planner/plannerCore.js`
- `app.py`
- `app_api_client.py`
- `pagina_import.py`

### Feitelijk businesslogica in UI

- `pagina_accountant.py`
- delen van `pagina_componenten.py`
- scenario CRUD- en inheritance-gedrag in `pagina_scenario.py`

## 9. Wat fase 4 betekent voor herstructurering

De UI- en API-laag zijn pas echt veilig te scheiden nadat drie dingen zijn
opgelost:

1. de accountantspagina mag niet langer zelfstandig rekenen
2. React en andere clients moeten één gestandaardiseerde outputstructuur lezen
3. requestbouw en tariefvoorbereiding moeten op minder plaatsen leven

## 10. Kortste samenvatting

De API en React liggen al redelijk dicht bij een presentatie-op-core model, maar
de Streamlit accountantspagina en delen van de Streamlit orchestration bevatten
nog zelfstandige reken- en interpretatielogica, waardoor UI en core nu nog niet
volledig van elkaar gescheiden zijn.
