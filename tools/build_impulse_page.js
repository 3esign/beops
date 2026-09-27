'use strict';
// Public projection of the existing geographic study. All reads use one frozen
// release root and its snapshot clock; raw AI packets/prompts never cross here.
const fs=require('node:fs'),path=require('node:path');
const {build}=require('./build_impulses');
const {buildSummary}=require('./resource_summary');
const model=require('./impulse_model');
const {hash,validLocation}=require('./ai_feed_context');
const {packItems}=require('../public/impulse-codec');
const ROOT=path.resolve(__dirname,'..');
const pick=(o,keys)=>Object.fromEntries(keys.filter(k=>o?.[k]!==undefined).map(k=>[k,o[k]]));
const read=file=>JSON.parse(fs.readFileSync(file,'utf8').replace(/^\uFEFF/,''));
const fmt=new Intl.NumberFormat('sr-Latn',{maximumFractionDigits:1});
const n=v=>typeof v==='number'?fmt.format(v):'nepoznato';
const date=v=>new Date(v).toLocaleString('sr-Latn',{timeZone:'Europe/Belgrade',day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
const digest=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v)?v:null;
function evidence(value){
 const out=pick(value,['source','retrieved_at','source_name','source_kind','licence','limitation','context_verified','validation']);
 for(const key of ['source_url','repertoire_url'])if(value?.[key])out[key]=model.safeURL(value[key]);
 for(const key of ['raw_sha256','context_hash'])if(value?.[key])out[key]=digest(value[key]);
 // Permission capture is an evidence identifier, never a local file path.
 if(typeof value?.permission_capture==='string'&&/^[A-Za-z0-9_-]{1,100}$/.test(value.permission_capture))out.permission_capture=value.permission_capture;
 return out;
}
function estimate(value){if(!value)return null;return {...pick(value,['place_id','name','lon','lat','radius_m','precision','confidence','method','matched_text','location_cue','radius_basis','verified']),evidence:evidence(value.evidence)};}
function publicItem(item){
 const out=pick(item,['id','kind','title','source_id','source','clock','event_time','first_received','last_received','latest_revision_published','revisions','state','schedule_age_hours','schedule_fresh','geo_status','limitation']);
 out.source_url=model.safeURL(item.source_url);out.evidence=evidence(item.evidence);
 out.places=(item.places||[]).map(p=>pick(p,['name','kind','method','confidence','limitation','coordinates']));
 out.point=item.point?{...pick(item.point,['lon','lat','place','source_id','fact_id','context_hash','method']),source_url:model.safeURL(item.point.source_url)}:null;
 out.location_estimate=estimate(item.location_estimate);
 if(item.geo)out.geo={...pick(item.geo,['scope','status','reason','method','gazetteer_version','limitation']),candidates:(item.geo.candidates||[]).map(c=>({...pick(c,['place_id','name','scope','precision','matched_text','reason','location_cue','eligible','nearby','coordinates','radius_m','confidence','method']),evidence:evidence(c.evidence)}))};
 if(item.kind==='ai_observation'){
  out.cited_source_urls=(item.cited_source_urls||[]).map(model.safeURL).filter(Boolean);
  // A globally valid instrument coordinate is not an administrative geography.
  out.geo={scope:'unknown',status:'instrument_coordinate_only',reason:'cited_coordinate_does_not_establish_administrative_scope'};
 }
 return out;
}
function publicFact(f){
 const out=pick(f,['id','kind','sid','source','place','stream','metric','value','unit','time','received_at','reported_time','result_time','clock','quality','age_minutes','reception_age_minutes','clock_explanation','domain','dataset_id','edition','attribution','territory_id','geography','period','limitation','note']);
 out.url=model.safeURL(f.url);
 if(validLocation(f.location))out.location=f.location;
 if(f.map_anchor)out.map_anchor=pick(f.map_anchor,['layer','id']);
 if(f.clocks)out.clocks=pick(f.clocks,['measurement_time','result_time','reception_time','placement_time','basis']);
 if(f.comparison)out.comparison=pick(f.comparison,['kind','from_value','from_time','delta','limitation']);
 return out;
}
function aiEvidence(root,item,reviews){
 const id=item.id.replace(/^ai-/,'');if(!/^[a-f0-9]{32}$/.test(id))throw Error('invalid_public_ai_id');
 const entry=read(path.join(root,'runtime/ai-feed/entries',id+'.json'));
 const contextHash=digest(entry.context_hash),contextPath=contextHash&&path.join(root,'runtime/ai-feed/contexts',contextHash+'.json');
 const packet=contextPath&&fs.existsSync(contextPath)?read(contextPath):null;
 const verified=Boolean(packet&&hash(packet)===contextHash),cited=new Set((entry.content.paragraphs||[]).flatMap(p=>p.cites||[]));
 const flags=(reviews.records||[]).filter(r=>r.entry_id===id).map(r=>{
  if(r.entry_sha256!==hash(entry))throw Error('ai_review_entry_hash_mismatch');
  return pick(r,['status','reviewed_at','reason_sr','reason_en','reference']);
 });
 return {schema:'beops-impulse-ai-evidence/v1',id,at:entry.at,provider:entry.provider,model:entry.model,
  content:{...pick(entry.content,['title','question','limitations']),paragraphs:(entry.content.paragraphs||[]).map(p=>pick(p,['text','cites']))},
  provenance:{entry_sha256:hash(entry),context_hash:contextHash,context_verified:verified,context_as_of:verified?packet.as_of||null:null},
  cited_facts:verified?(packet.facts||[]).filter(f=>cited.has(f.id)).map(publicFact):[],
  missing_citations:[...cited].filter(id=>!verified||!(packet.facts||[]).some(f=>f.id===id)),reviews:flags,
  note:'Public projection of accepted model prose and cited facts only. Context hash refers to the full retained packet, not this projection. Automatic acceptance is not factual verification; an anchor is an instrument location, not a new event.'};
}
function resourcesPublic(summary){
 const out=JSON.parse(JSON.stringify(summary));delete out.coverage.invalid_receipt_files;
 return out;
}
function encode(value){
 const text=JSON.stringify(value);
 // Fail the release instead of silently disclosing local filesystem material.
 if(/(?:^|["\s])(?:[A-Za-z]:[\\/]|file:\/\/|\/(?:Users|home)\/)/.test(text))throw Error('local_path_in_public_impulse_export');
 return text+'\n';
}
function durable(target){
 const absolute=path.resolve(target),allowed=path.resolve('C:/Svemir');
 if(!absolute.toLowerCase().startsWith(allowed.toLowerCase()+path.sep))throw Error('output_outside_durable_root');
 return absolute;
}
async function buildPage(root=ROOT,options={}){
 root=path.resolve(root);
 const snapshot=read(path.join(root,'public/live-snapshot.json'));
 const at=options.asOf||snapshot.as_of,time=model.stamp(at);
 if(time===null||time!==model.stamp(snapshot.as_of))throw Error('impulse_snapshot_time_mismatch');
 const asOf=snapshot.as_of,inputGeneration=snapshot.input_generation||null;
 const local=await build(root,time,{canonicalHeadlines:true});
 const config=read(path.join(root,'research/AI_FEED.json'));
 const retained=local.items.filter(i=>(i.kind!=='ai_observation'||config.public_enabled===true)&&
  (model.inWindow(i,time-30*model.DAY,time)||i.kind==='scheduled_event'&&model.stamp(i.clock.at)>=time));
 const items=retained.map(publicItem);
 const summarized=model.buildSnapshot(items,time);
 const resources=resourcesPublic(buildSummary(root,new Date(time)));
 resources.as_of=asOf;
 const reviewsFile=path.join(root,'research/AI_FEED_REVIEWS.json'),reviews=fs.existsSync(reviewsFile)?read(reviewsFile):{records:[]};
 const proofs=Object.fromEntries(items.filter(i=>i.kind==='ai_observation').map(i=>[i.id.replace(/^ai-/,''),aiEvidence(root,i,reviews)]));
 const impulses={schema:'beops-public-impulses/v2',as_of:asOf,input_generation:inputGeneration,
  timezone:model.TZ,scope:local.scope,semantics:local.semantics,coverage:summarized.coverage,
  audit:{headline_projection:'Canonical public archive with corrections, first and last retained receptions. Collection-row totals are not inferred.',
   input_errors:local.audit.input_errors.map(e=>({reason:e.reason,source_id:e.source_id||null})),calendar_cache_state:local.audit.calendar_cache_state,calendar_received_at:local.audit.calendar_received_at,
   retained_items_outside_export:local.items.length-retained.length},
  encoding:'column-dictionaries/v1',encoding_note:'Each record has one cell per column. A column with values uses integer dictionary indexes (-1 means absent); other columns contain raw JSON. impulse-codec.js reconstructs the full source records without loss.',...packItems(items)};
 const view={};
 for(const key of ['day','week','month']){
  const w=summarized.windows[key];
  view[key]={start:w.start,end:w.end,period:`Poslednjih ${w.duration_hours} sati · ${date(w.start)} – ${date(w.end)} · Europe/Belgrade`,
   resource:resources.windows[key],resource_note:!resources.observation_start?'Nema sačuvanih ciklusa merenja.':Date.parse(resources.observation_start)>Date.parse(w.start)?'Obuhvat je delimičan; merenje je počelo tokom ovog perioda.':'Obuhvat je delimičan; uključene su samo instrumentisane putanje.',counts:w.counts};
 }
 const history=resources.historical_provider_usage;
 const data={schema:'beops-impulse-view/v1',as_of:asOf,input_generation:inputGeneration,generated_at:asOf,view,
  basemap:read(path.join(root,'public/basemap-belgrade.json')),
  meter_note:resources.observation_start?'Merenje od '+date(resources.observation_start)+'.':'Prvi ciklus još nije zabeležen.',
  scope_note:'Beleže se sakupljač, kalendar, AI, vesti, mind i zakazani nadzor/guard/legal. Nisu obuhvaćeni objava, izgradnja i testovi, deca procesa, lokalni model serveri/GPU, tokeni news/mind organa, udaljena infrastruktura i osnovna potrošnja računara.',
  history_note:`Svi sačuvani AI pokušaji: ${n(history.all.attempts)}. Sa prijavljenim tokenima: ${n(history.all.reported_calls)}; bez: ${n(history.all.unreported_calls)}. Ulaz: ${n(history.all.input_tokens)}; izlaz: ${n(history.all.output_tokens)}. Obuhvata i neuspele/odbijene pokušaje; preklapa se sa novim brojačem i ne dodaje se na njegov zbir.`};
 const generation=hash({as_of:asOf,input_generation:inputGeneration,data,impulses,resources,proofs});
 const envelope=value=>({schema:value.schema,as_of:asOf,input_generation:inputGeneration,generation,...value});
 const manifest={as_of:asOf,input_generation:inputGeneration,generation,view:'impulse-data/view-data.json',impulses:'impulse-data/impulses.json',resources:'impulse-data/resources.json'};
 const json=encode(manifest).trim().replaceAll('<','\\u003c').replaceAll('>','\\u003e').replaceAll('\u2028','\\u2028').replaceAll('\u2029','\\u2029');
 const template=fs.readFileSync(path.join(root,'public/impulsi.html'),'utf8');
 if(!template.includes('__IMPULSE_MANIFEST__'))throw Error('impulse_template_marker_missing');
 const html=template.replace('__IMPULSE_MANIFEST__',json),output=durable(options.outputDir||path.join(root,'docs'));
 const artifacts={'impulsi.html':html,'impulsi.js':fs.readFileSync(path.join(root,'public/impulsi.js'),'utf8'),
  'impulse-codec.js':fs.readFileSync(path.join(root,'public/impulse-codec.js'),'utf8'),
  'impulse-data/view-data.json':encode(envelope(data)),'impulse-data/impulses.json':encode(envelope(impulses)),
  'impulse-data/resources.json':encode(envelope(resources))};
 for(const [id,proof]of Object.entries(proofs))artifacts['impulse-data/ai-evidence/'+id+'.json']=encode(envelope(proof));
 for(const [name,text]of Object.entries(artifacts)){
  const file=path.join(output,name);fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,text,'utf8');
 }
 return {as_of:asOf,input_generation:inputGeneration,generation,files:Object.keys(artifacts),coverage:impulses.coverage};
}
async function main(){
 const args=process.argv.slice(2),options={};let root=ROOT;
 for(let i=0;i<args.length;i++){
  if(args[i]==='--root')root=args[++i];else if(args[i]==='--as-of')options.asOf=args[++i];else if(args[i]==='--output-dir')options.outputDir=args[++i];else throw Error('Unknown argument '+args[i]);
 }
 console.log(JSON.stringify(await buildPage(root,options)));
}
module.exports={buildPage,publicItem,publicFact,aiEvidence,encode};
if(require.main===module)main().catch(error=>{console.error(error.message);process.exitCode=1;});
