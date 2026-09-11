#!/usr/bin/env python3
"""test_guard_checks.py - the guard has fifteen checks and three of them were named in any test.

The C-050 sweep found this: the thing that decides, every quarter of an hour, whether the collection
is still lawful had almost none of its own reasoning driven by anything. `test_guard_verdict.py`
covers how the verdict is folded from the checks. This covers the checks themselves - each one given
a violating world and a clean one, and asked to say the right thing about each.

The failure this is built against is not a check saying STOP when it should say OK. It is a check
saying **OK when it cannot see** - a monitor that reports "no problem found" because it found nothing
to look at. Every check here is asked what it says when its inputs are missing, and the answer has to
be UNKNOWN.
"""
import contextlib
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import guard as g  # noqa: E402

REG_CLEAN = {"sources": [{"id": "S01", "status": "collected", "name": "One"},
                         {"id": "S02", "status": "collected", "name": "Two"},
                         {"id": "S99", "status": "opted_out", "name": "Refuser d.o.o."}]}
COL_CLEAN = {"sources": [{"sid": "S01", "enabled": True}, {"sid": "S02", "enabled": True},
                         {"sid": "S99", "enabled": False}]}
LED_CLEAN = [{"sid": "S01"}, {"sid": "S02"}]


@contextlib.contextmanager
def world(reg=None, col=None, ledger=LED_CLEAN, snapshot=None, names=None,
          receipt=None, statics=None, docs=None, no_collectors=False, ledger_is_a_dir=False,
          claims=None, guard_ledger=None):
    """A whole small BEOPS on disk, with the guard pointed at it."""
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "research" / "08-provenance").mkdir(parents=True)
        (root / "data" / "live").mkdir(parents=True)
        (root / "runtime").mkdir(parents=True)
        (root / "public").mkdir(parents=True)
        (root / "docs").mkdir(parents=True)
        w = lambda p, o: (root / p).write_text(json.dumps(o, ensure_ascii=False), encoding="utf-8")
        w("research/SOURCE_REGISTRY.json", reg if reg is not None else REG_CLEAN)
        if not no_collectors:
            w("research/COLLECTORS.json", col if col is not None else COL_CLEAN)
        lp = root / "research" / "08-provenance" / "LEDGER.jsonl"
        if ledger_is_a_dir:
            lp.mkdir()
        elif ledger is not None:
            lp.write_text("\n".join(json.dumps(x) for x in ledger), encoding="utf-8")
        if snapshot is not None:
            w("public/live-snapshot.json", snapshot)
        if names is not None:
            w("research/REFUSER_NAMES.json", names)
        if receipt is not None:
            (root / "data" / "live" / "publish-receipt.json").write_text(
                json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
        if statics is not None:
            w("research/STATIC_LAYERS.json", statics)
        if claims is not None:
            (root / "data" / "live" / "derived" / "mind").mkdir(parents=True, exist_ok=True)
            (root / "data" / "live" / "derived" / "mind" / "claims.jsonl").write_text(
                "\n".join(json.dumps(x) for x in claims), encoding="utf-8")
        if guard_ledger is not None:
            (root / "data" / "live" / "guard-ledger.jsonl").write_text(
                "\n".join(json.dumps(x) for x in guard_ledger), encoding="utf-8")
        for name, body in (docs or {}).items():
            (root / "docs" / name).write_text(body, encoding="utf-8")
        old = (g.ROOT, g.RESEARCH, g.LIVE)
        g.ROOT, g.RESEARCH, g.LIVE = root, root / "research", root / "data" / "live"
        try:
            yield root
        finally:
            g.ROOT, g.RESEARCH, g.LIVE = old


def by(checks, name):
    for c in checks:
        if c["check"] == name:
            return c
    raise AssertionError(f"no check named {name!r}; got {[c['check'] for c in checks]}")


class Permission(unittest.TestCase):
    def test_a_clean_world_passes_all_three_permission_invariants(self):
        with world():
            out = g.permission_invariants()
        for name in ("no named refusal is polled",
                     "every polled source has stored permission evidence",
                     "no polled source is in an unverified or unsettled state"):
            self.assertEqual(by(out, name)["state"], g.OK, by(out, name)["why"])

    def test_polling_a_named_refusal_stops_and_says_which(self):
        col = {"sources": [{"sid": "S01", "enabled": True}, {"sid": "S99", "enabled": True}]}
        with world(col=col, ledger=LED_CLEAN + [{"sid": "S99"}]):
            c = by(g.permission_invariants(), "no named refusal is polled")
        self.assertEqual(c["state"], g.STOP)
        self.assertIn("S99", c["why"])

    def test_a_polled_source_with_no_permission_evidence_stops_and_says_which(self):
        with world(ledger=[{"sid": "S01"}]):
            c = by(g.permission_invariants(), "every polled source has stored permission evidence")
        self.assertEqual(c["state"], g.STOP)
        self.assertIn("S02", c["why"])

    def test_every_unsettled_status_stops_collection(self):
        """The seven statuses that mean 'this was never verified'. If one of them ever stops
        stopping, a source nobody checked is being polled and the guard says ok."""
        for st in ("lead", "primary_page", "needs_decision", "restricted", "blocked",
                   "account_required", "token_required"):
            reg = {"sources": [{"id": "S01", "status": st, "name": "One"},
                               {"id": "S02", "status": "collected", "name": "Two"}]}
            with world(reg=reg):
                c = by(g.permission_invariants(), "no polled source is in an unverified or unsettled state")
            self.assertEqual(c["state"], g.STOP, f"status {st!r} did not stop collection")
            self.assertIn(st, c["why"])

    def test_a_guard_that_cannot_read_the_registers_says_unknown_and_not_ok(self):
        with world(no_collectors=True):
            out = g.permission_invariants()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["state"], g.UNKNOWN)
        self.assertNotEqual(out[0]["state"], g.OK)

    def test_an_unreadable_ledger_says_unknown_rather_than_no_evidence_missing(self):
        """The dangerous shape: no ledger read, therefore no sid missing, therefore everything fine."""
        with world(ledger_is_a_dir=True):
            out = g.permission_invariants()
        c = by(out, "permission evidence")
        self.assertEqual(c["state"], g.UNKNOWN)
        self.assertNotIn("every polled source has stored permission evidence",
                         [x["check"] for x in out],
                         "the evidence check reported a verdict from a ledger it could not read")


