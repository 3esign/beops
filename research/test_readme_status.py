#!/usr/bin/env python3
"""The two README files must not become a stale front door again."""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
RESEARCH_README = ROOT / "research" / "README.md"
UPUTSTVO = ROOT / "UPUTSTVO.md"


class ReadmeStatus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.top = README.read_text(encoding="utf-8")
        cls.research = RESEARCH_README.read_text(encoding="utf-8")
        cls.uputstvo = UPUTSTVO.read_text(encoding="utf-8")
        cls.registry = json.loads((ROOT / "research" / "SOURCE_REGISTRY.json").read_text(encoding="utf-8"))
        cls.source_count = len(cls.registry["sources"])

    def test_top_readme_describes_the_live_system(self):
        self.assertIn("Status: active research instrument", self.top)
        self.assertIn("STRUCTURE_CONTRACT_2026-09-11.md", self.top)
        self.assertIn("OPERATIONAL_ORDER_2026-09-11.md", self.top)
        self.assertIn("https://github.com/3esign/beops", self.top)
        self.assertNotIn("No public deployment or conference submission has occurred.", self.top)
        self.assertNotIn("Interface development is paused", self.top)
        self.assertNotIn("Claude Fable", self.top)

    def test_top_readme_source_count_matches_the_registry(self):
        self.assertIn(f"{self.source_count} source records", self.top)
        stale_counts = re.findall(r"\b(?:189|191) source records\b", self.top)
        self.assertEqual(stale_counts, [])

    def test_research_readme_points_to_the_current_paper_line(self):
        self.assertIn("06-paper/PRE_PAPER_v5_2026-09-10.md", self.research)
        self.assertIn("STABILITY_REVIEW_2026-09-10.md", self.research)
        self.assertNotRegex(self.research, r"Serbian pre-paper V2.*current discussion entry")

    def test_uputstvo_is_not_the_old_paused_interface_map(self):
        self.assertIn("https://3esign.github.io/beops/", self.uputstvo)
        self.assertIn("STRUCTURE_CONTRACT_2026-09-11.md", self.uputstvo)
        self.assertNotIn("UI je odlozen", self.uputstvo)
        self.assertNotIn("neaktivni i neverifikovani nacrti", self.uputstvo)


if __name__ == "__main__":
    unittest.main()
