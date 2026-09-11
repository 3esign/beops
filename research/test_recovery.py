"""Adversarial recovery cases. No live network or model calls; all mutations use temp roots."""
import copy
import hashlib
import json
import os
import pathlib
import sys
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'research')]
import contracts as C
import permission_policy as P
import legal_capture as L
import collect_daemon as D
import organ_mind as M
import organ_news as N
import claim_evidence as E
import baseline as B
import agreement as A
import local_models as LM
from recovery_fixtures import permission

NOW = datetime(2026, 9, 11, 6, tzinfo=timezone.utc)


class EntryPoints(unittest.TestCase):
    def test_staged_manifest_refuses_git_newline_conversion(self):
        import mirror_transaction as T
        import verify_staged_export as V
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td);(root/'docs').mkdir();T.git(root,'init','-q')
            attributes=root/'.gitattributes';attributes.write_bytes(b'*.json text eol=lf\r\n*.pdf -text\r\n')
            text=root/'docs/data.json';text.write_bytes(b'{\r\n "ok":true\r\n}')
            binary=root/'docs/file with space.pdf';binary.write_bytes(b'%PDF fixture\x00\r\n')
            def stage():
                rows=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (text,binary,attributes,root/'docs/public-links.json') if p.exists()]
                (root/'docs/export-manifest.json').write_text(json.dumps({'files':rows}),encoding='utf-8')
                T.git(root,'add','--','.gitattributes','docs')
            stage()
            with self.assertRaisesRegex(ValueError,'staged bytes differ'):V.verify(root)
            import validate_public_tree as P
            P.validate(root);stage()
            self.assertEqual(V.verify(root)['staged_files_verified'],4)

    def test_legacy_direct_baseline_task_respects_maintenance(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td);(root/'runtime').mkdir();(root/'runtime/MAINTENANCE').write_text('fixture')
            with patch.object(B,'ROOT',root),patch.object(B,'build',side_effect=AssertionError('build while paused')):
                self.assertEqual(B.main(['baseline.py','build']),75)

    def test_failed_mirror_copy_restores_bytes_and_keeps_new_files(self):
        import mirror_transaction as T
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)/'public'; root.mkdir()
            T.git(root,'init','-q')
            (root/'.gitattributes').write_bytes(b'*.txt text eol=lf\n')
            (root/'old.txt').write_bytes(b'original\r\n')
            T.git(root,'add','old.txt','.gitattributes')
            T.git(root,'-c','user.name=Semir Poturak','-c','user.email=scumutator@gmail.com','commit','-qm','fixture')
            saved = T.capture(root)
            (root/'old.txt').write_bytes(b'partial copy')
            (root/'new.txt').write_bytes(b'new content')
            T.git(root,'add','old.txt','new.txt')
            restored = T.restore(root,saved['archive'])
            self.assertEqual((root/'old.txt').read_bytes(),b'original\n')
            import zipfile
            with zipfile.ZipFile(saved['archive']) as z:self.assertEqual(z.read('old.txt'),b'original\r\n')
            self.assertFalse((root/'new.txt').exists())
            self.assertEqual((pathlib.Path(restored['new_files_kept'])/'new.txt').read_bytes(),b'new content')
            self.assertEqual(T.git(root,'status','--porcelain'),'')
            (root/'old.txt').write_bytes(b'later committed change')
            T.git(root,'add','old.txt')
            T.git(root,'-c','user.name=Semir Poturak','-c','user.email=scumutator@gmail.com','commit','-qm','new head')
            with self.assertRaisesRegex(ValueError,'HEAD changed'):
                T.restore(root,saved['archive'])
            self.assertEqual((root/'old.txt').read_bytes(),b'later committed change')

    def test_collect_help_and_invalid_arguments_cannot_load_network_or_store(self):
        # Copy ONLY the entry point. Any attempt to import the old Store or spawn
        # the active collector fails; help must work without either implementation.
        with tempfile.TemporaryDirectory() as td:
            script = pathlib.Path(td) / 'collect.js'
            script.write_bytes((ROOT/'tools/collect.js').read_bytes())
            help_result = subprocess.run(['node', str(script), '--help'], capture_output=True, text=True, timeout=10)
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            self.assertIn('Usage:', help_result.stdout)
            bad = subprocess.run(['node', str(script), '--typo'], capture_output=True, text=True, timeout=10)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(sorted(p.name for p in pathlib.Path(td).iterdir()), ['collect.js'])

    def test_manual_refusal_stays_refused_in_generated_index(self):
        import build_provenance_index as I
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            ledger = root/'ledger.jsonl'
            rows = [{'sid':'S1','name':'Fixture','captured_at_utc':'2026-09-10T00:00:00Z','evidence_dir':'research/evidence/legal/S1/a','manual_verdict':'refused','manual_reason':'editor veto','allowed_for_us':False},
                    {'sid':'S1','name':'Fixture','captured_at_utc':'2026-09-11T00:00:00Z','evidence_dir':'research/evidence/legal/S1/b','allowed_for_us':True,'capture_ok':True}]
            ledger.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            out = root/'index.md'
            with patch.object(I,'ROOT',str(root)),patch.object(I,'LEDGER',str(ledger)),patch.object(I,'OUT',str(out)),patch.object(I,'load_registry',return_value={}):
                I.main()
            text = out.read_text(encoding='utf-8')
            self.assertIn('0 access checks passed · 1 refused', text)


