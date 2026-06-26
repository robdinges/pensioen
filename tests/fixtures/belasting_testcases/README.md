# Belasting Testcases

Dit directory bevat testcases voor validatie van de belastingberekeningen in het pensioenmodel. Elke testcase representeert een concreet huishouden met een bekende of nog te bevestigen belastinguitkomst (bijv. echte aangifte of persona-draft).

---

## Directory Structuur

```
belasting_testcases/
├── raw/                    # Ruwe JSONs zoals aangeleverd
│   ├── tc_2025_001.json   # Verschillende structuren mogelijk
│   ├── tc_2025_002.json
│   ├── tc_2025_003.json   # Persona draft: alleenstaand werkend
│   ├── tc_2025_004.json   # Persona draft: echtpaar met woning/hypotheek
│   └── tc_2025_005.json   # Persona draft: gepensioneerde alleenstaand
├── normalized/             # Genormaliseerde JSONs (uniform schema)
│   ├── tc_2025_001_normalized.json
│   ├── tc_2025_002_normalized.json
│   ├── tc_2025_003_normalized.json
│   ├── tc_2025_004_normalized.json
│   └── tc_2025_005_normalized.json
├── schema.md              # JSON schema documentatie
├── README.md              # Dit bestand
└── normalization_report.md  # Rapport van normalisatie-proces (gegenereerd)
```

---

## Workflow

### 1️⃣ Aanlevering (Iteratief)

Gebruiker levert testcase aan in **elk formaat**:
- Gekopieerde tekst uit browser
- Excel/CSV bestand  
- PDF aangifte
- Handmatig getypte gegevens

**AI converteert** direct naar JSON en slaat op in `raw/`.

**Voorbeeld prompt**:
```
Screen scrape aangifte 2025, alleenstaand AOW:
- Geboortedatum: 15-03-1955
- Pensioen: €86.813
- Vermogen: €500k (40% sparen, 60% beleggen)
- Totaal verschuldigd: €32.177
```

**Output**: `raw/tc_2025_001.json` (flexibele structuur)

---

### 2️⃣ Normalisatie (Na Alle Aanleveringen)

Na verzamelen van **alle testcases**:

```bash
python tools/normalize_testcases.py
```

Dit script:
- ✅ Analyseert alle `raw/*.json` files
- ✅ Uniformeert naar consistent schema (zie [schema.md](schema.md))
- ✅ Vult defaults aan (bijv. `spaargeld_fractie = 0.4`)
- ✅ Valideert verplichte velden
- ✅ Output: `normalized/*.json` files
- 📝 Genereert `normalization_report.md` met warnings

**Handmatige review** nodig:
- ⚠️ Testcases met `_incomplete: true`
- ⚠️ Aannames die gemaakt zijn

---

### 3️⃣ Validatie (Geautomatiseerd)

```bash
PYTHONPATH=src:. /usr/local/bin/python3.11 tools/test_validatie_pipeline.py
```

Voor elke testcase:
1. Laad genormaliseerde JSON
2. Converteer naar Scenario + Persoon objecten
3. Bereken via accountant-engine
4. Vergelijk met `verwachte_belasting`
5. Rapport: ✅ matches / ❌ afwijkingen

**Output**:
- Terminal: Samenvatting per testcase (verwacht, berekend, verschil, status)

---

## Huidige Status (2026-06-26)

- 5 testcases aanwezig in `raw/` en genormaliseerd in `normalized/`.
- Nieuwe 2025 persona-drafts: `tc_2025_003`, `tc_2025_004`, `tc_2025_005`.
- Voor deze 3 persona-drafts zijn `verwachte_belasting`-uitkomsten nog placeholder en nog niet afkomstig uit de Belastingdienst-simulator.
- Laatste validatie-run (pipeline) gaf momenteel 5x `FAIL`:
	- `tc_2025_001`: afwijking -€380
	- `tc_2025_002`: afwijking +€353
	- `tc_2025_003`: placeholder verwacht 0, berekend €41.863
	- `tc_2025_004`: placeholder verwacht 0, berekend €52.583
	- `tc_2025_005`: placeholder verwacht 0, berekend €33.289
- Belangrijke beperking voor exacte fiscale match in 2025:
	- Eigen woning, hypotheekrente en eigenwoningforfait zijn nog niet volledig end-to-end opgenomen in deze testcase-validatieflow.

---

## Testcase Overzicht

| ID | Naam | Jaar | Type | Status | Opmerking |
|----|------|------|------|--------|-----------|
| tc_2025_001 | Alleenstaand AOW-ontvanger 2025 | 2025 | ALLEENSTAAND | ❌ Failed | Referentiecase met kleine structurele afwijking |
| tc_2025_002 | Gehuwd paar - 1 AOW + 1 werkend 2025 | 2025 | GEHUWD | ❌ Failed | Referentiecase met kleine structurele afwijking |
| tc_2025_003 | Plain vanilla alleenstaande werkend 2025 | 2025 | ALLEENSTAAND | ⚠️ Partial | Persona-draft, fiscale uitkomst nog invullen |
| tc_2025_004 | Echtpaar met woning en hypotheek 2025 | 2025 | GEHUWD | ⚠️ Partial | Persona-draft + woning/hypotheek deels nog niet gemodelleerd |
| tc_2025_005 | Gepensioneerde alleenstaande met woning 2025 | 2025 | ALLEENSTAAND | ⚠️ Partial | Persona-draft, AOW/simulatordetail nog invullen |

