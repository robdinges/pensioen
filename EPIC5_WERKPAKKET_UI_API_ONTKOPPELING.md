---
post_title: "Epic 5 Werkpakket UI API Ontkoppeling"
author1: "GitHub Copilot"
post_slug: "epic-5-werkpakket-ui-api-ontkoppeling"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "epic-5"
  - "ui"
  - "api"
ai_note: "AI-assisted implementation planning based on the analysis and execution plan documents; no application code was modified."
summary: "Concreet uitvoerbaar werkpakket voor Epic 5: UI- en API-lagen reduceren tot pure consumptie van engine-output en client-side interpretatielogica minimaliseren."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Status 2026-07-26

De implementatie is afgerond. De primaire functionele stap is `Resultaten`.
`JaarResultaat.jaar_samenvatting` en `JaarResultaat.accountant_detail` zijn de
formele bronnen voor alle presentatiepaden. De API publiceert contractversie
`1.0`; React en `app_api_client.py` reconstrueren geen jaarbelasting of netto
inkomen meer uit maandvelden.

Request- en tariefvoorbereiding is gecentraliseerd in
`calculations/resultaat_service.py`. Alleen formattering, grafiektransformatie
en expliciet niet-fiscale vergelijkingen blijven in presentatielagen.

De technische poort is groen. Handmatige gelijkheidscontrole van Streamlit en
React blijft de gebruikersvalidatie voor afsluiting.

## Doel

Dit document werkt alleen **Epic 5** uit:

```text
UI/API ontkoppeling en presentatiemigratie
```

Het doel van Epic 5 is om vast te leggen en daarna technisch af te dwingen dat:

- UI-lagen alleen engine-output presenteren
- API een contractlaag is en geen alternatieve berekenlogica bevat
- client-side herleiding en interpretatielogica zo ver mogelijk wordt teruggebracht

## Functionele stap

Primary step:

- `Resultaten`

Dependent steps:

- alle voorgaande berekenstappen

Current source of truth:

- op hoofdlijn de engine, maar met extra interpretatie in UI- en clientlagen

Conflicting paths:

- Streamlit accountantpad had eigen herberekening
- `app_api_client.py` berekent netto client-side uit JSON-velden
- React aggregeert jaarresultaten client-side via `aggregateYearRows()`
- `app.py` en API bouwen op meerdere plekken voorbereidingslogica rond tarieven

Migration note:

- Epic 5 is de fase waarin presentatie en contractlagen zoveel mogelijk teruggaan
  naar pure consumptie

## Scope

Epic 5 omvat:

- Streamlit resultaten/accountant/rapport consumeren alleen engine-output
- client-side herleiding minimaliseren in React en API-client
- requestvoorbereiding en tariefvoorbereiding waar mogelijk harmoniseren
- voorkomen dat nieuwe presentatiepaden eigen fiscaliteit introduceren

Epic 5 omvat niet:

- finale verwijdering van alle legacycode
- volledige doelarchitectuurconsolidatie

## Gewenste uitkomst

Na afronding van Epic 5 moet gelden:

1. geen enkel scherm rekent box 1, box 3, eigen woning of netto inkomen zelfstandig uit
2. React en Streamlit presenteren dezelfde engine-definitie van output
3. API is een dun contract boven de core

## Werkpakket

### Werkstroom 1 — Consumptiecontract per UI-pad vastleggen

#### Taak 1.1

Leg per presentatielaag vast welke engine-output gelezen mag worden.

#### Te onderscheiden paden

- Streamlit resultaten
- Streamlit accountant
- Streamlit rapportage
- React resultaten
- React accountant
- `app_api_client.py`

#### Acceptatiecriterium werkstroom 1

- voor elk presentatiepad is duidelijk welke engine-output de enige toegestane bron is

### Werkstroom 2 — Streamlit hoofdpad opschonen

#### Taak 2.1

Beperk `app.py` tot orchestration en state, niet tot alternatieve interpretatie.

#### Taak 2.2

Verwijder of minimaliseer logica die resultaten opnieuw inhoudelijk afleidt buiten
de engine-output.

#### Betrokken code werkstroom 2

- `app.py`
- `src/pensioen/ui/pagina_resultaten.py`
- `src/pensioen/ui/pagina_rapport.py`

#### Acceptatiecriterium werkstroom 2

- Streamlit hoofdschermen consumeren engine-output zonder zelfstandige fiscale afleiding

### Werkstroom 3 — React en API-client herleiding minimaliseren

#### Taak 3.1

