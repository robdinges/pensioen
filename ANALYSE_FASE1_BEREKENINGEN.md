---
post_title: "Analyse Fase 1 Berekeningen"
author1: "GitHub Copilot"
post_slug: "analyse-fase-1-berekeningen"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "analysis"
  - "calculations"
  - "pension"
  - "tax"
ai_note: "AI-assisted calculation-path analysis based on repository inspection; no application code was modified."
summary: "Fase 1 analyse van de rekenengine: inhoudelijke rekenboom, call graph, parallelle rekenpaden, grondslagen en tussenresultaten."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel en afbakening

Dit document is de aangescherpte fase-1 analyse van uitsluitend de
rekenengine.

Deze fase richt zich alleen op:

- berekeningen
- inhoudelijke rekenstappen
- afhankelijkheden tussen rekenfuncties
- grondslagen en tussenresultaten
- parallelle rekenpaden die tot verschillende uitkomsten kunnen leiden

Deze fase richt zich niet op:

- volledige UI-analyse
- React-architectuur
- testdekking per functie
- documentatie of beheerprocessen

## Kernconclusie

De applicatie heeft niet één rekenpad, maar minimaal twee relevante paden:

1. het hoofdpad via `bereken_huishouden()`
2. het accountantpad via `_bereken_jaar_detail()` in
   `src/pensioen/ui/pagina_accountant.py`

Die twee paden zijn inhoudelijk niet gelijk.

De belangrijkste functionele afwijkingen zijn:

- het hoofdpad gebruikt pensioen uit `Scenario.componenten`
- het accountantpad gebruikt pensioen uit `records1` en `records2`
- het hoofdpad verwerkt geen eigen-woningcorrectie in box 1
- het accountantpad verwerkt eigen-woningforfait, renteaftrek, Hillen en
  tariefsaanpassing wel
- het hoofdpad gebruikt `netto_uit_bruto()` als black-box jaarberekening
- het accountantpad rekent box 1, premies, kortingen en eigen woning stap voor
  stap zelf uit

Daarmee is de hoofdconclusie van fase 1:

**de applicatie heeft geen eenduidige single source of truth voor de volledige
fiscale berekening.**

## 1. Hoofdrekenpad

### Functioneel eindresultaat

De hoofdengine berekent uiteindelijk per jaar een `JaarResultaat` en per maand
een `MaandResultaat`.

De kern van de hoofdflow is:

```text
Netto cashflow per maand

=
bruto arbeidsinkomen
+ bruto overig inkomen
+ bruto AOW
+ bruto pensioen
+ netto inkomenscomponenten
- maandbelasting P1
- maandbelasting P2
+ maandheffingskorting P1
+ maandheffingskorting P2
- box 3 per maand
- inhoudingen
- huishoudelijke uitgaven
+ incidentele ontvangst
- incidentele uitgave
+ rendement op vermogen
+ inleg per maand
```

Dat bedrag wordt toegevoegd aan het beginsaldo van de maand om het
`vermogen_einde_maand` te bepalen.

### Technisch hoofdpad

```text
bereken_huishouden
  -> resolve_scenario
  -> scenario_resolved.totaal_vermogen_start
  -> per jaar: _bereken_jaar
     -> bereken_aow_datum P1/P2
     -> per maand:
        -> _component_som_maand
           -> FinancieelComponent.bedrag_per_maand_actief
              -> selecteer_periodieke_waarde
        -> _incidentele_items_voor_maand
        -> bereken_aow_maand
     -> jaargrondslagen opbouwen
     -> netto_uit_bruto P1
     -> netto_uit_bruto P2
     -> bereken_box3_heffing
     -> per maand:
        -> scenario.bereken_spaargeld_fractie_op_datum
        -> bereken_rente_maand
        -> MaandResultaat samenstellen
     -> JaarResultaat samenstellen
  -> HuishoudCashflow samenstellen
```

## 2. Inhoudelijke rekenboom van het hoofdpad

### Stap 1: scenario voorbereiden

Functie:

- `resolve_scenario()` in `calculations/inheritance_engine.py`

Doel:

- als het scenario een afgeleid scenario is, eerst overrides op parentwaarden
  toepassen

Resultaat:

