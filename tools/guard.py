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

TASKS = ["Beops_Collect", "Beops_Mind", "Beops_Organ", "Beops_Publish", "Beops_Watch", "Beops_Legal"]
# A task that legitimately runs rarely must not be called dead for not having run in an hour.
MAX_SILENCE_H = {"Beops_Collect": 0.5, "Beops_Mind": 0.5, "Beops_Organ": 1.0,
                 "Beops_Publish": 1.0, "Beops_Watch": 1.0, "Beops_Legal": 36.0}

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


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def sh(args: list[str]) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=45,
                              encoding="utf-8", errors="replace").stdout or ""
    except Exception as e:                                   # noqa: BLE001
        return "ERROR " + type(e).__name__ + " " + str(e)


def task_state(name: str) -> dict:
    """Read one task through schtasks. A task we cannot read is unknown, never ok."""
    out = sh(["schtasks", "/query", "/tn", name, "/fo", "LIST", "/v"])
    if not out.strip() or "ERROR" in out[:6]:
        return {"task": name, "state": UNKNOWN, "why": "cannot be read"}
    f = {}
    for line in out.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            f.setdefault(k.strip().lower(), v.strip())
    status = f.get("status", "")
    scheduled = f.get("scheduled task state", "")
    last = f.get("last run time", "")
    result = f.get("last result", "")
    d = {"task": name, "status": status, "scheduled": scheduled, "last_run": last, "last_result": result}
    if scheduled.lower() == "disabled" or status.lower() == "disabled":
        d.update(state=WARN, why="disabled", fix="disabled")
        return d
    age = None
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%d.%m.%Y. %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            age = (datetime.now() - datetime.strptime(last, fmt)).total_seconds() / 3600.0
            break
        except ValueError:
            continue
    d["hours_since_last_run"] = None if age is None else round(age, 2)
    if age is None:
        d.update(state=UNKNOWN, why="last run time could not be read: " + last)
    elif age > MAX_SILENCE_H.get(name, 1.0) * 3:
        d.update(state=WARN, why=f"has not run for {age:.1f} h", fix="not running")
    elif age > MAX_SILENCE_H.get(name, 1.0):
        d.update(state=WARN, why=f"late by {age:.1f} h")
    else:
        d.update(state=OK, why=f"ran {age:.2f} h ago")
    return d


def repair(name: str, what: str) -> str:
    if what == "disabled":
        sh(["schtasks", "/change", "/tn", name, "/enable"])
    sh(["schtasks", "/run", "/tn", name])
    after = task_state(name)
    return f"{name}: {what} -> re-enabled and started; now {after.get('state')} ({after.get('why')})"


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
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("sid"):
                    led.add(r["sid"])
    except OSError:
        out.append({"check": "permission evidence", "state": UNKNOWN, "why": "ledger unreadable"})
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
        m = re.search(r"headline rows past 90 days\s*:\s*(\d+)", txt)
        due_m = re.search(r"first erasure falls due\s*:\s*(\S+)", txt)
        if r.returncode != 0 or m is None:
            out.append({"check": "retention", "state": UNKNOWN,
                        "why": "apply_retention did not report a plan"})
        elif int(m.group(1)) > 0:
            out.append({"check": "retention", "state": STOP,
                        "why": f"{m.group(1)} headline rows are past the 90-day window and have not "
                               f"been erased - run tools/apply_retention.py --apply"})
        else:
            out.append({"check": "retention", "state": OK,
                        "why": "nothing past the 90-day window" +
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
    try:
        age_h = (now() - datetime.fromisoformat(str(at).replace("Z", "+00:00"))).total_seconds() / 3600.0
    except ValueError:
        age_h = None
    out = []
    if r.get("tests_ok"):
        out.append({"check": "the publish is gated", "state": OK,
                    "why": "last publish ran the suite and it passed (%s)" % (r.get("tests") or "no summary")})
    else:
        state = STOP if (age_h is not None and age_h >= 0.5) else WARN
        out.append({"check": "the publish is gated", "state": state,
                    "why": "THE SUITE DID NOT PASS, so nothing has been published%s: %s"
                           % (" for %.1f h" % age_h if age_h is not None else "",
                              (r.get("why") or "")[:160])})
    if age_h is not None and age_h > 1.0 and r.get("tests_ok"):
        out.append({"check": "the publisher is still running", "state": WARN,
                    "why": "the last publish receipt is %.1f h old; the site may be frozen for a reason "
                           "this check cannot see" % age_h})
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
    legal = permission_invariants() + refusal_route() + publish_gate()
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
