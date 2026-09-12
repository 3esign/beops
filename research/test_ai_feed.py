"""Offline regression of the durable feed and captured context importer."""
import pathlib
import subprocess
import sys
import unittest
import json

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_context_catalog as catalog


class Feed(unittest.TestCase):
    def test_offline_feed_contracts(self):
        r=subprocess.run(['node',str(ROOT/'research/test_ai_feed_node.js')],capture_output=True,
                         text=True,encoding='utf-8',timeout=25,
                         creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(r.returncode,0,r.stdout+'\n'+r.stderr)
        self.assertIn('offline feed contracts passed',r.stdout)

    def test_rzs_captured_formats_and_selected_geography(self):
        directory=ROOT/'research/evidence/S148/20260906T020314Z'
        if not directory.exists():self.skipTest('private evidence is absent in this checkout')
        manifest=json.loads((directory/'MANIFEST.json').read_text(encoding='utf-8'))
        total=0
        for entry in manifest['files']:
            rows=catalog.unpack(directory/entry.get('stored_as',entry['file']),entry)
            self.assertTrue(rows)
            total+=1
            if entry['file'].startswith('240304'):
                self.assertEqual({r['IDTer'] for r in rows},{'RS'})
        self.assertEqual(total,6)

    def test_all_rendered_data_tables_have_matching_hashes(self):
        import hashlib
        file=ROOT/'public/context-catalog.json'
        if not file.exists():self.skipTest('context tables not built')
        doc=json.loads(file.read_text(encoding='utf-8'))
        for d in doc['datasets']:
            if not d.get('table'):continue
            p=ROOT/'public'/d['table']
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),d['table_sha256'])


if __name__=='__main__':unittest.main()
