#!/usr/bin/env python3
"""test_prose.py - the difference between quoting a thing and claiming it.

Two tools read a document looking for a time it states about itself. Both were confused by a document
that QUOTES such a time as an example of the format it is abolishing. The first was fixed in place;
the second was written afterwards without the fix, because the fix was a line in a file rather than a
function anywhere. The publish gate refused a correct pre-paper for quoting an incorrect ledger.
"""
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import correction_times as ct  # noqa: E402
import paper_stamps as ps  # noqa: E402
import prose  # noqa: E402

STAMP = re.compile(r"(\d{4}-\d\d-\d\d)[ ,]+(\d\d:\d\d)(?::\d\d)?\s*UTC")


class Claims(unittest.TestCase):
    def test_a_stamp_in_backticks_is_quoted_not_claimed(self):
        self.assertIsNone(STAMP.search(prose.claims("of the form `**2026-09-10, 15:40 UTC.**` and wrong")))

    def test_a_stamp_in_quotation_marks_is_quoted_not_claimed(self):
        """The shape that broke the second tool: pre-paper v5 quotes the format in italics and
        quotation marks rather than in a code span."""
        line = 'carried a hand-typed line of the form *"2026-09-10, 15:40 UTC."* and ten were wrong'
        self.assertIsNone(STAMP.search(prose.claims(line)))

    def test_a_stamp_in_the_documents_own_voice_is_still_read(self):
        for line in ("**2026-09-10, 15:40 UTC.** Found by a sweep",
                     "*Figures taken 2026-09-10 14:00 UTC by the figure tool.*"):
            self.assertIsNotNone(STAMP.search(prose.claims(line)), line)

    def test_blanking_keeps_the_line_the_same_length(self):
        """So a caller that reports a column is still right about where it was looking."""
        line = 'x `2026-09-10, 15:40 UTC` y "quoted" z'
        self.assertEqual(len(prose.claims(line)), len(line))

    def test_both_tools_use_the_one_rule_and_not_their_own_copy(self):
        """The actual correction. If either grows its own copy again, the next tool written will be
        the one without it."""
        self.assertIs(ct.CODE_SPAN, prose.CODE_SPAN)
        self.assertIs(ps.CODE_SPAN, prose.CODE_SPAN)
        for src in (ROOT / "tools" / "correction_times.py", ROOT / "tools" / "paper_stamps.py"):
            body = src.read_text(encoding="utf-8")
            self.assertNotIn('re.compile(r"`[^`]*`")', body,
                             f"{src.name} has its own copy of the quotation rule again")


if __name__ == "__main__":
    unittest.main()
