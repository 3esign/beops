#!/usr/bin/env python3
"""
watchman.py - check what was actually produced, never what a task says about itself.

    python -B tools/watchman.py                 the reading, and a row in the ledger
    python -B tools/watchman.py --dry           the reading, writing nothing
    python -B tools/watchman.py --json          machine-readable, for a build step

C-014 is the reason this exists. A scheduled task ran roughly a hundred times over seventeen hours
with status Ready, last result 0 and a log line per run, and published nothing. Every signal that
said "fine" was a signal the task emitted about itself. So this watchman is forbidden to read any of
them: no exit codes, no task status, no log lines. It reads rows, receipts, the history file, the
published commit - artefacts, which either exist and are recent or do not.

Three distinctions it is built around, because getting them wrong is how a monitor lies:

  a source that is SILENT is not a source that FAILED. If the receipts are current and the rows are
  old, we asked and the publisher had nothing to say - that is an observation, and it belongs in the
  record rather than in an alarm. If the RECEIPTS are old, we stopped asking, and that is ours.

  an unreadable check is UNKNOWN, never OK. A monitor that reports success when it cannot see is
  worse than no monitor, because it is trusted.

  the watchman cannot vouch for the time it was not running. Its ledger is append-only and every row
  carries the gap since the previous one, so a hole in the watching is visible as a hole rather than
  as an unbroken run of green.

Exit code: 0 everything current · 1 something late or unknown · 2 something stalled. The code is for
a human reading a terminal. Nothing in this project should ever trust it as evidence.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = ROOT / "data" / "live"
LEDGER = LIVE / "watch-ledger.jsonl"
PUBLIC = ROOT / "public" / "watch.json"
CADENCE_MIN = 10                      # the watchman's own schedule, for judging its own gaps

OK, LATE, STALLED, UNKNOWN = "ok", "late", "stalled", "unknown"
RANK = {OK: 0, LATE: 1, UNKNOWN: 1, STALLED: 2}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse(s):
    if not isinstance(s, str) or not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def mins(a: datetime, b: datetime) -> float:
    return round((a - b).total_seconds() / 60, 1)


def check(name: str, state: str, said: str, **extra) -> dict:
    return {"check": name, "state": state, "said": said, **extra}


# ---------------------------------------------------------------- the checks
def newest_receipt(sid: str):
    d = LIVE / "receipts" / sid
    if not d.is_dir():
        return None, "no receipts directory"
    files = sorted(d.glob("*.json"))
    if not files:
        return None, "no receipts"
    try:
        r = json.loads(files[-1].read_text(encoding="utf-8"))
    except Exception as e:                                        # noqa: BLE001
        return None, f"unreadable receipt: {type(e).__name__}"
    # attempted_at is the moment we asked, which is the only thing a receipt can honestly date; the
    # rest are fallbacks for older receipt shapes.
    t = parse(r.get("attempted_at") or r.get("completed_at") or r.get("receivedTime")
              or r.get("claimed_at") or r.get("at"))
    return (t, None) if t else (None, "receipt carries no time")


def newest_row(sid: str):
    d = LIVE / "rows" / sid
    if not d.is_dir():
        return None, "no rows directory"
    newest = None
    for f in sorted(d.glob("*.jsonl")):
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception as e:                                    # noqa: BLE001
            return None, f"unreadable rows: {type(e).__name__}"
        for line in reversed(lines[-400:]):
            if not line.strip():
                continue
            try:
                t = parse(json.loads(line).get("receivedTime"))
            except ValueError:
                continue
            if t and (newest is None or t > newest):
                newest = t
            break
    return (newest, None) if newest else (None, "no dated row")


def sources(now: datetime) -> list[dict]:
    try:
        cfg = json.loads((ROOT / "research" / "COLLECTORS.json").read_text(encoding="utf-8"))
    except Exception as e:                                        # noqa: BLE001
        return [check("sources", UNKNOWN, f"the collector list could not be read ({type(e).__name__})")]
    out = []
    for s in cfg["sources"]:
        if not s.get("enabled"):
            continue
        sid = s["sid"]
        cad = max(1, int(s.get("cadence_seconds") or 3600) // 60)
        rt, rerr = newest_receipt(sid)
        rowt, rowerr = newest_row(sid)
        if rt is None:
            out.append(check(f"source {sid}", UNKNOWN, f"we cannot tell whether we asked: {rerr}",
                             sid=sid, cadence_min=cad))
            continue
        asked = mins(now, rt)
        heard = mins(now, rowt) if rowt else None
        if asked > 6 * cad:
            state, said = STALLED, f"we stopped asking {asked:.0f} min ago (cadence {cad} min) - this is ours, not the publisher's"
        elif asked > 2 * cad:
            state, said = LATE, f"last asked {asked:.0f} min ago, over two cadences of {cad} min"
        elif heard is None:
            state, said = OK, f"asked {asked:.0f} min ago; nothing has ever arrived ({rowerr})"
        elif heard > 6 * cad:
            state, said = OK, f"asked {asked:.0f} min ago, silent for {heard:.0f} min - the source has nothing to say, which is a record and not a fault"
        else:
            state, said = OK, f"asked {asked:.0f} min ago, newest value {heard:.0f} min old"
        out.append(check(f"source {sid}", state, said, sid=sid, cadence_min=cad,
                         asked_min_ago=asked, heard_min_ago=heard))
    return out


def history(now: datetime) -> dict:
    p = ROOT / "public" / "history.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:                                        # noqa: BLE001
        return check("history", UNKNOWN, f"history.json could not be read ({type(e).__name__})")
    ends = str(d.get("history_ends") or "")
    t = parse(ends + ":00:00Z") if len(ends) == 13 else parse(ends)
    hours = d.get("hours_of_history")
    if t is None:
        return check("history", UNKNOWN, f"the newest hour could not be read from {ends!r}", hours=hours)
    behind = mins(now, t) / 60
    if behind > 4:
        state, said = STALLED, f"the newest hour is {behind:.1f} h behind; the history has stopped growing"
    elif behind > 2:
        state, said = LATE, f"the newest hour is {behind:.1f} h behind"
    else:
        state, said = OK, f"{hours} h of record, newest hour {behind:.1f} h behind"
    return check("history", state, said, hours=hours, newest_hour=ends, hours_behind=round(behind, 2))


def rows_total() -> dict:
    d = LIVE / "rows"
    if not d.is_dir():
        return check("rows", UNKNOWN, "the rows directory is not there")
    n = 0
    try:
        for f in d.rglob("*.jsonl"):
            with open(f, "rb") as fh:
                n += sum(1 for line in fh if line.strip())
    except Exception as e:                                        # noqa: BLE001
        return check("rows", UNKNOWN, f"the rows could not be counted ({type(e).__name__})")
    return check("rows", OK, f"{n} rows on disk", rows=n)


def published(now: datetime) -> dict:
    pub = ROOT.parent / "Beops-public"
    if not pub.is_dir():
        return check("published", UNKNOWN, "the published working copy is not where it was")
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cI %h"], capture_output=True, text=True,
                             cwd=pub, timeout=60).stdout.strip()
    except Exception as e:                                        # noqa: BLE001
        return check("published", UNKNOWN, f"git could not be asked ({type(e).__name__})")
    t = parse(out.split(" ")[0]) if out else None
    if t is None:
        return check("published", UNKNOWN, "the published commit has no readable time")
    age = mins(now, t)
    if age > 60:
        state, said = STALLED, f"the public site is {age:.0f} min old - the publish is not publishing"
    elif age > 25:
        state, said = LATE, f"the public site is {age:.0f} min old, past two publish cadences"
    else:
        state, said = OK, f"published {age:.0f} min ago"
    return check("published", state, said, age_min=age, commit=out.split(" ")[-1] if out else None)


def mind(now: datetime) -> dict:
    d = LIVE / "derived" / "mind"
    if not d.is_dir():
        return check("mind", UNKNOWN, "the mind's directory is not there")
    newest = None
    try:
        for f in sorted(d.glob("*.jsonl")):
            for line in reversed(f.read_text(encoding="utf-8", errors="replace").splitlines()[-200:]):
                if not line.strip():
                    continue
                try:
                    t = parse(json.loads(line).get("derivedTime") or json.loads(line).get("at"))
                except ValueError:
                    continue
                if t and (newest is None or t > newest):
                    newest = t
                break
    except Exception as e:                                        # noqa: BLE001
        return check("mind", UNKNOWN, f"the drops could not be read ({type(e).__name__})")
    if newest is None:
        return check("mind", UNKNOWN, "no dated drop")
    age = mins(now, newest)
    state = OK if age <= 30 else (LATE if age <= 120 else STALLED)
    return check("mind", state, f"newest drop {age:.0f} min ago", age_min=age)


def continuity(now: datetime) -> tuple[dict, dict | None]:
    """The watchman's own record. A gap here is a period nothing below can speak for."""
    prev = None
    if LEDGER.exists():
        try:
            for line in LEDGER.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.strip():
                    try:
                        prev = json.loads(line)
                    except ValueError:
                        continue
        except Exception:                                         # noqa: BLE001
            prev = None
    if prev is None:
        return check("watchman", UNKNOWN, "no earlier reading - this is the first, and it vouches for nothing before it"), None
    t = parse(prev.get("at"))
    if t is None:
        return check("watchman", UNKNOWN, "the previous reading has no readable time"), prev
    gap = mins(now, t)
    if gap > 3 * CADENCE_MIN:
        return check("watchman", LATE,
                     f"{gap:.0f} min since the last reading - nothing here speaks for that gap",
                     gap_min=gap), prev
    return check("watchman", OK, f"{gap:.0f} min since the last reading", gap_min=gap), prev


