'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const studies=path.join(__dirname,'05-design/studies');
const data=fs.readFileSync(path.join(studies,'podaci.html'),'utf8');
const now=fs.readFileSync(path.join(studies,'sada.html'),'utf8');
const oneLine=(html,name)=>{const line=html.split(/\r?\n/).find(x=>x.startsWith('function '+name+'('));assert.ok(line,name);return line;};
const legend={innerHTML:''},fills=[];let arc=null;
const g={setTransform(){},clearRect(){},beginPath(){arc=null;},arc(x,y,r){arc={x,y,r};},
 fill(){if(arc)fills.push({...arc,color:this.fillStyle});},stroke(){},moveTo(){},lineTo(){},
 measureText(){return {width:20};},fillText(){}};
const canvas={clientWidth:300,clientHeight:200,getContext(){return g;}};
const rows=[10,175,10000].map((v,i)=>({parameter:'PM10',lat:i+1,lon:i+1,unit:'ug.m-3',points:[{v}]}));
rows.push({parameter:'PM10',lat:4,lon:4,points:[{v:null}]});
const context={document:{getElementById(id){return id==='map'?canvas:legend;}},window:{devicePixelRatio:1},
 css:name=>name,sepa:()=>({datastreams:rows}),PAR:'PM10',VIEW:{k:1,tx:0,ty:0},BASEMAP:null,
 proj:(lat,lon)=>[lat*30,lon*30],projBase:(lat,lon)=>[lat*30,lon*30],metresPerPx:()=>100,
 S:sr=>sr,esc:String};
vm.createContext(context);
const map=data.slice(data.indexOf('function drawMap(){'),data.indexOf('function renderSepa(){'));
assert.ok(map.length>100,'real map function');
vm.runInContext(oneLine(data,'latestPoint')+'\n'+oneLine(data,'latest')+'\n'+oneLine(data,'airMarkerStyle')+'\n'+map,context);
context.drawMap();
const markers=fills.filter(x=>x.r===5);
assert.equal(markers.length,3,'all present numeric values remain visible');
assert.ok(markers.every(x=>x.color==='--ink60'),'all concentrations use neutral ink');
assert.match(legend.innerHTML,/Satna vrednost nije upoređena/);
assert.doesNotMatch(legend.innerHTML,/iznad 45|ispod 45/);
const latestNull={last_by_measurement:{v:null,t:'2026-09-09T10:50:00Z'},last_received:{v:10,t:'2026-09-09T10:10:00Z'},points:[{v:10}]};
assert.equal(context.latest(latestNull),null,'later reception cannot hide latest measured null');
assert.equal(context.latestPoint(latestNull).t,'2026-09-09T10:50:00Z','missing value keeps its known clock');
vm.runInContext(oneLine(now,'lastPoint'),context);
assert.equal(context.lastPoint(latestNull).v,null,'Sada retains the same latest null');
assert.equal(context.lastPoint({last_by_measurement:null,last_received:{v:0,tu:true}}).v,0,'untimed zero reception is retained');
console.log('Actual map drawing and both latest selectors passed.');
