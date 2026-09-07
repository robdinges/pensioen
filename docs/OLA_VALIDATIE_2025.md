# OLA-validatie en rekenfix 2025

De gevonden fouten in de schijfgrenzen, premiegrens, arbeidskorting, fiscale
afronding en afbouwgrens van de ouderenkorting zijn gecorrigeerd. De drie
looncases komen exact overeen met OLA. De twee pensioencases hebben nog een
expliciet AHK-verschil van €1; de tolerantie blijft €1 per vastgelegd veld.

| Case | OLA | Pensioenapp | Verschil |
| --- | ---: | ---: | ---: |
| Alleenstaande, €45.000 loon | €8.735 | €8.735 | €0 |
| Partners, €45.000 + €30.000 loon | €11.210 | €11.210 | €0 |
| Afrondingscontrole, €45.003 loon | €8.736 | €8.736 | €0 |
| Alleenstaande, €16.752 AOW + €25.000 pensioen | €4.447 | €4.448 | +€1 |
| Partners, ieder €11.568 AOW, pensioen €25.000 / €15.000 | €4.429 | €4.428 | -€1 |

Bedragen zijn verschuldigde IB/PVV vóór voorheffingen, exclusief Zvw. De
pensioencases zijn op 7 september 2026 live opgenomen, zonder woning, vermogen,
arbeidsinkomen of bijzondere situaties. Beide personen hebben heel 2025 de
AOW-leeftijd. AOW-invoer is bewust gelijk aan de huidige engine-output:
**dit valideert de fiscale behandeling, niet de hoogte van de SVB-uitkering**.

## AOW-validatie 7 september 2026

Primaire berekenstap: **Heffingskortingen**. Source of truth:
`src/pensioen/tax/heffingskorting.py`, met tarieven uit `config/belasting_2025.json`.
Invoer: verzamelinkomen en AOW-status. Uitvoer: ouderenkorting; afhankelijk:
netto inkomen, vermogen en resultaten. De 2025-afbouwgrens was ten onrechte
€40.888 en is €45.308, met maximum €2.035 en afbouw 15%.
De officiële fiscale informatie (§21.4.1) en live OLA bevestigen dit.
Bij €41.752 inkomen stijgt de korting van €1.906 naar €2.035.

OLA toont voor die alleenstaande AHK €1.114; de gepubliceerde tabelformule in
de app geeft €1.113. Voor partner 1 bij €36.568 toont OLA €1.277 tegenover
€1.278 in de app; partner 2 bij €26.568 geeft in beide €1.536. De verschillen
zijn geregistreerd als tolerantieverschil, zonder de formules op voorbeelden
bij te stellen. IB, IB/PVV vóór kortingen, ouderenkorting en de vastgelegde
alleenstaandeouderenkorting komen exact overeen. De interne OLA-afronding van
de AHK is nog niet volledig verklaard; geen claim van exacte overeenstemming.

Directe grensgevallen en hogere regressies staan in `tests/test_ola_aow_pensioen.py`.
Bronfixtures: `tc_2025_016` en `tc_2025_017` (raw en generated normalized).
Opnamen met screenshots, HTML, tekst en bewijshashes:
- `validatie/ola/runs/ola_2025_alleen_pensioen/20260907T020716Z-ac166246`
- `validatie/ola/runs/ola_2025_paar_pensioen/20260907T021049Z-11c421fc`

Voor deze nieuwe API-tests wordt het fiscale jaarbedrag uit `accountant_detail`
tegen de OLA-aanslag getoetst met €1 tolerantie. Het verschil tussen fiscale
jaaraanslag en opgetelde maandbedragen wordt afzonderlijk begrensd op de maximale
centenafronding van belasting en korting per persoon/maand. Bij de alleenstaande
is de maandsom €4.448,04, tegenover €4.448 als fiscale jaaruitkomst.
Oude API-baselines en externe bronverwachtingen blijven ongewijzigd.

De tool-export bewaart nu ook alleenstaandeouderenkorting en een expliciete
spaargeldfractie, zodat de bestaande normalisatieketen Decimal-tekst accepteert.
Dit betreft stap **Resultaten**: uitsluitend projectie van bronbedragen en
invoerverhouding, geen nieuw fiscaal rekenpad.

## Functionele wijzigingen

- **Box 1** — source of truth: `belasting_engine.py` en `belasting_2025.json`.
  Invoer: belastbaar inkomen, geboortedatum en jaartarieven. Uitvoer: IB en premies.
  Reguliere schijfgrens €38.441, oudere cohortgrens €40.502 (geboren vóór 1946).
  De premiegrens is voor beide cohorten €38.441.
- **Heffingskortingen** — source of truth: `heffingskorting.py` en jaarconfig.
  Invoer: arbeidsinkomen en opbouwsegmenten; uitvoer: arbeidskorting.
  De drie officiële opbouwsegmenten vervangen de maximumkorting bij lagere lonen.
  Het AOW-AHK-maximum is exact €1.536 in de config; een benaderde factor mag
  door afronding geen onterechte extra euro opleveren.
