#!/usr/bin/env python3
"""test_make_maps.py - 19 KB that draw the three published maps, and nothing tested them.

Found by the C-050 sweep. These maps are cited in the paper and served on the site. They carry
counts in their legends, names beside their dots, and an attribution on their face - every one of
which is a claim, and none of which anything checked. A map is the easiest place in this project to
publish a number that is not in the record, because nobody reads a picture the way they read a table.

The rules enforced here are the project's own, applied to a drawing:
  - no second copy of a number: the legend's counts are the marks actually drawn
  - nothing drawn that the inputs do not contain: every dot is an instrument with a published
    coordinate, and every name beside a dot is that instrument's own
  - missing is not zero: a hollow mark means nothing was received, and it is counted as such
  - the ground is named where it is shown
"""
import json
import pathlib
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_maps as mm  # noqa: E402


class Maps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not mm.SNAPSHOT.exists():
            raise unittest.SkipTest("no live snapshot on this machine")
        cls.bm = json.loads(mm.BASEMAP.read_text(encoding="utf-8")) if mm.BASEMAP.exists() else {"features": []}
        cls.snap = json.loads(mm.SNAPSHOT.read_text(encoding="utf-8"))
        cls.pts = mm.instruments(cls.snap)
        cls.svgs = {"instruments": mm.map_instruments(cls.bm, cls.snap, cls.pts),
                    "coverage": mm.map_coverage(cls.bm, cls.snap, cls.pts),
                    "last24h": mm.map_last24h(cls.bm, cls.snap, cls.pts)}

    # ---------------------------------------------------------------- what may be drawn at all

    def test_every_point_is_an_instrument_the_snapshot_publishes_a_coordinate_for(self):
        want = set()
        for src in self.snap["sources"]:
            for ds in src["datastreams"]:
                if ds.get("lat") is not None and ds.get("lon") is not None:
                    want.add((src["sid"], ds.get("station")))
        self.assertEqual({p["key"] for p in self.pts}, want,
                         "the map draws a point that is not an instrument with a published coordinate")

    def test_nothing_is_drawn_outside_the_frame(self):
        """A mark outside the viewBox is counted in the legend and invisible on the page: the map
        says twelve and shows eleven, and nothing complains. One citizen sensor does sit outside -
        twelve pixels above the top edge - so the rule is not that it cannot happen but that it may
        never happen silently."""
        for svg in self.svgs.values():
            for x, y in re.findall(r"<circle cx='(-?[\d.]+)' cy='(-?[\d.]+)'", svg):
                self.assertTrue(-8 <= float(x) <= mm.W + 8 and -8 <= float(y) <= mm.H + 8,
                                f"a mark is drawn at ({x},{y}), outside {mm.W}x{mm.H}")

    def test_an_instrument_outside_the_frame_is_said_out_loud(self):
        """Missing is not zero, and neither is invisible. It stays in the counts and the map states
        how many it could not draw."""
        off = mm.off_frame(self.pts)
        self.assertEqual(off, sum(1 for p in self.pts if not mm.inside(p["lat"], p["lon"])))
        if off:
            self.assertIn("outside this frame", self.svgs["instruments"],
                          "an instrument is not drawn and the legend does not say so")
            self.assertIn(f"{off} outside this frame", self.svgs["last24h"],
                          "the last-24h map does not state what it could not draw")
        for p in self.pts:
            if not mm.inside(p["lat"], p["lon"]):
                self.assertIn(p["sid"], {s["sid"] for s in self.snap["sources"]},
                              "an instrument outside the frame was dropped from the record too")

    def test_every_name_beside_a_dot_is_that_instruments_own(self):
        stations = {p["station"] for p in self.pts if p["station"]}
        drawn = set(re.findall(r">([^<>]+)</text>", self.svgs["instruments"]))
        named = {d for d in drawn if d in stations}
        self.assertEqual(named, {p["station"] for p in self.pts if p["sid"] == "S146" and p["station"]},
                         "a station name on the map is not one of the named instruments")

    # ---------------------------------------------------------------- the legend is the drawing

    def test_the_legend_counts_are_the_marks_actually_drawn(self):
        """No second copy of a number, applied to a picture: the figure in the legend and the number
        of marks on the ground are the same count or one of them is wrong."""
        svg = self.svgs["instruments"]
        body = svg.split("<g transform='translate(0 ")[0]      # everything before the legend block
        n = {k: sum(1 for p in self.pts if p["sid"] == k) for k in ("S146", "S04", "S10")}
        off = {k: mm.off_frame(self.pts, k) for k in n}
        self.assertEqual(body.count("r='5'"), n["S146"] - off["S146"],
                         "SEPA marks drawn differ from SEPA instruments inside the frame")
        self.assertEqual(body.count("r='2.6'"), n["S04"] - off["S04"],
                         "citizen-sensor marks drawn differ from citizen sensors inside the frame")
        self.assertEqual(body.count("width='6' height='6'"), n["S10"] - off["S10"],
                         "parking marks drawn differ from parking lots inside the frame")
        for k in ("S146", "S04", "S10"):
            self.assertIn(f"({n[k]})", svg, f"the legend does not state how many {k} instruments exist")
            if off[k]:
                self.assertIn(f"({n[k]}) - {off[k]} outside this frame", svg,
                              f"the legend counts {k} instruments it did not draw and does not say so")

    def test_a_hollow_mark_means_nothing_was_received_and_is_counted_as_such(self):
        """Missing is not zero: a silent instrument is drawn as known-and-silent, not omitted."""
        svg = self.svgs["last24h"]
        body = svg.split("<g transform='translate(0 ")[0]      # the legend carries a swatch of each
        heard = [p for p in self.pts if p["rx"] > 0 and mm.inside(p["lat"], p["lon"])]
        silent = [p for p in self.pts if p["rx"] == 0 and mm.inside(p["lat"], p["lon"])]
        self.assertEqual(body.count("stroke-dasharray='2 2'"), len(silent),
                         "the hollow marks and the silent instruments are different counts")
        self.assertEqual(body.count("fill-opacity='.10'"), len(heard),
                         "the filled marks and the instruments heard are different counts")
        all_heard = sum(1 for p in self.pts if p["rx"] > 0)
        all_silent = sum(1 for p in self.pts if p["rx"] == 0)
        self.assertIn(f"{all_heard} instruments heard, {all_silent} silent", svg)
        self.assertEqual(all_heard + all_silent, len(self.pts))

    # ---------------------------------------------------------------- what the face must say

    def test_every_map_names_the_ground_it_is_drawn_on(self):
        """C-049's rule, on the artefact rather than in a register."""
        for name, svg in self.svgs.items():
            self.assertIn("Natural Earth", svg, f"{name} draws the basemap and does not name it")
            self.assertIn("public domain", svg, f"{name} does not say on what terms it may draw it")

    def test_the_refused_boundaries_are_stated_on_the_map_that_would_have_used_them(self):
        self.assertIn("refused", self.svgs["instruments"],
                      "the map omits municipality boundaries and does not say why")

    # ---------------------------------------------------------------- the drawing itself

    def test_the_maps_are_well_formed_xml(self):
        for name, svg in self.svgs.items():
            try:
                ET.fromstring(svg)
            except ET.ParseError as e:
                self.fail(f"{name} is not well-formed XML: {e}")

    def test_the_same_inputs_draw_the_same_map(self):
        """A map that changes without its inputs changing cannot be cited by a paper."""
        for name, fn in (("instruments", mm.map_instruments), ("coverage", mm.map_coverage),
                         ("last24h", mm.map_last24h)):
            self.assertEqual(fn(self.bm, self.snap, self.pts), self.svgs[name],
                             f"{name} is not the same drawing twice from the same files")

    def test_an_empty_snapshot_draws_no_instruments_rather_than_inventing_one(self):
        empty = {"as_of": self.snap["as_of"], "sources": [],
                 "status": {"sources": []}}
        pts = mm.instruments(empty)
        self.assertEqual(pts, [])
        svg = mm.map_last24h(self.bm, empty, pts)
        self.assertIn("0 instruments heard, 0 silent", svg)
        ET.fromstring(svg)


if __name__ == "__main__":
    unittest.main()
