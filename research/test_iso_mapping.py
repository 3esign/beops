#!/usr/bin/env python3
"""The ISO 37120 mapping is a claim about our own coverage, so it is checked like one.

Nothing here validates the standard - we do not have its text and do not claim conformity. What is
checked is that the mapping is complete, that every source it names is a source we actually poll, and
that the counts in its `finding` are the counts of its own rows rather than a number someone typed.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAP = json.loads((ROOT / "research" / "ISO37120_MAPPING.json").read_text(encoding="utf-8"))
COLL = json.loads((ROOT / "research" / "COLLECTORS.json").read_text(encoding="utf-8"))
POLLED = {s["sid"] for s in COLL["sources"]}


class IsoMappingTests(unittest.TestCase):
    def test_all_nineteen_themes_are_present_once(self):
        names = [t["theme"] for t in MAP["themes"]]
        self.assertEqual(len(names), 19)
        self.assertEqual(len(set(names)), 19)
        self.assertEqual(MAP["standard"]["themes"], 19)

    def test_every_verdict_is_declared(self):
        for t in MAP["themes"]:
            self.assertIn(t["verdict"], MAP["verdicts"], t["theme"])

    def test_every_named_source_is_one_we_actually_poll(self):
        for t in MAP["themes"]:
            for sid in t["sids"]:
                self.assertIn(sid, POLLED, f"{t['theme']} names {sid}, which is not in COLLECTORS.json")

    def test_every_theme_carries_a_reason(self):
        for t in MAP["themes"]:
            self.assertGreater(len(t["note"].strip()), 40, t["theme"] + " has no reason")

    def test_a_theme_with_sources_is_not_called_empty(self):
        for t in MAP["themes"]:
            if t["verdict"] in ("indicator_reachable", "adjacent") and t["theme"] not in ("Population and social conditions",):
                self.assertTrue(t["sids"], t["theme"] + " claims coverage with no source behind it")
            if t["verdict"] in ("administrative_only", "out_of_scope_by_design"):
                self.assertEqual(t["sids"], [], t["theme"] + " claims no coverage while naming sources")

    def test_the_finding_counts_its_own_rows(self):
        f = MAP["finding"]
        counted = {}
        for t in MAP["themes"]:
            counted[t["verdict"]] = counted.get(t["verdict"], 0) + 1
        self.assertEqual(f["themes_total"], len(MAP["themes"]))
        for verdict in MAP["verdicts"]:
            self.assertEqual(f.get(verdict, 0), counted.get(verdict, 0),
                             f"finding says {f.get(verdict)} for {verdict}, the rows say {counted.get(verdict, 0)}")
        self.assertEqual(sum(counted.values()), f["themes_total"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