- Beide stappen leveren hun uitkomsten aan netto inkomen, vermogen en resultaten.
  UI, API en rapportage krijgen geen zelfstandige fiscale formules.
  Nieuwe optionele configvelden blijven behouden bij tariefperiode-resolutie.
  Alleen de 2025-config activeert aanslagafronding; andere jaarconfigs behouden
  hun bestaande gedrag.

## Afronding en bewijs

Bij OLA is de IB de som van de per schijf naar beneden afgeronde belasting.
€45.003 loon onderscheidt dit van afronding van de totaalsom:
€3.140 + €2.459 = €5.599; afronding van de ongeronde som zou €5.600 geven.

Premies worden afzonderlijk naar beneden getoond, maar het premietotaal wordt
uit de ongeronde premiebedragen berekend en daarna naar beneden afgerond.
Bij €45.000 zijn de getoonde premies €6.880, €38 en €3.709, totaal €10.628.
OLA vermeldt expliciet dat de getoonde onderdelen door afronding kunnen afwijken
van het totaal. Het engineveld `totaal_premies` is daarom leidend.

Heffingskortingen worden na de volledige formule naar boven afgerond.
Bedragen blijven Decimal; maandverdeling en cashflow blijven centen gebruiken.
Maandsommen kunnen daardoor enkele centen van het fiscale jaartotaal verschillen.

Bronnen:
- [Ouderenkorting 2025, paragraaf 21.4.1](https://www.belastingdienst.nl/wps/wcm/connect/fisin/fisin2025/heffingskortingen)
- [Belastingberekening 2025](https://www.belastingdienst.nl/wps/wcm/connect/fisin/fisin2025/belastingberekening)
- [Premies 2025](https://www.belastingdienst.nl/wps/wcm/connect/fisin/fisin2025/premie_volksverzekeringen)
- [Arbeidskorting 2025](https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/prive/inkomstenbelasting/heffingskortingen_boxen_tarieven/heffingskortingen/arbeidskorting/tabel-arbeidskorting-2025)
- [Algemene heffingskorting 2025](https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/prive/inkomstenbelasting/heffingskortingen_boxen_tarieven/heffingskortingen/algemene_heffingskorting/tabel-algemene-heffingskorting-2025)
- [Afronding van heffingskortingen](https://kennisgroepen.belastingdienst.nl/publicaties/kg202202214-afronding-heffingskortingen/)
  beschrijft afronding in het voordeel van belastingplichtige; bijzondere
  situaties met gedeeltelijke belasting-/premieplicht vallen buiten deze cases.

## Herhaling en regressies

Recepten: `config/ola/verified/`. Uitvoer met screenshots, bronbedragen, hashes en
exacte engine-invoer staat onder `validatie/ola/runs/`.
Gebruik `python3 -m tools.ola batch config/ola/verified --controleur NAAM --headless`.
De volledige batch is op 7 september opnieuw uitgevoerd met exitcode 0:
alle vijf recepten PASS, zonder invoerverschillen. Herhaalde pensioenruns:
`20260907T021636Z-693610e4` (alleen) en `20260907T021801Z-dfbd8dbb` (partners).

Directe grens-, cohort-, afrondings- en hogere engine-tests:
`tests/test_ola_fiscale_correcties.py`. Externe brongevallen:
`tc_2025_013`, `tc_2025_014`, `tc_2025_015` in raw en generated normalized.
De eerdere OLA-bedragen en bestaande API-baseline zijn niet aangepast.
De xfails voor de twee OLA-cases zijn verwijderd; de API-test houdt dezelfde €1-tolerantie.

Validatie: 372 tests geslaagd, één bekende AOW-bronafwijking strikt xfail.
De bouwsteen-/contractpoort slaagt (219 tests); 12 fixtures hebben geen
normalisatiedrift en de React-productiebuild slaagt. Ruff en mypy zijn niet
geïnstalleerd en zijn niet uitgevoerd. De strikte externe validatie geeft nog
exitcode 1 vanwege de geregistreerde oude cases 008/010/011; hun referenties
zijn niet vervangen door nieuwe engine-uitkomsten.
De oude externe validatieset houdt afzonderlijke afwijkingen; actuele bedragen
en reviewreden staan in het afwijkingenregister. Dit is geen volledige fiscale
certificering: AOW-deeljaren, werkende AOW-gerechtigden, box 3 en eigen woning
zijn niet met deze vijf cases opnieuw live gevalideerd. De volgende stap is
de bruto AOW-bron (inclusief halfjaarwijzigingen en vakantiegeld) toetsen aan SVB
en daarna dezelfde fiscale cases herhalen. De oude gemengde referenties met
woning/vermogen zijn hiermee nog niet inhoudelijk afgedaan.

Zie [de toolhandleiding](../tools/ola/README.md) voor installatie en bronopname.
