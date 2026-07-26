---
post_title: "Masterplan Pensioenapplicatie"
author1: "GitHub Copilot"
post_slug: "masterplan-pensioenapplicatie"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "analysis"
  - "masterplan"
  - "calculation-architecture"
  - "refactoring"
ai_note: "AI-assisted synthesis of prior repository analyses; no application code was modified."
summary: "Masterplan voor de pensioenapplicatie met functionele berekenarchitectuur, source-of-truth-matrix, migratiestrategie en afgeleide doelarchitectuur."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel

Dit document is geen softwarearchitectuurdocument in klassieke zin.

Het is een masterplan dat de eerdere analyses samenbrengt tot één leidraad voor
alle volgende wijzigingen.

De centrale vraag is niet:

```text
Hoe moeten de modules eruitzien?
```

maar:

```text
Hoe moet de fiscale berekenlogica beheersbaar, herleidbaar en testbaar worden?
```

## Kernconclusie

De applicatie heeft primair geen architectuurprobleem, maar een
**beheersbaarheidsprobleem**.

De kernproblemen zijn:

- er is geen eenduidige source of truth voor alle berekeningen
- er is geen expliciete hiërarchie van berekeningen
- een bug is moeilijk terug te leiden naar precies één berekenstap
- de accountantspagina rekent deels zelfstandig
- de testset is omvangrijk, maar niet georganiseerd rond de rekenlogica

Daarom moet de eerstvolgende stap niet zijn om direct een nieuwe
softwarearchitectuur te tekenen, maar om eerst de **functionele
berekenarchitectuur** vast te leggen.

## 1. Het werkelijke systeembeeld

De applicatie bestaat functioneel uit vier systemen rond één centrale kern.

```text
                Pensioenplanner

        ┌───────────────────────────┐
        │       Gebruikersdata      │
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │      Rekenengine          │
        │   (source of truth)       │
        └────────────┬──────────────┘
                     │
        ┌────────────┼─────────────┐
        ▼            ▼             ▼
   Resultaten   Accountant    Rapportages
                     │
                     ▼
                 Testengine
```

Gewenst principe:

- de **Rekenengine** is de enige plaats waar wordt gerekend
- **Resultaten**, **Accountant** en **Rapportages** presenteren alleen output
- de **Testengine** controleert alleen de rekenengine en haar output

Huidige situatie:

- resultaten gebruiken grotendeels de hoofdengine
- accountant gebruikt deels een eigen rekensysteem
- tests controleren deels bouwstenen, deels regressies, maar niet de volledige
  functionele hiërarchie

## 2. Functionele berekenarchitectuur

### Hoofdboom

De gewenste functionele berekenhiërarchie is:

```text
Scenario
    ↓
Persoonsgegevens
    ↓
Pensioen
    ↓
AOW
    ↓
Arbeid
    ↓
Bruto inkomen
    ↓
Eigen woning
    ↓
Box 1
    ↓
Heffingskortingen
    ↓
Netto inkomen
    ↓
Box 3
    ↓
Vermogen
    ↓
Resultaten
```

Dat is de functionele volgorde waarin de applicatie beheersbaar moet worden.

### Waarom deze boom cruciaal is

Deze boom bepaalt:

- welke berekeningen zelfstandig moeten kunnen draaien
- welke output per stap beschikbaar moet zijn
- welke tests per stap horen
- waar een bug herleidbaar moet worden
- welke schermen alleen afnemer van output mogen zijn

## 3. Stap-voor-stap matrix

### 3.1 Scenario

Functies:

- `resolve_scenario()`
- `Scenario.totaal_vermogen_start()`
- `Scenario.totaal_jaarlijkse_inleg()`
- `Scenario.bereken_spaargeld_fractie_startvermogen()`
- `Scenario.bereken_spaargeld_fractie_op_datum()`

Gebruikte data:

- `Scenario`
- `Scenario.overrides`
- legacy velden `spaargeld_start`, `beleggingen_start`
- `componenten`
- `vermogensitems`

Gebruikte tarieven:

- geen fiscale tarieven direct

Tests:

- `tests/test_inheritance_engine.py`
- delen van `tests/test_scenario_engine.py`

Accountantdetail:

- gebruikt scenario indirect als bron voor maanddata, box 3-verdeling en
  eigen-woningafleiding

Afhankelijkheden:

- fundering voor alle volgende stappen

Source of truth:

- **gedeeltelijk onzuiver**

Probleem:

- legacy vermogensvelden en `vermogensitems` bestaan naast elkaar

