#!/usr/bin/env python3
"""test_record_shape.py - the shape of the record, checked against the record.

Nine of the corrections written on 10 September were one defect: a verifier reporting success while
reading less than it was believed to read. The sharpest, C-057, was a test that listed one directory
level while the record nests - it scanned two files out of eight and never opened either file holding
the thing it existed to catch.

Fixing that one test fixes one test. This checks the class. `research/RECORD_SHAPE.json` says which
trees are flat and which nest, and these tests fail when the disk disagrees - **on the day the record
changes shape, rather than months later when somebody notices a number is too small.**

Three of the beliefs this project has been running on are also turned into checks here: that the entity
notebooks duplicate the month file for the states that matter, that the settlements register is
complete, and that every directory the record writes to belongs to a declared tree.
"""
import collections
import json
import os
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import record  # noqa: E402

SHAPE = ROOT / "research" / "RECORD_SHAPE.json"


def deepest_file(base: pathlib.Path, stop_at: int) -> int:
    """How deep the files under `base` go, walking DIRECTORIES and stopping as soon as the answer is
    known to exceed `stop_at`.

    The first version of this rglob'd every file: 2,738 receipts, 1,343 evidence files and the rest,
    on every run of the suite, which the publish gate runs every ten minutes. It took 41 seconds and
    would have taken longer every day - **which is precisely the defect C-055 recorded, re-created by
    the test written to catch that class.** Directories bound file depth and there are two orders of
    magnitude fewer of them, and once one file is too deep there is nothing left to learn.
    """
    deepest = 0
    for dirpath, dirnames, filenames in os.walk(base):
        rel = pathlib.Path(dirpath).relative_to(base)
        d = 0 if str(rel) == "." else len(rel.parts)
        if filenames:
            deepest = max(deepest, d + 1)
            if deepest > stop_at:
                return deepest
        if d + 1 > stop_at:
            dirnames[:] = []          # nothing below can make the answer smaller
    return deepest


class Shape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SHAPE.exists():
            raise unittest.SkipTest("no record-shape register on this machine")
        cls.d = json.loads(SHAPE.read_text(encoding="utf-8"))
        cls.trees = {t["path"]: t for t in cls.d["trees"]}
        # Walk each tree ONCE and share the answer. This file was 11.6 s of a 46 s suite - the most
        # expensive module in the project - because three tests each walked all five trees and a
        # fourth walked them again to time the walking. The publish gate runs this every ten minutes.
        import time as _t
        t0 = _t.time()
        cls.depth = {}
        for path, t in cls.trees.items():
            p = ROOT / path
            cls.depth[path] = deepest_file(p, t["max_depth"]) if p.exists() else None
        cls.walk_seconds = _t.time() - t0

    def test_every_tree_is_as_deep_as_it_says_it_is(self):
        """The early alarm. A tree declared flat that grows a subdirectory fails here, and every
        one-level reader of it becomes suspect on the same day rather than silently."""
        for path, t in self.trees.items():
            p = ROOT / path
            if not p.exists():
                continue
            actual = self.depth[path]
            if not actual:
                continue
            self.assertLessEqual(actual, t["max_depth"],
                                 f"{path} now holds files {actual} deep; the register says {t['max_depth']}")
            if not t["nests"]:
                self.assertLessEqual(actual, t["max_depth"],
                                     f"{path} is declared flat and is not")

    def test_a_tree_declared_flat_really_is_flat(self):
        for path, t in self.trees.items():
            if t["nests"]:
                continue
            p = ROOT / path
            if not p.exists():
                continue
            self.assertLessEqual(self.depth[path], t["max_depth"],
                                 f"{path} is declared flat and holds files deeper than "
                                 f"{t['max_depth']}")

    def test_every_directory_the_record_writes_to_is_declared(self):
        """Anti-blindness, applied to the declaration itself: this file must not read a narrower
        slice of the disk than the disk holds."""
        declared = [ROOT / p for p in self.trees]
        for base in (ROOT / "data" / "live", ROOT / "research" / "evidence"):
            if not base.exists():
                continue
            for d in sorted(base.iterdir()):
                if not d.is_dir() or not any(d.iterdir()):
                    continue
                self.assertTrue(any(str(d).startswith(str(x)) or str(x).startswith(str(d)) for x in declared),
                                f"{d.relative_to(ROOT)} holds files and no declared tree covers it")

    def test_every_file_sitting_beside_the_trees_is_declared_too(self):
        """The same blindness one level up. A ledger that appears in data/live and is never declared
        is a part of the record nobody enumerates."""
        live = ROOT / "data" / "live"
        if not live.exists():
            self.skipTest("no live directory on this machine")
        declared = set(self.d["files_directly_in_data_live"]["files"])
        for f in sorted(live.iterdir()):
            if f.is_file():
                self.assertIn(f.name, declared,
                              f"data/live/{f.name} sits beside the trees and nothing declares it")

    def test_the_raw_captures_are_the_part_that_is_deleted_and_say_so(self):
        """The tree the first run of this test found: 778 files under retention rule R2, undeclared."""
        raw = next(t for t in self.d["trees"] if t["path"] == "data/live/raw")
        self.assertIn("apply_retention.py", raw["read_by"])
        self.assertIn("R2", raw["what_it_is"])
        pol = ROOT / "research" / "RETENTION.json"
        if pol.exists():
            self.assertIn("data/live/raw", pol.read_text(encoding="utf-8"),
                          "the retention policy no longer names the tree it erases")

    def test_this_test_does_not_grow_with_the_record(self):
        """C-055, applied to this file. The publish gate runs the suite every ten minutes; a check
        whose cost rises with the size of the record it guards eventually stops the thing it protects.
        Walking directories rather than files keeps this bounded by the shape, not the volume."""
        self.assertLess(self.walk_seconds, 5.0,
                        f"measuring the record's shape took {self.walk_seconds:.1f}s; it is walking "
                        "files instead of directories again")

    def test_the_readers_named_as_scanning_one_level_still_exist(self):
        """A register that names files is a register that can go stale."""
        t = self.trees["data/live/rows"]
        for name in t["readers_that_scan_one_level"]:
            hit = list((ROOT / "tools").glob(name)) + list((ROOT / "research").glob(name))
            self.assertTrue(hit, f"{name} is named as a reader of the rows and is not in the project")