class Permission(unittest.TestCase):
    def test_same_route_fresh_hashed_evidence_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); url = 'https://example.test/measure?from=1'
            entry = permission(root, 'S1', url, NOW)
            self.assertTrue(P.authorize('S1', {'S1': entry}, root, url, NOW)[0])
            for other in ('https://example.test/elsewhere', 'https://other.test/measure', 'javascript:alert(1)', None):
                self.assertFalse(P.authorize('S1', {'S1': entry}, root, other, NOW)[0])
            self.assertFalse(P.authorize('S1', {'S1': entry}, root, url, NOW + timedelta(days=9))[0])
            (root / entry['evidence_dir'] / 'robots.txt').write_text('Allow: /')
            self.assertFalse(P.authorize('S1', {'S1': entry}, root, url, NOW)[0])

    def test_signals_and_manual_decision_are_sticky(self):
        for headers in ({'Content-Signal':'ai-input=no'}, {'TDM-Reservation':'1'}, {'X-Robots-Tag':'noai'}):
            self.assertFalse(P.access_state({'allowed_for_us':True, 'capture_ok':True,'opt_out_signals_seen':{'u':headers}})[0])
        self.assertTrue(P.access_state({'allowed_for_us':True,'capture_ok':True,'opt_out_signals_seen':{'u':{'X-Robots-Tag':'noindex'}}})[0])
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'ledger.jsonl'
            p.write_text(json.dumps({'sid':'S1','captured_at_utc':'1','manual_verdict':'refused'})+'\n'+json.dumps({'sid':'S1','captured_at_utc':'2','allowed_for_us':True,'capture_ok':True})+'\n')
            self.assertFalse(P.access_state(P.latest(p)['S1'])[0])

    def test_duplicate_robots_groups_combine_and_signal_only_groups_end(self):
        text='User-agent: *\nAllow: /\nUser-agent: *\nDisallow: /blocked\n'
        self.assertFalse(L.rfc9309(text, '*', '/blocked')[0])
        self.assertTrue(L.rfc9309(text, '*', '/open')[0])
        self.assertEqual(len(L.parse_groups('User-agent: *\nContent-Signal: ai-input=no\nUser-agent: other\nAllow: /')), 2)

    def test_capture_never_fetches_denied_path_or_manual_stop(self):
        requests=[]
        def fetch(url):
            requests.append(url)
            return 200, {}, b'User-agent: *\nDisallow: /blocked\n', None
        with patch.object(L,'fetch',fetch):
            r=L.capture('S1','Test',['https://example.test/blocked'],[],'fixture',dry=True)
            self.assertFalse(r['allowed_for_us']); self.assertEqual(requests,['https://example.test/robots.txt'])
            requests.clear()
            L.capture('S1','Test',['https://example.test/blocked'],[],'fixture',dry=True,refused='operator refusal')
            self.assertEqual(requests,[])

    def test_same_capture_path_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(L,'ROOT',td),patch.object(L,'EVIDENCE',td),patch.object(L,'LEDGER',str(pathlib.Path(td)/'l.jsonl')),patch.object(L,'utcstamp',return_value='fixed'),patch.object(L,'fetch',return_value=(404,{},b'',None)):
                L.capture('S1','Test',['https://example.test/'],[],'fixture',refused='stop')
                manifest=pathlib.Path(td)/'S1/fixed/MANIFEST.json'; before=manifest.read_bytes()
                with self.assertRaises(FileExistsError): L.capture('S1','Test',['https://example.test/'],[],'again')
                self.assertEqual(before,manifest.read_bytes())


