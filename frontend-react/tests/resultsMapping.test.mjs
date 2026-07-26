import assert from "node:assert/strict";
import test from "node:test";

import {
  buildRequestPayload,
  createEmptyValues,
  selectYearRows,
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
