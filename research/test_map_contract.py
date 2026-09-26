"""Behavior contracts for the spatial view; no browser or third-party dependencies."""
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


class SpatialContract(unittest.TestCase):
    def test_data_transforms_fail_closed(self):
        script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const map = require('./public/mapa.js');
const registry = JSON.parse(fs.readFileSync('research/MAP_LAYERS.json','utf8'));
assert.equal(map.validRegistry(registry).length,5);
const malformed = JSON.parse(JSON.stringify(registry));
malformed.layers[0].dossier_fields.push({id:'ai-feed'});
assert.throws(()=>map.validRegistry(malformed));
assert.equal(map.localRoute('https://third-party.example/tile.json'),false);
assert.equal(map.localRoute('../outside.json'),false);
assert.equal(map.localRoute('ai-feed/latest.json'),true);
assert.equal(map.coordinate(null,20.4),false);
assert.equal(map.coordinate('44.8',20.4),false);
assert.equal(map.coordinate(Infinity,20.4),false);
assert.equal(map.readingState(null),'unavailable');
assert.equal(map.readingState({v:null,t:'2026-09-26T12:00:00Z'}),'unavailable');
assert.equal(map.readingState({v:0,t:null,tu:true}),'untimed');
assert.equal(map.readingState({v:1,t:'2026-09-26T12:00:00Z',tc:'2026-09-26T10:00:00Z'}),'estimated');
assert.equal(map.readingState({v:2,t:'2026-09-26T12:00:00Z',q:'forecast'}),'forecast');
const snap={as_of:'2026-09-26T13:00:00Z',status:{sources:[{sid:'S146',captured:7,expected_slots:24,quorum:'###'}]},sources:[{sid:'S146',name:'SEPA',datastreams:[
 {station:'Test',datastream:'test|PM10',parameter:'PM10',lat:44.8,lon:20.4,unit:'ug/m3',last_received:{v:12,t:'2026-09-26T12:00:00Z',rx:'2026-09-26T12:02:00Z'}},
 {station:'Test',datastream:'test|PM2.5',parameter:'PM2.5',lat:44.8,lon:20.4,unit:'ug/m3',last_received:{v:0,t:null,tu:true,rx:'2026-09-26T12:03:00Z'}},
 {station:'Missing coordinates',lat:null,lon:20.4,points:[]},
 {station:'No reading',lat:44.81,lon:20.41,points:[]}
]}]};
const instruments=map.instruments(snap);
assert.equal(instruments.length,2);
assert.equal(instruments[0].data.measurements.length,2);
assert.equal(instruments[0].data.measurements[1].value,0);
assert.equal(instruments[0].data.captured,7);
assert.equal(instruments[0].data.expected_slots,24);
assert.equal(instruments[0].data.last_received,'2026-09-26T12:03:00Z');
assert.equal(instruments[1].state,'unavailable');
const population=map.populationPoints({source:{release:'2022-06-30'},hexes:[[20.4,44.8,0,'h3-zero'],[20.5,44.8,300,'h3-positive'],[20.5,44.8,null,'bad'],[20.5,null,50,'bad2']]});
assert.equal(population.length,2);
assert.equal(population[0].data.population,0);
assert.equal(population[0].state,'estimated');
const entry=(id,geo,model='fixture-model')=>({id,model,at:'2026-09-26T12:00:00Z',content:{title:'Fixture only',geo}});
const ai=map.anchoredAI([
 entry('no-geo',undefined),entry('null-geo',{lat:null,lon:20.4}),entry('string-geo',{lat:'44.8',lon:20.4}),
 entry('outside',{lat:44.8,lon:2}),entry('unresolved',{layer:'materija',id:'NBG-B21-01'}),
 entry('no-model',{lat:44.8,lon:20.4},''),entry('valid',{lat:44.8,lon:20.4}),
 entry('resolved',{layer:'kontur-population',id:'h3-positive'})
], [...instruments,...population]);
assert.deepEqual(ai.map(p=>p.id),['valid','resolved']);
assert.equal(ai[0].data.model,'fixture-model');
assert.equal(ai[0].state,'estimated');
assert.equal(ai[1].lon,20.5);
assert.equal(map.geometryParts({geometry:{type:'MultiLineString',coordinates:[[[20,44],[21,45]],[[20,45],[21,46]]]}}).length,2);
assert.equal(map.geometryParts({geometry:{type:'MultiPolygon',coordinates:[[[[20,44],[21,45],[20,44]]]]}})[0].closed,true);
console.log('Spatial behavior contract passed');
"""
        result = subprocess.run(["node", "-"], input=script, text=True, encoding="utf-8", cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_registry_export_has_no_invented_material_source(self):
        registry = json.loads((ROOT / 'research' / 'MAP_LAYERS.json').read_text(encoding='utf-8'))
        public = json.loads((ROOT / 'public' / 'MAP_LAYERS.json').read_text(encoding='utf-8'))
        self.assertEqual(registry, public)
        layers = {layer['id']: layer for layer in registry['layers']}
        self.assertEqual(layers['materija']['states_it_may_carry'], ['unavailable'])
        self.assertIsNone(layers['materija']['sid'])
        self.assertNotEqual(layers['ai-feed']['licence'].lower(), 'public domain')
        for layer in layers.values():
            self.assertFalse(layer['route'].startswith('public/'))
            self.assertTrue(all(isinstance(field, str) for field in layer['dossier_fields']))


if __name__ == '__main__':
    unittest.main()
