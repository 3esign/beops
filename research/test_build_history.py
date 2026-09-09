"""Offline tests for tools/build_history.py.

The rules tested are the ones a chart makes easy to break: a gap is not a zero, a null result is
not a zero, a source with no measurement time is bucketed by reception and says so, and text rows
are counted rather than averaged.
"""
import importlib.util
import json
import pathlib
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("build_history", ROOT / "tools" / "build_history.py")
bh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bh)

NOW = datetime(2026, 9, 9, 14, 30, tzinfo=timezone.utc)


def row(**kw):
    base = {"sid": "S01", "datastream": "Beograd|temperature", "station_name": "Beograd",
            "parameter": "temperature", "unit": "Cel", "result": 20.0,
            "phenomenonTime": "2026-09-09T10:00:00Z", "phenomenonTimeUnknown": False,
            "receivedTime": "2026-09-09T10:05:00Z"}
    base.update(kw)
    return base


class HistoryCase(unittest.TestCase):
    def fold(self, rows_by_sid):
        tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(tmp.name)
        for sid, rows in rows_by_sid.items():
            d = root / "data" / "live" / "rows" / sid
            d.mkdir(parents=True, exist_ok=True)
            (d / "2026-09.jsonl").write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
        (root / "research").mkdir(parents=True, exist_ok=True)
        (root / "research" / "COLLECTORS.json").write_text(
            json.dumps({"sources": [{"sid": "S01", "cadence_seconds": 900}]}), encoding="utf-8")
        old_rows, old_cfg = bh.ROWS, bh.CONFIG
        bh.ROWS = root / "data" / "live" / "rows"
        bh.CONFIG = root / "research" / "COLLECTORS.json"
        try:
            return bh.fold(now=NOW)
        finally:
            bh.ROWS, bh.CONFIG = old_rows, old_cfg
            tmp.cleanup()

    def test_an_absent_hour_is_absent_not_a_zero(self):
        d = self.fold({"S01": [row(phenomenonTime="2026-09-09T10:00:00Z", result=20.0),
                               row(phenomenonTime="2026-09-09T13:00:00Z", result=26.0)]})
        s = d["series"][0]
        self.assertEqual(sorted(s["buckets"]), ["2026-09-09T10", "2026-09-09T13"])
        self.assertNotIn("2026-09-09T11", s["buckets"])          # no bucket at all, not a zero one
        self.assertEqual((s["hours_present"], s["hours_expected"]), (2, 4))
        self.assertEqual(d["hours_of_history"], 4)

    def test_a_null_result_is_missing_and_never_enters_the_mean(self):
        d = self.fold({"S01": [row(result=20.0), row(result=None), row(result=30.0)]})
        b = d["series"][0]["buckets"]["2026-09-09T10"]
        self.assertEqual((b["n"], b["missing"]), (3, 1))
        self.assertEqual((b["min"], b["max"], b["mean"]), (20.0, 30.0, 25.0))   # not 16.67

    def test_a_source_without_a_measurement_time_is_bucketed_by_reception_and_says_so(self):
        d = self.fold({"S01": [row(phenomenonTime=None, phenomenonTimeUnknown=True,
                                   receivedTime="2026-09-09T12:20:00Z", result=5.0)]})
        s = d["series"][0]
        self.assertEqual(s["time_basis"], "received")
        self.assertEqual(sorted(s["buckets"]), ["2026-09-09T12"])

    def test_measured_and_received_series_are_never_folded_together(self):
        d = self.fold({"S01": [row(result=20.0),
                               row(phenomenonTime=None, phenomenonTimeUnknown=True,
                                   receivedTime="2026-09-09T10:20:00Z", result=99.0)]})
        bases = sorted(s["time_basis"] for s in d["series"])
        self.assertEqual(bases, ["measured", "received"])
        measured = next(s for s in d["series"] if s["time_basis"] == "measured")
        self.assertEqual(measured["buckets"]["2026-09-09T10"]["max"], 20.0)   # 99 stayed out

    def test_text_rows_are_counted_and_not_averaged(self):
        d = self.fold({"S01": [row(datastream="S68|news", parameter="headline", result=None,
                                   result_text="a headline", unit=None)]})
        s = d["series"][0]
        self.assertEqual(s["kind"], "count")
        self.assertNotIn("mean", s["buckets"]["2026-09-09T10"])
        self.assertEqual(s["buckets"]["2026-09-09T10"]["n"], 1)

    def test_a_truncated_line_is_skipped_and_the_rest_still_folds(self):
        tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(tmp.name)
        d = root / "data" / "live" / "rows" / "S01"
        d.mkdir(parents=True, exist_ok=True)
        (d / "2026-09.jsonl").write_text(json.dumps(row()) + '\n{"sid": "S01", "datast\n',
                                         encoding="utf-8")
        old_rows, old_cfg = bh.ROWS, bh.CONFIG
        bh.ROWS, bh.CONFIG = root / "data" / "live" / "rows", root / "nope.json"
        try:
            out = bh.fold(now=NOW)
        finally:
            bh.ROWS, bh.CONFIG = old_rows, old_cfg
            tmp.cleanup()
        self.assertEqual(len(out["series"]), 1)
        self.assertEqual(out["series"][0]["buckets"]["2026-09-09T10"]["n"], 1)

    def test_an_interval_is_bucketed_by_its_start_hour(self):
        d = self.fold({"S01": [row(phenomenonTime="2026-09-09T10:00:00Z/2026-09-09T11:00:00Z", result=7.0)]})
        s = d["series"][0]
        self.assertEqual(s["time_basis"], "measured")
        self.assertEqual(sorted(s["buckets"]), ["2026-09-09T10"])   # the hour the source labels it with

    def test_an_interval_object_is_bucketed_by_its_start(self):
        # SEPA's hourly means arrive as {"start": ..., "end": ...}; the value belongs to the hour the
        # source labels it with, which is the start.
        d = self.fold({"S01": [row(phenomenonTime={"start": "2026-09-09T10:00:00Z",
                                                   "end": "2026-09-09T11:00:00Z"}, result=41.0)]})
        s = d["series"][0]
        self.assertEqual(s["time_basis"], "measured")
        self.assertEqual(sorted(s["buckets"]), ["2026-09-09T10"])
        self.assertEqual(d["unreadable_measurement_times"], {})

    def test_an_unreadable_measurement_time_is_dropped_not_moved_to_the_other_clock(self):
        d = self.fold({"S01": [row(phenomenonTime="whenever", receivedTime="2026-09-09T12:00:00Z"),
                               row(result=1.0)]})
        self.assertEqual(d["unreadable_measurement_times"], {"S01": 1})
        self.assertEqual([s["time_basis"] for s in d["series"]], ["measured"])
        self.assertEqual(sorted(d["series"][0]["buckets"]), ["2026-09-09T10"])

    def test_rows_from_the_future_and_the_distant_past_are_left_out(self):
        d = self.fold({"S01": [row(phenomenonTime="2026-09-09T10:00:00Z"),
                               row(phenomenonTime="2027-01-01T00:00:00Z"),
                               row(phenomenonTime="2020-01-01T00:00:00Z")]})
        self.assertEqual(sorted(d["series"][0]["buckets"]), ["2026-09-09T10"])


if __name__ == "__main__":
    unittest.main()
