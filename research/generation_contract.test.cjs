'use strict';
const assert=require('node:assert/strict');
const {validateGeneration}=require('../tools/verify_public_site.js');
const id='a'.repeat(64),generation={id,schema:'beops-input-generation/v1',observation_prefix:'complete-lf-lines/v1',captured_at:'2026-09-14T12:00:00.321Z'};
for(const route of ['live-snapshot.json','history.json','city-overview.json','city-analysis.json']){
 const value={as_of:'2026-09-14T12:00:00Z',input_generation:generation,edition:{input_generation:generation}};
 assert.equal(validateGeneration(route,value,id),id);
 assert.equal(validateGeneration(route,value,id,value.as_of),id);
 assert.throws(()=>validateGeneration(route,value,id,'2026-09-13T12:00:00Z'),/clock differs/);
 assert.throws(()=>validateGeneration(route,value,'b'.repeat(64)),/generation differs/);
 assert.throws(()=>validateGeneration(route,{...value,as_of:'2026-09-13T12:00:00Z'},id),/clock differs/);
 assert.throws(()=>validateGeneration(route,{as_of:value.as_of},id),/generation differs/);
}
console.log('Public generation: four projections, exact manifest identity, missing generation and stale projection refusal passed.');
