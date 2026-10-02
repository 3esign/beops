"""The chain of confirmations records every cycle outcome and survives scrutiny.

Each link commits to the previous one by hash, so editing history breaks the
chain loudly. Appending is idempotent per receipt, refuses a broken chain, and
attaches the P1 inventory root only when the last manifest provably describes
the receipt's own source commit. The chain never gates a publish.
"""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import release_chain as C


def receipt(at='2026-09-30T14:00:00Z', head='a' * 40, published=False, why='x'):
    return {'schema': 'beops-publish-receipt/v1', 'at': at, 'source_head': head,
            'published': published, 'tests_ok': published, 'site_verified': published,
            'pushed': published, 'why': why}


class ChainTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir=str(ROOT / 'runtime' / 'tmp')
                                                if (ROOT / 'runtime' / 'tmp').is_dir() else None)
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        (self.root / 'data' / 'live').mkdir(parents=True)

    def write_receipt(self, row):
        path = self.root / 'data' / 'live' / 'publish-receipt.json'
        path.write_text(json.dumps(row), encoding='utf-8')
        return path

    def test_links_grow_and_verify(self):
        first = C.append_link(self.root, self.write_receipt(receipt()))
        self.assertTrue(first['appended'])
        second = C.append_link(self.root, self.write_receipt(
            receipt(at='2026-09-30T15:00:00Z', published=True, why='')))
        self.assertEqual(second['seq'], 2)
        links = C.read_chain(self.root / C.CHAIN_REL)
        self.assertIsNone(C.verify_links(links))
        self.assertEqual(links[1]['prev'], links[0]['this'])
        code, message = C.verify(self.root, self.root / 'data' / 'live' / 'publish-receipt.json')
        self.assertEqual(code, 0, message)

    def test_append_is_idempotent_per_receipt(self):
        path = self.write_receipt(receipt())
        C.append_link(self.root, path)
        again = C.append_link(self.root, path)
        self.assertFalse(again['appended'])
        self.assertEqual(len(C.read_chain(self.root / C.CHAIN_REL)), 1)

    def test_tamper_is_a_stop_and_append_refuses(self):
        C.append_link(self.root, self.write_receipt(receipt()))
        C.append_link(self.root, self.write_receipt(receipt(at='2026-09-30T15:00:00Z')))
        chain = self.root / C.CHAIN_REL
        rows = chain.read_text(encoding='utf-8').splitlines()
        first = json.loads(rows[0])
        first['outcome']['why'] = 'edited history'
        chain.write_text('\n'.join([json.dumps(first, sort_keys=True, separators=(',', ':'))]
                                   + rows[1:]) + '\n', encoding='utf-8')
        code, message = C.verify(self.root)
        self.assertEqual(code, 1)
        self.assertIn('stored hash', message)
        with self.assertRaises(ValueError):
            C.append_link(self.root, self.write_receipt(receipt(at='2026-09-30T16:00:00Z')))

    def test_chain_behind_receipt_is_a_warning_not_silence(self):
        C.append_link(self.root, self.write_receipt(receipt()))
        newer = self.write_receipt(receipt(at='2026-09-30T17:00:00Z', published=True, why=''))
        code, message = C.verify(self.root, newer)
        self.assertEqual(code, 2)
        self.assertIn('behind the receipt', message)

    def test_empty_chain_warns(self):
        code, message = C.verify(self.root)
        self.assertEqual(code, 2)
        self.assertIn('empty', message)

    def test_inventory_root_only_for_matching_oid(self):
        manifest = self.root / 'runtime' / 'release-inputs-last.json'
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({'source_oid': 'a' * 40,
                                        'inventory': {'root': 'f' * 64}}), encoding='utf-8')
        C.append_link(self.root, self.write_receipt(receipt(head='a' * 40)))
        C.append_link(self.root, self.write_receipt(
            receipt(at='2026-09-30T15:00:00Z', head='b' * 40)))
        links = C.read_chain(self.root / C.CHAIN_REL)
        self.assertEqual(links[0]['inventory_root'], 'f' * 64)
        self.assertIsNone(links[1]['inventory_root'])

    def test_bom_receipt_is_readable(self):
        path = self.root / 'data' / 'live' / 'publish-receipt.json'
        path.write_bytes(b'\xef\xbb\xbf' + json.dumps(receipt()).encode('utf-8'))
        self.assertTrue(C.append_link(self.root, path)['appended'])


if __name__ == '__main__':
    unittest.main()
