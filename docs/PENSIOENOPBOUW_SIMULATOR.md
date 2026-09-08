# Pensioen schatten bij eerder stoppen

Open **Scenario’s → Wat krijg ik als ik eerder stop?** en kies **Bereken mijn drie opties**.
De simulator neemt de laatste werkdag uit de loonposten van de gekozen persoon,
en bedragen en oorspronkelijke ingangsdatums uit diens pensioenposten in het
actieve scenario. Je hoeft geen offerte of drie uitkeringsbedragen in te vullen.

1. **Direct pensioen ontvangen:** minder opbouw en een actuariële verlaging
   omdat de uitkering eerder begint.
2. **Wachten, niet doorbetalen:** minder opbouw, uitkering vanaf de oorspronkelijke
   datum van iedere regeling.
3. **Premie doorbetalen, later pensioen:** een geschatte maandpremie financiert
   de ontbrekende opbouw; het oorspronkelijke pensioenbedrag blijft staan.

De derde variant is een financieringsraming, geen reglementaire fondspremie.
De premie staat eenmaal als netto uitgave in de cashflow, zonder belastingaftrek.
Bij meerdere regelingen stopt iedere premie op de eigen pensioendatum.
De kaarten tonen het totaal van de betrokken regelingen; reeds ingegaan pensioen
blijft in de huishoudberekening staan en wordt apart als ongewijzigd vermeld.
AOW volgt de bestaande AOW-engine.

## Aannames controleren

De import vertelt niet betrouwbaar welk deel al opgebouwd is. Standaard
behandelen we toekomstige bedragen als **te bereiken pensioen** en nemen we
gelijkmatige opbouw vanaf 25 jaar aan. Vink bij **Aannames** pensioen bij eerdere
werkgevers of volledig opgebouwde rechten aan als **al opgebouwd**. Daarop volgt
geen opbouwkorting en geen voortzettingspremie. Deze aanname over de opbouwhistorie
kan veel meer verschil maken dan de actuariële vervroegingsfactor.

Instelbaar per scenario: persoon, startleeftijd opbouw, rekenrente en
premieopslag. Standaard 3% rente en 10% opslag; dit zijn verkenningsaannames.
De getoonde gevoeligheid varieert alleen de rente (1%, 5% en de gekozen rente),
en is geen betrouwbaarheidsinterval. Instellingen worden via de bestaande
browseropslag bewaard; na wijziging moet opnieuw worden berekend.

De eerste volledige maand na de laatste werkdag is de vervroegde ingang.
Pensioenstart wordt op kalendermaand verwerkt. Tijdelijk pensioen, netto
pensioen en waardeperiodes worden voor de betrokken toekomstige posten
afgewezen. Alle loonposten moeten een einddatum hebben en mogen geen
waardeperiodes bevatten. De horizon moet stoppen en alle oorspronkelijke
pensioendatums omvatten. Partner en andere invoer blijven behouden.

## Rekencontract: Pensioen

Primaire functionele stap: **Pensioen**. Source of truth voor de raming:
`src/pensioen/calculations/actuariele_schatting.py`.
Invoer: geboortedatum, stopmaand, oorspronkelijke start, bruto maandpensioen,
indexatie en expliciete aannames. Uitvoer: opbouwfactor, vervroegingsfactor,
drie bruto maandpensioenen en geschatte maandpremie.

- Opbouwfactor = maanden vanaf aangenomen opbouwstart tot stoppen / maanden
  vanaf opbouwstart tot oorspronkelijke pensioenstart, maximaal 1.
  Voor reeds opgebouwd pensioen is de factor 1.
- Wachten zonder premie = oorspronkelijk bedrag × opbouwfactor.
- Vervroegingsfactor = contante waarde van €1 uitgesteld maandpensioen /
  contante waarde van €1 direct maandpensioen.
- Direct pensioen = wachten zonder premie × vervroegingsfactor.
- Maandpremie = ontbrekend maandpensioen × contantewaardefactor uitgesteld /
  contantewaardefactor tijdelijke premiebetalingen × (1 + kostenopslag).

Alle contante waarden gebruiken overleving, maandelijkse discontering en
betaling aan het begin van de maand. Indexatie is maandelijks equivalent in
de waardering; de bestaande cashflow-engine verwerkt componentgroei per
kalenderjaar. De raming is dus een maandbenadering, geen exacte fondsberekening.

Sterftebron: [AG2024](https://www.actuarieelgenootschap.nl/kennisbank/prognosetafel-ag2024-2).
De gepinde officiële Excel is herleidbaar met SHA256 in
`config/actuarieel_ag2024.json`. `tools/actuarieel/normaliseer_ag2024.py`
regenereert dit bestand uit de Excel. Het model volgt leeftijd én kalenderjaar
(2025–2200), met afzonderlijke overleving voor mannen en vrouwen, 50/50 gewogen
bij aanvang. Jaarsterfte wordt naar maandsterfte omgerekend met constante
sterfte-intensiteit; uitkeringen na leeftijd 120 worden afgekapt.
Aannames staan in `config/actuariele_schatting.json`.
Partnerpensioen, salarisgeschiedenis, fondsspecifieke rechten en Wtp-transitie
zijn geen onderdeel van deze schatting.

`actuariele_scenarios.py` vertaalt de raming naar drie diepe scenariokopieën.
API: `POST /api/v1/simulaties/actuarieel`, met `berekening` en optionele
`keuze`. De bestaande cashflow-, belasting- en vermogensengines berekenen
de gevolgen. React presenteert de engine-uitvoer en introduceert geen fiscale
formules. Tests: `tests/test_actuariele_schatting.py`, frontend-presentatietests
en interne fixture `metadata.regressies_actuarieel` in testcase 018.
Externe OLA-verwachtingen veranderen niet.

## Bestaande handmatige API

`POST /api/v1/simulaties/pensioenopbouw` blijft compatibel voor eerder
opgeslagen handmatige keuzes: drie expliciet opgegeven bedragen, één regeling,
maandgrenzen en een zelf opgegeven premie. Deze API schat geen actuariële
rechten. Bron/datum blijven verplicht in de stand uitvoerdersgegevens.
Het omslagpunt komt uit cumulatieve engine-cashflows en geldt alleen binnen
de berekeningshorizon. Tests: `test_pensioenopbouw_simulator.py` en
`metadata.regressies_opbouw`. De nieuwe schermroute gebruikt de actuariële API.
