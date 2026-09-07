import assert from 'node:assert/strict';
import test from 'node:test';
import { compactSession, saveSession } from '../src/planner/sessionStorage.js';

test('stores inputs for all households and scenarios without duplicated calculation output', () => {
  const result = { data: 'x'.repeat(2_000_000) };
  const scenario = { posts: [{ titel: 'Sparen', values: { beginwaarde: '1000' } }],
    importPreviewP1: [{ bedrag: '2000' }], resultaat: result, calculationStatus: 'fresh', inputSignatureAtCalculation: 'old' };
  const original = { ...scenario, households: [{ id: 'h' }], activeHouseholdId: 'h',
    householdPreferences: { h: { persoonNaam: 'Test' } },
    householdSnapshots: { h: { ...scenario, comparisonResult: result, scenarioSnapshots: { a: scenario, b: scenario } } } };
  assert.ok(JSON.stringify(original).length > 5_000_000);
  const compact = compactSession(original);
  assert.ok(JSON.stringify(compact).length < 2000);
  assert.deepEqual(compact.householdSnapshots.h.scenarioSnapshots.b.posts, scenario.posts);
  assert.deepEqual(compact.importPreviewP1, scenario.importPreviewP1);
  assert.equal(compact.householdSnapshots.h.scenarioSnapshots.a.resultaat, null);
  assert.equal(compact.calculationStatus, 'idle');
  assert.equal(original.resultaat, result);
  let saved;
  saveSession(original, { setItem(key, value) {
    assert.equal(key, 'pensioen-ui-session-v1');
    if (value.length > 5000) throw Object.assign(new Error(), { name: 'QuotaExceededError' });
    saved = value;
  } });
  assert.deepEqual(JSON.parse(saved), compact);
});

test('storage errors remain visible and never delete the previous session', () => {
  const error = Object.assign(new Error(), { name: 'SecurityError' });
  assert.throws(() => saveSession({}, { setItem() { throw error; }, removeItem() { assert.fail('must not delete'); } }), /./);
});
