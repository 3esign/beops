"""P1: one immutable walk, cached hashes, and a reproducible Merkle root."""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_release as P  # noqa: E402
import release_inventory as I  # noqa: E402


class ReleaseInventory(unittest.TestCase):
    def test_merkle_root_is_order_independent_and_groups_are_stable(self):
        rows = [
            {'path': 'research/evidence/S1/a.txt', 'sha256': 'a' * 64},
            {'path': 'data/live/receipts/S1/one.json', 'sha256': 'b' * 64},
        ]
        left = I.inventory_summary(rows)
        right = I.inventory_summary(list(reversed(rows)))
        self.assertEqual(left, right)
        self.assertEqual(left['files'], 2)
        self.assertEqual(set(left['groups']), {'research/evidence', 'data/live/receipts'})

    def test_second_inventory_reuses_hashes_but_still_observes_current_stats(self):
        with tempfile.TemporaryDirectory() as folder:
            base = pathlib.Path(folder)
            source = base / 'source'
            evidence = source / 'research/evidence/S1/proof.txt'
            receipt = source / 'data/live/receipts/S1/one.json'
            evidence.parent.mkdir(parents=True)
            receipt.parent.mkdir(parents=True)
            evidence.write_bytes(b'proof')
            receipt.write_bytes(b'{"state":"ok"}\n')
            cache = base / 'inventory-cache.jsonl'

            first, rows, first_metrics, _ = I.build_inventory(source, cache)
            I.save_cache(cache, rows)
            with patch.object(I, '_sha256_file', side_effect=AssertionError('cache miss')):
                second, _, second_metrics, entries = I.build_inventory(source, cache)

            self.assertEqual(first, second)
            self.assertEqual(first_metrics['hashed_files'], 2)
            self.assertEqual(second_metrics['hashed_files'], 0)
            self.assertEqual(len(entries), 2)

    def test_capture_publishes_inventory_root_and_cache_without_a_second_immutable_walk(self):
        with tempfile.TemporaryDirectory() as folder:
            base = pathlib.Path(folder)
            source = base / 'source'
            dest = base / 'release'
            evidence = source / 'research/evidence/S1/proof.txt'
            evidence.parent.mkdir(parents=True)
            evidence.write_bytes(b'proof')
            dest.mkdir()
            metrics = {}
            with patch.object(pathlib.Path, 'rglob', side_effect=AssertionError('immutable rglob')):
                rows, _, _ = P.capture_inputs(source, dest, metrics)

            immutable = [row for row in rows if row['path'].startswith('research/evidence/')]
            expected = I.inventory_summary(immutable)
            self.assertEqual(metrics['inventory']['root'], expected['root'])
            self.assertEqual(metrics['inventory_root'], expected['root'])
            self.assertTrue(metrics['inventory_cache_saved'])
            cache = source / 'runtime/inventory-cache.jsonl'
            self.assertTrue(cache.is_file())
            self.assertEqual(json.loads(cache.read_text(encoding='utf-8').splitlines()[0])['schema'],
                             I.CACHE_SCHEMA)


if __name__ == '__main__':
    unittest.main()
