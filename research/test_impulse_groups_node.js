'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {buildGroups,encode,descriptor}=require('../tools/build_impulse_groups');
const source=path.resolve(__dirname,'..'),base=path.resolve(process.env.BEOPS_TEST_TEMP||path.join(source,'runtime/impulse-group-tests'));
const at='2026-09-27T12:00:00Z',capture='20260927T070000Z',receipt='2026-09-27T11:00:00Z';
const digest=value=>crypto.createHash('sha256').update(value).digest('hex');
function write(root,name,value){const file=path.join(root,name);fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,typeof value==='string'||Buffer.isBuffer(value)?value:JSON.stringify(value),'utf8');}
function read(root,name){return JSON.parse(fs.readFileSync(path.join(root,name),'utf8'));}
function object(root,entry){return read(root,'docs/'+entry.path);}
function policy(root,sid,url,override={}){
 const origin=new URL(url).origin,directory='research/evidence/legal/'+sid+'/'+capture;
 const verdict=JSON.stringify({[origin]:{paths:{[url]:{allowed_for_us:true}}}});
 write(root,directory+'/robots_verdict.json',verdict);
 const manifest=JSON.stringify({sid,captured_at_utc:capture,files:{'robots_verdict.json':{bytes:Buffer.byteLength(verdict),sha256:digest(verdict)}}});
 write(root,directory+'/MANIFEST.json',manifest);
 const entry={sid,captured_at_utc:capture,evidence_dir:directory,manifest_sha256:digest(manifest),
  allowed_for_us:true,capture_ok:true,status_by_url:{[url]:200},...override};
 fs.mkdirSync(path.join(root,'research/08-provenance'),{recursive:true});
 fs.appendFileSync(path.join(root,'research/08-provenance/LEDGER.jsonl'),JSON.stringify(entry)+'\n','utf8');
 return entry;
}
function fixture(){
 assert.ok(['C:/Svemir','D:/Svemir'].some(root=>base.toLowerCase().startsWith(path.resolve(root).toLowerCase()+path.sep)));
 fs.mkdirSync(base,{recursive:true});const root=fs.mkdtempSync(path.join(base,'fixture-'));
 const executable=path.join(source,'runtime/test-python.json');
 if(fs.existsSync(executable))write(root,'runtime/test-python.json',fs.readFileSync(executable));
 write(root,'public/basemap-belgrade.json',{type:'FeatureCollection',features:[],attribution:'Natural Earth'});
 const url='https://www.kolarac.rs/koncerti/';
 const event={id:'show',title:'Official concert',url:url+'test/',source_id:'S225',source:'Kolarac',verified:true,
  classification:'official-repertoire',event_start:'2026-09-28T16:00:00Z',location:'Velika dvorana',
  ticket_availability:'sold_out',private_note:'C:\\private\\raw-cache',
  provenance:{received_at:receipt,url,raw_sha256:'f'.repeat(64),source_label:'Official concert Velika dvorana'}};
 write(root,'data/live/derived/events/repertoire.json',{schema:'beops-repertoire-cache/v2',state:'available',
  sources:[{source_id:'S225',name:'Kolarac',url,state:'available',received_at:receipt,permission_capture:capture,events:[event]}],events:[event]});
 policy(root,'S225',url);
 return root;
}
function cleanup(root){assert.ok(path.resolve(root).startsWith(base+path.sep));fs.rmSync(root,{recursive:true,force:true});}
const cacheFile='data/live/derived/events/repertoire.json',pointerFile='docs/impulse-data/groups/current.json';
function changeCache(root,fn){const cache=read(root,cacheFile);fn(cache);write(root,cacheFile,cache);}

test('calendar groups use real venue projection and canonical policy; never read unrelated feeds',async()=>{
 const root=fixture(),original=fs.readFileSync,originalOpen=fs.openSync;
 const forbidden=['public/headlines.json','public/history.json','runtime/resources/receipts/x.json','data/live/rows/S146/2026-09.jsonl'];
 for(const file of forbidden)write(root,file,'MUST NOT READ');
 try{
  fs.openSync=function(file,...args){if(typeof file==='string')assert.ok(!forbidden.some(p=>path.resolve(file)===path.join(root,p)),'unrelated feed opened');return originalOpen.call(fs,file,...args);};
  const result=await buildGroups(root,{asOf:at}),calendar=object(root,result.groups.calendar),context=object(root,result.groups.context);
  assert.equal(result.changed,true);assert.equal(result.objectWrites,2);assert.equal(result.pointerWrites,1);
  assert.equal(calendar.schema,'beops-calendar-group/v1');assert.equal(context.schema,'beops-context-group/v1');
  assert.equal(calendar.items.length,1);assert.equal(calendar.items[0].kind,'scheduled_event');
  assert.equal(calendar.items[0].ticket_availability,'sold_out');assert.equal(calendar.items[0].venue_location.precision,'venue');
  assert.equal(calendar.items[0].point,null);assert.equal(calendar.items[0].private_note,undefined);
  assert.equal(calendar.sources[0].state,'available');assert.equal(calendar.sources[0].event_count,1);
  assert.equal(calendar.dependencies.context,result.groups.context.revision);
  for(const entry of Object.values(result.groups)){
   const raw=original(path.join(root,'docs',entry.path));assert.equal(raw.length,entry.bytes);assert.equal(digest(raw),entry.revision);
   assert.ok(!raw.toString('utf8').includes('C:\\private'));assert.ok(raw.equals(encode(JSON.parse(raw))));
  }
  assert.match(calendar.policy_revision,/^[a-f0-9]{64}$/);assert.match(calendar.transform_revision,/^[a-f0-9]{64}$/);
  assert.ok(result.inputReadBytes>0);assert.ok(result.inputFiles.includes('research/08-provenance/LEDGER.jsonl'));
  assert.ok(result.inputFiles.every(p=>!forbidden.includes(p)));
 }finally{fs.openSync=originalOpen;cleanup(root);}
});

