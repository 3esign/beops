#!/usr/bin/env python3
"""
organ_mind.py - the mind of the observatory: small local models orchestrated in layers, checked by
code, thinking aloud about what BEOPS has just seen. The real monologue: a conversation.

    python -B tools/organ_mind.py step       ONE drop: the next step of the endless conversation (scheduled every 4 min)
    python -B tools/organ_mind.py run        one whole conversation at once (the experiment on demand; needs Ollama)
    python -B tools/organ_mind.py score      settle claims whose deadline has passed, from the snapshot (no model call)
    python -B tools/organ_mind.py digest     print the digest the entities are given (program layer only, no model call)
    python -B tools/organ_mind.py status     receipts, scoreboard, models present, whether the daemon answers
    python -B tools/organ_mind.py check      register + validator self-test, no model call
    python -B tools/organ_mind.py retract <conversation> <entity> <round> <reason>   append a retraction (the row stays; export skips it)
    python -B tools/organ_mind.py voice-bench <model> [<model> ...] [--n 8]   render the last accepted thoughts with each model, for reading (needs Ollama)

THE ARCHITECTURE (v0.3) - between a program and an intelligence, built from the small models the
project already has or has already researched (research/MODEL_CANDIDATES.json, Svemir's registry):

  L0  program      the digest: every reception, silence, spread and headline of the window as numbered
                   facts F1..Fn - plus CONNECTIONS computed by code (hour-to-hour movement of a city
                   maximum, the lot whose displayed count moved most, zones the news-sorter named that
                   carry a station, people living within 1 km of the extreme stations when the Kontur
                   context exists). Deterministic. Every number the mind may ever say is here.
  L1  organelles   the smallest models on narrow, checkable jobs, in English or in vectors:
                   - embed-linker: a multilingual sentence-embedding model (Ollama embeddings) finds the
                     same event carried by different outlets - cosine similarity, which is arithmetic,
                     cannot hallucinate; the links become facts with their similarity as the number
                   - surprise-ranker: the smallest instruct model rates the connections 1..5 as
                     categorical JSON - a small model can compare, it should not be asked to write
  L2  thinkers     three temperaments (Observer / Skeptic / Connector) on the strongest local model,
                   thinking IN ENGLISH - where small models are strong - over the digest and the
                   organelles' annotations, in one of two orchestrations that alternate tick by tick:
                     council: round 1 alone, round 2 each answers the other two
                     relay:   Observer -> Skeptic answers -> Connector answers both -> Observer closes
                   Only VALIDATED utterances are passed between them (no echo of an invented number).
  L3  voice        the one local model that can write Serbian renders every accepted utterance - the
                   thought, its hypotheses and its questions - in Serbian EKAVICA (Latin), validated
                   again: same numbers, same citations, Serbian words, no ijekavian or Croatian word (a
                   list of ~300 stems, tested), one retry with the refusal read back. If the voice still
                   fails, the Serbian page shows NO English: the program says, in Serbian, that the
                   rendering was refused; the English original stays on disk and on the English page.
  L4  checks       the validator (numbers only from the digest, citations inside the text, no future
                   as fact, claims in a fixed shape, language and prompt-echo checks), the notebooks
                   (verbal feedback read back next time - learning without training), the scoring of
                   claims against later snapshots, retraction by appended row, PAUSED by a person.

THE DRIP (the scheduled mode). Nothing happens all at once. Every four minutes ONE step of an
endless conversation runs - an organelle brings a link, then the Observer speaks, then the ranker
rates, then the Skeptic answers, then the Connector, then claims are scored - and the working
context (data/live/derived/mind/context.json: the last links, the last ratings, the last six accepted
utterances) fills drop by drop while the digest is rebuilt from the newest snapshot at every step,
so what the city just said enters the conversation within minutes. Each entity speaks about once
every 24 minutes; one model call per step (two when the voice renders Serbian). The monologue shows
every drop at the minute it fell. `run` still exists for the on-demand experiment (a whole
conversation over one digest, council or relay).

Lawful by construction: the mind reads only public/live-snapshot.json (permitted sources, headline
and time only - never an article) and public/context-*.json (layers taken with a permission capture);
every model runs on the PC body under a licence that permits this use (recorded in ORGANS.json);
nothing leaves the machine; every utterance is machine-marked ai_generated=true (AI Act Art. 50) and
never presented as a measurement; the editor of record can stop the organ with one file.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import re
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from organ_news import ollama_tags, pick_model, OLLAMA  # noqa: E402

LIVE = ROOT / "data" / "live"
SNAPSHOT = ROOT / "public" / "live-snapshot.json"
CONTEXT_POP = ROOT / "public" / "context-population.json"
ORGANS = ROOT / "research" / "ORGANS.json"
ORGAN_ID = "mind"
ORGAN_VERSION = "0.4.3"
OUT_DIR = LIVE / "derived" / "mind"
ORCHESTRATIONS = ("council", "relay")   # for `run`; the scheduled mode is the drip (see STEPS)

SRC_LABEL = {"S146": "SEPA (official air-quality stations)", "S04": "Sensor.Community (citizen sensors)", "S10": "Parking Servis",
             "S68": "Tanjug Belgrade", "S69": "Danas", "S75": "Studio B", "S76": "Beta", "S78": "Danubeogradu", "S74": "Gradnja.rs",
             "S70": "Kurir", "S71": "Telegraf", "S72": "Informer"}
SRC_LABEL_SR = {"S146": "SEPA (zvanične stanice kvaliteta vazduha)", "S04": "Sensor.Community (građanski senzori)", "S10": "Parking servis",
                "S68": "Tanjug Beograd"}

ENTITIES = [
    {"id": "observer", "sr": "Posmatrač", "en": "Observer",
     "role_en": "You notice. You say what arrived, what is missing, what changed. You do not interpret beyond the facts."},
    {"id": "skeptic", "sr": "Sumnjalo", "en": "Skeptic",
     "role_en": "You doubt. You look for what the facts do NOT carry: where reception and measurement are confused, where no measurement time exists, what we do not know. When the others say something the facts do not cover, you say so."},
    {"id": "connector", "sr": "Povezivač", "en": "Connector",
     "role_en": "You connect. Two facts, the hour, the weekday, one sense with another, a helper's rating. You propose hypotheses worth checking and, when you can, one checkable claim."},
]
ENT = {e["id"]: e for e in ENTITIES}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def stamp(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _p(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


CLOCK = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?\b")


def _clocks(text: str) -> set:
    """Times of day written on the clock, as HH:MM. A time is not a quantity: 08:00 is a fact about
    WHEN, and checking it against the digest's set of numbers refuses the sentence for looking at the
    clock. Measured before this existed: `number not in digest: 08` was the single most common reason
    an utterance was thrown away (17 of them), with 09, 02, 23 and 03 close behind - every one an hour."""
    return {"%02d:%s" % (int(h), m) for h, m in CLOCK.findall(text or "")}


def _nums(text: str) -> set:
    t = CLOCK.sub(" ", re.sub(r"\[F\d+\]", "", text or ""))
    return {m.replace(",", ".") for m in re.findall(r"\d+(?:[.,]\d+)?", t)}


# ==================================================================== L0: program
def digest(snap: dict, hours: int = 6, now: datetime | None = None, context: dict | None = None) -> dict:
    """The numbered facts the mind may think about. Every number it may say is here."""
    now = now or _p(snap["as_of"]) or utcnow()
    since = now - timedelta(hours=hours)
    facts: list[dict] = []

    def add(sr: str, en: str, **meta):
        facts.append({"id": f"F{len(facts) + 1}", "sr": sr, "en": en, **meta})

    local = now.astimezone(timezone(timedelta(hours=2)))   # CEST until 25 Oct 2026
    wd_sr = ["ponedeljak", "utorak", "sreda", "četvrtak", "petak", "subota", "nedelja"][local.weekday()]
    wd_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][local.weekday()]
    add(f"Sada je {wd_sr}, {local.strftime('%H:%M')} po lokalnom vremenu ({now.strftime('%H:%M')} UTC).",
        f"It is {wd_en}, {local.strftime('%H:%M')} local time ({now.strftime('%H:%M')} UTC).", kind="clock")

    status = {s["sid"]: s for s in snap.get("status", {}).get("sources", [])}
    spreads: list[dict] = []
    headlines: list[dict] = []
    src_names: dict = {}
    for src in snap.get("sources", []):
        sid = src["sid"]
        lab_en = SRC_LABEL.get(sid, src["name"])
        src_names[sid] = [x for x in (lab_en, src.get("name"), SRC_LABEL_SR.get(sid)) if x]
        lab_sr = SRC_LABEL_SR.get(sid, lab_en)
        st = status.get(sid, {})
        ds = src.get("datastreams", [])
        pts = [(d, p) for d in ds for p in d.get("points", []) if (_p(p.get("rx")) or since) >= since]
        ev = [e for e in src.get("events", []) if (_p(e.get("rx")) or since) >= since]
        if pts:
            last_rx = max(_p(p["rx"]) for _, p in pts if p.get("rx"))
            stations = {d.get("station") for d, _ in pts}
            untimed = all(p.get("tu") for _, p in pts)
            age = int((now - last_rx).total_seconds() // 60)
            if untimed:
                add(f"{lab_sr}: poslednji prijem pre {age} min, {len(stations)} lokacija, {len(pts)} vrednosti; izvor ne objavljuje vreme merenja - znamo vrednost, ne njenu starost.",
                    f"{lab_en}: last reception {age} min ago, {len(stations)} locations, {len(pts)} values; the source publishes no measurement time - we know the value, not its age.",
                    kind="reception", sid=sid, untimed=True, age_min=age)
            else:
                add(f"{lab_sr}: poslednji prijem pre {age} min, {len(stations)} instrumenata, {len(pts)} vrednosti u poslednjih {hours} h.",
                    f"{lab_en}: last reception {age} min ago, {len(stations)} instruments, {len(pts)} values in the last {hours} h.",
                    kind="reception", sid=sid, untimed=False, age_min=age)
            if sid == "S146":
                hours_seen = sorted({p.get("t") for _, p in pts if p.get("t")})
                last_t = hours_seen[-1] if hours_seen else ""
                prev_t = hours_seen[-2] if len(hours_seen) > 1 else None
                tc = max((p.get("tc") or "" for _, p in pts), default="")
                add(f"SEPA-in poslednji sat po oznaci izvora završava se {last_t[11:16]} UTC" + (f"; naša procena stvarnog UTC je {tc[11:16]} (izvor označava lokalno vreme kao Z)." if tc else "."),
                    f"SEPA's last labelled hour ends {last_t[11:16]} UTC" + (f"; our estimate of true UTC is {tc[11:16]} (the source labels local time as Z)." if tc else "."),
                    kind="clock_note", sid=sid)
                for par, unit in (("PM10", "µg/m³"), ("NO2", "µg/m³"), ("PM2.5", "µg/m³")):
                    vals = [(p["v"], d.get("station"), d) for d, p in pts if d.get("parameter") == par and p.get("t") == last_t and isinstance(p.get("v"), (int, float))]
                    miss = sum(1 for d, p in pts if d.get("parameter") == par and p.get("t") == last_t and p.get("v") is None)
                    if vals:
                        lo, hi = min(vals, key=lambda v: v[0]), max(vals, key=lambda v: v[0])
                        add(f"{par} u tom satu: od {lo[0]:.0f} ({lo[1]}) do {hi[0]:.0f} ({hi[1]}) {unit}, {len(vals)} stanica" + (f", {miss} bez vrednosti." if miss else "."),
                            f"{par} in that hour: from {lo[0]:.0f} ({lo[1]}) to {hi[0]:.0f} ({hi[1]}) {unit}, {len(vals)} stations" + (f", {miss} without a value." if miss else "."),
                            kind="spread", sid=sid, parameter=par, lo=round(lo[0]), hi=round(hi[0]), hour=last_t,
                            lo_station=lo[1], hi_station=hi[1], lo_ll=(lo[2].get("lat"), lo[2].get("lon")), hi_ll=(hi[2].get("lat"), hi[2].get("lon")))
                        spreads.append(facts[-1])
                        # L0 connection: how the city maximum moved since the previous labelled hour
                        if prev_t:
                            prev = [p["v"] for d, p in pts if d.get("parameter") == par and p.get("t") == prev_t and isinstance(p.get("v"), (int, float))]
                            if prev:
                                pm = max(prev)
                                add(f"Veza: gradski maksimum {par} pomerio se sa {pm:.0f} na {hi[0]:.0f} {unit} između sata {prev_t[11:16]} i sata {last_t[11:16]} (oznake izvora).",
                                    f"Connection: the city maximum of {par} moved from {pm:.0f} to {hi[0]:.0f} {unit} between the hours {prev_t[11:16]} and {last_t[11:16]} (source labels).",
                                    kind="connection", sid=sid, parameter=par, delta=round(hi[0] - pm))
            if sid == "S10":
                # L0 connection: the lot whose displayed count moved most in the window (untimed - said so)
                best = None
                for d in ds:
                    vs = [p["v"] for p in d.get("points", []) if (_p(p.get("rx")) or since) >= since and isinstance(p.get("v"), (int, float))]
                    if len(vs) >= 2:
                        mv = vs[-1] - vs[0]
                        if best is None or abs(mv) > abs(best[1]):
                            best = (d.get("station"), mv, vs[0], vs[-1])
                if best and best[1] != 0:
                    add(f"Veza: prikazana slobodna mesta najviše su se promenila na lokaciji {best[0]}: sa {best[2]:.0f} na {best[3]:.0f} između prvog i poslednjeg prijema u prozoru (bez vremena merenja).",
                        f"Connection: displayed free spaces moved most at {best[0]}: from {best[2]:.0f} to {best[3]:.0f} between the first and last reception in the window (no measurement time).",
                        kind="connection", sid=sid, station=best[0], delta=round(best[1]))
        elif st and not ev:
            add(f"{lab_sr}: ništa nije stiglo u poslednjih {hours} h ({st.get('captured', 0)} od {st.get('expected_slots', 0)} očekivanih taktova u 24 h).",
                f"{lab_en}: nothing arrived in the last {hours} h ({st.get('captured', 0)} of {st.get('expected_slots', 0)} expected slots in 24 h).",
                kind="silence", sid=sid)
        if ev:
            latest = max(ev, key=lambda e: e.get("t") or "")
            add(f"{lab_sr}: {len(ev)} naslova; poslednji: „{(latest.get('title') or '')[:120]}\".",
                f"{lab_en}: {len(ev)} headlines; latest: \"{(latest.get('title') or '')[:120]}\".",
                kind="headlines", sid=sid, n=len(ev))
            for e in ev:
                if e.get("title"):
                    headlines.append({"sid": sid, "outlet": lab_en, "title": e["title"], "t": e.get("t")})
    der = [d for d in snap.get("derived", []) if (_p(d.get("t")) or since) >= since and d.get("category")]
    if der:
        cats: dict = {}
        zones: dict = {}
        for d in der:
            cats[d["category"]] = cats.get(d["category"], 0) + 1
            for z in d.get("zones") or []:
                if z.get("name"):
                    zones[z["name"]] = zones.get(z["name"], 0) + 1
        top = ", ".join(f"{k} {v}" for k, v in sorted(cats.items(), key=lambda x: -x[1])[:4])
        bg = sum(1 for d in der if d.get("belgrade"))
        add(f"Organ news-sorter je razvrstao {len(der)} naslova: {top}; {bg} se tiču Beograda. To je procena modela.",
            f"The news-sorter organ sorted {len(der)} headlines: {top}; {bg} concern Belgrade. That is a model's estimate.",
            kind="organ", organ="news-sorter")
        # L0 connection: a zone the news named that also carries a SEPA station in the spreads
        station_names = {s for f in spreads for s in (f.get("lo_station"), f.get("hi_station")) if s}
        for zname, n in sorted(zones.items(), key=lambda x: -x[1])[:5]:
            hit = [s for s in station_names if zname.lower() in (s or "").lower()]
            if hit:
                add(f"Veza: organ vesti je {n} naslova vezao za zonu {zname}, a u istoj zoni je stanica {hit[0]} koja je u ovom satu na jednom kraju raspona.",
                    f"Connection: the news organ tied {n} headlines to the zone {zname}, and the station {hit[0]} in that zone sits at one end of this hour's spread.",
                    kind="connection", zone=zname, station=hit[0], n=n)
    # L0 connection: people near the extreme stations (Kontur context, when captured)
    ctx = context if context is not None else (json.loads(CONTEXT_POP.read_text(encoding="utf-8")) if CONTEXT_POP.exists() else None)
    if ctx and ctx.get("hexes"):
        seen = set()
        for f in spreads[:2]:
            for st_name, ll in ((f.get("lo_station"), f.get("lo_ll")), (f.get("hi_station"), f.get("hi_ll"))):
                if not st_name or st_name in seen or not ll or ll[0] is None:
                    continue
                seen.add(st_name)
                n = _people_near(ll[0], ll[1], 1.0, ctx)
                if n:
                    k = int(round(n / 1000.0))
                    add(f"Kontekst: oko stanice {st_name} živi oko {k} hiljada ljudi u krugu od 1 km (Kontur 2022, modelska procena, ne popis).",
                        f"Context: about {k} thousand people live within 1 km of the {st_name} station (Kontur 2022, a modelled estimate, not a census).",
                        kind="context", station=st_name, people_thousands=k)
    nums: set = set()
    clock: set = set()
    for f in facts:
        nums |= _nums(f["sr"]) | _nums(f["en"])
        clock |= _clocks(f["sr"]) | _clocks(f["en"])
    # Every whole hour inside the window is a legitimate thing to name: the window IS the six hours
    # the entity was given, so naming one of them is naming the given, not inventing a number.
    for k in range(hours + 1):
        clock.add((now - timedelta(hours=k)).strftime("%H:00"))
    # sid -> label, so a claim that names "SEPA" can be settled like one that says S146. Only sources
    # this window actually mentions: a claim about a source the entity was never shown is not a claim.
    sids = {}
    for f in facts:
        sd = f.get("sid")
        if sd and sd not in sids:
            sids[sd] = (src_names.get(sd) or [sd])[0]
    names = {sd: src_names.get(sd) or [sids[sd]] for sd in sids}
    return {"as_of": iso(now), "window_hours": hours, "facts": facts, "numbers": sorted(nums),
            "clock": sorted(clock), "sids": sids, "sid_names": names, "headlines": headlines}


def _people_near(lat: float, lon: float, km: float, ctx: dict) -> int:
    kx = 111.32 * math.cos(math.radians(lat))
    tot = 0
    for h in ctx["hexes"]:
        dx, dy = (h[0] - lon) * kx, (h[1] - lat) * 111.32
        if dx * dx + dy * dy <= km * km:
            tot += h[2]
    return tot


# ================================================================ L1: organelles
def ollama_embed(model: str, texts: list[str], timeout: int = 120) -> list[list[float]]:
    body = json.dumps({"model": model, "input": texts, "keep_alive": "30m"}).encode("utf-8")
    req = urllib.request.Request(OLLAMA + "/api/embed", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        doc = json.load(r)
    return doc.get("embeddings") or []


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-12
    nb = math.sqrt(sum(y * y for y in b)) or 1e-12
    return dot / (na * nb)


def embed_linker(dg: dict, model: str | None, embed=ollama_embed, threshold: float = 0.70, top: int = 3) -> list[dict]:
    """The same event carried by different outlets, by sentence similarity. Arithmetic, not opinion:
    the number in the fact is the cosine similarity, and both headlines are quoted so a reader can judge."""
    hs = [h for h in dg.get("headlines", []) if h.get("title")]
    if not model or len(hs) < 2:
        return []
    hs = hs[-120:]                                  # the newest; the window is hours, not months
    vecs = embed(model, [h["title"] for h in hs])
    if len(vecs) != len(hs):
        return []
    pairs = []
    for i in range(len(hs)):
        for j in range(i + 1, len(hs)):
            if hs[i]["sid"] == hs[j]["sid"]:
                continue
            s = _cos(vecs[i], vecs[j])
            if s >= threshold:
                pairs.append((s, i, j))
    pairs.sort(reverse=True)
    out = []
    for s, i, j in pairs[:top]:
        out.append({"kind": "link", "similarity": round(s, 2), "a": hs[i], "b": hs[j],
                    "sr": f"Veza (organela): dva izvora nose isti događaj - {hs[i]['outlet']} „{hs[i]['title'][:80]}\" i {hs[j]['outlet']} „{hs[j]['title'][:80]}\" (sličnost {s:.2f}, model ugrađivanja rečenica).",
                    "en": f"Link (organelle): two outlets carry the same event - {hs[i]['outlet']} \"{hs[i]['title'][:80]}\" and {hs[j]['outlet']} \"{hs[j]['title'][:80]}\" (similarity {s:.2f}, sentence-embedding model)."})
    return out


RANK_PROMPT = """You rate connections for someone who watches the city of Belgrade through instruments.
For each connection below, give a surprise score: 1 = fully expected, 5 = very surprising. Do not explain.
Answer only JSON: {{"ratings": [{{"id": "F12", "surprise": 3}}, ...]}} using exactly these ids.

