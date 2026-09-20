"""Frozen-input reuse must preserve values and reject any changed input bytes."""
import hashlib
import json
import os
import pathlib
import stat as statmod
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import live_view
import paper_numbers
import prepare_release
from release_observation import input_generation
from contracts import observation_rows


class FrozenObservations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.live = self.root/'data/live'
        self.file = self.live/'rows/S01/2026-09.jsonl'
        self.file.parent.mkdir(parents=True)
        self.file.write_bytes(b'{"sid":"S01","result":7}\n')
        self.manifest = {'schema':'beops-release-inputs/v1','source_oid':'a'*40,'files':[
            {'path':self.file.relative_to(self.root).as_posix(),'bytes':self.file.stat().st_size,
             'sha256':hashlib.sha256(self.file.read_bytes()).hexdigest()}]}
        (self.root/'runtime').mkdir()
        (self.root/'.beops-generated-workspace.json').write_text(json.dumps({'source_oid':'a'*40}))
        self.env = patch.dict(os.environ, {'BEOPS_FROZEN_ROOT':str(self.root),
                                          'BEOPS_FROZEN_SOURCE_OID':'a'*40})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.bind_manifest()

    def bind_manifest(self):
        raw = json.dumps(self.manifest).encode()
        (self.root/'runtime/release-inputs.json').write_bytes(raw)
        os.environ['BEOPS_FROZEN_MANIFEST_SHA256'] = hashlib.sha256(raw).hexdigest()

    def test_real_live_copy_and_verified_release_produce_identical_observations(self):
        with patch.dict(os.environ, {'BEOPS_FROZEN_ROOT':''}):
            with live_view.observation_view(self.live) as copied:
                old = list(observation_rows(copied/'rows/S01/2026-09.jsonl'))
                self.assertNotEqual(copied, self.live)
        metrics = {}
        with patch.object(live_view.tempfile, 'TemporaryFile', side_effect=AssertionError('copy attempted')):
            with live_view.observation_view(self.live, metrics) as reused:
                self.assertEqual(reused, self.live)
                self.assertEqual(list(observation_rows(reused/'rows/S01/2026-09.jsonl')), old)
        self.assertEqual(metrics['copied_bytes'], 0)
        self.assertEqual(metrics['bytes'], self.file.stat().st_size)

    def test_same_size_and_mtime_cannot_hide_a_changed_payload(self):
        before = self.file.stat()
        self.file.write_bytes(self.file.read_bytes().replace(b'7', b'8'))
        os.utime(self.file, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaisesRegex(ValueError, 'payload changed'):
            with live_view.observation_view(self.live):
                self.fail('unverified bytes yielded')

    def test_sealed_jsonl_identity_avoids_rehashing_frozen_observation_bytes(self):
        self.file.chmod(statmod.S_IREAD)
        self.addCleanup(lambda: self.file.exists() and self.file.chmod(statmod.S_IREAD | statmod.S_IWRITE))
        observed = self.file.stat()
        self.manifest['files'][0].update(state_index_sealed=True,
                                         state_index_mtime_ns=observed.st_mtime_ns,
                                         state_index_file_id=observed.st_ino,
                                         state_index_device=observed.st_dev)
        self.bind_manifest()
        real_open = pathlib.Path.open

        def guarded_open(path, *args, **kwargs):
            if pathlib.Path(path) == self.file and args and args[0] == 'rb':
                raise AssertionError('sealed payload was rehashed')
            return real_open(path, *args, **kwargs)

        with patch.object(pathlib.Path, 'open', guarded_open):
            with live_view.observation_view(self.live) as reused:
                self.assertEqual(reused, self.live)

    def test_manifest_identity_is_required_and_foreign_fixture_uses_live_copy(self):
        with patch.dict(os.environ, {'BEOPS_FROZEN_MANIFEST_SHA256':'0'*64}):
            with self.assertRaisesRegex(ValueError, 'manifest hash'):
                with live_view.observation_view(self.live): pass
        with patch.dict(os.environ, {'BEOPS_FROZEN_SOURCE_OID':'b'*40}):
            with self.assertRaisesRegex(ValueError, 'source identity'):
                with live_view.observation_view(self.live): pass
        foreign = self.root/'foreign';foreign.mkdir()
        with live_view.observation_view(foreign) as copied:
            self.assertNotEqual(copied, foreign)

    def test_generation_requires_complete_prefix_and_binds_the_exact_manifest(self):
        with self.assertRaisesRegex(ValueError, 'complete observation prefix'):
            input_generation(self.live)
        self.manifest.update(source_tree='b'*40, captured_at='2026-09-14T12:00:00+00:00',
                             observation_prefix='complete-lf-lines/v1', configuration=[])
        self.bind_manifest()
        generation=input_generation(self.live)
        self.assertEqual(generation['id'],os.environ['BEOPS_FROZEN_MANIFEST_SHA256'])
        self.assertEqual(generation['captured_at'],'2026-09-14T12:00:00+00:00')
        self.assertIsNone(input_generation(self.root/'foreign'))

    def test_real_snapshot_and_history_share_capture_clock_and_configuration(self):
        import shutil
        import collect_daemon as collector
        import build_history as history
        import build_city_view as city
        cfg=self.root/'research/COLLECTORS.json';cfg.parent.mkdir()
        cfg.write_text(json.dumps({'sources':[{'sid':'S01','name':'Test source','cadence_seconds':300,
                                               'url':'https://example.invalid/fixture','parser':'sensor_community',
                                               'max_bytes':1000,'timeout_seconds':1}]}))
        row={'sid':'S01','datastream':'station|temperature','station_id':'station','parameter':'temperature','unit':'C',
             'result':7,'phenomenonTime':'2026-09-14T11:00:00Z','receivedTime':'2026-09-14T11:01:00Z'}
        raw=(json.dumps(row)+'\n').encode();self.file.write_bytes(raw)
        self.manifest['files'][0].update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        self.manifest.update(source_tree='b'*40,captured_at='2026-09-14T14:00:00.456789+02:00',
                             observation_prefix='complete-lf-lines/v1',configuration=[{
                                 'path':'research/COLLECTORS.json','bytes':cfg.stat().st_size,
                                 'sha256':hashlib.sha256(cfg.read_bytes()).hexdigest()}])
        self.bind_manifest();docs=self.root/'docs';docs.mkdir()
        with patch.multiple(collector,ROOT=self.root,CONFIG=cfg,LIVE=self.live):
            snapshot=collector.export()
        shutil.copyfile(snapshot,docs/'live-snapshot.json')
        with patch.multiple(history,ROWS=self.live/'rows',CONFIG=cfg,OUT=docs/'history.json'):
            history.main()
        city.build(docs)
        snap=json.loads(snapshot.read_bytes());hist=json.loads((docs/'history.json').read_bytes())
        self.assertEqual(snap['as_of'],'2026-09-14T12:00:00Z')
        self.assertEqual(hist['as_of'],snap['as_of'])
        self.assertEqual(snap['input_generation'],hist['input_generation'])
        self.assertEqual(hist['series'][0]['buckets']['2026-09-14T11']['mean'],7)
        self.assertEqual(self.file.read_bytes(),raw)
        cfg.write_text('{}')
        with self.assertRaisesRegex(ValueError,'configuration changed'):
            input_generation(self.live)

    def test_inventory_addition_removal_and_escape_are_refused(self):
        extra = self.file.with_name('extra.jsonl');extra.write_bytes(b'{}\n')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            with live_view.observation_view(self.live): pass
        extra.unlink()
        saved = self.file.read_bytes();self.file.unlink()
        with self.assertRaisesRegex(ValueError, 'inventory'):
            with live_view.observation_view(self.live): pass
        self.file.write_bytes(saved)
        self.manifest['files'][0]['path'] = '../escape.jsonl'
        self.bind_manifest()
        with self.assertRaisesRegex(ValueError, 'unsafe release input'):
            with live_view.observation_view(self.live): pass


class CaptureCounts(unittest.TestCase):
    def test_capacity_estimate_uses_last_manifest_before_deep_scan(self):
        with tempfile.TemporaryDirectory() as folder:
            source = pathlib.Path(folder)/'source'
            (source/'runtime').mkdir(parents=True)
            (source/'runtime/release-inputs-last.json').write_text(
                json.dumps({'timings': {'captured_bytes': 1234}}), encoding='utf-8')
            with patch.object(pathlib.Path, 'rglob', side_effect=AssertionError('deep scan attempted')):
                amount, origin = prepare_release.estimate_release_input_bytes(source)
            self.assertEqual(amount, 1234 + prepare_release.CAPACITY_ESTIMATE_MARGIN_BYTES)
            self.assertEqual(origin, 'runtime/release-inputs-last.json+512MiB')

    def test_immutable_siblings_prepare_the_output_directory_once(self):
        with tempfile.TemporaryDirectory() as folder:
            base=pathlib.Path(folder);source=base/'source';dest=base/'dest';dest.mkdir()
            receipts=source/'data/live/receipts/S01';receipts.mkdir(parents=True)
            for i in range(100):
                (receipts/f'{i:03}.json').write_bytes(b'{}\n')
            parent=dest/'data/live/receipts/S01'
            calls=[]
            mkdir=pathlib.Path.mkdir
            def tracked(path, *args, **kwargs):
                if path == parent: calls.append(path)
                return mkdir(path, *args, **kwargs)
            with patch.object(pathlib.Path, 'mkdir', tracked):
                inputs, _, _ = prepare_release.capture_inputs(source, dest)
            self.assertEqual(len(inputs),100)
            self.assertEqual(len(calls),1,'one directory must not issue a mkdir/stat pair for every file')
            self.assertTrue(all((dest/row['path']).read_bytes()==b'{}\n' for row in inputs))

    def test_capture_counts_and_paper_iterator_agree_across_block_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            base=pathlib.Path(folder);source=base/'source';dest=base/'dest';dest.mkdir()
            file=source/'data/live/rows/S01/sample.jsonl';file.parent.mkdir(parents=True)
            data=(b' \r\n\n'+b'x'*(1024*1024+3)+
                  b'\n\t\r\n{"receivedTime":"2026-09-14T11:01:00Z","x":2}\r\nunterminated')
            file.write_bytes(data)
            trace = base/'phases.jsonl'
            with patch.dict(os.environ, {'BEOPS_PHASE_TRACE': str(trace)}):
                inputs, _, _ = prepare_release.capture_inputs(source, dest)
            phases = [json.loads(line) for line in trace.read_text().splitlines()]
            self.assertEqual([row['event'] for row in phases], ['start', 'end']*4)
            self.assertEqual(phases[3]['bytes'], len(data))
            self.assertTrue(all(row['seconds'] >= 0 for row in phases if row['event'] == 'end'))
            item=next(row for row in inputs if row['path'].endswith('sample.jsonl'))
            self.assertEqual(item['newest_received_time'], '2026-09-14T11:01:00Z')
            evidence={}
            with patch.object(paper_numbers, 'ROOT', dest):
                self.assertEqual(paper_numbers.rows_on_disk(evidence), {'rows':2,'files':1})
            self.assertEqual(item['nonblank_lines'], 2)
            actual=evidence[item['path']]
            self.assertEqual(actual['sha256'], item['sha256'])
            prefix=data[:data.rfind(b'\n')+1]
            self.assertEqual(actual['bytes'], len(prefix))
            self.assertEqual((dest/item['path']).read_bytes(),prefix)
            self.assertEqual(file.read_bytes(),data)
            self.assertEqual(item['source_sha256'],hashlib.sha256(data).hexdigest())
            self.assertEqual(item['source_bytes'],len(data))
            self.assertEqual(item['excluded_tail_bytes'],len(b'unterminated'))

    def test_capture_indexes_state_key_across_block_boundary_without_a_second_read(self):
        with tempfile.TemporaryDirectory() as folder:
            base=pathlib.Path(folder);source=base/'source';dest=base/'dest';dest.mkdir()
            clean=source/'data/live/rows/S01/clean.jsonl';clean.parent.mkdir(parents=True)
            marked=source/'data/live/derived/mind/marked.jsonl';marked.parent.mkdir(parents=True)
            escaped=source/'data/live/derived/mind/escaped.jsonl'
            noisy=source/'data/live/derived/mind/noisy.jsonl'
            nested=source/'data/live/rows/S146/nested.jsonl'
            clean.write_bytes(b'{"result":"'+b'x'*(1024*1024)+b'"}\n')
            # The six-byte needle starts in one 1 MiB block and ends in the next.
            marked.write_bytes(b'{"padding":"'+b'x'*(1024*1024-17)+b'","state":"thought"}\n')
            escaped.write_bytes(b'{"\\u0073tate":"thought"}\n')
            noisy.write_bytes(b'{"path":"C:\\\\temp","word":"\\u0073tate"}\n')
            nested.parent.mkdir(parents=True)
            nested.write_bytes(b'{"phenomenonTimeCorrected":{"state":"estimated"},"result":1}\n')
            inputs, _, _ = prepare_release.capture_inputs(source, dest)
            indexed={row['path']:row for row in inputs}
            self.assertIs(indexed['data/live/rows/S01/clean.jsonl']['state_key_present'], False)
            self.assertIs(indexed['data/live/derived/mind/marked.jsonl']['state_key_present'], True)
            self.assertIs(indexed['data/live/derived/mind/escaped.jsonl']['state_key_present'], True)
            self.assertIs(indexed['data/live/derived/mind/noisy.jsonl']['state_key_present'], False)
            self.assertIs(indexed['data/live/rows/S146/nested.jsonl']['state_key_present'], False)
            for rel in ('data/live/rows/S01/clean.jsonl',
                        'data/live/derived/mind/marked.jsonl',
                        'data/live/derived/mind/escaped.jsonl',
                        'data/live/derived/mind/noisy.jsonl',
                        'data/live/rows/S146/nested.jsonl'):
                item=indexed[rel];observed=(dest/rel).stat()
                self.assertIs(item['state_index_sealed'], True)
                self.assertEqual(item['state_index_mtime_ns'], observed.st_mtime_ns)
                self.assertEqual(item['state_index_file_id'], observed.st_ino)
                self.assertFalse(observed.st_mode & (statmod.S_IWUSR|statmod.S_IWGRP|statmod.S_IWOTH))


if __name__ == '__main__':
    unittest.main()
