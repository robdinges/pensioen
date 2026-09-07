# Vermogen: rendement per liquide post

Primaire stap: **Vermogen**. Eigenaar: `calculations/vermogen_engine.py`,
`maandrendement` en `LiquidePortefeuille`. Classificatie: twee codebugs.
De gesplitste renteberekening sloeg negatieve rendementen over; React middelde
postrendementen ongewogen en de hoofdengine negeerde de individuele rendementen.

Invoer: saldo, groei_pct, aanschafdatum, verkoopdatum, jaarlijkse_inleg per
spaar-/beleggingspost en maandelijkse huishoudcashflow. Uitvoer: rendement,
inleg, post- en kassaldi per maand. De cashflowengine orkestreert. API,
accountantoutput en rapporten presenteren deze bedragen; React middelt geen
rendementen meer. Box 3 ontvangt de actuele belaste saldi per 1 januari via de
bestaande belastingmodule; er is geen nieuwe fiscale formule toegevoegd.

## Rekenafspraken

- Geld en samengestelde groei gebruiken Decimal. Maandrendement is
  `(1 + jaarpercentage / 100) ** (1 / 12) - 1`; afronding per post/maand op
  centen met ROUND_HALF_UP. Jaarpercentage moet eindig zijn en minimaal -100%.
  Bij -100% resteert bij de eerste rendementsperiode geen saldo.
- Per liquide post is `groei_pct` leidend, ook bij expliciet nul. De engine
  bewaart werkelijke saldi tussen maanden/jaren; aanschafwaarden worden niet
  telkens opnieuw gewaardeerd. Voor een aanschaf vóór de prognosestart wordt
  de beginwaarde eenmaal doorgerekend met de bestaande 365,25-dagenconventie.
- Start-/sluitdatums zijn inclusief. Rendement en inleg zijn naar actieve dagen
  binnen de maand verdeeld. Een toekomstige beginwaarde is een externe
  toevoeging in de startmaand, zichtbaar als eenmalige ontvangst. Voer deze
  niet nogmaals als incidentele ontvangst in. Het is geen interne overboeking.
- `jaarlijkse_inleg` per post wordt per actieve maand/dag verdeeld en aan het
  maandeinde toegevoegd, zonder rendement in diezelfde maand. Het is externe
  inleg naast de opgegeven huishoudcashflow: geen automatische reservering uit
  reeds ingevoerd loon. Vermijd dubbele invoer van dezelfde geldstroom.
- Algemene overschotten/tekorten worden aan het maandeinde verwerkt, naar rato
  van aanwezige postsaldi. Kasgeld wordt bij tekorten eerst aangesproken.
  Zonder postsaldo wordt een overschot gelijk verdeeld over nog actieve posten.
  Een tekort groter dan het vermogen blijft als negatieve kas zichtbaar;
  daarop ontstaat geen positief of negatief beleggingsrendement. Nieuwe inleg
  en inkomsten vullen zo'n tekort eerst aan.
- Sluiten van een liquide post verplaatst het resterende saldo naar renteloos
  kasgeld. Er verdwijnt geen geld en er volgt geen rendement/inleg na sluiting.
  Een afzonderlijke verkoopprijs van een liquide post wordt niet verwerkt;
  dit pad sluit op actuele boekwaarde. Fysieke bezittingen en hun verkooplogica
  zijn buiten deze wijziging gehouden. Kasgeld telt mee als spaargeld voor Box 3;
  bijzondere vrijstellingen bij het sluiten zijn niet gemodelleerd.

## Compatibiliteit en presentatie

Zonder liquide posten blijft het bestaande scenario-rendementpad beschikbaar,
nu ook met negatieve rendementen. Met liquide posten zijn de posten leidend,
ook als zij nul saldo hebben of pas later beginnen; gespiegeld legacy
startvermogen wordt niet dubbel of te vroeg toegevoegd.

Het nieuwe optionele `VermogensItem.jaarlijkse_inleg` behoudt oude aanvragen:
`null`/ontbrekend gebruikt scenario-inleg als fallback per soort. Zodra voor
een soort expliciete post-inleg aanwezig is (ook 0), vervalt die fallback voor
die soort. React stuurt expliciete inleg per liquide post. Bestaande globale
rendementsvelden blijven leesbaar, maar worden bij liquide posten genegeerd.

Maandoutput bevat `gebruikte_tarieven.vermogen.posten`, `kas`, `bron` en
`inleg_per_maand`. Accountantoutput aggregeert de werkelijke inleg; de
`vermogen_rijen` sluiten beginstand + cashflow = eindstand aan. Het oude
algemene maandrendement is bij postberekeningen niet van toepassing;
`rendement_bron` geeft de juiste interpretatie. Huishoudcashflow exclusief
externe inleg behoudt zijn bestaande betekenis.

## Borging

- `tests/test_vermogen_rendement_regressie.py`: verlies, rendementsgrenzen,
  verschillende rekeningen, inleg, dagen, sluiting, tekorten, geldbehoud,
  jaarovergang, Box-3-broninvoer, accountantoutput en API-contract.
- `frontend-react/tests/vermogenPayload.test.mjs`: individuele rendementen,
  bedragen, datums en inleg blijven intact; geen frontendgemiddelde.
- Raw `tc_2025_018` bevat onder `metadata.regressies_vermogen` twee expliciet
  **interne** acceptatiegevallen, geen nieuwe OLA-waarnemingen. Normalisatie
  bewaart deze regressies. Bestaande externe belastingverwachtingen en
  API-baselines zijn ongewijzigd.
- Acceptatie zonder inleg/uitgaven/Box 3: €100.000 tegen -10% eindigt na een
  jaar op ongeveer €90.000; €1.000 tegen 1% plus €99.000 tegen 5% op ongeveer
  €104.960 (centenafronding per maand).

Validatie: 407 Python-tests geslaagd, drie bestaande strikte xfails; coverage
56%. Bouwsteen-/contractpoort: 237 geslaagd en dezelfde drie xfails. Alle
14 fixtures zonder normalisatiedrift. Elf frontendtests en productiebuild
slagen. De strikte fiscale pipeline blijft exitcode 1 geven voor de bestaande
008/010/011-afwijkingen, met ongewijzigde bedragen. Ruff en mypy zijn niet
geïnstalleerd; die controles zijn niet uitgevoerd.
