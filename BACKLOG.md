# BACKLOG - Pensioenplanner Feature & Improvement Backlog

> Statuscontrole 26 juli 2026: dit is de brede productbacklog en bevat ook
> historische planning en nog niet opnieuw gevalideerde statussen. Voor de
> actuele herstructurering zijn `UITVOERINGSPLAN_HERSTRUCTURERING.md`,
> `EPIC6_ISSUES_BACKLOG.md` en `EPIC7_ISSUES_BACKLOG.md` leidend.

## 📋 GEREGISTREERDE PRODUCTSCOPE (v1.0)

### ✅ Werkende Use Cases

#### Inkomsten & Uitgaven

1. **Loon met bruto/netto keuze** - Vast maandloon, bruto of netto, met belastingberekening per persoon
2. **Variabel loon** - Meerdere periodes met verschillende bedragen (bonus, loonsverhoging)
3. **Pensioenuitkering** - Ouderdomspensioen vanaf pensioenleeftijd, bruto, met belasting
4. **AOW-uitkering** - Automatische berekening vanaf AOW-leeftijd, gekoppeld aan geboortedatum
5. **Overige inkomsten** - Uitkeringen, lijfrente, huurinkomsten (bruto of netto)
6. **Huishoudelijke uitgaven** - Vaste lasten per maand/jaar (huur, verzekeringen, boodschappen)
7. **Inhoudingen** - Pensioenpremie, vakbondsbijdrage (netto, na belasting)
8. **Eenmalige cashflows** - Erfenis, auto kopen, verbouwing (exacte datum)

#### Vermogen & Rendement

9. **Spaarrekening** - Spaargeld met rendement, compound interest, maandelijks berekend
10. **Beleggingsportefeuille** - Beleggingen met hoger rendement dan sparen
11. **Overschot/tekort verwerking** - Netto overschot → spaarrekening (+), tekort → spaarrekening (-)
12. **Box 3 heffing** - Fictief rendement op vermogen per 1 januari, gewogen naar sparen/beleggen
13. **Dynamische vermogensverdeling** - Automatische berekening spaargeld vs beleggingen fractie

#### Belasting & Heffingen

14. **Box 1 progressief** - Schijvenstelsel met AOW-korting
15. **Algemene heffingskorting** - Automatisch berekend op basis van inkomen
16. **Arbeidskorting** - Bij arbeidsinkomen, afbouwend bij hoge inkomens
17. **Ouderenkorting** - Voor 65+ met laag inkomen
18. **Partner belasting** - Aparte berekening per persoon, dubbele box 3 vrijstelling

#### Planning & Scenario's

19. **Multi-scenario vergelijking** - Meerdere toekomstscenario's naast elkaar
20. **Tijdshorizon flexibel** - Prognose van jaar X tot jaar Y
21. **Groeipercentages** - Inflatie, indexatie pensioen, loonstijging per component
22. **Sessie persistentie** - Opslaan en laden van complete sessies

#### Import & Export

23. **MPO CSV import** - MijnPensioenoverzicht.nl ouderdomspensioenen
24. **MPO JSON import** - Stichting Pensioenregister format (auto-detect)
25. **Excel rapport** - Uitgebreide cashflowprognose met grafieken
26. **Accountantsoverzicht** - Gedetailleerde maand-voor-maand uitsplitsing

---

## 🔮 TOEKOMSTIGE FEATURES

## 🚀 STRATEGISCHE EPICS (juli 2026)

### Historische prioriteitsvolgorde
1. Rond #401 volledig af (API-contracten en stabiele endpoints).
2. Start direct daarna #403 als verplichte kwaliteitspoort in CI.
3. Plan #405 pas na stabiele regressiebasis vanuit #403.

### Historisch uitvoeringsplan

#### Stap A: #403 Kwaliteitspoort activeren
Doel:
- API-contracten en regressietests verplicht maken voor merges.

Minimum oplevering:
- Contracttests voor:
	- `GET /api/v1/health`
	- `POST /api/v1/berekeningen`
	- `POST /api/v1/vergelijkingen`
	- `POST /api/v1/rapportages/excel`
- Regressieset op `tests/fixtures/belasting_testcases/normalized/*_normalized.json`.
- CI-fail op afwijkingen buiten afgesproken toleranties.

Gate om naar #402 te gaan:
- 5 opeenvolgende groene CI-runs op `main` zonder regressiebreuk.

#### Stap B: #402 Parametercodering starten
Startmoment:
- Direct na Gate A.

