'use strict';
let en=false, data=null, generation=0;
const $=id=>document.getElementById(id), say=(sr,eng)=>en?eng:sr;
function safeURL(value){try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)&&!u.username&&!u.password?u.href:null;}catch{return null;}}
function stamp(value){return value?value.replace('T',' ').replace(/(?:\.\d+)?(?:Z|\+00:00)$/,' UTC'):say('nepoznato','unknown');}
function labels(){
  document.documentElement.lang=en?'en':'sr';
  $('lang').textContent=en?'Srpski':'English';
  $('heading').textContent=say('Svi sačuvani naslovi','All retained headlines');
  $('lead').textContent=say(
    'Cela prikupljena arhiva, sa izvornim naslovima, vezama i vremenima. Vreme objave nije vreme događaja. Izmenjeni naslovi ostaju kao posebne verzije. Tekst članaka se ne objavljuje. Naslovi se čuvaju bez automatskog brisanja; objavljene verzije ostaju i u Git istoriji.',
    'The complete collected archive, with original headlines, links and timestamps. Publication time is not event time. Revised headlines remain separate versions. Article bodies are not published. Headlines have no automatic expiry; published versions also remain in Git history.');
  for(const [id,sr,eng] of [
    ['search-label','Pretraga','Search'],['source-label','Izvor','Source'],
    ['from-label','Od datuma (UTC)','From date (UTC)'],['to-label','Do datuma (UTC)','To date (UTC)'],
    ['reset','Prikaži sve','Show all']]) $(id).textContent=say(sr,eng);
  $('source').options[0].textContent=say('Svi izvori','All sources');
}
function readingPosition(){
  const focused=document.activeElement.closest('#items article');
  const anchor=focused||[...$('items').children].find(e=>e.getBoundingClientRect().bottom>0);
  return {id:anchor?.dataset.id,top:anchor?.getBoundingClientRect().top,
    focused:focused?document.activeElement.tagName:null,
    open:new Set([...$('items').querySelectorAll('details[open]')].map(e=>e.parentElement.dataset.id))};
}
function articleFor(r, opened){
  const article=document.createElement('article'); article.dataset.id=r.id;
  const name=document.createElement('p'),h=document.createElement('h2'),times=document.createElement('p');
  const details=document.createElement('details'),summary=document.createElement('summary');
  name.textContent=r.source+' · '+r.sid;
  const url=safeURL(r.link);
  if(url){const a=document.createElement('a');a.href=url;a.rel='noopener noreferrer';a.textContent=r.title;h.append(a);}
  else h.textContent=r.title;
  times.textContent=say('Objavljeno: ','Published: ')+stamp(r.published)+' · '+say('Primljeno: ','Received: ')+stamp(r.received);
  summary.textContent=say('Poreklo zapisa','Record provenance');details.open=opened.has(r.id);
  details.append(summary,document.createTextNode('ID: '+r.id+' · capture: '+(r.permission_capture||'unknown')+' · SHA-256: '+(r.raw_sha256||'unknown')));
  article.append(name,h,times,details);return article;
}
async function render(options={}){
  labels();if(!data)return;
  const position=options.preserve?readingPosition():null,token=++generation;
  const q=$('query').value.trim().toLocaleLowerCase(),sid=$('source').value,from=$('from').value,to=$('to').value;
  const invalid=!!(from&&to&&from>to);
  for(const id of ['from','to'])$(id).setAttribute('aria-invalid',String(invalid));
  if(invalid){$('status').textContent=say('Početni datum mora biti pre završnog.','The start date must precede the end date.');$('items').setAttribute('aria-busy','false');return;}
  const rows=data.rows.filter(r=>{
    const day=(r.published||r.received||'').slice(0,10);
    return (!sid||r.sid===sid)&&(!q||(r.title+' '+r.source).toLocaleLowerCase().includes(q))&&(!from||day>=from)&&(!to||day<=to);
  });
  const fragment=document.createDocumentFragment();$('items').setAttribute('aria-busy','true');
  for(let start=0;start<rows.length;start+=200){
    if(token!==generation)return;
    for(const r of rows.slice(start,start+200))fragment.append(articleFor(r,position?.open||new Set()));
    await new Promise(requestAnimationFrame);
  }
  if(token!==generation)return;
  $('items').replaceChildren(fragment);$('items').setAttribute('aria-busy','false');
  if(position?.id){
    const anchor=[...$('items').children].find(e=>e.dataset.id===position.id);
    if(anchor){if(position.focused)anchor.querySelector(position.focused)?.focus({preventScroll:true});window.scrollBy(0,anchor.getBoundingClientRect().top-position.top);}
  }
  $('status').textContent=say('Prikazano','Showing')+' '+rows.length+' / '+data.count+' · '+say('arhiva ažurirana','archive updated')+' '+stamp(data.as_of);
}
async function load(){
  try{
    const response=await fetch('headlines.json',{cache:'no-store'});
    if(!response.ok)throw new Error('HTTP '+response.status);
    const next=await response.json();
    if(!Array.isArray(next.rows)||next.count!==next.rows.length||next.rows.some(r=>!r.id||typeof r.title!=='string'))throw new Error(say('Neispravan zapis arhive','Invalid archive data'));
    data=next;
    const old=$('source').value;
    while($('source').options.length>1)$('source').remove(1);
    const names=new Map(data.rows.map(r=>[r.sid,r.source]));
    for(const [sid,name] of [...names].sort((a,b)=>a[1].localeCompare(b[1]))){const o=document.createElement('option');o.value=sid;o.textContent=name+' · '+sid;$('source').append(o);}
    $('source').value=old;await render({preserve:true});
  }catch(e){$('status').textContent=say('Arhiva trenutno nije učitana: ','Archive could not be loaded: ')+e.message;$('items').setAttribute('aria-busy','false');}
}
for(const id of ['query','source','from','to'])$(id).addEventListener('input',()=>render());
$('reset').onclick=()=>{for(const id of ['query','source','from','to'])$(id).value='';render();};
$('lang').onclick=()=>{en=!en;render({preserve:true});};
labels();load();setInterval(()=>{if(!document.hidden)load();},60000);
