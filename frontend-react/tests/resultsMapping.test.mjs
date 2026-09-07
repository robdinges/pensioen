import assert from "node:assert/strict";
import test from "node:test";

import {
  buildRequestPayload,
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
  assert.equal(summary.stopMomentLabel, "Risico");
  assert.equal(summary.wealthAt80, 66000);
  assert.match(summary.summaryText, /tekort/);
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
  assert.equal(cards[1].label, "Vergelijking");
  assert.equal(cards[2].label, "Beste netto");
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
  assert.match(advice, /aanbevolen/);
});
