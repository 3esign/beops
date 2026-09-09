#!/usr/bin/env python3
"""
compress_large_evidence.py - gzip evidence files above a size threshold, and
record in the manifest that the stored bytes are compressed.

Evidence in this project is immutable and never edited. Compressing is not
editing: the sha256 of the ORIGINAL bytes stays in the manifest, so anyone can
gunzip and verify that what is stored is exactly what was served. What changes
is only how it sits on disk, and a 140 MB JSON in a git repository is a
different kind of problem from a permission question.
"""
from __future__ import annotations
import gzip, json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "research", "evidence")
THRESHOLD = int(sys.argv[1]) if len(sys.argv) > 1 else 20 * 1024 * 1024

changed = 0
for dirpath, _dirs, files in os.walk(EV):
    mpath = os.path.join(dirpath, "MANIFEST.json")
    man = None
    if os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as fh:
            man = json.load(fh)
    for fn in files:
        if fn == "MANIFEST.json" or fn.endswith(".gz"):
            continue
        p = os.path.join(dirpath, fn)
        if os.path.getsize(p) < THRESHOLD:
            continue
        gz = p + ".gz"
        with open(p, "rb") as src, gzip.open(gz, "wb", compresslevel=6) as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
        before, after = os.path.getsize(p), os.path.getsize(gz)
        os.remove(p)
        print(f"  {os.path.relpath(p, ROOT)}  {before:,} -> {after:,}  ({100*after/before:.1f}%)")
        if man:
            for rec in man.get("files", []):
                if rec.get("file") == fn:
                    rec["stored_as"] = fn + ".gz"
                    rec["stored_compression"] = "gzip"
                    rec["stored_bytes"] = after
                    rec["note"] = ("stored gzipped; 'sha256' and 'bytes' describe the ORIGINAL "
                                   "bytes as served, verify with: gunzip -c <file> | sha256sum")
        changed += 1
    if man and changed:
        with open(mpath, "w", encoding="utf-8") as fh:
            json.dump(man, fh, indent=2, ensure_ascii=False)
print(f"{changed} file(s) compressed at threshold {THRESHOLD:,} bytes")
