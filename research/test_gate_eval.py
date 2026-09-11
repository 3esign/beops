#!/usr/bin/env python3
"""The gate evaluation as a test, so a hole that was closed cannot silently reopen.

`eval_gate.py` measures; this pins the measurement. If a later edit to the validator lets one of the
locked families through again, this fails with the family's name. If a later edit closes one of the
three residues, this fails too - and the right response then is to move that family out of the
residue list and say so in the paper, not to loosen the test.
"""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
sys.path.insert(0, str(ROOT / "tools"))

import eval_gate as E  # noqa: E402

# Measured against organ version 0.3.5 on 2026-09-09, before the semantic guards existed.
BASELINE_FALSE_ACCEPTS = 17
BASELINE_RATE = 0.472

# What the gate must keep catching. One name per family, taken from the set.
LOCKED = {
    "number_not_in_digest", "no_citation", "unknown_fact_id", "too_short", "too_long",
    "future_as_fact", "prompt_echo", "not_english", "claim_malformed", "claim_horizon",
    "hypothesis_as_fact", "hypothesis_number", "echo_of_previous",
    "citation_mismatch", "untimed_as_now", "silence_as_zero", "causal_invention", "unit_swap",
    "advice", "superlative_unsupported", "coverage_overclaim", "link_as_fact", "authority_borrowing",
    "voice_ijekavica", "voice_citation_drift", "voice_untranslated", "voice_not_serbian",
    "voice_meaning_drift", "voice_number_added", "voice_number_invented", "voice_prompt_echo", "voice_too_short",
}

# What the gate is known NOT to catch, and cannot without a reader. Named in the paper as the residue.
RESIDUE = {"number_rebinding", "measurement_time_drift"}  # v0.5 closes the negation-drift fixture; general semantics still need a reader


class GateEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(E.SET_PATH.read_text(encoding="utf-8"))
        cls.out = E.run(cls.data)
        cls.summary = E.summarise(cls.out["results"])

    def test_the_set_is_well_formed(self):
        seen = set()
        for it in self.data["items"]:
            self.assertNotIn(it["id"], seen, "duplicate item id")
            seen.add(it["id"])
            self.assertIn(it["should"], ("accept", "reject"))
            self.assertIn(it["stage"], ("think", "voice"))
            self.assertTrue(it["why"].strip(), it["id"] + " carries no label reason")
        self.assertGreaterEqual(len(self.data["items"]), 40)

    def test_every_digest_fact_is_bilingual(self):
        for f in self.data["digest"]["facts"]:
            self.assertTrue(f["sr"].strip() and f["en"].strip(), f["id"])

    def test_the_locked_families_are_all_refused(self):
        leaked = sorted({r["family"] for r in self.out["results"]
                         if r["family"] in LOCKED and r["outcome"] == "false_accept"})
        self.assertEqual(leaked, [], "the gate stopped catching: " + ", ".join(leaked))

    def test_the_residue_is_exactly_what_the_paper_says_it_is(self):
        missed = {r["family"] for r in self.out["results"] if r["outcome"] == "false_accept"}
        self.assertEqual(missed, RESIDUE,
                         "the residue changed; update RESIDUE and the paper together, in that order")

    def test_faithful_utterances_are_not_silenced(self):
        silenced = sorted(r["id"] for r in self.out["results"]
                          if r["outcome"] == "false_reject" and r["family"] != "rounding")
        self.assertEqual(silenced, [], "the gate began refusing supported sentences: " + ", ".join(silenced))

    def test_the_rate_is_better_than_the_baseline_and_stays_there(self):
        self.assertLess(self.summary["false_accept"], BASELINE_FALSE_ACCEPTS)
        self.assertLessEqual(self.summary["false_accept_rate"], 0.10)
        self.assertGreater(BASELINE_RATE, self.summary["false_accept_rate"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
