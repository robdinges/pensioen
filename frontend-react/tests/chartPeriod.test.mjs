import assert from 'node:assert/strict';
import { test } from 'node:test';
import { selectChartPeriod } from '../src/planner/chartPeriod.js';
const rows = [2025, 2026, 2027].map(jaar => Object.freeze({ jaar, netto: '-123.45' }));
test('chart period includes boundaries and preserves original engine rows', () => {
  const selected = selectChartPeriod(rows, '2026', '2027');
  assert.deepEqual(selected.map(row => row.jaar), [2026, 2027]);
  assert.equal(selected[0], rows[1]);
  assert.equal(selected[0].netto, '-123.45');
  assert.deepEqual(selectChartPeriod(rows, 2026, 2026), [rows[1]]);
});
test('empty, reset and obsolete period selections are safe', () => {
  assert.deepEqual(selectChartPeriod([], '2026', '2027'), []);
  assert.deepEqual(selectChartPeriod(rows), rows);
  assert.deepEqual(selectChartPeriod(rows, '2040', '2050'), rows);
  assert.deepEqual(selectChartPeriod(rows, '2027', '2025'), rows);
});
