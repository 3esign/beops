'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {buildContext,validateOutput,readJSON,hash}=require('./ai_feed_context');
const providers=require('./ai_feed_providers');
const {classifyFailure}=require('./ai_feed_catalogue');
const ROOT=path.resolve(__dirname,'..');
function durable(file,text,exclusive=false){
  fs.mkdirSync(path.dirname(file),{recursive:true});
  const fd=fs.openSync(file,exclusive?'wx':'w');try{fs.writeFileSync(fd,text);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
}
function atomic(file,value){const tmp=file+'.'+process.pid+'.tmp';durable(tmp,JSON.stringify(value));fs.renameSync(tmp,file);}
function immutableBytes(file,bytes){
  if(fs.existsSync(file)){if(fs.readFileSync(file,'utf8')!==bytes)throw Error('immutable_conflict');return;}
  const tmp=file+'.'+process.pid+'.'+crypto.randomBytes(4).toString('hex')+'.tmp';
  durable(tmp,bytes,true);
  try{fs.linkSync(tmp,file);}catch(e){if(e.code!=='EEXIST'||fs.readFileSync(file,'utf8')!==bytes)throw e;}
  finally{fs.unlinkSync(tmp);}
}
function immutable(file,value){immutableBytes(file,JSON.stringify(value));}
function append(file,value){
  fs.mkdirSync(path.dirname(file),{recursive:true});
  const fd=fs.openSync(file,'a+');
  try{
    const size=fs.fstatSync(fd).size;
    if(size){
      const length=Math.min(size,262144),tail=Buffer.alloc(length);fs.readSync(fd,tail,0,length,size-length);
      if(tail[length-1]!==10){
        const at=tail.lastIndexOf(10),start=size-length+at+1;
        if(at<0&&size>length)throw Error('journal_tail_too_large');
        const fragment=tail.subarray(at+1),digest=crypto.createHash('sha256').update(fragment).digest('hex');
        const archive=path.join(path.dirname(file),'journal-fragments',digest+'.txt');
        if(!fs.existsSync(archive))durable(archive,fragment,true);
        fs.truncateSync(file,start);
        fs.writeSync(fd,JSON.stringify({event:'journal_tail_recovered',at:new Date().toISOString(),sha256:digest,bytes:fragment.length})+'\n');
      }
    }
    fs.writeSync(fd,JSON.stringify(value)+'\n');fs.fsyncSync(fd);
  }finally{fs.closeSync(fd);}
}
function acquire(directory){
  const file=path.join(directory,'worker.lock');fs.mkdirSync(directory,{recursive:true});
  const temp=file+'.'+process.pid+'.'+crypto.randomBytes(4).toString('hex')+'.tmp';
  durable(temp,JSON.stringify({schema:'beops-ai-lock/v1',pid:process.pid,at:new Date().toISOString()}),true);
  try{fs.linkSync(temp,file);}
  catch(e){
    if(e.code!=='EEXIST')throw e;
    let old;try{old=readJSON(file,4096);}catch{return null;}
    if(old.schema!=='beops-ai-lock/v1'||!Number.isInteger(old.pid))return null;
    try{process.kill(old.pid,0);return null;}catch(err){if(err.code!=='ESRCH')return null;}
    fs.unlinkSync(file);return acquire(directory);
  }finally{fs.unlinkSync(temp);}
  return ()=>{fs.unlinkSync(file);};
}
function stateFromReceipts(directory){
  const state={providers:{},models:{},last_success:null};
  const dir=path.join(directory,'receipts');
  const attempts=new Map();
  for(const name of fs.existsSync(dir)?fs.readdirSync(dir).sort():[]){
    if(!name.endsWith('-finish.json')&&!name.endsWith('-start.json'))continue;
    const r=readJSON(path.join(dir,name),65536);
    if(name.endsWith('-finish.json')||!attempts.has(r.id))attempts.set(r.id,r);
  }
  for(const r of attempts.values()){
    const previous=state.providers[r.provider];
    if(!previous||r.at>previous.at)state.providers[r.provider]={at:r.at,next_at:r.next_at,state:r.state,model:r.model,failure_count:r.failure_count||0};
    if(r.state==='accepted'&&(!state.last_success||r.at>state.last_success))state.last_success=r.at;
    const key=r.provider+'|'+r.model;if(!state.models[key]||r.at>state.models[key].at)state.models[key]=r;
  }
  const newest=allEntries(directory)[0];if(newest)state.last_success=newest.at;
  return state;
}
function allEntries(directory){const d=path.join(directory,'entries');return (fs.existsSync(d)?fs.readdirSync(d):[]).filter(n=>/^[a-f0-9]{32}\.json$/.test(n)).map(n=>readJSON(path.join(d,n),65536)).sort((a,b)=>b.at.localeCompare(a.at)||a.id.localeCompare(b.id));}
function exportFeed(root=ROOT, now=new Date()){
  const config=readJSON(path.join(root,'research/AI_FEED.json'));
  const dir=path.join(root,'runtime/ai-feed'),out=path.join(root,'docs/ai-feed');
  fs.mkdirSync(out,{recursive:true});
  const entries=config.public_enabled?allEntries(dir):[];
  const reviews={},reviewFile=path.join(root,'research/AI_FEED_REVIEWS.json');
  if(fs.existsSync(reviewFile)){
    const doc=readJSON(reviewFile,1024*1024);
    if(doc.schema!=='beops-ai-reviews/v1'||!Array.isArray(doc.records))throw Error('invalid_review_ledger');
    for(const r of doc.records){
      if(!/^[a-f0-9]{32}$/.test(r.entry_id)||r.status!=='quality_flag'||
        !/^[a-f0-9]{64}$/.test(r.entry_sha256)||!Number.isFinite(Date.parse(r.reviewed_at))||
        !['reason_sr','reason_en','reviewer'].every(k=>typeof r[k]==='string'&&r[k].length>0&&r[k].length<1000))throw Error('invalid_review');
      const entry=entries.find(e=>e.id===r.entry_id);
      if(entry&&hash(entry)!==r.entry_sha256)throw Error('review_entry_hash_mismatch');
      if(entry)(reviews[r.entry_id]||=[]).push(r);
    }
  }
  let status={state:'not_started',at:null,providers:[]};
  if(fs.existsSync(path.join(dir,'status.json')))status=readJSON(path.join(dir,'status.json'),65536);
  const pageSize=20,pages=[];
  for(let i=Math.floor((entries.length-1)/pageSize)*pageSize;i>=0;i-=pageSize){
    const page={schema:'beops-ai-page/v1',entries:entries.slice(i,i+pageSize),next:pages[0]?.filename||null};
    const filename='page-'+hash(page).slice(0,24)+'.json';pages.unshift({filename,page});
    atomic(path.join(out,filename),page);
  }
  for(const e of entries){
    const packet=readJSON(path.join(dir,'contexts',e.context_hash+'.json'),65536);
    if(hash(packet)!==e.context_hash)throw Error('context_hash_mismatch');
    const system=fs.readFileSync(path.join(dir,'prompts',e.prompt_hash+'.txt'),'utf8');
    if(hash(system)!==e.prompt_hash)throw Error('prompt_hash_mismatch');
    atomic(path.join(out,e.id+'.json'),{entry:e,system_prompt:system,
      reviews:reviews[e.id]||[],
      user_prompt:(e.instruction_delivery==='user_preamble'?system+'\n\n':'')+'Write your monologue about this frozen situation. Data packet:\n'+JSON.stringify(packet),context:packet,
      instruction_delivery:e.instruction_delivery||'system',
      provider_internal_instructions:'Not exposed by the provider; no claim of access to hidden reasoning.'});
  }
  atomic(path.join(out,'latest.json'),{schema:'beops-ai-index/v1',exported_at:now.toISOString(),total:entries.length,
    first_page:pages[0]?.filename||null,latest_at:entries[0]?.at||null,status,
    reviews,review_revision:hash(reviews),
    target_gap_minutes:60,experimental:true,scope:'AI interpretation; automatic checks do not establish factual truth.'});
  return {total:entries.length,status:status.state};
}
async function tick(root=ROOT, options={}){
  const now=options.now||new Date(), config=readJSON(path.join(root,'research/AI_FEED.json'));
  const deadline=Date.now()+Math.min(120,config.job_timeout_seconds)*1000;
  const dir=path.join(root,'runtime/ai-feed');
  if(!config.enabled||fs.existsSync(path.join(root,'runtime/MAINTENANCE'))||fs.existsSync(path.join(dir,'PAUSED')))return {state:'paused'};
  if(!Array.isArray(config.providers)||config.providers.some(p=>!p.id||!Number.isFinite(p.interval_minutes)||p.interval_minutes<5||p.interval_minutes>55))throw Error('invalid_provider_cadence');
  const release=acquire(dir);if(!release)return {state:'busy'};
  try{
    // A dead worker leaves a start receipt. Preserve that interrupted attempt; never silently retry it.
    const receiptDirectory=path.join(dir,'receipts');
    for(const name of fs.existsSync(receiptDirectory)?fs.readdirSync(receiptDirectory):[]){
      if(!name.endsWith('-start.json'))continue;
      const finishPath=path.join(receiptDirectory,name.replace('-start.json','-finish.json'));
      if(fs.existsSync(finishPath))continue;
      const prior=readJSON(path.join(receiptDirectory,name),65536);
      const accepted=fs.existsSync(path.join(dir,'entries',prior.id+'.json'));
      const recovery={...prior,state:accepted?'accepted':'interrupted',recovered_at:now.toISOString(),reason:'Previous worker ended before its finish receipt.'};
      immutable(finishPath,recovery);append(path.join(dir,'events.jsonl'),recovery);
    }
    // The immutable finishes are authority; a lost mutable cache cannot repeat an accepted slot.
    const state=stateFromReceipts(dir), checked=[];
    const day=now.toISOString().slice(0,10),receipts=path.join(dir,'receipts'),counts={};
    let attemptsToday=0;
    for(const name of fs.existsSync(receipts)?fs.readdirSync(receipts):[]){
      if(!name.startsWith(day)||!name.endsWith('-start.json'))continue;
      const terminal=path.join(receipts,name.replace('-start.json','-finish.json'));
      if(fs.existsSync(terminal)&&readJSON(terminal,65536).state==='deferred_capacity')continue;
      const start=readJSON(path.join(receipts,name),65536);counts[start.provider]=(counts[start.provider]||0)+1;attemptsToday++;
    }
    for(const p of config.providers){
      let candidate=p;
      const prior=state.providers[p.id];
      if(p.models){
        let models=p.models.filter(m=>{const r=state.models[p.id+'|'+m];return !(r?.reason==='provider_http_429'&&+now-Date.parse(r.at)<3600000);});
        if(prior?.state==='failed'&&models.includes(prior.model)){
          const i=(models.indexOf(prior.model)+1)%models.length;models=[...models.slice(i),...models.slice(0,i)];
        }else if(prior?.state==='deferred_capacity'&&models.includes(prior.model))models=[prior.model,...models.filter(m=>m!==prior.model)];
        candidate={...p,models};
      }
      const ready=(counts[p.id]||0)>=(config.max_attempts_per_provider_per_day||48)?{ready:false,reason:'daily_provider_budget'}:await (options.availability||providers.availability)(candidate,{state,now,directory:dir});
      checked.push({...p,...ready,last_at:state.providers[p.id]?.at||null,next_at:state.providers[p.id]?.next_at||null});
    }
    let eligible=checked.filter(p=>p.ready && (!p.next_at||Date.parse(p.next_at)<=+now || options.retry && ['failed','deferred_capacity'].includes(state.providers[p.id]?.state)));
    eligible.sort((a,b)=>(a.last_at?Date.parse(a.last_at):0)-(b.last_at?Date.parse(b.last_at):0)||a.offset_minutes-b.offset_minutes);
    const status={schema:'beops-ai-status/v1',at:now.toISOString(),state:'waiting',last_success:state.last_success,
      providers:checked.map(p=>({id:p.id,label:p.label,ready:p.ready,reason:p.reason||null,interval_minutes:p.interval_minutes,last_at:p.last_at,next_at:p.next_at,selected_model:p.model||null,route_id:p.route_id||null,candidate_count:p.candidate_count??null,held_count:p.held_count??null,qualification_held:p.qualification_held||0})),
      global_min_interval_minutes:config.global_min_interval_minutes||0,
      next_generation_at:state.last_success?new Date(Date.parse(state.last_success)+(config.global_min_interval_minutes||0)*60000).toISOString():null,
      overdue:!state.last_success||+now-Date.parse(state.last_success)>3600000};
    const recordStatus=()=>{atomic(path.join(dir,'status.json'),status);append(path.join(dir,'events.jsonl'),{at:status.at,event:'tick',state:status.state,overdue:status.overdue,providers:status.providers});};
    if(status.global_min_interval_minutes>0&&status.next_generation_at&&Date.parse(status.next_generation_at)>+now){status.state='global_interval';recordStatus();return status;}
    if(!eligible.length){status.state=checked.some(p=>p.ready)?'waiting':'providers_unavailable';recordStatus();return status;}
    if(attemptsToday>=config.max_attempts_per_day){status.state='daily_budget';recordStatus();return status;}
    let packet;try{packet=(options.buildContext||buildContext)(root,now,config);}catch(e){status.state=e.message;if(e.diagnostic)status.diagnostic=e.diagnostic;recordStatus();return status;}
    const promptVersion=config.prompt_version||1;
    if(![1,2].includes(promptVersion))throw Error('invalid_prompt_version');
    const provider=eligible[0],system=fs.readFileSync(path.join(root,'research/03-models/AI_FEED_SYSTEM_PROMPT_v'+promptVersion+'.txt'),'utf8');
    const contextHash=hash(packet),promptHash=hash(system),id=crypto.randomBytes(16).toString('hex');
    immutable(path.join(dir,'contexts',contextHash+'.json'),packet);
    const promptFile=path.join(dir,'prompts',promptHash+'.txt');immutableBytes(promptFile,system);
    const prefix=now.toISOString().replace(/:/g,'-')+'-'+id;
    const start={schema:'beops-ai-attempt/v1',id,at:now.toISOString(),provider:provider.id,model:provider.model,
      next_at:new Date(+now+provider.interval_minutes*60000).toISOString(),route_id:provider.route_id||null,
      context_hash:contextHash,prompt_hash:promptHash,state:'started'};
    immutable(path.join(receipts,prefix+'-start.json'),start);append(path.join(dir,'events.jsonl'),start);
    // Persist interruption accounting BEFORE invoking a provider; recovery honours this attempt's cooldown.
    let finish={...start,at:now.toISOString(),state:'interrupted',failure_count:state.providers[provider.id]?.failure_count||0,next_at:new Date(+now+provider.interval_minutes*60000).toISOString()};
    immutable(path.join(receipts,prefix+'-intent.json'),finish);
    let response;
    const cwd=path.join(dir,'work',id);fs.mkdirSync(cwd,{recursive:true});
    try{
      const remaining=deadline-Date.now();if(remaining<1000)throw Error('job_deadline');
      response=await (options.generate||providers.generate)(provider,provider.model,packet,system,cwd,remaining);
      // Save exact final response before parsing or validating it, including rejected attempts.
      immutable(path.join(dir,'responses',id+'.json'),response);
      let value;try{value=provider.adapter==='antigravity-cli'?providers.parseAntigravity(response.text):providers.parseObject(response.text);}catch{throw Error('response_not_json');}
      const validation=validateOutput(value,packet,config.max_output_characters);
      finish.validation=validation;
      if(!validation.ok)throw Error('validation_rejected');
      const entry={schema:'beops-ai-entry/v1',id,at:(options.clock||(()=>new Date()))().toISOString(),as_of:packet.as_of,provider:provider.id,
        provider_label:provider.label,model:response.model,identity:response.identity,transport:response.transport,
        context_hash:contextHash,prompt_hash:promptHash,validation,content:value,route_id:provider.route_id||null,
        instruction_delivery:response.instruction_delivery||'system'};
      immutable(path.join(dir,'entries',id+'.json'),entry);
      finish.state='accepted';finish.failure_count=0;finish.at=entry.at;status.last_success=entry.at;status.overdue=false;
      status.next_generation_at=new Date(Date.parse(entry.at)+(config.global_min_interval_minutes||0)*60000).toISOString();
    }catch(e){finish.state=e.code==='EMINDLOCK'?'deferred_capacity':'failed';finish.reason=String(e.message||e.code||'provider_failed').slice(0,160);
      if(finish.state==='failed'){
        finish.failure_count++;
        finish.failure_kind=e.failureKind||classifyFailure(finish.reason);
        finish.cooldown_until=new Date(+now+(['rate-limit','auth','unsupported-model'].includes(finish.failure_kind)?60:15)*60000).toISOString();
      }
      const retryMinutes=finish.state==='deferred_capacity'?5:Math.min(provider.interval_minutes,5*2**Math.min(finish.failure_count-1,4));
      finish.next_at=new Date(+now+retryMinutes*60000).toISOString();
    }
    immutable(path.join(receipts,prefix+'-finish.json'),finish);append(path.join(dir,'events.jsonl'),finish);
    status.state=finish.state;status.providers.find(p=>p.id===provider.id).last_at=finish.at;
    status.providers.find(p=>p.id===provider.id).next_at=finish.next_at;recordStatus();
    return finish;
  }finally{release();}
}
module.exports={tick,exportFeed,acquire,stateFromReceipts,allEntries,atomic,immutable,append};
if(require.main===module){const command=process.argv[2]||'tick';
  Promise.resolve(command==='export'?exportFeed():tick()).then(r=>console.log(JSON.stringify(r))).catch(e=>{console.error(e.message);process.exitCode=1;});}
