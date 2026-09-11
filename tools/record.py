#!/usr/bin/env python3
"""record.py - reading a record that has outgrown memory.

`data/live/rows` is 78 MB across 28 files, two of which are 41 MB and 31 MB, and every file grows
every ten minutes. Five tests read those files with `read_text().splitlines()`, which holds the whole
file and a list of every line in it at once - several hundred megabytes for one 41 MB file. On
2026-09-10, with 592 MB free on this machine, six tests died of `MemoryError` and the publish gate
refused a commit that was correct.

It failed closed, which is the right direction, but the lesson is the other one: **the gate can be
killed by the size of the record it guards, and it would have happened on its own within weeks.** A
gate that fails for reasons unrelated to correctness is a gate whose refusals stop meaning anything.

Everything here streams. Nothing holds a whole row file, and nothing holds a list of its lines.
"""
from __future__ import annotations

import json
import pathlib
from itertools import islice
from contracts import json_rows


def lines(path: pathlib.Path, errors: str = "replace"):
    """Every line of a file, one at a time. The file is never held whole."""
    with open(path, encoding="utf-8", errors=errors) as fh:
        for ln in fh:
            yield ln.rstrip("\n")


def count_lines(path: pathlib.Path, non_blank: bool = True) -> int:
    n = 0
    for ln in lines(path):
        if not non_blank or ln.strip():
            n += 1
    return n


def objects(path: pathlib.Path, limit: int | None = None):
    """Strict streaming read: corruption is reported with its line, never silently dropped."""
    it = json_rows(path)
    yield from (islice(it, limit) if limit is not None else it)


def files(root: pathlib.Path):
    """Every row file under a directory of per-source directories, in a stable order."""
    if not root.exists():
        return
    for d in sorted(root.iterdir()):
        if d.is_dir():
            for f in sorted(d.glob("*.jsonl")):
                yield d, f


def all_objects(root: pathlib.Path, limit_per_file: int | None = None):
    for _, f in files(root):
        yield from objects(f, limit_per_file)
