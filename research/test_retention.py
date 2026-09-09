#!/usr/bin/env python3
"""The retention rule is the one place this project erases, so it is tested harder than the rest.

What must hold: the sentence goes, everything that makes the row evidence stays, a measurement is
never touched, a row that is not yet due is never touched, running it twice changes nothing the
second time, the ledger records what happened, and a dry run writes nothing at all.
"""
import datetime as dt
import json
import pathlib
import os
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import apply_retention as R  # noqa: E402

NOW = dt.datetime(2026, 12, 20, 12, 0, tzinfo=dt.timezone.utc)


def headline(sid, when, text="Ministar Petrović otvorio most u Zemunu", extra=None):
    row = {"schema": "beops-observation-row/v1", "sid": sid, "kind": "text",
           "datastream": f"{sid}|headline", "station_id": sid, "parameter": "headline",
           "result": text, "unit": None, "link": "https://example.rs/a/1",
           "phenomenonTime": None, "phenomenonTimeUnknown": True,
           "phenomenonTimeReason": "a headline carries its publication time",
           "resultTime": when, "receivedTime": when, "resultQuality": "unvalidated",
           "dedupe_key": f"{sid}|deadbeef", "permission_capture": "20260906T021824Z",
           "raw_sha256": "0" * 64}
    row.update(extra or {})
    return row


