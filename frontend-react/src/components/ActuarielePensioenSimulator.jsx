import {useState} from 'react';
import ScenarioComparison from './ScenarioComparison';

export default function ActuarielePensioenSimulator({baseRequest,apiBase,euro,draft={},onDraft}) {
  const settings=draft.actuarieel || {};
  const persoon=settings.persoon || 'P1';
  const posten=(baseRequest.scenario?.componenten || []).map((c,index)=>({...c,index}))
    .filter(c=>c.persoon===persoon && c.categorie==='pensioen_inkomen');
  const postKey=post=>JSON.stringify([post.persoon,post.omschrijving,post.begindatum,post.bedrag]);
  const opgebouwd=settings.opgebouwde_regelingen || [];
  const optional=value=>value === '' || value == null ? null : value;
  const keuze={persoon,reeds_opgebouwde_posten:posten.filter(post=>opgebouwd.includes(postKey(post))).map(post=>post.index),
    rekenrente_pct:optional(settings.rekenrente_pct),startleeftijd_opbouw:optional(settings.startleeftijd_opbouw),
    premie_kostenopslag_pct:optional(settings.premie_kostenopslag_pct)};
  const request={berekening:baseRequest,keuze};
  const signature=JSON.stringify(request);
  const [result,setResult]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const current=result?.signature===signature?result.data:null;
  const update=(key,value)=>onDraft({...draft,actuarieel:{...settings,[key]:value}});
  const run=async()=>{
    setBusy(true);setError('');
    try {
      const response=await fetch(`${apiBase}/simulaties/actuarieel`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request)});
      const data=await response.json();
      if(!response.ok)throw new Error(Array.isArray(data.detail)?data.detail.map(x=>x.msg).join(' '):data.detail || 'Berekening mislukt.');
      setResult({signature,data});
    }catch(e){setError(e.message);}finally{setBusy(false);}
  };
  const r=current?.raming;
  return <section className="opbouw-simulator">
    <h3>Wat krijg ik als ik eerder stop?</h3>
    <p>We gebruiken je stopdatum, pensioenbedragen en oorspronkelijke pensioendatums uit <strong>{baseRequest.scenario?.naam}</strong>. Je hoeft geen offerte of drie nieuwe bedragen in te vullen.</p>
    <label className="field inline-field"><span>Voor wie?</span><select value={persoon} onChange={e=>onDraft({...draft,actuarieel:{...settings,persoon:e.target.value,opgebouwde_regelingen:[]}})}>
      <option value="P1">{baseRequest.persoon1?.naam || 'Persoon 1'}</option>
      {baseRequest.persoon2?<option value="P2">{baseRequest.persoon2.naam || 'Persoon 2'}</option>:null}
    </select></label>
    <p>{posten.length} pensioenposten gevonden. AOW blijft op de AOW-datum ingaan.</p>
    <p className="notice">We schatten gemiste opbouw en de gevolgen van langer uitkeren. Standaardaannames zijn gelijkmatige opbouw vanaf 25 jaar en 3% rekenrente. Controleer onder Aannames welke pensioenen al volledig opgebouwd zijn.</p>
    <button type="button" disabled={busy || !posten.length} onClick={run}>{busy?'Actuarieel berekenen…':'Bereken mijn drie opties'}</button>
    <details className="scenario-technical"><summary>Aannames aanpassen (optioneel)</summary>
      <p>De AG2024-sterftetafel weegt overleving mee. De rekenrente, opbouwhistorie en opslag zijn modelaannames en kunnen afwijken van jouw regeling.</p>
      <div className="opbouw-fields">
        <label className="field"><span>Rekenrente % (standaard 3)</span><input type="number" min="0" max="10" step="0.25" value={settings.rekenrente_pct ?? ''} onChange={e=>update('rekenrente_pct',e.target.value)} /></label>
        <label className="field"><span>Pensioenopbouw gestart op leeftijd (standaard 25)</span><input type="number" min="18" max="40" value={settings.startleeftijd_opbouw ?? ''} onChange={e=>update('startleeftijd_opbouw',e.target.value)} /></label>
        <label className="field"><span>Opslag op berekende premie % (standaard 10)</span><input type="number" min="0" max="50" value={settings.premie_kostenopslag_pct ?? ''} onChange={e=>update('premie_kostenopslag_pct',e.target.value)} /></label>
      </div>
      <p>Vink aan als het geïmporteerde bedrag <strong>al opgebouwd</strong> is, bijvoorbeeld bij een vorige werkgever. Dan passen we alleen een eventuele vervroeging toe, geen korting voor ontbrekende opbouw.</p>
      {posten.map(post=><label className="field" key={post.index}><span><input type="checkbox" checked={keuze.reeds_opgebouwde_posten.includes(post.index)} onChange={e=>update('opgebouwde_regelingen',e.target.checked?[...opgebouwd,postKey(post)]:opgebouwd.filter(key=>key!==postKey(post)))} /> {post.omschrijving} — al opgebouwd</span></label>)}
    </details>
    {error?<p className="error" role="alert">{error}</p>:null}
    {result&&!current?<p className="notice">Scenario of aannames gewijzigd. Bereken opnieuw voor een actuele schatting.</p>:null}
    {r?<>
      <p className="notice"><strong>Raming, geen vastgestelde aanspraak.</strong> Laatste werkdag uit je scenario: {r.laatste_werkdag}. Eerste volledige maand na stoppen: {r.vanaf_stoppen}. Opbouw vanaf {r.startleeftijd_opbouw} jaar; rekenrente {Number(r.rekenrente_pct).toLocaleString('nl-NL')}%.</p>
      <div className="scenario-cards">
        <article className="scenario-card"><h3>1. Direct pensioen ontvangen</h3><p>Vanaf {r.vanaf_stoppen}</p><strong>{euro(Number(r.totaal_direct_bruto_maand))} bruto per maand</strong><p>Minder opbouw én een lagere uitkering doordat het pensioen langer wordt uitgekeerd.</p></article>
        <article className="scenario-card"><h3>2. Wachten, niet doorbetalen</h3><p>Vanaf de oorspronkelijke pensioendatum per regeling</p><strong>{euro(Number(r.totaal_wachten_bruto_maand))} bruto per maand</strong><p>Je bouwt minder op, maar het pensioen wordt niet vervroegd. Tot de ingangsdatum overbrug je uit andere inkomsten of vermogen.</p></article>
        <article className="scenario-card"><h3>3. Premie doorbetalen, later pensioen</h3><p>Vanaf de oorspronkelijke pensioendatum per regeling</p><strong>{euro(Number(r.totaal_doorbetalen_bruto_maand))} bruto per maand</strong><p>Actuarieel geschatte premie bij de start: <strong>{euro(Number(r.premie_per_maand_bij_start))} per maand</strong>. Totaal in de berekening: {euro(Number(r.totale_premie))}.</p><small>Inclusief {Number(r.premie_kostenopslag_pct)}% modelopslag, zonder belastingaftrek. Dit is niet de premieofferte van een fonds.</small></article>
      </div>
      <p>De bedragen bij wachten en doorbetalen zijn het totaal zodra alle getoonde regelingen lopen. Bij verschillende ingangsdatums zie je de fasering hieronder en in de jaaropbouw.</p>
      <details open className="scenario-technical"><summary>Zo ontstaat je geschatte pensioen</summary><div className="table-wrap"><table>
        <thead><tr><th>Pensioen</th><th>Oorspronkelijke datum</th><th>Uit scenario bruto p/m</th><th>Na gemiste opbouw</th><th>Direct bij stoppen</th><th>Rentegevoeligheid direct</th><th>Geschatte premie p/m</th></tr></thead>
        <tbody>{r.regelingen.map(row=><tr key={row.index}><td>{row.naam}<br/><small>{row.verdere_opbouw_aangenomen?'Verdere opbouw aangenomen':'Reeds opgebouwd'}</small></td><td>{row.normaal_vanaf}</td><td>{euro(Number(row.import_bruto_maand))}</td><td>{euro(Number(row.wachten_bruto_maand))}<br/><small>{(Number(row.opbouwfactor)*100).toFixed(1)}% behouden</small></td><td>{euro(Number(row.direct_bruto_maand))}<br/><small>Vervroegingsfactor {Number(row.vervroegingsfactor).toFixed(3)}</small></td><td>{euro(Number(row.direct_laag))}–{euro(Number(row.direct_hoog))}</td><td>{euro(Number(row.premie_bruto_maand))}<br/><small>Gevoeligheid {euro(Number(row.premie_laag))}–{euro(Number(row.premie_hoog))}</small></td></tr>)}</tbody>
      </table></div><p>De gevoeligheid gebruikt rekenrentes {r.gevoeligheid_rentes_pct.map(x=>`${Number(x)}%`).join(', ')}. Dit is geen betrouwbaarheidsinterval.</p></details>
      {r.overgeslagen.length?<p className="notice">{r.overgeslagen.join(' ')}</p>:null}
      <ScenarioComparison comparisonResult={current.vergelijking} activeScenarioName="Direct pensioen bij stoppen" euro={euro} />
      <details className="scenario-technical"><summary>Rekenmethode en bronnen</summary><p>{r.bron_sterfte}. <a href="https://www.actuarieelgenootschap.nl/kennisbank/prognosetafel-ag2024-2" target="_blank" rel="noreferrer">Open AG2024-bron</a>.</p><ul>{r.aannames.map((x,i)=><li key={i}>{x}</li>)}</ul></details>
    </>:null}
  </section>;
}
