import collections
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import storage_health as s
import guard

Usage = collections.namedtuple('Usage', 'total used free')


class Storage(unittest.TestCase):
    def write_capacity(self, root, *, at=None, free=None, **changes):
        required = 10 * s.GIB
        free = 9*s.GIB if free is None else free
        at = at or datetime.now(timezone.utc)
        record = {'schema': s.CAPACITY_SCHEMA, 'at': at.isoformat() if isinstance(at, datetime) else at,
                  'source': str(root), 'release_parent': str(root/'previous-retained-release'),
                  'input_bytes': 2*s.GIB, 'source_bytes': 0, 'required_bytes': required,
                  'reserve_bytes': s.RESERVE_BYTES, 'formula': s.CAPACITY_FORMULA,
                  'free_bytes': free, 'admitted': free >= required}
        record.update(changes)
        (root/'runtime').mkdir(exist_ok=True)
        (root/'runtime/release-capacity.json').write_text(json.dumps(record), encoding='utf-8')
        return record

    def inspect_capacity(self, root, free, now=None):
        with patch.dict(os.environ, {'BEOPS_RELEASE_ROOT': str(root/'configured-release')}, clear=False):
            result = s.inspect(root, lambda _: Usage(0, 0, free), now=now)
        return result, next(c for c in result['checks'] if c['name'] == 'release-capacity')

    def test_reserve_survives_complete_allocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            required = 4*1234 + 3*5678 + s.RESERVE_BYTES
            with self.assertRaisesRegex(RuntimeError, '2 GiB reserve'):
                s.require_release_capacity(tmp, 1234, 5678, lambda _: Usage(0,0,required-1))
            self.assertEqual(s.require_release_capacity(tmp,1234,5678,lambda _: Usage(0,0,required))['required_bytes'],required)
            self.assertEqual(list(pathlib.Path(tmp).iterdir()), [], 'generic admission must remain read-only')

    def test_floor_ok_but_actual_release_allocation_does_not_fit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.write_capacity(root)
            result, check = self.inspect_capacity(root, 9*s.GIB)
            self.assertEqual(result['checks'][0]['state'], 'OK')
            self.assertEqual((result['state'], check['state']), ('WARN', 'WARN'))
            self.assertEqual(check['required_bytes'], 10*s.GIB)

    def test_partitioned_capacity_keeps_full_copy_fallback_and_fixed_reserve(self):
        with tempfile.TemporaryDirectory() as tmp:
            required = 4 * 234 + 1000 + 3 * 5678 + 2 * s.GIB
            with self.assertRaises(s.ReleaseCapacityError):
                s.require_release_capacity(tmp, 1234, 5678, lambda _: Usage(0, 0, required-1),
                                           evidence_bytes=1000)
            capacity = s.require_release_capacity(tmp, 1234, 5678, lambda _: Usage(0, 0, required),
                                                  evidence_bytes=1000)
            self.assertEqual(capacity['required_bytes'], required)
            self.assertEqual(capacity['reserve_bytes'], 2 * s.GIB)
            self.assertEqual(list(pathlib.Path(tmp).iterdir()), [])

    def test_invalid_partition_counts_are_rejected_before_disk_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = ((100, 0, -1), (100, 0, 101), (100, 0, True), (100, 0, 1.0),
                     (True, 0, 0), (100, -1, 0), (100, 0, '1'),
                     (s.CAPACITY_MAX_BYTES, 0, 0), (0, s.CAPACITY_MAX_BYTES, 0))
            for input_bytes, source_bytes, evidence_bytes in cases:
                with self.subTest(counts=(input_bytes, source_bytes, evidence_bytes)):
                    with self.assertRaises(ValueError):
                        s.require_release_capacity(tmp, input_bytes, source_bytes,
                            lambda _: self.fail('invalid allocation reached disk probe'),
                            evidence_bytes=evidence_bytes)

    def test_partitioned_receipt_is_checked_without_rescanning_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.write_capacity(root, free=8*s.GIB, schema=s.CAPACITY_PARTITION_SCHEMA,
                input_bytes_from='live_stat_scan', evidence_bytes=s.GIB,
                evidence_bytes_from=s.CAPACITY_EVIDENCE_ORIGIN,
                formula=s.CAPACITY_PARTITION_FORMULA, required_bytes=7*s.GIB, admitted=True)
            with patch.object(pathlib.Path, 'rglob', side_effect=AssertionError('archive scan')):
                result, check = self.inspect_capacity(root, 8*s.GIB)
            self.assertEqual((result['state'], check['state']), ('OK', 'OK'))
            self.assertEqual(check['required_bytes'], 7*s.GIB)
            # The 2 GiB reserve remains included at the exact admission boundary.
            _, check = self.inspect_capacity(root, 7*s.GIB - 1)
            self.assertEqual(check['state'], 'WARN')

    def test_unproven_or_malformed_partition_receipts_cannot_claim_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            fields = dict(schema=s.CAPACITY_PARTITION_SCHEMA, input_bytes_from='live_stat_scan',
                evidence_bytes=s.GIB, evidence_bytes_from=s.CAPACITY_EVIDENCE_ORIGIN,
                formula=s.CAPACITY_PARTITION_FORMULA, required_bytes=7*s.GIB, admitted=True)
            cases = ({'input_bytes_from': 'cached'}, {'evidence_bytes_from': 'inferred'},
                     {'evidence_bytes': True}, {'evidence_bytes': -1}, {'evidence_bytes': 3*s.GIB},
                     {'evidence_bytes': 1.0}, {'evidence_bytes': None},
                     {'required_bytes': 6*s.GIB}, {'formula': s.CAPACITY_FORMULA},
                     {'schema': s.CAPACITY_SCHEMA, 'formula': s.CAPACITY_FORMULA,
                      'required_bytes': 10*s.GIB})
            for changes in cases:
                with self.subTest(changes=changes):
                    self.write_capacity(root, free=11*s.GIB, **{**fields, **changes})
                    result, check = self.inspect_capacity(root, 11*s.GIB)
                    self.assertEqual((result['state'], check['state']), ('UNKNOWN', 'UNKNOWN'))

    def test_compression_recovery_rechecks_free_space_not_old_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            record = self.write_capacity(root)
            with patch.object(pathlib.Path, 'rglob', side_effect=AssertionError('archive scan')):
                result, check = self.inspect_capacity(root, 11*s.GIB)
            self.assertEqual(result['state'], 'OK')
            self.assertEqual(check['state'], 'OK')
            self.assertFalse(check['measured_admitted'])
            self.assertEqual(check['measured_at'], record['at'])

    def test_stale_success_and_failure_do_not_claim_current_readiness(self):
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for admitted_free in (9*s.GIB, 11*s.GIB):
                with self.subTest(admitted_free=admitted_free):
                    self.write_capacity(root, at=now-timedelta(minutes=91), free=admitted_free)
                    result, check = self.inspect_capacity(root, 11*s.GIB, now)
                    self.assertEqual((result['state'], check['state']), ('WARN', 'WARN'))
                    self.assertNotIn('free_bytes', check)
                    self.assertIn('older than 90 minutes', check['why'])

    def test_prior_manual_target_does_not_select_the_wrong_volume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            configured = root/'configured-release'; configured.mkdir()
            previous = root/'previous-retained-release'; previous.mkdir()
            self.write_capacity(root, free=11*s.GIB)
            def usage(path):
                return Usage(0, 0, 9*s.GIB if path == configured else 11*s.GIB)
            with patch.dict(os.environ, {'BEOPS_RELEASE_ROOT': str(configured)}, clear=False):
                result = s.inspect(root, usage)
            check = next(c for c in result['checks'] if c['name'] == 'release-capacity')
            self.assertEqual(check['state'], 'WARN')
            self.assertEqual(check['path'], str(configured))
            self.assertEqual(check['measured_release_parent'], str(previous))

    def test_missing_receipt_only_reports_basic_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, check = self.inspect_capacity(pathlib.Path(tmp), 11*s.GIB)
            self.assertEqual(check['state'], 'WARN')
            self.assertIn('not measured', check['why'])
            self.assertEqual(list(pathlib.Path(tmp).iterdir()), [])

    def test_invalid_capacity_receipts_cannot_claim_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            cases = ({'schema': 'wrong'}, {'source': str(root/'another-source')},
                     {'input_bytes': True}, {'required_bytes': 1}, {'admitted': True},
                     {'release_parent': 'relative'}, {'at': '2026-09-27T00:00:00'},
                     {'at': (datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()})
            for fields in cases:
                with self.subTest(fields=fields):
                    self.write_capacity(root, **fields)
                    result, check = self.inspect_capacity(root, 11*s.GIB)
                    self.assertEqual((result['state'], check['state']), ('UNKNOWN', 'UNKNOWN'))
            for raw in ('{broken', ' '*(s.CAPACITY_MAX_RECEIPT_BYTES+1)):
                (root/'runtime/release-capacity.json').write_text(raw)
                result, check = self.inspect_capacity(root, 11*s.GIB)
                self.assertEqual(check['state'], 'UNKNOWN')

    def test_allocation_warning_keeps_guard_backward_compatible(self):
        record = {'verdict': guard.OK}
        with patch.object(guard, 'run', return_value=record), \
             patch.object(s, 'inspect', return_value={'state': 'WARN'}), \
             patch.object(guard, 'report', return_value='allocation warning'), \
             patch.object(sys, 'argv', ['guard.py', '--dry']):
            self.assertEqual(guard.main(), 0)
            self.assertEqual(record['verdict'], guard.WARN)

    def test_inspection_preserves_pause_and_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);(root/'runtime').mkdir();(root/'runtime/MAINTENANCE').write_text('operator pause')
            result=s.inspect(root, lambda _: Usage(9*s.GIB,8*s.GIB,s.GIB))
            self.assertEqual(result['state'],'WARN')
            self.assertEqual((root/'runtime/MAINTENANCE').read_text(),'operator pause')
            self.assertEqual(len(list(root.rglob('*'))),2)

    def test_unknown_capacity_cannot_be_ok(self):
        def unavailable(_): raise OSError('unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(s.inspect(tmp,unavailable)['state'],'UNKNOWN')

    def test_unknown_storage_reaches_guard_verdict(self):
        record={'verdict':guard.OK}
        with patch.object(guard,'run',return_value=record), patch.object(s,'inspect',return_value={'state':'UNKNOWN'}), patch.object(guard,'report',return_value='unknown'), patch.object(sys,'argv',['guard.py','--dry']):
            self.assertEqual(guard.main(),1)
            self.assertEqual(record['verdict'],guard.UNKNOWN)

    @unittest.skipUnless(sys.platform=='win32','Windows scheduler')
    def test_abandoned_cleanup_preserves_live_retained_and_unowned_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=pathlib.Path(tmp);source=base/'source';source.mkdir();releases=base/'releases';releases.mkdir()
            created=(datetime.now(timezone.utc)-timedelta(hours=3)).isoformat()
            folders=[]
            for n,pid,retained,schema in [('1',2147483647,False,'beops-generated-workspace/v2'),
                                          ('2',os.getpid(),False,'beops-generated-workspace/v2'),
                                          ('3',2147483647,True,'beops-generated-workspace/v2'),
                                          ('4',2147483647,False,'legacy')]:
                folder=releases/('beops-release-'+n*32);folder.mkdir();(folder/'runtime').mkdir()
                (folder/'sentinel').write_text('preserve unless provably abandoned')
                (folder/'.beops-generated-workspace.json').write_text(json.dumps({'schema':schema,'source':str(source),'destination':str(folder),'source_oid':'abc','owner_pid':pid,'created_at':created,'retained':retained}))
                folders.append(folder)
            command=f". '{ROOT/'tools/publish_safety.ps1'}'; Clear-BeopsAbandonedReleases -SourceRoot '{source}' -BaseRoot '{releases}'"
            result=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(folders[0].exists(),result.stdout)
            self.assertTrue(all((f/'sentinel').exists() for f in folders[1:]))

    @unittest.skipUnless(sys.platform=='win32','Windows scheduler')
    def test_half_hour_tick_runs_after_normal_success_but_slow_success_still_rests(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt=pathlib.Path(tmp)/'receipt.json'
            attempt=pathlib.Path(tmp)/'attempt.json'
            status=pathlib.Path(tmp)/'publish-scheduler-status.json'
            receipt.write_text(json.dumps({'published':True,'cycle_started_at':'2026-09-14T00:00:00Z','at':'2026-09-14T00:07:00Z'}))
            def call(at):
                return subprocess.run(['powershell','-NoProfile','-File',str(ROOT/'tools/publish_due.ps1'),'-ReceiptPath',str(receipt),'-AttemptReceiptPath',str(attempt),'-StatusPath',str(status),'-NowUtc',at],capture_output=True,timeout=20).returncode
            self.assertEqual(call('2026-09-14T00:10:00Z'),75)
            self.assertEqual(call('2026-09-14T00:30:00Z'),0)
            receipt.write_text(json.dumps({'published':True,'cycle_started_at':'2026-09-14T00:00:00Z','at':'2026-09-14T00:40:00Z'}))
            self.assertEqual(call('2026-09-14T00:40:00Z'),75)
            self.assertEqual(call('2026-09-14T00:44:59Z'),75)
            self.assertEqual(call('2026-09-14T00:45:00Z'),0)
