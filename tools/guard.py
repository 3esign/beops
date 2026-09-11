#!/usr/bin/env python3
"""guard.py - the part that makes sure the rest is still running, and still allowed to.

The watchman answers "is the record current". This answers two different questions, every quarter of
an hour, and it is allowed to act on the first:

  1. Are the scheduled tasks still there, still enabled, and still firing? A task that was disabled,
     or that missed its window while the machine slept, is re-enabled and started. This is the only
     thing in the project that repairs rather than reports, and it repairs exactly one class of
     thing: a BEOPS task that exists and is not running.

  2. Are the ORGANS still producing, or do they at least say why not? A task can run on time, return
     success, and produce nothing - which is exactly what happened on 2026-09-10 between 00:38 and
     01:22: the mind ticked every four minutes, every tick failed to reach its model, and the task
     check, the watchman and this guard all said "ok" for forty-four minutes. The task was healthy.
     The organ was mute. Those had never been different questions here, so nobody could tell them
     apart. The guard does NOT repair this class either - an organ may be silent lawfully, and
     restarting one because it is quiet is how a record starts inventing.

  3. Is the collection still lawful? The permission invariants are re-checked from the files on every
     pass, not once in a test run that happened days ago: no named refusal is polled, every polled
     source has stored permission evidence, no polled source carries a status meaning it was never
     verified, and the retention clock is not overdue. If any of those fails the guard does NOT
     repair - it says STOP, loudly, in its ledger and on stdout, because a collector that has lost
     its permission must be stopped by a person who understands why.

Everything it does is appended to data/live/guard-ledger.jsonl. ASCII output only.
"""
from __future__ import annotations

import json
from contracts import json_rows
from permission_policy import MAX_AGE_HOURS
import pathlib
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = ROOT / "data" / "live"
LEDGER = LIVE / "guard-ledger.jsonl"
RESEARCH = ROOT / "research"

TASKS = ["Beops_Collect", "Beops_Mind", "Beops_Organ", "Beops_Publish", "Beops_Watch",
         "Beops_Legal", "Beops_Guard", "Beops_Baseline"]
# A task that legitimately runs rarely must not be called dead for not having run in an hour.
MAX_SILENCE_H = {"Beops_Collect": 0.5, "Beops_Mind": 0.5, "Beops_Organ": 1.0,
                 "Beops_Publish": 1.0, "Beops_Watch": 1.0, "Beops_Legal": float(MAX_AGE_HOURS),
                 "Beops_Guard": 0.5, "Beops_Baseline": 1.5}

# An organ is alive when it PRODUCES, not when its task exits zero. For each: where its rows land,
# where its receipts land, and how long it may go without a row before somebody should be told.
# A silence with a receipt that explains it is a WARN carrying the reason; a silence with no receipt
# at all is UNKNOWN, because then we do not even know whether it ran.
ORGANS = {
    "mind": {"rows": LIVE / "derived" / "mind", "receipts": LIVE / "derived" / "mind" / "receipts",
             "max_row_h": 1.0},
    "news": {"rows": LIVE / "derived" / "news", "receipts": LIVE / "derived" / "news" / "receipts",
             "max_row_h": 3.0},
}

OK, WARN, STOP, UNKNOWN = "ok", "warn", "STOP", "unknown"
REPAIRABLE = {"disabled", "not running"}

# What the scheduled publish is set to, and how long publish_github.ps1 waits before taking a lock
# over. A publish that runs longer than the first is queueing; longer than the second and the next
# publish will step over it.
PUBLISH_EVERY_MIN = 10.0
LOCK_TAKEOVER_MIN = 15.0


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def sh(args: list[str]) -> str:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=45,
                              encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if proc.returncode:
            return f"ERROR exit {proc.returncode}: {(proc.stderr or proc.stdout)[:200]}"
        return proc.stdout or ""
    except Exception as e:                                   # noqa: BLE001
        return "ERROR " + type(e).__name__ + " " + str(e)


