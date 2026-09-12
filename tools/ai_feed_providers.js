'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {spawn}=require('node:child_process');
const crypto=require('node:crypto');
const svemirRoot=()=>process.env.BEOPS_SVEMIR_ROOT||'C:/Svemir';
function persona(url){return require(path.join(svemirRoot(),'lib/incognito.js')).headers(url);}
async function request(url,body,headers={},timeout=110000){
  const r=await fetch(url,{method:body?'POST':'GET',headers:{...persona(url),'Content-Type':'application/json',...headers},
    body:body?JSON.stringify(body):undefined,redirect:'error',signal:AbortSignal.timeout(timeout)});
  const reader=r.body.getReader();let size=0;const chunks=[];
  while(true){const x=await reader.read();if(x.done)break;size+=x.value.length;if(size>1024*1024){await reader.cancel();throw Error('provider_response_too_large');}chunks.push(Buffer.from(x.value));}
  if(!r.ok) throw Error('provider_http_'+r.status); // Never log auth headers or full error bodies.
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}
function ollamaBase(){
  const url=new URL(process.env.BEOPS_OLLAMA||'http://127.0.0.1:11434');
  if(url.protocol!=='http:' || !['127.0.0.1','localhost','[::1]'].includes(url.hostname) || url.username || url.password || url.pathname!=='/') throw Error('ollama_must_be_loopback');
  return url.origin;
}
function claudeExecutable(){return path.join(os.homedir(),'.local','bin',process.platform==='win32'?'claude.exe':'claude');}
function codexExecutable(){return path.join(os.homedir(),'AppData/Roaming/npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe');}
function codexQualification(){
  const q=JSON.parse(fs.readFileSync(path.join(__dirname,'../research/AI_FEED_CODEX_QUALIFICATION.json'),'utf8'));
  const digest=crypto.createHash('sha256').update(fs.readFileSync(codexExecutable())).digest('hex');
  if(q.schema!=='beops-codex-qualification/v1'||q.request_tools?.length!==0||digest!==q.executable_sha256)throw Error('cli_qualification_required');
  return q;
}
async function availability(provider){
  if(provider.adapter==='codex-cli'){
    try{
      const q=codexQualification();
      if(q.model!==provider.model)return {ready:false,reason:'model_qualification_required'};
      const row=require(path.join(svemirRoot(),'lib/cli_bridge.js')).chatModels({includeUnavailable:true}).find(m=>m.device==='pc'&&m.bridge==='codex'&&m.model===provider.model);
      return row?.runnable?{ready:true,model:provider.model}:{ready:false,reason:row?.status||'not_in_svemir_catalogue'};
    }catch{return {ready:false,reason:'cli_qualification_required'};}
  }
  if(provider.adapter==='ollama'){
    try{const d=await request(ollamaBase()+'/api/tags',null,{},5000);const names=new Set((d.models||[]).map(m=>m.name));
      const model=provider.models.find(m=>names.has(m));return model?{ready:true,model}:{ready:false,reason:'no_configured_model'};
    }catch{return {ready:false,reason:'ollama_unavailable'};}
  }
  if(provider.adapter==='claude-cli'){
    if(!fs.existsSync(claudeExecutable())) return {ready:false,reason:'cli_missing'};
    try{
      const catalogue=require(path.join(svemirRoot(),'lib/cli_bridge.js')).chatModels({includeUnavailable:true});
      const row=catalogue.find(m=>m.device==='pc'&&m.bridge==='claude'&&m.model===provider.model);
      if(!row?.runnable) return {ready:false,reason:row?.status||'not_in_svemir_catalogue'};
      return {ready:true,model:provider.model};
    }catch{return {ready:false,reason:'catalogue_unavailable'};}
  }
  return process.env[provider.key_env]?{ready:true,model:provider.model}:{ready:false,reason:'api_credentials_unavailable'};
}
function parseObject(text){
  const t=String(text||'').trim().replace(/^```(?:json)?\s*/,'').replace(/\s*```$/,'');
  return JSON.parse(t);
}
function claude(prompt,system,model,cwd,timeout){
  return new Promise((resolve,reject)=>{
    // Safe mode preserves CLI-owned authentication but disables user customisations/hooks/plugins.
    const args=['-p','--safe-mode','--setting-sources','','--tools','','--strict-mcp-config',
      '--mcp-config','{"mcpServers":{}}','--disable-slash-commands','--no-session-persistence',
      '--output-format','stream-json','--verbose','--model',model,'--system-prompt',system];
    const child=spawn(claudeExecutable(),args,{cwd,windowsHide:true,stdio:['pipe','pipe','pipe'],
      env:{...process.env,CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC:'1'}});
    let out='',count=0,closed=false,violation=false,toolsetSeen=false,result=null;
    const timer=setTimeout(()=>{child.kill();},timeout);
    child.stdout.setEncoding('utf8');child.stdin.on('error',()=>{});
    child.stdout.on('data',b=>{
      count+=b.length;if(count>1024*1024){violation=true;child.kill();return;}
      out+=b.toString('utf8');let at;
      while((at=out.indexOf('\n'))>=0){const line=out.slice(0,at);out=out.slice(at+1);let e;try{e=JSON.parse(line);}catch{continue;}
        if(e.type==='system'&&e.subtype==='init'){toolsetSeen=true;if((e.tools||[]).length){violation=true;child.kill();}}
        if(e.message?.content?.some(c=>c.type==='tool_use')){violation=true;child.kill();}
        if(e.type==='result') result=e;
      }
    });
    child.stderr.on('data',()=>{});
    child.on('error',e=>{clearTimeout(timer);reject(Error('cli_start_'+e.code));});
    child.on('close',code=>{if(closed)return;closed=true;clearTimeout(timer);
      if(violation || !toolsetSeen) return reject(Error('cli_tool_isolation_unverified'));
      if(code!==0 || !result || result.is_error) return reject(Error('cli_failed_or_timed_out'));
      resolve({text:result.result,model,identity:'requested_alias',usage:result.usage||null,transport:'Claude CLI; built-in and MCP tools disabled',tools:[]});
    });
    child.stdin.end(prompt);
  });
}
function codex(prompt,system,model,cwd,timeout){
  const q=codexQualification();
  if(q.model!==model)throw Error('model_qualification_required');
  fs.writeFileSync(path.join(cwd,'observer-system.txt'),system);
  const schema={type:'object',additionalProperties:false,required:['title','paragraphs','question','limitations'],properties:{title:{type:'string'},paragraphs:{type:'array',items:{type:'object',additionalProperties:false,required:['text','cites'],properties:{text:{type:'string'},cites:{type:'array',items:{type:'string'}}}}},question:{type:'string'},limitations:{type:'string'}}};
  fs.writeFileSync(path.join(cwd,'observer-schema.json'),JSON.stringify(schema));
  return new Promise((resolve,reject)=>{
    const args=[...q.args,'-c','model_instructions_file='+JSON.stringify(path.join(cwd,'observer-system.txt')),'--output-schema',path.join(cwd,'observer-schema.json'),'-'];
    const child=spawn(codexExecutable(),args,{cwd,windowsHide:true,stdio:['pipe','pipe','pipe'],env:{...process.env,OTEL_SDK_DISABLED:'true'}});
    let out='',bytes=0,text='',usage=null,violation=false,completed=false,timedOut=false;
    const timer=setTimeout(()=>{timedOut=true;child.kill();},timeout);
    child.stdout.setEncoding('utf8');child.stdin.on('error',()=>{});
    child.stdout.on('data',chunk=>{
      bytes+=Buffer.byteLength(chunk);if(bytes>1024*1024){violation=true;child.kill();return;}out+=chunk;
      let at;while((at=out.indexOf('\n'))>=0){const line=out.slice(0,at);out=out.slice(at+1);let e;try{e=JSON.parse(line);}catch{continue;}
        if(e.item&&['command_execution','mcp_tool_call','web_search','file_change','collab_tool_call'].includes(e.item.type)){violation=true;child.kill();}
        if(e.type==='item.completed'&&e.item?.type==='agent_message')text=e.item.text||'';
        if(e.type==='turn.completed'){completed=true;usage=e.usage||null;}
      }
    });
    child.stderr.on('data',()=>{});
    child.on('error',e=>{clearTimeout(timer);reject(Error('cli_start_'+e.code));});
    child.on('close',code=>{clearTimeout(timer);
      if(violation)return reject(Error('cli_unexpected_tool_or_large_output'));
      if(code!==0||!completed||!text)return reject(Error(timedOut?'cli_timed_out':'cli_failed'));
      resolve({text,model,identity:'requested_alias',usage,transport:'Codex CLI; pinned executable qualified with empty tools',tools:[],qualification:q.executable_sha256});
    });
    child.stdin.end(prompt);
  });
}
async function generate(provider,model,packet,system,cwd,timeout=110000){
  const deadline=Date.now()+timeout;
  const prompt='Write your monologue about this frozen situation. Data packet:\n'+JSON.stringify(packet);
  if(provider.adapter==='codex-cli')return codex(prompt,system,model,cwd,timeout);
  if(provider.adapter==='ollama'){
    const mutex=require(path.join(svemirRoot(),'lib/mind_lock.js'));
    return mutex.withLock('ollama',async()=>{
      const meta=await request(ollamaBase()+'/api/show',{model},{},Math.min(timeout,10000));
      const remote=Boolean(meta.remote_host||meta.remote_model||meta.remote_url||model.includes('cloud'));
      if(remote&&!provider.allow_remote) throw Error('remote_model_not_allowed');
      const schema={type:'object',additionalProperties:false,required:['title','paragraphs','question','limitations'],properties:{
        title:{type:'string'},paragraphs:{type:'array',minItems:1,maxItems:3,items:{type:'object',additionalProperties:false,required:['text','cites'],properties:{text:{type:'string'},cites:{type:'array',minItems:1,maxItems:4,items:{type:'string',enum:packet.facts.map(f=>f.id)}}}}},question:{type:'string'},limitations:{type:'string'}}};
      const d=await request(ollamaBase()+'/api/chat',{model,stream:false,think:false,format:schema,
        messages:[{role:'system',content:system},{role:'user',content:prompt}],
        options:{temperature:0.6,num_predict:800,num_ctx:4096},keep_alive:remote?undefined:'0s'}, {},Math.max(1,deadline-Date.now()));
      if(d.message?.tool_calls?.length) throw Error('unexpected_tool_call');
      return {text:d.message?.content,model:d.model||model,identity:d.model?'provider_reported':'requested',
        usage:{input_tokens:d.prompt_eval_count??null,output_tokens:d.eval_count??null},
        transport:remote?'Ollama broker / remote inference':'Ollama / local inference',tools:[]};
    },{mind:'beops-ai-feed-'+process.pid,waitMs:10000,ttlSec:180});
  }
  if(provider.adapter==='claude-cli') return claude(prompt,system,model,cwd,timeout);
  if(provider.adapter==='openai'){
    const d=await request('https://api.openai.com/v1/responses',{model,instructions:system,input:prompt,
      tools:[],tool_choice:'none',store:false,max_output_tokens:1400},{Authorization:'Bearer '+process.env[provider.key_env]},timeout);
    if((d.output||[]).some(x=>x.type!=='message'&&x.type!=='reasoning')) throw Error('unexpected_tool_call');
    return {text:(d.output||[]).flatMap(x=>x.content||[]).filter(x=>x.type==='output_text').map(x=>x.text).join(''),
      model:d.model||model,identity:'provider_reported',usage:d.usage||null,transport:'OpenAI Responses API; tools disabled',tools:[]};
  }
  if(provider.adapter==='gemini'){
    const d=await request('https://generativelanguage.googleapis.com/v1beta/models/'+encodeURIComponent(model)+':generateContent',
      {systemInstruction:{parts:[{text:system}]},contents:[{role:'user',parts:[{text:prompt}]}],
        generationConfig:{responseMimeType:'application/json',maxOutputTokens:1400}}, {'x-goog-api-key':process.env[provider.key_env]},timeout);
    const parts=d.candidates?.[0]?.content?.parts||[];
    if(parts.some(p=>p.functionCall)) throw Error('unexpected_tool_call');
    return {text:parts.filter(p=>p.text&&!p.thought).map(p=>p.text).join(''),model:d.modelVersion||model,
      identity:d.modelVersion?'provider_reported':'requested',usage:d.usageMetadata||null,transport:'Gemini API; no tools supplied',tools:[]};
  }
  throw Error('unsupported_adapter');
}
module.exports={availability,generate,parseObject,request,ollamaBase};
