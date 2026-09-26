#!/usr/bin/env python3
"""Contract test: mapa.js sme da prikazuje samo polja iz registra."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAPA_JS = ROOT / 'public' / 'mapa.js'

class MapLayersContract(unittest.TestCase):
    def test_mapa_js_loads_map_layers(self):
        js_code = MAPA_JS.read_text(encoding='utf-8')
        self.assertIn("fetch('MAP_LAYERS.json')", js_code, 'mapa.js mora da ucitava MAP_LAYERS.json')
        
    def test_mapa_js_uses_dossier_fields(self):
        js_code = MAPA_JS.read_text(encoding='utf-8')
        self.assertIn("dossier_fields", js_code, 'mapa.js mora da koristi dossier_fields iz registra')
        
if __name__ == '__main__':
    unittest.main()