class Data(unittest.TestCase):
    def test_raw_replay_accepts_relative_root_but_refuses_escaped_raw_path(self):
        import repair_record as R
        # Windows cannot express C: temp paths relative to a D: project junction.
        with tempfile.TemporaryDirectory(dir=pathlib.Path.cwd()) as td:
            root=pathlib.Path(td);src={'sid':'S1','parser':'rhmz_gauges'}
            body=b'<p>11.09.2026 vreme: 8:00 (06:00 UTC)</p><tr><td>SAVA</td><td>x</td><td>BEOGRAD</td><td>100</td><td>2</td><td>500</td><td>20</td></tr>'
            row=D.parse_rhmz_gauges(body,NOW,src)[0];row['result']=999
            row['raw_sha256']=hashlib.sha256(body).hexdigest()
            for d in ('research','data/live/rows/S1','data/live/receipts/S1','data/live/raw'): (root/d).mkdir(parents=True,exist_ok=True)
            (root/'research/COLLECTORS.json').write_text(json.dumps({'sources':[src]}))
            (root/'data/live/raw/capture').write_bytes(body)
            (root/'data/live/rows/S1/2026-09.jsonl').write_text(json.dumps(row)+'\n')
            receipt={'raw_sha256':row['raw_sha256'],'raw_file':'data/live/raw/capture'}
            file=root/'data/live/receipts/S1/one.json';file.write_text(json.dumps(receipt))
            relative=os.path.relpath(root,pathlib.Path.cwd())
            self.assertEqual(R.gauges(relative)['planned_corrections'],1)
            receipt['raw_file']='../outside';file.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError,'outside project'):R.gauges(relative)

    def test_each_missing_gauge_cell_keeps_its_parameter(self):
        expected=[100,2,500,20]
        for absent in range(4):
            vals=[str(x) if i!=absent else '' for i,x in enumerate(expected)]
            for icons in ('','<td><img src="nrt.gif"></td><td><img src="izv.gif"></td>'):
                body='<p>11.09.2026 vreme: 8:00 (06:00 UTC)</p><tr><td>SAVA</td><td>x</td><td>BEOGRAD</td>'+icons+''.join('<td>'+v+'</td>' for v in vals)+'</tr>'
                rows=D.parse_rhmz_gauges(body.encode(),NOW,{'sid':'S1'})
                self.assertEqual([r['result'] for r in rows],[None if i==absent else x for i,x in enumerate(expected)])

    def test_nonfinite_and_boolean_measurements_are_missing(self):
        raw=json.dumps({'data':[{'station_id':1,'value':v} for v in (True,float('inf'),float('-inf'),None,0)]}).encode()
        self.assertEqual([r['result'] for r in D.parse_sepa_hvd(raw,NOW,{'sid':'S1'})],[None,None,None,None,0])

    def test_clock_contract_and_dst_gap_fold(self):
        row={'phenomenonTime':{'start':'2026-09-11T08:00:00Z','end':'2026-09-11T09:00:00Z'},
             'phenomenonTimeCorrected':{'start':'2026-09-11T06:00:00Z','end':'2026-09-11T07:00:00Z'}}
        self.assertEqual(C.row_clock(row)[0].hour,7)
        self.assertEqual(B._hour_of(row),(7,True,'corrected'))
        self.assertEqual(A._hour_of(row),('2026-09-11T07','corrected',True))
        self.assertEqual(C.belgrade_local(datetime(2026,3,29,1,30))[0].hour,0)
        self.assertEqual(C.belgrade_local(datetime(2026,3,29,2,30)),(None,None))
        self.assertEqual(C.belgrade_local(datetime(2026,10,25,2,30)),(None,None))
        self.assertEqual(C.belgrade_offset(datetime(2026,12,1,tzinfo=timezone.utc)),1)

    def test_revision_is_retained_and_corruption_is_reported(self):
        a={'dedupe_key':'x','result':10,'receivedTime':'2026-09-11T00:00:00Z'}
        self.assertNotEqual(D._row_key(a),D._row_key(dict(a,result=11)))
        self.assertEqual(D._row_key(a),D._row_key(dict(a,receivedTime='2026-09-11T01:00:00Z')))
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'rows.jsonl';p.write_text('{"ok":true}\n{broken\n')
            with self.assertRaisesRegex(ValueError,'rows.jsonl:2'): list(C.json_rows(p))

    def test_antipodal_directions_have_no_defined_mean(self):
        self.assertIsNone(A._circular_mean([0,180]))
        self.assertAlmostEqual(A._circular_mean([350,10])%360,0,places=6)


