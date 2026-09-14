"""Real Git objects survive working-tree corruption; damaged evidence fails closed."""
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import published_editions as E


class PublishedEditions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = pathlib.Path(self.tmp.name)
        self.root = self.base/'mirror'; self.root.mkdir()
        self.edition = 'a'*64
        self.folder = self.root/E.PREFIX/self.edition; self.folder.mkdir(parents=True)
        self.payload = b'actual,source\n1,observation\n'
        (self.folder/'sources.csv').write_bytes(self.payload)
        self.manifest = {'edition_id': self.edition, 'files': [{'name': 'sources.csv',
            'bytes': len(self.payload), 'sha256': hashlib.sha256(self.payload).hexdigest()}]}
        (self.folder/'MANIFEST.json').write_text(json.dumps(self.manifest), encoding='utf-8')
        E.git(self.root, 'init', '-q')
        self.commit()

    def commit(self):
        E.git(self.root, 'add', 'public')
        E.git(self.root, '-c', 'user.name=Semir Poturak', '-c', 'user.email=scumutator@gmail.com', 'commit', '-qm', 'edition fixture')

    def test_export_uses_fixed_git_bytes_despite_null_working_files(self):
        oid = E.git(self.root, 'rev-parse', 'HEAD').decode().strip()
        for path in self.folder.iterdir(): path.write_bytes(b'\0'*path.stat().st_size)
        result = E.export(self.root, self.base/'out', oid)
        self.assertEqual(result['editions'], 1)
        self.assertEqual((self.base/'out'/self.edition/'sources.csv').read_bytes(), self.payload)

    def test_bad_committed_manifest_is_refused_before_any_export(self):
        (self.folder/'MANIFEST.json').write_bytes(b'\0'*20); self.commit()
        with self.assertRaisesRegex(ValueError, 'invalid published edition'):
            E.export(self.root, self.base/'out')
        self.assertFalse((self.base/'out').exists())

    def test_bad_committed_payload_is_refused(self):
        (self.folder/'sources.csv').write_bytes(b'changed'); self.commit()
        with self.assertRaisesRegex(ValueError, 'payload hash mismatch'): E.committed(self.root)

    def test_unsafe_or_duplicate_manifest_members_are_refused(self):
        for name in ('../outside', 'MANIFEST.json'):
            manifest = {'edition_id': self.edition, 'files': [{'name': name}]}
            with self.assertRaisesRegex(ValueError, 'unsafe or duplicate'):
                E.validate({'MANIFEST.json': json.dumps(manifest).encode()}, self.edition)

    def test_recovery_preserves_null_bytes_and_quarantines_unknown_without_invention(self):
        for path in self.folder.iterdir(): path.write_bytes(b'\0'*path.stat().st_size)
        unknown = self.root/E.PREFIX/('b'*64); unknown.mkdir()
        (unknown/'MANIFEST.json').write_bytes(b'\0'*31)
        result = E.recover(self.root, self.base/'evidence')
        self.assertEqual(result['restored_files'], 2)
        self.assertEqual(result['unresolved_local_editions'], ['b'*64])
        self.assertEqual((self.folder/'sources.csv').read_bytes(), self.payload)
        self.assertTrue((self.base/'evidence/before-recovery.zip').exists())
        self.assertFalse(unknown.exists())
        self.assertEqual((self.base/'_to_delete/beops-unresolved-editions-evidence'/('b'*64)/'MANIFEST.json').read_bytes(), b'\0'*31)

    def test_nonzero_unrelated_edit_is_never_overwritten(self):
        path = self.folder/'sources.csv'; path.write_bytes(b'other work')
        with self.assertRaisesRegex(ValueError, 'nonzero local edit'):
            E.recover(self.root, self.base/'evidence')
        self.assertEqual(path.read_bytes(), b'other work')
        self.assertFalse((self.base/'evidence').exists())

    def test_fixed_oid_is_retained_when_public_head_moves(self):
        oid = E.git(self.root, 'rev-parse', 'HEAD').decode().strip()
        (self.folder/'sources.csv').write_bytes(b'changed'); self.commit()
        self.assertEqual(E.committed(self.root, oid)[1][self.edition]['sources.csv'], self.payload)

    def test_preflight_precedes_expensive_capture_and_copy_uses_git(self):
        script = (ROOT/'tools/publish_github.ps1').read_text(encoding='utf-8-sig')
        self.assertLess(script.index('verify committed public editions'), script.index("$prepareArgs ="))
        self.assertNotIn('foreach ($edition in Get-ChildItem -LiteralPath $priorEditions', script)
        self.assertIn('copy verified committed public editions', script)


if __name__ == '__main__': unittest.main()
