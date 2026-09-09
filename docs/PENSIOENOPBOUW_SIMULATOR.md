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
per post als **Gelijk in alle drie varianten** getoond, met de concrete reden.
Deze posten behouden hun oorspronkelijke start, bedrag, einde en waardeperiodes,
en tellen ongewijzigd mee in de volledige vergelijking. Alleen bij ontbrekende
startdatum blijft **Nog niet berekend** gelden. Geldige
pensioenposten leveren wel drie afzonderlijke uitkeringsramingen op. De
statuslijst toont ook reeds ingegane, ongewijzigde pensioenen. Bij een
onvolledige raming worden totaalkaarten en de huishoudvergelijking verborgen;
er wordt geen nuluitkomst als volledige raming gepresenteerd. De oorspronkelijke
posten worden nooit automatisch verwijderd of aangepast om deze controle te
omzeilen. Alle loonposten moeten een einddatum hebben en mogen geen
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

### Validatie per pensioenpost

Deze correctie hoort bij de stap **Pensioen**. De scenario-adapter
`actuariele_scenarios.py` bepaalt per invoerpost de status; de bestaande
actuariële bron en tarieven blijven ongewijzigd. Uitvoer bevat `posten` en
`volledig`. Bij een onvolledige raming retourneert de API `vergelijking: null`
en `totale_premie: null`: afhankelijke netto- en vermogensvergelijkingen worden
niet als volledig doorgerekend. Tests dekken iedere afzonderlijke afwijsreden,
geldige posten naast ongeldige, alleen ongeldige posten en ongewijzigde invoer.


## Eén huishoudscenario, twee pensioenkeuzes

**Pas toe in dit scenario** is de standaardactie. De gekozen bedragen en datums
worden in het actieve scenario verwerkt, inclusief eventuele premie. De naam
en het aantal scenario's veranderen niet. Je blijft op de scenariopagina om
daarna voor P2 te kiezen. Het overzicht bovenaan toont de keuze per persoon.
**Bekijk het gezamenlijke meerjarenplan** opent de bijgewerkte Resultaten.

**Bewaar als nieuw scenario** maakt alleen op expliciete keuze een kopie.
Onvolledige ramingen zijn niet toepasbaar. De bestaande browseropslag bewaart
beide keuzes, oorspronkelijke pensioenposten en de IDs van toegevoegde premies.

Bij opnieuw vergelijken wordt alleen de oorspronkelijke pensioeninvoer van de
gekozen persoon hersteld voor de simulator, met behoud van de andere persoon
en overige posten. Opnieuw toepassen vervangt diens eerdere keuze en premie.
Aannames worden per persoon bewaard. Verwijderde of handmatig gewijzigde
toegepaste pensioenposten geven een melding, zodat wijzigingen niet ongemerkt
worden overschreven. Oudere keuzes zonder bewaarde oorspronkelijke posten
houden de terugkeer naar het oorspronkelijke scenario als migratieroute.

## Jaarlijkse belastingvergelijking

**Belasting en netto resultaat per jaar** toont de drie varianten naast elkaar
per kalenderjaar. Verschillen zijn variant minus *Wachten zonder doorbetalen*.
Een positief belastingverschil betekent meer belasting.

Getoond worden bruto inkomen exclusief rendement, box 1 na heffingskortingen,
box 3, belastingverschil, engine-belastingdruk en verschil in procentpunten,
netto inkomen, netto verschil, voortzettingspremie, vrije cashflow en eindvermogen.
De premie zit al in de vrije cashflow. AOW-fases horen bij de gekozen persoon,
bedragen bij het huishouden. De AOW-datum komt uit de bestaande AOW-engine.

De belastingdruk volgt de bestaande definitie: belasting na kortingen inclusief
box 3 / bruto inclusief rendement. Netto ingevoerd loon is geen onderdeel van
die bruto grondslag: dit is bij gemengde invoer geen volledige belastingdruk
op alle inkomsten. Toekomstige fiscale bedragen volgen de engine-aannames.

Primaire stap van deze uitbreiding: **Resultaten**, bron
calculations/actuariele_jaarvergelijking.py. Invoer is bestaande jaaroutput;
er komen geen fiscale tarieven of belastingformules bij. De Scenario-opslag
kopieert uitsluitend bedragen en datums uit de enginevariant. De daaropvolgende
Pensioen-, belasting- en vermogensberekeningen blijven bij hun bestaande owners.
Validatie: directe belastingdelta-test, API-herberekening van alle drie varianten
met identieke jaaroutput, frontend opslag/herladen en presentatie van AOW-fases
en bedragen. Fixture: case 018, toepassen_en_jaarvergelijking.


### Ongewijzigd meenemen als expliciete aanname

Een niet-actuarieel-berekenbare post met oorspronkelijke ingangsdatum blijft
op gebruikerskeuze in alle drie varianten gelijk. De scenario-adapter is de
source of truth voor deze Pensioen-aanname. Bedrag, bedragtype, frequentie,
start, einde en waardeperiodes worden niet aangepast; geen extra premie.
Dit is geen bevestiging dat eerder stoppen voor die regeling werkelijk
zonder gevolgen blijft. De reden en aanname staan zichtbaar per post.

Ook als alle posten zo worden meegenomen, kan de gebruiker de drie identieke
uitkomsten vergelijken en als nieuw scenario bewaren. De bruto kaarten tonen
alleen berekende regelingen, nooit een onvolledig totaal als totaalpensioen.
De volledige cashflow en belastingvergelijking bevatten alle posten. Zonder
oorspronkelijke ingangsdatum blijft de raming onvolledig en niet toepasbaar.
API-regressie controleert identieke jaaroutput voor drie fallbackvarianten.


### Foutmeldingen

De simulator valideert het serviceadres en onderscheidt netwerkfouten,
API-invoermeldingen en een niet-JSON antwoord (met HTTP-status). Een mislukte
nieuwe aanvraag laat geen oude simulatie als actuele uitkomst staan.


### Contract voor toepassen per persoon

Primaire stap **Scenario**, source of truth voor opslag en herstel:
frontend-react/src/planner/actuarialVariant.js. Invoer zijn de oorspronkelijke
posten en de enginevariant; uitvoer is een snapshot met maximaal één actieve
keuze per persoon. Er worden geen pensioen- of fiscale formules toegevoegd.
Tests dekken P1 toepassen, P2 toevoegen, P1 opnieuw kiezen, verwijderen van
alleen de eerdere P1-premie, behoud P2, browserherladen en ongewijzigde bron.
Rekenregels en tarieven blijven bij de bestaande engines.
