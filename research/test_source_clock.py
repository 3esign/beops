#!/usr/bin/env python3
"""test_source_clock.py - a source may have a wrong clock. It may not have one quietly.

S146 publishes hourly means whose timestamps are labelled UTC and are Belgrade local time. That was
found by reading a row, written into COLLECTORS.json as a source_clock_note, and handled: the label
is kept exactly as served and our ESTIMATE of the true UTC travels beside it, marked estimated.

The handling was correct and the discovery was luck. Nothing in this project asserted that a source
delivering values which arrive BEFORE their own measurement window has closed must be declared, so a
second source with the same defect would have been silently wrong in the same way. This file is that
assertion, written as a property of any source rather than as a fact about SEPA:

  1. a public point cannot arrive before the hour it describes has ended. Where a source does that
     materially, it must carry a written source_clock_note;
  2. a note that names an offset must actually produce a corrected time on public points, so that a
     note cannot be decorative;
  3. the corrected time must be an estimate and must say so - it is our reading of somebody else's
     clock, never their statement.
"""
import json
import pathlib
import sys
import unittest
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SNAPSHOT = ROOT / "public" / "live-snapshot.json"
COLLECTORS = ROOT / "research" / "COLLECTORS.json"

MIN_ROWS = 5          # below this it is not a pattern
MIN_SHARE = 0.01      # 1 % of a source's timed rows arriving early is not a rounding artefact


def _p(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def sources():
    d = json.loads(COLLECTORS.read_text(encoding="utf-8"))
    return {s["sid"]: s for s in d["sources"]}


def scan():
    """(sid) -> {'timed': n, 'early': n, 'corrected': n, 'estimated': n} from the public 24 h cut."""
    out = {}
    if not SNAPSHOT.exists():
        return out
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    for source in snapshot.get("sources", []):
        sid = source.get("sid")
        if not sid:
            continue
        c = {"timed": 0, "early": 0, "corrected": 0, "estimated": 0}
        for stream in source.get("datastreams", []):
            for point in stream.get("points", []):
                if point.get("tu"):
                    continue
                pe, rx = _p(point.get("t")), _p(point.get("rx"))
                if not pe or not rx:
                    continue
                c["timed"] += 1
                if rx < pe:
                    c["early"] += 1
                if point.get("tc") or point.get("tc0") or point.get("rtc"):
                    c["corrected"] += 1
                    if "ESTIMATE" in str(point.get("clock_note") or ""):
                        c["estimated"] += 1
        if c["timed"]:
            out[sid] = c
    return out


class SourceClock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scan = scan()
        cls.src = sources()
        if not cls.scan:
            raise unittest.SkipTest("no public snapshot on this machine")

    def test_a_source_that_delivers_rows_before_their_hour_has_closed_is_declared(self):
        """The general form of the SEPA defect. A source is allowed a wrong clock; it is not allowed
        an undeclared one, because an undeclared wrong clock is indistinguishable from a right one."""
        undeclared = []
        for sid, c in self.scan.items():
            share = c["early"] / c["timed"]
            if c["early"] < MIN_ROWS or share < MIN_SHARE:
                continue
            note = (self.src.get(sid) or {}).get("source_clock_note") or {}
            if not str(note.get("text") or "").strip():
                undeclared.append("%s: %d of %d rows (%.0f%%) arrived before their own hour closed, "
                                  "and COLLECTORS.json says nothing about its clock" % (sid, c["early"], c["timed"], 100 * share))
        self.assertEqual(undeclared, [], "undeclared source clock: " + "; ".join(undeclared))

    def test_a_note_that_names_an_offset_actually_corrects_the_rows(self):
        """A note is a claim that something is being done about it. This is the doing."""
        empty = []
        for sid, s in self.src.items():
            note = s.get("source_clock_note") or {}
            if not note.get("offset_seconds"):
                continue
            c = self.scan.get(sid)
            if c and c["timed"] and not c["corrected"]:
                empty.append("%s: note claims an offset of %s s and no row carries a corrected time"
                             % (sid, note["offset_seconds"]))
        self.assertEqual(empty, [], "a decorative clock note: " + "; ".join(empty))

    def test_a_corrected_time_is_marked_as_our_estimate(self):
        """It is our reading of somebody else's clock. It may never travel as their statement."""
        bad = [f"{sid}: {c['corrected']} corrected rows, {c['estimated']} marked estimated"
               for sid, c in self.scan.items() if c["corrected"] and c["estimated"] != c["corrected"]]
        self.assertEqual(bad, [], "a corrected time not marked as an estimate: " + "; ".join(bad))

    def test_the_declared_source_is_still_the_one_we_know_about(self):
        """Not a rule - a tripwire. If a second source ever earns a clock note, this fails and asks
        for the pre-paper's clock paragraph to be re-read rather than silently generalised."""
        declared = sorted(sid for sid, s in self.src.items() if (s.get("source_clock_note") or {}).get("offset_seconds"))
        self.assertEqual(declared, ["S146"],
                         "the set of sources with a corrected clock changed: " + ", ".join(declared))


if __name__ == "__main__":
    unittest.main()
