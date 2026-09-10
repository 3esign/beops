#!/usr/bin/env python3
"""
capture_backlog.py - clear the permission-capture backlog.

The registry holds many sources that are not refused, not restricted and not
absent - they simply have no stored permission capture, and this project's own
rule forbids collecting without one. That backlog is ours, not anyone else's,
and it is the largest single category in the registry.

This walks every source that has no capture yet and is not already known to be
unavailable, and runs tools/legal_capture.py against its registered URL,
sequentially, with a delay. It does not collect anything: it only reads
robots.txt, the response headers and the terms page, and stores them.

Sources whose status already records an obstacle - opted_out, no_coverage,
dead, needs_decision, token_required, restricted, account_required, blocked -
are skipped, because their reason is already on the record.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "research", "SOURCE_REGISTRY.json")
LEDGER = os.path.join(ROOT, "research", "08-provenance", "LEDGER.jsonl")
WALL = {"opted_out", "no_coverage", "dead", "needs_decision",
        "token_required", "restricted", "account_required", "blocked"}
DELAY = 1.0


def captured() -> set:
    out = set()
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    out.add(json.loads(line)["sid"])
    return out


def targets(sources: list, done: set) -> list:
    """Which sources this tool may approach, separated from the approaching.

    It was written inside main(), wrapped around a subprocess loop that talks to the network, so the
    one decision that matters here - **who gets asked** - could not be tested without asking them.
    A refuser must never appear in this list, and that is now a test rather than a reading of the
    code (C-062).
    """
    return [r for r in sources
            if r.get("id") not in done
            and r.get("status") not in WALL
            and (r.get("url") or "").startswith("http")]


def main() -> int:
    python = sys.argv[1] if len(sys.argv) > 1 else sys.executable
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    with open(REG, encoding="utf-8") as fh:
        reg = json.load(fh)
    done = captured()
    todo = targets(reg["sources"], done)
    print(f"{len(todo)} sources to capture (of {len(reg['sources'])} in the registry)\n")
    ok = fail = 0
    for i, r in enumerate(todo[:limit], 1):
        cmd = [python, "-B", "tools/legal_capture.py", "--sid", r["id"],
               "--name", (r.get("name") or r["id"])[:120], "--url", r["url"],
               "--note", "backlog capture " + (r.get("status") or ""),
               "--allow-shared-host"]
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180)
            try:
                e = json.loads(p.stdout)
                v = e.get("allowed_for_us")
                mark = {True: "allow", False: "REFUSE", None: "unknown"}[v]
                print(f"{i:4d}/{len(todo)}  {r['id']:6s} {mark:8s} {(r.get('name') or '')[:52]}")
                ok += 1
            except Exception:
                print(f"{i:4d}/{len(todo)}  {r['id']:6s} {'noparse':8s} "
                      f"{(p.stdout or p.stderr or '')[:70].strip()}")
                fail += 1
        except subprocess.TimeoutExpired:
            print(f"{i:4d}/{len(todo)}  {r['id']:6s} {'timeout':8s}")
            fail += 1
        time.sleep(DELAY)
    print(f"\n{ok} captured, {fail} failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