- één effectief scenario-object dat door de hoofdengine verder wordt gebruikt

Belangrijk:

- alleen velden in `overrides` worden echt opnieuw gezet
- overerving is dus voorafgaande inputresolutie, geen rekenslag op zich

### Stap 2: beginvermogen bepalen

Functie:

- `Scenario.totaal_vermogen_start()`

Formule:

```text
startvermogen = spaargeld_start + beleggingen_start
```

Belangrijk:

- dit gebruikt de legacy velden `spaargeld_start` en `beleggingen_start`
- dit gebruikt niet rechtstreeks `vermogensitems`
- de hoofdengine start dus vanuit legacy vermogensgrondslag

### Stap 3: AOW-ingangsdata bepalen

Functie:

- `aow_engine.bereken_aow_datum(geboortedatum)`

Substappen:

- laad `config/aow_leeftijden.json`
- zoek leeftijdsregel op basis van geboortejaar
- tel jaren en maanden op bij geboortedatum

Resultaat:

- exacte AOW-ingangsdatum per persoon

### Stap 4: maandelijkse inkomensgrondslagen opbouwen

Voor elke maand worden de volgende bedragen bepaald.

#### 4.1 Arbeidsinkomen bruto en netto

Functie:

- `_component_som_maand(..., CategorieComponent.ARBEIDSINKOMEN, ...)`

Subfunctie:

- `FinancieelComponent.bedrag_per_maand_actief(jaar, maand)`

Functionele stap:

```text
arbeid_bruto_p1 = som van alle actieve arbeidscomponenten P1 met bedrag_type=BRUTO
arbeid_bruto_p2 = idem voor P2
arbeid_netto_p1 = som van alle actieve arbeidscomponenten P1 met bedrag_type=NETTO
arbeid_netto_p2 = idem voor P2
```

#### 4.2 Overig inkomen bruto en netto

Functie:

- `_component_som_maand(..., CategorieComponent.OVERIG_INKOMEN, ...)`

Extra regel:

- handmatig ingevoerde AOW-componenten worden hier desgewenst uitgefilterd via
  `is_handmatige_aow_component()`

Functionele stap:

```text
overig_bruto = som van actieve overig-inkomencomponenten
overig_netto = som van actieve onbelaste overig-inkomencomponenten
```

#### 4.3 AOW per maand

Functie:

- `pensioen_engine.bereken_aow_maand(...)`

Functionele stap:

```text
als AOW nog niet is ingegaan: 0
als AOW al liep op de eerste van de maand: volledig maandbedrag
als AOW in deze maand start: pro-rata op basis van resterende dagen
```

#### 4.4 Pensioen per maand in het hoofdpad

Functie:

- `_component_som_maand(..., CategorieComponent.PENSIOEN_INKOMEN, ...)`

Belangrijk:

- `bereken_huishouden()` gebruikt hier niet `records1` of `records2`
- pensioen in de hoofdengine komt dus uit scenario-componenten, niet uit
  `PensioenRecord`

Functionele stap:

```text
pensioen_p1 = som van actieve pensioencomponenten P1
pensioen_p2 = som van actieve pensioencomponenten P2
```

#### 4.5 Uitgaven en inhoudingen

Functies:

- `_component_som_maand(..., CategorieComponent.UITGAVE, ...)`
- `_component_som_maand(..., CategorieComponent.INHOUDING, ...)`
- `_incidentele_items_voor_maand(...)`

Functionele stap:

```text
uitgaven_maand = som actieve uitgavecomponenten
inhoudingen_maand = som actieve inhoudingscomponenten
incidentele_ontvangst = som positieve incidentele items in maand
incidentele_uitgave = som absolute waarde van negatieve incidentele items in maand
```

### Stap 5: jaargrondslagen opbouwen voor box 1

Na 12 maanden worden jaartotalen opgebouwd:

```text
bruto_jaar_p1 = jaar_arbeid_p1 + jaar_overig_p1 + jaar_aow_p1 + jaar_pensioen_p1
bruto_jaar_p2 = jaar_arbeid_p2 + jaar_overig_p2 + jaar_aow_p2 + jaar_pensioen_p2
```

Daarnaast wordt apart bijgehouden:

