#!/usr/bin/env python3
"""The project structure contract says what is source, generated, live, private and public."""
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "research" / "STRUCTURE_CONTRACT.json"
DOC = ROOT / "research" / "STRUCTURE_CONTRACT_2026-09-11.md"
PUBLISH = ROOT / "tools" / "publish_github.ps1"
IGNORE = ROOT / ".gitignore"


def tracked():
    p = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True)
    return [line for line in p.stdout.splitlines() if line]


class StructureContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.ignore = IGNORE.read_text(encoding="utf-8")
        cls.publish = PUBLISH.read_text(encoding="utf-8")

    def test_the_public_site_is_the_named_surface(self):
        self.assertEqual(self.contract["public_surface"]["url"], "https://3esign.github.io/beops/")
        self.assertIn("Public surface: https://3esign.github.io/beops/", DOC.read_text(encoding="utf-8"))

    def test_every_tracked_root_path_is_declared(self):
        root_files = set(self.contract["root_files"])
        root_dirs = set(self.contract["root_dirs"])
        unknown = []
        for rel in tracked():
            first = rel.split("/", 1)[0]
            if "/" not in rel and rel not in root_files:
                unknown.append(rel)
            elif "/" in rel and first not in root_dirs:
                unknown.append(rel)
        self.assertEqual(unknown, [], "tracked root paths outside the contract: " + ", ".join(unknown))

    def test_generated_public_patterns_are_ignored_and_have_a_publish_route(self):
        for item in self.contract["generated_public_ignored"]:
            pattern = item["pattern"]
            base = pattern.replace("/**", "/").replace("REPORT_*.md", "REPORT_*.md")
            self.assertIn(base, self.ignore, f"{pattern} is generated but not ignored")
            self.assertIn("writer", item)
            self.assertIn("published_by", item)

    def test_generated_private_patterns_are_ignored(self):
        for item in self.contract["generated_private_ignored"]:
            self.assertIn(item["pattern"], self.ignore)
            self.assertIn("writer", item)

    def test_publisher_copies_generated_public_outputs_explicitly(self):
        for rel in self.contract["public_export_extra"]:
            self.assertIn(rel, self.publish, f"{rel} is ignored in source but not copied by publisher")

    def test_current_entry_points_exist_and_are_tracked(self):
        files = set(tracked())
        for rel in self.contract["current_entry_points"]:
            self.assertIn(rel, files, f"{rel} is a current entry point but not tracked")


if __name__ == "__main__":
    unittest.main()
