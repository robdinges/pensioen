import assert from 'node:assert/strict';
import {test} from 'node:test';
import {applyActuarialVariant} from '../src/planner/actuarialVariant.js';
import {buildRequestPayload, normalizeScenarioSnapshot, createPost} from '../src/planner/plannerCore.js';

test('saved variant preserves unrelated inputs, exact pension amounts and one premium after reload', () => {
  const loon=createPost('loon'), pensioen=createPost('pensioen'), sparen=createPost('sparen');
  pensioen.titel='Fonds';
  pensioen.values={...pensioen.values,bedrag:'1000',startdatum:'2027-01-01',inflatie_pct:'0'};
  const base={posts:[loon,sparen,pensioen],jaarVan:'2025',jaarTot:'2030',opbouwDraft:{}};
  const params={persoonNaam:'Test',geboortedatum:'1960-01-01',jaarVan:'2025',jaarTot:'2030',scenarioNaam:'Test',heeftPartner:false};
  const request=buildRequestPayload({...params,posts:base.posts});
  const variant=structuredClone(request.scenario);
  variant.naam='Doorbetalen en later pensioen';
  variant.componenten[1].bedrag='952.38';
  variant.componenten.push({omschrijving:'Premie Fonds',categorie:'uitgave',persoon:'P1',bedrag:'370.87',
    bedrag_type:'netto',frequentie:'maandelijks',begindatum:'2025-01-01',einddatum:'2026-12-31',groei_pct:'0',beleggings_type:'sparen'});
  const raming={volledig:true,persoon:'P1',regelingen:[{index:1}],aannames:['Actuariële schatting']};
  const before=structuredClone(base);
  const result=applyActuarialVariant(base,variant,raming,{cashflow:{}});
  const restored=normalizeScenarioSnapshot(JSON.parse(JSON.stringify(result)));
  const roundtrip=buildRequestPayload({...params,posts:restored.posts});
  assert.deepEqual(roundtrip.scenario.componenten,variant.componenten);
  assert.deepEqual(result.posts.slice(0,2),base.posts.slice(0,2));
  assert.deepEqual(base,before);
  assert.equal(restored.opbouwDraft.toegepast[0].persoon,'P1');
  assert.throws(()=>applyActuarialVariant(base,variant,{...raming,volledig:false},null),/onvolledige/);
});

test('P1 and P2 choices share one snapshot and reselecting P1 preserves P2 without stacked premiums',async()=>{
  const {prepareActuarialSnapshot}=await import('../src/planner/actuarialVariant.js');
  const p1=createPost('pensioen'), p2=createPost('pensioen');
  p1.titel='Fonds P1';p2.titel='Fonds P2';
  p1.values={...p1.values,persoon:'P1',bedrag:'1000',startdatum:'2029-01-01'};
  p2.values={...p2.values,persoon:'P2',bedrag:'800',startdatum:'2030-01-01'};
  const base={posts:[p1,p2],opbouwDraft:{},jaarVan:'2025',jaarTot:'2035'};
  const params={persoonNaam:'P1',partnerNaam:'P2',geboortedatum:'1960-01-01',partnerGeboortedatum:'1961-01-01',heeftPartner:true,jaarVan:'2025',jaarTot:'2035',scenarioNaam:'Huishouden'};
  const variantFor=(snapshot,person,amount,withPremium=false)=>{
    const source=prepareActuarialSnapshot(snapshot,person);
    const variant=buildRequestPayload({...params,posts:source.posts}).scenario;
    const index=person==='P1'?0:1;
    variant.naam=withPremium?'Doorbetalen':'Direct';
    variant.componenten[index].bedrag=amount;
    if(withPremium) variant.componenten.push({omschrijving:'Premie',categorie:'uitgave',persoon:person,bedrag:'100',bedrag_type:'netto',frequentie:'maandelijks',begindatum:'2025-01-01',einddatum:'2028-12-31',groei_pct:'0'});
    return applyActuarialVariant(snapshot,variant,{volledig:true,persoon:person,regelingen:[{index}],aannames:[]},null);
  };
  const one=variantFor(base,'P1','900',true);
  const both=variantFor(one,'P2','600');
  assert.equal(both.posts[0].values.bedrag,'900');
  assert.equal(both.posts[1].values.bedrag,'600');
  assert.equal(both.posts.length,3);
  const again=variantFor(JSON.parse(JSON.stringify(both)),'P1','700');
  assert.equal(again.posts.length,2);
  assert.equal(again.posts[1].values.bedrag,'600');
  assert.equal(again.opbouwDraft.toegepast.length,2);
  assert.equal(prepareActuarialSnapshot(again,'P1').posts[0].values.bedrag,'1000');
  assert.equal(prepareActuarialSnapshot(again,'P2').posts[1].values.bedrag,'800');
  assert.deepEqual(base.posts,[p1,p2]);
  again.posts[0].values.bedrag='123';
  assert.throws(()=>prepareActuarialSnapshot(again,'P1'),/handmatig gewijzigd/);
});
