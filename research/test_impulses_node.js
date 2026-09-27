'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {test}=require('node:test');
const m=require('../tools/impulse_model'),{hash}=require('../tools/ai_feed_context'),{build}=require('../tools/build_impulses');
const now=Date.parse('2026-09-27T12:00:00Z');
const headline=(extra={})=>({sid:'S15',parameter:'headline',result:'Radovi na Novom Beogradu',link:'https://example.test/notice',resultTime:'2026-09-26T12:00:00Z',receivedTime:'2026-09-26T13:00:00Z',...extra});
test('local publication dates preserve Belgrade daylight-saving day lengths',()=>{
 const autumn=m.clock('2026-10-25',null),spring=m.clock('2026-03-29',null);
 assert.equal(autumn.start,'2026-10-24T22:00:00.000Z');assert.equal(Date.parse(autumn.end)-Date.parse(autumn.start),25*3600000);
 assert.equal(spring.start,'2026-03-28T23:00:00.000Z');assert.equal(Date.parse(spring.end)-Date.parse(spring.start),23*3600000);
 assert.equal(m.clock('2026-02-30','2026-09-26T13:00:00Z').basis,'first_reception');
 assert.equal(m.clock('2026-09-26T12:00:00',null).basis,'unknown');
});
test('canonical source URL removes repeat collection and revisions without moving first clock',()=>{
 const result=m.collectHeadlines([headline(),headline({result:'Novo obaveštenje',link:'https://example.test/notice?utm_source=x#top',resultTime:'2026-09-27T10:00:00Z',receivedTime:'2026-09-27T11:00:00Z'}),headline()],now);
 assert.equal(result.items.length,1);assert.equal(result.items[0].revisions,2);assert.equal(result.items[0].clock.at,'2026-09-26T12:00:00.000Z');assert.equal(result.items[0].title,'Novo obaveštenje');assert.equal(result.audit.repeated_or_revised_rows,2);
 assert.equal(m.collectHeadlines([headline(),headline({sid:'S208'})],now).items.length,2);
});
test('redacted, future and invalid receptions are not mapped',()=>{
 const result=m.collectHeadlines([headline({redacted:true}),headline({receivedTime:'2026-09-28T00:00:00Z'}),headline({receivedTime:'invalid'})],now);
 assert.equal(result.items.length,0);assert.equal(result.audit.redacted_rows,1);assert.equal(result.audit.after_snapshot_rows,1);assert.equal(result.audit.invalid_receipt_rows,1);
});
test('Cyrillic and Latin place-name matches do not invent a coordinate or event time',()=>{
 const result=m.collectHeadlines([headline({result:'Радови на Новом Београду и Бранковом мосту'})],now).items[0];
 assert.deepEqual(result.places.map(p=>p.name),['Novi Beograd','Brankov most']);assert.equal(result.point,null);assert.equal(result.event_time,null);assert.ok(result.places.every(p=>p.coordinates===null));
 assert.equal(m.mentions('Palilula')[0].kind,'ambiguous_area');assert.deepEqual(m.mentions('Zemunica'),[]);
});
test('AI points require accepted entry, frozen context hash and exactly cited coordinates',()=>{
 const packet={facts:[{id:'F1',sid:'S146',place:'Station',url:'https://example.test/data',location:[20.4,44.8]}]};
 const entry={id:'1',at:'2026-09-27T10:00:00Z',validation:{ok:true},context_hash:hash(packet),model:'fixture',content:{title:'Observation',paragraphs:[{cites:['F1']}],geo:{lat:44.8,lon:20.4}}};
 const item=m.aiItem(entry,packet,now);assert.equal(item.point.lon,20.4);assert.equal(item.clock.basis,'model_output_time');assert.equal(item.event_time,null);assert.equal(item.source_url,'https://example.test/data');
 assert.equal(m.aiItem({...entry,validation:{ok:false}},packet,now),null);
 assert.equal(m.aiItem({...entry,context_hash:'0'.repeat(64)},packet,now).point,null);
 assert.equal(m.aiItem({...entry,content:{...entry.content,geo:{lat:44.80001,lon:20.4}}},packet,now).point,null);
 assert.equal(m.aiItem({...entry,content:{...entry.content,paragraphs:[{cites:[]}]}},packet,now).point,null);
});
test('official schedules stay separate from occurrence and require explicit source time',()=>{
 const event={id:'e',verified:true,classification:'official-repertoire',event_start:'2026-10-11T14:00:00Z',source_id:'S225',source:'Kolarac',url:'https://example.test/concert',provenance:{received_at:'2026-09-27T10:00:00Z'}};
 assert.equal(m.calendarItems([{...event,verified:'true'}],now).length,0);
 const items=m.calendarItems([event,event],now);assert.equal(items.length,1);assert.equal(items[0].point,null);assert.equal(items[0].clock.basis,'scheduled_event_time');
 const snapshot=m.buildSnapshot(items,now);assert.equal(snapshot.upcoming.counts.scheduled_events,1);assert.equal(snapshot.windows.month.counts.scheduled_events,0);
});
const officialEvent=(extra={})=>({id:'venue-e',title:'Official concert',verified:true,classification:'official-repertoire',event_start:'2026-09-28T14:00:00Z',source_id:'S226',source:'Dom omladine',url:'https://domomladine.org/koncerti/example/',location:'DOB//Amerikana',venue_id:'dom-omladine',provenance:{received_at:'2026-09-27T10:00:00Z',url:'https://domomladine.org/',raw_sha256:'a'.repeat(64),source_label:'Official concert 28.9.2026 DOB//Amerikana'},...extra});
test('explicit official venue binding stays separate from headline estimates and AI anchors',()=>{
 const item=m.calendarItems([officialEvent()],now)[0];
 assert.equal(item.geo.scope,'belgrade');assert.equal(item.point,null);assert.equal(item.location_estimate,undefined);
 assert.equal(item.venue_location.place_id,'dom-omladine');assert.equal(item.venue_location.verified,false);
 assert.equal(item.venue_location.lon,20.4628098);assert.match(item.venue_location.evidence.source_url,/\/way\/41234985$/);
 assert.match(item.venue_location.address_evidence.address,/Makedonska 22/);
 assert.equal(item.clock.basis,'scheduled_event_time');assert.equal(item.state,'scheduled');
 const result=m.buildSnapshot([item],now);
 assert.equal(result.coverage.estimated_locations,0);assert.equal(result.coverage.with_coordinates,0);assert.equal(result.coverage.located_scheduled_events,1);
 assert.equal(result.windows.month.counts.scheduled_events,0);assert.equal(result.upcoming.counts.located_scheduled_events,1);
});
test('venue binding rejects publisher-only, conflicting, stale and unsourced location data',()=>{
 const good=officialEvent();
 for(const event of [
  officialEvent({location:'Narodno pozorište'}),officialEvent({location:null}),
  officialEvent({venue_id:'kcb-artget'}),officialEvent({source_id:'S227'}),
  officialEvent({url:'https://example.test/concert'}),
  officialEvent({provenance:{...good.provenance,url:'https://example.test/'}}),
  officialEvent({provenance:{...good.provenance,raw_sha256:null}}),
  officialEvent({provenance:{...good.provenance,source_label:'Concert without explicit room'}}),
  officialEvent({provenance:{...good.provenance,received_at:'2026-09-25T10:00:00Z'}})
 ]){const item=m.calendarItems([event],now)[0];assert.equal(item.venue_location,null,JSON.stringify(event));assert.equal(item.geo.scope,'unknown');}
 const future=officialEvent({provenance:{...good.provenance,received_at:'2026-09-28T10:00:00Z'}});
 assert.equal(m.calendarItems([future],now).length,0);
});
test('freshness is checked independently for every official source, including legacy Kolarac',()=>{
 const event=officialEvent(),source={source_id:'S226',state:'available',received_at:event.provenance.received_at};
 assert.equal(m.calendarItems([event],now,[source]).length,1);
 for(const sources of [[],[{...source,state:'failed'}],[{...source,received_at:'2026-09-27T11:00:00Z'}],[{...source,source_id:'S227'}]])assert.equal(m.calendarItems([event],now,sources).length,0);
 const kolarac=officialEvent({source_id:'S225',url:'https://www.kolarac.rs/koncerti/example/',location:'Велика дворана',venue_id:null,provenance:{...event.provenance,url:'https://www.kolarac.rs/koncerti/',source_label:'Концерт 28.9.2026 Велика дворана'}});
 const item=m.calendarItems([kolarac],now)[0];assert.equal(item.venue_location.place_id,'kolarac');assert.equal(item.venue_location.lon,20.456328);assert.equal(item.places[0].name,'Велика дворана');
 const artget=officialEvent({source_id:'S227',url:'https://www.kcb.org.rs/2026/09/example/',location:'Galerija ARTGET',venue_id:'kcb-artget',provenance:{...event.provenance,url:'https://www.kcb.org.rs/',source_label:'Concert Galerija ARTGET'}});
 assert.equal(m.calendarItems([artget],now)[0].venue_location.place_id,'kcb-artget');
});
test('frozen impulse builder rejects missing v2 source metadata and exposes per-source stale health',async()=>{
 const base=path.resolve(process.env.BEOPS_TEST_TEMP||path.resolve(__dirname,'../runtime/impulse-test-work'));fs.mkdirSync(base,{recursive:true});const root=fs.mkdtempSync(path.join(base,'calendar-'));
 try{
  fs.mkdirSync(path.join(root,'research'),{recursive:true});fs.mkdirSync(path.join(root,'data/live/derived/events'),{recursive:true});
  fs.writeFileSync(path.join(root,'research/COLLECTORS.json'),JSON.stringify({sources:[]}));
  const event=officialEvent(),target=path.join(root,'data/live/derived/events/repertoire.json');
  fs.writeFileSync(target,JSON.stringify({schema:'beops-repertoire-cache/v2',state:'available',sources:[],events:[event]}));
  assert.equal((await build(root,now)).coverage.scheduled_events,0);
  const old=officialEvent({provenance:{...event.provenance,received_at:'2026-09-25T10:00:00Z'}});
  fs.writeFileSync(target,JSON.stringify({schema:'beops-repertoire-cache/v2',state:'available',sources:[{source_id:'S226',state:'available',received_at:old.provenance.received_at}],events:[old]}));
  const result=await build(root,now);assert.equal(result.coverage.scheduled_events,0);assert.equal(result.audit.calendar_sources[0].state,'stale');assert.equal(result.audit.calendar_sources[0].event_count,0);
 }finally{assert.ok(path.resolve(root).startsWith(base+path.sep));fs.rmSync(root,{recursive:true,force:true});}
});
test('rolling durations and exclusive end stay explicit, and local-day records overlap honestly',()=>{
 const items=m.collectHeadlines([headline(),headline({sid:'S2',link:'https://example.test/two',resultTime:'2026-09-27',receivedTime:'2026-09-27T11:00:00Z'})],now).items;
 const result=m.buildSnapshot(items,now);assert.equal(result.windows.day.duration_hours,24);assert.equal(result.windows.week.duration_hours,168);assert.equal(result.windows.month.duration_hours,720);
 assert.equal(result.windows.day.counts.total,2);assert.equal(result.windows.day.timezone,'Europe/Belgrade');
 assert.equal(m.inWindow({clock:{start:new Date(now).toISOString(),end:null}},now-m.DAY,now),false);
});
test('bounded reader ignores empty row files and fails closed for correction overlays',async()=>{
 const base=path.resolve(process.env.BEOPS_TEST_TEMP||path.resolve(__dirname,'../runtime/impulse-test-work'));assert.ok(base.toLowerCase().startsWith(path.resolve('C:/Svemir').toLowerCase()+path.sep));fs.mkdirSync(base,{recursive:true});const root=fs.mkdtempSync(path.join(base,'test-'));
 try{
  fs.mkdirSync(path.join(root,'research'),{recursive:true});fs.mkdirSync(path.join(root,'data/live/rows/S15'),{recursive:true});
  fs.writeFileSync(path.join(root,'research/COLLECTORS.json'),JSON.stringify({sources:[{sid:'S15',name:'City',parser:'city_listing'}]}));
  fs.writeFileSync(path.join(root,'data/live/rows/S15/2026-09.jsonl'),'');assert.equal((await build(root,now)).coverage.total,0);
  fs.writeFileSync(path.join(root,'data/live/rows/S15/2026-09.jsonl'),JSON.stringify(headline())+'\n');
  fs.writeFileSync(path.join(root,'data/live/corrections.jsonl'),JSON.stringify({sid:'S15',fields:{redacted:true}})+'\n');
  const out=await build(root,now);assert.equal(out.coverage.total,0);assert.equal(out.audit.input_errors[0].source_id,'S15');
 }finally{assert.ok(path.resolve(root).startsWith(base+path.sep));fs.rmSync(root,{recursive:true,force:true});}
});

