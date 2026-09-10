#!/usr/bin/env python3
"""test_latency.py - the age of a value when it reached us. Built rows in a temporary tree.

The properties that matter are not arithmetic. They are: that the corrected clock wins over the label
where one exists; that a source publishing no measurement time gets a sentence rather than a number;
that a thin sample is withheld rather than described; and that our own polling interval travels beside
every age, because it is part of every age and the record cannot subtract it.
"""
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import latency as lt  # noqa: E402

NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def Z(d):
    return d.isoformat().replace("+00:00", "Z")


def row(sid, par, value, end: datetime | None, received: datetime, corrected: datetime | None = None,
        note: str | None = None):
    r = {"schema": "beops-row/v1", "sid": sid, "station_id": "A", "station_name": "A",
         "parameter": par, "result": value, "unit": "Cel", "receivedTime": Z(received)}
    if end is None:
        r["phenomenonTime"] = None
        r["phenomenonTimeUnknown"] = True
    else:
        r["phenomenonTime"] = {"start": None, "end": Z(end)}
        r["phenomenonTimeUnknown"] = False
    if corrected is not None:
        r["phenomenonTimeCorrected"] = {"start": None, "end": Z(corrected), "state": "estimated",
                                        "why": note or "the source labels local time as Z"}
        r["sourceClockNote"] = note or "the source labels local time as Z"
    return r


class Tree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.tmp.name)
        lt.ROOT = base
        lt.ROWS = base / "data" / "live" / "rows"
        lt.OUT = base / "data" / "live" / "derived" / "latency"
        lt.COLLECTORS = base / "collectors.json"
        lt.ROWS.mkdir(parents=True)
        lt.COLLECTORS.write_text(json.dumps({"sources": [{"sid": "S01", "cadence_seconds": 600},
                                                         {"sid": "S99", "cadence_seconds": 3600}]}), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, sid, rows):
        d = lt.ROWS / sid
        d.mkdir(exist_ok=True)
        (d / "2026-09.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


class Ages(Tree):
    def test_the_corrected_clock_wins_over_the_label(self):
        """C-040 in one assertion. A source whose label is two hours ahead would show an age two hours
        too small - and, half the time, negative - if the layer read the label. It reads the correction
        and says which clock it used."""
        rows = []
        for i in range(30):
            rx = NOW - timedelta(minutes=10 * i)
            label = rx + timedelta(minutes=110)          # two hours ahead, as SEPA labels them
            true_end = rx - timedelta(minutes=10)
            rows.append(row("S01", "PM10", 20.0 + i, label, rx, corrected=true_end))
        self.write("S01", rows)
        b = lt.build_source("S01", now=NOW, src={"cadence_seconds": 600})
        self.assertEqual(b["clocks"], ["corrected"])
        self.assertEqual(b["arrived_before_the_window_closed"], 0)
        self.assertAlmostEqual(b["age_minutes"]["median"], 10.0, delta=0.6)
        self.assertIn("labels local time", b["source_clock_note"])

    def test_a_source_with_no_measurement_time_gets_a_sentence_and_no_number(self):
        """Missing is not zero, and it is not a fast source either. An absent measurement time may
        never be rendered as an age of nothing."""
        rows = [row("S99", "free_spaces", 40 + i, None, NOW - timedelta(minutes=5 * i)) for i in range(40)]
        self.write("S99", rows)
        b = lt.build_source("S99", now=NOW, src={"cadence_seconds": 3600})
        self.assertIsNone(b["age_minutes"])
        self.assertEqual(b["rows_with_a_measurement_time"], 0)
        self.assertEqual(b["rows_without_a_measurement_time"], 40)
        self.assertIn("no measurement time at all", b["what_this_source_publishes"])

    def test_a_thin_sample_is_withheld_rather_than_described(self):
        rows = [row("S01", "temperature", 20.0, NOW - timedelta(minutes=5 + i), NOW - timedelta(minutes=i))
                for i in range(lt.MIN_N - 1)]
        self.write("S01", rows)
        b = lt.build_source("S01", now=NOW, src={"cadence_seconds": 600})
        self.assertIsNone(b["age_minutes"])
        self.assertIn("too few timed values", b["what_this_source_publishes"])

    def test_our_own_polling_interval_travels_with_the_age(self):
        """The age contains the publisher's delay plus up to one interval of ours, and the record
        cannot split them. It must therefore never present the age as the publisher's alone."""
        rows = [row("S01", "temperature", 20.0, NOW - timedelta(minutes=5 + i), NOW - timedelta(minutes=i))
                for i in range(30)]
        self.write("S01", rows)
        b = lt.build_source("S01", now=NOW, src={"cadence_seconds": 600})
        self.assertEqual(b["our_polling_interval_minutes"], 10)
        self.assertIn("cannot separate", b["what_this_is"])
        self.assertIn("not a measurement of the publisher alone", b["what_this_is"])

    def test_two_clocks_are_never_blended_into_one_number(self):
        """The layer's own first run did this: it averaged a source's corrected rows together with the
        rows collected before its clock note existed, and printed one median across both. Two clocks
        are not one distribution."""
        rows = []
        for i in range(30):                                   # later rows: corrected
            rx = NOW - timedelta(minutes=10 * i)
            rows.append(row("S01", "PM10", 20.0, rx + timedelta(minutes=110), rx,
                            corrected=rx - timedelta(minutes=10)))
        for i in range(30):                                   # earlier rows: label only
            rx = NOW - timedelta(minutes=10 * (i + 40))
            rows.append(row("S01", "PM10", 20.0, rx + timedelta(minutes=110), rx))
        self.write("S01", rows)
        b = lt.build_source("S01", now=NOW, src={"cadence_seconds": 600})
        self.assertIsNone(b["age_minutes"])
        self.assertEqual(b["mixed_clocks"], ["corrected", "measured"])
        self.assertEqual(sorted(b["age_by_clock"]), ["corrected", "measured"])
        self.assertAlmostEqual(b["age_by_clock"]["corrected"]["median"], 10.0, delta=0.6)
        self.assertLess(b["age_by_clock"]["measured"]["median"], 0)      # the label puts it in the future
        self.assertIn("not one distribution", b["what_this_source_publishes"])

    def test_it_is_never_called_a_quality_score(self):
        rows = [row("S01", "temperature", 20.0, NOW - timedelta(minutes=5 + i), NOW - timedelta(minutes=i))
                for i in range(30)]
        self.write("S01", rows)
        b = lt.build_source("S01", now=NOW, src={"cadence_seconds": 600})
        self.assertIn("not a quality score", b["what_this_is"])


if __name__ == "__main__":
    unittest.main()
