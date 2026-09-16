'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const observationClocks = require('../research/05-design/studies/observation-clocks.js');
const relationRules = require('./ai_feed_relations');
const hash = value => crypto.createHash('sha256').update(typeof value === 'string' ? value : JSON.stringify(value)).digest('hex');
function readJSON(file, cap = 64 * 1024 * 1024) {
  if (fs.statSync(file).size > cap) throw Error('input_too_large');
  return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
}
const stamp = observationClocks.stamp;
function sampleTime(p) { const clock=observationClocks.placement(p);return clock.basis==='unresolved'?null:clock.at; }
function frame(p) { return ({corrected:'corrected_measurement',measured:'measurement',received:'reception_only',unresolved:'unknown_clock'})[observationClocks.placement(p).basis]; }
function clean(s, n = 240) { return String(s || '').replace(/[\x00-\x1f<>]/g, ' ').slice(0,n); }
function allowedSources(root, now) {
  const {spawnSync}=require('node:child_process');
  const bundled=path.join(process.env.USERPROFILE||'', '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe');
  const runtimePath=path.join(root,'runtime/test-python.json');
  let runtimePython=null;
  try{if(fs.existsSync(runtimePath))runtimePython=JSON.parse(fs.readFileSync(runtimePath,'utf8').replace(/^\uFEFF/,'')).python;}catch{}
  const exe=process.env.BEOPS_TEST_PYTHON || (runtimePython&&fs.existsSync(runtimePython)?runtimePython:null) || (fs.existsSync(bundled)?bundled:'python');
  // The projection normally takes about five seconds on the live ledger, but collection, publishing
  // and the hourly baseline can legitimately contend for the same disk. Keep it inside the 120 s job
  // deadline while avoiding a false failure at the old 20 s cliff.
  const r=spawnSync(exe,['-X','utf8','-B',path.join(__dirname,'ai_feed_policy.py'),root,now.toISOString()],{windowsHide:true,timeout:45000,encoding:'utf8',maxBuffer:1024*1024});
  if(r.error || r.status!==0){
    const e=Error('permission_projection_failed');
    // Never copy child stderr (paths or secrets) into the public status.
    e.diagnostic={code:r.error?.code||null,exit_code:r.status,signal:r.signal||null,
      stderr_bytes:Buffer.byteLength(r.stderr||''),stderr_sha256:hash(r.stderr||'')};throw e;
  }
  let allowed;try{allowed=JSON.parse(r.stdout);}catch{throw Error('permission_projection_invalid_output');}
  if(!Array.isArray(allowed)||allowed.some(s=>!/^S\d+$/.test(s)))throw Error('permission_projection_invalid_output');
  return new Set(allowed);
}
function buildContext(root, now = new Date(), config = {}, permittedOverride) {
  const snapshot = readJSON(path.join(root, 'public/live-snapshot.json'));
  const asof = stamp(snapshot.as_of), time = +now;
  if (asof === null || asof > time + 300000 || time - asof > (config.stale_snapshot_minutes || 30) * 60000) throw Error('snapshot_stale_or_invalid');
  const registry = readJSON(path.join(root,'research/SOURCE_REGISTRY.json'));
  const sources = new Map(registry.sources.map(s=>[s.id,s]));
  const permitted=permittedOverride || allowedSources(root,now);
  const facts = [], coverage = [];
  for (const source of snapshot.sources || []) {
    const reg = sources.get(source.sid);
    if (!reg || !permitted.has(source.sid) || ['opted_out','restricted','needs_decision','account_required','no_coverage'].includes(reg.status)) continue;
    const candidates = [];
    const cadenceSeconds = source.sid === 'S52' ? 86400 : (source.cadence_seconds || 3600);
    const maxAgeMs = (source.sid === 'S52' ? 86400 * 3 : 86400) * 1000;
    for (const stream of source.datastreams || []) {
      // Last received revision wins for the same observation; future receptions cannot leak in.
      const unique = new Map();
      for (const p of stream.points || []) {
        const t = stamp(sampleTime(p)), rx = stamp(p.rx);
        if (t === null || rx === null || t > asof || rx > asof || t < asof - maxAgeMs) continue;
        const key = frame(p) + '|' + t;
        if (!unique.has(key) || rx >= stamp(unique.get(key).rx)) unique.set(key,p);
      }
      const values = [...unique.values()].sort((a,b)=>stamp(sampleTime(a))-stamp(sampleTime(b)));
      const last = values.at(-1);
      if (!last || typeof last.v !== 'number' || !Number.isFinite(last.v)) continue;
      const ageMinutes = Math.round((asof - stamp(sampleTime(last)))/60000);
      if (ageMinutes > Math.max(120, cadenceSeconds/60*3)) continue;
      const prevWindowMin = source.sid === 'S52' ? 86400000 * 3 : 21600000;
      const previous = values.find(p=>typeof p.v==='number' && Number.isFinite(p.v) && frame(p)===frame(last) && stamp(sampleTime(p)) < stamp(sampleTime(last))-1800000 && stamp(sampleTime(p)) >= stamp(sampleTime(last))-prevWindowMin);
      const namedClocks=observationClocks.disclose(last,source.clock_rules);
      const fact = {kind:'observation',sid:source.sid,source:clean(source.name),url:reg.url,
        place:clean(stream.station),stream:clean(stream.datastream),metric:clean(stream.parameter),
        value:last.v,unit:clean(stream.unit),time:sampleTime(last),received_at:last.rx,
        reported_time:last.t || null,result_time:last.rt || null,clock:frame(last),quality:clean(last.q),
        age_minutes:namedClocks.measurement_time===null?null:ageMinutes,
        reception_age_minutes:Math.round((asof-stamp(last.rx))/60000),
        clocks:namedClocks,clock_explanation:observationClocks.describe(last,'sr',source.clock_rules)};
      if (Number.isFinite(stream.lat) && Number.isFinite(stream.lon)) fact.location = [stream.lon,stream.lat];
      if (previous) fact.comparison = {kind:'same_stream_change',from_value:previous.v,from_time:sampleTime(previous),
        delta:Math.round((last.v-previous.v)*1e6)/1e6,limitation:'Two observations on the same clock, not a causal explanation or a long-term trend.'};
      candidates.push(fact);
    }
    coverage.push({sid:source.sid,usable_streams:candidates.length,observed_streams:(source.datastreams||[]).length});
    // Rotate over stations rather than repeatedly selecting the highest reading.
    candidates.sort((a,b)=>a.stream.localeCompare(b.stream));
    if (source.sid === 'S52') {
      const interesting = candidates.filter(c => !(c.metric === 'water_level_change' && c.value === 0));
      const sava = interesting.filter(c => c.place.includes('Sava'));
      const dunav = interesting.filter(c => c.place.includes('Dunav') || c.place.includes('Zemun'));
      const start = Math.floor(time/1800000);
      if (sava.length) facts.push(sava[start % sava.length]);
      if (dunav.length) facts.push(dunav[start % dunav.length]);
      if (!sava.length && !dunav.length && interesting.length) facts.push(interesting[start % interesting.length]);
    } else {
      const count = source.sid === 'S146' ? Math.min(2, candidates.length) : Math.min(1, candidates.length);
      const start = candidates.length ? Math.floor(time/1800000)%candidates.length : 0;
      for (let i=0;i<count;i++) facts.push(candidates[(start+i)%candidates.length]);
    }
  }
  const selected = facts.slice(0,config.max_live_facts || 8);
  const popFile = path.join(root,'public/context-population.json');
  if (fs.existsSync(popFile)) {
    try {
      const pop = readJSON(popFile, 4 * 1024 * 1024);
      if (pop && typeof pop.people_total === 'number' && Number.isFinite(pop.people_total)) {
        selected.push({
          kind:'demographic_context',dataset_id:pop.name||'kontur-population',sid:pop.source?.sid||'S120',
          source:'Kontur Population',edition:clean(pop.source?.release||'2022-06-30'),
          attribution:clean(pop.attribution||'Kontur Population, Serbia resource release 2022-06-30, CC BY 4.0; filtered by BEOPS.'),
          url:clean(pop.source?.url||'https://data.humdata.org/'),
          territory_id:null,place:'prozor posmatranja oko centra Beograda (ne administrativna granica)',geography:'observation_window',
          period:'2022',value:pop.people_total,unit:'stanovnika',
          metric:'Modelovan zbir stanovnika u H3 ćelijama unutar prozora posmatranja',
          limitation:'H3 modelovana procena gustine naseljenosti unutar prozora posmatranja; nije broj stanovnika Grada Beograda niti trenutni popis.'
        });
      }
    } catch {}
  }
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
    const eligibleDatasets = (catalog.datasets || []).filter(dataset => {
      if(catalog.rights?.redistribution !== true || catalog.rights?.external_ai !== true || !Number.isFinite(Date.parse(catalog.rights.review_due)) || Date.parse(catalog.rights.review_due)<time) return false;
      return dataset.ai_eligible === true && Array.isArray(dataset.latest) && dataset.latest.length > 0;
    });
    if (eligibleDatasets.length) {
      const tourism = eligibleDatasets.find(d => d.id === 'rzs-220205IND02');
      if (tourism && tourism.latest?.length) {
        const tRow = tourism.latest[Math.floor(time / 3600000) % tourism.latest.length];
        selected.push({kind:'historical_context',dataset_id:tourism.id,sid:tourism.sid,source:tourism.title,
          edition:tourism.edition,attribution:tourism.attribution,url:tourism.url,...tRow,
          limitation:'A dated statistic at the stated geography, not a live reading or a causal explanation.'});
      }
      const econ = eligibleDatasets.filter(d => d.id !== 'rzs-220205IND02');
      if (econ.length) {
        const eDataset = econ[Math.floor(time / 3600000) % econ.length];
        const eRow = (eDataset.latest || []).find(r=>['79014','RS110'].includes(r.territory_id)) || (eDataset.latest || [])[0];
        if (eRow) selected.push({kind:'historical_context',dataset_id:eDataset.id,sid:eDataset.sid,source:eDataset.title,
          edition:eDataset.edition,attribution:eDataset.attribution,url:eDataset.url,...eRow,
          limitation:'A dated statistic at the stated geography, not a live reading or a causal explanation.'});
      }
    }
  }
  if (!selected.length) throw Error('no_usable_facts');

  const hourUTC = new Date(time).getUTCHours();
  if (hourUTC >= 22 || hourUTC <= 5) {
    selected.push({
      kind: 'temporal_context', sid: 'TIME', source: 'System', metric: 'time_of_day',
      period: 'noć/rano jutro', value: hourUTC, unit: 'h UTC',
      note: 'Noćni i ranojutarnji časovi (UTC). Ovo je samo doba dana, ne podatak o saobraćaju ili parkiranju.'
    });
  }

  let seed = Math.floor(time / 1800000);
  for (let i = selected.length - 1; i > 0; i--) {
    const x = Math.sin(seed++) * 10000;
    const r = x - Math.floor(x);
    const j = Math.floor(r * (i + 1));
    [selected[i], selected[j]] = [selected[j], selected[i]];
  }

  selected.forEach((f,i)=>{f.id='F'+(i+1);f.domain=relationRules.domain(f);});

  const recentTitles = [];
  try {
    const ed = path.join(root, 'runtime/ai-feed/entries');
    if (fs.existsSync(ed)) {
      const files = fs.readdirSync(ed).filter(f=>f.endsWith('.json'))
        .map(f => ({ name: f, time: fs.statSync(path.join(ed, f)).mtimeMs }))
        .sort((a,b) => b.time - a.time).slice(0, 5);
      for (const f of files) {
        const e = JSON.parse(fs.readFileSync(path.join(ed, f.name), 'utf8'));
        if (e?.content?.title) recentTitles.push(e.content.title);
      }
    }
  } catch(e) {}

  const packet={schema:'beops-ai-context/v1',as_of:snapshot.as_of,created_at:now.toISOString(),language:'sr-Latn',
    scope:'Belgrade; historical and demographic context retains its own geography and period.',facts:selected,coverage,
    selection:'Multi-domain live streams (air, meteorology, rivers, parking) with station rotation, plus demographic and statistical context. No articles or conversation memory.',
    baseline:'Same-stream comparisons only in v1. No long-term normality or health threshold is supplied.',
    recent_titles:recentTitles,
    relations:relationRules.relations(selected),
    relation_rule:'Facts may be discussed together only through a listed relation; all other facts are described separately.',
    catalog_hash:catalog ? hash(catalog) : null};
  while (Buffer.byteLength(JSON.stringify(packet))>(config.max_context_bytes||24000) && packet.facts.length>1) { packet.facts.pop(); packet.relations=relationRules.relations(packet.facts); }
  if (Buffer.byteLength(JSON.stringify(packet))>(config.max_context_bytes||24000)) throw Error('context_budget_exceeded');
  return packet;
}
// Numbers in IDs, coordinates, URLs and timestamp fragments are NOT measurements.
// This checks membership, not whether prose assigns the right value to the right noun.
function numericReasons(text, facts) {
  const reasons=[], values=facts.flatMap(f=>[f.value,f.comparison?.from_value,f.comparison?.delta]).filter(Number.isFinite);
  const times=facts.flatMap(f=>[f.time,f.comparison?.from_time]).filter(s=>stamp(s)!==null).map(s=>new Date(s).toISOString().slice(11,16));
  let rest=text.replace(/\b(\d{1,2})[:.](\d{2})\s*UTC\b/g,(whole,h,m)=>{
    if(!times.includes(h.padStart(2,'0')+':'+m))reasons.push('unsupported_time');return ' ';
  }).replace(/\b(\d{1,2})\s+(?:časova|čas|sati|sata)\s+UTC\b/g,(whole,h)=>{
    if(!times.includes(h.padStart(2,'0')+':00'))reasons.push('unsupported_time');return ' ';
  });
  // Ambiguous local times cannot borrow digits from measurement values.
  if(/\b\d{1,2}:\d{2}\b|\b\d{1,2}\.\d{2}\s*(?:čas|sat)|\b\d{1,2}\s+(?:časova|čas|sati|sata)\b/.test(rest))reasons.push('unsupported_time');
  const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  for(const f of facts){
    const tokens=[f.metric,f.unit];
    if(f.metric==='PM2.5')tokens.push('PM2,5');
    // Only the exact supplied period can be named; unrelated years remain rejected.
    if(typeof f.period==='string')tokens.push(f.period);
    for(const token of tokens.filter(s=>typeof s==='string'&&/\d/.test(s))){
      rest=rest.replace(new RegExp('(?<![\\p{L}\\d])'+escape(token)+'(?![\\p{L}\\d])','gu'),' ');
    }
  }
  const numbers=rest.match(/[+−-]?\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?/g)||[];
  for(const raw of numbers){
    const n=Number(raw.replace('−','-').replace(',','.'));
    if(!values.some(v=>Object.is(n,v)||n===v||
      (Math.sign(n)===Math.sign(v)&&n===Number(v.toFixed(2)))))reasons.push('unsupported_number');
  }
  return [...new Set(reasons)];
}
// citizen-v3: what may be connected, and what may be claimed without a baseline.
const fold=t=>String(t||'').normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D').toLowerCase();
const TERRAIN=/\b(greben\w*|padin\w*|kotlin\w*|brezulj\w*|uzvis\w*|brd(o|a|u|ima)?|obod\w*|ravnic\w*|podno|tvrdav\w*|dolin\w*|visoravn\w*|uzbrdic\w*|nizbrdic\w*|reljef\w*)\b/g;
const NORM=/\b(obicn\w*|uobicajen\w*|neobicn\w*|neuobicajen\w*|ocekuje se|ocekivan\w*|redovn\w*|tipicn\w*|normaln\w*|iznenadujuc\w*|zacudujuc\w*)\b/;
const PATTERN=/\b(obraz(ac|ca|ci|ce|cu|cima)|ritam\w*|ritm\w*|trend\w*|svakodnevn\w*|svake (noci|veceri|jutro|jutra|dana)|dnevn\w* migracij\w*|ponavlja se)\b/;
const NEGATED=/\b(ne|nije|nisu|niti|bez|ni)\s+(\S+\s+){0,4}?(obraz\w*|ritam\w*|ritm\w*|trend\w*|obicn\w*|uobicajen\w*|ocekivan\w*|normaln\w*|tipicn\w*)/g;
const SIMULTANEOUS=/\b(istovremeno|u isto vreme|u istom (trenutku|periodu|casu|satu|terminu)|u isti mah|paralelno)\b/;
const DOMAIN_WORDS={
  air:/\b(cestic\w*|azot\w*|ozon\w*|ugljen\w*|sumpor\w*|zagad\w*|pm10|pm2|benzen\w*|kvalitet\w* vazduha)\b/,
  weather:/\b(vet(ar|r)\w*|pritis\w*|vlazn\w*|kosav\w*|strujanj\w*|temperatur\w* vazduha|magl\w*)\b/,
  river:/\b(rek[aeiu]\w*|recn\w*|sav[aeiu]|dunav\w*|vodostaj\w*|vod[eu]|vodenih|usc[aeu])\b/,
  parking:/\b(parking\w*|parkiral\w*|garaz\w*|slobodn\w* mest\w*|vozil\w*|saobracaj\w*)\b/,
  statistics:/\b(zaposlen\w*|nezaposlen\w*|turist\w*|stanovni\w*)\b/,
};
const LIVE=new Set(['air','weather','river','parking']);
function reasoningReasons(value, packet){
  const reasons=[], facts=(packet.facts||[]).map(f=>({...f,domain:f.domain||relationRules.domain(f)}));
  const byId=new Map(facts.map(f=>[f.id,f])), rels=relationRules.relations(facts);
  const places=fold(facts.map(f=>[f.place,f.source,f.stream].join(' ')).join(' '));
  const paragraphs=Array.isArray(value.paragraphs)?value.paragraphs:[];
  const claimText=fold([value.title,...paragraphs.map(p=>p&&p.text),value.question].join(' '));
  for(const m of claimText.matchAll(TERRAIN)){ if(!places.includes(m[0])){reasons.push('invented_terrain');break;} }
  const stripped=claimText.replace(NEGATED,' ');
  if(NORM.test(stripped))reasons.push('unsupported_norm');
  if(PATTERN.test(stripped))reasons.push('premature_pattern');
  let previous=[];
  for(const p of paragraphs){
    if(!p||!Array.isArray(p.cites))continue;
    const cited=p.cites.map(c=>byId.get(c)).filter(Boolean);
    const live=cited.filter(f=>LIVE.has(f.domain)), context=cited.filter(f=>['statistics','population'].includes(f.domain));
    if(context.length&&live.length)reasons.push('context_mixed_with_live');
    if(new Set(live.map(f=>f.domain)).size>1&&!relationRules.connected(live,rels))reasons.push('unrelated_domains');
    if(SIMULTANEOUS.test(fold(p.text))){
      const times=[...cited,...previous].map(relationRules.when).filter(t=>t!==null);
      if(times.length>1&&Math.max(...times)-Math.min(...times)>3600000)reasons.push('false_simultaneity');
    }
    previous=cited;
  }
  const linked=new Set(rels.map(r=>[byId.get(r.facts[0]).domain,byId.get(r.facts[1]).domain].sort().join('+')));
  for(const text of [value.title,value.question]){
    const hit=Object.entries(DOMAIN_WORDS).filter(([,re])=>re.test(fold(text))).map(([d])=>d);
    if(hit.length<2)continue;
    const ok=hit.every((a,i)=>hit.slice(i+1).every(b=>a===b||linked.has([a,b].sort().join('+'))));
    if(!ok){reasons.push('unrelated_question');break;}
  }
  return [...new Set(reasons)];
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
    reasons.push(...numericReasons(p.text,p.cites.map(c=>facts.get(c))));
  }
  const prose=[value.title,...paragraphs.map(p=>p?.text),value.question,value.limitations].join(' ');
  if(/kratak naslov|zapažanje i oprezno tumačenje na srpskom|šta priloženi podaci ne mogu da objasne|frozen situation/i.test(prose))reasons.push('copied_prompt_template');
  if(/\p{Script=Cyrillic}/u.test(prose) || (prose.match(/\b(?:je|nije|ali|da|ne|se|u|na|kako|ovo|podaci|koji|kao|koje)\b/gi)||[]).length<6) reasons.push('serbian_latin_not_established');
  if(/\b(?:I (?:walk|saw|went|live)|video sam|videla sam|lično sam|dok šetam|šetao sam|šetala sam)\b/i.test(prose)) reasons.push('invented_firsthand_experience');
  if(prose.length>cap || /<[^>]*>|https?:|\b(?:system prompt|ignore previous|api[_ -]?key)\b/i.test(prose)) reasons.push('unsafe_or_large_text');
  // Uncited title/question/limitation must not introduce a numeric claim.
  if(numbers([value.title,value.question,value.limitations].join(' ')).length) reasons.push('uncited_number');
  if(!/[?？]/.test(value.question||'')) reasons.push('missing_question');
  reasons.push(...reasoningReasons(value,packet));
  return {ok:!reasons.length,reasons:[...new Set(reasons)],version:'citizen-v3',scope:'Structure, template, cited numeric membership, explicit UTC times, allowed relations between cited facts, simultaneity, invented terrain, unsupported norms and premature patterns; not proof of claim-to-fact mapping or interpretation accuracy.'};
}
module.exports={buildContext,validateOutput,numericReasons,reasoningReasons,readJSON,hash,stamp,allowedSources};
