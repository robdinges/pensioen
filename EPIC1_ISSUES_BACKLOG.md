---
post_title: "Epic 1 Issues Backlog"
author1: "GitHub Copilot"
post_slug: "epic-1-issues-backlog"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "epic-1"
  - "backlog"
  - "issues"
ai_note: "AI-assisted backlog structuring based on the approved execution plan; no application code was modified."
summary: "Concrete issue-level backlog for Epic 1 with small implementation slices, dependencies, and acceptance criteria per task group."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel

Deze backlog vertaalt Epic 1 naar kleine, uitvoerbare issues.

De issues zijn bewust klein gehouden, zodat:

- iedere wijziging één fiscale bouwsteen raakt
- tests per stap beheersbaar blijven
- regressies snel terug te leiden zijn

## Volgorde

De aanbevolen uitvoervolgorde is:

1. contract en testbasis
2. premies
3. losse heffingskortingen
4. totaalkorting
5. contractvalidatie tegen bestaande integraties

## Epic 1-A — Contractbasis fiscale bouwstenen

### Issue 1

Titel:

`Leg functioneel contract vast voor premieberekening`

Scope:

- beschrijf invoer, grondslag, afronding en output van
  `bereken_premies_volksverzekeringen()`

Bestanden:

- `src/pensioen/tax/belasting_engine.py`
- eventueel begeleidende documentatie

Acceptatiecriteria:

- premiegrondslag is expliciet gedefinieerd
- AOW-volledig-jaar gedrag is expliciet gedefinieerd
- afrondingsmoment per premiecomponent is expliciet

### Issue 2

Titel:

`Leg functioneel contract vast voor losse heffingskortingen`

Scope:

- beschrijf invoer, grondslag, afbouw en afronding van:
  - `bereken_ahk()`
  - `bereken_ahk_met_aow()`
  - `bereken_arbeidskorting()`
  - `bereken_ouderenkorting()`
  - `bereken_alleenstaandeouderenkorting()`

Bestanden:

- `src/pensioen/tax/heffingskorting.py`

Acceptatiecriteria:

- per functie is duidelijk welke grondslag gebruikt wordt
- per functie is duidelijk waar minimum of vloer ingrijpt
- voor AHK met AOW is duidelijk dat de factor op het maximum werkt

### Issue 3

Titel:

`Leg functioneel contract vast voor totale heffingskorting`

Scope:

- definieer `bereken_totale_heffingskortingen()` als optelsom van de losse
  functies inclusief afrondingsvolgorde

Bestanden:

- `src/pensioen/tax/heffingskorting.py`

Acceptatiecriteria:

- totale korting is formeel beschreven als som van afgeronde componenten

## Epic 1-B — Premieberekening direct testen

### Issue 4

Titel:

`Voeg directe unit-tests toe voor bereken_premies_volksverzekeringen basisgevallen`

Scope:

- geen premiesconfig
- inkomen onder premiegrens
- inkomen exact op premiegrens
- inkomen boven premiegrens

Bestanden:

- `tests/test_belasting_engine.py` of aparte testmodule

Acceptatiecriteria:

- elk basisgeval heeft een directe test
- geen afhankelijkheid van `netto_uit_bruto()` voor verificatie

### Issue 5

Titel:

`Voeg directe unit-tests toe voor AOW-effect in premieberekening`

Scope:

- niet-AOW-gerechtigd
- volledig AOW-gerechtigd
- controle dat alleen AOW-premie wegvalt en Anw/Wlz blijven gelden

Bestanden:

- `tests/test_belasting_engine.py` of aparte testmodule

Acceptatiecriteria:

- AOW-premieverschil is expliciet bewezen met directe asserts

### Issue 6

Titel:

`Voeg directe afrondingstests toe voor premieberekening`

Scope:

- randgevallen met centafronding per premiecomponent

Acceptatiecriteria:

- afronding op componentniveau is expliciet getest

## Epic 1-C — Losse heffingskortingen direct testen

### Issue 7

