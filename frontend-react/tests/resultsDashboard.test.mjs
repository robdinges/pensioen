import assert from "node:assert/strict";
import { after, test } from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const server = await createServer({ server: { middlewareMode: true, hmr: false, ws: false, watch: null }, logLevel: "error" });
after(() => server.close());
const { default: ResultsSection } = await server.ssrLoadModule("/src/components/ResultsSection.jsx");
const props = {
  SectionHeader: ({ title }) => React.createElement("h2", null, title),
  euro: value => `EUR ${value}`, calculationStatus: "fresh", activeScenarioName: "Basis",
  onStepSelect() {},
  jaarRows: [
    { jaar: 2026, bruto: 45000, netto: 36000, belasting: 9000, cashflow: -2400, vermogenEinde: 97600 },
    { jaar: 2027, bruto: 50000, netto: 40000, belasting: 10000, cashflow: 1600, vermogenEinde: 99200 },
  ],
};
const render = overrides => renderToStaticMarkup(React.createElement(ResultsSection, { ...props, ...overrides }));

test("dashboard shows the first year rather than a misleading whole-period average", () => {
  const html = render();
  const cards = html.slice(html.indexOf('class="dashboard-kpis"'), html.indexOf('<strong>Plancontrole:'));
  for (const text of ["Netto inkomen", "EUR 36000", "EUR 9000", "EUR 97600", "Aan te vullen uit vermogen", "EUR 2400", "tekort in 2026"]) assert.ok(cards.includes(text), text);
  assert.doesNotMatch(cards, /EUR 38000|EUR 40000/);
  assert.match(html, /value="2026" selected=""/);
  assert.match(html, /value="2027"/);
  assert.match(html, /Eerste tekortjaar: 2026/);
  assert.match(html, /Alle jaarbedragen bekijken/);
  assert.match(html, /EUR -2400/); // Signed source cashflow remains in the detailed table.
});

test("negative wealth and outdated results remain explicit", () => {
  const jaarRows = [{ ...props.jaarRows[0], vermogenEinde: -100 }];
  assert.match(render({ jaarRows }), /Vermogen negatief/);
  assert.match(render({ jaarRows }), /EUR -100/);
  const stale = render({ jaarRows, calculationStatus: "stale" });
  assert.match(stale, /eerdere berekening/);
  assert.match(stale, /Bereken opnieuw/);
  assert.doesNotMatch(stale, /Het plan vraagt aanpassing/);
});

test("comparison controls exclude active and duplicate third scenarios and expose loading errors", () => {
  const html = render({
    scenarios: [{ id: "a", naam: "Basis" }, { id: "b", naam: "Eerder" }, { id: "c", naam: "Later" }],
    activeScenarioId: "a", compareScenarioId: "b", thirdScenarioId: "c", isComparing: true,
    comparisonError: "Vergelijking mislukt. Probeer opnieuw.",
  });
  const controls = html.slice(html.indexOf('class="dashboard-comparison-controls"'));
  const third = controls.slice(controls.indexOf("Derde scenario"), controls.indexOf("Scenario’s berekenen"));
  assert.doesNotMatch(controls, /option value="a"/);
  assert.doesNotMatch(third, /option value="b"/);
  assert.match(third, /value="c" selected=""/);
  assert.match(controls, /button type="button" disabled=""/);
  assert.match(controls, /role="alert"/);
  assert.match(controls, /Vergelijking mislukt/);
});

test("empty dashboard prompts for input and single-plan dashboard explains scenario creation", () => {
  const empty = render({ jaarRows: [] });
  assert.match(empty, /Inkomen &amp; vermogen invullen/);
  assert.doesNotMatch(empty, /dashboard-kpis|<svg/);
  assert.match(render(), /Maak een kopie van je plan/);
  assert.match(render(), /Scenario’s beheren/);
});

test("both interactive charts expose selected-year buttons and the matching detail row", () => {
  const html = render();
  assert.equal((html.match(/role="group"/g) || []).length, 2);
  assert.equal((html.match(/aria-pressed="true"/g) || []).length, 4);
  assert.equal((html.match(/aria-pressed="false"/g) || []).length, 4);
  assert.match(html, /role="button" aria-pressed="false" aria-label="Bekijk 2027/);
  assert.equal((html.match(/class="chart-selected-year"/g) || []).length, 2);
  const detail = html.slice(html.indexOf('aria-label="Details gekozen jaar"'), html.indexOf('class="dashboard-scenarios"'));
  for (const value of ['Jaardetails · 2026', 'EUR 45000', 'EUR 9000', 'EUR 36000', 'EUR -2400', 'EUR 97600']) assert.ok(detail.includes(value), value);
  assert.doesNotMatch(detail, /EUR 99200/);
});

test("single-year charts remain selectable without invalid coordinates", () => {
  const html = render({ jaarRows: [props.jaarRows[1]] });
  assert.equal((html.match(/aria-pressed="true"/g) || []).length, 4);
  assert.doesNotMatch(html, /aria-pressed="false"|NaN|Infinity/);
  assert.match(html, /Jaardetails · 2027/);
});

const { default: YearIncomeDetails } = await server.ssrLoadModule('/src/components/YearIncomeDetails.jsx');
test('income details select the requested year and preserve engine totals and shared amounts', () => {
  const html = renderToStaticMarkup(React.createElement(YearIncomeDetails, {
    jaar: 2027, euro: value => `EUR ${value}`, jaren: [
      {jaar: 2026, accountant_detail: {jaar_pen_p1: '999'}},
      {jaar: 2027, accountant_detail: {heeft_partner: true, jaar_pen_p1: '1234.56', jaar_pen_p2: '0',
        netto_aansluiting: [{label: 'Engine totaal', p1: '100', p2: '200', gezamenlijk: '-5', huishouden: '295'}]}},
    ],
  }));
  for (const text of ['EUR 1234.56', 'EUR 0', 'Persoon 2', 'EUR -5', 'EUR 295', 'Niet beschikbaar', 'Engine totaal']) assert.ok(html.includes(text), text);
  assert.doesNotMatch(html, /EUR 999/);
});
test('missing income details stay unknown and single-person output hides the partner column', () => {
  const renderIncome = jaren => renderToStaticMarkup(React.createElement(YearIncomeDetails, {jaar: 2027, jaren, euro: String}));
  assert.match(renderIncome([]), /niet beschikbaar/);
  const html = renderIncome([{jaar: 2027, accountant_detail: {heeft_partner: false}}]);
  assert.doesNotMatch(html, /Persoon 2/);
  assert.match(html, /De aansluiting naar netto inkomen is niet beschikbaar/);
});