def task_state(name: str) -> dict:
    """Read scheduler fields as JSON, independent of the Windows display language."""
    if name not in MAX_SILENCE_H:
        return {'task': name, 'state': UNKNOWN, 'why': 'unknown BEOPS task'}
    script = ("$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new(); "
              "$t=Get-ScheduledTask -TaskName '" + name + "'; "
              "$i=Get-ScheduledTaskInfo -TaskName '" + name + "'; "
              "[pscustomobject]@{status=[int]$t.State;enabled=[bool]$t.Settings.Enabled;"
              "last_run=$i.LastRunTime.ToUniversalTime().ToString('o');"
              "last_result=[long]$i.LastTaskResult} | ConvertTo-Json -Compress")
    out = sh(['powershell.exe', '-NoProfile', '-Command', script])
    try:
        fields = json.loads(out)
        if not isinstance(fields, dict) or not isinstance(fields.get('enabled'), bool):
            raise ValueError('missing scheduler fields')
        status, code = fields['status'], fields['last_result']
        if type(status) is not int or type(code) is not int:
            raise ValueError('invalid scheduler numeric fields')
        last = parse_iso(fields.get('last_run'))
        if last is None or last.tzinfo is None:
            raise ValueError('invalid scheduler clock')
    except (ValueError, KeyError, TypeError):
        return {'task': name, 'state': UNKNOWN, 'why': 'structured scheduler observation unavailable'}
    age = (now() - last).total_seconds() / 3600.0
    d = {'task': name, 'status': {3:'Ready',4:'Running',1:'Disabled'}.get(status, str(status)),
         'scheduled': 'Enabled' if fields['enabled'] else 'Disabled',
         'last_run': fields['last_run'], 'last_result': code, 'hours_since_last_run': round(age, 2)}
    if not fields['enabled'] or status == 1:
        d.update(state=WARN, why='disabled', fix='disabled')
    elif status == 4:
        d.update(state=OK, why='scheduler reports running; artefact checks determine the outcome')
    elif code == 267011:
        d.update(state=UNKNOWN, why='task has not yet run')
    elif code != 0:
        d.update(state=WARN, why=f'last execution failed with result {code}')
    elif age < -0.05:
        d.update(state=UNKNOWN, why='scheduler clock is in the future')
    elif age > MAX_SILENCE_H[name] * 3:
        d.update(state=WARN, why=f'has not run for {age:.1f} h', fix='not running')
    elif age > MAX_SILENCE_H[name]:
        d.update(state=WARN, why=f'late by {age:.1f} h')
    else:
        d.update(state=OK, why=f'ran {age:.2f} h ago with result 0; artefact checks determine success')
    return d


def repair(name: str, what: str) -> str:
    if (ROOT / "runtime" / "PAUSED").exists() or (ROOT / "runtime" / "pauses" / name).exists():
        return f"{name}: operator pause respected"
    if what == "disabled":
        return f"{name}: disabled task requires an explicit operator resume"
    result = sh(["schtasks", "/run", "/tn", name])
    if result.startswith("ERROR"):
        return f"{name}: start failed: {result}"
    after = task_state(name)
    return f"{name}: start requested; now {after.get('state')} ({after.get('why')})"


