#!/usr/bin/env python3
"""Structural checks on the built site, so its defects stop being found by eye.

Every assertion here corresponds to a defect that was actually shipped and then noticed by a person
looking at a screen: a frame that grew to 255 000 pixels because a viewport height was measured
inside an auto-sized iframe; a ribbon that stayed English on the English page because the language
switch iterated a hard-coded list of frames; a legend whose English half was missing; a link to a
file the build no longer copied. None of them broke a test, because there was no test that looked at
the artefact. This is that test. It reads only what the build produced.
"""
import json
import pathlib
import re
import unittest
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
INDEX = DOCS / "index.html"


def read(p):
    return p.read_text(encoding="utf-8", errors="replace")


class BuiltSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = read(INDEX)
        cls.frames = [f.split("?")[0] for f in re.findall(r'<iframe[^>]*src="([^"]+)"', cls.s)]

    def test_the_page_was_actually_built(self):
        self.assertTrue(INDEX.exists(), "docs/index.html is missing")
        self.assertGreater(len(self.s), 100_000, "the page is too small to be a complete build")
        self.assertTrue(self.s.lstrip().lower().startswith("<!doctype html>"))
        self.assertIn('lang="sr"', self.s[:400])

    def test_no_placeholder_survived_into_the_artefact(self):
        """C-021. The first version of this searched for the markers as bare substrings, which is
        wrong on a page that is half Serbian: `TODO` is inside `METODOLOGIJA`, and the test failed on
        a correction entry that merely quoted a filename category. A test that cries wolf on correct
        content is worse than no test, because the next real failure is read as noise. Word-shaped
        markers are matched as words; the bracket-shaped ones stay literal, since they cannot occur
        inside a word."""
        for marker in ("{{", ">None<", "[object Object]"):
            self.assertFalse(marker in self.s, f"the built page carries {marker!r}")
        for word in ("TODO", "FIXME", "undefined", "NaN"):
            self.assertNotRegex(self.s, r"\b%s\b" % word, f"the built page carries {word!r}")

    def test_every_serbian_span_has_an_english_twin(self):
        """The pairing is by exact class string: sr-only and en-only always ship together, in the same
        variant. A missing twin is how a legend ends up half-translated."""
        classes = Counter(re.findall(r'class="([^"]*)"', self.s))
        for cls, n in classes.items():
            if "sr-only" in cls:
                twin = cls.replace("sr-only", "en-only")
                self.assertEqual(classes.get(twin, 0), n,
                                 f'class "{cls}" appears {n} times but "{twin}" appears {classes.get(twin, 0)}')

    def test_the_four_language_door_has_all_four_answers(self):
        counts = {lang: len(re.findall(r'class="[^"]*\bw-%s\b' % lang, self.s)) for lang in ("sr", "en", "zh", "de")}
        self.assertGreater(counts["sr"], 0, "the front door has no Serbian")
        self.assertEqual(len(set(counts.values())), 1,
                         "the four languages of the front door are not in step: " + json.dumps(counts))

    def test_no_element_id_is_used_twice(self):
        dupes = [i for i, n in Counter(re.findall(r'\sid="([^"]+)"', self.s)).items() if n > 1]
        self.assertEqual(dupes, [], "duplicate ids: " + ", ".join(dupes))

    def test_every_frame_and_local_link_points_at_a_file_that_exists(self):
        targets = set(self.frames)
        for h in re.findall(r'href="([^"]+)"', self.s):
            if h.startswith(("http", "#", "mailto:", "data:")) or "'+" in h:
                continue
            targets.add(h.split("?")[0])
        for t in sorted(targets):
            self.assertTrue((DOCS / t).exists(), f"the page links to docs/{t}, which the build did not produce")

    def test_the_page_fetches_nothing_over_plain_http(self):
        """Source URLs the registry records may be http - that is the publisher's choice and part of
        the evidence. What the PAGE loads may not be."""
        loaded = re.findall(r'<(?:script|link|img|iframe)[^>]*(?:src|href)="(http://[^"]+)"', self.s)
        self.assertEqual(loaded, [], "the page loads a resource over plain http")

    def test_no_frame_reports_a_height_it_measured_from_its_own_scroll_height(self):
        """The runaway: a frame sized to its scrollHeight can never report a smaller number, because
        the height it was just given IS its scroll height. One frame reached 255 523 px on a phone.
        The height a frame reports must be measured from the bottom of its own content, never from
        scrollHeight - so the measurement is of the content, not of the box the content was put in."""
        for f in self.frames:
            p = DOCS / f
            if not p.exists():
                continue
            body = read(p)
            if "beops" not in body or "postMessage" not in body:
                continue
            self.assertNotRegex(body, r"(documentElement|body)\.scrollHeight",
                                f"docs/{f} measures its height from scrollHeight, which cannot shrink")

    def test_no_element_inside_an_embedded_frame_is_sized_from_the_viewport_height(self):
        """The parent measures the frame from its content, so a child asking for a share of the
        viewport is asking for a share of itself. `body.embedded .map .cv{min-height:52vh}` settled at
        H = 1873 + 0.52H = 3900 px on a 412 px phone and left a 2000 px empty box under the pulse map.
        The frame's OWN box may fill its viewport - that is the parent's decision to honour - but no
        descendant of it may, because a descendant is what the measurement reads."""
        for f in self.frames:
            p = DOCS / f
            if not p.exists():
                continue
            for rule in re.findall(r"([^{}]*embedded[^{}]*)\{([^}]*)\}", read(p)):
                selector, body = rule[0].strip(), rule[1]
                descendant = re.search(r"embedded[^,{]*\s+\S", selector)
                if descendant and re.search(r"\d\s*d?vh\b", body):
                    self.fail(f"docs/{f}: `{selector}` sizes a descendant of an embedded frame in vh: {body.strip()[:90]}")

    def test_a_canvas_is_resized_when_either_dimension_changes(self):
        """The pulse map compared only its width against the backing store, so when its box grew taller
        the bitmap stayed 589 px while the projection drew into 2027 px: everything below the old
        height fell outside the bitmap and the map read as empty."""
        for f in self.frames:
            p = DOCS / f
            if not p.exists():
                continue
            body = read(p)
            # A page that re-sizes its canvas on every draw needs no guard. One that guards the resize
            # must guard on both dimensions, or a taller box keeps a shorter bitmap.
            if re.search(r"\.width\s*!==\s*Math\.round\(", body):
                self.assertRegex(body, r"\.height\s*!==\s*Math\.round\(",
                                 f"docs/{f} guards its canvas resize on width alone")

    def test_every_frame_reports_its_own_height_and_takes_the_language(self):
        for f in self.frames:
            p = DOCS / f
            if not p.exists():
                continue
            body = read(p)
            self.assertIn("beops", body, f"docs/{f} does not speak the frame protocol")
            self.assertIn("postMessage", body, f"docs/{f} never reports its height")
            self.assertIn("addEventListener('message'", body.replace('"', "'"),
                          f"docs/{f} never listens for the language switch")

    def test_the_language_switch_reaches_every_frame_not_a_list_of_them(self):
        """The ribbon stayed Serbian on the English page because setLang messaged two named frames."""
        self.assertRegex(self.s, r"querySelectorAll\(\s*'iframe'\s*\)|getElementsByTagName\(\s*'iframe'\s*\)",
                         "the language switch does not iterate all iframes")

    def test_an_embedded_frame_carries_both_languages_itself(self):
        for f in self.frames:
            p = DOCS / f
            if p.exists():
                body = read(p)
                self.assertIn("sr-only", body, f"docs/{f} has no Serbian half")
                self.assertIn("en-only", body, f"docs/{f} has no English half")


if __name__ == "__main__":
    unittest.main(verbosity=2)