test('identical semantic inputs are a byte-for-byte no-op with zero public writes',async()=>{
 const root=fixture();try{
  const first=await buildGroups(root,{asOf:at}),pointer=fs.readFileSync(path.join(root,pointerFile));
  const second=await buildGroups(root,{asOf:at});
  assert.equal(second.changed,false);assert.equal(second.writtenBytes,0);assert.equal(second.objectWrites,0);assert.equal(second.pointerWrites,0);
  assert.deepEqual(second.groups,first.groups);assert.ok(fs.readFileSync(path.join(root,pointerFile)).equals(pointer));
  assert.ok(second.verifiedBytes>=first.groups.context.bytes+first.groups.calendar.bytes);
 }finally{cleanup(root);}
});

test('calendar advances alone without copying context or a history sentinel',async()=>{
 const root=fixture();try{
  const first=await buildGroups(root,{asOf:at});write(root,'docs/history-sentinel.bin','retained independently');
  changeCache(root,cache=>{cache.events[0].title='Changed concert';});
  const second=await buildGroups(root,{asOf:at});
  assert.equal(second.changed,true);assert.deepEqual(second.groups.context,first.groups.context);
  assert.notEqual(second.groups.calendar.revision,first.groups.calendar.revision);assert.equal(second.objectWrites,1);
  assert.equal(second.writtenBytes,second.groups.calendar.bytes+fs.statSync(path.join(root,pointerFile)).size);
  assert.equal(fs.readFileSync(path.join(root,'docs/history-sentinel.bin'),'utf8'),'retained independently');
 }finally{cleanup(root);}
});

test('context replacement binds a new calendar revision to the exact new context',async()=>{
 const root=fixture();try{
  const first=await buildGroups(root,{asOf:at});
  write(root,'public/basemap-belgrade.json',{type:'FeatureCollection',features:[],attribution:'Updated attribution'});
  const next=await buildGroups(root,{asOf:at});assert.equal(next.objectWrites,2);
  assert.notEqual(next.groups.context.revision,first.groups.context.revision);
  assert.notEqual(next.groups.calendar.revision,first.groups.calendar.revision);
  assert.equal(object(root,next.groups.calendar).dependencies.context,next.groups.context.revision);
 }finally{cleanup(root);}
});

test('as_of is semantic: receipt freshness expires even when cache bytes do not change',async()=>{
 const root=fixture();try{
  const first=await buildGroups(root,{asOf:at}),next=await buildGroups(root,{asOf:'2026-09-28T12:00:00Z'});
  assert.deepEqual(next.groups.context,first.groups.context);assert.notEqual(next.groups.calendar.revision,first.groups.calendar.revision);
  const calendar=object(root,next.groups.calendar);assert.equal(calendar.items.length,0);assert.equal(calendar.sources[0].state,'stale');
 }finally{cleanup(root);}
});

test('failed and future source receipts cannot borrow the union timestamp or events',async()=>{
 const root=fixture();try{
  changeCache(root,c=>{c.sources[0].state='unavailable';});
  let result=await buildGroups(root,{asOf:at}),calendar=object(root,result.groups.calendar);
  assert.equal(calendar.items.length,0);assert.equal(calendar.sources[0].state,'unavailable');
  changeCache(root,c=>{c.sources[0].state='available';c.sources[0].received_at='2026-09-27T13:00:00Z';});
  result=await buildGroups(root,{asOf:at});calendar=object(root,result.groups.calendar);
  assert.equal(calendar.items.length,0);assert.equal(calendar.sources[0].state,'future_receipt');
 }finally{cleanup(root);}
});

