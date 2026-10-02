'use strict';
const fs=require('node:fs'),path=require('node:path'),https=require('node:https');
const {buildGroups}=require('./build_impulse_groups');
const publication=require('./group_publication');
const {git,parse,digest}=publication;
function durable(target){
 const resolved=fs.realpathSync(path.resolve(target));
 if(!resolved.toLowerCase().startsWith('c:\\svemir\\'))throw Error('group_root_outside_durable_workspace');return resolved;
}
function atomic(file,value){const tmp=file+'.'+process.pid+'.tmp';fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(tmp,JSON.stringify(value,null,2)+'\n');fs.renameSync(tmp,file);}
function fetchBytes(url){
 const incognito=require('C:/Svemir/lib/incognito.js'),headers=incognito.headers(url,{vrsta:'html'});delete headers['Accept-Encoding'];
 return new Promise((resolve,reject)=>{
  const req=https.get(url,{headers,timeout:10000},res=>{
   if(res.statusCode!==200){res.resume();reject(Error('group_http_'+res.statusCode));return;}
   const chunks=[];let size=0;res.on('data',chunk=>{size+=chunk.length;if(size>16*1024*1024)req.destroy(Error('group_response_too_large'));else chunks.push(chunk);});res.on('end',()=>resolve(Buffer.concat(chunks)));res.on('error',reject);
  });req.on('timeout',()=>req.destroy(Error('group_http_timeout')));req.on('error',reject);
 });
}
async function verifyPublic(mirror,pointer,{attempts=9,head='HEAD'}={}){
 const names=[publication.POINTER,publication.MANIFEST,...Object.values(pointer.groups).map(ref=>'docs/'+ref.path)];let last;
 for(let attempt=0;attempt<attempts;attempt++){
  try{
   for(const name of names){
    const remote=await fetchBytes('https://3esign.github.io/beops/'+name.slice(5)+'?groups='+Date.now());
    const local=git(mirror,['show',head+':'+name]);if(!remote.equals(local))throw Error('group_public_bytes_differ: '+name);
   }return {verified_routes:names.length};
  }catch(e){last=e;if(attempt+1<attempts)await new Promise(resolve=>setTimeout(resolve,10000));}
 }throw last;
}
async function main(){
 const root=durable(process.env.BEOPS_ROOT||path.resolve(__dirname,'..'));
 const mirror=durable(process.env.BEOPS_PUBLIC_ROOT||path.resolve(root,'..','Beops-public'));
 if(process.env.BEOPS_GROUP_LOCKED!=='1')throw Error('use_publish_groups_ps1_lock_wrapper');
 const sourceHead=git(root,['rev-parse','HEAD']).toString().trim();
 const lastFull=parse(fs.readFileSync(path.join(root,'data/live/publish-last-success.json')));
 const gateAge=Date.now()-Date.parse(lastFull.last_full_gate_at);
 if(lastFull.source_head!==sourceHead||lastFull.site_verified!==true||lastFull.tests_ok!==true||!Number.isFinite(gateAge)||gateAge<0||gateAge>=86400000)throw Error('group_source_requires_verified_full_release');
 const manifest=parse(git(mirror,['show','HEAD:docs/export-manifest.json']));
 if(manifest.source_head!==sourceHead)throw Error('group_source_requires_full_release');
 if(!git(mirror,['show','HEAD:docs/impulsi.html']).toString().includes('impulse-data/groups/current.json'))throw Error('group_browser_requires_full_release');
 const tracked=git(root,['diff','HEAD','--name-only','--','tools','public','research/COLLECTORS.json','research/EVENTS.json','research/05-design/studies/observation-clocks.js']).toString().trim();
 if(tracked)throw Error('group_source_modified_requires_commit');
 const remote=git(mirror,['remote','get-url','origin']).toString().trim();
 if(remote!=='https://github.com/3esign/beops.git')throw Error('unexpected_group_remote');
 const stage=path.join(root,'runtime','group-release');fs.mkdirSync(stage,{recursive:true});
 // The cut must follow receipts already in the cache. Rounding backward can hide
 // a freshly received programme until the next interval.
 const asOf=new Date().toISOString();
 const started=Date.now(),receiptFile=path.join(root,'data/live/group-publish-receipt.json');
 const receipt={schema:'beops-group-publish-receipt/v1',started_at:new Date().toISOString(),source_head:sourceHead,published:false,history_read_bytes:0,history_copied_bytes:0};
 try{
  const built=await buildGroups(root,{asOf,outputDir:path.join(stage,'docs')});receipt.build=built;
  const delta=publication.prepareDelta(mirror,stage,sourceHead),applied=publication.applyDelta(mirror,delta);
  Object.assign(receipt,applied,{calendar_as_of:delta.asOf,pointer:delta.pointer,committed:true});atomic(receiptFile,receipt);
  git(mirror,['push','origin','HEAD:refs/heads/main']);
  const remoteHead=git(mirror,['ls-remote','origin','refs/heads/main']).toString().trim().split(/\s+/)[0];
  if(remoteHead!==applied.head)throw Error('group_remote_head_mismatch');receipt.pushed=true;
  Object.assign(receipt,await verifyPublic(mirror,delta.pointer,{head:applied.head}),{published:true,site_verified:true});
 }catch(e){receipt.error=e.message;throw e;}
 finally{receipt.finished_at=new Date().toISOString();receipt.seconds=(Date.now()-started)/1000;atomic(receiptFile,receipt);console.log(JSON.stringify(receipt));}
}
module.exports={verifyPublic};
if(require.main===module)main().catch(e=>{console.error(e.message);process.exitCode=1;});
