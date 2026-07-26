---
archived: true
post_title: "Epic 1 Werkpakket Fiscale Bouwstenen"
author1: "GitHub Copilot"
post_slug: "epic-1-werkpakket-fiscale-bouwstenen"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "epic-1"
  - "tests"
  - "tax"
ai_note: "AI-assisted implementation planning based on the analysis documents; no application code was modified."
summary: "Concreet uitvoerbaar werkpakket voor Epic 1: fiscale bouwstenen isoleren, inclusief testtaken, verwachte code-impact, risico’s en acceptatiecriteria."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel

Dit document werkt alleen **Epic 1** uit:

```text
Fiscale bouwstenen isoleren
```

Het doel van Epic 1 is niet om de hele engine te verbouwen, maar om de losse
fiscale bouwstenen:

- expliciet te maken
- direct testbaar te maken
- functioneel te contracteren
- veilig te maken als basis voor latere harmonisatie

Epic 1 is daarmee de eerste echte implementatiefase na de analyse.

**Status: ✅ AFGEROND (26 juli 2026).** De actuele status per issue en de
verificatie-uitkomst staan in `EPIC1_ISSUES_BACKLOG.md`.

## Scope

Epic 1 omvat alleen de volgende functies:

- `bereken_premies_volksverzekeringen()`
- `bereken_ahk()`
- `bereken_ahk_met_aow()`
- `bereken_arbeidskorting()`
- `bereken_ouderenkorting()`
- `bereken_alleenstaandeouderenkorting()`
- `bereken_totale_heffingskortingen()`

Epic 1 omvat niet:

- pensioenharmonisatie
- eigen woning in de hoofdengine
- accountant-engine
- UI- of API-ontkoppeling
- migratie van legacy vermogen

## Waarom deze epic eerst komt

Uit de analyse blijkt dat juist deze bouwstenen nog niet sterk genoeg als
zelfstandige rekenelementen zijn vastgezet.

De situatie nu is:

- `bereken_box1_belasting()` is redelijk direct getest
- `netto_uit_bruto()` is redelijk direct getest
- maar de onderliggende premie- en kortingfuncties zijn grotendeels slechts
  indirect afgedekt

Daardoor geldt nu:

```text
een fout in een korting- of premiefunctie
    -> wordt vaak pas zichtbaar via grotere integratietests
    -> is moeilijker te herleiden
    -> vergroot regressierisico bij latere herstructurering
```

## Huidige dekking en gaten

### Redelijk aanwezig

- `bereken_ahk_met_aow()`
  - via `test_ahk_aow_heel_jaar_gebruikt_factor_op_maximum`
  - via `test_ahk_aow_deeljaar_gebruikt_gewogen_maximum`

### Ontbrekend als directe unitdekking

- `bereken_premies_volksverzekeringen()`
- `bereken_ahk()`
- `bereken_arbeidskorting()`
- `bereken_ouderenkorting()`
- `bereken_alleenstaandeouderenkorting()`
- `bereken_totale_heffingskortingen()`

## Gewenst eindresultaat van Epic 1

Na afronding van Epic 1 moet gelden:

1. iedere losse fiscale bouwsteen heeft directe unit-tests
2. iedere bouwsteen heeft een expliciete functionele contractbeschrijving
3. afrondingsregels zijn per bouwsteen expliciet vastgelegd
4. grondslagen per bouwsteen zijn expliciet vastgelegd
5. latere refactors in box 1 kunnen veilig starten zonder black-box onzekerheid

## Werkpakket

### Werkstroom 1 — Functionele contracten vastleggen

#### Taak 1.1

Beschrijf per functie formeel:

- doel
- invoer
- grondslag
- afrondingsmoment
- output
- randgevallen

#### Betrokken code werkstroom 2

- `src/pensioen/tax/belasting_engine.py`
- `src/pensioen/tax/heffingskorting.py`

#### Verwachte code-impact werkstroom 2

- geen functionele wijziging vereist
- mogelijk alleen verduidelijking van docstrings of aanvullende documentatie

#### Acceptatiecriterium werkstroom 2

- voor alle Epic 1-functies is de functionele contractdefinitie expliciet

### Werkstroom 2 — Premiefunctie direct testen

