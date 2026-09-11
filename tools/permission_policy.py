"""One operational access policy. Captured signals are evidence, not a legal opinion."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, unquote
from contracts import json_rows

MAX_AGE_HOURS = 192  # weekly recheck plus a one-day grace; one value used by guard


def header_refusals(entry):
    out = {}
    for url, signals in (entry.get("opt_out_signals_seen") or {}).items():
        for key, value in (signals or {}).items():
            k, v = key.lower(), re.sub(r"\s+", "", str(value).lower())
            denied = (k == "x-robots-tag" and re.search(r"\b(noai|noimageai)\b", v)
                      or k == "tdm-reservation" and v == "1"
                      or k == "content-usage" and re.search(r"(?:^|[,;])(ai|tdm)=n(?:$|[,;])", v)
                      or k == "content-signal" and re.search(r"(?:^|[,;])(ai-input|search)=no(?:$|[,;])", v))
            if denied:
                out.setdefault(url, {})[key] = value
    return out


def access_state(entry):
    if not entry:
        return False, "no permission capture"
    if entry.get("manual_verdict") in ("refused", "needs_decision"):
        return False, "manual decision: " + entry["manual_verdict"]
    if header_refusals(entry):
        return False, "HTTP opt-out forbids this use"
    for signals in (entry.get("content_signal") or {}).values():
        if any(str(signals.get(k, "")).lower() == "no" for k in ("ai-input", "search")):
            return False, "Content-Signal forbids this use"
    if entry.get("allowed_for_us") is not True or entry.get("capture_ok") is not True:
        return False, "permission unknown, refused, or incomplete"
    return True, entry.get("captured_at_utc", "")


def latest(path):
    result, vetoes = {}, {}
    for entry in json_rows(path):
        sid = entry.get("sid")
        if not sid:
            continue
        if entry.get("manual_verdict") in ("refused", "needs_decision"):
            vetoes[sid] = entry
        elif entry.get("manual_verdict") == "released" and entry.get("manual_reviewed_by"):
            vetoes.pop(sid, None)
        if sid not in result or entry.get("captured_at_utc", "") >= result[sid].get("captured_at_utc", ""):
            result[sid] = dict(entry)
    for sid, veto in vetoes.items():
        result[sid].update(manual_verdict=veto["manual_verdict"], manual_reason=veto.get("manual_reason"))
    return result


def route(url):
    p = urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        raise ValueError("unsupported URL")
    # Decode percent escapes for exact comparisons; do not widen a permission to the host.
    return p.scheme.lower(), p.netloc.lower(), unquote(p.path or "/")


def authorize(sid, entries, root, url, now=None):
    e = entries.get(sid)
    ok, why = access_state(e)
    if not ok:
        return ok, why
    if not url:
        return False, "exact request URL required"
    try:
        at = datetime.strptime(e["captured_at_utc"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        age = (now or datetime.now(timezone.utc)) - at
        if age < timedelta(minutes=-5) or age > timedelta(hours=MAX_AGE_HOURS):
            return False, "permission capture expired or future dated"
        root = pathlib.Path(root).resolve()
        directory = (root / e["evidence_dir"]).resolve()
        directory.relative_to(root / "research" / "evidence" / "legal")
        raw = (directory / "MANIFEST.json").read_bytes()
        if e.get("manifest_sha256") and hashlib.sha256(raw).hexdigest() != e["manifest_sha256"]:
            return False, "permission manifest hash mismatch"
        manifest = json.loads(raw)
        if manifest.get("sid") != sid or manifest.get("captured_at_utc") != e["captured_at_utc"]:
            return False, "permission manifest identity mismatch"
        for name, meta in manifest["files"].items():
            path = (directory / name).resolve()
            path.relative_to(directory)
            data = path.read_bytes()
            if len(data) != meta["bytes"] or hashlib.sha256(data).hexdigest() != meta["sha256"]:
                return False, "permission evidence hash mismatch: " + name
        wanted = route(url)
        if not any(route(u) == wanted and status == 200 for u, status in (e.get("status_by_url") or {}).items()):
            return False, "this request route was not successfully captured"
        # Queries can carry robots rules. Re-evaluate the exact URL against the stored robots bytes.
        verdict = json.loads((directory / "robots_verdict.json").read_text(encoding="utf-8"))
        origin = urlsplit(url).scheme + "://" + urlsplit(url).netloc
        v = verdict.get(origin)
        if not v or not any(route(u) == wanted and p.get("allowed_for_us") is True for u, p in v.get("paths", {}).items()):
            return False, "stored robots decision does not cover this route"
        from legal_capture import rfc9309
        for name, meta in manifest["files"].items():
            if meta.get("url") == origin + "/robots.txt" and meta.get("status") == 200:
                txt = (directory / name).read_text(encoding="utf-8", errors="replace")
                p = urlsplit(url)
                target = (p.path or "/") + (("?" + p.query) if p.query else "")
                from transport import user_agent
                for ua in ("*", manifest.get("user_agent") or "*", user_agent(url)):
                    allow, _, sig = rfc9309(txt, ua, target)
                    if not allow or any(sig.get(k) == "no" for k in ("ai-input", "search")):
                        return False, "stored robots rules disallow the exact URL"
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        return False, "permission evidence invalid: " + str(exc)[:160]
    return True, e["captured_at_utc"]