test('estimated headline areas stay separate from exact AI anchors and retain geographic exclusions',()=>{
 const rows=[
  headline({result:'Radovi na Novom Beogradu'}),
  headline({result:'Zagađen vazduh u Nišu',link:'https://example.test/nis'}),
  headline({result:'Požar u Parizu',link:'https://example.test/paris'}),
  headline({result:'Kvalitet vazduha je loš',link:'https://example.test/unknown'})
 ];
 const items=m.collectHeadlines(rows,now).items,local=items[0];
 assert.equal(local.point,null);assert.equal(local.event_time,null);
 assert.equal(local.geo.scope,'belgrade');assert.ok(local.location_estimate.radius_m>0);
 assert.equal(local.location_estimate.verified,false);
 const out=m.buildSnapshot(items,now),w=out.windows.month;
 assert.equal(out.schema,'beops-impulses/v2');assert.equal(w.points.length,0);
 assert.equal(w.counts.with_coordinates,0);assert.ok(w.counts.estimated_locations>=1);
 assert.equal(w.counts.belgrade_headlines,1);assert.equal(w.counts.serbia_headlines,1);
 assert.equal(w.counts.outside_headlines,1);assert.equal(w.counts.unknown_geography,1);
 assert.equal(w.counts.total,4);
 const circle=w.estimates.find(x=>x.id===local.id);
 assert.equal(circle.source_url,local.source_url);assert.equal(circle.radius_m,local.location_estimate.radius_m);
 assert.equal(circle.scope,'belgrade');assert.ok(circle.evidence);
 assert.match(out.semantics.locations,/not calibrated probability/);
});