### 3.2 Persoonsgegevens

Functies:

- `bereken_aow_datum()`
- `aow_breuk_jaar()`

Gebruikte data:

- `Persoon.naam`
- `Persoon.geboortedatum`
- partnerstatus

Gebruikte tarieven/data:

- `config/aow_leeftijden.json`

Tests:

- `tests/test_aow_engine.py`

Accountantdetail:

- gebruikt dezelfde AOW-bron

Afhankelijkheden:

- nodig voor AOW-uitkering
- nodig voor box 1-weging
- nodig voor kortingen en premies

Source of truth:

- **ja**, AOW-engine

### 3.3 Pensioen

Functies:

- hoofdpad: `_component_som_maand(... PENSIOEN_INKOMEN ...)`
- importtransformatie: `pensioenrecords_naar_rekencomponenten()`
- legacy recordfunctie: `bereken_pensioen_maand()` (alleen directe bouwsteentests)

Gebruikte data:

- rekenbron: `Scenario.componenten` met categorie `PENSIOEN_INKOMEN`
- ruwe importbron: `PensioenRecord`, vóór de expliciete transformatie

Gebruikte tarieven:

- geen fiscale tarieven direct

Tests:

- `tests/test_parser_mpo.py`
- `tests/test_pensioen_engine.py`
- `tests/test_cashflow_engine.py`
- `tests/test_regression_bugs.py`

Accountantdetail:

- consumeert de pensioenopbouw uit engine-output

Afhankelijkheden:

- bouwsteen van bruto inkomen

Source of truth:

- **ja**, de componentlaag na expliciete record-naar-componenttransformatie

Migratiecontract:

- `PensioenRecord` blijft ondersteund als ruwe importvorm en als invoerparameter
  voor achterwaartse compatibiliteit, maar wordt niet rechtstreeks berekend
- partner- en nabestaandenpensioen worden standaard niet naar regulier
  pensioeninkomen getransformeerd

### 3.4 AOW

Functies:

- `bereken_aow_maand()`
- `bereken_aow_datum()`

Gebruikte data:

- geboortedatum
- huishoudsituatie

Gebruikte tarieven:

- `aow_bedrag` uit `BelastingConfig`

Tests:

- `tests/test_aow_engine.py`
- delen van `tests/test_pensioen_engine.py`

Accountantdetail:

- gebruikt dezelfde maandfunctie

Afhankelijkheden:

- bouwsteen van bruto inkomen
- bron voor AOW-status in fiscaliteit

Source of truth:

- **ja**, mits hoofdengine en accountantpad dezelfde persoonsinput gebruiken

### 3.5 Arbeid

Functies:

- hoofdpad: `_component_som_maand(... ARBEIDSINKOMEN ...)`
- aparte helper: `bereken_arbeid_maand()`

Gebruikte data:

- arbeidscomponenten
- bedrag_type bruto/netto

Gebruikte tarieven:

- geen directe fiscale tarieven

Tests:

- `tests/test_cashflow_engine.py`
- `tests/test_pensioen_engine.py` voor `bereken_arbeid_maand()`

Accountantdetail:

- bouwt arbeid ook uit componenten op

Afhankelijkheden:

- bron voor bruto inkomen
- bron voor arbeidskorting

Source of truth:

- **redelijk ja**, componentlaag

### 3.6 Bruto inkomen

Functies:

- hoofdpad: `BrutoInkomenJaar` in `_bereken_jaar()`
- accountantpad: `bouw_accountant_detail()` consumeert dezelfde engine-output

Formule:

```text
bruto_jaar = arbeid + overig + AOW + pensioen
```

Gebruikte data:

- componenten
- AOW
- pensioenbron

Gebruikte tarieven:

- nog niet

Tests:

- direct op de DTO via `tests/test_cashflow_engine.py`
- vergelijking hoofdengine/accountant via `tests/test_regression_bugs.py`

Accountantdetail:

- consumeert `BrutoInkomenJaar` per persoon

Source of truth:

- **ja**, `JaarResultaat.bruto_inkomen`

### 3.7 Eigen woning

Functies:

- `Scenario.verzamel_fiscale_eigen_woning_invoer()`
- `Scenario.sync_eigen_woning_uit_vermogensitems()`
- `bereken_eigen_woning()`

Gebruikte data:

- `Scenario.eigen_woning`
- `vermogensitems` woning/hypotheek

Gebruikte tarieven:

- `config.eigen_woning`

Tests:

