# Afwijkingenregister IB 2025

Laatste validatie: 7 september 2026.

De machineleesbare borging staat in `bekende_afwijkingen.json`. De bedragen
hieronder zijn applicatie minus externe verwachting.

| ID | Status | Verschil | Classificatie | Vervolgstap |
| --- | --- | ---: | --- | --- |
| E6-AFW-001 / `tc_2025_006` | PASS | +€0,37 | tolerantieverschil | afronding blijft zichtbaar |
| `tc_2025_007` | PASS | +€0,53 | tolerantieverschil | afronding blijft zichtbaar |
| E6-AFW-003 / `tc_2025_008` | FAIL | -€376,13 | referentieschuld | AOW-heffingskortingen tegen primaire bron valideren |
| `tc_2025_009` | PASS | +€3,70 | referentieschuld | premies en box 1 per partner valideren |
| E6-AFW-002 / `tc_2025_010` | FAIL | -€1.622,89 | bronconflict | leidende AOW-bron voor fiscaal partnerschap kiezen |
| `tc_2025_011` | FAIL | -€2.231,92 | referentieschuld | AOW-kortingen en premies voor twee gepensioneerden valideren |
| `tc_2025_016` | PASS | +€1,00 | tolerantieverschil | interne OLA-afronding AHK verklaren |
| `tc_2025_017` | PASS | -€1,00 | tolerantieverschil | interne OLA-afronding AHK verklaren |
| `tc_2025_019` | PASS | +€1,00 | tolerantieverschil | AHK P1: OLA €1.206, app €1.205 |

Review 7 september: afbouwgrens ouderenkorting gecorrigeerd naar €45.308.
TC010 krijgt daardoor €663 extra korting; de oude bronverwachting is niet
aangepast. Het verschil verandert van -€959,89 naar -€1.622,89. Het AOW-bronconflict
blijft open. De nieuwe eenvoudige pensioencases 016/017 bevestigen de fiscale
behandeling bij gelijke bruto invoer, niet de juiste SVB-uitkeringshoogte.

Review 6 september: schijf- en premiegrenzen en OLA-afronding gecorrigeerd op primaire bron.
Oude externe verwachtingen blijven intact; de gewijzigde verschillen zijn
bewust herbeoordeeld, inclusief de verslechtering voor oude AOW-referenties.
De vorige bedragen staan in het JSON-register. Zie `docs/OLA_VALIDATIE_2025.md`.

## API-regressiepad

`tc_2025_006` voldoet nu aan de bestaande API-baseline; zijn xfail is verwijderd.
`tc_2025_010` blijft strikt xfail. Nieuwe live brongevallen `tc_2025_013` tot
en met `tc_2025_015` zijn PASS, ook bij de ongewijzigde OLA-tolerantie van €1.
Hun fiscale jaaruitkomsten wijken €0 af. Maandverdeling blijft op centen;
de API-test borgt dat ook de opgetelde maanden binnen deze tolerantie blijven.
De tijdelijke xfails voor 013/014 zijn verwijderd. Na de SVB-broncorrectie zijn
016/017 in het API-pad strikt xfail: hun oude bruto AOW-invoer komt niet meer
overeen met de productieflow. De tabel hierboven betreft het historische fiscale
pad met expliciet bevroren bruto broninvoer, niet deze API-bronconflicten.
Nieuwe SVB-cases 018/019 toetsen het fiscale API-jaarbedrag met de oorspronkelijke
€1-tolerantie. Maandafronding wordt afzonderlijk begrensd. 018 is exact, 019 +€1.
OLA-invoer is expliciet naar hele euro omlaag afgerond; enginecashflow behoudt centen.
Oude bronverwachtingen en API-baselines zijn niet gewijzigd.

- de suite blijft bruikbaar als blokkerende poort
- de afwijkingen blijven zichtbaar
- een onverwachte PASS faalt de suite en dwingt herbeoordeling af

## Productbesluiten nodig

1. Welke externe fiscale bron is leidend: simulatortranscript, officiële
   rekentooluitvoer of handmatig samengestelde componentwaarden?
2. Geldt tolerantie op huishoudtotaal, persoonsniveau of elk component?
3. Oude gemengde AOW-bronconflicten heropnemen met de SVB-bronperioden;
   de gewone gevallen zijn nu gedekt door 018/019.
