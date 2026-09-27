'use strict';
// Process-local observations. Nothing here converts CPU time into electricity or money.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {AsyncLocalStorage}=require('node:async_hooks');
const active=new AsyncLocalStorage();
function count(value){return Number.isSafeInteger(value)&&value>=0?value:null;}
function tokenUsage(usage){
  const u=usage&&typeof usage==='object'?usage:{};
  // Keep cache reads separate: provider input counts do not share one universal billing definition.
  const input=count(u.input_tokens??u.prompt_tokens??u.promptTokenCount);
  const output=count(u.output_tokens??u.completion_tokens??u.candidatesTokenCount);
  const cached=count(u.cached_input_tokens??u.cache_read_input_tokens??u.input_tokens_details?.cached_tokens??u.prompt_tokens_details?.cached_tokens??u.cachedContentTokenCount);
  const reasoning=count(u.output_tokens_details?.reasoning_tokens??u.thoughtsTokenCount);
  const cacheCreation=count(u.cache_creation_input_tokens);
  return {input_tokens:input,output_tokens:output,cached_input_tokens:cached,
    reasoning_tokens:reasoning,cache_creation_input_tokens:cacheCreation,
    provider_total_tokens:count(u.total_tokens??u.totalTokenCount),
    state:input!==null||output!==null?'provider_reported':'unavailable'};
}
function immutable(file,value){
  fs.mkdirSync(path.dirname(file),{recursive:true});
  const temporary=file+'.'+crypto.randomBytes(8).toString('hex')+'.tmp';
  const fd=fs.openSync(temporary,'wx');
  try{fs.writeFileSync(fd,JSON.stringify(value)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  try{fs.linkSync(temporary,file);}finally{fs.unlinkSync(temporary);}
}
class Meter{
  constructor(root,activity){
    this.directory=path.join(root,'runtime/resources/receipts');this.started=process.hrtime.bigint();this.cpu=process.cpuUsage();
    this.record={schema:'beops-resource-cycle/v1',id:crypto.randomBytes(16).toString('hex'),activity,
      started_at:new Date().toISOString(),phase:'start',pid:process.pid,runtime:'node'};
    this.http={request_attempts:0,response_body_bytes:0,body_reports:0,unreported_bodies:0};
    this.calls=[];
    immutable(path.join(this.directory,this.record.id+'-start.json'),this.record);
  }
  providerAttempt(){this.calls.push(null);return this.calls.length-1;}
  providerResponse(index,response){this.calls[index]=tokenUsage(response?.usage);}
  finish(outcome='completed'){
    const delta=process.cpuUsage(this.cpu),tokens={input_tokens:null,output_tokens:null,cached_input_tokens:null,
      reasoning_tokens:null,cache_creation_input_tokens:null,provider_total_tokens:null,
      reported_calls:this.calls.filter(x=>x?.state==='provider_reported').length,
      unreported_calls:this.calls.filter(x=>!x||x.state!=='provider_reported').length,
      state:this.calls.length?'partial_provider_reporting':'no_generation_attempt'};
    for(const key of ['input_tokens','output_tokens','cached_input_tokens','reasoning_tokens','cache_creation_input_tokens','provider_total_tokens']){
      const values=this.calls.map(x=>x?.[key]).filter(x=>x!==null&&x!==undefined);
      if(values.length)tokens[key]=values.reduce((a,b)=>a+b,0);
    }
    const record={...this.record,phase:'finish',finished_at:new Date().toISOString(),outcome,
      wall_seconds:Number(process.hrtime.bigint()-this.started)/1e9,cpu_seconds:(delta.user+delta.system)/1e6,
      peak_rss_bytes:process.resourceUsage().maxRSS*1024,http:this.http,tokens,electricity_wh:null,money:null,
      scope:{cpu:'current Node process only; excludes CLI children, model servers and remote inference',
        memory:'current process lifetime peak RSS; not cycle-only or additive',
        http:'instrumented provider request() attempts; decoded response body bytes; excludes opaque CLI traffic, headers and TLS',
        tokens:'returned generation usage only; unavailable/failed calls and qualification probes can consume unreported tokens; provider field definitions differ; no total inferred',
        electricity:'unavailable; no physical energy meter connected to this recorder',
        meter_overhead:'start receipt included; final receipt write excluded'}};
    immutable(path.join(this.directory,this.record.id+'-finish.json'),record);return record;
  }
}
async function withMeter(root,activity,fn){
  let meter;
  try{meter=new Meter(root,activity);}catch(error){
    if(!error.code)throw error;
    console.error('resource_meter_unavailable:'+error.code);
    return fn({providerAttempt:()=>null,providerResponse:()=>{}});
  }
  let outcome='failed';
  try{return await active.run(meter,async()=>{const result=await fn(meter);outcome=result?.state||'completed';return result;});}
  finally{try{meter.finish(outcome);}catch(error){if(!error.code)throw error;console.error('resource_meter_finish_unavailable:'+error.code);}}
}
function httpAttempt(){const meter=active.getStore();if(meter){meter.http.request_attempts++;meter.http.unreported_bodies++;}return meter;}
function httpBody(meter,bytes){if(meter&&count(bytes)!==null){meter.http.response_body_bytes+=bytes;meter.http.body_reports++;meter.http.unreported_bodies--;}}
module.exports={Meter,withMeter,tokenUsage,httpAttempt,httpBody};
