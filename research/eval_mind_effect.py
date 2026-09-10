#!/usr/bin/env python3
"""eval_mind_effect.py - did a correction change anything?

Split the mind's own record at a moment and compare the two halves. It exists because the pattern this
record keeps repeating is a fix asserted rather than measured: C-028 declared the panel stable without
measuring the range that was broken, and C-034/C-035 would have been the same claim if the organ's rows
had not been counted afterwards. A correction to the mind is not finished until this has been run
across it and the numbers written into CORRECTIONS.md.

    python research/eval_mind_effect.py 2026-09-10T02:15

Reads only. Prints; writes nothing.
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MIND = ROOT / "data" / "live" / "derived" / "mind"
TICKS = ROOT / "runtime" / "mind-tick.log"
MODEL_STEPS = ("observer", "skeptic", "connector", "linker", "ranker")


def rows(p: pathlib.Path) -> list[dict]:
    out = []
    if not p.exists():
        return out
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if ln.startswith("{"):
            try:
                out.append(json.loads(ln))
            except ValueError:
                pass
    return out


def receipts() -> list[dict]:
    if not TICKS.exists():
        return []
    t = TICKS.read_text(encoding="utf-8", errors="replace")
    out = []
    for _at, b in re.findall(r"---- (\S+) \n(\{.*?\n\})", t, re.S):
        try:
            out.append(json.loads(b))
        except ValueError:
            pass
    return out


def is_hour(reason: str) -> bool:
    """A refusal that names a two-digit number 00..23 as 'not in the digest' is almost always a CLOCK
    the entity read correctly - the defect C-034 fixed."""
    tail = reason.split(": ")[-1]
    return reason.startswith("number not in digest") and len(tail) == 2 and tail.isdigit() and int(tail) <= 23


def report(cut: str) -> int:
    ut = rows(MIND / "2026-09.jsonl") or [r for p in sorted(MIND.glob("*.jsonl")) if p.name != "claims.jsonl" for r in rows(p)]
    cl = rows(MIND / "claims.jsonl")
    rc = receipts()
    if not ut:
        print("no rows to compare")
        return 2

    def half(stamp: str) -> str:
        return "after" if str(stamp or "") >= cut else "before"

    print(f"cut at {cut}   rows {len(ut)}   receipts {len(rc)}\n")

    print("=== utterances: accepted vs refused ===")
    print("  (a correction that makes the CHECKS stricter lowers this on purpose - read it with the next block)")
    print("  an utterance the model never produced is NOT a refusal: it is counted separately, because")
    print("  a rate that mixes 'said something unsupportable' with 'said nothing at all' measures two")
    print("  different failures as one. 16 of 47 refusals on 2026-09-10 were empty strings.")
    for h in ("before", "after"):
        m = [r for r in ut if half(r.get("derivedTime")) == h and r.get("state") in ("thought", "rejected") and r.get("entity")]
        empty = [r for r in m if not str(r.get("en") or "").strip()]
        said = [r for r in m if str(r.get("en") or "").strip()]
        th = [r for r in said if r.get("state") == "thought"]
        print("  %-6s utterances %4d | produced nothing %3d | of what was SAID: accepted %4d (%5.1f%%) | refused %4d"
              % (h, len(m), len(empty), len(th), 100.0 * len(th) / max(1, len(said)), len(said) - len(th)))

    print("\n=== which model spoke, and how it fared ===")
    print("  (C-036's fallback means the smaller model speaks when the larger one has failed, so this")
    print("   rate falls when the machine is under memory pressure - a fact about the body, not the checks)")
    for h in ("before", "after"):
        m = [r for r in ut if half(r.get("derivedTime")) == h and r.get("state") in ("thought", "rejected")
             and str(r.get("en") or "").strip()]
        by: dict = {}
        for r in m:
            k = str(r.get("model") or "?")
            a, b = by.get(k, (0, 0))
            by[k] = (a + (1 if r.get("state") == "thought" else 0), b + 1)
        parts = ["%s %d/%d (%.0f%%)" % (k, v[0], v[1], 100.0 * v[0] / max(1, v[1]))
                 for k, v in sorted(by.items(), key=lambda x: -x[1][1])]
        print("  %-6s %s" % (h, " | ".join(parts) or "nothing"))

    print("\n=== why they were refused ===")
    for h in ("before", "after"):
        c: collections.Counter = collections.Counter()
        for r in [x for x in ut if half(x.get("derivedTime")) == h and x.get("state") == "rejected"]:
            for w in (r.get("rejected_because") or []):
                s = str(w)
                key = ("a clock read as a quantity" if is_hour(s) else
                       "time outside the window" if s.startswith("time outside") else
                       "echoed its own notebook" if "echoed its own notebook" in s else
                       s.split(":")[0])
                c[key] += 1
        print("  %-6s %s" % (h, ", ".join(f"{k} {v}" for k, v in c.most_common(8)) or "none"))

    print("\n=== the Serbian ===")
    for h in ("before", "after"):
        th = [r for r in ut if half(r.get("derivedTime")) == h and r.get("state") == "thought" and r.get("entity")]
        v = sum(1 for r in th if r.get("sr_state") == "voiced")
        ref = [r for r in th if r.get("sr_state") and r.get("sr_state") != "voiced"]
        kept = sum(1 for r in ref if (r.get("sr_refused") or "").strip())
        print("  %-6s thoughts %4d | voiced %4d (%5.1f%%) | refused %3d | refusals that KEPT their text %3d"
              % (h, len(th), v, 100.0 * v / max(1, len(th)), len(ref), kept))

    print("\n=== the validator's own words inside a stored utterance (C-037) ===")
    for h in ("before", "after"):
        n = sum(1 for r in ut if half(r.get("derivedTime")) == h
                and re.search(r"->\s*REFUSED|number not in digest", str(r.get("en") or "")))
        print("  %-6s rows whose text quotes a refusal: %d" % (h, n))

    print("\n=== claims: can they be settled at all ===")
    for h in ("before", "after"):
        m = [c for c in cl if half(c.get("at")) == h]
        out = collections.Counter(str(c.get("outcome")) for c in m)
        named = sum(1 for c in m if not re.fullmatch(r"S\d+", str((c.get("claim") or {}).get("sid") or "")))
        print("  %-6s claims %3d | outcomes %s | naming a source in words rather than by id: %d"
              % (h, len(m), dict(out) or "-", named))

    print("\n=== the organ's own steps: did it go quiet ===")
    for h, a, b in (("before", "0000", cut), ("after", cut, "9999")):
        w = [r for r in rc if a <= str(r.get("at", "")) < b]
        ms = [r for r in w if r.get("step_name") in MODEL_STEPS]
        bad = [r for r in ms if r.get("state") in ("organ_silent", "organ_failed")]
        fb = [r for r in ms if r.get("fell_back_from")]
        print("  %-6s model steps %4d | silent or failed %3d (%5.1f%%) | fell back to another model %2d"
              % (h, len(ms), len(bad), 100.0 * len(bad) / max(1, len(ms)), len(fb)))
        for r in fb[:4]:
            print("      %s %-10s spoke: %-14s after %s" % (str(r.get("at"))[11:19], r.get("step_name"), r.get("model"), r.get("fell_back_from")))
    print("\nread the acceptance rate together with the refusal reasons: a stricter check is not a worse mind.")
    return 0


if __name__ == "__main__":
    raise SystemExit(report(sys.argv[1] if len(sys.argv) > 1 else "2026-09-10T02:15"))
