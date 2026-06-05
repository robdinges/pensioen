# Belasting Vergelijkingstool

**Standalone validatie tool** voor het vergelijken van `dutch_tax` (2025) belastingberekeningen met de `pensioen-app` berekeningen (2026).

## ⚠️ Belangrijke Waarschuwing

Deze tool is **NIET** onderdeel van de productie pensioen-app. Het is een **validatie en analysehulpmiddel** dat volledig standalone opereert. De gehele `/validatie/` folder kan worden verwijderd zonder impact op de pensioen-app.

**Gebruik**: Alleen voor interne validatie en het identificeren van verbeterpunten in de pensioen-app.

## Doel

Identificeer verschillen tussen:
- **dutch_tax**: Uitgebreide belastingberekening met eigenwoningforfait, aftrekposten, Box 2, etc.
- **pensioen-app**: Vereenvoudigde berekening gericht op pensioeninkomsten

De tool genereert rapporten met:
- Gedetailleerde verschillenanalyse per categorie (Box 1, Box 3, heffingskortingen)
- Hypotheses over oorzaken van verschillen
- Concrete aanbevelingen voor verbeteringen aan de pensioen-app

## Structuur

```
validatie/
├── README.md                           # Deze documentatie
├── run_vergelijking.py                 # CLI entry point
├── belasting_vergelijking/
│   ├── __init__.py
│   ├── dutch_tax_adapter.py            # Parse dutch_tax JSON → standaard formaat
│   ├── pensioen_adapter.py             # Roep pensioen-app engines aan
│   ├── vergelijker.py                  # Vergelijk beide berekeningen
│   └── rapport_generator.py            # Genereer markdown/Excel rapporten
└── tests/
    ├── __init__.py
    ├── test_vergelijking.py            # Tests met synthetische data
    └── fixtures/
        ├── test_alleenstaand.json      # Synthetische testcase: alleenstaand
        └── test_partner_eigenwoning.json  # Synthetische testcase: partner + eigen woning
```

## Installatie

Geen extra dependencies vereist — maakt gebruik van bestaande pensioen-app dependencies:
- `pydantic` (validatie)
- `decimal` (nauwkeurige berekeningen)
- `openpyxl` (optioneel, voor Excel export)

## Gebruik

### 1. Basis gebruik (alleen markdown rapport)

```bash
cd /Users/robvandererve/Documents/python_projects/pensioen

python3 -m validatie.run_vergelijking \
  --input /Users/robvandererve/Documents/python_projects/dutch_tax/submissions/frits.json \
  --jaar 2026 \
  --geboortedatum-p1 1960-05-15 \
  --output rapporten/frits_vergelijking.md
```

### 2. Met fiscaal partner

```bash
python3 -m validatie.run_vergelijking \
  --input /Users/robvandererve/Documents/python_projects/dutch_tax/submissions/MrsT.json \
  --jaar 2026 \
  --geboortedatum-p1 1958-03-20 \
  --geboortedatum-p2 1960-07-12 \
  --output rapporten/mrst_vergelijking.md
```

### 3. Met Excel export

```bash
python3 -m validatie.run_vergelijking \
  --input /Users/robvandererve/Documents/python_projects/dutch_tax/submissions/lr.json \
  --jaar 2026 \
  --geboortedatum-p1 1962-11-05 \
  --geboortedatum-p2 1964-02-28 \
  --output rapporten/lr_vergelijking.md \
  --excel rapporten/lr_vergelijking.xlsx
```

### 4. Verbose modus (voor debugging)

```bash
python3 -m validatie.run_vergelijking \
  --input submission.json \
  --jaar 2026 \
  --geboortedatum-p1 1960-01-01 \
  --output rapport.md \
  --verbose
```

## Parameters

| Parameter | Verplicht | Beschrijving | Voorbeeld |
|-----------|-----------|--------------|-----------|
| `--input`, `-i` | ✅ | Pad naar dutch_tax submission JSON | `submissions/frits.json` |
| `--jaar`, `-j` | ❌ | Belastingjaar (standaard: 2026) | `2026` |
| `--geboortedatum-p1` | ✅ | Geboortedatum persoon 1 (YYYY-MM-DD) | `1960-05-15` |
| `--geboortedatum-p2` | ❌ | Geboortedatum persoon 2 / partner | `1962-03-20` |
| `--output`, `-o` | ❌ | Markdown output pad (standaard: `vergelijking_rapport.md`) | `rapport.md` |
| `--excel`, `-x` | ❌ | Excel output pad (indien gewenst) | `rapport.xlsx` |
| `--verbose`, `-v` | ❌ | Toon uitgebreide logging | (vlag) |

## Rapportage Structuur

### Markdown Rapport

Het gegenereerde markdown rapport bevat:

