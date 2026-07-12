---
post_title: "Epic 2 Werkpakket Pensioen en Inkomensbronnen"
author1: "GitHub Copilot"
post_slug: "epic-2-werkpakket-pensioen-en-inkomensbronnen"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "epic-2"
  - "pension"
  - "income"
ai_note: "AI-assisted implementation planning based on the analysis and execution plan documents; no application code was modified."
summary: "Concreet uitvoerbaar werkpakket voor Epic 2: pensioenbron harmoniseren en bruto-inkomensopbouw eenduidig maken tussen hoofdengine en accountantpad."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel

Dit document werkt alleen **Epic 2** uit:

```text
Pensioen en inkomensbronnen harmoniseren
```

Het doel van Epic 2 is om vast te leggen en daarna technisch af te dwingen dat:

- pensioen nog maar één inhoudelijk leidende bron heeft
- bruto inkomen een expliciete tussenstap wordt
- hoofdengine en accountantpad dezelfde opbouw van inkomsten gebruiken

## Functionele stap

Primary step:

- `Pensioen`

Dependent steps:

- `AOW`
- `Arbeid`
- `Bruto inkomen`
- `Netto inkomen`
- `Resultaten`

Current source of truth:

- niet zuiver

Conflicting paths:

- hoofdengine: pensioen uit `Scenario.componenten`
- accountantpad: pensioen uit `records1` en `records2` via
  `bereken_pensioen_maand()`

Migration note:

- zolang deze dubbele bron bestaat, blijft bruto inkomen functioneel instabiel

## Scope

Epic 2 omvat:

- formele keuze van de leidende pensioenbron
- expliciete bruto-inkomen opbouw per persoon
- uitlijning van hoofdengine en accountantpad op dezelfde pensioenbron
- regressiebewaking op inkomstenopbouw

Epic 2 omvat niet:

- eigen woningharmonisatie
- box 1-detailoutput voor accountant
- UI-ontkoppeling
- box 3- of vermogensmigratie

## Centrale ontwerpbeslissing

Epic 2 kan pas veilig uitgevoerd worden na een expliciete keuze voor één van
deze drie modellen:

### Model A

`PensioenRecord` is de primaire bron en wordt in de engine zelf omgerekend.

### Model B

`Scenario.componenten` is de primaire bron en MPO-import is alleen een
transformatielaag naar componenten.

### Model C

er komt een expliciete tussenlaag `PensioenBron -> PensioenComponenten`, en
zowel hoofdengine als accountant consumeren uitsluitend de output daarvan.

## Aanbevolen keuze

Op basis van de huidige code is **Model C** het veiligst.

Waarom:

- de hoofdengine is nu al componentgericht
- de importlaag zet records nu feitelijk al om naar componenten
- accountantlogica kan dan dezelfde getransformeerde bron gebruiken
- dit voorkomt dat ruwe records en scenario-componenten parallel leidinggevend
  blijven

## Gewenst eindresultaat van Epic 2

Na afronding van Epic 2 moet gelden:

1. er is nog maar één inhoudelijk leidende pensioenbron
2. bruto inkomen is expliciet beschikbaar per persoon en per jaar
3. accountant en hoofdengine bouwen bruto inkomen op uit dezelfde bron
4. regressietests bewaken dat pensioensommen niet uiteenlopen

## Werkpakket

### Werkstroom 1 — Functionele bronkeuze vastleggen

#### Taak 1.1

Leg formeel vast welke pensioenbron leidend is.

#### Te beantwoorden vragen

1. Waar hoort pensioen inhoudelijk thuis: recordlaag of componentlaag?
2. Is import een verrijkingsstap of een alternatieve invoerbron?
3. Welke vorm moet de rekenengine uiteindelijk consumeren?

#### Betrokken bestanden

- `MASTERPLAN_PENSIOENAPPLICATIE.md`
- `UITVOERINGSPLAN_HERSTRUCTURERING.md`
- eventuele aanvullende architectuur- of contractdocumenten

#### Acceptatiecriterium werkstroom 2

- de leidende pensioenbron is formeel vastgelegd

### Werkstroom 2 — Pensioen-transformatielaag expliciteren

#### Taak 2.1

Breng de huidige record-naar-component-transformatie formeel onder als
expliciete stap in de keten.

#### Betrokken code werkstroom 3

- `src/pensioen/parsers/parser_mpo.py`
- `src/pensioen/ui/pagina_import.py`

#### Gewenst resultaat

- duidelijk onderscheid tussen:
  - ruwe importbron
  - getransformeerde rekenbron

#### Acceptatiecriterium werkstroom 3

- er is geen impliciete pensioenbronwissel meer tussen import en berekening

### Werkstroom 3 — Bruto inkomen expliciet modelleren

#### Taak 3.1

