'use strict';
// Independent public calendar/context revisions. Only their bounded inputs are
// read: no observations, headline archive, history, AI packets, or resource log.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const model=require('./impulse_model');
const ROOT=path.resolve(__dirname,'..'),GROUPS='impulse-data/groups',DIGEST=/^[a-f0-9]{64}$/;
const MAX_FILE_BYTES=16*1024*1024,MAX_INPUT_BYTES=64*1024*1024;
const TRANSFORMS=['build_impulse_groups.js','build_impulse_page.js','impulse_model.js',
 'ai_feed_context.js','headline_geo.js','event_venues.json','calendar_group_policy.py',
 'permission_policy.py','legal_capture.py','contracts.py','transport.py','net_fetch.js','network_identity.js',
 'ai_feed_relations.js','headline_places.json','../research/05-design/studies/observation-clocks.js'];
const sha256=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function canonical(value){
 if(value===null||typeof value!=='object')return value;
 if(Array.isArray(value))return value.map(canonical);
 return Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])]));
}
function encode(value){
 const text=JSON.stringify(canonical(value))+'\n';
 if(/(?:^|["\s])(?:[A-Za-z]:[\\/]|file:\/\/|\/(?:Users|home)\/)/.test(text))throw Error('local_path_in_public_group');
 return Buffer.from(text,'utf8');
}
// Durable roots: the Svemir body on C: and the project disk it was moved to on
// 2026-09-28 (C:\Svemir\!Projekti is a junction to D:\Svemir\!Projekti). A
// C:-only root refused every release prepared under D:\Svemir\_runtime.
const durableRoots=()=>(process.env.BEOPS_DURABLE_ROOTS||'C:/Svemir;D:/Svemir').split(';')
 .map(s=>s.trim()).filter(Boolean).map(p=>path.resolve(p));
const underRoot=(absolute,root)=>absolute.toLowerCase().startsWith(root.toLowerCase()+path.sep);
function durable(target){
 const absolute=path.resolve(target);
 if(!durableRoots().some(root=>underRoot(absolute,root)))throw Error('group_output_outside_durable_root');
 // Refuse a junction/symlink that turns an apparently durable path into a non-durable place.
 let ancestor=absolute;while(!fs.existsSync(ancestor))ancestor=path.dirname(ancestor);
 const real=fs.realpathSync(ancestor).toLowerCase();
 const ok=durableRoots().filter(root=>fs.existsSync(root)).map(root=>fs.realpathSync(root).toLowerCase())
  .some(root=>real===root||real.startsWith(root+path.sep));
 if(!ok)throw Error('group_output_junction_outside_durable_root');
 return absolute;
}
function json(bytes){return JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/,''));}
function boundedRead(file,limit=MAX_FILE_BYTES){
 if(fs.statSync(file).size>limit)throw Error('group_input_byte_limit');
 const fd=fs.openSync(file,'r');
 try{
  const chunks=[];let total=0;
  for(;;){const chunk=Buffer.alloc(Math.min(64*1024,limit-total+1)),size=fs.readSync(fd,chunk,0,chunk.length,null);
   if(!size)break;total+=size;if(total>limit)throw Error('group_input_byte_limit');chunks.push(chunk.subarray(0,size));}
  return Buffer.concat(chunks,total);
 }finally{fs.closeSync(fd);}
}
function readInput(file,metrics){
 const bytes=boundedRead(file,Math.min(MAX_FILE_BYTES,MAX_INPUT_BYTES-metrics.inputReadBytes));metrics.inputReadBytes+=bytes.length;
 metrics.inputFiles.add(file);return bytes;
}
function transformationRevision(metrics){
 return sha256(encode(Object.fromEntries(TRANSFORMS.map(name=>[name,sha256(readInput(path.join(__dirname,name),metrics))]))));
}
function policyFor(root,asOf,sources,metrics){
 // Missing calendar caches need no permissions and do not require Python.
 if(!sources.length)return {revision:sha256(encode({sources:[]})),decisions:[]};
 let executable=process.env.BEOPS_PYTHON,pythonpath;
 if(executable&&/\.(?:cmd|bat)$/i.test(executable))executable=null;
 const config=[path.join(root,'runtime/test-python.json'),path.join(ROOT,'runtime/test-python.json')].find(file=>fs.existsSync(file));
 if(config){
  const value=json(readInput(config,metrics));executable=executable||value.python;pythonpath=value.pythonpath;
 }
 if(executable&&/\.(?:cmd|bat)$/i.test(executable))throw Error('calendar_policy_requires_python_executable');
 const env={...process.env,PYTHONDONTWRITEBYTECODE:'1',PYTHONIOENCODING:'utf-8'};
 if(pythonpath)env.PYTHONPATH=pythonpath+(env.PYTHONPATH?path.delimiter+env.PYTHONPATH:'');
 const result=execFileSync(executable||'python',['-B',path.join(__dirname,'calendar_group_policy.py'),
  '--root',root,'--as-of',asOf,'--byte-budget',String(MAX_INPUT_BYTES-metrics.inputReadBytes)],{input:JSON.stringify(sources.map(s=>({source_id:s.source_id,url:s.url}))),
  encoding:'utf8',timeout:600000,maxBuffer:1024*1024,windowsHide:true,env});
 const policy=JSON.parse(result);
 if(policy.schema!=='beops-calendar-policy/v1'||!DIGEST.test(policy.revision)||!Array.isArray(policy.decisions)||
    !Number.isSafeInteger(policy.inputReadBytes)||policy.inputReadBytes<0)throw Error('invalid_calendar_policy_result');
 metrics.inputReadBytes+=policy.inputReadBytes;
 if(metrics.inputReadBytes>MAX_INPUT_BYTES)throw Error('group_input_byte_limit');
 for(const file of policy.inputFiles||[])metrics.inputFiles.add(path.join(root,file));
 return policy;
}
function descriptor(bytes){if(bytes.length>MAX_FILE_BYTES)throw Error('group_output_byte_limit');const revision=sha256(bytes);return {revision,path:GROUPS+'/objects/'+revision+'.json',bytes:bytes.length};}
function verifyObject(output,entry,metrics){
 if(!entry||!DIGEST.test(entry.revision)||entry.path!==GROUPS+'/objects/'+entry.revision+'.json'||
    !Number.isSafeInteger(entry.bytes)||entry.bytes<1||entry.bytes>MAX_FILE_BYTES)throw Error('invalid_group_descriptor');
 const bytes=boundedRead(path.join(output,entry.path));metrics.verifiedBytes+=bytes.length;
 if(bytes.length!==entry.bytes||sha256(bytes)!==entry.revision)throw Error('group_object_integrity_mismatch');
 return json(bytes);
}
function verifyPointer(output,pointer,metrics){
 if(pointer.schema!=='beops-impulse-groups/v1'||!pointer.groups)throw Error('invalid_group_pointer');
 const context=verifyObject(output,pointer.groups.context,metrics),calendar=verifyObject(output,pointer.groups.calendar,metrics);
 if(context.schema!=='beops-context-group/v1'||calendar.schema!=='beops-calendar-group/v1'||
    calendar.dependencies?.context!==pointer.groups.context.revision)throw Error('group_dependency_mismatch');
}
function writeDurable(file,bytes){
 const fd=fs.openSync(file,'wx');try{fs.writeFileSync(fd,bytes);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
}
async function buildGroups(root=ROOT,options={}){
 root=path.resolve(root);const time=model.stamp(options.asOf);
 if(time===null)throw Error('calendar_group_as_of_requires_timezone');
 const asOf=options.asOf,output=durable(options.outputDir||path.join(root,'docs'));
 const groupRoot=durable(path.join(output,GROUPS)),lock=path.join(groupRoot,'.writer.lock');
 fs.mkdirSync(durable(path.join(groupRoot,'objects')),{recursive:true});
 const token=crypto.randomBytes(16).toString('hex');
 // Fail fast, never steal by PID or timeout (PID reuse cannot prove ownership).
 // A killed writer leaves this marker. Recovery is manual: verify its process
 // is dead, preserve/check current.json, then remove this exact lock only.
 try{writeDurable(lock,Buffer.from(JSON.stringify({pid:process.pid,token,started_at:new Date().toISOString()})));}
 catch(error){if(error.code==='EEXIST')throw Error('group_writer_locked_manual_recovery_if_owner_dead');throw error;}
 const metrics={inputReadBytes:0,writtenBytes:0,verifiedBytes:0,inputFiles:new Set(),objectWrites:0,pointerWrites:0};
 const temporary=[];
 try{
  const current=path.join(groupRoot,'current.json');
  let previous=null;if(fs.existsSync(current)){previous=boundedRead(current,64*1024);verifyPointer(output,json(previous),metrics);}
  const cachePath=path.join(root,'data/live/derived/events/repertoire.json');
  const cache=fs.existsSync(cachePath)?json(readInput(cachePath,metrics)):{};
  const basemap=json(readInput(path.join(root,'public/basemap-belgrade.json'),metrics));
  const sources=Array.isArray(cache.sources)?cache.sources:cache.source_id?[cache]:[];
  if(sources.length>100||sources.some(s=>!s||typeof s.source_id!=='string')||new Set(sources.map(s=>s.source_id)).size!==sources.length)throw Error('invalid_calendar_sources');
  const transformRevision=transformationRevision(metrics);
  const policy=policyFor(root,asOf,sources,metrics),permissions=new Map(policy.decisions.map(s=>[s.source_id,s]));
  const checked=sources.map(s=>({...s,state:permissions.get(s.source_id)?.allowed===true&&
   /^[0-9]{8}T[0-9]{6}Z$/.test(s.permission_capture||'')?s.state:'permission_unavailable'}));
  // Lazy import avoids a cycle when the full-page builder calls this builder.
  const {publicItem}=require('./build_impulse_page');
  const items=model.calendarItems(cache.events,time,checked)
   .filter(i=>model.inWindow(i,time-30*model.DAY,time)||model.stamp(i.clock.at)>=time)
   .map(publicItem).sort((a,b)=>a.id.localeCompare(b.id));
  const publicSources=checked.map(s=>{
   const received=model.stamp(s.received_at),state=s.state!=='available'?s.state||'missing':
    received===null?'missing_receipt':received>time?'future_receipt':time-received>model.DAY?'stale':'available';
   return {source_id:s.source_id,name:s.name||s.events?.[0]?.source||s.source_id,url:model.safeURL(s.url),state,
    received_at:s.received_at||null,event_count:items.filter(i=>i.source_id===s.source_id).length};
  }).sort((a,b)=>a.source_id.localeCompare(b.source_id));
  const contextBytes=encode({schema:'beops-context-group/v1',basemap}),context=descriptor(contextBytes);
  const calendarBytes=encode({schema:'beops-calendar-group/v1',as_of:asOf,items,sources:publicSources,
   dependencies:{context:context.revision},policy_revision:policy.revision,transform_revision:transformRevision});
  const calendar=descriptor(calendarBytes),pointer={schema:'beops-impulse-groups/v1',groups:{calendar,context}};
  const pointerBytes=encode(pointer);
  for(const [entry,bytes]of [[context,contextBytes],[calendar,calendarBytes]]){
   const target=path.join(output,entry.path);
   if(fs.existsSync(target)){verifyObject(output,entry,metrics);continue;}
   const temp=path.join(groupRoot,'objects','.'+entry.revision+'.'+token+'.tmp');temporary.push(temp);
   writeDurable(temp,bytes);fs.renameSync(temp,target);metrics.writtenBytes+=bytes.length;metrics.objectWrites++;
   verifyObject(output,entry,metrics);
  }
  const changed=!previous||!previous.equals(pointerBytes);
  if(changed){
   // Test hook can interrupt immediately before the sole public pointer commit.
   // Production CLI offers no hooks or permission bypasses.
   if(options.beforeCommit)await options.beforeCommit(pointer);
   const temp=path.join(groupRoot,'.current.'+token+'.tmp');temporary.push(temp);
   writeDurable(temp,pointerBytes);fs.renameSync(temp,current);
   metrics.writtenBytes+=pointerBytes.length;metrics.pointerWrites++;
  }
  return {as_of:asOf,changed,groups:pointer.groups,...metrics,inputFiles:[...metrics.inputFiles].map(file=>path.relative(root,file).replaceAll('\\','/')).sort()};
 }finally{
  for(const file of temporary)if(fs.existsSync(file))fs.unlinkSync(file);
  // Delete only a lock still bearing this invocation's unguessable token.
  let owner;try{if(fs.existsSync(lock))owner=json(boundedRead(lock,4096));}catch{/* Preserve damaged ownership evidence. */}
  if(owner?.token===token)fs.unlinkSync(lock);
 }
}
async function main(){
 const args=process.argv.slice(2),options={};let root=ROOT;
 for(let i=0;i<args.length;i++){
  const value=args[i+1];if(!value||value.startsWith('--'))throw Error('missing_group_cli_value');
  if(args[i]==='--root')root=value;else if(args[i]==='--as-of')options.asOf=value;
  else if(args[i]==='--output-dir')options.outputDir=value;else throw Error('Unknown argument '+args[i]);i++;
 }
 console.log(JSON.stringify(await buildGroups(root,options)));
}
module.exports={buildGroups,canonical,encode,descriptor,verifyPointer};
if(require.main===module)main().catch(error=>{console.error(error.message);process.exitCode=1;});
