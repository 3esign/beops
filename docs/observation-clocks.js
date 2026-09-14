(function(root,factory){
  'use strict';
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.beopsClocks=api;
})(typeof globalThis==='object'?globalThis:this,function(){
  'use strict';
  function stamp(value){
    if(typeof value!=='string')return null;
    const m=value.match(/^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d)(?::(\d\d)(?:\.\d+)?)?(Z|[+-]\d\d:\d\d)$/);
    if(!m)return null;
    const y=+m[1],month=+m[2],day=+m[3],leap=y%4===0&&(y%100!==0||y%400===0);
    const days=[31,leap?29:28,31,30,31,30,31,31,30,31,30,31];
    if(month<1||month>12||day<1||day>days[month-1]||+m[4]>23||+m[5]>59||+(m[6]||0)>59)return null;
    const t=Date.parse(value);return Number.isFinite(t)?t:null;
  }
  function disclose(point,rules){
    const p=point||{},rule=rules?.[p.clock_ref]||p,hasEstimate=Object.hasOwn(p,'tc');
    const original=p.source_label??p.t??null,corrected=p.tc??null;
    const chosen=hasEstimate?corrected:p.t;
    const invalid=p.clock_unresolved||(!p.tu&&stamp(chosen)===null);
    const state=invalid?'unresolved':p.tu?'unknown':hasEstimate?'estimated':'source_label';
    const measured=['source_label','estimated'].includes(state)?chosen:null;
    const start=state==='estimated'?p.tc0:p.t0;
    const a=stamp(start),b=stamp(measured);
    return {schema:'beops-observation-clocks/v1',measurement_state:state,
      source_interval_start:p.t0??null,source_interval_end:original,
      estimated_interval_start:p.tc0??null,estimated_interval_end:corrected,
      measurement_time:measured,measurement_interval_seconds:a!==null&&b!==null&&b>=a?(b-a)/1000:null,
      source_publication_time:p.rt??null,estimated_publication_time:p.rtc??null,
      received_at:stamp(p.rx)!==null?p.rx:null,
      correction:{rule_id:rule.clock_rule??null,valid_until:rule.clock_valid_until??null,
        note:rule.clock_note??null,state:state==='estimated'?'estimated':state==='unresolved'?'unresolved':null}};
  }
  function placement(point){
    const c=disclose(point);
    if(c.measurement_time!==null)return {at:c.measurement_time,basis:c.measurement_state==='estimated'?'corrected':'measured'};
    return {at:c.received_at,basis:c.measurement_state==='unresolved'?'unresolved':'received'};
  }
  const words={
    sr:{source:'izvorni sat',interval:'izvorni interval',estimate:'procenjen sat',estimatedInterval:'procenjen interval',publication:'objava po izvoru',estimatedPublication:'procenjena objava',reception:'primljeno',unknown:'vreme merenja nije poznato',unresolved:'sat merenja nije razrešen',missing:'nepoznato'},
    en:{source:'source clock',interval:'source interval',estimate:'estimated clock',estimatedInterval:'estimated interval',publication:'source publication',estimatedPublication:'estimated publication',reception:'received',unknown:'measurement time is unknown',unresolved:'measurement clock is unresolved',missing:'unknown'},
    zh:{source:'来源时刻',interval:'来源区间',estimate:'估计时刻',estimatedInterval:'估计区间',publication:'来源发布时刻',estimatedPublication:'估计发布时刻',reception:'接收时刻',unknown:'测量时刻未知',unresolved:'测量时钟未确定',missing:'未知'},
    de:{source:'Quellzeit',interval:'Quellintervall',estimate:'geschätzte Zeit',estimatedInterval:'geschätztes Intervall',publication:'Veröffentlichung laut Quelle',estimatedPublication:'geschätzte Veröffentlichung',reception:'empfangen',unknown:'Messzeit ist unbekannt',unresolved:'Messzeit ist ungeklärt',missing:'unbekannt'}
  };
  function describe(point,language='sr',rules){
    const c=disclose(point,rules),w=words[language]||words.en,parts=[];
    const fmt=s=>stamp(s)===null?w.missing:new Date(stamp(s)).toISOString().slice(0,16).replace('T',' ')+' UTC';
    const interval=(start,end)=>start!==null?fmt(start)+' – '+fmt(end):fmt(end);
    if(c.source_interval_end!==null)parts.push((c.source_interval_start!==null?w.interval:w.source)+' '+interval(c.source_interval_start,c.source_interval_end));
    if(c.measurement_state==='estimated')parts.push((c.estimated_interval_start!==null?w.estimatedInterval:w.estimate)+' '+interval(c.estimated_interval_start,c.estimated_interval_end));
    if(c.measurement_state==='unknown'||c.measurement_state==='unresolved')parts.push(w[c.measurement_state]);
    if(c.source_publication_time!==null)parts.push(w.publication+' '+fmt(c.source_publication_time));
    if(c.estimated_publication_time!==null&&c.measurement_state==='estimated')parts.push(w.estimatedPublication+' '+fmt(c.estimated_publication_time));
    parts.push(w.reception+' '+fmt(c.received_at));
    return parts.join(' · ');
  }
  function summary(point,language='sr'){
    const c=disclose(point),w=words[language]||words.en;
    const fmt=s=>stamp(s)===null?w.missing:new Date(stamp(s)).toISOString().slice(5,16).replace('T',' ')+' UTC';
    const measured=c.measurement_time!==null?(c.measurement_state==='estimated'?w.estimate:w.source)+' '+fmt(c.measurement_time):w[c.measurement_state];
    return measured+' · '+w.reception+' '+fmt(c.received_at);
  }
  function html(point,language='sr',rules){
    const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const c=disclose(point,rules);
    const note=c.correction.note?' · '+c.correction.note:'';
    return '<details class="observation-clock"><summary>'+esc(summary(point,language))+'</summary><span>'+esc(describe(point,language,rules)+note)+'</span></details>';
  }
  function basisLabel(basis,language='sr'){
    const w=words[language]||words.en;
    return ({measured:w.source,corrected:w.estimate,received:w.reception,unresolved:w.unresolved})[basis]||w.unknown;
  }
  return {stamp,disclose,placement,describe,summary,html,basisLabel};
});