- `tests/test_eigen_woning_engine.py`
- delen van `tests/test_scenario_engine.py`
- regressies in `tests/test_regression_bugs.py`

Accountantdetail:

- gebruikt deze stap wel expliciet

Afhankelijkheden:

- moet box 1-grondslag beïnvloeden

Source of truth:

- **nee**

Probleem:

- hoofdengine gebruikt eigen woning niet als fiscale kernstap
- accountantpad wel

### 3.8 Box 1

Functies:

- `bereken_box1_belasting()`
- `bereken_premies_volksverzekeringen()`
- `netto_uit_bruto()`

Gebruikte data:

- bruto inkomen
- arbeidsinkomen
- AOW-breuk
- mogelijk eigen-woningcorrectie

Gebruikte tarieven:

- box1 schijven
- premiegrens
- premiepercentages

Tests:

- `tests/test_belasting_engine.py`
- `tests/validatie_aangifte_2025.py`

Accountantdetail:

- rekent box 1 stapsgewijs opnieuw uit

Source of truth:

- **gedeeltelijk**

Probleem:

- hoofdpad gebruikt black-box `netto_uit_bruto()`
- accountantpad gebruikt uitgesplitste variant met eigen-woningstap

### 3.9 Heffingskortingen

Functies:

- `bereken_ahk()`
- `bereken_ahk_met_aow()`
- `bereken_arbeidskorting()`
- `bereken_ouderenkorting()`
- `bereken_alleenstaandeouderenkorting()`
- `bereken_totale_heffingskortingen()`

Gebruikte data:

- bruto inkomen of box1-grondslag
- arbeidsinkomen
- partnerstatus
- AOW-status

Gebruikte tarieven:

- AHK config
- arbeidskorting config
- ouderenkorting config
- AOK config
- `ahk_aow_factor`

Tests:

- deels direct in `tests/test_belasting_engine.py`
- deels indirect via `validatie_aangifte_2025.py`

Accountantdetail:

- berekent kortingcomponenten los uit
- bevat zelfs een speciale AHK-afwijking voor alleenstaande AOW-case

Source of truth:

- **nee**, door afwijkende accountantlogica

### 3.10 Netto inkomen

Functies:

- hoofdpad: uit `netto_uit_bruto()` en optelling van netto componenten
- accountantpad: expliciet opgebouwd uit bruto minus verschuldigd plus netto
  componenten

Gebruikte data:

- bruto
- box 1
- premies
- kortingen
- netto componenten

Gebruikte tarieven:

- alle box1/premie/kortingtarieven

Tests:

- `tests/test_belasting_engine.py`
- `tests/test_cashflow_engine.py`

Accountantdetail:

- expliciet zichtbaar

Source of truth:

- **gedeeltelijk**

Probleem:

- de formule is functioneel gelijk, maar niet uit één outputbron afgeleid

### 3.11 Box 3

Functies:

- `bereken_box3_heffing()`

Gebruikte data:

- saldo begin jaar
- partnerstatus
- spaargeldfractie

Gebruikte tarieven:

- vrijstelling
- forfait spaargeld
- forfait overig
- box 3-tarief

Tests:

- `tests/test_belasting_engine.py`
- `tests/validatie_aangifte_2025.py`

Accountantdetail:

- expliciet zichtbaar en uitgesplitst

Source of truth:

- **bijna ja**

Maar:

- box 3 gebruikt startjaarsfractie, rendement gebruikt dynamische maandfractie

### 3.12 Vermogen

Functies:

- `bereken_rente_maand()`
- saldo-opbouw in `_bereken_jaar()`

Gebruikte data:

- saldo begin maand
- rendementen
- spaargeldfractie
- netto cashflow

Gebruikte tarieven:

- geen fiscale tarieven

Tests:

- `tests/test_vermogen_engine.py`
- `tests/test_rendement_split.py`
- delen van `tests/test_cashflow_engine.py`

Accountantdetail:

- rekent saldo-opbouw opnieuw uit

Source of truth:

- **gedeeltelijk**

Probleem:

- twee paden rekenen de vermogensopbouw opnieuw uit

### 3.13 Resultaten

Functies:

- `MaandResultaat`
- `JaarResultaat`
- `HuishoudCashflow`

Gebruikte data:

- output van alle vorige stappen

Gebruikte tarieven:

- alleen indirect via meegedragen metadata

Tests:

- `tests/test_cashflow_engine.py`
- `tests/test_grafiek_consistency.py`
- `tests/test_grafiek_validator.py`

