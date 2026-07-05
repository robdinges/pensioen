# Testcase JSON Schema

Documentatie voor de JSON-structuur van belastingtestcases. Dit schema beschrijft de **normalized** vorm - raw JSONs mogen afwijken.

## Overzicht

Elke testcase representeert een compleet huishouden met alle relevante gegevens om de belastingberekening te valideren tegen een bekende uitkomst (bijv. echte aangifte).

---

## Root Schema

```json
{
  "testcase_id": "string (verplicht, uniek)",
  "naam": "string (verplicht, beschrijvend)",
  "jaar": "integer (verplicht, belastingjaar)",
  "datum_aangeleverd": "string (ISO date, optioneel)",
  "bron_formaat": "string (Excel/CSV/PDF/tekst, optioneel)",
  "huishouden": { ... },
  "personen": [ ... ],
  "vermogen": { ... },
  "verwachte_belasting": { ... },
  "metadata": { ... }
}
```

---

## Huishouden

```json
"huishouden": {
  "type": "string (ALLEENSTAAND|PAAR|GEHUWD)",
  "aantal_personen": "integer (1 of 2)",
  "is_gehuwd": "boolean (optioneel)",
  "eigen_huis": "boolean (optioneel, default: false)"
}
```

**Waardes**:
- `type`: ALLEENSTAAND, PAAR (samenwonend), GEHUWD
- `aantal_personen`: 1 (alleenstaand) of 2 (paar/gehuwd)
- `eigen_huis`: Heeft invloed op vermogensvrijstelling Box 3

---

## Personen

Array met 1 of 2 personen (afhankelijk van huishouden-type).

```json
"personen": [
  {
    "naam": "string (Persoon 1, Partner, etc.)",
    "geboortedatum": "string (ISO date YYYY-MM-DD, verplicht)",
    "bruto_arbeid": "number (jaarinkomen, default: 0)",
    "bruto_pensioen": "number (jaarinkomen werkgeverspensioen, default: 0)",
    "bruto_aow": "number (jaarinkomen AOW, default: 0)",
    "bruto_overig": "number (overig inkomen, default: 0)",
    "is_aow_heel_jaar": "boolean (optioneel, auto-detect via geboortedatum+jaar)"
  }
]
```

**Notities**:
- `bruto_*` bedragen zijn **jaarbedragen** (niet per maand)
- `is_aow_heel_jaar`: Wordt automatisch berekend via `aow_engine.aow_breuk_jaar()` als niet aanwezig
- Alle inkomens zijn **bruto** (vóór belasting)

---

## Vermogen

```json
"vermogen": {
  "totaal": "number (verplicht, totaal vermogen op 1 januari)",
  "spaargeld": "number (optioneel, absolute waarde)",
  "beleggingen": "number (optioneel, absolute waarde)",
  "spaargeld_fractie": "number (0.0-1.0, fractie sparen vs beleggen)",
  "_opmerking": "Geef spaargeld+beleggingen OF spaargeld_fractie (niet beide)"
}
```

**Berekeningsregels**:
- Als `spaargeld` en `beleggingen` gegeven: `spaargeld_fractie = spaargeld / totaal`
- Als alleen `spaargeld_fractie` gegeven: OK (standaard split)
- Default `spaargeld_fractie`: 0.4 (40% sparen, 60% beleggen) bij ontbreken

---

## Verwachte Belasting

Referentiewaarden waartegen het model wordt gevalideerd. 

**Minimaal vereist**: `totaal_verschuldigd` (huishouden-niveau)  
**Per-persoon details**: Optioneel, alleen voor gedetailleerde belastingvalidatie

**Notitie pensioenplanning**: Voor cashflow-berekeningen is het huishouden-totaal voldoende. Per-persoon breakdown is vooral nuttig voor belastingtechnische validatie.

