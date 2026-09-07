# Review pensioenplanner — 5 september 2026

Update vervolgwerk: de twee hieronder oorspronkelijk gevonden P0-vermogensbugs
zijn opgelost: negatieve rendementen en de ongewogen frontendmiddeling.
Zie [het vermogenscontract](VERMOGEN_REKENCONTRACT.md) voor werking, tests en
beperkingen. De oorspronkelijke bevindingen hieronder blijven als historie staan.

De grootste klantwaarde zit in een betrouwbaar antwoord op: **kan ik op mijn
gewenste moment stoppen met werken, wat houd ik over en hoe lang kan mijn
vermogen dat dragen?** De technische basis is bruikbaar, maar er zijn nog
reken-, betekenis- en opslagproblemen die vóór zelfstandig klantgebruik
moeten worden opgelost.

## Reikwijdte en bewijs

Brede repositoryreview van modellen, berekenketen, fiscaliteit, API,
import/export, React, Streamlit, sessieopslag, tests, CI en projectdocumentatie.
Architectuur en relevante codepaden zijn inhoudelijk onderzocht; 56 Python-
bronbestanden zijn tevens syntactisch gecontroleerd. Dit is geen volledige
regel-voor-regel audit of onafhankelijke fiscale certificering. Primaire
belastingbronnen zijn bij deze code-review niet opnieuw gevalideerd.

De bestaande centrale `resultaat_service` en engine-detailoutput zijn een
sterk uitgangspunt. Het historische masterplan beschrijft ook problemen die
inmiddels zijn opgelost; de actuele code en het legacyregister zijn daarom
naast de documentatie beoordeeld.

## Prioriteiten

P0: oplossen vóór zelfstandig gebruik voor financiële keuzes of vóór de
genoemde deploymentvorm. P1: eerstvolgende productiteratie. P2: daarna.

