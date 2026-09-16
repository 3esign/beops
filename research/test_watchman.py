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
from unittest.mock import patch
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
        d = self.dir/'data/live'; d.mkdir(parents=True, exist_ok=True)
        receipt = dict(published=True, pushed=True, site_verified=True, site_live_hash='a', site_local_hash='a',
                       remote_head='commit', site_checked_at=iso(NOW), generated_as_of=iso(NOW),
                       verified_history={'hours_of_history':hours, 'history_ends':newest_hour})
        for name in ('publish-last-success.json', 'publish-receipt.json'):
            (d/name).write_text(json.dumps(receipt), encoding='utf-8')


class WatchmanTests(unittest.TestCase):
    def setUp(self):
        self.t = Tree()
        self._root, self._live, self._led, self._pub = W.ROOT, W.LIVE, W.LEDGER, W.PUBLIC
        W.ROOT = self.t.dir
        W.LIVE = self.t.dir / "data" / "live"
        W.LEDGER = W.LIVE / "watch-ledger.jsonl"
        W.PUBLIC = self.t.dir / "public" / "watch.json"
        self.policy = patch.object(W.source_policy, 'decision', return_value=('allowed', 'fixture'))
        self.policy.start()
        self.addCleanup(self.policy.stop)

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

    def test_newest_row_validates_only_the_new_append_after_a_cached_prefix(self):
        d = self.t.dir / "data" / "live" / "rows" / "S01"
        d.mkdir(parents=True, exist_ok=True)
        path = d / "2026-09.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for i in range(5000):
                f.write(json.dumps({"receivedTime": iso(NOW - timedelta(minutes=5000 - i))}) + "\n")
        index = {"schema": W.ROW_INDEX_SCHEMA, "files": {}}
        W.newest_row("S01", index)  # one strict validation establishes the immutable prefix
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"receivedTime": iso(NOW), "payload": "x" * 70000}) + "\n\n")

        real_loads = json.loads
        with patch.object(W.json, "loads", wraps=real_loads) as loads:
            newest, error = W.newest_row("S01", index)

        self.assertEqual(newest, NOW)
        self.assertIsNone(error)
        self.assertEqual(loads.call_count, 1)

    def test_cached_prefix_change_is_strictly_revalidated(self):
        self.t.row("S01", NOW - timedelta(minutes=2), 3)
        index = {"schema": W.ROW_INDEX_SCHEMA, "files": {}}
        W.newest_row("S01", index)
        path = self.t.dir / "data" / "live" / "rows" / "S01" / "2026-09.jsonl"
        body = path.read_text(encoding="utf-8")
        path.write_text(body.replace('"result": 1', '"result": 9', 1), encoding="utf-8")
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"receivedTime": iso(NOW)}) + "\n")

        newest, error = W.newest_row("S01", index)
        self.assertEqual(newest, NOW)
        self.assertIsNone(error)

    def test_newest_row_fails_closed_when_the_appended_tail_is_malformed(self):
        self.t.row("S01", NOW - timedelta(minutes=1))
        path = self.t.dir / "data" / "live" / "rows" / "S01" / "2026-09.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write('{"receivedTime":')

        newest, error = W.newest_row("S01")
        self.assertIsNone(newest)
        self.assertIn("unreadable rows", error)

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

    def test_publication_freshness_is_not_the_retired_ten_minute_cadence(self):
        self.t.history("2026-09-10T11")
        for age, expected in ((30, W.OK), (44, W.OK), (46, W.LATE), (61, W.STALLED)):
            receipt_path = W.LIVE/'publish-last-success.json'
            receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
            receipt['generated_as_of'] = iso(NOW - timedelta(minutes=age))
            receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
            self.assertEqual(W.published(NOW)['state'], expected)
        # A newer failed attempt must still raise an alert even with fresh inputs.
        receipt['generated_as_of'] = iso(NOW - timedelta(minutes=10))
        receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
        (W.LIVE/'publish-receipt.json').write_text(json.dumps(dict(
            published=False, at=iso(NOW + timedelta(seconds=1)))), encoding='utf-8')
        self.assertEqual(W.published(NOW)['state'], W.LATE)

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

    def _snapshot(self, captured, expected=144, age_min=5):
        (self.t.dir / "public" / "live-snapshot.json").write_text(json.dumps({"status": {
            "as_of": iso(NOW - timedelta(minutes=age_min)),
            "sources": [{"sid": "S04", "expected_slots": expected, "captured": captured, "paused": None}]}}), encoding="utf-8")

    def test_a_week_of_missed_slots_is_late_even_when_the_last_ask_was_recent(self):
        self._snapshot(83)
        c = W.coverage(NOW)
        self.assertEqual(c["state"], W.LATE)
        self.assertIn("S04 58%", c["said"])

    def test_low_coverage_alone_does_not_fail_the_watch_process(self):
        r = {"verdict": W.LATE, "checks": [{"check": "coverage 24h", "state": W.LATE}, {"check": "rows", "state": W.OK}]}
        self.assertEqual(W.exit_code(r), 0)
        r["checks"].append({"check": "source S01", "state": W.LATE})
        self.assertEqual(W.exit_code(r), 1)

    def test_full_coverage_is_ok_and_stale_counts_are_unknown(self):
        self._snapshot(140)
        self.assertEqual(W.coverage(NOW)["state"], W.OK)
        self._snapshot(140, age_min=45)
        self.assertEqual(W.coverage(NOW)["state"], W.UNKNOWN)
        (self.t.dir / "public" / "live-snapshot.json").unlink()
        self.assertEqual(W.coverage(NOW)["state"], W.UNKNOWN)

    def test_the_report_never_claims_more_than_the_checks(self):
        self.t.receipt("S01", NOW - timedelta(minutes=4)); self.t.row("S01", NOW)
        r = W.run(NOW)
        text = W.report(r)
        self.assertIn("verdict:", text)
        for c in r["checks"]:
            if c["state"] != W.OK:
                self.assertIn(c["check"], text)

    def test_a_policy_block_does_not_make_the_watch_process_fail(self):
        self.assertEqual(W.exit_code({"verdict": W.BLOCKED}), 0)
        self.assertEqual(W.exit_code({"verdict": W.PAUSED}), 0)
        self.assertEqual(W.exit_code({"verdict": W.STALLED}), W.RANK[W.STALLED])

    def test_expected_provider_capacity_is_visible_without_failing_the_watch_task(self):
        (self.t.dir / 'research' / 'AI_FEED.json').write_text(
            json.dumps({'enabled': True}), encoding='utf-8')
        status_path = self.t.dir / 'runtime' / 'ai-feed' / 'status.json'
        status_path.parent.mkdir(parents=True)
        status = {
            'at': iso(NOW - timedelta(minutes=5)),
            'last_success': iso(NOW - timedelta(hours=2)),
            'state': 'providers_unavailable',
            'providers': [
                {'id': 'local', 'ready': False, 'reason': 'daily_provider_budget'},
                {'id': 'remote', 'ready': False, 'reason': 'rate-limited'},
            ],
        }
        status_path.write_text(json.dumps(status), encoding='utf-8')

        finding = W.ai_feed(NOW)
        self.assertEqual(finding['state'], W.BLOCKED)
        self.assertIn('stale', finding['said'])
        self.assertEqual(W.exit_code({'verdict': finding['state']}), 0)

        status['providers'][0]['reason'] = 'cli_missing'
        status_path.write_text(json.dumps(status), encoding='utf-8')
        self.assertEqual(W.ai_feed(NOW)['state'], W.LATE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
