## IB 2025 Validatierapport

- Gegenereerd op: 2026-07-26 12:21
- Aantal testcases: 6

## Samenvatting

| Testcase | Status | Verwacht huishouden | Berekend huishouden | Verschil |
|---|---|---:|---:|---:|
| tc_2025_006 | WARN | EUR 33,021.00 | EUR 32,989.71 | EUR -31.29 |
| tc_2025_007 | WARN | EUR 25,412.00 | EUR 25,380.51 | EUR -31.49 |
| tc_2025_008 | FAIL | EUR 10,055.50 | EUR 9,755.18 | EUR -300.32 |
| tc_2025_009 | FAIL | EUR 51,094.00 | EUR 51,033.42 | EUR -60.58 |
| tc_2025_010 | FAIL | EUR 38,313.71 | EUR 37,525.51 | EUR -788.20 |
| tc_2025_011 | FAIL | EUR 35,857.86 | EUR 34,031.80 | EUR -1,826.06 |

## tc_2025_006 - IB2025 TC1 - Alleenstaand werkend zonder eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 33,021.00 | EUR 32,989.71 | EUR -31.29 | WARN |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 33,021.00 | EUR 32,989.71 | EUR -31.29 | WARN |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 19,098.00 | EUR 18,495.46 | EUR -602.54 | FAIL |
| totaal_premies_p1 | EUR 10,628.00 | EUR 11,198.80 | EUR 570.80 | FAIL |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 6,490.00 | EUR 6,490.37 | EUR 0.37 | PASS |

## tc_2025_007 - IB2025 TC2 - Alleenstaand werkend met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 25,412.00 | EUR 25,380.51 | EUR -31.49 | WARN |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,412.00 | EUR 25,380.51 | EUR -31.49 | WARN |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 11,489.00 | EUR 10,886.26 | EUR -602.74 | FAIL |
| totaal_premies_p1 | EUR 10,628.00 | EUR 11,198.80 | EUR 570.80 | FAIL |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 6,490.00 | EUR 6,490.37 | EUR 0.37 | PASS |

## tc_2025_008 - IB2025 TC3 - Alleenstaand gepensioneerd met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 10,055.50 | EUR 9,755.18 | EUR -300.32 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 10,055.50 | EUR 9,755.18 | EUR -300.32 | FAIL |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 3,425.10 | EUR 3,202.64 | EUR -222.46 | FAIL |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,822.00 | EUR 74.00 | FAIL |
| totaal_kortingen_p1 | EUR 3,607.97 | EUR 3,759.83 | EUR 151.86 | FAIL |
| box3_heffing | EUR 6,490.00 | EUR 6,490.37 | EUR 0.37 | PASS |

## tc_2025_009 - IB2025 TC4 - Paar beide werkend met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 51,094.00 | EUR 51,033.42 | EUR -60.58 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,547.00 | EUR 25,515.74 | EUR -31.26 | WARN |
| P2 | EUR 25,547.00 | EUR 25,515.74 | EUR -31.26 | WARN |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 15,293.00 | EUR 14,690.86 | EUR -602.14 | FAIL |
| totaal_premies_p1 | EUR 10,628.00 | EUR 11,198.80 | EUR 570.80 | FAIL |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 5,642.00 | EUR 5,643.94 | EUR 1.94 | PASS |
| box1_ib_p2 | EUR 15,293.00 | EUR 14,690.86 | EUR -602.14 | FAIL |
| totaal_premies_p2 | EUR 10,628.00 | EUR 11,198.80 | EUR 570.80 | FAIL |
| totaal_kortingen_p2 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |

## tc_2025_010 - IB2025 TC5 - Paar werkend en gepensioneerd met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 38,313.71 | EUR 37,525.51 | EUR -788.20 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,550.93 | EUR 25,516.71 | EUR -34.22 | WARN |
| P2 | EUR 12,762.78 | EUR 12,008.80 | EUR -753.98 | FAIL |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 15,294.94 | EUR 14,690.86 | EUR -604.08 | FAIL |
| totaal_premies_p1 | EUR 10,628.00 | EUR 11,198.80 | EUR 570.80 | FAIL |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 7,397.98 | EUR 6,793.90 | EUR -604.08 | FAIL |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,948.94 | EUR 200.94 | FAIL |
| totaal_kortingen_p2 | EUR 1,205.17 | EUR 1,556.01 | EUR 350.84 | FAIL |

## tc_2025_011 - IB2025 TC6 - Paar beide gepensioneerd zonder eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 35,857.86 | EUR 34,031.80 | EUR -1,826.06 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 17,928.93 | EUR 17,015.90 | EUR -913.03 | FAIL |
| P2 | EUR 17,928.93 | EUR 17,015.90 | EUR -913.03 | FAIL |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 11,370.86 | EUR 10,766.78 | EUR -604.08 | FAIL |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,948.94 | EUR 200.94 | FAIL |
| totaal_kortingen_p1 | EUR 11.90 | EUR 521.79 | EUR 509.89 | FAIL |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 11,370.86 | EUR 10,766.78 | EUR -604.08 | FAIL |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,948.94 | EUR 200.94 | FAIL |
| totaal_kortingen_p2 | EUR 11.90 | EUR 521.79 | EUR 509.89 | FAIL |