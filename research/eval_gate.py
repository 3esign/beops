#!/usr/bin/env python3
"""
eval_gate.py - measure the validator instead of demonstrating it.

    python -B research/eval_gate.py            print the report
    python -B research/eval_gate.py --write    also write research/06-paper/GATE_EVAL_<date>.json

The monologue's gate (tools/organ_mind.validate and .validate_voice) has until now been reported by
its refusal count: 49 of 176 drops refused. A refusal count says how often the gate fired, never
whether it fired at the right things. This runs the real validator over a fixed set of hand-labelled
utterances (research/GATE_ADVERSARIAL_SET.json) built against one synthetic digest, and reports the
two rates that matter:

    false accept - an utterance a careful reader could not verify from the digest, which the gate let
                   through. Each one is a sentence the public monologue could have published.
    false reject - an utterance the digest does support, which the gate refused. These cost the
                   system its voice, not its honesty.

No model is called and no network is touched: the digest is fixed, the utterances are written down,
and the only thing under test is the code that decides.

Honest reading of what this can and cannot show is in the set's own `annotation` block: one
annotator, attacks its author could imagine, and therefore a LOWER BOUND on the false-accept rate.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import organ_mind as M  # noqa: E402

SET_PATH = ROOT / "research" / "GATE_ADVERSARIAL_SET.json"

# The same set, run against the gate as it stood before the semantic guards were written. Kept here so
# the improvement is a comparison and not a claim, and so a later reader can see what the arithmetic
# checks alone were worth.
BASELINE = {"gate_version": "0.3.5", "measured": "2026-09-09", "labelled_reject": 36,
            "false_accept": 17, "false_accept_rate": 0.472, "false_reject": 1,
            "families_missed": ["advice", "authority_borrowing", "causal_invention", "citation_mismatch",
                                "coverage_overclaim", "link_as_fact", "measurement_time_drift",
                                "number_rebinding", "silence_as_zero", "superlative_unsupported",
                                "unit_swap", "untimed_as_now", "voice_meaning_drift",
                                "voice_not_serbian", "voice_number_added"]}


def build_digest(spec: dict) -> dict:
    """Rebuild the digest exactly the way organ_mind does, so `numbers` is not hand-maintained."""
    nums: set = set()
    for f in spec["facts"]:
        nums |= M._nums(f["sr"]) | M._nums(f["en"])
    return {**spec, "numbers": sorted(nums)}


def prepare(answer: dict) -> dict:
    a = dict(answer)
    pad = a.pop("_pad_to", None)
    if pad:
        a["text"] = a["text"].replace("LONGFILLER", "and the window holds nothing else worth saying " * 40)
        a["text"] = a["text"][: max(pad, len(a["text"]))] if len(a["text"]) >= pad else a["text"] + "x" * (pad - len(a["text"]))
    return a


def run(data: dict) -> dict:
    dg = build_digest(data["digest"])
    results = []
    for it in data["items"]:
        if it["stage"] == "think":
            ok, reasons = M.validate(prepare(it["answer"]), dg, it.get("previous"))
        elif it["stage"] == "voice":
            ok, reasons = M.validate_voice(it["sr"], it["en"], dg)
        else:
            raise ValueError("unknown stage: " + it["stage"])
        gate = "accept" if ok else "reject"
        outcome = {
            ("accept", "accept"): "true_accept",
            ("reject", "reject"): "true_reject",
            ("reject", "accept"): "false_accept",
            ("accept", "reject"): "false_reject",
        }[(it["should"], gate)]
        results.append({"id": it["id"], "stage": it["stage"], "family": it["family"],
                        "should": it["should"], "gate": gate, "outcome": outcome,
                        "reasons": reasons, "why": it["why"]})
    return {"results": results, "digest_numbers": dg["numbers"]}


def summarise(results: list[dict]) -> dict:
    def n(o, rs=None):
        return sum(1 for r in (rs if rs is not None else results) if r["outcome"] == o)

    should_reject = [r for r in results if r["should"] == "reject"]
    should_accept = [r for r in results if r["should"] == "accept"]
    fa, fr = n("false_accept"), n("false_reject")
    out = {
        "items": len(results),
        "labelled_reject": len(should_reject), "labelled_accept": len(should_accept),
        "true_accept": n("true_accept"), "true_reject": n("true_reject"),
        "false_accept": fa, "false_reject": fr,
        "false_accept_rate": round(fa / len(should_reject), 3) if should_reject else None,
        "false_reject_rate": round(fr / len(should_accept), 3) if should_accept else None,
        "families_missed": sorted({r["family"] for r in results if r["outcome"] == "false_accept"}),
        "families_overcaught": sorted({r["family"] for r in results if r["outcome"] == "false_reject"}),
    }
    for stage in ("think", "voice"):
        rs = [r for r in results if r["stage"] == stage]
        sr_ = [r for r in rs if r["should"] == "reject"]
        out[stage] = {"items": len(rs), "false_accept": n("false_accept", rs), "false_reject": n("false_reject", rs),
                      "false_accept_rate": round(n("false_accept", rs) / len(sr_), 3) if sr_ else None}
    return out


def report(data: dict, run_out: dict, summary: dict) -> str:
    L = []
    L.append(f"GATE EVALUATION - set {data['version']} against organ version {M.ORGAN_VERSION}")
    L.append("=" * 78)
    L.append(f"{summary['items']} hand-labelled utterances over one fixed digest, no model called.")
    L.append(f"labelled reject {summary['labelled_reject']} · labelled accept {summary['labelled_accept']}")
    L.append("")
    L.append(f"  false accept  {summary['false_accept']:>3} / {summary['labelled_reject']:<3}"
             f"  rate {summary['false_accept_rate']}   (published sentences the record does not support)")
    L.append(f"  false reject  {summary['false_reject']:>3} / {summary['labelled_accept']:<3}"
             f"  rate {summary['false_reject_rate']}   (supported sentences the gate silenced)")
    L.append("")
    L.append("by stage")
    for stage in ("think", "voice"):
        s = summary[stage]
        L.append(f"  {stage:<6} items {s['items']:>3}  false accept {s['false_accept']:>2} (rate {s['false_accept_rate']})"
                 f"  false reject {s['false_reject']:>2}")
    L.append("")
    L.append("WHAT THE GATE DOES NOT CATCH")
    misses = [r for r in run_out["results"] if r["outcome"] == "false_accept"]
    if not misses:
        L.append("  nothing in this set")
    for r in misses:
        L.append(f"  {r['id']}  {r['family']}")
        L.append(f"        {r['why']}")
    over = [r for r in run_out["results"] if r["outcome"] == "false_reject"]
    if over:
        L.append("")
        L.append("WHAT THE GATE OVER-CATCHES")
        for r in over:
            L.append(f"  {r['id']}  {r['family']}: " + "; ".join(r["reasons"]))
    L.append("")
    L.append("EVERY ITEM")
    L.append(f"  {'id':<5}{'stage':<7}{'label':<8}{'gate':<8}{'outcome':<14}family")
    for r in run_out["results"]:
        mark = " " if r["outcome"].startswith("true") else "!"
        L.append(f"{mark} {r['id']:<5}{r['stage']:<7}{r['should']:<8}{r['gate']:<8}{r['outcome']:<14}{r['family']}")
    L.append("")
    L.append(f"BEFORE THE SEMANTIC GUARDS (organ {BASELINE['gate_version']}, same set)")
    L.append(f"  false accept {BASELINE['false_accept']:>3} / {BASELINE['labelled_reject']:<3}  rate {BASELINE['false_accept_rate']}"
             f"   -> now {summary['false_accept']} / {summary['labelled_reject']}  rate {summary['false_accept_rate']}")
    L.append("")
    L.append("HONEST VERDICT")
    L.append("  " + data["annotation"]["known_bias"])
    L.append("  The families listed above are the ones one author could imagine in one sitting. A")
    L.append("  false-accept rate measured against them is a floor. It is still the first number this")
    L.append("  project has had for the question the refusal count never answered.")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write the result JSON next to the paper")
    a = ap.parse_args()
    data = json.loads(SET_PATH.read_text(encoding="utf-8"))
    run_out = run(data)
    summary = summarise(run_out["results"])
    text = report(data, run_out, summary)
    print(text)
    if a.write:
        stamp = dt.datetime.now(dt.timezone.utc)
        out = ROOT / "research" / "06-paper" / f"GATE_EVAL_{stamp:%Y-%m-%d}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "schema": "beops-gate-eval/v1",
            "run_at": stamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "set_version": data["version"],
            "gate_version": M.ORGAN_VERSION,
            "baseline": BASELINE,
            "annotation": data["annotation"],
            "summary": summary,
            "results": run_out["results"],
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("\nwrote " + out.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