Titel:

`Voeg directe unit-tests toe voor bereken_ahk grenswaarden`

Scope:

- onder afbouwgrens
- exact op afbouwgrens
- boven afbouwgrens
- minimum bereikt

Acceptatiecriteria:

- AHK-gedrag is zonder integratielaag bewezen

### Issue 8

Titel:

`Voeg directe unit-tests toe voor bereken_arbeidskorting grenswaarden`

Scope:

- nul arbeidsinkomen
- laag arbeidsinkomen
- afbouw boven drempel
- minimumvloer

Acceptatiecriteria:

- arbeidskorting heeft directe dekking op de kritieke overgangen

### Issue 9

Titel:

`Voeg directe unit-tests toe voor bereken_ouderenkorting grenswaarden`

Scope:

- zonder AOW
- met AOW onder afbouwgrens
- met AOW boven afbouwgrens
- minimumvloer

Acceptatiecriteria:

- ouderenkorting is direct afgedekt zonder `netto_uit_bruto()`

### Issue 10

Titel:

`Voeg directe unit-tests toe voor bereken_alleenstaandeouderenkorting`

Scope:

- niet-AOW
- niet alleenstaand
- geen AOK-config
- geldig AOW + alleenstaand
- jaarafhankelijk afbouwgedrag

Acceptatiecriteria:

- AOK is direct afgedekt in zowel nul- als positieve scenario’s

## Epic 1-D — Totale heffingskorting direct testen

### Issue 11

Titel:

`Voeg directe unit-tests toe voor bereken_totale_heffingskortingen basisscenario's`

Scope:

- geen arbeid, geen AOW
- arbeid zonder AOW
- AOW zonder arbeid
- alleenstaand AOW-geval met AOK

Acceptatiecriteria:

- totale korting is direct getest in representatieve functionele scenario’s

### Issue 12

Titel:

`Voeg contracttest toe dat totale korting exact som is van losse kortingcomponenten`

Scope:

- vergelijk expliciet losse functies met `bereken_totale_heffingskortingen()`

Acceptatiecriteria:

- de totale korting is aantoonbaar gelijk aan de som van de losse afgeronde
  componenten

## Epic 1-E — Integratiebehoud en regressiepoort

### Issue 13

Titel:

`Verifieer aansluiting van nieuwe directe tests op netto_uit_bruto`

Scope:

- controleer dat bestaande tests op `netto_uit_bruto()` logisch blijven
- leg afwijkingen vast als contractverschil, niet als impliciet gedrag

Acceptatiecriteria:

- geen onverwachte semantische drift tussen losse bouwstenen en
  `netto_uit_bruto()`

### Issue 14

Titel:

`Verifieer aansluiting van Epic 1 op validatie_aangifte_2025`

Scope:

- controleer dat de 2025-validatie nog past bij de nieuwe expliciete contracten

Acceptatiecriteria:

- verschillen zijn expliciet verklaard of afwezig

### Issue 15

Titel:

`Leg bekende afwijking accountant AHK-special case expliciet vast`

Scope:

- documenteer dat accountantpad nog afwijkende AHK-logica kent voor
  alleenstaande AOW-situaties

Acceptatiecriteria:

- deze afwijking is niet langer impliciete kennis

### Issue 16

Titel:

`Valideer begrenzing van verrekenbare heffingskortingen op verschuldigde IB en premies`

Status:

`AFGEROND - fiscaal gevalideerd voor de ondersteunde individuele verrekening`

Huidige implementatie:

- de engine berekent eerst de totale heffingskortingen
- de daadwerkelijk verrekende korting is begrensd op de verschuldigde
  inkomstenbelasting plus premies volksverzekeringen
- een eventueel restant verlaagt de verschuldigde belasting niet verder dan nul
  en wordt als niet-benutte heffingskorting in accountantdetail getoond

Open controlevraag:

- klopt deze generieke begrenzing voor iedere ondersteunde korting, in het
  bijzonder AHK, arbeidskorting, ouderenkorting en alleenstaandeouderenkorting?
