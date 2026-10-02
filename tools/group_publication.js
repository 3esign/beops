'use strict';
// A narrow transaction over an already verified public edition. Observations,
// source code and their generation are never relabelled by a calendar refresh.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const PREFIX='docs/impulse-data/groups/';
const POINTER=PREFIX+'current.json',MANIFEST='docs/export-manifest.json';
const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const MAX_FILE=16*1024*1024;
function boundedRead(file){if(fs.statSync(file).size>MAX_FILE)throw Error('group_file_limit');const bytes=fs.readFileSync(file);if(bytes.length>MAX_FILE)throw Error('group_file_limit');return bytes;}
function git(root,args,options={}){
 const result=spawnSync('git',['-c','core.longpaths=true','-C',root,...args],{windowsHide:true,timeout:900000,maxBuffer:16*1024*1024,...options});
 if(result.error||result.status!==0)throw Error('git '+args[0]+' failed: '+(result.error?.message||result.stderr?.toString()||result.status));
 return result.stdout;
}
function parse(bytes){return JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/,''));}
function objectName(name){return /^docs\/impulse-data\/groups\/objects\/[a-f0-9]{64}\.json$/.test(name);}
function verifyObject(name,bytes){if(!objectName(name)||digest(bytes)!==path.basename(name,'.json'))throw Error('group_object_hash_mismatch');}
function updateManifest(previous,changes,asOf){
 if(previous.schema!=='beops-export-manifest/v1'||!Array.isArray(previous.files))throw Error('invalid_export_manifest');
 const map=new Map(previous.files.map(row=>[row.path,row]));
 if(map.size!==previous.files.length)throw Error('duplicate_manifest_path');
 for(const [name,bytes]of changes){
  if(name!==POINTER&&!objectName(name))throw Error('group_delta_path_refused');
  if(objectName(name))verifyObject(name,bytes);
  map.set(name,{path:name,bytes:bytes.length,sha256:digest(bytes)});
 }
 const files=[...map.values()].sort((a,b)=>a.path.localeCompare(b.path,'en'));
 return {...previous,file_count:files.length,files,group_publication:{schema:'beops-group-publication/v1',calendar_as_of:asOf,pointer:POINTER}};
}
function readChanges(stage){
 const pointerFile=path.join(stage,POINTER),raw=boundedRead(pointerFile),pointer=parse(raw);
 if(pointer.schema!=='beops-impulse-groups/v1')throw Error('invalid_group_pointer');
 const changes=new Map();
 for(const id of ['context','calendar']){
  const ref=pointer.groups?.[id],name='docs/'+ref?.path;
  if(!ref||ref.path!=='impulse-data/groups/objects/'+ref.revision+'.json'||!Number.isSafeInteger(ref.bytes))throw Error('invalid_group_reference');
  const bytes=boundedRead(path.join(stage,name));verifyObject(name,bytes);
  if(bytes.length!==ref.bytes)throw Error('group_object_size_mismatch');changes.set(name,bytes);
 }
 const calendar=parse(changes.get('docs/'+pointer.groups.calendar.path));
 if(calendar.dependencies?.context!==pointer.groups.context.revision)throw Error('group_dependency_mismatch');
 changes.set(POINTER,raw);
 return {changes,asOf:calendar.as_of,pointer};
}
function prepareDelta(mirror,stage,sourceHead){
 const status=git(mirror,['status','--porcelain','--untracked-files=all']).toString().trim();
 if(status)throw Error('public_mirror_dirty');
 const priorHead=git(mirror,['rev-parse','HEAD']).toString().trim();
 const priorRaw=git(mirror,['show',priorHead+':'+MANIFEST]),previous=parse(priorRaw);
 if(previous.source_head!==sourceHead)throw Error('group_source_requires_full_release');
 const html=git(mirror,['show',priorHead+':docs/impulsi.html']).toString();
 if(!html.includes('impulse-data/groups/current.json'))throw Error('group_browser_requires_full_release');
 const {changes,asOf,pointer}=readChanges(stage);
 for(const [name,bytes]of [...changes]){
  const row=previous.files.find(row=>row.path===name);
  if(row&&row.bytes===bytes.length&&row.sha256===digest(bytes)){
   const committed=git(mirror,['show',priorHead+':'+name]);
   if(digest(committed)!==row.sha256)throw Error('prior_group_manifest_mismatch');
   changes.delete(name);
  }
 }
 if(!changes.size)return {priorHead,changes,asOf,pointer};
 const manifest=updateManifest(previous,changes,asOf);
 changes.set(MANIFEST,Buffer.from(JSON.stringify(manifest,null,2)+'\n'));
 return {priorHead,changes,asOf,pointer};
}
function applyDelta(mirror,delta,{beforeCommit}={}){
 if(git(mirror,['rev-parse','HEAD']).toString().trim()!==delta.priorHead)throw Error('public_head_changed');
 if(!delta.changes.size)return {changed:false,head:delta.priorHead,written_bytes:0};
 const backup=new Map();let committed=false;
 try{
  for(const [name,bytes]of delta.changes){
   if(name!==MANIFEST&&name!==POINTER&&!objectName(name))throw Error('group_delta_path_refused');
   const file=path.join(mirror,name);if(bytes.length>MAX_FILE)throw Error('group_file_limit');backup.set(name,fs.existsSync(file)?boundedRead(file):null);
   fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,bytes);
  }
  const names=[...delta.changes.keys()];git(mirror,['add','-f','--',...names]);
  const staged=git(mirror,['diff','--cached','--name-only','-z']).toString().split('\0').filter(Boolean);
  if(staged.some(name=>!delta.changes.has(name)))throw Error('unrelated_staged_group_delta');
  for(const name of staged)if(!git(mirror,['show',':'+name]).equals(delta.changes.get(name)))throw Error('staged_group_bytes_differ');
  if(beforeCommit)beforeCommit();
  // Commit the verified index. Path-limited commit would re-read worktree bytes.
  git(mirror,['-c','user.name=Semir Poturak','-c','user.email=scumutator@gmail.com','commit','-m','Refresh independent calendar '+delta.asOf]);committed=true;
  return {changed:true,head:git(mirror,['rev-parse','HEAD']).toString().trim(),written_bytes:[...delta.changes.values()].reduce((n,b)=>n+b.length,0),paths:staged};
 }finally{
  if(!committed){
   const names=[...backup.keys()];if(names.length)git(mirror,['reset','-q',delta.priorHead,'--',...names]);
   for(const [name,bytes]of backup){const file=path.join(mirror,name);if(bytes===null){if(fs.existsSync(file))fs.unlinkSync(file);}else fs.writeFileSync(file,bytes);}
  }
 }
}
function retainObjects(mirror,destination,oid='HEAD'){
 const names=git(mirror,['ls-tree','-r','--name-only',oid,'--',PREFIX+'objects/']).toString().trim().split('\n').filter(Boolean);let copied=0,bytes=0;
 for(const name of names){
  if(!objectName(name))throw Error('unexpected_retained_group_path');
  const data=git(mirror,['show',oid+':'+name]);verifyObject(name,data);const target=path.join(destination,name);
  if(fs.existsSync(target)){if(!fs.readFileSync(target).equals(data))throw Error('retained_group_collision');continue;}
  fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,data,{flag:'wx'});copied++;bytes+=data.length;
 }
 return {retained_objects:copied,retained_bytes:bytes};
}
module.exports={PREFIX,POINTER,MANIFEST,digest,git,parse,verifyObject,updateManifest,readChanges,prepareDelta,applyDelta,retainObjects};
if(require.main===module){
 try{if(process.argv[2]!=='retain')throw Error('expected retain mirror destination oid');console.log(JSON.stringify(retainObjects(process.argv[3],process.argv[4],process.argv[5]||'HEAD')));}catch(e){console.error(e.message);process.exitCode=1;}
}
