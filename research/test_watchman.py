#!/usr/bin/env python3
"""The watchman is the thing that will be believed when nobody is looking, so it is tested for the
ways a monitor lies: calling silence a failure, calling blindness success, and vouching for a period
it slept through."""
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import watchman as W  # noqa: E402

NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


class Tree:
    """A synthetic record, so nothing here reads the real one."""

    def __init__(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        (self.dir / "research").mkdir()
        (self.dir / "public").mkdir()
        self.collectors({"S01": 15, "S02": 60})

    def collectors(self, sids: dict):
        (self.dir / "research" / "COLLECTORS.json").write_text(json.dumps({
            "schema": "x", "sources": [{"sid": s, "enabled": True, "cadence_seconds": m * 60,
                                        "name": s, "parser": "x"} for s, m in sids.items()]}),
            encoding="utf-8")

    def receipt(self, sid, when):
        d = self.dir / "data" / "live" / "receipts" / sid
        d.mkdir(parents=True, exist_ok=True)
        (d / (iso(when).replace(":", "") + ".json")).write_text(
            json.dumps({"receivedTime": iso(when), "state": "captured", "http_status": 200, "rows": 3}), encoding="utf-8")

    def row(self, sid, when, n=1):
        d = self.dir / "data" / "live" / "rows" / sid
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "2026-09.jsonl", "a", encoding="utf-8") as f:
            for _ in range(n):
                f.write(json.dumps({"sid": sid, "receivedTime": iso(when), "result": 1}) + "\n")

    def history(self, newest_hour, hours=23):
        (self.dir / "public" / "history.json").write_text(json.dumps(
            {"hours_of_history": hours, "history_ends": newest_hour, "series": []}), encoding="utf-8")


