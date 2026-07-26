---
post_title: "Uitvoeringsplan Herstructurering Pensioenapplicatie"
author1: "GitHub Copilot"
post_slug: "uitvoeringsplan-herstructurering-pensioenapplicatie"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "planning"
  - "refactoring"
  - "backlog"
  - "governance"
ai_note: "AI-assisted implementation planning based on prior analysis documents; no application code was modified."
summary: "Concreet uitvoeringsplan voor de herstructurering van de pensioenapplicatie met epics, volgorde, afhankelijkheden, beslispoorten en definition of done per stap."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel

Dit document vertaalt het masterplan naar een uitvoerbare veranderbacklog.

Het doel is niet om direct code te ontwerpen, maar om wijzigingen in een vaste
volgorde uit te voeren zodat:

- de rekenengine stap voor stap beheersbaar wordt
- iedere wijziging een duidelijke plaats heeft
- iedere bug terug te leiden is naar één berekenstap
- de accountantspagina uiteindelijk alleen engine-output presenteert

## Uitgangspunten

Alle wijzigingen moeten de volgende principes respecteren:

1. Rekenen gebeurt uiteindelijk alleen in de rekenengine.
2. Iedere berekenstap krijgt één source of truth.
3. Iedere berekenstap krijgt eigen tests.
4. UI, API en rapportage consumeren output; ze herberekenen niet.
5. Legacy gedrag wordt pas verwijderd nadat een nieuwe bron aantoonbaar leidend is.

## Werkvolgorde in één overzicht

```text
Epic 0  Besturingslaag en contracten
Epic 1  Fiscale bouwstenen isoleren
Epic 2  Pensioen en inkomensbronnen harmoniseren
Epic 3  Eigen woning en vermogen harmoniseren
Epic 4  Engine-detailoutput en accountant-engine
Epic 5  UI/API ontkoppeling en presentatiemigratie
Epic 6  Regressie-, validatie- en governance-verankering
Epic 7  Opschoning en doelarchitectuur consolideren
```

## Epic 0 — Besturingslaag en contracten

### Doel Epic 0

Maak de functionele berekenarchitectuur operationeel als wijzigingscontract.

### Werk Epic 0

1. Leg per berekenstap een formeel contract vast:
   invoer, output, tarieven, afhankelijkheden, tests.
2. Definieer welke huidige functie voorlopig de source of truth is.
3. Leg vast welke huidige paden afwijkend zijn.
4. Introduceer een wijzigingssjabloon voor toekomstige fiscale wijzigingen.

### Deliverables Epic 0

- berekencontracten per stap
- source-of-truth-register
- afwijkingenregister hoofdengine versus accountantpad

### Afhankelijkheden Epic 0

- geen; dit is de basis voor alle volgende epics

### Definition of Done Epic 0

- iedere stap uit de functionele berekenboom heeft een expliciete contractpagina
- voor pensioen, eigen woning, box 1, kortingen, box 3 en vermogen is benoemd
  of de source of truth al zuiver is of nog niet
- bekende dubbele paden zijn vastgelegd als migratieobjecten

## Epic 1 — Fiscale bouwstenen isoleren

**Status: ✅ AFGEROND (26 juli 2026).** Zie `EPIC1_ISSUES_BACKLOG.md` voor de
status per issue en de uitgevoerde regressiepoort.

### Doel Epic 1

Maak de pure fiscale functies volledig zelfstandig testbaar en expliciet.

### Werk Epic 1

1. Maak directe unit-tests voor:
   - `bereken_premies_volksverzekeringen()`
   - `bereken_ahk()`
   - `bereken_arbeidskorting()`
   - `bereken_ouderenkorting()`
   - `bereken_alleenstaandeouderenkorting()`
   - `bereken_totale_heffingskortingen()`
2. Leg per functie de formele invoer- en outputverwachting vast.
3. Breng expliciet in kaart welke afrondingsregels per functie gelden.

### Deliverables Epic 1

- directe unit-testset voor alle losse fiscale bouwstenen
- afrondings- en grondslagnotities per functie

### Afhankelijkheden Epic 1

- Epic 0

### Definition of Done Epic 1

- iedere fiscale bouwsteen kan los worden aangeroepen zonder UI-context
- voor iedere bouwsteen bestaat directe unitdekking
- afronding, premiegrondslag en AOW-logica zijn expliciet gedocumenteerd

## Epic 2 — Pensioen en inkomensbronnen harmoniseren

