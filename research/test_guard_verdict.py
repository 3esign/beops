#!/usr/bin/env python3
"""test_guard_verdict.py - the guard's own promise, asserted for the first time.

The guard's docstring says that when a permission invariant fails it "does NOT repair - it says STOP,
loudly". On 2026-09-10 a sweep found that of its fifteen checks only three were named in any test,
`guard.run` was tested by nobody, and the string STOP appeared in no test in the project. A refactor
that made STOP unreachable, or that let an `unknown` resolve to `ok`, would have passed all 288 tests
while the guard went on printing a clean verdict.

These tests drive the verdict logic directly, with the checks replaced, so they say nothing about
whether the machine is healthy and everything about whether the guard can still report that it is not.
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import guard as g  # noqa: E402


def row(state, name="x"):
    return {"check": name, "state": state, "why": ""}


class Verdict(unittest.TestCase):
    def setUp(self):
        self._saved = (g.TASKS, g.permission_invariants, g.refusal_route,
                       g.publish_gate, g.static_layers, g.organ_output)
        g.TASKS = []                                   # no schtasks call: this is about the arithmetic

    def tearDown(self):
        (g.TASKS, g.permission_invariants, g.refusal_route,
         g.publish_gate, g.static_layers, g.organ_output) = self._saved

    def set(self, *states):
        it = iter(list(states) + [[]] * 5)
        g.permission_invariants = lambda: next(it)
        g.refusal_route = lambda: next(it)
        g.publish_gate = lambda: next(it)
        g.static_layers = lambda: next(it)
        g.organ_output = lambda: next(it)

    def test_one_stop_anywhere_makes_the_whole_verdict_stop(self):
        for i in range(5):
            with self.subTest(position=i):
                groups = [[row(g.OK)] for _ in range(5)]
                groups[i] = [row(g.STOP, "the one that failed")]
                self.set(*groups)
                self.assertEqual(g.run(dry=True)["verdict"], g.STOP,
                                 "a STOP in position %d did not reach the verdict" % i)

    def test_an_unknown_can_never_report_ok(self):
        """The watchman's third rule, which the guard inherits: anything unreadable is UNKNOWN, and a
        run containing an UNKNOWN can never report OK."""
        self.set([row(g.OK)], [row(g.UNKNOWN)], [row(g.OK)], [row(g.OK)], [row(g.OK)])
        self.assertEqual(g.run(dry=True)["verdict"], g.UNKNOWN)

    def test_a_stop_outranks_an_unknown(self):
        self.set([row(g.UNKNOWN)], [row(g.STOP)], [], [], [])
        self.assertEqual(g.run(dry=True)["verdict"], g.STOP)

    def test_an_unknown_outranks_a_warn(self):
        self.set([row(g.WARN)], [row(g.UNKNOWN)], [], [], [])
        self.assertEqual(g.run(dry=True)["verdict"], g.UNKNOWN)

    def test_a_warn_outranks_ok_and_does_not_become_a_stop(self):
        self.set([row(g.OK)], [row(g.WARN)], [], [], [])
        self.assertEqual(g.run(dry=True)["verdict"], g.WARN)

    def test_all_ok_is_ok(self):
        self.set([row(g.OK)], [row(g.OK)], [row(g.OK)], [row(g.OK)], [row(g.OK)])
        self.assertEqual(g.run(dry=True)["verdict"], g.OK)

    def test_the_guard_never_repairs_a_permission_failure(self):
        """It may restart a stopped scheduled task. It may never make a permission failure go away,
        because a collector that has lost its permission must be stopped by a person who understands
        why. REPAIRABLE is the whole list of what it is allowed to touch."""
        self.assertEqual(set(g.REPAIRABLE), {"disabled", "not running"},
                         "the guard has been given permission to repair something new")

    def test_every_check_the_guard_emits_carries_a_state_and_a_reason(self):
        """A check that reports without saying why is a check nobody can act on."""
        self.set([row(g.OK, "a")], [row(g.WARN, "b")], [], [], [])
        r = g.run(dry=True)
        for c in r["lawful"] + r["organs"]:
            self.assertIn("state", c)
            self.assertIn("why", c)
            self.assertIn(c["state"], (g.OK, g.WARN, g.STOP, g.UNKNOWN),
                          "a check reported a state outside the guard's own four: %r" % c["state"])

    def test_the_report_prints_the_verdict_it_computed(self):
        self.set([row(g.STOP, "the one that failed")], [], [], [], [])
        r = g.run(dry=True)
        text = g.report(r)
        self.assertIn(g.STOP, text)
        self.assertIn("the one that failed", text)


if __name__ == "__main__":
    unittest.main()
