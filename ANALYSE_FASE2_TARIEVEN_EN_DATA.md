---
post_title: "Analyse Fase 2 Tarieven en Data"
author1: "GitHub Copilot"
post_slug: "analyse-fase-2-tarieven-en-data"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "analysis"
  - "tax"
  - "configuration"
  - "data"
ai_note: "AI-assisted tariff and dataset analysis based on repository inspection; no application code was modified."
summary: "Fase 2 analyse van belastingtabellen, AOW, heffingskortingen, box 3, eigen woning, inflatie en tariefoverrides."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel en afbakening

Deze fase analyseert uitsluitend:

- belastingtabellen
- AOW-data
- heffingskortingen
- box 3-parameters
- eigen-woningparameters
- inflatie- en overridevelden
- de route van configbron naar gebruikende functie

Deze fase analyseert niet:

- UI-architectuur
- testdekking
- volledige call graph van schermen

## 1. Centrale databronnen

### Configbestanden

| Bestand | Doel | Formaat | Wordt geladen door |
| --- | --- | --- | --- |
| `config/belasting_2025.json` | fiscale parameters 2025 | JSON | `belasting_loader.laad_tarieven()` |
| `config/belasting_2026.json` | fiscale parameters 2026 | JSON | `belasting_loader.laad_tarieven()` |
| `config/aow_leeftijden.json` | AOW-leeftijdentabel | JSON | `aow_engine._laad_aow_tabel()` |

### Runtime databronnen buiten config

| Bron | Vorm | Gebruik |
| --- | --- | --- |
| `Scenario.tarief_periodes` | lijst overrides | overschrijft subset van configvelden per jaar |
| `Scenario.inflatie_pct` | scenariofield | rapportage/UI, niet centrale fiscale config |
| `Scenario.rendement_*` | scenariofield | vermogen/rendement |
| `VermogensItem.groei_pct` | itemfield | waardegroei per item |
| `Scenario.eigen_woning` | modeldata | legacy eigen-woninginput |
| `Scenario.vermogensitems` | modeldata | nieuwe vermogens- en woningbron |

## 2. Route van bron naar berekening

### Belastingconfiguratie

```text
config/belasting_YYYY.json
    -> belasting_loader.laad_tarieven(jaar)
    -> BelastingConfig
    -> laad_tarieven_bereik()
    -> resolve_tariefwaarden_voor_jaar()
    -> gebruikt door:
       - belasting_engine.netto_uit_bruto
       - belasting_engine.bereken_box3_heffing
       - pensioen_engine.bereken_aow_maand via aow_bedrag uit cashflow/accountantpad
       - eigen_woning_engine.bereken_eigen_woning
       - accountantdetail
```

### AOW-leeftijdentabel

```text
config/aow_leeftijden.json
    -> aow_engine._laad_aow_tabel
    -> aow_engine.bereken_aow_datum
    -> aow_engine.aow_breuk_jaar
    -> gebruikt door:
       - belasting_engine.netto_uit_bruto
       - cashflow_engine
       - accountantpad
```

## 3. Volledige fiscale configstructuur

### In `BelastingConfig`

| Onderdeel | Velden | Gebruikt door |
| --- | --- | --- |
| `box1_niet_aow` | schijven met `tot`, `tarief` | `bereken_box1_belasting` |
| `box1_aow` | schijven met `tot`, `tarief` | `bereken_box1_belasting` |
| `ahk` | `max_bedrag`, `afbouw_inkomen_van`, `afbouw_pct`, `minimum` | `bereken_ahk`, `bereken_ahk_met_aow` |
| `arbeidskorting` | `max_bedrag`, `afbouw_drempel`, `afbouw_pct`, `minimum` | `bereken_arbeidskorting` |
| `ouderenkorting` | `max_bedrag`, `afbouw_inkomen_van`, `afbouw_pct`, `minimum` | `bereken_ouderenkorting` |
| `alleenstaandeouderenkorting` | idem | `bereken_alleenstaandeouderenkorting` |
| `box3` | vrijstelling, tarief, forfait sparen, forfait overig, disclaimer | `bereken_box3_heffing`, accountantdetail |
| `aow_bedrag` | alleenstaand per maand, gehuwd/samenwonend per maand | `cashflow_engine`, accountantpad |
| `premies` | premiegrens, AOW/Anw/Wlz tarieven | `bereken_premies_volksverzekeringen` |
| `ahk_aow_factor` | factor op AHK-maximum | `bereken_ahk_met_aow` |
| `eigen_woning` | forfaitschijven, tariefsaanpassing, Hillen | `bereken_eigen_woning` |

## 4. Per tarief: bron, gebruik en afhankelijkheden

### 4.1 Box 1 schijven

Bron:

