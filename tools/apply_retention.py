#!/usr/bin/env python3
"""
apply_retention.py - enforce research/RETENTION.json, and write down what it erased.

    python -B tools/apply_retention.py                what is due today, changing nothing
    python -B tools/apply_retention.py --apply        do it, and append to the ledger

Every other file in this project is append-only: an observation is never edited, a correction is
appended beside it. This one is the exception, and the exception is the point. A retention rule that
cannot erase is a sentence in a document; erasure that leaves no trace is unauditable. So the row
survives with its times, its source, its link and its capture hash, the sentence inside it does not,
and data/live/retention-ledger.jsonl records - append-only, like everything else - which file was
touched, how many rows, under which rule, and the file's sha256 before and after. Anyone can verify
that nothing else in the file changed by checking that no other field moved; nobody can recover the
sentence, which is the intent.

Deletion of a raw capture (rule R2) is real deletion. The receipt that proves the fetch happened -
its time, its byte length, its sha256 - is not touched, so the chain of custody for every row that
came out of that capture survives the bytes it came from.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
POLICY = ROOT / "research" / "RETENTION.json"
LEDGER = "data/live/retention-ledger.jsonl"


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_time(s):
    if not isinstance(s, str) or not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except ValueError:
        return None


def row_age_time(row: dict):
    """The clock that decides retention is when the row entered OUR record, not when the world made
    it: reception is the only time we are the author of, and the only one a publisher cannot move."""
    return parse_time(row.get("receivedTime")) or parse_time(row.get("resultTime"))


def due(root: pathlib.Path, policy: dict, now: dt.datetime) -> dict:
    """What rules R1 and R2 have to say about the record as it stands. Reads only."""
    rules = {r["id"]: r for r in policy["rules"]}
    r1, r2 = rules["R1"], rules["R2"]
    cut1 = now - dt.timedelta(days=r1["keep_days"])
    cut2 = now - dt.timedelta(days=r2["keep_days"])
    plan = {"now": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "rows": [], "raw": [], "oldest_headline": None,
            "first_erasure_due": None}
    oldest = None
    for sid in r1["sids"]:
        d = root / "data" / "live" / "rows" / sid
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.jsonl")):
            n = 0
            for line in f.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("parameter") != "headline" or row.get("result") in (None, ""):
                    continue
                t = row_age_time(row)
                if t is None:
                    continue
                if oldest is None or t < oldest:
                    oldest = t
                if t < cut1:
                    n += 1
            if n:
                plan["rows"].append({"sid": sid, "file": str(f.relative_to(root)).replace("\\", "/"), "rows": n})
        raw = root / "data" / "live" / "raw" / sid
        if raw.is_dir():
            for f in sorted(raw.rglob("*")):
                if f.is_file():
                    ts = dt.datetime.fromtimestamp(f.stat().st_mtime, dt.timezone.utc)
                    if ts < cut2:
                        plan["raw"].append({"sid": sid, "file": str(f.relative_to(root)).replace("\\", "/"),
                                            "bytes": f.stat().st_size})
    if oldest:
        plan["oldest_headline"] = oldest.strftime("%Y-%m-%dT%H:%M:%SZ")
        plan["first_erasure_due"] = (oldest + dt.timedelta(days=r1["keep_days"])).strftime("%Y-%m-%d")
    return plan


def redact_file(path: pathlib.Path, cut: dt.datetime, rule_id: str, now: dt.datetime) -> int:
    """Empty the sentence, keep the row. Rewrites the file only if something actually changed."""
    lines = path.read_text(encoding="utf-8").splitlines()
    out, n = [], 0
    for line in lines:
        if not line.strip():
            out.append(line)
            continue
        try:
            row = json.loads(line)
        except ValueError:
            out.append(line)          # a truncated line is evidence of a truncated write; leave it
            continue
        t = row_age_time(row)
        if (row.get("parameter") == "headline" and row.get("result") not in (None, "")
                and t is not None and t < cut):
            row["result"] = None
            row["redacted"] = {"rule": rule_id, "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "field": "result",
                               "policy": "research/RETENTION.json"}
            n += 1
            out.append(json.dumps(row, ensure_ascii=False))
        else:
            out.append(line)
    if n:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text("\n".join(out) + "\n", encoding="utf-8")
        tmp.replace(path)
    return n


def apply(root: pathlib.Path, policy: dict, now: dt.datetime, plan: dict) -> list[dict]:
    rules = {r["id"]: r for r in policy["rules"]}
    cut1 = now - dt.timedelta(days=rules["R1"]["keep_days"])
    entries = []
    for item in plan["rows"]:
        p = root / item["file"]
        before = sha256(p)
        n = redact_file(p, cut1, "R1", now)
        if n:
            entries.append({"schema": "beops-retention-ledger/v1", "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "rule": "R1", "sid": item["sid"], "file": item["file"], "rows_redacted": n,
                            "field": "result", "sha256_before": before, "sha256_after": sha256(p)})
    for item in plan["raw"]:
        p = root / item["file"]
        if p.exists():
            digest = sha256(p)
            p.unlink()
            entries.append({"schema": "beops-retention-ledger/v1", "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "rule": "R2", "sid": item["sid"], "file": item["file"], "deleted": True,
                            "bytes": item["bytes"], "sha256_deleted": digest})
    if entries:
        led = root / LEDGER
        led.parent.mkdir(parents=True, exist_ok=True)
        with open(led, "a", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return entries


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="erase; without it nothing is written")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--now", default=None, help="ISO instant, for tests")
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root)
    now = parse_time(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    policy = json.loads((root / "research" / "RETENTION.json").read_text(encoding="utf-8"))
    plan = due(root, policy, now)
    rows = sum(i["rows"] for i in plan["rows"])
    raw = len(plan["raw"])
    print(f"retention as of {plan['now']} (policy decided {policy['decided']})")
    print(f"  headline rows past 90 days : {rows} in {len(plan['rows'])} files")
    print(f"  raw news captures past 90 d: {raw} files, {sum(i['bytes'] for i in plan['raw'])} bytes")
    if plan["oldest_headline"]:
        print(f"  oldest headline held       : {plan['oldest_headline']}")
        print(f"  first erasure falls due    : {plan['first_erasure_due']}")
    if not a.apply:
        print("  dry run - nothing written. Pass --apply to enforce.")
        return 0
    entries = apply(root, policy, now, plan)
    print(f"  applied: {len(entries)} ledger entries appended to {LEDGER}")
    for e in entries[:10]:
        print("   ", e["rule"], e["file"], e.get("rows_redacted", "deleted"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
