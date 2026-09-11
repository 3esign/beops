'use strict';
// Serve the generated observatory only. The old prototype is available as start:legacy.
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const mirror=path.resolve(__dirname,'../../Beops-public');
let root=path.resolve(__dirname,'../docs');
try{const owner=JSON.parse(fs.readFileSync(path.join(mirror,'.git/beops-export-owner.json'),'utf8').replace(/^\uFEFF/,''));if(owner.schema==='beops-public-owner/v1'&&owner.path.toLowerCase()===fs.realpathSync(mirror).toLowerCase()&&owner.remote==='https://github.com/3esign/beops.git'&&fs.existsSync(path.join(mirror,'docs/index.html')))root=path.join(mirror,'docs');}catch{}
const types={'.html':'text/html; charset=utf-8','.json':'application/json; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.pdf':'application/pdf'};
const server=http.createServer((req,res)=>{
 let name;try{name=decodeURIComponent(new URL(req.url,'http://localhost').pathname);}catch{res.writeHead(400).end();return;}
 if(!['GET','HEAD'].includes(req.method)){res.writeHead(405).end();return;}
 const file=path.resolve(root,'.'+(name.endsWith('/')?name+'index.html':name));
 const rel=path.relative(root,file);if(rel.startsWith('..')||path.isAbsolute(rel)||rel.split(path.sep).some(x=>x.startsWith('.'))){res.writeHead(403).end();return;}
 try{const real=fs.realpathSync(file);if(!real.startsWith(fs.realpathSync(root)+path.sep)||!fs.statSync(real).isFile())throw Error();res.writeHead(200,{'Content-Type':types[path.extname(real)]||'application/octet-stream','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'none'"});if(req.method==='HEAD')res.end();else fs.createReadStream(real).pipe(res);}catch{res.writeHead(404,{'Content-Type':'text/plain; charset=utf-8'}).end('Not generated or unavailable. Build the site first.');}
});
server.listen(Number(process.env.BEOPS_PORT||0),'127.0.0.1',()=>process.stdout.write(JSON.stringify({url:`http://127.0.0.1:${server.address().port}/`,root})+'\n'));
