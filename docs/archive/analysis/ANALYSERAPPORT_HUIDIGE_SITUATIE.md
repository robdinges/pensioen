---
post_title: "Analyserapport Huidige Situatie Pensioenapplicatie"
author1: "GitHub Copilot"
post_slug: "analyserapport-huidige-situatie-pensioenapplicatie"
microsoft_alias: "n/a"
featured_image: ""
categories:
  - "Documentation"
tags:
  - "analysis"
  - "python"
  - "pension"
  - "tax"
  - "architecture"
ai_note: "AI-assisted codebase analysis based on repository inspection; no application code was modified."
summary: "Volledige analyse van de huidige pensioen- en belastingapplicatie: architectuur, rekenketen, data, tarieven, tests, UI, risico's en refactor-kansen."
post_date: "2026-07-12"
archived: true
---

<!-- markdownlint-disable MD041 MD060 -->

## Scope en methode

Deze analyse is gebaseerd op directe inspectie van de huidige codebase,
configuratiebestanden, tests, UI-lagen en bestaande documentatie.

De analyse omvat:

- backendmodules in `src/pensioen`
- Streamlit UI in `app.py` en `src/pensioen/ui`
- FastAPI-laag in `src/pensioen/api`
- React frontend in `frontend-react/src`
- configuratie in `config/`
- tests in `tests/` en `validatie/`

Er zijn geen wijzigingen gedaan aan applicatiecode, testcode of configuratie.
Alleen dit rapport is toegevoegd.

## 1. Projectstructuur

### Directorystructuur

| Pad | Doel |
|---|---|
| `app.py` | Hoofd-Streamlit UI |
| `app_api_client.py` | Simpele Streamlit API-client boven FastAPI |
| `src/pensioen/models` | Domeinmodellen en outputmodellen |
| `src/pensioen/calculations` | Rekenengines en scenariovergelijking |
| `src/pensioen/tax` | Belasting-, AOW-, heffingskorting- en eigen-woninglogica |
| `src/pensioen/parsers` | MPO-import en conversie naar interne modellen |
| `src/pensioen/api` | FastAPI requests, normalisatie en serialisatie |
| `src/pensioen/reports` | Excel-rapportage |
| `src/pensioen/ui` | Streamlit-pagina’s, flow, helpers, sessieopslag |
| `src/pensioen/validators` | Inputvalidatie en outputconsistentie |
| `frontend-react/src` | Experimentele React UI |
| `config` | Jaarafhankelijke fiscale configuratie en AOW-tabel |
| `tests` | Unit-, integratie- en regressietests |
| `tools` | Validatie-, normalisatie- en exporthulpmiddelen |
| `validatie` | Vergelijking met externe fiscale validatie/adapters |

### Belangrijkste modules en verantwoordelijkheden

| Module | Verantwoordelijkheid |
|---|---|
| `models/scenario.py` | Centrale invoercontainer voor scenario, componenten, vermogen, eigen woning en tariefoverrides |
| `models/component.py` | Periodieke inkomens-, uitgaven- en inhoudingscomponenten |
| `models/vermogensitem.py` | Vermogensitems zoals sparen, beleggen, woning en hypotheek |
| `models/cashflow.py` | Resultaatmodellen per maand en per jaar |
| `calculations/cashflow_engine.py` | Hoofdorkestratie van de volledige huishoudberekening |
| `calculations/pensioen_engine.py` | Pro-rata pensioen-, AOW- en arbeidsmaandbedragen |
| `calculations/vermogen_engine.py` | Rendement, vermogensgroei en vermogenshulpfuncties |
| `calculations/scenario_engine.py` | Vergelijking van meerdere scenario’s |
| `calculations/inheritance_engine.py` | Resolutie en validatie van scenario-overerving |
| `tax/belasting_loader.py` | Laden van belastingconfiguraties en tariefoverrides |
| `tax/belasting_engine.py` | Box 1, premies, netto-uit-bruto en box 3 |
| `tax/heffingskorting.py` | AHK, arbeidskorting, ouderenkorting en alleenstaandeouderenkorting |
| `tax/aow_engine.py` | AOW-datum en AOW-breuk per jaar |
| `tax/eigen_woning_engine.py` | Eigenwoningforfait, renteaftrek, Hillen en tariefsaanpassing |
| `api/main.py` | Dikke request-validatie, dunne API-laag, doorroep naar engine |
| `ui/pagina_accountant.py` | Accountantsoverzicht met eigen herberekening en detailtabellen |
| `ui/pagina_resultaten.py` | Grafieken, tabellen en consistentievalidatie |
| `parsers/parser_mpo.py` | Import van CSV, Excel, JSON en PDF naar `PensioenRecord` |
| `reports/rapport_engine.py` | Excel-export van cashflow en scenariovergelijking |

### Afhankelijkheden tussen modules

```text
UI / React / API
    -> Scenario / Persoon / Component / VermogensItem modellen
    -> belasting_loader.laad_tarieven(_bereik)
    -> cashflow_engine.bereken_huishouden
        -> inheritance_engine.resolve_scenario
        -> aow_engine.bereken_aow_datum
        -> component.bedrag_per_maand_actief
            -> periodieke_waarde.selecteer_periodieke_waarde
        -> pensioen_engine.bereken_aow_maand
        -> belasting_engine.netto_uit_bruto
            -> aow_engine.aow_breuk_jaar
            -> bereken_box1_belasting
            -> bereken_premies_volksverzekeringen
            -> heffingskorting.bereken_totale_heffingskortingen
        -> belasting_engine.bereken_box3_heffing
        -> vermogen_engine.bereken_rente_maand
    -> reports.rapport_engine.genereer_rapport

Streamlit accountantspagina
    -> herroept zelfstandig tax-, pensioen- en vermogensengines
    -> gebruikt niet direct de maandregels uit cashflow_engine
```

### Opvallende structurele bevindingen

- `src/pensioen/ui/pagina_scenario.py` bestaat, maar `app.py` routeert deze pagina
  niet in `STAP_NAAR_PAGINA`. De flow kent wel een scenariostap.
- `records1` en `records2` worden in `cashflow_engine.py` wel geaccepteerd,
  maar in de hoofdengine niet gebruikt voor de berekening.
- De React UI bouwt standaard requests met `records1: []` en `records2: []`.

## 2. Architectuur

### Lagen

