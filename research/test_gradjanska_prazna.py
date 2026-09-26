#!/usr/bin/env python3
"""test_gradjanska_prazna.py - the bare-screen test for the citizen front door.

The plan for the citizen page (research/05-design/PLAN_GRADJANSKA_STRANA.md, section 3) says the
rule that separates it from a city portal: every sentence is a link to the measurement it came from,
and where there is no measurement the page says *I do not know* - never a zero, never a reassuring
noise. Nothing asserted that. The page was built against a full record, it looked right, and the
one screen nobody ever sees during development - the screen with an empty record - carried the
sentence "Beograd u realnom vremenu: stanice belezi redovan puls fizike grada" in the largest type
on the page, which is a claim that stations are recording, made exactly when none are.

So this test builds the page against an empty record and against a partial one, and reads what it
says. It is the cheapest test in the suite and it is the only one that looks at the page a broken
collector would produce.
"""
import json
import pathlib
import re
import tempfile
import unittest

import build_public_page as bpp

ROOT = pathlib.Path(__file__).resolve().parent.parent


def build_against(tmp, docs=None, public=None, research=None):
    """Build the citizen page with the record replaced by whatever is handed in."""
    base = pathlib.Path(tmp)
    for name, payload in (("docs", docs), ("public", public), ("research", research)):
        d = base / name
        d.mkdir(parents=True, exist_ok=True)
        for fname, obj in (payload or {}).items():
            (d / fname).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    saved = (bpp.DOCS, bpp.PUBLIC, bpp.RESEARCH)
    bpp.DOCS, bpp.PUBLIC, bpp.RESEARCH = base / "docs", base / "public", base / "research"
    try:
        return bpp.format_citizen_page()
    finally:
        bpp.DOCS, bpp.PUBLIC, bpp.RESEARCH = saved


def visible_text(html):
    body = html.split("<body", 1)[-1]
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", body, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", body))


