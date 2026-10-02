'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),crypto=require('node:crypto'),fs=require('node:fs'),vm=require('node:vm');
const {loadGroups,applyGroups,hydrate}=require('../public/impulsi');
const calendarAt='2026-09-27T18:00:00Z',observationAt='2026-09-27T12:00:00Z',received='2026-09-27T17:00:00Z';
const pointerPath='impulse-data/groups/current.json',digest=value=>crypto.createHash('sha256').update(value).digest('hex');
function event(id,at='2026-09-27T19:00:00Z',extra={}){return {id,kind:'scheduled_event',title:id,source_id:'S1',clock:{at,start:at,end:null,basis:'scheduled_event_time'},first_received:received,schedule_fresh:true,...extra};}
function fixture(change=()=>{}){
 const context={schema:'beops-context-group/v1',basemap:{type:'FeatureCollection',features:[],name:'new-context'}};
 const contextBytes=Buffer.from(JSON.stringify(context)),contextRevision=digest(contextBytes);
 const calendar={schema:'beops-calendar-group/v1',as_of:calendarAt,items:[event('new')],sources:[{source_id:'S1',state:'available',received_at:received}],dependencies:{context:contextRevision},policy_revision:'a'.repeat(64),transform_revision:'b'.repeat(64)};
 change(calendar,context);
 const calendarBytes=Buffer.from(JSON.stringify(calendar)),calendarRevision=digest(calendarBytes);
 const reference=(revision,bytes)=>({revision,path:'impulse-data/groups/objects/'+revision+'.json',bytes});
 const pointer={schema:'beops-impulse-groups/v1',groups:{calendar:reference(calendarRevision,calendarBytes.length),context:reference(contextRevision,contextBytes.length)}};
 const bodies=new Map([[pointerPath,Buffer.from(JSON.stringify(pointer))],[pointer.groups.calendar.path,calendarBytes],[pointer.groups.context.path,contextBytes]]),calls=[];
 const request=async(name,options)=>{calls.push({name,options});const bytes=bodies.get(name);return {ok:!!bytes,json:async()=>JSON.parse(bytes),arrayBuffer:async()=>Uint8Array.from(bytes).buffer};};
 const setPointer=()=>bodies.set(pointerPath,Buffer.from(JSON.stringify(pointer)));
 return {calendar,context,pointer,bodies,calls,request,setPointer};
}
function base(){
 const row={id:'headline',kind:'headline_mention',title:'Retained headline',clock:{at:'2026-09-27T11:00:00Z',start:'2026-09-27T11:00:00Z',end:null},geo:{scope:'belgrade'}};
 const view={as_of:observationAt,generated_at:observationAt,view:Object.fromEntries(['day','week','month'].map(key=>[key,{start:'2026-09-26T12:00:00Z',end:observationAt,counts:{headlines:1}}])),basemap:{name:'old'}};
 return {view,impulses:{items:[row,event('old')]},resources:{windows:{day:{cpu_seconds:7},week:{cpu_seconds:9},month:{cpu_seconds:10}}}};
}
test('independent calendar/context verified from immutable byte paths',async()=>{
 const f=fixture(),groups=await loadGroups(pointerPath,f.request,crypto.webcrypto.subtle);
 assert.equal(groups.calendar.items[0].id,'new');assert.equal(groups.revisions.context,f.pointer.groups.context.revision);
 assert.equal(f.calls.length,3);assert.ok(f.calls.every(call=>call.options.cache==='no-cache'));
});
test('calendar advance preserves headline/resource clock and replaces prior schedules',async()=>{
 const f=fixture(calendar=>calendar.items.push(event('already-past','2026-09-27T17:30:00Z'))),groups=await loadGroups(pointerPath,f.request,crypto.webcrypto.subtle),{view,impulses,resources}=base();
 applyGroups(view,impulses,groups);const data=hydrate(view,impulses,resources);
 assert.equal(data.as_of,observationAt);assert.equal(data.generated_at,observationAt);assert.equal(data.calendar_as_of,calendarAt);
 assert.deepEqual(data.upcoming.map(item=>item.id),['new']);assert.ok(!impulses.items.some(item=>item.id==='old'));
 assert.equal(data.view.day.records[0].id,'headline');assert.equal(data.view.day.resource.cpu_seconds,7);assert.equal(data.basemap.name,'new-context');
});
test('legacy payload retains its original upcoming clock and basemap',()=>{
 const {view,impulses,resources}=base();applyGroups(view,impulses,null);hydrate(view,impulses,resources);
 assert.equal(view.calendar_as_of,undefined);assert.equal(view.basemap.name,'old');assert.deepEqual(view.upcoming.map(item=>item.id),['old']);
});
test('missing object, wrong size and corrupted same-length bytes are rejected',async()=>{
 for(const failure of ['missing','size','hash']){
  const f=fixture(),name=f.pointer.groups.calendar.path;
  if(failure==='missing')f.bodies.delete(name);
  if(failure==='size')f.bodies.set(name,Buffer.concat([f.bodies.get(name),Buffer.from(' ')]));
  if(failure==='hash'){const bytes=Buffer.from(f.bodies.get(name));bytes[bytes.length-2]^=1;f.bodies.set(name,bytes);}
  await assert.rejects(loadGroups(pointerPath,f.request,crypto.webcrypto.subtle),new RegExp(failure==='missing'?'group_object_unavailable':'group_object_'+failure));
 }
});
test('old calendar with newly published context is rejected, retained old pair stays readable',async()=>{
 const f=fixture(),before=await loadGroups(pointerPath,f.request,crypto.webcrypto.subtle);
 const bytes=Buffer.from(JSON.stringify({schema:'beops-context-group/v1',basemap:{type:'FeatureCollection',features:[],name:'changed'}})),revision=digest(bytes);
 f.pointer.groups.context={revision,path:'impulse-data/groups/objects/'+revision+'.json',bytes:bytes.length};f.bodies.set(f.pointer.groups.context.path,bytes);f.setPointer();
 await assert.rejects(loadGroups(pointerPath,f.request,crypto.webcrypto.subtle),/group_dependency_mismatch/);
 assert.equal(before.context.basemap.name,'new-context');
});
test('pointer rejects external/traversal paths, invalid hashes and byte sizes before object requests',async()=>{
 for(const mutation of [ref=>ref.path='https://example.test/leak',ref=>ref.path='../history.json',ref=>ref.revision='g'.repeat(64),ref=>ref.bytes=0,ref=>ref.bytes=17*1024*1024]){
  const f=fixture();mutation(f.pointer.groups.calendar);f.setPointer();
  await assert.rejects(loadGroups(pointerPath,f.request,crypto.webcrypto.subtle),/group_reference_invalid/);assert.equal(f.calls.length,1);
 }
 await assert.rejects(loadGroups('https://example.test/current.json',()=>assert.fail('network must not run'),crypto.webcrypto.subtle),/group_pointer_invalid/);
});
test('malformed pointer/object schema and unqualified calendar clocks fail closed',async()=>{
 const f=fixture();f.pointer.schema='other';f.setPointer();await assert.rejects(loadGroups(pointerPath,f.request,crypto.webcrypto.subtle),/group_pointer_schema/);
 for(const [change,error]of [[calendar=>calendar.schema='other',/group_object_schema/],[calendar=>calendar.as_of='2026-09-27T18:00:00',/group_object_shape/],[calendar=>calendar.items[0].kind='headline_mention',/group_calendar_item/],[calendar=>calendar.items[0].clock.at='tomorrow',/group_calendar_item/]]){
  const f=fixture(change);await assert.rejects(loadGroups(pointerPath,f.request,crypto.webcrypto.subtle),error);
 }
});
test('stale, future, failed and unmatched source receipts never borrow another source freshness',async()=>{
 const f=fixture(calendar=>{
  calendar.sources.push({source_id:'failed',state:'unavailable',received_at:received},{source_id:'stale',state:'available',received_at:'2026-09-26T17:59:59Z'},{source_id:'future',state:'available',received_at:'2026-09-27T18:00:01Z'});
  calendar.items.push(event('failed',undefined,{source_id:'failed'}),event('stale',undefined,{source_id:'stale',first_received:'2026-09-26T17:59:59Z'}),event('future',undefined,{source_id:'future',first_received:'2026-09-27T18:00:01Z'}),event('mismatch',undefined,{first_received:'2026-09-27T16:00:00Z'}),event('unknown',undefined,{source_id:'unknown'}));
 }),groups=await loadGroups(pointerPath,f.request,crypto.webcrypto.subtle),{view,impulses}=base();
 applyGroups(view,impulses,groups);assert.deepEqual(impulses.items.filter(item=>item.kind==='scheduled_event').map(item=>item.id),['new']);
});
test('exact 24-hour receipt boundary remains usable at group cut',async()=>{
 const f=fixture(calendar=>{calendar.sources[0].received_at='2026-09-26T18:00:00Z';calendar.items[0].first_received='2026-09-26T18:00:00Z';}),groups=await loadGroups(pointerPath,f.request,crypto.webcrypto.subtle),{view,impulses}=base();
 applyGroups(view,impulses,groups);assert.equal(impulses.items.filter(item=>item.kind==='scheduled_event').length,1);
});
test('empty group removes prior scheduled events without erasing retained headlines',async()=>{
 const f=fixture(calendar=>calendar.items=[]),groups=await loadGroups(pointerPath,f.request,crypto.webcrypto.subtle),{view,impulses,resources}=base();
 applyGroups(view,impulses,groups);hydrate(view,impulses,resources);assert.equal(view.upcoming.length,0);assert.equal(view.view.day.records.length,1);
});
test('group failure reaches visible browser alert and disables controls',async()=>{
 const f=fixture(calendar=>calendar.dependencies.context='f'.repeat(64));
 const expected={as_of:observationAt,generation:'g',groups:pointerPath,view:'view.json',impulses:'impulses.json',resources:'resources.json'},status={hidden:true,setAttribute(name,value){this[name]=value;}},controls=[{disabled:false},{disabled:false}];
 const documents={'view.json':{schema:'beops-impulse-view/v1'},'impulses.json':{schema:'beops-public-impulses/v2'},'resources.json':{schema:'beops-resource-summary/v1'}};
 const fetch=async(name,options)=>{const value=documents[name.split('?')[0]];return value?{ok:true,json:async()=>({...value,as_of:observationAt,generation:'g'})}:f.request(name,options);};
 const document={getElementById:id=>id==='payload'?{textContent:JSON.stringify(expected)}:status,querySelectorAll:selector=>selector==='button,select'?controls:[]};
 vm.runInNewContext(fs.readFileSync(require.resolve('../public/impulsi'),'utf8'),{document,fetch,crypto:crypto.webcrypto,TextDecoder,BeopsImpulseCodec:{decodeImpulses:value=>value}});
 for(let i=0;i<30&&status.role!=='alert';i++)await new Promise(setImmediate);
 assert.equal(status.hidden,false);assert.equal(status.role,'alert');assert.ok(status.textContent.includes('ne podudaraju'));assert.ok(controls.every(control=>control.disabled));
});
