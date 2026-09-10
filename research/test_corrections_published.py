"""Every correction the ledger numbers must reach the list the public sees.

The page tells the reader that the list of failures "is never deleted". That promise is about
removal, and it was kept - nothing was ever removed. What was not kept is the weaker promise the
sentence implies: that everything written down arrives there in the first place.

Three corrections did not. C-033, C-034 and C-035 share one heading, and the parser that builds the
public list matched a single id followed by an em dash, so the whole entry produced no row at all.
Nothing failed, nothing was logged, and the list was simply three corrections shorter than the ledger
(C-067).

That is the blind-check shape again, in the other direction: the reader cannot tell a list that holds
everything from a list that quietly holds less, because both look like a list.

So this module asks the question the parser cannot ask about itself: not "did you parse what you
matched", but "is every number the ledger uses present in what you produced".
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_site                                                   # noqa: E402

LEDGER = ROOT / "research" / "08-provenance" / "CORRECTIONS.md"

# C-044 records that these three were written down in the code they fixed and never carried into the
# ledger. They are a declared hole, not a parsing failure, and the declaration is checked below
# against the ledger itself rather than being taken on this file's word.
NEVER_WRITTEN = ("C-026", "C-027", "C-028")


class Published(unittest.TestCase):

    def setUp(self):
        self.entries = build_site.corrections()
        self.ids = [i for e in self.entries for i in e["ids"]]

    def test_the_parser_produced_something(self):
        self.assertGreater(len(self.entries), 50, "the corrections list came back nearly empty")

    def test_no_number_is_published_twice(self):
        dupes = sorted({i for i in self.ids if self.ids.count(i) > 1})
        self.assertEqual(dupes, [], "the same correction is published under two rows: %s" % dupes)

    def test_every_number_the_ledger_uses_is_published_or_declared_missing(self):
        """The check that would have caught C-067 on the day it happened."""
        highest = max(int(i[2:]) for i in self.ids)
        absent = ["C-%03d" % n for n in range(1, highest + 1)
                  if "C-%03d" % n not in self.ids and "C-%03d" % n not in NEVER_WRITTEN]
        self.assertEqual(absent, [], "numbered in the ledger, missing from the public list: %s" % absent)

    def test_the_declared_hole_is_declared_in_the_ledger_and_not_only_here(self):
        """A test file may not invent an exception. Each number excused above has to be named in the
        ledger's own text, or the excuse is this file's opinion rather than the record's."""
        txt = LEDGER.read_text(encoding="utf-8", errors="replace")
        for cid in NEVER_WRITTEN:
            self.assertIn(cid, txt, "%s is excused here but appears nowhere in the ledger" % cid)

    def test_a_shared_heading_publishes_all_of_its_numbers(self):
        shared = [e for e in self.entries if len(e["ids"]) > 1]
        self.assertTrue(shared, "no combined heading found - C-033/034/035 should be one")
        for e in shared:
            self.assertEqual(e["ids"], re.findall(r"C-\d+", e["id"]))
            self.assertTrue(e["title"], "a combined entry lost its title")

    def test_every_row_carries_a_title(self):
        for e in self.entries:
            self.assertTrue(e["title"].strip(), "%s published with no title" % e["id"])


if __name__ == "__main__":
    unittest.main()