| Laag | Bestanden | Functie |
|---|---|---|
| Presentatie | `app.py`, `src/pensioen/ui/*`, `frontend-react/src/*` | Invoer, visualisatie, interactie |
| API | `src/pensioen/api/*` | HTTP-contract, normalisatie en serialisatie |
| Orkestratie | `calculations/cashflow_engine.py`, `scenario_engine.py` | Samenstellen van de rekenketen |
| Business rules | `tax/*`, `calculations/*`, delen van `models/*` | Fiscale en financiële logica |
| Domeinmodel | `models/*` | Typen, validatie en helpermethoden |
| Invoer/uitvoer | `parsers/*`, `reports/*`, `validators/*` | Import, export en validatie |
| Configuratie/data | `config/*` | Jaarafhankelijke tabellen en parameters |

### Waar zitten de business rules

| Onderwerp | Hoofdlocatie |
|---|---|
| Box 1 en netto/bruto | `tax/belasting_engine.py` |
| Heffingskortingen | `tax/heffingskorting.py` |
| AOW-leeftijd en AOW-breuk | `tax/aow_engine.py` |
| Eigen woning | `tax/eigen_woning_engine.py` |
| Box 3 | `tax/belasting_engine.py` |
| Jaar- en maandorkestratie | `calculations/cashflow_engine.py` |
| Pensioen- en AOW-maandbedragen | `calculations/pensioen_engine.py` |
| Vermogensrendement | `calculations/vermogen_engine.py` |
| Scenariologica en overerving | `models/scenario.py`, `calculations/inheritance_engine.py` |

### Waar worden tarieven opgehaald

- `tax/belasting_loader.py`
- bronbestanden: `config/belasting_2025.json`, `config/belasting_2026.json`
- AOW-leeftijden uit `config/aow_leeftijden.json`

### Waar zit de UI

| UI | Locatie |
|---|---|
| Streamlit hoofdapp | `app.py` |
| Streamlit pagina’s | `src/pensioen/ui/*.py` |
| Streamlit API-client | `app_api_client.py` |
| React frontend | `frontend-react/src/*` |

### Helpers en utilities

| Type | Locatie |
|---|---|
| Session persistence | `ui/sessie_persistentie.py` |
| Scenario context | `ui/scenario_context.py` |
| Flow management | `ui/flow_context.py` |
| Formatters | `ui/helpers.py`, `ui/style.py` |
| API referentietabellen | `api/referentietabellen.py` |
| JSON serialisatie | `api/serialisatie.py` |

### Sterk gekoppelde onderdelen

| Koppeling | Observatie |
|---|---|
| `cashflow_engine` <-> `belasting_engine` | Kernkoppeling; logisch maar centraal en zwaar |
| `cashflow_engine` <-> `Scenario` | Scenario bevat zowel invoerdata als berekende afleidingen |
| `pagina_accountant.py` <-> tax/calculation modules | UI herberekent direct businesslogica |
| `app.py` <-> session state | Streamlit gebruikt `st.session_state` als primaire datastore |
| React <-> API payloadvorm | Payloadmapping is handmatig en niet contractgedreven |

### Wat idealiter losgekoppeld zou moeten worden

- accountantdetailberekening uit de UI naar een backendservice of outputmodule
- scenario-mutaties uit de UI naar een pure domeinservice
- tariefoverrides uit `app.py` en accountantspagina naar één centrale resolver
- React payloadmapping naar een expliciet gedeeld contract of schema-afleiding
- session-state-opslag naar een expliciete opslaglaag

## 3. Berekeningen

### Overzichtstabel van berekeningen

