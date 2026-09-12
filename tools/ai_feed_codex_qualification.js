'use strict';
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto'),{spawn}=require('node:child_process');
// A new menu model qualifies itself against a loopback mock before any paid inference.
// The CLI alone owns authentication; this request uses a dummy provider and no account credential.
async function qualify(executable,q,model,directory){
 const args=[...q.args],slot=args.indexOf('--model');if(slot<0)throw Error('qualification_missing_model');args[slot+1]=model;
 const key=crypto.createHash('sha256').update(JSON.stringify({exe:q.executable_sha256,args})).digest('hex');
 const folder=path.join(directory,'qualifications',key),file=path.join(folder,'result.json');
 if(fs.existsSync(file)){const saved=JSON.parse(fs.readFileSync(file,'utf8'));if(saved.key===key&&saved.model===model)return {...saved,cached:true};}
 fs.mkdirSync(folder,{recursive:true});
 const schema=path.join(folder,'schema.json'),instructions=path.join(folder,'system.txt');
 fs.writeFileSync(schema,JSON.stringify({type:'object',required:['title'],properties:{title:{type:'string'}},additionalProperties:false}));fs.writeFileSync(instructions,'Offline qualification. Return JSON only.');
 const findings=[];
 const server=http.createServer((req,res)=>{const chunks=[];let size=0;req.on('data',b=>{size+=b.length;if(size>1024*1024)req.destroy();else chunks.push(b);});req.on('end',()=>{
   if(req.url.endsWith('/responses')){try{const p=JSON.parse(Buffer.concat(chunks));findings.push({model:p.model,tools:(p.tools||[]).map(t=>({type:t.type,name:t.name}))});}catch{}}
   res.writeHead(400,{'Content-Type':'application/json'}).end('{"error":{"message":"Intentional local capability probe; no inference."}}');
 });});
 try{
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  const base='http://127.0.0.1:'+server.address().port+'/v1';
  const probe=[...args,'-c','model_instructions_file='+JSON.stringify(instructions),'--output-schema',schema,'-c','model_provider="beops_probe"','-c','model_providers.beops_probe.name="Offline qualification"','-c','model_providers.beops_probe.base_url='+JSON.stringify(base),'-c','model_providers.beops_probe.wire_api="responses"','-c','model_providers.beops_probe.env_key="BEOPS_PROBE_TOKEN"','-c','model_providers.beops_probe.requires_openai_auth=false','-c','model_providers.beops_probe.request_max_retries=0','-c','model_providers.beops_probe.stream_max_retries=0','-'];
  await new Promise(resolve=>{const child=spawn(executable,probe,{cwd:folder,windowsHide:true,stdio:['pipe','pipe','pipe'],env:{...process.env,BEOPS_PROBE_TOKEN:'offline-not-a-secret',OTEL_SDK_DISABLED:'true'}});const timer=setTimeout(()=>child.kill(),20000);child.stdout.on('data',()=>{});child.stderr.on('data',()=>{});child.stdin.on('error',()=>{});child.once('error',()=>{clearTimeout(timer);resolve();});child.once('close',()=>{clearTimeout(timer);resolve();});child.stdin.end('Return a JSON title, without tools.');});
  const result={schema:'beops-cli-model-qualification/v1',key,model,at:new Date().toISOString(),ok:findings.length>0&&findings.every(f=>f.model===model&&f.tools.length===0),findings};
  // Inconclusive probes are retried on a later tick; a measured tool set is bound to the binary+args.
  if(findings.length){const temp=file+'.'+process.pid+'.tmp';fs.writeFileSync(temp,JSON.stringify(result));fs.renameSync(temp,file);}
  return result;
 }finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
}
module.exports={qualify};