Beoordeel welke client-side aggregatie noodzakelijk is en welke in de engine moet zitten.

#### Taak 3.2

Minimaliseer netto- en jaarsomherleiding in:

- `frontend-react/src/planner/plannerCore.js`
- `app_api_client.py`

#### Betrokken code werkstroom 3

- `frontend-react/src/planner/plannerCore.js`
- `frontend-react/src/components/ResultsSection.jsx`
- `frontend-react/src/components/AccountantSection.jsx`
- `app_api_client.py`

#### Acceptatiecriterium werkstroom 3

- client-side code reconstrueert geen fiscale logica die beter uit de engine kan komen

### Werkstroom 4 — API-voorbereiding harmoniseren

#### Taak 4.1

Breng in kaart welke requestvoorbereiding en tariefvoorbereiding dubbel bestaat
tussen Streamlit en API.

#### Taak 4.2

Harmoniseer waar mogelijk zonder nieuwe logische duplicatie te introduceren.

#### Betrokken code werkstroom 4

- `app.py`
- `src/pensioen/api/main.py`
- `src/pensioen/api/schemas.py`

#### Acceptatiecriterium werkstroom 4

- voorbereidingslogica is aantoonbaar minder dubbel of expliciet verantwoord

### Werkstroom 5 — Regressie- en contractbewaking

#### Taak 5.1

Voeg tests toe die bewaken dat presentatielagen geen afwijkende businessuitkomst tonen.

#### Taak 5.2

Voeg contractchecks toe voor API-responsevelden die door React en Streamlit
worden geconsumeerd.

#### Betrokken tests werkstroom 5

- `tests/test_api_main.py`
- `tests/test_api_regressie_normalized.py`
- eventuele nieuwe UI-contracttests

#### Acceptatiecriterium werkstroom 5

- wijzigingen in outputcontracten veroorzaken direct testfalen op consumptiepaden

## Verwachte bestandsimpact

### Waarschijnlijk aan te passen

- `app.py`
- `app_api_client.py`
- `src/pensioen/api/main.py`
- `src/pensioen/ui/pagina_resultaten.py`
- `src/pensioen/ui/pagina_accountant.py`
- `src/pensioen/ui/pagina_rapport.py`
- `frontend-react/src/planner/plannerCore.js`
- `frontend-react/src/components/ResultsSection.jsx`
- `frontend-react/src/components/AccountantSection.jsx`
- `tests/test_api_main.py`
- `tests/test_api_regressie_normalized.py`

### Waarschijnlijk niet primair aan te passen in deze epic

- losse fiscale bouwsteenmodules
- eigen-woning- of premiefuncties als zodanig

## Belangrijkste risico’s

### Risico 1

Te veel client-side logica ineens verwijderen kan tijdelijke bruikbaarheid van
schermen verslechteren.

Mitigatie:

- eerst contracteren welke output ontbreekt, daarna pas clientlogica afbouwen

### Risico 2

Voorbereidingslogica tussen Streamlit en API te agressief harmoniseren kan leiden
tot verplaatsing van complexiteit zonder echte winst.

Mitigatie:

- alleen harmoniseren waar inhoudelijke duplicatie aantoonbaar is

### Risico 3

UI’s kunnen nog verborgen afhankelijk zijn van velden die niet formeel in de
engine-output zijn gegarandeerd.

Mitigatie:

- outputcontracttests toevoegen voordat velden worden verplaatst of verwijderd

## Beslispunten na Epic 5

Na Epic 5 moeten deze vragen met ja beantwoord kunnen worden:

1. Rekent geen enkel scherm nog zelfstandig box 1, box 3, eigen woning of netto uit?
2. Zijn Streamlit en React inhoudelijk op dezelfde outputbron aangesloten?
3. Is de API een dun contractpad geworden zonder alternatieve businesslogica?

Alleen dan is Epic 6 veilig opstartbaar.

## Definition of Done

Epic 5 is gereed als:

1. consumptiecontracten per presentatiepad zijn vastgelegd
2. Streamlit hoofdschermen engine-output consumeren zonder eigen fiscale logica
3. React en API-client client-side herleiding tot een minimum is teruggebracht
4. dubbele voorbereidingslogica aantoonbaar is verminderd of expliciet gemotiveerd behouden
5. outputcontracttests de consumptiepaden bewaken

## Samenvatting

Epic 5 is de fase waarin de UI- en API-lagen eindelijk gaan doen wat ze moeten
doen: niet rekenen, maar de engine op een consistente manier tonen en ontsluiten.
