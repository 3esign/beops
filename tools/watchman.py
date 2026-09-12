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
from contracts import json_rows, exclusive, atomic_json
import pathlib
import subprocess
import permission_policy
import source_policy
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = ROOT / "data" / "live"
LEDGER = LIVE / "watch-ledger.jsonl"
PUBLIC = ROOT / "public" / "watch.json"
CADENCE_MIN = 10                      # the watchman's own schedule, for judging its own gaps

OK, LATE, STALLED, UNKNOWN = "ok", "late", "stalled", "unknown"
BLOCKED, PAUSED = 'blocked', 'paused'
RANK = {OK: 0, LATE: 1, UNKNOWN: 1, STALLED: 2, BLOCKED: 1, PAUSED: 1}


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
        # Keep attempt and outcome separate: a fresh HTTP failure is not a healthy source.
    if t and r.get("state") not in ("captured", "empty", "unchanged"):
        return t, f"{r.get('state', 'unknown')} (HTTP {r.get('http_status')}); {str(r.get('error') or '')[:100]}"
    return (t, None) if t else (None, "receipt carries no time")


def newest_row(sid: str):
    d = LIVE / "rows" / sid
    if not d.is_dir():
        return None, "no rows directory"
    newest = None
    for f in sorted(d.glob("*.jsonl")):
        try:
            for row in json_rows(f):
                t = parse(row.get('receivedTime'))
                if t and (newest is None or t > newest):
                    newest = t
        except Exception as e:                                    # noqa: BLE001
            return None, f"unreadable rows: {e}"
    return (newest, None) if newest else (None, "no dated row")


