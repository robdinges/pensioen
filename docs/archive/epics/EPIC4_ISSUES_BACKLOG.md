---
archived: true
post_title: "Epic 4 Issues Backlog"
author1: "GitHub Copilot"
post_slug: "epic-4-issues-backlog"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "epic-4"
  - "backlog"
  - "issues"
ai_note: "AI-assisted backlog structuring based on the approved Epic 4 work package; no application code was modified."
summary: "Concrete issue-level backlog for Epic 4 with small implementation slices, dependencies, and acceptance criteria for engine detailoutput and accountant migration."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel

Deze backlog vertaalt Epic 4 naar kleine, uitvoerbare issues.

## Implementatiestatus 2026-07-26

Status: **implementatie afgerond, fiscale referentievalidatie open**.

- Issues 1-11 zijn geïmplementeerd op `codex/epic4-engine-detailoutput`.
- `JaarResultaat.accountant_detail`, opgebouwd door
  `detail_output_engine.py`, is de source of truth voor resultaatdetail.
- Primaire en afgeleide contractvelden zijn expliciet geclassificeerd.
- De accountantpagina rekent één doorlopende meerjarige engine-reeks en bevat
  geen zelfstandige fiscale herberekening.
- Excel en testcase-validatie consumeren de centrale detailoutput.
- De compatibiliteitsfunctie `_bereken_jaar_detail()` blijft tijdelijk bestaan,
  maar delegeert volledig naar `bereken_accountant_jaar_detail()`.
- De Epic 4-contracttests zijn groen. De IB-2025-validatie blijft op 2 WARN en
  4 FAIL; onder meer TC008 en TC010 hebben bestaande expliciete regressietests.
  Deze referentieafwijkingen worden niet stil gerebaselined.

Verschilclassificatie:

| Verschil | Classificatie | Actie |
| --- | --- | --- |
| Accountant startte ieder jaar een losse eenjaarsberekening | echte bug | vervangen door één meerjarige engine-run |
| Validatie importeerde een Streamlit-helper | migratieschuld | rechtstreeks aangesloten op berekenlaag |
| IB-2025-pipeline: 2 WARN, 4 FAIL | bestaande fiscale validatieschuld | open laten voor inhoudelijke validatie |

Epic 4 draait om één hoofdvraag:

```text
Hoe maken we accountantdetail een normale outputvorm van de engine in plaats van een tweede rekensysteem?
```

## Volgorde

De aanbevolen uitvoervolgorde is:

1. detailoutput contracteren
2. detailassembler bouwen
3. accountantpad migreren
4. oud en nieuw accountantpad vergelijken
5. rapportage en validatie aansluiten

## Epic 4-A — Detailoutput contracteren

### Issue 1

Titel:

`Leg formeel vast welke detailvelden de engine moet leveren`

Scope:

- inkomensdetail
- eigen woning detail
- box 1 detail
- heffingskortingen detail
- box 3 detail
- vermogensdetail

Acceptatiecriteria:

- accountantdetailvelden zijn formeel gecontracteerd

### Issue 2

Titel:

`Leg vast welke detailvelden primaire output zijn en welke afgeleid mogen worden`

Scope:

- onderscheid tussen rekenkundige bronvelden en toegestane afleidingen

Acceptatiecriteria:

- geen ambiguïteit meer tussen bronwaarden en presentatiewaarden

## Epic 4-B — Detailassembler bouwen

### Issue 3

Titel:

`Ontwerp pure detailassembler of accountant-engine in de berekenlaag`

Scope:

- ontwerp zonder UI-afhankelijkheid
- definieer invoer, output en lifecycle

Betrokken bestanden:

- `src/pensioen/calculations/cashflow_engine.py`
- eventueel nieuwe module in `src/pensioen/calculations`
- `src/pensioen/models/cashflow.py` of nieuwe detailmodellen

Acceptatiecriteria:

- detailoutput kan buiten UI-context worden gegenereerd

### Issue 4