| Naam | Bestand | Functie | Input | Output | Tarieven/data | Afhankelijk van | Gebruikt door |
|---|---|---|---|---|---|---|---|
| Periodeselectie | `models/periodieke_waarde.py` | `selecteer_periodieke_waarde` | periodes, peildatum | actieve periode | geen | `_is_actief` | `FinancieelComponent.bedrag_per_maand_actief` |
| Waarde op datum | `models/periodieke_waarde.py` | `get_waarde_op_datum` | periodes, peildatum | Decimal/None | geen | `selecteer_periodieke_waarde` | generieke helper |
| Component actief? | `models/component.py` | `is_actief` | jaar, maand | bool | componentdatums | periodeselectie | `cashflow_engine`, accountant UI |
| Bedrag per maand | `models/component.py` | `bedrag_per_maand_actief` | jaar, maand | Decimal | groei_pct | periodeselectie | `cashflow_engine`, accountant UI |
| Startvermogen | `models/scenario.py` | `totaal_vermogen_start` | scenario | Decimal | scenario legacy velden | geen | `cashflow_engine`, resultaten UI |
| Box 3 spaargeldfractie start | `models/scenario.py` | `bereken_spaargeld_fractie_startvermogen` | scenario | Decimal | legacy box3 veld | startvermogen | `cashflow_engine` |
| Jaarlijkse inleg totaal | `models/scenario.py` | `totaal_jaarlijkse_inleg` | scenario | Decimal | scenario velden | geen | `cashflow_engine` |
| Dynamische spaargeldfractie | `models/scenario.py` | `bereken_spaargeld_fractie_op_datum` | peildatum | Decimal | componenten, legacy startwaarden | componentbedragen | `cashflow_engine` |
| Vermogenswaarde item | `models/vermogensitem.py` | `waarde_op_datum` | peildatum | Decimal | groei_pct, WOZ, hypotheekrente | itemeigenschappen | scenariomethoden, vermogenshelpers |
| AOW-datum | `tax/aow_engine.py` | `bereken_aow_datum` | geboortedatum | datum | `config/aow_leeftijden.json` | `_zoek_aow_leeftijd` | `cashflow_engine`, accountant UI, personenpagina |
| AOW-breuk jaar | `tax/aow_engine.py` | `aow_breuk_jaar` | geboortedatum, jaar | Decimal | AOW-tabel | `bereken_aow_datum` | `belasting_engine` |
| Pensioen maand | `calculations/pensioen_engine.py` | `bereken_pensioen_maand` | record, jaar, maand | Decimal | record indexatie | `_bruto_per_maand` | accountant UI |
| AOW maand | `calculations/pensioen_engine.py` | `bereken_aow_maand` | geboortedatum, aow_datum, bedrag, jaar, maand | Decimal | AOW maandbedrag | geen | `cashflow_engine`, accountant UI |
| Arbeid maand | `calculations/pensioen_engine.py` | `bereken_arbeid_maand` | jaarsalaris, stopdatum, jaar, maand | Decimal | geen | geen | beperkt direct gebruik |
| Maandrendement | `calculations/vermogen_engine.py` | `maandrendement` | jaarrendement_pct | Decimal | geen | float-tussenstap | `bereken_rente_maand` |
| Rente maand | `calculations/vermogen_engine.py` | `bereken_rente_maand` | saldo, rendementen, fractie | Decimal | scenario rendementen | `maandrendement` | `cashflow_engine`, accountant UI |
| Vermogensontwikkeling | `calculations/vermogen_engine.py` | `bereken_vermogensontwikkeling` | saldo, mutaties, jaren | lijst per maand | geen | `bereken_rente_maand` | alleen tests |
| Vermogen totaal | `calculations/vermogen_engine.py` | `bereken_vermogen_totaal` | items, peildatum | Decimal | itemdata | `waarde_op_datum` | alleen tests |
| Box 3 belast vermogen | `calculations/vermogen_engine.py` | `bereken_vermogen_box3_belast` | items, peildatum | Decimal | itemdata | `waarde_op_datum` | alleen tests |
| Vermogen per type | `calculations/vermogen_engine.py` | `bereken_vermogen_per_type` | items, peildatum | dict | itemdata | `waarde_op_datum` | alleen tests |
| Vermogensitems updaten | `calculations/vermogen_engine.py` | `update_vermogensitems_waarde` | items, peildatum, cashflow | lijst items | itemdata | `waarde_op_datum` | alleen tests |
| Schijfbepaling | `tax/belasting_engine.py` | `_bereken_schijven` | inkomen, schijven | Decimal | `box1_*` schijven | geen | `bereken_box1_belasting` |
| Box 1 belasting | `tax/belasting_engine.py` | `bereken_box1_belasting` | bruto, config, aow_breuk | Decimal | `box1_niet_aow`, `box1_aow` | `_bereken_schijven` | `netto_uit_bruto` |
| Premies volksverzekeringen | `tax/belasting_engine.py` | `bereken_premies_volksverzekeringen` | bruto, config, is_aow | tuple premies | premiesconfig | geen | `netto_uit_bruto` |
| AHK | `tax/heffingskorting.py` | `bereken_ahk` | inkomen, config | Decimal | AHK-config | `_afbouw_korting` | totale korting |
| AHK met AOW | `tax/heffingskorting.py` | `bereken_ahk_met_aow` | inkomen, config, aow_breuk | Decimal | AHK-config, aow_factor | `_afbouw_korting_met_maximum` | `netto_uit_bruto` |
| Arbeidskorting | `tax/heffingskorting.py` | `bereken_arbeidskorting` | arbeidsinkomen, config | Decimal | arbeidskorting-config | geen | `netto_uit_bruto` |
| Ouderenkorting | `tax/heffingskorting.py` | `bereken_ouderenkorting` | inkomen, config, is_aow | Decimal | ouderenkorting-config | `_afbouw_korting` | `netto_uit_bruto` |
| Alleenstaandeouderenkorting | `tax/heffingskorting.py` | `bereken_alleenstaandeouderenkorting` | inkomen, config, flags | Decimal | AOK-config | `_afbouw_korting` | `netto_uit_bruto` |
| Totale kortingen | `tax/heffingskorting.py` | `bereken_totale_heffingskortingen` | bruto, arbeidsinkomen, config, flags | Decimal | alle kortingconfig | bovengenoemde functies | `netto_uit_bruto` |
| Netto uit bruto | `tax/belasting_engine.py` | `netto_uit_bruto` | bruto, arbeidsinkomen, config, geboortedatum, jaar | `BelastingResultaat` | box 1, premies, kortingen | AOW-breuk, box1, premies, kortingen | `cashflow_engine`, accountant UI |
| Box 3 heffing | `tax/belasting_engine.py` | `bereken_box3_heffing` | spaarsaldo, config, partnerflag, fractie | tuple heffing/disclaimer | box 3 config | geen | `cashflow_engine`, accountant UI |
| Eigenwoningforfait | `tax/eigen_woning_engine.py` | `_bereken_eigenwoningforfait` | WOZ, config | Decimal | eigen_woning.forfait_schijven | geen | `bereken_eigen_woning` |
| Tariefsaanpassing eigen woning | `tax/eigen_woning_engine.py` | `_bereken_tariefsaanpassing` | aftrek, inkomen, config | Decimal | `tariefsaanpassing_pct` | box1 schijven | `bereken_eigen_woning` |
| Eigen woning totaal | `tax/eigen_woning_engine.py` | `bereken_eigen_woning` | `EigenWoningInvoer`, config | `EigenWoningResultaat` | eigen woning config | forfait, tariefsaanpassing | accountant UI |
| Maandcomponentsom | `calculations/cashflow_engine.py` | `_component_som_maand` | scenario, categorie, persoon, jaar, maand | Decimal | componentdata | component.bedrag_per_maand_actief | `_bereken_jaar` |
| Incidentele maanditems | `calculations/cashflow_engine.py` | `_incidentele_items_voor_maand` | scenario, jaar, maand | tuple | incidentele_items | geen | `_bereken_jaar` |
| Jaarberekening | `calculations/cashflow_engine.py` | `_bereken_jaar` | personen, scenario, config, saldo | `JaarResultaat` | alle jaarconfig | vrijwel alle engines | `bereken_huishouden` |
| Huishoudberekening | `calculations/cashflow_engine.py` | `bereken_huishouden` | scenario, personen, jaren, configs | `HuishoudCashflow` | jaarconfigs | scenario-resolutie, `_bereken_jaar` | UI, API, rapporten, vergelijking |
| Scenario samenvatting | `calculations/scenario_engine.py` | `_bereken_samenvatting` | scenario, cashflow, persoon1 | `ScenarioResultaat` | geen | cashflow output | `vergelijk_scenarios` |
| Scenariovergelijking | `calculations/scenario_engine.py` | `vergelijk_scenarios` | scenario’s, personen, jaren | `ScenarioVergelijking` | geladen tarieven | `bereken_huishouden` | UI, API, rapportage |

### Dependency tree van berekeningen

```text
bereken_huishouden
  -> resolve_scenario
  -> _bereken_jaar
     -> aow_engine.bereken_aow_datum
     -> _component_som_maand
        -> FinancieelComponent.bedrag_per_maand_actief
           -> selecteer_periodieke_waarde
     -> pensioen_engine.bereken_aow_maand
     -> belasting_engine.netto_uit_bruto
        -> aow_engine.aow_breuk_jaar
           -> bereken_aow_datum
        -> bereken_box1_belasting
           -> _bereken_schijven
        -> bereken_premies_volksverzekeringen
        -> heffingskorting.bereken_totale_heffingskortingen
           -> bereken_ahk_met_aow
           -> bereken_arbeidskorting
           -> bereken_ouderenkorting
           -> bereken_alleenstaandeouderenkorting
     -> belasting_engine.bereken_box3_heffing
     -> scenario.bereken_spaargeld_fractie_startvermogen
     -> scenario.bereken_spaargeld_fractie_op_datum
     -> vermogen_engine.bereken_rente_maand
        -> maandrendement
```

