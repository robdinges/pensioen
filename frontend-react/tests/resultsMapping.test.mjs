import assert from "node:assert/strict";
import test from "node:test";

import {
  buildRequestPayload,
  buildScenarioComparisonRequest,
  selectCurrentComparison,
  createEmptyValues,
  selectYearRows,
  computeStopmomentSummary,
  buildScenarioDecisionCards,
  buildScenarioDecisionAdvice,
} from "../src/planner/plannerCore.js";

test("resultaatmapping verwart positief netto inkomen niet met negatieve cashflow", () => {
  const rows = selectYearRows({
    jaren: [{
      jaar: 2031,
      jaar_samenvatting: {
        bruto: "114968.58",
        belasting: "35162.76",
        netto: "-12000",
        netto_inkomen: "79805.82",
        netto_cashflow: "-12000",
        netto_per_maand: "-1000",
        vermogen_einde_jaar: "-50000",
      },
    }],
  });

  assert.equal(rows[0].netto, 79805.82);
  assert.equal(rows[0].cashflow, -12000);
  assert.equal(rows[0].vermogenEinde, -50000);
});

test("jaarlijkse P1-component behoudt frequentie in het API-verzoek", () => {
  const payload = buildRequestPayload({
    posts: [{
      id: "jaarinkomen",
      type: "loon",
      titel: "Jaarinkomen P1",
      values: {
        ...createEmptyValues("loon"),
        persoon: "P1",
        bedrag: "12000",
        bedrag_type: "bruto",
        frequentie: "jaarlijks",
      },
    }],
    persoonNaam: "P1",
    geboortedatum: "1980-01-01",
    jaarVan: "2027",
    jaarTot: "2027",
    scenarioNaam: "Frequentietest",
    heeftPartner: false,
    partnerNaam: "",
    partnerGeboortedatum: "",
  });

  assert.equal(payload.scenario.componenten[0].frequentie, "jaarlijks");
  assert.equal(payload.scenario.componenten[0].bedrag, "12000");
});

test("stopmomentsummary markeert het eerste tekortjaar en geeft een klantvriendelijke beoordeling", () => {
  const summary = computeStopmomentSummary([
    { jaar: 2029, bruto: 60000, belasting: 15000, netto: 45000, cashflow: 2500, vermogenEinde: 70000 },
    { jaar: 2030, bruto: 62000, belasting: 16000, netto: 46000, cashflow: -500, vermogenEinde: 68000 },
    { jaar: 2031, bruto: 61000, belasting: 17000, netto: 44000, cashflow: -1500, vermogenEinde: 66000 },
  ]);

  assert.equal(summary.firstShortfallYear, 2030);
  assert.equal(summary.stopMomentLabel, "Interen op vermogen");
  assert.equal(summary.wealthAt80, null);
  assert.match(summary.summaryText, /negatief/);
});

test("scenario decision cards compare active plan, alternative and best case in one compact set", () => {
  const cards = buildScenarioDecisionCards({
    scenario_resultaten: [
      { scenario_naam: "Actief", netto_per_maand_mediaan: 5000, vermogen_op_80: 800000 },
      { scenario_naam: "Eerder stoppen", netto_per_maand_mediaan: 4300, vermogen_op_80: 720000 },
      { scenario_naam: "Minder werken", netto_per_maand_mediaan: 5600, vermogen_op_80: 920000 },
    ],
    beste_scenario_netto: { scenario_naam: "Minder werken" },
  }, "Actief", "Eerder stoppen");

  assert.equal(cards.length, 3);
  assert.equal(cards[0].label, "Actieve keuze");
  assert.equal(cards[1].label, "Alternatief");
  assert.equal(cards[2].label, "Alternatief");
  assert.equal(cards[1].nettoDelta, -700);
  assert.equal(cards[2].scenarioName, "Minder werken");
});

test("decision advice turns scenario differences into a clear recommendation", () => {
  const advice = buildScenarioDecisionAdvice({
    scenario_resultaten: [
      { scenario_naam: "Actief", netto_per_maand_mediaan: 5000, vermogen_op_80: 800000 },
      { scenario_naam: "Eerder stoppen", netto_per_maand_mediaan: 4300, vermogen_op_80: 720000 },
      { scenario_naam: "Minder werken", netto_per_maand_mediaan: 5600, vermogen_op_80: 920000 },
    ],
    beste_scenario_netto: { scenario_naam: "Minder werken" },
  }, "Actief", "Eerder stoppen");

  assert.match(advice, /Minder werken/);
  assert.match(advice, /€ 600/);
  assert.match(advice, /vrije cashflow/);
});

test('plancontrole benoemt negatief vermogen en gebruikt het echte 80-jaar', () => {
  const rows = [
    {jaar:2030,cashflow:0,vermogenEinde:-5000},
    {jaar:2040,cashflow:100,vermogenEinde:8000},
    {jaar:2041,cashflow:100,vermogenEinde:9000},
  ];
  const summary = computeStopmomentSummary(rows, '1960-04-15');
  assert.equal(summary.wealthAt80,8000);
  assert.equal(summary.stopMomentLabel,'Vermogen negatief');
  assert.doesNotMatch(summary.summaryText,/hele horizon positief|Haalbaar/);
  assert.equal(computeStopmomentSummary(rows,'1980-01-01').wealthAt80,null);
});