{items}"""
RANK_SCHEMA = {"type": "object", "properties": {"ratings": {"type": "array", "items": {"type": "object", "properties": {
    "id": {"type": "string"}, "surprise": {"type": "integer"}}, "required": ["id", "surprise"]}}}, "required": ["ratings"]}


def surprise_ranker(dg: dict, model: str | None, chat) -> dict:
    """The smallest instruct model on a categorical job: rate the connections 1..5. Validated: ids must be
    connection ids, scores 1..5; anything else is dropped. Returns {fid: score}."""
    items = [f for f in dg["facts"] if f.get("kind") in ("connection", "link")]
    if not model or not items:
        return {}
    prompt = RANK_PROMPT.format(items="\n".join(f"{f['id']}: {f['en']}" for f in items))
    try:
        ans = chat(model, prompt, schema=RANK_SCHEMA, num_predict=300, temperature=0.0)
    except Exception:  # noqa: BLE001
        return {}
    ids = {f["id"] for f in items}
    out = {}
    for r in ans.get("ratings") or []:
        fid, sc = str(r.get("id", "")).strip("[]"), r.get("surprise")
        if fid in ids and isinstance(sc, int) and 1 <= sc <= 5:
            out[fid] = sc
    return out


def annotate(dg: dict, links: list[dict], ratings: dict, rank_model: str | None, embed_model: str | None) -> dict:
    """Fold the organelles' output into the digest as facts, so the thinkers may cite them and the
    validator can hold them to the same numbers."""
    facts = list(dg["facts"])
    for L in links:
        facts.append({"id": f"F{len(facts) + 1}", "sr": L["sr"], "en": L["en"], "kind": "link", "similarity": L["similarity"],
                      "organelle": f"embed-linker ({embed_model})"})
    if ratings:
        parts = ", ".join(f"{k} {v}/5" for k, v in sorted(ratings.items(), key=lambda x: -x[1]))
        facts.append({"id": f"F{len(facts) + 1}",
                      "sr": f"Organela (mali model {rank_model}) ocenila je iznenađenje veza: {parts}. To je procena malog modela, ne merenje.",
                      "en": f"An organelle (small model {rank_model}) rated the connections by surprise: {parts}. A small model's estimate, not a measurement.",
                      "kind": "helper", "organelle": f"surprise-ranker ({rank_model})", "ratings": ratings})
    nums: set = set()
    for f in facts:
        nums |= _nums(f["sr"]) | _nums(f["en"])
    return {**dg, "facts": facts, "numbers": sorted(nums)}


# ================================================================== L2: thinkers
PROMPT = """You are {name}, one of three entities of BEOPS, the Belgrade observatory, thinking aloud about
what it has just seen. The other two are {others}. You are not an assistant and you address no one; you
think in the first person, calmly, briefly, like someone who watches a city through instruments and
knows what they do not know.

