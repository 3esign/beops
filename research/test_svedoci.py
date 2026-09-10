#!/usr/bin/env python3
"""test_svedoci.py - the two layers reach the page, and reach it with their caveats attached.

A layer that computes something true and publishes it without the sentence that says what it is NOT
is worse than one that publishes nothing: the reader takes the number and supplies their own meaning.
Both of these have a caveat that is load-bearing - an age is not the publisher's alone, and a gap is
not an error bar - so the caveats are asserted here rather than trusted to survive an edit.

It also holds the frame protocol lessons that cost four attempts each: `d` declared before it is read
(C-027), and the ask placed AFTER the handler is registered (C-038).
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
STUDY = ROOT / "research" / "05-design" / "studies" / "svedoci.html"
DOCS = ROOT / "docs"


class Study(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = STUDY.read_text(encoding="utf-8")

    def test_the_age_is_never_presented_as_the_publishers_own(self):
        self.assertIn("not the publisher's delay", self.s)
        self.assertIn("cannot separate them", self.s)
        self.assertIn("not a quality score", self.s)

    def test_the_gap_is_never_presented_as_an_error_bar(self):
        self.assertIn("not an error bar", self.s)
        self.assertIn("different places", self.s)
        self.assertRegex(self.s, r"cannot separate the two")

    def test_absence_is_drawn_rather_than_left_blank(self):
        """A source that publishes no measurement time gets a mark and a sentence, never an empty
        cell that reads as a fast source."""
        self.assertIn("no measurement time published at all", self.s)
        self.assertIn("absent", self.s)

    def test_our_own_polling_interval_is_drawn_to_scale(self):
        """The hatch is our ignorance, drawn. Where it is wider than the bar, none of the age can be
        attributed to the publisher, and the picture has to say so without a caption."""
        self.assertIn("our polling interval", self.s)
        self.assertIn("ours", self.s)

    def test_the_message_handler_declares_d_before_reading_it(self):
        """C-027: three frames once threw a ReferenceError on every message because the handler's
        parameter was `ev` and the body read `d`. The theme died, and so did the language, silently."""
        m = re.search(r"addEventListener\('message',function\(ev\)\{\s*\n\s*(var d=ev&&ev\.data;)", self.s)
        self.assertIsNotNone(m, "the message handler does not declare d from ev before using it")

    def test_the_ask_comes_after_the_handler_is_registered(self):
        """C-038: a message delivered before its handler exists is not late, it is lost."""
        h = self.s.find("addEventListener('message'")
        a = self.s.find("beopsAsk")
        self.assertGreater(h, -1, "no message handler")
        self.assertGreater(a, h, "the frame asks for the theme before its handler exists")

    def test_the_scrollbar_gutter_is_reserved_and_the_scrollbar_is_the_pages_own(self):
        """C-026 and C-030, the two that this frame would otherwise repeat."""
        self.assertIn("scrollbar-gutter:stable", self.s)
        self.assertIn("scrollbar-color:var(--ink30)", self.s)

    def test_it_carries_both_themes_and_paints_its_own_ground(self):
        self.assertIn('prefers-color-scheme: dark', self.s)
        self.assertIn(':root[data-theme="dark"]', self.s)
        self.assertRegex(self.s, r"body\{[^}]*background:var\(--field\)")


class Published(unittest.TestCase):
    def setUp(self):
        if not (DOCS / "index.html").exists():
            self.skipTest("no built site on this machine")

    def test_the_frame_and_its_data_are_mirrored_into_the_public_directory(self):
        for f in ("svedoci.html", "latency.json", "agreement.json"):
            self.assertTrue((DOCS / f).exists(), f"{f} is not published, so the layer exists for nobody")

    def test_the_page_carries_the_frame_and_the_caveat_in_four_languages(self):
        idx = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertIn('src="svedoci.html', idx, "the page does not embed the frame")
        self.assertIn("not an error bar, because the sources stand in different places", idx)
        for cls in ("sr-only i18n", "en-only i18n", "zh-only", "de-only"):
            self.assertIn(cls, idx)


if __name__ == "__main__":
    unittest.main()
