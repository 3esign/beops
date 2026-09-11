#!/usr/bin/env python3
"""The research index must name every Markdown document it claims to govern."""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
INDEX = ROOT / "README.md"


class ResearchIndex(unittest.TestCase):
    def test_every_research_markdown_file_is_named_in_the_index(self):
        index = INDEX.read_text(encoding="utf-8")
        missing = []
        result = subprocess.run(["git", "ls-files", "research"], cwd=ROOT.parent,
                                text=True, capture_output=True, check=True)
        tracked = sorted(line for line in result.stdout.splitlines()
                         if line.startswith("research/") and line.endswith(".md"))
        for rel_from_repo in tracked:
            rel = rel_from_repo.removeprefix("research/")
            if rel == "README.md" or "/_scratch/" in f"/{rel}":
                continue
            if rel not in index:
                missing.append(rel)
        self.assertEqual(missing, [], "research Markdown files missing from research/README.md: "
                         + ", ".join(missing))


if __name__ == "__main__":
    unittest.main()
