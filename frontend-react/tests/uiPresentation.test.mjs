import assert from "node:assert/strict";
import { after, test } from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const server = await createServer({
  server: { middlewareMode: true, hmr: false, ws: false, watch: null },
  logLevel: "error",
});
after(() => server.close());

const { default: ResultsSection } = await server.ssrLoadModule("/src/components/ResultsSection.jsx");
const { default: ContextTopBar } = await server.ssrLoadModule("/src/components/layout/ContextTopBar.jsx");
const SectionHeader = ({ title }) => React.createElement("h2", null, title);

test("stale results remain identifiable and preserve engine assumptions as text", () => {
  const props = {
    SectionHeader,
    jaarRows: [{ jaar: 2026, bruto: 40000, belasting: 6000, netto: 34000, cashflow: -1000, vermogenEinde: 99000 }],
    euro: (value) => `EUR ${value}`,
    aannames: ["Tarieven <2026> doorgerold"],
  };
  const stale = renderToStaticMarkup(React.createElement(ResultsSection, { ...props, calculationStatus: "stale" }));
  assert.match(stale, /eerdere berekening/);
  assert.match(stale, /Tarieven &lt;2026&gt; doorgerold/);
  assert.match(stale, /EUR -1000/);
  const fresh = renderToStaticMarkup(React.createElement(ResultsSection, { ...props, calculationStatus: "fresh" }));
  assert.doesNotMatch(fresh, /eerdere berekening/);
});

test("storage failure never claims the plan was saved", () => {
  const html = renderToStaticMarkup(React.createElement(ContextTopBar, {
    autosaveStatus: "error", canCalculate: false, calculationStatus: "idle",
  }));
  assert.match(html, /Niet opgeslagen/);
  assert.doesNotMatch(html, /Opgeslagen in deze browser/);
  assert.match(html, /disabled/);
});


const { default: PostCard } = await server.ssrLoadModule("/src/components/PostCard.jsx");
const { TYPE_CONFIG, FIELD_META } = await server.ssrLoadModule("/src/planner/plannerCore.js");
const { default: ScenarioComparison } = await server.ssrLoadModule("/src/components/ScenarioComparison.jsx");

test("empty income dates explicitly mean no start or end", () => {
  const html = renderToStaticMarkup(React.createElement(PostCard, {
    post: { id: "x", type: "pensioen", titel: "Pensioen", values: { startdatum: "", einddatum: "", bedrag: "1000" } },
    config: TYPE_CONFIG.pensioen, fieldMeta: FIELD_META, onChange() {}, onDelete() {},
  }));
  assert.match(html, /Geen begindatum/);
  assert.match(html, /Geen einddatum/);
});

test("assets show dated balances instead of duration fields", () => {
  const html = renderToStaticMarkup(React.createElement(PostCard, {
    post: { id: "x", type: "sparen", titel: "Sparen", values: { beginwaarde: "1000", peildatum: "2025-01-01",
      saldostanden: [{ peildatum: "2025-07-16", bedrag: "500" }] } },
    config: TYPE_CONFIG.sparen, fieldMeta: FIELD_META, onChange() {}, onDelete() {},
  }));
  assert.match(html, /Stand op 2025-07-16/);
  assert.match(html, /Nieuwe saldostand toevoegen/);
  assert.doesNotMatch(html, />Vanaf</);
  assert.doesNotMatch(html, />T\/m</);
});

test("accountant presents engine reconciliation with a shared column", async () => {
  const { default: AccountantSection } = await server.ssrLoadModule('/src/components/AccountantSection.jsx');
  const html = renderToStaticMarkup(React.createElement(AccountantSection, {
    SectionHeader, euro: (value) => `EUR ${value}`,
    resultaat: { cashflow: { jaren: [{ jaar: 2025, accountant_detail: {
      heeft_partner: true, netto_aansluiting: [{ label: 'Netto inkomen inclusief rendement',
        p1: 12000, p2: 24000, gezamenlijk: 300, huishouden: 36300 }],
    } }] } },
  }));
  assert.match(html, /Gezamenlijk \/ niet toegewezen/);
  assert.match(html, /EUR 12000/);
  assert.match(html, /EUR 24000/);
  assert.match(html, /EUR 36300/);
});

