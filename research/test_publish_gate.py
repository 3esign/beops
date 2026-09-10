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
TICK = ROOT / "tools" / "publish_tick.bat"
RECEIPT = ROOT / "data" / "live" / "publish-receipt.json"


class Gate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = PS.read_text(encoding="utf-8")

    def test_the_publisher_runs_the_suite(self):
        self.assertIn("unittest discover", self.s,
                      "the publisher no longer runs the tests: every scheduled publish would go out unchecked")

    def test_the_suite_runs_after_the_site_is_built(self):
        """Tests placed before build_site.py would check yesterday's page and pass it while today's
        went out untested. That was the first design and reading the file refuted it."""
        build = self.s.find("build_site.py")
        gate = self.s.find("unittest discover")
        self.assertGreater(build, -1)
        self.assertGreater(gate, build, "the gate runs before the site is built, so it checks the wrong page")

    def test_a_failing_suite_publishes_nothing_and_says_so(self):
        gate = self.s.find("unittest discover")
        push = self.s.find("git -C $pub push")
        self.assertGreater(push, gate, "the push happens before the gate")
        self.assertIn("NOTHING WAS PUBLISHED", self.s)
        self.assertIn("exit 3", self.s)

    def test_the_export_tree_is_not_touched_until_the_gate_passes(self):
        gate = self.s.find('Write-Output "gate:')
        clear = self.s.find("Get-ChildItem -Path $pub")
        copy = self.s.find("Copy-Item -LiteralPath (Join-Path $src $f)")
        self.assertGreater(gate, -1)
        self.assertGreater(clear, gate, "the public mirror is cleared before the gate passes")
        self.assertGreater(copy, gate, "files are copied to the public mirror before the gate passes")

    def test_the_gate_leaves_a_receipt_the_guard_can_read(self):
        """A gate that stops the site silently has exchanged one failure for a quieter one."""
        self.assertIn("publish-receipt.json", self.s)
        self.assertIn("beops-publish-receipt/v1", self.s)

    def test_two_publishers_cannot_race_for_the_export(self):
        """C-045: the loser of a race for git's index.lock read exactly like a clean tree."""
        self.assertIn("publish.lock", self.s)
        self.assertIn("another publish holds the lock", self.s)

    def test_a_failing_gate_releases_the_lock(self):
        """PowerShell does not run finally on exit. A lock left by a failing gate would block every
        publish for fifteen minutes - a second outage caused by the first."""
        i = self.s.find("NOTHING WAS PUBLISHED")
        j = self.s.find("exit 3")
        seg = self.s[i:j]
        self.assertIn("Remove-Item $lockFile", seg,
                      "the gate exits without releasing the lock it holds")

    def test_an_unreadable_status_is_never_reported_as_clean(self):
        """C-045's own correction, held in place."""
        self.assertIn("could not read the export status", self.s)


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
