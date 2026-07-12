---
post_title: "Analyse Fase 3 Testarchitectuur"
author1: "GitHub Copilot"
post_slug: "analyse-fase-3-testarchitectuur"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "analysis"
  - "tests"
  - "coverage"
  - "regression"
ai_note: "AI-assisted test architecture analysis based on repository inspection; no application code was modified."
summary: "Fase 3 analyse van testdekking per berekening, inclusief directe tests, indirecte dekking, regressies en ontbrekende tests."
post_date: "2026-07-12"
---

<!-- markdownlint-disable MD041 -->

## Doel en afbakening

Deze fase koppelt berekeningen aan tests.

Per berekening wordt aangegeven:

- directe tests
- indirecte tests
- regressietests
- bekende validaties
- belangrijkste ontbrekende tests

## 1. Hoofdobservatie

De codebase test de meeste pure fiscale functies redelijk goed, maar de dekking
neemt sterk af zodra de berekening orkestrerend, scenario-afhankelijk of
UI-gebonden wordt.

In één zin:

**hoe puurder de functie, hoe beter de dekking; hoe dichter bij de accountant- en
UI-logica, hoe slechter de dekking.**

## 2. Matrix: berekening -> tests

| Berekening / functie | Direct getest? | Directe tests | Indirecte tests | Gaten |
| --- | --- | --- | --- | --- |
| `aow_engine.bereken_aow_datum` | Ja | `test_geboren_1947_of_eerder`, `test_geboren_1948`, `test_geboren_1955_aow_leeftijd`, `test_geboren_1963_aow_op_67`, `test_geboren_29_februari`, `test_maandoptelling_over_jaargrens` | `test_partner_veel_jonger_twee_aow_data` | weinig |
| `aow_engine.aow_breuk_jaar` | Ja | `test_heel_jaar_geen_aow`, `test_heel_jaar_aow`, `test_aow_start_1_juli`, `test_aow_start_17_september` | `validatie_aangifte_2025` | weinig |
| `pensioen_engine.bereken_pensioen_maand` | Ja | `test_pensioen_start_midden_september`, `test_pensioen_volledig_lopende_maand`, `test_pensioen_nog_niet_ingegaan`, `test_pensioen_al_gestopt`, `test_partner_pensioen_niet_meegeteld`, `test_indexatie_na_10_jaar`, `test_stoppen_halverwege_maand` | accountant regressies | niet getest in hoofdengine-pad |
| `pensioen_engine.bereken_aow_maand` | Ja | `test_aow_niet_ingegaan`, `test_aow_volledig_lopend`, `test_aow_start_pro_rata` | cashflow- en accountantpad | weinig |
| `pensioen_engine.bereken_arbeid_maand` | Ja | `test_stoppen_halverwege_jaar`, `test_na_stopdatum_geen_inkomen`, `test_voor_stopdatum_vol_salaris` | geen duidelijke productdekking | nauwelijks integratie |
| `belasting_engine.bereken_box1_belasting` | Ja | `test_box1_enkelvoudig_schijf1`, `test_box1_twee_schijven`, `test_box1_drie_schijven`, `test_box1_aow_gerechtigd_heel_jaar`, `test_box1_aow_breuk_50_procent`, `test_box1_nul_inkomen`, `test_box1_negatief_inkomen_wordt_nul` | `validatie_aangifte_2025`, accountantpad | geen detailtests op box1 met eigen woning in hoofdpad |
| `belasting_engine.bereken_premies_volksverzekeringen` | Nee als zelfstandige suite | geen dedicated testmodule | indirect via `netto_uit_bruto`, `validatie_aangifte_2025`, accountantpad | mist directe unitdekking |
| `heffingskorting.bereken_ahk_met_aow` | Ja, beperkt | `test_ahk_aow_heel_jaar_gebruikt_factor_op_maximum`, `test_ahk_aow_deeljaar_gebruikt_gewogen_maximum` | `netto_uit_bruto`, validatie 2025 | weinig grensgevallen |
| `heffingskorting.bereken_ahk` | Nee als zelfstandige suite | geen dedicated test | `validatie_aangifte_2025` | mist directe unitdekking |
| `heffingskorting.bereken_arbeidskorting` | Nee als zelfstandige suite | geen dedicated test | `netto_uit_bruto`, validatie 2025 | mist directe unitdekking en lage/overgangsinkomens |
| `heffingskorting.bereken_ouderenkorting` | Nee als zelfstandige suite | geen dedicated test | `netto_uit_bruto`, validatie 2025 | mist directe unitdekking |
| `heffingskorting.bereken_alleenstaandeouderenkorting` | Nee als zelfstandige suite | geen dedicated test | validatie 2025, accountantpad | mist directe unitdekking |
| `heffingskorting.bereken_totale_heffingskortingen` | Nee | geen dedicated test | `netto_uit_bruto` | mist expliciete unitdekking |
| `belasting_engine.netto_uit_bruto` | Ja | `test_netto_kleiner_dan_bruto`, `test_effectief_tarief_is_percentage`, `test_netto_niet_negatief`, `test_transparantie_tarieven_aanwezig` | cashflow, validatie-adapter, accountantvergelijking | te weinig expliciete scenario’s per kortingstype |
| `belasting_engine.bereken_box3_heffing` | Ja | `test_onder_vrijstelling_geen_heffing`, `test_boven_vrijstelling_positieve_heffing`, `test_dubbele_vrijstelling_met_partner`, `test_box3_verschillende_spaargeld_fracties` | `validatie_aangifte_2025`, accountantpad | weinig randgevallen met afronding en nulfractie |
| `eigen_woning_engine.bereken_eigen_woning` | Ja | `test_forfait_woz_500k`, `test_forfait_woz_onder_75k`, `test_forfait_woz_hoog_boven_1200k`, `test_saldo_negatief_aftrekpost`, `test_saldo_positief_bijtelling`, `test_tariefsaanpassing_hoog_inkomen`, `test_tariefsaanpassing_laag_inkomen`, `test_geen_tariefsaanpassing_positief_saldo`, `test_woning_niet_in_box3`, `test_hillen_80_pct_2025`, `test_hillen_niet_van_toepassing_bij_negatief_saldo`, `test_geen_config_geeft_nul` | accountant regressies | niet gekoppeld aan hoofdengine |
| `vermogen_engine.maandrendement` | Ja, indirect via suite | `test_nul_rendement`, `test_positief_rendement`, `test_samengesteld_rendement_klopt` | `bereken_rente_maand`-tests | geen expliciete negatieve rendementstest |
| `vermogen_engine.bereken_rente_maand` | Ja | `test_geen_saldo_geen_rente`, `test_negatief_saldo_geen_rente`, `test_rente_positief_bij_positief_saldo`, `test_aparte_rendementen_sparen_beleggen`, `test_spaargeld_fractie_scenarios`; plus `test_rendement_sparen_100_procent`, `test_rendement_beleggen_100_procent`, `test_rendement_50_50_split` | cashflow- en accountantpad | weinig integratie met `vermogensitems` |
| `vermogen_engine.bereken_vermogensontwikkeling` | Ja | `test_saldo_groeit_zonder_mutaties`, `test_aantal_resultaten_klopt`, `test_stortingen_verhogen_saldo`, `test_nul_rendement_saldo_stabiel` | geen productgebruik | productfunctie lijkt ongebruikt |
| `vermogen_engine.bereken_vermogen_totaal` | Ja | `test_bereken_vermogen_totaal_enkelvoudig`, `test_bereken_vermogen_totaal_meerdere_items` | geen productgebruik | ongebruikt in productpad |
| `vermogen_engine.bereken_vermogen_box3_belast` | Ja | `test_bereken_vermogen_box3_belast` | geen productgebruik | ongebruikt in productpad |
| `vermogen_engine.bereken_vermogen_per_type` | Ja | `test_bereken_vermogen_per_type` | geen productgebruik | ongebruikt in productpad |
| `vermogen_engine.update_vermogensitems_waarde` | Ja | `test_update_vermogensitems_waarde_overschot`, `test_update_vermogensitems_waarde_tekort`, `test_update_vermogensitems_geen_liquide_items`, `test_update_vermogensitems_pro_rata_verdeling` | geen productgebruik | ongebruikt in productpad |
| `cashflow_engine.bereken_huishouden` | Ja | `test_basisberekening_levert_resultaten`, `test_netto_groter_dan_nul`, `test_partner_veel_jonger_twee_aow_data`, `test_geen_pensioen_alleen_spaargeld`, `test_incidentele_ontvangst_op_exacte_maand`, `test_negatieve_cashflow_jaren_worden_gemarkeerd`, `test_overlappende_inkomstenbronnen`, `test_toekomstig_jaar_tarief_fallback`, `test_huishoudelijke_uitgaven_verlagen_netto`, `test_bruto_component_wordt_belast_en_netto_niet`, `test_overschot_naar_spaarrekening`, `test_tekort_van_spaarrekening`, `test_eenmalige_uitgave_impact` | `test_grafiek_consistency`, `test_grafiek_validator`, regressies, rendement split | geen hoofdpad-test voor eigen woning, geen echte record-inputtest |
| `cashflow_engine._bereken_jaar` | Nee | geen directe test | indirect via `bereken_huishouden` | mist directe granulariteit |
| `cashflow_engine._component_som_maand` | Nee in eigen suite | geen dedicated test | indirect via cashflow en accountanthelper-tests | mist directe edge-case tests |
| `cashflow_engine._incidentele_items_voor_maand` | Nee | geen dedicated test | indirect via cashflowtests | mist directe unittests |
| `inheritance_engine.resolve_scenario` | Ja | `test_resolve_base_scenario`, `test_resolve_1level_inheritance`, `test_resolve_2level_inheritance`, `test_get_override_chain` | scenariovergelijking | geen cashflow-specific override cases |
| `inheritance_engine.validate_inheritance_tree` | Ja | `test_validate_no_warnings_valid_tree`, `test_validate_orphaned_scenario`, `test_validate_circular_dependency` | API 422 tests | goed voor pure validatie |
| `pagina_accountant._bereken_jaar_detail` | Beperkt | regressies in `test_regression_bugs.py`, gebruik in `testcase_validatie.py` | accountantflow | geen volledige dedicated suite, geen golden master op volledige detailstructuur |