- zijn er uitzonderingen, overdrachtsregels of uitbetalingsregels die per
  belastingjaar of huishoudsituatie afzonderlijk gemodelleerd moeten worden?

Validatie-uitkomst:

- voor 2025 en 2026 worden AHK, arbeidskorting, ouderenkorting en
  alleenstaandeouderenkorting verrekend met de verschuldigde inkomstenbelasting
  en premies volksverzekeringen; het individuele saldo wordt niet negatief
- niet-benutte arbeidskorting wordt vanaf 2023 niet meer uitbetaald
- niet-benutte ouderenkorting en alleenstaandeouderenkorting kennen binnen de
  ondersteunde individuele berekening geen afzonderlijke uitbetalingsregel
- uitzondering: niet-benutte algemene heffingskorting kan in 2025 en 2026 onder
  voorwaarden worden uitbetaald aan een minstverdienende fiscale partner die
  vóór 1963 is geboren; deze huishoudelijke partneroverdracht wordt nog niet
  gemodelleerd en blijft expliciete migratieschuld
- de centrale begrenzing staat in
  `belasting_engine.begrens_verrekenbare_heffingskorting()` en wordt door
  hoofdengine en accountantdetail gebruikt

Gezaghebbende bronnen:

- Belastingdienst, Fiscale informatie 2025, hoofdstuk 21:
  `https://www.belastingdienst.nl/wps/wcm/connect/fisin/fisin2025/heffingskortingen`
- Belastingdienst, Fiscale informatie 2026, hoofdstuk 21:
  `https://www.belastingdienst.nl/wps/wcm/connect/fisin/fisin2026/heffingskortingen`
- Belastingdienst, Heffingskortingen laten uitbetalen:
  `https://www.belastingdienst.nl/wps/wcm/connect/nl/aftrek-en-kortingen/content/heffingskortingen-laten-uitbetalen`

Betrokken bestanden:

- `src/pensioen/tax/belasting_engine.py`
- `src/pensioen/calculations/cashflow_engine.py`
- `src/pensioen/calculations/detail_output_engine.py`
- `frontend-react/src/components/AccountantSection.jsx`

Acceptatiecriteria:

- fiscale regel is geverifieerd tegen een gezaghebbende bron per ondersteund jaar
- per korting is expliciet vastgelegd of een niet-benut bedrag vervalt, wordt
  uitbetaald of op andere wijze kan worden verrekend
- directe tests dekken minimaal: korting lager dan, gelijk aan en hoger dan de
  verschuldigde IB plus premies
- accountantdetail toont berekend, daadwerkelijk verrekend en niet-benut bedrag
- de uitzondering voor partneruitbetaling is als niet-ondersteunde
  huishoudregel vastgelegd en mag niet stilzwijgend als individueel
  verrekeningssaldo worden behandeld

## Afhankelijkheden tussen issues

| Issue | Blokkeert |
| --- | --- |
| 1 | 4, 5, 6 |
| 2 | 7, 8, 9, 10 |
| 3 | 11, 12 |
| 4, 5, 6 | 13 |
| 7, 8, 9, 10, 11, 12 | 13 |
| 13 | 14 |
| 14, 15, 16 | Epic 1 afronding |

## Definition of Done voor Epic 1 als geheel

Epic 1 is klaar als:

1. issues 1 tot en met 16 afgerond zijn
2. alle losse fiscale bouwstenen directe unitdekking hebben
3. grondslagen en afronding expliciet vastliggen
4. bestaande integratietests en validaties nog aansluiten op de contracten
5. bekende accountantafwijkingen expliciet gedocumenteerd zijn

## Samenvatting

Deze backlog maakt van Epic 1 een serie kleine, herleidbare stappen.

Dat is precies het doel van de nieuwe werkwijze:

- niet één grote refactor
- maar kleine veranderingen per berekenbouwsteen
- met directe tests, heldere contracten en expliciete beslismomenten
