// Berekeningsresultaten blijven in het tabblad; alleen invoer wordt bewaard.
export const SESSION_KEY = 'pensioen-ui-session-v1';

export function compactSession(snapshot) {
  if (!snapshot || typeof snapshot !== 'object' || Array.isArray(snapshot)) return snapshot;
  const compact = { ...snapshot, resultaat: null, comparisonResult: null,
    calculationStatus: 'idle', inputSignatureAtCalculation: '' };
  for (const collection of ['householdSnapshots', 'scenarioSnapshots']) {
    if (snapshot[collection] && typeof snapshot[collection] === 'object') {
      compact[collection] = Object.fromEntries(Object.entries(snapshot[collection])
        .map(([id, value]) => [id, compactSession(value)]));
    }
  }
  return compact;
}

export function saveSession(snapshot, storage = window.localStorage) {
  storage.setItem(SESSION_KEY, JSON.stringify(compactSession(snapshot)));
}
