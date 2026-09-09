#!/usr/bin/env python3
"""The second reader's sheet must not tell them the answer, and the arithmetic that scores it must be
the arithmetic it claims to be."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

import gate_agreement as G  # noqa: E402


class SheetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = G.load()
        cls.text = G.write_sheet(cls.data).read_text(encoding="utf-8")

    def test_every_item_has_a_blank_to_fill(self):
        for it in self.data["items"]:
            self.assertIn(f"`{it['id']}:`", self.text, it["id"] + " has no blank")

    def test_the_sheet_carries_no_label_and_no_family(self):
        for it in self.data["items"]:
            self.assertNotIn(it["family"], self.text, "the family name gives the answer away: " + it["family"])
            self.assertNotIn(it["why"][:40], self.text, "the first reader's reasoning leaked into the sheet")

    def test_the_digest_is_there_or_the_reader_cannot_judge(self):
        for f in self.data["digest"]["facts"]:
            self.assertIn(f["id"], self.text)
            self.assertIn(f["en"][:40], self.text)

    def test_a_filled_sheet_reads_back(self):
        filled = self.text
        for it in self.data["items"]:
            filled = filled.replace(f"`{it['id']}:` ", f"`{it['id']}:` {it['should']}")
        back = G.read_sheet_text(filled) if hasattr(G, "read_sheet_text") else None
        if back is None:
            tmp = ROOT / "research" / "_agreement_roundtrip.tmp.md"
            tmp.write_text(filled, encoding="utf-8")
            try:
                back = G.read_sheet(tmp)
            finally:
                tmp.unlink()
        self.assertEqual(len(back), len(self.data["items"]))
        self.assertEqual(back["A01"], next(i["should"] for i in self.data["items"] if i["id"] == "A01"))

    def test_kappa_behaves(self):
        same = [("accept", "accept")] * 8 + [("reject", "reject")] * 36
        self.assertEqual(G.kappa(same), 1.0)
        mixed = [("accept", "reject")] * 4 + [("accept", "accept")] * 4 + [("reject", "reject")] * 36
        k = G.kappa(mixed)
        self.assertTrue(0 < k < 1, k)
        self.assertIsNone(G.kappa([]))

    def test_scoring_names_every_disagreement(self):
        second = {it["id"]: it["should"] for it in self.data["items"]}
        second["A21"] = "accept" if second["A21"] == "reject" else "reject"
        out = G.score(self.data, second)
        self.assertIn("A21", out)
        self.assertIn("WHERE THEY DISAGREE", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
