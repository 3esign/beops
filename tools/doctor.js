'use strict';
const fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process');
const bundled=path.join(process.env.USERPROFILE||'','.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe');
const candidates=[process.env.BEOPS_PYTHON,fs.existsSync(bundled)?bundled:null,'python','python3'].filter(Boolean);
const checks=[{name:'Node 22+',ok:Number(process.versions.node.split('.')[0])>=22,actual:process.version}];
let python=null;
for(const exe of candidates){const r=spawnSync(exe,['-X','utf8','-B','-c','import sys,json; print(json.dumps({"version":sys.version,"supported":sys.version_info >= (3,12)}))'],{encoding:'utf8',timeout:5000,windowsHide:true});if(r.status===0){const d=JSON.parse(r.stdout);checks.push({name:'Python 3.12+',ok:d.supported,actual:d.version,executable:exe});python=exe;break;}}
if(!python)checks.push({name:'Python 3.12+',ok:false});
checks.push({name:'Git',ok:spawnSync('git',['--version'],{timeout:5000,windowsHide:true}).status===0});
checks.push({name:'Incognito HTTP provider',ok:[process.env.BEOPS_INCOGNITO,'C:/Svemir/lib/incognito.js','D:/Svemir/lib/incognito.js'].filter(Boolean).some(p=>fs.existsSync(p))});
if(python){const r=spawnSync(python,['-B','-c','import reportlab; print(reportlab.Version)'],{encoding:'utf8',timeout:5000,windowsHide:true});checks.push({name:'ReportLab (document build only)',ok:r.status===0,actual:r.stdout?.trim(),optional:true});}
checks.push({name:'Generated site',ok:fs.existsSync(path.resolve(__dirname,'../docs/index.html')),optional:true});
process.stdout.write(JSON.stringify({checks,requirements:'No npm additions. Core data processing uses Python stdlib; PDF builds additionally use the existing ReportLab runtime and a supported local font set. Scheduler installation requires Windows.'},null,2)+'\n');
process.exitCode=checks.some(c=>!c.ok&&!c.optional)?1:0;
