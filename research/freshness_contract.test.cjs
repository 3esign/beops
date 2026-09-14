'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(path.join(__dirname,'05-design/studies/sada.html'),'utf8');
const block=html.split('// BEOPS freshness contract:')[1]?.split('// END BEOPS freshness contract')[0];
assert.ok(block,'Public panel must independently check publication and watcher age');
const ctx=vm.createContext({});vm.runInContext(block.slice(block.indexOf('\n')),ctx);
const fixtures={"at":"2026-09-13T21:31:09.091Z","passed":10,"cases":[{"name":"published incident: 205-minute record and watch","snap":"2026-09-13T18:00:00.000Z","watch":"2026-09-13T18:01:00.000Z","record":false,"check":false},{"name":"fresh publication and watcher","snap":"2026-09-13T21:21:00.000Z","watch":"2026-09-13T21:22:00.000Z","record":true,"check":true},{"name":"fresh publication cannot freshen old watcher","snap":"2026-09-13T21:23:00.000Z","watch":"2026-09-13T19:55:00.000Z","record":true,"check":false},{"name":"fresh watcher cannot freshen old publication","snap":"2026-09-13T19:55:00.000Z","watch":"2026-09-13T21:24:00.000Z","record":false,"check":true},{"name":"publication limit inclusive","snap":"2026-09-13T20:25:00.000Z","watch":"2026-09-13T21:05:00.000Z","record":true,"check":true},{"name":"publication and watch past limits","snap":"2026-09-13T20:24:59.400Z","watch":"2026-09-13T21:04:59.400Z","record":false,"check":false},{"name":"missing timestamps","snap":null,"watch":null,"record":false,"check":false},{"name":"invalid timestamps","snap":"invalid","watch":"invalid","record":false,"check":false},{"name":"future clock beyond tolerance","snap":"2026-09-13T21:31:00.000Z","watch":"2026-09-13T21:31:00.000Z","record":false,"check":false},{"name":"bounded clock skew","snap":"2026-09-13T21:29:00.000Z","watch":"2026-09-13T21:29:00.000Z","record":true,"check":true}]};
const now=Date.parse('2026-09-13T21:25:00Z');
for(const fixture of fixtures.cases){
 const result=ctx.beopsRecordState(fixture.snap,fixture.watch,now);
 assert.equal(result.recordFresh,fixture.record,fixture.name+': publication');
 assert.equal(result.watchFresh,fixture.check,fixture.name+': watcher');
}
for(const script of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi))new vm.Script(script[1]);
console.log(fixtures.cases.length+' freshness scenarios passed; embedded scripts parse.');

// Render the real provenance functions, including corrected/source clocks and unknown times.
const proof=html.slice(html.indexOf('function evidenceText('),html.indexOf('// BEOPS freshness contract:'));
const proofCtx=vm.createContext({beopsClocks:require('./05-design/studies/observation-clocks.js'),LANG:'en',SNAP:{sources:[{sid:'S03',name:'Open-Meteo'}]},t:k=>k,P:Date.parse,utc:ms=>new Date(ms).toISOString().slice(11,16),hh:d=>d.toISOString().slice(11,16),agoText:()=> 'age'});
vm.runInContext(proof,proofCtx);
const corrected=proofCtx.provenanceFull({src:'SEPA',sourceHour:true},{d:{station:'Station A'},p:{tc:'2026-09-13T12:00:00Z',t:'2026-09-13T14:00:00Z',rx:'2026-09-13T13:00:00Z'}});
assert.match(corrected,/estimated clock 2026-09-13 12:00 UTC/);assert.match(corrected,/source clock 2026-09-13 14:00 UTC/);assert.match(corrected,/Station A/);
const parking=proofCtx.provenanceFull({src:'Parking servis'},{d:{},n:3,firstRx:'2026-09-13T12:00:00Z',p:{tu:true,t:null,rx:'2026-09-13T12:05:00Z'}});
assert.match(parking,/3 trackedGarages/);assert.match(parking,/unknown/);assert.match(parking,/2026-09-13T12:00:00Z – 2026-09-13T12:05:00Z/);assert.doesNotMatch(parking,/measured/);
const escaped=proofCtx.provenance({src:'SEPA',sourceHour:true},{d:{station:'<img>'},p:{t:null}});
assert.ok(!escaped.includes('<img>'));
const fallback=proofCtx.provenanceFull({src:'RHMZ'},{sid:'S03',d:{},p:{v:20,t:null}});
assert.match(fallback,/Open-Meteo/);assert.doesNotMatch(fallback,/RHMZ/);
console.log('Corrected/source time, reception range, coverage and escaping passed.');
