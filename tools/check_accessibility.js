'use strict';
// Real browser verification of the generated site. No request leaves loopback.
const fs=require('node:fs'), path=require('node:path'), http=require('node:http');
const {chromium}=require(process.env.BEOPS_PLAYWRIGHT || path.join(process.env.USERPROFILE || process.env.HOME,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'));
const root=path.resolve(process.argv[2]||'docs'), out=path.resolve(process.argv[3]||'runtime/accessibility');
fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
  fs.readFile(file,(err,data)=>{if(err){res.writeHead(404).end();return;}res.setHeader('Content-Type',(types[path.extname(file)]||'application/octet-stream')+'; charset=utf-8');res.end(data);});
});
async function main(){
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const base='http://127.0.0.1:'+server.address().port;
  const browser=await chromium.launch({channel:'msedge',headless:true,args:['--disable-background-networking']});
  const results=[], functional=[];
  try{
    for(const theme of (process.env.BEOPS_A11Y_THEMES||'light').split(','))for(const width of (process.env.BEOPS_A11Y_WIDTHS||'390,1440').split(',').map(Number))for(const route of (process.env.BEOPS_A11Y_ROUTES||'index.html,naslovi.html,podaci.html,monolog.html,sada.html,traka.html,svedoci.html').split(',')){
      const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce',colorScheme:theme});
      await context.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());
      const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
      if(route==='traka.html')await page.addInitScript(()=>{
        const proto=CanvasRenderingContext2D.prototype,clear=proto.clearRect,fill=proto.fillText;
        proto.clearRect=function(...args){if(this.canvas.closest?.('.axis'))this.canvas.__beopsAxisLabels=[];return clear.apply(this,args);};
        proto.fillText=function(s,x,y,...rest){if(this.canvas.closest?.('.axis'))(this.canvas.__beopsAxisLabels ||= []).push({text:s,left:x,right:x+this.measureText(s).width});return fill.call(this,s,x,y,...rest);};
      });
      await page.goto(base+'/'+route,{waitUntil:'networkidle'});
      if(route==='naslovi.html')await page.waitForFunction(()=>document.getElementById('items').getAttribute('aria-busy')==='false');
      const dom=await page.evaluate(()=>{
        function rgba(s){if(s.startsWith('color(srgb')){const n=s.match(/[\d.]+/g).map(Number);return [n[0]*255,n[1]*255,n[2]*255,n[3]??1];}const a=s.match(/[\d.]+/g)?.map(Number)||[0,0,0,0];return [a[0],a[1],a[2],a[3]??1];}
        function over(a,b){return a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3])).concat(1);}
        function lum(c){return c.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}).reduce((n,v,i)=>n+v*[.2126,.7152,.0722][i],0);}
        const seen=new Set(), low=[], unsupported=[];let examined=0;
        for(const e of document.body.querySelectorAll('*')){
          if(![...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))continue;
          const r=e.getBoundingClientRect(),s=getComputedStyle(e);
          if(r.width<=1||r.height<=1||s.visibility!=='visible'||s.display==='none'||!e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))continue;
          const ancestors=[];let opacity=1;for(let n=e;n;n=n.parentElement){ancestors.unshift(n);opacity*=Number(getComputedStyle(n).opacity);}
          if(ancestors.some(n=>getComputedStyle(n).backgroundImage!=='none')){unsupported.push(e.tagName);continue;}
          let bg=[255,255,255,1];for(const n of ancestors)bg=over(rgba(getComputedStyle(n).backgroundColor),bg);
          const fg=rgba(s.color);fg[3]*=opacity;const a=lum(over(fg,bg)),b=lum(bg),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
          const large=parseFloat(s.fontSize)>=24||(parseFloat(s.fontSize)>=18.66&&parseInt(s.fontWeight)>=700),min=large?3:4.5;
          examined++;const key=[s.color,s.backgroundColor,s.fontSize,s.fontWeight,e.className].join('|');
          if(ratio+.02<min&&!seen.has(key)){seen.add(key);low.push({tag:e.tagName,class:String(e.className),text:e.textContent.trim().slice(0,80),ratio:+ratio.toFixed(2),minimum:min,color:s.color,opacity,parents:ancestors.slice(-4).map(n=>({tag:n.tagName,class:String(n.className),color:getComputedStyle(n).color,opacity:getComputedStyle(n).opacity}))});}
        }
        return {lang:document.documentElement.lang,main:!!document.querySelector('main,[role=main]'),overflow:document.documentElement.scrollWidth>innerWidth+1,overflowElements:[...document.body.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>innerWidth+1 || e.scrollWidth>e.clientWidth+1).slice(0,8).map(e=>({tag:e.tagName,class:String(e.className),right:e.getBoundingClientRect().right,width:e.clientWidth,scrollWidth:e.scrollWidth,text:e.textContent.slice(0,60)})),examined,lowContrast:low,complexBackgrounds:unsupported.length,tables:document.querySelectorAll('table').length,tablesWithoutCaption:[...document.querySelectorAll('table')].filter(t=>!t.caption).length,unnamedCanvas:[...document.querySelectorAll('canvas')].filter(c=>!c.getAttribute('aria-label')).length};
      });
      const cdp=await context.newCDPSession(page),ax=await cdp.send('Accessibility.getFullAXTree');
      const controls=ax.nodes.filter(n=>!n.ignored&&['button','combobox','searchbox','textbox','slider','separator'].includes(n.role?.value));
      const unnamed=controls.filter(n=>!n.name?.value).map(n=>n.role.value);
      if(route==='traka.html'){
        const axis=await page.evaluate(()=>{
          const cv=document.querySelector('.axis canvas'),labels=cv?.__beopsAxisLabels;
          if(!labels?.length)return {axisAvailable:false};
          return {axisAvailable:true,labels,axisOverlap:labels.some((p,i)=>i&&p.left<labels[i-1].right+7.9),axisOutOfBounds:labels.some(p=>p.left<0||p.right>cv.clientWidth)};
        });
        functional.push({check:'time axis legibility',width,theme,...axis});
      }
      await page.keyboard.press('Tab');const firstFocus=await page.locator(':focus').textContent().catch(()=>null);
      await page.locator(':focus').evaluate(e=>e.blur()).catch(()=>{});
      await page.screenshot({path:path.join(out,route.replace('.html','')+'-'+width+'-'+theme+'.png')});
      results.push({route,width,theme,...dom,unnamedControls:unnamed,firstFocus,errors});
      if(route==='naslovi.html'&&width===390){
        const all=await page.locator('#items article').count();
        await page.locator('#query').fill('beops-no-such-headline-912387');
        await page.waitForFunction(()=>document.querySelectorAll('#items article').length===0);
        await page.locator('#reset').click();await page.waitForFunction(n=>document.querySelectorAll('#items article').length===n,all);
        const summary=page.locator('#items article').nth(10).locator('summary');await summary.focus();await page.keyboard.press('Enter');
        const before=await page.locator(':focus').evaluate(e=>({id:e.closest('article').dataset.id,top:e.getBoundingClientRect().top}));
        await page.evaluate(()=>load());
        const after=await page.locator(':focus').evaluate(e=>({id:e.closest('article')?.dataset.id,top:e.getBoundingClientRect().top,open:e.parentElement.open}));
        functional.push({check:'archive search, reset and refresh',all,focusRetained:before.id===after.id,openRetained:after.open,scrollDelta:Math.abs(before.top-after.top)});
        await page.locator('#lang').click();functional.push({check:'archive language',lang:await page.locator('html').getAttribute('lang')});
      }
      if(route==='monolog.html'&&width===390){
        await page.locator('#grip').focus();const before=Number(await page.locator('#grip').getAttribute('aria-valuenow'));await page.keyboard.press('ArrowDown');
        functional.push({check:'keyboard separator resize',before,after:Number(await page.locator('#grip').getAttribute('aria-valuenow'))});
      }
      await context.close();
    }
  }finally{await browser.close();server.close();}
  const report={at:new Date().toISOString(),root,results,functional,scope:'DOM, Chromium accessibility tree, keyboard scenarios, flat-color computed contrast, recorded widths/themes, reduced motion. Not a screen-reader certification; complex backgrounds and canvas pixels require visual/manual review.'};
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
  const hasIssue=r=>r.errors.length||r.overflow||r.unnamedControls.length||r.lowContrast.length||!r.main||!r.lang||r.tablesWithoutCaption||r.unnamedCanvas;
  console.log(JSON.stringify({pages:results.length,issues:results.filter(hasIssue),functional}));
  if(results.some(hasIssue)||functional.some(r=>r.focusRetained===false||r.openRetained===false||r.scrollDelta>2||r.axisAvailable===false||r.axisOverlap||r.axisOutOfBounds))process.exitCode=1;
}
main().catch(e=>{console.error(e);server.close();process.exitCode=1;});