```json
"verwachte_belasting": {
  "totaal_verschuldigd": "number (verplicht, huishouden-totaal)",
  "totaal_verschuldigd_p1": "number (optioneel, alleen voor gedetailleerde validatie)",
  "totaal_verschuldigd_p2": "number (optioneel, alleen voor gedetailleerde validatie)",
  
  "bruto_p1": "number (optioneel, totaal bruto inkomen persoon 1)",
  "bruto_p2": "number (optioneel, totaal bruto inkomen persoon 2)",
  
  "box1_ib_p1": "number (optioneel, inkomstenbelasting vóór kortingen P1)",
  "box1_ib_p2": "number (optioneel, inkomstenbelasting vóór kortingen P2)",
  
  "premie_aow_p1": "number (optioneel, AOW-premie P1)",
  "premie_aow_p2": "number (optioneel, AOW-premie P2)",
  "premie_anw_p1": "number (optioneel, Anw-premie P1)",
  "premie_anw_p2": "number (optioneel, Anw-premie P2)",
  "premie_wlz_p1": "number (optioneel, Wlz-premie P1)",
  "premie_wlz_p2": "number (optioneel, Wlz-premie P2)",
  
  "ahk_p1": "number (optioneel, algemene heffingskorting P1)",
  "ahk_p2": "number (optioneel, algemene heffingskorting P2)",
  "arbeidskorting_p1": "number (optioneel, arbeidskorting P1)",
  "arbeidskorting_p2": "number (optioneel, arbeidskorting P2)",
  "ouderenkorting_p1": "number (optioneel, ouderenkorting P1)",
  "ouderenkorting_p2": "number (optioneel, ouderenkorting P2)",
  "alleenstaandeouderenkorting": "number (optioneel, alleen voor alleenstaanden)",
  
  "box3_grondslag": "number (optioneel, belastbare grondslag Box 3)",
  "box3_fictief_rendement": "number (optioneel, berekend forfaitair rendement)",
  "box3_heffing": "number (optioneel, verschuldigde Box 3 belasting)",
  
  "netto_p1": "number (optioneel, netto inkomen P1)",
  "netto_p2": "number (optioneel, netto inkomen P2)"
}
```

**Notities**:
- Meer tussenresultaten = betere validatie (vindt exact waar afwijking zit)
- `_p1` / `_p2` suffix: Per persoon (Persoon 1, Persoon 2)
- Zonder suffix: Huishouden-niveau (bijv. `box3_grondslag`)

---

## Metadata

Vrije vorm voor context, uitgangspunten, opmerkingen.

```json
"metadata": {
  "uitgangspunten": [
    "string (lijst van aannames/uitgangspunten)"
  ],
  "opmerkingen": "string (vrije tekst opmerkingen)",
  "data_kwaliteit": "string (volledig|gedeeltelijk|minimaal)",
  "bron": "string (bijv. 'Aangifte 2025 Belastingdienst')",
  "_incomplete": "boolean (true als data ontbreekt)"
}
```

**Gebruik**:
- `uitgangspunten`: Lijst van relevante aannames (bijv. "Geen eigen huis", "AOW heel jaar")
- `data_kwaliteit`: Indicatie volledigheid tussenresultaten
- `_incomplete`: Flag voor normalisatie-script (handmatige review nodig)

---

## Voorbeeld: Volledig Testcase

