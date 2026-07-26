---
archived: true
post_title: "Epic 2 Issues Backlog"
author1: "GitHub Copilot"
post_slug: "epic-2-issues-backlog"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "epic-2"
  - "backlog"
  - "issues"
ai_note: "AI-assisted backlog structuring based on the approved Epic 2 work package; no application code was modified."
summary: "Concrete issue-level backlog for Epic 2 with small implementation slices, dependencies, and acceptance criteria for pension source harmonization and gross-income modeling."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel

Deze backlog vertaalt Epic 2 naar kleine, uitvoerbare issues.

## Status

**Epicstatus: 🟡 IMPLEMENTATIE AFGEROND — GO/NO-GO-VALIDATIE OPEN**

Alle issues 1 tot en met 13 zijn geïmplementeerd. De pensioenbronketen is
gericht gevalideerd met 56 geslaagde parser-, cashflow- en pensioentests plus
de afzonderlijke accountantvergelijkingstest.

De bredere regressiepoort is nog niet groen door reeds bestaande fiscale
referentieverschillen buiten de Epic 2-berekenstap. De volledige testset heeft
vier fouten:

- `test_api_berekeningen_regressie_genormaliseerde_cases[tc_2025_006]`
- `test_api_berekeningen_regressie_genormaliseerde_cases[tc_2025_010]`
- `test_validatie_tc010_is_intern_consistent_na_rebaseline`
- `test_validatie_tc008_heffingskortingen_sluiten_aan_op_verwachting`

Epic 2 kan definitief op `✅ AFGEROND` zodra deze fiscale referentiecases
inhoudelijk zijn gevalideerd of bewust opnieuw zijn gebaselined. Het actuele
`validatie_rapport_ib2025.md` bevat daarnaast twee `WARN`- en vier
`FAIL`-huishoudresultaten; deze fiscale verschillen moeten afzonderlijk van de
pensioenbronharmonisatie worden beoordeeld.

Epic 2 draait om twee functionele uitkomsten:

- één leidende pensioenbron
- één expliciete bruto-inkomensopbouw

## Volgorde

De aanbevolen uitvoervolgorde is:

1. bronkeuze en contract
2. transformatielaag expliciteren
3. bruto-inkomen modelleren
4. hoofdpad en accountantpad uitlijnen
5. regressie- en vergelijkingstests toevoegen

## Epic 2-A — Bronkeuze en contract

### Issue 1

Status: `✅ AFGEROND`

Titel:

`Leg leidende pensioenbron formeel vast`

Scope:

- kies formeel tussen recordlaag, componentlaag of expliciete transformatielaag
- leg de keuze vast in het masterplan of aanvullend contractdocument

Acceptatiecriteria:

- de pensioenbronkeuze is expliciet en niet meer impliciet verspreid over code

### Issue 2

Status: `✅ AFGEROND`

Titel:

`Leg contract vast voor pensioenbron-transformatie`

Scope:

- definieer wat ruwe pensioeninvoer is
- definieer wat de rekenbron is
- definieer wanneer transformatie plaatsvindt

Acceptatiecriteria:

- ruwe import en rekenbron zijn functioneel van elkaar onderscheiden

## Epic 2-B — Transformatielaag expliciteren

### Issue 3

Status: `✅ AFGEROND`

Titel:

`Maak record-naar-componenttransformatie expliciet in parser/importpad`

Scope:

- formaliseer de huidige omzetting van `PensioenRecord` naar
  `FinancieelComponent`

Betrokken bestanden:

- `src/pensioen/parsers/parser_mpo.py`
- `src/pensioen/ui/pagina_import.py`

Acceptatiecriteria:

- er bestaat een expliciete en herbruikbare transformatielaag voor pensioen

### Issue 4

Status: `✅ AFGEROND`

Titel:

`Voorkom impliciete pensioenbronwissel in importflow`

Scope:

- maak duidelijk waar de applicatie van ruwe records naar rekenbron overgaat
- verwijder verborgen of dubbelzinnige stappen in die overgang

Acceptatiecriteria:

- de importflow kent precies één functionele overgang naar de rekenbron

## Epic 2-C — Bruto inkomen expliciet maken

### Issue 5

Status: `✅ AFGEROND`

Titel:

`Definieer DTO of outputstructuur voor bruto inkomen per persoon`

Scope:

- arbeid bruto P1/P2
- AOW bruto P1/P2
- pensioen bruto P1/P2
- overig bruto P1/P2
- totaal bruto P1/P2 en huishouden

Betrokken bestanden:

- `src/pensioen/models/cashflow.py`
- `src/pensioen/calculations/cashflow_engine.py`

Acceptatiecriteria:

- bruto inkomen is als expliciete tussenoutput beschikbaar

### Issue 6

Status: `✅ AFGEROND`

Titel:

`Laat hoofdengine bruto-inkomensopbouw expliciet vullen`

Scope:

