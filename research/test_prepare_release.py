"""Release metadata savings preserve the archived scope and linked-file identity."""
import hashlib
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_release as P


class PreparationMetadata(unittest.TestCase):
    def test_capacity_source_size_uses_fixed_archive_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            source = pathlib.Path(folder)
            files = {'source.txt': b'code\n', 'research/code.txt': b'research\n',
                     'research/evidence/proof.txt': b'proof' * 100,
                     'research/_scratch/draft.txt': b'draft' * 200}
            for name, raw in files.items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            P.git(source, 'init', '-q')
            P.git(source, '-c', 'core.autocrlf=false', 'add', '.')
            P.git(source, '-c', 'user.name=Semir Poturak',
                  '-c', 'user.email=scumutator@gmail.com', 'commit', '-qm', 'fixture')
            oid = P.git(source, 'rev-parse', 'HEAD')
            # A working-tree change must not affect the fixed release estimate.
            (source / 'source.txt').write_bytes(b'new uncommitted bytes' * 100)
            size = P.archive_source_bytes(source, oid, P.archive_paths(source, oid))
            self.assertEqual(size, len(files['source.txt']) + len(files['research/code.txt']))

    def capture(self, source, dest):
        dest.mkdir()
        with patch.dict(os.environ, {'BEOPS_RELEASE_LINK_EVIDENCE': '1'}):
            return P.capture_inputs(source, dest)

    def evidence(self, base):
        source, dest = base / 'source', base / 'release'
        rel = pathlib.Path('research/evidence/S01/proof.txt')
        evidence = source / rel
        evidence.parent.mkdir(parents=True)
        evidence.write_bytes(b'permission evidence\n')
        return source, dest, rel, evidence

    def test_link_identity_reuses_source_stat_without_rereading_path(self):
        with tempfile.TemporaryDirectory() as folder:
            source, dest, rel, evidence = self.evidence(pathlib.Path(folder))
            with patch.object(P.os.path, 'samefile', side_effect=AssertionError('duplicate source stat')):
                rows, _, _ = self.capture(source, dest)
            self.assertTrue(os.path.samefile(evidence, dest / rel))
            self.assertEqual(rows[0]['sha256'], hashlib.sha256(evidence.read_bytes()).hexdigest())

    def test_copy_reported_as_link_is_rejected_even_with_equal_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            source, dest, _, _ = self.evidence(pathlib.Path(folder))
            with patch.object(P.os, 'link', side_effect=shutil.copyfile):
                with self.assertRaisesRegex(RuntimeError, 'linked input is not the captured file'):
                    self.capture(source, dest)


if __name__ == '__main__':
    unittest.main()