Definieer een formele tussenoutput voor bruto inkomen per persoon.

#### Minimale inhoud

- arbeid bruto P1/P2
- AOW bruto P1/P2
- pensioen bruto P1/P2
- overig bruto P1/P2
- totaal bruto P1/P2
- totaal bruto huishouden

#### Betrokken code werkstroom 4

- `src/pensioen/calculations/cashflow_engine.py`
- `src/pensioen/models/cashflow.py`
- eventueel nieuwe DTO of helperstructuur

#### Acceptatiecriterium werkstroom 4

- bruto inkomen is geen impliciete tussenstap meer maar expliciet uitleesbaar

### Werkstroom 4 — Hoofdengine en accountantpad uitlijnen

#### Taak 4.1

Zorg dat accountantdetail dezelfde pensioenbron gebruikt als de hoofdengine.

#### Belangrijke randvoorwaarde

- dit mag niet in UI-formules worden opgelost
- de oplossing moet richting engine of gedeelde transformatielaag bewegen

#### Betrokken code

- `src/pensioen/calculations/cashflow_engine.py`
- `src/pensioen/ui/pagina_accountant.py`
- mogelijk gedeelde helper/service

#### Acceptatiecriterium werkstroom 5

- dezelfde invoer geeft dezelfde pensioenopbouw in hoofdpad en accountantpad

### Werkstroom 5 — Test- en regressielaag toevoegen

#### Taak 5.1

Voeg directe tests toe voor de gekozen pensioenbronketen.

#### Verplichte scenario’s

1. één pensioenbron P1
2. meerdere pensioenbronnen P1
3. pensioen P1 en P2 samen
4. partner- of nabestaandenpensioen dat niet als regulier inkomen moet tellen
5. geïmporteerde MPO-data die naar rekenbron wordt getransformeerd

#### Taak 5.2

Voeg vergelijkingstests toe tussen hoofdengine en accountantpad op pensioenopbouw.

#### Betrokken tests

- `tests/test_cashflow_engine.py`
- `tests/test_parser_mpo.py`
- `tests/test_regression_bugs.py`
- mogelijk nieuwe testmodule voor pensioenbroncontracten

#### Acceptatiecriterium

- pensioensom en bruto-inkomensopbouw zijn regressiebewaakt

## Verwachte bestandsimpact

### Waarschijnlijk aan te passen

- `src/pensioen/parsers/parser_mpo.py`
- `src/pensioen/ui/pagina_import.py`
- `src/pensioen/calculations/cashflow_engine.py`
- `src/pensioen/models/cashflow.py`
- `src/pensioen/ui/pagina_accountant.py`
- `tests/test_cashflow_engine.py`
- `tests/test_parser_mpo.py`
- `tests/test_regression_bugs.py`

### Waarschijnlijk niet aan te passen

- `src/pensioen/tax/heffingskorting.py`
- `src/pensioen/tax/belasting_engine.py`
- `src/pensioen/tax/eigen_woning_engine.py`

## Belangrijkste risico’s

### Risico 1

Een te vroege keuze voor records of componenten kan later eigen woning- en
accountantmigratie bemoeilijken.

Mitigatie:

- kies expliciet voor een transformatielaag als tussenmodel

### Risico 2

Bruto-inkomen DTO kan te vroeg teveel fiscale detail bevatten.

Mitigatie:

- houd deze stap zuiver: alleen inkomensopbouw, nog geen box 1-detail

### Risico 3

Accountantpad kan tijdelijk nog afhankelijk blijven van oude recordslogica.

Mitigatie:

- markeer dit expliciet als migratieschuld totdat werkstroom 4 afgerond is

## Beslispunten na Epic 2

Na Epic 2 moeten deze vragen met ja beantwoord kunnen worden:

1. Is er nog maar één inhoudelijk leidende pensioenbron?
2. Is bruto inkomen expliciet en uitleesbaar per persoon?
3. Sluiten hoofdengine en accountantpad aan op dezelfde pensioenopbouw?

Alleen dan is Epic 3 of Epic 4 veilig opstartbaar.

## Definition of Done

Epic 2 is gereed als:

1. de leidende pensioenbron formeel gekozen en vastgelegd is
2. de transformatielaag van import naar rekenbron expliciet is
3. bruto inkomen als expliciete tussenoutput bestaat
4. accountantpad en hoofdengine dezelfde pensioenopbouw gebruiken
5. regressietests deze gelijkheid bewaken

## Samenvatting

Epic 2 draait niet om fiscale formules, maar om het harmoniseren van de bron
waaruit de rest van de berekening wordt opgebouwd.

Zonder deze stap blijft bruto inkomen instabiel en blijft iedere latere
herstructurering van box 1, netto inkomen, accountantdetail en resultaten
onnodig risicovol.
