## Uitgebreid validatierapport - tc_2025_011

- Naam testcase: IB2025 TC6 - Paar beide gepensioneerd zonder eigen woning
- Jaar: 2025
- Tariefjaar gebruikt door engine: 2025
- Tariefaanname/fallback: 
- Verwacht-bron voor validatie: huishoudtotaal
- Eindstatus: PASS

## 1. Inkomensopbouw

| Component | P1 | P2 | Huishouden |
|---|---:|---:|---:|
| Arbeidsinkomen | EUR 0.00 | EUR 0.00 | EUR 0.00 |
| Pensioen | EUR 0.00 | EUR 0.00 | EUR 0.00 |
| AOW | EUR 20,400.00 | EUR 20,400.00 | EUR 40,800.00 |
| Overig inkomen | EUR 40,000.00 | EUR 40,000.00 | EUR 80,000.00 |
| **Totaal bruto** | **EUR 60,400.00** | **EUR 60,400.00** | **EUR 120,800.00** |

## 2. Berekeningsstappen applicatie

### Persoon 1

- Box 1 grondslag = bruto + eigen woning mutatie = EUR 60,400.00 + EUR 0.00 = EUR 60,400.00
- IB voor kortingen = EUR 11,370.86
- Premies totaal = EUR 3,748.00
- Tariefsaanpassing eigen woning = EUR 0.00
- Heffingskortingen totaal = EUR 11.90
- Netto verschuldigd P1 = max(0, IB + premies + tariefsaanpassing - kortingen) = EUR 15,106.96

### Persoon 2

- Box 1 grondslag = bruto + eigen woning mutatie = EUR 60,400.00 + EUR 0.00 = EUR 60,400.00
- IB voor kortingen = EUR 11,370.86
- Premies totaal = EUR 3,748.00
- Tariefsaanpassing eigen woning = EUR 0.00
- Heffingskortingen totaal = EUR 11.90
- Netto verschuldigd P2 = max(0, IB + premies + tariefsaanpassing - kortingen) = EUR 15,106.96

## 3. Vergelijking met Belastingdienst

### Huishouden

| Maatstaf | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| Totaal verschuldigd | EUR 35,857.86 | EUR 35,857.86 | EUR 0.00 | PASS |

### Per persoon

| Persoon | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 17,928.93 | EUR 17,928.93 | EUR 0.00 | PASS |
| P2 | EUR 17,928.93 | EUR 17,928.93 | EUR 0.00 | PASS |

### Componentniveau

| Component | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 11,370.86 | EUR 11,370.86 | EUR 0.00 | PASS |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 11.90 | EUR 11.90 | EUR 0.00 | PASS |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 11,370.86 | EUR 11,370.86 | EUR 0.00 | PASS |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p2 | EUR 11.90 | EUR 11.90 | EUR 0.00 | PASS |

## 4. Box 3 en vermogenskoppeling

- Box 3 vrijstelling huishouden: EUR 115,368.00
- Box 3 belastbare grondslag: EUR 384,632.00
- Box 3 heffing totaal: EUR 5,643.94
- Box 3 heffing P1: EUR 2,821.97
- Box 3 heffing P2: EUR 2,821.97

## 5. Datakwaliteit en aandachtspunten

- Geen interne inconsistenties gedetecteerd in verwachte velden.

## 6. Reproduceerbaarheid

Gebruik deze commandostructuur om dezelfde vergelijking opnieuw te draaien:

- Één testcase: PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_010
- Meerdere testcases: PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py tc_2025_008 tc_2025_010 tc_2025_011
- Alle beschikbare cases in een directory: PYTHONPATH=src:. .venv312/bin/python tools/export_accountant_details.py --input-dir tests/fixtures/belasting_testcases/normalized

Volledige JSON dump: tests/fixtures/belasting_testcases/accountant_exports/tc_2025_011_accountant_detail.json