def measurement(when):
    return {"schema": "beops-observation-row/v1", "sid": "S146", "kind": "measurement",
            "datastream": "S146|PM10", "parameter": "PM10", "result": 37.2, "unit": "ug/m3",
            "phenomenonTime": when, "receivedTime": when, "resultQuality": "preliminary"}


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        (self.dir / "research").mkdir()
        shutil.copy(ROOT / "research" / "RETENTION.json", self.dir / "research" / "RETENTION.json")
        self.policy = json.loads((self.dir / "research" / "RETENTION.json").read_text(encoding="utf-8"))
        rows = self.dir / "data" / "live" / "rows" / "S68"
        rows.mkdir(parents=True)
        self.f = rows / "2026-09.jsonl"
        self.old = "2026-09-01T10:00:00Z"          # 110 days before NOW
        self.fresh = "2026-12-01T10:00:00Z"        # 19 days before NOW
        lines = [headline("S68", self.old), headline("S68", self.fresh, "Sveza vest o gradu"),
                 measurement(self.old)]
        self.f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in lines) + "\n", encoding="utf-8")
        raw = self.dir / "data" / "live" / "raw" / "S68"
        raw.mkdir(parents=True)
        self.raw_old = raw / "20260901T100000Z.xml"
        self.raw_old.write_text("<rss>Ministar Petrović ...</rss>", encoding="utf-8")
        old_ts = dt.datetime(2026, 9, 1, 10, 0, tzinfo=dt.timezone.utc).timestamp()
        os.utime(self.raw_old, (old_ts, old_ts))
        self.raw_new = raw / "20261201T100000Z.xml"
        self.raw_new.write_text("<rss>sveza</rss>", encoding="utf-8")
        new_ts = dt.datetime(2026, 12, 1, 10, 0, tzinfo=dt.timezone.utc).timestamp()
        os.utime(self.raw_new, (new_ts, new_ts))

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def rows(self):
        return [json.loads(l) for l in self.f.read_text(encoding="utf-8").splitlines() if l.strip()]

    def test_a_dry_run_writes_nothing(self):
        before = self.f.read_bytes()
        plan = R.due(self.dir, self.policy, NOW)
        self.assertEqual(sum(i["rows"] for i in plan["rows"]), 1)
        self.assertEqual(len(plan["raw"]), 1)
        self.assertEqual(self.f.read_bytes(), before)
        self.assertTrue(self.raw_old.exists())
        self.assertFalse((self.dir / R.LEDGER).exists())

    def test_the_sentence_goes_and_the_evidence_stays(self):
        R.apply(self.dir, self.policy, NOW, R.due(self.dir, self.policy, NOW))
        old, fresh, meas = self.rows()
        self.assertIsNone(old["result"])
        self.assertEqual(old["redacted"]["rule"], "R1")
        for keep in ("sid", "link", "resultTime", "receivedTime", "dedupe_key", "raw_sha256",
                     "permission_capture", "phenomenonTimeUnknown", "resultQuality"):
            self.assertIn(keep, old, keep + " was lost with the sentence")
        self.assertEqual(old["link"], "https://example.rs/a/1")
        self.assertEqual(old["raw_sha256"], "0" * 64)
        self.assertEqual(fresh["result"], "Sveza vest o gradu")
        self.assertEqual(meas["result"], 37.2)

    def test_a_measurement_is_never_touched_however_old(self):
        R.apply(self.dir, self.policy, NOW, R.due(self.dir, self.policy, NOW))
        meas = self.rows()[2]
        self.assertNotIn("redacted", meas)
        self.assertEqual(meas["result"], 37.2)

    def test_the_raw_capture_of_a_due_feed_is_deleted_and_a_fresh_one_is_not(self):
        R.apply(self.dir, self.policy, NOW, R.due(self.dir, self.policy, NOW))
        self.assertFalse(self.raw_old.exists())
        self.assertTrue(self.raw_new.exists())

    def test_the_ledger_records_the_erasure_and_the_file_hashes(self):
        R.apply(self.dir, self.policy, NOW, R.due(self.dir, self.policy, NOW))
        entries = [json.loads(l) for l in (self.dir / R.LEDGER).read_text(encoding="utf-8").splitlines()]
        by_rule = {e["rule"]: e for e in entries}
        self.assertEqual(by_rule["R1"]["rows_redacted"], 1)
        self.assertNotEqual(by_rule["R1"]["sha256_before"], by_rule["R1"]["sha256_after"])
        self.assertEqual(len(by_rule["R2"]["sha256_deleted"]), 64)
        self.assertTrue(by_rule["R2"]["deleted"])

    def test_running_it_twice_changes_nothing_the_second_time(self):
        R.apply(self.dir, self.policy, NOW, R.due(self.dir, self.policy, NOW))
        after = self.f.read_bytes()
        n = len((self.dir / R.LEDGER).read_text(encoding="utf-8").splitlines())
        R.apply(self.dir, self.policy, NOW, R.due(self.dir, self.policy, NOW))
        self.assertEqual(self.f.read_bytes(), after)
        self.assertEqual(len((self.dir / R.LEDGER).read_text(encoding="utf-8").splitlines()), n)

    def test_nothing_is_due_before_the_window_closes(self):
        early = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)   # 61 days after the old row
        plan = R.due(self.dir, self.policy, early)
        self.assertEqual(plan["rows"], [])
        self.assertEqual(plan["first_erasure_due"], "2026-11-30")

    def test_a_truncated_line_is_left_exactly_as_it_was(self):
        with open(self.f, "a", encoding="utf-8") as f:
            f.write('{"schema": "beops-observation-row/v1", "sid": "S68", "para')
        R.apply(self.dir, self.policy, NOW, R.due(self.dir, self.policy, NOW))
        tail = self.f.read_text(encoding="utf-8").splitlines()[-1]
        self.assertEqual(tail, '{"schema": "beops-observation-row/v1", "sid": "S68", "para')

    def test_the_policy_covers_every_news_source_we_poll(self):
        coll = json.loads((ROOT / "research" / "COLLECTORS.json").read_text(encoding="utf-8"))
        news = {s["sid"] for s in coll["sources"] if s.get("parser") in ("rss", "city_listing")}
        r1 = next(r for r in self.policy["rules"] if r["id"] == "R1")
        self.assertEqual(news - set(r1["sids"]), set(),
                         "a news source is polled that the retention rule does not cover")


if __name__ == "__main__":
    unittest.main(verbosity=2)