### Belangrijkste observaties bij de berekeningen

- `cashflow_engine` gebruikt pensioenrecords niet inhoudelijk; pensioen in de
  hoofdflow komt uit `Scenario.componenten`.
- `pagina_accountant.py` gebruikt pensioenrecords wel opnieuw via
  `pensioen_engine.bereken_pensioen_maand`.
- Daardoor bestaan feitelijk twee rekenpaden voor pensioeninformatie.

## 4. Rekenketen

### Hoofdpad vanuit Streamlit

```text
Gebruiker
    -> app.py
    -> laad_tarieven_bereik
    -> resolve_tariefwaarden_voor_jaar
    -> bereken_huishouden
       -> resolve_scenario
       -> _bereken_jaar per jaar
          -> bereken_aow_datum P1/P2
          -> _component_som_maand per categorie/persoon/maand
             -> FinancieelComponent.bedrag_per_maand_actief
                -> selecteer_periodieke_waarde
          -> bereken_aow_maand
          -> netto_uit_bruto per persoon
             -> aow_breuk_jaar
             -> bereken_box1_belasting
             -> bereken_premies_volksverzekeringen
             -> bereken_totale_heffingskortingen
          -> bereken_box3_heffing
          -> bereken_rente_maand
          -> maak MaandResultaat
       -> maak JaarResultaat
    -> sla HuishoudCashflow op in session state
    -> pagina_resultaten / pagina_rapport / pagina_accountant
```

### Hoofdpad vanuit FastAPI

```text
React / API-client
    -> POST /api/v1/berekeningen
    -> BerekeningRequest.normaliseer_codes
    -> _bouw_belasting_configs
       -> laad_tarieven_bereik
       -> resolve_tariefwaarden_voor_jaar
    -> bereken_huishouden
    -> naar_json_compatibel
    -> JSON response
    -> ResultsSection / AccountantSection / ReportSection
```

### Alternatief rekenpad: accountantspagina

De accountantspagina volgt niet het hoofdpad van de reeds berekende
`HuishoudCashflow`, maar herberekent jaar voor jaar opnieuw met:

- `aow_engine.bereken_aow_datum`
- `pensioen_engine.bereken_aow_maand`
- `pensioen_engine.bereken_pensioen_maand`
- `belasting_engine.netto_uit_bruto`
- `belasting_engine.bereken_box3_heffing`
- `bereken_eigen_woning`
- `vermogen_engine.bereken_rente_maand`

Dat is architectonisch de grootste afwijking in de codebase.

## 5. Tarieven en data

### Tariefoverzicht

| Tarief/dataset | Bestand | Formaat | Jaarafhankelijk | Hardcoded? | Waar gebruikt | Directe gebruiksplaatsen |
|---|---|---|---|---|---|---|
| Box 1 schijven niet-AOW | `config/belasting_2025.json`, `config/belasting_2026.json` | JSON | ja | nee | box 1 belasting | `belasting_loader`, `belasting_engine`, tests |
| Box 1 schijven AOW | idem | JSON | ja | nee | box 1 belasting | idem |
| Premiegrens | idem | JSON | ja | nee | premies volksverzekeringen | `belasting_engine`, tests |
| AOW-premietarief | idem | JSON | ja | nee | premieberekening | `belasting_engine`, tests |
| Anw-premie | idem | JSON | ja | nee | premieberekening | `belasting_engine`, tests |
| Wlz-premie | idem | JSON | ja | nee | premieberekening | `belasting_engine`, tests |
| Algemene heffingskorting | idem | JSON | ja | nee | AHK-berekening | `heffingskorting`, `belasting_engine`, tests |
| `aow_factor` op AHK | vooral 2025 aanwezig | JSON | ja | nee | AHK met AOW | `heffingskorting`, `belasting_engine`, tests |
| Arbeidskorting | idem | JSON | ja | nee | arbeidskorting | `heffingskorting`, `belasting_engine`, tests |
| Ouderenkorting | idem | JSON | ja | nee | ouderenkorting | `heffingskorting`, `belasting_engine`, tests |
| Alleenstaandeouderenkorting | idem | JSON | ja | nee | AOW-korting alleenstaand | `heffingskorting`, `belasting_engine`, tests |
| Box 3 vrijstelling | idem | JSON | ja | nee | box 3 heffing | `belasting_engine`, `cashflow_engine`, tests |
| Box 3 tarief | idem | JSON | ja | nee | box 3 heffing | `belasting_engine`, `cashflow_engine`, tests |
| Box 3 forfait spaargeld | idem | JSON | ja | nee | box 3 heffing en accountantpayload | `belasting_engine`, `cashflow_engine`, tests |
| Box 3 forfait overig | idem | JSON | ja | nee | box 3 heffing en accountantpayload | `belasting_engine`, `cashflow_engine`, tests |
| AOW-bedrag alleenstaand | idem | JSON | ja | nee | AOW-maandbedrag | `cashflow_engine`, accountant UI, tests |
| AOW-bedrag gehuwd/samenwonend | idem | JSON | ja | nee | AOW-maandbedrag | `cashflow_engine`, accountant UI, tests |
| Eigenwoningforfait schijven | idem | JSON | ja | nee | eigen woning | `eigen_woning_engine`, accountant UI, tests |
| Tariefsaanpassing eigen woning | idem | JSON | ja | nee | eigen woning | `eigen_woning_engine`, tests |
| Wet Hillen percentage | idem | JSON | ja | nee | eigen woning | `eigen_woning_engine`, tests |
| AOW-leeftijdtabel | `config/aow_leeftijden.json` | JSON | ja | nee | AOW-datum en AOW-breuk | `aow_engine`, tests |
| MPO importdata | uploads, `tests/fixtures/mpo_partner*.csv` | CSV/Excel/JSON/PDF | nee | nee | import | parser en tests |
| Genormaliseerde fiscale testcases | `tests/fixtures/belasting_testcases/*` | JSON | ja | nee | regressie/validatie | tests en tools |
| Inflatie gebruiker | `Scenario.inflatie_pct` | modelwaarde | ja, per scenario | user input | rapport/UI | scenario, React payload |
| Rendementen sparen/beleggen | `Scenario` of `VermogensItem.groei_pct` | modelwaarde | ja, per scenario | user input | rendement en box 3-fractie | `cashflow_engine`, `vermogen_engine`, UI |

### Belastingtabellen, AOW, heffingskortingen en box 3

