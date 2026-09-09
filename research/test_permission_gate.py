#!/usr/bin/env python3
"""The claim at the centre of this project, as a test rather than a sentence.

"Nothing is collected without a captured permission, and every named refusal is honoured" is the one
assertion the whole record rests on. Until now it was true because the collector checks a gate at
runtime and because a person went and looked. This makes it a checked invariant: if a source is ever
added to the polling list without evidence behind it, or if a publisher who said no is ever polled,
the suite fails before anything is collected.

It also fixes a claim that reads worse than it is. The provenance index reports 26 undocumented
sources, which sounds like 26 sources being read without paperwork. It is the opposite: they are the
queue of sources NOT being read. This test is where that distinction is enforced.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

COLLECTORS = json.loads((ROOT / "research" / "COLLECTORS.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "research" / "SOURCE_REGISTRY.json").read_text(encoding="utf-8"))
POLLED = {s["sid"] for s in COLLECTORS["sources"] if s.get("enabled")}
LISTED = {s["sid"] for s in COLLECTORS["sources"]}
STATUS = {s.get("id"): s.get("status") for s in REGISTRY["sources"]}

# A status that means the publisher has not agreed, or that we have not settled the question.
FORBIDDEN = {"opted_out", "needs_decision", "restricted", "blocked", "account_required",
             "token_required", "dead", "no_coverage"}


def ledger_sids() -> set:
    p = ROOT / "research" / "08-provenance" / "LEDGER.jsonl"
    out = set()
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue                      # a truncated line proves a truncated write, not a permission
        if row.get("sid"):
            out.add(row["sid"])
    return out


class PermissionGateTests(unittest.TestCase):
    def test_every_polled_source_has_stored_permission_evidence(self):
        missing = sorted(POLLED - ledger_sids())
        self.assertEqual(missing, [], "polled with no line in the permission ledger: " + ", ".join(missing))

    def test_no_publisher_who_said_no_is_polled(self):
        refused = sorted(sid for sid in POLLED if STATUS.get(sid) == "opted_out")
        self.assertEqual(refused, [], "a named refusal is being polled: " + ", ".join(refused))

    def test_no_polled_source_sits_in_an_unsettled_state(self):
        bad = sorted(f"{sid}={STATUS.get(sid)}" for sid in POLLED if STATUS.get(sid) in FORBIDDEN)
        self.assertEqual(bad, [], "polled while unsettled: " + ", ".join(bad))

    def test_a_polled_source_has_at_least_been_probed(self):
        """C-017. The registry's own legend says `lead` means "not independently verified in this
        pass" and `primary_page` means "actual local feed not validated". Four sources carried one of
        those while the collector was reading them on a schedule. The permission was never in doubt -
        all four have a ledger line - but a status is a claim about a source, and the audit is what
        the paper leans on. Reading a source every ten minutes IS a bounded parse succeeding, which is
        what `probe_ok` asserts, so that is the status they now carry."""
        NEVER_PROBED = {"lead", "primary_page"}
        wrong = sorted(f"{sid}={STATUS.get(sid)}" for sid in POLLED if STATUS.get(sid) in NEVER_PROBED)
        self.assertEqual(wrong, [],
                         "polled while the registry says it was never verified: " + ", ".join(wrong))

    def test_every_polled_source_is_a_source_the_registry_knows(self):
        unknown = sorted(sid for sid in POLLED if sid not in STATUS)
        self.assertEqual(unknown, [], "polled but not in the registry: " + ", ".join(unknown))

    def test_a_disabled_collector_says_why_it_is_disabled(self):
        for s in COLLECTORS["sources"]:
            if not s.get("enabled"):
                self.assertTrue((s.get("why_disabled") or "").strip(),
                                f"{s['sid']} is disabled with no reason recorded")

    def test_the_undocumented_queue_is_not_being_collected(self):
        """The 26 are a work queue, not a hole in the collection."""
        idx = (ROOT / "research" / "08-provenance" / "INDEX.md").read_text(encoding="utf-8", errors="replace")
        import re
        m = re.search(r"\n#+ [^\n]*not yet documented[^\n]*\n(.*?)(?=\n#+ |\Z)", idx, re.S | re.I)
        if not m:
            self.skipTest("the index has no 'not yet documented' section to check against")
        queued = set(re.findall(r"\b(S\d+)\b", m.group(1)))
        self.assertEqual(sorted(queued & POLLED), [],
                         "a source in the undocumented queue is being polled: " + ", ".join(sorted(queued & POLLED)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
