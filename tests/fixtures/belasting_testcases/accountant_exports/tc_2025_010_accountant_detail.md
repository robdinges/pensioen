## Uitgebreid validatierapport - tc_2025_010

- Naam testcase: IB2025 TC5 - Paar werkend en gepensioneerd met eigen woning
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
| AOW | EUR 0.00 | EUR 20,400.00 | EUR 20,400.00 |
| Overig inkomen | EUR 0.00 | EUR 40,000.00 | EUR 40,000.00 |
| **Totaal bruto** | **EUR 80,000.00** | **EUR 60,400.00** | **EUR 140,400.00** |

## 2. Berekeningsstappen applicatie

### Persoon 1

- Box 1 grondslag = bruto + eigen woning mutatie = EUR 80,000.00 + EUR -10,600.00 = EUR 69,400.00
- IB voor kortingen = EUR 14,744.06
- Premies totaal = EUR 10,628.94
- Tariefsaanpassing eigen woning = EUR 550.88
- Heffingskortingen totaal = EUR 3,194.92
- Netto verschuldigd P1 = max(0, IB + premies + tariefsaanpassing - kortingen) = EUR 22,728.96

### Persoon 2

- Box 1 grondslag = bruto + eigen woning mutatie = EUR 60,400.00 + EUR -10,600.00 = EUR 49,800.00
- IB voor kortingen = EUR 7,397.98
- Premies totaal = EUR 3,748.00
- Tariefsaanpassing eigen woning = EUR 0.00
- Heffingskortingen totaal = EUR 1,205.17
- Netto verschuldigd P2 = max(0, IB + premies + tariefsaanpassing - kortingen) = EUR 9,940.81

## 3. Vergelijking met Belastingdienst

### Huishouden

| Maatstaf | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| Totaal verschuldigd | EUR 38,313.71 | EUR 38,313.71 | EUR 0.00 | PASS |

### Per persoon

| Persoon | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,550.93 | EUR 25,550.93 | EUR 0.00 | PASS |
| P2 | EUR 12,762.78 | EUR 12,762.78 | EUR 0.00 | PASS |

### Componentniveau

| Component | Belastingdienst | Applicatie | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 15,294.94 | EUR 15,294.94 | EUR 0.00 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.94 | EUR 0.94 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 7,397.98 | EUR 7,397.98 | EUR 0.00 | PASS |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p2 | EUR 1,205.17 | EUR 1,205.17 | EUR 0.00 | PASS |

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

Volledige JSON dump: tests/fixtures/belasting_testcases/accountant_exports/tc_2025_010_accountant_detail.json