class ThirdPartyRoute(unittest.TestCase):
    SNAP_CLEAN = {"sources": [{"sid": "S01", "events": []}], "derived": []}

    def test_no_snapshot_is_unknown_not_ok(self):
        with world():
            out = g.refusal_route()
        self.assertEqual(out[0]["state"], g.UNKNOWN)

    def test_a_refuser_appearing_as_our_source_stops(self):
        snap = {"sources": [{"sid": "S99", "events": []}], "derived": []}
        with world(snapshot=snap, names={"names": {}}):
            c = by(g.refusal_route(), "a named refusal is never our source")
        self.assertEqual(c["state"], g.STOP)
        self.assertIn("S99", c["why"])

    def test_a_refuser_as_the_input_of_a_derived_row_stops_too(self):
        snap = {"sources": [], "derived": [{"input_sid": "S99"}]}
        with world(snapshot=snap, names={"names": {}}):
            c = by(g.refusal_route(), "a named refusal is never our source")
        self.assertEqual(c["state"], g.STOP)

    def test_without_a_watchlist_the_route_check_says_unknown_and_never_ok(self):
        """No list of names to watch for means nothing is found, which is not the same as nothing
        being there. This is the exact shape the check exists to refuse."""
        with world(snapshot=self.SNAP_CLEAN):
            out = g.refusal_route()
        c = by(out, "a refusal reached by another route stays the third party's utterance")
        self.assertEqual(c["state"], g.UNKNOWN)
        self.assertIn("REFUSER_NAMES", c["why"])

    def test_a_refuser_named_in_somebody_elses_headline_is_permitted_and_counted(self):
        snap = {"sources": [{"sid": "S01", "events": [
            {"title": "MUP saopstio nove mere", "link": "https://outlet.example/1"}]}], "derived": []}
        with world(snapshot=snap, names={"names": {"MUP": "S99"}}):
            c = by(g.refusal_route(), "a refusal reached by another route stays the third party's utterance")
        self.assertEqual(c["state"], g.OK)
        self.assertIn("1 headline", c["why"])

    def test_the_same_headline_without_the_outlet_that_wrote_it_stops(self):
        snap = {"sources": [{"sid": "S01", "events": [
            {"title": "MUP saopstio nove mere", "link": "   "}]}], "derived": []}
        with world(snapshot=snap, names={"names": {"MUP": "S99"}}):
            c = by(g.refusal_route(), "a refusal reached by another route stays the third party's utterance")
        self.assertEqual(c["state"], g.STOP)
        self.assertIn("S99", c["why"])