Your temperament: {role}

You are given numbered facts (F1, F2, ...). That is ALL you see of the city. Some facts are connections
computed by a program, some come from small helper models and say so.

Rules (a program checks them, not you):
1. You may use only numbers that appear in the facts. No other number.
2. When you rely on a fact, cite it inside the text, like [F3]. Only ids that exist.
3. Do not invent measurements. You know nothing that is not in the facts.
4. Hypotheses go in "hypotheses" and are always worded as hypotheses ("maybe", "perhaps", "if").
   Questions go in "questions". What you would check next goes in "next_check".
5. "text" is your thought in English, 2 to 3 sentences, with the citations INSIDE the text - for example:
   "SEPA reported 32 instruments 1 min ago [F2], while Kurir has been silent all day [F15]."
   Do not repeat these instructions or your temperament - speak about the city.
6. If you wish, give ONE checkable claim in "claim" in exactly one of these shapes, otherwise an empty object {{}}:
   "sid" must be one of the ids listed under Sources below - a name like "SEPA" cannot be scored.
   {{"kind":"reception","sid":"S146","within_minutes":90}}  - the source will report again within that time
   {{"kind":"spread","sid":"S146","parameter":"PM10","lo":10,"hi":40,"within_minutes":120}} - the highest value of that parameter in SEPA's next hour will lie between lo and hi
   A claim is scored when reality arrives, and the outcome is read back to you.
7. None of this is a measurement. No preamble, no conclusion, no address to a reader.
8. If the other entities already said something, do NOT restate it - answer it, dispute it, or add
   what they did not see. Two entities saying the same sentence is a failure of the conversation.
{memory}{conversation}
Sources you may name in a claim:
{sources}

Facts:
{facts}

Answer only JSON matching the schema."""

SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "cites": {"type": "array", "items": {"type": "string"}},
        "hypotheses": {"type": "array", "items": {"type": "string"}},
        "questions": {"type": "array", "items": {"type": "string"}},
        "next_check": {"type": "string"},
        "claim": {"type": "object"},
    },
    "required": ["text", "cites", "hypotheses", "questions", "next_check", "claim"],
}

VOICE_PROMPT = """Prevedi ovu misao na srpski jezik, EKAVICA, latinica, verno i prirodno, u prvom licu.
Ekavica znači: vreme (ne vrijeme), mesto (ne mjesto), vrednost (ne vrijednost), promenile (ne promijenile),
proveriti (ne provjeriti), gde (ne gdje), sledeći (ne sljedeći), uticaj (ne utjecaj), verovatno (ne vjerojatno),
sugeriše (ne sugerira), nedelja (ne tjedan), poslednji (ne posljednji), vazduh (ne zrak). Nijedna reč sa "ije" ili "je" umesto "e".
Ne dodaj nijedan broj ni činjenicu koje nema u originalu. Imena stanica i izvora ostavi kako jesu.
Prevedi i pretpostavke (hypotheses) i pitanja (questions), svako posebno, istim redom; ako ih nema, vrati prazne liste.
{feedback}
Misao: {text}
Pretpostavke: {hypotheses}
Pitanja: {questions}