| Categorie | Centrale bron | Opmerking |
|---|---|---|
| Belastingtabellen | `config/belasting_YYYY.json` | goed centraal opgezet |
| AOW-leeftijden | `config/aow_leeftijden.json` | goed centraal opgezet |
| Heffingskortingen | `config/belasting_YYYY.json` | centraal, maar interpretatie in code vereenvoudigd |
| Box 3 | `config/belasting_YYYY.json` | centraal, met expliciete disclaimer |
| Inflatie | scenario- of UI-veld | niet centraal als dataset |
| Pensioenparameters | `PensioenRecord`, componenten | verspreid over model en parser |
| Eigen woning | deels config, deels scenario/vermogensitems | gemengd domeinmodel |

### Dubbele of inconsistente tarieven/data

| Bevinding | Analyse |
|---|---|
| `algemene_heffingskorting.aow_factor` ontbreekt in 2026-config | loader valt dan terug op `1`; gedrag verschilt inhoudelijk met 2025 |
| `alleenstaandeouderenkorting` is in 2025 feitelijk niet-afbouwend en in 2026 wel afbouwend | kan inhoudelijk juist zijn, maar is in code/documentatie als indicatief gemarkeerd en dus risicovol |
| tariefoverrides dekken niet alle fiscale velden | `resolve_tariefwaarden_voor_jaar` flatteert geen premies, geen `ahk_aow_factor`, geen eigen woning, geen alleenstaandeouderenkorting |
| spaargeld/beleggingen bestaan zowel legacy als nieuw | `spaargeld_start`/`beleggingen_start` leven naast `vermogensitems` |
| eigen woning bestaat dubbel | `Scenario.eigen_woning` naast `VermogensItem(type=EIGEN_WONING/HYPOTHEEK)` |

### Wat eenvoudig centraal gemaakt kan worden

- alle tariefoverrides, inclusief premies en eigen woning
- volledige box 3-bronselectie op basis van `vermogensitems`
- pensioenbronkeuze: ofwel alleen records, ofwel alleen componenten
- inflatie- en groeiregels per componenttype in één parametriseerbare laag

## 6. Testarchitectuur

### Overzicht van testbestanden

| Testbestand | Doel | Geteste modules | Afgedekte functionaliteit | Wat ontbreekt grotendeels |
|---|---|---|---|---|
| `tests/test_aow_engine.py` | AOW-leeftijd en breuken | `tax/aow_engine.py` | AOW-datum, schrikkeljaar, deeljaar | weinig configuratiefouten |
| `tests/test_api_main.py` | API-contract | `api/main.py`, `api/schemas.py` | endpoints, normalisatie, foutcodes | geen zware validatie/edge-load |
| `tests/test_api_regressie_normalized.py` | regressie op fixtures | API + baseline | contract- en outputstabiliteit | foutlokalisatie is beperkt |
| `tests/test_audit.py` | auditlog | `models/audit.py` | entry’s en serialisatie | weinig functionele impact |
| `tests/test_belasting_engine.py` | fiscal core | `belasting_engine`, `belasting_loader` | box 1, box 3, AHK, fallbacks | beperkte grensgevallen over jaren |
| `tests/test_cashflow_engine.py` | hoofdengine | `cashflow_engine.py` | netto, componenten, box 3, vermogen | geen echte pensioenrecord-integratie |
| `tests/test_eigen_woning_engine.py` | eigen woning | `eigen_woning_engine.py` | forfait, tariefsaanpassing, Hillen | vooral config-afhankelijk |
| `tests/test_grafiek_consistency.py` | resultatenconsistentie | `cashflow`, grafieklogica | bronopbouw en nettocontrole | geen UI-rendering |
| `tests/test_grafiek_validator.py` | validator | `validators/grafiek_validator.py` | beperkte validatiecase | zeer smalle dekking |
| `tests/test_inheritance_engine.py` | scenario-overerving | `inheritance_engine.py` | chain, cycle, orphan, overrides | geen end-to-end cashflow per override |
| `tests/test_parser_mpo.py` | MPO import | `parser_mpo.py`, `validator.py` | CSV/Excel/JSON/PDF parsing | echte PDF-randgevallen beperkt |
| `tests/test_pensioen_engine.py` | pensioenlogica | `pensioen_engine.py` | pro-rata, indexatie, stopmomenten | beperkt op record-naar-engine-flow |
| `tests/test_periodieke_waarde.py` | periode-selectie | `periodieke_waarde.py` | overlap, hiaat, open intervallen | goed geïsoleerd |
| `tests/test_regression_bugs.py` | historische bugs | gemengd, inclusief accountant UI | regressies, accountantspecifieke fouten | testbestand is breed en zwaar |
| `tests/test_rendement_split.py` | rendementssplit | `vermogen_engine.py`, scenariofractie | sparen/beleggen verdeling | weinig randgevallen |
| `tests/test_scenario_context.py` | UI context | `ui/scenario_context.py` | actieve scenarioselectie | kleine dekking |
| `tests/test_scenario_engine.py` | scenariovergelijking en helpers | `scenario_engine.py`, `scenario.py` | samenvattingen, eigen woning sync | beperkte businessdiepte |
| `tests/test_sessie_persistentie.py` | session save/load | `ui/sessie_persistentie.py` | schrijven/herstellen | geen corruptie/herstel onder stress |
| `tests/test_vermogen_engine.py` | vermogenshelpers | `vermogen_engine.py` | rendement, mutaties, helpers | productgebruik van helpers ontbreekt |
| `tests/test_vermogensitem.py` | modelberekening | `vermogensitem.py` | waardering, validatie, verkoop | geen end-to-end integratie |
| `tests/validatie_aangifte_2025.py` | fiscale validatie | validatiepipeline | baseline/aangiftevergelijking | beperkte scope naar 2025 |

### Functioneel coverage-overzicht

- ✅ AOW-datum en AOW-breuk
- ✅ box 1 schijven
- ✅ box 3 vrijstelling en forfait
- ✅ heffingskortingen
- ✅ eigen woning
- ✅ scenario-overerving
- ✅ MPO parsing
- ✅ session persistence basisgedrag
- ✅ cashflow basispad met componenten
- ✅ regressies op bekende bugs
- ❌ Streamlit UI-flow end-to-end
- ❌ React componenttests
- ❌ accountantspagina als zelfstandige functionele module
- ❌ echte multi-user/session-isolation
- ❌ negatieve rendementen in productflow
- ❌ uitgebreide grenswaarden rond datums en overlap in gecombineerde scenario’s
- ❌ contracttests tussen React en API over payloadversies