#### Taak 2.1

Maak een directe testset voor `bereken_premies_volksverzekeringen()`.

#### Verplichte testgevallen taak 3.1

1. geen premiesconfig aanwezig
2. inkomen onder premiegrens
3. inkomen exact op premiegrens
4. inkomen boven premiegrens
5. niet-AOW-gerechtigd: AOW-premie actief
6. volledig AOW-gerechtigd: AOW-premie nul
7. Anw en Wlz altijd actief binnen premiegrondslag
8. afronding op centen

#### Betrokken code

- nieuwe tests in `tests/test_belasting_engine.py` of aparte gerichte testmodule
- functie in `src/pensioen/tax/belasting_engine.py`

#### Verwachte code-impact

- primair testcode
- mogelijk kleine verduidelijking als gedrag ambigu blijkt

#### Acceptatiecriterium

- alle genoemde scenario’s zijn met directe asserts afgedekt

### Werkstroom 3 — Losse kortingfuncties direct testen

#### Taak 3.1

Maak directe tests voor `bereken_ahk()`.

#### Verplichte testgevallen taak 3.2

1. inkomen onder afbouwgrens
2. inkomen exact op afbouwgrens
3. inkomen boven afbouwgrens
4. inkomen zo hoog dat minimum bereikt wordt

#### Taak 3.2

Maak directe tests voor `bereken_arbeidskorting()`.

#### Verplichte testgevallen taak 3.3

1. geen arbeidsinkomen
2. laag arbeidsinkomen
3. arbeidsinkomen rond maximumlogica
4. afbouw boven drempel
5. minimumvloer

#### Taak 3.3

Maak directe tests voor `bereken_ouderenkorting()`.

#### Verplichte testgevallen taak 3.4

1. geen AOW-status
2. wel AOW-status onder afbouwgrens
3. boven afbouwgrens
4. minimumvloer

#### Taak 3.4

Maak directe tests voor `bereken_alleenstaandeouderenkorting()`.

#### Verplichte testgevallen

1. geen AOW-status
2. niet alleenstaand
3. config bevat geen AOK
4. geldig AOW + alleenstaand
5. afbouw of geen afbouw afhankelijk van jaarconfig

#### Betrokken code werkstroom 3

- `src/pensioen/tax/heffingskorting.py`
- tests in `tests/test_belasting_engine.py` of aparte module

#### Verwachte code-impact werkstroom 3

- vooral testcode
- mogelijk kleine functionele verduidelijking als tests onduidelijkheden blootleggen

#### Acceptatiecriterium werkstroom 3

- iedere losse kortingfunctie heeft een eigen directe testgroep met grenswaarden

### Werkstroom 4 — Totale korting direct testen

#### Taak 4.1

Maak een directe testset voor `bereken_totale_heffingskortingen()`.

#### Verplichte testgevallen werkstroom 4

1. geen arbeidsinkomen, geen AOW
2. arbeidsinkomen zonder AOW
3. AOW zonder arbeidsinkomen
4. alleenstaand AOW-geval met AOK
5. deeljaar AOW via `aow_breuk`
6. controle dat totaal exact gelijk is aan som van de losse componenten

#### Betrokken code werkstroom 4

- `src/pensioen/tax/heffingskorting.py`
- testmodule voor heffingskortingen

#### Verwachte code-impact werkstroom 4

- testcode
- mogelijk minimale correctie als inconsistenties boven water komen

#### Acceptatiecriterium werkstroom 4

- `bereken_totale_heffingskortingen()` is niet langer alleen via
  `netto_uit_bruto()` indirect gedekt

### Werkstroom 5 — Afrondings- en grondslagnotities vastleggen

#### Taak 5.1

Leg per functie vast:

- of er vóór of ná sommatie wordt afgerond
- of percentages op bruto of box1-grondslag werken
- of AOW-breuk op tarief of op maximum wordt toegepast

#### Verplichte onderdelen

- `bereken_premies_volksverzekeringen()`
- `bereken_ahk_met_aow()`
- `bereken_arbeidskorting()`
- `bereken_totale_heffingskortingen()`
- `netto_uit_bruto()` als consument van de bouwstenen

#### Verwachte code-impact werkstroom 5

