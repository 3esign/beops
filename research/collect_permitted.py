#!/usr/bin/env python3
"""
collect_permitted.py - fetch and store, once, everything the provenance ledger
says we may have.

The gate, and it is not advisory
--------------------------------
Before a single request, this reads research/08-provenance/LEDGER.jsonl and
takes the NEWEST capture for each source. A source is collectable only if that
capture says allowed_for_us is true AND capture_ok is true. Anything else -
refused, undecided, evidence incomplete, or never captured at all - is skipped
with the reason printed. There is no flag to override it.

That is the same rule as CONTRIBUTING.md section 10, moved from a document into
the code that would otherwise break it.

What one collection stores
--------------------------
  research/evidence/<SID>/<UTC>/<filename>   the bytes exactly as served
  research/evidence/<SID>/<UTC>/MANIFEST.json
      sha256, byte length, HTTP status, response headers, the URL, and the
      UTC time of each fetch, plus the ledger capture this run was gated on

Manners
-------
Sequential. One request at a time. A delay between them. An honest user-agent.
Once - this is not a recurring collector, and turning it into one requires
research/08-provenance/EDGE_CASES.md E-004 to be revisited first.

Usage
    python -B research/collect_permitted.py --plan research/COLLECTION_PLAN.json
    python -B research/collect_permitted.py --plan ... --only S146,S157
    python -B research/collect_permitted.py --plan ... --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = "policy: wildcard; request headers supplied by incognito"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "research", "08-provenance", "LEDGER.jsonl")
EVIDENCE = os.path.join(ROOT, "research", "evidence")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import permission_policy
import transport

DELAY_S = 1.5
MAX_BYTES = 250 * 1024 * 1024


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


def gate() -> dict:
    return permission_policy.latest(LEDGER)


def may_collect(sid: str, latest: dict, url=None, now=None) -> tuple[bool, str]:
    return permission_policy.authorize(sid, latest, ROOT, url, now)


def fetch(url: str, timeout: int = 120):
    res = transport.fetch(url, timeout, MAX_BYTES)
    return res["status"], res["headers"], res["body"], res["error"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    with open(a.plan, encoding="utf-8") as fh:
        plan = json.load(fh)
    only = {s.strip() for s in a.only.split(",") if s.strip()}
    latest = gate()
    stamp = utcstamp()

    by_sid: dict = {}
    for item in plan["items"]:
        by_sid.setdefault(item["sid"], []).append(item)

    ok_files = skipped = failed = 0
    for sid in sorted(by_sid, key=lambda s: int("".join(c for c in s if c.isdigit()) or 0)):
        if only and sid not in only:
            continue
        allowed, why = permission_policy.access_state(latest.get(sid))
        if not allowed:
            print(f"\n[SKIP] {sid}  {why}")
            skipped += len(by_sid[sid])
            continue
        items = by_sid[sid]
        print(f"\n[{sid}] {items[0].get('name','')[:60]}  ({len(items)} file(s))  {why}")
        outdir = os.path.join(EVIDENCE, sid, stamp)
        manifest = {"sid": sid, "collected_at_utc": stamp, "user_agent": UA,
                    "delay_seconds": DELAY_S, "gated_on_capture": latest[sid]["captured_at_utc"],
                    "gated_on_evidence": latest[sid]["evidence_dir"],
                    "files": [], "failed": []}
        if not a.dry_run:
            os.makedirs(outdir, exist_ok=False)
        for it in items:
            url, fn = it["url"], it["file"]
            if a.dry_run:
                print(f"    would fetch  {fn:44s} {url[:80]}")
                continue
            allowed, why = may_collect(sid, latest, url)
            if not allowed:
                manifest["failed"].append({"url": url, "file": fn, "status": None, "error": why})
                skipped += 1
                continue
            st, hd, body, err = fetch(url)
            if body is None:
                manifest["failed"].append({"url": url, "file": fn, "status": st, "error": err})
                print(f"    ERR  {fn:44s} {err}")
                failed += 1
            else:
                with open(os.path.join(outdir, fn), "wb") as f:
                    f.write(body)
                manifest["files"].append({
                    "url": url, "file": fn, "status": st, "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "content_type": hd.get("Content-Type"),
                    "last_modified": hd.get("Last-Modified"),
                    "fetched_at_utc": utcstamp(),
                })
                print(f"    ok   {fn:44s} {len(body):>12,} B")
                ok_files += 1
            time.sleep(DELAY_S)
        if not a.dry_run:
            with open(os.path.join(outdir, "MANIFEST.json"), "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n{ok_files} files stored, {failed} failed, {skipped} skipped by the gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