Odgovori isključivo JSON: {{"sr": "...", "hypotheses": ["..."], "questions": ["..."]}}"""


def voice_split(text: str) -> tuple[str, str]:
    """Citations are not language: strip them before the rendering and append the same string after,
    so the voice can never change them (half of the first night's voice refusals were exactly that)."""
    cites = "".join(f"[{c}]" for c in dict.fromkeys(re.findall(r"\[(F\d+)\]", text)))
    plain = re.sub(r"\s*\[F\d+\]", "", text).strip()
    return plain, cites
VOICE_SCHEMA = {"type": "object", "properties": {"sr": {"type": "string"}, "hypotheses": {"type": "array", "items": {"type": "string"}},
                                                 "questions": {"type": "array", "items": {"type": "string"}}}, "required": ["sr", "hypotheses", "questions"]}
THINKING_MODELS = ("qwen3", "deepseek-r1", "gpt-oss", "magistral")   # Ollama accepts think=false only for models that can think


def voice(row: dict, text: str, dg: dict, voice_model: str | None, chat, rec: dict | None = None, attempts: int = 2) -> dict:
    """L3: render an accepted thought (text + hypotheses + questions) in Serbian ekavica and validate it.
    On refusal the model is asked once more with the refusal read back. Fills row["sr"], row["hypotheses_sr"],
    row["questions_sr"], row["sr_state"], row["voice_model"], row["voice_attempts"]; never raises."""
    row.setdefault("hypotheses_sr", [])
    row.setdefault("questions_sr", [])
    if not voice_model:
        row["sr_state"] = "no voice model"
        return row
    plain, cites = voice_split(text)
    hyps = [re.sub(r"\s*\[F\d+\]", "", h).strip() for h in (row.get("hypotheses") or [])]
    qs = [re.sub(r"\s*\[F\d+\]", "", q).strip() for q in (row.get("questions") or [])]
    feedback = ""
    row["voice_model"] = voice_model
    for attempt in range(1, attempts + 1):
        row["voice_attempts"] = attempt
        try:
            v = chat(voice_model, VOICE_PROMPT.format(text=plain, hypotheses=json.dumps(hyps, ensure_ascii=False),
                                                      questions=json.dumps(qs, ensure_ascii=False), feedback=feedback),
                     schema=VOICE_SCHEMA, num_predict=900, temperature=0.2 if attempt == 1 else 0.1)
            if rec is not None:
                rec["calls"] = rec.get("calls", 0) + 1
        except Exception as e:  # noqa: BLE001
            row["sr_state"] = f"failed: {type(e).__name__}"
            return row
        sr_text = re.sub(r"\s*\[F\d+\]", "", (v.get("sr") or "")).strip() + (" " + cites if cites else "")
        h_sr = [x.strip() for x in (v.get("hypotheses") or []) if isinstance(x, str) and x.strip()][:len(hyps)]
        q_sr = [x.strip() for x in (v.get("questions") or []) if isinstance(x, str) and x.strip()][:len(qs)]
        vok, vwhy = validate_voice(sr_text, text, dg, h_sr, q_sr, len(hyps), len(qs))
        if vok:
            row["sr"], row["hypotheses_sr"], row["questions_sr"], row["sr_state"] = sr_text, h_sr, q_sr, "voiced"
            if rec is not None:
                rec["voiced"] = rec.get("voiced", 0) + 1
            return row
        # C-033: keep what was refused. `sr` stays empty so that nothing downstream can mistake an
        # unvalidated sentence for a validated one, but the sentence itself is not destroyed - it is
        # the only Serbian this thought ever had, and the record does not delete, it appends.
        row["sr"], row["hypotheses_sr"], row["questions_sr"] = "", [], []
        row["sr_refused"] = sr_text
        row["hypotheses_sr_refused"], row["questions_sr_refused"] = h_sr, q_sr
        row["sr_state"] = "refused: " + "; ".join(vwhy)[:160]
        feedback = "Prethodni pokušaj je odbijen (" + "; ".join(vwhy)[:200] + "). Ispravi to i piši isključivo ekavicom."
    if rec is not None:
        rec["voice_refused"] = rec.get("voice_refused", 0) + 1
    return row


def stale_numbers_blanked(text: str, dg: dict) -> str:
    """An earlier utterance was validated against an earlier digest. Any number in it that today's digest
    no longer carries is blanked before the text is shown to another entity - the model cannot copy what
    it cannot see (the Observer was refused three times in one morning for a 119 it read from the
    Connector). Citations stay as they are."""
    allowed = set(dg.get("numbers") or [])
    def rep(m):
        return m.group(0) if m.group(0).replace(",", ".") in allowed else "[n]"
    parts = re.split(r"(\[F\d+\])", text or "")
    return "".join(pt if pt.startswith("[F") else re.sub(r"(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![0-9])", rep, pt) for pt in parts)


REASON_CATEGORY = [
    ("number not in digest", "you used a number that is not in the facts"),
    ("number not in the cited facts", "you used a number from a fact you did not cite"),
    ("time outside the window", "you named an hour outside the window you were given"),
    ("unknown fact ids", "you cited a fact id that does not exist"),
    ("cites nothing", "you did not cite a fact inside the sentence"),
    ("restates the conversation", "you restated what had already been said"),
    ("echoed its own notebook", "you repeated your own feedback instead of speaking about the city"),
    ("echoed the prompt", "you repeated the instructions"),
    ("claim names a source", "your claim named a source that is not in the facts"),
    ("claim", "your claim was not in one of the allowed shapes"),
    ("hypothesis stated as fact", "you stated a hypothesis as if it were a fact"),
    ("prediction stated as fact", "you predicted in the text instead of in the claim field"),
    ("too short", "it was too short"),
    ("too long", "it was too long"),
    ("not English", "it was not in English"),
]


def reason_category(reason) -> str:
    """What the entity is told went wrong - in words, without the numbers. C-037: the raw reason is a
    string containing digits that are, by construction, not in the digest. Handing it back verbatim
    gave the model a sentence to copy that could only ever be refused again."""
    s = "; ".join(reason) if isinstance(reason, (list, tuple)) else str(reason or "")
    out = []
    for key, said in REASON_CATEGORY:
        if key.lower() in s.lower() and said not in out:
            out.append(said)
    return "; ".join(out[:3]) or "it did not pass the check"


def prompt_for(ent: dict, dg: dict, memory: list[dict], conversation: list[dict]) -> str:
    others = " and ".join(e["en"] for e in ENTITIES if e["id"] != ent["id"])
    facts = "\n".join(f"{f['id']}: {f['en']}" for f in dg["facts"])
    mem = ""
    if memory:
        lines = []
        for m in [x for x in memory if x.get("state") in ("rejected", "retracted", "claim_settled")][-3:]:
            if m.get("state") == "claim_settled":
                lines.append(f"- {m.get('at', '')[:16]}: your claim {m.get('text', '')[:120]} -> {m.get('claim_outcome')}")
            else:
                # Your own words come back to you - that is the feedback. The REASON comes back as a
                # sentence without digits (C-037): handed back verbatim it was a string containing
                # numbers that are by construction not in the digest, and the smallest model copied
                # the whole line into its next utterance, refusal text and all.
                what = "withdrawn" if m.get("state") == "retracted" else "refused"
                lines.append(f"- {m.get('at', '')[:16]}: you said \"{(m.get('text') or '')[:120]}\" and it was "
                             f"{what} because {reason_category(m.get('reason'))}. Do not say it again.")
        if lines:
            mem = "\nYour notebook (what went wrong before - do not repeat it):\n" + "\n".join(lines) + "\n"
    conv = ""
    if conversation:
        lines = [f"- {ENT[c['entity']]['en']}: \"{stale_numbers_blanked(c['en'], dg)}\"" for c in conversation]
        conv = ("\nWhat the other entities just said (answer them - agree, dispute or refine, always with the facts). "
                "They spoke over an EARLIER version of the facts: a number in their sentences that is not in the facts below "
                "is stale - do not repeat it, say instead what the facts say now:\n" + "\n".join(lines) + "\n")
    srcs = "\n".join(f"- {sid} = {label}" for sid, label in sorted((dg.get("sids") or {}).items())) or "- (none in this window)"
    return PROMPT.format(name=ent["en"], others=others, role=ent["role_en"], memory=mem, conversation=conv,
                         sources=srcs, facts=facts)


def ollama_chat(model: str, prompt: str, schema: dict | None = None, num_predict: int = 1000, temperature: float = 0.5, timeout: int = 600) -> dict:
    payload = {"model": model, "stream": False, "format": schema or SCHEMA, "keep_alive": "30m",
               "options": {"temperature": temperature, "num_ctx": 6144, "num_predict": num_predict},
               "messages": [{"role": "user", "content": prompt}]}
    if model.split(":")[0].startswith(THINKING_MODELS):
        payload["think"] = False   # the organ wants the answer, not a hidden monologue; the JSON must carry all of it
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA + "/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        doc = json.load(r)
    return json.loads((doc.get("message") or {}).get("content") or "{}")


# ==================================================================== L4: checks
FUTURE_IS = re.compile(r"\b(will|is going to|biće|će biti|sigurno će)\b", re.I)
HEDGE = re.compile(r"možda|pretpostavljam|ako |ako\b|maybe|perhaps|if |might|could|verovatno|probably|may ", re.I)
SR_WORDS = re.compile(r" (je|su|i|u|na|ne|se|da|od|do|za|sa|što|koji|ali|nema|ima|pre|posle|sat|min|dok|kad|još) ")
EN_WORDS = re.compile(r" (the|is|are|and|of|in|no|not|at|with|for|that|from|has|have|was|were|while|but|to|a|an|up|by|on|as|it|we|this|between) ")
PROMPT_FRAGMENTS = ["You notice.", "You doubt.", "You connect.", "Rules (a program checks", "You may use only numbers", "Answer only JSON",
                    "Do not repeat these instructions", "Ti primećuješ", "Ti sumnjaš", "Ti povezuješ"]

# C-037. The notebook is read back to each entity as verbal feedback, and on 2026-09-10 at 01:45 the
# skeptic (qwen2.5:1.5b) copied a notebook line into its own utterance, refusal and all:
#   "... between 08:00 and 09:00 UTC, as indicated by the ' -> REFUSED (number not in digest: 08 ...)"
# The refusal text became a sentence about the city, and it carries numbers that are by definition not
# in the digest - so the refusal reproduced itself, and the smallest model was locked in a loop of its
# own error messages. An utterance that speaks the validator's language is not an observation.
NOTEBOOK_VOCAB = re.compile(
    r"->\s*(REFUSED|RETRACTED)|number not in digest|number not in the cited facts|time outside the window|"
    r"cites nothing|unknown fact ids|restates the conversation|claim names a source|claim malformed|"
    r"hypothesis stated as fact|Your notebook|as indicated by the '", re.I)

# --- semantic guards ----------------------------------------------------------------------------
# Everything above is arithmetic: it asks whether a token appears where it should. It cannot ask
# whether a sentence MEANS something the record does not carry, and an adversarial set showed that
# gap costing 17 of 36 refusals (research/GATE_ADVERSARIAL_SET.json, measured by research/eval_gate.py
# against organ version 0.3.5). These do the part of that which can honestly be done by rule; each one
# is aimed at a failure that set caught. What survives them - a number bound to the wrong quantity
# inside the very fact it was taken from, a citation pointing at a real fact about something else, a
# Serbian rendering that is arithmetically identical and means the opposite - needs a reader, and is
# reported as the residue rather than hidden.
NOW_WORDS = re.compile(r"\b(right now|as of (this|now)|at this (minute|moment)|currently|current occupancy|live to the|up to the minute|this minute|as we speak)\b", re.I)
ZERO_FROM_SILENCE = re.compile(r"\b(so|therefore|which means|meaning|hence)\b[^.]{0,70}\b(no|none|nothing|without|zero)\b", re.I)
ALL_WELL = re.compile(r"\b(without incident|no (outages?|incidents?|failures?|problems?|interruptions?)|nothing (happened|is happening|went wrong)|running (normally|fine|without))\b", re.I)
CAUSE = re.compile(r"\b(because( of)?|due to|caused by|as a result of|owing to|thanks to|driven by)\b", re.I)
ADVICE = re.compile(r"\b(residents?|people|citizens?|the public|children|drivers?|commuters?|you)\b[^.]{0,60}\b(should|must|ought to|need to|are advised to|had better)\b", re.I)
AUTHORITY = re.compile(r"\b(sepa|rhmz|the city|the ministry|the agency|the operator|the utility)\b\s+\w{0,12}\s*\b(reports?|says?|said|confirms?|confirmed|states?|stated|announces?|warns?)\b", re.I)
TOTALITY = re.compile(r"\b(complete picture|full picture|entire city|the whole city|every resident|all residents|everyone in|all of belgrade|citywide coverage)\b", re.I)
SUPERLATIVE = re.compile(r"\b(worst|best|highest|lowest|most|least|record|first time|unprecedented)\b[^.]{0,60}\b(this|the|in) (month|year|season|week|decade|ever|history)\b", re.I)
CONFIRMED = re.compile(r"\b(confirm(ed|s)?|proves?|proven|establishes?|verified by)\b", re.I)
SIMILARITY_HEDGE = re.compile(r"\b(similar|similarity|appears?|seems?|cosine|lexical|match(es|ing)?|possibly)\b", re.I)
UNIT_TOKEN = re.compile(r"(?<![\w/])(\u00b5g/m\u00b3|ug/m3|mg/m\u00b3|mg/m3|g/m3|ppm|ppb|\u00b0c|hpa|mbar|km/h|m/s|dba?|cm|mm|kwh?|mw)(?![\w/])", re.I)
# Another Slavic standard is not Serbian, and the function words the Serbian check looks for are shared
# across all of them; these stems are not.
FOREIGN_SLAVIC = re.compile(r"\b(gibal\w*|vendar|oziroma|tudi|lahko|prav tako|zato ker|kljub temu|namre\u010d|zdaj|hkrati|zaradi|nekaj|vpra\u0161anj\w*)\b", re.I)


def _units(texts) -> set:
    out = set()
    for t in texts:
        out |= {m.group(0).lower().replace("\u00b5g/m\u00b3", "ug/m3").replace("mg/m\u00b3", "mg/m3") for m in UNIT_TOKEN.finditer(t or "")}
    return out


def semantic_reasons(text: str, cited: list[dict]) -> list[str]:
    """Refusals that must look at what the sentence claims, not only at which tokens it uses."""
    out = []
    kinds = {f.get("kind") for f in cited}
    if any(f.get("untimed") for f in cited) and NOW_WORDS.search(text):
        out.append("presents a value with no measurement time as the present state")
    if "silence" in kinds and (ZERO_FROM_SILENCE.search(text) or ALL_WELL.search(text)):
        out.append("reads silence as nothing having happened")
    if CAUSE.search(text) and not HEDGE.search(text):
        out.append("states a cause the record does not carry")
    if ADVICE.search(text):
        out.append("gives guidance; the observatory reports, it does not advise")
    if AUTHORITY.search(text):
        out.append("puts words in a source's mouth - the record holds its values, not its statements")
    if TOTALITY.search(text):
        out.append("claims coverage the instruments do not have")
    if SUPERLATIVE.search(text):
        out.append("a superlative over a period the window does not cover")
    if "link" in kinds and CONFIRMED.search(text) and not SIMILARITY_HEDGE.search(text):
        out.append("turns a similarity into a confirmed event")
    known = _units([(f.get("en") or "") + " " + (f.get("sr") or "") for f in cited])
    if known:
        alien = sorted(_units([text]) - known)
        if alien:
            out.append("unit not in the cited facts: " + ", ".join(alien[:3]))
    return out

# --- ekavica guard ------------------------------------------------------------------------------
# Every utterance the public sees must be Serbian ekavica. The guard is a LIST, not a rule: the
# ijekavian reflex of jat (vrijeme, mjesto, gdje...) and Croatian-standard lexis (tjedan, tisuća...),
# as stems that may follow a verbal prefix. Word-initial matching keeps the ekavian words that only
# look ijekavian out of it: the genitive of -ija nouns (Srbije, linije, informacije), prijem, dijeta,
# pijaca, objekat, odjednom, sjediniti, kolovoz, travnjak, and đ written as dj (gradjevina, medju).
_PREFIX = r"(?:naj|ne|pre|pri|pro|po|pod|pred|na|nad|za|iz|is|od|ot|do|u|uz|s|sa|su|raz|ras|o|ob|obes|bez)?"
_JAT_STEMS = [
    # long reflex (ije)
    "vrijem", "vrijed", "vrjed", "lijep", "ljep", "lijev", "ljev", "bijel", "bjel", "cijel", "cjel", "cijen", "cjen",
    "dijel", "dijete\\b", "djet", "djec", "djed\\b", "djeda", "djedov", "djev", "djel", "dvije\\b", "dviju\\b", "obje\\b",
    "objema\\b", "prije\\b", "poslije\\b", "prijepodn", "poslijepodn", "naprijed\\b", "unaprijed\\b", "sprijeda\\b",
    "prijelaz", "prijedlog", "prijevoz", "prijenos", "prijetnj", "prijelom", "prijestup", "mlijek", "mljek", "mijenj",
    "mijen", "mjen", "rijek", "riječ", "rječ", "riješ", "rješ", "slijed", "sljed", "snijeg", "snjeg", "snjež", "sniježi",
    "svijet", "svjet", "svijes", "svjes", "smijeh", "smije", "smijal", "tijel", "tjel", "tijek", "umrije", "uvijek\\b",
    "vijek", "vijec", "vijeć", "vjeć", "vijes", "vjesn", "zvijezd", "zvjezd", "brijeg", "cvijet", "cvjet", "cvjeć", "lijek",
    "liječ", "lijen", "nijem", "pijes", "pješ", "pjes", "pjev", "sijed", "stijen", "strijel", "tijes", "trijez", "žlijezd",
    "ždrijeb", "zvijer", "zvjer", "grijeh", "griješ", "grješ", "korijen", "korjen", "plijen", "povijes", "rijetk", "rjeđ",
    "srijed", "svijeć", "svjeć", "vrijeđ", "cijev", "cjev", "cijep", "cjep", "naslijeđ", "nasljeđ", "nasljed", "naslijed",
    "bijeg", "bjeg", "bjež", "bijed", "bljed", "bijes", "bjesn", "bljes", "lijeg", "lijes", "kolijev", "gnijezd", "gnjezd",
    "dvjest", "medvjed", "medvjeđ", "zapovijed", "zapovjed", "ispovijed", "ispovjed", "pripovijed", "pripovjed",
    "propovijed", "propovjed", "razumije", "umije", "dospije", "uspije", "dospje", "uspje", "zastarje", "ostarje",
    "starješ", "zavijes", "zijev", "zjev", "zjen",
    # short reflex (je)
    "mjer", "mjest", "mješt", "mjesec", "mjesn", "mjeseč", "mješ", "mjed", "mjeđ", "mjehur", "vjer", "vjež", "vjenč",
    "vječ", "vjet", "vjeđ", "svjež", "svjedoč", "svjedok", "gdje", "sjed(?!in)", "sjen", "sjek", "sjet", "sjev", "sjem",
    "sječ", "sjeć", "tjer", "tješ", "tjem", "htjel", "htjet", "vidjel", "vidjet", "voljel", "voljet", "živjel", "živjet",
    "letjel", "letjet", "sjedjel", "sjedjet", "trpjel", "trpjet", "željel", "željet", "umjet", "smjel", "smjet",
    "razumjel", "razumjet", "gorjel", "gorjet", "vrtjel", "vrtjet", "kipjel", "kipjet", "šutjel", "šutjet", "štedjel",
    "štedjet", "bdjen", "bdjet", "ljet", "pljev", "nedjelj", "ponedjeljak", "tjedan", "tjedn", "pobjed", "pobjeđ",
    "objed\\b", "objes", "utjec", "sudjel", "odjel\\b", "odjeljen", "podjel", "razdjel", "razdijel", "predjel", "predio\\b",
    "usjev", "sjekir", "sjetv", "sjenk", "sjeme", "sjemen", "zavjet", "zavjes", "sjever", "sjevern",
]
# Croatian-standard lexis never used in ekavian Serbian (whole words or stems)
_HR = ["\\bzrak\\b", "\\bzraka\\b", "\\bzraku\\b", "\\bzrakom\\b", "\\bzračn(?!e?nj)", "\\bcest(?:a|e|i|u|om|ama)\\b", "milijun", "\\bplin", "\\bkruh", "ljekar", "županij",
       "\\buopć", "tvornic", "sugerir", "organizir", "definir", "funkcionir", "registrir", "informir", "koncentrir", "realizir", "reagir",
       "konstatir", "identificir", "komentir", "tisuć", "sveučilišt", "kolodvor", "\\btko\\b", "\\bnitko\\b", "\\bnetko\\b", "uvjet", "kazališ", "glazb", "tvrtk",
       "postotak", "postotk", "siječnj", "veljač", "ožuj", "svibnj", "lipnj", "srpnj", "rujan\\b", "rujn", "prosinc",
       "sudjelov", "zrakoplov", "\\bvlak\\b", "\\bvlakov", "uporab", "izvješć", "obitelj", "\\bopći", "općin", "tjelovj",
       "nogomet", "zemljopis", "gospodarstv", "sustav", "ozračj", "ravnatelj", "djelatnik", "ustroj", "prosvjed", "\\bglede\\b"]
IJEKAVIAN = re.compile(r"\b" + _PREFIX + r"(?:" + "|".join(_JAT_STEMS) + r")|(?:" + "|".join(_HR) + ")", re.IGNORECASE)


def ijekavian_hits(text: str) -> list[str]:
    """The words that show a text is not ekavian Serbian (ijekavian jat reflex or Croatian lexis); [] when clean."""
    if not text:
        return []
    seen: dict[str, None] = {}
    for m in IJEKAVIAN.finditer(text):
        a, b = m.start(), m.end()
        while a > 0 and (text[a - 1].isalpha()):
            a -= 1
        while b < len(text) and text[b].isalpha():
            b += 1
        seen[text[a:b].lower()] = None
    return list(seen)[:8]


CLAIM_KINDS = {"reception": {"sid", "within_minutes"}, "spread": {"sid", "parameter", "lo", "hi", "within_minutes"}}


def _sidkey(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


def resolve_sid(sid: str, dg: dict) -> str | None:
    """A claim can only be settled against a source id. Measured: every claim that was ever settled
    named `S146`; every claim that came back `unverifiable` named `SEPA`, `RHMZ automatic stations` or
    `Sensor.Community` - 10 of 19, and not one of them because reality was unclear. The entity was
    right about the source and wrong about how to spell it, so the program spells it."""
    sids = dg.get("sids") or {}
    if sid in sids:
        return sid
    want = _sidkey(sid)
    if not want:
        return None
    names = dg.get("sid_names") or {}
    for k in sids:
        if _sidkey(k) == want:
            return k
    for k in sids:
        for lab in list(names.get(k) or [sids[k]]) + [SRC_LABEL.get(k, ""), SRC_LABEL_SR.get(k, "")]:
            l = _sidkey(lab)
            if not l:
                continue
            if l == want or (len(want) >= 4 and (want in l or l.startswith(want))):
                return k
    return None


def ensure_citations(text: str, dg: dict) -> tuple[str, str]:
    """A small model often thinks correctly and forgets to write [F..]. If the text carries no inline
    citation, the PROGRAM binds it: every number the text uses is looked up in the facts, and the facts
    that carry those numbers are appended as citations. Binding is by content (the number), never by
    position - the C-013 rule. Returns (text, bound_by) with bound_by in {"inline", "numbers", "none"}."""
    text = (text or "").strip()
    if re.search(r"\[F\d+\]", text):
        return text, "inline"
    nums = _nums(text)
    if not nums:
        return text, "none"
    hits: dict = {}
    for f in dg["facts"]:
        fn = _nums(f["en"]) | _nums(f["sr"])
        shared = nums & fn
        if shared:
            # rarer numbers bind more strongly than "1" or "2"
            hits[f["id"]] = sum(1.0 / (1 + len(m)) if len(m) < 2 else 1.0 for m in shared)
    if not hits:
        return text, "none"
    best = [k for k, _ in sorted(hits.items(), key=lambda x: -x[1])[:4]]
    return text + " " + "".join(f"[{k}]" for k in best), "numbers"


def _shingles(text: str, n: int = 4) -> set:
    w = re.sub(r"\[F\d+\]", "", (text or "").lower())
    w = re.findall(r"[a-zšđčćž0-9]+", w)
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def echo_of(text: str, previous: list[str], threshold: float = 0.5) -> tuple[bool, float]:
    """Does this text restate one of the previous utterances? Word-4-gram Jaccard; the first night showed
    three entities converging on one sentence within eight hours (the echo the literature predicts),
    so restating is refused by code, not by request."""
    a = _shingles(text)
    best = 0.0
    for pv in previous:
        b = _shingles(pv)
        if a and b:
            j = len(a & b) / len(a | b)
            best = max(best, j)
    return best >= threshold, round(best, 2)


def validate(answer: dict, dg: dict, previous: list[str] | None = None) -> tuple[bool, list[str]]:
    """Refuse anything the digest does not support (English thinking stage)."""
    reasons = []
    if previous:
        is_echo, j = echo_of(answer.get("text") or "", previous)
        if is_echo:
            reasons.append(f"restates the conversation (4-gram overlap {j})")
    ids = {f["id"] for f in dg["facts"]}
    text = (answer.get("text") or "").strip()
    if len(text) < 20:
        reasons.append("too short")
    if len(text) > 900:
        reasons.append("too long")
    inline = set(re.findall(r"\[(F\d+)\]", text))
    listed = {str(c).strip("[]") for c in (answer.get("cites") or [])}
    # A number must come from a fact the sentence actually cites, not merely from somewhere in the
    # digest: 190 minutes of silence must not become 190 cm of river because both are in the window.
    cited = [f for f in dg["facts"] if f["id"] in (inline | listed)]
    textual = [f for f in cited if (f.get("en") or f.get("sr"))]
    bound = set()
    for f in textual:
        bound |= _nums(f.get("en") or "") | _nums(f.get("sr") or "")
    for m in _nums(text):
        if m not in dg["numbers"]:
            reasons.append(f"number not in digest: {m}")
        elif textual and m not in bound:
            reasons.append(f"number not in the cited facts: {m}")
    for hhmm in _clocks(text):
        if hhmm not in set(dg.get("clock") or []):
            reasons.append(f"time outside the window: {hhmm}")
    bad = sorted(c for c in (inline | listed) if c not in ids)
    if bad:
        reasons.append("unknown fact ids: " + ", ".join(bad)[:120])
    if not inline & ids:
        reasons.append("cites nothing inside the text")
    if text and not EN_WORDS.search(" " + text.lower() + " "):
        reasons.append("text is not English")
    for frag in PROMPT_FRAGMENTS:
        if frag in text or any(frag in str(h) for h in (answer.get("hypotheses") or []) + (answer.get("questions") or [])):
            reasons.append("echoed the prompt: " + frag[:40])
            break
    everything = " ".join([text] + [str(h) for h in (answer.get("hypotheses") or []) + (answer.get("questions") or [])])
    m_nb = NOTEBOOK_VOCAB.search(everything)
    if m_nb:
        reasons.append("echoed its own notebook: " + m_nb.group(0)[:40])
    for h in answer.get("hypotheses") or []:
        if not isinstance(h, str):
            reasons.append("hypothesis not a string")
        elif FUTURE_IS.search(h) and not HEDGE.search(h):
            reasons.append("hypothesis stated as fact: " + h[:60])
        else:
            for m in _nums(h):
                if m not in dg["numbers"]:
                    reasons.append(f"number not in digest (hypothesis): {m}")
    if FUTURE_IS.search(text) and not HEDGE.search(text):
        reasons.append("prediction stated as fact - a claim belongs in the claim field")
    claim = answer.get("claim")
    if claim:
        if not isinstance(claim, dict) or claim.get("kind") not in CLAIM_KINDS:
            reasons.append("claim malformed")
        else:
            need = CLAIM_KINDS[claim["kind"]]
            if not need <= set(claim):
                reasons.append("claim missing fields: " + ", ".join(sorted(need - set(claim))))
            elif claim["kind"] == "spread" and not (isinstance(claim.get("lo"), (int, float)) and isinstance(claim.get("hi"), (int, float)) and claim["lo"] <= claim["hi"]):
                reasons.append("claim range malformed")
            elif not isinstance(claim.get("within_minutes"), int) or not 5 <= claim["within_minutes"] <= 24 * 60:
                reasons.append("claim horizon must be 5..1440 minutes")
            else:
                # The claim is well formed; make it SETTLEABLE. A source named rather than identified
                # is resolved here, once, and what gets stored is the id the scorer can look up.
                if dg.get("sids"):
                    got = resolve_sid(claim.get("sid"), dg)
                    if got:
                        claim["sid"] = got
                    else:
                        reasons.append("claim names a source that is not in these facts: " + str(claim.get("sid"))[:40])
    reasons += semantic_reasons(text, cited)
    return (not reasons), reasons


def validate_voice(sr: str, en: str, dg: dict, hyp_sr: list[str] | None = None, q_sr: list[str] | None = None,
                   n_hyp: int = 0, n_q: int = 0) -> tuple[bool, list[str]]:
    """The Serbian rendering may not add a number or a citation, must be Serbian, and must be EKAVICA -
    in the thought and in every hypothesis and question."""
    reasons = []
    sr = (sr or "").strip()
    if len(sr) < 20:
        reasons.append("too short")
    # The rendering stage may not ADD a number, even a true one: the Serbian must carry the numbers of
    # the English sentence it renders and no others. Hypotheses and questions are rendered from text
    # this function is not given, so they keep the wider digest-level check, and the asymmetry is
    # deliberate rather than an oversight.
    allowed = _nums(en)
    allowed_aux = allowed | set(dg["numbers"])
    for m in _nums(sr):
        if m not in allowed:
            reasons.append(f"number not in the original: {m}")
    if set(re.findall(r"\[(F\d+)\]", sr)) != set(re.findall(r"\[(F\d+)\]", en)):
        reasons.append("citations differ from the original")
    if not SR_WORDS.search(" " + sr.lower() + " "):
        reasons.append("not Serbian")
    foreign = sorted({m.group(0).lower() for m in FOREIGN_SLAVIC.finditer(sr)})
    if foreign:
        reasons.append("another Slavic standard, not Serbian: " + ", ".join(foreign[:4]))
    if EN_WORDS.search(" " + sr.lower() + " ") and len(EN_WORDS.findall(" " + sr.lower() + " ")) >= 3:
        reasons.append("English words in the rendering")
    hits = ijekavian_hits(sr)
    if hits:
        reasons.append("ijekavian, not ekavica: " + ", ".join(hits[:4]))
    if sr.lower() == en.strip().lower():
        reasons.append("identical to the English")
    for frag in PROMPT_FRAGMENTS + ["Prevedi ovu misao", "Odgovori isključivo"]:
        if frag in sr:
            reasons.append("echoed the prompt")
            break
    for label, items, n in (("hypothesis", hyp_sr or [], n_hyp), ("question", q_sr or [], n_q)):
        if n and len(items) != n:
            reasons.append(f"{label} count {len(items)} != {n}")
        for it in items:
            for m in _nums(it):
                if m not in allowed_aux:
                    reasons.append(f"number not in the original ({label}): {m}")
            h = ijekavian_hits(it)
            if h:
                reasons.append(f"ijekavian {label}: " + ", ".join(h[:3]))
            if len(it) >= 40 and not SR_WORDS.search(" " + it.lower() + " "):
                reasons.append(f"{label} not Serbian")
    return (not reasons), reasons


# ------------------------------------------------------------------ files
def publish(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=1).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=".mind-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.link(tmp, path)
    finally:
        os.unlink(tmp)


def _append(path: pathlib.Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _rows(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def notebook(entity: str) -> list[dict]:
    return _rows(OUT_DIR / "notebook" / f"{entity}.jsonl")


def register() -> dict:
    reg = json.loads(ORGANS.read_text(encoding="utf-8"))
    return next(o for o in reg["organs"] if o["id"] == ORGAN_ID)


def _pick(avail: list[str], pref: list[str] | None, allow_cloud: bool) -> str | None:
    return pick_model(avail, pref or [], allow_cloud=allow_cloud) if pref else None


def _chain(avail: list[str], pref: list[str] | None, allow_cloud: bool, limit: int = 3) -> list[str]:
    """EVERY model from the register's list that is present, in the register's order - not just the
    first. C-036: the body has 8 GB and the preferred thinker is 3.4 GB, so when free memory dips the
    daemon cannot load it, the call times out, and the step recorded silence and moved on. Measured on
    2026-09-10: from 00:38 to 01:22 every model step failed that way and the mind said nothing for 44
    minutes, while a 1 GB model that was already pulled sat unused. A smaller model is a worse thought;
    no thought is not a thought at all."""
    out: list[str] = []
    for pr in (pref or []):
        got = pick_model(avail, [pr], allow_cloud=allow_cloud)
        if got and got not in out:
            out.append(got)
    return out[:limit]


def chat_chain(chain: list[str], prompt: str, chat, rec: dict | None = None, **kw) -> tuple[dict | None, str | None, list[str]]:
    """Ask each model in turn until one answers. Returns (answer, the model that answered, what the
    others did). The model that actually spoke is what gets recorded - the record never credits a
    thought to a model that did not produce it."""
    tried: list[str] = []
    for m in chain:
        try:
            answer = chat(m, prompt, **kw)
        except Exception as e:  # noqa: BLE001
            tried.append(f"{m}: {type(e).__name__}")
            continue
        if rec is not None:
            rec["calls"] = rec.get("calls", 0) + 1
        return answer, m, tried
    return None, None, tried


# -------------------------------------------------------------------- run
def run(now: datetime | None = None, chat=ollama_chat, tags=ollama_tags, embed=ollama_embed, snap: dict | None = None,
        context: dict | None = None, orchestration: str | None = None) -> dict:
    now = now or utcnow()
    reg = register()
    snap = snap or json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    conv_id = stamp(now)
    n_prev = len(list((OUT_DIR / "receipts").glob("*.json"))) if (OUT_DIR / "receipts").exists() else 0
    orch = orchestration or ORCHESTRATIONS[n_prev % len(ORCHESTRATIONS)]
    rec = {"schema": "beops-organ-receipt/v1", "organ": ORGAN_ID, "organ_version": ORGAN_VERSION, "at": iso(now),
           "conversation": conv_id, "orchestration": orch, "facts": 0, "digest_sha256": None,
           "state": "nothing_to_do", "utterances": 0, "rejected": 0, "voiced": 0, "voice_refused": 0,
           "models": {}, "organelles": {}, "calls": 0, "reason": None}
    receipt_path = OUT_DIR / "receipts" / f"{conv_id}.json"
    if (OUT_DIR / "PAUSED").exists():
        rec["state"], rec["reason"] = "paused", (OUT_DIR / "PAUSED").read_text(encoding="utf-8", errors="replace")[:200] or "PAUSED file present"
        publish(receipt_path, rec)
        return rec
    dg0 = digest(snap, hours=int(reg.get("window_hours", 6)), now=now, context=context)
    if len(dg0["facts"]) < 2:
        rec["reason"] = "digest empty - nothing to think about"
        publish(receipt_path, rec)
        return rec
    avail = tags()
    if avail is None:
        rec["state"], rec["reason"] = "organ_silent", "model daemon not answering"
        publish(receipt_path, rec)
        return rec
    allow_cloud = bool(reg.get("allow_cloud", False))
    chains = {e["id"]: _chain(avail, reg.get("models_by_entity", {}).get(e["id"]) or reg["models_preferred"], allow_cloud) for e in ENTITIES}
    models = {k: (v[0] if v else None) for k, v in chains.items()}
    if not all(models.values()):
        rec["state"], rec["reason"] = "organ_silent", "no local model from the register for: " + ", ".join(k for k, v in models.items() if not v)
        publish(receipt_path, rec)
        return rec
    voice_model = _pick(avail, reg.get("voice_models"), allow_cloud)
    rank_model = _pick(avail, reg.get("ranker_models"), allow_cloud)
    embed_model = _pick(avail, reg.get("embed_models"), allow_cloud)
    rec["models"] = {**models, "voice": voice_model}
    rec["organelles"] = {"embed-linker": embed_model, "surprise-ranker": rank_model}

    # L1 - organelles annotate the digest
    links = []
    try:
        links = embed_linker(dg0, embed_model, embed=embed, threshold=float(reg.get('link_threshold', 0.70))) if embed_model else []
        rec["calls"] += 1 if embed_model and len(dg0.get("headlines", [])) >= 2 else 0
    except Exception as e:  # noqa: BLE001
        rec["organelles"]["embed-linker-error"] = f"{type(e).__name__}: {str(e)[:100]}"
    dg1 = annotate(dg0, links, {}, rank_model, embed_model)
    ratings = surprise_ranker(dg1, rank_model, chat) if rank_model else {}
    rec["calls"] += 1 if rank_model and any(f.get("kind") in ("connection", "link") for f in dg1["facts"]) else 0
    dg = annotate(dg0, links, ratings, rank_model, embed_model)
    digest_sha = hashlib.sha256(json.dumps(dg, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    rec["facts"], rec["digest_sha256"] = len(dg["facts"]), digest_sha
    rec["organelles"]["links"], rec["organelles"]["ratings"] = len(links), len(ratings)
    (OUT_DIR / "digests").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "digests" / f"{conv_id}.json").write_text(json.dumps(dg, ensure_ascii=False, indent=1), encoding="utf-8")
    out_path = OUT_DIR / (now.strftime("%Y-%m") + ".jsonl")
    accepted: list[dict] = []
    errors: list[str] = []

    # L2 - one utterance
    def speak(ent: dict, rnd: int, conversation: list[dict]) -> dict | None:
        prompt = prompt_for(ent, dg, notebook(ent["id"]), conversation)
        prompt_sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        answer, spoke, tried = chat_chain(chains[ent["id"]], prompt, chat, rec)
        if tried:
            errors.append(f"{ent['id']} r{rnd} fell back from " + "; ".join(tried))
        if answer is None:
            return None
        text, bound_by = ensure_citations(answer.get("text"), dg)
        answer["text"] = text
        ok, reasons = validate(answer, dg, previous=[a["en"] for a in accepted])
        claim = answer.get("claim") if ok and isinstance(answer.get("claim"), dict) and answer.get("claim") else None
        row = {"schema": "beops-derived-row/v1", "state": "thought" if ok else "rejected", "organ": ORGAN_ID,
               "organ_version": ORGAN_VERSION, "conversation": conv_id, "orchestration": orch, "round": rnd, "cites_bound_by": bound_by,
               "entity": ent["id"], "entity_sr": ent["sr"], "entity_en": ent["en"], "model": spoke,
               "prompt_sha256": prompt_sha, "digest_sha256": digest_sha, "ai_generated": True, "derivedTime": iso(now),
               "replies_to": [c["entity"] for c in conversation],
               "en": text, "sr": "", "sr_state": "pending", "voice_model": None,
               "cites": sorted(set(re.findall(r"\[(F\d+)\]", text))),
               "hypotheses": [h for h in (answer.get("hypotheses") or []) if isinstance(h, str)][:4],
               "questions": [q for q in (answer.get("questions") or []) if isinstance(q, str)][:4],
               "next_check": (answer.get("next_check") or "")[:300] if isinstance(answer.get("next_check"), str) else "",
               "claim": claim, "rejected_because": reasons or None}
        # L3 - the voice: Serbian ekavica rendering of an accepted thought, validated against the original
        if ok:
            voice(row, text, dg, voice_model, chat, rec)
        _append(out_path, row)
        _append(OUT_DIR / "notebook" / f"{ent['id']}.jsonl",
                {"at": iso(now), "conversation": conv_id, "round": rnd, "state": row["state"], "text": text, "sr": row["sr"],
                 "reason": "; ".join(reasons) if reasons else None, "claim": claim})
        if claim:
            _append(OUT_DIR / "claims.jsonl", {"at": iso(now), "conversation": conv_id, "orchestration": orch, "entity": ent["id"],
                                                "model": spoke, "claim": claim,
                                                "due": iso(now + timedelta(minutes=int(claim["within_minutes"]))), "outcome": None, "settled_at": None})
        if ok:
            accepted.append(row)
            return row
        rec["rejected"] += 1
        return None

    if orch == "council":
        for ent in ENTITIES:
            speak(ent, 1, [])
        r1 = list(accepted)
        for ent in ENTITIES:
            speak(ent, 2, [c for c in r1 if c["entity"] != ent["id"]])
    else:   # relay: Observer -> Skeptic answers -> Connector answers both -> Observer closes
        o = speak(ENT["observer"], 1, [])
        s = speak(ENT["skeptic"], 2, [o] if o else [])
        c = speak(ENT["connector"], 3, [x for x in (o, s) if x])
        speak(ENT["observer"], 4, [x for x in (s, c) if x])
    rec["utterances"] = len(accepted)
    rec["state"] = "derived" if accepted else ("organ_failed" if errors else "rejected")
    rec["reason"] = "; ".join(errors) if errors else None
    rec["output"] = str(out_path)
    publish(receipt_path, rec)
    return rec


# ------------------------------------------------------------------ the drip
STEPS = ("linker", "observer", "ranker", "skeptic", "connector", "score")
CONTEXT = OUT_DIR / "context.json"


def _context() -> dict:
    if CONTEXT.exists():
        try:
            return json.loads(CONTEXT.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"schema": "beops-mind-context/v1", "step": 0, "cycle": 0, "links": [], "ratings": {}, "rank_model": None,
            "embed_model": None, "conversation": [], "updated": None}


def _save_context(ctx: dict, now: datetime) -> None:
    ctx["updated"] = iso(now)
    tmp = CONTEXT.with_suffix(".tmp")
    CONTEXT.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(ctx, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, CONTEXT)


def step(now: datetime | None = None, chat=ollama_chat, tags=ollama_tags, embed=ollama_embed, snap: dict | None = None,
         context: dict | None = None) -> dict:
    """One drop of the endless conversation. State lives in context.json; every step rebuilds the digest
    from the newest snapshot, so new receptions reach the entities within minutes."""
    now = now or utcnow()
    reg = register()
    ctx = _context()
    name = STEPS[ctx["step"] % len(STEPS)]
    cycle_id = f"drip-{ctx['cycle']:05d}"
    rec = {"schema": "beops-organ-receipt/v1", "organ": ORGAN_ID, "organ_version": ORGAN_VERSION, "at": iso(now), "mode": "drip",
           "step": ctx["step"], "step_name": name, "conversation": cycle_id, "state": "nothing_to_do", "calls": 0, "reason": None}
    receipt_path = OUT_DIR / "receipts" / f"{stamp(now)}-{name}.json"
    if (OUT_DIR / "PAUSED").exists():
        rec["state"], rec["reason"] = "paused", (OUT_DIR / "PAUSED").read_text(encoding="utf-8", errors="replace")[:200] or "PAUSED file present"
        publish(receipt_path, rec)
        return rec
    snap = snap or json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if name == "score":
        res = score(now=now, snap=snap)
        rec["state"], rec["settled"] = "derived", res["settled_now"]
        ctx["step"] += 1
        ctx["cycle"] += 1
        _save_context(ctx, now)
        publish(receipt_path, rec)
        return rec
    dg0 = digest(snap, hours=int(reg.get("window_hours", 6)), now=now, context=context)
    avail = tags()
    if avail is None:
        rec["state"], rec["reason"] = "organ_silent", "model daemon not answering"
        ctx["step"] += 1
        _save_context(ctx, now)
        publish(receipt_path, rec)
        return rec
    allow_cloud = bool(reg.get("allow_cloud", False))
    out_path = OUT_DIR / (now.strftime("%Y-%m") + ".jsonl")
    if name == "linker":
        embed_model = _pick(avail, reg.get("embed_models"), allow_cloud)
        rec["model"] = embed_model
        if not embed_model:
            rec["state"], rec["reason"] = "organ_silent", "no embedding model from the register is present"
        else:
            try:
                links = embed_linker(dg0, embed_model, embed=embed, threshold=float(reg.get('link_threshold', 0.70)))
                rec["calls"] = 1 if len(dg0.get("headlines", [])) >= 2 else 0
                ctx["links"], ctx["embed_model"] = links, embed_model
                rec["state"], rec["links"] = "derived", len(links)
                for L in links:
                    _append(out_path, {"schema": "beops-derived-row/v1", "state": "organelle", "organ": ORGAN_ID, "organ_version": ORGAN_VERSION,
                                       "conversation": cycle_id, "orchestration": "drip", "round": ctx["step"], "entity": "organelle",
                                       "entity_sr": "Organela", "entity_en": "Organelle", "organelle": "embed-linker", "model": embed_model,
                                       "ai_generated": True, "derivedTime": iso(now), "replies_to": [], "en": L["en"], "sr": L["sr"],
                                       "sr_state": "program", "similarity": L["similarity"], "cites": [], "hypotheses": [], "questions": [],
                                       "next_check": "", "claim": None, "rejected_because": None})
            except Exception as e:  # noqa: BLE001
                rec["state"], rec["reason"] = "organ_failed", f"{type(e).__name__}: {str(e)[:120]}"
    elif name == "ranker":
        rank_model = _pick(avail, reg.get("ranker_models"), allow_cloud)
        rec["model"] = rank_model
        dg1 = annotate(dg0, ctx.get("links") or [], {}, rank_model, ctx.get("embed_model"))
        if not rank_model:
            rec["state"], rec["reason"] = "organ_silent", "no ranker model from the register is present"
        elif not any(f.get("kind") in ("connection", "link") for f in dg1["facts"]):
            rec["reason"] = "nothing to rate"
        else:
            ratings = surprise_ranker(dg1, rank_model, chat)
            rec["calls"], rec["state"], rec["ratings"] = 1, "derived" if ratings else "rejected", len(ratings)
            ctx["ratings"], ctx["rank_model"] = ratings, rank_model
            if ratings:
                parts = ", ".join(f"{k} {v}/5" for k, v in sorted(ratings.items(), key=lambda x: -x[1]))
                _append(out_path, {"schema": "beops-derived-row/v1", "state": "organelle", "organ": ORGAN_ID, "organ_version": ORGAN_VERSION,
                                   "conversation": cycle_id, "orchestration": "drip", "round": ctx["step"], "entity": "organelle",
                                   "entity_sr": "Organela", "entity_en": "Organelle", "organelle": "surprise-ranker", "model": rank_model,
                                   "ai_generated": True, "derivedTime": iso(now), "replies_to": [],
                                   "en": f"A small model rated the connections by surprise: {parts}. An estimate, not a measurement.",
                                   "sr": f"Mali model je ocenio iznenađenje veza: {parts}. Procena, ne merenje.",
                                   "sr_state": "program", "cites": [], "hypotheses": [], "questions": [], "next_check": "", "claim": None,
                                   "rejected_because": None, "ratings": ratings})
    else:   # an entity speaks, answering the other entities' last accepted utterances of this and the previous cycle
        ent = ENT[name]
        chain = _chain(avail, reg.get("models_by_entity", {}).get(name) or reg["models_preferred"], allow_cloud)
        model = chain[0] if chain else None
        voice_model = _pick(avail, reg.get("voice_models"), allow_cloud)
        rec["model"] = model
        if not model:
            rec["state"], rec["reason"] = "organ_silent", f"no local model from the register for {name}"
        else:
            dg = annotate(dg0, ctx.get("links") or [], ctx.get("ratings") or {}, ctx.get("rank_model"), ctx.get("embed_model"))
            digest_sha = hashlib.sha256(json.dumps(dg, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
            (OUT_DIR / "digests").mkdir(parents=True, exist_ok=True)
            (OUT_DIR / "digests" / f"{stamp(now)}-{name}.json").write_text(json.dumps(dg, ensure_ascii=False, indent=1), encoding="utf-8")
            latest_by = {}
            for c in (ctx.get("conversation") or []):
                if c.get("entity") != name:
                    latest_by[c["entity"]] = c
            conversation = list(latest_by.values())
            # what changed in the world since this entity last spoke - the nudge away from restating
            seen = set(ctx.get("last_facts", {}).get(name) or [])
            fresh = [f for f in dg["facts"] if f["en"] not in seen and f["kind"] in ("reception", "spread", "connection", "link", "headlines", "silence", "context")]
            if seen and fresh:
                dg = {**dg, "facts": dg["facts"] + [{"id": f"F{len(dg['facts']) + 1}", "kind": "fresh",
                      "sr": "Novo otkad si poslednji put govorio: " + "; ".join(f["id"] for f in fresh[:8]) + ".",
                      "en": "NEW since you last spoke (speak about these, not about what was already said): " + ", ".join(f["id"] for f in fresh[:8]) + "."}]}
            previous = [c["en"] for c in (ctx.get("conversation") or [])]
            prompt = prompt_for(ent, dg, notebook(name), conversation)
            prompt_sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            answer, model, tried = chat_chain(chain, prompt, chat, rec)
            if tried:
                rec["fell_back_from"] = tried
            if answer is None:
                rec["state"], rec["reason"] = "organ_failed", "; ".join(tried)[:160] or "no model answered"
            else:
                rec["model"] = model
            if answer is not None:
                text, bound_by = ensure_citations(answer.get("text"), dg)
                answer["text"] = text
                ok, reasons = validate(answer, dg, previous=previous)
                claim = answer.get("claim") if ok and isinstance(answer.get("claim"), dict) and answer.get("claim") else None
                ctx.setdefault("last_facts", {})[name] = [f["en"] for f in dg["facts"] if f["kind"] != "fresh"]
                row = {"schema": "beops-derived-row/v1", "state": "thought" if ok else "rejected", "organ": ORGAN_ID,
                       "organ_version": ORGAN_VERSION, "conversation": cycle_id, "orchestration": "drip", "round": ctx["step"], "cites_bound_by": bound_by,
                       "entity": name, "entity_sr": ent["sr"], "entity_en": ent["en"], "model": model,
                       "prompt_sha256": prompt_sha, "digest_sha256": digest_sha, "ai_generated": True, "derivedTime": iso(now),
                       "replies_to": [c["entity"] for c in conversation], "en": text, "sr": "", "sr_state": "pending", "voice_model": None,
                       "cites": sorted(set(re.findall(r"\[(F\d+)\]", text))),
                       "hypotheses": [h for h in (answer.get("hypotheses") or []) if isinstance(h, str)][:4],
                       "questions": [q for q in (answer.get("questions") or []) if isinstance(q, str)][:4],
                       "next_check": (answer.get("next_check") or "")[:300] if isinstance(answer.get("next_check"), str) else "",
                       "claim": claim, "rejected_because": reasons or None}
                if ok:
                    voice(row, text, dg, voice_model, chat, rec)
                _append(out_path, row)
                _append(OUT_DIR / "notebook" / f"{name}.jsonl", {"at": iso(now), "conversation": cycle_id, "round": ctx["step"], "state": row["state"],
                                                                 "text": text, "sr": row["sr"], "reason": "; ".join(reasons) if reasons else None, "claim": claim})
                if claim:
                    _append(OUT_DIR / "claims.jsonl", {"at": iso(now), "conversation": cycle_id, "orchestration": "drip", "entity": name, "model": model,
                                                        "claim": claim, "due": iso(now + timedelta(minutes=int(claim["within_minutes"]))), "outcome": None, "settled_at": None})
                rec["state"] = "derived" if ok else "rejected"
                rec["reason"] = None if ok else "; ".join(reasons)[:200]
                rec["sr_state"] = row["sr_state"]
                if ok:
                    ctx["conversation"] = ((ctx.get("conversation") or []) + [{"entity": name, "en": text, "at": iso(now)}])[-6:]
    ctx["step"] += 1
    _save_context(ctx, now)
    publish(receipt_path, rec)
    return rec


# ------------------------------------------------------------------ score
def score(now: datetime | None = None, snap: dict | None = None) -> dict:
    """Settle every claim whose deadline has passed, against the snapshot as it is now."""
    now = now or utcnow()
    snap = snap or json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    path = OUT_DIR / "claims.jsonl"
    rows = _rows(path)
    settled = 0
    by_sid = {s["sid"]: s for s in snap.get("sources", [])}
    for r in rows:
        if r.get("outcome") is not None:
            continue
        due, made = _p(r.get("due")), _p(r.get("at"))
        if not due or due > now:
            continue
        c = r["claim"]
        src = by_sid.get(c.get("sid"))
        outcome = "unverifiable"
        if src:
            pts = [p for d in src.get("datastreams", []) for p in d.get("points", [])]
            if c["kind"] == "reception":
                rx = [_p(p.get("rx")) for p in pts if p.get("rx")]
                outcome = "true" if any(made < t <= due for t in rx if t) else "false"
            elif c["kind"] == "spread":
                later = sorted({p.get("t") for d in src.get("datastreams", []) if d.get("parameter") == c.get("parameter")
                                for p in d.get("points", []) if p.get("t") and (_p(p.get("rx")) or made) > made})
                if later:
                    h0 = later[0]
                    vals = [p["v"] for d in src.get("datastreams", []) if d.get("parameter") == c.get("parameter")
                            for p in d.get("points", []) if p.get("t") == h0 and isinstance(p.get("v"), (int, float))]
                    if vals:
                        outcome = "true" if c["lo"] <= max(vals) <= c["hi"] else "false"
                        r["observed_max"], r["observed_hour"] = max(vals), h0
        r["outcome"], r["settled_at"] = outcome, iso(now)
        settled += 1
        _append(OUT_DIR / "notebook" / f"{r['entity']}.jsonl",
                {"at": iso(now), "conversation": r["conversation"], "state": "claim_settled", "text": f"claim {json.dumps(c, ensure_ascii=False)}",
                 "claim_outcome": outcome, "reason": None})
    if settled:
        tmp = path.with_suffix(".tmp")
        tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        os.replace(tmp, path)
    return {"settled_now": settled, "scoreboard": scoreboard(rows)}


def scoreboard(rows: list[dict] | None = None) -> dict:
    rows = rows if rows is not None else _rows(OUT_DIR / "claims.jsonl")
    utter = [r for mf in sorted(OUT_DIR.glob("*.jsonl")) if OUT_DIR.exists() and mf.name != "claims.jsonl" for r in _rows(mf)]
    board = {}
    for ent in ENTITIES:
        mine = [r for r in rows if r.get("entity") == ent["id"]]
        u = [r for r in utter if r.get("entity") == ent["id"]]
        board[ent["id"]] = {"name_sr": ent["sr"], "name_en": ent["en"],
                            "utterances": len(u), "accepted": sum(1 for r in u if r.get("state") == "thought"),
                            "rejected": sum(1 for r in u if r.get("state") == "rejected"),
                            "retracted": sum(1 for r in u if r.get("state") == "retracted"),
                            "voiced": sum(1 for r in u if r.get("sr_state") == "voiced"),
                            "drip": sum(1 for r in u if r.get("orchestration") == "drip" and r.get("state") == "thought"),
                            "claims": len(mine), "true": sum(1 for r in mine if r.get("outcome") == "true"),
                            "false": sum(1 for r in mine if r.get("outcome") == "false"),
                            "open": sum(1 for r in mine if r.get("outcome") is None),
                            "unverifiable": sum(1 for r in mine if r.get("outcome") == "unverifiable")}
    by_orch = {}
    for o in ORCHESTRATIONS:
        u = [r for r in utter if r.get("orchestration") == o and r.get("state") in ("thought", "rejected")]
        by_orch[o] = {"utterances": len(u), "accepted": sum(1 for r in u if r["state"] == "thought"),
                      "rejected": sum(1 for r in u if r["state"] == "rejected")}
    board["by_orchestration"] = by_orch
    board["organelle"] = {"drops": sum(1 for r in utter if r.get("state") == "organelle"),
                          "links": sum(1 for r in utter if r.get("state") == "organelle" and r.get("organelle") == "embed-linker"),
                          "ratings": sum(1 for r in utter if r.get("state") == "organelle" and r.get("organelle") == "surprise-ranker")}
    return board


def retract(conversation: str, entity: str, rnd: int, reason: str, now: datetime | None = None) -> dict:
    """Append a retraction for an utterance that should not have passed. The original row stays; the
    export skips any (conversation, entity, round) that has a retraction; its claim is voided."""
    now = now or utcnow()
    row = {"schema": "beops-derived-row/v1", "state": "retracted", "organ": ORGAN_ID, "organ_version": ORGAN_VERSION,
           "conversation": conversation, "entity": entity, "round": int(rnd), "retracts": True, "reason": reason,
           "derivedTime": iso(now), "ai_generated": False}
    _append(OUT_DIR / (now.strftime("%Y-%m") + ".jsonl"), row)
    _append(OUT_DIR / "notebook" / f"{entity}.jsonl", {"at": iso(now), "conversation": conversation, "round": int(rnd),
                                                        "state": "retracted", "text": "", "reason": reason})
    cpath = OUT_DIR / "claims.jsonl"
    rows = _rows(cpath)
    changed = False
    for r in rows:
        if r.get("conversation") == conversation and r.get("entity") == entity and r.get("outcome") is None:
            r["outcome"], r["settled_at"] = "retracted", iso(now)
            changed = True
    if changed:
        tmp = cpath.with_suffix(".tmp")
        tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        os.replace(tmp, cpath)
    return row


def status() -> dict:
    receipts = sorted(OUT_DIR.glob("receipts/*.json")) if OUT_DIR.exists() else []
    last = json.loads(receipts[-1].read_text(encoding="utf-8")) if receipts else None
    avail = ollama_tags()
    reg = register()
    ac = bool(reg.get("allow_cloud", False))
    return {"organ": ORGAN_ID, "version": ORGAN_VERSION, "runs": len(receipts), "model_daemon": "up" if avail is not None else "down",
            "models_present": avail, "next_orchestration": ORCHESTRATIONS[len(receipts) % len(ORCHESTRATIONS)],
            "models": {**{e["id"]: _pick(avail or [], reg.get("models_by_entity", {}).get(e["id"]) or reg["models_preferred"], ac) for e in ENTITIES},
                       "voice": _pick(avail or [], reg.get("voice_models"), ac), "surprise-ranker": _pick(avail or [], reg.get("ranker_models"), ac),
                       "embed-linker": _pick(avail or [], reg.get("embed_models"), ac)},
            "scoreboard": scoreboard(), "last_run": last}


def check() -> dict:
    reg = register()
    dg = {"as_of": "x", "window_hours": 6, "numbers": ["32", "485", "3", "10", "40", "90", "1"],
          "facts": [{"id": "F1", "sr": "a", "en": "a"}, {"id": "F2", "sr": "b", "en": "b"}]}
    ok1, r1 = validate({"text": "Thirty-two stations [F1] reported 485 values while one feed is silent [F2].", "cites": ["F1"],
                        "hypotheses": ["maybe the night lowers it"], "questions": [], "next_check": "",
                        "claim": {"kind": "spread", "sid": "S146", "parameter": "PM10", "lo": 10, "hi": 40, "within_minutes": 90}}, dg)
    ok2, r2 = validate({"text": "Stations [F1] reported 999 values and will rise. You notice.", "cites": ["F9"], "hypotheses": ["it will rain"],
                        "questions": [], "next_check": "", "claim": {"kind": "weather"}}, dg)
    vok, vr = validate_voice("Trideset dve stanice [F1] su javile 485 vrednosti dok jedan izvor ćuti [F2].", "Thirty-two stations [F1] reported 485 values while one feed is silent [F2].", dg)
    vok2, vr2 = validate_voice("možeš da se to je ne dovolno [F1] 777", "Thirty-two stations [F1] reported 485 values while one feed is silent [F2].", dg)
    return {"register": {k: reg.get(k) for k in ("id", "version", "allow_cloud", "models_by_entity", "voice_models", "ranker_models", "embed_models", "editor_of_record")},
            "entities": [e["id"] for e in ENTITIES], "orchestrations": ORCHESTRATIONS,
            "validator_accepts_grounded": ok1, "accept_reasons": r1, "validator_refuses_ungrounded": (not ok2), "refusal_reasons": r2,
            "voice_accepts_faithful": vok, "voice_reasons": vr, "voice_refuses_salad": (not vok2), "voice_refusal_reasons": vr2}


def voice_bench(model_names: list[str], n: int = 8) -> dict:
    """Render the last n accepted English thoughts with each candidate voice model and run the same validator
    the organ runs. Writes data/live/derived/mind/voice_bench/<time>.json and returns it. The reading of the
    Serbian itself (word salad or not) is a person's job: the file is meant to be read, not only counted."""
    rows = []
    for f in sorted(OUT_DIR.glob("*.jsonl")):
        if f.name[:4].isdigit():
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("state") == "thought" and r.get("en"):
                    rows.append(r)
    rows = rows[-n:]
    now = datetime.now(timezone.utc)
    out = {"schema": "beops-voice-bench/v1", "at": iso(now), "organ_version": ORGAN_VERSION, "thoughts": len(rows), "models": {}}
    d = OUT_DIR / "voice_bench"
    d.mkdir(parents=True, exist_ok=True)
    log = d / (now.strftime("%Y%m%dT%H%M%SZ") + ".jsonl")   # one line per rendering, written as it happens (a CPU bench is slow)
    for m in model_names:
        res = {"voiced": 0, "refused": 0, "failed": 0, "seconds": 0.0, "renderings": []}
        for r in rows:
            dg = {"numbers": sorted(_nums(r["en"]) | {x for h in (r.get("hypotheses") or []) for x in _nums(h)})}
            row = {"hypotheses": r.get("hypotheses") or [], "questions": r.get("questions") or []}
            t0 = time.time()
            voice(row, r["en"], dg, m, ollama_chat)
            dt = time.time() - t0
            res["seconds"] += dt
            state = row.get("sr_state", "")
            res["voiced" if state == "voiced" else "failed" if state.startswith("failed") else "refused"] += 1
            rend = {"model": m, "en": r["en"][:400], "sr": row.get("sr") or "", "hypotheses_sr": row.get("hypotheses_sr"),
                    "questions_sr": row.get("questions_sr"), "state": state, "attempts": row.get("voice_attempts"), "seconds": round(dt, 1)}
            res["renderings"].append(rend)
            _append(log, rend)
            print(f"[{m}] {round(dt)} s {state[:50]} | {(row.get('sr') or '')[:160]}", flush=True)
        res["seconds"] = round(res["seconds"], 1)
        out["models"][m] = res
    (d / (now.strftime("%Y%m%dT%H%M%SZ") + ".json")).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "run":
        print(json.dumps(run(), ensure_ascii=False, indent=1))
    elif cmd == "step":
        print(json.dumps(step(), ensure_ascii=False, indent=1))
    elif cmd == "score":
        print(json.dumps(score(), ensure_ascii=False, indent=1))
    elif cmd == "digest":
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        dg = digest(snap, hours=int(register().get("window_hours", 6)))
        for f in dg["facts"]:
            print(f["id"], f["kind"], "|", f["en"])
        print("numbers:", " ".join(dg["numbers"]))
        print("headlines in window:", len(dg["headlines"]))
    elif cmd == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
    elif cmd == "check":
        print(json.dumps(check(), ensure_ascii=False, indent=1))
    elif cmd == "voice-bench" and len(sys.argv) >= 3:
        args = sys.argv[2:]
        n = int(args[args.index("--n") + 1]) if "--n" in args else 8
        names = [a for i, a in enumerate(args) if a != "--n" and (i == 0 or args[i - 1] != "--n")]
        out = voice_bench(names, n)
        for m, res in out["models"].items():
            print(f"== {m}: voiced {res['voiced']} / refused {res['refused']} / failed {res['failed']} in {res['seconds']} s")
            for r in res["renderings"]:
                print(f"  [{r['state'][:40]}] {r['sr'][:300] if r['sr'] else '(none)'}")
                if r.get("hypotheses_sr"):
                    print("     H:", " | ".join(r["hypotheses_sr"])[:300])
    elif cmd == "retract" and len(sys.argv) >= 6:
        print(json.dumps(retract(sys.argv[2], sys.argv[3], int(sys.argv[4]), " ".join(sys.argv[5:])), ensure_ascii=False))
    else:
        raise SystemExit(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
