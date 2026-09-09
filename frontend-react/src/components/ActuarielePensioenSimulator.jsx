import {useState} from 'react';
import {requestActuarialVariants} from '../planner/actuarialRequest.js';
import ScenarioComparison from './ScenarioComparison';

export function PensioenPostStatus({raming,euro}) {
  const labels={berekend:'Berekend',niet_berekend:'Nog niet berekend',ongewijzigd:'Ongewijzigd',ongewijzigde_aanname:'Gelijk in alle drie varianten'};
  return <>
    {!raming.volledig?<p className="notice" role="status"><strong>Onvolledige raming.</strong> De beschikbare resultaten staan per pensioen hieronder. Er is geen totaaladvies of huishoudvergelijking zolang niet alle toekomstige pensioenen berekend kunnen worden.</p>:null}
    {raming.posten?.some(p=>p.status==='ongewijzigde_aanname')?<p className="notice">Niet actuarieel berekenbare pensioenen blijven op basis van je oorspronkelijke invoer gelijk in alle drie varianten. Ze tellen mee in het meerjarenoverzicht en de belastingberekening.</p>:null}
    <div className="table-wrap"><table>
      <caption>Alle pensioenposten van de gekozen persoon</caption>
      <thead><tr><th>Pensioen</th><th>Invoer uit scenario</th><th>Status en toelichting</th></tr></thead>
      <tbody>{(raming.posten || []).map(post=><tr key={post.index}>
        <td>{post.naam}</td>
        <td>{euro(Number(post.bedrag))} {post.bedrag_type} · {post.frequentie}<br/>
          <small>Vanaf {post.begindatum || 'niet ingevuld'} · t/m {post.einddatum || 'geen einddatum'}</small>
        </td>
        <td><strong>{labels[post.status]}</strong><br/>{post.reden}</td>
      </tr>)}</tbody>
    </table></div>
  </>;
}

export function ActuarieleJaarvergelijking({data,euro}) {
  return <details open className="scenario-technical"><summary>Belasting en netto resultaat per jaar</summary>
    <p>AOW-datum van {data.persoon}: {data.aow_datum}. De fase gaat over deze persoon; bedragen zijn voor het hele huishouden.
      Verschillen zijn steeds tegenover <strong>{data.referentie}</strong>.</p>
    <p>Box 1 bevat inkomstenbelasting en volksverzekeringen na heffingskortingen. Belastingdruk is het bestaande enginepercentage:
      box 1 na kortingen plus box 3, gedeeld door bruto inclusief rendement. Netto opgegeven loon zit niet in die bruto grondslag;
      bij gemengde bruto/netto invoer is dit geen volledige belastingdruk op al je inkomsten.</p>
    <div className="table-wrap"><table>
      <thead><tr><th>Jaar / AOW-fase</th><th>Variant</th><th>Bruto inkomen excl. rendement</th>
        <th>Box 1 na kortingen</th><th>Box 3</th><th>Verschil belasting</th><th>Belastingdruk / verschil</th>
        <th>Netto inkomen</th><th>Verschil netto inkomen</th><th>Voortzettingspremie</th><th>Over na uitgaven</th><th>Vermogen eind jaar</th></tr></thead>
      <tbody>{(data.varianten[0]?.jaren || []).flatMap((jaar,index)=>data.varianten.map(variant=>{
        const row=variant.jaren[index];
        return <tr key={variant.naam+row.jaar}><td>{row.jaar}<br/><small>{row.aow_fase}</small></td>
          <td>{variant.naam}</td><td>{euro(Number(row.bruto_inkomen))}</td>
          <td>{euro(Number(row.box1_na_kortingen))}</td><td>{euro(Number(row.box3))}</td>
          <td>{euro(Number(row.belastingverschil))}</td>
          <td>{Number(row.belastingdruk).toLocaleString('nl-NL',{maximumFractionDigits:1})}%<br/>
            <small>{Number(row.belastingdrukverschil_pp).toLocaleString('nl-NL',{maximumFractionDigits:1,signDisplay:'always'})} pp</small></td>
          <td>{euro(Number(row.netto_inkomen))}</td><td>{euro(Number(row.netto_verschil))}</td>
          <td>{euro(Number(row.voortzettingspremie))}</td><td>{euro(Number(row.over_na_uitgaven))}</td><td>{euro(Number(row.vermogen))}</td></tr>;
      }))}</tbody>
    </table></div>
    <p>Een positief belastingverschil betekent meer belasting dan bij wachten zonder doorbetalen.
      De voortzettingspremie is al verwerkt in ‘Over na uitgaven’. Toekomstige belastingregels volgen de aannames van de engine.</p>
  </details>;
}

