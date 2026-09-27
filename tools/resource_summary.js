'use strict';
// Reads only measured receipts. Historical provider usage is separate and never added to cycle totals.
const fs=require('node:fs'),path=require('node:path');
const {tokenUsage}=require('./resource_meter');
const ROOT=path.resolve(__dirname,'..');
const TOKEN_FIELDS=['input_tokens','output_tokens','cached_input_tokens','reasoning_tokens','cache_creation_input_tokens','provider_total_tokens'];
function validFinish(row){
  const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
  const count=x=>Number.isSafeInteger(x)&&x>=0;
  return ['wall_seconds','cpu_seconds'].every(key=>Number.isFinite(row[key])&&row[key]>=0)&&
    (row.peak_rss_bytes===null||count(row.peak_rss_bytes))&&typeof row.outcome==='string'&&
    object(row.tokens)&&object(row.http)&&typeof row.tokens.state==='string'&&
    count(row.tokens.reported_calls)&&(row.tokens.unreported_calls===null||count(row.tokens.unreported_calls))&&
    TOKEN_FIELDS.every(key=>row.tokens[key]===undefined||row.tokens[key]===null||count(row.tokens[key]))&&
    ['request_attempts','response_body_bytes','body_reports','unreported_bodies'].every(key=>count(row.http[key]))&&
    row.http.request_attempts===row.http.body_reports+row.http.unreported_bodies;
}
function files(directory){return fs.existsSync(directory)?fs.readdirSync(directory).filter(x=>x.endsWith('.json')).sort():[];}
function read(file,errors){try{const stat=fs.statSync(file);if(stat.size>2*1024*1024)throw Error('oversize');return JSON.parse(fs.readFileSync(file,'utf8').replace(/^\uFEFF/,''));}catch{errors.push(path.basename(file));return null;}}
function sumKnown(rows,key){const values=rows.map(x=>x?.[key]).filter(x=>Number.isFinite(x)&&x>=0);return values.length?values.reduce((a,b)=>a+b,0):null;}
function tokenTotals(rows){
  const output={reported_calls:0,unreported_calls:0,unknown_call_count_cycles:0,field_reports:{}};
  for(const key of TOKEN_FIELDS){output[key]=sumKnown(rows,key);output.field_reports[key]=rows.filter(r=>Number.isFinite(r?.[key])).length;}
  for(const row of rows){output.reported_calls+=row.reported_calls||0;if(row.unreported_calls===null&&row.state!=='not_applicable')output.unknown_call_count_cycles++;else output.unreported_calls+=row.unreported_calls||0;}
  return output;
}
function totals(starts,finishes){
  const done=starts.map(x=>finishes.get(x.id)).filter(Boolean);
  return {started_cycles:starts.length,finished_cycles:done.length,unfinished_cycles:starts.length-done.length,
    wall_seconds:sumKnown(done,'wall_seconds'),cpu_seconds:sumKnown(done,'cpu_seconds'),
    peak_rss_bytes:done.some(x=>Number.isFinite(x.peak_rss_bytes))?Math.max(...done.map(x=>x.peak_rss_bytes||0)):null,
    request_attempts:sumKnown(done.map(x=>x.http),'request_attempts'),
    response_body_bytes:sumKnown(done.map(x=>x.http),'response_body_bytes'),
    unreported_bodies:sumKnown(done.map(x=>x.http),'unreported_bodies'),
    tokens:tokenTotals(done.map(x=>x.tokens)),outcomes:done.reduce((counts,x)=>{counts[x.outcome]=(counts[x.outcome]||0)+1;return counts;},{}),
    electricity_wh:null,money:null};
}
function history(root,now,errors){
  const directory=path.join(root,'runtime/ai-feed'),attempts=new Map();
  for(const name of files(path.join(directory,'receipts'))){
    if(!name.endsWith('-start.json')&&!name.endsWith('-finish.json'))continue;
    const row=read(path.join(directory,'receipts',name),errors);if(!/^[a-f0-9]{32}$/.test(row?.id||''))continue;
    const recordedAt=Date.parse(row.recovered_at||row.at);
    if(!Number.isFinite(recordedAt)||recordedAt>+now)continue;
    const terminal=name.endsWith('-finish.json');
    if(!attempts.has(row.id)||terminal)attempts.set(row.id,{...row,has_terminal_receipt:terminal});
  }
  const rows=[];
  for(const attempt of attempts.values()){
    if(!Number.isFinite(Date.parse(attempt.at))||Date.parse(attempt.at)>+now)continue;
    const file=path.join(directory,'responses',attempt.id+'.json');
    // A later finish/response must not give a historical pending attempt future usage.
    const response=attempt.has_terminal_receipt&&fs.existsSync(file)?read(file,errors):null,usage=tokenUsage(response?.usage);
    rows.push({at:attempt.at,provider:attempt.provider,model:response?.model||attempt.model,state:attempt.state,
      ...usage,reported_calls:usage.state==='provider_reported'?1:0,unreported_calls:usage.state==='provider_reported'?0:1,
      attempt_state:attempt.state});
  }
  const aggregate=items=>({attempts:items.length,...tokenTotals(items),
    outcomes:items.reduce((o,r)=>{o[r.attempt_state]=(o[r.attempt_state]||0)+1;return o;},{})});
  const windows={};for(const [key,days] of [['day',1],['week',7],['month',30]]){
    windows[key]=aggregate(rows.filter(x=>Date.parse(x.at)>=+now-days*86400000&&Date.parse(x.at)<=+now));
  }
  return {scope:'All retained AI-feed attempts, including rejected/failed/unfinished; usage only where returned. Qualification probes and news/mind usage excluded. Overlaps cycle tokens: do not add.',
    first_attempt:rows.map(x=>x.at).filter(Boolean).sort()[0]||null,last_attempt:rows.map(x=>x.at).filter(Boolean).sort().at(-1)||null,
    all:aggregate(rows),windows,providers:[...new Set(rows.map(x=>x.provider))].sort().map(provider=>({provider,...aggregate(rows.filter(x=>x.provider===provider))}))};
}
function buildSummary(root=ROOT,now=new Date()){
  now=new Date(now);if(!Number.isFinite(+now))throw Error('invalid_summary_time');
  const errors=[],startMap=new Map(),finishes=new Map(),directory=path.join(root,'runtime/resources/receipts');
  for(const name of files(directory)){
    if(!name.endsWith('-start.json')&&!name.endsWith('-finish.json'))continue;
    const row=read(path.join(directory,name),errors);
    if(row?.schema!=='beops-resource-cycle/v1'||!Number.isFinite(Date.parse(row.started_at))||
      !/^[a-f0-9]{32}$/.test(row.id||'')||name!==row.id+'-'+row.phase+'.json'){errors.push(name);continue;}
    if(row.phase==='start')startMap.set(row.id,row);else if(row.phase==='finish')finishes.set(row.id,row);
  }
  const starts=[...startMap.values()].filter(x=>Date.parse(x.started_at)<=+now);
  for(const [id,finish] of finishes){
    const start=startMap.get(id);
    if(!start||!validFinish(finish)||['activity','runtime','started_at','pid'].some(key=>start[key]!==finish[key])||
      !Number.isFinite(Date.parse(finish.finished_at))||Date.parse(finish.finished_at)<Date.parse(finish.started_at)){
      errors.push(id+'-finish.json');finishes.delete(id);
    }else if(Date.parse(finish.finished_at)>+now){finishes.delete(id);}
  }
  const windows={};for(const [key,days] of [['day',1],['week',7],['month',30]]){
    const from=new Date(+now-days*86400000).toISOString(),selected=starts.filter(x=>Date.parse(x.started_at)>=Date.parse(from)&&Date.parse(x.started_at)<=+now);
    windows[key]={from,to:now.toISOString(),...totals(selected,finishes),
      activities:[...new Set(selected.map(x=>x.activity))].sort().map(activity=>({activity,...totals(selected.filter(x=>x.activity===activity),finishes)}))};
  }
  const historical=history(root,now,errors);
  return {schema:'beops-resource-summary/v1',as_of:now.toISOString(),observation_start:starts.map(x=>x.started_at).sort()[0]||null,
    scope:'Observed portions of Beops work, not total host or consciousness cost. Rolling UTC windows by cycle start; whole finished-cycle amounts, not prorated.',
    coverage:{instrumented:['collection (including local snapshot export)','calendar refresh','ai_feed','news process (run)','mind process (run/step)','scheduled watch process','scheduled guard process','scheduled legal permission recapture'],
      excluded:['publication/build/baseline/test processes','legacy obs001 process','CPU of all child processes','local model servers and GPU','remote provider hardware','opaque CLI network traffic','news/mind token usage','qualification-probe tokens','host idle/baseline electricity'],
      cpu:'Current instrumented process CPU seconds only; may overlap concurrent work; elapsed time is not energy.',
      memory:'Maximum process lifetime RSS among finished receipts, not sum or whole-system memory.',
      http:'Attempted instrumented requests and decoded response body bytes; no claim of wire bytes or all machine traffic.',
      tokens:'Observed provider fields, with field coverage; no billing-equivalent total inferred. Failed/timeout calls may consume unreported tokens.',
      overhead:'Start receipt included in cycle measurements; final receipt writing and this summary are not measured.',
      persistence:'Meter I/O failures warn in existing process stderr logs and do not stop collection; no whole-machine completeness claim.',
      incomplete_receipts:errors.length,invalid_receipt_files:errors},windows,
    historical_provider_usage:historical,
    electricity:{state:'unavailable',wh:null,reason:'No physical energy readings supplied; CPU seconds are not watts or Wh.'},
    money:{state:'unavailable',amount:null,currency:null,reason:'No tariff, measured electricity, or provider billing records supplied. Subscription price does not establish marginal request cost.'}};
}
module.exports={buildSummary,tokenTotals};
if(require.main===module){
  if(process.argv.length>2){console.error('Usage: node tools/resource_summary.js (read-only JSON on stdout)');process.exitCode=2;}
  else process.stdout.write(JSON.stringify(buildSummary(),null,2)+'\n');
}
