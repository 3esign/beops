'use strict';
const fs=require('node:fs/promises'),path=require('node:path');
const {boundedJSON}=require('../src/store'),{hash}=require('../src/evidence');
const query='[out:json][timeout:25];(way[waterway=river](44.76,20.32,44.90,20.57);way[highway~"^(motorway|trunk|primary)$"](44.76,20.32,44.90,20.57););out tags geom;';
(async()=>{
  const {value,bytes}=await boundedJSON('https://overpass-api.de/api/interpreter',{method:'POST',headers:{'content-type':'application/x-www-form-urlencoded'},body:'data='+encodeURIComponent(query),signal:AbortSignal.timeout(40000),maxBytes:6*1024*1024});
  if(value.remark)throw new Error(value.remark);
  const map={type:'FeatureCollection',source:'https://overpass-api.de/api/interpreter',attribution:'OpenStreetMap contributors',license:'ODbL-1.0',retrievedAt:new Date().toISOString(),rawHash:hash(bytes),bbox:[20.32,44.76,20.57,44.90],
    features:value.elements.filter(e=>e.type==='way'&&e.geometry?.length>1).map(e=>({type:'Feature',id:e.id,properties:{name:e.tags?.name||'',waterway:e.tags?.waterway||'',highway:e.tags?.highway||''},geometry:{type:'LineString',coordinates:e.geometry.map(p=>[p.lon,p.lat])}}))};
  if(!map.features.length)throw new Error('Empty map');
  await fs.mkdir(path.join(__dirname,'../public'),{recursive:true});
  await fs.writeFile(path.join(__dirname,'../public/map.json'),JSON.stringify(map));
  console.log(JSON.stringify({features:map.features.length,bytes:bytes.length,hash:map.rawHash}));
})().catch(error=>{console.error(error);process.exitCode=1;});
