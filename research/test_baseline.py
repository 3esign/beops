#!/usr/bin/env python3
"""test_baseline.py - the usual, offline. Built rows in a temporary tree; no network, no daemon."""
import importlib
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import baseline as bl  # noqa: E402

NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def AT(hour: int, minute: int, days_ago: int) -> datetime:
    """A time pinned INSIDE one hour. Subtracting minutes from a whole hour crosses into the previous
    one and quietly splits a bucket in two - which is how the first version of this test lied."""
    return (NOW - timedelta(days=days_ago)).replace(hour=hour, minute=minute, second=0, microsecond=0)


def row(sid, station, par, value, when: datetime, timed=True, unit="ug.m-3"):
    r = {"schema": "beops-row/v1", "sid": sid, "station_id": station, "station_name": station,
         "parameter": par, "result": value, "unit": unit,
         "receivedTime": when.isoformat().replace("+00:00", "Z")}
    if timed:
        r["phenomenonTime"] = {"start": None, "end": when.isoformat().replace("+00:00", "Z")}
        r["phenomenonTimeUnknown"] = False
    else:
        r["phenomenonTime"] = None
        r["phenomenonTimeUnknown"] = True
    return r


class Tree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.tmp.name)
        bl.ROOT = base
        bl.ROWS = base / "data" / "live" / "rows"
        bl.OUT = base / "data" / "live" / "derived" / "baseline"
        bl.ROWS.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, sid, rows):
        d = bl.ROWS / sid
        d.mkdir(exist_ok=True)
        (d / "2026-09.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


class Buckets(Tree):
    def test_a_usual_needs_enough_days_and_enough_values_or_it_is_absent(self):
        """A thin bucket is left OUT, never filled in. Two afternoons is an anecdote; the record says
        nothing rather than something it cannot support - which is the same rule as missing-is-not-zero,
        applied to a summary instead of to a value."""
        rows = []
        for day in range(2):                       # only two days
            for i in range(6):
                rows.append(row("S146", "Stari grad", "PM10", 20 + i, AT(9, i, day)))
        self.write("S146", rows)
        b = bl.build_source("S146", now=NOW)
        self.assertEqual(b["buckets"], {})
        self.assertEqual(b["buckets_too_thin_to_publish"], 1)

        for day in range(2, 5):                    # now five days
            for i in range(6):
                rows.append(row("S146", "Stari grad", "PM10", 20 + i, AT(9, i, day)))
        self.write("S146", rows)
        b = bl.build_source("S146", now=NOW)
        self.assertEqual(len(b["buckets"]), 1)
        got = bl.usual(b, "Stari grad", "PM10", 9)
        self.assertEqual((got["median"], got["days"], got["n"]), (22.5, 5, 30))

    def test_a_missing_value_is_not_a_zero(self):
        rows = []
        for day in range(5):
            for i in range(6):
                rows.append(row("S146", "Zemun", "PM10", 40, AT(10, i, day)))
            rows.append(row("S146", "Zemun", "PM10", None, AT(10, 9, day)))
        self.write("S146", rows)
        b = bl.build_source("S146", now=NOW)
        got = bl.usual(b, "Zemun", "PM10", 10)
        self.assertEqual((got["median"], got["n"], got["min"]), (40.0, 30, 40.0))

    def test_a_source_without_a_measurement_time_is_bucketed_by_ARRIVAL_and_says_so(self):
        """Parking publishes no measurement time. Its hour is the hour we heard from it, which is a
        different fact, and the bucket carries the difference rather than hiding it."""
        rows = [row("S10", "Pinki", "free_spaces", 90 + i, AT(11, i, d),
                    timed=False, unit="1")
                for d in range(5) for i in range(6)]
        self.write("S10", rows)
        b = bl.build_source("S10", now=NOW)
        got = bl.usual(b, "Pinki", "free_spaces", 11)
        self.assertFalse(got["hour_is_the_measurement_s_own"])

    def test_stations_parameters_and_hours_never_mix(self):
        rows = []
        for d in range(5):
            for i in range(6):
                rows.append(row("S146", "Stari grad", "PM10", 20, AT(8, i, d)))
                rows.append(row("S146", "Zemun", "PM10", 60, AT(8, i, d)))
                rows.append(row("S146", "Stari grad", "NO2", 5, AT(8, i, d)))
                rows.append(row("S146", "Stari grad", "PM10", 99, AT(5, i, d)))
        self.write("S146", rows)
        b = bl.build_source("S146", now=NOW)
        h4 = 8
        h7 = 5
        self.assertEqual(bl.usual(b, "Stari grad", "PM10", h4)["median"], 20.0)
        self.assertEqual(bl.usual(b, "Zemun", "PM10", h4)["median"], 60.0)
        self.assertEqual(bl.usual(b, "Stari grad", "NO2", h4)["median"], 5.0)
        self.assertEqual(bl.usual(b, "Stari grad", "PM10", h7)["median"], 99.0)

    def test_a_headline_is_not_a_measurement(self):
        rows = [row("S69", "S69", "headline", 1, AT(11, i, d))
                for d in range(5) for i in range(6)]
        self.write("S69", rows)
        b = bl.build_source("S69", now=NOW)
        self.assertEqual(b["buckets"], {})

    def test_it_says_what_it_is_and_refuses_to_be_a_threshold(self):
        """The wording is load-bearing: this number will be read by people and by models, and neither
        may take it for a limit."""
        rows = [row("S146", "Stari grad", "PM10", 20, AT(9, i, d))
                for d in range(5) for i in range(6)]
        self.write("S146", rows)
        b = bl.build_source("S146", now=NOW)
        what = b["what_this_is"].lower()
        self.assertIn("not a norm", what)
        self.assertIn("health", what)
        for forbidden in ("limit value", "safe", "acceptable", "exceeds the standard"):
            self.assertNotIn(forbidden, what)

    def test_nothing_is_written_for_a_source_with_no_record(self):
        self.assertIsNone(bl.build_source("S999", now=NOW))
        self.assertIsNone(bl.usual(None, "x", "y", 3))


if __name__ == "__main__":
    unittest.main()