test('policy revocation, missing capture and damaged evidence block retained calendar rows',async()=>{
 for(const mode of ['revoked','missing-capture','corrupt-evidence','expired','missing-ledger']){
  const root=fixture();try{
   const first=await buildGroups(root,{asOf:at});
   if(mode==='revoked')policy(root,'S225','https://www.kolarac.rs/koncerti/',{manual_verdict:'refused'});
   if(mode==='missing-capture')changeCache(root,c=>{delete c.sources[0].permission_capture;});
   if(mode==='corrupt-evidence')write(root,'research/evidence/legal/S225/'+capture+'/robots_verdict.json','{}');
   if(mode==='missing-ledger')fs.unlinkSync(path.join(root,'research/08-provenance/LEDGER.jsonl'));
   const result=await buildGroups(root,{asOf:mode==='expired'?'2026-10-06T12:00:00Z':at});
   const calendar=object(root,result.groups.calendar);assert.equal(calendar.items.length,0,mode);
   assert.equal(calendar.sources[0].state,'permission_unavailable',mode);
   assert.notEqual(first.groups.calendar.revision,result.groups.calendar.revision,mode);
  }finally{cleanup(root);}
 }
});

test('unrelated source policy changes do not invalidate the calendar',async()=>{
 const root=fixture();try{
  const first=await buildGroups(root,{asOf:at});policy(root,'UNRELATED','https://example.test/unrelated');
  const next=await buildGroups(root,{asOf:at});assert.equal(next.changed,false);assert.deepEqual(next.groups,first.groups);
 }finally{cleanup(root);}
});

test('object corruption fails closed even when an existing object would otherwise be reused',async()=>{
 const root=fixture();try{
  const first=await buildGroups(root,{asOf:at}),pointer=fs.readFileSync(path.join(root,pointerFile));
  const file=path.join(root,'docs',first.groups.context.path),raw=fs.readFileSync(file);raw[raw.length-2]^=1;fs.writeFileSync(file,raw);
  await assert.rejects(buildGroups(root,{asOf:at}),/group_object_integrity_mismatch/);
  assert.ok(fs.readFileSync(path.join(root,pointerFile)).equals(pointer));
 }finally{cleanup(root);}
});

test('a pointer with stale dependencies is rejected before any replacement',async()=>{
 const root=fixture();try{
  const first=await buildGroups(root,{asOf:at}),pointer=read(root,pointerFile),calendar=object(root,first.groups.calendar);
  calendar.dependencies.context='0'.repeat(64);const raw=encode(calendar),entry=descriptor(raw);
  write(root,'docs/'+entry.path,raw);pointer.groups.calendar=entry;write(root,pointerFile,pointer);
  await assert.rejects(buildGroups(root,{asOf:at}),/group_dependency_mismatch/);
 }finally{cleanup(root);}
});

test('interrupted publication leaves the previous pointer intact and reuses finished objects on retry',async()=>{
 const root=fixture();try{
  await buildGroups(root,{asOf:at});const before=fs.readFileSync(path.join(root,pointerFile));
  changeCache(root,c=>{c.events[0].title='New title after interrupt';});
  await assert.rejects(buildGroups(root,{asOf:at,beforeCommit(){throw Error('simulated_interrupt');}}),/simulated_interrupt/);
  assert.ok(fs.readFileSync(path.join(root,pointerFile)).equals(before));
  assert.equal(fs.existsSync(path.join(root,'docs/impulse-data/groups/.writer.lock')),false);
  const result=await buildGroups(root,{asOf:at});assert.equal(result.changed,true);assert.equal(result.objectWrites,0);assert.equal(result.pointerWrites,1);
  assert.equal(object(root,result.groups.calendar).items[0].title,'New title after interrupt');
 }finally{cleanup(root);}
});

test('existing writer ownership cannot be stolen, including an apparently dead owner',async()=>{
 const root=fixture();try{
  const lock='docs/impulse-data/groups/.writer.lock',owner={pid:2147483647,token:'other-owner',started_at:'2000-01-01T00:00:00Z'};
  write(root,lock,owner);await assert.rejects(buildGroups(root,{asOf:at}),/group_writer_locked_manual_recovery/);
  assert.deepEqual(read(root,lock),owner);assert.equal(fs.existsSync(path.join(root,pointerFile)),false);
 }finally{cleanup(root);}
});

test('empty calendar creates bounded groups without requiring a policy interpreter',async()=>{
 const root=fixture();try{
  fs.unlinkSync(path.join(root,cacheFile));const result=await buildGroups(root,{asOf:at});
  assert.deepEqual(object(root,result.groups.calendar).items,[]);assert.deepEqual(object(root,result.groups.calendar).sources,[]);
 }finally{cleanup(root);}
});

test('oversized group input fails before allocation or pointer replacement',async()=>{
 const root=fixture();try{
  await buildGroups(root,{asOf:at});const before=fs.readFileSync(path.join(root,pointerFile));
  const fd=fs.openSync(path.join(root,cacheFile),'r+');try{fs.ftruncateSync(fd,16*1024*1024+1);}finally{fs.closeSync(fd);}
  await assert.rejects(buildGroups(root,{asOf:at}),/group_input_byte_limit/);
  assert.ok(fs.readFileSync(path.join(root,pointerFile)).equals(before));
 }finally{cleanup(root);}
});