class BareScreen(unittest.TestCase):
    """An empty record must produce a page that admits it."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.html = build_against(cls.tmp.name)
        cls.text = visible_text(cls.html)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_page_is_still_a_page(self):
        self.assertTrue(self.html.lstrip().lower().startswith("<!doctype html>"))
        self.assertIn("Beograd danas", self.html)

    def test_no_placeholder_is_left_unfilled(self):
        left = sorted(set(re.findall(r"__[A-Z0-9_]+__", self.html)))
        self.assertEqual(left, [], "the empty record left template slots unfilled: %s" % left)

    def test_the_largest_sentence_does_not_claim_a_measurement(self):
        """The hero sentence is the one a passer-by reads. With no readings it may only say so."""
        m = re.search(r'class="hero-headline"[^>]*>(.*?)</', self.html, re.S)
        self.assertIsNotNone(m, "the page has no hero sentence")
        hero = re.sub(r"\s+", " ", re.sub(r"<[^>]*>", "", m.group(1))).strip()
        for claim in ("belež", "belez", "merne stanice belež", "povoljni uslovi", "umereno opterećenje"):
            self.assertNotIn(claim, hero.lower(),
                             "with an empty record the hero sentence claims a measurement: %r" % hero)
        self.assertTrue(re.search(r"nema .*(?:očitavanj|merenj)|ne govori|ne zna", hero.lower()),
                        "with an empty record the hero sentence does not say so: %r" % hero)

    def test_empty_action_cards_preserve_distinct_evidence_limits_without_advice(self):
        cards = re.findall(r'<div class="action-card">(.*?)<div class="action-proof">', self.html, re.S)
        self.assertEqual(len(cards), 3, "missing an evidence category on the empty screen")
        by_name = {re.search(r'class="action-name">([^<]+)', card).group(1): card for card in cards}
        air = by_name['Vazduh na mernim mestima']
        roads = by_name['Kretanje kroz grad']
        activities = by_name['Boravak i aktivnosti napolju']
        self.assertIn('>NEMA PODATKA<', air)
        self.assertIn('0 vremenski određenih PM2.5 serija', air)
        self.assertIn('>NASLOVI<', roads)
        self.assertIn('0 naslova', roads)
        self.assertIn('Trajanje i trenutna prohodnost nisu potvrđeni', roads)
        self.assertIn('>BEZ PROCENE<', activities)
        self.assertIn('Zapisi nisu dovoljni za ličnu preporuku', activities)
        badges = re.findall(r'class="badge [^"]*">([^<]*)<', self.html)
        for badge in badges:
            self.assertNotIn(badge.strip(), ('DA', 'NE', 'OPREZ', 'PODACI'),
                             "an empty record must not produce advice or claim measured data")

    def test_absent_is_never_shown_as_zero(self):
        """Rule 3 of the instrument, on the citizen page: missing is not zero."""
        for bad in ("0 µg/m³", "0 stanica", "Stanica u mreži: 0", "0 sati"):
            self.assertNotIn(bad, self.text, "an absent quantity was rendered as zero: %r" % bad)
        self.assertIn("—", self.text, "nothing was marked absent on a page with an empty record")

    def test_the_empty_blocks_say_silence_is_a_record(self):
        self.assertIn("ćutanje izvora je zapis", self.text.lower())


class PartialRecord(unittest.TestCase):
    """Timed observations describe their stations; even three pollutants do not certify the city."""

    def stream(self, parameter, points, **extra):
        return {"station": "A", "parameter": parameter, "unit": "µg/m³", "points": points, **extra}

    def page(self, streams):
        snapshot = {"snapshot": {"as_of": "2026-09-26T12:00:00Z", "sources": [
            {"sid": "S146", "datastreams": streams}]}}
        with tempfile.TemporaryDirectory() as tmp:
            return build_against(tmp, docs={"city-overview.json": snapshot})

    def assert_no_citywide_or_personal_advice(self, html):
        text = visible_text(html)
        for unsupported in ('bez zabeleženih ekstrema', 'povoljni uslovi', 'vazduh čist'):
            self.assertNotIn(unsupported, text.lower())
        self.assertIn('Prosek ne opisuje svaku lokaciju u gradu', text)
        self.assertIn('Zapisi nisu dovoljni za ličnu preporuku', text)
        badges = re.findall(r'class="badge [^"]*">([^<]*)<', html)
        self.assertFalse(set(badges) & {'DA', 'NE', 'OPREZ'})

    def test_fresh_pm25_reports_latest_value_without_inventing_other_evidence(self):
        html = self.page([self.stream('PM2.5', [
            {'t': '2026-09-26T10:00:00Z', 'v': 9.0},
            {'t': '2026-09-26T11:00:00Z', 'v': 11.0}])])
        text = visible_text(html)
        self.assertIn('prosek 11.0 µg/m³ iz 1 serije', text)
        self.assertIn('>PODACI<', html)
        self.assert_no_citywide_or_personal_advice(html)

    def test_three_fresh_pollutants_still_cannot_certify_citywide_absence_of_extremes(self):
        html = self.page([self.stream(parameter, [{'t': '2026-09-26T11:00:00Z', 'v': value}])
                          for parameter, value in [('PM2.5', 11.0), ('PM10', 20.0), ('O3', 40.0)]])
        self.assertIn('prosek 11.0 µg/m³ iz 1 serije', visible_text(html))
        self.assert_no_citywide_or_personal_advice(html)

    def test_untimed_stale_future_and_forecast_numbers_are_not_current_measurements(self):
        streams = [
            self.stream('PM2.5', [{'v': 117.0}]),
            self.stream('PM2.5', [{'t': '2026-09-26T08:59:59Z', 'v': 117.0}]),
            self.stream('PM2.5', [{'t': '2026-09-26T13:00:00Z', 'v': 117.0}]),
            self.stream('PM2.5', [{'t': '2026-09-26T11:00:00Z', 'v': 117.0}], state='forecast'),
            self.stream('PM2.5', [{'t': '2026-09-26T11:00:00Z', 'v': 117.0}], unit='unknown'),
        ]
        for stream in streams:
            with self.subTest(stream=stream):
                html = self.page([stream])
                text = visible_text(html)
                self.assertIn('nema upotrebljivog PM2.5 merenja', text)
                self.assertNotIn('117', text)
                self.assertIn('>NEMA PODATKA<', html)
                self.assertNotIn('>PODACI<', html)
                self.assert_no_citywide_or_personal_advice(html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
