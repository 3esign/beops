'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const p=require('../tools/group_publication');
const base=path.resolve(__dirname,'../runtime/group-publication-tests');fs.mkdirSync(base,{recursive:true});
function write(root,name,data){const file=path.join(root,name);fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,data);}
function fixture(){
 const root=fs.mkdtempSync(path.join(base,'case-')),mirror=path.join(root,'mirror'),stage=path.join(root,'stage');fs.mkdirSync(mirror);
 p.git(mirror,['init','-q']);p.git(mirror,['config','user.name','Semir Poturak']);p.git(mirror,['config','user.email','scumutator@gmail.com']);
 write(mirror,'docs/history.json','UNCHANGED HISTORY');write(mirror,'docs/impulsi.html','impulse-data/groups/current.json');
 const source='a'.repeat(40),files=['docs/history.json','docs/impulsi.html'].map(name=>{const data=fs.readFileSync(path.join(mirror,name));return {path:name,bytes:data.length,sha256:p.digest(data)};});
 write(mirror,p.MANIFEST,JSON.stringify({schema:'beops-export-manifest/v1',source_head:source,generated_as_of:'2026-09-27T10:00:00Z',inputs_manifest_sha256:'b'.repeat(64),files,file_count:files.length}));
 p.git(mirror,['add','.']);p.git(mirror,['commit','-qm','Fixture']);
 const context=Buffer.from(JSON.stringify({schema:'beops-context-group/v1',basemap:{type:'FeatureCollection',features:[]}}));
 const calendar=Buffer.from(JSON.stringify({schema:'beops-calendar-group/v1',as_of:'2026-09-27T12:00:00Z',items:[],sources:[],dependencies:{context:p.digest(context)}}));
 const groups={};for(const[id,data]of [['context',context],['calendar',calendar]]){const hash=p.digest(data),name='impulse-data/groups/objects/'+hash+'.json';groups[id]={revision:hash,path:name,bytes:data.length};write(stage,'docs/'+name,data);}
 write(stage,p.POINTER,JSON.stringify({schema:'beops-impulse-groups/v1',groups}));return {root,mirror,stage,source};
}
function cleanup(f){assert.ok(f.root.startsWith(base+path.sep));fs.rmSync(f.root,{recursive:true,force:true});}
test('delta changes only group files and manifest; retains observation clock and bytes',()=>{
 const f=fixture();try{
  const delta=p.prepareDelta(f.mirror,f.stage,f.source),done=p.applyDelta(f.mirror,delta);
  assert.equal(done.changed,true);assert.ok(done.paths.every(name=>name===p.MANIFEST||name.startsWith(p.PREFIX)));
  assert.equal(fs.readFileSync(path.join(f.mirror,'docs/history.json'),'utf8'),'UNCHANGED HISTORY');
  const manifest=p.parse(fs.readFileSync(path.join(f.mirror,p.MANIFEST)));assert.equal(manifest.generated_as_of,'2026-09-27T10:00:00Z');assert.equal(manifest.inputs_manifest_sha256,'b'.repeat(64));
  assert.equal(p.prepareDelta(f.mirror,f.stage,f.source).changes.size,0);
 }finally{cleanup(f);}
});
test('failure before commit restores exact previous files and leaves clean index',()=>{
 const f=fixture();try{const delta=p.prepareDelta(f.mirror,f.stage,f.source);assert.throws(()=>p.applyDelta(f.mirror,delta,{beforeCommit(){throw Error('interrupted');}}),/interrupted/);assert.equal(p.git(f.mirror,['rev-parse','HEAD']).toString().trim(),delta.priorHead);assert.equal(p.git(f.mirror,['status','--porcelain']).toString().trim(),'');assert.equal(fs.existsSync(path.join(f.mirror,p.POINTER)),false);}finally{cleanup(f);}
});
test('commit publishes verified index even if worktree changes after its check',()=>{
 const f=fixture();try{
  const delta=p.prepareDelta(f.mirror,f.stage,f.source),expected=delta.changes.get(p.POINTER);
  const result=p.applyDelta(f.mirror,delta,{beforeCommit(){write(f.mirror,p.POINTER,'concurrent edit');}});
  assert.deepEqual(p.git(f.mirror,['show',result.head+':'+p.POINTER]),expected);
  assert.equal(fs.readFileSync(path.join(f.mirror,p.POINTER),'utf8'),'concurrent edit');
 }finally{cleanup(f);}
});
test('refuses source mismatch, dirty mirror, corruption and path traversal',()=>{
 const f=fixture();try{
  assert.throws(()=>p.prepareDelta(f.mirror,f.stage,'c'.repeat(40)),/requires_full_release/);
  write(f.mirror,'unknown.txt','USER FILE');assert.throws(()=>p.prepareDelta(f.mirror,f.stage,f.source),/mirror_dirty/);fs.unlinkSync(path.join(f.mirror,'unknown.txt'));
  const ptr=p.parse(fs.readFileSync(path.join(f.stage,p.POINTER)));write(f.stage,'docs/'+ptr.groups.calendar.path,'corrupt');assert.throws(()=>p.prepareDelta(f.mirror,f.stage,f.source),/hash_mismatch/);
  assert.throws(()=>p.updateManifest({schema:'beops-export-manifest/v1',files:[]},new Map([['../bad',Buffer.from('x')]]),'now'),/path_refused/);
 }finally{cleanup(f);}
});
test('later full stage retains and verifies immutable objects from committed Git',()=>{
 const f=fixture();try{p.applyDelta(f.mirror,p.prepareDelta(f.mirror,f.stage,f.source));const dest=path.join(f.root,'next');assert.equal(p.retainObjects(f.mirror,dest).retained_objects,2);assert.equal(p.retainObjects(f.mirror,dest).retained_objects,0);}finally{cleanup(f);}
});
