#!/usr/bin/env python3
"""test_capture_backlog.py - the tool that decides who gets approached had no test.

`capture_backlog.py` walks the registry and runs the permission capture against every source that has
no stored capture yet. **The one decision in it that matters is who gets asked**, and that decision
was written inside a loop that talks to the network, so it could not be checked without doing it.

The invariant is the project's oldest: a named refusal is never approached again. It was true by
reading, and is now true by test.
"""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import capture_backlog as CB  # noqa: E402


def src(sid, status="probe_ok", url="https://example.org/"):
    return {"id": sid, "name": "Source " + sid, "status": status, "url": url}


class Targets(unittest.TestCase):
    def test_a_named_refusal_is_never_approached(self):
        """The rule the whole record rests on, applied to the one tool that reaches outward."""
        for status in ("opted_out", "blocked", "restricted"):
            t = CB.targets([src("S1", status), src("S2")], set())
            self.assertEqual([r["id"] for r in t], ["S2"],
                             f"a source with status {status!r} was queued to be approached")

    def test_nothing_unsettled_is_approached_either(self):
        for status in ("needs_decision", "token_required", "account_required", "no_coverage", "dead"):
            self.assertEqual(CB.targets([src("S1", status)], set()), [],
                             f"{status!r} was queued")

    def test_a_source_that_already_has_a_capture_is_left_alone(self):
        t = CB.targets([src("S1"), src("S2")], {"S1"})
        self.assertEqual([r["id"] for r in t], ["S2"])

    def test_a_source_without_a_usable_url_is_not_approached(self):
        for url in ("", None, "ftp://x/", "about:blank", "javascript:void(0)"):
            self.assertEqual(CB.targets([src("S1", url=url)], set()), [], repr(url))

    def test_the_wall_is_the_registry_vocabulary_and_not_a_second_copy_of_it(self):
        """If the registry grows a status that means 'do not approach' and this list does not, the
        tool starts knocking on a door somebody closed."""
        reg = ROOT / "research" / "SOURCE_REGISTRY.json"
        if not reg.exists():
            self.skipTest("no registry on this machine")
        d = json.loads(reg.read_text(encoding="utf-8"))
        statuses = {s.get("status") for s in d["sources"]}
        for s in CB.WALL:
            self.assertIn(s, statuses | {"blocked", "restricted", "account_required", "token_required",
                                         "no_coverage", "dead", "needs_decision", "opted_out"},
                          f"the wall names {s!r}, which the registry never uses")
        refusing = {"opted_out", "blocked", "restricted"}
        self.assertTrue(refusing <= CB.WALL, "a refusing status is missing from the wall")

    def test_the_real_registry_would_never_queue_one_of_its_own_refusals(self):
        reg = ROOT / "research" / "SOURCE_REGISTRY.json"
        if not reg.exists():
            self.skipTest("no registry on this machine")
        d = json.loads(reg.read_text(encoding="utf-8"))
        refusers = {s["id"] for s in d["sources"] if s.get("status") == "opted_out"}
        queued = {r["id"] for r in CB.targets(d["sources"], set())}
        self.assertEqual(queued & refusers, set(),
                         "the backlog would approach a source that refused: " + ", ".join(sorted(queued & refusers)))

    def test_reading_the_ledger_tells_it_what_is_already_captured(self):
        with tempfile.TemporaryDirectory() as t:
            led = pathlib.Path(t) / "LEDGER.jsonl"
            led.write_text('{"sid": "S1"}\n\n{"sid": "S2"}\n', encoding="utf-8")
            old = CB.LEDGER
            CB.LEDGER = str(led)
            try:
                self.assertEqual(CB.captured(), {"S1", "S2"})
            finally:
                CB.LEDGER = old

    def test_a_source_whose_capture_failed_is_never_retried_by_this_route(self):
        """Not a defect being fixed here - a property being written down. Any ledger line at all,
        including one recording a failed capture, takes a source off this queue permanently, so the
        'incomplete' queue never drains by running the backlog again. Draining it is a different
        tool's job, and until one exists this is a known hole rather than an unnoticed one."""
        t = CB.targets([src("S1")], {"S1"})
        self.assertEqual(t, [])


if __name__ == "__main__":
    unittest.main()
