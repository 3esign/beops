"""The serious-baseline gate counts complete days, gaps, duplicates and revisions."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import history_qualification as hq


NOW = datetime(2026, 9, 13, 12, tzinfo=timezone.utc)
START = datetime(2026, 8, 14, tzinfo=timezone.utc)


class Qualification(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        (self.root / "research").mkdir()
        config = {
            "schema": "beops-collectors/v1",
            "sources": [{"sid": "S1", "name": "Fixture", "url": "https://invalid.test",
                         "parser": "fixture", "cadence_seconds": 86400, "enabled": True}],
        }
        policy = {
            "schema": "beops-history-qualification-policy/v1",
            "windows_days": [7, 14, 30],
            "serious_baseline": {
                "consecutive_complete_calendar_days": 30,
                "minimum_receipt_coverage": 0.9,
                "minimum_valid_observations_per_used_hour_bucket": 20,
            },
            "limits": ["missing remains missing"],
        }
        (self.root / "research/COLLECTORS.json").write_text(json.dumps(config), encoding="utf-8")
        (self.root / "research/HISTORY_QUALIFICATION_POLICY.json").write_text(
            json.dumps(policy), encoding="utf-8"
        )
        receipts = self.root / "data/live/receipts/S1"
        rows = self.root / "data/live/rows/S1"
        receipts.mkdir(parents=True)
        rows.mkdir(parents=True)
        for day in range(27):
            at = START + timedelta(days=day, hours=1)
            receipt = {"schema": "beops-live-receipt/v1", "sid": "S1", "state": "captured",
                       "attempted_at": hq.iso(at), "rows": 5, "rows_new": 3}
            (receipts / f"{day:02d}.json").write_text(json.dumps(receipt), encoding="utf-8")
        duplicate = {"schema": "beops-live-receipt/v1", "sid": "S1", "state": "captured",
                     "attempted_at": hq.iso(START + timedelta(hours=2)), "rows": 2, "rows_new": 2}
        (receipts / "duplicate.json").write_text(json.dumps(duplicate), encoding="utf-8")
        # A receipt after two empty slots makes the preceding watch gap observable.
        failed_at = START + timedelta(days=29, hours=1)
        failed = {"schema": "beops-live-receipt/v1", "sid": "S1", "state": "failed",
                  "attempted_at": hq.iso(failed_at), "rows": 0, "rows_new": 0}
        (receipts / "failed.json").write_text(json.dumps(failed), encoding="utf-8")
        observations = []
        for day in range(30):
            at = START + timedelta(days=day, hours=3)
            observations.append({
                "schema": "beops-observation-row/v1", "sid": "S1", "datastream": "x",
                "station_name": "Zone", "parameter": "x", "unit": "u", "result": day,
                "phenomenonTime": hq.iso(at), "phenomenonTimeUnknown": False,
                "resultTime": hq.iso(at), "receivedTime": hq.iso(at + timedelta(minutes=1)),
                "resultQuality": "fixture",
            })
        revised = dict(observations[0])
        revised["result"] = 999
        revised["receivedTime"] = hq.iso(START + timedelta(hours=3, minutes=2))
        observations.append(revised)
        (rows / "2026.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in observations), encoding="utf-8"
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_thirty_day_gate_and_counts_are_explicit(self):
        report = hq.build(self.root, NOW)
        window7, window14, window30 = report["windows"]
        self.assertEqual([window7["days"], window14["days"], window30["days"]], [7, 14, 30])
        source = window30["sources"][0]
        self.assertEqual(source["expected_receipt_slots"], 30)
        self.assertEqual(source["captured_receipt_slots"], 27)
        self.assertEqual(source["failed_receipt_slots"], 1)
        self.assertEqual(source["missing_receipt_slots"], 2)
        self.assertEqual(source["duplicate_receipts_in_slot"], 1)
        self.assertEqual(source["duplicate_rows_discarded"], 54)
        self.assertGreaterEqual(source["late_receipt_slots"], 1)
        self.assertEqual(source["revised_events"], 1)
        self.assertEqual(source["observation_days"], 30)
        self.assertTrue(source["eligible_source_for_serious_baseline"])
        self.assertEqual(report, hq.build(self.root, NOW))

    def test_daily_output_is_immutable_and_versioned(self):
        report = hq.build(self.root, NOW)
        first = hq.persist(report, self.root)
        second = hq.persist(report, self.root)
        self.assertEqual(first["daily"], second["daily"])
        changed = dict(report)
        changed["report_sha256"] = "0" * 64
        with self.assertRaisesRegex(FileExistsError, "preserve both"):
            hq.persist(changed, self.root)


if __name__ == "__main__":
    unittest.main()