test('results show actual age-80 value and all three engine scenario deltas', () => {
  const comparisonResult = {vermogen80Beschikbaar:true,scenario_resultaten:[
    {scenario_naam:'Actief',netto_per_maand_mediaan:5000,vermogen_op_80:800000,aantal_tekortjaren:0},
    {scenario_naam:'Eerder',netto_per_maand_mediaan:4300,vermogen_op_80:720000,aantal_tekortjaren:2},
    {scenario_naam:'Later',netto_per_maand_mediaan:5600,vermogen_op_80:920000,aantal_tekortjaren:0},
  ],beste_scenario_netto:{scenario_naam:'Later'},klantvergelijking:{actief_scenario:'Actief',gemiddelde_van:'2040-01-01',gemiddelde_tot:'2041-12-31',horizon_van:2040,horizon_tot:2041,na_stoppen:true}};
  comparisonResult.scenario_resultaten.forEach((item,i)=>{item.klantbeeld={
    gemiddeld_over_per_maand:[5100,4400,5700][i],aantal_maanden_gemiddelde:24,
    verschil_gemiddeld_over_per_maand:[0,-700,600][i],verschil_vermogen_op_80:[0,-80000,120000][i],
    vermogen_op_80:item.vermogen_op_80,laagste_buffer:50000,laagste_buffer_maand:'2040-02',
    grootste_jaartekort:2000,grootste_jaartekort_jaar:2040,jaren_interen:i===1?2:0,jaren_negatief_vermogen:0,
    jaarregels:[{jaar:2040,over_na_uitgaven:-2000,interen:2000,vermogen_eind:50000,negatief_vermogen:false}],
  }});
  const html = renderToStaticMarkup(React.createElement(ResultsSection, {
    SectionHeader, euro:value=>`EUR ${value}`, calculationStatus:'fresh',
    geboortedatum:'1960-01-01',activeScenarioName:'Actief',compareScenarioName:'Eerder',comparisonResult,
    jaarRows:[{jaar:2040,bruto:0,netto:0,cashflow:0,vermogenEinde:800000},
              {jaar:2041,bruto:0,netto:0,cashflow:0,vermogenEinde:900000}],
  }));
  assert.match(html,/persoon 1 80 wordt: EUR 800000/);
  assert.match(html,/EUR 700 minder/);
  assert.match(html,/EUR 600 meer/);
  assert.match(html,/EUR 80000 minder/);
  assert.match(html,/EUR 120000 meer/);
  assert.match(html,/2 jaren met interen/);
  assert.match(html,/EUR 4400/);
  assert.match(html,/Laagste verwachte vermogensbuffer/);
  assert.match(html,/Rekendetails/);
});

test('scenario comparison shows each person age at the last workday', () => {
  const html = renderToStaticMarkup(React.createElement(ScenarioComparison, {
    activeScenarioName: 'Actief', euro: value => `EUR ${value}`,
    comparisonResult: {
      klantvergelijking: { actief_scenario: 'Actief' },
      scenario_resultaten: [{ scenario_naam: 'Actief', klantbeeld: {
        jaarregels: [], laatste_werkdagen: { P1: '2030-03-15', P2: '2031-06-22' },
        leeftijden_op_laatste_werkdag: { P1: '67j 3 m', P2: '66j 0 m' },
      } }],
    },
  }));
  assert.match(html, /Laatste werkdag P1: 2030-03-15/);
  assert.match(html, /Laatste werkdag P1: 2030-03-15 \(67j 3 m\)/);
  assert.match(html, /Laatste werkdag P2: 2031-06-22/);
  assert.match(html, /Laatste werkdag P2: 2031-06-22 \(66j 0 m\)/);
});

test('scenario comparison derives ages when an older API response lacks age data', () => {
  const html = renderToStaticMarkup(React.createElement(ScenarioComparison, {
    activeScenarioName: 'Actief', euro: value => `EUR ${value}`,
    geboortedatum: '1963-03-15', partnerGeboortedatum: '1965-06-22',
    comparisonResult: {
      klantvergelijking: { actief_scenario: 'Actief' },
      scenario_resultaten: [{ scenario_naam: 'Actief', klantbeeld: {
        jaarregels: [], laatste_werkdagen: { P1: '2030-03-14', P2: '2031-06-22' },
      } }],
    },
  }));
  assert.match(html, /Laatste werkdag P1: 2030-03-14 \(66j 11 m\)/);
  assert.match(html, /Laatste werkdag P2: 2031-06-22 \(66j 0 m\)/);
});

