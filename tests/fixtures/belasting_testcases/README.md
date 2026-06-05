# Belasting Testcases

Dit directory bevat testcases voor validatie van de belastingberekeningen in het pensioenmodel. Elke testcase representeert een concreet huishouden met bekende belastinguitkomst (bijv. echte aangifte).

---

## Directory Structuur

```
belasting_testcases/
├── raw/                    # Ruwe JSONs zoals aangeleverd
│   ├── tc_2025_001.json   # Verschillende structuren mogelijk
│   ├── tc_2025_002.json
│   └── tc_2026_001.json
├── normalized/             # Genormaliseerde JSONs (uniform schema)
│   ├── tc_2025_001_normalized.json
│   └── tc_2025_002_normalized.json
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
python tests/run_all_testcases.py
```

Voor elke testcase:
1. Laad genormaliseerde JSON
2. Converteer naar Scenario + Persoon objecten
3. Bereken via accountant-engine
4. Vergelijk met `verwachte_belasting`
5. Rapport: ✅ matches / ❌ afwijkingen

**Output**:
- Terminal: Colored summary per testcase
- `rapporten/validatie_batch_{datum}.md`: Volledig rapport
- `rapporten/validatie_batch_latest.json`: Machine-readable

---

## Testcase Overzicht

| ID | Naam | Jaar | Type | Status | Opmerking |
|----|------|------|------|--------|-----------|
| *Nog geen testcases aangeleverd* | | | | | |

**Status**:
- 📥 Raw: Ruwe JSON aanwezig
- ✅ Normalized: Genormaliseerd en gevalideerd
- 🔄 Validatie running: Berekening in uitvoering
- ✅ Passed: Validatie geslaagd (binnen tolerantie)
- ⚠️ Partial: Gedeeltelijke match (kleine afwijkingen)
- ❌ Failed: Grote afwijkingen (actie nodig)

*(Deze tabel wordt automatisch bijgewerkt na normalisatie)*

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
| `tests/run_all_testcases.py` | Valideer alle testcases | `normalized/*.json` | Validatie rapport |

---

## Volgende Stappen

1. **Lever eerste testcase aan** via chat (elk formaat)
2. **Verzamel 5-10 testcases** (verschillende huishouden-types, jaren)
3. **Run normalisatie**: `python tools/normalize_testcases.py`
4. **Review warnings** in `normalization_report.md`
5. **Run validatie**: `python tests/run_all_testcases.py`
6. **Analyseer afwijkingen** en pas model/config aan indien nodig

---

## Bijdragen

Nieuwe testcases altijd welkom! Hoe meer diversiteit (alleenstaand/paar, werkend/AOW, eigen huis, verschillende jaren), hoe robuuster het model.

**Contact**: Via chat message met "Nieuwe testcase:" prefix.
