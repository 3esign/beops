#!/usr/bin/env python3
"""
organ_news.py - the first BEOPS organ: a small local model reads the headlines the collector
received and sorts them (topic, Belgrade or not, candidate zones). It DERIVES; it never measures.

    python -B tools/organ_news.py run            classify headlines not yet classified (needs Ollama on this body)
    python -B tools/organ_news.py status         what the organ has done, what is waiting, whether the model answers
    python -B tools/organ_news.py check          registry + gazetteer sanity, no model call

Rules (CONTRIBUTING.md, 05-design grammar, 07-legal, AI Act Art. 50 notes in research/ORGANS.json):

  * Every output row is state "estimated": drawn with a structural stroke, never chromatic, never
    counted as an observation. It carries the model id, the prompt hash, the organ version and the
    input row's dedupe key, so any sentence the organ produced can be traced to one headline and one
    model. Text produced by the model is marked ai_generated=true (Art. 50 transparency).
  * Zone binding is a hypothesis that keeps its losers (03-models/GEOPARSING.md): the model chooses
    only from the project's gazetteer, and every candidate with its score is kept, never just the winner.
  * The organ is allowed to be silent. If the model does not answer, the run leaves a receipt with
    state "organ_silent" and no derived rows. Silence is a record, not an error to hide.
  * The organ reads only what the collector stored: headline, link, publication time. Never the article.
"""
from __future__ import annotations

import argparse
from contracts import json_rows, serialized, atomic_json
from contracts import exclusive, finite, organ_pause_reason
import local_models
import news_state
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE = ROOT / "data" / "live"
ORGANS = ROOT / "research" / "ORGANS.json"
ORGAN_ID = "news-sorter"
ORGAN_VERSION = "0.2.1"
OLLAMA = os.environ.get("BEOPS_OLLAMA", "http://127.0.0.1:11434")

CATEGORIES = ["saobracaj", "radovi", "iskljucenja", "javni_prevoz", "vreme_i_vazduh", "voda_i_reke",
              "dogadjaj_kultura_sport", "bezbednost_incident", "uprava_odluke", "gradnja_urbanizam",
              "ekonomija_cene", "zdravlje", "ostalo", "nije_beograd"]