- zorg dat de engine de bruto-opbouw vanuit dezelfde formele structuur
  opbouwt in plaats van alleen impliciete jaarsommen te gebruiken

Acceptatiecriteria:

- bruto inkomen is niet langer alleen afleidbaar, maar direct uitleesbaar

## Epic 2-D — Hoofdpad en accountantpad uitlijnen

### Issue 7

Status: `✅ AFGEROND`

Titel:

`Laat accountantpad dezelfde pensioenbron consumeren als hoofdengine`

Scope:

- vervang afwijkende pensioenbronlogica in accountantpad door gedeelde bron of
  gedeelde transformatielaag

Betrokken bestanden:

- `src/pensioen/ui/pagina_accountant.py`
- `src/pensioen/calculations/cashflow_engine.py`
- eventuele gedeelde helper/service

Acceptatiecriteria:

- bij identieke invoer ontstaat identieke pensioenopbouw in beide paden

### Issue 8

Status: `✅ AFGEROND`

Titel:

`Maak bruto-inkomen vergelijkingstest tussen hoofdengine en accountantpad`

Scope:

- bewijs dat de bruto-opbouw in beide paden exact overeenkomt voor
  representatieve scenario’s

Acceptatiecriteria:

- brute pensioen-, AOW-, arbeids- en overige inkomensopbouw matcht tussen beide paden

## Epic 2-E — Test- en regressielaag

### Issue 9

Status: `✅ AFGEROND`

Titel:

`Voeg directe tests toe voor pensioenbronketen`

Scope:

- één pensioenbron P1
- meerdere pensioenbronnen P1
- pensioen P1 en P2
- partner- en nabestaandenpensioen niet als regulier inkomen

Betrokken tests:

- `tests/test_cashflow_engine.py`
- `tests/test_pensioen_engine.py`
- eventueel nieuwe contracttestmodule

Acceptatiecriteria:

- de gekozen pensioenbronketen is regressiebewaakt

### Issue 10

Status: `✅ AFGEROND`

Titel:

`Voeg tests toe voor MPO-import naar formele rekenbron`

Scope:

- test de overgang van importdata naar gekozen rekenbron

Betrokken tests:

- `tests/test_parser_mpo.py`
- eventueel nieuwe transformatietestmodule

Acceptatiecriteria:

- importtransformatie is functioneel bewezen en niet alleen handmatig verondersteld

### Issue 11

Status: `✅ AFGEROND`

Titel:

`Voeg regressietests toe voor gelijkheid hoofdengine en accountantpad op pensioenopbouw`

Scope:

- gebruik representatieve scenario’s en partnercases

Betrokken tests:

- `tests/test_regression_bugs.py`
- eventueel aparte vergelijkingstestmodule

Acceptatiecriteria:

- afwijkende pensioenopbouw tussen paden veroorzaakt direct een testfout

## Epic 2-F — Integratiepoort

### Issue 12

Status: `✅ AFGEROND`

Titel:

`Verifieer dat bruto-inkomen DTO geen fiscale detailstap vervuilt`

Scope:

- controleer dat bruto-inkomen alleen inkomensopbouw bevat en nog geen box 1- of
  eigen-woningdetail

Acceptatiecriteria:

- de tussenstap bruto inkomen blijft functioneel zuiver

### Issue 13

Status: `✅ AFGEROND`

Titel:

`Leg resterende migratieschuld in accountantpad expliciet vast`

Scope:

- alles wat na Epic 2 nog niet gelijkgetrokken is, moet als migratieschuld
  benoemd blijven

Acceptatiecriteria:

- geen verborgen restafwijkingen in het pensioenpad

Vastgelegde migratieschuld:

- `records1` en `records2` blijven parameters van `bereken_huishouden()` voor
  achterwaartse compatibiliteit, maar zijn niet inhoudelijk leidend
- `bereken_pensioen_maand()` blijft beschikbaar voor directe legacytests; de
  huishoudengine en accountantoutput roepen deze functie niet aan

## Afhankelijkheden tussen issues

| Issue | Blokkeert |
| --- | --- |
| 1 | 3, 4, 5, 7 |
| 2 | 3, 4 |
| 3, 4 | 7, 10 |
| 5 | 6, 8, 12 |
| 6, 7 | 8, 9, 11 |
| 8, 9, 10, 11, 12 | 13 |

## Definition of Done voor Epic 2 als geheel

Epic 2 is klaar als:

1. issues 1 tot en met 13 afgerond zijn
2. de leidende pensioenbron expliciet gekozen en vastgelegd is
3. de transformatielaag expliciet en testbaar is
4. bruto inkomen als tussenstap expliciet bestaat
5. hoofdengine en accountantpad dezelfde pensioenopbouw gebruiken
6. regressietests die gelijkheid bewaken aanwezig zijn

## Samenvatting

Deze backlog maakt van Epic 2 een serie kleine stappen rond één functionele
beslissing: welke pensioenbron werkelijk leidend is en hoe die zonder ambiguïteit
in bruto inkomen doorwerkt.
