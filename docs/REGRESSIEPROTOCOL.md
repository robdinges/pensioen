# Regressieprotocol

Dit protocol geldt voor iedere fout in berekeningen, fiscale configuratie,
API-output of resultaatpresentatie.

## Verplichte herleidbaarheid

Iedere bugfix bevat:

1. één oorzaak gekoppeld aan precies één primaire berekenstap
2. de source of truth voor die stap
3. een directe test bij de eigenaar van de regel
4. een hogere regressietest op het pad waar de fout zichtbaar werd
5. een fixture-update als fiscale of cashflow-output verandert
6. een classificatie van het verschil

Toegestane classificaties:

- `codebug`
- `bronconflict`
- `referentieschuld`
- `tolerantieverschil`
- `nog_te_onderzoeken`

## Fixturecontract

- `raw/` bevat de menselijke of externe bron en wordt niet uit `normalized/`
  teruggerekend.
- `normalized/` wordt uitsluitend met `tools/normalize_testcases.py`
  gegenereerd.
- `python tools/normalize_testcases.py --check` controleert in CI dat raw en
  normalized niet uiteenlopen.
- Een referentiewaarde verandert alleen met bronvermelding, reviewreden en
  expliciete goedkeuring.
- `api_regressie_baseline.json` mag alleen bewust worden aangepast; de
  CI-marker `[baseline-update]` maakt de wijziging zichtbaar maar vervangt geen
  inhoudelijke review.

## Bekende afwijkingen

Bekende WARN/FAIL-resultaten staan machineleesbaar in
`tests/fixtures/belasting_testcases/bekende_afwijkingen.json` en leesbaar in
`AFWIJKINGENREGISTER.md` in dezelfde map.

Een bekende afwijking wordt niet als PASS behandeld. Een wijziging in status
of bedrag laat de governancetest falen totdat oorzaak en classificatie opnieuw
zijn beoordeeld. Ook een verbetering moet worden gereviewd voordat de
registratie wordt aangepast.

## Minimale validatiepoort

```bash
PYTHONPATH=src:. python3 tools/normalize_testcases.py --check
python3 -m pytest -m "bouwsteen or contract" -q
python3 -m pytest tests/ -q
PYTHONPATH=src:. python3 tools/test_validatie_pipeline.py --strict
cd frontend-react && npm run build
```

De externe strikte validatie mag in CI tijdelijk rapporterend zijn zolang alle
bekende afwijkingen via de blokkerende governancetest worden bewaakt.
Onverwachte unit-, contract- of regressiefouten zijn altijd blokkerend.

## Reviewvragen

- Welke primaire bron ondersteunt de verwachte uitkomst?
- Is de wijziging een codefix of een referentie-/baselinewijziging?
- Zijn raw, normalized, rapport en afwijkingenregister synchroon?
- Is er naast de directe test ook een hoger regressiepad?
- Introduceert UI, API of rapportage geen zelfstandige fiscale herberekening?
