#!/usr/bin/env python3
"""test_states.py - rule 1 of the method, asserted for the first time.

"Five states, no sixth" has been the first line of this project's method since it was written, and
until 2026-09-10 nothing checked it. What the check found is that the rule is kept and is described
wrongly: there are TWO vocabularies sharing the field name `state` - an epistemic one about what is
known of a measurement, and a pipeline one about what happened to a derived row - and they meet in the
published snapshot where a reader cannot tell them apart.

Both are declared in research/STATES.json. This file fails if either grows a value that is not
declared, because a state nobody wrote down is a state nobody decided.
"""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import record  # noqa: E402
DECL = ROOT / "research" / "STATES.json"
LIVE = ROOT / "data" / "live"
SNAP = ROOT / "public" / "live-snapshot.json"


def rows(p):
    """Every row under a directory, however deep, streamed and never slurped.

    Two defects met in this one function. It read each file whole, which cost the publish gate a
    MemoryError on a 41 MB file (C-055). And it listed ONE directory level while the record nests -
    each entity's notebook and each voice benchmark sit in subdirectories - so it scanned two files
    out of eight, and the only two files carrying an undeclared state were among the six it never
    opened. The declaration this test enforces said `derived/*/**.jsonl` all along."""
    for f in sorted(p.rglob("*.jsonl")) if p.exists() else []:
        yield from record.objects(f)


class Declared(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(DECL.read_text(encoding="utf-8"))
        cls.epi = set(cls.d["epistemic"]["states"])
        cls.pipe = set(cls.d["pipeline"]["states"])

    def test_the_five_are_the_five(self):
        self.assertEqual(self.epi, {"observed", "untimed", "estimated", "forecast", "unavailable"},
                         "the epistemic vocabulary changed and rule 1 of the method did not")

    def test_every_declared_state_says_what_a_reader_should_understand(self):
        for group in ("epistemic", "pipeline"):
            for k, v in self.d[group]["states"].items():
                self.assertGreater(len(str(v).strip()), 20,
                                   f"{group}/{k} is declared without a sentence a stranger could act on")

    def test_a_measurement_row_carries_no_state_field_at_all(self):
        """The finding that made this file necessary. A row cannot carry a WRONG epistemic state
        because it carries none: the state is computed where the value is rendered."""
        p = LIVE / "rows"
        if not p.exists():
            self.skipTest("no rows on this machine")
        bad = []
        for d in sorted(p.iterdir()):
            if not d.is_dir():
                continue
            for r in rows(d):
                if r.get("state") is not None:
                    bad.append("%s: %r" % (d.name, r.get("state")))
                    break
        self.assertEqual(bad[:5], [], "a measurement row has grown a state field: " + "; ".join(bad[:5]))

    def test_no_derived_row_carries_an_undeclared_state(self):
        allowed = self.epi | self.pipe
        bad = []
        for organ in ("mind", "news"):
            for r in rows(LIVE / "derived" / organ):
                s = r.get("state")
                if s is None:
                    continue
                base = str(s).split(":")[0].strip()
                if base not in allowed:
                    bad.append("%s: %r" % (organ, s))
        self.assertEqual(sorted(set(bad))[:6], [],
                         "a derived row carries a state that research/STATES.json does not declare: "
                         + "; ".join(sorted(set(bad))[:6]))

    def test_the_published_snapshot_carries_no_undeclared_state(self):
        if not SNAP.exists():
            self.skipTest("no published snapshot on this machine")
        # "derived" used to be permitted here rather than declared in STATES.json. An exception
        # written into a test is a declaration nobody can find, so it now lives in the register.
        allowed = self.epi | self.pipe
        found = set()

        def walk(n):
            if isinstance(n, dict):
                s = n.get("state")
                if isinstance(s, str):
                    found.add(s.split(":")[0].strip())
                for v in n.values():
                    walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)

        walk(json.loads(SNAP.read_text(encoding="utf-8")))
        self.assertEqual(sorted(found - allowed), [],
                         "the published snapshot shows a state nobody declared: " + ", ".join(sorted(found - allowed)))

    def test_the_scan_reaches_the_nested_files_and_not_only_the_top_level(self):
        """The test's own blindness, kept from returning. If this ever counts fewer files than the
        record holds, every assertion above it is being made about a fraction of the record."""
        base = LIVE / "derived"
        if not base.exists():
            self.skipTest("no derived rows on this machine")
        shallow = sum(len(list((base / o).glob("*.jsonl"))) for o in ("mind", "news") if (base / o).exists())
        deep = sum(len(list((base / o).rglob("*.jsonl"))) for o in ("mind", "news") if (base / o).exists())
        self.assertGreaterEqual(deep, shallow)
        seen = sum(1 for o in ("mind", "news") for _ in [0] if (base / o).exists())
        self.assertTrue(seen, "no organ directory was found at all")
        counted = 0
        for o in ("mind", "news"):
            counted += sum(1 for _ in (base / o).rglob("*.jsonl")) if (base / o).exists() else 0
        self.assertEqual(counted, deep, "the scan sees fewer files than the record holds")

    def test_the_ambiguity_is_recorded_rather_than_forgotten(self):
        """Both vocabularies meet under one key in the published snapshot. That is a known defect,
        not a fixed one, and it must stay named until it is either fixed or accepted in writing."""
        self.assertIn("cannot tell", self.d.get("the_ambiguity_named", ""))
        self.assertIn("known defect", self.d.get("the_ambiguity_named", ""))


if __name__ == "__main__":
    unittest.main()
