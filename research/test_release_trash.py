"""2026-10-01: workspace cleanup leaves the critical path of a publication.

Remove-Item over a 64,000-file workspace ran before capture and took tens of minutes with no
phase trace (the "stall after resolve release OID"). Now an owned workspace is renamed to
beops-trash-<32 hex> at once, under the same boundary checks, and deleted with rd at the end of
the cycle. What must stay true: an unowned or misnamed directory is never touched, a read-only
(sealed) file does not stop the deletion, and the original path is gone immediately."""
import json
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAFETY = ROOT / 'tools' / 'publish_safety.ps1'


def ps(script):
    return subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
                           ". '" + str(SAFETY) + "'; " + script],
                          capture_output=True, text=True, timeout=120)


@unittest.skipUnless(os.name == 'nt' and shutil.which('powershell'), 'Windows PowerShell semantics')
class ReleaseTrash(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = pathlib.Path(self.tmp.name)
        self.source, self.base = base / 'source', base / 'releases'
        self.source.mkdir()
        self.base.mkdir()
        self.run_root = self.base / ('beops-release-' + 'a' * 32)
        (self.run_root / 'data/live/rows/S01').mkdir(parents=True)
        sealed = self.run_root / 'data/live/rows/S01/2026-09.jsonl'
        sealed.write_text('{"x":1}\n', encoding='utf-8')
        sealed.chmod(stat.S_IREAD)
        (self.run_root / '.beops-generated-workspace.json').write_text(json.dumps({
            'schema': 'beops-generated-workspace/v2', 'destination': str(self.run_root),
            'source': str(self.source), 'retained': False, 'owner_pid': 1}), encoding='utf-8')

    def test_owned_workspace_moves_at_once_and_is_deleted_at_cycle_end(self):
        r = ps("$t = Move-BeopsReleaseToTrash -Path '%s' -SourceRoot '%s' -BaseRoot '%s'; Write-Output $t"
               % (self.run_root, self.source, self.base))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.run_root.exists(), 'the release path is free immediately')
        trash = list(self.base.glob('beops-trash-*'))
        self.assertEqual(len(trash), 1)
        self.assertRegex(trash[0].name, r'^beops-trash-[a-f0-9]{32}$')
        r = ps("Clear-BeopsReleaseTrash -BaseRoot '%s'" % self.base)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(list(self.base.iterdir()), [], 'trash with a read-only file is deleted')

    def test_unowned_directory_is_never_touched(self):
        (self.run_root / '.beops-generated-workspace.json').unlink()
        r = ps("Move-BeopsReleaseToTrash -Path '%s' -SourceRoot '%s' -BaseRoot '%s'" % (self.run_root, self.source, self.base))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.run_root.exists())
        stray = self.base / ('beops-trash-' + 'b' * 32)
        stray.mkdir()  # a trash-named directory without the workspace marker is not ours either
        ps("Clear-BeopsReleaseTrash -BaseRoot '%s'" % self.base)
        self.assertTrue(stray.exists())

    def test_misnamed_directory_is_refused(self):
        odd = self.base / 'beops-release-not-hex'
        odd.mkdir()
        r = ps("Move-BeopsReleaseToTrash -Path '%s' -SourceRoot '%s' -BaseRoot '%s'" % (odd, self.source, self.base))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('boundary refused', r.stdout + r.stderr)
        self.assertTrue(odd.exists())

    def test_background_deletion_releases_the_cycle_at_once(self):
        """2026-10-02: deleting two 66,000-file workspaces held the preparation lock for 40 and 55 minutes.
        In the publisher's final step the deletion is detached: the call returns at once, the folder is
        gone shortly after, and a second call while it runs does not start another deleter."""
        import time
        r = ps("$null = Move-BeopsReleaseToTrash -Path '%s' -SourceRoot '%s' -BaseRoot '%s'" % (self.run_root, self.source, self.base))
        self.assertEqual(r.returncode, 0, r.stderr)
        r = ps("Clear-BeopsReleaseTrash -BaseRoot '%s' -Background" % self.base)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('started in background', r.stdout)
        deadline = time.time() + 60
        while time.time() < deadline and any(self.base.iterdir()):
            time.sleep(0.5)
        self.assertEqual(list(self.base.iterdir()), [], 'the detached deleter removed the trash and its runner')

    def test_the_seal_on_the_live_file_survives_deletion(self):
        """2026-10-02: a release links sealed months (same inode as the live record) and the read-only
        attribute IS the seal. attrib -r over a trash workspace lifted it on the live file too. With an
        interpreter, the background deleter is tools/release_trash.py, which removes the read-only name
        without changing the shared file's attributes."""
        import sys, time
        live = pathlib.Path(self.tmp.name) / 'live-2026-08.jsonl'
        live.write_text('{"sealed":1}\n', encoding='utf-8')
        live.chmod(stat.S_IREAD)
        os.link(live, self.run_root / 'data/live/rows/S01/2026-08.jsonl')
        r = ps("$null = Move-BeopsReleaseToTrash -Path '%s' -SourceRoot '%s' -BaseRoot '%s'" % (self.run_root, self.source, self.base))
        self.assertEqual(r.returncode, 0, r.stderr)
        r = ps("Clear-BeopsReleaseTrash -BaseRoot '%s' -Background -Python '%s'" % (self.base, sys.executable))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('started in background', r.stdout)
        deadline = time.time() + 60
        while time.time() < deadline and any(self.base.iterdir()):
            time.sleep(0.5)
        self.assertEqual(list(self.base.iterdir()), [], 'the trash is gone')
        self.assertTrue(live.exists(), 'the live record is untouched')
        self.assertFalse(os.stat(live).st_mode & stat.S_IWRITE, 'the live record is still sealed (read-only)')

    def tearDown(self):
        for f in pathlib.Path(self.tmp.name).rglob('*'):
            try:
                f.chmod(stat.S_IREAD | stat.S_IWRITE)
            except OSError:
                pass


if __name__ == '__main__':
    unittest.main()
