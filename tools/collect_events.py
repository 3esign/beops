#!/usr/bin/env python3
"""
collect_events.py - explicit official repertoire facts and separate untimed headline signals.

Only schedule metadata is retained: title, URL, explicit start and venue. Descriptions and
images are not republished; this code makes no blanket claim about their copyright status.
"""
from __future__ import annotations

import json
import hashlib
from html.parser import HTMLParser
from urllib.parse import urlsplit
from contracts import atomic_json, belgrade_local, exclusive
from event_repertoires import SOURCES, parse_official_programme
import pathlib
import re
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
DOCS = ROOT / "docs"

ZONES = {
    "Novi Beograd": ["novi beograd", "novom beogradu", "ušk", "usce", "arena", "bežanij", "omladinskih brigada", "blok "],
    "Stari grad": ["stari grad", "starom gradu", "kalemegdan", "trg republike", "knez mihail", "dorćol", "dorcol", "terazij"],
    "Savski venac": ["savski venac", "savskom vencu", "beograd na vodi", "kneza miloša", "mostar", "prokop", "gazel"],
    "Vračar": ["vračar", "vracaru", "slavij", "hram svetog save", "južni bulevar"],
    "Palilula": ["palilul", "borč", "borca", "krnjač", "krnjaca", "tašmajdan", "tasmajdan", "pančevački most"],
    "Zvezdara": ["zvezdar", "mirijev", "bulevar kralja aleksandra", "zeleno brdo", "cvetkova pijaca"],
    "Voždovac": ["voždov", "vozdovac", "autokomand", "jajinc", "banjic", "trošarin", "kumodraž"],
    "Čukarica": ["čukaric", "cukarica", "banovo brdo", "ada ciganlija", "žarkov", "železnik", "požešk"],
    "Zemun": ["zemun", "zemunsk", "kej oslobođenja", "gardoš", "batajnic"],
    "Rakovica": ["rakovic", "vidikovac", "kneževac", "labudovo brdo"],
    "Mostovi": ["brankov most", "gazel", "pančevački most", "most na adi", "pupinov most"]
}

CATEGORIES = {
    "saobracaj_radovi": [
        "radovi", "zatvara se", "zatvorena", "izmena linij", "rebalans linij", "gsp", "staje saobraćaj",
        "obustava saobraćaja", "isključenje", "havarija", "raskrsnic", "presvlačenje asfalta", "rekonstrukcij"
    ],
    "kultura": [
        "koncert", "pozorišt", "predstava", "premijera", "izložba", "muzej", "kolarac", "dom omladine",
        "film", "bioskop", "književn", "tribina", "festival", "bitef", "bemus", "beogradsko leto"
    ],
    "sport": [
        "utakmica", "derbi", "maraton", "polumaraton", "trka", "liga šampiona", "evroliga",
        "arena", "pionir", "stadion", "partizan", "crvena zvezda", "kup"
    ],
    "upozorenje": [
        "upozorenje", "oluja", "jak vetar", "obilne padavine", "topli talas", "hladni talas",
        "crveni meteoalarm", "narandžasti meteoalarm"
    ]
}

OFFICIAL_SOURCES = {"S208", "S206", "S15", "S12", "S01"}

REPERTOIRE_URL = "https://www.kolarac.rs/koncerti/"
REPERTOIRE_SID = "S225"
CACHE = ROOT / "data/live/derived/events/repertoire.json"


