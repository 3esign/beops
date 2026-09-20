import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mirror_transaction


def sha(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(root, paths):
    docs = root / 'docs'
    docs.mkdir(exist_ok=True)
    rows = []
    for rel in sorted(paths):
        p = root / rel
        rows.append({'path': rel, 'bytes': p.stat().st_size, 'sha256': sha(p)})
    (docs / 'export-manifest.json').write_text(json.dumps({'files': rows}), encoding='utf-8')


@unittest.skipUnless(shutil.which('git'), 'git required')
class MirrorTransaction(unittest.TestCase):
    def test_partial_capture_keeps_unchanged_large_files_out_of_rollback_archive(self):
        with tempfile.TemporaryDirectory(dir=str(ROOT / 'runtime')) as folder:
            base = pathlib.Path(folder)
            mirror = base / 'mirror'
            stage = base / 'stage'
            mirror.mkdir()
            stage.mkdir()
            (mirror / 'docs').mkdir()
            (stage / 'docs').mkdir()
            unchanged = 'docs/unchanged.json'
            changed = 'docs/changed.json'
            deleted = 'docs/delete-me.json'
            new = 'docs/new.json'
            (mirror / unchanged).write_text('same' * 20000, encoding='utf-8')
            (mirror / changed).write_text('old', encoding='utf-8')
            (mirror / deleted).write_text('delete', encoding='utf-8')
            (stage / unchanged).write_text('same' * 20000, encoding='utf-8')
            (stage / changed).write_text('new', encoding='utf-8')
            (stage / new).write_text('new file', encoding='utf-8')
            write_manifest(mirror, [unchanged, changed, deleted])
            write_manifest(stage, [unchanged, changed, new])
            subprocess.run(['git', 'init', '-q', str(mirror)], check=True, timeout=10)
            subprocess.run(['git', '-C', str(mirror), 'add', '.'], check=True, timeout=10)
            subprocess.run(['git', '-C', str(mirror), '-c', 'user.name=Semir Poturak',
                            '-c', 'user.email=scumutator@gmail.com', 'commit', '-qm', 'mirror fixture'],
                           check=True, timeout=10)

            capture = mirror_transaction.capture_changes(mirror, stage)
            archive = pathlib.Path(capture['archive'])
            with mirror_transaction.zipfile.ZipFile(archive) as z:
                manifest = json.loads(z.read('COPY_MANIFEST.json'))
            self.assertTrue(manifest['partial'])
            self.assertIn(changed, manifest['files'])
            self.assertIn(deleted, manifest['files'])
            self.assertIn('docs/export-manifest.json', manifest['files'])
            self.assertNotIn(unchanged, manifest['files'])

            (mirror / changed).write_text('new', encoding='utf-8')
            (mirror / deleted).unlink()
            (mirror / new).write_text('new file', encoding='utf-8')
            result = mirror_transaction.restore(mirror, archive)
            self.assertEqual(result['restored'], 3)
            self.assertEqual((mirror / unchanged).read_text(encoding='utf-8'), 'same' * 20000)
            self.assertEqual((mirror / changed).read_text(encoding='utf-8'), 'old')
            self.assertEqual((mirror / deleted).read_text(encoding='utf-8'), 'delete')
            self.assertFalse((mirror / new).exists())
            status = subprocess.run(['git', '-C', str(mirror), 'status', '--porcelain'],
                                    check=True, capture_output=True, text=True, timeout=10).stdout.strip()
            self.assertEqual(status, '')


if __name__ == '__main__':
    unittest.main()