Scope eerste iteratie:
- Codesets voor inkomenssoorten, vermogenssoorten en frequenties.
- Validatie op codes in API-schema's.
- Lookup-tabellen voor labels (NL) als bron voor UI en rapportage.

Gate om #406 te starten:
- Geen hardcoded labels meer in API-responses voor gecodeerde velden.
- Minimaal 1 backward-compat pad voor bestaande invoer gevalideerd.

#### Stap C: #406 Gebruiksvriendelijke UI herstellen
Startmoment:
- Na Gate B (mag in laatste fase van #402 voorbereid worden).

Scope eerste iteratie:
- Expliciete Berekenen-knop en verouderd-status bij invoerwijziging.
- Wizard/progress-flow over kernstappen.
- Eenduidige foutmeldingen gekoppeld aan API-validatiecodes.

#### #401: Epic 1 - API-laag + simpele API-UI 🔴 HIGH
> Let op: dit is de API-roadmap. Dit is niet **Epic 1 — Fiscale bouwstenen
> isoleren** uit `UITVOERINGSPLAN_HERSTRUCTURERING.md`; die fiscale Epic 1 is
> afgerond en gearchiveerd in
> `docs/archive/epics/EPIC1_ISSUES_BACKLOG.md`.

**Beschrijving**: Stateless API-first MVP bovenop de bestaande rekenengine.

**In scope (MVP)**:
- FastAPI API met OpenAPI/Swagger
- Endpoints voor health, berekening, scenariovergelijking en Excel-rapportage
- Inheritance-validatie op API-input (cycles/orphans/self-parent)
- Simpele Streamlit API-client met expliciete Berekenen-knop
- Verouderd-status in UI bij invoerwijziging sinds laatste berekening

**Opgeleverd in deze iteratie**:
- `src/pensioen/api/main.py`
- `src/pensioen/api/schemas.py`
- `src/pensioen/api/serialisatie.py`
- `app_api_client.py`
- `tests/test_api_main.py`

**Status**: ✅ GEÏMPLEMENTEERD — functionele validatie loopt via Epic 5/6

---

#### #402: Epic 2 - Referentie- en parametertabellen 🔴 HIGH
**Beschrijving**: Vaste codes + lookup-tabellen voor domeinwaarden.

**Details**:
- Codes voor inkomenssoorten, vermogenssoorten, frequenties, categorieen, datumtypes en belastingsoorten
- Lookup-tabellen voor labels en meertaligheid
- Validatie op codes, onafhankelijk van hoofdletters/spaties

**Afhankelijkheden**: #401

**Status**: ✅ GEÏMPLEMENTEERD — beheer en governance worden in Epic 6 geborgd

---

#### #403: Epic 3 - API-validatie en regressietestframework 🔴 HIGH
**Beschrijving**: Uitgebreide testset voor businesslogica via API.

**Details**:
- API-contracttests
- Regressietests met vaste referentiesets
- Validatiesets en scenariovergelijkingen
- Startpunt voor automatische acceptatietests

**Afhankelijkheden**: #401

**Acceptatiecriteria (MVP-gate)**:
- API-contracttests dekken alle primaire endpoints en foutpaden.
- Regressieset draait op genormaliseerde referentiesets (`*_normalized.json`).
- CI faalt bij afwijkingen buiten afgesproken toleranties.
- Een rekenwijziging is niet mergebaar zonder bijgewerkte testcase-artefacten.

**Uitvoeringssubtaken #403 (operationeel)**:
- API-contracttests uitbreiden met foutpaden per endpoint (422/validatiecodes).
- Regressietest toevoegen die alle `normalized/*_normalized.json` cases doorrekent.
- Tolerantiegrenzen centraliseren in testconfig (PASS/WARN/FAIL drempels).
- CI workflow uitbreiden met verplichte stap: normalize -> validatiepipeline -> API-regressie.
- Merge policy: blokkeren bij regressieafwijking buiten tolerantie.

**Huidige voortgang #403 (26 juli 2026)**:
- Contracttests basis + extra foutpaden voor vergelijkingen/rapportage staan in `tests/test_api_main.py`.
- Batch-regressietests draaien op de genormaliseerde set.
- Twee API-baselineafwijkingen zijn verklaard en strikt als bekende `xfail`
  geregistreerd.
- CI-, fixture- en baseline-governance zijn geïmplementeerd.

**Status**: ✅ GEÏMPLEMENTEERD — externe productvalidatie blijft open

---

#### #404: Epic 4 - Audit trail 🟡 MEDIUM
**Beschrijving**: Volledige mutatiegeschiedenis van scenario-invoer.

**Details**:
- Wie wijzigde wat
- Oude en nieuwe waarde
- Datum/tijd
- Optionele reden van wijziging

**Afhankelijkheden**: #401, #403

**Status**: 📝 PLANNED

---

#### #405: Epic 5 - Rekenmodel uitbreidingen 🔴 HIGH
**Beschrijving**: Nauwkeuriger modelleren van praktijkwijzigingen.

**Details**:
- Werkelijke vermogensstand als correctiemechanisme
- Componenten per afgeleid scenario deactiveren (enabled-flag)
- Jaarconfiguratie belasting met geldigheidsperiodes en zonder terugwerkende kracht
- Uitgebreide validatie op modelconsistentie

**Afhankelijkheden**: #401, #402

**Status**: 📝 PLANNED

---

#### #406: Epic 6 - UX-flow en berekenstatus 🟡 MEDIUM
**Beschrijving**: Betere gebruikersflow met expliciete herberekening.

**Details**:
- Wizard/progress-bar benadering
- Duidelijke Berekenen-knop
- Status "gegevens gewijzigd sinds laatste berekening"
- Resultaatweergave met verouderd/actueel indicatie

**Afhankelijkheden**: #401

**Status**: 📝 PLANNED

---

#### #407: Epic 7 - Privacy-by-design + authenticatie 🔴 HIGH
**Beschrijving**: Client/server-architectuur met minimale serverdata.

**Details**:
- Geen serveropslag van persoonsgegevens
- Lokale opslag persoonsgegevens aan clientzijde
- Authenticatie en sessiemanagement (hashes, tokens, timeout)
- Alleen noodzakelijke data tijdelijk verwerken op server

**Afhankelijkheden**: #401, #403

**Status**: 📝 PLANNED

---

#### #408: Epic 8 - Monte Carlo module 🟡 MEDIUM
**Beschrijving**: Onzekerheidsanalyse bovenop scenario's.

**Details**:
- Selecteerbare onzekerheidsvariabelen
- Kansverdelingen en bandbreedtes
- Percentielrapportage (bijv. P5/P50/P95)
- Outlier-beperking in visualisatie

**Afhankelijkheden**: #401, #402, #403

**Status**: 📝 PLANNED

---

### High Priority - Vermogenstypen & Box 3

#### #001: Eigen woning 🔴 HIGH
**Beschrijving**: Toevoegen van eigen woning als vermogenstype

**Details**:
- WOZ-waarde met jaarlijkse groei
- Vrijstelling voor box 3 (eigen woning eigenwoningforfait sinds 2026)
- Hypotheekschuld als negatief vermogen
- Aflossingsvorm (lineair, annuïteit, aflossingsvrij)
- Renteaftrek box 1

**Impact**: Box 3 berekening, netto inkomen door hypotheekrenteaftrek

**Afhankelijkheden**: ✅ #114 voltooid - VermogensType enum en VermogensItem model beschikbaar

**Status**: 📝 PLANNED

---

#### #002: Overige bezittingen (auto, kunst, boot) 🔴 HIGH
**Beschrijving**: Generieke vermogenstypen met waardering

**Details**:
- Type: AUTO, KUNST, BOOT, OVERIG
- Aanschafwaarde en aanschafdatum
- Afschrijving (negatieve groei) of waardestijging
- Wel/niet box 3 belast
- Optioneel verkoopdatum met opbrengst

**Scenario's**:
- Auto: €30.000, -15% afschrijving per jaar, verkoop na 5 jaar voor restwaarde
- Kunst: €50.000, +3% waardestijging, niet verkopen
- Boot: €80.000, -10% afschrijving, box 3 vrijgesteld (recreatie)

**Status**: ✅ DONE (22 mei 2026)

**Implementatie**:
- VermogensItem model met VermogensType enum (SPAARGELD, BELEGGINGEN, EIGEN_WONING, AUTO, KUNST, BOOT, OVERIG)
- 18 tests voor VermogensItem model
- vermogen_engine uitgebreid met functies voor VermogensItems
- 9 tests voor vermogen_engine VermogensItems functionaliteit
- UI pagina voor vermogensitems beheer (pagina_vermogen.py)
- Geïntegreerd in app.py flow als stap 5 "Vermogen"
- Backwards compatible via migreer_legacy_vermogen()


---

#### #003: Box 3 herzien (2026+ stelsel) 🟡 MEDIUM
**Beschrijving**: Implementeer nieuwe box 3 wetgeving

**Details**:
- Werkelijk rendement i.p.v. forfaitair (indien van kracht)
- Verschillende box 3 vrijstellingen per vermogenstype
- Vermogensrendementsheffing met daadwerkelijke opbrengsten

**Status**: ⏳ WAITING (Afwachten definitieve wetgeving)

---

### High Priority - Inkomsten & Uitgaven

#### #004: Hypotheeklasten 🔴 HIGH
**Beschrijving**: Gedetailleerde hypotheekberekening

**Details**:
- Hypotheekbedrag, rentepercentage, looptijd
- Berekening maandlast (rente + aflossing)
- Renteaftrek in box 1
- Verschillende aflossingsvarianten
- Oversluitscenario's (vervroegd aflossen, oversluiten)

**Status**: 📝 PLANNED

---

#### #005: Alimentatie (betalen/ontvangen) 🟡 MEDIUM
**Beschrijving**: Alimentatieverplichtingen

**Details**:
- Partner- en kinderalimentatie
- Aftrekbaar voor betaler, belast voor ontvanger
- Indexatie conform CBS of afspraak
- Einddatum (bijv. kind 18 jaar)

**Status**: 📝 PLANNED

---

#### #006: Studiefinanciering 🟡 MEDIUM
**Beschrijving**: Studiekosten en -financiering

**Details**:
- Studietoeslag (belast inkomen)
- Collegegeld als uitgave
- Studieschuld met rente en aflossing

**Status**: 📝 PLANNED

---

#### #007: Kinderopvang & toeslagen 🟢 LOW
**Beschrijving**: Kinderopvangtoeslag en kinderkorting

**Details**:
- Kinderopvangtoeslag op basis van inkomen
- Kindgebonden budget
- Kinderkorting in belasting

**Status**: 📝 PLANNED

---

### Medium Priority - Belasting & Heffingen

#### #008: Zorgtoeslag 🟡 MEDIUM
**Beschrijving**: Automatische berekening zorgtoeslag

**Details**:
- Op basis van toetsingsinkomen en vermogen
- Jaarlijkse indexatie
- Partnertoeslag

**Status**: 📝 PLANNED

---

#### #009: Huurtoeslag 🟡 MEDIUM
**Beschrijving**: Huurtoeslag voor huurders

**Details**:
- Maximale huurprijs voor toeslag
- Inkomensgrenzen
- Vermogenstoets

**Status**: 📝 PLANNED

---

#### #010: IB-ondernemers 🟢 LOW
**Beschrijving**: Ondersteuning zelfstandigen

**Details**:
- Winst uit onderneming
- Zelfstandigenaftrek, startersaftrek
- MKB-winstvrijstelling
- Ondernemersaftrek (indien voortzetting)

**Status**: 📝 PLANNED

---

#### #011: DGA/directeur-grootaandeelhouder 🟢 LOW
**Beschrijving**: DGA-specifieke regelingen

**Details**:
- Gebruikelijk loon
- Stamrechtvrijstelling
- Lijfrentepremieaftrek

**Status**: 📝 PLANNED

---

### Medium Priority - Pensioen

#### #012: Partner- en nabestaandenpensioen 🟡 MEDIUM
**Beschrijving**: Alle pensioentypes uit MPO

**Details**:
- Partnerpensioen bij overlijden
- Wezenpensioen
- ANW-hiaatverzekering
- Voorwaardelijke indexatie

**Opmerking**: ⚠️ Parser ondersteunt dit al, maar UI en berekening niet

**Status**: 📝 PLANNED

---

#### #013: Lijfrente & annuïteit 🟡 MEDIUM
**Beschrijving**: Lijfrentepolissen en annuïteiten

**Details**:
- Inleg tijdens werkzame jaren (aftrekbaar)
- Uitkering vanaf pensioendatum (belast)
- Verschillende uitkeringsvormen

**Status**: 📝 PLANNED

---

#### #014: AOW franchise/toeslag 🟢 LOW
**Beschrijving**: AOW-varianten

**Details**:
- AOW-toeslag voor partner zonder AOW
- Vakantietoeslag
- AOW-franchise bij arbeid

**Status**: 📝 PLANNED

---

### Low Priority - Geavanceerde Features

#### #015: Inflatie per categorie 🟢 LOW
**Beschrijving**: Verschillende inflatiepercentages

**Details**:
- Energie-inflatie hoger dan voedsel
- Loon-indexatie anders dan prijsindex
- Zorg-inflatie afwijkend

**Status**: 💡 IDEA

---

#### #016: Monte Carlo simulatie 🟢 LOW
**Beschrijving**: Onzekerheidsbanden rond prognose

**Details**:
- Variabele rendementen (normaalverdeling)
- Levensverwachting onzeker
- Percentiel-banden (P10, P50, P90)

**Status**: 💡 IDEA

---

#### #017: Multi-valuta ondersteuning 🟢 LOW
**Beschrijving**: Pensioenen uit buitenland

**Details**:
- Wisselkoersen
- Belastingverdragen
- Buitenlandse box 3 vrijstellingen

**Status**: 💡 IDEA

---

#### #019: Werkelijke vermogensstand per datum 🔴 HIGH
**Beschrijving**: Vermogensitems updaten met werkelijke waarde op specifieke datum

**Details**:
- Mogelijkheid om per vermogensitem (spaarrekening, beleggingen, etc.) de werkelijke stand op een datum in te voeren
- Vanaf die datum wordt met dat nieuwe bedrag verder gerekend (overschrijft vorige berekende waarde)
- Rendement wordt vanaf die datum weer toegepast op de nieuwe werkelijke waarde
- Bij datum midden in een jaar: rendement pro-rata berekenen (bijv. bij invoer op 1 juli = 50% van jaarrendement)
- Meerdere datumpunten mogelijk voor dezelfde bezitting (historie van correcties)
- Gebruik: jaarlijkse correctie met bankafschrift, beleggingswaarde op peildatum

**Scenario's**:
- Spaarrekening: start €10.000, na 1 jaar werkelijke stand €10.500 (i.p.v. berekende €10.300), verder rekenen met €10.500
- Beleggingen: jaarlijkse correctie met werkelijke waarde van broker statement
- Eigen woning: WOZ-waarde bijwerken per 1 januari elk jaar

**Impact**: Nauwkeurigere vermogensprognose, elimineren van cumulatieve rekenfouten

**Status**: 📝 PLANNED

---

#### #020: Spaarrekening als vaste bezitting 🔴 HIGH
**Beschrijving**: Spaarrekening kan niet worden verwijderd, ontvangt automatisch overschot

**Details**:
- Systeem vereist minimaal 1 spaarrekening/spaargeld bezitting
- Jaarlijks netto overschot wordt automatisch toegevoegd aan de (eerste) spaarrekening
- Bij tekort wordt automatisch van de spaarrekening afgehaald
- Gebruiker kan niet de spaarrekening verwijderen indien het de enige is
- Indien meerdere spaarrekeningen: duidelijk aangeven welke de "primaire" is voor overschot
- Volgorde: eerst primaire spaarrekening, dan secundaire, dan beleggingen bij uitzonderlijk hoge overschotten

**Logica**:
- Einde maand: netto cashflow berekend
- Positief → toevoegen aan primaire spaarrekening
- Negatief → afhalen van primaire spaarrekening (kan negatief worden = schuld)
- Rendering van primaire spaarrekening anders: badge "Hoofdrekening" of vergelijkbaar

**Impact**: Realistischer vermogensverloop, consistent met praktijk

**Status**: 📝 PLANNED

---

#### #018: Successieplanning 🟢 LOW
**Beschrijving**: Erfenis en schenking

**Details**:
- Erfbelasting
- Schenkingsvrijstelling
- Tijdelijke verhogingen

**Status**: 💡 IDEA

---

## 🔧 VERBETERINGEN & TECHNISCHE SCHULD

### UI/UX Verbeteringen

#### #101: Component bulk acties 🟡 MEDIUM
**Beschrijving**: Meerdere componenten tegelijk bewerken/verwijderen

**Details**:
- Checkboxes voor selectie
- Bulk delete knop
- Bulk edit (bijv. alle bedragen +3% inflatie)

**Status**: 📝 PLANNED

---

#### #102: Component templates 🟡 MEDIUM
**Beschrijving**: Herbruikbare sjablonen

**Details**:
- "Standaard huishouden" template
- "Minimale basisuitgaven" template
- "Luxe pensioen" template
- Eigen templates opslaan

**Status**: 📝 PLANNED

---

#### #103: Drag & drop componenten 🟢 LOW
**Beschrijving**: Componenten slepen om volgorde te wijzigen

**Details**:
- Visuele ordening
- Categorieën groeperen
- Automatisch sorteren op datum/bedrag

**Status**: 💡 IDEA

---

#### #104: Grafiek interacties 🟢 LOW
**Beschrijving**: Klikbare grafieken

**Details**:
- Klik op jaar → detail tabel
- Klik op lijn → component details
- Zoom in/out op tijdslijn

**Status**: 💡 IDEA

---

#### #105: Dark mode 🟢 LOW
**Beschrijving**: Donkere UI optie

**Status**: 💡 IDEA

---

### Data & Validatie

#### #106: Geavanceerde validatie 🟡 MEDIUM
**Beschrijving**: Uitgebreidere controles

**Details**:
- Waarschuwing bij tekortjaren
- Waarschuwing bij extreem hoge box 3 heffing
- Suggesties voor optimalisatie
- Sanity checks (bijv. AOW > €40.000 = fout)

**Status**: 📝 PLANNED

---

#### #107: Import uitbreiden 🟡 MEDIUM
**Beschrijving**: Meer importformaten

**Details**:
- MPO PDF (nu alleen CSV/JSON/Excel)
- ING/Rabobank bankafschriften
- Belastingaangifte XML

**Status**: 📝 PLANNED

---

#### #108: Export uitbreiden 🟡 MEDIUM
**Beschrijving**: Meer exportformaten

**Details**:
- PDF rapport met grafieken
- CSV voor verdere analyse
- JSON voor API-integratie

**Status**: 📝 PLANNED

---

### Performance & Schaalbaarheid

#### #109: Caching berekeningen 🟡 MEDIUM
**Beschrijving**: Cache tussenresultaten

**Details**:
- Belastingtarieven cachen
- AOW-datums cachen
- Scenario-berekeningen cachen (invalideren bij wijziging)

**Impact**: 50-70% sneller bij herhaalde berekeningen

**Status**: 📝 PLANNED

---

#### #110: Async berekeningen 🟢 LOW
**Beschrijving**: Lange berekeningen in background

**Details**:
- Progress bar
- Annuleren mogelijk
- Multi-threading voor scenario-vergelijkingen

**Status**: 💡 IDEA

---

#### #111: Database backend 🟢 LOW
**Beschrijving**: Vervang JSON-files door database

**Details**:
- SQLite voor lokale installatie
- PostgreSQL voor server-deployment
- Versiebeheer van scenario's
- Audit trail (wie, wanneer, wat gewijzigd)

**Impact**: 🔴 BREAKING CHANGE

**Status**: 💡 IDEA (tenzij multi-user vereist)

---

### Code Kwaliteit

#### #112: Type coverage verhogen 🟡 MEDIUM
**Beschrijving**: Volledige type hints overal

**Huidige status**: ~90% coverage

**Doel**: 100% met mypy strict mode

**Status**: 📝 PLANNED

---

#### #113: Test coverage verhogen 🟡 MEDIUM
**Beschrijving**: Meer unit tests

**Huidige status (26 juli 2026)**: 52% line coverage, 295 verzamelde tests;
293 tests slagen en 2 bekende externe afwijkingen zijn strikt als `xfail`
geregistreerd

**Doel**: 80%+ line coverage, 200+ tests

**Focus**:
- UI code (nu 0% coverage)
- Edge cases (negatief vermogen, extreem hoge inkomens)
- Integratietests (end-to-end scenarios)

**Status**: 📝 PLANNED

---

#### #114: Refactor vermogen_engine 🔴 HIGH
**Beschrijving**: Scheiden van sparen/beleggen/overige bezittingen

**Details**:
- VermogensType enum (SPAARGELD, BELEGGINGEN, EIGEN_WONING, ...)
- Per type aparte berekening
- Generieke interface voor alle types

**Impact**: 🔴 BREAKING CHANGE (interne API)

**Blokkerende voor**: #001, #002

**Status**: ✅ DONE (22 mei 2026)

**Implementatie**:
- VermogensItem Pydantic model met volledige validatie
- VermogensType enum: SPAARGELD, BELEGGINGEN, EIGEN_WONING, AUTO, KUNST, BOOT, OVERIG
- scenario.py uitgebreid met vermogensitems lijst
- vermogen_engine nieuwe functies: bereken_vermogen_totaal(), bereken_vermogen_box3_belast(), bereken_vermogen_per_type(), update_vermogensitems_waarde()
- Oude functies behouden voor backwards compatibility
- 27 tests (18 voor VermogensItem, 9 voor vermogen_engine)
- Alle 142 bestaande tests blijven slagen


---

#### #115: Logging & monitoring 🟡 MEDIUM
**Beschrijving**: Gestructureerde logs

**Details**:
- Berekeningen loggen voor debugging
- Performance metrics
- Error tracking (Sentry-integratie)

**Status**: 📝 PLANNED

---

## 🐛 BEKENDE ISSUES

#### #201: Box 3 disclaimer altijd tonen 🟢 LOW
**Beschrijving**: Disclaimer is te algemeen, niet specifiek per situatie

**Fix**: Conditionele disclaimers op basis van vermogensniveau

**Status**: 📝 PLANNED

---

#### #202: MPO parser ondersteunt geen PDF 🟡 MEDIUM
**Beschrijving**: PDF-parsing is stubbed maar niet geïmplementeerd

**Workaround**: Gebruik CSV of JSON export

**Fix**: pdfplumber integreren voor tabelextractie

**Status**: 📝 PLANNED

---

#### #203: Geen validatie op overlappende componenten 🟡 MEDIUM
**Beschrijving**: Twee identieke pensioenen kunnen worden toegevoegd

**Impact**: Dubbeltelling in berekening

**Fix**: Deduplicatie check bij import en toevoegen

**Status**: 📝 PLANNED

---

#### #204: AOW-breuk bij deel-jaar niet getest 🟢 LOW
**Beschrijving**: Edge case: AOW start 17 september, geen test

**Status**: Code aanwezig, test ontbreekt

**Fix**: Toevoegen test voor AOW mid-year start

**Status**: 📝 PLANNED

---

#### #205: Dubbeltelling eigen woning in accountantsoverzicht 🔴 HIGH
**Beschrijving**: Eigen woninggegevens (WOZ en hypotheek) worden op huishoudniveau ingevoerd,
maar in het accountantsoverzicht bij zowel P1 als partner meegerekend.

**Impact**: Dubbeltelling in box 1/eigen-woningcomponenten en onjuiste netto-uitkomst in detailoverzicht.

**Fix**: Splits eigen woninginvoer exact 50/50 tussen partners (of volgens expliciete toewijzingsregel)
en valideer dat de huishoudsom gelijk blijft aan de broninvoer.

**Status**: 📝 PLANNED

---

#### #206: Dubbeltelling AOW in accountantsoverzicht 🔴 HIGH
**Beschrijving**: AOW wordt in de accountantspagina toegevoegd via de automatische AOW-berekening,
terwijl AOW ook als financieel component kan zijn ingevoerd.

**Impact**: Dubbeltelling van AOW in bruto inkomen en daardoor onjuiste belasting- en netto-uitkomst.

**Fix**: Introduceer één bronregel voor AOW in accountantsoverzicht (of automatische AOW, of component-AOW)
met expliciete validatie/waarschuwing als beide tegelijk aanwezig zijn.

**Status**: 📝 PLANNED

---

#### #207: Accountantspagina toont verouderde/verkeerde vermogensversie 🔴 HIGH
**Beschrijving**: In de accountantspagina wordt nog een oude of inconsistente versie van vermogen getoond,
die niet overeenkomt met de actuele vermogensitems/rekensituatie.

**Impact**: Onjuiste controle-informatie voor accountant en mogelijke verkeerde conclusies over vermogen en cashflow.

**Fix**: Laat accountantspagina uitsluitend renderen vanuit dezelfde actuele vermogensbron als de rekenengine
(single source of truth) en voeg regressietest toe op weergaveconsistentie.

**Status**: 📝 PLANNED

---

#### #208: Accountantspagina pakt niet altijd juiste box 3 forfaitversie 🔴 HIGH
**Beschrijving**: In de accountantspagina wordt bij box 3 niet altijd gerekend met het actuele forfait voor
sparen en beleggen, ondanks bijgewerkte config/instellingen.

**Impact**: Verkeerde box 3 heffing in detailoverzicht en afwijking tussen verwachting en accountantspagina.

**Waarschijnlijke oorzaak**: Jaar-fallback in tariefloader (ontbrekend jaar gebruikt laatste beschikbare jaar)
of mismatch tussen actieve scenario-instellingen (tariefperiodes) en getoonde scenario-context.

**Fix**: Toon expliciet bron voor box3_forfait_spaargeld en box3_forfait_overig per jaar in accountantsoverzicht,
blokkeer stille fallback voor accountantmodus of markeer hard warning, en voeg regressietest toe.

**Status**: 📝 PLANNED

---

#### #209: Instellingenwijzigingen worden niet automatisch naar belasting_JSON opgeslagen 🔴 HIGH
**Beschrijving**: Wijzigingen in jaarinstellingen/tarieven worden in de UI gegenereerd als download,
maar niet direct teruggeschreven naar `config/belasting_YYYY.json`.

**Impact**: Gebruiker verwacht opgeslagen wijzigingen, maar app blijft rekenen met oude of fallback-config
totdat bestand handmatig is geplaatst en app is herstart.

**Waarschijnlijke oorzaak**: Instellingenpagina gebruikt `st.download_button` voor JSON-export en bevat
geen schrijfpad naar de config-map.

**Fix**: Voeg expliciete "Opslaan naar config"-actie toe (met padvalidatie, backup en bevestiging),
en toon na opslaan een melding dat herstart nodig is.

**Status**: 📝 PLANNED

---

## 📚 DOCUMENTATIE

#### #301: API documentatie 🟡 MEDIUM
**Beschrijving**: Volledige API docs voor developers

**Details**:
- Sphinx of MkDocs
- Alle functies gedocumenteerd
- Voorbeelden per module

**Status**: 📝 PLANNED

---

#### #302: Gebruikershandleiding 🟡 MEDIUM
**Beschrijving**: End-user documentatie

**Details**:
- Stapsgewijze tutorials
- Screenshots
- FAQ sectie
- Video's (optioneel)

**Status**: 📝 PLANNED

---

#### #303: Architectuur documentatie 🟢 LOW
**Beschrijving**: Technische architectuur

**Details**:
- C4 diagrammen (Context, Containers, Components)
- Data flow diagrammen
- Decision records (ADRs)

**Status**: 💡 IDEA

---

## 🎯 ROADMAP

### Historische roadmap (opgesteld vóór 26 juli 2026)

Onderstaande kwartaalindeling is planningshistorie. De actuele prioriteit is
Epic 6, gevolgd door Epic 7.

### Q2 2026 (afgelopen)
- ✅ Sparen & beleggen split implementatie (DONE)
- ✅ Tests voor sparen/beleggen functionaliteit (DONE)
- #114: Refactor vermogen_engine voor meerdere types
- #001: Eigen woning implementatie
- #002: Overige bezittingen (auto, kunst)

### Q3 2026 (juli - september 2026)
- #401: Epic 1 API-laag + simpele API-UI (gestart)
- #004: Hypotheeklasten
- #106: Geavanceerde validatie
- #107: Import uitbreiden (PDF)
- #113: Test coverage naar 60%+

### Q4 2026 (oktober - december 2026)
- #012: Partner- en nabestaandenpensioen
- #101: Component bulk acties
- #102: Component templates
- #109: Caching berekeningen

### 2027
- #003: Box 3 herzien (afhankelijk van wetgeving)
- #005-#011: Overige inkomsten/uitgaven types
- #111: Database backend (bij multi-user behoefte)
- #302: Gebruikershandleiding

---

## 💡 IDEEËN VOOR LATER

- **Mobiele app**: React Native wrapper voor on-the-go planning
- **API voor adviseurs**: REST API voor financieel adviseurs
- **AI assistent**: ChatGPT-achtige interface "Wat als ik met 62 stop?"
- **Collaborative planning**: Meerdere gebruikers aan één scenario
- **Benchmark rapporten**: Vergelijk met gemiddelden in leeftijdscategorie
- **Notificaties**: "Je vermogen is onder €50.000 gedaald in scenario X"

---

## 📝 BIJDRAGEN

Voor het oppakken van items uit deze backlog:
1. Claim een issue door een comment te plaatsen
2. Maak een feature branch: `feature/#XXX-korte-beschrijving`
3. Implementeer met tests (vereist voor #001-#018)
4. Update BACKLOG.md met status
5. Pull request met referentie naar #XXX

---

## 🏷️ LEGENDA

**Prioriteiten:**
- 🔴 HIGH: Binnen 3 maanden
- 🟡 MEDIUM: Binnen 6 maanden
- 🟢 LOW: Nice to have

**Status indicatoren:**
- ✅ DONE: Geïmplementeerd en getest
- 🚧 IN PROGRESS: Wordt momenteel aan gewerkt
- 📝 PLANNED: Gepland voor implementatie
- ⏳ WAITING: Wacht op externe afhankelijkheid
- ⚠️ BLOCKED: Geblokkeerd door andere issue
- 💡 IDEA: Nog niet gepland, alleen concept

---

*Laatste statuscontrole: 26 juli 2026*
*Versie: 1.3 - actuele herstructureringsbron en Epic 6-nulmeting toegevoegd*