test('scenario selection offers a distinct optional third plan', async () => {
  const {default:ScenarioSection} = await server.ssrLoadModule('/src/components/ScenarioSection.jsx');
  const html = renderToStaticMarkup(React.createElement(ScenarioSection, {
    SectionHeader,scenarios:[{id:'a',naam:'Actief'},{id:'b',naam:'Tweede'},{id:'c',naam:'Derde'}],
    activeScenarioId:'a',activeScenarioName:'Actief',compareScenarioId:'b',thirdScenarioId:'c',
    comparisonResult:null,
  }));
  assert.match(html,/Derde scenario \(optioneel\)/);
  const thirdSelect = html.slice(html.indexOf('Derde scenario (optioneel)'),html.indexOf("Vergelijk scenario&#x27;s"));
  assert.match(thirdSelect,/value="c" selected=""/);
  assert.doesNotMatch(thirdSelect,/value="a"|value="b"/);
});

test('opbouw simulator makes assumptions, premium and source explicit', async () => {
  const {default:Simulator}=await server.ssrLoadModule('/src/components/PensioenopbouwSimulator.jsx');
  const props={baseRequest:{scenario:{naam:'Plan',componenten:[{categorie:'pensioen_inkomen',persoon:'P1',omschrijving:'Fonds'}]},jaar_van:2025,jaar_tot:2040},apiBase:'/api/v1',euro:v=>`EUR ${v}`,onDraft(){}};
  const html=renderToStaticMarkup(React.createElement(Simulator,{...props,draft:{keuze:{pensioen_index:'0',premie_per_maand:'800'}}}));
  assert.match(html,/Pensioenopbouw na stoppen/);
  assert.match(html,/P1 · Fonds/);
  assert.match(html,/werkgeversdeel/);
  assert.match(html,/geen belastingaftrek/);
  assert.match(html,/EUR 800/);
  assert.match(html,/Bewaar configuratie als JSON/);
  const confirmed=renderToStaticMarkup(React.createElement(Simulator,{...props,draft:{keuze:{modus:'uitvoerder'}}}));
  assert.match(confirmed,/Datum uitvoerdersberekening/);
  assert.doesNotMatch(confirmed,/type="range"/);
});

const { default: ActuarielePensioenSimulator } = await server.ssrLoadModule("/src/components/ActuarielePensioenSimulator.jsx");

test("automatic pension estimate starts from scenario and exposes paid-up assumptions", () => {
  const html = renderToStaticMarkup(React.createElement(ActuarielePensioenSimulator, {
    baseRequest: { persoon1: { naam: "Test" }, scenario: { naam: "Stop op 65", componenten: [
      { persoon: "P1", categorie: "pensioen_inkomen", omschrijving: "Oud fonds", begindatum: "2027-01-01", bedrag: "1000" },
    ] } }, apiBase: "/api/v1", euro: String, onDraft: () => {},
    draft: { actuarieel: { rekenrente_pct: 0, opgebouwde_regelingen: [
      JSON.stringify(["P1", "Oud fonds", "2027-01-01", "1000"])
    ] } },
  }));
  assert.match(html, /Stop op 65/);
  assert.match(html, /Bereken mijn drie opties/);
  assert.match(html, /Oud fonds.*al opgebouwd/);
  assert.match(html, /type="checkbox" checked=""/);
  assert.doesNotMatch(html, /type="date"/);
  assert.match(html, /Je hoeft geen offerte/);
  assert.match(html, /value="0"/);
});

const { PensioenPostStatus } = await server.ssrLoadModule("/src/components/ActuarielePensioenSimulator.jsx");
test("partial pension estimate identifies every post without suggesting complete advice", () => {
  const html = renderToStaticMarkup(React.createElement(PensioenPostStatus, {
    euro: value => 'EUR ' + value,
    raming: { volledig: false, posten: [
      {index: 1, naam: 'Tijdelijk fonds', bedrag: '500', bedrag_type: 'bruto', frequentie: 'maandelijks',
       begindatum: '2027-01-01', einddatum: '2030-12-31', status: 'niet_berekend', reden: 'Einddatum 2030-12-31: tijdelijk pensioen.'},
      {index: 2, naam: 'Geldig fonds', bedrag: '1000', status: 'berekend', reden: 'Drie opties beschikbaar.'},
      {index: 3, naam: 'Lopend fonds', bedrag: '100', status: 'ongewijzigd', reden: 'Al ingegaan.'},
    ]},
  }));
  for (const label of ['Onvolledige raming', 'Tijdelijk fonds', 'Geldig fonds', 'Lopend fonds',
    'Nog niet berekend', 'Berekend', 'Ongewijzigd', '2030-12-31', 'geen totaaladvies']) {
    assert.ok(html.includes(label), label);
  }
});

