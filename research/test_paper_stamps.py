#!/usr/bin/env python3
"""test_paper_stamps.py - the times the papers type into themselves.

C-052 left this on the open list: the papers carry the same kind of hand-typed line as the corrections
ledger did, and nobody had checked them. Two papers carry one. Both are right - each sits ten to
twenty-five minutes before the commit that introduced the document. This keeps them right.
"""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import paper_stamps as ps  # noqa: E402


class Stamps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ps.PAPERS.exists():
            raise unittest.SkipTest("no papers on this machine")
        cls.doc = ps.build()
        if not cls.doc["git_readable"]:
            raise unittest.SkipTest("git is not readable here")

    def test_no_paper_verified_its_figures_after_it_was_committed(self):
        """The one invariant that needs no run log: figures cannot be checked after the document
        reporting them entered the record."""
        for e in self.doc["entries"]:
            self.assertNotIn("impossible", e["verdict"],
                             f"{e['file']} line {e['line']}: {e['text']}")

    def test_the_two_audited_stamps_stay_what_they_were_measured_to_be(self):
        """Frozen, like the ledger's wrong stamps are frozen - for the opposite reason. These were
        found to be right, and a right answer is as worth protecting from a quiet edit as a wrong one
        is from a quiet tidy-up."""
        found = {}
        for e in self.doc["entries"]:
            found.setdefault(e["file"], e["stated_minus_committed_minutes"])
        for name, minutes in ps.MEASURED.items():
            self.assertIn(name, found, f"{name} no longer carries the stamp that was audited")
            self.assertEqual(found[name], minutes,
                             f"{name}'s stamp or its commit changed since it was measured")
            self.assertLess(minutes, 0)

    def test_a_stamp_written_after_runs_were_recorded_must_match_a_run(self):
        for e in self.doc["entries"]:
            self.assertNotIn("unevidenced: no recorded run", e["verdict"],
                             f"{e['file']} line {e['line']} states a time no recorded run supports")

    def test_running_the_figures_leaves_a_line_behind(self):
        """The receipt that makes the claim checkable at all. Written to a temporary file: a record
        that a test may append to is not evidence of anything."""
        with tempfile.TemporaryDirectory() as d:
            log = pathlib.Path(d) / "runs.jsonl"
            now = ps.datetime.now(ps.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            ps.record({"a": 1}, now, path=log)
            ps.record({"a": 2}, now, path=log)
            got = ps.runs(path=log)
        self.assertEqual(len(got), 2)
        self.assertIn("figures_sha256", got[-1])
        self.assertNotEqual(got[0]["figures_sha256"], got[1]["figures_sha256"],
                            "two different sets of figures hashed to the same receipt")
        self.assertTrue(got[-1]["taken_at"].endswith("Z"))

    def test_the_real_run_log_is_never_written_to_by_the_suite(self):
        """If a test can append to it, it is not a record of runs."""
        n = len(ps.runs())
        ps.build()
        self.assertEqual(len(ps.runs()), n, "auditing the stamps wrote to the run log")

    def test_a_time_quoted_in_backticks_is_not_the_paper_claiming_it(self):
        line = "the ledger said `2026-09-09 19:07 UTC` and nothing checked it"
        self.assertIsNone(ps.STAMP.search(ps.CODE_SPAN.sub("", line)))


if __name__ == "__main__":
    unittest.main()
