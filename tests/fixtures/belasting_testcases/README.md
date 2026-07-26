# Belasting Testcases

## Governance

- `raw/` is de menselijke of externe bron.
- `normalized/` wordt uitsluitend uit raw gegenereerd.
- Controleer drift met
  `PYTHONPATH=src:. python3 tools/normalize_testcases.py --check`.
- Bekende externe afwijkingen staan in `bekende_afwijkingen.json` en
  `AFWIJKINGENREGISTER.md`.
- Zie `docs/REGRESSIEPROTOCOL.md` voor wijzigingen aan referenties en
  baselines.

Dit directory bevat testcasebestanden voor validatie van de belastingberekeningen
in het pensioenmodel.

## Doel

De testcaseflow maakt vergelijking mogelijk tussen:
- Invoer (raw testcase)
- Verwachte uitkomst (Belastingdienst referentie)
- Berekende uitkomst (pensioenapp)

Vergelijking gebeurt op drie niveaus:
- Huishoudenstotaal
- Per persoon totaal
- Componentniveau (box 1, premies, kortingen, box 3)

## Directory Structuur

```text
belasting_testcases/
|- raw/
|  |- tc_2025_006.json
|  |- ...
|  |- tc_2025_011.json
|- normalized/
|  |- tc_2025_006_normalized.json
|  |- ...
|  |- tc_2025_011_normalized.json
|- schema.md
|- normalization_report.md
|- validatie_rapport_ib2025.md
|- accountant_exports/
|  |- tc_2025_006_accountant_detail.json
|  |- tc_2025_006_accountant_detail.md
|  |- ...
|  |- batch_summary.md
|- README.md
```

## IB 2025 Set

De huidige IB 2025 validatieset bevat 6 nieuwe cases:
- tc_2025_006: Alleenstaand werkend zonder eigen woning
- tc_2025_007: Alleenstaand werkend met eigen woning
- tc_2025_008: Alleenstaand gepensioneerd (pensioen + AOW) met eigen woning
- tc_2025_009: Paar, beide werkend, met eigen woning
- tc_2025_010: Paar, werkend + gepensioneerd, met eigen woning
- tc_2025_011: Paar, beide gepensioneerd, zonder eigen woning

Afspraken die zijn vastgelegd:
- TC4 wordt met eigen woning gemodelleerd.
- TC6 wordt zonder eigen woning gemodelleerd.

## Workflow

### 1) Raw aanlevering

Plaats of update testcasegegevens in `raw/`.
Gebruik waar mogelijk volledige componentvelden in `verwachte_belasting`.

### 2) Normalisatie

```bash
PYTHONPATH=src:. .venv312/bin/python tools/normalize_testcases.py
```

Output:
- `normalized/*_normalized.json`
- `normalization_report.md`

### 3) Validatie en vergelijking

```bash
PYTHONPATH=src:. .venv312/bin/python tools/test_validatie_pipeline.py
```

Output:
- Terminalresultaten per testcase
- `validatie_rapport_ib2025.md` voor de IB 2025 set (`tc_2025_006` t/m `tc_2025_011`)

### 4) Uitgebreide accountant-export

Batch (default: alle cases uit `normalized/`):

```bash
PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py
```

Specifieke testcase(s):

```bash
PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_007
PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_007 tc_2025_010
```

Aangepaste outputdirectory:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py --output-dir /tmp/accountant_exports
```

Output:
- `accountant_exports/<testcase>_accountant_detail.json` (volledige detaildump)
- `accountant_exports/<testcase>_accountant_detail.md` (samenvatting per testcase)
- `accountant_exports/batch_summary.md` (totaaloverzicht met PASS/WARN/FAIL)

## Rapportage

`validatie_rapport_ib2025.md` bevat per testcase:
- Huishouden: verwacht vs berekend, verschil, status
- Persoon P1/P2: verwacht vs berekend, verschil, status
- Componenten: verwacht vs berekend, verschil, status

Statuslogica:
- PASS: absolute afwijking <= EUR 5
- WARN: absolute afwijking <= EUR 50
- FAIL: absolute afwijking > EUR 50

## Bekende Beperkingen

Voor 2025 zijn er bekende verschillen, vooral bij cases met eigen woning:
- Eigenwoningmodellering is nog niet volledig fiscaal gelijk aan de referentie.
- Dit kan doorwerken in box 1, kortingen en totaalsom.
- Box 3 kan kleine structurele verschillen tonen door modelaannames.

## Snelle Checks

Normalisatie + validatie in volgorde:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/normalize_testcases.py
PYTHONPATH=src:. .venv312/bin/python tools/test_validatie_pipeline.py
```

Alleen een specifieke testcase draaien:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/test_validatie_pipeline.py tc_2025_006
```

Alleen accountant-export draaien voor 1 case:

```bash
PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_006
```
