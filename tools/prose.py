#!/usr/bin/env python3
"""prose.py - what a line of a document actually claims, as opposed to what it quotes.

A document that abolishes a format has to be able to print that format. Pre-paper v5 says, of the
corrections ledger, that thirteen entries "carried a hand-typed line of the form 2026-09-10, 15:40
UTC" - and two separate tools read that quotation as the document stating its own verification time.

The first time, in `correction_times.py`, the fix was one line: strip inline code spans before looking
for a stamp. It was written into that file. Four hours later `paper_stamps.py` was written without it,
because the fix lived in a file rather than in a function, and the publish gate refused a correct
document for quoting an incorrect one. **A rule that exists in one place is a rule the next tool will
not have.** This module is that one place.

What counts as quotation here: an inline code span (`like this`), and a run inside straight or
typographic double quotes. A verification stamp a document is making as its own claim is never inside
either - it is a plain sentence at the foot of a page.
"""
from __future__ import annotations

import re

CODE_SPAN = re.compile(r"`[^`]*`")
QUOTED = re.compile(r"\"[^\"\n]{0,400}\"|\u201c[^\u201d\n]{0,400}\u201d|\u201e[^\u201c\u201d\n]{0,400}[\u201c\u201d]")


def claims(line: str) -> str:
    """The part of a line the document is asserting in its own voice.

    Quotations are blanked rather than deleted, so character offsets stay usable and a caller that
    reports a column is still right about where in the line it was looking.
    """
    line = CODE_SPAN.sub(lambda m: " " * len(m.group(0)), line)
    line = QUOTED.sub(lambda m: " " * len(m.group(0)), line)
    return line


def quotes(line: str) -> list[str]:
    """Everything the line quotes, in order. The inverse of claims(), for a caller that wants to
    check what was quoted rather than ignore it."""
    return [m.group(0) for m in CODE_SPAN.finditer(line)] + [m.group(0) for m in QUOTED.finditer(line)]


FENCE = re.compile(r"^\s*(```|~~~)")


def outside_fences(text: str) -> str:
    """The document's own structure, with the contents of fenced code blocks blanked.

    Same rule as claims(), one level up. claims() asks what a LINE asserts as opposed to quotes;
    this asks what a DOCUMENT is as opposed to shows. A heading inside a fence is a document
    displaying a heading, not a document having one - and a tool that cannot tell the difference
    reads an example as structure.

    That is not hypothetical: the entry describing C-067 quoted the very heading whose shape had
    broken the site builder, and the builder - the one just fixed - parsed the quotation as a second
    copy of that entry (caught by the test written in the same commit, before anything was
    committed).

    Every character offset is preserved, so a caller can match against the result and slice the
    original text with the same indices.
    """
    out, inside = [], False
    for line in text.split("\n"):
        if FENCE.match(line):
            inside = not inside
            out.append(" " * len(line))
        else:
            out.append(" " * len(line) if inside else line)
    return "\n".join(out)
