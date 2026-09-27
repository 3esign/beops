'use strict';
// Offline, auditable guesses about the place a headline describes. A radius is
// an editorial place-scale buffer, never a confidence interval or a boundary.
const fs=require('node:fs');
const gazetteer=require('./headline_places.json');
const VERSION='headline-place-rules/1';
const CYR='абвгдђежзијклљмнњопрстћуфхцчџш';
const LAT=['a','b','v','g','d','dj','e','z','z','i','j','k','l','lj','m','n','nj','o','p','r','s','t','c','u','f','h','c','c','dz','s'];
function normalize(text){return String(text||'').toLowerCase().replace(/[а-яђјљњћџ]/g,c=>LAT[CYR.indexOf(c)]||c).replace(/đ/g,'dj').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();}
const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const compiled=gazetteer.places.map(p=>({...p,patterns:[...new Set(p.aliases.map(normalize))].sort((a,b)=>b.length-a.length).map(a=>({alias:a,re:new RegExp('(?:^| )('+escape(a)+')(?= |$)','g')}))}));
const domesticContexts=[['Srbija',['srbija','srbiji','srbije','srbiju']],['Vojvodina',['vojvodina','vojvodini','vojvodine']],['Šumadija',['sumadija','sumadiji','sumadije']]];
const foreignContexts=[
 ['Rusija',['rusija','rusiji','rusije','rusiju']],['Ukrajina',['ukrajina','ukrajini','ukrajine','ukrajinu']],
 ['SAD',['sad','amerika','americi','amerike','ameriku','sjedinjene americke drzave','sjedinjenim americkim drzavama']],
 ['Kina',['kina','kini','kine','kinu']],['Izrael',['izrael','izraelu','izraela']],['Iran',['iran','iranu','irana']],
 ['Liban',['liban','libanu','libana']],['Palestina',['palestina','palestini','palestine']],['Gaza',['gaza','gazi','gaze']],
 ['Nemačka',['nemacka','nemackoj','nemacke','nemacku']],['Francuska',['francuska','francuskoj','francuske','francusku']],
 ['Britanija',['britanija','britaniji','britanije','engleska','engleskoj','engleske']],['Italija',['italija','italiji','italije']],
 ['Španija',['spanija','spaniji','spanije']],['Grčka',['grcka','grckoj','grcke']],['Turska',['turska','turskoj','turske']],
 ['Hrvatska',['hrvatska','hrvatskoj','hrvatske']],['Bosna i Hercegovina',['bosna','bosni','bosne','bih','bosna i hercegovina','bosni i hercegovini']],
 ['Crna Gora',['crna gora','crnoj gori','crne gore']],['Severna Makedonija',['severna makedonija','severnoj makedoniji','severne makedonije']],
 ['Slovenija',['slovenija','sloveniji','slovenije']],['Mađarska',['madjarska','madjarskoj','madjarske']],
 ['Rumunija',['rumunija','rumuniji','rumunije']],['Bugarska',['bugarska','bugarskoj','bugarske']],
 ['Austrija',['austrija','austriji','austrije']],['Švajcarska',['svajcarska','svajcarskoj','svajcarske']],
 ['Japan',['japan','japanu','japana']],['Indija',['indija','indiji','indije']],['Brazil',['brazil','brazilu','brazila']],
 ['Australija',['australija','australiji','australije']],['Kanada',['kanada','kanadi','kanade']],
 ['Sarajevo',['sarajevo','sarajevu','sarajeva']],['Zagreb',['zagreb','zagrebu','zagreba']],['Podgorica',['podgorica','podgorici','podgorice']],
 ['Skoplje',['skoplje','skoplju','skoplja']],['Ljubljana',['ljubljana','ljubljani','ljubljane']],
 ['Banja Luka',['banja luka','banjaluka','banjoj luci','banjaluci','banje luke','banjaluke']],
 ['Moskva',['moskva','moskvi','moskve']],['Kijev',['kijev','kijevu','kijeva']],['Vašington',['vasington','vasingtonu','vasingtona']],
 ['Njujork',['njujork','njujorku','njujorka','nju jork','nju jorku','nju jorka']],['Peking',['peking','pekingu','pekinga']],
 ['Berlin',['berlin','berlinu','berlina']],['Pariz',['pariz','parizu','pariza']],['London',['london','londonu','londona']],
 ['Rim',['rim','rimu','rima']],['Madrid',['madrid','madridu','madrida']],['Atina',['atina','atini','atine']],
 ['Istanbul',['istanbul','istanbulu','istanbula']],['Beč',['bec','becu','beca']],['Budimpešta',['budimpesta','budimpesti','budimpeste']],
 ['Brisel',['brisel','briselu','brisela']],['Teheran',['teheran','teheranu','teherana']]
];
function contextCandidates(text,original){
  const result=[];
  for(const [scope,list]of[['serbia',domesticContexts],['outside',foreignContexts]])for(const[name,aliases]of list){
    const matched=aliases.find(a=>(' '+text+' ').includes(' '+a+' ')&&(a!=='sad'||/\bSAD\b|САД/.test(original)));
    if(matched){const start=(' '+text+' ').indexOf(' '+matched+' ');result.push({place_id:'context-'+normalize(name).replace(/ /g,'-'),name,scope,precision:'country_or_external_context',matched_text:matched,normalized_span:[start,start+matched.length],reason:'scope_context_only',coordinates:null,confidence:'unverified',method:VERSION});}
  }
  return result;
}
function findPlaces(text){
  const found=[];
  for(const place of compiled)for(const {re,alias}of place.patterns){re.lastIndex=0;let m;while((m=re.exec(text))!==null){const start=m.index+(m[0].startsWith(' ')?1:0);found.push({place,matched_text:alias,start,end:start+alias.length});}}
  // "Novi Beograd" is one name, not a simultaneous mention of Beograd.
  return found.sort((a,b)=>(b.end-b.start)-(a.end-a.start)).filter((f,i,all)=>!all.slice(0,i).some(g=>g.start<=f.start&&g.end>=f.end)).sort((a,b)=>a.start-b.start);
}
function cueFor(text,match,original){
  const before=text.slice(Math.max(0,match.start-80),match.start),after=text.slice(match.end);
  // Personal origin, institutions, teams and political metonymy are not locations.
  if(match.place.id==='nis'&&/\bNIS(?:\b|-)/.test(original)&&!/[Нн][Ии][Шш]|[Nn][Ii][Šš]/.test(original))return {ok:false,reason:'company_acronym_not_city'};
  if(/(?:ulici|ulica|bulevaru|bulevar|trgu|trg) $/.test(before)&&match.place.precision==='city')return {ok:false,reason:'street_name_not_city'};
  if(/(?:fk|kk|ok|rk|ofk|klub|klubu|kluba|ekipa|ekipe|tim|tima|univerzitet|univerziteta|univerzitetu) $/.test(before))return {ok:false,reason:'institution_or_team_name'};
  if(/(?:^| )(?:fakultet[a-z]*|univerzitet[a-z]*|institut[a-z]*|ambasad[a-z]*|bolnic[a-z]*) u $/.test(before))return {ok:false,reason:'institution_location_not_event_site'};
  if(/(?:^| )(?:iz|od|za|protiv) $/.test(before))return {ok:false,reason:'origin_destination_or_entity_not_event_site'};
  const cue=before.match(/(?:^| )(u|na|kod|oko|blizu)(?: (?:centru|okolini|opstini|naselju|delu|podrucju|teritoriji|blizini|gradu|gradskom naselju))?(?: (?:beogradskoj|beogradskom))? $/);
  if(!cue)return {ok:false,reason:'name_mention_without_event_location_cue'};
  if(/\b(?:izjava|izjavu|izjave|stavu|stav|odnosima|odnose|politici|politika)\b/.test(before)&&/^(?: (?:i|prema|o) )/.test(after))return {ok:false,reason:'possible_political_metonymy'};
  if(/^(?: igrac| fudbaler| kosarkas| vaterpolista| potpisao| igra | igrace | igrao )/.test(after)&&!/(?:utakmica|mec|turnir|stadion|hala|bazen)/.test(text))return {ok:false,reason:'possible_sports_club_reference'};
  const loose=/(?:kod|oko|blizu|okolini|blizini)/.test(cue[0]);
  return {ok:true,reason:loose?'explicit_nearby_place_cue':'explicit_location_cue',cue:cue[0].trim(),loose};
}
function locateHeadline(input){
  const original=typeof input==='string'?input:String(input?.title||input?.headline||input?.result||input?.text||'');
  const text=normalize(original),matches=findPlaces(text),contexts=contextCandidates(text,original);
  const hasBelgrade=matches.some(m=>m.place.id==='beograd'&&cueFor(text,m,original).ok);
  const conflictingCity=matches.some(m=>m.place.scope!=='belgrade'&&m.place.precision==='city');
  const candidates=matches.map(m=>{
    let cue=cueFor(text,m,original);
    const tiedBelgrade=/\bbeogradsk(?:oj|om) $/.test(text.slice(0,m.start));
    if(m.place.requires_belgrade&&(!(hasBelgrade||tiedBelgrade)||conflictingCity))cue={ok:false,reason:'shared_name_requires_unambiguous_belgrade_context'};
    return {place_id:m.place.id,name:m.place.name,scope:m.place.scope,precision:m.place.precision,matched_text:m.matched_text,normalized_span:[m.start,m.end],reason:cue.reason,location_cue:cue.cue||null,eligible:cue.ok,nearby:Boolean(cue.loose),coordinates:m.place.lon==null?null:[m.place.lon,m.place.lat],radius_m:m.place.radius_m||null,confidence:cue.ok?'rule_supported_unvalidated':'candidate',method:VERSION,evidence:m.place.evidence||null};
  });
  const base={scope:'unknown',status:matches.length?'ambiguous':'unknown',estimate:null,candidates:[...candidates,...contexts],method:VERSION,gazetteer_version:gazetteer.version,limitation:'Headline-only inference, not verified event location. Radius is a disclosed place-scale approximation, not a boundary or probability.'};
  const eligible=candidates.filter(c=>c.eligible&&c.coordinates);
  // A route or two distinct places must not silently collapse onto one endpoint.
  const route=/\b(?:izmedju|deonic[a-z]*|tras[a-z]*|relacij[a-z]*)\b/.test(text)||(/\b(?:put|puta|putu|pruga|pruge|pruzi|autoput[a-z]*)\b/.test(text)&&new Set(candidates.map(c=>c.place_id)).size>1);
  const coordinated=candidates.some((c,i)=>i>0&&c.place_id!==candidates[i-1].place_id&&/^(?: i | , |, | i u | i na )$/.test(text.slice(candidates[i-1].normalized_span[1],c.normalized_span[0])));
  if((route||coordinated)&&candidates.length){base.reason='route_or_multiple_locations';return base;}
  const unique=[...new Map(eligible.map(c=>[c.place_id,c])).values()];
  const specific=unique.filter(c=>c.place_id!=='beograd');
  // A citywide incident digest is not wholly situated at the one named detail.
  const roundup=/\b(?:noc u beogradu|tokom noci u beogradu|nocas u beogradu)\b/.test(text)&&matches.some(m=>m.place.id!=='beograd')&&/[,:;]/.test(original);
  if(roundup){base.status='ambiguous';base.reason='multiple_incidents_in_city_roundup';return base;}
  const choices=unique.some(c=>c.place_id==='beograd')&&specific.length&&specific.every(c=>c.scope==='belgrade')?specific:unique;
  const contextualLocation=c=>{
    const prefix=text.slice(0,c.normalized_span[0]);
    const direct=/(?:^| )(?:u|na|kod|oko|blizu)(?: (?:centralnoj|severnoj|juznoj|istocnoj|zapadnoj|celoj|jugoistocnoj|severozapadnoj))? $/.test(prefix);
    // A second place inherits the spatial role in "u Beograd i Sarajevo".
    const linked=candidates.some(p=>p.eligible&&p.normalized_span[1]<c.normalized_span[0]&&/^(?: | (?:i|ili|kao i)(?: (?:u|na))?(?: (?:centralnoj|severnoj|juznoj|istocnoj|zapadnoj|celoj|jugoistocnoj|severozapadnoj))? )$/.test(text.slice(p.normalized_span[1],c.normalized_span[0])));
    return direct||linked;
  };
  const externalLocation=contexts.some(c=>c.scope==='outside'&&contextualLocation(c));
  const broadLocation=contexts.some(contextualLocation);
  if(choices.length===1&&!broadLocation){
    const c=choices[0];
    // Another city even without a locative may be a route endpoint or event site.
    const otherPlace=candidates.some(o=>o.place_id!==c.place_id&&!['origin_destination_or_entity_not_event_site','company_acronym_not_city','institution_or_team_name','institution_location_not_event_site'].includes(o.reason)&&!(o.place_id==='beograd'&&c.scope==='belgrade'));
    if(!otherPlace){
      base.scope=c.scope;base.status='estimated';base.reason=c.reason;
      base.estimate={place_id:c.place_id,name:c.name,lon:c.coordinates[0],lat:c.coordinates[1],radius_m:c.radius_m*(c.nearby?2:1),precision:c.precision,confidence:c.confidence,method:VERSION,matched_text:c.matched_text,location_cue:c.location_cue,evidence:c.evidence,radius_basis:'editorial_place_scale_buffer_not_statistical_error',verified:false};
      return base;
    }
  }
  if(choices.length>1||broadLocation&&choices.length){base.status='ambiguous';base.reason='multiple_location_candidates';return base;}
  const contextScopes=[...new Set(contexts.map(c=>c.scope))];
  const spatialCandidates=candidates.filter(c=>c.eligible);
  const candidateScopes=[...new Set((spatialCandidates.length?spatialCandidates:candidates.filter(c=>!['company_acronym_not_city','institution_or_team_name','institution_location_not_event_site','shared_name_requires_unambiguous_belgrade_context','origin_destination_or_entity_not_event_site','street_name_not_city'].includes(c.reason))).map(c=>c.scope))];
  // Scope can be known without claiming a mappable event location.
  if(externalLocation)base.scope='outside';
  else if(candidateScopes.length===1)base.scope=candidateScopes[0];
  else if(!candidateScopes.length&&contextScopes.length===1)base.scope=contextScopes[0];
  base.reason=base.candidates.length?'insufficient_or_ambiguous_location_evidence':'no_known_place';
  return base;
}
if(require.main===module){
  try{const value=JSON.parse(fs.readFileSync(0,'utf8').replace(/^\uFEFF/,''));if(!Array.isArray(value))throw Error('Expected a JSON array of headlines');process.stdout.write(JSON.stringify(value.map(locateHeadline))+'\n');}
  catch(error){process.stderr.write(error.message+'\n');process.exitCode=1;}
}
module.exports={locateHeadline,normalize,VERSION,GAZETTEER:gazetteer};
