## IB 2025 Validatierapport

- Gegenereerd op: 2026-09-06 16:45
- Aantal testcases: 8

## Samenvatting

| Testcase | Status | Verwacht huishouden | Berekend huishouden | Verschil |
|---|---|---:|---:|---:|
| tc_2025_006 | PASS | EUR 33,021.00 | EUR 33,023.93 | EUR 2.93 |
| tc_2025_007 | PASS | EUR 25,412.00 | EUR 25,414.73 | EUR 2.73 |
| tc_2025_008 | FAIL | EUR 10,055.50 | EUR 9,681.18 | EUR -374.32 |
| tc_2025_009 | WARN | EUR 51,094.00 | EUR 51,101.86 | EUR 7.86 |
| tc_2025_010 | FAIL | EUR 38,313.71 | EUR 37,358.79 | EUR -954.92 |
| tc_2025_011 | FAIL | EUR 35,857.86 | EUR 33,629.92 | EUR -2,227.94 |
| tc_2025_013 | PASS | EUR 8,735.00 | EUR 8,738.02 | EUR 3.02 |
| tc_2025_014 | PASS | EUR 11,210.00 | EUR 11,213.21 | EUR 3.21 |

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
| EUR 10,055.50 | EUR 9,681.18 | EUR -374.32 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 10,055.50 | EUR 9,681.18 | EUR -374.32 | FAIL |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 3,425.10 | EUR 3,202.64 | EUR -222.46 | FAIL |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 3,607.97 | EUR 3,759.83 | EUR 151.86 | FAIL |
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
| EUR 38,313.71 | EUR 37,358.79 | EUR -954.92 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,550.93 | EUR 25,550.93 | EUR 0.00 | PASS |
| P2 | EUR 12,762.78 | EUR 11,807.86 | EUR -954.92 | FAIL |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 15,294.94 | EUR 15,294.94 | EUR 0.00 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.94 | EUR 0.94 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,194.92 | EUR -0.08 | PASS |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 7,397.98 | EUR 6,793.90 | EUR -604.08 | FAIL |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p2 | EUR 1,205.17 | EUR 1,556.01 | EUR 350.84 | FAIL |

## tc_2025_011 - IB2025 TC6 - Paar beide gepensioneerd zonder eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 35,857.86 | EUR 33,629.92 | EUR -2,227.94 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 17,928.93 | EUR 16,814.96 | EUR -1,113.97 | FAIL |
| P2 | EUR 17,928.93 | EUR 16,814.96 | EUR -1,113.97 | FAIL |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 11,370.86 | EUR 10,766.78 | EUR -604.08 | FAIL |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 11.90 | EUR 521.79 | EUR 509.89 | FAIL |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 11,370.86 | EUR 10,766.78 | EUR -604.08 | FAIL |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,748.00 | EUR 0.00 | PASS |
| totaal_kortingen_p2 | EUR 11.90 | EUR 521.79 | EUR 509.89 | FAIL |

## tc_2025_013 - Alleenstaand werkend

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 8,735.00 | EUR 8,738.02 | EUR 3.02 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | n.v.t. | EUR 8,738.02 | EUR 0.00 | NVT |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 5,598.00 | EUR 5,598.94 | EUR 0.94 | PASS |
| totaal_premies_p1 | n.v.t. | EUR 10,628.94 | EUR 0.00 | NVT |
| totaal_kortingen_p1 | n.v.t. | EUR 7,489.86 | EUR 0.00 | NVT |
| box3_heffing | n.v.t. | EUR 0.00 | EUR 0.00 | NVT |

## tc_2025_014 - Fiscale partners met alleen loon

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 11,210.00 | EUR 11,213.21 | EUR 3.21 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | n.v.t. | EUR 8,738.02 | EUR 0.00 | NVT |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 5,598.00 | EUR 5,598.94 | EUR 0.94 | PASS |
| totaal_premies_p1 | n.v.t. | EUR 10,628.94 | EUR 0.00 | NVT |
| totaal_kortingen_p1 | n.v.t. | EUR 7,489.86 | EUR 0.00 | NVT |
| box3_heffing | n.v.t. | EUR 0.00 | EUR 0.00 | NVT |
| box1_ib_p2 | EUR 2,451.00 | EUR 2,451.00 | EUR 0.00 | PASS |
| totaal_premies_p2 | n.v.t. | EUR 8,295.00 | EUR 0.00 | NVT |
| totaal_kortingen_p2 | n.v.t. | EUR 8,270.81 | EUR 0.00 | NVT |