- `config/belasting_2025.json`
- `config/belasting_2026.json`

Gebruikt door:

- `bereken_box1_belasting()`
- accountantpad via `bereken_box1_belasting()`

Afhankelijkheden:

- `aow_breuk_jaar()` bepaalt de weging tussen AOW- en niet-AOW-schijven

Overschrijfbaar via `tarief_periodes`:

- ja, voor grenzen en tarieven van `box1_niet_aow`
- ja, voor grenzen en tarieven van `box1_aow`

Niet overschrijfbaar via `tarief_periodes`:

- de keuze van AOW versus niet-AOW pad zelf niet; alleen de waarden

### 4.2 Premies volksverzekeringen

Bron:

- `premies_volksverzekeringen` in `belasting_YYYY.json`

Gebruikt door:

- `bereken_premies_volksverzekeringen()`
- indirect `netto_uit_bruto()`
- accountantpad rekent premies ook expliciet uit

Afhankelijkheden:

- `is_aow_heel_jaar`
- `premiegrens`

Overschrijfbaar via `tarief_periodes`:

- nee

Gevolg:

- premies kunnen niet per jaarperiode door gebruiker worden gesimuleerd via de
  bestaande override-infrastructuur

### 4.3 Algemene heffingskorting

Bron:

- `algemene_heffingskorting` in `belasting_YYYY.json`

Gebruikt door:

- `bereken_ahk()`
- `bereken_ahk_met_aow()`
- `bereken_totale_heffingskortingen()`
- accountantpad gebruikt deels afwijkende AHK-logica

Afhankelijkheden:

- bruto of box1-grondslag, afhankelijk van pad
- `ahk_aow_factor`
- `aow_breuk`

Overschrijfbaar via `tarief_periodes`:

- `ahk_max`
- `ahk_afbouw_van`
- `ahk_afbouw_pct`
- `ahk_minimum`

Niet overschrijfbaar:

- `ahk_aow_factor`

### 4.4 Arbeidskorting

Bron:

- `arbeidskorting` in `belasting_YYYY.json`

Gebruikt door:

- `bereken_arbeidskorting()`
- `bereken_totale_heffingskortingen()`
- accountantpad

Overschrijfbaar via `tarief_periodes`:

- `ak_max`
- `ak_afbouw_drempel`
- `ak_afbouw_pct`
- `ak_minimum`

### 4.5 Ouderenkorting

Bron:

- `ouderenkorting` in `belasting_YYYY.json`

Gebruikt door:

- `bereken_ouderenkorting()`
- `bereken_totale_heffingskortingen()`
- accountantpad

Overschrijfbaar via `tarief_periodes`:

- `ok_max`
- `ok_afbouw_van`
- `ok_afbouw_pct`
- `ok_minimum`

### 4.6 Alleenstaandeouderenkorting

Bron:

- `alleenstaandeouderenkorting` in `belasting_YYYY.json`

Gebruikt door:

- `bereken_alleenstaandeouderenkorting()`
- `bereken_totale_heffingskortingen()`
- accountantpad

Overschrijfbaar via `tarief_periodes`:

- nee

### 4.7 Box 3

Bron:

- `box3` in `belasting_YYYY.json`

Gebruikt door:

- `bereken_box3_heffing()`
- accountantdetail en `gebruikte_tarieven` payload

Afhankelijkheden:

- partnerstatus
- `spaargeld_fractie`
- saldo begin jaar

Overschrijfbaar via `tarief_periodes`:

- `box3_vrijstelling`
- `box3_tarief`
- `box3_forfait_spaargeld`
- `box3_forfait_overig`

Niet overschrijfbaar:

- disclaimertekst

### 4.8 AOW-bedragen

Bron:

- `aow_bedrag` in `belasting_YYYY.json`

Gebruikt door:

- `cashflow_engine._bereken_jaar()`
- accountantpad `_bereken_jaar_detail()`

Overschrijfbaar via `tarief_periodes`:

- `aow_alleenstaand_pm`
- `aow_gehuwd_pm`

### 4.9 Eigen woning

Bron:

- `eigen_woning` in `belasting_YYYY.json`

Gebruikt door:

- `bereken_eigen_woning()`
- accountantpad

Overschrijfbaar via `tarief_periodes`:

- nee

Gevolg:

- eigen-woningregels zijn niet mee te simuleren via scenario-overrides, terwijl
  box 1-, box 3- en AOW-bedragen dat gedeeltelijk wel zijn

## 5. Exacte overridebare sleutels

De huidige flattening in `config_naar_tariefwaarden()` maakt alleen de volgende
sleutels overridebaar:

### Box 1 niet-AOW

- `box1_niet_aow_s1_tot`
- `box1_niet_aow_s1_tarief`
- `box1_niet_aow_s2_tot`
- `box1_niet_aow_s2_tarief`
- `box1_niet_aow_s3_tarief`

