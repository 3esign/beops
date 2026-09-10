#!/usr/bin/env python3
"""test_fetch_static.py - the layer that tells the mind how many people a reading is about.

`people_near()` is how a measurement becomes a statement about a city: "about nine thousand people
live within a kilometre of this station". The mind is allowed to say that, and everything it is
allowed to say has to be a fact read from the record. This function had no test.

Two properties are load-bearing and neither is obvious. It counts a hexagon **by its centroid**, so a
hexagon straddling the radius is wholly in or wholly out - at H3 resolution 8 that is a 460 m
quantisation, which is fine and must be stated rather than discovered. And with no population layer on
the machine it returns **None**, not zero: nobody living near a station and nothing known about who
lives near it are different answers, and this record never renders the second as the first.
"""
import json
import math
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import fetch_static as F  # noqa: E402

# hexes are [lon, lat, people, h3]
def ctx(hexes):
    return {"hexes": hexes, "layer": "kontur-population"}


class PeopleNear(unittest.TestCase):
    def test_missing_is_not_zero_when_there_is_no_population_layer(self):
        """With no layer on the machine the answer is unknown, not nobody."""
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            old = F.PUBLIC
            F.PUBLIC = pathlib.Path(t)
            try:
                self.assertIsNone(F.people_near(44.8, 20.45, 1.0))
            finally:
                F.PUBLIC = old

    def test_a_layer_that_is_present_and_empty_answers_unknown_and_not_nobody(self):
        """It used to return 0, which would have let the digest say 'nobody lives within a kilometre
        of this station' - false, and written in the same words as the true version."""
        self.assertIsNone(F.people_near(44.8, 20.45, 1.0, ctx={"hexes": []}))

    def test_an_empty_context_falls_back_to_the_published_layer_rather_than_answering_from_it(self):
        """A trap worth knowing about: the parameter is applied with `or`, so a caller who passes an
        empty dict gets the file on disk instead of their own empty context."""
        p = F.PUBLIC / "context-population.json"
        if not p.exists():
            self.skipTest("no population layer on this machine")
        self.assertIsNotNone(F.people_near(44.8186, 20.4573, 1.0, ctx={}))

    def test_it_sums_only_the_hexagons_inside_the_radius(self):
        c = ctx([[20.45, 44.80, 100, "a"],       # exactly on the point
                 [20.46, 44.80, 200, "b"],       # about 0.8 km east
                 [20.60, 44.80, 400, "c"]])      # about 12 km east
        self.assertEqual(F.people_near(44.80, 20.45, 1.0, c), 300)
        self.assertEqual(F.people_near(44.80, 20.45, 0.1, c), 100)
        self.assertEqual(F.people_near(44.80, 20.45, 20.0, c), 700)

    def test_it_never_shrinks_as_the_radius_grows(self):
        c = ctx([[20.40 + i * 0.01, 44.80, 10 * (i + 1), str(i)] for i in range(12)])
        got = [F.people_near(44.80, 20.45, r, c) for r in (0.2, 0.5, 1, 2, 5, 10)]
        self.assertEqual(got, sorted(got), "a larger radius returned fewer people")

    def test_a_hexagon_is_counted_by_its_centroid_and_not_by_its_overlap(self):
        """Stated in the docstring and true in the arithmetic: the quantisation is the hexagon."""
        east = 20.45 + 1.2 / (111.32 * math.cos(math.radians(44.8)))    # 1.2 km east of the point
        c = ctx([[east, 44.80, 5000, "just outside"]])
        self.assertEqual(F.people_near(44.80, 20.45, 1.0, c), 0,
                         "a hexagon whose centroid is outside the radius was counted")
        self.assertEqual(F.people_near(44.80, 20.45, 1.5, c), 5000)

    def test_the_published_layer_answers_for_a_real_station(self):
        p = F.PUBLIC / "context-population.json"
        if not p.exists():
            self.skipTest("no population layer on this machine")
        d = json.loads(p.read_text(encoding="utf-8"))
        total = sum(h[2] for h in d["hexes"])
        self.assertEqual(F.people_near(44.8186, 20.4573, 200.0, d), total,
                         "a radius covering the whole window did not return the whole population")
        near = F.people_near(44.8186, 20.4573, 1.0, d)
        self.assertGreater(near, 0)
        self.assertLess(near, total)


class Register(unittest.TestCase):
    def test_every_layer_the_register_declares_can_be_looked_up(self):
        if not F.REGISTER.exists():
            self.skipTest("no static-layer register on this machine")
        reg = json.loads(F.REGISTER.read_text(encoding="utf-8"))
        for L in reg["layers"]:
            self.assertIn("id", L, "a layer in the register has no id, so nothing can ask for it")
            got = F.layer(L["id"])
            self.assertEqual(got["id"], L["id"])
            for key in ("file", "sid", "sha256", "must_be_named"):
                self.assertIn(key, got, f"{L['id']} does not record its {key}")

    def test_every_name_this_tool_asks_for_is_a_name_the_register_answers_to(self):
        """The defect this file was written for: both entry points call layer() on their first line,
        and it raised KeyError for every lookup from the day the register was rewritten - so the tool
        that builds the population layer could not start, while the layer it had built earlier sat on
        disk looking fine."""
        if not F.REGISTER.exists():
            self.skipTest("no static-layer register on this machine")
        src = (ROOT / "tools" / "fetch_static.py").read_text(encoding="utf-8")
        asked = set(re.findall(r'layer\("([^"]+)"\)', src))
        self.assertTrue(asked, "this test no longer knows what the tool asks for")
        for lid in asked:
            got = F.layer(lid)          # raises with a readable message if the register lost it
            self.assertTrue(got.get("file"))

    def test_a_layer_can_be_found_by_the_other_names_it_carries(self):
        if not F.REGISTER.exists():
            self.skipTest("no static-layer register on this machine")
        reg = json.loads(F.REGISTER.read_text(encoding="utf-8"))
        L = reg["layers"][0]
        for key in ("id", "sid", "file"):
            if L.get(key):
                self.assertEqual(F.layer(L[key])["file"], L["file"], f"lookup by {key} failed")

    def test_an_unknown_layer_says_what_it_looked_for_and_what_exists(self):
        if not F.REGISTER.exists():
            self.skipTest("no static-layer register on this machine")
        with self.assertRaises(KeyError) as e:
            F.layer("a-layer-that-was-never-accepted")
        msg = str(e.exception)
        self.assertIn("a-layer-that-was-never-accepted", msg, "the error does not say what was asked for")
        self.assertIn("kontur-population", msg, "the error does not say what the register does hold")

    def test_the_status_report_names_the_source_of_every_context_file(self):
        """A context file whose source is unknown is a file this record cannot show."""
        st = F.status()
        for name, d in st.items():
            self.assertTrue(d.get("source"), f"{name} is on disk and does not say where it came from")
            self.assertGreater(d["entries"], 0, f"{name} carries nothing")


if __name__ == "__main__":
    unittest.main()
