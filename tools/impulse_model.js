'use strict';
// A received/publication signal is not evidence that an event occurred.
const crypto = require('node:crypto');
const {geoReasons, validLocation, hash} = require('./ai_feed_context');
const {locateHeadline} = require('./headline_geo');
const venueRegister = require('./event_venues.json');
const TZ = 'Europe/Belgrade';
const DAY = 86400000;
const dateFormat = new Intl.DateTimeFormat('en-CA', {timeZone: TZ, year:'numeric', month:'2-digit', day:'2-digit'});
const stamp = value => typeof value === 'string' && /(?:Z|[+-]\d\d:\d\d)$/.test(value) && Number.isFinite(Date.parse(value)) ? Date.parse(value) : null;
const localDate = value => dateFormat.format(new Date(value));
const iso = value => new Date(value).toISOString();
const midnights = new Map();
function localMidnight(day) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || !Number.isFinite(Date.parse(day)) || iso(Date.parse(day)).slice(0,10)!==day) return null;
  if(midnights.has(day))return midnights.get(day);
  const noon = Date.parse(day+'T12:00:00Z');
  // Belgrade local dates begin at 22:00 or 23:00 UTC; derive this from Intl, not a fixed DST rule.
  for (let t=noon-15*3600000;t<=noon;t+=3600000) if(localDate(t)===day && localDate(t-1)!==day) {midnights.set(day,t);return t;}
  return null;
}
function clock(published, received) {
  const at=stamp(published);
  if(at!==null) return {basis:'publication_time',at:iso(at),start:iso(at),end:null};
  const start=typeof published==='string'?localMidnight(published):null;
  if(start!==null){const next=iso(Date.parse(published+'T12:00:00Z')+DAY).slice(0,10);return {basis:'publication_day',at:null,date:published,start:iso(start),end:iso(localMidnight(next))};}
  const rx=stamp(received);
  return rx===null?{basis:'unknown',at:null,start:null,end:null}:{basis:'first_reception',at:iso(rx),start:iso(rx),end:null};
}
const CYR='абвгдђежзијклљмнњопрстћуфхцчџш';
const LAT=['a','b','v','g','d','dj','e','z','z','i','j','k','l','lj','m','n','nj','o','p','r','s','t','c','u','f','h','c','c','dz','s'];
function normalize(text){return String(text||'').toLowerCase().replace(/[а-яђјљњћџ]/g,c=>LAT[CYR.indexOf(c)]||c).replace(/đ/g,'dj').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();}
// This is a disclosed name matcher, not a geocoder or an administrative boundary dataset.
const PLACES=[
 ['Novi Beograd','area',['novi beograd','novom beogradu','novog beograda']],
 ['Stari grad','area',['stari grad','starom gradu','starog grada']],
 ['Savski venac','area',['savski venac','savskom vencu','savskog venca']],
 ['Vračar','area',['vracar','vracaru','vracara']], ['Zvezdara','area',['zvezdara','zvezdari','zvezdare']],
 ['Voždovac','area',['vozdovac','vozdovcu','vozdovca']], ['Čukarica','area',['cukarica','cukarici','cukarice']],
 ['Rakovica','area',['rakovica','rakovici','rakovice']], ['Zemun','area',['zemun','zemunu','zemuna']],
 ['Palilula','ambiguous_area',['palilula','paliluli','palilule']], ['Borča','area',['borca','borci','borce']],
 ['Mirijevo','area',['mirijevo','mirijevu','mirijeva']], ['Batajnica','area',['batajnica','batajnici','batajnice']],
 ['Dorćol','area',['dorcol','dorcolu','dorcola']], ['Kalemegdan','landmark',['kalemegdan','kalemegdanu','kalemegdana']],
 ['Ada Ciganlija','landmark',['ada ciganlija','adi ciganliji','ade ciganlije']],
 ['Trg republike','landmark',['trg republike','trgu republike','trga republike']],
 ['Kolarac','venue',['kolarac','kolarcu','kolarca']], ['Dom omladine Beograda','venue',['dom omladine beograda','domu omladine beograda','doma omladine beograda']],
 ['Sava centar','venue',['sava centar','sava centru','sava centra']], ['Beogradska arena','venue',['beogradska arena','beogradskoj areni','stark arena','stark areni']],
 ['Gazela','bridge',['gazela','gazeli','gazele']], ['Brankov most','bridge',['brankov most','brankovom mostu','brankovog mosta']],
 ['Pančevački most','bridge',['pancevacki most','pancevackom mostu','pancevackog mosta']],
 ['Most na Adi','bridge',['most na adi','mostu na adi','mosta na adi']],
 ['Pupinov most','bridge',['pupinov most','pupinovom mostu','pupinovog mosta']],
 ['Slavija','landmark',['slavija','slaviji','slavije']], ['Tašmajdan','landmark',['tasmajdan','tasmajdanu','tasmajdana']]
];
function mentions(title){const n=' '+normalize(title)+' ';return PLACES.filter(p=>p[2].some(a=>n.includes(' '+a+' '))).map(([name,kind])=>({name,kind,method:'headline_name_match',coordinates:null,confidence:'candidate',limitation:kind==='ambiguous_area'?'Name is shared by more than one city; no Belgrade location is established.':'Mention alone does not establish where an event happened.'}));}
function safeURL(value){try{const u=new URL(value);return /^https?:$/.test(u.protocol)&&!u.username&&!u.password?u.href:null;}catch{return null;}}
function canonicalURL(value){const good=safeURL(value);if(!good)return null;const u=new URL(good);u.hash='';for(const k of [...u.searchParams.keys()])if(/^utm_|^fbclid$|^gclid$/i.test(k))u.searchParams.delete(k);u.searchParams.sort();return u.href;}
const id = value => crypto.createHash('sha256').update(value).digest('hex').slice(0,24);
function headlineKey(row){return row.sid+'|'+(canonicalURL(row.link)||row.dedupe_key||normalize(row.result));}
function collectHeadlines(rows, asof){
  const grouped=new Map();let raw=0,redacted=0,after_snapshot=0,invalid=0;
  for(const r of rows){
    if(r.parameter!=='headline'||typeof r.result!=='string'||!r.result.trim())continue;
    raw++;if(r.redacted){redacted++;continue;}
    const rx=stamp(r.receivedTime);if(rx===null){invalid++;continue;}if(rx>asof){after_snapshot++;continue;}
    const key=headlineKey(r),previous=grouped.get(key),revision=hash([r.result,r.resultTime]);
    if(previous){previous.revisions.add(revision);previous.raw_count++;if(rx<previous.first_received){previous.first_row=r;previous.first_received=rx;}if(rx>previous.last_received){previous.row=r;previous.last_received=rx;}continue;}
    grouped.set(key,{row:r,first_row:r,first_received:rx,last_received:rx,revisions:new Set([revision]),raw_count:1});
  }
  const items=[...grouped].map(([key,g])=>({id:'headline-'+id(key),kind:'headline_mention',title:g.row.result,source_id:g.row.sid,source:g.row.source||g.row.sid,source_url:safeURL(g.row.link),clock:clock(g.first_row.resultTime,iso(g.first_received)),event_time:null,first_received:iso(g.first_received),last_received:iso(g.last_received),latest_revision_published:g.row.resultTime||null,revisions:g.revisions.size,collection_rows:g.raw_count,places:mentions(g.row.result),point:null,evidence:{raw_sha256:g.row.raw_sha256||null,permission_capture:g.row.permission_capture||null},limitation:'A collected headline, not a verified event; repeated collections and URL revisions count once at the first retained publication/receipt clock. Title is the latest retained revision.'}));
  for(const item of items){
    item.geo=locateHeadline(item.title);
    item.location_estimate=item.geo.estimate;
    // The center of an estimated area is never promoted to an exact event point.
    if(item.location_estimate)item.limitation+=' Location is a headline-derived estimate with a disclosed radius, not a verified event coordinate.';
  }
  return {items,audit:{raw_headline_rows:raw,unique_headlines:items.length,repeated_or_revised_rows:raw-redacted-after_snapshot-invalid-items.length,redacted_rows:redacted,after_snapshot_rows:after_snapshot,invalid_receipt_rows:invalid}};
}
function scheduledVenue(event,asof){
 const received=stamp(event.provenance?.received_at),location=normalize(event.location);
 if(received===null||received>asof||asof-received>DAY||!location||!/^[a-f0-9]{64}$/.test(event.provenance?.raw_sha256||''))return null;
 const sourceURL=safeURL(event.url),repertoireURL=safeURL(event.provenance?.url);
 if(!sourceURL||!repertoireURL)return null;
 const venue=venueRegister.venues.find(v=>v.source_id===event.source_id&&(!event.venue_id||event.venue_id===v.id)&&
  v.location_aliases.some(alias=>normalize(alias)===location)&&v.source_hosts.includes(new URL(sourceURL).hostname)&&v.source_hosts.includes(new URL(repertoireURL).hostname));
 if(!venue||!normalize(event.provenance?.source_label).includes(location)||!validLocation([venue.lon,venue.lat]))return null;
 return {place_id:venue.id,name:venue.name,lon:venue.lon,lat:venue.lat,radius_m:venue.radius_m,precision:'venue',confidence:'explicit_source_venue',method:'official_schedule_venue_register/1',matched_text:event.location,radius_basis:'editorial_venue_buffer_not_statistical_error',verified:false,evidence:venue.evidence,address_evidence:venue.address_evidence};
}
function calendarItems(events,asof,sources=null){
 const seen=new Set(),items=[],sourceMap=sources===null?null:new Map(sources.map(s=>[s.source_id,s]));
 for(const e of events||[]){
  const at=stamp(e.event_start),received=stamp(e.provenance?.received_at),source=sourceMap?.get(e.source_id);
  if(e.verified!==true||e.classification!=='official-repertoire'||at===null||received===null||received>asof)continue;
  // V2 source failures cannot borrow the top-level union's timestamp or health.
  if(sourceMap&&(!source||source.state!=='available'||stamp(source.received_at)!==received||asof-received>DAY))continue;
  const key=e.source_id+'|'+(safeURL(e.url)||e.id)+'|'+iso(at);if(seen.has(key))continue;seen.add(key);
  const venue=scheduledVenue(e,asof);
  items.push({id:'schedule-'+id(key),kind:'scheduled_event',title:e.title,source_id:e.source_id,source:e.source,source_url:safeURL(e.url),clock:{basis:'scheduled_event_time',at:iso(at),start:iso(at),end:null},event_time:iso(at),first_received:iso(received),places:[{name:e.location||'Unknown venue',kind:'venue',method:'official_repertoire',coordinates:null,confidence:'source_stated'}],point:null,venue_location:venue,geo:{scope:venue?'belgrade':'unknown',status:venue?'scheduled_venue':'unresolved_venue',reason:venue?'explicit_source_venue_bound_to_sourced_building':'no_verified_venue_binding'},state:at>=asof?'scheduled':'past_schedule_unconfirmed',ticket_availability:e.ticket_availability==='sold_out'?'sold_out':'unknown',schedule_age_hours:Math.round((asof-received)/3600000*10)/10,schedule_fresh:asof-received<=DAY,evidence:{raw_sha256:e.provenance.raw_sha256||null,repertoire_url:safeURL(e.provenance.url)},limitation:'Official schedule facts from one source; actual occurrence, cancellation and end time are unknown. '+(venue?'Venue reference identifies the mapped building or gallery, not an exact event position.':'Venue coordinates have not been established.')});
 }
 return items;
}
function aiItem(entry,packet,asof){
  const at=stamp(entry.at);if(at===null||at>asof||!entry.id||!entry.content||entry.validation?.ok!==true)return null;
  let point=null,geo_status='no_explicit_anchor';
  const bound=packet&&entry.context_hash===hash(packet),geo=entry.content.geo;
  if(geo){geo_status=bound?'anchor_not_cited':'context_unverified';if(bound&&!geoReasons(entry.content,packet).length){const cites=new Set((entry.content.paragraphs||[]).flatMap(p=>p.cites||[]));const f=(packet.facts||[]).find(f=>cites.has(f.id)&&validLocation(f.location)&&(geo.layer?f.map_anchor?.layer===geo.layer&&f.map_anchor?.id===geo.id:f.location[0]===geo.lon&&f.location[1]===geo.lat));if(f){point={lon:f.location[0],lat:f.location[1],place:f.place||null,source_id:f.sid,source_url:safeURL(f.url),fact_id:f.id,context_hash:entry.context_hash,method:'exact_cited_context_coordinate'};geo_status='cited_anchor';}}}
  const cited=new Set((entry.content.paragraphs||[]).flatMap(p=>p.cites||[])),source_urls=bound?[...new Set((packet.facts||[]).filter(f=>cited.has(f.id)).map(f=>safeURL(f.url)).filter(Boolean))]:[];
  return {id:'ai-'+entry.id,kind:'ai_observation',title:entry.content.title,source_id:entry.provider||null,source:entry.model||null,source_url:point?.source_url||source_urls[0]||null,cited_source_urls:source_urls,clock:{basis:'model_output_time',at:iso(at),start:iso(at),end:null},event_time:null,first_received:iso(at),places:[],point,geo_status,evidence:{context_hash:entry.context_hash,context_verified:Boolean(bound),validation:entry.validation?.ok===true},limitation:'A model interpretation at a cited instrument location, not a new measurement or evidence of an event. Source URLs belong to cited facts, not to the model prose.'};
}
function counts(items){const headlines=items.filter(i=>i.kind==='headline_mention');return {total:items.length,headline_mentions:headlines.length,scheduled_events:items.filter(i=>i.kind==='scheduled_event').length,located_scheduled_events:items.filter(i=>i.kind==='scheduled_event'&&i.venue_location).length,ai_observations:items.filter(i=>i.kind==='ai_observation').length,with_coordinates:items.filter(i=>i.point).length,estimated_locations:headlines.filter(i=>i.location_estimate).length,belgrade_headlines:headlines.filter(i=>i.geo?.scope==='belgrade').length,serbia_headlines:headlines.filter(i=>i.geo?.scope==='serbia').length,outside_headlines:headlines.filter(i=>i.geo?.scope==='outside').length,unknown_geography:headlines.filter(i=>!i.geo||i.geo.scope==='unknown').length,with_name_candidates:items.filter(i=>i.places.length).length,without_location:items.filter(i=>!i.point&&!i.location_estimate&&!i.venue_location&&!i.places.length).length,unknown_clock:items.filter(i=>!i.clock.start).length};}
function inWindow(item,start,end){const a=stamp(item.clock.start),b=stamp(item.clock.end);return a!==null&&(b===null?a>=start&&a<end:a<end&&b>start);}
function summarize(items){const places=new Map(),daily=new Map();for(const i of items){for(const p of i.places){const key=p.kind+'|'+p.name;const g=places.get(key)||{name:p.name,kind:p.kind,coordinates:null,count:0,headline_mentions:0,scheduled_events:0,examples:[]};g.count++;if(i.kind==='headline_mention')g.headline_mentions++;if(i.kind==='scheduled_event')g.scheduled_events++;if(g.examples.length<3)g.examples.push({id:i.id,title:i.title,source_url:i.source_url,clock:i.clock});places.set(key,g);}const date=i.clock.date||(i.clock.at?localDate(stamp(i.clock.at)):null);if(date){const g=daily.get(date)||{date,headline_mentions:0,scheduled_events:0,ai_observations:0,with_coordinates:0};g[({headline_mention:'headline_mentions',scheduled_event:'scheduled_events',ai_observation:'ai_observations'})[i.kind]]++;if(i.point)g.with_coordinates++;daily.set(date,g);}}
return {counts:counts(items),points:items.filter(i=>i.point).map(i=>({id:i.id,kind:i.kind,title:i.title,clock:i.clock,...i.point})),estimates:items.filter(i=>i.kind==='headline_mention'&&i.location_estimate).map(i=>({id:i.id,kind:i.kind,title:i.title,clock:i.clock,source_url:i.source_url,...i.location_estimate,scope:i.geo.scope})),venues:items.filter(i=>i.kind==='scheduled_event'&&i.venue_location).map(i=>({id:i.id,kind:i.kind,title:i.title,clock:i.clock,source_url:i.source_url,...i.venue_location,scope:i.geo.scope})),named_places:[...places.values()].sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name)),daily:[...daily.values()].sort((a,b)=>a.date.localeCompare(b.date))};}
function buildSnapshot(items,asof,audit={}){
  if(!Number.isFinite(asof))throw Error('Invalid as_of');
  const windows={};
  for(const [name,days]of[['day',1],['week',7],['month',30]]){
    const start=asof-days*DAY;
    windows[name]={start:iso(start),end:iso(asof),duration_hours:days*24,timezone:TZ,
      semantics:'rolling_duration; publication-day intervals overlap windows; not a count of actual events',
      ...summarize(items.filter(i=>inWindow(i,start,asof)))};
  }
  const future=items.filter(i=>i.kind==='scheduled_event'&&stamp(i.clock.at)>=asof);
  return {schema:'beops-impulses/v2',as_of:iso(asof),timezone:TZ,
    scope:'Retained source signals; geographic coverage of collection, never citywide activity.',
    semantics:{
      headline_mention:'Publication or first receipt, never event time. One source URL counts once across repeated collection and revisions; separate sources are not assumed to describe distinct events.',
      scheduled_event:'Official scheduled start; occurrence not verified.',
      ai_observation:'Time the model produced an interpretation; exact cited context coordinates only.',
      locations:'Headline-derived location estimates are separate from exact cited AI anchors and explicitly stated scheduled venues. Their sourced centers and policy radii disclose spatial resolution, not calibrated probability or verified event coordinates. Names without adequate event-place context stay candidates.',
      geography:'Belgrade, Serbia outside or broader than Belgrade, outside Serbia, and unknown are separate scopes. Unknown or nonlocal titles cannot substantiate a Belgrade instrument comparison.',
      windows:'Trailing 24/168/720 hours ending at as_of (end exclusive); daily buckets use Europe/Belgrade. Day-resolution publication intervals overlap boundaries and may precede the first displayed local date.'
    },coverage:counts(items),audit,windows,upcoming:{counts:counts(future),items:future},items};
}
module.exports={TZ,DAY,stamp,localDate,localMidnight,clock,normalize,mentions,safeURL,canonicalURL,collectHeadlines,calendarItems,aiItem,counts,inWindow,buildSnapshot,PLACE_COUNT:PLACES.length};
