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
