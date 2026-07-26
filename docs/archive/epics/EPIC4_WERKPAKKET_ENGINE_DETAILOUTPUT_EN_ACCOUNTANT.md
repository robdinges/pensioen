---
archived: true
post_title: "Epic 4 Werkpakket Engine Detailoutput en Accountant"
author1: "GitHub Copilot"
post_slug: "epic-4-werkpakket-engine-detailoutput-en-accountant"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "epic-4"
  - "accountant"
  - "detailoutput"
ai_note: "AI-assisted implementation planning based on the analysis and execution plan documents; no application code was modified."
summary: "Concreet uitvoerbaar werkpakket voor Epic 4: detailoutput uit de engine opbouwen en de accountantspagina migreren van zelfstandige herberekening naar pure consumptie van engine-output."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Status 2026-07-26

De implementatie is afgerond. De functionele stap is `Resultaten`; de source of
truth is `JaarResultaat.accountant_detail`, samengesteld in
`detail_output_engine.py` uit engine-output. Accountant, Excel en
testcase-validatie gebruiken dit contract zonder fiscale herberekening.

De integratiepoort blijft geel door reeds bestaande IB-2025-afwijkingen:
2 WARN en 4 FAIL in de validatiepipeline. Deze zijn geen verschil tussen oud en
nieuw accountantpad en zijn bewust niet gerebaselined.

## Doel

Dit document werkt alleen **Epic 4** uit:

```text
Engine-detailoutput en accountant-engine
```

Het doel van Epic 4 is om vast te leggen en daarna technisch af te dwingen dat:

- alle relevante tussenresultaten uit de engine komen
- de accountantspagina geen tweede rekensysteem meer is
- detailcontrole, rapportage en validatie op dezelfde outputbron steunen

## Functionele stap

Primary step:

- `Resultaten`

Dependent steps:

- `Pensioen`
- `AOW`
- `Arbeid`
- `Bruto inkomen`
- `Eigen woning`
- `Box 1`
- `Heffingskortingen`
- `Netto inkomen`
- `Box 3`
- `Vermogen`

Current source of truth:

- niet zuiver op detailniveau

Conflicting paths:

- hoofdengine levert hoofdoutput
- accountantpad berekent jaar- en maanddetail zelfstandig opnieuw via
  `_bereken_jaar_detail()`

Migration note:

- Epic 4 is de fase waarin accountantdetail van een parallelle engine wordt
  teruggebracht tot een view op centrale engine-output

## Scope

Epic 4 omvat:

- formele detailoutput uit de engine
- accountantdetail-DTO of equivalente outputstructuur
- pure detailassembler of accountant-engine in de berekenlaag
- migratie van accountantspagina naar centrale detailoutput

Epic 4 omvat niet:

- volledige UI-ontkoppeling buiten accountant/resultaat/rapport-consumptie
- finale opschoning van alle legacy of presentatielogica

## Gewenste uitkomst

Na afronding van Epic 4 moet gelden:

1. de engine levert detailoutput voor controle en narekening
2. accountantdetail wordt niet meer in UI-formules berekend
3. hoofdresultaat en accountantdetail zijn twee presentaties van dezelfde
   rekenbron

## Minimale detailoutput die de engine moet leveren

### Inkomensdetail

- arbeid bruto per persoon
- AOW bruto per persoon
- pensioen bruto per persoon
- overig bruto per persoon
- netto componentinkomen

### Eigen woning detail

- WOZ
- hypotheekrente
- overige kosten
- forfait
- saldo
- Hillen
- box1-mutatie
- tariefsaanpassing

### Box 1 detail

- box1-grondslag per persoon
- IB vóór korting
- premiecomponenten
- totaal IB + premies

### Heffingskorting detail

- AHK
- arbeidskorting
- ouderenkorting
- AOK
- totaalkorting

### Box 3 detail

- vrijstelling
- belastbaar vermogen
- spaargeldfractie
- forfaiten
- fictief rendement
- heffing

### Vermogensdetail

- saldo begin jaar
- saldo begin maand
- rente/rendement per maand
- netto cashflow per maand
- saldo einde maand
- saldo einde jaar

## Werkpakket

### Werkstroom 1 — Detailoutput contracteren

#### Taak 1.1

Definieer formeel welke detailvelden de engine moet leveren voor accountant,
rapportage en validatie.

#### Taak 1.2

Leg vast welke velden rechtstreeks uit berekeningen komen en welke afleidingen
toegestaan zijn.

#### Acceptatiecriterium werkstroom 1

- accountantdetailvelden zijn formeel gecontracteerd

### Werkstroom 2 — Detailassembler in de berekenlaag bouwen

#### Taak 2.1

Ontwerp een pure detailassembler of accountant-engine in de berekenlaag.

#### Taak 2.2

Laat deze assembler uitsluitend steunen op formele bouwstenen en engine-input,
niet op UI-state-specifieke reconstructies.