| Prio | Bevinding en klantimpact | Concrete eerstvolgende actie en acceptatie |
| --- | --- | --- |
| **P0** | **Negatieve beleggingsrendementen verdwijnen.** `bereken_rente_maand` verwerkt in het gesplitste pad alleen rendementen groter dan nul. Reproductie: € 100.000 beleggen, −10%, spaarfractie 0 geeft **€ 0** maandrendement. Een slechtweerscenario wordt daardoor te gunstig. [Bron](../src/pensioen/calculations/vermogen_engine.py), aangeroepen door [cashflow_engine](../src/pensioen/calculations/cashflow_engine.py). | Slice **Vermogen**: ondersteun verliezen binnen een expliciet rendementsdomein, met directe negatieve-rendementtest, regressie via de hoofdengine en bijgewerkte raw/normalized fixtures. Source of truth: vermogen-engine. |
| **P0** | **React middelt rendementen ongewogen.** € 1.000 tegen 1% plus € 99.000 tegen 5% levert een verstuurd spaarrendement van **3%** op; naar beginsaldo gewogen is dat **4,96%**. Dit is lokaal gereproduceerd in `buildRequestPayload`. De hoofdengine gebruikt deze scenariorendementen. [Bron](../frontend-react/src/planner/plannerCore.js). | Slice **Vermogen**: laat rendement per actieve vermogenspost door de engine bepalen, met inleg, looptijden en saldomutaties in het contract. Behoud inputcompatibiliteit totdat gelijkheids- en migratietests bestaan. Alleen een gewogen frontendgemiddelde toevoegen lost de dubbele verantwoordelijkheid niet op. |
| **P0** | **Fiscale referenties zijn nog niet sluitend.** De strikte pipeline geeft vier FAILs en twee WARNs voor de zes IB-2025-cases; grootste geregistreerde verschil: **−€ 1.826,06**. De zevende, 2026-case slaagt. API-regressietests bewaken bovendien afwijkingsbaselines, niet uitsluitend gelijkheid met een externe bron. [Register](../tests/fixtures/belasting_testcases/bekende_afwijkingen.json), [API-test](../tests/test_api_regressie_normalized.py). | Onderzoek elke afwijking afzonderlijk: Box 1, Heffingskortingen of AOW, afhankelijk van de vastgestelde oorzaak. Leg primaire bron, eigenaar en afrondingsniveau vast. Behandel bronconflicten niet vooraf als bewezen codebugs. Laat bekende afwijkingen niet stilzwijgend verdwijnen in nieuwe baselines. |
| **P0 bij gedeelde hosting** | **Streamlit gebruikt één gedeeld sessiebestand.** `SESSIE_PAD` wijst voor alle gebruikers naar `.sessie.json`; `app.py` laadt dit automatisch. Daarmee ontbreekt in deze opslaglaag scheiding tussen klantdossiers. React gebruikt lokale browseropslag, zonder centrale back-up. [Bron](../src/pensioen/ui/sessie_persistentie.py), [React](../frontend-react/src/App.jsx). | Kies expliciet lokaal persoonlijk gebruik of een dienst met meerdere gebruikers. Voor die laatste vorm: identiteit, autorisatie per dossier, geïsoleerde opslag, herstel en verwijdering. Acceptatie: twee gebruikers kunnen elkaars dossier niet laden of overschrijven. |
| **P1** | **Scenariovergelijking noemt cashflow ‘netto inkomen’.** `netto_per_maand_mediaan` komt uit `JaarResultaat.netto_per_maand`, dat `netto` gebruikt; dat is de cashflow inclusief overige geldstromen. Het React-resultatenscherm onderscheidt netto inkomen inmiddels wel. Daarnaast geeft vermogen op 80 buiten de horizon € 0, terwijl de waarde onbekend is. [Scenario-engine](../src/pensioen/calculations/scenario_engine.py), [DTO](../src/pensioen/models/cashflow.py), [weergave](../frontend-react/src/components/ScenarioSection.jsx). | Slice **Resultaten**: maak inkomen, vrije cashflow en ontbrekende horizonwaarden expliciet in het outputcontract; gebruik dezelfde definities in vergelijking, grafieken en rapport. Test een positief inkomen met negatieve cashflow en een horizon die vóór leeftijd 80 eindigt. |
| **P1** | **Onvoldoende onderscheid tussen voorbeeld en persoonlijk plan.** Een nieuwe sessie bevat Jan Jansen met geboortedatum 15-03-1963. De berekenknop vereist geen bevestigd uitgavenbudget. Daardoor is snel een ogenschijnlijk persoonlijk resultaat beschikbaar op onvolledige aannames. [Defaults](../frontend-react/src/planner/plannerCore.js), [berekenvoorwaarden](../frontend-react/src/App.jsx). | Introduceer een expliciete demostart en een persoonlijke intake: gewenste stopdatum, huidig inkomen, pensioen, maandbudget en vermogen. Laat ontbrekende posten bevestigen. Acceptatie: de gebruiker ziet vóór berekenen welke gegevens ontbreken of voorbeeldgegevens zijn. |
| **P1** | **Lopende requests zijn niet aan hun oorspronkelijke dossier gebonden.** `runBerekening` schrijft na `await fetch` naar de dan actieve React-state; huishouden/scenario wisselen blijft mogelijk. Dit is een codepad-risico, niet in de browser gereproduceerd. | Koppel request-ID, huishouden, scenario en invoersignatuur aan de response; negeer verouderde responses of blokkeer contextwissels tijdens verwerking. Test met een vertraagde response en tussentijds wisselen. |
| **P1 vóór publieke API** | **API-resourcelimieten ontbreken in de applicatielaag.** PDF-upload leest de volledige inhoud en parseert synchroon binnen een async endpoint. Jaarranges en aantallen scenario's hebben geen maximum. `python-multipart` wordt gebruikt via `File` maar staat niet expliciet in `pyproject.toml`. [API](../src/pensioen/api/main.py), [schema's](../src/pensioen/api/schemas.py), [dependencies](../pyproject.toml). | Begrens uploadgrootte, looptijd en lijsten; voer PDF-verwerking buiten de eventloop uit. Verifieer een schone installatie en voeg de benodigde dependency expliciet toe. Onderzoek eventuele limieten in de uiteindelijke proxy/deployment apart. |
| **P1** | **Herstel en bewaren zijn kwetsbaar.** React schrijft het hele dossier frequent naar localStorage; de errorboundary bood alleen sessiewissen als herstel. Verwijderen van huishoudens/scenario's heeft geen herstelpad. De opslagfoutmelding is in deze wijziging verbeterd, maar back-up en herstel ontbreken nog. [App](../frontend-react/src/App.jsx), [errorboundary](../frontend-react/src/main.jsx). | Voeg dossierexport/import met versiecontrole toe, plus herstel of ongedaan maken bij verwijderen. Test volle/geblokkeerde opslag, corrupte sessies, herladen en dossierwissels. |
| **P1** | **Klantreizen zijn beperkt automatisch getest.** Python: 55% totale dekking, maar de centrale engine heeft 99%; de lage totaalscore zit vooral in Streamlit. React had acht import/mappingtests. CI bouwt React maar voert `npm test` niet uit. [CI](../.github/workflows/ci.yml). | Laat frontendtests meelopen in CI en test de hele reis: intake → import bevestigen → budget → berekenen → scenario vergelijken → rapport → sessie herstellen. Geef deze klantpaden voorrang boven uitsluitend een hoger totaalcoveragepercentage. |
| **P2** | **Documentatie stuurt nog naar oude situaties.** AGENTS/masterplan noemen actieve Epic 6/7-documenten die onder het archief staan. De overdracht beschrijft afkappen van negatief saldo en spreiden van jaarbedragen; de huidige hoofdengine/componentlogica wijkt daarvan af. [Overdracht](operations/OVERDRACHT_FUNCTIONEEL_BEHEER.md), [componentmodel](../src/pensioen/models/component.py). | Maak één actuele productbacklog met status, eigenaar en acceptatiecriteria. Markeer historische rekenbeschrijvingen duidelijk en voeg een korte klanthandleiding met één herkenbaar voorbeeld toe. Kies React als klantinterface en geef Streamlit een expliciete beheer-/ontwikkelrol, of leg een andere productkeuze vast. |

