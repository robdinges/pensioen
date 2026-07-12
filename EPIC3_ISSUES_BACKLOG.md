---
post_title: "Epic 3 Issues Backlog"
author1: "GitHub Copilot"
post_slug: "epic-3-issues-backlog"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "epic-3"
  - "backlog"
  - "issues"
ai_note: "AI-assisted backlog structuring based on the approved Epic 3 work package; no application code was modified."
summary: "Concrete issue-level backlog for Epic 3 with small implementation slices, dependencies, and acceptance criteria for harmonizing eigen woning and vermogen." 
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel

Deze backlog vertaalt Epic 3 naar kleine, uitvoerbare issues.

Epic 3 draait om grondslagen:

- welke woning- en hypotheekbron leidend is
- welke vermogensbron leidend is
- hoe box 1, box 3 en vermogen daarop steunen

## Volgorde

De aanbevolen uitvoervolgorde is:

1. formele bronkeuze woning en vermogen
2. eigen woning als engine-stap
3. legacy vermogen versus `vermogensitems`
4. box 3- en rendementsgrondslagen expliciteren
5. regressie- en vergelijkingstests

## Epic 3-A — Bronkeuze woning en vermogen

### Issue 1

Titel:

`Leg leidende bron voor eigen woning en hypotheek formeel vast`

Scope:

- kies expliciet tussen `Scenario.eigen_woning`, `vermogensitems` of een read
  model afgeleid uit `vermogensitems`

Acceptatiecriteria:

- de leidende woning/hypotheekbron is formeel vastgelegd

### Issue 2

Titel:

`Leg formeel vast hoe legacy vermogen zich verhoudt tot vermogensitems`

Scope:

- definieer de rol van `spaargeld_start` en `beleggingen_start` tijdens migratie

Acceptatiecriteria:

- legacy vermogen heeft een expliciete migratiestatus

## Epic 3-B — Eigen woning als engine-stap

### Issue 3

Titel:

`Definieer formele engine-output voor eigen woning`

Scope:

- WOZ
- hypotheekrente
- overige kosten
- forfait
- Hillen
- box1-mutatie
- tariefsaanpassing

Betrokken bestanden:

- `src/pensioen/tax/eigen_woning_engine.py`
- `src/pensioen/models/scenario.py`

Acceptatiecriteria:

- eigen woning heeft een formeel gedefinieerde outputstructuur

### Issue 4

Titel:

`Maak eigen woning een expliciete stap tussen bruto inkomen en box 1`

Scope:

- veranker in de rekenketen dat eigen woning de box1-grondslag beïnvloedt

Betrokken bestanden:

- `src/pensioen/calculations/cashflow_engine.py`
- `src/pensioen/tax/eigen_woning_engine.py`

Acceptatiecriteria:

- box 1 kan het woningeffect uit engine-output afleiden

## Epic 3-C — Legacy vermogen en vermogensitems harmoniseren

### Issue 5

Titel:

`Definieer formeel hoe startvermogen in de engine wordt opgebouwd`

Scope:

- maak expliciet welke velden of items het startvermogen vormen

Acceptatiecriteria:

- startvermogen is niet langer impliciet of dubbelzinnig

### Issue 6

Titel:

`Beperk onafhankelijk leidend gebruik van legacy vermogen en vermogensitems`

Scope:

- voorkom dat beide bronnen tegelijk zelfstandig leidinggevend zijn

Betrokken bestanden:

- `src/pensioen/models/scenario.py`
- `src/pensioen/calculations/cashflow_engine.py`

Acceptatiecriteria:

- er is nog maar één formele uitleg van startvermogen in de engine

## Epic 3-D — Box 3 en rendementsgrondslagen expliciteren

### Issue 7

Titel:

`Leg formeel vast welke grondslag box 3 gebruikt`

Scope:

- peildatumgrondslag
- partnereffect
- spaargeldfractiebron

Acceptatiecriteria:

- box 3-grondslag is expliciet en herleidbaar

### Issue 8

Titel:

`Leg formeel vast welke grondslag maandrendement gebruikt`

Scope:

- saldo begin maand
- dynamische spaargeld/beleggingsverdeling

Acceptatiecriteria:

- rendementsgrondslag is expliciet en herleidbaar

### Issue 9

Titel:

`Documenteer of harmoniseer verschil tussen box 3-grondslag en rendementsgrondslag`

Scope:

- maak zichtbaar waarom beide mogen verschillen of trek ze gecontroleerd gelijk

Acceptatiecriteria:

- verschil tussen box 3 en rendement is geen verborgen gedragsverschil meer

## Epic 3-E — Regressie- en vergelijkingstests

### Issue 10

Titel:

`Voeg tests toe voor eigen woning als engine-stap`

Scope:

- engine-output voor woningeffect
- box 1 met woningcorrectie

Betrokken tests:

- `tests/test_cashflow_engine.py`
- `tests/test_eigen_woning_engine.py`

Acceptatiecriteria:

- woningeffect is regressiebewaakt in de engine

### Issue 11

Titel:

`Voeg tests toe voor gekozen vermogensbron en startvermogenopbouw`

Scope:

- startvermogen uit gekozen bron
- overgang legacy -> vermogensitems

Betrokken tests:

- `tests/test_scenario_engine.py`
- `tests/test_cashflow_engine.py`

Acceptatiecriteria:

- startvermogenbron is testmatig vastgezet

### Issue 12

Titel:

`Voeg vergelijkingstests toe voor hoofdengine versus accountantpad op woning en box 3`

Scope:

- eigen-woningeffect
- box 3-grondslag
- vermogensgrondslag

Betrokken tests:

- `tests/test_regression_bugs.py`
- eventueel aparte vergelijkingstestmodule

Acceptatiecriteria:

- verschillen in woning- of vermogensgrondslag veroorzaken direct een testfout

## Epic 3-F — Integratiepoort

### Issue 13

Titel:

`Verifieer dat Epic 3 de rekenketen zuiverder maakt zonder verborgen nevenpaden`

Scope:

- controleer dat woning en vermogen niet opnieuw in UI of rapportage worden
  herberekend om de wijziging te compenseren

Acceptatiecriteria:

- Epic 3 voegt geen nieuw parallel rekenpad toe

## Afhankelijkheden tussen issues

| Issue | Blokkeert |
| --- | --- |
| 1, 2 | 3, 4, 5, 6, 7, 8 |
| 3 | 4, 10, 12 |
| 5, 6 | 7, 8, 11 |
| 7, 8 | 9, 12 |
| 4, 9, 10, 11, 12 | 13 |

## Definition of Done voor Epic 3 als geheel

Epic 3 is klaar als:

1. issues 1 tot en met 13 afgerond zijn
2. woning- en vermogensbron formeel gekozen zijn
3. eigen woning een expliciete engine-stap is
4. startvermogen en box 3-grondslagen niet meer dubbelzinnig zijn
5. regressietests deze keuzes bewaken

## Samenvatting

Deze backlog maakt van Epic 3 een serie kleine stappen rond één functionele
vraag: welke woning- en vermogensgrondslagen werkelijk leidend zijn en hoe die
consequent in box 1, box 3 en vermogen moeten doorwerken.
