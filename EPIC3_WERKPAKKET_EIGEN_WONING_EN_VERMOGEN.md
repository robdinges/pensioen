---
post_title: "Epic 3 Werkpakket Eigen Woning en Vermogen"
author1: "GitHub Copilot"
post_slug: "epic-3-werkpakket-eigen-woning-en-vermogen"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "epic-3"
  - "eigen-woning"
  - "vermogen"
ai_note: "AI-assisted implementation planning based on the analysis and execution plan documents; no application code was modified."
summary: "Concreet uitvoerbaar werkpakket voor Epic 3: eigen woning en vermogensgrondslagen harmoniseren, inclusief bronkeuze, engine-stap, box-3/vermogen-relatie en migratie van legacy vermogensvelden."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel

Dit document werkt alleen **Epic 3** uit:

```text
Eigen woning en vermogen harmoniseren
```

Het doel van Epic 3 is om vast te leggen en daarna technisch af te dwingen dat:

- eigen woning nog maar één inhoudelijk leidende bron heeft
- vermogensgrondslagen niet meer dubbel uit legacy velden en `vermogensitems`
  komen
- box 1, box 3 en vermogensopbouw functioneel op consistente grondslagen draaien

**Status: 🟡 IMPLEMENTATIE AFGEROND — FUNCTIONELE VALIDATIE OPEN.** Zie
`EPIC3_ISSUES_BACKLOG.md` voor de status per issue en het open beslispunt over
de verdeling van toekomstige netto cashflow over belast en vrijgesteld
liquide vermogen.

## Functionele stap

Primary step:

- `Eigen woning`

Dependent steps:

- `Scenario`
- `Bruto inkomen`
- `Box 1`
- `Box 3`
- `Vermogen`
- `Resultaten`

Current source of truth:

- niet zuiver

Conflicting paths:

- hoofdengine start vanuit legacy `spaargeld_start` en `beleggingen_start`
- accountantpad gebruikt eigen-woninginvoer uit `vermogensitems` plus
  `Scenario.eigen_woning`
- box 3-startverdeling en vermogensitemwereld zijn niet volledig geharmoniseerd

Migration note:

- zolang woning en vermogen niet op één formele bron steunen, blijven box 1,
  box 3 en netto-resultaten kwetsbaar voor grondslagverschillen

## Scope

Epic 3 omvat:

- formele keuze van de leidende woning/hypotheekbron
- expliciete engine-stap voor eigen woning
- heldere relatie tussen legacy vermogen en `vermogensitems`
- expliciete relatie tussen box 3-grondslag en vermogensontwikkeling

Epic 3 omvat niet:

- accountantdetail als volledige engine-output
- volledige UI-ontkoppeling
- definitieve opschoning van alle presentatielogica

## Centrale ontwerpbeslissingen

Epic 3 kan pas veilig uitgevoerd worden na expliciete keuzes voor:

### Beslissing A

Wat is de leidende bron voor woning en hypotheek?

Opties:

- `Scenario.eigen_woning`
- `VermogensItem(type=EIGEN_WONING/HYPOTHEEK)`
- read model afgeleid uit `vermogensitems`

### Beslissing B

Wat is de leidende bron voor startvermogen?

Opties:

- legacy `spaargeld_start` / `beleggingen_start`
- uitsluitend `vermogensitems`
- migratielaag waarbij legacy alleen nog import/backward compatibility is

### Beslissing C

Hoe expliciet moet het onderscheid blijven tussen:

- box 3 peildatumgrondslag
- maandelijkse rendementsgrondslag

## Aanbevolen keuzes

### Aanbevolen keuze A

Gebruik `vermogensitems` als primaire bron en een read model voor fiscale
eigen-woninginvoer.

### Aanbevolen keuze B

Breng legacy vermogensvelden onder migratieregime en werk toe naar een
`vermogensitems`-gedreven model.

### Aanbevolen keuze C

Behoud functioneel het verschil tussen box 3-peildatum en maandrendement, maar
maak beide expliciet en herleidbaar vanuit dezelfde formele vermogensbron.

## Gewenst eindresultaat van Epic 3

Na afronding van Epic 3 moet gelden:

1. eigen woning heeft één leidende bron
2. box 1 kan woningeffect uit de engine afleiden
3. box 3-grondslag en vermogensopbouw zijn functioneel verklaarbaar vanuit één
   formeel model
4. legacy vermogen is read-only migratielaag of uitgefaseerd

## Werkpakket

### Werkstroom 1 — Bronkeuze woning en vermogen vastleggen

#### Taak 1.1

Leg formeel vast dat woning/hypotheek primair uit `vermogensitems` komen,
eventueel via een afgeleid read model.

#### Taak 1.2

Leg formeel vast hoe legacy `spaargeld_start` en `beleggingen_start` zich tot
`vermogensitems` verhouden tijdens de migratie.

#### Acceptatiecriterium werkstroom 1

- woning- en vermogensbronkeuze zijn expliciet vastgelegd

### Werkstroom 2 — Eigen woning engine-stap expliciteren

#### Taak 2.1

Maak eigen woning een formele engine-stap tussen bruto inkomen en box 1.

#### Minimale output

- WOZ-waarde
- aftrekbare hypotheekrente
- overige aftrekbare kosten
- eigenwoningforfait
- saldo eigen woning
- Hillen-correctie
- box1-mutatie
- tariefsaanpassing

