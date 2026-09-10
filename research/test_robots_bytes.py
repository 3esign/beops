#!/usr/bin/env python3
"""test_robots_bytes.py - the permission claim, re-derived from the bytes rather than from the note.

The guard asserts every run that no named refusal is polled. It reads that from SOURCE_REGISTRY.json
- from what we WROTE DOWN when we checked. Nothing re-derives it from what the publisher actually
served, so a verdict recorded on 6 September was, until this file existed, believed on 10 September
because it was written down, not because it was still true. That is the record's own distinction
between permission as memory and permission as bytes, applied to the permission layer itself.

It also locks the matcher. `urllib.robotparser` implements no wildcard at all and returns the FIRST
matching rule; RFC 9309 says the LONGEST match wins and Allow wins a tie. legal_capture.py carries a
correct implementation for exactly that reason and stores the stricter of the two verdicts. These
tests hold that behaviour in place, because the day someone simplifies it back to the standard
library, every stored verdict silently becomes more permissive and nothing else would notice.
"""
import json
import pathlib
import sys
import unittest
import urllib.parse
import urllib.robotparser

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import legal_capture as lc  # noqa: E402

EV = ROOT / "research" / "evidence" / "legal"
COLLECTORS = ROOT / "research" / "COLLECTORS.json"
UA = "BeopsBot"


def polled():
    d = json.loads(COLLECTORS.read_text(encoding="utf-8"))
    return {s["sid"]: s for s in d["sources"] if s.get("enabled")}


def newest_robots(sid: str):
    d = EV / sid
    if not d.exists():
        return None
    for cap in sorted((p for p in d.iterdir() if p.is_dir()), reverse=True):
        f = cap / "robots.txt"
        if f.exists():
            return f.read_text(encoding="utf-8", errors="replace")
    return None


def path_of(src: dict) -> str:
    url = str(src.get("url") or "").replace("{from_iso}", "2026-01-01T00:00:00Z")
    pr = urllib.parse.urlparse(url)
    p = pr.path or "/"
    return p + ("?" + pr.query if pr.query else "")


class Matcher(unittest.TestCase):
    """What the standard library gets wrong, held as examples so it cannot be reintroduced."""

    def test_a_wildcard_rule_forbids(self):
        """urllib matches rules with startswith, so it reads this as no rule at all and says yes."""
        text = "User-agent: *\nDisallow: *.osm.pbf\n"
        ok, rule, _ = lc.rfc9309(text, UA, "/europe/serbia-latest.osm.pbf")
        self.assertFalse(ok)
        self.assertIn("osm.pbf", rule)
        p = urllib.robotparser.RobotFileParser()
        p.parse(text.splitlines())
        self.assertTrue(p.can_fetch(UA, "https://x/europe/serbia-latest.osm.pbf"))  # the blindness itself

    def test_a_dollar_anchors_the_end(self):
        text = "User-agent: *\nDisallow: /*.csv$\n"
        self.assertFalse(lc.rfc9309(text, UA, "/data/x.csv")[0])
        self.assertTrue(lc.rfc9309(text, UA, "/data/x.csv?page=2")[0])

    def test_the_longest_match_wins_not_the_first(self):
        """The transit.land shape named in legal_capture.py: urllib answers allowed because Allow
        comes first; the correct answer is disallowed because Disallow is more specific."""
        text = "User-agent: *\nAllow: /feeds\nDisallow: /feeds/\n"
        self.assertFalse(lc.rfc9309(text, UA, "/feeds/abc")[0])
        self.assertTrue(lc.rfc9309(text, UA, "/feeds")[0])

    def test_allow_wins_a_tie(self):
        text = "User-agent: *\nDisallow: /x\nAllow: /x\n"
        self.assertTrue(lc.rfc9309(text, UA, "/x")[0])

    def test_a_named_group_beats_the_star_group(self):
        text = "User-agent: *\nDisallow:\n\nUser-agent: beopsbot\nDisallow: /\n"
        self.assertFalse(lc.rfc9309(text, UA, "/anything")[0])


class Bytes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.polled = polled()
        cls.robots = {sid: newest_robots(sid) for sid in cls.polled}
        if not any(cls.robots.values()):
            raise unittest.SkipTest("no stored robots.txt on this machine")

    def test_every_polled_source_is_still_allowed_by_the_bytes_we_stored(self):
        """Not by the ledger line, not by the registry status: by re-reading what the host served."""
        forbidden = []
        for sid, src in sorted(self.polled.items()):
            text = self.robots.get(sid)
            if text is None:
                continue
            path = path_of(src)
            ok, rule, _ = lc.rfc9309(text, UA, path)
            if not ok:
                forbidden.append(f"{sid} {path} is forbidden by {rule}")
        self.assertEqual(forbidden, [], "a polled source is forbidden by its own robots.txt: " + "; ".join(forbidden))

    def test_no_polled_source_lacks_the_bytes_entirely(self):
        """A source with no stored robots.txt has no re-derivable permission, only a memory of one."""
        missing = [sid for sid, t in sorted(self.robots.items()) if t is None]
        self.assertEqual(missing, [], "polled with no stored robots.txt: " + ", ".join(missing))

    def test_where_the_two_parsers_disagree_the_record_is_told(self):
        """Today they agree on every collected path. This is the tripwire for the day they do not -
        which will happen the first time a collected URL gains a query string that a wildcard rule
        matches, and would otherwise be invisible."""
        disagreements = []
        for sid, src in sorted(self.polled.items()):
            text = self.robots.get(sid)
            if text is None:
                continue
            path = path_of(src)
            p = urllib.robotparser.RobotFileParser()
            p.parse(text.splitlines())
            py_ok = p.can_fetch(UA, "https://host" + path)
            std_ok = lc.rfc9309(text, UA, path)[0]
            if py_ok != std_ok:
                disagreements.append(f"{sid} {path}: urllib={py_ok} rfc9309={std_ok}")
        self.assertEqual(disagreements, [],
                         "the two robots parsers disagree about a path we collect, so the stored "
                         "verdict depends on which one wrote it: " + "; ".join(disagreements))


if __name__ == "__main__":
    unittest.main()