- `arbeidsinkomen` voor arbeidskorting
- netto componentinkomen dat buiten box 1 blijft

### Stap 6: box 1, premies en heffingskortingen

Functie:

- `belasting_engine.netto_uit_bruto()`

#### Inhoudelijke formuleboom

```text
Netto inkomen uit box 1-bronnen

=
bruto jaarinkomen
- netto verschuldigde box 1 + premies

waarbij:

netto verschuldigd
= max(0, inkomstenbelasting + premies - totale heffingskortingen)
```

#### 6.1 AOW-breuk

Functie:

- `aow_engine.aow_breuk_jaar(geboortedatum, jaar)`

Doel:

- bepaalt welk deel van het jaar het AOW-tarief en AOW-gerelateerde korting
  van toepassing is

#### 6.2 Inkomstenbelasting box 1

Functie:

- `bereken_box1_belasting(bruto, config, aow_breuk)`

Subfunctie:

- `_bereken_schijven(inkomen, schijven)`

Inhoudelijke formule:

```text
belasting_niet_aow = schijfberekening over bruto met box1_niet_aow
belasting_aow = schijfberekening over bruto met box1_aow

box1_ib =
    (1 - aow_breuk) * belasting_niet_aow
  + aow_breuk * belasting_aow
```

#### 6.3 Premies volksverzekeringen

Functie:

- `bereken_premies_volksverzekeringen(bruto_inkomen, config, is_aow_heel_jaar)`

Inhoudelijke formule:

```text
premiegrondslag = min(bruto_inkomen, premiegrens)

premie_aow = premiegrondslag * aow_tarief_niet_aow of 0 bij volledig AOW-jaar
premie_anw = premiegrondslag * anw_tarief
premie_wlz = premiegrondslag * wlz_tarief

totaal_premies = premie_aow + premie_anw + premie_wlz
```

#### 6.4 Heffingskortingen

Functie:

- `bereken_totale_heffingskortingen(...)`

Subfuncties:

- `bereken_ahk_met_aow()`
- `bereken_arbeidskorting()`
- `bereken_ouderenkorting()`
- `bereken_alleenstaandeouderenkorting()`

Inhoudelijke formule:

```text
totale_heffingskortingen
= ahk + arbeidskorting + ouderenkorting + alleenstaandeouderenkorting
```

AHK en ouderenkorting zijn afbouwkortingen:

```text
korting = max(minimum, maximum - max(0, inkomen - afbouwgrens) * afbouw_pct)
```

Arbeidskorting is vereenvoudigd geïmplementeerd:

```text
korting_voor_afbouw = min(max_bedrag, arbeidsinkomen)
arbeidskorting = max(minimum, korting_voor_afbouw - afbouw)
```

Dat is een vereenvoudigd model, geen volledige meerfasige arbeidskortingstabel.

#### 6.5 Netto uit bruto

Functie:

- `netto_uit_bruto()`

Eindformule:

```text
totaal_belasting_en_premies = box1_ib + totaal_premies
netto_verschuldigd = max(0, totaal_belasting_en_premies - totale_kortingen)
netto = bruto - netto_verschuldigd
```

### Stap 7: box 3 heffing

Functie:

- `bereken_box3_heffing(spaarsaldo, config, heeft_partner, spaargeld_fractie)`

#### Grondslag in het hoofdpad

```text
spaarsaldo = saldo_begin_jaar
```

Belangrijk:

- box 3 gebruikt in het hoofdpad het beginsaldo van het jaar
- box 3 gebruikt niet de actuele maandontwikkeling als grondslag

#### Inhoudelijke formule voor rendement

```text
vrijstelling = vrijstelling_per_persoon * aantal_fiscale_partners
belastbaar_vermogen = max(0, saldo_begin_jaar - vrijstelling)

gewogen_forfait =
    spaargeld_fractie * forfaitair_spaargeld
  + (1 - spaargeld_fractie) * forfaitair_overig

fictief_rendement = belastbaar_vermogen * gewogen_forfait
box3_heffing = fictief_rendement * box3_tarief
```

De gebruikte `spaargeld_fractie` voor box 3 komt uit:

- `Scenario.bereken_spaargeld_fractie_startvermogen()`

