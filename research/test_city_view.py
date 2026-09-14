"""Null, sparse, future and unequal-sample inputs cannot become confident city claims."""
import hashlib
import json
import pathlib
import sys
import subprocess
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import build_city_view as V


class CityView(unittest.TestCase):
    def test_html_entries_replace_old_pin_before_scripts_and_reject_missing_head(self):
        from build_site import pin_entry
        import re
        for shell in ('<HEAD><script src="beops-view.js"></script></HEAD><body></body>',
                      '<!doctype html><html lang="sr"><meta charset="utf-8"><title>Implicit head</title><main>Body</main></html>',
                      '<head><meta name="beops-input-generation" content="old"></head>'):
            pinned = pin_entry(shell, 'a'*64)
            self.assertEqual(pinned, pin_entry(pinned, 'a'*64))
            self.assertEqual(pinned.count('name="beops-input-generation"'), 1)
            self.assertEqual(len(re.findall(r'src="beops-view.js"', pinned)), 1)
            self.assertLess(pinned.index('name="beops-input-generation"'), pinned.index('<script'))
        with self.assertRaises(ValueError): pin_entry('<body>legacy</body>', 'a'*64)

    def test_actual_public_templates_with_optional_head_tags_are_pinned(self):
        from build_site import pin_entry
        for name in ('sada.html','podaci.html','traka-live.html','monolog-puls.html','svedoci.html','naslovi.html'):
            with self.subTest(page=name):
                content=(ROOT/'research/05-design/studies'/name).read_text(encoding='utf-8')
                pinned=pin_entry(content, 'a'*64)
                self.assertLess(pinned.index('name="beops-input-generation"'), pinned.index('<script'))
                self.assertEqual(pinned, pin_entry(pinned, 'a'*64))

    def test_public_verifier_checks_generation_and_projection_clock(self):
        run=subprocess.run(['node',str(ROOT/'research/generation_contract.test.cjs')],capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_mixed_or_old_projection_is_refused_before_analysis_is_written(self):
        generation={'schema':'beops-input-generation/v1','id':'a'*64,
                    'captured_at':'2026-09-14T08:00:00Z','observation_prefix':'complete-lf-lines/v1'}
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)
            snapshot={'as_of':'2026-09-14T08:00:00Z','sources':[],'input_generation':generation}
            (root/'live-snapshot.json').write_bytes(V.encode(snapshot))
            for history in ({'series':[]},
                            {'series':[],'input_generation':dict(generation,id='b'*64),'as_of':snapshot['as_of']},
                            {'series':[],'input_generation':generation,'as_of':'2026-09-13T08:00:00Z'}):
                (root/'history.json').write_bytes(V.encode(history))
                with self.assertRaises(ValueError): V.build(root)
                self.assertFalse((root/'city-analysis.json').exists())
            (root/'history.json').write_bytes(V.encode({'series':[],'input_generation':generation,'as_of':snapshot['as_of']}))
            V.build(root)
            view=json.loads((root/'city-overview.json').read_bytes())
            analysis=json.loads((root/'city-analysis.json').read_bytes())
            self.assertEqual(view['edition']['input_generation'],analysis['input_generation'])
            self.assertEqual(view['edition']['state'],'verified_capture')

    def test_browser_rejects_different_generation_and_shares_parent(self):
        run=subprocess.run(['node',str(ROOT/'research/city_view_contract.test.cjs')],capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_latest_null_is_not_replaced_by_older_value(self):
        points=[{'v':19,'t':'2026-09-14T07:00:00Z','rx':'2026-09-14T07:01:00Z'},
                {'v':None,'t':'2026-09-14T08:00:00Z','rx':'2026-09-14T08:01:00Z'}]
        snap={'as_of':'2026-09-14T08:05:00Z','sources':[{'sid':'S1','datastreams':[{'points':points}]}]}
        self.assertEqual(V.summarize(snap)['sources'][0]['datastreams'][0]['points'],points[-1:])

    def test_sparse_hours_preserve_coverage_and_weight_by_samples(self):
        series={'buckets':{'2026-09-14T01':{'mean':2,'n':3,'min':1,'max':3},'2026-09-14T03':{'mean':10,'n':1,'min':10,'max':10},
            '2026-09-14T08':{'mean':999,'n':9},'2026-09-14T09':{'mean':999,'n':9}}}
        value=V.windows(series,'2026-09-14T08:05:00Z')['24']
        self.assertEqual(value['samples'],4);self.assertEqual(value['hours_with_values'],2)
        self.assertEqual(value['sample_mean'],4);self.assertEqual(value['endpoint_difference'],8)
        self.assertEqual(value['min'],1);self.assertEqual(value['max'],10)

    def test_no_data_is_null_and_recurrence_is_not_invented(self):
        out=V.analyze({'series':[{'kind':'numeric','time_basis':'received','buckets':{}}]},'2026-09-14T08:00:00Z')
        row=out['series'][0];self.assertEqual(row['time_basis'],'received')
        self.assertIsNone(row['windows']['720']['sample_mean'])
        self.assertEqual(row['recurrence']['state'],'not_tested')

    def test_missing_results_do_not_weight_mean_and_are_visible(self):
        series={'buckets':{'2026-09-14T01':{'mean':2,'n':10,'missing':9},
                           '2026-09-14T02':{'mean':10,'n':1},
                           '2026-09-14T03':{'n':4,'missing':4}}}
        value=V.windows(series,'2026-09-14T08:05:00Z')['24']
        self.assertEqual(value['sample_mean'],6)
        self.assertEqual(value['samples'],2)
        self.assertEqual(value['received_samples'],15)
        self.assertEqual(value['missing_samples'],13)
        self.assertEqual(value['hours_with_values'],2)
        for bucket in ({'n':1,'missing':2},{'n':1,'missing':1,'mean':9},{'n':1}):
            with self.assertRaises(ValueError):
                V.windows({'buckets':{'2026-09-14T01':bucket}},'2026-09-14T08:05:00Z')

    def test_overview_pins_real_bytes_and_fits_budget(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)
            for name,data in [('live-snapshot.json',{'as_of':'2026-09-14T08:00:00Z','sources':[]}),('history.json',{'series':[]}),('watch.json',{'at':'2026-09-14T08:00:00Z','counts':{'ok':1}})]:
                (root/name).write_bytes(V.encode(data))
            result=V.build(root);view=json.loads((root/'city-overview.json').read_bytes())
            self.assertLess(result['overview_bytes'],150*1024)
            for name,spec in view['resources'].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),spec['sha256'])
            before=result['generation'];(root/'watch.json').write_bytes(V.encode({'counts':{'ok':2}}))
            self.assertNotEqual(V.build(root)['generation'],before)


if __name__=='__main__':unittest.main()