## Volgorde voor klantwaarde

1. **Betrouwbaar plan:** los de twee vermogensproblemen op en sluit de fiscale
   bronverschillen. Regel dossierisolatie vóór gedeelde hosting.
2. **Eerste bruikbare uitkomst:** een begeleide persoonlijke intake, zichtbaar
   maandbudget en een samenvatting van inkomen, tekortmoment en vermogen.
   Laat nieuwe KPI's door de engine leveren.
3. **Een keuze kunnen maken:** vergelijk ‘doorgaan’, ‘eerder stoppen’ en
   ‘minder werken’, met duidelijk onderscheid tussen inkomen en cashflow.
4. **Terugkomen en bespreken:** betrouwbaar bewaren/herstellen en een compact
   deelbaar plan met scenario, uitgangspunten en rekenversie.

Toets met vijf beoogde gebruikers of zij zonder uitleg een plan kunnen maken,
de eerste tekortperiode kunnen aanwijzen en het verschil tussen twee
scenario's begrijpen. Dit is een voorgestelde gebruikstest, nog niet uitgevoerd.

## Doorgevoerde UI-verbetering

React is voor deze implementatie als klantinterface gekozen. Streamlit is
meegenomen in de review, maar de Streamlit-schermen zijn niet herontworpen.

- Rustigere algemene stijl, beter leesbare navigatie, mobiele indeling,
  zichtbare toetsenbordfocus en een link om navigatie over te slaan.
