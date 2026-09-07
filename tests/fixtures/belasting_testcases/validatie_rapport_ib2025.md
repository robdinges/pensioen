## IB 2025 Validatierapport

- Gegenereerd op: 2026-09-07 04:16
- Aantal testcases: 11

## Samenvatting

| Testcase | Status | Verwacht huishouden | Berekend huishouden | Verschil |
|---|---|---:|---:|---:|
| tc_2025_006 | PASS | EUR 33,021.00 | EUR 33,021.37 | EUR 0.37 |
| tc_2025_007 | PASS | EUR 25,412.00 | EUR 25,412.53 | EUR 0.53 |
| tc_2025_008 | FAIL | EUR 10,055.50 | EUR 9,679.37 | EUR -376.13 |
| tc_2025_009 | PASS | EUR 51,094.00 | EUR 51,097.70 | EUR 3.70 |
| tc_2025_010 | FAIL | EUR 38,313.71 | EUR 36,690.82 | EUR -1,622.89 |
| tc_2025_011 | FAIL | EUR 35,857.86 | EUR 33,625.94 | EUR -2,231.92 |
| tc_2025_013 | PASS | EUR 8,735.00 | EUR 8,735.00 | EUR 0.00 |
| tc_2025_014 | PASS | EUR 11,210.00 | EUR 11,210.00 | EUR 0.00 |
| tc_2025_015 | PASS | EUR 8,736.00 | EUR 8,736.00 | EUR 0.00 |
| tc_2025_016 | PASS | EUR 4,447.00 | EUR 4,448.00 | EUR 1.00 |
| tc_2025_017 | PASS | EUR 4,429.00 | EUR 4,428.00 | EUR -1.00 |

## tc_2025_006 - IB2025 TC1 - Alleenstaand werkend zonder eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 33,021.00 | EUR 33,021.37 | EUR 0.37 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 33,021.00 | EUR 33,021.37 | EUR 0.37 | PASS |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 19,098.00 | EUR 19,098.00 | EUR 0.00 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,195.00 | EUR 0.00 | PASS |
| box3_heffing | EUR 6,490.00 | EUR 6,490.37 | EUR 0.37 | PASS |

## tc_2025_007 - IB2025 TC2 - Alleenstaand werkend met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 25,412.00 | EUR 25,412.53 | EUR 0.53 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,412.00 | EUR 25,412.53 | EUR 0.53 | PASS |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 11,489.00 | EUR 11,489.16 | EUR 0.16 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,195.00 | EUR 0.00 | PASS |
| box3_heffing | EUR 6,490.00 | EUR 6,490.37 | EUR 0.37 | PASS |

## tc_2025_008 - IB2025 TC3 - Alleenstaand gepensioneerd met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 10,055.50 | EUR 9,679.37 | EUR -376.13 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 10,055.50 | EUR 9,679.37 | EUR -376.13 | FAIL |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 3,425.10 | EUR 3,202.00 | EUR -223.10 | FAIL |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,747.00 | EUR -1.00 | PASS |
| totaal_kortingen_p1 | EUR 3,607.97 | EUR 3,760.00 | EUR 152.03 | FAIL |
| box3_heffing | EUR 6,490.00 | EUR 6,490.37 | EUR 0.37 | PASS |

## tc_2025_009 - IB2025 TC4 - Paar beide werkend met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 51,094.00 | EUR 51,097.70 | EUR 3.70 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,547.00 | EUR 25,547.88 | EUR 0.88 | PASS |
| P2 | EUR 25,547.00 | EUR 25,547.88 | EUR 0.88 | PASS |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 15,293.00 | EUR 15,293.88 | EUR 0.88 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,195.00 | EUR 0.00 | PASS |
| box3_heffing | EUR 5,642.00 | EUR 5,643.94 | EUR 1.94 | PASS |
| box1_ib_p2 | EUR 15,293.00 | EUR 15,293.88 | EUR 0.88 | PASS |
| totaal_premies_p2 | EUR 10,628.00 | EUR 10,628.00 | EUR 0.00 | PASS |
| totaal_kortingen_p2 | EUR 3,195.00 | EUR 3,195.00 | EUR 0.00 | PASS |

## tc_2025_010 - IB2025 TC5 - Paar werkend en gepensioneerd met eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 38,313.71 | EUR 36,690.82 | EUR -1,622.89 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 25,550.93 | EUR 25,548.85 | EUR -2.08 | PASS |
| P2 | EUR 12,762.78 | EUR 11,141.97 | EUR -1,620.81 | FAIL |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 15,294.94 | EUR 15,293.88 | EUR -1.06 | PASS |
| totaal_premies_p1 | EUR 10,628.00 | EUR 10,628.00 | EUR 0.00 | PASS |
| totaal_kortingen_p1 | EUR 3,195.00 | EUR 3,195.00 | EUR 0.00 | PASS |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 7,397.98 | EUR 6,793.00 | EUR -604.98 | FAIL |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,747.00 | EUR -1.00 | PASS |
| totaal_kortingen_p2 | EUR 1,205.17 | EUR 2,220.00 | EUR 1,014.83 | FAIL |