def sources(now: datetime) -> list[dict]:
    try:
        cfg = json.loads((ROOT / "research" / "COLLECTORS.json").read_text(encoding="utf-8"))
    except Exception as e:                                        # noqa: BLE001
        return [check("sources", UNKNOWN, f"the collector list could not be read ({type(e).__name__})")]
    out = []
    try:
        entries = permission_policy.latest(ROOT/'research/08-provenance/LEDGER.jsonl')
    except (OSError, ValueError) as exc:
        return [check('sources', UNKNOWN, f'permission record unreadable: {exc}')]
    for s in cfg["sources"]:
        if not s.get("enabled"):
            continue
        sid = s["sid"]
        cad = max(1, int(s.get("cadence_seconds") or 3600) // 60)
        state, reason = source_policy.decision(ROOT, LIVE, s, entries, now)
        if state != 'allowed':
            out.append(check(f'source {sid}', state, f'collection {state}: {reason}', sid=sid,
                             cadence_min=cad, network_requests=0))
            continue
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
        elif rerr:
            state, said = LATE, f"attempted {asked:.0f} min ago; last attempt {rerr}"
        elif heard is None:
            state, said = OK, f"asked {asked:.0f} min ago; nothing has ever arrived ({rowerr})"
        elif heard > 6 * cad:
            state, said = OK, f"asked {asked:.0f} min ago, silent for {heard:.0f} min - the source has nothing to say, which is a record and not a fault"
        else:
            state, said = OK, f"asked {asked:.0f} min ago, newest value {heard:.0f} min old"
        out.append(check(f"source {sid}", state, said, sid=sid, cadence_min=cad,
                         asked_min_ago=asked, heard_min_ago=heard))
    return out


def last_success():
    p = LIVE/'publish-last-success.json'
    d = json.loads(p.read_text(encoding='utf-8-sig'))
    if not all(d.get(k) is True for k in ('published', 'pushed', 'site_verified')):
        raise ValueError('publication not verified')
    if not d.get('site_live_hash') or d.get('site_live_hash') != d.get('site_local_hash'):
        raise ValueError('publication hash evidence missing or mismatched')
    if not d.get('remote_head') or not parse(d.get('site_checked_at')):
        raise ValueError('verification time or commit missing')
    return d


def history(now: datetime) -> dict:
    try:
        if (ROOT/'runtime/release-inputs.json').is_file():
            d = json.loads((ROOT/'public/history.json').read_text(encoding='utf-8'))
        else:
            receipt = last_success()
            d = receipt['verified_history']
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
    if (ROOT/'runtime/PUBLISH_PAUSED').exists():
        return check('published', PAUSED, 'publication explicitly paused by the operator; this is not a claim of current site data')
    try:
        receipt = last_success()
    except Exception as e:                                        # noqa: BLE001
        return check('published', UNKNOWN, f'last verified publication unavailable: {type(e).__name__}')
    t = parse(receipt.get('generated_as_of'))
    if t is None or t > now + timedelta(minutes=5):
        return check('published', UNKNOWN, 'publication has no valid input snapshot time')
    age = mins(now, t)
    if age > 60:
        state, said = STALLED, f"the public site is {age:.0f} min old - the publish is not publishing"
    elif age > 25:
        state, said = LATE, f"the public site is {age:.0f} min old, past two publish cadences"
    else:
        state, said = OK, f"last verified publication carries inputs {age:.0f} min old"
    try:
        attempt = json.loads((LIVE/'publish-receipt.json').read_text(encoding='utf-8-sig'))
        if not attempt.get('published') and (parse(attempt.get('at')) or t) > parse(receipt['site_checked_at']):
            state = STALLED if state == STALLED else LATE
            said += '; newer attempt failed; details in the local publication receipt'
    except (OSError, ValueError):
        state = STALLED if state == STALLED else UNKNOWN
        said += '; latest attempt unreadable'
    return check('published', state, said, age_min=age, commit=receipt['remote_head'],
                 verified_at=receipt['site_checked_at'])


def mind(now: datetime) -> dict:
    d = LIVE / "derived" / "mind"
    if not d.is_dir():
        return check("mind", UNKNOWN, "the mind's directory is not there")
    newest = None
    try:
        for f in sorted(d.glob("*.jsonl")):
            for row in json_rows(f):
                t = parse(row.get('derivedTime') or row.get('at'))
                if t and (newest is None or t > newest):
                    newest = t
    except Exception as e:                                        # noqa: BLE001
        return check("mind", UNKNOWN, f"the drops could not be read ({e})")
    if newest is None:
        return check("mind", UNKNOWN, "no dated drop")
    age = mins(now, newest)
    state = OK if age <= 30 else (LATE if age <= 120 else STALLED)
    return check("mind", state, f"newest drop {age:.0f} min ago", age_min=age)


def ai_feed(now: datetime) -> dict:
    config = ROOT / 'research/AI_FEED.json'
    if not config.exists():
        return check('AI observations', UNKNOWN, 'experimental feed is not configured')
    try:
        if not json.loads(config.read_text(encoding='utf-8')).get('enabled'):
            return check('AI observations', PAUSED, 'experimental feed is disabled')
        status = json.loads((ROOT/'runtime/ai-feed/status.json').read_text(encoding='utf-8'))
        tick_at, success = parse(status.get('at')), parse(status.get('last_success'))
        if tick_at is None or mins(now,tick_at) > 20:
            return check('AI observations', STALLED, 'no recent durable feed tick')
        if success is None or mins(now,success) > 60:
            return check('AI observations', LATE, 'no accepted monologue within one hour; '+str(status.get('state')), last_success=status.get('last_success'))
        return check('AI observations', OK, 'latest accepted monologue is within one hour', age_min=mins(now,success))
    except (OSError, ValueError) as exc:
        return check('AI observations', UNKNOWN, 'feed status unavailable: '+type(exc).__name__)


def continuity(now: datetime) -> tuple[dict, dict | None]:
    """The watchman's own record. A gap here is a period nothing below can speak for."""
    prev = None
    if LEDGER.exists():
        try:
            for row in json_rows(LEDGER):
                prev = row
        except (OSError, ValueError) as exc:
            return check('watchman', UNKNOWN, f'prior ledger unreadable: {exc}'), None
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
    checks = [cont, published(now), history(now), mind(now), ai_feed(now)]
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
    elif BLOCKED in states:
        verdict = BLOCKED
    elif PAUSED in states:
        verdict = PAUSED
    else:
        verdict = OK
    figures = {"rows": rt.get("rows"), "hours": next((c.get("hours") for c in checks if c["check"] == "history"), None)}
    return {"schema": "beops-watch/v1", "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "verdict": verdict,
            "counts": {s: sum(1 for c in checks if c["state"] == s) for s in RANK},
            "figures": figures,
            "not_current": sorted(c["check"] for c in checks if c["state"] != OK),
            "checks": checks}


def report(r: dict) -> str:
    L = [f"watchman {r['at']}  verdict: {r['verdict'].upper()}"]
    c = r["counts"]
    L.append(f"  {c[OK]} current · {c[LATE]} late · {c[STALLED]} stalled · {c[UNKNOWN]} unknown · {c[BLOCKED]} blocked · {c[PAUSED]} paused")
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
    ap.add_argument("--export", action="store_true", help="write a view of frozen inputs without appending a monitoring run")
    a = ap.parse_args()
    r = run()
    print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else report(r))
    if not a.dry:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        if not a.export:
            with exclusive(LIVE/'.write.lock'):
                with open(LEDGER, "a", encoding="utf-8") as f:
                    f.write(json.dumps({k: r[k] for k in ("schema", "at", "verdict", "counts", "figures", "not_current")},
                                       ensure_ascii=False) + "\n")
        PUBLIC.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(PUBLIC, r)
    return 0 if a.export else RANK[r['verdict']]


if __name__ == "__main__":
    raise SystemExit(main())
