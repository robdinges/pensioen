# Handmatige debughulpmiddelen

Deze scripts zijn diagnostische hulpmiddelen en maken geen deel uit van de
geautomatiseerde pytest-suite in `tests/`.

Voer ze vanuit de projectroot uit, bijvoorbeeld:

```bash
PYTHONPATH=src python3 tools/debug/diagnose_scenario.py
PYTHONPATH=src python3 tools/debug/test_component_inheritance.py
```

Bestanden met de prefix `test_` zijn hier bewust behouden vanwege hun
herkenbare doel, maar worden door `pytest` niet verzameld omdat `testpaths`
naar `tests/` wijst.
