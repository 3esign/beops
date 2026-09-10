#!/usr/bin/env python3
"""compress_large_evidence.py - gzip evidence files above a size threshold, and record in the
manifest that the stored bytes are compressed.

Evidence in this project is immutable and never edited. Compressing is not editing: the sha256 of the
ORIGINAL bytes stays in the manifest, so anyone can gunzip and verify that what is stored is exactly
what was served. What changes is only how it sits on disk, and a 140 MB JSON in a git repository is a
different kind of problem from a permission question.

    python -B tools/compress_large_evidence.py            compress above 20 MB
    python -B tools/compress_large_evidence.py 5000000    compress above 5 MB
    python -B tools/compress_large_evidence.py --dry-run  say what would be compressed, touch nothing

**Three defects were fixed here on 2026-09-10, all of them in the direction of losing evidence.**

1. The original was deleted before anything read the compressed copy back. A gzip written to a full
   disk, or interrupted, would have left the only copy of a captured page destroyed and a manifest
   pointing at a file that no longer exists. The copy is now decompressed and hashed, and must match
   the original byte for byte, before the original is removed.
2. The manifest was rewritten in every directory that had one, whenever ANY directory had compressed
   something, because the counter was global. An evidence manifest was being rewritten to say exactly
   what it already said - which is a modification to an immutable record for no reason.
3. It was top-level code with no function, so it could not be imported, tested, or asked what it
   would do without doing it. That is why it had no test.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EV = ROOT / "research" / "evidence"
DEFAULT_THRESHOLD = 20 * 1024 * 1024


def sha256_of(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_gz(path: pathlib.Path) -> str:
    """The hash of what comes back OUT of the archive. This is the number that decides whether the
    original may be deleted."""
    h = hashlib.sha256()
    with gzip.open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compress_file(path: pathlib.Path) -> tuple[str, int, int]:
    """Write path.gz, verify it decompresses to exactly the original bytes, then remove the original.

    Returns (sha256 of the original, bytes before, bytes after). Raises if the round trip does not
    match, leaving BOTH files on disk, because a failed compression must never cost the evidence.
    """
    gz = path.with_name(path.name + ".gz")
    before = path.stat().st_size
    digest = sha256_of(path)
    with open(path, "rb") as src, gzip.open(gz, "wb", compresslevel=6) as dst:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            dst.write(chunk)
    back = sha256_of_gz(gz)
    if back != digest:
        raise OSError("gzip round trip does not match for %s: %s != %s (original kept, archive kept)"
                      % (path.name, back, digest))
    after = gz.stat().st_size
    os.remove(path)
    return digest, before, after


def update_manifest(man: dict, filename: str, digest: str, after: int) -> bool:
    """Record in the manifest that the bytes are stored compressed. Returns whether anything changed.

    The manifest keeps the sha256 and length of the ORIGINAL, because that is what was served and
    what a reader verifies against. Only how it sits on disk is new information.
    """
    touched = False
    for rec in man.get("files", []):
        if rec.get("file") != filename or rec.get("stored_compression") == "gzip":
            continue
        rec["stored_as"] = filename + ".gz"
        rec["stored_compression"] = "gzip"
        rec["stored_bytes"] = after
        rec["stored_sha256_verified"] = digest
        rec["note"] = ("stored gzipped; 'sha256' and 'bytes' describe the ORIGINAL bytes as served, "
                       "verified by decompressing before the original was removed; check with: "
                       "gunzip -c <file> | sha256sum")
        touched = True
    return touched


def run(root: pathlib.Path = None, threshold: int = DEFAULT_THRESHOLD, dry_run: bool = False) -> dict:
    root = pathlib.Path(root or EV)
    done, skipped, failed = [], [], []
    if not root.exists():
        return {"compressed": done, "too_small": skipped, "failed": failed, "manifests_written": []}
    written = []
    for dirpath, _dirs, files in os.walk(root):
        d = pathlib.Path(dirpath)
        mpath = d / "MANIFEST.json"
        man = None
        if mpath.exists():
            try:
                man = json.loads(mpath.read_text(encoding="utf-8"))
            except ValueError:
                man = None
        dirty = False                       # per directory, not per run: see defect 2 in the header
        for fn in sorted(files):
            if fn == "MANIFEST.json" or fn.endswith(".gz"):
                continue
            p = d / fn
            if p.stat().st_size < threshold:
                skipped.append(str(p))
                continue
            if dry_run:
                done.append(str(p))
                continue
            try:
                digest, before, after = compress_file(p)
            except OSError as e:
                failed.append("%s: %s" % (p, e))
                continue
            done.append(str(p))
            print("  %s  %s -> %s  (%.1f%%)" % (p.relative_to(ROOT) if str(p).startswith(str(ROOT)) else p,
                                                f"{before:,}", f"{after:,}", 100 * after / before))
            if man and update_manifest(man, fn, digest, after):
                dirty = True
        if man is not None and dirty and not dry_run:
            mpath.write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
            written.append(str(mpath))
    return {"compressed": done, "too_small": skipped, "failed": failed, "manifests_written": written}


def main(argv: list) -> int:
    dry = "--dry-run" in argv
    nums = [a for a in argv if a.isdigit()]
    threshold = int(nums[0]) if nums else DEFAULT_THRESHOLD
    r = run(threshold=threshold, dry_run=dry)
    print("%d file(s) %s at threshold %s bytes; %d manifest(s) written"
          % (len(r["compressed"]), "would be compressed" if dry else "compressed",
             f"{threshold:,}", len(r["manifests_written"])))
    for f in r["failed"]:
        print("  FAILED, both copies kept: " + f)
    return 1 if r["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