class PublishGate(unittest.TestCase):
    def test_no_receipt_is_unknown(self):
        with world():
            self.assertEqual(g.publish_gate()[0]["state"], g.UNKNOWN)

    def test_a_passing_receipt_is_ok(self):
        with world(receipt={"at": g.iso(g.now()), "tests_ok": True, "pushed": True, "site_verified": True, "published": True, "tests": "Ran 364 tests OK"}):
            c = by(g.publish_gate(), "the publish is gated")
        self.assertEqual(c["state"], g.OK)
        self.assertIn("364", c["why"])

    def test_one_failing_run_warns_and_half_an_hour_of_them_stops(self):
        """A flake should not scream; a site deliberately kept stale for half an hour should."""
        fresh = g.iso(g.now() - timedelta(minutes=5))
        old = g.iso(g.now() - timedelta(minutes=40))
        with world(receipt={"at": fresh, "tests_ok": False, "why": "one flake"}):
            self.assertEqual(by(g.publish_gate(), "the publish is gated")["state"], g.WARN)
        with world(receipt={"at": old, "tests_ok": False, "why": "still failing"}):
            self.assertEqual(by(g.publish_gate(), "the publish is gated")["state"], g.STOP)

    def test_fresh_failed_receipts_do_not_reset_the_failure_streak(self):
        """Audit 08: every new failed publish wrote a fresh receipt, so the guard never reached STOP."""
        rows = []
        for minutes in (70, 55, 40):
            rows.append({
                "at": g.iso(g.now() - timedelta(minutes=minutes)),
                "lawful": [{"check": "the publish is gated", "state": g.WARN,
                            "why": "THE SUITE DID NOT PASS, so nothing has been published: old"}],
            })
        with world(receipt={"at": g.iso(g.now() - timedelta(minutes=2)), "tests_ok": False,
                            "why": "still failing"},
                   guard_ledger=rows):
            c = by(g.publish_gate(), "the publish is gated")
        self.assertEqual(c["state"], g.STOP)
        self.assertIn("1.", c["why"])

    def test_a_prior_success_breaks_the_failed_publish_streak(self):
        rows = [
            {"at": g.iso(g.now() - timedelta(minutes=70)),
             "lawful": [{"check": "the publish is gated", "state": g.WARN,
                         "why": "THE SUITE DID NOT PASS, so nothing has been published: old"}]},
            {"at": g.iso(g.now() - timedelta(minutes=20)),
             "lawful": [{"check": "the publish is gated", "state": g.OK,
                         "why": "last publish ran the suite and it passed"}]},
        ]
        with world(receipt={"at": g.iso(g.now() - timedelta(minutes=2)), "tests_ok": False,
                            "why": "new failure"},
                   guard_ledger=rows):
            c = by(g.publish_gate(), "the publish is gated")
        self.assertEqual(c["state"], g.WARN)

    def test_a_receipt_written_by_powershell_with_a_bom_is_still_readable(self):
        """C-047: -Encoding UTF8 on PowerShell 5.1 writes a BOM, and this check reported unknown
        against a receipt that was perfectly well-formed."""
        with world() as root:
            (root / "data" / "live" / "publish-receipt.json").write_text(
                json.dumps({"at": g.iso(g.now()), "tests_ok": True, "pushed": True, "site_verified": True, "published": True, "tests": "Ran 1 test OK"}),
                encoding="utf-8-sig")
            c = by(g.publish_gate(), "the publish is gated")
        self.assertEqual(c["state"], g.OK, "a BOM made the guard blind to a good receipt again")

    def test_a_publish_holding_the_lock_longer_than_the_interval_is_said_out_loud(self):
        """A publisher that STOPPED is caught by the age of its receipt. One that is STUCK was
        invisible: on 2026-09-10 a publish held the lock for more than thirteen minutes - longer than
        the gap between publishes - and nothing anywhere reported it."""
        import os
        import time
        with world(receipt={"at": g.iso(g.now()), "tests_ok": True, "pushed": True, "site_verified": True, "published": True, "tests": "OK"}) as root:
            lock = root / "runtime" / "publish.lock"
            lock.write_text("held by a publish", encoding="utf-8")
            old = time.time() - 14 * 60
            os.utime(lock, (old, old))
            c = by(g.publish_gate(), "a publish is not stuck")
        self.assertEqual(c["state"], g.WARN)
        self.assertIn("queueing", c["why"])
        self.assertIn("14", c["why"].split(" min")[0])

    def test_a_lock_older_than_the_takeover_says_the_next_publish_will_step_over_it(self):
        import os
        import time
        with world(receipt={"at": g.iso(g.now()), "tests_ok": True, "pushed": True, "site_verified": True, "published": True, "tests": "OK"}) as root:
            lock = root / "runtime" / "publish.lock"
            lock.write_text("held", encoding="utf-8")
            old = time.time() - 40 * 60
            os.utime(lock, (old, old))
            c = by(g.publish_gate(), "a publish is not stuck")
        self.assertEqual(c["state"], g.WARN)
        self.assertIn("take the lock over", c["why"])

    def test_a_publish_that_is_simply_running_is_not_reported(self):
        """A lock a minute old is a publish doing its job. A check that mentions it every quarter of
        an hour is a check nobody reads."""
        with world(receipt={"at": g.iso(g.now()), "tests_ok": True, "pushed": True, "site_verified": True, "published": True, "tests": "OK"}) as root:
            (root / "runtime" / "publish.lock").write_text("held", encoding="utf-8")
            names = [c["check"] for c in g.publish_gate()]
        self.assertNotIn("a publish is not stuck", names)

    def test_no_lock_at_all_says_nothing(self):
        with world(receipt={"at": g.iso(g.now()), "tests_ok": True, "pushed": True, "site_verified": True, "published": True, "tests": "OK"}):
            names = [c["check"] for c in g.publish_gate()]
        self.assertNotIn("a publish is not stuck", names)

    def test_a_stale_receipt_that_passed_still_warns_that_the_publisher_may_be_stopped(self):
        with world(receipt={"at": g.iso(g.now() - timedelta(hours=3)), "tests_ok": True, "pushed": True, "site_verified": True, "published": True, "tests": "OK"}):
            c = by(g.publish_gate(), "the publisher is still running")
        self.assertEqual(c["state"], g.WARN)


