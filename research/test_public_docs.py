#!/usr/bin/env python3
"""What reaches the public site is a decision, not a side effect.

C-018: a copy rule written to stop a published paper going missing published two internal working
documents instead. The rule is still "a document reaches the site by existing" - this is the fence
around it.

C-019 is not about documents but sits behind the same failure: a fix written from the instances in
front of you is not a fix. C-020 is that lesson arriving with a bill. The C-018 fence was built from
the two filenames that had just leaked, so three more internal PDFs stayed public - including a
pre-paper, which the project's own publish notice names as internal in so many words. Two of the
three had no source file left at all: the build only ever copied, so nothing could take a document
back once it stopped being eligible. The last two tests here are the ones that would have failed.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
RESEARCH = ROOT / "research"
SOURCE_FOLDERS = ("06-paper", "07-legal")

# Categories, not instances. Anything whose NAME says what kind of document it is, and whose kind is
# internal by policy, is excluded - whether or not such a file exists today.
NOT_PUBLIC = ("WORKING_DOCUMENT", "PISMA", "LETTER", "INTERNAL", "DRAFT", "PRESEK",
              "PRE_PAPER", "PREPAPER", "PRED_RAD", "ANALYSIS", "AUDIT", "ATLAS",
              "STRUKTURA", "METODOLOGIJA", "SCRATCH", "NOTES")


def published_pdfs():
    return sorted(f.name for f in DOCS.glob("*.pdf"))


def eligible_sources():
    out = set()
    for folder in SOURCE_FOLDERS:
        for p in (RESEARCH / folder).glob("*.pdf"):
            if not any(k in p.name.upper() for k in NOT_PUBLIC):
                out.add(p.name)
    return out


class PublicDocsTests(unittest.TestCase):
    def test_no_internal_document_is_published(self):
        leaked = [n for n in published_pdfs() if any(k in n.upper() for k in NOT_PUBLIC)]
        self.assertEqual(leaked, [], "internal documents on the public site: " + ", ".join(leaked))

    def test_the_builder_still_carries_the_fence(self):
        src = (ROOT / "tools" / "build_site.py").read_text(encoding="utf-8")
        self.assertIn("NOT_PUBLIC", src, "the exclusion was removed from build_site.py")
        for k in NOT_PUBLIC:
            self.assertIn(k, src, f"{k} is no longer excluded by the builder")

    def test_the_paper_itself_is_published(self):
        """The fence must not swallow what it was built to protect."""
        names = set(published_pdfs())
        self.assertTrue(any(n.startswith("PAPER_v1") for n in names),
                        "the paper is not on the site: " + ", ".join(sorted(names)))

    def test_nothing_is_published_without_a_source_that_is_still_eligible(self):
        """C-020's second half. Two of the three leaked PDFs had no source file left in research/ at
        all: they were published by a build that has since changed its mind, and no later build could
        take them back. Publication has to be a property recomputed every time, not a state that
        accumulates."""
        orphans = sorted(set(published_pdfs()) - eligible_sources())
        self.assertEqual(orphans, [],
                         "published with no eligible source in research/: " + ", ".join(orphans))

    def test_the_builder_can_withdraw_and_not_only_publish(self):
        src = (ROOT / "tools" / "build_site.py").read_text(encoding="utf-8")
        self.assertIn("withdrew docs/", src,
                      "build_site.py no longer withdraws PDFs that stopped being eligible")


if __name__ == "__main__":
    unittest.main(verbosity=2)
