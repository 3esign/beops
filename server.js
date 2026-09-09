'use strict';
const http=require('node:http'), fs=require('node:fs/promises'), path=require('node:path');
const {Store}=require('./src/store'), {CITIES}=require('./src/evidence'), model=require('./src/model');
const ROOT=__dirname;
async function start(port=Number(process.env.PORT||5092),root=process.env.BEOPS_DATA||path.join(ROOT,'runtime')) {
  const store=await new Store(root).init();let timer;
  const assets={'/':['public/index.html','text/html; charset=utf-8'],'/app.js':['public/app.js','text/javascript; charset=utf-8'],
    '/style.css':['public/style.css','text/css; charset=utf-8'],'/map.json':['public/map.json','application/json']};
  const server=http.createServer(async(req,res)=>{
    const json=(code,value)=>{res.writeHead(code,{'content-type':'application/json; charset=utf-8'});res.end(JSON.stringify(value));};
    res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');
    res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
    try {
      const host=req.headers.host;
      if(!host||!/^127\.0\.0\.1:\d+$/.test(host))return json(403,{error:'Loopback host required'});
      const origin='http://'+host,url=new URL(req.url,origin);
      if(req.headers.origin&&req.headers.origin!==origin)return json(403,{error:'Cross-origin access refused'});
      if(req.headers['sec-fetch-site']==='cross-site')return json(403,{error:'Cross-site access refused'});
      if(req.method==='GET'&&url.pathname==='/api/state')return json(200,{...store.snapshot(),cities:CITIES});
      if(req.method==='GET'&&url.pathname==='/api/health')return json(200,{ok:true,project:'Beops',version:'0.1.0',pid:process.pid});
      if(req.method==='GET'&&url.pathname==='/api/models')return json(200,await model.inventory().catch(error=>({installed:false,error:error.message})));
      if(req.method==='GET'&&url.pathname==='/api/export'){res.setHeader('Content-Disposition','attachment; filename="beops-evidence.json"');return json(200,{...store.snapshot(),cities:CITIES});}
      if(req.method==='POST'&&url.pathname==='/api/refresh')return json(200,await store.refresh());
      if(req.method==='POST'&&url.pathname==='/api/select'){
        const chunks=[];let size=0;for await(const part of req){size+=part.length;if(size>4096)return json(413,{error:'Payload too large'});chunks.push(part);}
        let input;try{input=JSON.parse(Buffer.concat(chunks).toString());}catch{return json(400,{error:'Invalid JSON'});}
        return json(200,await model.select(input.question,store.snapshot().observations.filter(r=>r.city===input.city),store));
      }
      if(req.method==='GET'&&assets[url.pathname]){const [file,type]=assets[url.pathname];const bytes=await fs.readFile(path.join(ROOT,file));res.writeHead(200,{'content-type':type});return res.end(bytes);}
      return json(404,{error:'Not found'});
    } catch(error){return json(503,{error:error.message});}
  });
  server.headersTimeout=10000;server.requestTimeout=110000;
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});
  if(process.env.BEOPS_NO_REFRESH!=='1'){
    store.refresh().catch(error=>console.error('refresh:',error.message));
    timer=setInterval(()=>store.refresh().catch(error=>console.error('refresh:',error.message)),15*60000);timer.unref();
  }
  server.on('close',()=>clearInterval(timer));return {server,store};
}
if(require.main===module)start().then(({server})=>console.log('BEOPS http://127.0.0.1:'+server.address().port)).catch(error=>{console.error(error);process.exitCode=1;});
module.exports={start};
