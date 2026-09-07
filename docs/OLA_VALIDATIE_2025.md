# OLA-validatie en rekenfix 2025

De AOW-cashflow voor 2025 gebruikt nu officiële halfjaarbedragen en betaalt
opgebouwd vakantiegeld in mei. De drie looncases komen exact overeen met OLA.
Met de nieuwe SVB-bedragen is de alleenstaande pensioencase ook exact; bij het
paar blijft €1 verschil in AHK. Tolerantie blijft €1 per vastgelegd veld.

| Actieve case | OLA IB/PVV | Pensioenapp | Verschil |
| --- | ---: | ---: | ---: |
| Alleenstaande, €45.000 loon | €8.735 | €8.735 | €0 |
| Partners, €45.000 + €30.000 loon | €11.210 | €11.210 | €0 |
| Afrondingscontrole, €45.003 loon | €8.736 | €8.736 | €0 |
| Alleenstaande, €20.192,44 AOW + €25.000 pensioen | €5.847 | €5.847 | €0 |
| Partners, ieder €13.850,18 AOW, pensioen €25.000 / €15.000 | €5.411 | €5.412 | +€1 |

IB/PVV is vóór voorheffingen en exclusief Zvw. OLA vereist hele euro’s:
AOW-formulierinvoer is expliciet €20.192 respectievelijk €13.850 per persoon.
De case en engine behouden centen; `formulierafrondingen` in het rapport legt
de conversie vast. De tool rondt geen fiscale enginegrondslag af.

## SVB-broncorrectie 7 september 2026

Primaire berekenstap: **AOW**. Source of truth:
`src/pensioen/tax/aow_engine.py::bereken_aow_uitkering_maand`, gevoed door
`aow_bedrag.periodes` in `config/belasting_2025.json`. Invoer: AOW-ingangsdatum,
jaar, maand, leefvorm en bronperiodes. Uitvoer: bruto maandcashflow inclusief
in mei betaald vakantiegeld. Afhankelijk: bruto inkomen, Box 1, heffingskortingen,
netto inkomen, vermogen en resultaten. Cashflowengine orkestreert; UI, API en
rapportage voegen geen fiscale formules toe.

Oorzaak: de oude config gebruikte het hele jaar €1.396 / €964 per maand;
de maandflow miste halfjaarwijzigingen én vakantiegeld.

| Periode | Alleenstaand p/m | Samenwonend p/m per persoon | Vakantieopbouw alleenstaand p/m | Vakantieopbouw samenwonend p/m |
| --- | ---: | ---: | ---: | ---: |
| januari–juni 2024, alleen opbouwhistorie | €1.536,03 | €1.042,10 | €76,20 | €54,44 |
| juli–december 2024, alleen opbouwhistorie | €1.564,25 | €1.061,97 | €78,34 | €55,96 |
| januari–juni 2025 | €1.580,92 | €1.081,50 | €102,46 | €73,18 |
| juli–december 2025 | €1.612,44 | €1.103,97 | €100,39 | €71,71 |

Vakantiegeld bestaat uit vaste maandbedragen, niet uit 8% van AOW. De betaling
in mei 2025 omvat mei 2024 t/m april 2025: €1.032,28 alleenstaand / €737,36 per
samenwonende bij volledige opbouw. De bruto jaarcashflow is dan €20.192,44 /
€13.850,18 per persoon. De opbouw vanaf mei 2025 wordt pas in mei 2026 betaald
(en dus niet als ontvangen inkomen in 2025 geboekt).

