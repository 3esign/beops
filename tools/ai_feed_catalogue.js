'use strict';
// Selection is pure; the Svemir menu remains the authority for executable CLI routes.
function selectModel(rows, provider, state={}, now=new Date(), isLocal=()=>true) {
  const eligible=[],held=[];
  for(const row of rows) {
    if(row.prov!=='cli'||row.bridge!==provider.catalogue_bridge||!isLocal(row.device))continue;
    if(!row.runnable || row.disabledUntil && Date.parse(row.disabledUntil)>+now){held.push({id:row.id,reason:row.status||'unavailable'});continue;}
    const previous=state.models?.[provider.id+'|'+row.model];
    // Quotas are frequently shared by all aliases of one CLI account. Do not hammer siblings.
    const family=Object.values(state.models||{}).find(r=>r.provider===provider.id&&r.failure_kind==='rate-limit'&&Date.parse(r.cooldown_until||r.next_at)>+now&&(provider.id!=='ollama'||String(r.model).includes('cloud')===String(row.model).includes('cloud')));
    if(family){held.push({id:row.id,reason:'account_cooldown'});continue;}
    if(previous && ['failed','interrupted'].includes(previous.state) && Date.parse(previous.cooldown_until||previous.next_at)>+now){held.push({id:row.id,reason:'model_cooldown'});continue;}
    eligible.push({...row,last_at:previous?.at||null});
  }
  eligible.sort((a,b)=>(a.last_at?Date.parse(a.last_at):0)-(b.last_at?Date.parse(b.last_at):0) || (a.costTier||2)-(b.costTier||2) || (b.speedTier||1)-(a.speedTier||1) || a.id.localeCompare(b.id));
  const chosen=eligible[0];
  return chosen?{ready:true,model:chosen.model,route_id:chosen.id,route_device:chosen.device,candidate_count:eligible.length,held_count:held.length,catalogue_status:chosen.status}
    :{ready:false,reason:held.some(h=>h.reason==='account_cooldown')?'account_cooldown':held.some(h=>h.reason==='model_cooldown')?'model_cooldown':held[0]?.reason||'no_runnable_catalogue_model',candidate_count:0,held_count:held.length};
}
function classifyFailure(text) {
  const s=String(text||'').toLowerCase();
  if(/429|rate.?limit|quota|usage limit|weekly limit|hit your limit|too many requests/.test(s))return 'rate-limit';
  if(/401|403|not logged in|unauthori|authentication|login required/.test(s))return 'auth';
  if(/unknown model|not supported|model.*not (available|supported)|invalid.*model/.test(s))return 'unsupported-model';
  if(/timeout|timed.out|job_deadline|aborted/.test(s))return 'timeout';
  if(/validation|json/.test(s))return 'invalid-output';
  return 'runtime';
}
module.exports={selectModel,classifyFailure};