Accountantdetail:

- gebruikt nu geen centrale result-DT0 als volledige bron

Source of truth:

- **nee voor detailniveau**, **ja voor hoofdoutput**

## 4. Source-of-truth-matrix

| Stap | Huidige source of truth | Oordeel |
| --- | --- | --- |
| Scenario-resolutie | `resolve_scenario()` | goed |
| Persoonsgegevens/AOW-leeftijd | `aow_engine` | goed |
| Pensioen | componenten in hoofdpad, records in accountantpad | fout / dubbel |
| Arbeid | componenten | goed |
| Bruto inkomen | afgeleid, maar pensioenbron verschilt | instabiel |
| Eigen woning | accountantpad + dubbele bron | fout / dubbel |
| Box 1 | `netto_uit_bruto()` plus accountantvariant | dubbel |
| Heffingskortingen | `heffingskorting.py` plus accountantspecial case | dubbel |
| Netto inkomen | hoofdpad + accountantopbouw | dubbel |
| Box 3 | `bereken_box3_heffing()` | redelijk goed |
| Vermogen | hoofdpad + accountantopbouw | dubbel |
| Resultaatdetail | geen uniforme detail-DTO | ontbreekt |

## 5. Gewenste functionele doeltoestand

Per berekenstap moet uiteindelijk gelden:

1. één invoerdefinitie
2. één set gebruikte tarieven
3. één uitvoerdefinitie
4. één testset
5. één verantwoordelijke functie of service
6. nul zelfstandige herberekeningen in UI

## 6. Migratiestrategie

### Fase A: expliciet maken

Doel:

- bestaande rekenstappen zichtbaar en herleidbaar maken

Werk:

1. definieer per stap een expliciete input/output-DTO
2. maak de fiscale detailoutput van de hoofdengine compleet
3. definieer per stap de officiële source of truth

Resultaat:

- de berekenboom is niet alleen beschreven, maar ook in outputstructuren
  zichtbaar

### Fase B: isoleren

Doel:

- losse bouwstenen zelfstandig uitvoerbaar en testbaar maken

Werk:

1. maak alle kortingfuncties zelfstandig testbaar
2. maak premies zelfstandig testbaar
3. maak box 3 zelfstandig testbaar
4. maak eigen woning zelfstandig testbaar als verplichte stap in de keten

Resultaat:

- elke fiscale bouwsteen is los controleerbaar

### Fase C: harmoniseren

Doel:

- dubbele rekensystemen verwijderen

Werk:

1. harmoniseer pensioenbron
2. harmoniseer eigen-woningbron
3. harmoniseer hoofdpad en accountantpad
4. vervang accountantherberekening door engine-output

Resultaat:

- één rekenpad

### Fase D: regressie verankeren

Doel:

- iedere bug laat zich terugbrengen naar één stap en één test

Werk:

1. koppel per berekenstap vaste tests
2. voeg vergelijkingstests toe tussen detailoutput en jaarsamenvatting
3. voeg regressietest toe voor elke gerepareerde bug

Resultaat:

- fouten zijn herleidbaar en blijvend bewaakt

### Fase E: presenteren

Doel:

- UI en rapporten reduceren tot pure afnemers van engine-output

Werk:

1. laat Streamlit resultaten alleen engine-output lezen
2. laat accountant alleen engine-detailoutput lezen
3. laat React alleen engine-output lezen
4. verwijder client-side interpretatie waar mogelijk

Resultaat:

- presentatielaag rekent niet meer zelfstandig

## 7. Concreet gefaseerd herstructureringsplan

### Stap 1

Maak alle kortingfuncties zelfstandig en volledig testbaar.

### Stap 2

Maak premies volksverzekeringen zelfstandig en volledig testbaar.

### Stap 3

Maak box 3 een expliciete, los aanroepbare berekenstap met vaste input/output.

### Stap 4

Maak eigen woning een expliciete, verplichte stap tussen bruto inkomen en box 1.

### Stap 5

Maak een accountant-engine die exact dezelfde berekeningsbron gebruikt als de
hoofdengine.

### Stap 6

Laat de hoofdengine een volledige detailoutput leveren voor:

- grondslagen
- tarieven
- tussenresultaten
- einduitkomsten

### Stap 7

Laat de accountantspagina alleen nog deze detailoutput presenteren.

### Stap 8

Verwijder dubbele logica uit UI, API-client en accountantpad.

### Stap 9

Organiseer tests per berekenstap in plaats van alleen per bestand of regressie.