- Klanttaal, een concrete berekenactie en vervolgknoppen met de volgende stap.
  De bestaande drie componentweergaven blijven beschikbaar onder
  ‘Weergave aanpassen’; ontwerpvoorbeeldteksten zijn vervangen door invoerhulp.
- Verbindingsinstellingen ingeklapt; globale berekeningsfouten en opslagfouten
  zichtbaar; opslagtekst maakt duidelijk dat het om deze browser gaat.
- Resultaten tonen een waarschuwing bij verouderde uitkomsten, bestaande
  API-aannames en uitleg over inkomen versus vrije cashflow. Een leeg scherm
  biedt een directe stap naar invoer. Import is herkenbaar optioneel en wordt
  bij een alleenstaande niet meer zonder bestand als voltooid gemarkeerd.

Rekenstap voor de resultaatpresentatie: **Resultaten**. Source of truth blijft
`resultaat_service` → `cashflow.jaren[].jaar_samenvatting` en bestaande
API-`aannames`. Invoer: die output plus UI-status; uitvoer: tekst, grafieken en
tabellen. Geen tariefformules of nieuwe fiscale berekeningen toegevoegd.
Afhankelijke gebruikersactie: herberekenen of rapport downloaden. De hierboven
genoemde rekenbevindingen zijn bewust als afzonderlijke vervolgslices vastgelegd.

## Verificatie en beperkingen

- Python-suite: **310 geslaagd, 2 verwachte fouten**, één bestaande
  Starlette/httpx-deprecatiewaarschuwing; totale line coverage **55%**.
- Normalisatiedrift: **7 cases zonder drift**.
- Strikte externe pipeline: **exitcode 1**, bekende vier FAILs/twee WARNs;
  de 2026-case slaagt. Dit is geen nieuw door de UI veroorzaakte regressie.
- React: **10 tests geslaagd**, inclusief twee nieuwe presentatietests voor
  verouderde resultaten, letterlijk tonen van engine-aannames en eerlijke
  opslagstatus. Productiebuild en `git diff --check` geslaagd.
- Visuele en interactieve browsercontrole kon niet worden uitgevoerd: de
  Browser-runtime rapporteert geen beschikbare browser. Mobiele geometrie,
  focusgedrag en volledige klantreis moeten nog visueel worden gecontroleerd.
- Geen afzonderlijke linter of typecheck geconfigureerd in de onderzochte
  package-scripts/pyproject; daarom geen claim dat die controles zijn geslaagd.
- Dependencies en rekenmodellen zijn ongewijzigd. Bestaande wijzigingen in
  `styles.css` zijn behouden; componentweergaven zijn aanvullend aangepast.
  Geen commit, push of publicatie uitgevoerd.

## Gewijzigde bestanden en diff

Werkbranch: `codex/klantwaarde-ui-review`.

| Bestand onder `frontend-react/` | Wijziging |
| --- | --- |
| `src/App.jsx` | Opslagfouten, globale foutmelding, invoerteksten, vervolgstappen en aannames doorgeven |
| `src/components/ComponentsSection.jsx` | Klantgerichte introductie en ingeklapte weergavekeuze, bovenop bestaande wijzigingen |
| `src/components/ResultsSection.jsx` | Lege staat, stale-waarschuwing, bestaande aannames en begrippenuitleg |
| `src/components/ReportSection.jsx` | Klantgerichte rapporttekst |
| `src/components/layout/AppShell.jsx` | Navigatie overslaan |
| `src/components/layout/ContextTopBar.jsx` | Berekenknop en expliciete lokale opslagstatus |
| `src/components/layout/WizardSidebar.jsx` | Leesbare navigatie, optionele import en actieve stap voor hulptechnologie |
| `src/main.jsx` | Nieuw stylesheet laden |
| `src/planner/plannerCore.js` | Alleen navigatielabels; payloadberekening ongewijzigd |
| `src/planner-ui.css` | Nieuw gedeeld stylesheet voor desktop/mobiel |
| `tests/uiPresentation.test.mjs` | Twee tests met serverrendering, zonder browser of luisterende server |

