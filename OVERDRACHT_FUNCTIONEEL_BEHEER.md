---
post_title: "Functioneel Overdrachtsdocument Pensioenplanner"
author1: "Senior Functioneel Beheer"
post_slug: "overdracht-pensioenplanner"
microsoft_alias: "n/a"
featured_image: "n/a"
categories:
  - "Other"
tags:
  - "pensioen"
  - "functioneel beheer"
  - "overdracht"
ai_note: "Document opgesteld met AI-ondersteuning en handmatige validatie op codebasis."
summary: "Uitgebreid overdrachtsdocument voor de Pensioenplanner met processen, berekenlogica, operationeel beheer, issues en roadmap."
post_date: "2026-06-27"
---

## Doel En Reikwijdte

Dit document is de volledige functionele overdracht van de Pensioenplanner aan
een opvolgend functioneel beheerder. Deze overdracht is gebaseerd op
[README.md](README.md), [BACKLOG.md](BACKLOG.md), [app.py](app.py),
[src/pensioen/calculations/cashflow_engine.py](src/pensioen/calculations/cashflow_engine.py),
[src/pensioen/tax/belasting_engine.py](src/pensioen/tax/belasting_engine.py),
[src/pensioen/tax/eigen_woning_engine.py](src/pensioen/tax/eigen_woning_engine.py),
[src/pensioen/models/scenario.py](src/pensioen/models/scenario.py),
[src/pensioen/models/vermogensitem.py](src/pensioen/models/vermogensitem.py),
[src/pensioen/parsers/parser_mpo.py](src/pensioen/parsers/parser_mpo.py),
[src/pensioen/reports/rapport_engine.py](src/pensioen/reports/rapport_engine.py) en
[src/pensioen/ui/pagina_accountant.py](src/pensioen/ui/pagina_accountant.py).

Het document beschrijft:

- de businessprocessen en gebruikersflow.
- de volledige functionele scope.
- de gedetailleerde berekeningen en fiscale aannames.
- operationeel beheer en controles.
- bekende issues, openstaande wensen en backlog-prioriteiten.
- risico's, beheeraanpak en aanbevelingen voor overdracht.

## Productcontext In Gewone Taal

De applicatie is een Nederlandse pensioenplanner met maand- en jaarprognoses
voor huishoudens. De kernvraag die de app beantwoordt is:

- hoeveel netto besteedbaar inkomen is er per maand/jaar.
- hoe ontwikkelt het vermogen zich door tijd.
- waar ontstaan tekorten.
- hoe verschillen alternatieve scenario's.

Het domein is expliciet Nederlands belastinggedreven:

- box 1 met schijven en heffingskortingen.
- box 3 met forfaitair rendement en vrijstelling.
- AOW-leeftijd op basis van geboortedatum.
- eigen woning/hypotheek als box 1-domein (niet in box 3 vermogenstotaal).

## Architectuur En Moduleverantwoordelijkheid

De oplossing volgt een duidelijke lagenstructuur:

- UI-laag: Streamlit schermen en flow in
  [app.py](app.py) en de modules onder
  [src/pensioen/ui](src/pensioen/ui).
- Domeinmodellen: Pydantic datamodellen onder
  [src/pensioen/models](src/pensioen/models).
- Rekenengines: businessregels onder
  [src/pensioen/calculations](src/pensioen/calculations).
- Fiscaliteit: belasting, AOW en eigen woning onder
  [src/pensioen/tax](src/pensioen/tax).
- Import/export: MPO parsing en rapportages onder
  [src/pensioen/parsers](src/pensioen/parsers) en
  [src/pensioen/reports](src/pensioen/reports).

Belangrijk functioneel principe:

- alle geldwaarden zijn Decimal-gebaseerd.
- maandberekening is leidend; jaarwaarden zijn aggregaties.
- scenario is de centrale businessentiteit.

## Hoofdprocessen Voor De Business

## Proces 1 Intake En Basisinstellingen

Doel:

