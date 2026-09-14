'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),studies=path.join(__dirname,'05-design/studies');
const clocks=require(path.join(studies,'observation-clocks.js'));
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const read=name=>fs.readFileSync(path.join(studies,name),'utf8');
const between=(html,start,end)=>{const a=html.indexOf(start),b=html.indexOf(end,a+start.length);assert.ok(a>=0&&b>a,start);return html.slice(a,b);};
const line=(html,name)=>{const found=html.split(/\r?\n/).find(x=>x.startsWith('function '+name+'('));assert.ok(found,name);return found;};
const escaped=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const stream={station:'Same station',datastream:'1|PM10',parameter:'PM10',unit:'ug.m-3',points:[p]};
const source={sid:'S146',name:'Same source',cadence_seconds:3600,datastreams:[stream]};
const elements=new Map();
const element=id=>{if(!elements.has(id))elements.set(id,{innerHTML:'',textContent:'',firstElementChild:{textContent:''}});return elements.get(id);};
const context={beopsClocks:clocks,LANG:'sr',SNAP:{sources:[source]},S:sr=>sr,t:k=>k,esc:escaped,
  document:{documentElement:{lang:'sr'},getElementById:element,querySelectorAll:()=>[]},
  css:String,spark:()=>'',PAR:'PM10',AIR_PARAMETERS:new Set(['PM10']),sepa:()=>source,drawMap(){},
  P:Date.parse,fmtT:String,fmt:String,pname:String,n1:String};
vm.createContext(context);
const expected=clocks.describe(p,'sr');
vm.runInContext(between(read('sada.html'),'function evidenceText(','// BEOPS freshness contract:'),context);
assert.ok(context.provenanceFull({src:'fallback'},{sid:'S146',d:stream,p}).includes(expected));
assert.ok(context.provenance({src:'fallback'},{sid:'S146',d:stream,p}).includes(clocks.html(p,'sr')));
const data=read('podaci.html');
vm.runInContext(line(data,'latestPoint')+'\n'+line(data,'latest')+'\n'+between(data,'function renderSepa(){','function renderSC(){'),context);
context.renderSepa();
assert.ok(element('septable').innerHTML.includes(clocks.html(p,'sr')),'Podaci keeps clocks on a latest null');
assert.ok(element('septable').innerHTML.includes('>—</td>'),'null remains missing');
const ribbon=read('traka-live.html');
context.lanes={groups:[{src:source,params:[{param:'PM10',unit:'ug.m-3',streams:[stream]}]}]};
vm.runInContext(line(ribbon,'pointAt')+'\n'+between(ribbon,'function reading(t){','function fmtT('),context);
assert.equal(context.pointAt(p),clocks.stamp(p.tc),'ribbon uses the estimated clock, not the uncorrected label');
context.reading(clocks.stamp(p.tc));
assert.ok(element('rr').innerHTML.includes(clocks.html(p,'sr')),'same row clocks in reading column');
const witnesses=read('svedoci.html');
vm.runInContext('var LAST_LATENCY;\n'+between(witnesses,'function drawLatency(d){','function drawAgreement('),context);
context.drawLatency({names:{S146:'Same source'},by_source:{S146:{
  polling_interval_minutes:10,age_by_clock:{corrected:{median:5,p90:8,n:30}},
  successful_reception_gaps:{max_minutes:40},clock_example:p}}});
assert.ok(element('lrows').innerHTML.includes(clocks.html(p,'sr')),'same row clocks in Svedoci');
assert.ok(element('lrows').innerHTML.includes('40 min'));
assert.ok(element('lrows').innerHTML.includes('Gornja granica našeg doprinosa kašnjenju nije poznata'));
assert.doesNotMatch(element('lrows').innerHTML,/class="ours"/,'cadence is not a measured part of age');

assert.equal(clocks.stamp('1970-01-01T00:00:00Z'),0);
assert.equal(clocks.stamp('2026-02-30T10:00:00Z'),null);
assert.equal(clocks.stamp('2026-09-14T15:00:00'),null);
assert.equal(clocks.stamp('2026-09-14T17:00:00+02:00'),clocks.stamp('2026-09-14T15:00:00Z'));
assert.equal(clocks.disclose({...p,tc:'invalid'}).measurement_time,null);
assert.equal(clocks.placement({...p,tc:'invalid'}).basis,'unresolved');
for(const lang of ['sr','en','zh','de']){
  const text=clocks.describe(p,lang);assert.ok(text.includes('17:00 UTC')&&text.includes('15:00 UTC'));
}
assert.ok(!clocks.html({...p,clock_note:'<img src=x onerror=alert(1)>'}).includes('<img'));

const temp=fs.mkdtempSync(path.join(os.tmpdir(),'beops-clock-surfaces-'));
try{
  fs.mkdirSync(path.join(temp,'public'));fs.mkdirSync(path.join(temp,'research'));
  fs.writeFileSync(path.join(temp,'research/SOURCE_REGISTRY.json'),JSON.stringify({sources:[{id:'S146',status:'collected',url:'https://example.org'}]}));
  const C=require(path.join(root,'tools/ai_feed_context.js'));
  const now=new Date(clocks.stamp(p.rx)+600000),file=path.join(temp,'public/live-snapshot.json');
  const write=points=>fs.writeFileSync(file,JSON.stringify({as_of:now.toISOString(),sources:[{...source,datastreams:[{...stream,points}]}]}));
  const valid={...p,v:20};write([valid]);
  const fact=C.buildContext(temp,now,{},new Set(['S146'])).facts[0];
  assert.deepEqual(fact.clocks,clocks.disclose(valid));
  assert.equal(fact.clock_explanation,expected);
  assert.equal(fact.clock,'corrected_measurement');
  write([valid,{...valid,v:null,tc:'2026-09-14T15:05:00Z',t:'2026-09-14T17:05:00Z',rx:'2026-09-14T15:08:00Z'}]);
  assert.throws(()=>C.buildContext(temp,now,{},new Set(['S146'])),/no_usable_facts/,'AI may not resurrect an older value after latest null');
  write([{...valid,tc:'invalid'}]);
  assert.throws(()=>C.buildContext(temp,now,{},new Set(['S146'])),/no_usable_facts/,'invalid measurement clock cannot borrow reception');
  write([{v:0,tu:true,t:null,rx:p.rx,q:'unvalidated'}]);
  const parking=C.buildContext(temp,now,{},new Set(['S146'])).facts[0];
  assert.equal(parking.value,0);assert.equal(parking.clock,'reception_only');assert.equal(parking.age_minutes,null);
  assert.equal(parking.clocks.measurement_time,null);assert.equal(parking.reception_age_minutes,10);
}finally{
  const target=fs.realpathSync(temp),base=fs.realpathSync(os.tmpdir());
  if(!target.startsWith(base+path.sep)||!path.basename(target).startsWith('beops-clock-surfaces-'))throw Error('unsafe fixture cleanup');
  fs.rmSync(target,{recursive:true,force:true});
}
for(const name of ['sada.html','podaci.html','traka-live.html','svedoci.html']){
  for(const script of read(name).matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi))new vm.Script(script[1]);
}
console.log('Same SEPA row passed through Sada, Podaci, Traka, Svedoci and AI context; null, clocks, gap, invalid time and escaping checked.');
