# Afwijkingenregister IB 2025

Laatste validatie: 26 juli 2026.

De machineleesbare borging staat in `bekende_afwijkingen.json`. De bedragen
hieronder zijn applicatie minus externe verwachting.

| ID | Status | Verschil | Classificatie | Vervolgstap |
| --- | --- | ---: | --- | --- |
| E6-AFW-001 / `tc_2025_006` | WARN | -€31,29 | tolerantieverschil | externe componentbron en afronding bevestigen |
| `tc_2025_007` | WARN | -€31,49 | tolerantieverschil | externe componentbron en afronding bevestigen |
| E6-AFW-003 / `tc_2025_008` | FAIL | -€300,32 | referentieschuld | AOW-heffingskortingen tegen primaire bron valideren |
| `tc_2025_009` | FAIL | -€60,58 | referentieschuld | premies en box 1 per partner valideren |
| E6-AFW-002 / `tc_2025_010` | FAIL | -€788,20 | bronconflict | leidende AOW-bron voor fiscaal partnerschap kiezen |
| `tc_2025_011` | FAIL | -€1.826,06 | referentieschuld | AOW-kortingen en premies voor twee gepensioneerden valideren |

## API-regressiepad

`tc_2025_006` en `tc_2025_010` overschrijden ook de bestaande
API-afwijkingsbaseline. Ze zijn daarom als strikte `xfail` geregistreerd:

- de suite blijft bruikbaar als blokkerende poort
- de afwijkingen blijven zichtbaar
- een onverwachte PASS faalt de suite en dwingt herbeoordeling af

## Productbesluiten nodig

1. Welke externe fiscale bron is leidend: simulatortranscript, officiële
   rekentooluitvoer of handmatig samengestelde componentwaarden?
2. Geldt tolerantie op huishoudtotaal, persoonsniveau of elk component?
3. Welk AOW-brutobedrag is leidend bij fiscaal partnerschap?