### Belangrijkste testgat

De accountantspagina bevat veel businesslogica, maar heeft geen eigen geïsoleerde
moduletests als primaire bron van waarheid. De bestaande regressietests dekken
alleen enkele bekende bugs en niet het volledige rekenoppervlak.

## 7. UI-analyse

### Streamlit schermen

| Scherm | Functie | Toont data | Roept berekeningen aan? | Businesslogica in UI? |
|---|---|---|---|---|
| Personen | persoonsinvoer | namen, geboortedata, partner | AOW-datum indicatief | beperkt |
| Pensioengegevens | MPO import | records, validatiemeldingen | parse/validatie | middel |
| Scenario | scenario CRUD | scenario’s, default, parent | geen fiscale berekening | middel |
| Componenten | inkomsten/uitgaven/vermogen | tiles en forms | geen hoofdcalculatie | middel |
| Resultaten | grafieken/tabellen | jaar- en grafiekdata | nee, gebruikt bestaande cashflow | laag |
| Accountant | detailoverzicht | jaar- en maanddetails, tarieven | ja, uitgebreide herberekening | hoog |
| Rapport | Excel-download | rapportactie | doorroep naar rapportage | laag |
| Instellingen | tarieven en beheer | configuratie | geen kernberekening | laag |

### React schermen/secties

| Component/sectie | Rol | Businesslogica |
|---|---|---|
| `App.jsx` | centrale state, scenario- en huishoudenbeheer | hoog voor UI-state, geen fiscale logica |
| `WizardSidebar` | stapnavigatie | laag |
| `ContextTopBar` | context en berekenactie | laag |
| `MpoImportSection` | importpreview en upload | middel |
| `ComponentsSection` | componentbeheer | laag-middel |
| `ScenarioSection` | scenariobeheer | middel |
| `ResultsSection` | resultaatweergave | laag |
| `AccountantSection` | presentatie van API-resultaten | laag |
| `ReportSection` | rapportaanvraag | laag |
| `plannerCore.js` | payloadmapping en aggregatie | middel |

### Waar businesslogica ten onrechte in de UI zit

- `pagina_accountant.py`: fiscale herberekening, eigen woning, box 3,
  heffingskortingen en pensioenlogica
- `app.py`: tariefoverrides en herberekening bij scenario-switch
- `pagina_import.py`: conversie van records naar scenario-componenten
- `pagina_componenten.py`: synchronisatie van eigen woning vanuit vermogensitems
- `frontend-react/src/planner/plannerCore.js`: handmatige API-payloadmapping,
  inclusief gemiddelden voor rendementen en typeconversies

### React-specifieke bevinding

De React UI importeert MPO-gegevens vooral voor preview en state, maar de
hoofdrequest naar de backend bevat standaard `records1: []` en `records2: []`.
De rekeninput komt daar dus uit `componenten` en `vermogensitems`, niet uit
`PensioenRecord`-lijsten.

## 8. Datastromen

```text
Gebruikersinput
    -> UI-state / session_state
    -> Pydantic modellen (Persoon, Scenario, Component, VermogensItem)
    -> tarieflading + optional overrides
    -> cashflow_engine / accountant-herberekening
    -> HuishoudCashflow / detaildicts
    -> Streamlit tabellen en grafieken / API JSON / Excel
```

### Waar gegevens worden aangepast

| Punt | Mutatie |
|---|---|
| `pagina_import.py` | vervangt pensioencomponenten P1/P2 op actief scenario |
| `Scenario.migreer_legacy_vermogen` | voegt impliciet vermogensitems toe |
| `Scenario.sync_eigen_woning_uit_vermogensitems` | schrijft afgeleide fiscale woningdata terug |
| `BerekeningRequest.normaliseer_codes` | normaliseert API-payload vóór modelbouw |
| `cashflow_engine` | bouwt resultaatstructuren op, maar muteert inputscenario niet bewust |
| `app.py` / React state | slaan resultaten en UI-context persistente op |

### Kritische datastroomobservaties

- Streamlit importeert MPO-records en zet die direct om naar componenten.
- `st.session_state["records_p1"]` en `records_p2` worden volgens comments niet
  meer gebruikt, maar de pagina toont nog wel de telling uit die keys.
- De accountantspagina gebruikt zowel scenario-componenten als losse records in
  een eigen pad, wat de datastroom minder eenduidig maakt.

## 9. Domeinmodel

### Belangrijkste objecten

| Object | Eigenschappen | Verantwoordelijkheid | Relaties |
|---|---|---|---|
| `Persoon` | naam, geboortedatum, heeft_partner | identificeert deelnemer | input voor AOW en belastingen |
| `PensioenRecord` | uitvoerder, regeling, type, ingangsdatum, einddatum, bruto_per_jaar, indexaties | ruwe pensioenimport | kan worden omgezet naar component |
| `FinancieelComponent` | categorie, persoon, bedrag, frequentie, bedrag_type, groei, datums | periodieke cashflow | hangt in `Scenario.componenten` |
| `VermogensItem` | type, aanschafwaarde, groei, box3_belast, woning/hypotheekvelden | waardeontwikkeling en fiscale typering | hangt in `Scenario.vermogensitems` |
| `IncidenteelItem` | datum, bedrag, omschrijving | eenmalige cashflow | hangt in `Scenario.incidentele_items` |
| `EigenWoningData` | WOZ, rente, schuld begin/eind, overige kosten | legacy fiscale woningbron | hangt in `Scenario.eigen_woning` |
| `TariefPeriodeItem` | sleutel, periode, waarde, inflatie | override op configwaarden | hangt in `Scenario.tarief_periodes` |
| `Scenario` | naam, parent, overrides, componenten, vermogen, box 3, inflatie | centrale scenario-invoer | relationeel hart van de app |
| `MaandResultaat` | bruto, netto, belasting, uitgaven, vermogen | resultaat per maand | onderdeel van `JaarResultaat` |
| `JaarResultaat` | maandlijst, totals, tariefmetadata | aggregatie per jaar | onderdeel van `HuishoudCashflow` |
| `HuishoudCashflow` | scenarionaam, jaren, aannames | topresultaat | gebruikt door UI en rapport |
| `BelastingConfig` | box1, box3, AOW, kortingen, premies, eigen woning | jaarconfiguratie | geladen uit JSON |

### Belangrijkste relaties

```text
Scenario
  -> componenten: list[FinancieelComponent]
  -> vermogensitems: list[VermogensItem]
  -> incidentele_items: list[IncidenteelItem]
  -> eigen_woning: EigenWoningData
  -> tarief_periodes: list[TariefPeriodeItem]

HuishoudCashflow
  -> jaren: list[JaarResultaat]
     -> maanden: list[MaandResultaat]
```