- vastleggen van personen, geboortedata en planninghorizon.

Actoren:

- eindgebruiker (adviseur/huishouden), functioneel beheer voor support.

Invoer:

- persoonsgegevens P1 en optioneel P2.
- jaar_van en jaar_tot.

Uitvoer:

- valide uitgangspositie voor berekening.

Functionele notities:

- zonder P1 geen berekening.
- partnerstatus beïnvloedt AOW-bedragen en box 3-vrijstelling.

## Proces 2 Scenario-opbouw

Doel:

- opbouwen van een of meer scenario's met inkomsten, uitgaven,
  inhoudingen, vermogensitems en incidentele posten.

Invoerblokken:

- componenten:
  - arbeidsinkomen.
  - pensioen_inkomen.
  - overig_inkomen.
  - uitgave.
  - inhouding.
- incidentele items (eenmalig met datum).
- vermogensitems (spaargeld, beleggingen, woning, hypotheek, overig).

Belangrijk:

- scenario's ondersteunen parent-child inheritance.
- child scenario's kunnen alleen overrides opslaan.

## Proces 3 Pensioenimport (MPO)

Doel:

- pensioeninformatie sneller inlezen in plaats van handmatige invoer.

Ondersteunde bronnen:

- CSV.
- Excel.
- JSON (Pensioenregister-structuur).
- PDF: best-effort, niet volledig betrouwbaar.

Functionele verwerking:

- mapping naar PensioenRecord.
- omzetting naar FinancieelComponenten mogelijk.
- validatie nodig op dubbels en kwaliteit.

## Proces 4 Berekening Hoofdscenario

Doel:

- genereren van maandresultaten en jaarresultaten voor 1 scenario.

Stapvolgorde op hoofdlijnen:

1. bruto componenten per maand bepalen.
2. jaargrondslagen per persoon opbouwen.
3. box 1 + premies + heffingskortingen berekenen.
4. box 3 heffing op peildatumlogica verwerken.
5. rente/rendement maandelijks toepassen.
6. netto cashflow en nieuw saldo per maand bepalen.
7. jaaraggregaties en signalering tekortjaren maken.

## Proces 5 Scenariovergelijking

Doel:

- vergelijken van alternatieve scenario's op uniforme KPI's.

Belangrijkste KPI's:

- mediaan netto per maand.
- laagste inkomensjaar.
- vermogen op 70 en 80 jaar.
- gemiddelde belastingdruk.
- aantal tekortjaren.

## Proces 6 Rapportage En Accountantsoverzicht

Doel:

- transparante verantwoording van resultaten richting gebruiker,
  adviseur en accountant.

Resultaatkanalen:

- Streamlit resultatenpagina.
- Accountantspagina met detailcomponenten.
- Excel export (jaaroverzicht, maanddetail, aannames, vergelijking).

## Functionele Scope (Wat Werkt Nu)

Conform code en backlog is de huidige werkende kern:

- bruto/netto componenten met frequenties en groeipercentages.
- AOW maandpro-rata op exacte ingangsdatum.
- pensioenmaandbedragen met pro-rata begin/eind en indexatie.
- box 1 met schijven, heffingskortingen en premiesplitsing.
- box 3 forfaitair op basis van vrijstelling en spaargeld/beleggingen mix.
- scenariovergelijking met samenvattings-KPI's.
- sessiepersistentie en scenarioselectie in de UI.
- eigen woning en hypotheek als fiscale invoer voor box 1.
- vermogensitems als generiek model (sparen, beleggen, overige bezittingen).

## Gedetailleerde Rekenlogica

## 1 Componentbedragen Naar Maandwaarden

Rekenregel:

- een component heeft frequentie (maand/kwartaal/halfjaar/jaar/eenmalig).
- bedrag_per_maand_actief spreidt periodieke bedragen lineair over maanden.
- groeipercentage wordt per kalenderjaar samengesteld toegepast.

Voorbeelden:

- jaarlijks bedrag 12.000 geeft 1.000 per maand.
- kwartaalbedrag 900 geeft 300 per maand equivalent.
- eenmalig bedrag telt volledig in de startmaand.

## 2 AOW Berekening

Logica:

- AOW-ingangsdatum komt uit AOW-engine op basis van geboortedatum.
- maand vóór ingangsdatum: 0.
- ingangsmaand: pro-rata op resterende dagen.
- maand na ingang: volledig maandbedrag.

Partnerinvloed:

- alleenstaand versus gehuwd/samenwonend maandbedrag uit belastingconfig.

## 3 Pensioen Berekening

Logica:

- pensioenrecord wordt per maand berekend.
- eerste maand pro-rata bij start binnen de maand.
- laatste maand pro-rata bij einddatum binnen de maand.
- indexatie wordt jaarlijks samengesteld toegepast vanaf ingangsjaar.

Uitzondering:

- partner- en nabestaandenpensioen tellen niet als regulier maandinkomen in
  deze standaardstroom.

## 4 Box 1 Belasting En Premies

Box 1 berekening bevat:

- inkomstenbelasting op schijven met AOW-breukweging.
- premies AOW/Anw/Wlz op premiegrondslag tot premiegrens.
- heffingskortingen: algemene, arbeidskorting, ouderenkorting,
  alleenstaandeouderenkorting.

Belangrijke functionele nuances:

- AOW-breuk kan deeljaar zijn, dus gewogen tarief.
- netto verschuldigd wordt niet negatief (ondergrens 0).
- resultaat houdt zowel legacy totaalbelasting als uitsplitsing premies bij.

## 5 Eigen Woning In Box 1

De module voor eigen woning rekent:

- eigenwoningforfait op basis van WOZ.
- aftrekbare hypotheekrente en overige aftrekbare kosten.
- saldo eigen woning (bijtelling of aftrekpost).
- Wet Hillen-correctie bij positief saldo.
- tariefsaanpassing aftrekbeperking bij hoge inkomens.

Expliet uitgangspunt:

- eigen woning en eigenwoningschuld blijven buiten box 3.

## 6 Box 3 Heffing

Functioneel model:

- belastbaar vermogen = max(0, saldo - vrijstelling).
- vrijstelling = per persoon, verdubbeld bij partner.
- fictief rendement = belastbaar vermogen x gewogen forfait.
- gewogen forfait combineert sparen en overig/beleggen.
- heffing = fictief rendement x box3 tarief.

De app toont disclaimertekst omdat wetgeving in beweging is.

## 7 Vermogensgroei

Maandrendement wordt afgeleid uit jaarrendement met:

- maand = (1 + jaar)^(1/12) - 1.

Bij apart sparen/beleggen rendement:

- saldo wordt gesplitst op basis van spaargeld_fractie.
- deelrendementen worden apart berekend en opgeteld.

## 8 Maandcashflow Integratie

Netto maandcashflow integreert:

- bruto en netto inkomenscomponenten.
- AOW + pensioencomponenten.
- belasting en heffingskortingen.
- box 3 maanddeel.
- uitgaven, inhoudingen, incidentele posten.
- rendement/rente.
- jaarlijkse inleg (omgeslagen per maand).

Eindsaldo maand:

- saldo nieuw = max(0, saldo oud + netto cashflow).

Dus negatief vermogen wordt in deze stroom afgekapt op 0.

## Datamodel En Belangrijke Entiteiten

## Scenario

Scenario bevat:

- metadata (naam, default, timestamps).
- inheritancevelden (parent_naam, overrides).
- componenten en incidentele items.
- legacy en nieuwe vermogensstructuur.
- box3-instellingen en tariefperiodes.
- eigen-woning fiscale velden.

Belangrijke beheerimplicatie:

- de code ondersteunt tegelijk legacy velden en nieuwe vermogensitems.
- bij laden van oude sessies vindt migratie naar vermogensitems plaats.

## FinancieelComponent

Kernvelden:

- categorie, persoon, bedrag, bedrag_type.
- frequentie, begin/einddatum, groei_pct.
- optioneel waarde_periodes voor periode-overrides.

## VermogensItem

Kernvelden:

- type, aanschafwaarde, groei_pct, box3_belast.
- aanschaf/verkoopdatum en verkoopprijs.
- type-specifieke velden voor woning en hypotheek.

Belangrijk:

- hypotheek wordt behandeld als fiscale invoer en niet als negatieve
  vermogenspost in totaaloverzichten.

## Inheritance (Parent-Child Scenario's)

Functioneel gedrag:

- base scenario heeft geen parent.
- child scenario verwijst naar parent_naam.
- only-changes model via overrides.
- resolutie merge't root -> child.

Validaties:

- self-parenting detectie.
- orphan parent detectie.
- cycle detectie in parent chain.

Beheeradvies:

- na scenario-mutaties altijd inheritance validatie uitvoeren.
- wees voorzichtig met hernoemen van parent scenario's.

## UI En Gebruikersreis

In de sidebar wordt een stappengestuurde flow gebruikt:

- personen.
- pensioenimport.
- componenten.
- resultaten.
- accountant.
- rapport.

Kenmerken:

- actief scenario kan live gewisseld worden.
- herberekening gebeurt bij expliciete berekenactie en in sommige gevallen
  bij scenariowissel.
- autosave draait na render.

Risico in beheer:

- stille fallback bij fouten tijdens herberekenen op scenariowissel wist
  eerder resultaat in sessiecontext.

## Rapportage

Excel export bevat minimaal:

