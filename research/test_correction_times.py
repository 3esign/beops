#!/usr/bin/env python3
"""test_correction_times.py - the ledger of corrections was wrong about when it was written.

Thirteen entries in CORRECTIONS.md carried a hand-typed line of the form `**2026-09-10, 15:40 UTC.**`
Measured against the commit that introduced each one, ten of the thirteen were wrong, by between
thirty-five minutes and six hours and twenty-eight. The offsets are not constant, so it is not a
timezone. Two entries were stamped out of order with each other, so the ledger's own sequence
contradicted the record it sits in.

This is the file whose entire claim is that this project is honest about time, in a record that
carries C-025, "the page prints UTC and the reader's clock does not, and nobody told the reader".
"""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import correction_times as ct  # noqa: E402


class Times(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ct.LEDGER.exists():
            raise unittest.SkipTest("no corrections ledger on this machine")
        cls.doc = ct.build()
        if not cls.doc["git_readable"]:
            raise unittest.SkipTest("git is not readable here, so no time can be read from the record")

    def test_every_correction_in_the_ledger_has_an_entry(self):
        ids = [e["id"] for e in self.doc["entries"]]
        want = []
        for ln in ct.LEDGER.read_text(encoding="utf-8").splitlines():
            m = ct.HEAD.match(ln)
            if m and m.group(1) not in want:
                want.append(m.group(1))
        self.assertEqual(sorted(ids), sorted(want))
        self.assertEqual(ids, sorted(ids, key=ct._num), "the entries are not in the order they were made")

    def test_a_time_is_read_from_the_record_and_not_typed(self):
        """From C-052 on, no entry states its own time. The commit that introduced it is the time."""
        for e in self.doc["entries"]:
            if ct._num(e["id"]) >= ct.TYPED_ERA_ENDS_BEFORE:
                self.assertIsNone(e["stated_in_ledger_utc"],
                                  f"{e['id']} types a time into the ledger; the commit is the time")

    def test_a_stamp_quoted_inside_backticks_is_not_the_entry_claiming_it(self):
        """C-052 quotes the format it abolishes. The rule read the quotation as a claim and refused
        to publish the entry that introduced it - correctly, by its own logic, and wrongly in fact."""
        self.assertEqual(ct.stated_times().get("C-052"), None,
                         "an entry quoting another entry's stamp is being read as making one")
        line = 'carried a line of the form `**2026-09-10, 15:40 UTC.**` and it was wrong'
        self.assertIsNone(ct.STAMP.search(ct.CODE_SPAN.sub("", line)))
        self.assertIsNotNone(ct.STAMP.search("**2026-09-10, 15:40 UTC.** Found by ..."),
                             "a real stamp outside a code span must still be read")

    def test_the_ten_wrong_stamps_stay_named(self):
        """They are not edited - corrections are appended, never rewritten - so they must still be
        wrong, and still be exactly these ten. An entry leaving this list means a stamp was quietly
        tidied or the history was rewritten."""
        self.assertEqual(sorted(self.doc["typed_and_wrong"]), sorted(ct.KNOWN_WRONG))
        for e in self.doc["entries"]:
            if e["id"] in ct.KNOWN_WRONG:
                self.assertIsNotNone(e["stated_in_ledger_utc"], f"{e['id']}'s typed time was removed")
                self.assertGreater(abs(e["stated_minus_written_minutes"]), ct.TOLERANCE_MINUTES)

    def test_only_the_newest_may_have_no_time_yet(self):
        """A correction has no time until the commit that introduces it exists. That is true of at
        most one entry, and it is always the last one."""
        without = self.doc["not_yet_in_the_record"]
        self.assertLessEqual(len(without), 1, f"more than one entry never entered the record: {without}")
        if without:
            self.assertEqual(without[0], self.doc["entries"][-1]["id"])

    def test_the_generated_file_is_on_disk_and_is_what_the_tool_produces(self):
        on_disk = json.loads(ct.OUT.read_text(encoding="utf-8"))
        a = {k: v for k, v in on_disk.items() if k != "generated_at"}
        b = {k: v for k, v in self.doc.items() if k != "generated_at"}
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_it_says_which_clock_every_time_is_on(self):
        for e in self.doc["entries"]:
            for k in ("stated_in_ledger_utc", "written_utc"):
                if e[k] is not None:
                    self.assertTrue(e[k].endswith("Z"), f"{e['id']}/{k} does not name its clock")


if __name__ == "__main__":
    unittest.main()