def rows_did_not_shrink(cur: dict, prev: dict | None) -> dict | None:
    """Rows are append-only. Retention empties a field; it never removes a line. A smaller count is
    data loss, and it is the one thing here that cannot be explained by a source going quiet."""
    if prev is None or "rows" not in cur:
        return None
    before = ((prev.get("figures") or {}).get("rows"))
    if not isinstance(before, int):
        return None
    if cur["rows"] < before:
        return check("rows kept", STALLED,
                     f"{before - cur['rows']} rows fewer than the last reading - the record lost lines",
                     before=before, after=cur["rows"])
    return check("rows kept", OK, f"{cur['rows'] - before} rows added since the last reading",
                 before=before, after=cur["rows"])


# ---------------------------------------------------------------- the run
def run(now: datetime | None = None) -> dict:
    now = now or now_utc()
    cont, prev = continuity(now)
    checks = [cont, published(now), history(now), mind(now)]
    rt = rows_total()
    checks.append(rt)
    kept = rows_did_not_shrink(rt, prev)
    if kept:
        checks.append(kept)
    checks += sources(now)
    states = {c["state"] for c in checks}
    if STALLED in states:
        verdict = STALLED
    elif LATE in states:
        verdict = LATE
    elif UNKNOWN in states:
        verdict = UNKNOWN            # not "fine": we could not see, and that is its own answer
    else:
        verdict = OK
    figures = {"rows": rt.get("rows"), "hours": next((c.get("hours") for c in checks if c["check"] == "history"), None)}
    return {"schema": "beops-watch/v1", "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "verdict": verdict,
            "counts": {s: sum(1 for c in checks if c["state"] == s) for s in (OK, LATE, STALLED, UNKNOWN)},
            "figures": figures,
            "not_current": sorted(c["check"] for c in checks if c["state"] != OK),
            "checks": checks}


def report(r: dict) -> str:
    L = [f"watchman {r['at']}  verdict: {r['verdict'].upper()}"]
    c = r["counts"]
    L.append(f"  {c[OK]} current · {c[LATE]} late · {c[STALLED]} stalled · {c[UNKNOWN]} unknown")
    for x in r["checks"]:
        if x["state"] != OK:
            L.append(f"  [{x['state']:<7}] {x['check']}: {x['said']}")
    quiet = [x for x in r["checks"] if x["state"] == OK and "which is a record and not a fault" in x["said"]]
    if quiet:
        L.append("  quiet, and asked: " + ", ".join(x["sid"] for x in quiet))
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="read and print, write nothing")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = run()
    print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else report(r))
    if not a.dry:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({k: r[k] for k in ("schema", "at", "verdict", "counts", "figures", "not_current")},
                               ensure_ascii=False) + "\n")
        PUBLIC.parent.mkdir(parents=True, exist_ok=True)
        PUBLIC.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    return {OK: 0, LATE: 1, UNKNOWN: 1, STALLED: 2}[r["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
