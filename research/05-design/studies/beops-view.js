/* One small observation generation shared by the page and its embedded panels. */
(function(root){
  'use strict';
  function checkPage(value){
    const expected=root.document?.querySelector('meta[name="beops-input-generation"]')?.content;
    if(root.document&&(expected||value.edition?.state==='verified_capture')&&expected!==value.edition?.input_generation?.id)throw Error('page_generation_mismatch');
    return value;
  }
  function clock(value){return typeof value==='string'&&/(Z|[+-]\d\d:\d\d)$/.test(value)?Date.parse(value):NaN;}
  function expandSnapshot(snapshot){
    if(snapshot.schema!=='beops-latest-observations/v2')return snapshot;
    const allowed=new Set(['t0','t','tc0','tc','rt','rtc','rx','q','tu','source_label','clock_unresolved','clock_ref']);
    const sources=snapshot.sources.map(source=>{
      const {point_defaults:defaults={},...rest}=source;
      if(!defaults||Array.isArray(defaults)||typeof defaults!=='object'||Object.keys(defaults).some(key=>!allowed.has(key)))throw Error('invalid_point_defaults');
      return {...rest,datastreams:source.datastreams.map(stream=>({...stream,points:stream.points.map(point=>{
        if(Object.keys(defaults).some(key=>Object.hasOwn(point,key)))throw Error('conflicting_point_defaults');
        return {...defaults,...point};
      })}))};
    });
    return {...snapshot,schema:'beops-latest-observations/v1',sources};
  }
  function editionState(view,now=Date.now()){
    if(view?.edition?.state!=='verified_capture')return {state:'unknown'};
    const built=clock(view.edition.built_at),cut=clock(view.edition.input_generation?.captured_at);
    if(!Number.isFinite(now)||!Number.isFinite(built)||!Number.isFinite(cut))return {state:'unknown'};
    if(built>now+300000||cut>now+300000||built<cut-300000)return {state:'clock_error'};
    const age_seconds=Math.max(0,(now-built)/1000),capture_age_seconds=Math.max(0,(now-cut)/1000);
    return {state:age_seconds>3600?'stale':capture_age_seconds>3600?'stale_capture':'current',age_seconds,capture_age_seconds};
  }
  function sourceState(source,now=Date.now()){
    if(source.paused)return 'paused';
    const attempt=clock(source.last_attempt_at),received=clock(source.last_captured_at);
    if(attempt>now+300000||received>now+300000)return 'clock_error';
    if(['failed','unparsed'].includes(source.last_attempt_state))return 'failed';
    if(!source.last_captured_at)return 'no_reception';
    if(!Number.isFinite(received))return 'unknown';
    const cadence=Number(source.cadence_seconds);
    if(!Number.isFinite(cadence)||cadence<=0)return 'unknown';
    return now-received>Math.max(cadence*2000,300000)?'old_reception':'received';
  }
  function mount(api){
    const doc=root.document;if(!doc)return;
    const run=()=>{
      if(doc.getElementById('beops-edition'))return;
      const box=doc.createElement('details');box.id='beops-edition';box.className='beops-edition';
      let embedded=false;try{embedded=root.parent!==root&&Boolean(root.parent.beopsView);}catch(e){}
      box.hidden=embedded;
      const title=doc.createElement('summary'),body=doc.createElement('div');box.append(title,body);
      const style=doc.createElement('style');style.textContent='.beops-edition{font:12px/1.5 system-ui,sans-serif;color:#343a36;background:#f3f1e9;border-bottom:1px solid #d4d8ce;padding:8px clamp(12px,3vw,40px)}.beops-edition summary{cursor:pointer}.beops-edition[data-state="stale"],.beops-edition[data-state="stale_capture"],.beops-edition[data-state="clock_error"],.beops-edition[data-state="unknown"]{border-left:4px solid #936225}.beops-edition p{margin:6px 0}.beops-edition ul{padding-left:18px;max-height:250px;overflow:auto}.beops-edition time{font-variant-numeric:tabular-nums}';doc.head.append(style);
      doc.body.prepend(box);
      const words={
        sr:{edition:'Izdanje',cut:'Presek',current:'Presek je mlađi od 60 minuta',stale:'Izdanje je zastarelo',stale_capture:'Presek podataka je zastareo',unknown:'Starost izdanja nije potvrđena',clock_error:'Vreme nije pouzdano',mismatch:'Stranica i podaci su iz različitih izdanja — osvežite stranicu',note:'Ovo je stanje iz sačuvanog preseka. Prijem nije vreme merenja; tekući sat ne potvrđuje rad kolektora.',sources:'Prijem po izvoru',paused:'pauziran',failed:'poslednji pokušaj neuspešan',no_reception:'nema uspešnog prijema u preseku',old_reception:'prijem kasni',received:'prijem u okviru ritma'},
        en:{edition:'Edition',cut:'Data cut',current:'Data cut is less than 60 minutes old',stale:'Edition is stale',stale_capture:'Data cut is stale',unknown:'Edition age is unverified',clock_error:'Clock is uncertain',mismatch:'Page and data belong to different editions — reload the page',note:'This describes the saved data cut. Reception is not measurement time; the current clock does not confirm collector operation.',sources:'Reception by source',paused:'paused',failed:'last attempt failed',no_reception:'no successful reception in this cut',old_reception:'reception overdue',received:'reception within cadence'},
        zh:{edition:'版本',cut:'数据截面',current:'数据截面距今不足60分钟',stale:'版本已过时',stale_capture:'数据截面已过时',unknown:'版本时间未确认',clock_error:'时钟不确定',mismatch:'页面与数据属于不同版本，请刷新',note:'这里显示保存的数据截面。接收时间不等于测量时间；当前时钟不能证明采集器正在运行。',sources:'各来源接收状态',paused:'已暂停',failed:'最近尝试失败',no_reception:'截面内没有成功接收',old_reception:'接收逾期',received:'按节奏接收'},
        de:{edition:'Ausgabe',cut:'Datenstand',current:'Datenstand ist jünger als 60 Minuten',stale:'Ausgabe ist veraltet',stale_capture:'Datenstand ist veraltet',unknown:'Alter der Ausgabe ist unbestätigt',clock_error:'Zeitangabe ist unsicher',mismatch:'Seite und Daten stammen aus verschiedenen Ausgaben — Seite neu laden',note:'Dies beschreibt den gespeicherten Datenstand. Empfangszeit ist keine Messzeit; die laufende Uhr bestätigt keinen Betrieb des Kollektors.',sources:'Empfang je Quelle',paused:'pausiert',failed:'letzter Versuch fehlgeschlagen',no_reception:'kein erfolgreicher Empfang in diesem Datenstand',old_reception:'Empfang überfällig',received:'Empfang im vorgesehenen Rhythmus'}
      };
      const update=async()=>{
        const lang=(doc.documentElement.lang||'sr').slice(0,2),w=words[lang]||words.en;
        try{
          const view=await api.overview(),state=editionState(view);box.dataset.state=state.state;
          box.hidden=embedded;
          title.textContent=w[state.state]+(Number.isFinite(state.age_seconds)?' · '+w.edition+': '+Math.floor(state.age_seconds/60)+' min':'');
          body.replaceChildren();const note=doc.createElement('p');note.textContent=w.note;body.append(note);
          for(const [label,date] of [[w.edition,view.edition?.built_at],[w.cut,view.edition?.input_generation?.captured_at]]){
            if(!date)continue;const row=doc.createElement('p'),time=doc.createElement('time');time.dateTime=date;time.textContent=date.replace('T',' ').replace('+00:00',' UTC').replace('Z',' UTC');row.append(label+': ',time);body.append(row);
          }
          const heading=doc.createElement('p');heading.textContent=w.sources;body.append(heading);
          const list=doc.createElement('ul');
          for(const source of view.collector?.sources||[]){const row=doc.createElement('li');row.textContent=source.sid+' — '+w[sourceState(source)]+(source.last_captured_at?' · '+source.last_captured_at:'');list.append(row);}body.append(list);
        }catch(error){box.hidden=false;box.dataset.state='unknown';title.textContent=error.message==='page_generation_mismatch'?w.mismatch:w.unknown;body.replaceChildren();}
      };
      title.textContent=words.en.unknown;update();root.setInterval(update,30000);
      new root.MutationObserver(update).observe(doc.documentElement,{attributes:true,attributeFilter:['lang']});
    };
    if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',run,{once:true});else run();
  }
  try{if(root.parent!==root&&root.parent.beopsView){
    const parent=root.parent.beopsView;
    root.beopsView={overview:async()=>checkPage(await parent.overview()),read:async(name,view)=>parent.read(name,checkPage(view||await parent.overview())),historyResource:(range,view)=>parent.historyResource?parent.historyResource(range,view):historyResource(range,view),editionState,sourceState};
    mount(root.beopsView);return;
  }}catch(e){}
  function historyResource(range,view){
    let hours=typeof range==='number'?range:0;
    if(typeof range==='string'){
      if(range.endsWith('d'))hours=parseFloat(range)*24;
      else if(range.endsWith('h'))hours=parseFloat(range);
      else if(range==='now')hours=0;
    }
    const candidates=[
      {maxHours:7*24,name:'history-7d.json'},
      {maxHours:14*24,name:'history-14d.json'},
      {maxHours:30*24,name:'history-30d.json'},
      {maxHours:Infinity,name:'history.json'}
    ];
    for(const c of candidates){
      if(hours<=c.maxHours){
        if(!view||!view.resources||view.resources[c.name])return c.name;
      }
    }
    return 'history.json';
  }
  let current=null,started=0;const cache=new Map();
  async function overview(){
    if(!current||Date.now()-started>=60000){
      started=Date.now();
      const pending=fetch('city-overview.json',{cache:'no-store'}).then(async r=>{
        if(!r.ok)throw Error('overview_unavailable');
        const value=await r.json();
        if(value.schema!=='beops-city-view/v1'||!/^[a-f0-9]{64}$/.test(value.generation)||!value.snapshot)throw Error('invalid_overview');
        checkPage(value);
        return {...value,snapshot:expandSnapshot(value.snapshot)};
      });
      current=pending;pending.catch(()=>{if(current===pending)current=null;});
      cache.clear();
    }
    return current;
  }
  async function read(name,view){
    if(!/^[a-z][a-z0-9-]*\.json$/.test(name))throw Error('invalid_resource');
    view=checkPage(view||await overview());
    const expected=view.resources[name];if(!expected)throw Error('resource_not_in_generation');
    const key=view.generation+'/'+name;
    if(!cache.has(key)){
      const request=fetch(name,{cache:'no-store'}).then(async response=>{
        if(!response.ok)throw Error('resource_unavailable');
        const bytes=await response.arrayBuffer();
        const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
        if(bytes.byteLength!==expected.bytes||digest!==expected.sha256)throw Error('generation_mismatch');
        return JSON.parse(new TextDecoder().decode(bytes));
      });
      cache.set(key,request);request.catch(()=>cache.delete(key));
    }
    return structuredClone(await cache.get(key));
  }
  root.beopsView={overview,read,historyResource,editionState,sourceState};
  mount(root.beopsView);
})(window);
