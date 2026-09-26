"""Large public histories verify under the scheduled publisher's 128 MiB heap."""
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERIFIER = ROOT / 'tools/verify_public_site.js'


class StreamedPublicVerification(unittest.TestCase):
    def run_node(self, script, timeout=90):
        with tempfile.TemporaryDirectory() as folder:
            runner = pathlib.Path(folder) / 'regression.cjs'
            runner.write_text(script, encoding='utf-8')
            result = subprocess.run(
                ['node', '--max-old-space-size=128', str(runner), str(VERIFIER)],
                capture_output=True, text=True, timeout=timeout)
            self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-10000:])

    def test_real_large_route_and_complete_cli_verification_fit_128_mib(self):
        self.run_node(r'''
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), http = require('node:http');
const {spawn} = require('node:child_process');
const base = __dirname, docs = path.join(base, 'public/docs');
fs.mkdirSync(docs, {recursive:true});
fs.mkdirSync(path.join(base,'lib'));
fs.writeFileSync(path.join(base,'lib/incognito.js'), 'exports.headers = () => ({});');
process.env.SVEMIR_ROOT = base;
const {inspectLocalRoute, fetchDigest, fetchMatchingRoute, validateGeneration} = require(process.argv[2]);
const id = 'a'.repeat(64), asOf = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
const generation = {id, schema:'beops-input-generation/v1', observation_prefix:'complete-lf-lines/v1', captured_at:asOf};
const html = '<meta name="beops-input-generation" content="'+id+'">Beograd danas BEOPS local AI infrastructure '+
  'Ovo je ono sto nam je Beograd rekao <a href="#izvori">sources</a><a href="#greske">corrections</a>';
const routes = ['index.html','instrument.html','events.json','mapa.html','mapa.js','MAP_LAYERS.json',
  'materija.json','ai-feed.html','ai-feed/latest.json','kontekst.html','context-catalog.json','podaci.html',
  'monolog.html','sada.html','traka.html','svedoci.html','obrasci.html','city-overview.json','city-analysis.json',
  'beops-view.js','live-snapshot.json','history.json','watch.json','latency.json','agreement.json','basemap-belgrade.json'];
for (const rel of routes) {
  const file=path.join(docs,rel); fs.mkdirSync(path.dirname(file),{recursive:true});
  fs.writeFileSync(file, rel.endsWith('.html') ? html : JSON.stringify({as_of:asOf,input_generation:generation,edition:{input_generation:generation}}));
}
const history = path.join(docs,'history.json'), fd=fs.openSync(history,'w');
fs.writeSync(fd,'{"nested":{"as_of":"wrong","input_generation":{"id":"decoy"}},"payload":"');
const chunk=Buffer.alloc(64*1024,120);
for(let i=0;i<1120;i++)fs.writeSync(fd,chunk);
fs.writeSync(fd,'","as_of":'+JSON.stringify(asOf)+',"input_generation":'+JSON.stringify(generation)+'}');
fs.closeSync(fd);
fs.writeFileSync(path.join(docs,'export-manifest.json'),JSON.stringify({inputs_manifest_sha256:id,
  generated_as_of:asOf,files:routes.map(rel=>({path:'docs/'+rel}))}));
const memoryFile=path.join(base,'memory.json'), hook=path.join(base,'heap.cjs');
fs.writeFileSync(hook,`let peak=0; const timer=setInterval(()=>{peak=Math.max(peak,process.memoryUsage().heapUsed)},10);timer.unref();process.on('exit',()=>require('node:fs').writeFileSync(${JSON.stringify(memoryFile)},JSON.stringify({peak})));`);
const server=http.createServer((req,res)=>{
  const rel=new URL(req.url,'http://localhost').pathname.slice(1)||'index.html';
  if(rel==='redirect'){res.writeHead(302,{location:'/history.json'});res.end();return;}
  const file=path.join(docs,rel);if(!fs.existsSync(file)){res.writeHead(404);res.end('missing');return;}
  res.setHeader('Content-Length',fs.statSync(file).size);fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const url='http://127.0.0.1:'+server.address().port+'/';
  const local=await inspectLocalRoute(history,'history.json');
  assert.ok(local.bytes>64*1024*1024);assert.equal(local.text,undefined);
  assert.equal(validateGeneration('history.json',local.metadata,id,asOf),id);
  const remote=await fetchMatchingRoute(url+'redirect',local.hash,Date.now()+30000,
   {get:u=>fetchDigest(u,local.bytes,Date.now()+30000)});
  assert.equal(remote.hash,local.hash);assert.equal(remote.byteLength,local.bytes);
  assert.equal(remote.bytes,undefined);assert.equal(remote.text,undefined);
  const child=spawn(process.execPath,['--max-old-space-size=128','--require',hook,process.argv[2]],
   {env:{...process.env,BEOPS_PUBLIC_ROOT:path.dirname(docs),BEOPS_SITE_URL:url,
    BEOPS_SITE_WAIT_SECONDS:'40',BEOPS_SITE_POLL_MS:'1',BEOPS_CHECK_RAW:'0'},windowsHide:true});
  let out='',err='';child.stdout.on('data',c=>out+=c);child.stderr.on('data',c=>err+=c);
  const code=await new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',resolve)});
  assert.equal(code,0,err+'\n'+out);
  const summary=JSON.parse(out);assert.equal(summary.operational_verdict,'CURRENT_AND_VERIFIED');
  const route=summary.routes.find(r=>r.route==='history.json');
  assert.equal(route.match,true);assert.equal(route.input_generation,id);assert.equal(route.bytes,local.bytes);
  const memory=JSON.parse(fs.readFileSync(memoryFile));assert.ok(memory.peak<96*1024*1024,JSON.stringify(memory));
 }finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exitCode=1;});
''')

    def test_metadata_cannot_be_supplied_by_nested_or_quoted_keys(self):
        self.run_node(r'''
const assert=require('node:assert/strict');
const {metadataReader,validateGeneration}=require(process.argv[2]);
const id='a'.repeat(64),asOf='2026-09-26T22:00:00Z';
const gen={id,schema:'beops-input-generation/v1',observation_prefix:'complete-lf-lines/v1',captured_at:asOf};
function read(raw){const parser=metadataReader();for(const char of raw)parser.write(char);return parser.finish();}
const decoys={nested:{as_of:asOf,input_generation:gen},quote:'\\"as_of\\":'+asOf};
assert.throws(()=>validateGeneration('history.json',read(JSON.stringify(decoys)),id,asOf),/generation differs/);
const real=read(JSON.stringify({...decoys,as_of:asOf,input_generation:gen}));
assert.equal(validateGeneration('history.json',real,id,asOf),id);
const city=read(JSON.stringify({as_of:asOf,edition:{nested:{input_generation:gen}}}));
assert.throws(()=>validateGeneration('city-overview.json',city,id,asOf),/generation differs/);
assert.equal(validateGeneration('city-overview.json',read(JSON.stringify({as_of:asOf,edition:{input_generation:gen}})),id,asOf),id);
assert.throws(()=>read('{"as_of":"x","as_\\u006ff":"y"}'),/Duplicate/);
assert.throws(()=>read('{"as_of":"x",}'),/metadata key/);
assert.throws(()=>read('{"as_of":"x"'),/Incomplete/);
assert.throws(()=>read('{"input_generation":"'+'x'.repeat(270000)+'"}'),/bounded size/);
''', timeout=15)

    def test_transport_keeps_byte_deadline_and_redirect_guards(self):
        self.run_node(r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
fs.mkdirSync(path.join(__dirname,'lib'));fs.writeFileSync(path.join(__dirname,'lib/incognito.js'),'exports.headers=()=>({});');
process.env.SVEMIR_ROOT=__dirname;
const {fetchDigest}=require(process.argv[2]);
const server=http.createServer((req,res)=>{
 const route=new URL(req.url,'http://localhost').pathname;
 if(route==='/loop'){res.writeHead(302,{location:'/loop'});res.end();return;}
 if(route==='/protocol'){res.writeHead(302,{location:'file:///untrusted'});res.end();return;}
 if(route==='/slow'){res.write('x');const timer=setInterval(()=>res.write('x'),5);res.on('close',()=>clearInterval(timer));return;}
 if(route==='/truncated'){res.writeHead(200,{'Content-Length':'10000'});res.end('short');return;}
 res.end('x'.repeat(1024));
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const url='http://127.0.0.1:'+server.address().port;
  await assert.rejects(fetchDigest(url,10,Date.now()+5000),/byte limit/);
  await assert.rejects(fetchDigest(url+'/loop',1024,Date.now()+5000),/too many/);
  await assert.rejects(fetchDigest(url+'/protocol',1024,Date.now()+5000),/unsupported protocol/);
  await assert.rejects(fetchDigest(url+'/slow',1024*1024,Date.now()+150),/deadline/);
  await assert.rejects(fetchDigest(url+'/truncated',10000,Date.now()+300),/before completion|deadline/);
 }finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exitCode=1;});
''', timeout=15)


if __name__ == '__main__':
    unittest.main()
