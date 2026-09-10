#!/usr/bin/env python3
"""correction_times.py - when a correction was actually written, read from the record instead of typed.

Every entry in CORRECTIONS.md carried a hand-typed line of the form `**2026-09-10, 15:40 UTC.**`.
Measured against the commit that introduced each entry, the last ten were wrong by up to three hours
and thirty-eight minutes, and two of them were out of order with each other. The offsets are not
constant, so it is not a timezone: it is a person typing a plausible time.

The rule that replaces it: a correction's time is the commit that introduced it. Nobody types it.
This tool reads that from git in one pass and writes it beside the ledger. The wrong stamps stay
where they are - corrections are appended, never edited - and are named here with the true time
beside them.
"""
import json
import pathlib
import re
import subprocess
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "research" / "08-provenance" / "CORRECTIONS.md"
OUT = ROOT / "research" / "08-provenance" / "CORRECTION_TIMES.json"

# From C-052 onward no entry may carry a typed time. Before it, these are the ones that did and were
# wrong; they are listed so that a stamp quietly appearing or vanishing is a test failure rather than
# a tidy-up.
TYPED_ERA_ENDS_BEFORE = 52
TOLERANCE_MINUTES = 15

# Measured 2026-09-10 against the commits that introduced them. These are frozen: the stamps stay in
# the ledger as written, because corrections are appended and never edited, and this list is what
# stops one of them being quietly tidied away later. If an entry leaves this list, either a stamp was
# edited or the history was rewritten - both are failures, not fixes.
KNOWN_WRONG = ("C-033", "C-037", "C-043", "C-044", "C-045",
               "C-046", "C-047", "C-048", "C-049", "C-050")

HEAD = re.compile(r"^#{2,3}\s*(C-\d{3})")
STAMP = re.compile(r"\*\*(\d{4}-\d\d-\d\d),\s*(\d\d:\d\d)\s*UTC")


def _num(cid):
    return int(cid.split("-")[1])


CODE_SPAN = re.compile(r"`[^`]*`")


def stated_times():
    """The typed time under each heading, as the ledger states it. May be absent.

    A stamp inside a code span is a quotation, not a claim. C-052 - the entry that introduced this
    rule - quotes the very format it is abolishing, and the first run of the rule read that quotation
    as the entry stating its own time. An entry quoting another entry's mistake has not made it.
    """
    out, cur = {}, None
    for ln in LEDGER.read_text(encoding="utf-8").splitlines():
        m = HEAD.match(ln)
        if m:
            cur = m.group(1)
            continue
        s = STAMP.search(CODE_SPAN.sub("", ln))
        if s and cur and cur not in out:
            out[cur] = s.group(1) + "T" + s.group(2) + ":00Z"
    return out


def commit_times():
    """The commit that first added each heading. One pass over the ledger's history."""
    try:
        p = subprocess.run(
            ["git", "log", "--reverse", "--format=@@@%H %cI", "-p", "--unified=0",
             "--", str(LEDGER.relative_to(ROOT)).replace("\\", "/")],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    out, sha, when = {}, None, None
    for ln in p.stdout.splitlines():
        if ln.startswith("@@@"):
            parts = ln[3:].split(" ", 1)
            sha, when = parts[0], (parts[1] if len(parts) > 1 else "")
            continue
        if not ln.startswith("+") or ln.startswith("+++"):
            continue
        m = HEAD.match(ln[1:])
        if m and m.group(1) not in out:
            out[m.group(1)] = (sha[:7], when)
    return out


def build():
    stated = stated_times()
    commits = commit_times()
    ids = []
    for ln in LEDGER.read_text(encoding="utf-8").splitlines():
        m = HEAD.match(ln)
        if m and m.group(1) not in ids:
            ids.append(m.group(1))

    entries = []
    for cid in sorted(ids, key=_num):
        c = (commits or {}).get(cid)
        commit_utc = None
        if c and c[1]:
            try:
                commit_utc = datetime.fromisoformat(c[1]).astimezone(timezone.utc).isoformat(
                    timespec="seconds").replace("+00:00", "Z")
            except ValueError:
                commit_utc = None
        delta = None
        if commit_utc and stated.get(cid):
            a = datetime.fromisoformat(stated[cid].replace("Z", "+00:00"))
            b = datetime.fromisoformat(commit_utc.replace("Z", "+00:00"))
            delta = round((a - b).total_seconds() / 60)
        entries.append({"id": cid,
                        "stated_in_ledger_utc": stated.get(cid),
                        "commit": c[0] if c else None,
                        "written_utc": commit_utc,
                        "stated_minus_written_minutes": delta})

    wrong = [e["id"] for e in entries
             if e["stated_minus_written_minutes"] is not None
             and abs(e["stated_minus_written_minutes"]) > TOLERANCE_MINUTES]
    doc = {
        "schema": "beops-correction-times/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "rule": ("A correction's time is the time of the commit that introduced it, read from the "
                 "repository. It is not typed. Entries before C-%d carry a typed time as well; where "
                 "the two disagree, the commit is the record and the typed time is the error."
                 % TYPED_ERA_ENDS_BEFORE),
        "tolerance_minutes": TOLERANCE_MINUTES,
        "typed_era_ends_before": TYPED_ERA_ENDS_BEFORE,
        "count": len(entries),
        "typed_and_wrong": wrong,
        "known_wrong_declared": list(KNOWN_WRONG),
        "not_yet_in_the_record": [e["id"] for e in entries if e["written_utc"] is None],
        "note_on_the_newest": ("The newest entry has no time until the commit that introduces it "
                               "exists. A correction that has not entered the record has no time, "
                               "and saying so is more accurate than giving it one."),
        "git_readable": commits is not None,
        "entries": entries,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc


if __name__ == "__main__":
    d = build()
    print("correction times -> %s" % OUT)
    print("  %d entries | git readable: %s | typed and wrong: %d"
          % (d["count"], d["git_readable"], len(d["typed_and_wrong"])))
    for e in d["entries"]:
        if e["id"] in d["typed_and_wrong"]:
            print("   %s stated %s  written %s  out by %+d min"
                  % (e["id"], e["stated_in_ledger_utc"], e["written_utc"],
                     e["stated_minus_written_minutes"]))
