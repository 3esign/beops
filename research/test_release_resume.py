"""An interrupted release preparation resumes instead of recapturing the world.

The fixed-source phase writes a progress marker only after extraction finished;
a later run trusts it only together with the workspace's own Git HEAD (verify on
the artefact). Mutable inputs are always recaptured fresh; hardlinked evidence
is reused only when it is the very same inode.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_release as P

SAFETY = ROOT / 'tools' / 'publish_safety.ps1'


def fixture_source(base):
    source = base / 'source'
    for name, raw in (('source.txt', b'code\n'), ('research/code.txt', b'research\n')):
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    evidence = source / 'research/evidence/S01/proof.txt'
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b'permission evidence\n')
    rows = source / 'data/live/rows/r1.jsonl'
    rows.parent.mkdir(parents=True)
    rows.write_text('{"state": {"x": 1}}\n', encoding='utf-8')
    P.git(source, 'init', '-q')
    P.git(source, '-c', 'core.autocrlf=false', 'add', 'source.txt', 'research/code.txt')
    P.git(source, '-c', 'user.name=Semir Poturak', '-c', 'user.email=scumutator@gmail.com',
          'commit', '-qm', 'fixture')
    return source


class ResumePreparation(unittest.TestCase):
    def prepared(self, base):
        source = fixture_source(base)
        dest = base / ('beops-release-' + 'a' * 32)
        first = P.prepare(source, dest, owner_pid=999999999)
        return source, dest, first

    def test_resume_skips_fixed_source_and_replays_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            source, dest, first = self.prepared(pathlib.Path(folder))
            # Simulate the interruption mid-capture: the manifest of the killed
            # run never came to exist, the progress marker did.
            (dest / 'runtime/release-inputs.json').unlink()
            calls = []
            real_git = P.git
            def spy(root, *args, **kwargs):
                calls.append(args[0])
                return real_git(root, *args, **kwargs)
            with patch.object(P, 'git', side_effect=spy):
                second = P.prepare(source, dest, owner_pid=os.getpid(), resume=True)
            self.assertNotIn('clone', calls)
            self.assertNotIn('archive', calls)
            self.assertEqual(first['source_oid'], second['source_oid'])
            manifest = json.loads((dest / 'runtime/release-inputs.json').read_text(encoding='utf-8'))
            self.assertTrue(manifest['timings'].get('fixed_source_resumed'))
            # The sealed read-only rows file from the first run was recaptured, not refused.
            rows = [row for row in manifest['files'] if row['path'] == 'data/live/rows/r1.jsonl']
            self.assertEqual(len(rows), 1)
            # Linked evidence still shares bytes with the source (same inode reused).
            self.assertTrue(os.path.samefile(source / 'research/evidence/S01/proof.txt',
                                             dest / 'research/evidence/S01/proof.txt'))
            # Ownership moved to the resuming process.
            owner = json.loads((dest / '.beops-generated-workspace.json').read_text(encoding='utf-8'))
            self.assertEqual(owner['owner_pid'], os.getpid())

    def test_resume_refuses_a_workspace_at_a_different_oid(self):
        with tempfile.TemporaryDirectory() as folder:
            source, dest, _ = self.prepared(pathlib.Path(folder))
            (dest / 'runtime/release-inputs.json').unlink()
            (source / 'source.txt').write_bytes(b'moved on\n')
            P.git(source, '-c', 'core.autocrlf=false', 'add', 'source.txt')
            P.git(source, '-c', 'user.name=Semir Poturak', '-c', 'user.email=scumutator@gmail.com',
                  'commit', '-qm', 'head moved')
            with self.assertRaisesRegex(RuntimeError, 'different source OID'):
                P.prepare(source, dest, resume=True)

    def test_fresh_prepare_still_refuses_an_existing_workspace(self):
        with tempfile.TemporaryDirectory() as folder:
            source, dest, _ = self.prepared(pathlib.Path(folder))
            with self.assertRaises(FileExistsError):
                P.prepare(source, dest)

    def test_resume_without_a_workspace_refuses(self):
        with tempfile.TemporaryDirectory() as folder:
            base = pathlib.Path(folder)
            source = fixture_source(base)
            with self.assertRaises(FileNotFoundError):
                P.prepare(source, base / ('beops-release-' + 'b' * 32), resume=True)

    def test_incomplete_fixed_source_is_not_resumable(self):
        with tempfile.TemporaryDirectory() as folder:
            source, dest, _ = self.prepared(pathlib.Path(folder))
            (dest / 'runtime/release-inputs.json').unlink()
            (dest / P.PROGRESS_NAME).unlink()
            with self.assertRaisesRegex(RuntimeError, 'markers unreadable'):
                P.prepare(source, dest, resume=True)


@unittest.skipUnless(os.name == 'nt', 'publish safety helpers are PowerShell')
class ResumableSafety(unittest.TestCase):
    OID = 'f' * 40

    def ps(self, body):
        script = textwrap.dedent(f"""
            $ErrorActionPreference='Stop'
            . '{SAFETY}'
            {body}
        """)
        return subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script],
            cwd=str(ROOT), text=True, capture_output=True, timeout=30)

    def workspace(self, base, *, oid=None, hours_old=3, progress=True):
        release = base / ('beops-release-' + 'c' * 32)
        (release / 'runtime').mkdir(parents=True)
        import datetime
        created = (datetime.datetime.now(datetime.timezone.utc)
                   - datetime.timedelta(hours=hours_old)).isoformat()
        (release / '.beops-generated-workspace.json').write_text(json.dumps({
            'schema': 'beops-generated-workspace/v2', 'source': str(base / 'src'),
            'destination': str(release), 'source_oid': oid or self.OID,
            'owner_pid': 999999999, 'created_at': created, 'retained': False}), encoding='utf-8')
        if progress:
            (release / '.beops-prepare-progress.json').write_text(json.dumps({
                'schema': 'beops-prepare-progress/v1', 'source_oid': oid or self.OID,
                'source_tree': 'e' * 40, 'fixed_source_complete': True,
                'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}), encoding='utf-8')
        (base / 'src').mkdir(exist_ok=True)
        return release

    def test_cleanup_preserves_a_resumable_workspace_and_finds_it(self):
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d)
            release = self.workspace(base)
            got = self.ps(f"Clear-BeopsAbandonedReleases -SourceRoot '{base / 'src'}' -BaseRoot '{base}' -ResumeOid '{self.OID}'\n"
                          f"Get-BeopsResumableRelease -BaseRoot '{base}' -SourceRoot '{base / 'src'}' -SourceOid '{self.OID}'")
            self.assertEqual(got.returncode, 0, got.stderr + got.stdout)
            self.assertIn('Preserved resumable release', got.stdout)
            self.assertIn(release.name, got.stdout.splitlines()[-1])
            self.assertTrue(release.exists())

    def test_cleanup_removes_a_workspace_whose_oid_moved_on(self):
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d)
            release = self.workspace(base, oid='0' * 40)
            got = self.ps(f"Clear-BeopsAbandonedReleases -SourceRoot '{base / 'src'}' -BaseRoot '{base}' -ResumeOid '{self.OID}'")
            self.assertEqual(got.returncode, 0, got.stderr + got.stdout)
            self.assertIn('Removed owned abandoned release', got.stdout)
            self.assertFalse(release.exists())

    def test_workspace_without_progress_marker_is_not_resumable(self):
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d)
            self.workspace(base, progress=False)
            got = self.ps(f"$r = Get-BeopsResumableRelease -BaseRoot '{base}' -SourceRoot '{base / 'src'}' -SourceOid '{self.OID}'\n"
                          "if ($null -eq $r) { 'none' } else { $r }")
            self.assertEqual(got.returncode, 0, got.stderr + got.stdout)
            self.assertIn('none', got.stdout)


if __name__ == '__main__':
    unittest.main()
