#!/usr/bin/env python3
"""test_make_layers.py - 28 KB that draw the scheme on the landing page, and nothing tested them.

The largest unguarded surface the C-050 sweep found. This drawing is not decoration: every plate is
an idiom that states something read from the registers - one clock per periodic source, one ring per
live source, the census hexagons at their real coordinates, the registry's own record count written
under the slab. Each of those is a number in a picture, which is the easiest place in this project
for a number to stop matching the record without anyone noticing.

The claim the drawing exists to make - **nothing overhangs the law** - is a geometric fact about the
slab, and it is checked here as one.
"""
import json
import pathlib
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_layers as ml  # noqa: E402

POLY = re.compile(r'<polygon class="([^"]*)" points="([^"]*)"')


def xs(points: str):
    return [float(p.split(",")[0]) for p in points.split() if "," in p]


class Layers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "research" / "SOURCE_REGISTRY.json").exists():
            raise unittest.SkipTest("no registry on this machine")
        cls.c = ml.counts()
        cls.svg = ml.build(cls.c)
        cls.small = ml.build(cls.c, small=True)

    def english(self):
        """The English labels as one run of prose. The drawing wraps a line at 66 characters into
        separate <text> elements, so a phrase that is plainly on the page is not in any single one
        of them - the first version of this test looked for one and did not find it."""
        return " ".join(re.findall(r'<text class="en-only[^"]*"[^>]*>([^<]*)</text>', self.svg))

    # ---------------------------------------------------------------- the registers it reads

    def test_the_polled_sources_are_split_and_not_double_counted(self):
        live, per = self.c["live"], self.c["periodic"]
        self.assertEqual(len(live) + len(per), self.c["polled"],
                         "a polled source is either drawn twice or not at all")
        self.assertTrue(all(s.get("cadence_seconds", 0) <= 900 for s in live))
        self.assertTrue(all(s.get("cadence_seconds", 0) > 900 for s in per))
        self.assertEqual(len({id(s) for s in live} & {id(s) for s in per}), 0)

    def test_the_record_count_under_the_slab_is_the_registry_count(self):
        """No second copy of a number: the figure written into the drawing is read from the file."""
        reg = json.loads((ROOT / "research" / "SOURCE_REGISTRY.json").read_text(encoding="utf-8"))
        self.assertEqual(self.c["records"], len(reg["sources"]))
        self.assertIn(f"{self.c['records']} registry records", self.english(),
                      "the drawing states a record count that is not the registry's")

    def test_the_static_layer_count_in_the_label_is_the_register(self):
        st = json.loads((ROOT / "research" / "STATIC_LAYERS.json").read_text(encoding="utf-8"))
        self.assertEqual(self.c["static"], len(st["layers"]))
        self.assertIn(f"{self.c['static']} layers", self.english())

    # ---------------------------------------------------------------- one mark per thing

    def test_one_clock_per_periodic_source_and_one_ring_per_live_source(self):
        clocks = ml.idiom_periodic(0, 0, self.c)
        live = ml.idiom_live(0, 0, self.c)
        self.assertEqual(clocks.count('class="clock"'), len(self.c["periodic"]))
        self.assertEqual(live.count('class="ring faint"'), len(self.c["live"]))
        self.assertEqual(live.count('class="dot"'), len(self.c["live"]))

    def test_an_empty_register_draws_nothing_rather_than_a_placeholder(self):
        """A drawing that shows a mark for a source that does not exist is worse than a blank plate."""
        blank = dict(self.c, live=[], periodic=[], basemap=None, people=None)
        self.assertEqual(ml.idiom_periodic(0, 0, blank), "")
        self.assertEqual(ml.idiom_live(0, 0, blank), "")
        self.assertEqual(ml.idiom_ground(0, 0, blank), "")
        self.assertEqual(ml.idiom_static(0, 0, blank), "")

    def test_the_five_states_and_no_sixth(self):
        states = json.loads((ROOT / "research" / "STATES.json").read_text(encoding="utf-8"))
        epistemic = set(states["epistemic"]["states"])
        drawn = ml.idiom_organize(0, 0, self.c)
        named = {w for w in ("observed", "untimed", "estimated", "forecast", "unavailable") if w in drawn}
        self.assertEqual(named, epistemic & named)
        self.assertEqual(len(named), 5, f"the organising plate draws {sorted(named)}, not the five states")
        self.assertTrue(named <= epistemic, "the drawing names a state the vocabulary does not declare")

    # ---------------------------------------------------------------- the claim the drawing makes

    def test_nothing_overhangs_the_law(self):
        """The editor's rule of 9 September, as geometry: the slab is wider than every plate on it."""
        slab, plates = [], []
        for cls, pts in POLY.findall(self.svg):
            if "slab" in cls and "top" in cls:
                slab += xs(pts)
            elif "top" in cls.split():
                plates.append(xs(pts))
        self.assertTrue(slab, "the law slab is not in the drawing")
        self.assertTrue(plates, "no stratum plate is in the drawing")
        lo, hi = min(slab), max(slab)
        for p in plates:
            self.assertGreaterEqual(min(p), lo - 0.5, "a plate hangs off the left edge of the law")
            self.assertLessEqual(max(p), hi + 0.5, "a plate hangs off the right edge of the law")

    def test_the_ground_and_the_census_are_named_where_they_are_drawn(self):
        """C-049 again: the drawing shows Natural Earth geometry and Kontur hexagons on its face."""
        self.assertIn("Natural Earth", self.svg)
        self.assertIn("public domain", self.svg)
        self.assertIn("Kontur", self.svg)
        self.assertIn("CC BY", self.svg)

    # ---------------------------------------------------------------- the drawing itself

    def test_every_label_exists_in_both_languages(self):
        for name, svg in (("full", self.svg), ("small", self.small)):
            sr, en = svg.count('class="sr-only'), svg.count('class="en-only')
            self.assertEqual(sr, en, f"{name}: {sr} Serbian labels and {en} English ones")
            self.assertGreater(sr, 0)
            texts = re.findall(r"<text([^>]*)>", svg)
            for t in texts:
                self.assertTrue("sr-only" in t or "en-only" in t,
                                f"{name}: a label belongs to neither language: <text{t[:80]}>")

    def test_the_drawing_is_well_formed_and_the_same_twice(self):
        ET.fromstring(self.svg)
        ET.fromstring(self.small)
        self.assertEqual(ml.build(self.c), self.svg, "the same registers draw two different pictures")

    def test_the_small_figure_is_the_same_drawing_and_not_a_different_claim(self):
        self.assertIn("small", self.small[:400])
        for n in (str(self.c["records"]), str(self.c["static"])):
            if n in self.small:
                self.assertIn(n, self.svg, "the small figure states a number the full drawing does not")


if __name__ == "__main__":
    unittest.main()