class RepertoireLinks(HTMLParser):
    """Only rendered entry-title anchors; publication metadata is not an event clock."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_title, self.url, self.parts, self.rows = False, None, [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('h2', 'h3') and 'entry-title' in attrs.get('class', '').split():
            self.in_title = True
        if self.in_title and tag == 'a':
            self.url, self.parts = attrs.get('href'), []
        elif self.url and tag == 'br':
            self.parts.append(' | ')

    def handle_data(self, value):
        if self.url:
            self.parts.append(value)

    def handle_endtag(self, tag):
        if tag == 'a' and self.url:
            self.rows.append((self.url, ' '.join(''.join(self.parts).split())))
            self.url = None
        if tag in ('h2', 'h3'):
            self.in_title = False


def parse_repertoire(body, received_at, raw_sha256):
    parser = RepertoireLinks()
    parser.feed(body.decode('utf-8'))
    events, seen = [], set()
    pattern = re.compile(r'(?<!\d)(\d{1,2})\.\s*(\d{1,2})\.\s*(20\d{2})\.\s*[уu]\s*(\d{1,2})(?:[:.](\d{2}))?(?!\d)', re.I)
    for url, label in parser.rows:
        match, route = pattern.search(label), urlsplit(url)
        if not match or route.scheme != 'https' or route.netloc != 'www.kolarac.rs' or not route.path.startswith('/koncerti/') or url in seen:
            continue
        title = label[:match.start()].strip(' |')
        if not title:  # never invent a missing title from the URL slug
            continue
        try:
            day, month, year, hour, minute = match.groups()
            local = datetime(int(year), int(month), int(day), int(hour), int(minute or 0))
            start, offset = belgrade_local(local)
        except ValueError:
            continue
        if start is None:  # DST fold or gap is not guessed
            continue
        venue = label[match.end():].strip(' .|') or None
        seen.add(url)
        events.append({
            'id': 'EV-' + hashlib.sha256((url + start.isoformat()).encode()).hexdigest()[:16],
            'title': title, 'category': 'kultura', 'zone': None, 'location': venue,
            'source': 'Kolarac — zvanični repertoar', 'source_id': REPERTOIRE_SID,
            'url': url, 'is_official': True, 'verified': True,
            'verification_scope': 'explicit schedule facts in one official source; not independent corroboration or occurrence verification',
            'classification': 'official-repertoire', 'state': 'forecast', 'event_status': 'scheduled',
            'event_start': start.isoformat().replace('+00:00', 'Z'),
            'event_start_local': local.isoformat(timespec='minutes') + f'{offset:+03d}:00',
            'event_timezone': 'Europe/Belgrade', 'event_end': None, 'published': None,
            'provenance': {'url': REPERTOIRE_URL, 'received_at': received_at, 'raw_sha256': raw_sha256,
                           'source_label': label, 'parser': 'kolarac-entry-title/v2'},
            'limitation': 'One official schedule; end time, availability and actual occurrence are unknown.'
        })
    return sorted(events, key=lambda event: event['event_start'])


def parse_stamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None


def read_cache():
    try:
        return json.loads(CACHE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def refresh_source(source, cache, now):
    """Each official programme retains its own attempt, receipt and failure state."""
    import permission_policy
    import transport
    sid, url = source['source_id'], source['url']
    attempted = parse_stamp(cache.get('attempted_at'))
    cooldown = 6 * 3600 if cache.get('state') == 'available' else 1800
    if attempted and 0 <= (now - attempted).total_seconds() < cooldown:
        return cache
    attempted_at = now.isoformat()
    try:
        ledger = ROOT / 'research/08-provenance/LEDGER.jsonl'
        entries = permission_policy.latest(ledger)
        allowed, reason = permission_policy.authorize(sid, entries, ROOT, url, now)
        if not allowed and reason == 'permission capture expired or future dated':
            import legal_capture
            legal_capture.capture(sid, source['name'], [url], [],
                                  'Periodic permission recapture; factual schedule metadata only.', False)
            allowed, reason = permission_policy.authorize(sid, permission_policy.latest(ledger), ROOT, url, now)
        if not allowed:
            raise ValueError('permission: ' + reason)
        result = transport.fetch(url, timeout_s=20, max_bytes=512 * 1024)
        if result.get('status') != 200 or result.get('error') or not result.get('body'):
            raise ValueError('fetch: ' + str(result.get('error') or result.get('status')))
        raw = result['body']
        digest = hashlib.sha256(raw).hexdigest()
        parsed = ({'events': parse_repertoire(raw, attempted_at, digest), 'rejected': []}
                  if sid == REPERTOIRE_SID else parse_official_programme(raw, source, attempted_at, digest))
        events = parsed['events']
        if not events:
            raise ValueError('source returned no parseable dated repertoire entries')
        raw_path = ROOT / 'data/live/raw' / sid / (digest + '.html')
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        if raw_path.exists():
            if hashlib.sha256(raw_path.read_bytes()).hexdigest() != digest:
                raise ValueError('existing raw evidence hash mismatch')
        else:
            raw_path.write_bytes(raw)
        cache = {'schema': 'beops-repertoire-source/v1', 'source_id': sid, 'name': source['name'],
                 'url': url, 'attempted_at': attempted_at, 'received_at': attempted_at,
                 'state': 'available', 'raw_path': raw_path.relative_to(ROOT).as_posix(),
                 'raw_sha256': digest, 'permission_capture': reason,
                 'request_user_agent': result.get('request_user_agent'), 'events': events,
                 'parser_audit': {'accepted': len(events), 'rejected': parsed['rejected']}}
    except Exception as exc:
        cache = {**cache, 'source_id': sid, 'name': source['name'], 'url': url,
                 'attempted_at': attempted_at, 'state': 'unavailable', 'error': str(exc)[:240]}
    return cache


def source_caches(cache):
    """Backward-compatible migration: legacy S225 receipts keep their original age."""
    if isinstance(cache.get('sources'), list):
        return cache['sources']
    return [cache] if cache.get('source_id') == REPERTOIRE_SID else []


def refresh_repertoire(now=None):
    """Bounded collection runs in collect_tick, never implicitly during offline builds."""
    now = now or datetime.now(timezone.utc)
    previous = {entry['source_id']: entry for entry in source_caches(read_cache())}
    sources = [refresh_source(source, previous.get(source['source_id'], {}), now) for source in SOURCES]
    available = [source for source in sources if source.get('state') == 'available']
    cache = {'schema': 'beops-repertoire-cache/v2',
             'state': 'available' if len(available) == len(sources) else 'partial' if available else 'unavailable',
             'attempted_at': max((source.get('attempted_at') or '' for source in sources), default=None),
             'received_at': min((source['received_at'] for source in available), default=None),
             'sources': sources,
             'events': sorted([event for source in available for event in source.get('events', [])],
                              key=lambda event: event['event_start'])}
    with exclusive(ROOT / 'data/live/.write.lock'):
        atomic_json(CACHE, cache)
    return cache


def scheduled_events(cache, now=None):
    now = now or datetime.now(timezone.utc)
    if isinstance(cache.get('sources'), list):
        # A healthy source must never lend its fresh receipt to another failed source.
        return sorted([event for source in cache['sources'] for event in scheduled_events(source, now)],
                      key=lambda event: event['event_start'])
    received = parse_stamp(cache.get('received_at'))
    if cache.get('state') != 'available' or received is None or not 0 <= (now - received).total_seconds() <= 86400:
        return []
    result = []
    for event in cache.get('events', []):
        start = parse_stamp(event.get('event_start'))
        if event.get('verified') is True and event.get('state') == 'forecast' and event.get('event_status') == 'scheduled' and start and start >= now:
            result.append(event)
    return sorted(result, key=lambda event: event['event_start'])


def public_source_status(source, now):
    """Project cache age without changing the source's original receipt or health."""
    summary = {k: source.get(k) for k in ('source_id', 'name', 'url', 'state', 'received_at',
               'attempted_at', 'error', 'raw_sha256', 'permission_capture', 'parser_audit')}
    if not summary['name']:
        summary['name'] = next((spec['name'] for spec in SOURCES if spec['source_id'] == source.get('source_id')), source.get('source_id'))
    summary['collection_state'] = source.get('state')
    received = parse_stamp(source.get('received_at'))
    if source.get('state') == 'available':
        if received is None:
            summary.update(state='unavailable', error='Schedule receipt timestamp is missing or invalid.')
        elif received > now:
            summary.update(state='unavailable', error='Schedule receipt is future-dated.')
        elif (now - received).total_seconds() > 86400:
            summary.update(state='unavailable', error='Schedule receipt is older than 24 hours.')
    summary['scheduled_count'] = len(scheduled_events(source, now))
    return summary

