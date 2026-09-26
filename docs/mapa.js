/* BEOPS spatial view. Pure transforms are exercised by the offline contract. */
(function () {
'use strict';
const BB={lo0:20.17,lo1:20.80,la0:44.55,la1:44.98};
const STATES=['observed','untimed','estimated','forecast','unavailable'];
function coordinate(lat,lon){return typeof lat==='number'&&typeof lon==='number'&&Number.isFinite(lat)&&Number.isFinite(lon)&&lat>=-90&&lat<=90&&lon>=-180&&lon<=180;}
function inWindow(lat,lon){return coordinate(lat,lon)&&lat>=BB.la0&&lat<=BB.la1&&lon>=BB.lo0&&lon<=BB.lo1;}
function localRoute(route){return typeof route==='string'&&/^[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_-]+)*\.json$/.test(route);}
function validRegistry(config){
    if(!config||config.schema!=='beops-map-layers/v1'||!Array.isArray(config.layers))throw Error('Registar slojeva nije važeći.');
    const ids=new Set();
    for(const l of config.layers){if(!l.id||ids.has(l.id)||!localRoute(l.route)||!Array.isArray(l.dossier_fields)||!l.dossier_fields.every(x=>typeof x==='string')||!Array.isArray(l.states_it_may_carry)||!l.states_it_may_carry.every(x=>STATES.includes(x)))throw Error('Nevažeći sloj u registru.');ids.add(l.id);}
    return config.layers;
}
function readingState(row){
    if(!row||row.v===null||row.v===undefined)return 'unavailable';
    if(STATES.includes(row.state))return row.state;
    if(row.tu||!row.t)return 'untimed';
    if(row.tc||row.clock_rule)return 'estimated';
    if(/forecast/i.test(String(row.q||'')))return 'forecast';
    return 'observed';
}
function instruments(snap){
    const groups=new Map(), statuses=new Map(((snap.status||{}).sources||[]).map(s=>[s.sid,s]));
    for(const src of snap.sources||[])for(const ds of src.datastreams||[]){
        if(!inWindow(ds.lat,ds.lon))continue;
        const id=src.sid+':'+(ds.station||ds.datastream)+':'+ds.lat+':'+ds.lon;
        let p=groups.get(id);
        if(!p){const st=statuses.get(src.sid)||{};p={id,layer:'instruments',lat:ds.lat,lon:ds.lon,data:{sid:src.sid,name:src.name,station:ds.station||ds.datastream,lat:ds.lat,lon:ds.lon,as_of:snap.as_of,last_received:st.last_captured_at||null,expected_slots:st.expected_slots,captured:st.captured,quorum:st.quorum,measurements:[]}};groups.set(id,p);}
        const row=ds.last_received||(ds.points||[]).slice(-1)[0], state=readingState(row);
        p.data.measurements.push({parameter:ds.parameter||ds.datastream,unit:ds.unit||'',value:row&&row.v!==undefined?row.v:null,state,measured:row?(row.tc||row.t||null):null,received:row?(row.rx||null):null,clock_note:row?(row.clock_note||null):null});
        if(row&&row.rx&&(!p.data.last_received||row.rx>p.data.last_received))p.data.last_received=row.rx;
    }
    for(const p of groups.values()){const states=[...new Set(p.data.measurements.map(m=>m.state))];p.data.state=states.join(', ');p.state=states.every(s=>s==='unavailable')?'unavailable':states.includes('untimed')?'untimed':states.includes('estimated')?'estimated':states.includes('forecast')?'forecast':'observed';}
    return [...groups.values()];
}
function populationPoints(pop){return(pop.hexes||[]).filter(h=>Array.isArray(h)&&inWindow(h[1],h[0])&&typeof h[2]==='number'&&Number.isFinite(h[2])&&h[2]>=0).map(h=>({id:h[3],layer:'kontur-population',lat:h[1],lon:h[0],state:'estimated',data:{id:h[3],population:h[2],state:'estimated',release:(pop.source||{}).release,source:pop.source,note:pop.note}}));}
function anchoredAI(entries,points){
    const result=[];
    for(const entry of entries||[]){
        if(!entry.content||!entry.content.geo||typeof entry.model!=='string'||!entry.model.trim())continue;
        const geo=entry.content.geo;let lat=geo.lat,lon=geo.lon;
        if(geo.layer&&geo.id){const anchor=points.find(p=>p.layer===geo.layer&&p.id===geo.id);if(!anchor)continue;lat=anchor.lat;lon=anchor.lon;}
        if(!inWindow(lat,lon))continue;
        result.push({id:entry.id,layer:'ai-feed',lat,lon,state:'estimated',is_ai:true,data:{model:entry.model,title:entry.content.title,question:entry.content.question,limitations:entry.content.limitations,at:entry.at,state:'estimated',geo,provenance:'Model-derived; automatska provera ne potvrđuje istinitost.'}});
    }return result;
}
function geometryParts(f){const g=f&&f.geometry;if(!g||!Array.isArray(g.coordinates))return[];if(g.type==='LineString')return[{coords:g.coordinates,closed:false}];if(g.type==='MultiLineString')return g.coordinates.map(coords=>({coords,closed:false}));if(g.type==='Polygon')return g.coordinates.map(coords=>({coords,closed:true}));if(g.type==='MultiPolygon')return g.coordinates.flatMap(poly=>poly.map(coords=>({coords,closed:true})));return[];}
const API={coordinate,inWindow,localRoute,validRegistry,readingState,instruments,populationPoints,anchoredAI,geometryParts};
if(typeof module!=='undefined'&&module.exports)module.exports=API;
if(typeof document==='undefined')return;
const canvas=document.getElementById('map'),ctx=canvas.getContext('2d'),status=document.getElementById('status'),layerList=document.getElementById('layers'),dossier=document.getElementById('dossier'),picker=document.getElementById('point-picker');
const PALETTE={observed:'#b93720',untimed:'#946a2b',estimated:'#536d7a',forecast:'#6a5791',unavailable:'#7b7d79'};
let width=1,height=1,dpr=1,scale=1,tx=0,ty=0,frame=0,layers=[],points=[],selected=null;
const loaded=new Map(),visible=new Set(),layerNotes=new Map();
function element(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function project(lat,lon){const kx=Math.cos(44.8*Math.PI/180),s=Math.min((width-36)/((BB.lo1-BB.lo0)*kx),(height-36)/(BB.la1-BB.la0));return[(width-(BB.lo1-BB.lo0)*kx*s)/2+(lon-BB.lo0)*kx*s,(height-(BB.la1-BB.la0)*s)/2+(BB.la1-lat)*s];}
function redraw(){if(!frame)frame=requestAnimationFrame(()=>{frame=0;draw();});}
function resize(){const r=canvas.getBoundingClientRect();width=Math.max(1,r.width);height=Math.max(1,r.height);dpr=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);redraw();}
function draw(){
    if(!ctx)return;
    ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#fbfaf7';ctx.fillRect(0,0,width,height);ctx.translate(tx,ty);ctx.scale(scale,scale);
    const base=loaded.get('belgrade-basemap');
    if(visible.has('belgrade-basemap')&&base)for(const f of base.features||[]){
        const water=f.layer==='river'||f.layer==='lake',parts=geometryParts(f);ctx.beginPath();
        for(const part of parts){let started=false;for(const c of part.coords){if(!Array.isArray(c)||!coordinate(c[1],c[0]))continue;const[x,y]=project(c[1],c[0]);if(!started){ctx.moveTo(x,y);started=true;}else ctx.lineTo(x,y);}if(part.closed)ctx.closePath();}
        ctx.fillStyle=water?'#d4dfe2':'#e8e7e1';ctx.strokeStyle=water?'#91a7b0':'#c9cbc4';ctx.lineWidth=(f.layer==='river'?3:0.8)/scale;if(parts.some(p=>p.closed))ctx.fill('evenodd');ctx.stroke();
    }
    for(const p of points){
        if(!visible.has(p.layer))continue;const[x,y]=project(p.lat,p.lon),sx=x*scale+tx,sy=y*scale+ty;if(sx<-20||sy<-20||sx>width+20||sy>height+20)continue;
        if(p.layer==='kontur-population'){ctx.globalAlpha=0.08+Math.min(0.42,Math.sqrt(p.data.population)/180);ctx.fillStyle='#536d7a';ctx.beginPath();ctx.arc(x,y,Math.max(2,Math.min(6,2+Math.sqrt(p.data.population)/30))/scale,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1;continue;}
        const r=(p.is_ai?5:4)/scale;ctx.beginPath();if(p.is_ai){ctx.moveTo(x,y-r);ctx.lineTo(x+r,y);ctx.lineTo(x,y+r);ctx.lineTo(x-r,y);ctx.closePath();}else ctx.arc(x,y,r,0,Math.PI*2);
        ctx.fillStyle=p.state==='unavailable'?'#fbfaf7':PALETTE[p.state];ctx.strokeStyle=PALETTE[p.state];ctx.lineWidth=1.3/scale;ctx.fill();ctx.stroke();
        if(p.is_ai){ctx.font=(10/scale)+'px monospace';ctx.fillStyle='#111311';ctx.fillText(p.data.model,x+7/scale,y+3/scale);}
        if(selected===p){ctx.beginPath();ctx.arc(x,y,9/scale,0,Math.PI*2);ctx.strokeStyle='#111311';ctx.stroke();}
    }
}
function describeValue(v){if(v===null||v===undefined||v==='')return'nije dostupno';if(Array.isArray(v))return v.map(x=>typeof x==='object'?JSON.stringify(x):String(x)).join('\n');return typeof v==='object'?JSON.stringify(v):String(v);}
const LABELS={sid:'Izvor',name:'Naziv izvora',station:'Instrument',state:'Stanje podatka',lat:'Širina',lon:'Dužina',as_of:'Presek fajla',last_received:'Poslednji prijem',expected_slots:'Očekivani prijemi izvora',captured:'Ostvareni prijemi izvora',quorum:'Ritam prijema izvora',population:'Modelovana populacija u ćeliji',release:'Izdanje',source:'Provenijencija',note:'Ograničenje',model:'Model',title:'Naslov',question:'Pitanje',limitations:'Ograničenja',at:'Nastalo',geo:'Prostorno sidro',provenance:'Poreklo',id:'Identifikator'};
function showDossier(p){
    selected=p;picker.value=String(points.indexOf(p));dossier.replaceChildren();const layer=layers.find(l=>l.id===p.layer);dossier.append(element('h2',p.data.station||p.data.title||'Populaciona ćelija'));const dl=element('dl');
    for(const field of layer.dossier_fields){if(field==='measurements')continue;dl.append(element('dt',LABELS[field]||field),element('dd',describeValue(p.data[field])));}dossier.append(dl);
    if(layer.dossier_fields.includes('measurements')){dossier.append(element('h3','Poslednji primljeni red po veličini'));for(const m of p.data.measurements){const line=element('div',undefined,'reading');line.append(element('strong',m.parameter+': '+describeValue(m.value)+' '+m.unit),element('p',m.state+' · vreme pojave: '+describeValue(m.measured)+' · primljeno: '+describeValue(m.received)));if(m.clock_note)line.append(element('p',m.clock_note));dossier.append(line);}}
    dossier.append(element('p','Uslovi: '+layer.licence,'meta'));const evidence=element('a','Otvori izvorni fajl →');evidence.href=layer.route;dossier.append(evidence);document.getElementById('dossier-hint').hidden=true;redraw();
}
function refreshPicker(){picker.replaceChildren(element('option','Izaberi instrument ili AI zapis'));picker.options[0].value='';for(const p of points.filter(p=>visible.has(p.layer)&&p.layer!=='kontur-population')){const o=element('option',(p.data.sid||'AI')+' · '+(p.data.station||p.data.title||p.id));o.value=String(points.indexOf(p));picker.append(o);}}
picker.addEventListener('change',()=>{if(picker.value!=='')showDossier(points[Number(picker.value)]);});
function renderLayers(){layerList.replaceChildren();for(const layer of layers){const item=element('div',undefined,'layer'),label=element('label'),check=element('input');check.type='checkbox';check.checked=visible.has(layer.id);check.disabled=!loaded.has(layer.id)||layer.id==='materija';check.id='toggle-'+layer.id;check.addEventListener('change',()=>{if(check.checked)visible.add(layer.id);else visible.delete(layer.id);refreshPicker();redraw();});label.append(check,element('span',layer.label));item.append(label,element('p',layerNotes.get(layer.id)||layer.note,'meta'),element('p',(layer.must_be_named||[]).join(' · ')+' · '+layer.licence,'attribution'));layerList.append(item);}}
async function fetchLayer(layer){const r=await fetch(layer.route);if(!r.ok)throw Error('HTTP '+r.status);return r.json();}
async function loadData(){
    try{
        const response=await fetch('MAP_LAYERS.json');if(!response.ok)throw Error('Registar: HTTP '+response.status);layers=validRegistry(await response.json());
        await Promise.all(layers.map(async layer=>{try{loaded.set(layer.id,await fetchLayer(layer));visible.add(layer.id);}catch(error){layerNotes.set(layer.id,'unavailable · '+error.message);}}));
        const snap=loaded.get('instruments');if(snap){points.push(...instruments(snap));layerNotes.set('instruments',points.filter(p=>p.layer==='instruments').length+' instrumenata u prozoru · presek '+(snap.as_of||'nepoznat')+'. Prijem nije potvrda merenja.');}
        const pop=loaded.get('kontur-population');if(pop){points.push(...populationPoints(pop));layerNotes.set('kontur-population','estimated · izdanje '+((pop.source||{}).release||'nepoznato')+'. Tačke su simboli ćelija, ne granice niti trenutni popis.');}
        const mat=loaded.get('materija');visible.delete('materija');layerNotes.set('materija','unavailable · '+(mat&&mat.reason||'Nema proverenih retro-pasoša sa dozvoljenim izvorom.'));
        const ai=loaded.get('ai-feed'),aiLayer=layers.find(l=>l.id==='ai-feed');
        if(ai&&aiLayer){let entries=Array.isArray(ai.entries)?ai.entries:[];if(ai.first_page){try{if(!/^page-[a-zA-Z0-9_-]+\.json$/.test(ai.first_page)||aiLayer.page_prefix!=='ai-feed/')throw Error('Nevažeća putanja AI stranice.');const r=await fetch(aiLayer.page_prefix+ai.first_page);if(!r.ok)throw Error('HTTP '+r.status);entries=(await r.json()).entries||[];}catch(error){layerNotes.set('ai-feed','unavailable · AI arhiva: '+error.message);}}const anchored=anchoredAI(entries,points);points.push(...anchored);if(!layerNotes.has('ai-feed'))layerNotes.set('ai-feed',anchored.length+' zapisa sa validnim sidrom na najnovijoj stranici; '+(entries.length-anchored.length)+' bez prikazivog sidra. Svaki je model-derived, estimated.');}
        renderLayers();refreshPicker();status.textContent='Pomeri mapu, uvećaj, izaberi tačku. '+(layers.length-loaded.size?(layers.length-loaded.size)+' sloj(a) nije dostupno.':'');resize();
    }catch(error){status.textContent='unavailable · '+error.message;}
}
function zoom(f,x=width/2,y=height/2){const next=Math.max(0.65,Math.min(20,scale*f));f=next/scale;tx=x-(x-tx)*f;ty=y-(y-ty)*f;scale=next;redraw();}
document.getElementById('zoom-in').addEventListener('click',()=>zoom(1.35));document.getElementById('zoom-out').addEventListener('click',()=>zoom(1/1.35));document.getElementById('reset-map').addEventListener('click',()=>{scale=1;tx=ty=0;redraw();});
canvas.addEventListener('wheel',e=>{e.preventDefault();const r=canvas.getBoundingClientRect();zoom(e.deltaY<0?1.12:1/1.12,e.clientX-r.left,e.clientY-r.top);},{passive:false});
let drag=null;
canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;canvas.setPointerCapture(e.pointerId);drag={id:e.pointerId,x:e.clientX,y:e.clientY,tx,ty,moved:false};});
canvas.addEventListener('pointermove',e=>{if(!drag||drag.id!==e.pointerId)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(dx,dy)>4)drag.moved=true;tx=drag.tx+dx;ty=drag.ty+dy;redraw();});
canvas.addEventListener('pointerup',e=>{if(!drag||drag.id!==e.pointerId)return;const click=!drag.moved;drag=null;if(!click)return;const r=canvas.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;let hit=null,best=13;for(const p of points){if(!visible.has(p.layer))continue;const[x,y]=project(p.lat,p.lon);let distance=Math.hypot(mx-(x*scale+tx),my-(y*scale+ty));if(p.layer==='kontur-population')distance+=5;if(distance<best){best=distance;hit=p;}}if(hit)showDossier(hit);});
canvas.addEventListener('pointercancel',()=>{drag=null;});
canvas.addEventListener('keydown',e=>{if(e.key==='+'||e.key==='=')zoom(1.35);else if(e.key==='-')zoom(1/1.35);else if(e.key==='0'){scale=1;tx=ty=0;redraw();}else if(e.key.startsWith('Arrow')){tx+=e.key==='ArrowLeft'?30:e.key==='ArrowRight'?-30:0;ty+=e.key==='ArrowUp'?30:e.key==='ArrowDown'?-30:0;redraw();}else return;e.preventDefault();});
window.addEventListener('resize',resize);
if(!ctx)status.textContent='Canvas nije dostupan; izvore otvori kroz Instrument.';else{resize();loadData();}
})();