#### Betrokken code werkstroom 2

- `src/pensioen/calculations/cashflow_engine.py`
- eventueel nieuwe module, bijvoorbeeld `accountant_engine.py` of
  `detail_output_engine.py`
- `src/pensioen/models/cashflow.py` of nieuwe detail-DTO’s

#### Acceptatiecriterium werkstroom 2

- detailoutput kan buiten UI-context worden gegenereerd

### Werkstroom 3 — Accountantpad migreren

#### Taak 3.1

Vervang `_bereken_jaar_detail()` als primaire businessimplementatie.

#### Taak 3.2

Laat `pagina_accountant.py` alleen nog engine-detailoutput consumeren.

#### Belangrijke randvoorwaarde

- eventuele tijdelijke compatibiliteitslaag mag geen tweede fiscale waarheid
  introduceren

#### Betrokken code werkstroom 3

- `src/pensioen/ui/pagina_accountant.py`
- nieuwe of aangepaste detailassembler in `src/pensioen/calculations`

#### Acceptatiecriterium werkstroom 3

- accountantspagina bevat geen zelfstandige fiscale herberekening meer

### Werkstroom 4 — Vergelijking met oude accountant-output

#### Taak 4.1

Maak vergelijkingstests tussen oude accountant-output en nieuwe engine-detailoutput
voor representatieve scenario’s.

#### Taak 4.2

Leg expliciet vast welke oude verschillen:

- echte bugs zijn
- oude migratieschuld zijn
- contractueel veranderd gedrag zijn

#### Betrokken tests werkstroom 4

- `tests/test_regression_bugs.py`
- `tests/testcase_validatie.py`
- eventueel nieuwe golden master of vergelijkingstestmodule

#### Acceptatiecriterium werkstroom 4

- overgang van oude accountantlogica naar engine-detailoutput is regressiebewaakt

### Werkstroom 5 — Resultaat-, rapportage- en validatieaansluiting

#### Taak 5.1

Controleer dat rapportage en validatie de nieuwe detailoutput kunnen hergebruiken.

#### Taak 5.2

Minimaliseer duplicatie tussen accountant, rapport en validatiepaden.

#### Betrokken code werkstroom 5

- `src/pensioen/reports/rapport_engine.py`
- `validatie/*`
- accountant-outputconsumenten

#### Acceptatiecriterium werkstroom 5

- detailoutput is bruikbaar buiten alleen de accountantspagina

## Verwachte bestandsimpact

### Waarschijnlijk aan te passen

- `src/pensioen/calculations/cashflow_engine.py`
- nieuwe detailassembler/module in `src/pensioen/calculations`
- `src/pensioen/models/cashflow.py` of nieuwe detailmodellen
- `src/pensioen/ui/pagina_accountant.py`
- `src/pensioen/reports/rapport_engine.py`
- `tests/test_regression_bugs.py`
- `tests/testcase_validatie.py`

### Waarschijnlijk niet centraal aan te passen in deze epic

- losse fiscale bouwsteenmodules
- React componenten buiten accountant/resultaat-consumptie

## Belangrijkste risico’s

### Risico 1

De nieuwe detailoutput kan te snel te veel presentatieconcerns meenemen.

Mitigatie:

- contracteer alleen rekenkundige detailvelden en grondslagen, geen UI-opmaak

### Risico 2

De oude accountant-output bevat impliciete special cases die niet allemaal
zichtbaar zijn in de huidige analyses.

Mitigatie:

- golden-master-achtige vergelijkingstests of expliciete migratievergelijkingen

### Risico 3

Er kan tijdelijke druk ontstaan om verschillen “in de UI” te repareren.

Mitigatie:

- verbied zelfstandige fiscale recomputatie in presentatiecode

## Beslispunten na Epic 4

Na Epic 4 moeten deze vragen met ja beantwoord kunnen worden:

1. Levert de engine alle benodigde tussenresultaten voor accountantcontrole?
2. Is accountantdetail volledig afgeleid uit engine-output?
3. Is `_bereken_jaar_detail()` als businesspad verdwenen of gedegradeerd?

Alleen dan is Epic 5 veilig opstartbaar.

## Definition of Done

Epic 4 is gereed als:

1. de detailoutput formeel gecontracteerd is
2. de engine detailoutput buiten UI-context kan produceren
3. accountantspagina geen zelfstandige fiscale herberekening meer bevat
4. regressietests de overgang van oud naar nieuw accountantpad bewaken
5. rapportage en validatie de detailoutput kunnen hergebruiken

## Samenvatting

Epic 4 is de fase waarin de accountantspagina ophoudt een tweede rekensysteem te
zijn. Vanaf dit punt moet detailcontrole niet meer een UI-truc zijn, maar een
normale outputvorm van dezelfde engine die ook het hoofdresultaat bepaalt.
