'use strict';
// Independent consumer of Python's real wire output, through the actual page loader.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const code=fs.readFileSync(path.join(__dirname,'05-design/studies/beops-view.js'),'utf8');
async function load(snapshot){
  const window={};window.parent=window;
  const fetch=async()=>({ok:true,json:async()=>({schema:'beops-city-view/v1',generation:'a'.repeat(64),snapshot})});
  vm.runInNewContext(code,{window,fetch,Date,Map,Set,Error,Object});
  return (await window.beopsView.overview()).snapshot;
}
(async()=>{
  const restored=await load(input.packed);
  assert.deepEqual(JSON.parse(JSON.stringify(restored)),input.expected);
  const clocks=require('./05-design/studies/observation-clocks.js');
  for(let i=0;i<restored.sources.length;i++)for(let j=0;j<restored.sources[i].datastreams.length;j++){
    const a=restored.sources[i],b=input.expected.sources[i];
    for(let k=0;k<a.datastreams[j].points.length;k++)
      assert.deepEqual(clocks.disclose(a.datastreams[j].points[k],a.clock_rules),clocks.disclose(b.datastreams[j].points[k],b.clock_rules));
  }
  const bad=structuredClone(input.packed),source=bad.sources.find(s=>s.point_defaults);
  if(source){
    source.point_defaults.v=999;await assert.rejects(load(bad),/invalid_point_defaults/);delete source.point_defaults.v;
    const key=Object.keys(source.point_defaults)[0];source.datastreams.find(d=>d.points.length).points[0][key]=null;
    await assert.rejects(load(bad),/conflicting_point_defaults/);
  }
  console.log('All restored point properties and named clocks match; invalid and conflicting defaults rejected.');
})().catch(error=>{console.error(error);process.exitCode=1;});