# Gazetteer: the 17 municipalities and a short list of places any Belgrade headline names.
# Zone level only - no streets, no buildings (ZONE_I_POVEZIVANJE.md). Extend by editing, never by the model.
GAZETTEER = ["Stari grad", "Vračar", "Savski venac", "Novi Beograd", "Zemun", "Palilula", "Zvezdara", "Voždovac",
             "Čukarica", "Rakovica", "Surčin", "Grocka", "Obrenovac", "Lazarevac", "Mladenovac", "Sopot", "Barajevo",
             "Kalemegdan", "Dorćol", "Slavija", "Terazije", "Ada Ciganlija", "Banovo brdo", "Bežanijska kosa",
             "Borča", "Krnjača", "Karaburma", "Mirijevo", "Dedinje", "Banjica", "Voždovac centar", "Autokomanda",
             "Beograd na vodi", "Ušće", "Gazela", "Brankov most", "Pančevački most", "Most na Adi", "Pupinov most",
             "Batajnica", "Zemun polje", "Vinča", "Košutnjak", "Topčider", "Blokovi", "Bulevar kralja Aleksandra",
             "Aerodrom Nikola Tesla", "Sava", "Dunav", "ceo Beograd"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def stamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# ------------------------------------------------------------------ inputs
def headlines(hours: int = 168) -> list[dict]:
    """Text rows from every rows/<sid>/ file, newest window only."""
    since = iso(utcnow() - timedelta(hours=hours))
    out = []
    rows_dir = LIVE / "rows"
    if not rows_dir.exists():
        return out
    for sid_dir in sorted(rows_dir.iterdir()):
        for mf in sorted(sid_dir.glob("*.jsonl")):
            for r in json_rows(mf):
                if r.get("kind") != "text" or not r.get("result"):
                    continue
                if (r.get("receivedTime") or "") < since:
                    continue
                r = dict(r)
                r["dedupe_key"] = r.get("row_id") or r.get("dedupe_key")
                out.append(r)
    # Each retained revision is attempted once per batch; fresh headlines come
    # first, then the bounded historical backlog. The archive retains all ages.
    unique = {}
    for row in sorted(out, key=lambda r: r.get('receivedTime') or '', reverse=True):
        unique.setdefault(row.get('dedupe_key'), row)
    return list(unique.values())


def done_keys() -> set:
    p = LIVE / "derived" / "news" / "_done.json"
    if p.exists():
        try:
            value = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(value, list) or any(not isinstance(k, str) for k in value):
                raise ValueError('expected a list of keys')
        except ValueError as exc:
            raise ValueError(f'Invalid completion cache {p}: {exc}') from exc
    return news_state.completed_keys(LIVE / 'derived/news', CATEGORIES)


def save_done(keys: set) -> None:
    p = LIVE / "derived" / "news" / "_done.json"
    with exclusive(LIVE / '.write.lock'):
        atomic_json(p, sorted(keys))


# ------------------------------------------------------------------- model
PROMPT = """Ti si organ BEOPS-a, opservatorije Beograda. Dobijaš naslove vesti (samo naslove).
Za SVAKI naslov vrati JSON objekat sa poljima:
- "i": redni broj naslova (ceo broj, kako je dat)
- "headline": naslov PREPISAN doslovno (prvih 60 znakova je dovoljno) - po njemu se odgovor vezuje za naslov
- "category": tačno jedna vrednost iz liste: %s
- "belgrade": true ako se vest odnosi na grad Beograd ili neku njegovu opštinu, inače false
- "zones": lista od najviše 3 kandidata {"name": <ime TAČNO iz gazetteera>, "score": 0..1} - samo ako je belgrade true; ako se ne može odrediti, prazna lista
- "event_time_text": doslovan izraz vremena iz naslova ako postoji ("od ponedeljka", "sutra", "u 18h"), inače null
Ne izmišljaj mesta koja nisu u gazetteeru. Ne piši ništa osim JSON-a.
Gazetteer: %s
Vrati: {"items":[...]}
Naslovi:
%s"""


def prompt_for(batch: list[dict]) -> str:
    lines = "\n".join(f"{i}. {r['result']}" for i, r in enumerate(batch))
    return PROMPT % (", ".join(CATEGORIES), ", ".join(GAZETTEER), lines)


SCHEMA = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {
        "type": "object",
        "properties": {"i": {"type": "integer"}, "headline": {"type": "string"}, "category": {"type": "string", "enum": CATEGORIES},
                       "belgrade": {"type": "boolean"},
                       "zones": {"type": "array", "items": {"type": "object", "properties": {
                           "name": {"type": "string"}, "score": {"type": "number"}}, "required": ["name", "score"]}},
                       "event_time_text": {"type": ["string", "null"]}},
        "required": ["i", "headline", "category", "belgrade", "zones", "event_time_text"]}}},
    "required": ["items"],
}


def ollama_tags(timeout: int = 5) -> list[str] | None:
    try:
        doc = local_models.request(OLLAMA, "/api/tags", timeout=timeout)
        return [m["name"] for m in doc.get("models", []) if not m.get("remote_host") and not m.get("remote_model")]
    except Exception:  # noqa: BLE001 - silence is a state
        return None


def pick_model(available: list[str], preferred: list[str], allow_cloud: bool = False) -> str | None:
    """First preferred model that is actually present. Names ending in ':cloud' are Ollama-hosted
    models that would send the prompt off the machine; they are skipped unless the organ's register
    entry says allow_cloud, because the register promises that no headline leaves the body."""
    for p in preferred:
        for a in available:
            if a.endswith(":cloud") or a.endswith("-cloud"):
                if not allow_cloud:
                    continue
            if a == p or a.startswith(p + ":") or a.split(":")[0] == p:
                return a
    return None


