#!/usr/bin/env python3
"""The research index must name every Markdown document it claims to govern."""
import pathlib
import subprocess
import unittest
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
INDEX = ROOT / "README.md"


def governed_files(root):
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "research"], cwd=root,
                            text=True, capture_output=True, check=True)
    return sorted(line for line in result.stdout.splitlines()
                  if line.startswith("research/") and line.endswith(".md"))


class ResearchIndex(unittest.TestCase):
    def test_new_untracked_research_document_is_visible_before_commit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            subprocess.run(["git", "init", "--quiet", folder], check=True)
            (root/"research").mkdir()
            (root/"research/new-study.md").write_text("Untracked study", encoding="utf-8")
            self.assertIn("research/new-study.md", governed_files(root))

    def test_every_research_markdown_file_is_named_in_the_index(self):
        index = INDEX.read_text(encoding="utf-8")
        missing = []
        tracked = governed_files(ROOT.parent)
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