dus uit de startverdeling van legacy spaargeld en beleggingen.

### Stap 8: rendement op vermogen

Functie:

- `bereken_rente_maand(saldo, jaarrendement_pct, jaarrendement_sparen_pct, jaarrendement_beleggen_pct, spaargeld_fractie)`

#### Inhoudelijke formule

Als aparte sparen/beleggen-rendementen zijn ingevuld:

```text
saldo_sparen = saldo * spaargeld_fractie
saldo_beleggen = saldo * (1 - spaargeld_fractie)

rente_sparen = saldo_sparen * maandrendement(rendement_sparen)
rente_beleggen = saldo_beleggen * maandrendement(rendement_beleggen)

rente = rente_sparen + rente_beleggen
```

Anders:

```text
rente = saldo * maandrendement(rendement_pct)
```

De dynamische `spaargeld_fractie` voor rendement komt uit:

- `Scenario.bereken_spaargeld_fractie_op_datum(peildatum)`

en gebruikt:

- legacy startsaldi
- jaarlijkse inleg sparen/beleggen
- actieve componenten met `beleggings_type`

Hier zit dus een inhoudelijk verschil met box 3:

- rendement gebruikt een dynamische maandfractie
- box 3 gebruikt een startjaarsfractie

### Stap 9: netto cashflow per maand

Inhoudelijke formule in `_bereken_jaar()`:

```text
netto_cashflow
= arbeid_bruto
+ overig_bruto
+ arbeid_netto
+ overig_netto
+ aow
+ pensioen
- maand_belasting
+ maand_heffingskorting
- box3_maand
- inhoudingen
- uitgaven
+ incidentele_ontvangst
- incidentele_uitgave
+ rente
+ inleg_per_maand
```

Daarna:

```text
saldo_einde_maand = max(0, saldo_begin_maand + netto_cashflow)
```

### Stap 10: jaarresultaat en totaalresultaat

`JaarResultaat` aggregeert maandregels naar:

- arbeid bruto
- AOW bruto
- pensioen bruto
- overig bruto
- totaal bruto
- totaal belasting
- totaal heffingskorting
- netto
- effectief tarief
- vermogen einde jaar

`HuishoudCashflow` bundelt alle jaren en aannames.

## 3. Werkelijke call graph per kernfunctie

### `bereken_huishouden()`

Roept aan:

- `resolve_scenario()`
- `_bereken_jaar()`

Wordt aangeroepen door:

- `app.py`
- `src/pensioen/api/main.py`
- `calculations/scenario_engine.py`
- `src/pensioen/ui/pagina_bereken.py`
- diverse tests

### `_bereken_jaar()`

Roept aan:

- `aow_engine.bereken_aow_datum()`
- `_component_som_maand()`
- `_incidentele_items_voor_maand()`
- `pensioen_engine.bereken_aow_maand()`
- `belasting_engine.netto_uit_bruto()`
- `belasting_engine.bereken_box3_heffing()`
- `Scenario.bereken_spaargeld_fractie_startvermogen()`
- `Scenario.bereken_spaargeld_fractie_op_datum()`
- `vermogen_engine.bereken_rente_maand()`

Wordt aangeroepen door:

- `bereken_huishouden()`

### `netto_uit_bruto()`

Roept aan:

- `aow_engine.aow_breuk_jaar()`
- `bereken_box1_belasting()`
- `bereken_premies_volksverzekeringen()`
- `heffingskorting.bereken_totale_heffingskortingen()`
  - `bereken_ahk_met_aow()`
  - `bereken_arbeidskorting()`
  - `bereken_ouderenkorting()`
  - `bereken_alleenstaandeouderenkorting()`

Wordt aangeroepen door:

- `cashflow_engine._bereken_jaar()`
- `validatie/belasting_vergelijking/pensioen_adapter.py`
- tests

### `bereken_box1_belasting()`

Roept aan:

- `_bereken_schijven()` voor niet-AOW
- `_bereken_schijven()` voor AOW

Wordt aangeroepen door:

- `netto_uit_bruto()`
- accountantpad `_bereken_jaar_detail()`
- tests

### `bereken_box3_heffing()`

Roept aan:

- geen andere businessfunctie