Titel:

`Implementeer detailassembler op basis van engine-bouwstenen`

Scope:

- gebruik formele bouwstenen en engine-input
- geen reconstructie vanuit presentation state

Acceptatiecriteria:

- de detailassembler gebruikt geen zelfstandige UI-rekenlogica

## Epic 4-C — Accountantpad migreren

### Issue 5

Titel:

`Vervang _bereken_jaar_detail als primaire businessimplementatie`

Scope:

- migreer businesslogica weg uit `pagina_accountant.py`

Betrokken bestanden:

- `src/pensioen/ui/pagina_accountant.py`
- nieuwe of aangepaste detailassembler

Acceptatiecriteria:

- accountantbusinesslogica zit niet meer primair in de UI-laag

### Issue 6

Titel:

`Laat accountantspagina alleen engine-detailoutput consumeren`

Scope:

- UI wordt pure view op detailoutput

Acceptatiecriteria:

- accountantspagina bevat geen zelfstandige fiscale herberekening meer

## Epic 4-D — Vergelijking oud versus nieuw accountantpad

### Issue 7

Titel:

`Voeg vergelijkingstests toe tussen oude accountant-output en nieuwe detailoutput`

Scope:

- representatieve scenario’s
- partnercases
- box 3- en woningeffecten

Betrokken tests:

- `tests/test_regression_bugs.py`
- `tests/testcase_validatie.py`
- eventueel aparte vergelijkingstestmodule

Acceptatiecriteria:

- overgang van oud naar nieuw accountantpad is regressiebewaakt

### Issue 8

Titel:

`Classificeer verschillen tussen oude en nieuwe accountantoutput`

Scope:

- echte bug
- oude migratieschuld
- contractueel gewijzigd gedrag

Acceptatiecriteria:

- verschillen zijn expliciet verklaard en niet stil weggewerkt

## Epic 4-E — Rapportage en validatieaansluiting

### Issue 9

Titel:

`Controleer hergebruik van detailoutput in rapportage`

Scope:

- kijk welke detailvelden direct door rapportage hergebruikt kunnen worden

Betrokken bestanden:

- `src/pensioen/reports/rapport_engine.py`

Acceptatiecriteria:

- rapportage kan de centrale detailoutput consumeren of gericht voorbereiden op consumptie

### Issue 10

Titel:

`Controleer hergebruik van detailoutput in validatiepaden`

Scope:

- vergelijkers, adapters en testcase-validatie aansluiten op centrale detailoutput

Betrokken bestanden:

- `validatie/*`
- `tests/testcase_validatie.py`

Acceptatiecriteria:

- validatie hoeft detaillogica niet zelfstandig opnieuw op te bouwen

## Epic 4-F — Integratiepoort

### Issue 11

Titel:

`Verifieer dat Epic 4 geen nieuwe presentation-side rekensporen introduceert`

Scope:

- controle op Streamlit, rapportage en andere detailconsumenten

Acceptatiecriteria:

- Epic 4 vermindert dubbele rekenpaden aantoonbaar

## Afhankelijkheden tussen issues

| Issue | Blokkeert |
| --- | --- |
| 1, 2 | 3, 4 |
| 3, 4 | 5, 6, 7 |
| 5, 6 | 7, 8 |
| 7, 8 | 9, 10 |
| 9, 10 | 11 |

## Definition of Done voor Epic 4 als geheel

Epic 4 is klaar als:

1. issues 1 tot en met 11 afgerond zijn
2. detailoutput formeel gecontracteerd is
3. accountantdetail door de engine geleverd wordt
4. accountantspagina geen primaire fiscale businesslogica meer bevat
5. regressietests de overgang van oud naar nieuw accountantpad bewaken
6. rapportage en validatie centrale detailoutput kunnen hergebruiken

## Samenvatting

Deze backlog maakt van Epic 4 een serie kleine stappen om accountantdetail uit
de UI te halen en terug te brengen naar waar het hoort: de rekenengine.
