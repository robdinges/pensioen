## IB 2025 Validatierapport

- Gegenereerd op: 2026-07-04 21:28
- Aantal testcases: 6

## Samenvatting

| Testcase | Status | Verwacht huishouden | Berekend huishouden | Verschil |
|---|---|---:|---:|---:|
| tc_2025_006 | PASS | EUR 33,021.00 | EUR 33,023.93 | EUR 2.93 |
| tc_2025_007 | PASS | EUR 25,412.00 | EUR 25,414.73 | EUR 2.73 |
| tc_2025_008 | FAIL | EUR 12,113.00 | EUR 10,055.50 | EUR -2,057.50 |
| tc_2025_009 | WARN | EUR 51,094.00 | EUR 51,101.86 | EUR 7.86 |
| tc_2025_010 | FAIL | EUR 38,314.00 | EUR 37,778.71 | EUR -535.29 |
| tc_2025_011 | FAIL | EUR 34,522.00 | EUR 33,495.72 | EUR -1,026.28 |

## tc_2025_006 - IB2025 TC1 - Alleenstaand werkend zonder eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 33,021.00 | EUR 33,023.93 | EUR 2.93 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 33,021.00 | EUR 33,023.93 | EUR 2.93 | PASS |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 19,098.00 | EUR 19,099.54 | EUR 1.54 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.94 | EUR 0.94 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 6,490.00 | EUR 6,490.37 | EUR 0.37 | PASS |

## tc_2025_007 - IB2025 TC2 - Alleenstaand werkend met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 25,412.00 | EUR 25,414.73 | EUR 2.73 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,412.00 | EUR 25,414.73 | EUR 2.73 | PASS |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 11,489.00 | EUR 11,490.34 | EUR 1.34 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.94 | EUR 0.94 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 6,490.00 | EUR 6,490.37 | EUR 0.37 | PASS |

## tc_2025_008 - IB2025 TC3 - Alleenstaand gepensioneerd met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 12,113.00 | EUR 10,055.50 | EUR -2,057.50 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 12,113.00 | EUR 10,055.50 | EUR -2,057.50 | FAIL |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 3,202.00 | EUR 3,425.10 | EUR 223.10 | FAIL |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 1,401.00 | EUR 3,607.97 | EUR 2,206.97 | FAIL |
| box3_heffing | EUR 6,490.00 | EUR 6,490.37 | EUR 0.37 | PASS |

## tc_2025_009 - IB2025 TC4 - Paar beide werkend met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 51,094.00 | EUR 51,101.86 | EUR 7.86 | WARN |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,547.00 | EUR 25,549.96 | EUR 2.96 | PASS |
| P2 | EUR 25,547.00 | EUR 25,549.96 | EUR 2.96 | PASS |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 15,293.00 | EUR 15,294.94 | EUR 1.94 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.94 | EUR 0.94 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 5,642.00 | EUR 5,643.94 | EUR 1.94 | PASS |
| box1_ib_p2 | EUR 15,293.00 | EUR 15,294.94 | EUR 1.94 | PASS |
| totaal_premies_p2 | EUR 10,628.00 | EUR 10,628.94 | EUR 0.94 | PASS |
| totaal_kortingen_p2 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |

## tc_2025_010 - IB2025 TC5 - Paar werkend en gepensioneerd met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 38,314.00 | EUR 37,778.71 | EUR -535.29 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,549.96 | EUR 25,550.93 | EUR 0.97 | PASS |
| P2 | EUR 12,226.81 | EUR 12,227.78 | EUR 0.97 | PASS |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 15,294.94 | EUR 15,294.94 | EUR 0.00 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.94 | EUR 0.94 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 6,793.00 | EUR 7,397.98 | EUR 604.98 | FAIL |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p2 | EUR 795.00 | EUR 1,740.17 | EUR 945.17 | FAIL |

## tc_2025_011 - IB2025 TC6 - Paar beide gepensioneerd zonder eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 34,522.00 | EUR 33,495.72 | EUR -1,026.28 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 16,746.89 | EUR 16,747.86 | EUR 0.97 | PASS |
| P2 | EUR 16,746.89 | EUR 16,747.86 | EUR 0.97 | PASS |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 10,766.00 | EUR 11,370.86 | EUR 604.86 | FAIL |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 274.00 | EUR 1,192.97 | EUR 918.97 | FAIL |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 10,766.00 | EUR 11,370.86 | EUR 604.86 | FAIL |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p2 | EUR 274.00 | EUR 1,192.97 | EUR 918.97 | FAIL |