#!/usr/bin/env python3
"""test_static_layers.py - a layer that legitimately never changes must not be silent about itself.

Two of this record's layers are not streams: a basemap and a population grid, each a dated RELEASE of
somebody else's dataset. The stability review listed them as having no staleness rule and nothing was
done, because the obvious rule - a maximum age - is the wrong rule: the Sava does not move, and a 2022
population grid is not stale at 34 hours. An age limit would have reported a fault every single day
and meant nothing on the day something actually changed.

What can go wrong is different, and the load-bearing one is attribution. context-population.json is
CC BY 4.0 and carries its attribution inside the file. If a refetch drops it, or a page shows the
layer without naming it, this record is publishing somebody's dataset unattributed - Article 41 for
data rather than for headlines, and the same defect the news layer had until 2026-09-10 made it a test.
"""
import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "research" / "STATIC_LAYERS.json"
DOCS = ROOT / "docs"


class Register(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(REG.read_text(encoding="utf-8"))
        cls.layers = cls.d.get("layers", [])

    def test_the_register_says_why_each_layer_has_no_expiry(self):
        """A layer with no age limit needs a written reason, or 'no rule' and 'no thought' look the
        same to the next reader."""
        for L in self.layers:
            self.assertTrue(str(L.get("why_no_expiry") or "").strip(),
                            f"{L.get('file')} has no expiry and no reason given for that")
            self.assertTrue(L.get("review_every_days"),
                            f"{L.get('file')} has no date by which somebody should look for a newer release")

    def test_each_layer_is_present_and_is_the_file_that_was_accepted(self):
        for L in self.layers:
            p = ROOT / L["file"]
            self.assertTrue(p.exists(), f"{L['file']} is in the register and not on disk")
            if L.get("sha256"):
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), L["sha256"],
                                 f"{L['file']} changed since it was accepted; re-accept it deliberately "
                                 "rather than letting the register drift to match")

    def test_each_layer_still_carries_its_source_and_attribution(self):
        """These are the terms we may show it under, and they live inside the file."""
        for L in self.layers:
            doc = json.loads((ROOT / L["file"]).read_text(encoding="utf-8"))
            for k in L.get("must_carry") or []:
                self.assertTrue(str(doc.get(k) or "").strip(),
                                f"{L['file']} has lost its {k}")

    def test_a_cc_by_layer_is_named_on_every_page_that_shows_it(self):
        """The file carrying the attribution is not the same as the page displaying it. Measured
        2026-09-10: Kontur and CC BY appear on the index and the monologue, Natural Earth on the data
        view, and nowhere that does not use them - correct, and by habit until this test."""
        if not DOCS.exists():
            self.skipTest("no built site on this machine")
        bad = []
        for L in self.layers:
            name = pathlib.Path(L["file"]).name
            # The register NAMES what must appear. The first version of this test sliced the
            # attribution string at its first full stop and then demanded that exact phrase, which
            # asked the page for "Made with Natural Earth" where the page says "Natural Earth 1:10
            # mil." - a check on wording rather than on credit, and it failed against pages that were
            # correctly attributed.
            for page in sorted(DOCS.glob("*.html")):
                body = page.read_text(encoding="utf-8", errors="replace")
                if name not in body:
                    continue
                for key in L.get("must_be_named") or []:
                    if key not in body:
                        bad.append(f"{page.name} shows {name} without naming {key}")
        self.assertEqual(bad, [], "; ".join(bad))

    def test_the_register_names_the_credit_rather_than_a_form_of_words(self):
        """A licence requires the credit. Demanding a phrase would fail a page that attributes
        correctly in its own sentence, which is what the first version of this check did."""
        for L in self.layers:
            self.assertTrue(L.get("must_be_named"),
                            f"{L.get('file')} does not say who must be named where it is shown")

    def test_the_register_says_what_it_is_for(self):
        self.assertIn("never how old it is", self.d.get("what_this_is", ""))
        self.assertIn("indistinguishable from neglect", self.d.get("what_this_is", ""))


if __name__ == "__main__":
    unittest.main()
