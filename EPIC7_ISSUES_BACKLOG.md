# Epic 7 — Issues backlog

## Status

**Open, maar uitvoering wacht op Epic 6.**

| Nr. | Issue | Resultaat | Afhankelijk |
| --- | --- | --- | --- |
| 1 | Bouw legacyregister | complete kandidatenlijst | Epic 6 |
| 2 | Meet callers en runtimegebruik | bewijs per kandidaat | 1 |
| 3 | Classificeer behouden/migreren/verwijderen | besluitregister | 2 |
| 4 | Ruim pensioencompatibiliteit op | één pensioenpad | 3 |
| 5 | Ruim legacy eigen-woningmodel op | één woningbron | 3 |
| 6 | Ruim legacy vermogensvelden op | één vermogensbron | 3 |
| 7 | Verwijder accountantcompatibiliteitswrapper | centrale detailservice | 3 |
| 8 | Type accountant- en jaardetailoutput | versieerbare DTO’s | 7 |
| 9 | Consolideer publieke calculation-service | één service-ingang | 4–8 |
| 10 | Formaliseer API-deprecationbeleid | beheersbare breaking changes | 8, 9 |
| 11 | Beslis frontendstrategie | React/Streamlit-doelbesluit | Epic 6 |
| 12 | Voer goedgekeurde frontendmigratie uit | minder dubbele UI-last | 11 |
| 13 | Verwijder ongebruikte helpers en imports | opgeschoonde codebasis | 4–12 |
| 14 | Archiveer tijdelijke analyses | actuele documentatielaag | 13 |
| 15 | Publiceer doelarchitectuur | definitieve ownershipmatrix | 9–14 |
| 16 | Draai eindvalidatie en migratiecheck | programma-go/no-go | 15 |

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

## Go/no-go-vraag

```text
Kan ieder overgebleven model, service en presentatiepad worden verklaard als
onderdeel van de definitieve architectuur, zonder tijdelijke shadow-logica?
```
