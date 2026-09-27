'use strict';
// Read-only source audit by default; output is an explicit local review artifact.
const fs=require('node:fs'),path=require('node:path'),readline=require('node:readline');
const model=require('./impulse_model');
const ROOT=path.resolve(__dirname,'..');
function read(file){return JSON.parse(fs.readFileSync(file,'utf8').replace(/^\uFEFF/,''));}
async function build(root=ROOT,asof=Date.now()){
 const config=read(path.join(root,'research/COLLECTORS.json')),names=new Map(config.sources.map(s=>[s.sid,s.name]));
 const sensor=new Set(['sepa_hvd','sensor_community','parking','rhmz_auto','metar','rhmz_gauges','danubehis','meteoalarm','rhmz_uv','rhmz_waves']);
 const rows=[],inputs=[],errors=[];
 const corrections=path.join(root,'data/live/corrections.jsonl'),correctedSources=new Set();
 // Fail closed rather than bypassing a redaction/correction overlay. The current
 // ledger corrects instruments only. Future headline overlays require the canonical
 // Python content_id projection before that source can join this local study.
 if(fs.existsSync(corrections))for(const line of fs.readFileSync(corrections,'utf8').split(/\r?\n/).filter(Boolean))correctedSources.add(JSON.parse(line).sid);
 for(const source of config.sources.filter(s=>!sensor.has(s.parser))){
  if(correctedSources.has(source.sid)){errors.push({source_id:source.sid,reason:'correction_overlay_requires_canonical_projection; source_excluded'});continue;}
  const dir=path.join(root,'data/live/rows',source.sid);if(!fs.existsSync(dir))continue;
  for(const name of fs.readdirSync(dir).filter(n=>/^\d{4}-\d{2}\.jsonl$/.test(n)).sort()){
   const file=path.join(dir,name),before=fs.statSync(file),input=path.relative(root,file).replaceAll('\\','/');
   inputs.push({path:input,bytes_at_open:before.size});if(!before.size)continue;
   let line=0;const stream=fs.createReadStream(file,{start:0,end:before.size-1,encoding:'utf8'});
   for await(const text of readline.createInterface({input:stream,crlfDelay:Infinity})){
    line++;if(!text.trim())continue;
    try{const r=JSON.parse(text);if(r.parameter==='headline')rows.push({...r,source:names.get(r.sid)});}
    catch{errors.push({input,line,reason:'invalid_json_or_concurrent_partial_line'});}
   }
  }
 }
 const h=model.collectHeadlines(rows,asof),cachePath=path.join(root,'data/live/derived/events/repertoire.json');
 const cache=fs.existsSync(cachePath)?read(cachePath):{},calendar=model.calendarItems(cache.events,asof),ai=[];
 const dir=path.join(root,'runtime/ai-feed/entries');if(fs.existsSync(dir))for(const name of fs.readdirSync(dir).filter(n=>/^[a-zA-Z0-9_-]+\.json$/.test(n)).sort()){let entry,packet=null;try{entry=read(path.join(dir,name));if(/^[a-f0-9]{64}$/.test(entry.context_hash||'')){const file=path.join(root,'runtime/ai-feed/contexts',entry.context_hash+'.json');if(fs.existsSync(file))packet=read(file);}const item=model.aiItem(entry,packet,asof);if(item)ai.push(item);}catch{errors.push({input:'runtime/ai-feed/entries/'+name,reason:'unreadable_entry_or_context'});}}
 const result=model.buildSnapshot([...h.items,...calendar,...ai],asof,{...h.audit,input_files:inputs,input_errors:errors,snapshot_mode:'Per-file bounded read, rows after as_of excluded. No global lock; partial lines are disclosed and excluded.',calendar_cache_state:cache.state||'missing',calendar_received_at:cache.received_at||null,geographic_name_dictionary:'headline_geo.js: sourced location estimates and policy radii; impulse_model.js PLACES/v1 ('+model.PLACE_COUNT+' labels) retained as unverified name candidates'});
 result.next_location_work=[{priority:1,kind:'verified_venue_register',target:'Kolarac and additional official repertoires',requirement:'Bind official venue address to independently documented coordinates; retain evidence URL, date, geometry and precision. Current Kolarac schedule has no coordinates.'},{priority:2,kind:'official_notice_geometry',target:'Transport works, street closures and utility notices',requirement:'Read each linked notice for explicit date interval and street segment; title name matches alone cannot identify an event location.'},{priority:3,kind:'reviewed_area_geometry',target:'Neighborhood and municipality mentions',requirement:'Use licensed/authorized boundaries with provenance, show areas rather than guessed point centroids. Resolve ambiguous city names first.'},{priority:4,kind:'ai_context_anchors',target:'Model interpretations',requirement:'Only exact coordinates attached to cited facts in the hash-verified frozen context. Never count an interpretation as a physical event.'}];
 return result;
}
async function main(){const args=process.argv.slice(2);let output=null,at=Date.now();for(let i=0;i<args.length;i++){if(args[i]==='--output')output=args[++i];else if(args[i]==='--as-of'){at=model.stamp(args[++i]);if(at===null)throw Error('--as-of requires an explicit timezone');}else throw Error('Unknown argument '+args[i]);}if(!output)throw Error('Provide --output inside C:\\Svemir for the review artifact');const target=path.resolve(output),durable=path.resolve('C:/Svemir');if(!target.toLowerCase().startsWith(durable.toLowerCase()+path.sep))throw Error('Output must remain inside C:\\Svemir');if(fs.existsSync(target))throw Error('Output exists; choose a new artifact path');const result=await build(ROOT,at);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({output:target,as_of:result.as_of,coverage:result.coverage,windows:Object.fromEntries(Object.entries(result.windows).map(([k,v])=>[k,v.counts])),upcoming:result.upcoming.counts,audit:{...result.audit,input_files:result.audit.input_files.length}},null,2));}
if(require.main===module)main().catch(e=>{console.error(e.message);process.exitCode=1;});
module.exports={build};
