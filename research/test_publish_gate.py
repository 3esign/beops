#!/usr/bin/env python3
"""test_publish_gate.py - the thing that publishes is the thing that checks.

Every ship batch in this project runs the suite and refuses to commit when it fails. The scheduled
publish did neither: it rebuilt the site every ten minutes and pushed it untested, so the gate
protected the rare path and not the one the public actually sees. The gate now lives inside
publish_github.ps1, which means every caller gets it by construction rather than by remembering - and
these tests exist so that it cannot be quietly removed by an edit that looks like a simplification.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PS = ROOT / "tools" / "publish_github.ps1"
SAFETY = ROOT / "tools" / "publish_safety.ps1"
TICK = ROOT / "tools" / "publish_tick.bat"
RECEIPT = ROOT / "data" / "live" / "publish-receipt.json"


class Gate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = PS.read_text(encoding="utf-8")
        cls.safety = SAFETY.read_text(encoding="utf-8")

    def test_the_publisher_runs_the_suite(self):
        self.assertIn("unittest discover", self.s,
                      "the publisher no longer runs the tests: every scheduled publish would go out unchecked")

    def test_direct_publisher_prefers_the_bundled_test_python(self):
        """The documented direct PowerShell command must not fall back to a random PATH python."""
        start = self.s.find("function Resolve-BeopsTestPython")
        end = self.s.find("$src =")
        self.assertGreater(start, -1)
        seg = self.s[start:end]
        self.assertIn("BEOPS_TEST_PYTHON", seg)
        self.assertIn("Resolve-BeopsBundledPython", seg)
        self.assertIn("Resolve-BeopsPython", seg)

    def test_the_suite_runs_after_the_site_is_built(self):
        """Tests placed before build_site.py would check yesterday's page and pass it while today's
        went out untested. That was the first design and reading the file refuted it."""
        build = self.s.find("build_site.py")
        gate = self.s.find("unittest discover")
        self.assertGreater(build, -1)
        self.assertGreater(gate, build, "the gate runs before the site is built, so it checks the wrong page")

    def test_a_failing_suite_publishes_nothing_and_says_so(self):
        gate = self.s.find("unittest discover")
        push = self.s.find("Invoke-BeopsNative 'git push public export'")
        self.assertGreater(push, gate, "the push happens before the gate")
        self.assertIn("NOTHING WAS PUBLISHED", self.s)
        self.assertIn("exit 3", self.s)

    def test_the_export_tree_is_not_touched_until_the_gate_passes(self):
        gate = self.s.find('Write-Output "gate:')
        clear = self.s.find("Get-ChildItem -LiteralPath $pub")
        archive = self.s.find("New-BeopsTrackedHeadArchive $keep")
        copy = self.s.find("Expand-BeopsTrackedHeadArchive")
        self.assertGreater(gate, -1)
        self.assertGreater(archive, gate, "source archive is made before the gate passes")
        self.assertLess(archive, clear, "a bad archive path can clear the public mirror before failing")
        self.assertGreater(clear, gate, "the public mirror is cleared before the gate passes")
        self.assertGreater(copy, gate, "files are copied to the public mirror before the gate passes")

    def test_the_gate_leaves_a_receipt_the_guard_can_read(self):
        """A gate that stops the site silently has exchanged one failure for a quieter one."""
        self.assertIn("publish-receipt.json", self.s)
        self.assertIn("beops-publish-receipt/v1", self.s)
        for k in (
            "source_tree",
            "source_files_from",
            "source_file_count",
            "generated_as_of",
            "built",
            "export_manifest",
            "export_changed",
            "committed",
            "pushed",
            "remote_head",
            "site_verified",
            "site_live_hash",
            "site_local_hash",
            "site_route_count",
            "site_checked_at",
        ):
            self.assertIn(k, self.s, f"the receipt no longer records {k}")

    def test_two_publishers_cannot_race_for_the_export(self):
        """C-045: the loser of a race for git's index.lock read exactly like a clean tree."""
        self.assertIn("publish.lock", self.s)
        self.assertIn("another publish holds the lock", self.safety)
        self.assertIn("[System.IO.FileMode]::CreateNew", self.safety,
                      "the publish lock is not taken atomically")

    def test_publish_test_transcript_is_per_run(self):
        self.assertIn("publish-tests-{0}.txt", self.s)
        self.assertIn("$script:publishTestsOutRun", self.s)

    def test_a_failing_gate_releases_the_lock(self):
        """PowerShell does not run finally on exit. A lock left by a failing gate would block every
        publish for fifteen minutes - a second outage caused by the first."""
        start = self.s.find("function Release-BeopsPublishRun")
        end = self.s.find("$lock = Enter-BeopsPublishLock")
        release = self.s[start:end]
        self.assertIn("Test-BeopsPublishLockOwnedByCurrentProcess", release,
                      "the shared cleanup may remove a lock held by another publisher")
        self.assertIn("Remove-Item -LiteralPath $lockFile", release,
                      "the shared publish cleanup no longer removes the lock")
        i = self.s.find("NOTHING WAS PUBLISHED")
        j = self.s.find("exit 3")
        seg = self.s[i:j]
        self.assertIn("Release-BeopsPublishRun", seg,
                      "the gate exits without releasing the lock it holds")

    def test_an_unreadable_status_is_never_reported_as_clean(self):
        """C-045's own correction, held in place."""
        self.assertIn("could not read the export status", self.s)

    def test_tracked_source_files_are_exported_from_head_not_the_working_tree(self):
        self.assertIn("git source HEAD file list", self.s)
        self.assertIn("git archive source HEAD", self.s)
        self.assertIn("New-BeopsTrackedHeadArchive $keep", self.s)
        self.assertIn("Expand-BeopsTrackedHeadArchive", self.s)
        self.assertNotIn("Copy-Item -LiteralPath (Join-Path $src $f)", self.s)

    def test_dirty_tracked_source_is_refused_before_public_mirror_is_touched(self):
        self.assertIn("tracked source working tree is dirty", self.s)
        before = self.s.find("Assert-BeopsTrackedSourceClean 'before build'")
        after = self.s.find("Assert-BeopsTrackedSourceClean 'after gate'")
        clear = self.s.find("Get-ChildItem -LiteralPath $pub")
        self.assertGreater(before, -1)
        self.assertGreater(after, before)
        self.assertGreater(clear, after, "the public mirror can be cleared before the post-gate dirty check")

    def test_the_export_has_a_manifest_with_file_hashes(self):
        self.assertIn("beops-export-manifest/v1", self.s)
        self.assertIn("docs/export-manifest.json", self.s)
        self.assertIn("Get-FileHash", self.s)

    def test_the_publisher_verifies_the_live_site_before_confirming_publication(self):
        push = self.s.find("Invoke-BeopsNative 'git push public export'")
        site = self.s.find("Invoke-BeopsSiteCheck", push)
        published = self.s.find("$receipt.published = $true", site)
        self.assertGreater(push, -1)
        self.assertGreater(site, push, "the live site check does not run after push")
        self.assertGreater(published, site, "published=true is set before the live site is verified")
        self.assertIn("tools\\verify_public_site.js", self.s)
        self.assertIn("REMOTE PUSH COMPLETED BUT LIVE SITE WAS NOT VERIFIED", self.s)

    def test_generated_public_files_are_force_added(self):
        for path in (
            "public/history.json",
            "public/watch.json",
            "public/dataset/permission-landscape",
            "research/08-provenance/CORRECTION_TIMES.json",
            "research/observations/live",
        ):
            self.assertIn(path, self.s, f"{path} is not explicitly copied and force-added to the export")

    def test_scheduler_stops_after_failed_pre_publish_steps(self):
        tick = TICK.read_text(encoding="utf-8")
        for step in ("collect_daemon.py export", "collect_daemon.py report", "build_history.py"):
            pos = tick.find(step)
            self.assertGreater(pos, -1)
            guard = tick.find("if errorlevel 1 exit /b %ERRORLEVEL%", pos)
            self.assertGreater(guard, pos, f"publish_tick.bat continues after {step} fails")