def detect_zone(text: str) -> str:
    text_lower = text.lower()
    for zone, keywords in ZONES.items():
        for kw in keywords:
            if kw in text_lower:
                return zone
    return None

def detect_category(text: str) -> str:
    text_lower = text.lower()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in text_lower:
                return cat
    return "ostalo"

def extract_events_from_headlines(headlines_data: dict) -> list[dict]:
    rows = headlines_data.get("rows", [])
    events = []
    seen_titles = set()

    for r in rows:
        title = r.get("title", "").strip()
        if not title:
            continue

        cat = detect_category(title)
        if cat == "ostalo":
            continue

        # Normalizacija za deduplikaciju
        norm = re.sub(r"[^\w\s]", "", title.lower())
        key = norm
        if key in seen_titles:
            continue
        seen_titles.add(key)

        zone = detect_zone(title)
        sid = r.get("sid", "")
        is_official = sid in OFFICIAL_SOURCES

        events.append({
            "id": r.get("id", "")[:16],
            "title": title,
            "category": cat,
            "zone": zone,
            "published": r.get("published", ""),
            "source": r.get("source", ""),
            "source_id": sid,
            "url": r.get("link", ""),
            "is_official": is_official,
            "verified": False,
            "classification": "keyword-derived",
            "state": "untimed",
            "event_start": None,
            "event_end": None,
            "limitation": "Headline classification; publication time is not event time."
        })

    # Sortiranje: službena obaveštenja i najsvežiji termini prvo
    events.sort(key=lambda x: (1 if x["is_official"] else 0, str(x.get("published") or "")), reverse=True)
    return events[:50]