**Status: 🟡 IMPLEMENTATIE AFGEROND — GO/NO-GO-VALIDATIE OPEN.** Zie
`EPIC2_ISSUES_BACKLOG.md`.

### Doel Epic 2

Maak pensioen en bruto-inkomensopbouw eenduidig.

### Werk Epic 2

1. Kies formeel de leidende pensioenbron:
   - of `PensioenRecord`
   - of `Scenario.componenten`
   - of een vaste transformatielaag van records naar componenten
2. Maak bruto inkomen een expliciete tussenstap met vaste output per persoon.
3. Zorg dat accountantpad en hoofdengine exact dezelfde pensioenbron gebruiken.

### Deliverables Epic 2

- formele pensioenbronkeuze
- bruto-inkomen DTO per persoon en per jaar
- vergelijkingstest hoofdpad versus accountantpad voor pensioenopbouw

### Afhankelijkheden Epic 2

- Epic 0
- Epic 1

### Definition of Done Epic 2

- er bestaat nog maar één inhoudelijk leidende pensioenbron
- bruto-inkomen is als expliciete tussenstap beschikbaar
- hoofdengine en accountantdetail geven identieke pensioenopbouw bij dezelfde invoer

## Epic 3 — Eigen woning en vermogen harmoniseren

### Doel Epic 3

Breng eigen woning en vermogensgrondslagen onder één consistente bron.

### Werk Epic 3

1. Kies de leidende bron voor woning/hypotheek:
   `vermogensitems` of expliciet read model daarvan.
2. Maak eigen woning een expliciete engine-stap tussen bruto inkomen en box 1.
3. Breng legacy `spaargeld_start` en `beleggingen_start` onder migratieregime.
4. Leg vast hoe box 3-grondslag en rendementsgrondslag zich tot elkaar verhouden.

### Deliverables Epic 3

- formele woning- en vermogensbron
- eigen-woning outputstructuur in de engine
- migratieplan voor legacy vermogensvelden

### Afhankelijkheden Epic 3

- Epic 0
- Epic 1

### Definition of Done Epic 3

- eigen woning zit in de formele engine-keten
- box 1 kan inclusief woningeffect uit de engine worden afgeleid
- legacy vermogen is gemarkeerd als read-only migratielaag of uitgefaseerd

## Epic 4 — Engine-detailoutput en accountant-engine

### Doel Epic 4

Maak van de accountantlogica een afnemer van de engine in plaats van een tweede engine.

### Werk Epic 4

1. Introduceer een formele detailoutput voor:
   - bruto opbouw
   - box1-grondslagen
   - premies
   - heffingskortingen
   - box 3
   - eigen woning
   - saldo-opbouw per maand
2. Bouw een pure accountant-engine of detailassembler in de berekenlaag.
3. Vervang `_bereken_jaar_detail()` als zelfstandige businessimplementatie.

### Deliverables Epic 4

- accountantdetail DTO
- detailassembler in de core
- vergelijkingstest tussen oud accountantpad en nieuwe detailoutput

### Afhankelijkheden Epic 4

- Epic 1
- Epic 2
- Epic 3

### Definition of Done Epic 4

- accountantdetail komt uit de engine en niet uit UI-herberekening
- alle tussenresultaten zijn per jaar en waar nodig per persoon beschikbaar
- `_bereken_jaar_detail()` is gedegradeerd tot presentatielaag of verwijderd

## Epic 5 — UI/API ontkoppeling en presentatiemigratie

### Doel Epic 5

Laat UI- en API-lagen uitsluitend nog consumeren.

### Werk Epic 5

1. Laat Streamlit resultaten, accountant en rapport alleen engine-output lezen.
2. Beperk `app.py` tot orchestration, niet tot alternatieve interpretatie.
3. Minimaliseer client-side herleiding in React en `app_api_client.py`.
4. Harmoniseer requestbouw en tariefvoorbereiding waar mogelijk.

### Deliverables Epic 5

- UI-consumptielaag zonder eigen berekeningen
- aangepaste accountant- en resultatenweergave
- afgeslankte client-side aggregatie waar nodig

### Afhankelijkheden Epic 5

- Epic 4

### Definition of Done Epic 5

- geen enkel scherm rekent box 1, box 3, eigen woning of netto inkomen zelfstandig uit
- React en Streamlit presenteren dezelfde engine-definitie van output
- accountantspagina is pure view op engine-detailoutput

## Epic 6 — Regressie, validatie en governance

### Doel Epic 6

