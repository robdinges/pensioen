## Uitgebreid validatierapport - tc_2025_006

- Naam testcase: IB2025 TC1 - Alleenstaand werkend zonder eigen woning
- Jaar: 2025
- Tariefjaar gebruikt door engine: 2025
- Tariefaanname/fallback: 
- Verwacht-bron voor validatie: huishoudtotaal
- Eindstatus: PASS

## 1. Inkomensopbouw

| Component | P1 | P2 | Huishouden |
|---|---:|---:|---:|
| Arbeidsinkomen | EUR 80,000.00 | EUR 0.00 | EUR 80,000.00 |
| Pensioen | EUR 0.00 | EUR 0.00 | EUR 0.00 |
| AOW | EUR 0.00 | EUR 0.00 | EUR 0.00 |
| Overig inkomen | EUR 0.00 | EUR 0.00 | EUR 0.00 |
| **Totaal bruto** | **EUR 80,000.00** | **EUR 0.00** | **EUR 80,000.00** |

## 2. Berekeningsstappen applicatie

### Persoon 1

- Box 1 grondslag = bruto + eigen woning mutatie = EUR 80,000.00 + EUR 0.00 = EUR 80,000.00
- IB voor kortingen = EUR 19,099.54
- Premies totaal = EUR 10,628.94
- Tariefsaanpassing eigen woning = EUR 0.00
- Heffingskortingen totaal = EUR 3,194.92
- Netto verschuldigd P1 = max(0, IB + premies + tariefsaanpassing - kortingen) = EUR 26,533.56

## 3. Vergelijking met Belastingdienst

### Huishouden

| Maatstaf | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| Totaal verschuldigd | EUR 33,021.00 | EUR 33,023.93 | EUR 2.93 | PASS |

### Per persoon

| Persoon | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 33,021.00 | EUR 33,023.93 | EUR 2.93 | PASS |

### Componentniveau

| Component | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 19,098.00 | EUR 19,099.54 | EUR 1.54 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.94 | EUR 0.94 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 6,490.00 | EUR 6,490.37 | EUR 0.37 | PASS |

## 4. Box 3 en vermogenskoppeling

- Box 3 vrijstelling huishouden: EUR 57,684.00
- Box 3 belastbare grondslag: EUR 442,316.00
- Box 3 heffing totaal: EUR 6,490.37
- Box 3 heffing P1: EUR 6,490.37
- Box 3 heffing P2: EUR 0.00

## 5. Datakwaliteit en aandachtspunten

- Geen interne inconsistenties gedetecteerd in verwachte velden.

## 6. Reproduceerbaarheid

Gebruik deze commandostructuur om dezelfde vergelijking opnieuw te draaien:

- Één testcase: PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_010
- Meerdere testcases: PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_008 tc_2025_010 tc_2025_011
- Alle beschikbare cases in een directory: PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py --input-dir tests/fixtures/belasting_testcases/normalized

Volledige JSON dump: tests/fixtures/belasting_testcases/accountant_exports/tc_2025_006_accountant_detail.json
