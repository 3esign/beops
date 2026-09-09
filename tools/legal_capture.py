#!/usr/bin/env python3
"""
legal_capture.py - capture the PERMISSION EVIDENCE for a source, not a claim about it.

BEOPS rule: a source may not enter SOURCE_REGISTRY.json until this tool has
captured, stored and hashed the evidence that collecting it is permitted.
The index in research/08-provenance/ is generated from those captures, so the
index cannot say anything the stored bytes do not.

What one capture stores, verbatim and immutable, under
research/evidence/legal/<SID>/<UTC-stamp>/ :

  robots.txt            the site's robots.txt exactly as served (or the status
                        code if there is none - a 404 is itself evidence)
  robots_verdict.json   the machine verdict of urllib.robotparser for our own
                        user-agent AND for '*', per probed path
  headers.json          response headers of every probed URL, including the
                        AI-opt-out signals X-Robots-Tag and Content-Signal
  terms_<n>.html        the licence / terms page(s) as served
  MANIFEST.json         sha256 + byte length + fetch time of every file above

Then one line is appended to research/08-provenance/LEDGER.jsonl.

Identity: the collector always identifies itself honestly. There is no mode of
this tool that hides who is asking. If a site says no, the answer is no.

Usage
  python -B tools/legal_capture.py --sid S134 \
      --name "Putevi Srbije - AADT counts" \
      --url https://www.putevi-srbije.rs/images/pdf/brojanje/2023/DP-IA-PGDS-2023-eng.xls \
      --url https://www.putevi-srbije.rs/ \
      --terms https://www.putevi-srbije.rs/index.php/sr/uslovi-koriscenja \
      --note "annual AADT per road section, 2018-2024"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import ssl
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone

UA = "Beops-Research-Capture/1.0 (urban observatory research; identifies honestly; respects robots.txt)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE = os.path.join(ROOT, "research", "evidence", "legal")
LEDGER = os.path.join(ROOT, "research", "08-provenance", "LEDGER.jsonl")
REGISTRY = os.path.join(ROOT, "research", "SOURCE_REGISTRY.json")

# Headers that carry a machine-readable "do not use this for AI" signal.
SIGNAL_HEADERS = ("x-robots-tag", "content-signal", "content-usage", "tdm-reservation", "tdm-policy")


WIN_BUNDLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ca-bundle-windows.pem")


def _tls_context() -> tuple[ssl.SSLContext, str]:
    """A verifying TLS context, and a one-line record of where its trust came from.

    There is deliberately no unverified mode. If certificates cannot be
    verified, the capture fails and is recorded as failed - a capture that
    cannot check who it is talking to is not evidence of anything.
    """
    # Prefer the machine's own roots, exported by tools/export_ca_bundle.ps1.
    # certifi shipped with this interpreter is older than some roots now in
    # use: parking-servis.co.rs presents a perfectly valid chain up to Sectigo
    # Public Server Authentication Root R46, which Windows trusts and certifi
    # does not carry, so the capture came back "unknown" for a site that is
    # fine. Under-trusting is the safe direction but it silently excludes
    # valid sources, and the trust decision belongs in a file we can hash.
    if os.path.exists(WIN_BUNDLE):
        try:
            ctx = ssl.create_default_context(cafile=WIN_BUNDLE)
            return ctx, f"machine trust store exported to {os.path.basename(WIN_BUNDLE)}"
        except Exception:
            pass
    try:
        import truststore  # uses the operating system trust store
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), "truststore (OS trust store)"
    except Exception:
        pass
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where()), f"certifi {certifi.where()}"
    except Exception:
        pass
    ctx = ssl.create_default_context()
    n = len(ctx.get_ca_certs())
    return ctx, f"python default context ({n} CA certs loaded)"


TLS_CTX, TLS_TRUST = _tls_context()


# ---------------------------------------------------------------------------
# RFC 9309 matching, because urllib.robotparser does not do it.
#
# urllib.robotparser returns the FIRST matching rule. RFC 9309 section 2.2.2
# says the MOST SPECIFIC (longest) match wins, and that Allow wins a tie. The
# difference is not academic: transit.land publishes
#
#     User-agent: *
#     Allow: /feeds
#     Disallow: /feeds/
#
# and urllib answers "allowed" for /feeds/<id> because Allow comes first, while
# the correct answer is disallowed. For a tool whose only job is to refuse to
# clear us when we are not clear, over-permitting is the worst failure it has.
#
# So: run both, and take the STRICTER of the two. Never the more permissive.
# ---------------------------------------------------------------------------

def _rule_re(pattern: str) -> re.Pattern:
    out, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            out.append(".*")
        elif c == "$" and i == len(pattern) - 1:
            out.append("$")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out))


def parse_groups(text: str) -> list[tuple[list[str], list[tuple[str, str]], dict]]:
    """[(user_agents, [(allow|disallow, pattern)], {content_signal: ...})]"""
    groups: list = []
    agents: list[str] = []
    rules: list = []
    signals: dict = {}
    starting = True
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field, value = field.strip().lower(), value.strip()
        if field == "user-agent":
            if not starting and rules:
                groups.append((agents, rules, signals))
                agents, rules, signals = [], [], {}
            agents.append(value.lower())
            starting = True
        elif field in ("allow", "disallow"):
            starting = False
            if value:
                rules.append((field, value))
        elif field == "content-signal":
            starting = False
            for part in value.split(","):
                k, _, v = part.partition("=")
                if k.strip():
                    signals[k.strip().lower()] = v.strip().lower()
    if agents:
        groups.append((agents, rules, signals))
    return groups


def rfc9309(text: str, ua: str, path: str) -> tuple[bool, str | None, dict]:
    """(allowed, matched_rule, content_signals) for the group that applies to ua."""
    ua_l = ua.lower()
    groups = parse_groups(text)
    chosen, best = None, -1
    for agents, rules, sig in groups:
        for a in agents:
            if a == "*":
                score = 0
            elif a in ua_l:
                score = len(a)
            else:
                continue
            if score > best:
                best, chosen = score, (rules, sig)
    if chosen is None:
        return True, None, {}
    rules, sig = chosen
    winner, wlen, wkind = None, -1, None
    for kind, pattern in rules:
        if _rule_re(pattern).match(path):
            # longest match wins; Allow wins a tie
            if len(pattern) > wlen or (len(pattern) == wlen and kind == "allow"):
                winner, wlen, wkind = pattern, len(pattern), kind
    if winner is None:
        return True, None, sig
    return wkind == "allow", f"{wkind}: {winner}", sig


def utcstamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# Some open endpoints answer with tens of megabytes (APR's company register is
# 57.8 MB). Permission lives in the status line, the headers and the terms page,
# not in the payload, so the body is read up to a cap and the truncation is
# recorded rather than the capture being allowed to fail.
MAX_BODY = 2 * 1024 * 1024


def fetch(url: str, timeout: int = 60):
    """Return (status, headers_dict, body_bytes, error_or_None). Never raises."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=TLS_CTX) as r:
            body = r.read(MAX_BODY + 1)
            hdrs = dict(r.headers.items())
            if len(body) > MAX_BODY:
                body = body[:MAX_BODY]
                hdrs["X-Beops-Body-Truncated"] = f"read {MAX_BODY} bytes of a larger response"
            return r.status, hdrs, body, None
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return e.code, dict(e.headers.items()) if e.headers else {}, body, None
    except Exception as e:  # DNS, TLS, timeout - the failure is itself evidence
        return None, {}, b"", f"{type(e).__name__}: {e}"


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def signals(headers: dict) -> dict:
    low = {k.lower(): v for k, v in headers.items()}
    return {h: low[h] for h in SIGNAL_HEADERS if h in low}


