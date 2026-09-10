#!/usr/bin/env python3
"""test_guard_organs.py - a task that runs and produces nothing must not look healthy.

2026-09-10, 00:38 to 01:22: the mind ticked every four minutes, every tick failed to reach its model,
and the task check, the watchman and the guard all reported ok for forty-four minutes. Nothing was
broken by any measure anyone was taking. The organ was mute and the measures could not say so, because
"is the task running" and "is the organ producing" had never been different questions.

Silence itself is not the failure - an organ may be quiet lawfully, and this record cares about the
difference between quiet and broken more than about either. So the shape asserted here is three-way:
a row inside the window is ok; no row but a receipt that gives a reason is a warn that CARRIES the
reason; no row and no receipt is unknown, because then we do not know whether it ran at all.
"""
import json
import pathlib
import sys
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import guard  # noqa: E402


class OrganOutput(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.tmp.name)
        self.rows = self.base / "mind"
        self.rec = self.rows / "receipts"
        self.rec.mkdir(parents=True)
        self.saved = guard.ORGANS
        guard.ORGANS = {"mind": {"rows": self.rows, "receipts": self.rec, "max_row_h": 1.0}}

    def tearDown(self):
        guard.ORGANS = self.saved
        self.tmp.cleanup()

    def write(self, path: pathlib.Path, hours_ago: float, body: str = "{}"):
        path.write_text(body, encoding="utf-8")
        t = time.time() - hours_ago * 3600
        import os
        os.utime(path, (t, t))

    def test_a_fresh_row_is_ok(self):
        self.write(self.rows / "2026-09.jsonl", 0.1)
        r = guard.organ_output()[0]
        self.assertEqual(r["state"], guard.OK, r)

    def test_a_silent_organ_that_still_ticks_warns_AND_CARRIES_THE_REASON(self):
        """The forty-four minutes. The reason was sitting in the receipts in plain words the whole
        time - 'model daemon not answering' - and no check ever read it."""
        self.write(self.rows / "2026-09.jsonl", 3.0)
        self.write(self.rec / "r1.json", 0.05,
                   json.dumps({"state": "organ_silent", "step_name": "connector",
                               "reason": "model daemon not answering"}))
        r = guard.organ_output()[0]
        self.assertEqual(r["state"], guard.WARN, r)
        self.assertIn("model daemon not answering", r["why"])
        self.assertIn("still ticking", r["why"])

    def test_a_silent_organ_that_has_stopped_ticking_is_unknown_not_a_warning(self):
        self.write(self.rows / "2026-09.jsonl", 3.0)
        self.write(self.rec / "r1.json", 4.0, json.dumps({"state": "derived"}))
        r = guard.organ_output()[0]
        self.assertEqual(r["state"], guard.UNKNOWN, r)
        self.assertIn("not merely quiet", r["why"])

    def test_an_organ_that_never_wrote_a_row_is_unknown(self):
        r = guard.organ_output()[0]
        self.assertEqual(r["state"], guard.UNKNOWN, r)

    def test_the_guard_never_repairs_an_organ(self):
        """It repairs exactly one class of thing - a task that exists and is not running. An organ
        that is quiet may be quiet for a good reason, and restarting it because it is quiet is how a
        record starts inventing."""
        src = (ROOT / "tools" / "guard.py").read_text(encoding="utf-8")
        self.assertIn("does NOT repair this class either", src)
        after = src.split("def organ_output")[1].split("def run(")[0]
        for forbidden in ("repair(", "Start-ScheduledTask", "Enable-ScheduledTask"):
            self.assertNotIn(forbidden, after, "the organ check tries to fix something")

    def test_the_report_shows_the_organs_and_the_verdict_counts_them(self):
        self.write(self.rows / "2026-09.jsonl", 3.0)
        self.write(self.rec / "r1.json", 0.05, json.dumps({"state": "organ_failed", "reason": "TimeoutError"}))
        line = guard.report({"at": "x", "verdict": "warn", "tasks": [], "lawful": [],
                             "organs": guard.organ_output(), "repairs": []})
        self.assertIn("organ mind", line)
        self.assertIn("TimeoutError", line)


if __name__ == "__main__":
    unittest.main()
