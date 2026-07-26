# Epic 7 — Opschoning en doelarchitectuur

## Status

**Afgerond en geaccepteerd op 26 juli 2026.**

## Doel

Verwijder aantoonbaar obsolete structuren en consolideer de definitieve
architectuur zonder functioneel gedrag stil te veranderen.

## Uitgangspunten

- verwijderen volgt op bewijs, niet op vermoeden
- iedere verwijdering heeft zoekbewijs, testbewijs en migratiebesluit
- fiscale formules blijven in `tax/`
- orkestratie blijft in `calculations/`
- UI, API en rapportage blijven pure consumenten
- compatibiliteit wordt expliciet beëindigd of gedocumenteerd behouden

## Scope

- legacy pensioen-, woning- en vermogensvelden
- compatibiliteitswrappers en ongebruikte helpers
- definitieve detailoutput- en DTO-contracten
- servicegrenzen tussen calculation, API en presentatie
- dubbele frontendstrategie
- verouderde analyses, instructies en tijdelijke migratienotities

Niet in scope:

- nieuwe fiscale functionaliteit
- grootschalige visuele redesign
- verwijdering zonder regressiedekking

## Werkstromen

### 1. Legacyregister

Maak per kandidaat inzichtelijk:

- definitie en huidige callers
- historische reden
- vervangende source of truth
- migratiepad
- verwijdercriterium
- compatibiliteitsimpact

Startkandidaten:

- `Scenario.spaargeld_start`
- `Scenario.beleggingen_start`
- `Scenario.eigen_woning`
- legacy pensioenrecord-berekenpaden
- `_bereken_jaar_detail()`-compatibiliteitswrapper
- ongebruikte UI- en vermogenshelpers
- dubbele resultaat- of tariefvoorbereiding

### 2. Veilige verwijdering per domeinstap

Werk in kleine slices:

1. pensioen
2. eigen woning
3. Box 3/vermogensgrondslag
4. resultaatdetail
5. presentatie- en API-adapters

Verwijder geen fallback voordat gelijkheidstests aantonen dat de nieuwe bron
dezelfde bedoelde output levert.

### 3. DTO- en serviceconsolidatie

Beslis en implementeer:

- typed detailoutput in plaats van brede `dict`-contracten
- publieke versus interne calculation-services
- één voorbereidingsservice voor tarieven en scenarioresolutie
- stabiele API-versies en deprecationbeleid

### 4. Frontendbesluit

Neem expliciet één besluit:

- React wordt primaire UI en Streamlit blijft beheer/validatie
- Streamlit blijft primaire UI en React stopt
- beide blijven, met afzonderlijk eigenaarschap en contracttests

Beoordeel onderhoudslast, functionele dekking, gebruikersdoel, deployment en
toegankelijkheid. Verwijder geen frontend vóór een goedgekeurd migratieplan.

### 5. Documentatie en instructies

- archiveer tijdelijke analyses
- actualiseer projectstructuur
- verwijder verwijzingen naar verdwenen compatibiliteit
- publiceer definitieve architectuur en ownershipmatrix

## Verwijderpoort per kandidaat

Een legacyonderdeel mag pas weg als:

1. `rg` alle callers en serialisatieafhankelijkheden in kaart heeft gebracht
2. vervangende source of truth expliciet is
3. directe en hogere regressietests groen zijn
4. fixture- en API-impact beoordeeld is
5. migratie- of release-notitie aanwezig is
6. rollback via Git mogelijk blijft

## Definition of Done

Epic 7 is gereed als:

1. alle legacykandidaten verwijderd of gemotiveerd behouden zijn
2. er één publieke service-ingang voor resultaatberekening is
3. detailoutput formeel getypeerd en versieerbaar is
4. dubbele fiscale en cashflowpaden afwezig zijn
5. de frontendstrategie expliciet is vastgesteld
6. projectdocumentatie de werkelijke architectuur beschrijft
7. de volledige Epic 6-validatiepoort groen of expliciet geaccepteerd is

## Uitvoering 26 juli 2026

- legacyregister gepubliceerd in `docs/architecture/LEGACYREGISTER.md`
- scenariovergelijking geconsolideerd op `bereken_resultaten()`
- Streamlit-accountant consumeert centrale detailoutput zonder wrapper of
  lokale detailopbouw
- typed en versieerbaar resultaatcontract gepubliceerd in
  `src/pensioen/models/output_contract.py`
- doelarchitectuur en API-deprecatiebeleid gepubliceerd onder
  `docs/architecture/`
- React als primaire UI vastgesteld; Streamlit voorlopig behouden voor
  beheer/validatie
- volledige Python-, frontend-, bouwsteen- en contracttestpoorten uitgevoerd
- genormaliseerde fixtures driftvrij; bestaande afwijkingen tegenover de
  fiscale 2025-referentiecijfers expliciet als open validatieschuld vastgelegd

Productbesluiten:

- React is de primaire UI; Streamlit blijft voor beheer en validatie.
- API-contract `1.0` en oude sessies blijven voorlopig ondersteund. Een
  toekomstige API v2 en bijbehorende migratie vormen een afzonderlijke scope.
- De bekende fiscale 2025-validatieafwijkingen zijn geaccepteerd voor
  afsluiting van Epic 7 en blijven geregistreerde validatieschuld.
