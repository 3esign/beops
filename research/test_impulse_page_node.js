'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {buildPage,encode}=require('../tools/build_impulse_page'),{hash}=require('../tools/ai_feed_context');
const {packItems,unpackItems,decodeImpulses}=require('../public/impulse-codec');
const source=path.resolve(__dirname,'..'),base=path.resolve(process.env.BEOPS_TEST_TEMP||path.join(source,'runtime/impulse-page-tests'));
const at='2026-09-27T12:00:00.123456Z',id='a'.repeat(32),cycle='b'.repeat(32),future='c'.repeat(32);
function write(root,name,value){const target=path.join(root,name);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,typeof value==='string'?value:JSON.stringify(value),'utf8');}
function read(root,name){return JSON.parse(fs.readFileSync(path.join(root,name),'utf8'));}
function readImpulses(root,name='docs/impulse-data/impulses.json'){return decodeImpulses(read(root,name));}
function fixture(){
 assert.ok(base.toLowerCase().startsWith(path.resolve('C:/Svemir').toLowerCase()+path.sep));fs.mkdirSync(base,{recursive:true});const root=fs.mkdtempSync(path.join(base,'fixture-'));
 const input_generation={schema:'beops-input-generation/v1',id:'d'.repeat(64),captured_at:at};
 write(root,'public/live-snapshot.json',{schema:'beops-live-snapshot/v1',as_of:at,input_generation});
 write(root,'research/COLLECTORS.json',{sources:[{sid:'S15',name:'Fixture news',parser:'city_listing'}]});
 write(root,'research/AI_FEED.json',{public_enabled:true});
 write(root,'public/basemap-belgrade.json',{type:'FeatureCollection',features:[],attribution:'Natural Earth'});
 for(const name of ['impulsi.html','impulsi.js','impulse-codec.js'])write(root,'public/'+name,fs.readFileSync(path.join(source,'public',name),'utf8'));
 const rows=[['local','Radovi na Novom Beogradu'],['unknown','Kvalitet vazduha je loš'],['serbia','Zagađenje u Nišu'],['outside','Požar u Parizu']].map(([key,title])=>({id:key,sid:'S15',title,link:'https://example.test/'+key,published:'2026-09-27T10:00:00Z',received:'2026-09-27T10:01:00Z',last_received:'2026-09-27T11:00:00Z',raw_sha256:'e'.repeat(64),permission_capture:'20260927T100000Z'}));
 rows.push({...rows[0],id:'future',title:'Future title',link:'https://example.test/future',received:'2026-09-28T10:00:00Z',last_received:'2026-09-28T10:00:00Z'});
 write(root,'public/headlines.json',{schema:'beops-headline-archive/v1',as_of:at,rows});
 // Canonical projection is authoritative even when raw rows/corrections differ.
 write(root,'data/live/rows/S15/2026-09.jsonl',JSON.stringify({sid:'S15',parameter:'headline',result:'REDACTED RAW TITLE',receivedTime:'2026-09-27T10:01:00Z'})+'\n');
 write(root,'data/live/corrections.jsonl','not a valid local overlay; canonical archive already applied it\n');
 const packet={schema:'beops-ai-context/v1',as_of:'2026-09-27T09:55:00Z',private_note:'C:\\private\\raw-packet',facts:[
  {id:'F1',sid:'S146',kind:'observation',place:'Station',url:'https://example.test/measurement',value:18,unit:'C',time:'2026-09-27T09:54:00Z',location:[20.4,44.8],private_field:'do not publish'},
  {id:'F2',value:'UNUSED PRIVATE FACT',url:'https://example.test/unused'}]};
 const entry={id,at:'2026-09-27T10:00:00Z',context_hash:hash(packet),validation:{ok:true},provider:'fixture',model:'test-model',route_id:'C:\\private\\route',content:{title:'Observation',paragraphs:[{text:'Cited reading, not an event.',cites:['F1'],hidden_reasoning:'PRIVATE REASONING'}],geo:{lon:20.4,lat:44.8},private_reasoning:'PRIVATE REASONING'}};
 write(root,'runtime/ai-feed/entries/'+id+'.json',entry);write(root,'runtime/ai-feed/contexts/'+entry.context_hash+'.json',packet);
 write(root,'research/AI_FEED_REVIEWS.json',{records:[{entry_id:id,entry_sha256:hash(entry),status:'quality_flag',reviewed_at:'2026-09-27T11:00:00Z',reason_sr:'Ograničen zaključak',reason_en:'Limited inference',reviewer:'private reviewer'}]});
 for(const [key,finish]of [[cycle,'2026-09-27T10:01:00Z'],[future,'2026-09-27T13:00:00Z']]){
  const start={schema:'beops-resource-cycle/v1',id:key,phase:'start',activity:'ai_feed',runtime:'node',started_at:'2026-09-27T10:00:00Z',pid:123};
  write(root,'runtime/resources/receipts/'+key+'-start.json',start);
  write(root,'runtime/resources/receipts/'+key+'-finish.json',{...start,phase:'finish',finished_at:finish,outcome:'completed',wall_seconds:60,cpu_seconds:3,peak_rss_bytes:1000,http:{request_attempts:1,response_body_bytes:600,body_reports:1,unreported_bodies:0},tokens:{state:'provider_reported',reported_calls:1,unreported_calls:0,input_tokens:10,output_tokens:2}});
 }
 write(root,'runtime/ai-feed/receipts/'+id+'-finish.json',{id,at:'2026-09-27T10:00:00Z',provider:'fixture',model:'test-model',state:'accepted'});
 write(root,'runtime/ai-feed/responses/'+id+'.json',{model:'test-model',usage:{input_tokens:10,output_tokens:2},private_reasoning:'DO NOT COPY RESPONSE'});
 return root;
}
function cleanup(root){assert.ok(path.resolve(root).startsWith(base+path.sep));fs.rmSync(root,{recursive:true,force:true});}