class ScheduledTasks(unittest.TestCase):
    def test_guard_tracks_all_registered_beops_clocks(self):
        expected = ["Beops_Collect", "Beops_Mind", "Beops_Organ", "Beops_Publish", "Beops_Watch",
                    "Beops_Legal", "Beops_Guard", "Beops_Baseline"]
        self.assertEqual(g.TASKS, expected)
        for name in expected:
            self.assertIn(name, g.MAX_SILENCE_H, f"{name} has no silence threshold")


class Predictions(unittest.TestCase):
    """A prediction that fell due and was never scored. The guard warns; it never stops the record."""

    def claim(self, hours_late, outcome=None):
        due = g.now() - timedelta(hours=hours_late)
        return {"at": g.iso(due - timedelta(hours=1)), "entity": "observer",
                "claim": {"kind": "spread"}, "due": g.iso(due),
                "outcome": outcome, "settled_at": g.iso(due) if outcome else None}

    def test_a_claim_still_within_its_grace_is_not_reported(self):
        with world(claims=[self.claim(1.0)]):
            c = by(g.predictions(), "no prediction was left unscored")
        self.assertEqual(c["state"], g.OK)

    def test_a_claim_long_past_due_and_unscored_warns_and_names_it(self):
        with world(claims=[self.claim(9.0)]):
            c = by(g.predictions(), "no prediction was left unscored")
        self.assertEqual(c["state"], g.WARN)
        self.assertIn("observer", c["why"])
        self.assertIn("9.0 h ago", c["why"])

    def test_it_never_stops_the_record(self):
        """The whole point of moving this out of the test suite: the record of the city's air has
        nothing to do with whether the language layer scored its own claim."""
        with world(claims=[self.claim(500.0), self.claim(400.0)]):
            for c in g.predictions():
                self.assertNotEqual(c["state"], g.STOP)

    def test_a_scored_claim_is_never_late(self):
        with world(claims=[self.claim(99.0, outcome="false")]):
            c = by(g.predictions(), "no prediction was left unscored")
        self.assertEqual(c["state"], g.OK)
        self.assertIn("1 claims on file", c["why"])

    def test_no_register_at_all_says_nothing(self):
        with world():
            self.assertEqual(g.predictions(), [])


