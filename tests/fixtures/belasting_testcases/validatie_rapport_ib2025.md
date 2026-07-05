## IB 2025 Validatierapport

- Gegenereerd op: 2026-07-05 09:31
- Aantal testcases: 6

## Samenvatting

| Testcase | Status | Verwacht huishouden | Berekend huishouden | Verschil |
|---|---|---:|---:|---:|
| tc_2025_006 | PASS | EUR 33,021.00 | EUR 33,023.93 | EUR 2.93 |
| tc_2025_007 | PASS | EUR 25,412.00 | EUR 25,414.73 | EUR 2.73 |
| tc_2025_008 | PASS | EUR 10,055.50 | EUR 10,055.50 | EUR 0.00 |
| tc_2025_009 | WARN | EUR 51,094.00 | EUR 51,101.86 | EUR 7.86 |
| tc_2025_010 | PASS | EUR 38,313.71 | EUR 38,313.71 | EUR 0.00 |
| tc_2025_011 | PASS | EUR 35,857.86 | EUR 35,857.86 | EUR 0.00 |

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
| EUR 10,055.50 | EUR 10,055.50 | EUR 0.00 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 10,055.50 | EUR 10,055.50 | EUR 0.00 | PASS |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 3,425.10 | EUR 3,425.10 | EUR 0.00 | PASS |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 3,607.97 | EUR 3,607.97 | EUR 0.00 | PASS |
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
| EUR 38,313.71 | EUR 38,313.71 | EUR 0.00 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,550.93 | EUR 25,550.93 | EUR 0.00 | PASS |
| P2 | EUR 12,762.78 | EUR 12,762.78 | EUR 0.00 | PASS |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 15,294.94 | EUR 15,294.94 | EUR 0.00 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.94 | EUR 0.94 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 7,397.98 | EUR 7,397.98 | EUR 0.00 | PASS |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p2 | EUR 1,205.17 | EUR 1,205.17 | EUR 0.00 | PASS |

## tc_2025_011 - IB2025 TC6 - Paar beide gepensioneerd zonder eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 35,857.86 | EUR 35,857.86 | EUR 0.00 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 17,928.93 | EUR 17,928.93 | EUR 0.00 | PASS |
| P2 | EUR 17,928.93 | EUR 17,928.93 | EUR 0.00 | PASS |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 11,370.86 | EUR 11,370.86 | EUR 0.00 | PASS |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 11.90 | EUR 11.90 | EUR 0.00 | PASS |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 11,370.86 | EUR 11,370.86 | EUR 0.00 | PASS |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p2 | EUR 11.90 | EUR 11.90 | EUR 0.00 | PASS |