test('public URL text remains valid while local filesystem paths fail closed',()=>{
 assert.match(encode({url:'https://example.test/data',source:'http://example.test/source'}),/https:/);
 for(const value of ['C:\\private\\source','D:/private/source','file:///C:/private','/home/user/private','see C:\\private\\source'])assert.throws(()=>encode({value}),/local_path_in_public/);
});
test('public build binds all files to frozen clock and keeps large record arrays out of HTML',async()=>{
 const root=fixture();try{
  const result=await buildPage(root,{asOf:at}),docs=path.join(root,'docs');
  assert.equal(result.as_of,at);assert.equal(result.coverage.headline_mentions,4);assert.equal(result.coverage.ai_observations,1);
  for(const file of ['impulse-data/view-data.json','impulse-data/impulses.json','impulse-data/resources.json','impulse-data/ai-evidence/'+id+'.json']){
   const json=read(docs,file);assert.equal(json.as_of,at);assert.equal(json.input_generation.id,'d'.repeat(64));assert.equal(json.generation,result.generation);
  }
  const html=fs.readFileSync(path.join(docs,'impulsi.html'),'utf8');assert.ok(Buffer.byteLength(html)<128*1024);assert.ok(!html.includes('Radovi na Novom Beogradu'));
  assert.ok(html.includes('impulse-data/resources.json'));assert.ok(html.includes('impulsi.js'));assert.ok(!html.includes('__IMPULSE_MANIFEST__'));
  const data=read(docs,'impulse-data/view-data.json');assert.ok(!data.view.month.records);assert.ok(!data.view.month.estimates);
  const all=JSON.stringify(readImpulses(docs,'impulse-data/impulses.json'));assert.ok(!all.includes('REDACTED RAW TITLE'));assert.ok(!all.includes('Future title'));assert.ok(!all.includes('input_files'));
  const items=readImpulses(docs,'impulse-data/impulses.json').items,local=items.find(i=>i.title==='Radovi na Novom Beogradu');
  assert.ok(local.location_estimate.radius_m>0);assert.equal(local.point,null);assert.equal(local.event_time,null);assert.equal(local.evidence.raw_sha256,'e'.repeat(64));
  const ai=items.find(i=>i.kind==='ai_observation');assert.equal(ai.geo.scope,'unknown');assert.equal(ai.point.lon,20.4);
  const repeated=await buildPage(root,{asOf:at,outputDir:path.join(root,'second')});assert.equal(repeated.generation,result.generation);
 }finally{cleanup(root)}
});
test('resource projection preserves missing energy and future finishes without adding historical usage',async()=>{
 const root=fixture();try{
  await buildPage(root,{asOf:at});const resources=read(root,'docs/impulse-data/resources.json');
  assert.equal(resources.windows.day.finished_cycles,1);assert.equal(resources.windows.day.unfinished_cycles,1);
  assert.equal(resources.windows.day.tokens.input_tokens,10);assert.equal(resources.historical_provider_usage.all.input_tokens,10);
  assert.equal(resources.electricity.wh,null);assert.equal(resources.money.amount,null);assert.equal(resources.windows.day.cpu_seconds,3);
  assert.equal(resources.coverage.invalid_receipt_files,undefined);
 }finally{cleanup(root)}
});
test('AI proof contains cited facts and review flags but no raw packet, prompt, route, unused fact or reasoning',async()=>{
 const root=fixture();try{
  await buildPage(root,{asOf:at});const proof=read(root,'docs/impulse-data/ai-evidence/'+id+'.json'),text=JSON.stringify(proof);
  assert.equal(proof.provenance.context_verified,true);assert.equal(proof.cited_facts.length,1);assert.equal(proof.cited_facts[0].id,'F1');assert.equal(proof.reviews[0].status,'quality_flag');
  assert.deepEqual(proof.missing_citations,[]);assert.ok(!/PRIVATE|private|route_id|hidden_reasoning|system_prompt|user_prompt/.test(text));
  assert.equal(proof.context,undefined);assert.equal(proof.entry,undefined);
 }finally{cleanup(root)}
});
test('disabled public AI feed exports no model titles, anchors or evidence files',async()=>{
 const root=fixture();try{
  write(root,'research/AI_FEED.json',{public_enabled:false});const result=await buildPage(root,{asOf:at});
  assert.equal(result.coverage.ai_observations,0);assert.ok(!result.files.some(f=>f.includes('ai-evidence/')));
  assert.ok(!readImpulses(root).items.some(i=>i.kind==='ai_observation'));
 }finally{cleanup(root)}
});
test('column encoding preserves all fields exactly including missing, null and per-title location cues',()=>{
 const rows=[{id:'a',title:'First',clock:{at:'2026-09-27T12:00:00Z',end:null},geo:{scope:'belgrade',matched_text:'u Novom Beogradu',candidates:[{name:'Novi Beograd',eligible:true}]},value:0},
  {id:'b',title:'Second',clock:{at:'2026-09-27T12:00:00Z',end:null},geo:{scope:'belgrade',matched_text:'na Novom Beogradu',candidates:[{name:'Novi Beograd',eligible:true}]},value:null,flag:false},
  {id:'c',title:'Third',clock:{at:'2026-09-27T11:00:00Z',end:null},geo:{scope:'unknown',matched_text:null},flag:true}];
 const packed=JSON.parse(JSON.stringify(packItems(rows)));
 assert.deepEqual(unpackItems(packed.columns,packed.records),rows);
 assert.deepEqual(unpackItems(...Object.values(packItems([]))),[]);
 assert.ok(packed.columns.find(c=>c.key==='value').values.includes(null));
});
test('large repeated provenance is sent once without duplicating whole records across windows',()=>{
 const rows=Array.from({length:250},(_,i)=>({id:'headline-'+i,title:'Title '+i,url:'https://example.test/'+i,
  source:'Official source',limitation:'A collected headline is not proof of an event. '.repeat(20),
  geo:{scope:'unknown',reason:'insufficient_location_evidence',candidates:[],method:'same-deterministic-rule'},
  evidence:{source_url:'https://example.test/archive',raw_sha256:'f'.repeat(64)},clock:{at:'2026-09-27T12:00:00Z',start:'2026-09-27T12:00:00Z',end:null,basis:'publication_time'}}));
 const packed=packItems(rows),before=Buffer.byteLength(JSON.stringify(rows)),after=Buffer.byteLength(JSON.stringify(packed));
 assert.ok(after<before*.2,after+' vs '+before);assert.deepEqual(unpackItems(packed.columns,packed.records),rows);
});
test('malformed dictionary references, record widths and duplicate columns fail closed',()=>{
 assert.throws(()=>unpackItems([{key:'id',values:['one']}],[[2]]),/invalid_impulse_reference/);
 assert.throws(()=>unpackItems([{key:'id'}],[[]]),/invalid_impulse_record/);
 assert.throws(()=>unpackItems([{key:'id'},{key:'id'}],[['a','b']]),/invalid_impulse_column/);
 assert.throws(()=>decodeImpulses({schema:'beops-public-impulses/v1'}),/unsupported_impulse_encoding/);
});
test('missing canonical archive or mismatched frozen clock refuses public generation',async()=>{
 const root=fixture();try{
  await assert.rejects(buildPage(root,{asOf:'2026-09-28T12:00:00Z'}),/snapshot_time_mismatch/);assert.ok(!fs.existsSync(path.join(root,'docs')));
  fs.renameSync(path.join(root,'public/headlines.json'),path.join(root,'public/saved-headlines.json'));
  await assert.rejects(buildPage(root,{asOf:at}),/ENOENT/);assert.ok(!fs.existsSync(path.join(root,'docs')));
 }finally{cleanup(root)}
});