def permission_invariants() -> list[dict]:
    """The four claims the whole record rests on, checked from the files, every pass."""
    out = []
    try:
        col = json.loads((RESEARCH / "COLLECTORS.json").read_text(encoding="utf-8"))
        reg = json.loads((RESEARCH / "SOURCE_REGISTRY.json").read_text(encoding="utf-8"))
    except Exception as e:                                   # noqa: BLE001
        return [{"check": "permission files", "state": UNKNOWN, "why": type(e).__name__}]
    polled = {s["sid"] for s in col["sources"] if s.get("enabled")}
    status = {s.get("id"): s.get("status") for s in reg["sources"]}

    refused = sorted(sid for sid in polled if status.get(sid) == "opted_out")
    n_ref = sum(1 for s in reg["sources"] if s.get("status") == "opted_out")
    out.append({"check": "no named refusal is polled", "state": STOP if refused else OK,
                "why": ("POLLING A REFUSAL: " + ", ".join(refused)) if refused
                       else "%d refusals on file, none of them polled" % n_ref})

    led = set()
    p = RESEARCH / "08-provenance" / "LEDGER.jsonl"
    try:
        for r in json_rows(p):
            if r.get('sid'):
                led.add(r['sid'])
    except (OSError, ValueError) as exc:
        out.append({"check": "permission evidence", "state": UNKNOWN, "why": f"ledger unreadable: {exc}"})
        led = None
    if led is not None:
        missing = sorted(polled - led)
        out.append({"check": "every polled source has stored permission evidence",
                    "state": STOP if missing else OK,
                    "why": ("no evidence for: " + ", ".join(missing)) if missing
                           else f"all {len(polled)} polled sources have a ledger line"})

    unsettled = sorted(f"{s}={status.get(s)}" for s in polled
                       if status.get(s) in {"lead", "primary_page", "needs_decision", "restricted",
                                            "blocked", "account_required", "token_required"})
    out.append({"check": "no polled source is in an unverified or unsettled state",
                "state": STOP if unsettled else OK,
                "why": ("unsettled: " + ", ".join(unsettled)) if unsettled else "all polled sources verified"})

    # The retention clock is not a date in a file - it is a plan computed from what is actually
    # held. apply_retention.py already computes it, so the guard asks it rather than keeping a second
    # copy of the arithmetic that could drift from the first.
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", "-B",
                            str(ROOT / "tools" / "apply_retention.py")],
                           capture_output=True, text=True, timeout=60,
                           encoding="utf-8", errors="replace")
        txt = (r.stdout or "") + (r.stderr or "")
        m = re.search(r"headline rows (?:past 90 days|due by policy)\s*:\s*(\d+)", txt)
        raw_due = re.search(r"raw news captures past 90 d\s*:\s*(\d+)", txt)
        due_m = re.search(r"first erasure falls due\s*:\s*(\S+)", txt)
        if r.returncode != 0 or m is None:
            out.append({"check": "retention", "state": UNKNOWN,
                        "why": "apply_retention did not report a plan"})
        elif int(m.group(1)) > 0 or (raw_due and int(raw_due.group(1)) > 0):
            out.append({"check": "retention", "state": STOP,
                        "why": f"retention due: {m.group(1)} headline rows and {raw_due.group(1) if raw_due else 'unknown'} raw payloads; apply the current policy"})
        else:
            out.append({"check": "retention", "state": OK,
                        "why": "no erasure due under the current retention policy" +
                               (f"; first erasure falls due {due_m.group(1)}" if due_m else "")})
    except Exception as e:                                   # noqa: BLE001
        out.append({"check": "retention", "state": UNKNOWN, "why": type(e).__name__})
    return out


def _newest(d: pathlib.Path, pattern: str = "*") -> tuple[float | None, pathlib.Path | None]:
    """(age in hours, path) of the most recently written file, or (None, None)."""
    if not d.exists():
        return None, None
    best, bp = None, None
    for f in d.glob(pattern):
        if not f.is_file():
            continue
        a = (now().timestamp() - f.stat().st_mtime) / 3600.0
        if best is None or a < best:
            best, bp = a, f
    return best, bp