def build_events_dataset() -> dict:
    hl_path = PUBLIC / "headlines.json"
    data = {}
    if hl_path.exists():
        try:
            data = json.loads(hl_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    extracted = extract_events_from_headlines(data)
    now = datetime.now(timezone.utc)
    now_utc = now.isoformat()
    repertoire = read_cache()
    scheduled = scheduled_events(repertoire, now)
    source_statuses = [public_source_status(source, now) for source in source_caches(repertoire)]
    healthy = sum(source['state'] == 'available' for source in source_statuses)
    repertoire_state = ('available' if source_statuses and healthy == len(source_statuses)
                        else 'partial' if healthy else 'unavailable')

    out = {
        "schema": "beops-events/v1",
        "as_of": now_utc,
        "count": len(scheduled) + len(extracted),
        "scheduled_count": len(scheduled),
        "headline_count": len(extracted),
        "repertoire": {**{k: repertoire.get(k) for k in ("source_id", "url", "state", "received_at", "attempted_at", "error", "raw_sha256", "permission_capture")},
                       'state': repertoire_state, 'collection_state': repertoire.get('state'),
                       'sources': source_statuses},
        "note": "Each scheduled item is an explicit fact from one named official repertoire (maximum per-source receipt age 24h). Headline signals remain unverified and untimed. Multiple repertoires are not independent corroboration of the same event; no citywide coverage claim.",
        "events": scheduled + extracted
    }
    return out

def main():
    if "--refresh" in sys.argv:
        cache = refresh_repertoire()
        print(json.dumps({**{k: cache.get(k) for k in ('state', 'received_at', 'attempted_at', 'error')},
                          'sources': [{k: source.get(k) for k in ('source_id', 'state', 'received_at', 'error', 'parser_audit')} for source in source_caches(cache)]}, ensure_ascii=False))
        return 0 if cache.get('state') == 'available' else 1
    if "--test" in sys.argv:
        # Sanity test
        dummy = {
            "rows": [
                {
                    "id": "abc1",
                    "title": "Radovi na Gazeli: izmena saobraćaja u subotu",
                    "sid": "S208",
                    "source": "Beoinfo",
                    "link": "https://beograd.rs/vest1",
                    "published": "2026-09-25T12:00:00Z"
                },
                {
                    "id": "abc2",
                    "title": "Koncert Beogradske filharmonije na Kolarcu",
                    "sid": "S195",
                    "source": "RTS",
                    "link": "https://rts.rs/vest2",
                    "published": "2026-09-25T11:00:00Z"
                }
            ]
        }
        res = extract_events_from_headlines(dummy)
        assert len(res) == 2, f"Expected 2 events, got {len(res)}"
        assert res[0]["category"] == "saobracaj_radovi"
        assert res[0]["is_official"] is True
        assert res[1]["category"] == "kultura"
        print("collect_events.py self-test passed.")
        return 0

    dataset = build_events_dataset()
    PUBLIC.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    text = json.dumps(dataset, ensure_ascii=False, indent=1)
    (PUBLIC / "events.json").write_text(text, encoding="utf-8")
    (DOCS / "events.json").write_text(text, encoding="utf-8")
    print(f"wrote {PUBLIC/'events.json'} and {DOCS/'events.json'} ({len(dataset['events'])} events)")
    return 0

if __name__ == "__main__":
    if "--refresh" in sys.argv:
        from resource_meter import run_main
        sys.exit(run_main(ROOT, "calendar", main))
    sys.exit(main())
