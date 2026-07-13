## Pensioenplanner

Professionele Nederlandse pensioenplanner met dag-nauwkeurige
cashflowprognose voor een huishouden.

## Features

- Bruto-naar-netto berekening voor loon, AOW en pensioen per persoon.
  - 2025 box-1 schijfgrens en premiegrens zijn geijkt op € 40.502 (AOW- en niet-AOW-schijf 1)
  - 2025 algemene heffingskorting volgt Belastingdienst-parameters: max € 3.068, afbouw vanaf € 28.406, afbouw 6,337%; voor heel jaar AOW: max € 1.536 en afbouw 3,170%
  - afbouw van de algemene heffingskorting volgt bruto jaarinkomen als toetsingsbasis
  - fiscale bouwstenen (premies, losse heffingskortingen en totaalkorting) hebben directe unit-tests met grenswaarden en afrondingschecks
  - pensioenbron in hoofdengine en accountantdetail is geharmoniseerd op `Scenario.componenten` (`PENSIOEN_INKOMEN`)
  - expliciete bruto-inkomensopbouw per jaar beschikbaar per persoon (arbeid, AOW, pensioen, overig) plus huishoudtotaal
- Box 3 berekening via forfaitair rendement:
  - spaargelddeel met `forfaitair_spaargeld`
  - overig/beleggingendeel met `forfaitair_overig`
  - belasting over fictief rendement tegen box 3 tarief
  - box 3 gebruikt expliciete peildatumgrondslag uit box-3-belaste vermogensitems; bij afwezigheid geldt legacy fallback
  - rendementsgrondslag blijft expliciet gescheiden (liquide vermogen), zodat box 3 en rendement herleidbaar apart blijven
- Afzonderlijke rendementen voor sparen en beleggen:
  - optioneel twee rendementstarieven instellen (spaarrekening vs. beleggingsportefeuille)
  - vermogenssplitsing gebaseerd op expliciet ingevoerd spaargeld en beleggingen
  - componenten kunnen per regel als sparen of beleggen worden gemarkeerd
  - deze componentmix stuurt zowel de maandelijkse rendementsverdeling als de box 3 verdeling
  - fallback naar uniform rendement als aparte tarieven niet ingesteld
- Scenario-invoer met verstelbare spaargeldfractie voor box 3.
- Eigen woning als expliciete engine-stap tussen bruto inkomen en box 1:
  - fiscale woninginvoer komt primair uit `vermogensitems` (woning/hypotheek), met legacy fallback op `Scenario.eigen_woning`
  - box 1-grondslag bevat de eigen-woningmutatie (forfait, renteaftrek, Hillen)
  - tariefsaanpassing aftrekposten wordt verwerkt in de jaarbelasting van de hoofdengine
- Accountantsoverzicht met volledige component-analyse van netto cashflow:
  - inkomen (na box 1)
  - box 3 heffing op fictief rendement
  - rendement op vermogen
  - inleg en opname (incl. incidentele ontvangsten/uitgaven)
  - gebruikt de actuele vermogens- en eigen-woningbron in plaats van verouderde legacy-weergave
  - toont bij een eenpersoonshuishouden nooit P2-kolommen of P2-bedragen
  - waarschuwt bij handmatig ingevoerde AOW-componenten en filtert deze uit de inkomenssom om dubbeltelling te voorkomen
  - toont de gebruikte bron voor box 3 tarief en forfaiten voor sparen/beleggen
  - gebruikt primair engine-detailoutput (`jaar_samenvatting` en `accountant_detail`) als bron, met alleen compatibiliteitsfallbacks voor legacy datasets
- Scriptmatige accountant-detail export voor validatie:
  - exporteert dezelfde jaar-detailberekening als de accountantspagina naar JSON en Markdown
  - ondersteunt batch-export van alle beschikbare genormaliseerde cases en losse testcase-ID's
  - schrijft een batchsamenvatting met PASS/WARN/FAIL drempels
- Gestructureerde scenario-invoer met meerdere regels per component:
  - extra bruto loon/uitkering
  - inhoudingen (loonbelasting etc.)
  - jaarlijkse huishoudelijke uitgaven
  - eenmalige ontvangsten/uitgaven
  - regels zijn per blok toe te voegen en te verwijderen.
  - typekeuze voor eigen woning, hypotheek, spaargeld, beleggingen en overige bezittingen
  - eigen woningvelden voor WOZ-waarde en jaarlijkse waardestijging
  - hypotheekvelden voor primaire woning, hypotheekrente en einddatum renteaftrek
  - eigen woning en hypotheek blijven fiscale invoer voor de box 1-berekening
  - hypotheek telt niet mee als negatieve vermogenspost in de vermogenssom
