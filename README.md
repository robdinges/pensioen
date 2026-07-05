## Pensioenplanner

Professionele Nederlandse pensioenplanner met dag-nauwkeurige
cashflowprognose voor een huishouden.

## Features

- Bruto-naar-netto berekening voor loon, AOW en pensioen per persoon.
  - afbouw van de algemene heffingskorting volgt bruto jaarinkomen als toetsingsbasis
- Box 3 berekening via forfaitair rendement:
  - spaargelddeel met `forfaitair_spaargeld`
  - overig/beleggingendeel met `forfaitair_overig`
  - belasting over fictief rendement tegen box 3 tarief
- Afzonderlijke rendementen voor sparen en beleggen:
  - optioneel twee rendementstarieven instellen (spaarrekening vs. beleggingsportefeuille)
  - vermogenssplitsing gebaseerd op expliciet ingevoerd spaargeld en beleggingen
  - componenten kunnen per regel als sparen of beleggen worden gemarkeerd
  - deze componentmix stuurt zowel de maandelijkse rendementsverdeling als de box 3 verdeling
  - fallback naar uniform rendement als aparte tarieven niet ingesteld
- Scenario-invoer met verstelbare spaargeldfractie voor box 3.
- Accountantsoverzicht met volledige component-analyse van netto cashflow:
  - inkomen (na box 1)
  - box 3 heffing op fictief rendement
  - rendement op vermogen
  - inleg en opname (incl. incidentele ontvangsten/uitgaven)
  - gebruikt de actuele vermogens- en eigen-woningbron in plaats van verouderde legacy-weergave
  - toont bij een eenpersoonshuishouden nooit P2-kolommen of P2-bedragen
  - waarschuwt bij handmatig ingevoerde AOW-componenten en filtert deze uit de inkomenssom om dubbeltelling te voorkomen
  - toont de gebruikte bron voor box 3 tarief en forfaiten voor sparen/beleggen
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
  - personen-stap met optionele partner (P2), inclusief validatie en correcte payload naar de API
  - periode-stap met jaarvalidatie; berekenen is geblokkeerd tot invoer geldig is
  - rapport-stap met directe Excel-download via API (`/api/v1/rapportages/excel`) op basis van actieve invoer
  - import-stap met MPO-bestandsimport naar pensioen-componenten (CSV, Excel en JSON in React; PDF volgt)
  - import-validatie in React met preview, duplicate-waarschuwingen en telling van overgeslagen regels

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

7. Beheer scenario's in het scherm Scenario:
  - kies het standaardscenario via de radioknoppen
  - gebruik de actieknoppen in dezelfde rij om een scenario actief te maken,
    te bewerken of te verwijderen.

8. Vul in het scherm Financiële Planning alle componenten in:
  - **Inkomsten & Uitgaven**: Periodieke inkomsten, pensioenen, uitgaven en inhoudingen
  - **Vermogen & Bezittingen**: Spaargeld, beleggingen, eigen woning, hypotheek, auto's, kunst, etc.
    * Kies bij het type **Eigen woning** voor de woningvelden zoals WOZ-waarde en jaarlijkse waardestijging
    * Kies bij het type **Hypotheek** voor primaire woning, hypotheekrente en einddatum renteaftrek
    * De hypotheek blijft fiscale invoer voor box 1 en telt niet mee als negatieve vermogenspost in de totalen
    * Elk vermogensitem heeft zijn eigen rendement/groei percentage
    * Voor spaargeld en beleggingen is dit het verwachte jaarrendement
    * Voor andere bezittingen is dit waardestijging of afschrijving
  - **Eenmalige Posten**: Eenmalige ontvangsten en uitgaven op specifieke data

9. Open in de app het tabblad Accountantsoverzicht en klik op
  Berekening uitvoeren.

10. Controleer de componenttabel Netto cashflow opgebouwd uit losse
  componenten in het accountantsoverzicht.

11. Exporteer uitgebreide accountantdetail-rapporten voor testcases:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py
```

Voor een specifieke testcase:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_007
```

Output staat standaard in
`tests/fixtures/belasting_testcases/accountant_exports/`.

12. Draai de volledige testcase-validatiepipeline en schrijf het IB 2025-overzicht:

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

13. Beheer belastingtarieven in het scherm Instellingen:
  - genereer een nieuw `belasting_YYYY.json` bestand op basis van een bestaand jaar
  - sla het bestand direct op naar `config/` vanuit de app of download het als fallback
  - herbereken bestaande resultaten na opslaan om nieuwe tarieven en forfaiten door te voeren

## Testing

```bash
python3 -m pytest tests/ -q
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
