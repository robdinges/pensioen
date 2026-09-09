import assert from 'node:assert/strict';
import {test} from 'node:test';
import {requestActuarialVariants} from '../src/planner/actuarialRequest.js';

test('HTML and empty error responses produce an actionable HTTP error instead of a browser parser error',async()=>{
  for(const text of ['', '<html>Bad gateway</html>','Internal Server Error']){
    await assert.rejects(requestActuarialVariants('/api/v1',{},async()=>({ok:false,status:500,text:async()=>text})),/HTTP 500/);
  }
});
test('normalizes service address and preserves domain validation messages',async()=>{
  let url;
  const result=await requestActuarialVariants(' /api/v1/ ',{},async(value)=>{
    url=value;return {ok:true,status:200,text:async()=>JSON.stringify({raming:{volledig:false}})};
  });
  assert.equal(url,'/api/v1/simulaties/actuarieel');
  assert.equal(result.raming.volledig,false);
  await assert.rejects(requestActuarialVariants('/api/v1',{},async()=>({ok:false,status:422,text:async()=>JSON.stringify({detail:'Einddatum ontbreekt'})})),/Einddatum ontbreekt/);
  await assert.rejects(requestActuarialVariants('bad address',{}),/adres.*ongeldig/);
  await assert.rejects(requestActuarialVariants('/api/v1',{},async()=>{throw new Error('The string did not match the expected pattern.');}),/niet bereikbaar/);
});