## 10. Mogelijke technische schuld

### Concrete bevindingen

| Type | Bevinding |
|---|---|
| Zeer lang bestand | `frontend-react/src/App.jsx` heeft 1315 regels |
| Zeer lang bestand | `src/pensioen/ui/pagina_accountant.py` heeft 1082 regels |
| Lang bestand | `src/pensioen/calculations/cashflow_engine.py` heeft 521 regels |
| Lang bestand | `src/pensioen/tax/belasting_loader.py` heeft 504 regels |
| Lang testbestand | `tests/test_regression_bugs.py` heeft 470 regels |
| Dubbele logica | accountantspagina herberekent de kernbusinesslogica |
| Dubbel model | legacy vermogen plus `vermogensitems` |
| Dubbel model | `Scenario.eigen_woning` plus woning/hypotheek in `vermogensitems` |
| Potentieel dode productcode | `bereken_vermogensontwikkeling`, `bereken_vermogen_totaal`, `bereken_vermogen_box3_belast`, `bereken_vermogen_per_type`, `update_vermogensitems_waarde` worden in `src/` niet aangeroepen |
| Orphaned UI-pad | `pagina_scenario.py` bestaat maar is niet gekoppeld in `app.py` |
| TODO | `validatie/belasting_vergelijking/pensioen_adapter.py` bevat TODO over dividendaftrek in box 3 |
| Tijdelijke oplossingen | comments en fallbacks rond legacy velden en gemigreerde structuren |

### Copy-paste-achtige patronen

- maandelijkse component- en incidentele-itemlogica komt zowel in
  `cashflow_engine.py` als in `pagina_accountant.py` terug
- tariefoverride-resolutie zit in `app.py` én via API-helper `_bouw_belasting_configs`
- eigen-woningbron wordt op meerdere plekken gesynchroniseerd in plaats van één
  read-only domeinbron te hebben

## 11. Mogelijke foutenbronnen

| Risico | Waarom risico |
|---|---|
| Afrondingen op maand versus jaar | `jaarbelasting / 12` en maandelijkse afronding kunnen cumulatieve verschillen geven |
| Decimal met float-tussenstap | `maandrendement` en `waarde_op_datum` gebruiken float voor exponenten |
| Maand/jaarconversie | componentfrequenties en pro-rata berekeningen mengen jaarbedragen en maandbedragen |
| Datumlogica | AOW, pensioeningang, einddata en periodieke waarden zijn gevoelig voor daggrenzen |
| Netto/bruto mix | `inkomen_componenten_netto` loopt buiten box 1, maar lijkt visueel op gewoon inkomen |
| Partnerlogica | verdeling van eigen woning wordt hard 50/50 gedaan |
| Belastingtabellen | toekomstjaren vallen terug op laatste bekende jaar; inhoudelijk bruikbaar maar risicovol |
| Legacy en nieuwe vermogensmodellen naast elkaar | kans op afwijkende grondslagen voor box 3 en vermogen |
| Box 3 peildatum versus maandverdeling | box 3 gebruikt startvermogen, rendement gebruikt dynamische fractie per maand |
| Records versus componenten | hoofdengine gebruikt records niet, accountantspagina wel |
| Session state als bron | stale state en half bijgewerkte objecten zijn mogelijk |
| Mutable objecten | scenario’s en componenten worden in UI rechtstreeks gemuteerd |
| React payloadmapping | handmatige veldmapping kan ongemerkt afwijken van backendmodel |
| Tariefoverrides onvolledig | sommige fiscale velden zijn overridebaar, andere niet |
| Accountantspagina als tweede waarheid | fixes in hoofdengine hoeven niet automatisch daar te landen |

## 12. Refactor-kansen

### Hoog

- accountantdetailberekening uit de UI halen en onderbrengen in backend/outputlaag
- pensioenbron harmoniseren: hoofdengine en accountantspagina moeten dezelfde bron gebruiken
- legacy vermogen en `vermogensitems` samenvoegen of legacy definitief uitfaseren
- eigen woning één bron geven, bij voorkeur `vermogensitems` met afgeleide read model
- tariefoverrides uitbreiden naar alle fiscale parameters of expliciet beperken

### Middel

- `App.jsx` opdelen in state, orchestration en view-componenten
- `cashflow_engine.py` opdelen in aparte stappen voor inkomen, belasting, box 3,
  vermogen en outputassemblage
- Streamlit session-state mutaties centreren in services/helpers
- scenario CRUD uit UI-bestand halen
- fiscale detail-output standaardiseren als DTO i.p.v. losse dicts

### Laag

- formatteringshelpers centraliseren
- consistente naamgeving rond P1/P2/Huishouden afdwingen
- dode vermogenshelpers verwijderen of in productie gaan gebruiken
- rapportgenerator uitbreiden met accountantdetail als dat een functionele wens is

## 13. Accountantspagina (inventarisatie)

### Welke informatie al beschikbaar is

| Onderdeel | Beschikbaar? | Bron |
|---|---|---|
| invoercomponenten | ja | `Scenario.componenten` |
| incidentele posten | ja | `Scenario.incidentele_items` |
| box 1 tarieven | ja | `BelastingConfig` |
| premies | ja | `BelastingConfig.premies` |
| box 3 parameters | ja | `BelastingConfig.box3` |
| AOW-breuk | ja | `aow_engine.aow_breuk_jaar` |
| eigen woning bron | ja, maar dubbel | `vermogensitems` en `Scenario.eigen_woning` |
| tussenstappen belasting | gedeeltelijk | `BelastingResultaat.gebruikte_tarieven` |
| bronposten per jaar | ja | accountantspagina stelt ze zelf samen |
| wetgevingsverwijzingen | beperkt | vooral toelichtingen in JSON/comments |

### Welke informatie ontbreekt of versnipperd is

| Onderdeel | Status |
|---|---|
| eenduidige bron van pensioeninput | ontbreekt |
| formele wetsartikelen per berekening | grotendeels ontbrekend |
| standaard backend-DTO voor accountantdetail | ontbreekt |
| volledige audit trail van input -> tussenstap -> uitkomst | ontbreekt |
| machineleesbare bronherkomst van overrides | gedeeltelijk aanwezig |
| maanddetail uit hoofdengine inclusief eigen woning | ontbreekt in hoofdpad |

### Wat automatisch gegenereerd kan worden