## 3. Belangrijkste patronen

### Goed afgedekt

- AOW-datum en AOW-breuk
- box 1 schijfberekening
- box 3 basisformule
- eigen woning als pure functie
- rendement en vermogenshelpers
- hoofd-cashflow bij componentgebaseerde scenario’s

### Redelijk afgedekt maar niet diep genoeg

- `netto_uit_bruto()`
- AHK met AOW-factor
- scenario-overerving
- grafiekconsistentie bovenop cashflow

### Zwak afgedekt

- premies als zelfstandige functie
- totale heffingskortingen als zelfstandige functie
- accountantdetail als volledige audit trail
- hoofdengine met eigen woning
- hoofdengine met echte `PensioenRecord`-keten

## 4. Welke berekeningen zijn nergens direct getest

De volgende functies hebben geen zelfstandige, directe unit-testset:

- `bereken_premies_volksverzekeringen()`
- `bereken_ahk()`
- `bereken_arbeidskorting()`
- `bereken_ouderenkorting()`
- `bereken_alleenstaandeouderenkorting()`
- `bereken_totale_heffingskortingen()`
- `cashflow_engine._bereken_jaar()`
- `cashflow_engine._component_som_maand()`
- `cashflow_engine._incidentele_items_voor_maand()`

Dat betekent niet dat ze ongetest zijn, maar wel dat fouten daarin nu vooral via
indirecte regressies zichtbaar worden.

