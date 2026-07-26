---
archived: true
post_title: "Epic 1 Implementatievolgorde Per Testbestand"
author1: "GitHub Copilot"
post_slug: "epic-1-implementatievolgorde-per-testbestand"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "epic-1"
  - "tests"
  - "implementation-order"
ai_note: "AI-assisted implementation sequencing based on the approved Epic 1 backlog; no application code was modified."
summary: "Praktische implementatievolgorde voor Epic 1, geordend per testbestand en testgroep, zodat uitvoering direct kan starten met kleine, beheersbare slices."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel

Dit document vertaalt Epic 1 naar een concrete uitvoervolgorde per testbestand.

De bedoeling is dat een ontwikkelaar direct kan beginnen zonder opnieuw te
hoeven bepalen:

- in welk bestand eerst gewerkt moet worden
- welke testgroep eerst logisch is
- welke volgorde het minste regressierisico geeft

## Functionele stap

Primary step:

- `Heffingskortingen`

Dependent step:

- `Box 1`

Current source of truth:

- `src/pensioen/tax/heffingskorting.py`
- `src/pensioen/tax/belasting_engine.py` voor premies en consumering via
  `netto_uit_bruto()`

Parallelle paden:

- accountantpad gebruikt nog eigen kortingopbouw en speciale AHK-afwijking

Smallest safe slice:

- eerst directe tests toevoegen voor losse bouwstenen
- pas daarna integratie-aansluiting controleren

## Hoofdregel voor uitvoering

Werk in deze volgorde:

1. bestaande testfile uitbreiden waar dat logisch kan
2. alleen een nieuw testbestand maken als de bestaande file te breed of te
   onoverzichtelijk wordt
3. pas na directe tests controleren of bestaande integratie- en validatietests
   nog inhoudelijk aansluiten

## Aanbevolen bestandsstrategie

### Voorkeursvariant

Gebruik twee testbestanden:

1. `tests/test_belasting_engine.py`
2. nieuw: `tests/test_heffingskorting.py`

Waarom:

- premies horen inhoudelijk dichter bij `belasting_engine.py`
- losse kortingfuncties verdienen een eigen, scherp bestand
- `test_belasting_engine.py` blijft dan leesbaar

### Acceptabele minimale variant

Alles in `tests/test_belasting_engine.py`.

Nadeel:

- de fiscale bouwstenen blijven dan minder zichtbaar als zelfstandige eenheden

## Implementatievolgorde per bestand

### Fase 1 — `tests/test_belasting_engine.py`

#### Groep 1A

Voeg directe tests toe voor `bereken_premies_volksverzekeringen()`:

1. geen premiesconfig
2. inkomen onder premiegrens
3. inkomen exact op premiegrens
4. inkomen boven premiegrens

Reden voor deze volgorde:

- dit fixeert eerst de grondslagdefinitie
- daarna pas het AOW-verschil

#### Groep 1B

Voeg aanvullende premietests toe voor AOW-gedrag:

1. niet-AOW-gerechtigd
2. volledig AOW-gerechtigd
3. Anw en Wlz blijven gelden

#### Groep 1C

Voeg afrondingstests toe voor premies:

1. AOW-premie afronding
2. Anw-premie afronding
3. Wlz-premie afronding
4. totaalsom van afgeronde componenten

#### Stopcriterium Fase 1

Ga pas verder als:

- premiefunctie volledig direct gedekt is
- bestaande tests in `tests/test_belasting_engine.py` nog logisch aansluiten

### Fase 2 — nieuw `tests/test_heffingskorting.py`

#### Groep 2A

Voeg directe tests toe voor `bereken_ahk()`:

1. onder afbouwgrens
2. exact op afbouwgrens
3. boven afbouwgrens
4. minimum bereikt

#### Groep 2B

Voeg directe tests toe voor `bereken_ahk_met_aow()` aanvullend op bestaande dekking:

1. AOW-breuk = 0
2. AOW-breuk = 1
3. deeljaar AOW
4. factor werkt op maximum, niet op al-afgebouwde uitkomst