Wordt aangeroepen door:

- `cashflow_engine._bereken_jaar()`
- accountantpad `_bereken_jaar_detail()`
- validatie-adapter
- tests

### `bereken_aow_datum()`

Roept aan:

- `_laad_aow_tabel()`
- `_zoek_aow_leeftijd()`
- `_voeg_jaren_toe()`
- `_voeg_maanden_toe()`

Wordt aangeroepen door:

- `cashflow_engine._bereken_jaar()`
- `aow_breuk_jaar()`
- accountantpad `_bereken_jaar_detail()`
- diverse UI-pagina’s
- tests

### `bereken_aow_maand()`

Roept aan:

- geen andere businessfunctie

Wordt aangeroepen door:

- `cashflow_engine._bereken_jaar()`
- accountantpad `_bereken_jaar_detail()`
- tests

### `bereken_pensioen_maand()`

Roept aan:

- `_bruto_per_maand()`

Wordt aangeroepen door:

- accountantpad `_bereken_jaar_detail()`
- tests

Belangrijk:

- deze functie wordt niet gebruikt in het hoofdpad `bereken_huishouden()`

### `bereken_rente_maand()`

Roept aan:

- `maandrendement()`

Wordt aangeroepen door:

- `cashflow_engine._bereken_jaar()`
- `bereken_vermogensontwikkeling()`
- accountantpad `_bereken_jaar_detail()`
- tests

### `bereken_eigen_woning()`

Roept aan:

- `_bereken_eigenwoningforfait()`
- `_bereken_tariefsaanpassing()`

Wordt aangeroepen door:

- accountantpad `_bereken_jaar_detail()`
- accountanthelper `_bereken_eigen_woning_voor_weergave()`
- tests

Belangrijk:

- deze functie wordt niet gebruikt in `bereken_huishouden()`

## 4. Parallelle rekenpaden en inhoudelijke verschillen

### Verschil 1: pensioenbron

Hoofdpad:

```text
pensioen = Scenario.componenten met categorie PENSIOEN_INKOMEN
```

Accountantpad:

```text
pensioen = som van bereken_pensioen_maand(record) over records1/records2
```

Gevolg:

- dezelfde gebruiker kan andere pensioenuitkomsten zien afhankelijk van pad
- import via MPO is in het hoofdpad alleen relevant voor zover records eerst naar
  componenten zijn omgezet
- accountantpad leest in de huidige pagina zelfs `records1 = []` en `records2 = []`
  in `toon_accountant_pagina()`, waardoor pensioen daar feitelijk op nul kan
  uitkomen tenzij er elders componenten zijn gebruikt in `overig_*`

### Verschil 2: eigen woning

Hoofdpad:

- geen oproep naar `bereken_eigen_woning()`
- box 1 grondslag is gelijk aan bruto jaarinkomen uit arbeid + overig + AOW +
  pensioen

Accountantpad:

- roept `Scenario.verzamel_fiscale_eigen_woning_invoer()` aan
- roept `bereken_eigen_woning()` per persoon aan
- corrigeert box 1 grondslag met `box1_mutatie`
- telt `tariefsaanpassing` mee in totaal verschuldigde belasting

Gevolg:

- hoofdresultaat en accountantresultaat kunnen inhoudelijk verschillen zodra er
  een eigen woning of hypotheek is

### Verschil 3: AHK-grondslag bij alleenstaande AOW-case

Hoofdpad:

- `netto_uit_bruto()` gebruikt `bereken_totale_heffingskortingen()` als standaard

Accountantpad:

- bevat een speciale afwijking:
  - bij AOW en geen partner wordt voor AHK `bereken_ahk(bruto_p1, config)`
    gebruikt in plaats van de standaard `bereken_ahk_met_aow(...)`

Gevolg:

- de accountantpagina bevat expliciet afwijkende logica ten opzichte van de
  hoofdengine

### Verschil 4: box 1 detail versus black-box

Hoofdpad:

- gebruikt `netto_uit_bruto()` als samengevatte jaarberekening

Accountantpad:

- rekent afzonderlijk:
  - `bereken_box1_belasting()`
  - `bereken_premies_volksverzekeringen()`
  - alle heffingskortingen los
  - eigen woning los