- Scenario-overzicht als compacte lijst met acties per rij:
  - eerste kolom toont welk scenario actief is
  - direct bewerken, selecteren en verwijderen vanuit dezelfde rij
  - standaardscenario kiezen via radioknop (geen ster-icoonactie)
- API-first laag (Epic 1 MVP):
  - FastAPI-endpoints voor healthcheck, berekening, scenariovergelijking en Excel-rapportage
  - automatische OpenAPI/Swagger documentatie
  - inheritance-validatie op scenario-lijsten (cycles, orphans, self-parenting)
  - code-normalisatie op API-input voor component- en vermogenscodes (hoofdletter/spatievarianten worden geharmoniseerd)
- Simpele API-gedreven UI:
  - minimale Streamlit client (`app_api_client.py`) die via HTTP de API aanroept
  - expliciete Berekenen-knop
  - melding wanneer invoer gewijzigd is sinds de laatste berekening
  - sidebar met live API-status en handmatige referentie-refresh
  - uitgebreid jaarresultaten-dashboard met KPI's, jaartabel en trendgrafieken
  - jaarresultaten in tabellen worden primair uit engineveld `jaar_samenvatting` opgebouwd
  - aparte tab voor ruwe API JSON-output
- Nieuwe React UI (experimenteel, aparte branch `feature/react-frontend-redesign-wizard`):
  - sectie **Inkomsten / Uitgaven** met tegel-cards voor loon, uitkering, pensioen en eenmalige posten
  - periodieke **Uitgave**-card in dezelfde sectie; wordt als negatieve cashflow verwerkt (buiten box 1/box 3)
  - sectie **Vermogen** met tegel-cards voor sparen, beleggen, eigen woning, overige bezittingen en hypotheek
  - type-afhankelijke invoervelden per card (o.a. begin/einddatum, bedrag, frequentie, groei/inflatie/rente)
  - berekenknop via API (`/api/v1/berekeningen`) met jaarresultaten in tabel/KPI's
  - wizard-shell met persistente stapnavigatie, statusindicatoren en centrale contextbalk
  - automatische local session save/restore in de frontend (zonder handmatige opslagknop)
  - huishouden-stap met toevoegen, hernoemen, verwijderen en wisselen tussen meerdere huishoudens
  - scenario-stap met toevoegen, hernoemen, verwijderen en kiezen van actief scenario per huishouden
  - scenario-stap met dupliceren van actief scenario en aparte invoersnapshots per scenario
  - scenario-stap met basale scenariovergelijking via API (`/api/v1/vergelijkingen`) inclusief KPI-tabel
  - personen-stap met optionele partner (P2), inclusief validatie en correcte payload naar de API
  - periode-stap met jaarvalidatie; berekenen is geblokkeerd tot invoer geldig is
  - rapport-stap met directe Excel-download via API (`/api/v1/rapportages/excel`) op basis van actieve invoer
  - import-stap met MPO-bestandsimport naar pensioen-componenten (CSV, Excel, JSON en PDF)
  - MPO JSON-import vult start- en einddatums robuuster: via leeftijd+geboortedatum en fallback op StandPer wanneer geboortedatum ontbreekt
  - PDF-import loopt via API-endpoint `/api/v1/import/mpo/pdf` en gebruikt de backend-parser voor MPO-PDF's
  - import-validatie in React met preview, compacte samenvatting per persoon, duplicate-waarschuwingen, telling van overgeslagen regels en feedback tijdens import
  - accountant-stap met uitgebreide controle per belastingjaar: jaaroverzicht, grondslagen, heffingskortingen, gebruikte schijven/premies, box-3 parameters en maandtabel voor narekening
  - accountant-stap consumeert primair `accountant_detail` uit de engine-output en reduceert client-side fiscale herberekeningen
  - overzichten in de React UI tonen op jaarniveau (jaartotalen), zonder maandtabel in accountant/resultaten-overzichten
  - accountantsoverzicht bevat per sectie expliciete post-specificaties (definitie + formule) voor controle en narekening
  - accountantsoverzicht toont per controlejaar ook de exacte actieve bronposten (welke lonen, uitkeringen, pensioenen, etc.) inclusief persoon, bedragtype, frequentie en periode
  - accountantsoverzicht toont jaren standaard ingeklapt; per jaar kan detail op verzoek worden uitgeklapt
  - accountantsoverzicht bevat een 1-op-1 narekeningstabel voor IB/PVV/HK (P1):
    * inkomstenbelasting per schijf
    * premies AOW/Anw/Wlz met grondslag en percentage
    * heffingskortingen (AHK, ouderenkorting, alleenstaandeouderenkorting)
    * totaallijn met te betalen bedrag na heffingskortingen
  - tarieffallback per jaar: als een belastingjaar ontbreekt, gebruikt de engine het laatst bekende jaar tot en met dat doeljaar, met expliciete melding in resultaten en accountant-stap

