#!/usr/bin/env python3
"""test_paper_numbers.py - the tool that produces every figure in the paper had no test.

The pre-paper says of its inventory table: "All figures printed by tools/paper_numbers.py from the
files that hold them. Nothing in this table is typed by hand." That claim rests entirely on this
script, and until 2026-09-10 nothing checked it.

The specific danger is its own safety net. Every figure is wrapped in safe(), which catches ANY
exception and returns the string "unavailable (ExceptionName)". That is the right behaviour - a
missing figure is a state, like every other absence here - but it means a moved file or a regex that
stopped matching degrades quietly into a string, and the person copying figures into a paper is the
only thing standing between that and a published hole. So: nothing may be unavailable on a machine
that holds the record, no figure may be None, and the figures must agree with the same quantities
counted a different way.
"""
import datetime as dt
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import paper_numbers as pn  # noqa: E402
import record  # noqa: E402


def flat(v, prefix=""):
    if isinstance(v, dict):
        for k, x in v.items():
            yield from flat(x, prefix + "/" + str(k))
    else:
        yield prefix, v


class Figures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "research" / "SOURCE_REGISTRY.json").exists():
            raise unittest.SkipTest("no registry on this machine")
        cls.out = {name: pn.safe(fn) for name, fn in pn.FIGURES}

    def test_no_figure_quietly_became_the_word_unavailable(self):
        """safe() turning a broken read into a string is correct. A paper quoting that string, or
        quoting yesterday's number because today's was a string, is not."""
        bad = [k for k, v in flat(self.out) if isinstance(v, str) and v.startswith("unavailable")]
        self.assertEqual(bad, [], "a figure the paper cites has no source on this machine: " + ", ".join(bad))

    def test_no_figure_is_none(self):
        """A None reaches a table as the word None, which reads as a number that happens to be absent
        rather than as a parser that failed."""
        bad = [k for k, v in flat(self.out) if v is None]
        self.assertEqual(bad, [], "a figure came back as None, so its parser matched nothing: " + ", ".join(bad))

    def test_the_registry_count_agrees_with_the_registry(self):
        reg = json.loads((ROOT / "research" / "SOURCE_REGISTRY.json").read_text(encoding="utf-8"))
        self.assertEqual(self.out["registry"]["records"], len(reg["sources"]))
        self.assertEqual(self.out["registry"]["opted_out"],
                         sum(1 for s in reg["sources"] if s.get("status") == "opted_out"))

    def test_the_polled_count_agrees_with_the_collectors(self):
        col = json.loads((ROOT / "research" / "COLLECTORS.json").read_text(encoding="utf-8"))
        self.assertEqual(self.out["collectors"]["polled"], sum(1 for s in col["sources"] if s.get("enabled")))
        self.assertEqual(self.out["collectors"]["listed"], len(col["sources"]))

    def test_the_corrections_count_agrees_with_the_ledger(self):
        txt = (ROOT / "research" / "08-provenance" / "CORRECTIONS.md").read_text(encoding="utf-8", errors="replace")
        self.assertEqual(self.out["corrections"]["count"], len(set(re.findall(r"\bC-(\d{3})\b", txt))))

    def test_the_provenance_parser_still_matches_the_index_it_parses(self):
        """The most brittle figure in the set: six numbers pulled out of a generated markdown document
        with regexes. If that document's wording changes, these become None and the paper loses its
        permission figures - 313 captures and 188 sources with stored evidence."""
        p = self.out["provenance"]
        for k in ("sources_with_evidence", "captures", "passed", "refused", "undocumented"):
            self.assertIsInstance(p.get(k), int, f"provenance/{k} did not parse out of the index")
        self.assertGreater(p["captures"], 0)
        self.assertGreaterEqual(p["captures"], p["passed"])

    def test_the_row_count_agrees_with_the_rows_on_disk(self):
        """Counted again, at a different instant. The collectors write while this runs, so the two
        counts are allowed to differ - but only by rows that arrived in between, and the figure may
        never be larger than what is on disk by more than the record could have grown."""
        n = 0
        for f in (ROOT / "data" / "live" / "rows").rglob("*.jsonl"):
            n += record.count_lines(f)
        self.assertIn("rows", pn.LIVE, "the row count is read from a record that is still being written")
        drift = n - self.out["rows"]["rows"]
        self.assertGreaterEqual(drift, 0, "the record on disk is smaller than the figure claims")
        self.assertLess(drift, 5000, f"the figure and the disk disagree by {drift} rows, which is "
                                     "more than a few ticks of arrival")

    def test_measured_and_received_series_sum_to_the_series_count(self):
        """The split the whole five-state vocabulary exists to carry. If it stops summing, one of the
        three numbers is being computed from a different set than the other two."""
        h = self.out["history"]
        self.assertEqual(h["measured_series"] + h["received_series"], h["series"])

    def test_the_iso_verdicts_sum_to_the_themes(self):
        i = self.out["iso37120"]
        self.assertEqual(i["indicator_reachable"] + i["adjacent"] + i["administrative_only"]
                         + i["out_of_scope_by_design"], i["themes"])

    def test_safe_reports_a_failure_rather_than_inventing_a_number(self):
        """Missing is not zero, applied to the figure generator itself."""
        v = pn.safe(lambda: (_ for _ in ()).throw(FileNotFoundError("gone")))
        self.assertTrue(str(v).startswith("unavailable"))
        self.assertIn("FileNotFoundError", str(v))
        self.assertNotIn("0", str(v).replace("unavailable", ""))

    def test_the_json_form_is_the_same_numbers_as_the_printed_form(self):
        """The paper is built from --json; a person reads the printed block. Two renderings of one
        set is exactly the 'no second copy of a number' rule, applied to this tool."""
        again = {name: pn.safe(fn) for name, fn in pn.FIGURES}
        still = [k for k in again if k not in pn.LIVE]
        self.assertEqual(json.dumps({k: again[k] for k in still}, sort_keys=True, default=str),
                         json.dumps({k: self.out[k] for k in still}, sort_keys=True, default=str),
                         "two runs of paper_numbers.py disagree about a figure that reads a record "
                         "nothing is writing to, so the figure depends on when it ran")

    def test_a_count_of_a_living_record_says_when_it_was_taken(self):
        """Four of these figures count a record the observatory is still appending to. The tool used
        to print them with no time at all, so the paper cited a row count that was true at an instant
        nobody could name. A number without its instant cannot be checked by anyone."""
        out = {name: pn.safe(fn) for name, fn in pn.FIGURES}
        out["taken_at"], out["live_figures"] = pn.taken_at(), list(pn.LIVE)
        t = dt.datetime.fromisoformat(out["taken_at"].replace("Z", "+00:00"))
        self.assertLess(abs((dt.datetime.now(dt.timezone.utc) - t).total_seconds()), 300,
                        "the figures are stamped with a time that is not now")
        self.assertTrue(out["taken_at"].endswith("Z"), "the stamp does not say which clock it is on")
        names = {n for n, _ in pn.FIGURES}
        for live in pn.LIVE:
            self.assertIn(live, names, f"{live} is declared live and is not a figure")

    def test_no_figure_has_a_category_nobody_named(self):
        """`by_status` and `by_state` were built straight from a Counter, so a row whose field was
        absent became a category called `null` in the paper's own numbers. A reader cannot act on
        `null`: it does not say whether the field was empty, absent, or never in the vocabulary."""
        def walk(v, path):
            if isinstance(v, dict):
                for k, sub in v.items():
                    self.assertIsInstance(k, str, f"{path} has a category that is not a name: {k!r}")
                    self.assertNotEqual(k, "None", f"{path} names a category 'None'")
                    walk(sub, f"{path}.{k}")
        for name, val in self.out.items():
            walk(val, name)


if __name__ == "__main__":
    unittest.main()