### Box 1 AOW

- `box1_aow_s1_tot`
- `box1_aow_s1_tarief`
- `box1_aow_s2_tot`
- `box1_aow_s2_tarief`
- `box1_aow_s3_tarief`

### AHK

- `ahk_max`
- `ahk_afbouw_van`
- `ahk_afbouw_pct`
- `ahk_minimum`

### Arbeidskorting

- `ak_max`
- `ak_afbouw_drempel`
- `ak_afbouw_pct`
- `ak_minimum`

### Ouderenkorting

- `ok_max`
- `ok_afbouw_van`
- `ok_afbouw_pct`
- `ok_minimum`

### Box 3

- `box3_vrijstelling`
- `box3_tarief`
- `box3_forfait_spaargeld`
- `box3_forfait_overig`

### AOW-bedragen

- `aow_alleenstaand_pm`
- `aow_gehuwd_pm`

## 6. Niet overridebare fiscale velden

De volgende configvelden worden wel gebruikt in berekeningen, maar niet door de
override-engine geflattened:

- `ahk_aow_factor`
- `alleenstaandeouderenkorting.*`
- `premies.premiegrens`
- `premies.aow_tarief_niet_aow`
- `premies.aow_tarief_aow`
- `premies.anw_tarief`
- `premies.wlz_tarief`
- `eigen_woning.forfait_schijven`
- `eigen_woning.tariefsaanpassing_pct`
- `eigen_woning.wet_hillen_pct`

Dit is de belangrijkste functionele beperking van de huidige override-opzet.

## 7. Fallback- en resolutieregels

### Jaarfallback bij ontbrekende config

`laad_tarieven(jaar)` doet:

1. probeer exact jaarbestand
2. anders: neem laatst bekende jaar `<= gevraagd jaar`
3. als dat niet bestaat: neem vroegst beschikbare jaar
4. voeg aanname-/waarschuwingsmelding toe

### Override-resolutie binnen `resolve_tariefwaarden_voor_jaar()`

Per sleutel:

1. als meerdere regels matchen: laatste regel wint
2. als geen regel matcht maar wel historische regels bestaan: laatst geldende
   historische regel rolt door
3. inflatie wordt toegepast vanaf `startjaar`
4. resultaat wordt teruggebouwd naar een nieuwe `BelastingConfig`

### Belangrijke beperking

Omdat niet alle fiscale velden worden geflattened, ontstaat er een gemengd model:

- een deel van de fiscale wereld is jaar-overridable
- een deel blijft hard gekoppeld aan basisconfig

## 8. Concrete inconsistenties en risico’s

### Inconsistentie 1: `ahk_aow_factor`

2025 bevat expliciet `aow_factor`; 2026 niet.

Daardoor valt 2026 terug op de defaultwaarde `1` in `BelastingConfig`.

Gevolg:

- AHK voor AOW-jaren kan zich anders gedragen tussen 2025 en 2026
- dit verschil is inhoudelijk niet via overrides te corrigeren

### Inconsistentie 2: eigen woning buiten override-mechanisme

Eigen woning beïnvloedt de accountantberekening, maar de parameters ervan zijn
niet overridebaar.

Gevolg:

- scenariomutaties kunnen wel box 3 simuleren, maar niet dezelfde mate van
  fiscal-rule-simulatie voor eigen woning

### Inconsistentie 3: premies buiten override-mechanisme

Box 1-schijven kunnen veranderen per override, maar premiegrens en premiepercentages
niet.

Gevolg:

- hypothetische fiscale scenario’s kunnen intern inconsistent worden

### Inconsistentie 4: twee bronnen voor vermogen en woning

`spaargeld_start` / `beleggingen_start` bestaan naast `vermogensitems`.

Gevolg:

- box 3-startverdeling en werkelijke vermogensinvoer kunnen uiteenlopen

## 9. Wat fase 2 oplevert voor het verbeterplan

De tarieflaag is niet slecht georganiseerd, maar wel onvolledig geharmoniseerd.

De drie belangrijkste conclusies zijn:

1. de fiscale basisconfig is centraal en bruikbaar
2. de override-engine dekt slechts een subset van de werkelijk gebruikte fiscale
   parameters
3. de combinatie van legacy vermogen, `vermogensitems` en niet-overridebare
   eigen-woningregels maakt volledige simulatietrouw onmogelijk

## 10. Kortste samenvatting

De applicatie heeft een bruikbare centrale fiscale configlaag, maar de
gebruikersoverrides dekken slechts een deel van de werkelijk gebruikte tarieven
en grondslagen, waardoor fiscale simulaties nu niet volledig consistent
parameteriseerbaar zijn.