Gevolg:

- de accountantpagina is geen pure projectie van hoofdresultaten
- het is een tweede implementatie

### Verschil 5: box 3 versus rendement

Binnen hetzelfde hoofdpad bestaan al twee verschillende verdelingslogica’s:

- box 3 gebruikt `bereken_spaargeld_fractie_startvermogen()`
- rendement gebruikt `bereken_spaargeld_fractie_op_datum()`

Gevolg:

- box 3 en rendement zijn gebaseerd op verschillende verdelingsdefinities

Dat hoeft inhoudelijk niet fout te zijn, maar het moet expliciet gedocumenteerd
en getest worden.

## 5. Welke tussenresultaten bestaan nu al expliciet

### In het hoofdpad (`MaandResultaat` / `JaarResultaat`)

Reeds expliciet beschikbaar:

- arbeid bruto P1/P2
- AOW bruto P1/P2
- pensioen bruto P1/P2
- overig bruto
- netto componentinkomen
- box 1-belasting verdeeld per maand
- heffingskorting verdeeld per maand
- box 3 verdeeld per maand
- inhoudingen
- huishoudelijke uitgaven
- incidentele ontvangsten en uitgaven
- rendement per maand
- vermogen einde maand

Niet expliciet als afzonderlijke jaarstap beschikbaar in het hoofdpad:

- box1-grondslag per persoon
- premiesplit per persoon in output
- afzonderlijke AHK, arbeidskorting, ouderenkorting, AOK in output
- eigenwoningforfait, Hillen, tariefsaanpassing

### In het accountantpad (`_bereken_jaar_detail()` dict)

Wel expliciet beschikbaar:

- bruto per persoon
- box1-grondslag per persoon
- AOW-breuk per persoon
- IB vóór korting per persoon
- premiecomponenten per persoon
- elk type heffingskorting per persoon
- totaal IB + premies per persoon
- netto belasting per persoon
- eigen-woningdetails per persoon
- box 3 details
- maanddetail van saldo-opbouw

Daarmee bevat het accountantpad de audit trail die het hoofdpad nog niet als
structurele output oplevert.

## 6. Isolatiegrenzen van de rekenengine

### Al goed isoleerbaar

- AOW-berekening
- schijfberekening
- premieberekening
- box 3-berekening
- heffingskortingen
- pro-rata pensioen/AOW per maand
- componentbedrag per maand
- waardering per vermogensitem

### Nog niet goed isoleerbaar

- volledige jaarberekening als transparante stap-voor-stap DTO
- volledige accountantberekening buiten de UI
- één uniforme grondslag voor pensioen
- één uniforme grondslag voor eigen woning

## 7. Belemmeringen voor herstructurering

De belangrijkste blokkades voor een veilige herstructurering zijn nu:

1. `bereken_huishouden()` en `_bereken_jaar_detail()` zijn niet equivalent.
2. De hoofdengine bevat geen expliciete fiscale detail-output.
3. Eigen woning is niet onderdeel van het hoofdpad, maar wel van het
   accountantpad.
4. Pensioenrecords en pensioencomponenten bestaan tegelijk als rekengrondslag.
5. De hoofdengine start vanuit legacy vermogensvelden, terwijl andere delen van
   het systeem steeds meer op `vermogensitems` leunen.

## 8. Minimale richting voor fase 2 en later

Op basis van fase 1 is de logische vervolgreeks:

1. tarieven en overrides exact uitwerken
2. per rekenfunctie de testmapping maken
3. pas daarna UI/API en accountantpad tegen de core afzetten

De belangrijkste technische doeltoestand voor de rekencore is:

```text
één hoofdengine
    -> één set grondslagen
    -> één fiscale detailstructuur
    -> één maanddetailstructuur
    -> alle schermen lezen alleen output
    -> geen scherm rekent zelfstandig opnieuw
```

## 9. Samenvatting in één zin

De huidige applicatie rekent de kerncashflow wel centraal uit, maar de
volledige fiscale audit trail zit in een tweede, afwijkend rekenpad, waardoor
de rekenengine nog niet veilig is te isoleren zonder eerst pensioen, eigen
woning en fiscale detailoutput te harmoniseren.