def _last_receipt_reason(d: pathlib.Path) -> str:
    """What the organ said about itself last, in its own words."""
    _, f = _newest(d, "*.json")
    if not f:
        return ""
    try:
        r = json.loads(f.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return ""
    bits = [str(r.get("state") or ""), str(r.get("step_name") or ""), str(r.get("reason") or "")]
    return " ".join(b for b in bits if b)[:120]


def organ_output() -> list[dict]:
    """Did each organ actually produce, and if not, does it say why? Reports; never repairs."""
    out = []
    for name, cfg in ORGANS.items():
        row_h, row_f = _newest(cfg["rows"], "*.jsonl")
        tick_h, _ = _newest(cfg["receipts"], "*")
        limit = float(cfg["max_row_h"])
        if row_h is None:
            state, why = UNKNOWN, "no rows have ever been written"
        elif row_h <= limit:
            state, why = OK, "last row %.1f h ago (limit %.1f h)" % (row_h, limit)
        elif tick_h is not None and tick_h <= limit:
            reason = _last_receipt_reason(cfg["receipts"])
            state = WARN
            why = ("no row for %.1f h but it is still ticking (last receipt %.1f h ago): %s"
                   % (row_h, tick_h, reason or "the receipt gives no reason"))
        else:
            state = UNKNOWN
            why = ("no row for %.1f h and no receipt either%s - the organ is not merely quiet, "
                   "it is not running" % (row_h, "" if tick_h is None else " for %.1f h" % tick_h))
        out.append({"organ": name, "state": state, "why": why,
                    "row_age_h": None if row_h is None else round(row_h, 2),
                    "tick_age_h": None if tick_h is None else round(tick_h, 2)})
    return out


def _fold(s: str) -> str:
    """Diacritics folded, so a rule written as 'Gradska cistoca' still sees 'Gradska cistoca' spelled
    the way a Serbian newspaper spells it. A check that only matches one spelling is not a check."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    # d-with-stroke does not decompose under NFKD, so it needs saying out loud.
    return s.replace("đ", "d").replace("Đ", "D").lower()


def refusal_route() -> list[dict]:
    """A refusal is a refusal to be OUR SOURCE. It is not a censorship of the world.

    Three organisations that told us no - MUP, JKP Beograd-put, JKP Gradska cistoca - have their
    notices republished by municipalities, by the City portal and by the outlets, so their material
    reaches this record anyway. Collecting that is lawful: it is the third party's own publication.
    What must never happen is that the route becomes a way to obtain what the refuser withheld, or
    that the refuser is presented as having supplied us with anything.

    So: a mention inside somebody else's headline is PERMITTED and counted here, out loud, because a
    number that is never printed is not an invariant. A refuser appearing as the source, the sid or
    the attribution of anything we publish is a STOP.

    See research/07-legal/THIRD_PARTY_ROUTE_RULE_2026-09-10.md."""
    out = []
    try:
        reg = json.loads((RESEARCH / "SOURCE_REGISTRY.json").read_text(encoding="utf-8"))
    except Exception as e:                                   # noqa: BLE001
        return [{"check": "third-party route", "state": UNKNOWN, "why": type(e).__name__}]
    refusers = {s.get("id"): (s.get("name") or "") for s in reg["sources"] if s.get("status") == "opted_out"}
    try:
        rule = json.loads((RESEARCH / "REFUSER_NAMES.json").read_text(encoding="utf-8"))
        watch = {_fold(k): v for k, v in rule.get("names", {}).items()}
    except Exception:                                        # noqa: BLE001
        watch = {}

    snap_p = ROOT / "public" / "live-snapshot.json"
    if not snap_p.exists():
        return [{"check": "a named refusal is never our source", "state": UNKNOWN,
                 "why": "no published snapshot to read"}]
    try:
        snap = json.loads(snap_p.read_text(encoding="utf-8"))
    except ValueError as e:
        return [{"check": "a named refusal is never our source", "state": UNKNOWN, "why": str(e)[:60]}]

    as_source = sorted({s.get("sid") for s in snap.get("sources", []) if s.get("sid") in refusers})
    for row in snap.get("derived", []):
        if row.get("input_sid") in refusers or row.get("sid") in refusers:
            as_source.append(str(row.get("input_sid") or row.get("sid")))
    as_source = sorted(set(as_source))
    out.append({"check": "a named refusal is never our source",
                "state": STOP if as_source else OK,
                "why": ("A REFUSER IS ATTRIBUTED AS OUR SOURCE: " + ", ".join(as_source)) if as_source
                       else "%d refusals on file, none of them a source, a sid or an attribution here"
                            % len(refusers)})

    if not watch:
        out.append({"check": "a refusal reached by another route stays the third party's utterance",
                    "state": UNKNOWN, "why": "research/REFUSER_NAMES.json is missing, so nothing is watched for"})
        return out

    named, unattributed = {}, []
    for s in snap.get("sources", []):
        sid = s.get("sid")
        if sid in refusers:
            continue
        for e in s.get("events", []):
            f = _fold(e.get("title") or "")
            for name, rid in watch.items():
                if name in f:
                    named.setdefault(rid, 0)
                    named[rid] += 1
                    if not (e.get("link") or "").strip() or not sid:
                        unattributed.append("%s via %s" % (rid, sid or "?"))
    total = sum(named.values())
    out.append({"check": "a refusal reached by another route stays the third party's utterance",
                "state": STOP if unattributed else OK,
                "why": ("UNATTRIBUTED: " + ", ".join(sorted(set(unattributed))[:6])) if unattributed
                       else ("%d refuser(s) named in %d headline(s), every one carrying the outlet that "
                             "wrote it and its link" % (len(named), total) if total
                             else "no refuser is named in any published headline right now")})
    return out


def publish_gate() -> list[dict]:
    """Did the last publish run the tests, and did they pass.

    Until 2026-09-10 the scheduled publish rebuilt the site and pushed it without running a single
    test: the gate protected the manual path and not the one that fires every ten minutes. The gate
    now lives inside the publisher, and this check reads the receipt it leaves - because a gate that
    stops the site silently has only exchanged one failure for a quieter one. That is the lesson
    C-036 bought for the organs, applied to the publisher.

    A suite that has just failed is a WARN: one flake should not scream. Half an hour of it - three
    ticks - is a STOP, because by then the public page is being kept deliberately stale and somebody
    has to know."""
    p = LIVE / "publish-receipt.json"
    if not p.exists():
        return [{"check": "the publish is gated", "state": UNKNOWN,
                 "why": "no publish receipt yet: the publisher has not run since the gate was added"}]
    try:
        # The receipt is written by PowerShell, whose -Encoding UTF8 on 5.1 means UTF-8 WITH A BOM.
        # Read as plain utf-8 the BOM survives as \ufeff and json refuses the first character, which
        # is how this check reported "unknown" against a receipt that was perfectly well-formed on
        # its very first run. utf-8-sig eats a BOM if there is one and is identical if there is not.
        r = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:                       # noqa: BLE001
        return [{"check": "the publish is gated", "state": UNKNOWN, "why": "receipt unreadable: %s" % type(e).__name__}]
    at = r.get("at") or ""
    at_dt = parse_iso(str(at))
    now_dt = now()
    age_h = None if at_dt is None else (now_dt - at_dt).total_seconds() / 3600.0
    out = []
    complete = all(r.get(k) is True for k in ("tests_ok", "pushed", "site_verified", "published"))
    if complete:
        out.append({"check": "the publish is gated", "state": OK,
                    "why": "last publish ran the suite and it passed (%s)" % (r.get("tests") or "no summary")})
    else:
        try:
            start_dt = publish_failure_started_at(at_dt)
        except (OSError, ValueError) as exc:
            out.append({'check': 'publish failure history', 'state': UNKNOWN, 'why': str(exc)})
            start_dt = None
        fail_h = None if start_dt is None else (now_dt - start_dt).total_seconds() / 3600.0
        state = STOP if (fail_h is not None and fail_h >= 0.5) else WARN
        out.append({"check": "the publish is gated", "state": state,
                    "why": ("THE SUITE DID NOT PASS" if not r.get("tests_ok") else "PUBLICATION INCOMPLETE") + ", no verified publication%s: %s"
                           % (" for %.1f h" % fail_h if fail_h is not None else "",
                              (r.get("why") or "")[:160])})
    if age_h is not None and age_h > 1.0 and r.get("tests_ok"):
        out.append({"check": "the publisher is still running", "state": WARN,
                    "why": "the last publish receipt is %.1f h old; the site may be frozen for a reason "
                           "this check cannot see" % age_h})

    # A publisher that has STOPPED is caught above, by the age of its receipt. A publisher that is
    # STUCK is a different thing and was invisible: on 2026-09-10 one held the lock for more than
    # thirteen minutes, longer than the interval between publishes, and nothing anywhere said so. The
    # lock is taken over after a quarter of an hour, so this never stops the record - but a publish
    # taking longer than the gap between publishes means they are queueing, and a queue nobody
    # mentions is how "it publishes every ten minutes" quietly stops being true.
    lock = ROOT / "runtime" / "publish.lock"
    if lock.exists():
        try:
            held_m = (now() - datetime.fromtimestamp(lock.stat().st_mtime, timezone.utc)).total_seconds() / 60.0
        except OSError:
            held_m = None
        if held_m is None:
            out.append({"check": "a publish is not stuck", "state": UNKNOWN,
                        "why": "there is a publish lock and its age cannot be read"})
        elif held_m > PUBLISH_EVERY_MIN:
            out.append({"check": "a publish is not stuck", "state": WARN,
                        "why": "a publish has held the lock for %.1f min, longer than the %.0f min "
                               "between publishes, so publishes are queueing behind it%s"
                               % (held_m, PUBLISH_EVERY_MIN,
                                  "; the next one will take the lock over" if held_m > LOCK_TAKEOVER_MIN
                                  else "")})
    return out


def publish_failure_started_at(current_receipt_at: datetime | None) -> datetime | None:
    """Return the start of the current continuous failed-publish streak, if visible."""
    if current_receipt_at is None:
        return None
    started = current_receipt_at
    p = LIVE / "guard-ledger.jsonl"
    for row in reversed(list(json_rows(p))):
        check = None
        for item in row.get("lawful", []):
            if item.get("check") == "the publish is gated":
                check = item
                break
        if not check:
            continue
        why = str(check.get("why") or "")
        failed = check.get("state") in (WARN, STOP) and why.startswith(("THE SUITE DID NOT PASS", "PUBLICATION INCOMPLETE"))
        if not failed:
            break
        row_at = parse_iso(str(row.get("at") or ""))
        if row_at is not None:
            started = row_at
    return started


# A prediction is scored within 24 minutes of falling due, over the 29 settled so far, and never
# later. Three hours is seven times the worst observed lag: past it, nobody scored it.
CLAIM_GRACE_H = 3.0


def predictions() -> list[dict]:
    """Whether any prediction the mind made fell due and was never scored.

    A record that keeps only the predictions that came true is not a record of predictions, so this
    is worth watching. It is a WARN and never a STOP, and the reason is the architecture: the organs
    are separate, and the record of the city's air has nothing to do with whether the language layer
    scored its own claim. A check that stopped publishing over an unscored prediction would be doing
    more damage than the fault it reports (C-066).
    """
    p = ROOT / "data" / "live" / "derived" / "mind" / "claims.jsonl"
    if not p.exists():
        return []
    open_late, n = [], 0
    try:
        for r in json_rows(p):
            n += 1
            if r.get("outcome") is not None:
                continue
            try:
                due = datetime.fromisoformat(str(r.get("due")).replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError('claim has no valid due time') from exc
            late_h = (now() - due).total_seconds() / 3600.0
            if late_h > CLAIM_GRACE_H:
                open_late.append("%s due %s (%.1f h ago)" % (r.get("entity"), r.get("due"), late_h))
    except (OSError, ValueError, TypeError) as e:
        return [{"check": "no prediction was left unscored", "state": UNKNOWN,
                 "why": "the claims register could not be read: %s" % e}]
    if not n:
        return []
    return [{"check": "no prediction was left unscored",
             "state": WARN if open_late else OK,
             "why": ("UNSCORED: " + "; ".join(sorted(open_late)[:4])) if open_late
                    else "%d claims on file, every one past its due time scored" % n}]


def static_layers() -> list[dict]:
    """The layers that are not a stream: a basemap and a population grid, each a dated RELEASE of
    somebody else's dataset.

    Age is the wrong question for them. The Sava does not move, and a 2022 population grid is not
    stale at 34 hours and would not be at 34 weeks - an age limit would report a fault every day and
    mean nothing on the day something actually changed. But silence about them is indistinguishable
    from neglect, which is the state they were in until now. So four questions instead:

      is it still there and readable; is it still the file we accepted (a change is not wrong, but it
      must be noticed and re-accepted rather than absorbed); does it still carry the source, licence
      and attribution under which we may show it; and has anybody looked for a newer release lately.

    The attribution one is the load-bearing one. context-population.json is CC BY 4.0 and its
    attribution lives inside the file: if a refetch drops it we are publishing somebody's dataset
    unattributed, which is Article 41 for data rather than for headlines - the same defect the news
    layer had until it became a test."""
    reg = RESEARCH / "STATIC_LAYERS.json"
    if not reg.exists():
        return [{"check": "static layers", "state": UNKNOWN, "why": "no research/STATIC_LAYERS.json"}]
    try:
        d = json.loads(reg.read_text(encoding="utf-8"))
    except ValueError as e:
        return [{"check": "static layers", "state": UNKNOWN, "why": "register unreadable: %s" % type(e).__name__}]

    import hashlib
    missing, changed, unattributed, due = [], [], [], []
    for L in d.get("layers", []):
        f = ROOT / str(L.get("file") or "")
        name = f.name
        if not f.exists():
            missing.append(name)
            continue
        raw = f.read_bytes()
        if L.get("sha256") and hashlib.sha256(raw).hexdigest() != L["sha256"]:
            changed.append(name)
        try:
            doc = json.loads(raw.decode("utf-8"))
        except Exception:                                    # noqa: BLE001
            missing.append(name + " (unreadable)")
            continue
        for k in L.get("must_carry") or []:
            if not str((doc or {}).get(k) or "").strip():
                unattributed.append("%s has lost its %s" % (name, k))
        # and the page that uses it has to show that attribution, not merely hold it in a file
        # What a licence requires is the CREDIT, not a form of words. The first version of this check
        # cut the attribution string at its first full stop and demanded that phrase, so it asked for
        # "Made with Natural Earth" from a page that says "Natural Earth 1:10 mil." and reported three
        # correctly attributed pages as unattributed. The register names the credit instead.
        for page in sorted((ROOT / "docs").glob("*.html")):
            try:
                body = page.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if name not in body:
                continue
            for key in L.get("must_be_named") or []:
                if key not in body:
                    unattributed.append("%s uses %s and does not name %s" % (page.name, name, key))
        rd = str(L.get("review_due") or "")
        if rd and rd < now().date().isoformat():
            due.append("%s (due %s)" % (name, rd))

    out = []
    out.append({"check": "static layers are present and still the file we accepted",
                "state": STOP if missing else (WARN if changed else OK),
                "why": ("MISSING: " + ", ".join(missing)) if missing else
                       ("changed since it was accepted, re-accept it deliberately: " + ", ".join(changed)) if changed
                       else "%d layers, each the file recorded in the register" % len(d.get("layers", []))})
    out.append({"check": "every static layer is named where it is shown",
                "state": STOP if unattributed else OK,
                "why": ("UNATTRIBUTED: " + "; ".join(unattributed[:4])) if unattributed
                       else "source, licence and attribution present in each file and on every page that uses it"})
    if due:
        out.append({"check": "somebody should look for a newer release", "state": WARN,
                    "why": "review date passed for " + ", ".join(due)})
    return out


def run(dry: bool = False) -> dict:
    checks, repairs = [], []
    for name in TASKS:
        d = task_state(name)
        if d.get("fix") in REPAIRABLE and not dry:
            repairs.append(repair(name, d["fix"]))
            d = task_state(name)
            d["repaired"] = True
        checks.append(d)
    legal = permission_invariants() + refusal_route() + publish_gate() + static_layers() + predictions()
    organs = organ_output()
    states = [c["state"] for c in checks] + [c["state"] for c in legal] + [c["state"] for c in organs]
    verdict = STOP if STOP in states else (UNKNOWN if UNKNOWN in states else
                                           (WARN if WARN in states else OK))
    return {"schema": "beops-guard/v1", "at": iso(now()), "verdict": verdict,
            "tasks": checks, "lawful": legal, "organs": organs, "repairs": repairs}


def report(r: dict) -> str:
    L = [f"guard {r['at']}  verdict: {r['verdict']}"]
    for c in r["tasks"]:
        L.append(f"  [{c['state']:<7}] {c['task']:<15} {c.get('why','')}")
    for c in r["lawful"]:
        L.append(f"  [{c['state']:<7}] {c['check']}: {c['why']}")
    for c in r.get("organs", []):
        L.append(f"  [{c['state']:<7}] organ {c['organ']}: {c['why']}")
    for x in r["repairs"]:
        L.append("  repaired: " + x)
    if r["verdict"] == STOP:
        L.append("  STOP means a permission claim no longer holds. Do not restart collection until a")
        L.append("  person has read the line above and decided. The guard does not repair this class.")
    return "\n".join(L)


def main() -> int:
    dry = "--dry" in sys.argv
    r = run(dry)
    print(report(r))
    if not dry:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return 0 if r["verdict"] in (OK, WARN) else 1


if __name__ == "__main__":
    raise SystemExit(main())