- Jaaroverzicht.
- Maanddetail.
- Aannames.
- Vergelijking (indien meerdere scenario's).

Sterk punt:

- expliciete opname van tariefjaaraannames en waarschuwingen in rapporttab.

## Openstaande Issues En Wensen

Onderstaand is functioneel relevant samengevat uit backlog en code-notities.

## High Priority (Kern)

- #001 Eigen woning verder uitwerken in totale productflow.
- #004 Gedetailleerde hypotheeklasten en aflossingsvormen.
- #019 Werkelijke vermogensstand per datum (correctiemechanisme).
- #020 Vaste primaire spaarrekening voor overschot/tekort routing.

## Medium Priority (Belasting/Datakwaliteit)

- #008 Zorgtoeslag.
- #009 Huurtoeslag.
- #012 Partner- en nabestaandenpensioen volledig in berekening/UI.
- #106 Geavanceerde validatie en signalering.
- #107 Import uitbreiden (waaronder robuuste PDF).
- #108 Extra exportformaten (PDF/CSV/JSON).

## Technische Schuld / Kwaliteit

- #113 Testcoverage verhogen (backlog vermeldt hoger doel).
- #115 Logging en monitoring structureren.
- Bekende TODO in box 3 validatie-adapter:
  [validatie/belasting_vergelijking/pensioen_adapter.py](validatie/belasting_vergelijking/pensioen_adapter.py)
  over dividend-aftrek in box 3 vergelijking.

## Bekende Functionele Aandachtspunten

- MPO PDF parsing is best-effort; uitkomsten handmatig verifiëren.
- overlap/dubbeltelling componenten vraagt extra validatie.
- box 3 disclaimer is nu generiek en niet contextspecifiek.
- er is spanning tussen gecommuniceerde teststatus in backlog en actuele
  testdefinitietelling; beheerder moet periodiek feitelijke metrics vastleggen.

## Operationeel Beheer (Dagelijks/Wekelijks/Maandelijks)

## Dagelijks

- check of berekeningen zonder fout lopen voor representatieve scenario's.
- check of sessiepersistentie nog correct werkt.
- monitor gebruikersmeldingen op onverwachte netto-uitkomsten.

## Wekelijks

- draai regressietests op kernengines en fiscaliteit.
- controleer wijzigingen in belastingconfig en aannameteksten.
- valideer scenario inheritance bij scenario-mutaties in testdata.

## Maandelijks

- actualiseer backlogstatus op basis van realisatie.
- controleer taxconfig-bestanden voor nieuwe jaren.
- review van open issues op impact voor jaarovergang.

## Jaarovergang (Kritisch)

- voeg nieuw belastingjaarbestand toe in config.
- controleer AOW- en box3-parameters.
- valideer fallback-gedrag wanneer jaarconfig ontbreekt.
- voer accountantscenario's uit als acceptance check.

## Incidentmanagement En Escalatie

Typische incidenttypen:

- belastinguitkomst wijkt sterk af van verwachting.
- saldo springt onverwacht door component-invoer.
- importformaten falen op bronbestanden.
- scenariowissel geeft lege resultaten.

Aanpak:

1. reproduceer met klein scenario.
2. controleer componentcategorie, bedrag_type en datumbereik.
3. controleer box 1/box 3 aannames in rapport en accountantsoverzicht.
4. vergelijk met validatiemodules onder
   [validatie](validatie).
5. documenteer root cause en voeg regressietest toe.

## Beheerrisico's En Mitigaties

Belangrijkste risico's:

- fiscale wetgeving wijzigt sneller dan releasecadans.
- mixed legacy/nieuwe vermogensstructuur kan verwarring geven.
- functionele verwachtingen rond hypotheek als schuld versus fiscale invoer.
- afhankelijkheid van correcte peildata en datumlogica.

Mitigaties:

- expliciete versiebeheerprocedure voor belastingconfig per jaar.
- regressietests voor datumranden (AOW start, pro-rata maanden).
- duidelijke gebruikersuitleg in UI over fiscale versus vermogensweergave.
- periodieke dataset-validatie met externe benchmarkcases.

## Kennisoverdracht Aan Opvolger

Startvolgorde voor een nieuwe beheerder:

1. lees [README.md](README.md) voor operationele start.
2. lees [BACKLOG.md](BACKLOG.md) voor scope en prioriteiten.
3. doorloop de flow in de app met 1 eenvoudig en 1 complex scenario.
4. valideer accountantsoverzicht en Excel-export met bekende testcase.
5. bestudeer de engines in deze volgorde:
   - [src/pensioen/calculations/cashflow_engine.py](src/pensioen/calculations/cashflow_engine.py)
   - [src/pensioen/tax/belasting_engine.py](src/pensioen/tax/belasting_engine.py)
   - [src/pensioen/tax/eigen_woning_engine.py](src/pensioen/tax/eigen_woning_engine.py)
   - [src/pensioen/models/scenario.py](src/pensioen/models/scenario.py)

## Beslisregels Voor Functioneel Beheer

Gebruik deze eenvoudige beslisregels:

- als afwijking alleen in visualisatie zit: behandel als UI defect.
- als afwijking in maand/jaar sommen zit: start in cashflow_engine.
- als afwijking persoonsafhankelijk is: controleer box 1, AOW-breuk,
  heffingskortingen.
- als afwijking vermogensgerelateerd is: controleer box 3 grondslag,
  spaargeldfractie en uitsluiting eigen woning/hypotheek.
- als afwijking alleen in child scenario zit: controleer inheritance overrides.

## Overdrachtsacceptatiecriteria

De overdracht is functioneel compleet als opvolger zelfstandig:

- een nieuw scenario kan opzetten en laten doorrekenen.
- het verschil tussen box 1, box 3 en netto cashflow kan uitleggen.
- een afwijkende uitkomst kan terugleiden tot component, tarief of datum.
- openstaande backlogitems op impact kan prioriteren.
- jaarovergang met nieuw belastingjaar veilig kan begeleiden.

## Slotopmerking

Deze applicatie is inhoudelijk sterk in transparante, maandnauwkeurige
cashflowberekeningen binnen het Nederlandse pensioendomein. De belangrijkste
beheeropgave is niet alleen technische continuiteit, maar vooral discipline in
fiscale actualisatie, regressietesten en heldere gebruikersverwachtingen.