1. **Samenvatting**
   - Aantal verschillen (totaal, kritiek, significant)
   - Totaal te betalen/terug via pensioen-app
   - Belangrijkste conclusies

2. **Aanbevelingen**
   - Geprioriteerde lijst van verbeteringen voor pensioen-app
   - Bijv. "Voeg eigenwoningforfait toe" met geschatte impact

3. **Gedetailleerde Verschillenanalyse**
   - Per categorie (Box 1, Box 3, Heffingskortingen)
   - Tabellen met:
     - dutch_tax waarde
     - pensioen-app waarde
     - Verschil (absoluut + percentage)
     - Ernst classificatie (🔴 KRITIEK, 🟡 SIGNIFICANT, 🔵 KLEIN, ⚪ VERWAARLOOSBAAR)
     - Hypothese over oorzaak

4. **Pensioen-app Berekening Details**
   - Volledige breakdown per persoon
   - Box 1: bruto, belasting, heffingskortingen
   - Box 3: vermogen, vrijstelling, heffing
   - Aannames en waarschuwingen

5. **Metadata**
   - Gebruikte belastingconfig
   - Huishoudsamenstelling
   - Disclaimer over validatie vs productie

### Excel Rapport (optioneel)

Het Excel rapport heeft 3 sheets:
- **Samenvatting**: Key metrics en totalen
- **Verschillen**: Sorteerbare tabel met alle verschillen
- **Aanbevelingen**: Geprioriteerde lijst

## Interpretatie van Verschillen

### Ernst Classificatie

| Ernst | Drempelwaarde | Betekenis | Actie |
|-------|---------------|-----------|-------|
| 🔴 **KRITIEK** | ≥ €1.000 | Groot verschil, mogelijk missende feature | Onderzoek prioriteit 1 |
| 🟡 **SIGNIFICANT** | €100 - €999 | Substantieel verschil | Onderzoek indien structureel |
| 🔵 **KLEIN** | €10 - €99 | Kleine afwijking | Controleer bij twijfel |
| ⚪ **VERWAARLOOSBAAR** | < €10 | Afrondingsverschil | Negeerbaar |

### Veelvoorkomende Oorzaken

1. **Tariefjaar verschil (2025 → 2026)**
   - Schijfgrenzen veranderen jaarlijks
   - Heffingskortingen worden aangepast
   - **Acceptabel**: Kleine verschillen (< €100) door tariefaanpassing

2. **Eigenwoningforfait ontbreekt in pensioen-app**
   - Impact: €100 - €500+ per jaar (afhankelijk van WOZ-waarde)
   - **Prioriteit 1**: Implementeer eigenwoningforfait berekening

3. **Aftrekposten niet ondersteund**
   - Beddengoed, giften, professionele kosten
   - Impact: €50 - €200 per aftrekpost
   - **Prioriteit 2**: Voeg veelvoorkomende aftrekposten toe

4. **Heffingskortingen berekeningsverschil**
   - dutch_tax: "Algemene korting" (totaal)
   - pensioen-app: AHK + arbeidskorting + ouderenkorting (opgesplitst)
   - **Acceptabel**: Kleine verschillen indien totaal vergelijkbaar

5. **Box 3 forfaitair rendement verschil**
   - dutch_tax 2025: spaargeld 1.37%, beleggen 5.88%
   - pensioen-app 2026: sparen 1.5%, beleggen 6.0%
   - **Acceptabel**: Tariefjaar verschil

6. **Dividend ingehouden niet verrekend**
   - Pensioen-app neemt mogelijk dividend niet mee
   - Impact: Kan leiden tot te veel belasting betalen
   - **Prioriteit 3**: Controleer Box 3 verrekening

## Tests Uitvoeren

De tool heeft uitgebreide tests met synthetische data:

```bash
cd /Users/robvandererve/Documents/python_projects/pensioen

# Voer validatie tests uit
pytest validatie/tests/ -v

# Met coverage
pytest validatie/tests/ --cov=validatie/belasting_vergelijking --cov-report=term-missing
```

Test scenarios:
- Alleenstaande met alleen AOW
- Partner met werkgeverspensioen + eigen woning
- Data-integriteit (Decimal precisie)
- Rapport generatie (markdown + Excel)

## Beperkingen & Disclaimers

### Wat deze tool NIET doet

- ❌ Geen volledige dutch_tax berekening (alleen pensioen-app vergelijken met input)
- ❌ Geen Box 2 berekening (aanmerkelijk belang niet relevant voor pensioen-app doelgroep)
- ❌ Geen automatische correctie van pensioen-app code
- ❌ Geen productie-klare belastingaangifte genereren

### Aannames

1. dutch_tax submissions zijn 2025 data, pensioen-app berekent voor 2026
2. Kleine tariefverschillen (< €100) door jaar-overgang zijn acceptabel
3. Geboortedatums moeten handmatig worden opgegeven (niet in submission JSON)
4. Box 3 verdeling wordt gelijk verdeeld over partners (pensioen-app aanname)