### Stap 10

Verwijder of migreer legacy vermogensvelden zodra de nieuwe bron volledig
leidend is.

## 8. Benodigde output per berekenstap

De toekomstige rekenengine moet per stap minimaal het volgende kunnen tonen:

| Stap | Minimale output |
| --- | --- |
| Pensioen | bronposten, periode, bedrag, indexatie |
| AOW | AOW-datum, AOW-breuk, maandbedrag, jaarbedrag |
| Arbeid | broncomponenten, bruto/netto, periode |
| Bruto inkomen | samenstellende posten per persoon |
| Eigen woning | WOZ, rente, forfait, Hillen, box1-mutatie, tariefsaanpassing |
| Box 1 | grondslag, schijven, IB vóór korting, premies |
| Heffingskortingen | AHK, AK, OK, AOK, regels en grondslagen |
| Netto inkomen | bruto minus belastingen plus netto componenten |
| Box 3 | vrijstelling, belastbaar vermogen, forfaiten, heffing |
| Vermogen | saldo begin, rendement, cashflowmutatie, saldo eind |
| Resultaat | maanddetail, jaardetail, aannames, gebruikte tariefjaren |

Dit is de functionele basis voor accountant, rapportage en debugging.

## 9. Afgeleide softwarearchitectuur

Pas nadat de functionele berekenarchitectuur leidend is gemaakt, volgt de
doelarchitectuur logisch uit de functieboom.

### Gewenste softwarelagen

```text
Inputlaag
    -> scenario, personen, records, vermogensitems

Berekenlaag
    -> pensioenservice
    -> aowservice
    -> arbeidservice
    -> eigenwoningservice
    -> box1service
    -> kortingservice
    -> box3service
    -> vermogensservice
    -> result assembler

Outputlaag
    -> jaarresultaat
    -> maandresultaat
    -> accountantdetail
    -> rapportage-output

Presentatielaag
    -> Streamlit
    -> React
    -> API

Controlelaag
    -> unit tests
    -> integratietests
    -> regressietests
    -> validatiecases
```

### Principe

- UI mag geen berekeningen uitvoeren
- API mag geen alternatieve berekeningen uitvoeren
- accountant mag geen tweede engine zijn
- tests moeten op de berekenlaag richten

## 10. Definitie van gereed per berekenstap

Een berekenstap is pas beheersbaar als aan alle onderstaande punten is voldaan:

1. de functionele plek in de berekenboom is expliciet
2. de invoer is eenduidig
3. de gebruikte tarieven zijn expliciet
4. de output is expliciet
5. de source of truth is uniek
6. er is directe unitdekking
7. er is integratiedekking in de hoofdengine
8. accountant en rapportage lezen alleen output, niet eigen logica

## 11. Beslisregels voor toekomstige wijzigingen

Bij elke toekomstige wijziging moet eerst worden bepaald:

1. in welke berekenstap zit deze wijziging?
2. wat is daar de officiële source of truth?
3. welke tests horen exclusief bij deze stap?
4. welke output moet zichtbaar veranderen?
5. welke schermen consumeren alleen deze output?

Als die vijf vragen niet direct te beantwoorden zijn, is de wijziging nog niet
veilig voorbereid.

## 12. Prioriteitenlijst

### Hoogste prioriteit

- source of truth per berekenstap expliciet maken
- accountantpad harmoniseren met de hoofdengine
- eigen woning in de functionele kern opnemen
- pensioenbron harmoniseren
- detailoutput uit de engine beschikbaar maken

### Tweede prioriteit

- tests per berekenstap organiseren
- premies en kortingen direct testen
- UI-interpretatielagen afbouwen

### Derde prioriteit

- doelarchitectuur en services scheiden
- legacy velden saneren
- client-side aggregatielogica minimaliseren

## 13. Samenvatting

De juiste volgende stap is niet direct een nieuwe target-architectuur, maar het
formaliseren van de functionele berekenarchitectuur als centrale waarheid.

Dat betekent concreet:

- eerst de berekenboom expliciet maken
- dan per stap source of truth, input, tarieven, output en tests vastleggen
- daarna pas gefaseerd herstructureren
- en pas als laatste de softwarearchitectuur definitief hertekenen

## 14. Kortste samenvatting in één zin

De pensioenapplicatie moet niet eerst technisch worden herbouwd, maar eerst
functioneel worden teruggebracht tot één expliciete berekenboom met één source
of truth per stap, waarna herstructurering en doelarchitectuur veilig kunnen
volgen.