## 5. Accountantpad: testbeeld

Het accountantpad is het meest risicovol vanuit testarchitectuur.

Wel aanwezig:

- regressies rond P1/P2-breakdown
- regressies rond eigen woning
- regressies rond handmatige AOW-filtering
- regressies rond box 3 resolved forfaiten
- `testcase_validatie.py` gebruikt `_bereken_jaar_detail()` als bron

Niet aanwezig als volwaardige suite:

- systematische test per tussenstap
- expliciete golden master voor volledige accountantoutput
- vergelijking hoofdengine versus accountantdetail op identieke invoer

## 6. Bekende structurele dekkingsgaten

### Gat 1: eigen woning in hoofdengine

`bereken_eigen_woning()` is goed getest als pure functie, maar de hoofdengine
roept die functie niet aan.

Gevolg:

- de testdekking van eigen woning zegt weinig over de juistheid van het
  hoofdresultaat op huishoudniveau

### Gat 2: pensioenrecords in hoofdflow

`bereken_pensioen_maand()` is goed getest, maar `bereken_huishouden()` gebruikt
die functie niet.

Gevolg:

- de geteste pensioenrecordlogica is niet de logica van het hoofdpad

### Gat 3: kortingen als losse componenten

De totaalkorting wordt vooral getest via `netto_uit_bruto()` en validatie 2025.

Gevolg:

- wanneer een individuele korting verandert, is niet direct zichtbaar welke
  subfunctie precies faalt zonder extra analyse

## 7. Welke tests zijn het belangrijkst voor regressie

### Hoge waarde

- `tests/test_cashflow_engine.py`
- `tests/test_belasting_engine.py`
- `tests/test_eigen_woning_engine.py`
- `tests/test_regression_bugs.py`
- `tests/validatie_aangifte_2025.py`

### Middelhoge waarde

- `tests/test_aow_engine.py`
- `tests/test_pensioen_engine.py`
- `tests/test_vermogen_engine.py`
- `tests/test_inheritance_engine.py`
- `tests/test_api_regressie_normalized.py`

## 8. Direct bruikbare conclusies voor herstructurering

Voor een stabiele herstructurering moet de testarchitectuur in deze volgorde
worden aangescherpt:

1. bouw een directe testset voor `bereken_premies_volksverzekeringen()` en de
   losse kortingfuncties
2. bouw een directe testset voor een toekomstige pure accountant-engine
3. voeg vergelijkingstests toe tussen hoofdengine en accountantdetail
4. voeg hoofdengine-tests toe voor eigen woning en hypotheek
5. voeg tests toe die expliciet bewaken welke pensioenbron leidend is

## 9. Kortste samenvatting

De testarchitectuur dekt de pure fiscale bouwstenen redelijk af, maar juist de
samengevoegde detailberekening en de verschillen tussen hoofdengine en
accountantpad zijn nog onvoldoende als eigen rekensysteem getest.
