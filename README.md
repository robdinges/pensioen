## Pensioenplanner

Professionele Nederlandse pensioenplanner met dag-nauwkeurige
cashflowprognose voor een huishouden.

## Features

- Bruto-naar-netto berekening voor loon, AOW en pensioen per persoon.
- Box 3 berekening via forfaitair rendement:
  - spaargelddeel met `forfaitair_spaargeld`
  - overig/beleggingendeel met `forfaitair_overig`
  - belasting over fictief rendement tegen box 3 tarief
- Afzonderlijke rendementen voor sparen en beleggen:
  - optioneel twee rendementstarieven instellen (spaarrekening vs. beleggingsportefeuille)
  - vermogenssplitsing gebaseerd op expliciet ingevoerd spaargeld en beleggingen
  - componenten kunnen per regel als sparen of beleggen worden gemarkeerd
  - deze componentmix stuurt zowel de maandelijkse rendementsverdeling als de box 3 verdeling
  - fallback naar uniform rendement als aparte tarieven niet ingesteld
- Scenario-invoer met verstelbare spaargeldfractie voor box 3.
- Accountantsoverzicht met volledige component-analyse van netto cashflow:
  - inkomen (na box 1)
  - box 3 heffing op fictief rendement
  - rendement op vermogen
  - inleg en opname (incl. incidentele ontvangsten/uitgaven)
  - gebruikt de actuele vermogens- en eigen-woningbron in plaats van verouderde legacy-weergave
  - toont bij een eenpersoonshuishouden nooit P2-kolommen of P2-bedragen
  - waarschuwt bij handmatig ingevoerde AOW-componenten en filtert deze uit de inkomenssom om dubbeltelling te voorkomen
  - toont de gebruikte bron voor box 3 tarief en forfaiten voor sparen/beleggen
- Gestructureerde scenario-invoer met meerdere regels per component:
  - extra bruto loon/uitkering
  - inhoudingen (loonbelasting etc.)
  - jaarlijkse huishoudelijke uitgaven
  - eenmalige ontvangsten/uitgaven
  - regels zijn per blok toe te voegen en te verwijderen.
  - typekeuze voor eigen woning, hypotheek, spaargeld, beleggingen en overige bezittingen
  - eigen woningvelden voor WOZ-waarde en jaarlijkse waardestijging
  - hypotheekvelden voor primaire woning, hypotheekrente en einddatum renteaftrek
  - eigen woning en hypotheek blijven fiscale invoer voor de box 1-berekening
  - hypotheek telt niet mee als negatieve vermogenspost in de vermogenssom
- Scenario-overzicht als compacte lijst met acties per rij:
  - eerste kolom toont welk scenario actief is
  - direct bewerken, selecteren en verwijderen vanuit dezelfde rij
  - standaardscenario kiezen via radioknop (geen ster-icoonactie)

## Usage

1. Installeer dependencies:

```bash
python3 -m pip install -e ".[dev]"
```

2. Start de app:

```bash
streamlit run app.py
```

3. Beheer scenario's in het scherm Scenario:
  - kies het standaardscenario via de radioknoppen
  - gebruik de actieknoppen in dezelfde rij om een scenario actief te maken,
    te bewerken of te verwijderen.

4. Vul in het scherm Financiële Planning alle componenten in:
  - **Inkomsten & Uitgaven**: Periodieke inkomsten, pensioenen, uitgaven en inhoudingen
  - **Vermogen & Bezittingen**: Spaargeld, beleggingen, eigen woning, hypotheek, auto's, kunst, etc.
    * Kies bij het type **Eigen woning** voor de woningvelden zoals WOZ-waarde en jaarlijkse waardestijging
    * Kies bij het type **Hypotheek** voor primaire woning, hypotheekrente en einddatum renteaftrek
    * De hypotheek blijft fiscale invoer voor box 1 en telt niet mee als negatieve vermogenspost in de totalen
    * Elk vermogensitem heeft zijn eigen rendement/groei percentage
    * Voor spaargeld en beleggingen is dit het verwachte jaarrendement
    * Voor andere bezittingen is dit waardestijging of afschrijving
  - **Eenmalige Posten**: Eenmalige ontvangsten en uitgaven op specifieke data

5. Open in de app het tabblad Accountantsoverzicht en klik op
  Berekening uitvoeren.

6. Controleer de componenttabel Netto cashflow opgebouwd uit losse
  componenten in het accountantsoverzicht.

7. Beheer belastingtarieven in het scherm Instellingen:
  - genereer een nieuw `belasting_YYYY.json` bestand op basis van een bestaand jaar
  - sla het bestand direct op naar `config/` vanuit de app of download het als fallback
  - herbereken bestaande resultaten na opslaan om nieuwe tarieven en forfaiten door te voeren

## Testing

```bash
python3 -m pytest tests/ -q
```
