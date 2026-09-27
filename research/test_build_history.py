"""Offline tests for tools/build_history.py.

The rules tested are the ones a chart makes easy to break: a gap is not a zero, a null result is
not a zero, a source with no measurement time is bucketed by reception and says so, and text rows
are counted rather than averaged.
"""
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
import weakref
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

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
        d = self.fold({"S01": [row(result=20.0),
                               row(result=None,phenomenonTime='2026-09-09T10:10:00Z'),
                               row(result=30.0,phenomenonTime='2026-09-09T10:20:00Z')]})
        b = d["series"][0]["buckets"]["2026-09-09T10"]
        self.assertEqual((b["n"], b["missing"]), (3, 1))
        self.assertEqual((b["min"], b["max"], b["mean"]), (20.0, 30.0, 25.0))   # not 16.67

    def test_a_revision_replaces_one_event_instead_of_becoming_an_extra_measurement(self):
        first = row(result=5.0, dedupe_key="S01|event")
        revised = row(result=20.0, receivedTime="2026-09-09T10:06:00Z", dedupe_key="S01|event")
        bucket = self.fold({"S01": [first, revised]})["series"][0]["buckets"]["2026-09-09T10"]
        self.assertEqual((bucket["n"], bucket["min"], bucket["max"]), (1, 20.0, 20.0))

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

    def test_a_truncated_line_fails_visibly_and_does_not_publish_a_partial_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = pathlib.Path(tmp) / 'rows'
            d = rows / 'S01'
            d.mkdir(parents=True)
            (d / '2026-09.jsonl').write_text('{"broken":', encoding='utf-8')
            with patch.object(bh, 'ROWS', rows), self.assertRaisesRegex(ValueError, 'invalid JSONL'):
                bh.fold(now=NOW)

    def test_an_interval_is_bucketed_by_its_end_hour(self):
        d = self.fold({"S01": [row(phenomenonTime="2026-09-09T10:00:00Z/2026-09-09T11:00:00Z", result=7.0)]})
        s = d["series"][0]
        self.assertEqual(s["time_basis"], "measured")
        self.assertEqual(sorted(s["buckets"]), ["2026-09-09T11"])   # canonical interval-end hour

    def test_an_interval_object_is_bucketed_by_its_end(self):
        # SEPA's hourly means arrive as {"start": ..., "end": ...}; the value belongs to the hour the
        # source labels it with, which is the start.
        d = self.fold({"S01": [row(phenomenonTime={"start": "2026-09-09T10:00:00Z",
                                                   "end": "2026-09-09T11:00:00Z"}, result=41.0)]})
        s = d["series"][0]
        self.assertEqual(s["time_basis"], "measured")
        self.assertEqual(sorted(s["buckets"]), ["2026-09-09T11"])
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

    def test_streamed_windows_match_materialized_json_bytes_and_preserve_input(self):
        data = self.fold({
            "S01": [row(station_name="Čukarica", result=20.123456),
                    row(result=None, phenomenonTime="2026-09-09T13:00:00Z"),
                    row(result=5, phenomenonTime=None, phenomenonTimeUnknown=True)],
            "S02": [row(sid="S02", parameter="headline", unit=None,
                        datastream="news", result=None, result_text="Živi grad")],
            "S03": [row(sid="S03", parameter="wind_direction", unit="deg",
                        datastream="direction", result=359)],
        })
        data["input_generation"] = {"id": "frozen-fixture", "as_of": "2026-09-09T14:30:00Z"}
        before = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        for days, now in [(7, NOW), (14, NOW), (30, NOW),
                          (7, NOW + timedelta(days=7)),
                          (7, NOW + timedelta(days=20))]:
            with self.subTest(days=days, now=now):
                window = bh.narrow(data, days, now)
                expected = json.dumps(window, ensure_ascii=False, separators=(",", ":"))
                target = io.StringIO()
                summary = bh.write_window(data, days, now, target)
                self.assertEqual(target.getvalue().encode("utf-8"), expected.encode("utf-8"))
                self.assertEqual(summary["series_count"], len(window["series"]))
                self.assertEqual(summary["hours_of_history"], window["hours_of_history"])
        self.assertEqual(json.dumps(data, ensure_ascii=False, separators=(",", ":")), before)

    def test_streamed_window_releases_compact_buckets_before_next_series(self):
        data = self.fold({"S01": [row()]})
        template = data["series"][0]
        bucket = next(iter(template["buckets"].values()))
        data["series"] = [dict(template, datastream=str(index), buckets={
            (NOW - timedelta(hours=hour)).strftime("%Y-%m-%dT%H"): bucket
            for hour in range(40)}) for index in range(8)]
        alive = weakref.WeakSet()
        peak = 0
        compact = bh.compact

        class TrackedBucket(dict):
            __hash__ = object.__hash__

        def track(bucket):
            nonlocal peak
            value = TrackedBucket(compact(bucket))
            alive.add(value)
            peak = max(peak, len(alive))
            return value

        with patch.object(bh, "compact", side_effect=track):
            summary = bh.write_window(data, 7, NOW, io.StringIO())
        self.assertEqual(summary["series_count"], 8)
        self.assertEqual(peak, 40)
        self.assertEqual(len(alive), 0)


if __name__ == "__main__":
    unittest.main()
