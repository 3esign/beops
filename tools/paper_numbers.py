#!/usr/bin/env python3
"""
paper_numbers.py - print every figure the conference paper cites, from the files that hold them.

    python -B tools/paper_numbers.py            the block, for reading
    python -B tools/paper_numbers.py --json     the same as JSON, for a build step

A paper whose numbers are typed by hand is a paper whose numbers drift. Every quantity in
research/06-paper/PAPER_v1_2026-09-09.md comes out of this script, and the script reads the record
rather than a summary of it. Where a figure cannot be computed the line says so instead of guessing -
an unavailable number is a state, like every other absence in this project.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROW_INDEX_SCHEMA = "beops-watch-row-index/v1"


def safe(fn, default="unavailable"):
    try:
        return fn()
    except Exception as e:                                    # noqa: BLE001 - a missing figure is a state
        return f"{default} ({type(e).__name__})"


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


NO_VALUE = "(none written)"


def named(c):
    """A Counter's categories, with the absent one named rather than left as null.

    Both of these tallies had a `None` key, so the paper's figures carried a category called `null`:
    215 sources by status, and every derived drop by state. A reader cannot act on `null` - it does
    not say whether the field was empty, absent, or never part of the vocabulary. Missing is not
    zero, and it is not a category either; it is a thing nobody wrote down, and it gets said so.
    """
    return {(NO_VALUE if k is None else str(k)): v for k, v in c.most_common()}


def registry():
    d = load("research/SOURCE_REGISTRY.json")
    c = Counter(s.get("status") for s in d["sources"])
    return {"records": len(d["sources"]), "reviewed_at": d.get("reviewed_at"),
            "by_status": named(c), "opted_out": c.get("opted_out", 0),
            "needs_decision": c.get("needs_decision", 0)}


def collectors():
    d = load("research/COLLECTORS.json")
    on = [s for s in d["sources"] if s.get("enabled")]
    off = [s for s in d["sources"] if not s.get("enabled")]
    news = [s for s in on if s.get("parser") in ("rss", "city_listing")]
    return {"listed": len(d["sources"]), "polled": len(on), "disabled": len(off),
            "disabled_sids": [s["sid"] for s in off],
            "news_polled": len(news),
            "cadence_min": sorted({int(s["cadence_seconds"] // 60) for s in on if s.get("cadence_seconds")})}


def provenance():
    txt = (ROOT / "research" / "08-provenance" / "INDEX.md").read_text(encoding="utf-8", errors="replace")
    out = {}
    for key, pat in (("sources_with_evidence", r"(\d+)\s+sources with stored evidence"),
                     ("captures", r"(\d+)\s+captures"),
                     ("passed", r"(\d+)\s+access checks passed"),
                     ("refused", r"(\d+)\s+refused"),
                     ("awaiting", r"(\d+)\s+awaiting decision"),
                     ("incomplete", r"(\d+)\s+incomplete"),
                     ("undocumented", r"(\d+)\s+undocumented")):
        m = re.search(pat, txt)
        out[key] = int(m.group(1)) if m else None
    m = re.search(r"Generated\s+([0-9-]+\s+[0-9:]+\s*UTC)", txt)
    out["generated"] = m.group(1) if m else None
    return out


def rows_on_disk(evidence=None):
    manifested = rows_from_release_manifest(evidence)
    if manifested is not None:
        return manifested
    indexed = rows_from_watch_index(evidence)
    if indexed is not None:
        return indexed
    n, files = 0, 0
    for p in (ROOT / "data" / "live" / "rows").rglob("*.jsonl"):
        files += 1
        # A bounded sequential read avoids thousands of tiny HDD reads while
        # other collectors use the same disk. Every nonblank line is still read.
        with open(p, "rb", buffering=1024 * 1024) as f:
            count, size = 0, 0
            digest = hashlib.sha256() if evidence is not None else None
            for line in f:
                count += bool(line.strip())
                if digest is not None:
                    digest.update(line)
                    size += len(line)
            n += count
            if evidence is not None:
                evidence[p.relative_to(ROOT).as_posix()] = {
                    'rows': count, 'bytes': size, 'sha256': digest.hexdigest()}
    return {"rows": n, "files": files}


def rows_from_release_manifest(evidence=None):
    manifest = ROOT / "runtime" / "release-inputs.json"
    if not manifest.is_file():
        return None
    try:
        document = json.loads(manifest.read_text(encoding="utf-8-sig"))
        entries = [row for row in document.get("files", [])
                   if isinstance(row, dict)
                   and isinstance(row.get("path"), str)
                   and row["path"].startswith("data/live/rows/")
                   and row["path"].endswith(".jsonl")]
        if not entries or any(not isinstance(row.get("nonblank_lines"), int) for row in entries):
            return None
    except (OSError, UnicodeError, ValueError, AttributeError):
        return None
    if evidence is not None:
        for row in entries:
            evidence[row["path"]] = {
                "rows": row["nonblank_lines"],
                "bytes": row["bytes"],
                "sha256": row["sha256"],
            }
    return {"rows": sum(row["nonblank_lines"] for row in entries), "files": len(entries)}


def rows_from_watch_index(evidence=None):
    live = ROOT / "data" / "live"
    rows_dir = live / "rows"
    index_path = live / "watch-row-index.json"
    if not rows_dir.is_dir() or not index_path.is_file():
        return None
    try:
        index = json.loads(index_path.read_text(encoding="utf-8-sig"))
        entries = index.get("files")
        if index.get("schema") != ROW_INDEX_SCHEMA or not isinstance(entries, dict) or not entries:
            return None
        actual = {p.relative_to(live).as_posix(): p for p in sorted(rows_dir.rglob("*.jsonl"))}
    except (OSError, UnicodeError, ValueError, AttributeError):
        return None
    if set(actual) != set(entries):
        return None
    total = 0
    try:
        for key, path in actual.items():
            row = entries.get(key)
            if not isinstance(row, dict):
                return None
            st = path.stat()
            if row.get("size") != st.st_size or row.get("mtime_ns") != st.st_mtime_ns:
                return None
            rows = row.get("rows")
            if not isinstance(rows, int) or rows < 0:
                return None
            total += rows
            if evidence is not None:
                evidence[path.relative_to(ROOT).as_posix()] = {"rows": rows, "bytes": st.st_size}
    except (OSError, ValueError):
        return None
    return {"rows": total, "files": len(actual)}


def history():
    d = load("docs/history.json")
    return {"hours": d.get("hours_of_history"), "series": len(d.get("series", [])),
            "starts": d.get("history_starts"), "ends": d.get("history_ends"),
            "unreadable_measurement_times": sum((d.get("unreadable_measurement_times") or {}).values()),
            "measured_series": sum(1 for s in d.get("series", []) if s.get("time_basis") in ("measured", "corrected")),
            "corrected_series_subset": sum(1 for s in d.get("series", []) if s.get("time_basis") == "corrected"),
            "clock_note": "measured_series includes series on an explicitly estimated corrected measurement clock; received_series has no measurement time",
            "received_series": sum(1 for s in d.get("series", []) if s.get("time_basis") == "received")}


def mind():
    c = Counter()
    import record
    for p in (ROOT / "data" / "live" / "derived" / "mind").glob("????-??.jsonl"):
        for r in record.objects(p):
            c[r.get("state")] += 1
    total = sum(c.values())
    spoken = c.get("thought", 0) + c.get("rejected", 0)
    return {"drops": total, "by_state": named(c),
            "population": "canonical monthly utterances only; notebooks and claim events excluded",
            "refusal_rate_of_utterances": round(c.get("rejected", 0) / spoken, 3) if spoken else None}


def corrections():
    txt = (ROOT / "research" / "08-provenance" / "CORRECTIONS.md").read_text(encoding="utf-8", errors="replace")
    ids = sorted(set(re.findall(r"\bC-(\d{3})\b", txt)))
    return {"count": len(ids), "last": "C-" + ids[-1] if ids else None}


def gate():
    files = sorted((ROOT / "research" / "06-paper").glob("GATE_EVAL_*.json"))
    if not files:
        return "unavailable (run research/eval_gate.py --write)"
    d = json.loads(files[-1].read_text(encoding="utf-8"))
    s = d["summary"]
    return {"file": files[-1].name, "gate_version": d.get("gate_version"),
            "items": s["items"], "labelled_reject": s["labelled_reject"],
            "false_accept": s["false_accept"], "false_accept_rate": s["false_accept_rate"],
            "false_reject": s["false_reject"], "false_reject_rate": s["false_reject_rate"],
            "residue": s["families_missed"],
            "baseline_false_accept": d["baseline"]["false_accept"],
            "baseline_rate": d["baseline"]["false_accept_rate"],
            "baseline_version": d["baseline"]["gate_version"]}


def iso():
    d = load("research/ISO37120_MAPPING.json")
    c = Counter(t["verdict"] for t in d["themes"])
    return {"themes": len(d["themes"]), **{k: c.get(k, 0) for k in d["verdicts"]}}


def retention():
    sys.path.insert(0, str(ROOT / "tools"))
    import datetime as dt

    import apply_retention as R
    policy = load("research/RETENTION.json")
    plan = R.due(ROOT, policy, dt.datetime.now(dt.timezone.utc))
    days = next(r['keep_days'] for r in policy['rules'] if r['id'] == 'R1')
    return {"policy_decided": policy["decided"], "keep_days": days if days is not None else 'indefinite',
            "rows_due_today": sum(i["rows"] for i in plan["rows"]),
            "oldest_headline": plan["oldest_headline"] or 'no headlines', "first_erasure_due": plan["first_erasure_due"] or 'not scheduled'}


FIGURES = [("registry", registry), ("collectors", collectors), ("provenance", provenance),
           ("rows", rows_on_disk), ("history", history), ("mind", mind), ("corrections", corrections),
           ("gate", gate), ("iso37120", iso), ("retention", retention)]

# Figures read from a record that is appended to while the observatory runs: the collectors write
# rows every tick, the mind writes drops, the legal captures append to the provenance ledger, and the
# history is derived from the rows. Two runs of this script minutes apart legitimately disagree about
# them. That is not drift - it is what a count of a living record is - but it means the number is only
# true as of `taken_at`, and a paper that prints it without saying when has printed a number nobody
# can check.
# Retention also changes with arrivals and the clock (oldest headline, raw-file
# expiry); it cannot be treated as a stable figure and recomputed for a static
# rendering comparison on every publication.
LIVE = ("provenance", "rows", "history", "mind", "retention")


def taken_at() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    out = {name: safe(fn) for name, fn in FIGURES}
    out["taken_at"] = taken_at()
    out["live_figures"] = list(LIVE)
    # A run leaves a line behind. A paper that says "figures verified at 19:07" was, until now, an
    # unverifiable claim about a run nobody recorded; from here a stamp can be matched to one.
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import paper_stamps
        paper_stamps.record({k: v for k, v in out.items() if k not in ("taken_at", "live_figures")},
                            out["taken_at"])
    except Exception as e:                                   # noqa: BLE001 - a receipt is not a figure
        print("could not record this run: %s" % type(e).__name__, file=sys.stderr)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    print("taken at %s - %s count a record that is still being written to, and are true as of that "
          "instant and no other" % (out["taken_at"], ", ".join(LIVE)))
    for name, val in out.items():
        if name in ("taken_at", "live_figures"):
            continue
        print(f"[{name}]")
        if isinstance(val, dict):
            for k, v in val.items():
                print(f"  {k:32} {v}")
        else:
            print("  " + str(val))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
