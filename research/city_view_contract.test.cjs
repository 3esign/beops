'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const code=fs.readFileSync(path.join(__dirname,'05-design/studies/beops-view.js'),'utf8');
for(const name of ['sada.html','podaci.html','obrasci.html']){
 const html=fs.readFileSync(path.join(__dirname,'05-design/studies',name),'utf8');
 for(const script of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi))new vm.Script(script[1],{filename:name});
}
const bytes=v=>new TextEncoder().encode(JSON.stringify(v));
const spec=b=>({bytes:b.byteLength,sha256:crypto.createHash('sha256').update(b).digest('hex')});
async function main(){
 let now=0,calls=[],body=bytes({series:[1]}),fail=false;
 let overview={schema:'beops-city-view/v1',generation:'a'.repeat(64),snapshot:{as_of:'first'},resources:{'history.json':spec(body)}};
 const window={};window.parent=window;
 const fetch=async name=>{calls.push(name);return {ok:!fail,json:async()=>overview,arrayBuffer:async()=>body.buffer};};
 vm.runInNewContext(code,{window,fetch,Date:{now:()=>now,parse:Date.parse},Map,Error,crypto:crypto.webcrypto,Uint8Array,TextDecoder,structuredClone});
 const api=window.beopsView;
 const [a,b]=await Promise.all([api.overview(),api.overview()]);assert.equal(a,b);assert.equal(calls.length,1);
 const first=await api.read('history.json',a);first.series.push(2);
 assert.deepEqual((await api.read('history.json',a)).series,[1]);assert.equal(calls.filter(x=>x==='history.json').length,1);
 now=61000;overview={...overview,generation:'b'.repeat(64)};const current=await api.overview();
 body=bytes({series:[999]});await assert.rejects(api.read('history.json',current),/generation_mismatch/);
 await assert.rejects(api.read('../secret.json',current),/invalid_resource/);
 await assert.rejects(api.read('unknown.json',current),/resource_not_in_generation/);
 now=122000;fail=true;await assert.rejects(api.overview(),/overview_unavailable/);fail=false;await api.overview();
 const child={parent:window};vm.runInNewContext(code,{window:child});const before=calls.length;assert.equal(await child.beopsView.overview(),await api.overview());assert.equal(calls.length,before);
 const N=Date.parse('2026-09-14T12:00:00Z');
 const edition=(built,cut)=>({edition:{state:'verified_capture',built_at:built,input_generation:{captured_at:cut}}});
 const fresh=edition('2026-09-14T11:55:00Z','2026-09-14T11:50:00Z');
 assert.equal(api.editionState(fresh,N).state,'current');
 assert.equal(api.editionState(fresh,N+3600000).state,'stale');
 assert.equal(api.editionState(edition('2026-09-14T11:55:00Z','2026-09-14T10:00:00Z'),N).state,'stale_capture');
 assert.equal(api.editionState(edition('2026-09-14T13:00:00Z','2026-09-14T11:50:00Z'),N).state,'clock_error');
 assert.equal(api.editionState(edition('not a clock','2026-09-14T11:50:00Z'),N).state,'unknown');
 assert.equal(api.editionState({},N).state,'unknown');
 const source={cadence_seconds:300,last_captured_at:'2026-09-14T11:59:00Z',last_attempt_at:'2026-09-14T11:59:00Z',last_attempt_state:'captured'};
 assert.equal(api.sourceState(source,N),'received');assert.equal(api.sourceState(source,N+3600000),'old_reception');
 assert.equal(api.sourceState({...source,paused:'operator'},N),'paused');
 assert.equal(api.sourceState({...source,last_attempt_state:'failed'},N),'failed');
 assert.equal(api.sourceState({...source,last_captured_at:null},N),'no_reception');
 assert.equal(api.sourceState({...source,last_captured_at:'2026-09-14T13:00:00Z'},N),'clock_error');
 const staleShell={parent:window,document:{readyState:'loading',addEventListener(){},querySelector(){return {content:'c'.repeat(64)};}}};
 vm.runInNewContext(code,{window:staleShell});await assert.rejects(staleShell.beopsView.overview(),/page_generation_mismatch/);
 overview={...overview,edition:{state:'verified_capture',input_generation:{id:'d'.repeat(64)}}};now+=61000;
 const unpinned={parent:window,document:{readyState:'loading',addEventListener(){},querySelector(){return null;}}};
 vm.runInNewContext(code,{window:unpinned});await assert.rejects(unpinned.beopsView.overview(),/page_generation_mismatch/);
 console.log('City view: shared generation, lazy request, cloned results, corruption refusal, invalid paths, retry and parent reuse passed.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