- gebruikte tarieven per jaar en per persoon
- bronposten per categorie en persoon
- box 3 grondslag, vrijstelling en forfaiten
- kortingenspecificatie uit `BelastingResultaat.gebruikte_tarieven`
- AOW-breuk en tariefjaar-fallbackmeldingen
- verschil tussen hoofdengine-uitkomst en accountantdetail als controlevlag

## 14. Testbaarheid

### Beoordeling per hoofdcalculatie

| Berekening | Geïsoleerd testbaar? | Toelichting |
|---|---|---|
| `selecteer_periodieke_waarde` | Ja | pure functie |
| `FinancieelComponent.bedrag_per_maand_actief` | Ja | modelmethode, geen externe afhankelijkheden |
| `VermogensItem.waarde_op_datum` | Ja | pure berekening per item |
| `bereken_aow_datum` | Ja | alleen JSON-config |
| `aow_breuk_jaar` | Ja | alleen AOW-datumlogica |
| `bereken_pensioen_maand` | Ja | pure recordberekening |
| `bereken_aow_maand` | Ja | pure datum-/bedragberekening |
| `bereken_rente_maand` | Ja | pure functie |
| `bereken_box1_belasting` | Ja | pure functie met config |
| `bereken_premies_volksverzekeringen` | Ja | pure functie met config |
| `bereken_totale_heffingskortingen` | Ja | pure functie met config |
| `bereken_box3_heffing` | Ja | pure functie met config |
| `bereken_eigen_woning` | Ja | pure functie met config |
| `_bereken_jaar` | Nee | hangt af van scenario, personen, config, models en meerdere engines |
| `bereken_huishouden` | Nee | orkestrator over jaren, scenario-resolutie en configset |
| `vergelijk_scenarios` | Nee | hangt af van hoofdengine en tarieflading |
| accountant-jaarherberekening | Nee | zit in UI, heeft veel gekoppelde afhankelijkheden |

### Waarom sommige berekeningen niet volledig geïsoleerd testbaar zijn

- te veel domeinobjecten worden tegelijk vereist
- fiscale config, scenario en UI-afgeleide data lopen door elkaar
- de accountantspagina zit in een presentatiemodule en niet in een pure service
- de hoofdengine maakt een brede orchestratie-test nodig in plaats van kleine
  stepwise contracttests

### Ideale opsplitsing

- `cashflow_engine`: splits naar income builder, tax allocator, wealth updater,
  result assembler
- accountantdetail: extract naar `calculations/accountant_engine.py`
- eigen woning: read model uit vermogensitems, zonder mutatie van scenario

## 15. Eindconclusie

De applicatie heeft een duidelijke domeinfocus, bruikbare centrale fiscale
configuratie en een redelijk compleet testpakket voor de kern van box 1, box 3,
AOW, eigen woning en scenario-overerving. De scheiding tussen domeinmodellen,
fiscale engines en outputmodellen is op hoofdlijnen herkenbaar en herbruikbaar.
Dat is de belangrijkste sterke basis.

De grootste risico’s zitten niet in een volledig ontbrekende architectuur, maar in
duplicatie en parallelle waarheden. De hoofdengine rekent met componenten en
jaartotalen, terwijl de accountantspagina een groot deel opnieuw berekent in de
UI. Daarnaast bestaan legacy en nieuwe modellen voor vermogen en eigen woning
naast elkaar. Pensioenrecords zijn in de hoofdflow niet meer leidend, maar leven
nog wel als API- en accountant-invoer. Dat vergroot de kans op subtiele
afwijkingen tussen schermen, exports en validaties.

De hoogste bugkans zit daardoor in grensvlakken: datumlogica, afrondingen,
box-3-grondslag, partnerverdeling van eigen woning, en verschillen tussen
React-, Streamlit- en accountantpaden. De eerste prioriteit zou moeten liggen bij
het terugbrengen naar één bron van waarheid voor de detailberekening, één bron
voor vermogen/eigen woning en één consistent pensioeninvoerpad. Daarna volgt het
uitbreiden van tests op de plekken waar nu vooral regressies of indirecte dekking
bestaan.

## Volwassenheidsoverzicht

| Onderdeel | Volwassenheid (1-10) | Risico | Prioriteit |
|---|---:|---|---|
| Berekeningen | 7 | Middel-hoog door dubbele paden | Hoog |
| Data & tarieven | 7 | Middel door legacy/override-onvolledigheid | Hoog |
| Testen | 7 | Middel door UI/accountant-gaten | Hoog |
| UI | 6 | Hoog door businesslogica in UI en dubbele frontends | Hoog |
| Architectuur | 6 | Hoog door parallelle waarheden | Hoog |
| Onderhoudbaarheid | 5 | Hoog door grote bestanden en duplicatie | Hoog |

## Top 20 verbeterpunten

1. Verplaats de accountantdetailberekening uit `pagina_accountant.py` naar een gedeelde backendmodule.
2. Maak `cashflow_engine` en accountantdetail afhankelijk van exact dezelfde maandregels.
3. Harmoniseer pensioeninput: kies één bron van waarheid voor berekening.
4. Faseer legacy velden `spaargeld_start` en `beleggingen_start` uit of laat ze alleen read-only migreren.
5. Breng eigen woning terug tot één invoerbron en één fiscale projectie.
6. Breid tariefoverrides uit naar premies, AHK AOW-factor, eigen woning en alleenstaandeouderenkorting.
7. Schrijf gerichte tests voor accountantdetail als zelfstandige service.
8. Voeg end-to-end tests toe voor Streamlit of vervang deze UI gefaseerd door één frontend.
9. Voeg componenttests of integratietests toe voor de React frontend.
10. Splits `frontend-react/src/App.jsx` op in orchestration, scenariobeheer, import en resultaten.
11. Splits `cashflow_engine.py` op in kleinere pure stappen met contracttests.
12. Maak de Streamlit flow consistent door de scenariopagina werkelijk in de flow op te nemen of expliciet te verwijderen.
13. Verwijder of activeer ongebruikte vermogenshulpfuncties in productiecode.
14. Introduceer een formele accountant-DTO met invoer, grondslagen, tussenstappen en uitkomsten.
15. Maak session-state mutaties centraler en voorspelbaarder.
16. Voeg expliciete validatie toe op conflictsituaties tussen records, componenten en vermogensitems.
17. Beperk directe mutatie van scenario-objecten vanuit UI-lagen.
18. Maak fallback- en aannamegedrag van tarieven explicieter zichtbaar in alle UI’s en exports.
19. Leg wetgevingsbron of bronverwijzing per fiscale berekening structureel vast.
20. Maak een architectuurkeuze tussen langdurige ondersteuning van twee UI’s of consolidatie naar één voorkeursfrontend.