class WatchmanTests(unittest.TestCase):
    def setUp(self):
        self.t = Tree()
        self._root, self._live, self._led, self._pub = W.ROOT, W.LIVE, W.LEDGER, W.PUBLIC
        W.ROOT = self.t.dir
        W.LIVE = self.t.dir / "data" / "live"
        W.LEDGER = W.LIVE / "watch-ledger.jsonl"
        W.PUBLIC = self.t.dir / "public" / "watch.json"

    def tearDown(self):
        W.ROOT, W.LIVE, W.LEDGER, W.PUBLIC = self._root, self._live, self._led, self._pub
        shutil.rmtree(self.t.dir, ignore_errors=True)

    def states(self, r):
        return {c["check"]: c["state"] for c in r["checks"]}

    def test_a_silent_source_we_are_still_asking_is_not_a_fault(self):
        """The publisher has nothing to say. We asked four minutes ago. That is an observation."""
        self.t.receipt("S01", NOW - timedelta(minutes=4))
        self.t.row("S01", NOW - timedelta(hours=9))
        r = W.run(NOW)
        s = self.states(r)["source S01"]
        self.assertEqual(s, W.OK)
        said = [c["said"] for c in r["checks"] if c["check"] == "source S01"][0]
        self.assertIn("a record and not a fault", said)

    def test_a_source_we_stopped_asking_is_ours(self):
        self.t.receipt("S01", NOW - timedelta(minutes=200))   # cadence 15 min, so far past 6x
        self.t.row("S01", NOW - timedelta(minutes=200))
        r = W.run(NOW)
        self.assertEqual(self.states(r)["source S01"], W.STALLED)
        self.assertIn("this is ours", [c["said"] for c in r["checks"] if c["check"] == "source S01"][0])

    def test_a_source_between_two_and_six_cadences_is_late_not_stalled(self):
        self.t.receipt("S01", NOW - timedelta(minutes=40))    # 2.7 cadences
        r = W.run(NOW)
        self.assertEqual(self.states(r)["source S01"], W.LATE)

    def test_what_cannot_be_read_is_unknown_and_never_ok(self):
        # no receipts at all for S02
        self.t.receipt("S01", NOW - timedelta(minutes=4))
        r = W.run(NOW)
        self.assertEqual(self.states(r)["source S02"], W.UNKNOWN)
        self.assertNotEqual(r["verdict"], W.OK)

    def test_a_run_with_only_unknowns_does_not_report_ok(self):
        r = W.run(NOW)
        self.assertEqual(r["verdict"], W.UNKNOWN)

    def test_the_history_falling_behind_is_seen(self):
        self.t.history("2026-09-10T05")            # 7 h behind NOW
        self.assertEqual(self.states(W.run(NOW))["history"], W.STALLED)
        self.t.history("2026-09-10T11")            # 1 h behind
        self.assertEqual(self.states(W.run(NOW))["history"], W.OK)

    def test_the_first_reading_vouches_for_nothing_before_it(self):
        r = W.run(NOW)
        c = [x for x in r["checks"] if x["check"] == "watchman"][0]
        self.assertEqual(c["state"], W.UNKNOWN)
        self.assertIn("vouches for nothing", c["said"])

    def test_a_gap_in_the_watching_is_recorded_as_a_gap(self):
        W.LEDGER.parent.mkdir(parents=True, exist_ok=True)
        W.LEDGER.write_text(json.dumps({"at": iso(NOW - timedelta(minutes=95)), "verdict": "ok",
                                        "figures": {"rows": 10}}) + "\n", encoding="utf-8")
        c = [x for x in W.run(NOW)["checks"] if x["check"] == "watchman"][0]
        self.assertEqual(c["state"], W.LATE)
        self.assertIn("speaks for that gap", c["said"])

    def test_rows_going_backwards_is_data_loss_and_stalls_the_verdict(self):
        self.t.receipt("S01", NOW - timedelta(minutes=2)); self.t.row("S01", NOW, 5)
        W.LEDGER.parent.mkdir(parents=True, exist_ok=True)
        W.LEDGER.write_text(json.dumps({"at": iso(NOW - timedelta(minutes=10)), "verdict": "ok",
                                        "figures": {"rows": 500}}) + "\n", encoding="utf-8")
        r = W.run(NOW)
        self.assertEqual(self.states(r)["rows kept"], W.STALLED)
        self.assertEqual(r["verdict"], W.STALLED)

    def test_rows_growing_is_reported_as_growth(self):
        self.t.receipt("S01", NOW - timedelta(minutes=2)); self.t.row("S01", NOW, 5)
        W.LEDGER.parent.mkdir(parents=True, exist_ok=True)
        W.LEDGER.write_text(json.dumps({"at": iso(NOW - timedelta(minutes=10)), "verdict": "ok",
                                        "figures": {"rows": 2}}) + "\n", encoding="utf-8")
        c = [x for x in W.run(NOW)["checks"] if x["check"] == "rows kept"][0]
        self.assertEqual(c["state"], W.OK)
        self.assertIn("3 rows added", c["said"])

    def test_the_ledger_is_append_only_and_keeps_what_was_not_current(self):
        self.t.receipt("S01", NOW - timedelta(minutes=300))
        W.main_argv = None
        for _ in range(2):
            r = W.run(NOW)
            W.LEDGER.parent.mkdir(parents=True, exist_ok=True)
            with open(W.LEDGER, "a", encoding="utf-8") as f:
                f.write(json.dumps({k: r[k] for k in ("schema", "at", "verdict", "counts", "figures",
                                                      "not_current")}) + "\n")
        lines = [json.loads(l) for l in W.LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(lines), 2)
        self.assertIn("source S01", lines[-1]["not_current"])

    def test_the_report_never_claims_more_than_the_checks(self):
        self.t.receipt("S01", NOW - timedelta(minutes=4)); self.t.row("S01", NOW)
        r = W.run(NOW)
        text = W.report(r)
        self.assertIn("verdict:", text)
        for c in r["checks"]:
            if c["state"] != W.OK:
                self.assertIn(c["check"], text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
