'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const hash = value => crypto.createHash('sha256').update(typeof value === 'string' ? value : JSON.stringify(value)).digest('hex');
function readJSON(file, cap = 64 * 1024 * 1024) {
  if (fs.statSync(file).size > cap) throw Error('input_too_large');
  return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
}
const stamp = s => typeof s === 'string' && Number.isFinite(Date.parse(s)) ? Date.parse(s) : null;
function sampleTime(p) { return p.tc || (!p.tu && p.t) || p.rx; }
function frame(p) { return p.tc ? 'corrected_measurement' : !p.tu && p.t ? 'measurement' : 'reception_only'; }
function clean(s, n = 240) { return String(s || '').replace(/[\x00-\x1f<>]/g, ' ').slice(0,n); }
function allowedSources(root, now) {
  const {spawnSync}=require('node:child_process');
  const bundled=path.join(process.env.USERPROFILE||'', '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe');
  const exe=process.env.BEOPS_TEST_PYTHON || (fs.existsSync(bundled)?bundled:'python');
  const r=spawnSync(exe,['-X','utf8','-B',path.join(__dirname,'ai_feed_policy.py'),root,now.toISOString()],{windowsHide:true,timeout:20000,encoding:'utf8',maxBuffer:1024*1024});
  if(r.status!==0)throw Error('permission_projection_failed');
  return new Set(JSON.parse(r.stdout));
}
function buildContext(root, now = new Date(), config = {}, permittedOverride) {
  const snapshot = readJSON(path.join(root, 'public/live-snapshot.json'));
  const asof = stamp(snapshot.as_of), time = +now;
  if (!asof || asof > time + 300000 || time - asof > (config.stale_snapshot_minutes || 30) * 60000) throw Error('snapshot_stale_or_invalid');
  const registry = readJSON(path.join(root,'research/SOURCE_REGISTRY.json'));
  const sources = new Map(registry.sources.map(s=>[s.id,s]));
  const permitted=permittedOverride || allowedSources(root,now);
  const facts = [], coverage = [];
  for (const source of snapshot.sources || []) {
    const reg = sources.get(source.sid);
    if (!reg || !permitted.has(source.sid) || ['opted_out','restricted','needs_decision','account_required','no_coverage'].includes(reg.status)) continue;
    const candidates = [];
    for (const stream of source.datastreams || []) {
      // Last received revision wins for the same observation; future receptions cannot leak in.
      const unique = new Map();
      for (const p of stream.points || []) {
        const t = stamp(sampleTime(p)), rx = stamp(p.rx);
        if (typeof p.v !== 'number' || !Number.isFinite(p.v) || !t || !rx || t > asof || rx > asof || t < asof - 86400000) continue;
        const key = frame(p) + '|' + t;
        if (!unique.has(key) || rx > stamp(unique.get(key).rx)) unique.set(key,p);
      }
      const values = [...unique.values()].sort((a,b)=>stamp(sampleTime(a))-stamp(sampleTime(b)));
      const last = values.at(-1);
      if (!last) continue;
      const ageMinutes = Math.round((asof - stamp(sampleTime(last)))/60000);
      if (ageMinutes > Math.max(120, (source.cadence_seconds || 3600)/60*3)) continue;
      const previous = values.find(p=>frame(p)===frame(last) && stamp(sampleTime(p)) < stamp(sampleTime(last))-1800000 && stamp(sampleTime(p)) >= stamp(sampleTime(last))-21600000);
      const fact = {kind:'observation',sid:source.sid,source:clean(source.name),url:reg.url,
        place:clean(stream.station),stream:clean(stream.datastream),metric:clean(stream.parameter),
        value:last.v,unit:clean(stream.unit),time:sampleTime(last),received_at:last.rx,
        reported_time:last.t || null,result_time:last.rt || null,clock:frame(last),quality:clean(last.q),age_minutes:ageMinutes};
      if (Number.isFinite(stream.lat) && Number.isFinite(stream.lon)) fact.location = [stream.lon,stream.lat];
      if (previous) fact.comparison = {kind:'same_stream_change',from_value:previous.v,from_time:sampleTime(previous),
        delta:Math.round((last.v-previous.v)*1e6)/1e6,limitation:'Two observations on the same clock, not a causal explanation or a long-term trend.'};
      candidates.push(fact);
    }
    coverage.push({sid:source.sid,usable_streams:candidates.length,observed_streams:(source.datastreams||[]).length});
    // Rotate over stations rather than repeatedly selecting the highest reading.
    candidates.sort((a,b)=>a.stream.localeCompare(b.stream));
    const start = candidates.length ? Math.floor(time/1800000)%candidates.length : 0;
    for (let i=0;i<Math.min(1,candidates.length);i++) facts.push(candidates[(start+i)%candidates.length]);
  }
  const selected = facts.slice(0,config.max_live_facts || 8);
  const catalogFile = path.join(root,'public/context-catalog.json');
  let catalog = null;
  if (fs.existsSync(catalogFile)) {
    catalog = readJSON(catalogFile,4*1024*1024);
    const admitted=readJSON(path.join(root,'research/CONTEXT_DATASETS.json'));
    const rights=admitted.rzs_rights;
    if(hash(catalog.rights)!==hash(rights))throw Error('context_rights_mismatch');
    const evidence=path.resolve(root,rights.evidence);
    if(!evidence.startsWith(path.resolve(root,'research/evidence')+path.sep) || crypto.createHash('sha256').update(fs.readFileSync(evidence)).digest('hex')!==rights.sha256)throw Error('context_rights_evidence_mismatch');
    for(const dataset of catalog.datasets||[]){
      if(!dataset.table)continue;
      const table=path.resolve(root,'public',dataset.table);
      if(!table.startsWith(path.resolve(root,'public/context-tables')+path.sep) || crypto.createHash('sha256').update(fs.readFileSync(table)).digest('hex')!==dataset.table_sha256)throw Error('context_table_hash_mismatch');
    }
    for (const dataset of catalog.datasets || []) {
      if(catalog.rights?.redistribution !== true || catalog.rights?.external_ai !== true || !Number.isFinite(Date.parse(catalog.rights.review_due)) || Date.parse(catalog.rights.review_due)<time)continue;
      if (dataset.ai_eligible !== true) continue;
      const row = (dataset.latest || []).find(r=>['79014','RS110'].includes(r.territory_id)) || (dataset.latest || [])[0];
      if (row) selected.push({kind:'historical_context',dataset_id:dataset.id,sid:dataset.sid,source:dataset.title,
        edition:dataset.edition,attribution:dataset.attribution,url:dataset.url,...row,
        limitation:'A dated statistic at the stated geography, not a live reading or a causal explanation.'});
      if (selected.length>=20) break;
    }
  }
  if (!selected.length) throw Error('no_usable_facts');
  selected.forEach((f,i)=>{f.id='F'+(i+1);});
  const packet={schema:'beops-ai-context/v1',as_of:snapshot.as_of,created_at:now.toISOString(),language:'sr-Latn',
    scope:'Belgrade; historical context retains its own geography and period.',facts:selected,coverage,
    selection:'At most one fresh stream per source, station rotation, then admitted historical context. No articles or conversation memory.',
    baseline:'Same-stream comparisons only in v1. No long-term normality or health threshold is supplied.',
    catalog_hash:catalog ? hash(catalog) : null};
  while (Buffer.byteLength(JSON.stringify(packet))>(config.max_context_bytes||24000) && packet.facts.length>1) packet.facts.pop();
  if (Buffer.byteLength(JSON.stringify(packet))>(config.max_context_bytes||24000)) throw Error('context_budget_exceeded');
  return packet;
}
function validateOutput(value, packet, cap=5000) {
  const reasons=[], keys=['title','paragraphs','question','limitations'];
  if (!value || typeof value!=='object' || Array.isArray(value)) return {ok:false,reasons:['not_an_object']};
  if (Object.keys(value).some(k=>!keys.includes(k)) || keys.some(k=>!(k in value))) reasons.push('fields');
  for (const k of ['title','question','limitations']) if (typeof value[k]!=='string' || !value[k].trim() || value[k].length>(k==='title'?140:900)) reasons.push(k);
  const facts=new Map(packet.facts.map(f=>[f.id,f]));
  const paragraphs=Array.isArray(value.paragraphs)?value.paragraphs:[];
  if (paragraphs.length<1 || paragraphs.length>3) reasons.push('paragraph_count');
  const numbers=s=>(s.match(/\d+(?:[.,]\d+)?/g)||[]).map(n=>n.replace(',','.'));
  for(const p of paragraphs){
    if(!p || typeof p.text!=='string' || p.text.length<20 || p.text.length>1800 || Object.keys(p).some(k=>!['text','cites'].includes(k))) {reasons.push('paragraph');continue;}
    if(!Array.isArray(p.cites) || !p.cites.length || p.cites.length>4 || p.cites.some(c=>!facts.has(c))) {reasons.push('citation');continue;}
    const allowed=new Set(numbers(p.cites.map(c=>JSON.stringify(facts.get(c))).join(' ')));
    if(numbers(p.text).some(n=>!allowed.has(n))) reasons.push('unsupported_number');
  }
  const prose=[value.title,...paragraphs.map(p=>p?.text),value.question,value.limitations].join(' ');
  if(/\p{Script=Cyrillic}/u.test(prose) || (prose.match(/\b(?:je|nije|ali|da|ne|se|u|na|kako|ovo|podaci|koji|kao|koje)\b/gi)||[]).length<6) reasons.push('serbian_latin_not_established');
  if(/\b(?:I (?:walk|saw|went|live)|video sam|videla sam|lično sam|dok šetam|šetao sam|šetala sam)\b/i.test(prose)) reasons.push('invented_firsthand_experience');
  if(prose.length>cap || /<[^>]*>|https?:|\b(?:system prompt|ignore previous|api[_ -]?key)\b/i.test(prose)) reasons.push('unsafe_or_large_text');
  // Uncited title/question/limitation must not introduce a numeric claim.
  if(numbers([value.title,value.question,value.limitations].join(' ')).length) reasons.push('uncited_number');
  if(!/[?？]/.test(value.question||'')) reasons.push('missing_question');
  return {ok:!reasons.length,reasons:[...new Set(reasons)],version:'citizen-v1',scope:'Structural, citation and numeric checks; not proof of interpretation accuracy.'};
}
module.exports={buildContext,validateOutput,readJSON,hash,stamp,allowedSources};