def _registry() -> dict:
    if not os.path.exists(REGISTRY):
        return {}
    with open(REGISTRY, encoding="utf-8") as fh:
        d = json.load(fh)
    recs = d.get("sources", d if isinstance(d, list) else [])
    return {r["id"]: r for r in recs if r.get("id")}


def check_identity(sid: str, urls: list[str], new_source: bool) -> list[str]:
    """Refuse to allocate an id that duplicates an existing source.

    Ids in this project are permanent, and one source has exactly one id. The
    rule was written in CONTRIBUTING.md and then broken within the hour by its
    own author, who assigned S134 to a source already registered as S57. A
    rule a machine checks cannot be forgotten; a rule in a document can.
    """
    reg = _registry()
    problems: list[str] = []

    if sid not in reg and not new_source:
        problems.append(
            f"{sid} is not in SOURCE_REGISTRY.json. If this really is a new "
            f"source, pass --new-source and add the registry entry in the same "
            f"commit. If it is not new, use the id it already has."
        )

    hosts = {urllib.parse.urlparse(u).netloc.lower().removeprefix("www.") for u in urls}
    for other_id, rec in reg.items():
        if other_id == sid:
            continue
        h = urllib.parse.urlparse(rec.get("url", "")).netloc.lower().removeprefix("www.")
        if h and h in hosts:
            problems.append(
                f"host '{h}' already belongs to {other_id} ({rec.get('name', '')!r}). "
                f"Capture under {other_id}, or explain why this is a genuinely "
                f"different source and pass --allow-shared-host."
            )
    return problems


