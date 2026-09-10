#!/usr/bin/env python3
"""test_agreement.py - the gap between independent observers, offline.

The arithmetic is a subtraction. What has to hold is everything around it: that a comparison needs
enough shared hours or it is withheld; that two sources are never compared across two clocks; that a
unit mismatch is flagged rather than subtracted; and that the output never calls itself an error bar,
because the sources stand in different places and this record cannot separate the city from the
instruments.
"""
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import agreement as ag  # noqa: E402

NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def Z(d):
    return d.isoformat().replace("+00:00", "Z")


def row(sid, par, value, when: datetime, unit="Cel", station="A", corrected: datetime | None = None):
    r = {"schema": "beops-row/v1", "sid": sid, "station_id": station, "station_name": station,
         "parameter": par, "result": value, "unit": unit,
         "receivedTime": Z(when), "phenomenonTime": {"start": None, "end": Z(when)},
         "phenomenonTimeUnknown": False}
    if corrected is not None:
        r["phenomenonTimeCorrected"] = {"start": None, "end": Z(corrected), "state": "estimated",
                                        "why": "the source labels local time as Z"}
        r["sourceClockNote"] = "the source labels local time as Z"
    return r


class Tree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.tmp.name)
        ag.ROOT = base
        ag.ROWS = base / "data" / "live" / "rows"
        ag.OUT = base / "data" / "live" / "derived" / "agreement"
        ag.ROWS.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, sid, rows):
        d = ag.ROWS / sid
        d.mkdir(exist_ok=True)
        (d / "2026-09.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


class Gaps(Tree):
    def hours(self, n):
        return [NOW - timedelta(hours=i) for i in range(n)]

    def test_two_sources_over_enough_hours_produce_a_gap(self):
        hs = self.hours(10)
        self.write("S01", [row("S01", "temperature", 20.0, h) for h in hs])
        self.write("S03", [row("S03", "temperature", 22.0, h, station="airport") for h in hs])
        d = ag.build(now=NOW)
        e = d["parameters"]["temperature"]
        self.assertEqual(e["shared_hours"], 10)
        self.assertAlmostEqual(e["pairs"][0]["median_gap"], 2.0, places=2)
        self.assertEqual(sorted(e["sources"]), ["S01", "S03"])

    def test_too_few_shared_hours_is_withheld_not_described(self):
        hs = self.hours(ag.MIN_HOURS - 1)
        self.write("S01", [row("S01", "temperature", 20.0, h) for h in hs])
        self.write("S03", [row("S03", "temperature", 22.0, h) for h in hs])
        d = ag.build(now=NOW)
        self.assertEqual(d["parameters"], {})
        self.assertEqual(d["withheld_too_few_shared_hours"][0]["parameter"], "temperature")

    def test_a_corrected_source_is_compared_on_the_corrected_clock(self):
        """The whole point. S146's label is two hours ahead; if the layer read labels, its 12:00 would
        be compared against everyone else's 12:00 and the gap would be a fiction about the clock."""
        hs = self.hours(10)
        self.write("S01", [row("S01", "temperature", 20.0, h) for h in hs])
        self.write("S146", [row("S146", "temperature", 20.0, h + timedelta(hours=2), corrected=h) for h in hs])
        d = ag.build(now=NOW)
        e = d["parameters"]["temperature"]
        self.assertEqual(e["shared_hours"], 10)
        self.assertAlmostEqual(e["pairs"][0]["median_gap"], 0.0, places=2)
        self.assertEqual(e["sources"]["S146"]["clocks"], ["corrected"])

    def test_a_unit_mismatch_is_flagged_and_never_silently_subtracted(self):
        hs = self.hours(10)
        self.write("S01", [row("S01", "temperature", 20.0, h, unit="Cel") for h in hs])
        self.write("S03", [row("S03", "temperature", 68.0, h, unit="degF") for h in hs])
        d = ag.build(now=NOW)
        p = d["parameters"]["temperature"]["pairs"][0]
        self.assertFalse(p["units_match"])
        self.assertEqual({p["unit_a"], p["unit_b"]}, {"Cel", "degF"})

    def test_a_bearing_is_measured_on_a_circle_and_not_on_a_line(self):
        """350 and 10 are 20 degrees apart. Subtracting them gives 340, and the first run of this layer
        reported a 90th percentile of 186 degrees for wind direction - the signature of that error."""
        hs = self.hours(10)
        self.write("S01", [row("S01", "wind_direction", 350.0, h, unit="deg") for h in hs])
        self.write("S03", [row("S03", "wind_direction", 10.0, h, unit="deg") for h in hs])
        d = ag.build(now=NOW)
        e = d["parameters"]["wind_direction"]
        self.assertEqual(e["geometry"], "circular_degrees")
        self.assertAlmostEqual(e["pairs"][0]["median_gap"], 20.0, places=2)
        self.assertLessEqual(e["widest_gap"]["max"], 180.0)

    def test_a_bearing_median_within_an_hour_is_a_direction_not_an_average(self):
        """An hour holding 350 and 10 is a north wind. Averaged as numbers it becomes 180 - due south."""
        hs = self.hours(10)
        rows = []
        for h in hs:
            rows.append(row("S01", "wind_direction", 350.0, h, unit="deg"))
            rows.append(row("S01", "wind_direction", 10.0, h, unit="deg"))
        self.write("S01", rows)
        self.write("S03", [row("S03", "wind_direction", 0.0, h, unit="deg") for h in hs])
        d = ag.build(now=NOW)
        self.assertLess(d["parameters"]["wind_direction"]["pairs"][0]["median_gap"], 1.0)

    def test_a_gap_between_two_units_is_withheld_rather_than_published_with_a_warning(self):
        """hPa minus Pa is not a large disagreement; it is not a quantity. A number that means nothing
        must not be published with a caveat attached - the caveat is read second, if at all."""
        hs = self.hours(10)
        self.write("S01", [row("S01", "pressure", 1013.0, h, unit="hPa") for h in hs])
        self.write("S04", [row("S04", "pressure", 101300.0, h, unit="Pa") for h in hs])
        d = ag.build(now=NOW)
        p = d["parameters"]["pressure"]["pairs"][0]
        self.assertIsNone(p["median_gap"])
        self.assertIsNone(p["max_gap"])
        self.assertIn("different units", p["withheld"])
        self.assertIn("our arithmetic presented as their measurement", p["withheld"])
        self.assertIsNone(d["parameters"]["pressure"]["widest_gap"])
        self.assertIn("not a quantity", d["parameters"]["pressure"]["widest_gap_withheld"])

    def test_it_never_calls_itself_an_error_bar(self):
        hs = self.hours(10)
        self.write("S01", [row("S01", "temperature", 20.0, h) for h in hs])
        self.write("S03", [row("S03", "temperature", 22.0, h) for h in hs])
        d = ag.build(now=NOW)
        w = d["what_this_is"]
        self.assertIn("not an error bar", w)
        self.assertIn("cannot separate", w)
        self.assertNotIn("accuracy", w)
        self.assertIn("different places", d["parameters"]["temperature"]["these_are_different_places"])

    def test_one_source_alone_produces_nothing(self):
        hs = self.hours(20)
        self.write("S01", [row("S01", "pressure", 1013.0, h, unit="hPa") for h in hs])
        d = ag.build(now=NOW)
        self.assertEqual(d["parameters"], {})
        self.assertEqual(d["withheld_too_few_shared_hours"], [])


if __name__ == "__main__":
    unittest.main()
