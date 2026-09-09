#!/usr/bin/env python3
"""
collect_putevi_aadt.py — S134 · JP "Putevi Srbije" annual AADT (PGDS) per road section.

What this is
    Serbia's road authority publishes, for each year and each state-road
    category (IA, IB, IIA, IIB), a table of Average Annual Daily Traffic per
    road section: passenger cars, buses, and five goods-vehicle classes, plus
    the section's length in kilometres.

Why it matters to BEOPS
    The last column, "Remark", labels HOW each row was arrived at:

        ATC <n>/<n>   a named automatic traffic counter stood on that section
        TS / TS <n>   a counting station / survey sample
        INT           interpolated between neighbouring sections

    The publisher states its own provenance, row by row. BEOPS does not have to
    impose the observed/estimated distinction on this source — the source
    already carries it, and our job is only to preserve it instead of
    flattening every row into one number.

Permission
    Documented in research/08-provenance/ as S134: no robots.txt is served
    (HTTP 404 — RFC 9309: no restrictions stated), no opt-out signal header on
    any probed URL, HTTP 200 on the files themselves. See EDGE_CASES.md E-003
    on why the absence of a stated reuse licence is not a grant, and what we
    therefore do and do not do with these figures.

Manners
    Sequential, one request at a time, with a delay between them, an honest
    user-agent, and no retry storm. 86 files fetched once are 86 requests; this
    is not a recurring collector and must never become one without revisiting
    EDGE_CASES.md E-004.

Usage
    python -B research/collect_putevi_aadt.py download   # raw files + manifest
    python -B research/collect_putevi_aadt.py parse      # tidy CSV (needs xlrd)
"""
from __future__ import annotations

import hashlib
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

SID = "S134"
UA = "Beops-Research-Collect/1.0 (urban observatory research; identifies honestly)"
BASE = "https://www.putevi-srbije.rs/images/pdf/brojanje/{year}/DP-{cat}-PGDS-{year}{suffix}.xls"
YEARS = range(2018, 2025)
CATS = ("IA", "IB", "IIA", "IIB")
SUFFIXES = ("", "-eng")
DELAY_S = 1.5

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "research", "evidence", "putevi-aadt")


def _ctx() -> ssl.SSLContext:
    try:
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:
        pass
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


CTX = _ctx()


def utcstamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def download() -> int:
    stamp = utcstamp()
    outdir = os.path.join(RAW, stamp)
    os.makedirs(outdir, exist_ok=True)
    manifest = {"sid": SID, "collected_at_utc": stamp, "user_agent": UA,
                "delay_seconds": DELAY_S, "files": [], "absent": []}

    for year in YEARS:
        for cat in CATS:
            for suffix in SUFFIXES:
                url = BASE.format(year=year, cat=cat, suffix=suffix)
                name = url.rsplit("/", 1)[-1]
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                try:
                    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
                        body = r.read()
                        hdrs = dict(r.headers.items())
                    path = os.path.join(outdir, f"{year}_{name}")
                    with open(path, "wb") as fh:
                        fh.write(body)
                    manifest["files"].append({
                        "url": url, "file": os.path.basename(path),
                        "year": year, "category": cat,
                        "language": "en" if suffix == "-eng" else "sr",
                        "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                        "last_modified": hdrs.get("Last-Modified"),
                        "fetched_at_utc": utcstamp(),
                    })
                    print(f"  ok   {year} {cat:4s} {suffix or 'sr ':4s} {len(body):>8} B")
                except urllib.error.HTTPError as e:
                    manifest["absent"].append({"url": url, "status": e.code})
                    print(f"  --   {year} {cat:4s} {suffix or 'sr ':4s} HTTP {e.code}")
                except Exception as e:
                    manifest["absent"].append({"url": url, "error": f"{type(e).__name__}: {e}"})
                    print(f"  ERR  {year} {cat:4s} {suffix or 'sr ':4s} {e}")
                time.sleep(DELAY_S)

    with open(os.path.join(outdir, "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    print(f"\n{len(manifest['files'])} files stored, {len(manifest['absent'])} absent")
    print(f"-> {os.path.relpath(outdir, ROOT)}")
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("download", "parse"):
        print(__doc__)
        return 2
    if sys.argv[1] == "download":
        return download()
    from putevi_parse import parse_all  # kept separate: parsing needs xlrd
    return parse_all(RAW, ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
