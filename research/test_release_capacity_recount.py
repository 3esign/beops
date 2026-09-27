"""A refused cached estimate may be recounted; the release reserve stays fixed."""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import call, patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_release as P
import storage_health as S

TEMP_ROOT = pathlib.Path(os.environ.get('BEOPS_TEST_TEMP_ROOT', ROOT / 'runtime' / 'test-capacity'))


class CapacityRecount(unittest.TestCase):
    def setUp(self):
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.source = self.root / 'source'
        (self.source / 'runtime').mkdir(parents=True)
        manifest = self.source / 'runtime/release-inputs-last.json'
        manifest.write_text(json.dumps({'timings': {'captured_bytes': 100}}), encoding='utf-8')
        live = self.source / 'data/live'
        live.mkdir(parents=True)
        (live / 'rows.jsonl').write_bytes(b'x' * 200)
        (live / 'ignored.lock').write_bytes(b'x' * 300)
        (live / 'ignored.tmp').write_bytes(b'x' * 400)
        self.estimate, self.origin = P.estimate_release_input_bytes(self.source)
        self.source_bytes = 47

    def capacity(self):
        return P.release_capacity(self.source, self.root, self.estimate, self.origin, self.source_bytes)

    def test_positive_cached_fast_path_never_scans(self):
        required = 4 * self.estimate + 3 * self.source_bytes + S.RESERVE_BYTES
        with patch.object(S.shutil, 'disk_usage', return_value=SimpleNamespace(free=required)), \
             patch.object(pathlib.Path, 'rglob', side_effect=AssertionError('unnecessary deep scan')):
            capacity, amount, origin = self.capacity()
        self.assertEqual((amount, origin), (self.estimate, P.CAPACITY_CACHED_ORIGIN))
        self.assertEqual(capacity, {'free_bytes': required, 'required_bytes': required,
                                    'reserve_bytes': 2 * 1024 ** 3})

    def test_refused_cache_uses_exact_inventory_with_same_guard_and_source_bytes(self):
        exact = 200
        required = 4 * exact + 3 * self.source_bytes + S.RESERVE_BYTES
        with patch.object(S.shutil, 'disk_usage', return_value=SimpleNamespace(free=required)), \
             patch.object(P, 'require_release_capacity', wraps=S.require_release_capacity) as guard:
            capacity, amount, origin = self.capacity()
        self.assertEqual((amount, origin), (exact, 'live_stat_scan'))
        self.assertEqual(capacity['required_bytes'], required)
        self.assertEqual(capacity['reserve_bytes'], 2 * 1024 ** 3)
        self.assertEqual(guard.call_args_list, [call(self.root, self.estimate, self.source_bytes),
                                               call(self.root, exact, self.source_bytes)])
        receipt = json.loads((self.source/'runtime/release-capacity.json').read_text())
        self.assertEqual(receipt['schema'], S.CAPACITY_SCHEMA)
        self.assertEqual(receipt['formula'], S.CAPACITY_FORMULA)
        self.assertEqual(receipt['source'], str(self.source))
        self.assertEqual(receipt['release_parent'], str(self.root))
        self.assertTrue(receipt['admitted'])
        self.assertEqual(receipt['input_bytes'], exact)
        self.assertEqual(receipt['input_bytes_from'], 'live_stat_scan')
        self.assertEqual(receipt['required_bytes'], required)

    def test_fresh_growth_still_refuses_without_third_attempt(self):
        exact = self.estimate + 1000
        available = 4 * self.estimate + 3 * self.source_bytes + S.RESERVE_BYTES - 1
        with patch.object(S.shutil, 'disk_usage', return_value=SimpleNamespace(free=available)), \
             patch.object(P, 'estimate_release_input_bytes', return_value=(exact, 'live_stat_scan')) as scan, \
             patch.object(P, 'require_release_capacity', wraps=S.require_release_capacity) as guard:
            with self.assertRaisesRegex(P.ReleaseCapacityError, str(4 * exact + 3 * self.source_bytes + S.RESERVE_BYTES)):
                self.capacity()
        scan.assert_called_once_with(self.source, use_cached=False)
        self.assertEqual(guard.call_args_list, [call(self.root, self.estimate, self.source_bytes),
                                               call(self.root, exact, self.source_bytes)])
        receipt = json.loads((self.source/'runtime/release-capacity.json').read_text())
        self.assertFalse(receipt['admitted'])
        self.assertEqual(receipt['input_bytes'], exact)
        self.assertEqual(receipt['free_bytes'], available)
        self.assertEqual(receipt['required_bytes'], 4*exact + 3*self.source_bytes + S.RESERVE_BYTES)

    def test_exact_or_unknown_origin_does_not_retry_a_refusal(self):
        for origin in ['live_stat_scan', 'unrecognized-estimate']:
            with self.subTest(origin=origin), \
                 patch.object(S.shutil, 'disk_usage', return_value=SimpleNamespace(free=0)), \
                 patch.object(P, 'estimate_release_input_bytes', side_effect=AssertionError('unexpected retry')):
                with self.assertRaises(P.ReleaseCapacityError):
                    P.release_capacity(self.source, self.root, 200, origin, self.source_bytes)

    def test_disk_space_is_measured_again_after_the_scan(self):
        cached_required = 4 * self.estimate + 3 * self.source_bytes + S.RESERVE_BYTES
        exact_required = 4 * 200 + 3 * self.source_bytes + S.RESERVE_BYTES
        with patch.object(S.shutil, 'disk_usage', side_effect=[
                SimpleNamespace(free=cached_required - 1),
                SimpleNamespace(free=exact_required - 1)]) as usage:
            with self.assertRaisesRegex(P.ReleaseCapacityError, str(exact_required - 1) + ' free bytes'):
                self.capacity()
        self.assertEqual(usage.call_count, 2)

    def test_unrelated_guard_error_propagates_without_recount(self):
        failure = RuntimeError('unrelated storage failure')
        with patch.object(P, 'require_release_capacity', side_effect=failure), \
             patch.object(P, 'estimate_release_input_bytes') as scan:
            with self.assertRaises(RuntimeError) as result:
                self.capacity()
        self.assertIs(result.exception, failure)
        scan.assert_not_called()

    def test_recount_scan_error_propagates_without_allocation_or_guard_retry(self):
        failure = OSError('stat failed')
        with patch.object(S.shutil, 'disk_usage', return_value=SimpleNamespace(free=0)), \
             patch.object(P, 'estimate_release_input_bytes', side_effect=failure), \
             patch.object(P, 'require_release_capacity', wraps=S.require_release_capacity) as guard:
            with self.assertRaises(OSError) as result:
                self.capacity()
        self.assertIs(result.exception, failure)
        guard.assert_called_once_with(self.root, self.estimate, self.source_bytes)

    def test_prepare_uses_recount_before_creating_release_directory(self):
        destination = self.root / 'releases/candidate'
        with patch.object(P, 'git', return_value='a' * 40), \
             patch.object(P, 'archive_paths', return_value=['source.py']), \
             patch.object(P, 'archive_source_bytes', return_value=self.source_bytes), \
             patch.object(S.shutil, 'disk_usage', return_value=SimpleNamespace(free=0)), \
             patch.object(P, 'release_capacity', wraps=P.release_capacity) as capacity, \
             patch.object(P, 'estimate_release_input_bytes', wraps=P.estimate_release_input_bytes) as estimate:
            with self.assertRaises(P.ReleaseCapacityError):
                P.prepare(self.source, destination)
        self.assertFalse(destination.exists())
        capacity.assert_called_once_with(self.source, destination.parent, self.estimate,
                                         P.CAPACITY_CACHED_ORIGIN, self.source_bytes)
        self.assertEqual(estimate.call_args_list, [call(self.source), call(self.source, use_cached=False)])


if __name__ == '__main__':
    unittest.main()