#### Groep 2C

Voeg directe tests toe voor `bereken_arbeidskorting()`:

1. geen arbeidsinkomen
2. laag arbeidsinkomen
3. rond maximumlogica
4. boven afbouwdrempel
5. minimumvloer

#### Groep 2D

Voeg directe tests toe voor `bereken_ouderenkorting()`:

1. geen AOW
2. wel AOW onder afbouwgrens
3. boven afbouwgrens
4. minimumvloer

#### Groep 2E

Voeg directe tests toe voor `bereken_alleenstaandeouderenkorting()`:

1. geen AOW
2. niet alleenstaand
3. geen config
4. geldig AOW + alleenstaand
5. jaarafhankelijk afbouwgedrag

#### Groep 2F

Voeg directe tests toe voor `bereken_totale_heffingskortingen()`:

1. geen arbeid, geen AOW
2. arbeid zonder AOW
3. AOW zonder arbeid
4. alleenstaand AOW met AOK
5. deeljaar AOW
6. som van losse afgeronde componenten is exact gelijk

#### Stopcriterium Fase 2

Ga pas verder als:

- alle losse kortingfuncties directe unitdekking hebben
- `bereken_totale_heffingskortingen()` contractueel is vastgezet

### Fase 3 — Terug naar `tests/test_belasting_engine.py`

#### Groep 3A

Voeg aansluitingschecks toe tussen bouwstenen en `netto_uit_bruto()`:

1. netto = bruto - max(0, IB + premies - kortingen)
2. gebruikte grondslagen in metadata blijven logisch
3. premies en kortingen sluiten aan op losse functies

#### Groep 3B

Voeg expliciete regressiechecks toe als de nieuwe directe tests ambiguïteit in
de bestaande implementatie blootleggen.

#### Stopcriterium Fase 3

- `netto_uit_bruto()` blijft inhoudelijk consistent met de losse bouwstenen

### Fase 4 — `tests/validatie_aangifte_2025.py`

#### Groep 4A

Controleer of de directe contracten botsen met de validatie-aanname van 2025.

#### Groep 4B

Leg afwijkingen expliciet vast als:

- contractkeuze
- bekende afwijking
- toekomstige migratieschuld

#### Stopcriterium Fase 4

- de 2025-validatie is nog bruikbaar of expliciet opnieuw geduid

## Volgorde van uitvoeren in de praktijk

```text
1. tests/test_belasting_engine.py      premies basis
2. tests/test_belasting_engine.py      premies AOW + afronding
3. tests/test_heffingskorting.py       AHK
4. tests/test_heffingskorting.py       AHK met AOW
5. tests/test_heffingskorting.py       arbeidskorting
6. tests/test_heffingskorting.py       ouderenkorting
7. tests/test_heffingskorting.py       alleenstaandeouderenkorting
8. tests/test_heffingskorting.py       totale heffingskortingen
9. tests/test_belasting_engine.py      aansluiting netto_uit_bruto
10. tests/validatie_aangifte_2025.py   validatiepoort
```

## Wat nog niet in Epic 1 hoort

Niet nu doen:

- accountantlogica aanpassen
- eigen woning in hoofdengine trekken
- pensioenbron harmoniseren
- detail-DTO’s bouwen voor accountant

Dat zijn vervolgstappen uit Epic 2, 3 en 4.

## Definitie van gereed

Epic 1 is praktisch klaar als:

1. `tests/test_belasting_engine.py` directe premiedekking bevat
2. `tests/test_heffingskorting.py` alle losse kortingfuncties direct dekt
3. `netto_uit_bruto()` aantoonbaar aansluit op de losse bouwstenen
4. `tests/validatie_aangifte_2025.py` nog past of expliciet opnieuw is geduid

## Samenvatting

De veiligste manier om Epic 1 uit te voeren is niet per module in abstracte zin,
maar per testbestand en per testgroep. Daarmee ontstaat de kleinste,
controleerbare werkvolgorde voor de eerste herstructureringsfase.
