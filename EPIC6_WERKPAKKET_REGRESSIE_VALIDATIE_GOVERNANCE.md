# Epic 6 — Regressie, validatie en governance

## Status

**Technische implementatie gereed — productvalidatie open (26 juli 2026).**

De nulmeting waarmee Epic 6 start:

- volledige pytest-suite: 286 tests, 282 geslaagd en 4 gefaald
- totale line coverage: 52%
- falende tests: twee API-baselineregressies en twee IB-2025-regressietests
- strikte IB-2025-validatie: 2 WARN en 4 FAIL
- React-productiebouw: geslaagd

Deze afwijkingen zijn startinput voor Epic 6 en mogen niet stilzwijgend als
nieuwe baseline worden geaccepteerd.

Uitkomst:

- 295 tests: 293 geslaagd, 2 strikt geregistreerde xfails
- 52% line coverage
- raw/normalized-driftcontrole groen
- React-productiebouw groen
- externe IB-2025-validatie blijft zichtbaar op 2 WARN en 4 FAIL
- één rekenbug opgelost: niet-verrekenbare heffingskorting wordt niet langer
  als uitbetaalbare maandcashflow verwerkt
- testmatrix, markers, regressieprotocol, afwijkingenregister, validatie-index,
  PR-template en gesplitste CI-poorten opgeleverd

Technische go/no-go: **GO**. Product-go/no-go voor Epic 7 blijft **OPEN** tot
de drie bron- en tolerantievragen onder Gebruikersvalidatie zijn beantwoord.

## Doel

Maak correctheid en wijzigingsdiscipline aantoonbaar. Iedere functionele
berekenstap krijgt een herkenbaar testcluster, iedere fiscale wijziging volgt
dezelfde validatieketen en bekende afwijkingen worden als expliciete schuld
beheerd.

## Functionele positie

Primaire stap: `Resultaten`, als verificatielaag over de volledige keten.

Afhankelijke stappen:

`Scenario -> Persoonsgegevens -> Pensioen -> AOW -> Arbeid -> Bruto inkomen ->
Eigen woning -> Box 1 -> Heffingskortingen -> Netto inkomen -> Box 3 ->
Vermogen -> Resultaten`

Source of truth:

- bouwsteentests voor losse regels
- engine-output voor samengestelde uitkomsten
- genormaliseerde belastingtestcases voor externe referentievergelijking

## Scope

- testmatrix per functionele berekenstap
- naamgeving en markers voor testclusters
- regressieprotocol voor bugs
- governance voor raw/normalized fixtures
- classificatie en eigenaarschap van bekende afwijkingen
- CI-poorten voor unit-, contract- en referentietests
- herleidbaar validatierapport

Niet in scope:

- fiscale afwijkingen stil rebaselinen
- legacycode verwijderen; dat hoort bij Epic 7
- nieuwe pensioenfunctionaliteit

## Werkstromen

### 1. Testinventarisatie en matrix

Classificeer iedere test naar precies één primaire berekenstap en optioneel één
hoger integratiepad. Leg ontbrekende dekking en dubbel geteste regels vast.

Deliverable: `tests/TESTMATRIX_BEREKENSTAPPEN.md`.

### 2. Teststructuur en markers

Introduceer pytest-markers voor minimaal:

- `bouwsteen`
- `engine`
- `contract`
- `referentie`
- `presentatie`

De bestaande bestandsstructuur mag incrementeel worden gemigreerd; een brede
bestandsverplaatsing is niet vereist.

### 3. Regressieprotocol

Iedere bugfix bevat:

1. herleidbare oorzaak en primaire berekenstap
2. directe test op de eigenaar van de regel
3. regressietest op het pad waar de fout zichtbaar werd
4. fixture-update indien fiscale of cashflow-output verandert
5. classificatie van verwacht verschil

Deliverable: `docs/REGRESSIEPROTOCOL.md`.

### 4. Fixture- en referentiegovernance

Leg vast:

- raw is menselijke bron en wordt nooit uit normalized teruggerekend
- normalized wordt uitsluitend door het normalisatiescript gegenereerd
- referentiewaarden veranderen alleen met bronvermelding en reviewreden
- validatierapporten tonen PASS, WARN en FAIL zonder verdoezeling
- bekende afwijkingen hebben eigenaar, oorzaakstatus en vervolgstap

### 5. CI-poorten

Maak afzonderlijke, herkenbare controles voor:

- snelle bouwsteen- en contracttests
- volledige enginesuite
- fixture-normalisatiecontrole
- externe referentievalidatie
- React-build

Bekende referentiefouten mogen tijdelijk als expliciete non-blocking rapportage
bestaan; onverwachte regressie mag nooit non-blocking zijn.

### 6. Validatierapport en governance

Maak één index die per functionele stap verwijst naar tests, fixtures,
tariefbronnen, open afwijkingen en laatste validatiedatum.

## Verplichte scenario’s

- alleenstaand werkend
- alleenstaand AOW/pensioen
- partners met verschillende AOW-status
- eigen woning met en zonder aftrek
- Box 3 onder en boven vrijstelling
- gemengd sparen/beleggen
- incidentele ontvangst en uitgave
- meerjarige vermogensdoorloop
- tarieffallback en periodeoverride

## Definition of Done

Epic 6 is gereed als:

1. iedere berekenstap een eigenaar en testcluster heeft
2. alle bestaande tests in de matrix zijn geclassificeerd
3. het regressieprotocol in instructies en CI is geborgd
4. raw, normalized en validatierapport reproduceerbaar aansluiten
5. bekende fiscale afwijkingen expliciet geregistreerd zijn
6. CI onverwachte contract- en rekenregressies blokkeert
7. een nieuwe bug aantoonbaar van oorzaak naar regressietest te volgen is

## Gebruikersvalidatie

De producteigenaar moet bevestigen:

- welke externe fiscale referentie leidend is
- welke tolerantie per validatieniveau acceptabel is
- of bekende IB-2025-afwijkingen eerst opgelost moeten worden voor Epic 7