## tc_2025_011 - IB2025 TC6 - Paar beide gepensioneerd zonder eigen woning

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 35,857.86 | EUR 33,625.94 | EUR -2,231.92 | FAIL |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | EUR 17,928.93 | EUR 16,812.97 | EUR -1,115.96 | FAIL |
| P2 | EUR 17,928.93 | EUR 16,812.97 | EUR -1,115.96 | FAIL |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 11,370.86 | EUR 10,766.00 | EUR -604.86 | FAIL |
| totaal_premies_p1 | EUR 3,748.00 | EUR 3,747.00 | EUR -1.00 | PASS |
| totaal_kortingen_p1 | EUR 11.90 | EUR 522.00 | EUR 510.10 | FAIL |
| box3_heffing | EUR 5,643.94 | EUR 5,643.94 | EUR 0.00 | PASS |
| box1_ib_p2 | EUR 11,370.86 | EUR 10,766.00 | EUR -604.86 | FAIL |
| totaal_premies_p2 | EUR 3,748.00 | EUR 3,747.00 | EUR -1.00 | PASS |
| totaal_kortingen_p2 | EUR 11.90 | EUR 522.00 | EUR 510.10 | FAIL |

## tc_2025_013 - Alleenstaand werkend

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 8,735.00 | EUR 8,735.00 | EUR 0.00 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | n.v.t. | EUR 8,735.00 | EUR 0.00 | NVT |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 5,598.00 | EUR 5,598.00 | EUR 0.00 | PASS |
| totaal_premies_p1 | n.v.t. | EUR 10,628.00 | EUR 0.00 | NVT |
| totaal_kortingen_p1 | n.v.t. | EUR 7,491.00 | EUR 0.00 | NVT |
| box3_heffing | n.v.t. | EUR 0.00 | EUR 0.00 | NVT |

## tc_2025_014 - Fiscale partners met alleen loon

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 11,210.00 | EUR 11,210.00 | EUR 0.00 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | n.v.t. | EUR 8,735.00 | EUR 0.00 | NVT |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 5,598.00 | EUR 5,598.00 | EUR 0.00 | PASS |
| totaal_premies_p1 | n.v.t. | EUR 10,628.00 | EUR 0.00 | NVT |
| totaal_kortingen_p1 | n.v.t. | EUR 7,491.00 | EUR 0.00 | NVT |
| box3_heffing | n.v.t. | EUR 0.00 | EUR 0.00 | NVT |
| box1_ib_p2 | EUR 2,451.00 | EUR 2,451.00 | EUR 0.00 | PASS |
| totaal_premies_p2 | n.v.t. | EUR 8,295.00 | EUR 0.00 | NVT |
| totaal_kortingen_p2 | n.v.t. | EUR 8,271.00 | EUR 0.00 | NVT |

## tc_2025_015 - Afronding som van belastingschijven

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 8,736.00 | EUR 8,736.00 | EUR 0.00 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | n.v.t. | EUR 8,736.00 | EUR 0.00 | NVT |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 5,599.00 | EUR 5,599.00 | EUR 0.00 | PASS |
| totaal_premies_p1 | n.v.t. | EUR 10,628.00 | EUR 0.00 | NVT |
| totaal_kortingen_p1 | n.v.t. | EUR 7,491.00 | EUR 0.00 | NVT |
| box3_heffing | n.v.t. | EUR 0.00 | EUR 0.00 | NVT |

## tc_2025_016 - Alleenstaand met AOW en pensioen

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 4,447.00 | EUR 4,448.00 | EUR 1.00 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | n.v.t. | EUR 4,448.00 | EUR 0.00 | NVT |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 4,380.00 | EUR 4,380.00 | EUR 0.00 | PASS |
| totaal_premies_p1 | n.v.t. | EUR 3,747.00 | EUR 0.00 | NVT |
| totaal_kortingen_p1 | n.v.t. | EUR 3,679.00 | EUR 0.00 | NVT |
| box3_heffing | n.v.t. | EUR 0.00 | EUR 0.00 | NVT |

## tc_2025_017 - Partners met AOW en pensioen zonder vermogen

### Huishouden

| Verwacht | Berekend | Verschil | Status |
|---:|---:|---:|---|
| EUR 4,429.00 | EUR 4,428.00 | EUR -1.00 | PASS |

### Per persoon

| Persoon | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| P1 | n.v.t. | EUR 3,239.00 | EUR 0.00 | NVT |

### Componentniveau

| Component | Verwacht | Berekend | Verschil | Status |
|---|---:|---:|---:|---|
| box1_ib_p1 | EUR 2,987.00 | EUR 2,987.00 | EUR 0.00 | PASS |
| totaal_premies_p1 | n.v.t. | EUR 3,565.00 | EUR 0.00 | NVT |
| totaal_kortingen_p1 | n.v.t. | EUR 3,313.00 | EUR 0.00 | NVT |
| box3_heffing | n.v.t. | EUR 0.00 | EUR 0.00 | NVT |
| box1_ib_p2 | EUR 2,170.00 | EUR 2,170.00 | EUR 0.00 | PASS |
| totaal_premies_p2 | n.v.t. | EUR 2,590.00 | EUR 0.00 | NVT |
| totaal_kortingen_p2 | n.v.t. | EUR 3,571.00 | EUR 0.00 | NVT |