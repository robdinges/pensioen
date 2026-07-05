## Uitgebreid validatierapport - tc_2025_008

- Naam testcase: IB2025 TC3 - Alleenstaand gepensioneerd met eigen woning
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
| AOW | EUR 20,400.00 | EUR 0.00 | EUR 20,400.00 |
| Overig inkomen | EUR 40,000.00 | EUR 0.00 | EUR 40,000.00 |
| **Totaal bruto** | **EUR 60,400.00** | **EUR 0.00** | **EUR 60,400.00** |

## 2. Berekeningsstappen applicatie

### Persoon 1

- Box 1 grondslag = bruto + eigen woning mutatie = EUR 60,400.00 + EUR -21,200.00 = EUR 39,200.00
- IB voor kortingen = EUR 3,425.10
- Premies totaal = EUR 3,748.00
- Tariefsaanpassing eigen woning = EUR 0.00
- Heffingskortingen totaal = EUR 3,607.97
- Netto verschuldigd P1 = max(0, IB + premies + tariefsaanpassing - kortingen) = EUR 3,565.13

## 3. Vergelijking met Belastingdienst

### Huishouden

| Maatstaf | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| Totaal verschuldigd | EUR 10,055.50 | EUR 10,055.50 | EUR 0.00 | PASS |

### Per persoon

| Persoon | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 10,055.50 | EUR 10,055.50 | EUR 0.00 | PASS |

### Componentniveau

| Component | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 3,425.10 | EUR 3,425.10 | EUR 0.00 | PASS |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 3,607.97 | EUR 3,607.97 | EUR 0.00 | PASS |
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

Volledige JSON dump: tests/fixtures/belasting_testcases/accountant_exports/tc_2025_008_accountant_detail.json
