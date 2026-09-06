# Afwijkingenregister IB 2025

Laatste validatie: 6 september 2026.

De machineleesbare borging staat in `bekende_afwijkingen.json`. De bedragen
hieronder zijn applicatie minus externe verwachting.

| ID | Status | Verschil | Classificatie | Vervolgstap |
| --- | --- | ---: | --- | --- |
| E6-AFW-001 / `tc_2025_006` | PASS | +€2,93 | tolerantieverschil | afronding blijft zichtbaar |
| `tc_2025_007` | PASS | +€2,73 | tolerantieverschil | afronding blijft zichtbaar |
| E6-AFW-003 / `tc_2025_008` | FAIL | -€374,32 | referentieschuld | AOW-heffingskortingen tegen primaire bron valideren |
| `tc_2025_009` | WARN | +€7,86 | referentieschuld | premies en box 1 per partner valideren |
| E6-AFW-002 / `tc_2025_010` | FAIL | -€954,92 | bronconflict | leidende AOW-bron voor fiscaal partnerschap kiezen |
| `tc_2025_011` | FAIL | -€2.227,94 | referentieschuld | AOW-kortingen en premies voor twee gepensioneerden valideren |

Review 6 september: schijf- en premiegrenzen gecorrigeerd op primaire bron.
Oude externe verwachtingen blijven intact; de gewijzigde verschillen zijn
bewust herbeoordeeld, inclusief de verslechtering voor oude AOW-referenties.
De vorige bedragen staan in het JSON-register. Zie `docs/OLA_VALIDATIE_2025.md`.

## API-regressiepad

`tc_2025_006` voldoet nu aan de bestaande API-baseline; zijn xfail is verwijderd.
`tc_2025_010` blijft strikt xfail. Nieuwe live brongevallen `tc_2025_013` en
`tc_2025_014` zijn strikt xfail tegen de ongewijzigde OLA-tolerantie van €1:
resterende centen/hele-euro-afrondingsschuld +€3,02 en +€3,21 op het jaarpad.
De oudere validatiepipeline noemt dit PASS bij zijn bestaande €5-tolerantie;
dat is nadrukkelijk geen PASS van de OLA-vergelijking. Directe hogere tests
bewaken apart de gecorrigeerde componenten en centenuitkomsten.

- de suite blijft bruikbaar als blokkerende poort
- de afwijkingen blijven zichtbaar
- een onverwachte PASS faalt de suite en dwingt herbeoordeling af

## Productbesluiten nodig

1. Welke externe fiscale bron is leidend: simulatortranscript, officiële
   rekentooluitvoer of handmatig samengestelde componentwaarden?
2. Geldt tolerantie op huishoudtotaal, persoonsniveau of elk component?
3. Welk AOW-brutobedrag is leidend bij fiscaal partnerschap?
