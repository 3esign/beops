#!/usr/bin/env python3
"""Behavioral tests for the publish safety helpers."""
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAFETY = ROOT / "tools" / "publish_safety.ps1"


def ps(script: str, *, cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=True,
        timeout=20,
    )


class PublishSafety(unittest.TestCase):
    def test_diagnostic_keeps_transcript_after_child_cleanup(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d); src = base/'source'; src.mkdir()
            release = base/('beops-release-' + 'a'*32)
            (release/'runtime').mkdir(parents=True)
            # The child removes its PID-specific file; its final copy must survive
            # the parent's later removal of the entire generated workspace.
            transcript = b'last complete test output\nactual failure or timeout\n'
            (release/'runtime/publish-tests.txt').write_bytes(transcript)
            self.assert_ps_ok(f"Save-BeopsReleaseDiagnostic -SourceRoot '{src}' -RunRoot '{release}' -SourceOid abc -Outcome publish-finished")
            folder = src/'runtime/release-diagnostics'
            diagnostic = json.loads((folder/(release.name+'.json')).read_text(encoding='utf-8-sig'))
            self.assertIsNotNone(diagnostic['test_transcript'])
            self.assertEqual((folder/diagnostic['test_transcript']).read_bytes(), transcript)

    def test_cleanup_removes_only_owned_generated_workspace(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d); src = base/'source'; src.mkdir()
            release = base/('beops-release-' + '1'*32); release.mkdir()
            (release/'sentinel').write_text('generated')
            call = f"Remove-BeopsGeneratedRelease -Path '{release}' -SourceRoot '{src}' -BaseRoot '{base}'"
            self.assert_ps_ok(call)
            self.assertTrue(release.exists(), 'unowned workspace must survive')
            (release/'.beops-generated-workspace.json').write_text(json.dumps({'source':str(src),'destination':str(release)}))
            self.assert_ps_ok(call)
            self.assertFalse(release.exists())
            self.assertTrue(src.exists())

    def test_native_success_keeps_stderr_out_of_json(self):
        with tempfile.TemporaryDirectory() as d:
            script = pathlib.Path(d) / 'native.py'
            script.write_text('import sys\nprint("warning", file=sys.stderr)\nprint(\'{"ok": true}\')\n')
            out = self.assert_ps_ok(f"$v = Get-BeopsNativeOutput -Name probe -FilePath '{sys.executable}' -ArgumentList @('{script}'); ($v | ConvertFrom-Json).ok")
            self.assertEqual(out.strip(), 'True')

    def test_native_failure_preserves_complete_traceback_and_exit(self):
        with tempfile.TemporaryDirectory() as d:
            script = pathlib.Path(d) / 'native.py'
            script.write_text('import sys\nprint("Traceback first line", file=sys.stderr)\nprint("actual final cause", file=sys.stderr)\nsys.exit(7)\n')
            out = self.assert_ps_fails(f"Get-BeopsNativeOutput -Name probe -FilePath '{sys.executable}' -ArgumentList @('{script}')", 'actual final cause')
            self.assertIn('exit code 7', out)
            self.assertIn('Traceback first line', out)

    def test_native_missing_command_fails(self):
        self.assert_ps_fails("Get-BeopsNativeOutput -Name probe -FilePath 'beops-does-not-exist-93817'", 'not recognized')

    def test_nonempty_unowned_default_folder_is_rejected_without_touching_it(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);src=root/'source';src.mkdir();pub=root/'Beops-public';pub.mkdir()
            sentinel=pub/'keep.txt';sentinel.write_bytes(b'original')
            self.assert_ps_fails(f"Assert-BeopsPublicRootSafe -SourceRoot '{src}' -PublicRoot '{pub}'",'expected public remote')
            self.assertEqual(sentinel.read_bytes(),b'original')

    def test_junction_to_source_is_rejected_and_sentinel_survives(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);src=root/'source';src.mkdir();alias=root/'Beops-public'
            sentinel=src/'keep.txt';sentinel.write_bytes(b'original')
            self.assert_ps_ok(f"New-Item -ItemType Junction -Path '{alias}' -Target '{src}' | Out-Null")
            try:
                self.assert_ps_fails(f"Assert-BeopsPublicRootSafe -SourceRoot '{src}' -PublicRoot '{alias}'",'source repository or inside it')
                self.assertEqual(sentinel.read_bytes(),b'original')
            finally:
                # Only our junction entry; never recurse into its target.
                alias.rmdir()

    def run_helper(self, body: str) -> subprocess.CompletedProcess[str]:
        script = textwrap.dedent(
            f"""
            $ErrorActionPreference = 'Stop'
            . '{SAFETY}'
            {body}
            """
        )
        return ps(script)

    def assert_ps_ok(self, body: str) -> str:
        got = self.run_helper(body)
        self.assertEqual(got.returncode, 0, got.stderr + got.stdout)
        return got.stdout

    def assert_ps_fails(self, body: str, needle: str) -> str:
        got = self.run_helper(body)
        self.assertNotEqual(got.returncode, 0, got.stderr + got.stdout)
        text = got.stderr + got.stdout
        self.assertIn(" ".join(needle.split()), " ".join(text.split()))
        return text

    def test_default_public_root_outside_source_is_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d)
            src = base / "source" / "Beops"
            pub = base / "Beops-public"
            src.mkdir(parents=True)
            out = self.assert_ps_ok(
                f"Assert-BeopsPublicRootSafe -SourceRoot '{src}' -PublicRoot '{pub}'"
            )
            self.assertIn(str(pub), out)

    def test_public_root_cannot_be_source_or_inside_source(self):
        with tempfile.TemporaryDirectory() as d:
            src = pathlib.Path(d) / "Beops"
            src.mkdir()
            self.assert_ps_fails(
                f"Assert-BeopsPublicRootSafe -SourceRoot '{src}' -PublicRoot '{src}'",
                "source repository or inside it",
            )
            self.assert_ps_fails(
                f"Assert-BeopsPublicRootSafe -SourceRoot '{src}' -PublicRoot '{src / 'Beops-public'}'",
                "source repository or inside it",
            )

    def test_public_root_cannot_contain_source(self):
        with tempfile.TemporaryDirectory() as d:
            pub = pathlib.Path(d) / "Beops-public"
            src = pub / "nested" / "Beops"
            src.mkdir(parents=True)
            self.assert_ps_fails(
                f"Assert-BeopsPublicRootSafe -SourceRoot '{src}' -PublicRoot '{pub}'",
                "contains the source repository",
            )

    def test_custom_public_root_requires_expected_remote(self):
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d)
            src = base / "Beops"
            custom = base / "CustomMirror"
            src.mkdir()
            custom.mkdir()
            subprocess.run(["git", "-C", str(custom), "init", "-q"], check=True)
            subprocess.run(
                ["git", "-C", str(custom), "remote", "add", "origin", "https://github.com/example/wrong.git"],
                check=True,
            )
            self.assert_ps_fails(
                f"Assert-BeopsPublicRootSafe -SourceRoot '{src}' -PublicRoot '{custom}'",
                "custom target must be the expected public remote",
            )
            subprocess.run(
                ["git", "-C", str(custom), "remote", "set-url", "origin", "https://github.com/3esign/beops.git"],
                check=True,
            )
            self.assert_ps_ok(
                f"Assert-BeopsPublicRootSafe -SourceRoot '{src}' -PublicRoot '{custom}'"
            )

    def test_deletion_target_must_be_inside_public_root_and_not_root(self):
        with tempfile.TemporaryDirectory() as d:
            pub = pathlib.Path(d) / "Beops-public"
            child = pub / "docs"
            outside = pathlib.Path(d) / "outside"
            child.mkdir(parents=True)
            outside.mkdir()
            self.assert_ps_ok(
                f"Assert-BeopsDeletionTarget -PublicRoot '{pub}' -Target '{child}'"
            )
            self.assert_ps_fails(
                f"Assert-BeopsDeletionTarget -PublicRoot '{pub}' -Target '{pub}'",
                "refusing to delete export root",
            )
            self.assert_ps_fails(
                f"Assert-BeopsDeletionTarget -PublicRoot '{pub}' -Target '{outside}'",
                "not inside export root",
            )

    def test_abandoned_lock_is_removed_and_retaken(self):
        with tempfile.TemporaryDirectory() as d:
            lock = pathlib.Path(d) / "publish.lock"
            lock.write_text("pid 999999 at old", encoding="utf-8")
            old = "2001-01-01T00:00:00Z"
            self.assert_ps_ok(
                f"""
                (Get-Item -LiteralPath '{lock}').LastWriteTimeUtc = [datetime]'{old}'
                $lock = Enter-BeopsPublishLock -Path '{lock}' -MaxAgeMinutes 15
                if (-not $lock.Acquired -or -not $lock.Recovered) {{ throw 'lock was not recovered' }}
                if (-not (Test-BeopsPublishLockOwnedByCurrentProcess -Path '{lock}')) {{ throw 'new lock is not ours' }}
                """
            )

    def test_old_lock_with_live_owner_is_not_removed(self):
        with tempfile.TemporaryDirectory() as d:
            lock = pathlib.Path(d) / "publish.lock"
            self.assert_ps_ok(
                f"""
                Set-Content -LiteralPath '{lock}' -Value ('pid ' + $PID + ' at old') -Encoding UTF8
                (Get-Item -LiteralPath '{lock}').LastWriteTimeUtc = [datetime]'2001-01-01T00:00:00Z'
                $lockResult = Enter-BeopsPublishLock -Path '{lock}' -MaxAgeMinutes 15
                if ($lockResult.Acquired) {{ throw 'live owner lock was acquired' }}
                if ($lockResult.Reason -ne 'owner-running') {{ throw ('wrong reason ' + $lockResult.Reason) }}
                """
            )

    def test_native_failure_throws(self):
        self.assert_ps_fails(
            "Invoke-BeopsNative 'expected failure' 'powershell' @('-NoProfile', '-Command', 'exit 7')",
            "expected failure failed with exit code 7",
        )


if __name__ == "__main__":
    unittest.main()