Dit reviewdocument is nieuw. `src/styles.css` was al gewijzigd bij aanvang en
is door deze opdracht niet aangepast. De Git-diff van de werkmap bevat ook
die eerdere wijzigingen.

Belangrijkste functionele diff:

```diff
- localStorage.setItem("pensioen-ui-session-v1", JSON.stringify(payload));
+ try {
+   localStorage.setItem("pensioen-ui-session-v1", JSON.stringify(payload));
+ } catch {
+   actions.setAutosaveStatus("error");
+   return;
+ }
```

## Vervolgfix: opslagfout na berekenen in Edge

De app bewaarde volledige berekeningsresultaten op meerdere niveaus van de
sessie. Een fictief plan 2025–2055 gaf circa 1,88 MB API-output; drie kopieën
leveren ruim 5,6 MB JSON op. Dit kan de localStorage-limiet overschrijden.
De melding bewijst op zichzelf niet dat het Edge-profiel opslag blokkeert.

De opslagfunctie bewaart nu invoer, importgegevens en alle huishoudens/scenario's,
maar geen opnieuw te berekenen resultaten. Na herladen is de berekenstatus idle
zodat de gebruiker opnieuw berekent. Resultaten in het geopende tabblad blijven
beschikbaar. Bestaande sessies worden bij de volgende succesvolle opslag
compact opgeslagen, zonder de vorige sessie eerst te verwijderen.

Bij blijvend falen zijn 'Download back-up van mijn invoer' en 'Opnieuw opslaan'
beschikbaar. Wis geen browsergegevens om deze fout te omzeilen. De JSON-download
is een reservekopie; een algemene import/herstelinterface blijft vervolgwerk.
Tijdens hot reload wordt de actuele invoer niet opnieuw uit de oude cache geladen.

Borging: `frontend-react/tests/sessionStorage.test.mjs` test een sessie met
meerdere grote resultaten, behoud van invoer en foutdoorgifte zonder wissen.
Alle 13 frontendtests en de productiebuild slagen. Het persoonlijke Edge-profiel
is niet rechtstreeks onderzocht. Bron voor de opslaglimiet:
[MDN Web Storage quota](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria).

### Aansluiting netto inkomen (7 september 2026)

Stap: Resultaten. Source of truth: bestaande maandresultaten uit cashflow_engine;
detail_output_engine assembleert de optelbare tabel `netto_aansluiting`.
Netto loon en overig netto inkomen behouden hun persoon. Bruto, werkelijk over
maanden verdeelde box 1 na kortingen, netto invoer, rendement en inhoudingen
staan afzonderlijk. P1 + P2 + gezamenlijk/niet toegewezen = huishouden, zowel
per rij als voor het totaal. Geen gewijzigde fiscale tarieven of kasstromen.
Rendement blijft in het bestaande huishoudelijke netto totaal opgenomen en wordt
nu expliciet benoemd. Inhoudingen zonder persoonsverdeling blijven zichtbaar
als niet toegewezen. Oude resultaten vereisen een nieuwe berekening.

Borging: directe assemblertest, partner-enginetest, frontendpresentatietest;
interne testcase-018-metadata (geen aanpassing van de externe OLA-verwachtingen).

### Plancontrole en scenario-afweging (7 september 2026)

Functionele stap: Resultaten. De bestaande jaar-/maandoutput en
`scenario_engine.ScenarioVergelijking` blijven source of truth; geen gewijzigde
belasting- of vermogensberekeningen. De UI vergelijkt maximaal drie unieke
scenario's op dezelfde personen en horizon. Delta = alternatief minus actief.
De enginevariabele `netto_per_maand_mediaan` betreft mediane vrije cashflow,
niet netto inkomen vóór uitgaven. Rendements- en belastingformules blijven in
de engine; UI toont uitsluitend selectie, verschillen en toelichting.

