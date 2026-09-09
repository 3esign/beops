#!/usr/bin/env python3
"""What reaches the public site is a decision, not a side effect.

C-018: a copy rule written to stop a published paper going missing published two internal working
documents instead. The rule is still "a document reaches the site by existing" - this is the fence
around it.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
NOT_PUBLIC = ("WORKING_DOCUMENT", "PISMA", "LETTER", "INTERNAL", "DRAFT", "PRESEK")


class PublicDocsTests(unittest.TestCase):
    def test_no_internal_document_is_published(self):
        leaked = sorted(f.name for f in DOCS.glob("*.pdf")
                        if any(k in f.name.upper() for k in NOT_PUBLIC))
        self.assertEqual(leaked, [], "internal documents on the public site: " + ", ".join(leaked))

    def test_the_builder_still_carries_the_fence(self):
        src = (ROOT / "tools" / "build_site.py").read_text(encoding="utf-8")
        self.assertIn("NOT_PUBLIC", src, "the exclusion was removed from build_site.py")
        for k in NOT_PUBLIC:
            self.assertIn(k, src, f"{k} is no longer excluded by the builder")

    def test_the_paper_itself_is_published(self):
        """The fence must not swallow what it was built to protect."""
        names = {f.name for f in DOCS.glob("*.pdf")}
        self.assertTrue(any(n.startswith("PAPER_v1") for n in names),
                        "the paper is not on the site: " + ", ".join(sorted(names)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
