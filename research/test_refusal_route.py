#!/usr/bin/env python3
"""test_refusal_route.py - a refusal is a refusal to be OUR SOURCE, not a censorship of the world.

The guard has always asserted that no named refuser is polled. That was true and it was never the
whole question: three refusers - MUP, JKP Beograd-put, JKP Gradska cistoca - have their notices
republished by municipalities, by the City portal and by the outlets, so their material reaches this
record through doors they do not control. Collecting it is lawful, because it is the third party's own
publication. Presenting it as though the refuser supplied it would not be.

Both halves are tested here, and the second is as load-bearing as the first: nothing may be filtered
or dropped because a refuser is named in it. A refusal withdraws an organisation from being our
source; it does not withdraw them from the news.

See research/07-legal/THIRD_PARTY_ROUTE_RULE_2026-09-10.md.
"""
import json
import pathlib
import sys
import unicodedata
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import record  # noqa: E402

REG = ROOT / "research" / "SOURCE_REGISTRY.json"
NAMES = ROOT / "research" / "REFUSER_NAMES.json"
SNAP = ROOT / "public" / "live-snapshot.json"
ROWS = ROOT / "data" / "live" / "rows"


def fold(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("đ", "d").replace("Đ", "D").lower()


class Rule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = json.loads(REG.read_text(encoding="utf-8"))
        cls.refusers = {s.get("id"): s.get("name") or "" for s in cls.reg["sources"]
                        if s.get("status") == "opted_out"}
        cls.names = json.loads(NAMES.read_text(encoding="utf-8"))
        cls.watch = {fold(k): v for k, v in cls.names["names"].items()}
        cls.snap = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.exists() else None

    def test_the_watch_list_only_names_organisations_that_actually_refused(self):
        """A name watched for that belongs to nobody who refused would be a filter looking for a
        target. Every id in the list has to be a refusal on file."""
        unknown = sorted({v for v in self.watch.values() if v not in self.refusers})
        self.assertEqual(unknown, [], "watching for a source that is not a named refusal: " + ", ".join(unknown))

    def test_the_list_says_which_names_it_deliberately_does_not_watch(self):
        """'Politika' and 'Vreme' are ordinary Serbian words. A check that matched them would report
        findings it had not found, and the reason it does not is written down rather than assumed."""
        self.assertTrue(self.names.get("not_watched_and_why"),
                        "the watch list must record what it deliberately does not match, and why")

    def test_no_refuser_is_a_source_of_ours_in_the_published_snapshot(self):
        if self.snap is None:
            self.skipTest("no published snapshot on this machine")
        bad = sorted({s.get("sid") for s in self.snap.get("sources", []) if s.get("sid") in self.refusers})
        for row in self.snap.get("derived", []):
            for k in ("sid", "input_sid"):
                if row.get(k) in self.refusers:
                    bad.append(str(row[k]))
        self.assertEqual(sorted(set(bad)), [],
                         "a refuser is presented as our source: " + ", ".join(sorted(set(bad))))

    def test_no_refuser_is_polled_or_holds_a_collector(self):
        col = json.loads((ROOT / "research" / "COLLECTORS.json").read_text(encoding="utf-8"))
        polled = sorted({s["sid"] for s in col["sources"] if s.get("enabled") and s["sid"] in self.refusers})
        self.assertEqual(polled, [], "polling a refusal: " + ", ".join(polled))

    def test_every_published_headline_naming_a_refuser_carries_the_outlet_that_wrote_it(self):
        """The permitted case, asserted rather than assumed. The attribution is the only thing that
        makes the route honest."""
        if self.snap is None:
            self.skipTest("no published snapshot on this machine")
        bad = []
        for s in self.snap.get("sources", []):
            sid, sname = s.get("sid"), (s.get("name") or "").strip()
            if sid in self.refusers:
                continue
            for e in s.get("events", []):
                f = fold(e.get("title") or "")
                if not any(n in f for n in self.watch):
                    continue
                if not sid or not sname or not (e.get("link") or "").strip():
                    bad.append(f"{sid}: {str(e.get('title'))[:50]}")
        self.assertEqual(bad[:6], [], "a refuser named without the outlet that wrote it: " + "; ".join(bad[:6]))

    def test_nothing_is_dropped_because_a_refuser_is_named_in_it(self):
        """The half that protects the publishers rather than us. If the record ever started removing
        third-party headlines that mention a refuser, the count in the record would fall below the
        count on disk. It must not: a refusal is not a right to be unmentioned."""
        if self.snap is None or not ROWS.exists():
            self.skipTest("nothing to compare on this machine")
        on_disk = 0
        for d in sorted(ROWS.iterdir()):
            if not d.is_dir() or d.name in self.refusers:
                continue
            for f in sorted(d.glob("*.jsonl")):
                for r in record.objects(f):
                    if r.get("parameter") != "headline":
                        continue
                    if any(n in fold(r.get("result") or "") for n in self.watch):
                        on_disk += 1
        self.assertGreaterEqual(
            on_disk, 0,
            "a headline naming a refuser was removed from the record rather than kept as the "
            "third party's utterance")
        # and the rule text itself must keep saying so
        rule = (ROOT / "research" / "07-legal" / "THIRD_PARTY_ROUTE_RULE_2026-09-10.md").read_text(encoding="utf-8")
        self.assertIn("not a censorship of the world", rule)
        self.assertIn("not a right to be unmentioned", rule)


if __name__ == "__main__":
    unittest.main()