class Claims(unittest.TestCase):
    def test_cli_mind_refreshes_model_input_before_the_step(self):
        with tempfile.TemporaryDirectory() as td:
            snapshot=pathlib.Path(td)/'snapshot.json';snapshot.write_text('{"generation":"old"}')
            def refresh():snapshot.write_text('{"generation":"current"}')
            def consume():
                self.assertEqual(json.loads(snapshot.read_text())['generation'],'current')
                return {'state':'checked'}
            with patch.object(M,'LIVE',pathlib.Path(td)),patch.object(M.sys,'argv',['organ_mind.py','step']),patch.object(D,'export',side_effect=refresh),patch.object(M,'step',side_effect=consume):
                self.assertEqual(M.main(),0)

    def test_registry_pause_stops_both_mind_entry_points_without_model_calls(self):
        with tempfile.TemporaryDirectory() as td:
            def no_model(): raise AssertionError('model call while paused')
            with patch.object(M,'OUT_DIR',pathlib.Path(td)),patch.object(M,'CONTEXT',pathlib.Path(td)/'context.json'),patch.object(M,'register',return_value={'enabled':False}):
                self.assertEqual(M.run(now=NOW,snap={},tags=no_model)['state'],'paused')
                self.assertEqual(M.step(now=NOW,snap={},tags=no_model)['state'],'paused')

    def test_invalid_state_caches_are_visible_failures(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td);p=root/'derived/news/_done.json';p.parent.mkdir(parents=True);p.write_text('{broken')
            with patch.object(N,'LIVE',root):
                with self.assertRaisesRegex(ValueError,'Invalid completion cache'):N.done_keys()
            context=root/'context.json';context.write_text('{broken')
            with patch.object(M,'CONTEXT',context):
                with self.assertRaisesRegex(ValueError,'Invalid mind context'):M._context()

    def setUp(self):
        self.dg={'numbers':['10'],'clock':['08:00'],'facts':[{'id':'F1','en':'The temperature is 10 degrees at 08:00.','sr':'Temperatura je 10 stepeni u 08:00.','kind':'spread'}]}
        self.answer={'text':'The temperature is 10 degrees at 08:00 [F1].','cites':['F1'],'hypotheses':[],'questions':[],'next_check':'','claim':None}

    def test_sign_and_every_public_text_field_are_checked(self):
        self.assertTrue(M.validate(self.answer,self.dg)[0])
        bad=copy.deepcopy(self.answer);bad['text']=bad['text'].replace('10','-10')
        self.assertFalse(M.validate(bad,self.dg)[0])
        for field in ('hypotheses','questions','next_check'):
            bad=copy.deepcopy(self.answer);text='Is the temperature 99999 degrees [F1]?'
            bad[field]=text if field=='next_check' else [text]
            self.assertFalse(M.validate(bad,self.dg)[0],field)

    def test_voice_preserves_time_number_and_negation(self):
        en=self.answer['text']
        self.assertTrue(M.validate_voice('Temperatura je 10 stepeni u 08:00 [F1].',en,self.dg)[0])
        for sr in ('Temperatura je 10 stepeni u 19:59 [F1].','Temperatura je poznata u 08:00 [F1].','Temperatura nije 10 stepeni u 08:00 [F1].'):
            self.assertFalse(M.validate_voice(sr,en,self.dg)[0])

    def test_late_and_old_measurement_never_settle_true_and_news_counts(self):
        row={'at':'2026-09-11T00:00:00Z','due':'2026-09-11T01:00:00Z','claim':{'kind':'spread','sid':'S1','parameter':'PM10','lo':40,'hi':60}}
        for rx,t in [('2026-09-11T01:30:00Z','2026-09-11T00:30:00Z'),('2026-09-11T00:30:00Z','2026-09-10T23:00:00Z')]:
            snap={'sources':[{'sid':'S1','datastreams':[{'parameter':'PM10','points':[{'rx':rx,'t':t,'v':50}]}]}]}
            self.assertEqual(E.evaluate(row,ROOT,snap)['outcome'],'unverifiable')
        row['claim']={'kind':'reception','sid':'S1'}
        self.assertEqual(E.evaluate(row,ROOT,{'sources':[{'sid':'S1','events':[{'rx':'2026-09-11T00:30:00Z'}]}]})['outcome'],'true')

    def test_remote_endpoint_and_remote_alias_are_refused(self):
        for url in ('https://example.test','http://127.0.0.1.evil.test:11434','http://user:pass@localhost:11434'):
            with self.assertRaises(ValueError): LM.endpoint(url)
        self.assertEqual(LM.endpoint('http://127.0.0.1:11434'),'http://127.0.0.1:11434')

    def test_news_time_must_be_quote_and_non_belgrade_has_no_zones(self):
        rows=N.derive([{'sid':'S1','result':'Radovi u gradu danas','dedupe_key':'x'}],{'items':[{'i':0,'category':'radovi','belgrade':False,'zones':[{'name':'Zemun','score':1}],'event_time_text':'u 19:59'}]},'test','hash',NOW)
        self.assertEqual(rows[0]['zones'],[]);self.assertIsNone(rows[0]['event_time_text'])
        self.assertEqual(N.derive([{'sid':'S1','result':'Test','dedupe_key':'x'}],{'items':[]},'test','hash',NOW)[0]['state'],'incomplete')


if __name__=='__main__': unittest.main()