class StaticLayers(unittest.TestCase):
    LAYER = {"layers": [{"file": "public/context-population.json", "sha256": None,
                         "must_carry": ["source", "licence"],
                         "must_be_named": ["Kontur", "CC BY"],
                         "review_due": "2099-01-01"}]}

    def _write_layer(self, root, doc):
        (root / "public" / "context-population.json").write_text(
            json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    def test_no_register_is_unknown(self):
        with world():
            self.assertEqual(g.static_layers()[0]["state"], g.UNKNOWN)

    def test_a_missing_layer_stops(self):
        with world(statics=self.LAYER):
            c = by(g.static_layers(), "static layers are present and still the file we accepted")
        self.assertEqual(c["state"], g.STOP)
        self.assertIn("context-population.json", c["why"])

    def test_a_layer_that_lost_its_licence_line_is_unattributed(self):
        with world(statics=self.LAYER) as root:
            self._write_layer(root, {"source": "Kontur", "licence": ""})
            c = by(g.static_layers(), "every static layer is named where it is shown")
        self.assertEqual(c["state"], g.STOP)
        self.assertIn("licence", c["why"])

    def test_a_page_that_shows_a_layer_must_name_its_credit(self):
        """C-049: the credit is what the licence requires, and it has to be on the page, not only in
        the file. The register names the credit; the check does not invent a form of words."""
        good = "<html>context-population.json Kontur population 2022 (CC BY 4.0)</html>"
        bad = "<html>context-population.json, drawn as hexagons</html>"
        with world(statics=self.LAYER, docs={"index.html": good}) as root:
            self._write_layer(root, {"source": "Kontur", "licence": "CC BY 4.0"})
            self.assertEqual(by(g.static_layers(), "every static layer is named where it is shown")["state"], g.OK)
        with world(statics=self.LAYER, docs={"index.html": bad}) as root:
            self._write_layer(root, {"source": "Kontur", "licence": "CC BY 4.0"})
            c = by(g.static_layers(), "every static layer is named where it is shown")
        self.assertEqual(c["state"], g.STOP)
        self.assertIn("index.html", c["why"])

    def test_a_changed_file_warns_rather_than_stops_because_a_change_is_not_a_fault(self):
        reg = {"layers": [dict(self.LAYER["layers"][0], sha256="0" * 64)]}
        with world(statics=reg) as root:
            self._write_layer(root, {"source": "Kontur", "licence": "CC BY 4.0"})
            c = by(g.static_layers(), "static layers are present and still the file we accepted")
        self.assertEqual(c["state"], g.WARN)
        self.assertIn("re-accept", c["why"])

    def test_a_review_date_in_the_past_asks_somebody_to_look(self):
        reg = {"layers": [dict(self.LAYER["layers"][0], review_due="2020-01-01")]}
        with world(statics=reg) as root:
            self._write_layer(root, {"source": "Kontur", "licence": "CC BY 4.0"})
            c = by(g.static_layers(), "somebody should look for a newer release")
        self.assertEqual(c["state"], g.WARN)


class EveryCheckIsDriven(unittest.TestCase):
    def test_no_check_the_guard_can_emit_is_left_undriven(self):
        """The sweep's own finding, kept from happening again: every name this file drives is
        collected here, and any check the guard can emit that is not in it is named out loud."""
        driven = {
            "no named refusal is polled",
            "every polled source has stored permission evidence",
            "no polled source is in an unverified or unsettled state",
            "permission files", "permission evidence",
            "a named refusal is never our source",
            "a refusal reached by another route stays the third party's utterance",
            "third-party route",
            "the publish is gated", "the publisher is still running", "a publish is not stuck",
            "static layers", "static layers are present and still the file we accepted",
            "every static layer is named where it is shown",
            "somebody should look for a newer release", "no prediction was left unscored",
        }
        src = (ROOT / "tools" / "guard.py").read_text(encoding="utf-8")
        import re
        emitted = set(re.findall(r'"check":\s*"([^"]+)"', src))
        # This test would pass on an empty set, which is the failure it exists to refuse: a check
        # that finds nothing because it looked at nothing. It passed first time and that is exactly
        # when to ask whether it looked.
        self.assertGreaterEqual(len(emitted), 12,
                                f"only {len(emitted)} check names found in guard.py - this test is "
                                "reading the wrong thing and would pass whatever the guard did")
        undriven = sorted(emitted - driven - {"retention"})
        self.assertEqual(undriven, [], "the guard can emit a check nothing drives: " + ", ".join(undriven))
        stale = sorted(driven - emitted)
        self.assertEqual(stale, [], "this file drives a check the guard no longer emits: " + ", ".join(stale))


if __name__ == "__main__":
    unittest.main()
