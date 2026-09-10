#!/usr/bin/env python3
"""test_attribution.py - Article 41 is the price of Article 43.

The Act permits free use of daily news (Art. 43(1)(4)) and of short extracts in a press review
(Art. 43(1)(2)) - and Art. 41 makes that permission conditional:

    "U slucajevima iskoriscavanja autorskog dela na osnovu odredaba ovog zakona o ogranicenju
     autorskog prava, moraju se navesti ime autora dela i izvor iz koga je delo preuzeto"

Every headline this record carries must therefore name where it came from. Until 2026-09-10 that was
true by habit: the code happened to keep the outlet and the link because they were useful. A condition
of lawfulness should not rest on a habit, so it is asserted here.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAP = ROOT / "public" / "live-snapshot.json"


def snapshot():
    if not SNAP.exists():
        return None
    try:
        return json.loads(SNAP.read_text(encoding="utf-8"))
    except ValueError:
        return None


class Attribution(unittest.TestCase):
    def setUp(self):
        self.snap = snapshot()
        if self.snap is None:
            self.skipTest("no published snapshot on this machine")

    def test_every_headline_names_its_source_and_carries_its_link(self):
        missing = []
        seen = 0
        for src in self.snap.get("sources", []):
            sid, name = src.get("sid"), (src.get("name") or "").strip()
            for e in src.get("events", []):
                if not (e.get("title") or "").strip():
                    continue
                seen += 1
                if not name:
                    missing.append(f"{sid}: source has no name")
                if not (e.get("link") or "").strip():
                    missing.append(f"{sid}: '{str(e.get('title'))[:40]}' has no link")
        self.assertEqual(missing[:8], [], "Art. 41 attribution missing: " + "; ".join(missing[:8]))

    def test_no_article_body_is_carried_with_a_headline(self):
        """Art. 43 permits the headline and the short extract, and stops there. A description field
        that slipped through would be the body of somebody's article sitting in our record."""
        long_ones = []
        for src in self.snap.get("sources", []):
            for e in src.get("events", []):
                for k, v in e.items():
                    if k in ("title", "link", "t", "rx"):
                        continue
                    if isinstance(v, str) and len(v) > 300:
                        long_ones.append(f"{src.get('sid')}.{k} ({len(v)} chars)")
        self.assertEqual(long_ones[:6], [], "a long text field travels with a headline: " + ", ".join(long_ones[:6]))

    def test_the_registry_states_a_reading_and_not_only_the_absence_of_an_objection(self):
        """A source justified only by 'nobody objected' has no case written down at all. Every news
        feed must name the article it is read to stand on - and that reading is marked as pending
        counsel wherever it appears, because a firmer footing asserted wrongly is worse than a modest
        one asserted rightly. This test checks that the reading is WRITTEN, never that it is right."""
        reg = json.loads((ROOT / "research" / "SOURCE_REGISTRY.json").read_text(encoding="utf-8"))
        srcs = reg["sources"] if isinstance(reg, dict) and "sources" in reg else reg
        feeds = [s for s in srcs if s.get("kind") in ("news_feed", "municipal_feed")]
        self.assertTrue(feeds, "no news feed in the registry")
        without = [s.get("id") for s in feeds
                   if "art. 43" not in json.dumps(s, ensure_ascii=False).lower()
                   and "art. 6" not in json.dumps(s, ensure_ascii=False).lower()
                   and "art. 49" not in json.dumps(s, ensure_ascii=False).lower()]
        self.assertEqual(without, [], "news sources with no legal reading stated: " + ", ".join(map(str, without)))
        # and nowhere is the reading allowed to read as settled law
        unmarked = [s.get("id") for s in feeds
                    if "legal_recomb_2026_09_10" in s
                    and not str(s["legal_recomb_2026_09_10"]).startswith("READING TO BE CONFIRMED")]
        self.assertEqual(unmarked, [], "a legal reading stated as if settled: " + ", ".join(map(str, unmarked)))


if __name__ == "__main__":
    unittest.main()