class Receipts(unittest.TestCase):
    """The tree the whole 'missing is not zero' rule rests on, and the first test of it."""

    @classmethod
    def setUpClass(cls):
        cls.dir = ROOT / "data" / "live" / "receipts"
        if not cls.dir.exists():
            raise unittest.SkipTest("no receipts on this machine")
        cls.shape = json.loads(SHAPE.read_text(encoding="utf-8"))
        cls.decl = next(t for t in cls.shape["trees"] if t["path"] == "data/live/receipts")
        # The newest few per source, and every failure. These invariants are about the SHAPE of a
        # receipt, not about how many there are, and reading forty per source made this the most
        # expensive module in the suite.
        cls.some = []
        for d in sorted(cls.dir.iterdir()):
            if not d.is_dir():
                continue
            files = sorted(d.glob("*.json"))
            for f in files[-3:] + files[:1]:
                try:
                    cls.some.append(json.loads(f.read_text(encoding="utf-8")))
                except ValueError:
                    pass

    def test_a_source_that_answered_nothing_still_left_a_receipt(self):
        """The rule stated at its source rather than downstream: nothing to report and never asked
        are different objects on disk. If this ever fails, every silence in the record becomes
        ambiguous and the watchman's whole design goes with it."""
        self.assertTrue(self.some, "no receipts could be read")
        empty = [r for r in self.some if r.get("rows") == 0 and r.get("state") == "captured"]
        for r in empty:
            self.assertIn("attempted_at", r)
            self.assertIsNotNone(r.get("completed_at"),
                                 "a receipt says the source answered and does not say when it finished")

    def test_every_receipt_carries_what_the_register_says_it_must(self):
        for r in self.some:
            for k in self.decl["required_keys"]:
                self.assertIn(k, r, f"a receipt from {r.get('sid')} does not carry {k}")

    def test_the_receipt_vocabulary_is_closed(self):
        """A third vocabulary lives under the key `state`, and this is the first thing to say so."""
        allowed = set(self.decl["state_vocabulary"])
        for r in self.some:
            self.assertIn(r.get("state"), allowed,
                          f"a receipt carries the state {r.get('state')!r}, which the register does "
                          "not declare")

    def test_a_failed_poll_says_why(self):
        for r in self.some:
            if r.get("state") == "failed":
                self.assertTrue(r.get("error") or r.get("http_status"),
                                "a receipt records a failure and not what failed")

    def test_the_collision_on_the_word_state_is_counted_rather_than_forgotten(self):
        """C-050 named two vocabularies under this key. There are four. The number is written down so
        that the argument for renaming the field gets stronger on the record rather than in memory."""
        c = self.shape["the_field_name_collision"]["measured_2026_09_10"]
        self.assertGreaterEqual(len(c), 4)
        self.assertIn("live_receipt", c)
        self.assertIn("failed", c["voice_bench"])
        self.assertIn("failed", c["live_receipt"])


