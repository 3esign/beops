'use strict';
const fs=require('node:fs'),path=require('node:path');
const candidates=[process.env.BEOPS_INCOGNITO,'C:/Svemir/lib/incognito.js','D:/Svemir/lib/incognito.js'].filter(Boolean);
const modulePath=candidates.find(candidate=>fs.existsSync(candidate));
if(!modulePath)throw Error('Incognito provider missing');
const value=require(path.resolve(modulePath)).headers('https://github.com/3esign/beops.git')['User-Agent'];
if(typeof value!=='string'||!value.trim())throw Error('Incognito transport identity missing');
process.stdout.write(value.trim());