test('drie kaarten zijn drie unieke scenarios; advies benoemt de nadelen', () => {
  const comparison = {scenario_resultaten:[
    {scenario_naam:'Actief',netto_per_maand_mediaan:5000,vermogen_op_80:800000,aantal_tekortjaren:0},
    {scenario_naam:'Alternatief',netto_per_maand_mediaan:4300,vermogen_op_80:720000,aantal_tekortjaren:1},
    {scenario_naam:'Risico',netto_per_maand_mediaan:5600,vermogen_op_80:-50000,aantal_tekortjaren:10},
  ],beste_scenario_netto:{scenario_naam:'Risico'}};
  const cards = buildScenarioDecisionCards(comparison,'Actief','Alternatief');
  assert.equal(new Set(cards.map(c=>c.scenarioName)).size,3);
  assert.equal(cards[2].vermogenDelta,-850000);
  const advice = buildScenarioDecisionAdvice(comparison,'Actief','Alternatief');
  assert.match(advice,/600,00/);
  assert.match(advice,/vrije cashflow/);
  assert.match(advice,/10 tekortjaren/);
  assert.match(advice,/50\.000,00/);
  assert.doesNotMatch(advice,/aanbevolen|gelijkwaardig/);
  assert.equal(buildScenarioDecisionCards(comparison,'Verdwenen','Alternatief').length,0);
});

test('twee scenarioresultaten worden niet verdubbeld en gelijke cashflow is geen gelijkwaardigheid', () => {
  const comparison = {scenario_resultaten:[
    {scenario_naam:'Actief',netto_per_maand_mediaan:5000,vermogen_op_80:800000,aantal_tekortjaren:0},
    {scenario_naam:'Anders',netto_per_maand_mediaan:5000,vermogen_op_80:100000,aantal_tekortjaren:3},
  ],beste_scenario_netto:{scenario_naam:'Actief'}};
  assert.equal(buildScenarioDecisionCards(comparison,'Actief','Anders').length,2);
  assert.doesNotMatch(buildScenarioDecisionAdvice(comparison,'Actief','Anders'),/gelijkwaardig|aanbevolen/);
});


test('comparison request sends three unique plans and stale advice is rejected', () => {
  const resolve = id => ({scenario:{naam:id},persoon1:{geboortedatum:'1960-01-01'},persoon2:null});
  const request = buildScenarioComparisonRequest(['a','b','c'],resolve,2025,2040);
  assert.deepEqual(request.scenarios.map(item=>item.naam),['a','b','c']);
  const result = {inputSignature:JSON.stringify(request)};
  assert.equal(selectCurrentComparison(result,request),result);
  assert.equal(selectCurrentComparison(result,{...request,jaar_tot:2041}),null);
  assert.equal(selectCurrentComparison(result,{...request,scenarios:[{naam:'gewijzigd'}]}),null);
  assert.throws(()=>buildScenarioComparisonRequest(['a','b','a'],resolve,2025,2040),/verschillende/);
  assert.equal(buildScenarioComparisonRequest(['a','b',''],resolve,2025,2040).scenarios.length,2);
});

test('outside horizon wealth is unknown and a temporary monthly deficit remains visible', () => {
  const summary = computeStopmomentSummary(selectYearRows({jaren:[{
    jaar:2040,jaar_samenvatting:{netto_cashflow:'0',vermogen_einde_jaar:'100'},
    maanden:[{vermogen_einde_maand:'-20'},{vermogen_einde_maand:'100'}],
  }]}),'1960-01-01');
  assert.equal(summary.stopMomentLabel,'Vermogen negatief');
  assert.equal(summary.wealthAt80,100);
  const comparison={vermogen80Beschikbaar:false,scenario_resultaten:[
    {scenario_naam:'a',netto_per_maand_mediaan:100,vermogen_op_80:0},
    {scenario_naam:'b',netto_per_maand_mediaan:200,vermogen_op_80:0},
  ],beste_scenario_netto:{scenario_naam:'b'}};
  assert.equal(buildScenarioDecisionCards(comparison,'a','b')[1].vermogenDelta,null);
  assert.match(buildScenarioDecisionAdvice(comparison,'a','b'),/niet beschikbaar/);
});

test('opbouw configuration survives scenario and household hydration', async () => {
  const {createScenarioSnapshot,normalizeScenarioSnapshot,normalizeHouseholdSnapshot}=await import('../src/planner/plannerCore.js');
  const opbouwDraft={keuze:{premie_per_maand:'800',modus:'aannames'},berekening:{scenario:{naam:'Bestand',componenten:[]}}};
  const snapshot=createScenarioSnapshot({posts:[],opbouwDraft});
  assert.deepEqual(normalizeScenarioSnapshot(JSON.parse(JSON.stringify(snapshot))).opbouwDraft,opbouwDraft);
  const household=normalizeHouseholdSnapshot({scenarios:[{id:'a',naam:'Plan'}],activeScenarioId:'a',scenarioSnapshots:{a:snapshot}});
  assert.deepEqual(household.activeScenarioSnapshot.opbouwDraft,opbouwDraft);
});