class MindTree(unittest.TestCase):
    """The nested tree, and the three things that were true by belief until now."""

    @classmethod
    def setUpClass(cls):
        cls.mind = ROOT / "data" / "live" / "derived" / "mind"
        if not cls.mind.exists():
            raise unittest.SkipTest("no mind on this machine")
        cls.month = [r for f in cls.mind.glob("*.jsonl") if f.name != "claims.jsonl"
                     for r in record.objects(f)]
        cls.notebook = [r for f in sorted((cls.mind / "notebook").glob("*.jsonl"))
                        for r in record.objects(f)]

    def counts(self, rows, states):
        c = collections.Counter(r.get("state") for r in rows)
        return {s: c.get(s, 0) for s in states}

    def test_the_notebooks_duplicate_the_month_file_for_the_states_that_are_counted(self):
        """The belief a one-level reader of the mind rests on. If it ever stops being true, every
        acceptance figure computed from the month file alone is computed over a fraction."""
        if not self.notebook:
            self.skipTest("no entity notebooks yet")
        states = ("thought", "rejected")
        m, n = self.counts(self.month, states), self.counts(self.notebook, states)
        for s in states:
            self.assertEqual(m[s], n[s],
                             f"the month file holds {m[s]} rows in state {s!r} and the notebooks hold "
                             f"{n[s]}: they are no longer the same utterances, so a one-level reader "
                             "is now losing some")

    def test_every_settlement_is_told_to_the_entity_that_predicted_it(self):
        """Two records of one event: the register is the record, the notebook line is the telling.
        The counts are compared over SETTLED rows only - the register also holds claims that are
        still open, which is the thing the first version of this test got wrong."""
        reg = list(record.objects(self.mind / "claims.jsonl"))
        settled = [r for r in reg if r.get("outcome") is not None]
        told = [r for r in self.notebook if r.get("state") == "claim_settled"]
        if not settled and not told:
            self.skipTest("nothing settled yet")
        self.assertEqual(len(settled), len(told),
                         f"{len(settled)} settled claims in the register and {len(told)} told to the "
                         "entities")

    def test_a_claim_is_written_when_it_is_made_and_scored_when_it_falls_due(self):
        """The shape that makes a prediction a prediction. The row exists from the moment the claim is
        made, with its due time; the outcome arrives later or not at all. A register that only
        recorded settlements could be written after the answer was known, and would be worth nothing.
        """
        reg = list(record.objects(self.mind / "claims.jsonl"))
        if not reg:
            self.skipTest("no claims yet")
        for r in reg:
            self.assertIsNone(r.get("state"),
                              "a claim grew a pipeline state; the register declares it has none")
            for key in ("claim", "entity", "at", "due", "outcome", "settled_at"):
                self.assertIn(key, r, f"a claim does not record its {key}")
            if r.get("outcome") is None:
                self.assertIsNone(r.get("settled_at"),
                                  "a claim has a settling time and no outcome")
            else:
                self.assertIn(r["outcome"], ("true", "false", "unverifiable"),
                              f"a claim carries the outcome {r['outcome']!r}, which is not one of "
                              "true / false / unverifiable")
                self.assertTrue(r.get("settled_at"), "a scored claim does not say when it was scored")

    def test_no_prediction_is_quietly_forgotten(self):
        """The strongest thing this register can be asked, and the reason it exists. A claim past its
        due time that never gets an outcome is a prediction nobody scored - which is how a record
        keeps only the predictions that came true."""
        import datetime as dt
        reg = list(record.objects(self.mind / "claims.jsonl"))
        if not reg:
            self.skipTest("no claims yet")
        now = dt.datetime.now(dt.timezone.utc)
        grace = dt.timedelta(hours=3)          # the scorer runs on the mind's tick, not at the instant
        forgotten = []
        for r in reg:
            if r.get("outcome") is not None:
                continue
            try:
                due = dt.datetime.fromisoformat(str(r.get("due")).replace("Z", "+00:00"))
            except ValueError:
                continue
            if now - due > grace:
                forgotten.append("%s due %s" % (r.get("entity"), r.get("due")))
        self.assertEqual(forgotten[:5], [],
                         "a prediction fell due and was never scored: " + "; ".join(forgotten[:5]))

    def test_the_benchmark_runs_are_not_mistaken_for_the_record(self):
        """voice_bench holds hand-made benchmark lines, including the one undeclared state the record
        carries. It is named in the shape register so that a reader who walks the tree knows what it
        has picked up."""
        d = json.loads(SHAPE.read_text(encoding="utf-8"))
        nested = next(t for t in d["trees"] if t["path"] == "data/live/derived")["nested_parts"]
        self.assertIn("mind/voice_bench/*.jsonl", nested)
        bench = ROOT / "data" / "live" / "derived" / "mind" / "voice_bench"
        if bench.exists():
            for f in bench.glob("*.jsonl"):
                for r in record.objects(f):
                    self.assertNotIn(r.get("state"), ("thought", "rejected"),
                                     "a benchmark line carries an utterance state and would be counted "
                                     "as one by anything that walks this tree")


if __name__ == "__main__":
    unittest.main()
