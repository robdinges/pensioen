# Epic 6 — Issues backlog

## Status

**Open — nulmeting uitgevoerd, gereed om te starten.**

Nulmeting 26 juli 2026: 282/286 pytest-tests groen, 52% line coverage,
IB-2025-validatie op 2 WARN en 4 FAIL en een geslaagde React-build. De vier
testfouten worden binnen deze Epic onderzocht; baselines worden niet
automatisch aangepast.

| Nr. | Issue | Resultaat | Afhankelijk |
| --- | --- | --- | --- |
| 1 | Inventariseer alle tests en fixtures | volledige inventarislijst | — |
| 2 | Classificeer tests per berekenstap | primaire stap per testmodule | 1 |
| 3 | Publiceer testmatrix | `tests/TESTMATRIX_BEREKENSTAPPEN.md` | 2 |
| 4 | Registreer ontbrekende en dubbele dekking | geprioriteerde gaps | 3 |
| 5 | Introduceer pytest-markers | selecteerbare testlagen | 2 |
| 6 | Schrijf regressieprotocol | verplicht bugfixproces | 3 |
| 7 | Borg protocol in agentinstructies | automatische uitvoeringsdiscipline | 6 |
| 8 | Contracteer raw/normalized lifecycle | reproduceerbare fixtures | 1 |
| 9 | Maak afwijkingenregister | eigenaar en status per mismatch | 8 |
| 10 | Splits CI in herkenbare poorten | snelle en volledige feedback | 5, 8 |
| 11 | Voeg normalisatie-driftcheck toe | CI faalt op niet-geregenereerde output | 8, 10 |
| 12 | Voeg resultaat/detail-gelijkheidstests toe | geen drift tussen outputvormen | 3 |
| 13 | Borg React/Streamlit/API-contracten | presentatiedrift wordt zichtbaar | 10, 12 |
| 14 | Genereer validatie-index | één ingang voor bewijs en afwijkingen | 9–13 |
| 15 | Voer volledige Epic 6-poort uit | onderbouwd go/no-go voor Epic 7 | 14 |

## Acceptatiecriteria per issue

### Issues 1–4 — Testmatrix

- iedere testmodule is opgenomen
- iedere module heeft één primaire functionele stap
- integratie- en presentatietests zijn apart herkenbaar
- ontbrekende directe dekking is niet verstopt onder integratiedekking

### Issues 5–7 — Regressiediscipline

- markers staan geregistreerd in `pyproject.toml`
- markerselecties draaien lokaal en in CI
- bugfixtemplate vraagt oorzaak, bouwsteentest en hogere regressietest
- calculation-affecting changes blijven fixture-updates vereisen

### Issues 8–9 — Referentiedata

- bron, normalisatie en rapport zijn herleidbaar
- handmatige wijzigingen aan normalized worden gedetecteerd
- iedere WARN/FAIL heeft classificatie: codebug, referentieschuld,
  tolerantieverschil of nog te onderzoeken

### Issues 10–13 — Automatische poorten

- onverwachte unit- of contractfouten blokkeren
- bekende fiscale afwijkingen worden apart en zichtbaar gerapporteerd
- React-build is onderdeel van de integratiepoort
- jaar_samenvatting en accountant_detail blijven onderling consistent

### Issues 14–15 — Go/no-go

- validatie-index bevat laatste uitvoerdatum en resultaat
- open risico’s hebben eigenaar en vervolgstap
- Epic 7 start pas na expliciete go/no-go

## Go/no-go-vraag

```text
Is iedere functionele regel herleidbaar naar een directe test, een hoger
regressiepad en — waar relevant — een externe referentie?
```
