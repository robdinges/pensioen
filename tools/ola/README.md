# OLA-validatie voor IH2025

Herbruikbare CLI voor fictieve huishoudens met één of twee personen. De tool
ontdekt het formulier op de officiële OLA-opleidingssite, bedient de zichtbare
aangifte en bewaart bronbedragen, screenshots, invoer en engine-output per run.
Alleen 2025 wordt geaccepteerd. Er wordt geen aangifte verzonden.

## Gebruik vanuit de projectroot

```bash
pip install -e ".[ola]"
python3 -m playwright install chromium
python3 -m tools.ola catalogus
python3 -m tools.ola voorbereiden config/ola/cases/alleen_werkend.json
python3 -m tools.ola uitvoeren config/ola/verified/alleen_werkend.json --controleur "naam" --headless
python3 -m tools.ola vergelijken PAD_NAAR_RUN
python3 -m tools.ola exporteren PAD_NAAR_RUN
```

Elke run krijgt een eigen map onder `validatie/ola/runs/` (gitignored).
`ola.json` bevat uitsluitend waargenomen OLA-bedragen en bewijshashes;
`pensioen.json` bevat de invoer, tarievenhash en output van de huidige engine.
`vergelijking.json`, `verschillen.csv` en `rapport.md` tonen de afwijkingen.
Export maakt een kandidaat voor het bestaande raw-testcasecontract, zonder
baselines te wijzigen. Exitcodes: 0 = PASS/voorbereid, 1 = afwijking of
invoerverschil, 2 = onvolledig/fout. PASS geldt alleen voor gelezen velden.

## Cases opnemen

De voorbeelden onder `config/ola/cases/` zijn invoersjablonen, geen complete
browserrecepten. `config/ola/verified/` bevat live opgenomen recepten.
Een opgenomen recept bewijst niet dat de pensioenengine dezelfde uitkomst geeft.

De vijf opgenomen recepten omvatten drie looncases en twee AOW/pensioencases
zonder woning of vermogen. De pensioencases gebruiken bewust de huidige
engine-AOW als gelijke fiscale invoer; de SVB-uitkeringshoogte is daarmee niet
gevalideerd. Hun resterende AHK-verschillen van €1 staan expliciet in
`docs/OLA_VALIDATIE_2025.md`. PASS betekent binnen tolerantie, niet altijd exact.

```bash
python3 -m tools.ola opnemen config/ola/cases/paar_werkend.json
# Alternatief: JSON-stappen in de terminal, met zichtbare DOM-inspectie
python3 -m tools.ola opnemen config/ola/cases/paar_werkend.json --terminal
```

De browsermodus gebruikt Alt-klik om een element aan een terminalopdracht te
koppelen. `velden` toont resultaatnamen. In terminalmodus toont `scherm` de
zichtbare tekst en bedieningselementen. Geef vervolgens JSON volgens `Stap`
in `modellen.py`. Sluit af met `klaar NAAM` na controle van invoer en bedragen.
Het definitieve recept staat in de `case.json` van de run; kopieer dat naar
een eigen configuratiebestand om het te herhalen. `batch MAP --controleur NAAM`
herhaalt alle recepten in een map.

Bind bedragen en geboortedata via `waarde_pad` aan de case. Leg overige keuzes
ook in de case vast. Dynamische OLA-elementen kunnen na een sitewijziging andere
selectors krijgen: een mislukte bediening is ONVOLLEDIG, nooit een geldige nul.

## Betekenis en beperkingen

Vergelijk verschuldigde IB/PVV **vóór** verrekening van loonheffing en voorlopige
aanslagen, exclusief Zvw. Bij nul voorheffingen is dit gelijk aan het getoonde
eindtotaal. Partners vereisen beide persoonsuitkomsten; het huishoudtotaal wordt
vergeleken omdat de engine geen afzonderlijke box-3-toedeling per partner geeft.
Woningverdeling is 100% alleen of 50/50 partners. Geen bijzondere situaties.

De engine bepaalt AOW zelf. Een verschil tussen case-AOW en engine-AOW geeft
INVOER_VERSCHIL en blokkeert export: eerst gelijke invoer organiseren, niet een
afwijkende bron stilzwijgend als fiscale baseline opnemen.

Functionele stap: **Resultaten**. Source of truth voor pensioenberekeningen is
de bestaande resultaatservice met accountant-detail; de tool voegt geen fiscale
formules toe. Invoer: case + tarieven 2025. Uitvoer: extern bewijs en vergelijking.
Vervolg: gerichte correcties per fiscale bouwsteen met directe en regressietests.
Tests van de tool staan in `tests/test_ola_tool.py`.


## AOW-bron en formulierafronding (2025)

De actieve pensioencases `verified/*_pensioen_svb.json` gebruiken officiële
halfjaarbedragen plus de in mei betaalde vakantieopbouw. OLA accepteert hele
euro’s: `formaat: "euro_heel_omlaag"` legt de keuze per inkomensveld vast.
Casebedragen en enginecashflow behouden centen. Invulblad en vergelijkingsrapport
vermelden de formulierbedragen apart (`formulierafrondingen`). Een PASS geldt
voor de opgenomen resultaatvelden binnen €1 tolerantie, met deze expliciete
formulierconversie; niet voor identieke centeninvoer in OLA.

`config/ola/historisch/` bewaart de oorspronkelijke pensioenrecepten met oude
AOW-bedragen. Hervergelijking met de actuele engine geeft `INVOER_VERSCHIL`;
de fiscale tests bevriezen deze historische bruto invoer afzonderlijk.
Zie `docs/OLA_VALIDATIE_2025.md` voor bronnen, opbouwtijdvak en beperkingen.