**Status**:
- 📥 Raw: Ruwe JSON aanwezig
- ✅ Normalized: Genormaliseerd en gevalideerd
- 🔄 Validatie running: Berekening in uitvoering
- ✅ Passed: Validatie geslaagd (binnen tolerantie)
- ⚠️ Partial: Gedeeltelijke match (kleine afwijkingen)
- ❌ Failed: Grote afwijkingen (actie nodig)

*(Deze tabel is handmatig bijgewerkt op 2026-06-26.)*

---

## Data Quality

### Minimaal (Voldoende voor Pensioenplanning)
Alleen huishouden-totalen:
- Totaal verschuldigd (huishouden)
- Bruto inkomen totaal
- Vermogen totaal

**Voordeel**: Voldoende voor cashflow-validatie over tijd  
**Gebruik**: Pensioenplanning, vermogensontwikkeling

### Gedeeltelijk
Hoofdcomponenten huishouden-niveau:
- Totaal verschuldigd
- Box 1 totaal
- Box 3 totaal
- Premies totaal

**Voordeel**: Basale belastingvalidatie mogelijk

### Volledig (Aanbevolen voor Belastingtechnische Validatie)
Alle tussenresultaten **per persoon**:
- Bruto inkomens per persoon
- Box 1 IB vóór kortingen per persoon
- Premies (AOW, Anw, Wlz) per persoon
- Heffingskortingen per persoon
- Box 3 detail (grondslag, fictief rendement, heffing)

**Voordeel**: Vindt exact waar afwijking ontstaat (cascading errors detecteren)  
**Gebruik**: Belastingtechnische validatie, debuggen tariefperiodes

---

## Toleranties

Bij validatie worden deze toleranties gehanteerd:

| Component | Tolerantie | Reden |
|-----------|------------|-------|
| Bruto inkomens | €1 | Exacte input |
| Box 1 IB | €1 | Schijfberekening exact |
| Premies (AOW/Anw/Wlz) | €0.50 | Kleine bedragen, streng |
| Heffingskortingen | €1 | Afbouw-berekeningen |
| Box 3 heffing | €10 | Forfaitaire rendementen hebben ruis |
| **Totaal verschuldigd** | €5 | Eindresultaat |

**Logica**:
- **Match** (binnen tolerantie): ✅ Groen
- **Kleine afwijking** (1-2x tolerantie): ⚠️ Geel + melding
- **Grote afwijking** (>2x tolerantie): ❌ Rood + suggestie voor aanpassing

---

## Isolatie

Elke testcase is **volledig geïsoleerd**:
- Eigen Scenario in `.sessie.json` met naam `Test_{testcase_naam}`
- Geen overerving (`parent_naam = None`)
- Geen overlap met gebruiker-scenario's

Dit voorkomt dat testcases elkaar beïnvloeden of normale gebruikers-data verstoren.

---

## Veelgestelde Vragen

**Q: Moet elke testcase exact hetzelfde formaat hebben?**  
A: Nee! Bij aanlevering mag elk formaat. Normalisatie-script uniformeert later.

**Q: Wat als ik geen tussenresultaten heb?**  
A: Minimaal `totaal_verschuldigd` is vereist. Meer = betere validatie, maar niet verplicht.

**Q: Kan ik testcases voor verschillende jaren?**  
A: Ja! Elk jaar kan apart (2025, 2026, etc.). Config wordt automatisch geladen per jaar.

**Q: Hoe voeg ik een nieuwe testcase toe?**  
A: Lever aan in chat → AI parseert → Opslaan in `raw/` → Later normaliseren.

**Q: Wat als validatie faalt?**  
A: Rapport toont exact welke component afwijkt + suggestie (bijv. "Check vermogen-split").

---

## Tools

| Script | Functie | Input | Output |
|--------|---------|-------|--------|
| `tools/convert_aanlevering_to_json.py` | Parse screen scrape → JSON | Tekst/Excel/CSV | `raw/*.json` |
| `tools/analyze_raw_testcases.py` | Analyseer raw JSONs | `raw/*.json` | Console rapport |
| `tools/normalize_testcases.py` | Normaliseer alle testcases | `raw/*.json` | `normalized/*.json` + rapport |
| `tools/test_validatie_pipeline.py` | Valideer alle testcases | `normalized/*.json` | Terminal rapport |

---

## Volgende Stappen

1. **Vul Belastingdienst-simulator uitkomsten in** voor `tc_2025_003`, `tc_2025_004`, `tc_2025_005`.
2. **Werk `verwachte_belasting` bij** in raw JSONs (liefst met zoveel mogelijk tussenresultaten).
3. **Run normalisatie**: `python tools/normalize_testcases.py`
4. **Review warnings** in `normalization_report.md`
5. **Run validatie**: `PYTHONPATH=src:. /usr/local/bin/python3.11 tools/test_validatie_pipeline.py`
6. **Analyseer afwijkingen** en pas model/config aan indien nodig

---

## Bijdragen

Nieuwe testcases altijd welkom! Hoe meer diversiteit (alleenstaand/paar, werkend/AOW, eigen huis, verschillende jaren), hoe robuuster het model.

**Contact**: Via chat message met "Nieuwe testcase:" prefix.