- vooral documentatie en tests
- geen architectuurwijziging

#### Acceptatiecriterium werkstroom 5

- er is geen impliciete afrondings- of grondslaglogica meer in Epic 1-functies

## Aanbevolen bestandsimpact

### Verwacht aan te passen

- `tests/test_belasting_engine.py`
- optioneel nieuwe testmodule, bijvoorbeeld:
  - `tests/test_heffingskorting.py`
  - of `tests/test_premies_en_kortingen.py`
- eventueel beperkte verduidelijking in:
  - `src/pensioen/tax/heffingskorting.py`
  - `src/pensioen/tax/belasting_engine.py`

### Verwacht niet aan te passen

- `cashflow_engine.py`
- `pagina_accountant.py`
- React frontend
- API schemas en endpoints
- scenario- en vermogensmodellen

## Teststrategie

### Niveau 1: pure unit-tests

Elke Epic 1-functie krijgt directe, kleine tests met expliciete input en
verwachte output.

### Niveau 2: contracttests

Controleer dat samengestelde functies exact aansluiten op losse bouwstenen:

- `bereken_totale_heffingskortingen()` = som losse kortingen
- `netto_uit_bruto()` = bruto - max(0, IB + premies - kortingen)

### Niveau 3: bestaand regressienet behouden

Na toevoegen van directe tests blijven deze suites relevant als vangnet:

- `tests/test_belasting_engine.py`
- `tests/validatie_aangifte_2025.py`
- `tests/test_cashflow_engine.py`

## Risico’s binnen Epic 1

### Risico 1

Directe tests kunnen onduidelijkheden blootleggen in de huidige bedoelde
functionele werking.

Gevolg:

- eerst contractkeuze nodig vóór codewijziging

### Risico 2

De bestaande validatie 2025 kan impliciet op ander gedrag leunen dan nieuwe
unit-tests veronderstellen.

Gevolg:

- verschillen moeten expliciet verklaard worden, niet stil aangepast

### Risico 3

De accountantspecial case voor AHK bij alleenstaande AOW kan botsen met de
formele contracten van de losse kortingfuncties.

Gevolg:

- niet in Epic 1 oplossen, wel expliciet markeren als afwijking

## Beslispunten na Epic 1

Na afronding van Epic 1 moeten deze vragen met ja beantwoord kunnen worden:

1. Zijn alle losse fiscale bouwstenen direct testbaar?
2. Is voor elke bouwsteen duidelijk welke grondslag en afronding geldt?
3. Kunnen latere refactors in box 1 plaatsvinden zonder uitsluitend te leunen op
   integratietests?

Alleen als het antwoord op alle drie ja is, is Epic 2 veilig opstartbaar.

## Definition of Done

Epic 1 is pas gereed als:

1. `bereken_premies_volksverzekeringen()` directe unit-tests heeft
2. alle losse kortingfuncties directe unit-tests hebben
3. `bereken_totale_heffingskortingen()` directe unit-tests heeft
4. grondslagen en afrondingsmomenten expliciet zijn vastgelegd
5. bestaande regressiesuites nog groen zijn
6. bekende afwijkingen met accountantlogica expliciet zijn benoemd, niet verborgen

## Eerste concrete takenlijst

1. Voeg directe tests toe voor `bereken_premies_volksverzekeringen()`.
2. Voeg directe tests toe voor `bereken_ahk()`.
3. Voeg directe tests toe voor `bereken_arbeidskorting()`.
4. Voeg directe tests toe voor `bereken_ouderenkorting()`.
5. Voeg directe tests toe voor `bereken_alleenstaandeouderenkorting()`.
6. Voeg directe tests toe voor `bereken_totale_heffingskortingen()`.
7. Leg afrondingsregels en grondslagen per functie schriftelijk vast.
8. Verifieer daarna dat `test_belasting_engine`, `validatie_aangifte_2025` en
   relevante integratietests nog logisch aansluiten.

## Samenvatting

Epic 1 is de fase waarin de fiscale bouwstenen uit de black box worden gehaald.

Nog niet om de hele engine te herontwerpen, maar om te zorgen dat de losse
rekenstenen zelfstandig, scherp en betrouwbaar genoeg zijn om de rest van de
herstructurering op te dragen.
