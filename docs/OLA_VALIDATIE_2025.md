# Live OLA-referenties voor 2025

## Rekenfix 6 september 2026

De twee hieronder beschreven codebugs zijn gecorrigeerd. Box 1 gebruikt nu
€38.441 voor het reguliere cohort, met behoud van €40.502 voor geboren vóór 1946.
De premiegrens is voor beide cohorten €38.441. De arbeidskorting gebruikt de
drie officiële opbouwsegmenten uit de 2025-tabel. Andere belastingjaren zijn
niet aangepast.

| Case | OLA (ongewijzigd) | App na fix | Resterend verschil |
| --- | ---: | ---: | ---: |
| Alleenstaand €45.000 loon | €8.735 | €8.738,02 | +€3,02 |
| Partners €45.000 + €30.000 | €11.210 | €11.213,21 | +€3,21 |

De oorspronkelijke verschillen van −€31,20 en −€326,19 zijn teruggebracht tot
afrondingsschuld. OLA geeft hele euro's; het bestaande enginecontract rondt op
centen. Geen afrondingsformule is uit slechts twee eindbedragen afgeleid.
De OLA-vergelijking blijft FAIL bij de ongewijzigde tolerantie van €1.
De nieuwe API-brongevallen zijn strikt xfail zolang deze aansluiting ontbreekt;
aanvullende regressietests bewaken de gecorrigeerde componenten en centenuitkomst.

Functionele slices: **Box 1**, source of truth `belasting_engine.py`, invoer
belastbaar inkomen/geboortedatum en 2025-config, uitvoer IB en premies;
**Heffingskortingen**, source of truth `heffingskorting.py`, invoer arbeidsinkomen
en opbouwsegmenten, uitvoer arbeidskorting. Beide werken door naar netto inkomen,
vermogen en resultaten; UI/API voegen geen formules toe. De optionele
configvelden blijven behouden bij tariefperiode-resolutie.

Directe en hogere regressietests: `tests/test_ola_fiscale_correcties.py`.
Nieuwe externe raw/normalized-cases: `tc_2025_013` en `tc_2025_014`.
De oude externe bronbedragen en API-baseline zijn niet gewijzigd. Het
afwijkingenregister vermeldt de gewijzigde uitkomsten expliciet, inclusief
verslechterde aansluiting van oude referenties na correctie van de premiegrens.

Validatie: 354 tests geslaagd, 3 strikt xfail. De externe strikte validatie
blijft niet groen door de afzonderlijk geregistreerde referentie-/AOW-schuld.
Werkende AOW-gerechtigden en hun arbeidskorting vallen buiten deze twee cases.

## Oorspronkelijke bevindingen (vóór de fix)

Opgenomen op 5 september 2026 in de officiële opleidingsomgeving,
formulier IH2025 versie 1, blanco casus. Fictieve alleenstaande geboren
12 april 1970, €45.000 loon, geen vermogen/woning/aftrekposten,
geen loonheffing of voorlopige aanslag. Volledig jaar Nederlands verzekerd.

| Onderdeel | OLA | Pensioenapp | Pensioen minus OLA |
| --- | ---: | ---: | ---: |
| Inkomstenbelasting vóór kortingen | €5.598 | €4.994,86 | −€603,14 |
| IB en premies vóór kortingen | €16.226 | €16.193,66 | −€32,34 |
| Algemene heffingskorting | €2.017 | €2.016,44 | −€0,56 |
| Arbeidskorting | €5.474 | €5.473,42 | −€0,58 |
| Verschuldigde IB/PVV | €8.735 | €8.703,80 | −€31,20 |

De externe vergelijking is **FAIL**, bij een tolerantie van €1 per veld.
Een groene softwaresuite betekent dus niet dat de fiscale aansluiting correct is.
Bewijs, exacte invoer en engine-output staan lokaal in
`validatie/ola/runs/ola_2025_alleen_werkend/20260905T190329Z-8b9fe8db/`.

## Eerst te onderzoeken rekenwijziging

De huidige `config/belasting_2025.json` gebruikt €40.502 als eerste
schijfgrens en premiegrens, ook voor deze niet-AOW-gerechtigde.
De [Belastingdienst-tabel voor 2025](https://www.belastingdienst.nl/wps/wcm/connect/fisin/fisin2025/belastingberekening)
onderscheidt €38.441 voor deze leeftijdsgroep en €40.502 voor geboren vóór 1946.
De [uitleg over box 1](https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/prive/inkomstenbelasting/heffingskortingen_boxen_tarieven/boxen_en_tarieven/box_1/box_1)
noemt €38.441 als premiegrens voor 2025.
Deze onjuiste grenzen verklaren het tegengestelde verschil tussen IB en premies;
afronding op hele euro's moet afzonderlijk worden onderzocht.

Dit is een bevinding, nog geen rekenfix. Behandel de correctie als bouwsteen
**Box 1**, source of truth `tax/belasting_engine.py` en belastingconfig/loader.
Neem eerst directe tests op voor beide geboortecohorten en premiegrenzen,
voeg de externe testcase toe volgens het regressieprotocol, normaliseer die
en borg het resultaat via het hogere enginepad. Wijzig geen baseline om
deze afwijking te verbergen.

## Dekking

De alleenstaande-case is op 6 september 2026 automatisch herhaald, met dezelfde
uitkomsten. De definitieve selectors identificeren resultaatvelden op hun DOM-id,
niet op een vooraf bekend bedrag. Bewijs van deze herhaling:
`validatie/ola/runs/ola_2025_alleen_werkend/20260906T143000Z-738356db/`.

Ook een gezamenlijk aangifte doend paar is op 6 september live vastgelegd:
geboortedata 12 april 1970 en 15 mei 1972, lonen €45.000 en €30.000,
geen vermogen/woning/aftrekposten/voorheffingen. OLA geeft €8.735 voor P1 en
€2.475 voor P2: samen **€11.210**. De pensioenapp geeft **€10.883,81**;
het huishoudverschil is **−€326,19**.

Bij P2 komen IB en premies vóór kortingen exact overeen (€10.746).
De arbeidskorting wijkt echter af: **OLA €5.304, pensioenapp €5.599**.
De vereenvoudigde arbeidskorting geeft bij dit inkomen ten onrechte het maximum.
Dit is een afzonderlijke vervolgslice **Heffingskortingen**, source of truth
`tax/heffingskorting.py` en de jaartarieven. Borg de oplopende inkomenssegmenten
met directe grenswaardetests en een regressietest op het huishoudpad.

De partnercase is ook volledig automatisch herhaald, met dezelfde uitkomsten:
`validatie/ola/runs/ola_2025_paar_werkend_zonder_vermogen/20260906T143702Z-19f4954c/`.
Beide recepten onder `config/ola/verified/` zijn daarmee live opgenomen én
herhaald. De vergelijking blijft terecht FAIL zolang de fiscale afwijkingen bestaan.

De overige configuraties met pensioen/AOW, vermogen en eigen woning zijn
invoersjablonen en nog niet live gevalideerd. Hun aanwezigheid is geen bewijs
van fiscale dekking. De vastgelegde afwijkingen zijn niet automatisch gerepareerd.

Bediening en reproduceerbare opdrachten: [tools/ola/README.md](../tools/ola/README.md).