```json
{
  "testcase_id": "tc_2025_example",
  "naam": "Alleenstaand voorbeeldcase 2025",
  "jaar": 2025,
  "datum_aangeleverd": "2026-06-05",
  "bron_formaat": "Excel",
  
  "huishouden": {
    "type": "ALLEENSTAAND",
    "aantal_personen": 1,
    "eigen_huis": false
  },
  
  "personen": [
    {
      "naam": "Persoon 1",
      "geboortedatum": "1955-03-15",
      "bruto_arbeid": 0,
      "bruto_pensioen": 86813,
      "bruto_aow": 0,
      "bruto_overig": 0,
      "is_aow_heel_jaar": true
    }
  ],
  
  "vermogen": {
    "totaal": 500000,
    "spaargeld_fractie": 0.4
  },
  
  "verwachte_belasting": {
    "totaal_verschuldigd": 32177,
    "bruto_p1": 86813,
    "box1_ib_p1": 22471,
    "premie_aow_p1": 0,
    "premie_anw_p1": 38,
    "premie_wlz_p1": 3709,
    "ahk_p1": 0,
    "arbeidskorting_p1": 0,
    "ouderenkorting_p1": 0,
    "alleenstaandeouderenkorting": 531,
    "box3_grondslag": 442316,
    "box3_fictief_rendement": 18028,
    "box3_heffing": 6490
  },
  
  "metadata": {
    "uitgangspunten": [
      "Alleenstaand, AOW-gerechtigd heel jaar 2025",
      "Alleen pensioeninkomen (werkgeverspensioen)",
      "Vermogen: €500k (40% sparen, 60% beleggen)",
      "Geen eigen huis"
    ],
    "data_kwaliteit": "volledig",
    "bron": "Aangifte 2025 via Belastingdienst"
  }
}
```

---

## Voorbeeld: Minimaal Testcase

```json
{
  "testcase_id": "tc_2026_002",
  "naam": "Paar werkend 2026",
  "jaar": 2026,
  
  "huishouden": {
    "type": "PAAR",
    "aantal_personen": 2
  },
  
  "personen": [
    {
      "naam": "Persoon 1",
      "geboortedatum": "1975-06-20",
      "bruto_arbeid": 65000,
      "bruto_pensioen": 0
    },
    {
      "naam": "Partner",
      "geboortedatum": "1978-11-05",
      "bruto_arbeid": 48000,
      "bruto_pensioen": 0
    }
  ],
  
  "vermogen": {
    "totaal": 120000,
    "spaargeld_fractie": 0.6
  },
  
  "verwachte_belasting": {
    "totaal_verschuldigd": 45230
  },
  
  "metadata": {
    "uitgangspunten": [
      "Beide partners werkend",
      "Geen AOW",
      "Vermogen: €120k (60% sparen, 40% beleggen)"
    ],
    "_incomplete": true
  }
}
```

---

## Normalisatie-Regels

Bij conversie van `raw/` naar `normalized/`:

1. **Verplichte velden**: `testcase_id`, `naam`, `jaar`, `huishouden.type`, `personen[0].geboortedatum`, `verwachte_belasting.totaal_verschuldigd`
2. **Defaults**: 
   - `bruto_*`: 0 bij ontbreken
   - `spaargeld_fractie`: 0.4 (40/60 split)
   - `eigen_huis`: false
3. **Auto-calculaties**:
   - `is_aow_heel_jaar`: Via `aow_engine.aow_breuk_jaar(geboortedatum, jaar)`
   - `huishouden.aantal_personen`: `len(personen)`
4. **Validatie**:
   - Geboortedatum ≤ jaar - 18 (minstens 18 jaar oud in belastingjaar)
   - Vermogen ≥ 0
   - `spaargeld_fractie` tussen 0.0 en 1.0
5. **Warnings**:
   - `_incomplete: true` → Handmatige review nodig
   - Ontbrekende tussenresultaten → Beperkte validatie mogelijk

---

## Data Quality Levels

| Level | Beschrijving | Tussenresultaten |
|-------|--------------|------------------|
| **volledig** | Alle tussenresultaten aanwezig | Box 1 IB, premies, kortingen, box 3 detail |
| **gedeeltelijk** | Alleen hoofdcomponenten | Totaal verschuldigd + box 1/box 3 totalen |
| **minimaal** | Alleen eindresultaat | Totaal verschuldigd |

**Aanbeveling**: Streef naar "volledig" voor maximale debugging-capaciteit.

---

## Versionering

- **Versie 1.0**: Initiële schema (juni 2026)
- Toekomstige wijzigingen: Backward compatible via optionele velden + defaults

Bij schema-wijzigingen: Update dit document + normalisatie-script.