const { ActuarieleJaarvergelijking } = await server.ssrLoadModule("/src/components/ActuarielePensioenSimulator.jsx");
test("annual pension comparison shows engine tax deltas and AOW transition without recalculating", () => {
  const row={jaar:2027,aow_fase:'AOW-overgangsjaar',bruto_inkomen:'12000',box1_na_kortingen:'1234',
    box3:'56',belastingverschil:'-789',belastingdruk:'12.3',belastingdrukverschil_pp:'-4.5',
    netto_inkomen:'10766',netto_verschil:'321',voortzettingspremie:'444',over_na_uitgaven:'555',vermogen:'666'};
  const html=renderToStaticMarkup(React.createElement(ActuarieleJaarvergelijking,{
    data:{persoon:'Test',aow_datum:'2027-01-01',referentie:'Wachten zonder doorbetalen',
      varianten:[{naam:'Direct pensioen',jaren:[row]}]},euro:value=>'EUR '+value}));
  for (const text of ['AOW-overgangsjaar','EUR -789','EUR 1234','EUR 56','EUR 444','EUR 555','EUR 666','12,3%','-4,5 pp','Wachten zonder doorbetalen']) {
    assert.ok(html.includes(text),text);
  }
});

test("unchanged pension assumption remains visible in a complete comparison", () => {
  const html=renderToStaticMarkup(React.createElement(PensioenPostStatus,{
    euro:String,raming:{volledig:true,posten:[{index:0,naam:'Fonds',bedrag:'500',
      begindatum:'2027-01-01',einddatum:'2030-12-31',status:'ongewijzigde_aanname',
      reden:'Oorspronkelijke invoer behouden.'}]}}));
  assert.match(html,/Gelijk in alle drie varianten/);
  assert.match(html,/meerjarenoverzicht en de belastingberekening/);
  assert.doesNotMatch(html,/Onvolledige raming/);
});

test("applied pension variant offers return to source instead of only a disabled calculate button",()=>{
  const props={baseRequest:{persoon1:{naam:'Test'},scenario:{naam:'Variant',componenten:[]}},
    euro:String,onDraft:()=>{},onChooseAgain:()=>{},
    draft:{toegepast:[{persoon:'P1',variant:'Direct pensioen',bronScenarioId:'base'}]},
    scenarios:[{id:'base',naam:'Oorspronkelijk'}]};
  const html=renderToStaticMarkup(React.createElement(ActuarielePensioenSimulator,props));
  assert.match(html,/Andere variant kiezen/);
  assert.doesNotMatch(html,/bij oudere keuzes/);
  const legacy=renderToStaticMarkup(React.createElement(ActuarielePensioenSimulator,{
    ...props,draft:{toegepast:[{persoon:'P1',variant:'Direct pensioen'}]}}));
  assert.match(legacy,/Kies je oorspronkelijke scenario/);
  assert.match(legacy,/Oorspronkelijk/);
});

test("household scenario shows both choices and allows reselecting a stored modern choice",()=>{
  const html=renderToStaticMarkup(React.createElement(ActuarielePensioenSimulator,{
    baseRequest:{persoon1:{naam:'Partner Een'},persoon2:{naam:'Partner Twee'},scenario:{naam:'Stopplan',componenten:[]}},
    euro:String,onDraft:()=>{},onViewPlan:()=>{},
    draft:{toegepast:[{persoon:'P1',variant:'Direct pensioen',basisPosten:[]},{persoon:'P2',variant:'Doorbetalen',basisPosten:[]}]}
  }));
  for(const text of ['Pensioenkeuzes in Stopplan','Partner Een','Partner Twee','Direct pensioen','Doorbetalen',
    'Bekijk het gezamenlijke meerjarenplan','Vergelijk opnieuw voor deze persoon']) assert.ok(html.includes(text),text);
  assert.doesNotMatch(html,/Kies je oorspronkelijke scenario/);
});
