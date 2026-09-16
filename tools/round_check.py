#!/usr/bin/env python3
"""round_check.py - did the repair round of 2026-09-16 really happen?

A repair is not finished when a command exits 0 or a status line says "closed". It is finished when
the artefacts that a reader, a publisher or the next mind will meet show it. This tool reads those
artefacts, and only those, and says for each promised result one of:

  PASS     the artefact shows it
  FAIL     the artefact shows the opposite, or the result is missing
  PENDING  the change is in place, but the evidence can only exist later (a new receipt, a new
           AI entry, a publication, enough mind rows) - it is not a pass
  UNKNOWN  the artefact could not be read - never counted as a pass

The steps are the agreed order of the round:
  0  honest identity to every source (C-070)             - done 2026-09-15, re-checked here
  1  the remediation register says only what is proven
  2  D-003: every model is named in public; the AI panel's population fact is not "the City"
  3  the mind: numbers keep their roles, the Serbian voice is not lost to a timeout
  4  the watch shows 24-hour coverage

Usage
  python -B tools/round_check.py                 all steps, human report
  python -B tools/round_check.py --step 1 --json one step, machine report
  python -B tools/round_check.py --live          also read the published site (network)

Exit code: 0 when no requested check is FAIL or UNKNOWN (PENDING is allowed and printed), 1 otherwise.
Read-only: it writes nothing, fetches nothing unless --live, and changes no state.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = ROOT / "data" / "live"
TOKEN = "Beops-Research-Collect/1.0"
PASS, FAIL, PENDING, UNKNOWN = "PASS", "FAIL", "PENDING", "UNKNOWN"
BACKLOG = ROOT / "research" / "01-programme" / "REMEDIATION_BACKLOG_2026-09-14.json"
PUBLIC_SITE = "https://3esign.github.io/beops/"
D003_NAMES = ("Gemini", "qwen3.5:4b", "qwen2.5:1.5b", "llama3.2:1b", "paraphrase-multilingual",
              "qwen2.5:3b", "Claude", "Codex")
MIN_MIND_ROWS = 10          # accepted thoughts needed before the mind step can PASS
MAX_VOICE_TIMEOUT_SHARE = 0.10


def result(check: str, state: str, said: str, **extra) -> dict:
    return {"check": check, "state": state, "said": said, **extra}


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip()[:200])
    return p.stdout.strip()


def commit_time(path: str) -> datetime | None:
    """When the newest commit that touched `path` was made - the moment a fix became the source."""
    out = git("log", "-1", "--format=%cI", "--", path)
    return datetime.fromisoformat(out) if out else None


def parse(t) -> datetime | None:
    if not t or not isinstance(t, str):
        return None
    try:
        d = datetime.fromisoformat(t.replace("Z", "+00:00"))
    except ValueError:
        try:
            d = datetime.strptime(t, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def jsonl(path: pathlib.Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8-sig") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def guarded(fn):
    """A check that cannot read its artefact answers UNKNOWN, never PASS."""
    def run(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as e:  # noqa: BLE001
            return [result(fn.__name__, UNKNOWN, f"could not read the artefact: {type(e).__name__}: {str(e)[:160]}")]
    run.__name__ = fn.__name__
    return run


def enabled_collectors() -> list[dict]:
    return [s for s in json.loads(text("research/COLLECTORS.json"))["sources"] if s.get("enabled", True)]


# ------------------------------------------------------------------ step 0: honest identity
@guarded
def step0() -> list[dict]:
    out = []
    nf = text("tools/net_fetch.js")
    ok = "incognito" not in nf.lower() and TOKEN in nf
    out.append(result("0.1 transport names the observatory", PASS if ok else FAIL,
                      "tools/net_fetch.js carries the fixed identity and loads no persona" if ok
                      else "tools/net_fetch.js still loads a persona or lacks the identity"))
    has = "## C-070" in text("research/08-provenance/CORRECTIONS.md")
    out.append(result("0.2 correction is on the record", PASS if has else FAIL,
                      "C-070 is in CORRECTIONS.md" if has else "C-070 is missing from CORRECTIONS.md"))
    import permission_policy
    latest = permission_policy.latest(ROOT / "research" / "08-provenance" / "LEDGER.jsonl")
    wrong, missing = [], []
    for s in enabled_collectors():
        e = latest.get(s["sid"]) or {}
        if not e.get("evidence_dir") or e.get("manual_verdict") in ("refused", "needs_decision"):
            continue
        m = ROOT / e["evidence_dir"] / "MANIFEST.json"
        if not m.exists():
            missing.append(s["sid"])
            continue
        ua = json.loads(m.read_text(encoding="utf-8")).get("user_agent") or ""
        if not ua.startswith(TOKEN):
            wrong.append(f"{s['sid']} ({ua[:30]})")
    state = FAIL if wrong else (UNKNOWN if missing else PASS)
    out.append(result("0.3 current permission captures were taken under the real name", state,
                      f"not under the real name: {', '.join(wrong)}" if wrong else
                      (f"manifest missing for {', '.join(missing)}" if missing else
                       "every current capture of a polled source names Beops-Research-Collect/1.0")))
    since = commit_time("tools/net_fetch.js")
    bad, none = [], []
    for s in enabled_collectors():
        if (latest.get(s["sid"]) or {}).get("allowed_for_us") is not True:
            continue        # not permitted now: the collector sends nothing, so there is no identity to check
        d = LIVE / "receipts" / s["sid"]
        rec = sorted(d.glob("*.json")) if d.is_dir() else []
        after = []
        for f in rec[-5:]:
            r = json.loads(f.read_text(encoding="utf-8"))
            if r.get("network_requests") and (parse(r.get("attempted_at")) or since) > since:
                after.append(r)
        if not after:
            none.append(s["sid"])
            continue
        if any(not str(r.get("request_user_agent") or "").startswith(TOKEN) for r in after):
            bad.append(s["sid"])
    if bad:
        out.append(result("0.4 receipts after the fix record the real name", FAIL, "wrong or missing identity: " + ", ".join(bad)))
    elif none:
        out.append(result("0.4 receipts after the fix record the real name", PENDING,
                          f"no network receipt yet after the fix for: {', '.join(none)}"))
    else:
        out.append(result("0.4 receipts after the fix record the real name", PASS, "every polled source's newest receipts name the observatory"))
    return out


# ------------------------------------------------------------------ step 1: the register
def register_findings(backlog: dict, commit_exists, file_exists) -> list[dict]:
    """Pure: which tasks claim a completion the record does not carry."""
    tasks = {t["id"]: t for t in backlog["tasks"]}
    done = ("closed", "verified")
    problems = []
    for t in backlog["tasks"]:
        if t.get("status") not in done:
            continue
        why = []
        if not t.get("source_commit"):
            why.append("no source commit")
        elif not commit_exists(t["source_commit"]):
            why.append("source commit not in the repository")
        ev = t.get("local_evidence") or []
        if not ev:
            why.append("no evidence")
        elif any(not file_exists(p) for p in ev):
            why.append("evidence file missing")
        if not parse(t.get("closed_at")):
            why.append("no closing time")
        open_deps = [d for d in t.get("depends_on") or [] if tasks.get(d, {}).get("status") not in done]
        if open_deps:
            why.append("depends on open " + "/".join(open_deps))
        if why:
            problems.append({"id": t["id"], "why": why})
    return problems


@guarded
def step1() -> list[dict]:
    b = json.loads(BACKLOG.read_text(encoding="utf-8-sig"))

    def exists(c):
        try:
            git("cat-file", "-e", c + "^{commit}")
            return True
        except RuntimeError:
            return False
    problems = register_findings(b, exists, lambda p: (ROOT / p).exists())
    out = [result("1.1 nothing is closed without commit, evidence, time and closed dependencies",
                  FAIL if problems else PASS,
                  "; ".join(f"{p['id']}: {', '.join(p['why'])}" for p in problems) or "every closed task carries its proof",
                  problems=problems)]
    r11 = next(t for t in b["tasks"] if t["id"] == "R11")
    mind_ok = all(c["state"] == PASS for c in step3_static())
    if r11.get("status") in ("closed", "verified") and not mind_ok:
        out.append(result("1.2 R11 is not closed while its counter-example still passes", FAIL, "R11 closed, step 3 checks do not pass"))
    else:
        out.append(result("1.2 R11 is not closed while its counter-example still passes", PASS, f"R11 status {r11.get('status')}"))
    reopened = [t["id"] for t in b["tasks"] if "reopened" in str(t.get("agent_note") or "").lower()]
    out.append(result("1.3 every reopened task says why", PASS if all(
        len(str(t.get("agent_note"))) > 40 for t in b["tasks"] if t["id"] in reopened) else FAIL,
        f"reopened with a reason: {', '.join(reopened) or 'none'}"))
    return out


# ------------------------------------------------------------------ step 2: D-003 and the AI panel
def d003_ok(decisions: str) -> list[str]:
    m = re.search(r"^## D-003\b(.*?)(?=^## D-\d+|\Z)", decisions, re.S | re.M)
    if not m:
        return ["D-003 missing"]
    return [n for n in D003_NAMES if n not in m.group(1)]


def footer_block(site_builder: str) -> str:
    i = site_builder.find("Where this runs")
    return site_builder[i:i + 6000] if i >= 0 else ""


@guarded
def step2(live: bool = False) -> list[dict]:
    out = []
    miss = d003_ok(text("research/DECISIONS.md"))
    out.append(result("2.1 D-003 names every model", FAIL if miss else PASS,
                      "missing: " + ", ".join(miss) if miss else "D-003 names all runtime and development models"))
    blk = footer_block(text("tools/build_site.py"))
    langs = sum(1 for cls in ("sr-only", "en-only", "zh-only", "de-only")
                if re.search(r'class="%s[^"]*">[^<]*Gemini' % cls, blk))
    out.append(result("2.2 'Where this runs' names Gemini in all four languages", PASS if langs == 4 else FAIL,
                      f"{langs} of 4 language spans name Gemini"))
    built = ROOT / "docs" / "index.html"
    b = built.read_text(encoding="utf-8") if built.exists() else ""
    if "Gemini" in footer_block(b):
        out.append(result("2.3 the built page carries it", PASS, "docs/index.html footer names Gemini"))
    else:
        out.append(result("2.3 the built page carries it", PENDING if langs == 4 else FAIL,
                          "not yet rebuilt by the publisher" if langs == 4 else "the source does not carry it either"))
    ctx = text("tools/ai_feed_context.js")
    kontur = ctx[ctx.find("demographic_context"):ctx.find("demographic_context") + 900]
    bad = [w for w in ("'administrative'", "narrative_hint", "360 km", "'79014',place:'Grad Beograd'") if w in kontur]
    out.append(result("2.4 the population fact is a window, not the City", FAIL if bad else PASS,
                      "still present: " + ", ".join(bad) if bad else "Kontur total is labelled as the observation window"))
    since = commit_time("tools/ai_feed_context.js")
    entries_dir = ROOT / "runtime" / "ai-feed" / "entries"
    newer, wrong = 0, []
    for f in sorted(entries_dir.glob("*.json")) if entries_dir.is_dir() else []:
        e = json.loads(f.read_text(encoding="utf-8"))
        if (parse(e.get("at")) or since) <= since:
            continue
        newer += 1
        cp = ROOT / "runtime" / "ai-feed" / "contexts" / (e["context_hash"] + ".json")
        packet = json.loads(cp.read_text(encoding="utf-8"))
        s = json.dumps(packet, ensure_ascii=False)
        prose = json.dumps(e.get("content"), ensure_ascii=False)
        if '"geography": "administrative"' in s and "Kontur" in s or "1719722 stanovnika" in prose and "Grad Beograd ima" in prose:
            wrong.append(e["id"])
    if wrong:
        out.append(result("2.5 new AI entries do not call the window the City", FAIL, "entries: " + ", ".join(wrong)))
    elif newer == 0:
        out.append(result("2.5 new AI entries do not call the window the City", PENDING, "no AI entry written since the fix"))
    else:
        out.append(result("2.5 new AI entries do not call the window the City", PASS, f"{newer} new entries checked"))
    if live:
        import urllib.request
        req = urllib.request.Request(PUBLIC_SITE, headers={"User-Agent": TOKEN})
        page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        ok = "Gemini" in footer_block(page)
        out.append(result("2.6 the published site names Gemini", PASS if ok else PENDING,
                          "live footer names Gemini" if ok else "live site not yet republished"))
    return out


# ------------------------------------------------------------------ step 3: the mind
# Real sentences from the public page (2026-09-14/15) with the facts they were judged against.
SPREAD_PM10 = {"id": "F4", "kind": "spread", "parameter": "PM10",
               "en": "PM10 in that hour, compared across 31 stations: lowest 8 (Zemun TB), highest 85 (Surčin) µg/m³."}
MOVE_PM10 = {"id": "F5", "kind": "connection", "parameter": "PM10",
             "en": "Connection: the highest measured value of PM10 moved from 76 to 85 µg/m³ between the hours 19:00 and 20:00 (source labels)."}
SPREAD_PM25 = {"id": "F8", "kind": "spread", "parameter": "PM2.5",
               "en": "PM2.5 in that hour, compared across 31 stations: lowest 5 (Topčiderska zvezda), highest 63 (Surčin) µg/m³."}
MOVE_PM25 = {"id": "F9", "kind": "connection", "parameter": "PM2.5",
             "en": "Connection: the highest measured value of PM2.5 moved from 18 to 63 µg/m³ between the hours 19:00 and 20:00 (source labels)."}
FACTS = [SPREAD_PM10, MOVE_PM10, SPREAD_PM25, MOVE_PM25]
MUST_REFUSE = [
    "The air quality in the city has been improving slightly, with PM10 values dropping from 85 to 63 µg/m³. [F4][F5][F8][F9]",
    "SEPA shows PM10 values rising from 8 to 85 µg/m³ in that hour [F4].",
    "SEPA says that the air is getting worse, PM10 reaching 85 µg/m³ [F4].",
]
MUST_ACCEPT = [
    "The highest PM10 value moved from 76 to 85 µg/m³ between the labelled hours [F5].",
    "PM10 ranged across stations between 8 and 85 µg/m³ in that hour [F4].",
]


def mind_module():
    sys.path.insert(0, str(ROOT / "tools"))
    import organ_mind
    return organ_mind


def step3_static() -> list[dict]:
    out = []
    try:
        m = mind_module()
        src = text("tools/organ_mind.py")
    except Exception as e:  # noqa: BLE001
        return [result("3.0 mind module", UNKNOWN, f"{type(e).__name__}: {e}")]
    dg = {"facts": FACTS, "numbers": set().union(*(m._nums(f["en"]) for f in FACTS)), "sids": {}}
    leaked = [s[:50] for s in MUST_REFUSE if m.validate({"text": s, "cites": []}, dg)[0]]
    blocked = [s[:50] for s in MUST_ACCEPT if not m.validate({"text": s, "cites": []}, dg)[0]]
    out.append(result("3.1 the validator refuses the published counter-examples", FAIL if leaked else PASS,
                      "still accepted: " + " | ".join(leaked) if leaked else f"{len(MUST_REFUSE)} of {len(MUST_REFUSE)} refused"))
    out.append(result("3.2 the validator still accepts true sentences", FAIL if blocked else PASS,
                      "wrongly refused: " + " | ".join(blocked) if blocked else f"{len(MUST_ACCEPT)} of {len(MUST_ACCEPT)} accepted"))
    ok = "compared across" in src and "in that hour: from" not in src
    out.append(result("3.3 the digest words a spread as a comparison of places", PASS if ok else FAIL,
                      "digest says 'compared across … lowest … highest'" if ok else "digest still says 'from … to'"))
    warm = '"keep_alive": "60s"' in src and "min(timeout, 120)" not in src
    out.append(result("3.4 the voice call is not starved by a cold reload or a hidden 120 s cap", PASS if warm else FAIL,
                      "keep_alive 60s, no hidden cap" if warm else "keep_alive 0s or the 120 s cap is still there"))
    mixed = hasattr(m, "mixed_script_words") and m.mixed_script_words("dosegaо 51") == ["dosegaо"]
    out.append(result("3.5 a word in two scripts is refused", PASS if mixed else FAIL,
                      "mixed-script guard present" if mixed else "no mixed-script guard"))
    return out


@guarded
def step3() -> list[dict]:
    out = step3_static()
    m = mind_module()
    if not hasattr(m, "role_reasons"):
        out.append(result("3.6 accepted thoughts since the fix keep their numbers' roles", FAIL, "the mind has no role check yet"))
        return out
    version = tuple(int(x) for x in m.ORGAN_VERSION.split("."))
    rows = []
    for f in sorted((LIVE / "derived" / "mind").glob("????-??.jsonl")):
        rows += [r for r in jsonl(f) if r.get("organ") == "mind" and r.get("orchestration") == "drip"
                 and r.get("entity") in ("observer", "skeptic", "connector")]
    new = [r for r in rows if tuple(int(x) for x in str(r.get("organ_version", "0.0.0")).split(".")) >= version]
    thoughts = [r for r in new if r.get("state") == "thought"]
    if len(thoughts) < MIN_MIND_ROWS:
        out.append(result("3.6 accepted thoughts since the fix keep their numbers' roles", PENDING,
                          f"{len(thoughts)} accepted thoughts under {m.ORGAN_VERSION}; {MIN_MIND_ROWS} needed"))
        out.append(result("3.7 the Serbian voice is not lost to timeouts", PENDING, "not enough accepted thoughts yet"))
        return out
    digests = {}
    for f in (LIVE / "derived" / "mind" / "digests").glob("*.json"):
        if f.stat().st_mtime >= min(parse(r["derivedTime"]) for r in thoughts).timestamp() - 600:
            d = json.loads(f.read_text(encoding="utf-8"))
            import hashlib
            digests[hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()] = d
    bad, unmatched = [], 0
    for r in thoughts:
        dg = digests.get(r.get("digest_sha256"))
        if dg is None:
            unmatched += 1
            continue
        ids = set(re.findall(r"\[(F\d+)\]", r["en"])) | set(r.get("cites") or [])
        reasons = m.role_reasons(r["en"], [f for f in dg["facts"] if f["id"] in ids])
        if reasons:
            bad.append(f"{r['derivedTime'][:16]} {reasons[0]}")
    if bad:
        out.append(result("3.6 accepted thoughts since the fix keep their numbers' roles", FAIL, "; ".join(bad[:5])))
    elif unmatched == len(thoughts):
        out.append(result("3.6 accepted thoughts since the fix keep their numbers' roles", UNKNOWN, "no digest matched its row"))
    else:
        out.append(result("3.6 accepted thoughts since the fix keep their numbers' roles", PASS,
                          f"{len(thoughts) - unmatched} thoughts re-checked against their own digests"))
    timeouts = sum(1 for r in thoughts if "TimeoutError" in str(r.get("sr_state")))
    share = timeouts / len(thoughts)
    out.append(result("3.7 the Serbian voice is not lost to timeouts", PASS if share <= MAX_VOICE_TIMEOUT_SHARE else FAIL,
                      f"{timeouts} of {len(thoughts)} voice renderings timed out ({share:.0%}; limit {MAX_VOICE_TIMEOUT_SHARE:.0%})"))
    return out


# ------------------------------------------------------------------ step 4: the watch
@guarded
def step4(live: bool = False) -> list[dict]:
    out = []
    src = text("tools/watchman.py")
    out.append(result("4.1 the watchman has a coverage check", PASS if "coverage 24h" in src else FAIL,
                      "coverage 24h present" if "coverage 24h" in src else "no coverage check"))
    wp = ROOT / "public" / "watch.json"
    w = json.loads(wp.read_text(encoding="utf-8"))
    c = next((x for x in w.get("checks", []) if x.get("check") == "coverage 24h"), None)
    if c is None:
        out.append(result("4.2 the local watch report shows coverage", PENDING if "coverage 24h" in src else FAIL,
                          "watch.json has no coverage line yet"))
        return out
    if str(c.get("state")).lower() == "unknown":
        out.append(result("4.2 the local watch report agrees with the slot counts", PENDING,
                          f"the watch could not judge coverage at {w.get('at')}: {c.get('said')} - re-run after a fresh collect tick"))
        return out
    snap = json.loads((ROOT / "public" / "live-snapshot.json").read_text(encoding="utf-8"))["status"]
    low = sorted(s["sid"] for s in snap["sources"]
                 if s.get("expected_slots") and s.get("captured") and not s.get("paused")
                 and s["captured"] / s["expected_slots"] < 0.9)
    claimed = sorted(x["sid"] for x in c.get("below", []))
    same = low == claimed
    out.append(result("4.2 the local watch report agrees with the slot counts", PASS if same else FAIL,
                      f"watch says below 90%: {claimed or 'none'}; recount: {low or 'none'}"
                      + (" (the two were read minutes apart; re-run if they differ by one source)" if not same else "")))
    return out


# ------------------------------------------------------------------ report
STEPS = {"0": lambda a: step0(), "1": lambda a: step1(), "2": lambda a: step2(a.live),
         "3": lambda a: step3(), "4": lambda a: step4(a.live)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", default="all", choices=["all", *STEPS])
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, str(ROOT / "tools"))
    steps = list(STEPS) if a.step == "all" else [a.step]
    report = {"schema": "beops-round-check/v1", "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "head": git("rev-parse", "--short", "HEAD"), "steps": {s: STEPS[s](a) for s in steps}}
    states = [c["state"] for s in report["steps"].values() for c in s]
    report["verdict"] = FAIL if FAIL in states else (UNKNOWN if UNKNOWN in states else (PENDING if PENDING in states else PASS))
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        print(f"round check at {report['at']} on {report['head']}: {report['verdict']}")
        for s, checks in report["steps"].items():
            print(f"step {s}")
            for c in checks:
                print(f"  {c['state']:<8} {c['check']} - {c['said']}")
    return 1 if report["verdict"] in (FAIL, UNKNOWN) else 0


if __name__ == "__main__":
    raise SystemExit(main())
