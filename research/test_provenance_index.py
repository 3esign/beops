#!/usr/bin/env python3
"""test_provenance_index.py - the file the paper's permission figures come from had no test.

`tools/build_provenance_index.py` renders research/08-provenance/INDEX.md from the capture ledger,
and `tools/paper_numbers.py` reads the numbers back out of that Markdown **with regular expressions**.
So the chain that produces "313 captures, 169 passed, 11 refused, 26 undocumented" in a paper runs:
ledger -> generator -> prose -> regex -> figure. Nothing tested either end of it, and a text interface
between two programs is the easiest place in the project for a number to change meaning silently.

The classification rules encoded in the generator are legal ones, not cosmetic: what refuses reading,
what merely speaks to search engines (C-010), and what is unknown - which is never a permission.
"""
import json
import os
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_provenance_index as B  # noqa: E402
import paper_numbers as pn  # noqa: E402


def cap(sid, **kw):
    e = {"sid": sid, "name": kw.pop("name", "Source " + sid),
         "captured_at_utc": kw.pop("at", "2026-09-01T00:00:00Z"),
         "capture_ok": kw.pop("capture_ok", True), "evidence_dir": "research/evidence/legal/%s" % sid}
    e.update(kw)
    return e


class Index(unittest.TestCase):
    def build(self, ledger, registry_ids=()):
        d = pathlib.Path(tempfile.mkdtemp())
        (d / "research" / "08-provenance").mkdir(parents=True)
        (d / "research" / "evidence" / "legal").mkdir(parents=True)
        (d / "research" / "08-provenance" / "LEDGER.jsonl").write_text(
            "\n".join(json.dumps(x) for x in ledger), encoding="utf-8")
        (d / "research" / "SOURCE_REGISTRY.json").write_text(
            json.dumps({"sources": [{"id": s, "name": s} for s in registry_ids]}), encoding="utf-8")
        old = (B.ROOT, B.LEDGER, B.REGISTRY, B.OUT)
        B.ROOT = str(d)
        B.LEDGER = str(d / "research" / "08-provenance" / "LEDGER.jsonl")
        B.REGISTRY = str(d / "research" / "SOURCE_REGISTRY.json")
        B.OUT = str(d / "research" / "08-provenance" / "INDEX.md")
        try:
            B.main()
        finally:
            B.ROOT, B.LEDGER, B.REGISTRY, B.OUT = old
        return d, (d / "research" / "08-provenance" / "INDEX.md").read_text(encoding="utf-8")

    def figures(self, d):
        """What the paper would print, read back out of the generated prose by the figure tool."""
        old = pn.ROOT
        pn.ROOT = d
        try:
            return pn.provenance()
        finally:
            pn.ROOT = old

    # ---------------------------------------------------------------- the classification

    def test_a_header_that_speaks_to_search_engines_is_not_a_refusal(self):
        """C-010, kept. The first version of this rule read any X-Robots-Tag as a refusal and listed
        a CC BY dataset that explicitly permits commercial reuse under 'said no'."""
        for value in ("noindex", "nofollow", "index, follow", "noarchive"):
            e = cap("S1", opt_out_signals_seen={"https://x/": {"X-Robots-Tag": value}})
            self.assertEqual(B.header_refusals(e), {}, f"{value!r} was read as a refusal to be read")

    def test_a_header_that_refuses_reading_or_mining_is_a_refusal(self):
        for header, value in (("X-Robots-Tag", "noai"), ("X-Robots-Tag", "noimageai"),
                              ("TDM-Reservation", "1"), ("Content-Usage", "ai=n"),
                              ("Content-Usage", "tdm=n")):
            e = cap("S1", opt_out_signals_seen={"https://x/": {header: value}})
            self.assertTrue(B.header_refusals(e), f"{header}: {value} did not refuse")

    def test_an_unknown_is_never_rendered_as_a_permission(self):
        """A capture that did not complete is incomplete, never permitted. The first run of the
        capture tool did exactly this and it is why the section exists."""
        d, txt = self.build([cap("S1", allowed_for_us=True, capture_ok=False),
                             cap("S2", allowed_for_us=None, capture_ok=True)], ["S1", "S2"])
        f = self.figures(d)
        self.assertEqual(f["passed"], 0, "an unfinished capture was counted as an access check passed")
        self.assertEqual(f["incomplete"], 2)

    def test_a_refusal_outranks_a_note_that_says_otherwise(self):
        d, txt = self.build([cap("S1", allowed_for_us=False, note="the owner told us verbally it is fine")],
                            ["S1"])
        self.assertEqual(self.figures(d)["refused"], 1)
        self.assertIn("Do not collect", txt)

    def test_a_source_awaiting_a_decision_is_neither_permitted_nor_refused(self):
        d, _ = self.build([cap("S1", allowed_for_us=True, manual_verdict="needs_decision")], ["S1"])
        f = self.figures(d)
        self.assertEqual((f["passed"], f["refused"], f["awaiting"]), (0, 0, 1))

    def test_reading_is_allowed_where_only_training_is_refused(self):
        """Content-Signal is per purpose. This project reads; it does not train. ai-train=no is
        honoured and recorded, and does not by itself stop reading - conflating them would either
        lose sources we may use or use ones we may not."""
        d, _ = self.build([cap("S1", allowed_for_us=True,
                               content_signal={"https://x/": {"ai-train": "no"}})], ["S1"])
        self.assertEqual(self.figures(d)["passed"], 1)
        d2, _ = self.build([cap("S2", allowed_for_us=True,
                                content_signal={"https://x/": {"ai-input": "no"}})], ["S2"])
        self.assertEqual(self.figures(d2)["refused"], 1)

    def test_the_newest_capture_decides_and_the_older_ones_are_kept(self):
        d, txt = self.build([cap("S1", at="2026-09-01T00:00:00Z", allowed_for_us=True),
                             cap("S1", at="2026-09-05T00:00:00Z", allowed_for_us=False)], ["S1"])
        f = self.figures(d)
        self.assertEqual(f["refused"], 1, "the older capture decided")
        self.assertEqual(f["captures"], 2, "an older capture was dropped from the count")

    def test_a_source_with_no_capture_is_listed_rather_than_hidden(self):
        d, txt = self.build([cap("S1", allowed_for_us=True)], ["S1", "S2", "S3"])
        f = self.figures(d)
        self.assertEqual(f["undocumented"], 2)
        self.assertIn("S2", txt)

    # ---------------------------------------------------------------- the interface to the paper

    def test_the_figures_the_paper_prints_are_the_rows_the_index_holds(self):
        """No second copy of a number, across a text interface between two programs. If the header
        sentence is ever reworded so a regex stops matching, the paper prints None and this fails."""
        led = [cap("S1", allowed_for_us=True), cap("S2", allowed_for_us=True),
               cap("S3", allowed_for_us=False), cap("S4", capture_ok=False, allowed_for_us=True),
               cap("S5", allowed_for_us=True, manual_verdict="needs_decision"),
               cap("S1", at="2026-09-02T00:00:00Z", allowed_for_us=True)]
        d, txt = self.build(led, ["S1", "S2", "S3", "S4", "S5", "S6", "S7"])
        f = self.figures(d)
        self.assertEqual(f["captures"], 6)
        self.assertEqual(f["sources_with_evidence"], 5)
        self.assertEqual(f["passed"], 2)
        self.assertEqual(f["refused"], 1)
        self.assertEqual(f["awaiting"], 1)
        self.assertEqual(f["incomplete"], 1)
        self.assertEqual(f["undocumented"], 2)
        for k, v in f.items():
            if k != "generated":
                self.assertIsNotNone(v, f"the figure tool could not read {k} out of the index")

    def test_the_four_verdicts_partition_the_sources_with_evidence(self):
        led = [cap("S%d" % i, allowed_for_us=(i % 3 == 0), capture_ok=(i % 4 != 0)) for i in range(1, 13)]
        d, _ = self.build(led, ["S%d" % i for i in range(1, 13)])
        f = self.figures(d)
        self.assertEqual(f["passed"] + f["refused"] + f["awaiting"] + f["incomplete"],
                         f["sources_with_evidence"],
                         "a source with evidence is in two categories or in none")

    def test_one_ledger_line_without_a_name_does_not_take_down_the_whole_index(self):
        """It used to read entry['name'] directly, so a single line written without that key raised
        and the file the paper's permission figures come from was not generated at all."""
        e = cap("S1", allowed_for_us=False)
        del e["name"]
        d, txt = self.build([e], ["S1"])
        self.assertEqual(self.figures(d)["refused"], 1)
        self.assertIn("S1", txt)

    def test_where_a_name_is_nowhere_the_row_says_so_rather_than_going_blank(self):
        self.assertEqual(B.name_of("S1", {}, {}), "(name not recorded in the capture)")
        self.assertEqual(B.name_of("S1", {"name": "From the capture"}, {"S1": {"name": "From the registry"}}),
                         "From the capture")
        self.assertEqual(B.name_of("S1", {}, {"S1": {"name": "From the registry"}}), "From the registry")
        self.assertEqual(B.name_of("S1", {}, {"S1": {"title": "A title"}}), "A title")

    def test_a_name_missing_from_the_capture_is_taken_from_the_registry(self):
        e = cap("S1", allowed_for_us=True)
        del e["name"]
        d = pathlib.Path(tempfile.mkdtemp())
        (d / "research" / "08-provenance").mkdir(parents=True)
        (d / "research" / "08-provenance" / "LEDGER.jsonl").write_text(json.dumps(e), encoding="utf-8")
        (d / "research" / "SOURCE_REGISTRY.json").write_text(
            json.dumps({"sources": [{"id": "S1", "name": "RHMZ automatic stations"}]}), encoding="utf-8")
        old = (B.ROOT, B.LEDGER, B.REGISTRY, B.OUT)
        B.ROOT, B.LEDGER = str(d), str(d / "research" / "08-provenance" / "LEDGER.jsonl")
        B.REGISTRY, B.OUT = str(d / "research" / "SOURCE_REGISTRY.json"), str(d / "research" / "08-provenance" / "INDEX.md")
        try:
            B.main()
            txt = (d / "research" / "08-provenance" / "INDEX.md").read_text(encoding="utf-8")
        finally:
            B.ROOT, B.LEDGER, B.REGISTRY, B.OUT = old
        self.assertIn("RHMZ automatic stations", txt)

    def test_the_index_says_it_is_generated_and_must_not_be_edited(self):
        d, txt = self.build([cap("S1", allowed_for_us=True)], ["S1"])
        self.assertIn("GENERATED by tools/build_provenance_index.py", txt)
        self.assertIn("Do not edit by hand", txt)

    def test_an_empty_ledger_produces_an_index_that_claims_nothing(self):
        d, txt = self.build([], ["S1", "S2"])
        f = self.figures(d)
        self.assertEqual((f["captures"], f["passed"], f["refused"]), (0, 0, 0))
        self.assertEqual(f["undocumented"], 2)


if __name__ == "__main__":
    unittest.main()
