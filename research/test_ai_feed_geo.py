#!/usr/bin/env python3
"""E4 Test: zapazanje bez sidra se ne crta; zapazanje sa sidrom nosi oznaku modela."""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAPA_JS = ROOT / 'public' / 'mapa.js'

class AIFeedGeoContract(unittest.TestCase):
    def test_geo_must_match_cited_frozen_evidence(self):
        script = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {validateOutput,geoReasons}=require('./tools/ai_feed_context.js');
const {monologueSchema}=require('./tools/ai_feed_providers.js');
const {anchoredAI}=require('./public/mapa.js');
const packet={facts:[
 {id:'F1',kind:'observation',sid:'S146',source:'SEPA',domain:'air',place:'Test',metric:'PM2.5',unit:'ug.m-3',value:12,time:'2026-09-26T12:00:00Z',location:[20.4,44.8],map_anchor:{layer:'instruments',id:'S146:Test:44.8:20.4'}},
 {id:'F2',kind:'observation',sid:'S146',source:'SEPA',domain:'air',place:'Other',metric:'PM2.5',unit:'ug.m-3',value:13,time:'2026-09-26T12:00:00Z',location:[20.5,44.9],map_anchor:{layer:'instruments',id:'S146:Other:44.9:20.5'}}
]};
const base={title:'Jedno merno mesto',paragraphs:[{text:'U ovom zapisu je navedeno merenje na stanici i ono se odnosi samo na to mesto. Iz ovih podataka ne možemo da zaključimo šta se dešava u ostatku grada.',cites:['F1']}],question:'Kako se ovo merenje menja u sledećem zapisu?',limitations:'Podaci ne govore o uzroku niti o celom gradu.'};
assert.equal(validateOutput(base,packet).ok,true,JSON.stringify(validateOutput(base,packet)));
for(const geo of [{lat:44.8,lon:20.4},{layer:'instruments',id:'S146:Test:44.8:20.4'}]) {
 const value={...base,geo};assert.equal(validateOutput(value,packet).ok,true,JSON.stringify(validateOutput(value,packet)));
 const shown=anchoredAI([{id:'test',model:'fixture-model',content:value}], [{layer:'instruments',id:'S146:Test:44.8:20.4',lat:44.8,lon:20.4}]);
 assert.equal(shown.length,1);assert.equal(shown[0].lat,44.8);assert.equal(shown[0].data.model,'fixture-model');
}
for(const geo of [null,{},[],{lat:44.8},{lat:'44.8',lon:20.4},{lat:NaN,lon:20.4},{lat:100,lon:20.4},{lat:44.8,lon:20.4,extra:true},{lat:44.9,lon:20.5},{lat:44.80001,lon:20.4},{layer:'instruments',id:'S146:Other:44.9:20.5'},{layer:'materija',id:'invented'}]) {
 assert.equal(validateOutput({...base,geo},packet).ok,false,'accepted ungrounded '+JSON.stringify(geo));
}
assert.deepEqual(geoReasons({...base,geo:{lat:44.8,lon:20.4}},{facts:[]}),['geo_not_cited']);
assert.deepEqual(geoReasons(base,{facts:[]}),[]);
const schema=monologueSchema(['F1']);
assert.equal(schema.required.includes('geo'),false);
assert.equal(schema.properties.geo.anyOf.length,2);
assert.deepEqual(schema.properties.paragraphs.items.properties.cites.items.enum,['F1']);
const config=JSON.parse(fs.readFileSync('research/AI_FEED.json','utf8'));
assert.equal(config.prompt_version,4);
assert.match(fs.readFileSync('research/03-models/AI_FEED_SYSTEM_PROMPT_v4.txt','utf8'),/PROSTORNO SIDRO/);
console.log('Grounded optional geo contract passed');
"""
        result = subprocess.run(['node', '-'], input=script, text=True, encoding='utf-8', cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_geo_logic_in_mapa(self):
        js_code = MAPA_JS.read_text(encoding='utf-8')
        
        # Test: zapazanje bez sidra se ne crta
        self.assertIn("entry.content.geo", js_code, "mapa.js mora da proverava prisustvo geo polja")
        
        # Test: zapazanje sa sidrom nosi oznaku modela
        self.assertIn("p.data.model", js_code, "mapa.js mora da koristi oznaku modela (p.data.model) na mapi")
        self.assertIn("ctx.fillText(p.data.model", js_code, "mapa.js mora da ispisuje oznaku modela na mapi")

if __name__ == '__main__':
    unittest.main()
