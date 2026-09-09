'use strict';
const { check, digest } = require('./engine_contracts');
const STOP = new Set('the and for with from this that not are was were has have into only than then its our but can will who what how kao koji koja koje ovo ona ono nije jesu biti kroz samo bez ili smo sve svaki treba data model models beops svemir research'.split(' '));
function tokens(text) {
  // Spans refer to the original JavaScript UTF-16 string; no transliteration or alias merging.
  return [...text.matchAll(/[\p{L}\p{N}][\p{L}\p{N}_-]*/gu)].map(m => ({ original: m[0], normalized: m[0].normalize('NFC').toLowerCase(), start: m.index, end: m.index + m[0].length }))
    .filter(t => t.normalized.length > 2 && !STOP.has(t.normalized) && !/^\d+$/.test(t.normalized));
}
function keywords(documents, limit = 100) {
  check(documents.length <= 200, 'corpus count budget');
  const vocab = new Map();
  for (const doc of documents) {
    check(doc.text.length <= 2 * 1024 * 1024, 'document budget');
    const ts = tokens(doc.text), local = new Map();
    for (let i=0; i<ts.length; i++) for (let n=1; n<=3 && i+n<=ts.length; n++) {
      const slice = ts.slice(i,i+n);
      // Never join tokens across punctuation, a dropped stopword, or a paragraph.
      if (slice.some((t,j) => j && !/^[ \t]+$/.test(doc.text.slice(slice[j-1].end,t.start)))) continue;
      const term = slice.map(t => t.normalized).join(' ');
      const row = local.get(term) || { count:0, start:slice[0].start, end:slice.at(-1).end };
      row.count++; local.set(term,row);
    }
    for (const [term,r] of local) {
      const item = vocab.get(term) || { term_id: digest(term), normalized:term, status:'candidate', aliases:[], type:null, evidence:[], score:0 };
      item.evidence.push({ ref:doc.ref, sha256:doc.sha256, span_utf16:[r.start,r.end], original:doc.text.slice(r.start,r.end), count:r.count });
      vocab.set(term,item);
    }
  }
  for (const item of vocab.values()) {
    item.document_frequency = item.evidence.length;
    item.score = item.evidence.reduce((s,x)=>s+1+Math.log(x.count),0) * (Math.log((documents.length+1)/(item.evidence.length+1))+1);
  }
  return [...vocab.values()].sort((a,b)=>b.score-a.score||a.normalized.localeCompare(b.normalized)).slice(0,limit);
}
function bm25(documents, query, limit = 10) {
  if (!documents.length) return [];
  const docs = documents.map(d=>({ ...d, terms:tokens(d.text).map(t=>t.normalized) }));
  const avg = docs.reduce((s,d)=>s+d.terms.length,0)/docs.length || 1;
  const terms = [...new Set(tokens(query).map(t=>t.normalized))];
  const df = new Map(terms.map(t=>[t,docs.filter(d=>d.terms.includes(t)).length]));
  return docs.map(d=>({ id:d.id, score:terms.reduce((sum,t)=> {
    const tf=d.terms.filter(x=>x===t).length;
    const idf=Math.log(1+(docs.length-df.get(t)+0.5)/(df.get(t)+0.5));
    return sum+idf*tf*2.2/(tf+1.2*(0.25+0.75*d.terms.length/avg));
  },0) })).filter(d=>d.score>0).sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).slice(0,limit);
}
function retrievalMetrics(ranked, relevance, k=5) {
  check(Number.isInteger(k)&&k>0,'invalid k');
  check(new Set(ranked).size === ranked.length, 'duplicate retrieval IDs');
  const relevant=Object.keys(relevance).filter(id=>relevance[id]>0);
  const dcg=values=>values.reduce((s,v,i)=>s+(2**v-1)/Math.log2(i+2),0);
  const ideal=dcg(Object.values(relevance).sort((a,b)=>b-a).slice(0,k));
  return { recall:relevant.length ? ranked.slice(0,k).filter(id=>relevance[id]>0).length/relevant.length : null,
    ndcg:ideal ? dcg(ranked.slice(0,k).map(id=>relevance[id]||0))/ideal : null };
}
function forecastMetrics(actual, predicted, training, season=1) {
  check(actual.length===predicted.length && actual.length>0,'unaligned forecast');
  check([...actual,...predicted,...training].every(Number.isFinite),'missing values cannot be silently imputed');
  check(Number.isInteger(season)&&season>0,'invalid season');
  const mae=actual.reduce((s,v,i)=>s+Math.abs(v-predicted[i]),0)/actual.length;
  const differences=training.slice(season).map((v,i)=>Math.abs(v-training[i]));
  const denominator=differences.length ? differences.reduce((a,b)=>a+b,0)/differences.length : null;
  return { n:actual.length, mae, mase:denominator ? mae/denominator : null, mase_denominator:denominator };
}
function pinball(actual, predicted, quantile) {
  check(actual.length>0&&actual.length===predicted.length&&quantile>0&&quantile<1,'invalid quantile input');
  check([...actual,...predicted].every(Number.isFinite),'nonfinite quantile input');
  return actual.reduce((s,y,i)=>{const e=y-predicted[i];return s+Math.max(quantile*e,(quantile-1)*e);},0)/actual.length;
}
function validateSplits(rows) {
  const groups=new Map(), ids=new Set();
  for (const row of rows) {
    check(row.id && !ids.has(row.id), 'duplicate benchmark id'); ids.add(row.id);
    check(['train','validation','test'].includes(row.split),'invalid split');
    check(row.event_group && row.origin_group,'event and source groups required');
    for (const key of ['event_group','origin_group']) {
      const group=key+':'+row[key];
      check(!groups.has(group)||groups.get(group)===row.split, 'split leakage: '+group); groups.set(group,row.split);
    }
  }
  return { rows:rows.length, groups:groups.size };
}
function priceKey(p) {
  for (const k of ['retailer','product_id','package','unit','currency','scope']) check(typeof p[k]==='string' && p[k].length>0,'missing price identity '+k);
  return digest([p.retailer,p.product_id,p.package,p.unit,p.currency,p.scope]);
}
function comparePrices(before,after) {
  function index(rows) {
    const m=new Map();
    for(const p of rows) { const k=priceKey(p);check(!m.has(k),'ambiguous duplicate product');check(Number.isFinite(p.price)&&p.price>=0,'invalid price');check(/^\d{4}-\d\d-\d\d$/.test(p.valid_date),'price date required');m.set(k,p); }
    return m;
  }
  const a=index(before),b=index(after),changes=[];
  for(const [k,p] of a) if(b.has(k)) {const q=b.get(k);check(q.valid_date>p.valid_date,'price versions must advance');changes.push({key:k,product_id:p.product_id,before:p.price,after:q.price,delta:q.price-p.price});}
  return {changes,unmatched_before:[...a.keys()].filter(k=>!b.has(k)).length,unmatched_after:[...b.keys()].filter(k=>!a.has(k)).length};
}
function parkingReport(events) {
  const rows=events.filter(e=>e.measurement.property==='free_spaces'), locations=new Map();
  for(const e of rows) { if(!locations.has(e.entity_id))locations.set(e.entity_id,[]);locations.get(e.entity_id).push(e); }
  return [...locations].map(([entity_id,series])=>{
    series.sort((a,b)=>Date.parse(a.ingested_at)-Date.parse(b.ingested_at));
    const pairs=[]; let excludedGaps=0;
    for(let i=1;i<series.length;i++) {
      const previous=series[i-1],current=series[i],gap=Date.parse(current.ingested_at)-Date.parse(previous.ingested_at);
      if(previous.measurement.value===null||current.measurement.value===null||gap<55*60000||gap>65*60000){excludedGaps++;continue;}
      pairs.push({input:previous.event_id,target:current.event_id,prediction:previous.measurement.value,actual:current.measurement.value});
    }
    return {entity_id, label:series[0].label, received_samples:series.length, known_source_times:series.filter(e=>e.observed_at!==null).length,
      zeros_preserved:series.filter(e=>e.measurement.value===0).length, missing:series.filter(e=>e.measurement.value===null).length,
      pairs, excluded_gaps:excludedGaps, reception_sequence_mae:pairs.length ? pairs.reduce((s,p)=>s+Math.abs(p.actual-p.prediction),0)/pairs.length : null,
      interpretation:'Exploratory persistence of displayed counts at approximately hourly retrievals; not instrument-time forecasting, traffic or causality.'};
  });
}
function pulse(events, zone=null) {
  const selected=events.filter(e=>!zone||e.spatial.zones.includes(zone));
  const cells=new Map();
  for(const e of selected) {const key=[e.domain,e.kind,e.measurement.property,e.measurement.unit].join('|');if(!cells.has(key))cells.set(key,{domain:e.domain,kind:e.kind,property:e.measurement.property,unit:e.measurement.unit,event_ids:new Set(),origins:new Set(),source_times:0});const c=cells.get(key);if(c.event_ids.has(e.event_id))continue;c.event_ids.add(e.event_id);c.origins.add(e.shared_origin_group);c.source_times+=e.observed_at!==null?1:0;}
  return {zone,unresolved_events:events.filter(e=>!e.spatial.zones.length).length,cells:[...cells.values()].map(c=>({...c,event_ids:[...c.event_ids],origin_groups:[...c.origins],origins:undefined})),interpretation:'Separate evidence channels; no cross-unit city score, no claim that domains corroborate one another.'};
}
module.exports={tokens,keywords,bm25,retrievalMetrics,forecastMetrics,pinball,validateSplits,priceKey,comparePrices,parkingReport,pulse};