def capture(sid: str, name: str, urls: list[str], terms: list[str], note: str, dry: bool = False,
            refused: str | None = None, needs_decision: str | None = None) -> dict:
    stamp = utcstamp()
    outdir = os.path.join(EVIDENCE, sid, stamp)
    manifest: dict = {"files": {}}
    if not dry:
        os.makedirs(outdir, exist_ok=True)

    def store(fname: str, body: bytes, meta: dict) -> None:
        manifest["files"][fname] = dict(meta, sha256=sha256(body), bytes=len(body))
        if not dry:
            with open(os.path.join(outdir, fname), "wb") as fh:
                fh.write(body)

    # --- robots.txt, one per distinct origin -------------------------------
    origins = []
    for u in list(urls) + list(terms):
        p = urllib.parse.urlparse(u)
        o = f"{p.scheme}://{p.netloc}"
        if o not in origins:
            origins.append(o)

    verdicts: dict = {}
    for i, origin in enumerate(origins):
        rurl = origin + "/robots.txt"
        st, hd, body, err = fetch(rurl)
        fname = "robots.txt" if i == 0 else f"robots_{urllib.parse.urlparse(origin).netloc}.txt"
        store(fname, body, {"url": rurl, "status": st, "error": err, "fetched_at": utcstamp()})

        rp = urllib.robotparser.RobotFileParser()
        # A 4xx robots.txt means "no restrictions stated" per RFC 9309; a 5xx
        # means "assume disallowed". We record which case we are in rather than
        # deciding silently.
        # A site that serves its own HTML for /robots.txt looks, to both
        # parsers, exactly like a robots.txt with no rules - and both then
        # answer "allowed". abs.gov.rs returns 82 KB of a Google Analytics
        # page with HTTP 200. The outcome is the same as a genuine absence but
        # the RECORD would say "robots.txt served", which is false, so the
        # regime is stated as what it is.
        ctype = " ".join(str(v) for k, v in hd.items() if k.lower() == "content-type").lower()
        looks_html = b"<html" in body[:2048].lower() or b"<!doctype" in body[:2048].lower()
        if st == 200 and (looks_html or "text/html" in ctype):
            rp.parse([])
            regime = (f"the /robots.txt path returns HTML (HTTP 200, {ctype or 'no content-type'}), "
                      f"so no robots.txt is actually served - treated as absent, not as permissive")
            body = b"# NOTE: this path returned HTML, not robots.txt. Stored verbatim below.\n" + body
        elif st == 200:
            rp.parse(body.decode("utf-8", "replace").splitlines())
            regime = "robots.txt served"
        elif st is not None and 400 <= st < 500:
            rp.parse([])
            regime = f"no robots.txt (HTTP {st}) - RFC 9309: no restrictions stated"
        else:
            regime = f"robots.txt unavailable (status={st}, error={err}) - treat as disallowed until re-checked"

        body_text = "" if regime.startswith("the /robots.txt path returns HTML") else (
            body.decode("utf-8", "replace") if st == 200 else "")
        per_path, signals_here = {}, {}
        for u in urls + terms:
            if not u.startswith(origin):
                continue
            readable = st == 200 or (st is not None and 400 <= st < 500)
            path = urllib.parse.urlparse(u).path or "/"
            py_ok = rp.can_fetch(UA, u) if readable else None
            py_star = rp.can_fetch("*", u) if readable else None
            if st == 200 and body_text:
                rfc_ok, matched, sig = rfc9309(body_text, UA, path)
                rfc_star, _, _ = rfc9309(body_text, "*", path)
                signals_here.update(sig)
            else:
                rfc_ok, rfc_star, matched = py_ok, py_star, None
            # When the two engines disagree, NEITHER is trusted and the
            # verdict is unknown - which never renders as a permission and is
            # surfaced for a human decision.
            #
            # The first version of this took the stricter of the two, on the
            # reasoning that over-permitting is the dangerous direction. That
            # was the wrong generalisation of the right observation. urllib is
            # simply unreliable: it over-permits where it ignores longest-match
            # (transit.land) and under-permits where it ignores the $ anchor
            # (jnportal.ujn.gov.rs publishes "Allow: /$", which RFC 9309 reads
            # as a permission and urllib reads as a refusal). Taking the
            # stricter turned that second case into a false refusal, silently.
            # A disagreement between two implementations of the same standard
            # is not a fact about the site. It is a fact about the tools, and
            # it belongs in front of a person.
            def strict(a, b):
                if a is None or b is None:
                    return None
                if a != b:
                    return None
                return a
            per_path[u] = {
                "allowed_for_us": strict(py_ok, rfc_ok),
                "allowed_for_star": strict(py_star, rfc_star),
                "urllib_robotparser": py_ok,
                "rfc9309_longest_match": rfc_ok,
                "matched_rule": matched,
                "engines_disagree": (py_ok is not None and rfc_ok is not None and py_ok != rfc_ok),
            }
        verdicts[origin] = {"robots_url": rurl, "status": st, "regime": regime,
                            "paths": per_path, "content_signal": signals_here}

    store("robots_verdict.json", json.dumps(verdicts, indent=2, ensure_ascii=False).encode(), {"generated": True})

    # --- the data URLs themselves ------------------------------------------
    heads: dict = {}
    for u in urls:
        st, hd, body, err = fetch(u)
        heads[u] = {
            "status": st,
            "error": err,
            "headers": hd,
            "opt_out_signals": signals(hd),
            "body_sha256": sha256(body) if body else None,
            "body_bytes": len(body),
            "fetched_at": utcstamp(),
        }
    store("headers.json", json.dumps(heads, indent=2, ensure_ascii=False).encode(), {"generated": True})

    # --- terms / licence pages ---------------------------------------------
    for n, t in enumerate(terms, 1):
        st, hd, body, err = fetch(t)
        ext = "html"
        ctype = {k.lower(): v for k, v in hd.items()}.get("content-type", "")
        if "pdf" in ctype:
            ext = "pdf"
        elif "json" in ctype:
            ext = "json"
        elif "text/plain" in ctype:
            ext = "txt"
        store(f"terms_{n}.{ext}", body, {"url": t, "status": st, "error": err,
                                         "opt_out_signals": signals(hd), "fetched_at": utcstamp()})

    manifest.update({
        "sid": sid, "name": name, "captured_at_utc": stamp, "note": note,
        "user_agent": UA, "urls": urls, "terms": terms,
        "tool": "tools/legal_capture.py",
    })
    store_path = os.path.join(outdir, "MANIFEST.json")
    if not dry:
        with open(store_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, ensure_ascii=False)

    # --- the permission verdict, in three states ---------------------------
    # A capture that could not read robots.txt, or could not reach the URL, is
    # NOT a permission. It is an unknown, and unknown never renders as allowed.
    per_path = [p["allowed_for_us"] for v in verdicts.values() for p in v["paths"].values()]
    fetch_failed = [u for u, h in heads.items() if h["status"] is None]
    robots_unreadable = [o for o, v in verdicts.items() if v["status"] is None]
    if refused:
        # A refusal a person recognises but the parser does not. robots.txt at
        # pleiades.stoa.org disallows ClaudeBot, Claude-Web and anthropic-ai by
        # name while User-agent: * permits everything - so a collector under any
        # other name reads as allowed. Choosing a name the ban does not mention
        # is circumvention, and the tool must be able to record that.
        # The machine may stop us; it may never clear us when we know better.
        allowed: bool | None = False
    elif needs_decision:
        allowed = None
    elif any(x is False for x in per_path):
        allowed = False
    elif robots_unreadable or fetch_failed or any(x is None for x in per_path) or not per_path:
        allowed = None
    else:
        allowed = True

    entry = {
        "sid": sid,
        "name": name,
        "captured_at_utc": stamp,
        "evidence_dir": os.path.relpath(outdir, ROOT).replace("\\", "/"),
        "tls_trust": TLS_TRUST,
        "capture_ok": not (fetch_failed or robots_unreadable),
        "fetch_failed_urls": fetch_failed,
        "robots_unreadable_origins": robots_unreadable,
        "robots": {o: {"status": v["status"], "regime": v["regime"]} for o, v in verdicts.items()},
        "allowed_for_us": allowed,
        "manual_verdict": ("refused" if refused else "needs_decision" if needs_decision else None),
        "manual_reason": refused or needs_decision,
        "opt_out_signals_seen": {u: h["opt_out_signals"] for u, h in heads.items() if h["opt_out_signals"]},
        # Content-Signal also lives INSIDE robots.txt, which is where Cloudflare
        # puts it, and where it is declared an express Article 4 reservation.
        # It is per-purpose, not yes/no: ai-train=no with ai-input=yes means we
        # may read but may not train, and the registry must say so.
        "content_signal": {o: v["content_signal"] for o, v in verdicts.items() if v.get("content_signal")},
        "engines_disagreed": [u for v in verdicts.values() for u, p in v["paths"].items()
                              if p.get("engines_disagree")],
        "status_by_url": {u: h["status"] for u, h in heads.items()},
        "note": note,
    }
    if not dry:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def recheck_collectors(dry: bool = False) -> int:
    """One capture per polled source. The collector's own gate reads the NEWEST ledger line for a
    source, so a refusal measured here stops the polling at the next tick without any other change."""
    cfg_path = os.path.join(ROOT, "research", "COLLECTORS.json")
    with open(cfg_path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    reg = _registry()
    changed = 0
    for src in cfg.get("sources", []):
        sid = src.get("sid")
        if not sid or sid not in reg:
            print(f"{sid}: not in the registry - skipped")
            continue
        url = src.get("url") or ""
        if "{" in url:   # a templated collector URL: capture the registry URL instead
            url = reg[sid].get("url") or url.split("{")[0]
        name = reg[sid].get("name") or src.get("name") or sid
        try:
            e = capture(sid, name, [url], [], "weekly re-check of a polled source", dry)
        except Exception as ex:  # noqa: BLE001
            print(f"{sid}: capture failed: {type(ex).__name__}: {str(ex)[:120]}")
            continue
        flag = "" if e.get("allowed_for_us") else "  <-- NOT PERMITTED NOW: the collector stops this source at its next tick"
        if flag:
            changed += 1
        print(f"{sid} {name[:40]!r}: capture_ok={e.get('capture_ok')} allowed={e.get('allowed_for_us')} "
              f"signals={json.dumps(e.get('opt_out_signals_seen') or {}, ensure_ascii=False)[:120]}{flag}")
    print(f"re-checked {len(cfg.get('sources', []))} polled sources; {changed} no longer permitted")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sid", help="source id in SOURCE_REGISTRY.json, e.g. S134")
    ap.add_argument("--name")
    ap.add_argument("--url", action="append", default=[], help="a URL we intend to collect (repeatable)")
    ap.add_argument("--terms", action="append", default=[], help="licence / terms page (repeatable)")
    ap.add_argument("--note", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--new-source", action="store_true",
                    help="this id is not yet in SOURCE_REGISTRY.json and is genuinely new")
    ap.add_argument("--allow-shared-host", action="store_true",
                    help="another source already uses this host, and that is correct")
    ap.add_argument("--refused", metavar="REASON",
                    help="force the verdict to REFUSED. For a refusal the parser cannot see - a "
                         "ban naming other agents, a clause in the terms, an operator's request. "
                         "There is no opposite flag: nothing can force a permission.")
    ap.add_argument("--needs-decision", metavar="REASON",
                    help="force the verdict to UNKNOWN pending a human decision, with the reason "
                         "recorded. For genuine edge cases - see 08-provenance/EDGE_CASES.md.")
    ap.add_argument("--recheck-collectors", action="store_true",
                    help="re-capture every source the collector polls (research/COLLECTORS.json), so that a "
                         "permission captured once is measured again - a robots.txt or a Content-Signal "
                         "can change any day (scheduled weekly as Beops_Legal)")
    a = ap.parse_args()
    if a.recheck_collectors:
        return recheck_collectors(a.dry_run)
    if not a.sid or not a.name:
        print("--sid and --name are required (or --recheck-collectors)", file=sys.stderr)
        return 2
    if not a.url:
        print("at least one --url is required", file=sys.stderr)
        return 2

    problems = check_identity(a.sid, a.url + a.terms, a.new_source)
    if a.allow_shared_host:
        problems = [p for p in problems if "already belongs to" not in p]
    if problems:
        print("REFUSED - identity check failed:", file=sys.stderr)
        for p in problems:
            print("  * " + p, file=sys.stderr)
        return 3
    if a.refused and a.needs_decision:
        print("--refused and --needs-decision are mutually exclusive", file=sys.stderr)
        return 2
    e = capture(a.sid, a.name, a.url, a.terms, a.note, a.dry_run, a.refused, a.needs_decision)
    print(json.dumps(e, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