## Usage

1. Installeer dependencies:

```bash
python3 -m pip install -e ".[dev]"
```

Gebruik Python 3.12+ (vereist door dit project).

2. Start de app:

```bash
streamlit run app.py
```

3. Start de API (Epic 1 MVP):

```bash
python -m uvicorn --app-dir src pensioen.api.main:app --reload
```

4. Open de Swagger/OpenAPI documentatie:

```text
http://127.0.0.1:8000/docs
```

5. Start de simpele API-client UI:

```bash
streamlit run app_api_client.py
```

De API-client toont berekeningen primair op jaarbasis in de tab
`Resultaten op Jaarbasis`.

6. Start de nieuwe React UI (op aparte branch):

```bash
cd frontend-react
npm install
npm run dev
```

Open daarna de lokale Vite URL (meestal `http://localhost:5173`).
De default API-basis in de UI is `/api/v1` en wordt lokaal via Vite-proxy
doorgezet naar `http://127.0.0.1:8000`.

Om te berekenen in de React UI:

1. Start eerst de API (`uvicorn ... pensioen.api.main:app`).
2. Start daarna de React UI (`npm run dev` in `frontend-react`).
3. Vul cards in voor inkomsten/uitgaven en vermogen.
4. Klik op `Berekenen` in de contextbalk bovenin.
5. Bekijk resultaten in de sectie `Resultaten op Jaarbasis`.
6. Importeer in de stap `Import` MPO-bestanden voor P1 en optioneel P2.
  Tijdens import toont de UI per persoon voortgang, foutmeldingen en de laatste succesvolle bestandsnaam.
7. Gebruik de stap `Accountant` voor detailcontrole per jaar:
  - controleer bruto-opbouw, heffingskortingen, box-3 grondslag en netto jaaruitkomst
  - bekijk gebruikte belastingtabellen, premiepercentages en AOW-breuken
  - loop de maandregels na inclusief belasting, uitgaven, incidentele posten en vermogen einde maand
  - details komen primair uit de enginevelden `accountant_detail` en `jaar_samenvatting` in de API-response

8. Beheer scenario's in het scherm Scenario:
  - kies het standaardscenario via de radioknoppen
  - gebruik de actieknoppen in dezelfde rij om een scenario actief te maken,
    te bewerken of te verwijderen.

9. Vul in het scherm Financiële Planning alle componenten in:
  - **Inkomsten & Uitgaven**: Periodieke inkomsten, pensioenen, uitgaven en inhoudingen
  - **Vermogen & Bezittingen**: Spaargeld, beleggingen, eigen woning, hypotheek, auto's, kunst, etc.
    * Kies bij het type **Eigen woning** voor de woningvelden zoals WOZ-waarde en jaarlijkse waardestijging
    * Kies bij het type **Hypotheek** voor primaire woning, hypotheekrente en einddatum renteaftrek
    * De hypotheek blijft fiscale invoer voor box 1 en telt niet mee als negatieve vermogenspost in de totalen
    * Elk vermogensitem heeft zijn eigen rendement/groei percentage
    * Voor spaargeld en beleggingen is dit het verwachte jaarrendement
    * Voor andere bezittingen is dit waardestijging of afschrijving
    * Voor de engine zijn `SPAARGELD` en `BELEGGINGEN` leidend als liquide startvermogen; box 3 gebruikt alleen box-3-belaste items als peildatumgrondslag
  - **Eenmalige Posten**: Eenmalige ontvangsten en uitgaven op specifieke data

