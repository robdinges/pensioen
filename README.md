## Pensioenplanner

Professionele Nederlandse pensioenplanner met dag-nauwkeurige
cashflowprognose voor een huishouden.

## Features

- Bruto-naar-netto berekening voor loon, AOW en pensioen per persoon.
- Box 3 berekening via forfaitair rendement:
  - spaargelddeel met `forfaitair_spaargeld`
  - overig/beleggingendeel met `forfaitair_overig`
  - belasting over fictief rendement tegen box 3 tarief
- Scenario-invoer met verstelbare spaargeldfractie voor box 3.
- Accountantsoverzicht met volledige component-analyse van netto cashflow:
  - inkomen (na box 1)
  - box 3 heffing op fictief rendement
  - rendement op vermogen
  - inleg en opname (incl. incidentele ontvangsten/uitgaven)
- Gestructureerde scenario-invoer met meerdere regels per component:
  - extra bruto loon/uitkering
  - inhoudingen (loonbelasting etc.)
  - jaarlijkse huishoudelijke uitgaven
  - eenmalige ontvangsten/uitgaven
  - regels zijn per blok toe te voegen en te verwijderen.

## Usage

1. Installeer dependencies:

```bash
python3 -m pip install -e ".[dev]"
```

2. Start de app:

```bash
streamlit run app.py
```

3. Open in de app het tabblad Accountantsoverzicht en klik op
   Berekening uitvoeren.

4. Controleer de componenttabel Netto cashflow opgebouwd uit losse
  componenten in het accountantsoverzicht.

## Testing

```bash
python3 -m pytest tests/ -q
```
