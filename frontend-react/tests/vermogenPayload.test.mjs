import assert from 'node:assert/strict';
import test from 'node:test';
import { buildRequestPayload } from '../src/planner/plannerCore.js';

test('sends each balance, rate, contribution and date without averaging returns', () => {
  const payload = buildRequestPayload({
    persoonNaam: 'Test', geboortedatum: '1990-01-01', jaarVan: 2025, jaarTot: 2026,
    scenarioNaam: 'Vermogen', heeftPartner: false,
    posts: [
      { type: 'sparen', titel: 'Klein', values: { beginwaarde: '1000', groei_pct: '1', inleg: '1200', startdatum: '2025-07-01', einddatum: '2026-06-30' } },
      { type: 'sparen', titel: 'Groot', values: { beginwaarde: '99000', groei_pct: '5', inleg: '2400' } },
      { type: 'beleggen', titel: 'Verlies', values: { beginwaarde: '10000', groei_pct: '-10', inleg: '0' } },
    ],
  });
  assert.equal(payload.scenario.rendement_sparen_pct, undefined);
  assert.equal(payload.scenario.rendement_beleggen_pct, undefined);
  assert.deepEqual(payload.scenario.vermogensitems.map(i => [i.aanschafwaarde, i.groei_pct, i.jaarlijkse_inleg]),
    [['1000', '1', '1200'], ['99000', '5', '2400'], ['10000', '-10', '0']]);
  assert.equal(payload.scenario.vermogensitems[0].aanschafdatum, null);
  assert.deepEqual(payload.scenario.vermogensitems[0].saldostanden, [{ peildatum: '2025-07-01', bedrag: '1000' }]);
  assert.equal(payload.scenario.vermogensitems[0].verkoopdatum, null);
});


test('balance history is passed intact and an empty reference date means planning start', () => {
  const payload = buildRequestPayload({ persoonNaam: 'Test', geboortedatum: '1990-01-01', jaarVan: 2025, jaarTot: 2026,
    scenarioNaam: 'Standen', heeftPartner: false, posts: [
      { type: 'sparen', titel: 'Spaar', values: { beginwaarde: '1000', peildatum: '', groei_pct: '2',
          saldostanden: [{ peildatum: '2025-07-16', bedrag: '500' }] } },
    ] });
  assert.deepEqual(payload.scenario.vermogensitems[0].saldostanden, [
    { peildatum: '2025-01-01', bedrag: '1000' }, { peildatum: '2025-07-16', bedrag: '500' },
  ]);
});