THINKING_MODELS = ("qwen3", "deepseek-r1", "gpt-oss", "magistral")   # Ollama accepts think=false only for models that can think


def ollama_chat(model: str, prompt: str, timeout: int = 600) -> dict:
    """One constrained call. Small local models on a CPU are slow: a batch of five headlines took
    minutes on qwen2.5:3b, so the timeout is generous and keep_alive holds the model in memory
    between batches. num_ctx is capped because the prompt is short and a big context slows it."""
    payload = {"model": model, "stream": False, "format": SCHEMA, "keep_alive": "30m",
               "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 1500},
               "messages": [{"role": "user", "content": prompt}]}
    if model.split(":")[0].startswith(THINKING_MODELS):
        payload["think"] = False   # measured 2026-09-09: left thinking, qwen3.5 spends its whole budget thinking and returns empty content
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA + "/api/chat", data=body, headers={"Content-Type": "application/json"})
    doc = local_models.request(OLLAMA, "/api/chat", payload, min(timeout, 120))
    content = (doc.get("message") or {}).get("content") or ""
    return json.loads(content)


# --------------------------------------------------------------------- run
def derive(batch: list[dict], answer: dict, model: str, prompt_sha: str, now: datetime) -> list[dict]:
    out = []
    raw_items = answer.get('items', []) if isinstance(answer, dict) else []
    items = [it for it in raw_items if isinstance(it, dict)] if isinstance(raw_items, list) else []
    by_i = {}
    for it in items:
        try:
            by_i.setdefault(int(it.get("i", -1)), it)
        except (TypeError, ValueError):
            pass

    def norm(t):
        return re.sub(r"[^a-z0-9]+", " ", str(t or "").lower()).strip()[:50]

    def match(i, r):
        """Bind by the echoed headline first (a 3B model shifted every index by one on the first run,
        C-013); fall back to the index only when the echo is absent or ambiguous."""
        key = norm(r["result"])
        cands = [it for it in items if key and norm(it.get("headline")) and (norm(it.get("headline")).startswith(key[:30]) or key.startswith(norm(it.get("headline"))[:30]))]
        if len(cands) == 1:
            return cands[0], "echo"
        it = by_i.get(i)
        return it, ("index" if it is not None else None)

    for i, r in enumerate(batch):
        it, how = match(i, r)
        base = {"schema": "beops-derived-row/v1", "state": "estimated", "organ": ORGAN_ID, "organ_version": ORGAN_VERSION,
                "model": model, "prompt_sha256": prompt_sha, "ai_generated": True,
                "input_sid": r["sid"], "input_key": r.get("dedupe_key"), "input_headline": r["result"],
                "input_resultTime": r.get("resultTime"), "derivedTime": iso(now)}
        if it is None:
            out.append({**base, "state": "incomplete", "category": None, "belgrade": None, "zones": [], "event_time_text": None,
                        "note": "model returned no item for this headline"})
            continue
        cat = it.get("category") if it.get("category") in CATEGORIES else None
        if cat is None or not isinstance(it.get('belgrade'), bool):
            base['state'] = 'incomplete'
            base['note'] = 'model item lacks a valid category or Belgrade decision'
        zones = []
        for z in it.get("zones") or []:
            name = z.get("name") if isinstance(z, dict) else None
            if name in GAZETTEER:
                try:
                    score = z.get('score', 0)
                    zones.append({"name": name, "score": max(0.0, min(1.0, float(score))) if finite(score) else 0.0})
                except (TypeError, ValueError):
                    zones.append({"name": name, "score": 0.0})
            elif name:
                zones.append({"name": None, "rejected": str(name)[:60], "score": 0.0,
                              "why": "not in gazetteer - a place the model named on its own is kept as a rejection, never as a zone"})
        zones.sort(key=lambda z: -z["score"])
        zones = zones[:3]
        if it.get("belgrade") is not True:
            zones = []
        time_text = str(it.get("event_time_text") or "").strip()
        time_ok = time_text and time_text.casefold() in str(r["result"]).casefold()
        base["validation"] = {"time_quote_supported": bool(time_ok), "zone_candidates": "model estimate"}
        out.append({**base, "bound_by": how, "category": cat, "belgrade": it.get("belgrade") if isinstance(it.get("belgrade"), bool) else None,
                    "zones": zones, "binding": "inferred_from_content" if zones and zones[0].get("name") else None,
                    "event_time_text": time_text[:80] if time_ok else None})
    return out