10. Open in de app het tabblad Accountantsoverzicht en klik op
  Berekening uitvoeren.

11. Controleer de jaarblokken, tarieven, grondslagen en maandregels in
  het accountantsoverzicht voor handmatige narekening.

12. Gebruik in de accountantstap de sectie `Narekening IB/PVV/HK (1-op-1)`
  voor regelmatige vergelijking met de Belastingdienst-opbouw:
  - per schijf: `x% van grondslag = bedrag`
  - per premie: tarief en premiegrondslag
  - per heffingskorting: componentbedragen en totaallijn

13. Exporteer uitgebreide accountantdetail-rapporten voor testcases:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py
```

Voor een specifieke testcase:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_007
```

Output staat standaard in
`tests/fixtures/belasting_testcases/accountant_exports/`.

14. Draai de volledige testcase-validatiepipeline en schrijf het IB 2025-overzicht:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/test_validatie_pipeline.py
```

Voor een enkele testcase zonder het volledige rapport te overschrijven:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/test_validatie_pipeline.py tc_2025_010
```

Alleen als je expliciet een single-case rapport wilt schrijven:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/test_validatie_pipeline.py tc_2025_010 --schrijf-rapport
```

15. Beheer belastingtarieven in het scherm Instellingen:
  - genereer een nieuw `belasting_YYYY.json` bestand op basis van een bestaand jaar
  - sla het bestand direct op naar `config/` vanuit de app of download het als fallback
  - herbereken bestaande resultaten na opslaan om nieuwe tarieven en forfaiten door te voeren

16. Controle voor 2025 AOW + pensioen (Belastingdienst-referentie):
  - verwachte componenten voor scenario met alleenstaande AOW + €50.000 pensioen liggen rond
    `IB box 1 ≈ 13.147`, `PVV ≈ 3.948`, `heffingskortingen ≈ 851`
  - de engine rekent op centniveau en toont daarom soms ±€1 verschil t.o.v. euro-afgeronde Belastingdienstweergave

## Testing

```bash
python3 -m pytest tests/ -q
```

Gerichte Epic 1 testset (directe fiscale bouwstenen + regressie op belastingpad):

```bash
PYTHONPATH=src .venv312/bin/python -m pytest tests/test_fiscale_bouwstenen.py tests/test_belasting_engine.py tests/validatie_aangifte_2025.py
```

Gerichte Epic 2 testset (pensioenbron-harmonisatie + bruto-opbouw):

```bash
PYTHONPATH=src .venv312/bin/python -m pytest tests/test_parser_mpo.py tests/test_cashflow_engine.py tests/test_regression_bugs.py -q
```

Gerichte Epic 3 testset (eigen woning + vermogen/box3 harmonisatie):

```bash
PYTHONPATH=src .venv312/bin/python -m pytest tests/test_scenario_engine.py tests/test_cashflow_engine.py tests/test_regression_bugs.py tests/test_eigen_woning_engine.py -q
```

Gerichte Epic 4/5 testset (engine detail-output + accountant/UI/API ontkoppeling):

```bash
PYTHONPATH=src .venv312/bin/python -m pytest tests/test_regression_bugs.py tests/test_cashflow_engine.py tests/test_api_main.py -q
```

Gerichte API-tests:

```bash
PYTHONPATH=src python3 -m pytest tests/test_api_main.py -q
```

API-contract + regressie op genormaliseerde cases:

```bash
PYTHONPATH=src python3 -m pytest tests/test_api_main.py tests/test_api_regressie_normalized.py -q
```

Strikte validatiepipeline (faalt bij FAIL-cases):

```bash
PYTHONPATH=src:. python3 tools/test_validatie_pipeline.py --strict
```

De regressiebaseline staat in:
`tests/fixtures/belasting_testcases/api_regressie_baseline.json`

In CI is een baseline-wijziging standaard geblokkeerd; alleen expliciet toegestaan met PR-titelmarker `[baseline-update]`.

Troubleshooting:

- Fout `ModuleNotFoundError: No module named 'pensioen'`:
  start de API met `--app-dir src` zoals hierboven.
- Fout met `dataclass(..., slots=True)` of andere syntax/import issues:
  controleer je interpreter met `python --version` en gebruik Python 3.12+.
