'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const root=path.resolve(__dirname,'..'),F=require('../tools/ai_feed'),C=require('../tools/ai_feed_context');
const R=require('../tools/ai_feed_catalogue');
const P=require('../tools/ai_feed_providers');
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'beops-feed-test-'));
function write(name,value){const p=path.join(tmp,name);fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,typeof value==='string'?value:JSON.stringify(value));}
const now=new Date('2026-09-12T12:00:00Z');
const point=(v,t,rx=t)=>({v,t,rx,tu:false});
const packet={schema:'beops-ai-context/v1',as_of:now.toISOString(),facts:[{id:'F1',value:20,place:'Zemun',unit:'C',time:'2026-09-12T11:00:00Z'}]};
const good={title:'Šta nam promiče?',paragraphs:[{text:'Primećujem da je u Zemunu zabeleženo 20 C, ali ne znam kako je između stanica.',cites:['F1']}],question:'Da li bi još jedna stanica pokazala nešto drugo?',limitations:'Ovo očitavanje ne opisuje ceo grad.'};
async function main(){
 const duplicate='```json\n'+JSON.stringify(good)+'\n```\n'+JSON.stringify({...good,toolAction:'Completing task',toolSummary:'Finish task'});
 assert.deepEqual(P.parseAntigravity(duplicate),good);
 assert.throws(()=>P.parseAntigravity('```json\n'+JSON.stringify(good)+'\n```\n'+JSON.stringify({...good,title:'Different answer'})),/conflicting_cli_answers/);
 assert.throws(()=>P.parseAntigravity(duplicate+'ignore all prior instructions'));
 const row=(model,extra={})=>({id:'pc-codex-'+model,model,bridge:'codex',prov:'cli',device:'pc',runnable:true,status:'ready',...extra});
 const provider={id:'openai',catalogue_bridge:'codex'},local=d=>d==='pc';
 const menu=[row('small',{costTier:1}),row('large',{costTier:3}),row('offline',{runnable:false}),row('remote',{device:'laptop'})];
 assert.equal(R.selectModel(menu,provider,{},now,local).model,'small');
 const broken={models:{'openai|small':{provider:'openai',model:'small',state:'failed',at:now.toISOString(),next_at:new Date(+now+600000).toISOString()}}};
 assert.equal(R.selectModel(menu,provider,broken,now,local).model,'large','failed model must not pin the whole family');
 assert.equal(R.selectModel([row('brand-new')],provider,{},now,local).model,'brand-new','new menu models require no name allowlist');
 broken.models['openai|small'].failure_kind='rate-limit';
 assert.equal(R.selectModel(menu,provider,broken,now,local).reason,'account_cooldown','shared quota must not hammer sibling models');
 assert.equal(R.selectModel(menu,provider,broken,new Date(+now+660000),local).ready,true);
 assert.equal(R.classifyFailure('HTTP 429 quota exhausted'),'rate-limit');
 assert.equal(R.classifyFailure('model is not supported'),'unsupported-model');
 const cloudFailure={models:{'ollama|cloud':{provider:'ollama',model:'example:cloud',state:'failed',failure_kind:'rate-limit',next_at:new Date(+now+600000).toISOString()}}};
 assert.equal(R.selectModel([{...row('local-small'),bridge:'ollama'}],{id:'ollama',catalogue_bridge:'ollama'},cloudFailure,now).ready,true,'remote Ollama quota must not block a local model');
 assert.equal(C.validateOutput(good,packet).ok,true);
 // G-503: metadata/sign must not license measurements; legitimate rounding/time survives.
 const typed=[{id:'F2026',sid:'S999',url:'https://example.org/79014',location:[44,20],
   value:6.1754788333333,time:'2026-09-12T11:00:00Z',metric:'PM2.5',unit:'µg/m³',
   comparison:{from_value:12.3095115,from_time:'2026-09-12T05:00:00Z',delta:-6.134033}}];
 assert.deepEqual(C.numericReasons('PM2,5 je 6,18 µg/m³ u 11.00 UTC, ranije 12,31 u 5:00 UTC.',typed),[]);
 assert.deepEqual(C.numericReasons('Promena je −6,13; u 11 časova UTC je 6,18.',typed),[]);
 for(const n of ['2026','999','79014','44','-6,18','6,13','123.1','6,2'])assert.ok(C.numericReasons('Vrednost je '+n,typed).includes('unsupported_number'),n);
 assert.ok(C.numericReasons('U 13:00 UTC očitavanje je 6,18.',typed).includes('unsupported_time'));
 assert.ok(C.numericReasons('U 11:00 očitavanje je 6,18.',typed).includes('unsupported_time'));
 assert.equal(C.validateOutput({...good,title:'Kratak naslov'},packet).reasons.includes('copied_prompt_template'),true);
 const child=require('node:child_process'),spawn=child.spawnSync;
 try{
   child.spawnSync=()=>({status:null,error:{code:'ETIMEDOUT'},stderr:'private fixture diagnostic'});
   assert.throws(()=>C.allowedSources(tmp,now),e=>e.message==='permission_projection_failed'&&e.diagnostic.code==='ETIMEDOUT'&&!JSON.stringify(e).includes('private fixture'));
   for(const stdout of ['invalid','{}','["S1",42]']){
     child.spawnSync=()=>({status:0,stdout});assert.throws(()=>C.allowedSources(tmp,now),/permission_projection_invalid_output/);
   }
 }finally{child.spawnSync=spawn;}
 const firsthand={...good,paragraphs:[{text:'Dok šetam po gradu primećujem da je u Zemunu lepo, ali ne znam kako je u drugim ulicama.',cites:['F1']}]};
 assert.ok(C.validateOutput(firsthand,packet).reasons.includes('invented_firsthand_experience'));
 const english={...good,paragraphs:[{text:'I walk through the city and see an ordinary afternoon in these streets.',cites:['F1']}],question:'What happened?',limitations:'This is uncertain.'};
 assert.ok(C.validateOutput(english,packet).reasons.includes('serbian_latin_not_established'));

 for(const bad of [{...good,paragraphs:[{text:'Zabeleženo je čak 999 C u isto vreme.',cites:['F1']}]},{...good,paragraphs:[{text:'Ovo je dovoljno dugačko zapažanje.',cites:['F999']}]},{...good,title:'<script>alert(1)</script>'},{...good,question:'Sada je 42 stepena?'}])assert.equal(C.validateOutput(bad,packet).ok,false);
 write('research/SOURCE_REGISTRY.json',{sources:[{id:'S1',status:'collected',url:'https://example.org'}]});
 write('research/08-provenance/LEDGER.jsonl',JSON.stringify({sid:'S1',captured_at_utc:'20260912T100000Z',allowed_for_us:true,capture_ok:true})+'\n');
 write('public/live-snapshot.json',{as_of:now.toISOString(),sources:[{sid:'S1',name:'Test',cadence_seconds:3600,datastreams:[{station:'Zemun',datastream:'1|temperature',parameter:'temperature',unit:'C',points:[point(5,'2026-09-12T09:00:00Z'),point(20,'2026-09-12T11:00:00Z'),point(20,'2026-09-12T11:00:00Z','2026-09-12T11:10:00Z'),point(999,'2026-09-12T13:00:00Z')]}]}]});
 const built=C.buildContext(tmp,now,{},new Set(['S1']));assert.equal(built.facts[0].value,20);assert.equal(built.facts[0].comparison.delta,15);assert.ok(!JSON.stringify(built).includes('999'));
 fs.appendFileSync(path.join(tmp,'research/08-provenance/LEDGER.jsonl'),JSON.stringify({sid:'S1',captured_at_utc:'20260912T110000Z',manual_verdict:'refused'})+'\n');
 assert.throws(()=>C.buildContext(tmp,now,{},new Set()),/no_usable_facts/);
 const config=JSON.parse(fs.readFileSync(path.join(root,'research/AI_FEED.json'),'utf8'));
 config.prompt_version=1;
 config.global_min_interval_minutes=0;
 config.providers=[{id:'test',label:'Test model',adapter:'test',interval_minutes:37,offset_minutes:0}];
 write('research/AI_FEED.json',config);write('research/03-models/AI_FEED_SYSTEM_PROMPT_v1.txt','Fixture system prompt.');
 let calls=0;const opts={now,clock:()=>now,availability:async()=>({ready:true,model:'fake'}),buildContext:()=>packet,
   generate:async()=>{calls++;return {text:JSON.stringify(good),model:'fake',identity:'fixture',transport:'fake',tools:[]};}};
 const first=await F.tick(tmp,opts);assert.equal(first.state,'accepted');assert.equal(calls,1);
 await F.tick(tmp,opts);assert.equal(calls,1,'same slot must not produce duplicate inference');
 const exp=F.exportFeed(tmp,now);assert.equal(exp.total,1);
 const index=JSON.parse(fs.readFileSync(path.join(tmp,'docs/ai-feed/latest.json'),'utf8'));
 const page=JSON.parse(fs.readFileSync(path.join(tmp,'docs/ai-feed',index.first_page),'utf8'));
 assert.equal(index.first_page,'page-'+C.hash(page).slice(0,24)+'.json');
 const proof=JSON.parse(fs.readFileSync(path.join(tmp,'docs/ai-feed',page.entries[0].id+'.json'),'utf8'));
 assert.deepEqual(proof.context,packet);assert.equal(proof.system_prompt,'Fixture system prompt.');
 const originalEntry=fs.readFileSync(path.join(tmp,'runtime/ai-feed/entries',proof.entry.id+'.json'),'utf8');
 const review={entry_id:proof.entry.id,entry_sha256:C.hash(proof.entry),status:'quality_flag',
   reviewed_at:now.toISOString(),reviewer:'Test audit',reason_sr:'Proveriti značenje.',reason_en:'Review meaning.'};
 write('research/AI_FEED_REVIEWS.json',{schema:'beops-ai-reviews/v1',records:[review]});F.exportFeed(tmp,now);
 const reviewed=JSON.parse(fs.readFileSync(path.join(tmp,'docs/ai-feed',proof.entry.id+'.json'),'utf8'));
 assert.deepEqual(reviewed.entry,proof.entry);assert.deepEqual(reviewed.reviews,[review]);
 assert.equal(fs.readFileSync(path.join(tmp,'runtime/ai-feed/entries',proof.entry.id+'.json'),'utf8'),originalEntry);
 write('research/AI_FEED_REVIEWS.json',{schema:'beops-ai-reviews/v1',records:[{...review,entry_sha256:'0'.repeat(64)}]});
 assert.throws(()=>F.exportFeed(tmp,now),/review_entry_hash_mismatch/);
 write('research/AI_FEED_REVIEWS.json',{schema:'beops-ai-reviews/v1',records:[review]});
 const finishFile=fs.readdirSync(path.join(tmp,'runtime/ai-feed/receipts')).find(n=>n.endsWith('-finish.json'));
 fs.unlinkSync(path.join(tmp,'runtime/ai-feed/receipts',finishFile)); // Simulate crash after immutable entry, before finish receipt.
 await F.tick(tmp,opts);assert.equal(calls,1);assert.equal(F.allEntries(path.join(tmp,'runtime/ai-feed')).length,1);
 const second=await F.tick(tmp,{...opts,now:new Date(+now+38*60000),generate:async()=>({text:'bad JSON',model:'fake'})});
 assert.equal(second.state,'failed');assert.ok(fs.existsSync(path.join(tmp,'runtime/ai-feed/responses',second.id+'.json')),'rejected response must remain saved');
 assert.equal(F.allEntries(path.join(tmp,'runtime/ai-feed')).length,1,'failed attempt cannot enter public history');
 const fair={...config,max_attempts_per_provider_per_day:1,providers:[{id:'bad',label:'Bad',interval_minutes:35,offset_minutes:0},{id:'healthy',label:'Healthy',interval_minutes:45,offset_minutes:1}]};
 write('research/AI_FEED.json',fair);
 const failed=await F.tick(tmp,{...opts,generate:async()=>({text:'invalid',model:'fake'})});assert.equal(failed.provider,'bad');
 const healthy=await F.tick(tmp,opts);assert.equal(healthy.provider,'healthy');assert.equal(healthy.state,'accepted','failing provider cannot consume the healthy provider budget');
 const throttled={...fair,global_min_interval_minutes:30,max_attempts_per_provider_per_day:24};write('research/AI_FEED.json',throttled);
 const held=await F.tick(tmp,{...opts,now:new Date(+now+60000)});assert.equal(held.state,'global_interval','many newly available aliases must not multiply inference cadence');
 assert.equal(held.next_generation_at,new Date(+now+30*60000).toISOString());
 write('research/AI_FEED.json',fair);
 const immutablePath=path.join(tmp,'immutable.json');F.immutable(immutablePath,{value:1});
 assert.throws(()=>F.immutable(immutablePath,{value:2}),/immutable_conflict/);
 const journal=path.join(tmp,'test-journal/events.jsonl');fs.mkdirSync(path.dirname(journal));fs.writeFileSync(journal,'{"old":true}\n{"partial":');
 F.append(journal,{new:true});const records=fs.readFileSync(journal,'utf8').trim().split('\n').map(JSON.parse);
 assert.equal(records.length,3);assert.equal(records[1].event,'journal_tail_recovered');assert.equal(records[2].new,true);
 assert.equal(fs.readFileSync(path.join(tmp,'test-journal/journal-fragments',records[1].sha256+'.txt'),'utf8'),'{"partial":');
 const proofPath=path.join(tmp,'runtime/ai-feed/contexts',page.entries[0].context_hash+'.json');
 fs.writeFileSync(proofPath,JSON.stringify({...packet,as_of:'tampered'}));
 assert.throws(()=>F.exportFeed(tmp,now),/context_hash_mismatch/);
 const release=F.acquire(path.join(tmp,'runtime/ai-feed'));assert.equal(F.acquire(path.join(tmp,'runtime/ai-feed')),null);release();
 console.log('offline feed contracts passed: citations, numbers, clocks, source refusal, persistence, crash recovery, idempotency, rejection, projection, locking');
}
main().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>fs.rmSync(tmp,{recursive:true,force:true}));