Veranker correctheid en wijzigingsdiscipline.

### Werk Epic 6

1. Organiseer tests per berekenstap.
2. Voeg vergelijkingstests toe tussen samenvatting en detailoutput.
3. Zorg dat elke gerepareerde bug resulteert in een regressietest.
4. Leg vast welke validatiecases verplicht zijn bij fiscale wijzigingen.

### Deliverables Epic 6

- testmatrix per berekenstap
- regressieprotocol
- wijzigingsprotocol voor fiscale logica

### Afhankelijkheden Epic 6

- Epic 1 tot en met 5

### Definition of Done Epic 6

- voor elke berekenstap is duidelijk welke tests exclusief daarbij horen
- bugfixes kunnen herleidbaar worden gekoppeld aan regressietests
- validatiepipeline sluit aan op de functionele berekenarchitectuur

## Epic 7 — Opschoning en doelarchitectuur consolideren

### Doel Epic 7

Ruim de tijdelijke dubbele structuren op en consolideer de uiteindelijke architectuur.

### Werk Epic 7

1. Verwijder obsolete legacy paden.
2. Verwijder ongebruikte vermogenshelpers als ze functioneel niet nodig blijken.
3. Consolideer definitieve service- en DTO-structuur.
4. Herzie UI-keuze: twee frontends blijven of consolideren.

### Deliverables Epic 7

- opgeschoonde codebasis
- definitieve doelarchitectuur
- verwijderde dubbele logica

### Afhankelijkheden Epic 7

- Epic 0 tot en met 6

### Definition of Done Epic 7

- dubbele rekenpaden zijn verdwenen
- legacy velden en shadow-logica zijn opgeruimd of expliciet gemotiveerd behouden
- doelarchitectuur volgt aantoonbaar uit de functionele berekenarchitectuur

## Beslispoorten

### Go/No-Go 1 — Na Epic 1

Vraag:

```text
Zijn alle losse fiscale bouwstenen direct testbaar en eenduidig gedefinieerd?
```

Zo nee:

- niet doorgaan naar harmonisatie van samengestelde paden

### Go/No-Go 2 — Na Epic 3

Vraag:

```text
Zijn pensioen, eigen woning en vermogen functioneel eenduidig gemaakt?
```

Zo nee:

- accountant-engine nog niet migreren

### Go/No-Go 3 — Na Epic 4

Vraag:

```text
Is accountantdetail volledig uit engine-output op te bouwen?
```

Zo nee:

- UI niet ombouwen en oude accountantlogica nog niet verwijderen

### Go/No-Go 4 — Na Epic 5

Vraag:

```text
Rekent geen enkele UI-laag nog zelfstandig?
```

Zo nee:

- niet beginnen met opschonen van legacy logica

## Definitie van gereed op programmaniveau

De herstructurering is pas gereed als alle onderstaande stellingen waar zijn:

1. er is één source of truth per berekenstap
2. hoofdengine en accountant gebruiken exact dezelfde berekenoutput
3. eigen woning maakt deel uit van de formele engine-keten
4. pensioenbron is eenduidig
5. tests zijn georganiseerd per berekenstap
6. UI en API consumeren alleen output
7. bugs zijn direct terug te leiden naar één berekenstap en één testcluster

## Aanbevolen uitvoervolgorde

1. Epic 0
2. Epic 1
3. Epic 2 en 3 parallel waar mogelijk
4. Epic 4
5. Epic 5
6. Epic 6
7. Epic 7

## Praktische eerste backlogitems

De eerste concrete backlogitems die direct opgepakt kunnen worden zijn:

1. Schrijf directe unit-tests voor `bereken_premies_volksverzekeringen()`.
2. Schrijf directe unit-tests voor alle losse heffingskortingfuncties.
3. Maak een formele keuze voor de leidende pensioenbron.
4. Beschrijf een engine-DTO voor bruto inkomen per persoon/per jaar.
5. Beschrijf een engine-DTO voor accountantdetail.
6. Leg formeel vast hoe eigen woning de box1-grondslag moet beïnvloeden.

## Samenvatting

Het masterplan beschrijft wat de applicatie functioneel moet worden.

Dit uitvoeringsplan beschrijft in welke volgorde dat veilig gerealiseerd kan
worden.

De essentie is:

- eerst contracten en bouwstenen
- dan harmonisatie van bronnen
- dan centrale detailoutput
- dan UI/API ontkoppeling
- pas daarna definitieve opschoning
