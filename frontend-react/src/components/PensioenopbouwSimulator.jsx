import { useState } from "react";
import ScenarioComparison from "./ScenarioComparison";

const defaults = {modus:"aannames",pensioen_index:"",laatste_werkdag:"",doorwerken_tot:"",pensioen_vanaf:"",
  premie_per_maand:"",pensioen_doorwerken:"",pensioen_zonder:"",pensioen_met:"",bron:"",brondatum:""};
const fields = [
  ["laatste_werkdag","Eerder stoppen: laatste werkdag","date"],
  ["doorwerken_tot","Doorwerken: laatste werkdag","date"],
  ["pensioen_vanaf","Pensioen ontvangen vanaf (alle opties)","date"],
  ["pensioen_doorwerken","Pensioen bij doorwerken · bruto per maand","number"],
  ["pensioen_zonder","Pensioen zonder doorbetalen · bruto per maand","number"],
  ["pensioen_met","Pensioen met doorbetalen · bruto per maand","number"],
  ["premie_per_maand","Zelf te betalen volledige premie per maand","number"],
];

export default function PensioenopbouwSimulator({baseRequest,apiBase,euro,draft={},onDraft}) {
  const form={...defaults,...draft.keuze};
  const basis=draft.berekening || baseRequest;
  const [result,setResult]=useState(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const change=(key,value)=>onDraft({...draft,keuze:{...form,[key]:value}});
  const candidates=(basis?.scenario?.componenten || []).map((component,index)=>({component,index}))
    .filter(({component})=>component.categorie==='pensioen_inkomen');
  const selected=candidates.find(({index,component})=>String(index)===String(form.pensioen_index)
    && (!form.pensioen_bron || form.pensioen_bron===JSON.stringify([component.omschrijving,component.persoon])));
  const payload={berekening:basis,keuze:{...form,pensioen_index:Number(form.pensioen_index),brondatum:form.brondatum || null}};
  const signature=JSON.stringify(payload);
  const current=result?.signature===signature ? result.data : null;
  const save=()=>{
    const blob=new Blob([JSON.stringify({versie:1,berekening:basis,keuze:form},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='pensioenopbouw-case.json';a.click();URL.revokeObjectURL(url);
  };
  const load=async event=>{
    try {
      const file=event.target.files?.[0];if(!file)return;
      if(file.size>2_000_000)throw new Error('Het configuratiebestand is te groot.');
      const data=JSON.parse(await file.text());
      if(data.versie!==1 || !Array.isArray(data.berekening?.scenario?.componenten) || !data.berekening.scenario.componenten.every(c=>c && typeof c.categorie==='string' && typeof c.persoon==='string' && typeof c.omschrijving==='string') || typeof data.berekening.scenario.naam!=='string' || !data.keuze || typeof data.keuze!=='object')throw new Error('Dit is geen pensioenopbouw-configuratie versie 1.');
      onDraft({berekening:data.berekening,keuze:data.keuze});setResult(null);setError('');
    }catch(e){setError(e.message);}finally{event.target.value='';}
  };
  const run=async event=>{
    event.preventDefault();setBusy(true);setError('');
    try {
      const response=await fetch(`${apiBase}/simulaties/pensioenopbouw`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const data=await response.json();
      if(!response.ok)throw new Error(Array.isArray(data.detail)?data.detail.map(x=>x.msg).join(' '):data.detail || 'Simulatie mislukt.');
      setResult({signature,data});
    }catch(e){setError(e.message);}finally{setBusy(false);}
  };
  return <section className="scenario-comparison opbouw-simulator">
    <h3>Pensioenopbouw na stoppen</h3>
    <p>Vergelijk doorwerken, stoppen zonder premie en stoppen met zelf doorbetalen. Je geeft het pensioen per optie op; de app leidt dit niet af uit de premie.</p>
    <p className="notice">Deze simulator rekent hele maanden: laatste werkdag aan het einde van een maand, pensioen vanaf de eerste dag. Kies één doorlopend pensioen. Andere pensioenposten blijven zoals ingevoerd. De premie loopt vanaf de dag na eerder stoppen tot de dag vóór de pensioenuitkering begint. Neem ook een eventueel werkgeversdeel mee. Er wordt geen belastingaftrek voor deze premie toegepast.</p>
    {draft.berekening ? <p className="notice">Je gebruikt de basisinvoer uit een opgeslagen configuratie ({basis.scenario.naam}). <button type="button" className="ghost" onClick={()=>onDraft({keuze:{...form,pensioen_index:"",pensioen_bron:""}})}>Gebruik het actieve plan</button></p> : <p>Basis: {basis?.scenario?.naam} · {basis?.jaar_van}–{basis?.jaar_tot}</p>}
    <form onSubmit={run}>
      <div className="household-controls">
        <label className="field"><span>Soort invoer</span><select value={form.modus} onChange={e=>change('modus',e.target.value)}>
          <option value="aannames">Verkennen met aannames</option><option value="uitvoerder">Gegevens van mijn uitvoerder</option>
        </select></label>
        <label className="field"><span>Welke pensioenpost?</span><select required value={selected ? String(form.pensioen_index) : ''} onChange={e=>{
          const match=candidates.find(x=>String(x.index)===e.target.value);
          onDraft({...draft,keuze:{...form,pensioen_index:e.target.value,pensioen_bron:match?JSON.stringify([match.component.omschrijving,match.component.persoon]):''}});
        }}><option value="">Kies een pensioenpost</option>{candidates.map(({component,index})=><option key={index} value={index}>{component.persoon} · {component.omschrijving}</option>)}</select></label>
      </div>
      {!candidates.length ? <p className="notice">Voeg eerst een pensioenpost en het bijbehorende werkinkomen toe aan je plan.</p> : null}
      <div className="opbouw-fields">{fields.map(([key,label,type])=><label className="field" key={key}><span>{label}</span><input required type={type} min={type==='number'?'0':undefined} step={type==='number'?'0.01':undefined} value={form[key]} onChange={e=>change(key,e.target.value)} /></label>)}</div>
      {form.modus==='aannames' ? <label className="field"><span>Verken de premie: {form.premie_per_maand===''?'nog niet ingevuld':euro(Number(form.premie_per_maand))} per maand</span><input aria-label="Premie verkennen" type="range" min="0" max={Math.max(5000,Number(form.premie_per_maand)||0)} step="25" value={Number(form.premie_per_maand)||0} onChange={e=>change('premie_per_maand',e.target.value)} /></label> : null}
      <div className="household-controls"><label className="field"><span>Bron / toelichting {form.modus==='aannames'?'(optioneel)':''}</span><input required={form.modus==='uitvoerder'} value={form.bron} onChange={e=>change('bron',e.target.value)} /></label><label className="field"><span>Datum uitvoerdersberekening</span><input type="date" required={form.modus==='uitvoerder'} value={form.brondatum || ""} onChange={e=>change('brondatum',e.target.value)} /></label></div>
      <button type="submit" disabled={busy || !selected}>{busy?'Simuleren…':'Vergelijk pensioenopbouw'}</button>
    </form>
    <div className="household-controls"><button type="button" className="ghost" onClick={save}>Bewaar configuratie als JSON</button><label className="field"><span>Open opgeslagen configuratie</span><input type="file" accept=".json,application/json" onChange={load} /></label></div>
    {error ? <p className="error" role="alert">{error}</p>:null}
    {result && !current ? <p className="notice">Invoer gewijzigd. Simuleer opnieuw voor actuele bedragen.</p>:null}
    {current ? <>
      <p className="notice"><strong>{form.modus==='aannames'?'Verkenning met aannames':'Door jou ingevulde uitvoerdersgegevens'}</strong>{form.bron?` · ${form.bron}`:''}{form.brondatum?` · ${form.brondatum}`:''}</p>
      <div className="kpis">
        <div className="kpi"><span>Totaal zelf te betalen premie</span><strong>{euro(Number(current.opbouw.totale_premie))}</strong></div>
        <div className="kpi"><span>Extra netto pensioen per maand door doorbetalen</span><strong>{current.opbouw.extra_netto_pensioen_per_maand==null?'Niet beschikbaar':euro(Number(current.opbouw.extra_netto_pensioen_per_maand))}</strong><small>Gemiddelde volledige pensioenmaanden, effect na box 1; exclusief rendement.</small></div>
        <div className="kpi"><span>Omslagpunt tegenover niet doorbetalen</span><strong>{Number(current.opbouw.totale_premie)===0?'Geen premie-uitgave':current.opbouw.omslag_maand?`${current.opbouw.omslag_maand} · leeftijd ${current.opbouw.omslag_leeftijd}`:'Niet bereikt binnen de periode'}</strong><small>Cumulatieve netto cashflow, inclusief berekend rendement; blijft tot de horizon niet negatief.</small></div>
      </div>
      <p className="notice">Extra geld nodig tot de pensioenstart, ten opzichte van doorwerken: zonder doorbetalen {euro(Number(current.opbouw.extra_geld_tot_pensioen_zonder))}; met doorbetalen {euro(Number(current.opbouw.extra_geld_tot_pensioen_met))}. Inclusief het effect op belasting en berekend rendement; een negatief verschil betekent minder geld nodig.</p>
      <details><summary>Aannames en beperkingen</summary><ul>{current.aannames.map(x=><li key={x}>{x}</li>)}</ul></details>
      <ScenarioComparison comparisonResult={current.vergelijking} activeScenarioName="Doorwerken" euro={euro} />
      <details><summary>Controleer het omslagpunt per maand</summary><div className="table-wrap"><table><thead><tr><th>Maand</th><th>Cumulatief verschil met − zonder doorbetalen</th></tr></thead><tbody>{current.opbouw.maandvergelijking.map(row=><tr key={row.maand}><td>{row.maand}</td><td>{euro(Number(row.cumulatief_verschil))}</td></tr>)}</tbody></table></div></details>
    </>:null}
  </section>;
}
