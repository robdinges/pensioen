export async function requestActuarialVariants(apiBase, request, fetcher = fetch) {
  const base = String(apiBase ?? '').trim().replace(/\/+$/, '');
  if (!base || /\s/.test(base) || !(/^(https?:\/\/|\/(?!\/))/.test(base))) {
    throw new Error('Het adres van de rekenservice is ongeldig. Controleer dit onder Berekeningsperiode (standaard /api/v1).');
  }
  let response;
  try {
    response = await fetcher(base + '/simulaties/actuarieel', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(request),
    });
  } catch {
    throw new Error('De rekenservice is niet bereikbaar of het adres is ongeldig. Controleer het serviceadres en probeer opnieuw.');
  }
  const body = await response.text();
  let data;
  try { data = JSON.parse(body); } catch {
    throw new Error(`De rekenservice gaf geen geldig rekenresultaat terug (HTTP ${response.status}). Je invoer is behouden. Probeer opnieuw; blijft dit gebeuren, vermeld scenario en deze HTTP-code.`);
  }
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(Array.isArray(detail) ? detail.map(x => x.msg).join(' ') :
      typeof detail === 'string' ? detail : detail?.message || `Berekening mislukt (HTTP ${response.status}).`);
  }
  if (!data.raming || (data.raming.volledig && (!data.vergelijking || !data.varianten))) {
    throw new Error('De rekenservice gaf een onvolledig antwoord. Herlaad de applicatie en bereken opnieuw.');
  }
  return data;
}
