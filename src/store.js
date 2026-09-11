'use strict';
const fs=require('node:fs/promises'), path=require('node:path');
const {sources,hash,normalize,viewRecord}=require('./evidence');
async function boundedJSON(url, options={}) {
  const providers=[process.env.BEOPS_INCOGNITO,'C:/Svemir/lib/incognito.js','D:/Svemir/lib/incognito.js'].filter(Boolean);
  const provider=providers.find(p=>require('node:fs').existsSync(p));
  if(!provider)throw new Error('Incognito HTTP provider is unavailable');
  const headers=require(provider).headers(url,{vrsta:'json'});
  const response=await fetch(url,{...options,headers,redirect:'error',signal:options.signal||AbortSignal.timeout(12000)});
  if (!response.ok) throw new Error(`Source HTTP ${response.status}`);
  const reader=response.body.getReader(), chunks=[]; let count=0;
  try {while(true){const {done,value}=await reader.read();if(done)break;count+=value.length;if(count>(options.maxBytes||1048576))throw new Error('Response size limit');chunks.push(Buffer.from(value));}}
  finally {await reader.cancel().catch(()=>{});}
  const bytes=Buffer.concat(chunks);return {bytes,value:JSON.parse(bytes.toString('utf8'))};
}
class Store {
  constructor(root, fetcher=boundedJSON) {this.root=root;this.fetcher=fetcher;this.state={version:1,sources:[],observations:[],timelines:{},updated:null};this.inFlight=null;this.nextAttempt=0;this.lastEvent=null;}
  async init() {
    await fs.mkdir(path.join(this.root,'raw'),{recursive:true});
    try {const value=JSON.parse(await fs.readFile(path.join(this.root,'state.json'),'utf8'));if(value.version!==1||!Array.isArray(value.observations)||!Array.isArray(value.sources))throw new Error('Invalid saved state');this.state=value;}
    catch(error){if(error.code!=='ENOENT')throw error;}
    return this;
  }
  snapshot(){return {...this.state,observations:this.state.observations.map(r=>viewRecord(r,this.state.sources.find(s=>s.id===r.source))),refreshing:!!this.inFlight,nextAttempt:this.nextAttempt};}
  async event(kind,data){const event={id:require('node:crypto').randomUUID(),at:new Date().toISOString(),kind,...data};await fs.appendFile(path.join(this.root,'events.jsonl'),JSON.stringify(event)+'\n');this.lastEvent=event;return event;}
  async refresh() {
    if(this.inFlight)return this.inFlight;
    if(Date.now()<this.nextAttempt)return this.snapshot();
    this.nextAttempt=Date.now()+10*60000;
    this.inFlight=this.collect().finally(()=>{this.inFlight=null;});return this.inFlight;
  }
  async collect() {
    for(const source of sources()) {
      const retrievedAt=new Date().toISOString();
      let status;
      try {
        const {bytes,value}=await this.fetcher(source.url);const digest=hash(bytes);
        const result=normalize(source,value,retrievedAt,digest);
        const target=path.join(this.root,'raw',digest+'.json');
        try{await fs.writeFile(target,bytes,{flag:'wx'});}catch(e){if(e.code!=='EEXIST')throw e;if(hash(await fs.readFile(target))!==digest)throw new Error('Existing raw object is corrupt');}
        await this.event('source.accepted',{source:source.id,contentHash:digest,retrievedAt,records:result.observations.length});
        this.state.observations=this.state.observations.filter(r=>r.source!==source.id).concat(result.observations);
        this.state.timelines[source.id]=result.timeline;
        status={...source,status:'ok',retrievedAt,contentHash:digest,error:null};
      } catch(error) {
        status={...source,status:'error',attemptedAt:retrievedAt,error:error.message};
        await this.event('source.failed',{source:source.id,error:error.message});
      }
      this.state.sources=this.state.sources.filter(s=>s.id!==source.id).concat(status);
    }
    this.state.updated=new Date().toISOString();
    const temp=path.join(this.root,'state.json.tmp');
    await fs.writeFile(temp,JSON.stringify(this.state,null,2));await fs.rename(temp,path.join(this.root,'state.json'));
    return this.snapshot();
  }
}
module.exports={Store,boundedJSON};
