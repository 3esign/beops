#!/usr/bin/env python3
"""paper_stamps.py - the times the papers type into themselves, checked against the record.

C-052 found that ten of thirteen hand-typed times in the corrections ledger were wrong, and said of
the papers' own line - "Figures verified 2026-09-09 19:07 UTC" - that it was the same kind of line
and had not been audited. This audits it.

Two papers carry such a stamp. Both turn out to be right: each sits between ten and twenty-five
minutes *before* the commit that introduced the document, which is what verifying the figures and
then writing the line looks like. That is a result worth writing down as plainly as a failure.

What is still missing is evidence rather than plausibility: nothing recorded that paper_numbers.py
ever ran at 19:07. From now it does - `paper_numbers.py` appends a line to the run log for every run -
and a stamp in a paper written after that log existed must match one.

The invariant that holds regardless: **a stamp may never be later than the commit that introduced the
document it is in.** Figures cannot be verified after the paper reporting them was committed.
"""
import hashlib
import json
import pathlib
import re
import subprocess
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAPERS = ROOT / "research" / "06-paper"
RUNS = ROOT / "data" / "live" / "paper-numbers-runs.jsonl"
OUT = PAPERS / "PAPER_STAMPS.json"

STAMP = re.compile(r"(\d{4}-\d\d-\d\d)[ ,]+(\d\d:\d\d)(?::\d\d)?\s*UTC")

# What a line claims, as opposed to what it quotes, lives in one place now. It did not, and this file
# was written without the fix that `correction_times.py` already had: pre-paper v5 quotes the stamp
# format it abolishes, this tool read the quotation as v5's own claim, and the publish gate refused a
# correct document. A rule that exists in one file is a rule the next tool will not have.
import prose
CODE_SPAN = prose.CODE_SPAN

# The run log did not exist before this. A stamp in a document added before it can be checked for
# possibility and plausibility, but not for evidence, and saying so is the honest verdict.
RUNS_LOG_SINCE = "2026-09-10T12:00:00Z"

# Measured 2026-09-10 against the commits that introduced these two documents. Frozen so that a stamp
# quietly edited later is a test failure rather than a tidy-up. Minutes are stamp minus commit, so a
# negative number means the figures were verified before the paper was committed, which is the only
# order that makes sense.
MEASURED = {"PRE_PAPER_v3_2026-09-09.md": -24, "PRE_PAPER_v4_2026-09-10.md": -10}
PLAUSIBLE_HOURS_BEFORE = 12


def _git(args):
    try:
        p = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout if p.returncode == 0 else None


def _added(rel):
    out = _git(["log", "--diff-filter=A", "--format=%cI", "--", rel])
    if not out:
        return None
    lines = [l for l in out.strip().splitlines() if l.strip()]
    if not lines:
        return None
    return datetime.fromisoformat(lines[-1]).astimezone(timezone.utc)


def runs(path=None):
    path = path or RUNS
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln.startswith("{"):
            continue
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue
    return out


def build():
    log = runs()
    run_times = []
    for r in log:
        try:
            run_times.append(datetime.fromisoformat(str(r.get("taken_at")).replace("Z", "+00:00")))
        except ValueError:
            continue
    since = datetime.fromisoformat(RUNS_LOG_SINCE.replace("Z", "+00:00"))

    entries = []
    for p in sorted(PAPERS.glob("*.md")):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        added = _added(rel)
        for i, ln in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            bare = prose.claims(ln)
            for m in STAMP.finditer(bare):
                stated = datetime.fromisoformat(f"{m.group(1)}T{m.group(2)}:00+00:00")
                delta = round((stated - added).total_seconds() / 60) if added else None
                if delta is None:
                    verdict = "unknown: the document is not in the record"
                elif delta > 0:
                    verdict = "impossible: verified after the document was committed"
                elif -delta > PLAUSIBLE_HOURS_BEFORE * 60:
                    verdict = "implausible: verified long before the document was committed"
                elif added < since:
                    verdict = "consistent, unevidenced: no run log existed yet"
                elif any(abs((stated - t).total_seconds()) < 900 for t in run_times):
                    verdict = "evidenced: a recorded run matches"
                else:
                    verdict = "unevidenced: no recorded run at that time"
                entries.append({"file": p.name, "line": i,
                                "stated_utc": stated.isoformat(timespec="seconds").replace("+00:00", "Z"),
                                "document_committed_utc": (added.isoformat(timespec="seconds").replace("+00:00", "Z")
                                                           if added else None),
                                "stated_minus_committed_minutes": delta,
                                "verdict": verdict,
                                "text": ln.strip()[:200]})

    doc = {"schema": "beops-paper-stamps/v1",
           "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
           "rule": ("A time typed into a paper is checked against the commit that introduced the "
                    "paper. It may never be later than that commit. From %s a paper written after a "
                    "recorded run must match one." % RUNS_LOG_SINCE),
           "papers_scanned": len(list(PAPERS.glob("*.md"))),
           "stamps": len(entries),
           "recorded_runs": len(run_times),
           "measured_and_frozen": MEASURED,
           "git_readable": _git(["rev-parse", "HEAD"]) is not None,
           "entries": entries}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc


def record(figures: dict, taken_at: str, path=None):
    """One line per run of paper_numbers.py: when, and a hash of what it produced.

    `path` exists so that a test can prove the receipt is written without writing test rows into the
    evidence itself. An append-only record that anything but a real run may append to is not one.
    """
    path = path or RUNS
    path.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(figures, ensure_ascii=False, sort_keys=True, default=str)
    line = json.dumps({"taken_at": taken_at,
                       "figures_sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
                       "figures": len(figures)}, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


if __name__ == "__main__":
    d = build()
    print("paper stamps -> %s" % OUT)
    print("  %d papers | %d typed times | %d recorded runs"
          % (d["papers_scanned"], d["stamps"], d["recorded_runs"]))
    for e in d["entries"]:
        d = e["stated_minus_committed_minutes"]
        print("   %-32s line %-5d %s  (%s)  %s"
              % (e["file"], e["line"], e["stated_utc"],
                 "%+d min vs commit" % d if d is not None else "not yet in the record",
                 e["verdict"]))