Vermogen op 80 betreft het einde van het jaar waarin P1 80 wordt. Buiten de
horizon is dit onbekend, niet nul. Plancontrole onderscheidt negatieve jaarlijkse
cashflow (interen) van negatief vermogen, inclusief negatieve maandstanden.
De vroegere claim “stopmoment haalbaar” is verwijderd: er wordt geen vroegste
haalbare stopdatum geoptimaliseerd. Het advies noemt cashflow, vermogen en
tekortjaren per scenario; hoogste cashflow is geen algehele aanbeveling.
Veranderde selectie of berekeninvoer maakt eerder vergelijkingsadvies ongeldig.

Borging: resultsMapping.test.mjs en uiPresentation.test.mjs bevatten regressies
voor leeftijd/horizon, negatieve maandstanden, drie unieke kaarten/verzoeken,
tegenstrijdige afwegingen, delta-richting en verouderde vergelijkingen.

Bij de API-ketencontrole bleek `beste_scenario_netto` als dataclass-property
niet geserialiseerd te worden. De API geeft nu expliciet de naam door van de
bestaande enginekeuze; geen tweede rangschikkingsberekening in de frontend.
De API-regressietest borgt dat deze naam aansluit op de hoogste engine-mediaan.

### Begrijpelijke scenariokaarten (7 september 2026)

Stap **Resultaten**, eigenaar `calculations/scenario_klantbeeld.py`. Invoer:
bestaande maandcashflow, scenario-werkdatums na inheritance-resolutie en
geboortedatum P1. Uitvoer: `ScenarioResultaat.klantbeeld` en gedeelde
`ScenarioVergelijking.klantvergelijking`. Geen nieuwe tarieven; fiscale en
vermogensformules blijven bij hun bestaande eigenaren. API en de gedeelde
Reactcomponent `ScenarioComparison` presenteren uitsluitend deze output.

- Gemiddelde over per maand = Decimal-som van maandcashflow gedeeld door het
  aantal geselecteerde maanden, afgerond op centen. Dit vervangt de mediaan in
  de hoofdweergave. Cashflow omvat belasting, uitgaven, rendement en eenmalige
  posten; het bedrag is geen garantie voor vrij besteedbaar inkomen.
- Voor alle scenario's dezelfde maanden: vanaf de eerste volledige maand na de
  laatste werk-einddatum van alle personen in alle scenario's. Zonder volledig
  vastgelegde einddatums gebruiken we expliciet de hele horizon. Zonder maanden
  na stoppen binnen de horizon is het gemiddelde onbekend. Overbruggingsjaren
  vóór deze gemeenschappelijke periode blijven in de buffer- en jaarrisico's.
- Grootste jaarlijkse tekort = grootste negatieve jaarsom als positief aan te
  vullen bedrag. Jaren met interen zijn geen jaren zonder geld; de jaaropbouw
  toont ieder jaar en bedrag. Jaren met negatieve maandstanden staan apart.
- Laagste buffer = laagste berekende maandultimo over de hele horizon, inclusief
  maand en jaar. Geen claim over de laagste stand binnen een maand.
- Vermogen op 80 blijft einde van het jaar waarin P1 80 wordt; ontbrekend jaar
  is onbekend. Verschillen worden centraal ten opzichte van het eerste/actieve
  scenario bepaald. Belastingsdruk en de oude mediaan staan onder Rekendetails.

Directe en API-regressies: `tests/test_scenario_klantbeeld.py`; interne broncase
018 met `regressies_scenariokaarten` en hernieuwde normalized fixture. Externe
OLA-verwachtingen blijven ongewijzigd. UI-regressie in `uiPresentation.test.mjs`.