### Privacy

- Synthetische testdata in `/validatie/tests/fixtures/` is volledig fictief
- Voor echte submissions: verwijder persoonlijke gegevens voor rapportage

## Voorbeelduitvoer

### Console Output

```
🔄 Vergelijking uitvoeren...
✅ Vergelijking voltooid

📊 Samenvatting:
   Huishouden: TestCase_Partner_Complexer
   Verschillen: 7
   Kritiek: 1, Significant: 2

🎯 Top aanbevelingen:
   1. PRIORITEIT 1: Implementeer eigenwoningforfait berekening (impact: €300-500)
   2. PRIORITEIT 2: Voeg ondersteuning toe voor veelvoorkomende aftrekposten
   3. PRIORITEIT 3: Controleer dividend verrekening in Box 3

📝 Markdown rapport schrijven naar: rapport.md
✅ Markdown rapport opgeslagen

🎉 Klaar! Bekijk het rapport: rapport.md
```

### Markdown Snippet

```markdown
## 🔍 Gedetailleerde Verschillenanalyse

### Box 1 - Marie Testpersoon

| Onderdeel | dutch_tax | pensioen-app | Verschil | % | Ernst | Hypothese |
|-----------|-----------|--------------|----------|---|-------|-----------|
| Eigenwoningforfait (ONTBREEKT) | €306.25 | €0.00 | -€306.25 | -100.0% | 🟡 SIGNIFICANT | Pensioen-app ondersteunt geen eigenwoningforfait. WOZ €350,000 → geschat forfait €875 → extra belasting ~€306 (indicatief) |
| Aftrekposten (ONTBREKEN) | €157.50 | €0.00 | -€157.50 | -100.0% | 🟡 SIGNIFICANT | Pensioen-app ondersteunt geen aftrekposten. 1 aftrekpost(en) totaal €450 → belastingvoordeel ~€158 (indicatief) |
```

## Troubleshooting

### Probleem: "Module not found: validatie"

**Oplossing**: Gebruik `python3 -m validatie.run_vergelijking` in plaats van `python3 validatie/run_vergelijking.py`:
```bash
cd /Users/robvandererve/Documents/python_projects/pensioen
python3 -m validatie.run_vergelijking --input ... --output ...
```

### Probleem: "openpyxl not found" bij Excel export

**Oplossing**: Excel export is optioneel. Zonder `--excel` geen probleem.
```bash
# Installeer indien nodig:
pip install openpyxl
```

### Probleem: "FileNotFoundError: Submission bestand niet gevonden"

**Controle**: Gebruik absoluut pad of relatief vanaf project root:
```bash
python validatie/run_vergelijking.py \
  --input /Users/robvandererve/Documents/python_projects/dutch_tax/submissions/frits.json \
  ...
```

### Probleem: Grote verschillen in heffingskortingen

**Analyse**: 
1. Check tariefjaar (2025 vs 2026 kan €100-300 verschil geven)
2. Vergelijk totale heffingskorting (niet individueel AHK/arbeidskorting)
3. Indien totaal vergelijkbaar: acceptabel verschil door berekeningssystematiek

## Ontwikkeling & Uitbreiding

### Nieuwe testcase toevoegen

1. Creëer JSON in `/validatie/tests/fixtures/test_<naam>.json`
2. Volg structuur van bestaande testcases
3. Voeg test toe in `test_vergelijking.py`

### Rapportage uitbreiden

Wijzig `rapport_generator.py`:
- `genereer_markdown_rapport()` voor markdown aanpassingen
- `genereer_excel_rapport()` voor Excel aanpassingen

### Nieuwe vergelijkings categorie

Wijzig `vergelijker.py`:
- Voeg functie toe aan `_vergelijk_*()` serie
- Roep aan in `vergelijk_berekeningen()`

## Roadmap (toekomstige verbeteringen)

- [ ] Automatische detectie geboortedatums uit submission (indien beschikbaar)
- [ ] Ondersteuning voor meerdere jaren (2024, 2027, etc.)
- [ ] Grafische visualisatie van verschillen (plotly)
- [ ] Batch mode: vergelijk alle submissions in folder
- [ ] JSON output formaat voor geautomatiseerde analyse

## Contact & Support

Voor vragen over deze tool:
- Check AGENTS.md in project root voor algemene pensioen-app conventie
- Check tests voor voorbeeldgebruik
- Deze tool is GEEN onderdeel van pensioen-app support

## Licentie

Deze tool maakt deel uit van het pensioen project en volgt dezelfde licentie.

---

**Laatst bijgewerkt**: 2026-05-25  
**Versie**: 1.0.0  
**Status**: Validatie tool — NIET voor productie gebruik
