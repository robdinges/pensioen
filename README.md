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
- Simpele API-gedreven UI:
  - minimale Streamlit client (`app_api_client.py`) die via HTTP de API aanroept
  - expliciete Berekenen-knop
  - melding wanneer invoer gewijzigd is sinds de laatste berekening

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

6. Beheer scenario's in het scherm Scenario:
  - kies het standaardscenario via de radioknoppen
  - gebruik de actieknoppen in dezelfde rij om een scenario actief te maken,
    te bewerken of te verwijderen.

7. Vul in het scherm Financiële Planning alle componenten in:
  - **Inkomsten & Uitgaven**: Periodieke inkomsten, pensioenen, uitgaven en inhoudingen
  - **Vermogen & Bezittingen**: Spaargeld, beleggingen, eigen woning, hypotheek, auto's, kunst, etc.
    * Kies bij het type **Eigen woning** voor de woningvelden zoals WOZ-waarde en jaarlijkse waardestijging
    * Kies bij het type **Hypotheek** voor primaire woning, hypotheekrente en einddatum renteaftrek
    * De hypotheek blijft fiscale invoer voor box 1 en telt niet mee als negatieve vermogenspost in de totalen
    * Elk vermogensitem heeft zijn eigen rendement/groei percentage
    * Voor spaargeld en beleggingen is dit het verwachte jaarrendement
    * Voor andere bezittingen is dit waardestijging of afschrijving
  - **Eenmalige Posten**: Eenmalige ontvangsten en uitgaven op specifieke data

8. Open in de app het tabblad Accountantsoverzicht en klik op
  Berekening uitvoeren.

9. Controleer de componenttabel Netto cashflow opgebouwd uit losse
  componenten in het accountantsoverzicht.

10. Exporteer uitgebreide accountantdetail-rapporten voor testcases:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py
```

Voor een specifieke testcase:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_007
```

Output staat standaard in
`tests/fixtures/belasting_testcases/accountant_exports/`.

11. Draai de volledige testcase-validatiepipeline en schrijf het IB 2025-overzicht:

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

12. Beheer belastingtarieven in het scherm Instellingen:
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

Troubleshooting:

- Fout `ModuleNotFoundError: No module named 'pensioen'`:
  start de API met `--app-dir src` zoals hierboven.
- Fout met `dataclass(..., slots=True)` of andere syntax/import issues:
  controleer je interpreter met `python --version` en gebruik Python 3.12+.