Primaire bronnen, gecontroleerd 7 september 2026:
- [SZW bedragen januari 2024](https://www.rijksoverheid.nl/documenten/2023/12/14/uitkeringsbedragen-per-1-januari-2024)
- [SZW bedragen juli 2024](https://open.overheid.nl/documenten/8302c040-99b9-45fb-b5db-2df56db39336/file)
- [SZW bedragen januari 2025](https://open.overheid.nl/documenten/55075c82-1c75-4d4e-9768-ac45a943c5ff/file)
- [SZW bedragen juli 2025](https://www.rijksoverheid.nl/documenten/2025/06/17/uitkeringsbedragen-per-1-juli-2025)
- [SVB vakantiegeld](https://www.svb.nl/nl/aow/bedragen-aow/vakantiegeld)
- [SVB: opbouwtijdvak van de betaling in mei 2025](https://www.svb.nl/nl/aow/nieuws/250424_vakantiegeld-valt-hoger-uit)

Directe bron-, opbouw-, dag-pro-rata- en engine-tests:
`tests/test_aow_bedragen_2025.py`. Live bronfixtures: `tc_2025_018/019`.
Recepten: `config/ola/verified/*_pensioen_svb.json`. Bronopnamen:
- alleenstaande: `20260907T071730Z-f00dd7ba`
- paar: `20260907T071800Z-42d2a6d1`

De nieuwe paarcase gebruikt P2 geboren op 15 mei 1956, zodat ook de opbouw
vanaf mei 2024 volledig is. De historische P2 (15 mei 1957) heeft gedeeltelijke
opbouw in mei 2024. Die oude case is niet gewijzigd. Bij partner 1 toont OLA
AHK €1.206 en de app €1.205; IB/PVV vóór kortingen en ouderenkorting zijn exact.
Het verschil is geregistreerd, zonder formule of tolerantie bij te stellen.

Scope: volledige AOW en een ongewijzigde leefvorm. De dag-pro-rata bij een
AOW-start wordt intern getest; fiscale AOW-deeljaren zijn nog niet live OLA
gevalideerd. Andere jaarconfigs, inclusief 2026, behouden voorlopig de oude
vlakke maandberekening zonder vakantiegeld. Tarieffallback behoudt de bestaande
waarschuwing en gebruikt geen historische periode als actueel jaar. Voor 2025
worden ontbrekende/overlappende bronperiodes geweigerd. Een expliciete afwijkende
maandbedrag-override geldt voor beide halfjaren; vaste vakantieopbouw blijft
uit de bronperiodes komen. De basisvelden bevatten januari, exclusief vakantiegeld. De instellingenpagina
toont voor 2025 beide halfjaarbedragen en licht de meibetaling toe.
De oude `pensioen_engine.bereken_aow_maand` blijft als compatibiliteitsfunctie
voor expliciete vlakke maandbedragen; de productieflow gebruikt de nieuwe eigenaar.

## Historische fiscale proef met oude AOW-invoer

De oude broncases 016/017 en recepten in `config/ola/historisch/` blijven intact.
Hun €16.752 / €11.568 jaar-AOW was gelijk aan de toenmalige engine, maar niet
gevalideerd tegen SVB. Fiscale bouwsteentests bevriezen die bruto invoer, zonder
extra vakantiegeld bovenop het jaarbedrag. Dit is een expliciet testcontract;
het valideert geen actuele SVB-cashflow. Live hervergelijking van deze recepten
met de huidige app geeft terecht `INVOER_VERSCHIL`. API-regressies 016/017 zijn
strikt xfail wegens dit bronconflict; nieuwe 018/019 toetsen de actuele API.
Oude externe verwachtingen en `api_regressie_baseline.json` zijn ongewijzigd.

## Eerdere heffingskortingcorrectie 7 september 2026

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

In de oorspronkelijke API-validatie werd het fiscale jaarbedrag uit `accountant_detail`
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
De actieve batch bevat drie looncases en twee SVB-pensioencases. Historische
recepten met oude AOW-invoer staan apart en worden niet stilzwijgend herschreven.

Directe grens-, cohort-, afrondings- en hogere engine-tests:
`tests/test_ola_fiscale_correcties.py`. Externe brongevallen:
`tc_2025_013`, `tc_2025_014`, `tc_2025_015` in raw en generated normalized.
De eerdere OLA-bedragen en bestaande API-baseline zijn niet aangepast.
De xfails voor de twee OLA-cases zijn verwijderd; de API-test houdt dezelfde €1-tolerantie.

Validatie 7 september 2026: **388 passed, 3 strict xfailed**, coverage 55%.
De drie API-xfails zijn de expliciete AOW-bronconflicten 010/016/017. De
bouwsteen-/contractpoort geeft 226 passed en dezelfde 3 xfails. Alle 14 raw-
fixtures zijn zonder normalisatiedrift; de React-productiebuild slaagt.
Streamlit AppTest opent instellingen voor 2025 en 2026 zonder exceptions en
controleert beide 2025-halfjaren inclusief centen. Ruff/mypy zijn niet
geïnstalleerd; deze controles zijn niet uitgevoerd.

De volledige live batch met vijf actieve recepten eindigt met exitcode 0;
herhaalde SVB-runs: `20260907T072305Z-6687eb84` (alleenstaande) en
`20260907T072435Z-e5e55155` (paar). Alle vastgelegde alleenstaande componenten
zijn exact; het paar houdt het hierboven geregistreerde AHK-verschil van €1.
De drie looncases blijven exact. De draaiende lokale API is herstart om de
nieuwe Python-code te laden.
De strikte externe validatie houdt de geregistreerde oude cases 008/010/011
zichtbaar; hun bronwaarden worden niet vervangen door engine-uitkomsten.

Beste vervolgstap: één gewone 2025-case met AOW-start halverwege het jaar live
in OLA opnemen. Daarmee worden dag-pro-rata, beperkte vakantieopbouw en de
fiscale overgang van werk naar AOW samen getoetst. Daarna de oude gemengde
referenties met woning/vermogen opnieuw opnemen met expliciete broninvoer.

Zie [de toolhandleiding](../tools/ola/README.md) voor installatie en bronopname.
