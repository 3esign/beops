'use strict';
const fs = require('node:fs');
const path = require('node:path');
function identityHeaders(url, options={}) {
  const candidates=[process.env.BEOPS_INCOGNITO,'C:/Svemir/lib/incognito.js','D:/Svemir/lib/incognito.js'].filter(Boolean);
  const provider=candidates.find(p=>fs.existsSync(p));
  if(!provider) throw new Error('Incognito boundary unavailable; request not sent');
  return require(path.resolve(provider)).headers(url, options);
}
module.exports={identityHeaders};