class Receipt(unittest.TestCase):
    def test_nothing_reads_the_receipt_as_plain_utf8(self):
        """The BOM again, asserted across the whole project rather than in the two places it bit."""
        import re as _re
        bad = []
        me = pathlib.Path(__file__).name
        for f in sorted((ROOT / "tools").glob("*.py")) + sorted((ROOT / "research").glob("test_*.py")):
            # This file carries the pattern it is looking for, as the pattern. A scanner that reads
            # its own regex as a finding has invented a defect, and inventing one is the same class
            # of error as missing one.
            if f.name == me:
                continue
            s = f.read_text(encoding="utf-8", errors="replace")
            if "publish-receipt" not in s:
                continue
            for m in _re.finditer(r'read_text\(encoding="utf-8"\)', s):
                seg = s[max(0, m.start() - 300):m.start()]
                if "publish-receipt" in seg or "RECEIPT" in seg:
                    bad.append(f.name)
        self.assertEqual(sorted(set(bad)), [],
                         "the publish receipt is read as plain utf-8 somewhere, and PowerShell writes it with a BOM: "
                         + ", ".join(sorted(set(bad))))

    def test_the_receipt_if_present_says_whether_the_tests_passed(self):
        if not RECEIPT.exists():
            self.skipTest("the publisher has not run since the gate was added")
        # Written by PowerShell, whose -Encoding UTF8 means UTF-8 WITH A BOM. Reading it as plain
        # utf-8 is what made the guard call a well-formed receipt unreadable on its first run, and
        # this test repeated the same mistake one file later - which is the shape of C-018, C-020 and
        # C-022: a fix applied where the symptom appeared rather than everywhere the pattern was
        # written. The suite caught it before the commit.
        r = json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
        self.assertEqual(r.get("schema"), "beops-publish-receipt/v1")
        for k in ("at", "tests_ok", "published", "why"):
            self.assertIn(k, r, f"the receipt does not say {k}")


if __name__ == "__main__":
    unittest.main()