def publish(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=1).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=".organ-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.link(tmp, path)
    finally:
        os.unlink(tmp)


@serialized(lambda: LIVE / "derived/news/.job.lock")
@local_models.budget(480)
def run(now: datetime | None = None, chat=ollama_chat, tags=ollama_tags, batch_size: int | None = None, limit: int | None = None) -> dict:
    now = now or utcnow()
    if limit is None:
        limit = int(os.environ.get("BEOPS_ORGAN_LIMIT", "60"))
    if batch_size is None:
        batch_size = int(os.environ.get("BEOPS_ORGAN_BATCH", "5"))
    if batch_size < 1 or limit < 0:
        raise ValueError('batch_size must be positive and limit nonnegative')
    reg = json.loads(ORGANS.read_text(encoding="utf-8"))
    organ = next(o for o in reg["organs"] if o["id"] == ORGAN_ID)
    receipt_path = LIVE / "derived" / "news" / "receipts" / f"{stamp(now)}.json"
    done = done_keys()
    attempts_path = LIVE / "derived/news/attempts.json"
    attempts = json.loads(attempts_path.read_text(encoding="utf-8")) if attempts_path.exists() else {}
    retry_path = LIVE / 'derived/news/retry.json'
    retry = json.loads(retry_path.read_text(encoding='utf-8')) if retry_path.exists() else {}
    pending = [r for r in headlines() if r.get('dedupe_key') and r['dedupe_key'] not in done]
    eligible = [r for r in pending if attempts.get(r['dedupe_key'], 0) < 3
                and retry.get(r['dedupe_key'], {}).get('next_attempt_at', '') <= iso(now)]
    todo = eligible[:limit]
    rec = {"schema": "beops-organ-receipt/v1", "organ": ORGAN_ID, "organ_version": ORGAN_VERSION, "at": iso(now),
           "waiting": len(todo), "state": "nothing_to_do", "derived": 0, "model": None, "calls": 0}
    rec.update(waiting_total=len(pending), waiting_eligible=len(eligible),
               incomplete_exhausted=sum(1 for r in pending if attempts.get(r['dedupe_key'], 0) >= 3))
    if organ_pause_reason(organ, LIVE / "derived" / "news"):
        rec.update(state="paused", reason="operator pause or inactive organ")
        publish(receipt_path, rec)
        return rec
    if not todo:
        if pending:
            rec['state'] = 'retry_exhausted' if rec['incomplete_exhausted'] == len(pending) else 'waiting_retry'
        publish(receipt_path, rec)
        return rec
    available = tags()
    model = pick_model(available or [], organ["models_preferred"], bool(organ.get("allow_cloud"))) if available else None
    if not model:
        rec["state"] = "organ_silent"
        rec["reason"] = "model daemon not answering" if available is None else f"none of {organ['models_preferred']} available; have {available[:8]}"
        publish(receipt_path, rec)
        return rec
    rec["model"] = model
    done = done_keys()
    out_path = LIVE / "derived" / "news" / (now.strftime("%Y-%m") + ".jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    derived_n = 0
    errors = []
    for k in range(0, len(todo), batch_size):
        batch = todo[k:k + batch_size]
        prompt = prompt_for(batch)
        sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        rec["calls"] += 1
        for row in batch:
            key = row['dedupe_key']
            attempts[key] = attempts.get(key, 0) + 1
            retry[key] = {'last_attempt_at': iso(now),
                          'next_attempt_at': iso(now + timedelta(minutes=5 * 2 ** (attempts[key] - 1))),
                          'state': 'attempted'}
        with exclusive(LIVE / ".write.lock"):
            atomic_json(attempts_path, attempts)
            atomic_json(retry_path, retry)
        try:
            answer = chat(model, prompt)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{type(exc).__name__}: {str(exc)[:160]}")
            for row in batch:
                retry[row['dedupe_key']].update(state='failed', reason=type(exc).__name__)
            with exclusive(LIVE / '.write.lock'):
                atomic_json(retry_path, retry)
            continue
        rows = derive(batch, answer, model, sha, now)
        with exclusive(LIVE / ".write.lock"):
            with open(out_path, "a", encoding="utf-8") as fh:
                for r in rows:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        for r in rows:
            if news_state.complete(r, CATEGORIES):
                done.add(r["input_key"])
            retry[r['input_key']].update(state='completed' if r['input_key'] in done else 'incomplete',
                                         reason=r.get('note'))
        with exclusive(LIVE / '.write.lock'):
            atomic_json(retry_path, retry)
        derived_n += len(rows)
    save_done(done)
    rec["derived"] = derived_n
    rec["errors"] = errors
    rec["incomplete_exhausted"] = sum(1 for key, count in attempts.items() if count >= 3 and key not in done)
    rec["state"] = "derived" if derived_n else ("organ_failed" if errors else "nothing_to_do")
    rec["output"] = str(out_path)
    publish(receipt_path, rec)
    return rec


@serialized(lambda: LIVE / 'derived/news/.job.lock')
def reconcile_completion():
    """Repair only the disposable cache, retaining its previous keys and a receipt."""
    directory = LIVE / 'derived/news'
    cache = directory / '_done.json'
    old = json.loads(cache.read_text(encoding='utf-8')) if cache.exists() else []
    if not isinstance(old, list) or any(not isinstance(k, str) for k in old):
        raise ValueError('invalid completion cache; preserve and inspect before reconciliation')
    with exclusive(LIVE / '.write.lock'):
        when = utcnow()
        backup = directory / 'reconciliation' / f'{stamp(when)}-cache-before.json'
        publish(backup, {'at': iso(when), 'keys': old})
        result = news_state.reconcile(directory, CATEGORIES, set(old))
        result.update(at=iso(when), state='reconciled', cache_before=str(backup),
                      scope='completion only, not independent quality annotation')
        publish(directory / 'reconciliation' / f'{stamp(when)}-result.json', result)
        return result


def status() -> dict:
    d = LIVE / "derived" / "news"
    receipts = sorted(d.glob("receipts/*.json")) if d.exists() else []
    last = json.loads(receipts[-1].read_text(encoding="utf-8")) if receipts else None
    done = done_keys()
    waiting = [r for r in headlines() if r.get("dedupe_key") and r["dedupe_key"] not in done]
    tags = ollama_tags()
    return {"organ": ORGAN_ID, "version": ORGAN_VERSION, "model_daemon": OLLAMA,
            "models_available": tags, "waiting_headlines": len(waiting), "done": len(done),
            "runs": len(receipts), "last_run": last}


def check() -> dict:
    reg = json.loads(ORGANS.read_text(encoding="utf-8"))
    organ = next(o for o in reg["organs"] if o["id"] == ORGAN_ID)
    return {"registry": str(ORGANS.relative_to(ROOT)), "organ": organ["id"], "purpose": organ["purpose"],
            "models_preferred": organ["models_preferred"], "gazetteer": len(GAZETTEER), "categories": CATEGORIES,
            "editor_of_record": organ["editor_of_record"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["run", "status", "check", "reconcile"])
    a = ap.parse_args()
    fn = {"run": run, "status": status, "check": check, "reconcile": reconcile_completion}[a.command]
    print(json.dumps(fn(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
