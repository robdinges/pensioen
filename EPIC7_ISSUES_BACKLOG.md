# Epic 7 — Issues backlog

## Status

**Afgerond en geaccepteerd op 26 juli 2026.**

| Nr. | Issue | Resultaat | Afhankelijk |
| --- | --- | --- | --- |
| 1–3 | Legacyregister, calleranalyse en classificatie | Gereed | `docs/architecture/LEGACYREGISTER.md` |
| 4–6 | Pensioen-, woning- en vermogenscompatibiliteit | Gemotiveerd behouden | migratie pas binnen toekomstige API v2 |
| 7 | Accountantcompatibiliteitswrapper verwijderen | Gereed | centrale detailoutput |
| 8 | Accountant- en jaardetailoutput typen | Gereed | contract 1.0 |
| 9 | Publieke calculation-service consolideren | Gereed | `bereken_resultaten()` |
| 10 | API-deprecatiebeleid | Gereed en goedgekeurd | contract 1.0 blijft compatibel |
| 11–12 | Frontendstrategie en migratie | Gereed en goedgekeurd | React primair; Streamlit beheer/validatie |
| 13 | Ongebruikte helpers | Geclassificeerd | veilige kandidaten behouden tot API v2 |
| 14 | Tijdelijke analyses archiveren | Gereed uit eerdere documentopschoning | — |
| 15 | Doelarchitectuur publiceren | Gereed | ownershipmatrix gepubliceerd |
| 16 | Eindvalidatie en migratiecheck | Geaccepteerd met geregistreerde fiscale afwijkingen | fiscale schuld blijft zichtbaar |

## Acceptatiecriteria

### Legacyverwijdering

- geen kandidaat wordt uitsluitend op naam of vermoedelijk gebruik verwijderd
- calleranalyse omvat Python, React, API-serialisatie, fixtures en sessiedata
- iedere verwijdering heeft regressiedekking
- fallbackgedrag wordt niet stil gewijzigd

### DTO en services

- publieke modellen hebben typecontract en versie
- fiscale modules worden niet afhankelijk van UI/API
- API en Streamlit gebruiken dezelfde resultaatservice
- tijdelijke dictvelden hebben een gedocumenteerd migratiepad

### Frontend

- producteigenaar heeft de doelkeuze bevestigd
- achterblijvende frontend heeft een expliciete functie en eigenaar
- functionaliteitspariteit is getoetst vóór verwijdering
- sessie- en rapportmigratie is beschreven

### Eindpoort

- geen bekende dubbele fiscale berekening
- alle Epic 6-contract- en regressiepoorten uitgevoerd
- architectuurdocumentatie komt overeen met de code
- resterende technische schuld staat met eigenaar en reden geregistreerd

Uitkomst op 26 juli 2026:

- 302 Python-tests geslaagd en 2 bekende API-regressiegevallen `xfail`
- 194 bouwsteen-/contracttests geslaagd en dezelfde 2 gevallen `xfail`
- 8 frontendtests en de productiebuild geslaagd
- alle 7 genormaliseerde belastingfixtures zijn driftvrij
- de strikte fiscale validatie blijft rood voor bestaande 2025-referentiecijfers;
  de 2026-regressiecase slaagt exact. Dit is fiscale validatieschuld en geen
  architectuurregressie van Epic 7.

## Productbesluit

Op 26 juli 2026 heeft de producteigenaar bevestigd:

- React is de primaire gebruikersinterface; Streamlit blijft voor beheer en
  validatie.
- API-contract `1.0` en oude sessies blijven voorlopig ondersteund. Breaking
  opschoning wordt afzonderlijk gepland binnen een toekomstige API v2.
- De geregistreerde fiscale 2025-validatieafwijkingen worden voor afsluiting
  van Epic 7 geaccepteerd en blijven als fiscale validatieschuld zichtbaar.

## Go/no-go-vraag

```text
Kan ieder overgebleven model, service en presentatiepad worden verklaard als
onderdeel van de definitieve architectuur, zonder tijdelijke shadow-logica?
```