export default function ActuarielePensioenSimulator({baseRequest,apiBase,euro,draft={},onDraft,onApply,onChooseAgain,scenarios=[],preparationError="",onViewPlan}) {
  const activeSettings=draft.actuarieel || {};
  const settings={...activeSettings,...(draft.perPersoon?.[activeSettings.persoon || "P1"] || {}),persoon:activeSettings.persoon || "P1"};
  const persoon=settings.persoon || 'P1';
  const toegepast=(draft.toegepast || []).find(x=>x.persoon===persoon);
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
  const [bronId,setBronId]=useState('');
  const [result,setResult]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const current=result?.signature===signature?result.data:null;
  const update=(key,value)=>onDraft({...draft,perPersoon:{...draft.perPersoon,[persoon]:{...settings,[key]:value}}});
  const apply=(index,asCopy=false)=>{
    try { onApply(current,index,asCopy);setResult(null); } catch(e) { setError(e.message); }
  };
  const run=async()=>{
    setBusy(true);setError('');setResult(null);
    try {
      const data=await requestActuarialVariants(apiBase,request);
      setResult({signature,data});
    }catch(e){setError(e.message);}finally{setBusy(false);}
  };
  const r=current?.raming;
  return <section className="opbouw-simulator">
    <h3>Wat krijg ik als ik eerder stop?</h3>
    <p>We gebruiken je stopdatum, pensioenbedragen en oorspronkelijke pensioendatums uit <strong>{baseRequest.scenario?.naam}</strong>. Je hoeft geen offerte of drie nieuwe bedragen in te vullen.</p>
    <div className="notice"><strong>Pensioenkeuzes in {baseRequest.scenario?.naam}</strong>
      <ul>{[['P1',baseRequest.persoon1],['P2',baseRequest.persoon2]].filter(([,p])=>p).map(([code,p])=><li key={code}>
        {p.naam || code}: {(draft.toegepast || []).find(x=>x.persoon===code)?.variant || 'Oorspronkelijke pensioeninvoer'}
      </li>)}</ul><p>Toepassen werkt dit huishoudscenario bij. De keuze van je partner blijft behouden.</p>
      {onViewPlan && draft.toegepast?.length?<button type="button" onClick={onViewPlan}>Bekijk het gezamenlijke meerjarenplan</button>:null}
    </div>
    <label className="field inline-field"><span>Voor wie wil je een keuze maken of wijzigen?</span><select value={persoon} onChange={e=>onDraft({...draft,perPersoon:{...draft.perPersoon,[persoon]:settings},actuarieel:{persoon:e.target.value}})}>
      <option value="P1">{baseRequest.persoon1?.naam || 'Persoon 1'}</option>
      {baseRequest.persoon2?<option value="P2">{baseRequest.persoon2.naam || 'Persoon 2'}</option>:null}
    </select></label>
    <p>{posten.length} pensioenposten gevonden. AOW blijft op de AOW-datum ingaan.</p>
    <p className="notice">We schatten gemiste opbouw en de gevolgen van langer uitkeren. Standaardaannames zijn gelijkmatige opbouw vanaf 25 jaar en 3% rekenrente. Controleer onder Aannames welke pensioenen al volledig opgebouwd zijn.</p>
    {toegepast && !toegepast.basisPosten?<div className="notice"><p>Gekozen: {toegepast.variant}. Kies opnieuw vanuit het oorspronkelijke scenario, zodat geen tweede opbouwkorting of dubbele premie ontstaat.</p>
      {scenarios.some(s=>s.id===toegepast.bronScenarioId)?
        <button type="button" onClick={()=>onChooseAgain(toegepast.bronScenarioId)}>Andere variant kiezen</button>:
        <><label className="field"><span>Oorspronkelijk scenario (bij oudere keuzes nog niet opgeslagen)</span><select value={bronId} onChange={e=>setBronId(e.target.value)}>
          <option value="">Kies je oorspronkelijke scenario</option>{scenarios.map(s=><option key={s.id} value={s.id}>{s.naam}</option>)}
        </select></label><button type="button" disabled={!bronId} onClick={()=>onChooseAgain(bronId)}>Andere variant kiezen</button></>}
    </div>:null}
    <button type="button" disabled={busy || !posten.length || Boolean(preparationError) || Boolean(toegepast && !toegepast.basisPosten)} onClick={run}>{busy?'Actuarieel berekenen…':toegepast?.basisPosten?'Vergelijk opnieuw voor deze persoon':'Bereken mijn drie opties'}</button>
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
    {preparationError?<p className="notice">{preparationError}</p>:null}
    {error?<p className="error" role="alert">{error}</p>:null}
    {result&&!current?<p className="notice">Scenario of aannames gewijzigd. Bereken opnieuw voor een actuele schatting.</p>:null}
    {r?<>
      <p className="notice"><strong>Raming, geen vastgestelde aanspraak.</strong> Laatste werkdag uit je scenario: {r.laatste_werkdag}. Eerste volledige maand na stoppen: {r.vanaf_stoppen}. Opbouw vanaf {r.startleeftijd_opbouw} jaar; rekenrente {Number(r.rekenrente_pct).toLocaleString('nl-NL')}%.</p>
      <PensioenPostStatus raming={r} euro={euro} />
      {r.volledig?<><div className="scenario-cards">
        <article className="scenario-card"><h3>1. Direct pensioen ontvangen</h3><p>{r.regelingen.length ? `Vanaf ${r.vanaf_stoppen} voor de berekende regelingen` : 'Oorspronkelijke startdatums blijven gelden'}</p><strong>{r.regelingen.length?<>{euro(Number(r.totaal_direct_bruto_maand))} bruto per maand voor de berekende regelingen</>:'Pensioen volgens oorspronkelijke invoer'}</strong><p>Voor de berekende regelingen: minder opbouw én een lagere uitkering doordat het pensioen langer wordt uitgekeerd.</p><button type="button" disabled={!onApply} onClick={()=>apply(0)}>Pas toe in dit scenario</button><button type="button" className="ghost" disabled={!onApply} onClick={()=>apply(0,true)}>Bewaar als nieuw scenario</button></article>
        <article className="scenario-card"><h3>2. Wachten, niet doorbetalen</h3><p>Vanaf de oorspronkelijke pensioendatum per regeling</p><strong>{r.regelingen.length?<>{euro(Number(r.totaal_wachten_bruto_maand))} bruto per maand voor de berekende regelingen</>:'Pensioen volgens oorspronkelijke invoer'}</strong><p>Bij de berekende regelingen bouw je minder op, maar het pensioen wordt niet vervroegd. Tot de ingangsdatum overbrug je uit andere inkomsten of vermogen.</p><button type="button" disabled={!onApply} onClick={()=>apply(1)}>Pas toe in dit scenario</button><button type="button" className="ghost" disabled={!onApply} onClick={()=>apply(1,true)}>Bewaar als nieuw scenario</button></article>
        <article className="scenario-card"><h3>3. Premie doorbetalen, later pensioen</h3><p>Vanaf de oorspronkelijke pensioendatum per regeling</p><strong>{r.regelingen.length?<>{euro(Number(r.totaal_doorbetalen_bruto_maand))} bruto per maand voor de berekende regelingen</>:'Pensioen volgens oorspronkelijke invoer'}</strong><p>Actuarieel geschatte premie bij de start: <strong>{euro(Number(r.premie_per_maand_bij_start))} per maand</strong>. Totaal in de berekening: {euro(Number(r.totale_premie))}.</p><small>Inclusief {Number(r.premie_kostenopslag_pct)}% modelopslag, zonder belastingaftrek. Dit is niet de premieofferte van een fonds.</small><button type="button" disabled={!onApply} onClick={()=>apply(2)}>Pas toe in dit scenario</button><button type="button" className="ghost" disabled={!onApply} onClick={()=>apply(2,true)}>Bewaar als nieuw scenario</button></article>
      </div>
      <p>De bruto bedragen hierboven omvatten alleen de actuarieel berekende regelingen. Ongewijzigde pensioenen komen daar volgens hun oorspronkelijke invoer bij. Het volledige huishouden staat in de jaarvergelijking. De bedragen bij wachten en doorbetalen gelden zodra alle berekende regelingen lopen. Bij verschillende ingangsdatums zie je de fasering hieronder en in de jaaropbouw.</p>
      </>:null}
      {r.regelingen.length?<details open className="scenario-technical"><summary>Zo ontstaat je geschatte pensioen</summary><div className="table-wrap"><table>
        <thead><tr><th>Pensioen</th><th>Oorspronkelijke datum</th><th>Uit scenario bruto p/m</th><th>Na gemiste opbouw</th><th>Direct bij stoppen</th><th>Rentegevoeligheid direct</th><th>Geschatte premie p/m</th></tr></thead>
        <tbody>{r.regelingen.map(row=><tr key={row.index}><td>{row.naam}<br/><small>{row.verdere_opbouw_aangenomen?'Verdere opbouw aangenomen':'Reeds opgebouwd'}</small></td><td>{row.normaal_vanaf}</td><td>{euro(Number(row.import_bruto_maand))}</td><td>{euro(Number(row.wachten_bruto_maand))}<br/><small>{(Number(row.opbouwfactor)*100).toFixed(1)}% behouden</small></td><td>{euro(Number(row.direct_bruto_maand))}<br/><small>Vervroegingsfactor {Number(row.vervroegingsfactor).toFixed(3)}</small></td><td>{euro(Number(row.direct_laag))}–{euro(Number(row.direct_hoog))}</td><td>{euro(Number(row.premie_bruto_maand))}<br/><small>Gevoeligheid {euro(Number(row.premie_laag))}–{euro(Number(row.premie_hoog))}</small></td></tr>)}</tbody>
      </table></div><p>De gevoeligheid gebruikt rekenrentes {r.gevoeligheid_rentes_pct.map(x=>`${Number(x)}%`).join(', ')}. Dit is geen betrouwbaarheidsinterval.</p></details>:<p>Geen pensioenpost is actuarieel aangepast. De posten met een oorspronkelijke startdatum blijven in alle drie varianten gelijk; zie de toelichting hierboven.</p>}
      {r.overgeslagen.length?<p className="notice">{r.overgeslagen.join(' ')}</p>:null}
      {r.volledig && current.jaarvergelijking?<ActuarieleJaarvergelijking data={current.jaarvergelijking} euro={euro} />:null}
      {r.volledig && current.vergelijking?<ScenarioComparison comparisonResult={current.vergelijking} activeScenarioName="Direct pensioen bij stoppen" euro={euro} />:null}
      <details className="scenario-technical"><summary>Rekenmethode en bronnen</summary><p>{r.bron_sterfte}. <a href="https://www.actuarieelgenootschap.nl/kennisbank/prognosetafel-ag2024-2" target="_blank" rel="noreferrer">Open AG2024-bron</a>.</p><ul>{r.aannames.map((x,i)=><li key={i}>{x}</li>)}</ul></details>
    </>:null}
  </section>;
}