#### Betrokken code werkstroom 2

- `src/pensioen/tax/eigen_woning_engine.py`
- `src/pensioen/models/scenario.py`
- `src/pensioen/calculations/cashflow_engine.py`

#### Acceptatiecriterium werkstroom 2

- de engine kan eigen-woningeffect formeel als tussenstap leveren

### Werkstroom 3 — Legacy vermogen en vermogensitems harmoniseren

#### Taak 3.1

Maak expliciet hoe startvermogen wordt opgebouwd in de engine.

#### Taak 3.2

Definieer of en wanneer legacy velden nog gelezen mogen worden.

#### Taak 3.3

Voorkom dat `spaargeld_start` / `beleggingen_start` en `vermogensitems`
tegelijk onafhankelijk leidinggevend zijn.

#### Betrokken code werkstroom 3

- `src/pensioen/models/scenario.py`
- `src/pensioen/calculations/cashflow_engine.py`
- `src/pensioen/calculations/vermogen_engine.py`

#### Acceptatiecriterium werkstroom 3

- er bestaat één formele verklaring van startvermogen in de engine

### Werkstroom 4 — Box 3 en rendementsgrondslag expliciteren

#### Taak 4.1

Leg expliciet vast welke peildatumgrondslag box 3 gebruikt.

#### Taak 4.2

Leg expliciet vast welke grondslag maandrendement gebruikt.

#### Taak 4.3

Maak zichtbaar waarom deze twee mogen verschillen of trek ze functioneel gelijk
als dat wenselijk blijkt.

#### Betrokken code werkstroom 4

- `src/pensioen/calculations/cashflow_engine.py`
- `src/pensioen/calculations/vermogen_engine.py`
- `src/pensioen/models/scenario.py`

#### Acceptatiecriterium werkstroom 4

- box 3 en rendementsgrondslag zijn expliciet herleidbaar

### Werkstroom 5 — Regressie- en vergelijkingslaag

#### Taak 5.1

Voeg directe en regressietests toe voor:

1. eigen woning als engine-stap
2. box 1 met woningeffect
3. startvermogen uit gekozen bron
4. box 3-grondslag versus vermogensopbouw

#### Taak 5.2

Voeg vergelijkingstests toe tussen hoofdengine en accountantpad voor
eigen-woningeffect en box 3-grondslag.

#### Betrokken tests

- `tests/test_eigen_woning_engine.py`
- `tests/test_cashflow_engine.py`
- `tests/test_scenario_engine.py`
- `tests/test_regression_bugs.py`
- eventueel nieuwe contracttestmodule voor vermogen/woning

#### Acceptatiecriterium werkstroom 5

- verschillen in woning- of vermogensgrondslag veroorzaken direct een testfout

## Verwachte bestandsimpact

### Waarschijnlijk aan te passen

- `src/pensioen/models/scenario.py`
- `src/pensioen/calculations/cashflow_engine.py`
- `src/pensioen/calculations/vermogen_engine.py`
- `src/pensioen/tax/eigen_woning_engine.py`
- `tests/test_cashflow_engine.py`
- `tests/test_eigen_woning_engine.py`
- `tests/test_scenario_engine.py`
- `tests/test_regression_bugs.py`

### Waarschijnlijk niet centraal aan te passen in deze epic

- React componenten
- API endpoints
- losse heffingskortingfuncties

## Belangrijkste risico’s

### Risico 1

Eigen woning te vroeg in de hoofdengine trekken zonder bronkeuze kan
legacy-dubbeling verplaatsen in plaats van oplossen.

Mitigatie:

- eerst bronkeuze en read-model definitie vastleggen

### Risico 2

Legacy vermogensvelden te vroeg verwijderen kan backward compatibility breken.

Mitigatie:

- read-only migratielaag gebruiken totdat regressies aantonen dat de nieuwe bron
  volledig leidend is

### Risico 3

Box 3 en rendement onbewust gelijk trekken kan inhoudelijk andere uitkomsten
geven dan nu bedoeld is.

Mitigatie:

- verschil eerst expliciet modelleren en pas daarna inhoudelijk heroverwegen

## Beslispunten na Epic 3

Na Epic 3 moeten deze vragen met ja beantwoord kunnen worden:

1. Heeft eigen woning één formele bron?
2. Is box 1 inclusief woningeffect engine-output?
3. Is startvermogen formeel verklaard?
4. Zijn box 3-grondslag en rendementsgrondslag expliciet herleidbaar?

Alleen dan is Epic 4 veilig opstartbaar.

## Definition of Done

Epic 3 is gereed als:

1. woning- en vermogensbron formeel gekozen en vastgelegd zijn
2. eigen woning een expliciete engine-stap is
3. startvermogen niet meer dubbelzinnig is
4. box 3-grondslag en rendementsgrondslag expliciet zijn gemaakt
5. regressietests deze keuzes bewaken

## Samenvatting

Epic 3 draait om grondslagen: welke woning- en vermogensdata werkelijk leidend
zijn en hoe die doorwerken in box 1, box 3 en vermogen.

Zonder deze stap blijft de fiscale engine structureel kwetsbaar voor dubbele
bronnen en niet-herleidbare verschillen tussen hoofdresultaat en accountantpad.
