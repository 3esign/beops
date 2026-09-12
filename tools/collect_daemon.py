#!/usr/bin/env python3
"""
collect_daemon.py - the first thing in BEOPS that runs without a person.

One tick = for every configured source that is due, one bounded request,
one immutable receipt, and rows appended in SensorThings vocabulary. It is
called by the Windows scheduled task ``Beops_Collect`` every five minutes
(tools/collect_tick.bat); it can also be run by hand:

    python -B tools/collect_daemon.py tick            one pass over due sources
    python -B tools/collect_daemon.py status          coverage of the last 24 h
    python -B tools/collect_daemon.py report          write research/observations/live/REPORT_<day>.md
    python -B tools/collect_daemon.py check           gate + config sanity, no network
    python -B tools/collect_daemon.py export          public/live-snapshot.json for the UI studies (copies rows, adds nothing)

Rules this file enforces (from CONTRIBUTING.md and 08-provenance/README.md):

  * No source is fetched without a permission capture in LEDGER.jsonl whose
    newest verdict is allowed_for_us == True and capture_ok. An unknown is
    never a permission. (Same gate as research/collect_permitted.py.)
  * Received is not measured. Every row carries phenomenonTime (the source's
    own measurement time, or null with phenomenonTimeUnknown=true and the
    reason), resultTime (when the source says it produced the result, or
    null) and receivedTime (our clock, always). The three never collapse.
  * Missing is not zero. A row whose value cannot be read gets
    result=null and resultQuality="missing"; a tick that fails leaves a
    receipt with state "failed" and never a row with a number.
  * Receipts are never overwritten: claim file first, then a receipt published
    by hard link (same pattern as research/observe_10k.py). A crash between
    the two leaves a visible claim and a gap, never a retry of the same slot.
  * 403 or 429 pauses the source until a person clears the pause file.
  * Transport uses verified TLS and the shared incognito header provider.
    Redirects require their own permission route; response bodies are bounded.
  * Byte caps per source. The SEPA observations endpoint returns the whole
    30-day bundle (140 MB) when asked without ``from``; the collector always
    asks for a window and stops at the cap.

Data lives outside git in data/live/ (see .gitignore): raw responses gzipped
under data/live/raw/<sid>/<UTC>.gz, receipts under data/live/receipts/<sid>/,
rows appended to data/live/rows/<sid>/<YYYY-MM>.jsonl. The daily report is
the only thing that goes back into the repository.
"""
from __future__ import annotations

import argparse
from contracts import json_rows, json_object, serialized, atomic_json, observation_rows
import gzip
import hashlib
from contracts import finite, belgrade_local, belgrade_offset, content_id, exclusive
import permission_policy
import source_policy
import transport
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "research"
LEDGER = RESEARCH / "08-provenance" / "LEDGER.jsonl"
CONFIG = RESEARCH / "COLLECTORS.json"
LIVE = ROOT / "data" / "live"
UA = "Beops-Research-Collect/1.0 (urban observatory research; identifies honestly)"
SCHEMA_RECEIPT = "beops-live-receipt/v1"
SCHEMA_ROW = "beops-observation-row/v1"

sys.path.insert(0, str(RESEARCH))


# --------------------------------------------------------------------- time
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def stamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def iso(dt: datetime | None) -> str | None:
    return None if dt is None else dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# --------------------------------------------------------------------- gate
def gate() -> dict:
    return permission_policy.latest(LEDGER)


def may_collect(sid: str, latest: dict, url: str | None = None, now=None) -> tuple[bool, str]:
    return permission_policy.authorize(sid, latest, ROOT, url, now)


def fetch(url: str, timeout_s: int, max_bytes: int) -> dict:
    return transport.fetch(url, timeout_s, max_bytes)


def parse_sepa_hvd(body: bytes, received: datetime, src: dict) -> list[dict]:
    """SEPA HVD /api/v1/observations: hourly means, phenomenonTime is an interval."""
    doc = json.loads(body.decode("utf-8"))
    keep = src.get("station_ids")  # Belgrade scope: the API is national; the registry rule is Belgrade only
    names = src.get("station_names") or {}
    coords = src.get("station_coords") or {}
    rows = []
    for rec in doc.get("data", []):
        st = str(rec.get("station_id"))
        if keep and st not in keep:
            continue
        val = rec.get("value")
        present = finite(val)
        rows.append({
            "schema": SCHEMA_ROW, "sid": src["sid"],
            "datastream": f"{st}|{rec.get('parameter_code')}",
            "station_id": st, "station_name": names.get(st), "parameter": rec.get("parameter_code"),
            "lat": (coords.get(st) or [None, None])[0], "lon": (coords.get(st) or [None, None])[1],
            "result": val if present else None, "unit": rec.get("unit"),
            "phenomenonTime": {"start": rec.get("time_start_utc"), "end": rec.get("time_end_utc")},
            "phenomenonTimeUnknown": False,
            "resultTime": rec.get("published_at_utc"),
            "receivedTime": iso(received),
            "resultQuality": ("source-preliminary" if present else "missing") if rec.get("data_status") == "preliminary"
                             else ("unvalidated" if present else "missing"),
            "aggregation": rec.get("aggregation_type"),
            "source_status": rec.get("data_status"),
        })
    note = src.get("source_clock_note")
    if note and note.get("offset_seconds"):
        off = int(note["offset_seconds"])
        for r in rows:
            r["sourceClockNote"] = note["text"]
            if note.get('valid_until') and iso(received) >= note['valid_until']:
                r['sourceClockUnresolved'] = True
                r['sourceClockRule'] = note.get('rule_id')
                continue
            pt = r["phenomenonTime"]
            r["phenomenonTimeCorrected"] = {"start": _shift(pt.get("start"), -off), "end": _shift(pt.get("end"), -off),
                                            "state": "estimated", "why": note["text"]}
            r["resultTimeCorrected"] = _shift(r["resultTime"], -off)
    return rows


def _shift(s: str | None, seconds: int) -> str | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return iso(dt + timedelta(seconds=seconds))


def parse_sensor_community(body: bytes, received: datetime, src: dict) -> list[dict]:
    """Sensor.Community /airrohr/v1/filter: latest 5-minute window per sensor; timestamp is UTC."""
    doc = json.loads(body.decode("utf-8"))
    rows = []
    for rec in doc:
        ts = rec.get("timestamp")
        ptime = None
        if isinstance(ts, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", ts):
            ptime = ts.replace(" ", "T") + "Z"
        sensor = rec.get("sensor") or {}
        loc = rec.get("location") or {}
        for v in rec.get("sensordatavalues", []):
            raw = v.get("value")
            try:
                num = float(raw)
                present = num == num
            except (TypeError, ValueError):
                num, present = None, False
            rows.append({
                "schema": SCHEMA_ROW, "sid": src["sid"],
                "datastream": f"{sensor.get('id')}|{v.get('value_type')}",
                "station_id": str(sensor.get("id")), "parameter": v.get("value_type"),
                "sensor_type": (sensor.get("sensor_type") or {}).get("name"),
                "location_id": loc.get("id"), "indoor": loc.get("indoor"),
                "lat": _f(loc.get("latitude")), "lon": _f(loc.get("longitude")),
                "result": num if present else None, "unit": _SC_UNITS.get(v.get("value_type")),
                "phenomenonTime": ptime, "phenomenonTimeUnknown": ptime is None,
                "phenomenonTimeReason": None if ptime else "source timestamp absent or unparseable",
                "resultTime": None, "receivedTime": iso(received),
                "resultQuality": "unvalidated" if present else "missing",
            })
    return rows


_SC_UNITS = {"P1": "ug.m-3", "P2": "ug.m-3", "P0": "ug.m-3", "temperature": "Cel",
             "humidity": "%", "pressure": "Pa", "pressure_at_sealevel": "Pa", "noise_LAeq": "dB(A)"}


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def parse_parking(body: bytes, received: datetime, src: dict) -> list[dict]:
    """Parking servis page: displayed free spaces per lot; the source publishes NO measurement time."""
    from probe_multidomain import Page  # research/, flat by design (see research/README.md)
    page = Page()
    page.feed(body.decode("utf-8", errors="replace"))
    if not page.parking:
        raise ValueError("parking list not found in page - layout changed or empty response")
    rows = []
    for lot in page.parking:
        val = lot.get("free_spaces")
        m = re.search(r"place/(-?\d+\.\d+),(-?\d+\.\d+)", lot.get("map_url") or "")
        lat, lon = (float(m.group(1)), float(m.group(2))) if m else (None, None)
        rows.append({
            "schema": SCHEMA_ROW, "sid": src["sid"],
            "datastream": f"{lot['name']}|free_spaces", "station_id": lot["name"], "parameter": "free_spaces",
            "result": val, "unit": "1",
            "phenomenonTime": None, "phenomenonTimeUnknown": True,
            "phenomenonTimeReason": "source publishes no measurement time, no Last-Modified, no ETag (OBS-001 audit)",
            "resultTime": None, "receivedTime": iso(received),
            "resultQuality": "unvalidated" if isinstance(val, int) else "missing",
            "map_url": lot.get("map_url"), "lat": lat, "lon": lon,
            "spatial_binding": "operator map link on the source page" if m else None,
        })
    return rows


def parse_rss(body: bytes, received: datetime, src: dict) -> list[dict]:
    """RSS 2.0 / Atom feed -> one text row per item: title, link, publication time. Nothing else.

    Legal frame (07-legal/COLLECTION_LEGAL_FRAME.md): Serbia has no text-and-data-mining exception, so
    the collector keeps only what Art. 49 short quotation and metadata allow - the headline (capped),
    the link and the publisher's own publication time - and never the description or body. For these
    sources the raw response is NOT stored (store_raw=false in COLLECTORS.json); only its hash is.
    Publication time is resultTime; the event's own time is unknown (phenomenonTimeUnknown)."""
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    root = ET.fromstring(body)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    rows = []
    items = root.findall(".//item")
    atom = not items
    if atom:
        items = root.findall(".//a:entry", ns)
    for it in items:
        if atom:
            title = (it.findtext("a:title", default="", namespaces=ns) or "").strip()
            link_el = it.find("a:link", ns)
            link = (link_el.get("href") if link_el is not None else "") or ""
            guid = (it.findtext("a:id", default="", namespaces=ns) or link).strip()
            pub = (it.findtext("a:published", default="", namespaces=ns) or it.findtext("a:updated", default="", namespaces=ns) or "").strip()
        else:
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            guid = (it.findtext("guid") or link).strip()
            pub = (it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date") or "").strip()
        rt = None
        if pub:
            try:
                rt = iso(parsedate_to_datetime(pub))
            except (TypeError, ValueError):
                try:
                    rt = iso(datetime.fromisoformat(pub.replace("Z", "+00:00")))
                except ValueError:
                    rt = None
        title = " ".join(title.split())
        if not title and not link:
            continue
        rows.append({
            "schema": SCHEMA_ROW, "sid": src["sid"], "kind": "text",
            "datastream": f"{src['sid']}|headline", "station_id": src["sid"], "parameter": "headline",
            "result": title or None, "unit": None, "link": link or None,
            "phenomenonTime": None, "phenomenonTimeUnknown": True,
            "phenomenonTimeReason": "a headline carries its publication time, not the time of what it reports",
            "resultTime": rt, "receivedTime": iso(received),
            "resultQuality": "unvalidated" if title else "missing",
            "dedupe_key": f"{src['sid']}|{hashlib.sha256((guid or link or title).encode('utf-8')).hexdigest()[:24]}",
        })
    return rows


def parse_city_listing(body: bytes, received: datetime, src: dict) -> list[dict]:
    """beograd.rs listing pages (Beoinfo vesti, servisne informacije) -> one text row per card: title, link,
    publication date. The City's own notices are official materials of a body exercising public function
    (Copyright Act Art. 6(2)); the collector still keeps only what it keeps for every feed - a headline, the
    link and the date - by the same rule. robots.txt disallows the portal's /feed/, so this is the listing
    route (NEWS_AUDIT_2026-09-09). The page gives a day, not a time: resultTime is that day at 00:00 in the
    source's local calendar, marked as a date-only publication."""
    import html as _html
    text = body.decode("utf-8", "replace")
    rows = []
    cards = re.findall(r'<div class="simple-news-card">(.*?)</div>\s*</a>\s*</div>', text, re.S)
    if not cards:   # the card markup changed: fall back to any article link with a title and a nearby time
        cards = re.findall(r'(<a href="/(?:lat|cir)/[^"]*/a\d+/[^"]*"[^>]*title="[^"]*"[^>]*>.*?news-card__time">[^<]*<)', text, re.S)
    base = re.match(r"https?://[^/]+", src.get("url") or "https://www.beograd.rs").group(0)
    for c in cards:
        m_href = re.search(r'href="([^"]+)"', c)
        m_title = re.search(r'title="([^"]*)"', c) or re.search(r'simple-news-card__title">([^<]*)<', c)
        m_time = re.search(r'news-card__time">\s*([0-9.]+)\s*<', c)
        if not m_href or not m_title:
            continue
        link = m_href.group(1)
        if link.startswith("/"):
            link = base + link
        title = " ".join(_html.unescape(m_title.group(1)).split())
        rt = None
        if m_time:
            try:
                d = datetime.strptime(m_time.group(1).strip("."), "%d.%m.%Y")
                rt = d.strftime("%Y-%m-%d")   # a date, not an instant - kept as the page gives it
            except ValueError:
                rt = None
        m_id = re.search(r"/a(\d+)/", link)
        guid = m_id.group(1) if m_id else link
        rows.append({
            "schema": SCHEMA_ROW, "sid": src["sid"], "kind": "text",
            "datastream": f"{src['sid']}|headline", "station_id": src["sid"], "parameter": "headline",
            "result": title or None, "unit": None, "link": link or None,
            "phenomenonTime": None, "phenomenonTimeUnknown": True,
            "phenomenonTimeReason": "a notice carries its publication day, not the time of what it announces",
            "resultTime": rt, "resultTimeResolution": "day" if rt else None, "receivedTime": iso(received),
            "resultQuality": "unvalidated" if title else "missing",
            "dedupe_key": f"{src['sid']}|{hashlib.sha256(guid.encode('utf-8')).hexdigest()[:24]}",
        })
    return rows


def _cells(row_html: str) -> list[str]:
    import html as _html
    return [" ".join(_html.unescape(re.sub(r"<[^>]+>", " ", c)).split()) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.S | re.I)]


def parse_eds_outages(body: bytes, received: datetime, src: dict) -> list[dict]:
    """Elektrodistribucija Srbije - planned power outages for Belgrade, one HTML table per day
    (Dan_1 = the next day). Rows: municipality | time window | streets with house numbers. Each row
    becomes one text row (a notice, like a headline): the day comes from the table title, the row is
    dedupe-keyed by its content, so a notice is recorded once even though the page is polled hourly.
    A public enterprise's notice is an official material of a body exercising public function
    (Copyright Act Art. 6(2)); the text is kept as served (Cyrillic)."""
    text = body.decode("utf-8", "replace")
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    day = m.group(1) if m else None
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S | re.I):
        c = _cells(tr)
        if len(c) != 3 or not re.match(r"\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}", c[1] or ""):
            continue
        muni, when, streets = c[0], " ".join(c[1].split()), c[2].rstrip(", ").strip()
        title = f"Планирано искључење струје {day or ''} · {muni} · {when} · {streets}"[:200]
        key = f"{day}|{muni}|{when}|{streets}"
        rows.append({
            "schema": SCHEMA_ROW, "sid": src["sid"], "kind": "text",
            "datastream": f"{src['sid']}|notice", "station_id": muni, "parameter": "planned_outage",
            "result": title, "unit": None, "link": src.get("url"),
            "phenomenonTime": None, "phenomenonTimeUnknown": True,
            "phenomenonTimeReason": "a planned outage is a notice about a future window; the day and hours are in the text, the publication instant is not given",
            "resultTime": day, "resultTimeResolution": "day" if day else None, "receivedTime": iso(received),
            "resultQuality": "unvalidated", "outage_day": day, "outage_window": when, "municipality": muni,
            "dedupe_key": f"{src['sid']}|{hashlib.sha256(key.encode('utf-8')).hexdigest()[:24]}",
        })
    return rows


RHMZ_BELGRADE = {  # coordinates: approximate, from the RHMZ station descriptions; to be replaced by the official list (S188 route)
    "Beograd": (44.800, 20.467), "Košutnjak": (44.766, 20.421), "Beograd-Opservatorija": (44.800, 20.467),
}


def _belgrade_local_offset(d: datetime) -> int:
    """Europe/Belgrade without tzdata: CEST (+2) from the last Sunday of March 01:00 UTC to the last Sunday of October 01:00 UTC, else CET (+1)."""
    def last_sunday(y, mth):
        x = datetime(y, mth + 1, 1, tzinfo=timezone.utc) - timedelta(days=1) if mth < 12 else datetime(y, 12, 31, tzinfo=timezone.utc)
        return x - timedelta(days=(x.weekday() + 1) % 7)
    y = d.year
    start = last_sunday(y, 3).replace(hour=1)
    end = last_sunday(y, 10).replace(hour=1)
    return 2 if start <= d.astimezone(timezone.utc) < end else 1


def parse_rhmz_auto(body: bytes, received: datetime, src: dict) -> list[dict]:
    """RHMZ automatic stations (hidmet.gov.rs/latin/osmotreni/automatske.php): the state network with one
    shared 'termin' (date + HH:MM, local time) and the supplementary network with a time per row.
    Only the Belgrade stations are kept (RHMZ_BELGRADE). Local time is converted to UTC with the
    project's own DST rule and marked so. Units and columns as served: temperature °C, pressure hPa,
    humidity %, wind direction (compass text or degrees), wind speed m/s."""
    text = body.decode("utf-8", "replace")
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})\.?(?:&nbsp;|\s)*termin:(?:&nbsp;|\s)*(\d{1,2}):(\d{2})", text)
    if not m:
        raise ValueError("expected RHMZ timestamp/table was not found")
    dd, mm, yy, hh, mi = (int(x) for x in m.groups())
    base_local = datetime(yy, mm, dd, hh, mi)
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S | re.I):
        c = _cells(tr)
        if not c or c[0] not in RHMZ_BELGRADE:
            continue
        if len(c) == 8 and re.fullmatch(r"\d{1,2}:\d{2}", c[1] or ""):
            th, tm = (int(x) for x in c[1].split(":"))
            local = base_local.replace(hour=th, minute=tm)
            vals = c[2:7]
        elif len(c) == 7:
            local = base_local
            vals = c[1:6]
        else:
            raise ValueError("unrecognized RHMZ automatic station column layout")
        pt, off = belgrade_local(local)
        lat, lon = RHMZ_BELGRADE[c[0]]
        for name, unit, raw in (("temperature", "Cel", vals[0]), ("pressure", "hPa", vals[1]), ("humidity", "%", vals[2]),
                                ("wind_direction", "compass", vals[3]), ("wind_speed", "m/s", vals[4])):
            text_val = None
            if name == "wind_direction":
                try:
                    val = float(raw)          # degrees on the supplementary network
                except (TypeError, ValueError):
                    val, text_val = None, (raw or None)   # a compass word on the state network: kept as text, never as a number
            else:
                try:
                    val = float(raw.replace(",", "."))
                except (TypeError, ValueError):
                    val = None
            rows.append({
                "schema": SCHEMA_ROW, "sid": src["sid"],
                "datastream": f"{c[0]}|{name}", "station_id": c[0], "station_name": c[0], "parameter": name,
                "result": val, "result_text": text_val, "unit": unit if name != "wind_direction" else ("deg" if val is not None else "compass"),
                "phenomenonTime": iso(pt), "phenomenonTimeUnknown": pt is None,
                "phenomenonTimeUnknownReason": "ambiguous or nonexistent local DST time" if pt is None else None,
                "phenomenonTimeSource": f"'termin' {local.strftime('%H:%M')} local (UTC+{off}, project DST rule) as printed on the page",
                "resultTime": None, "receivedTime": iso(received),
                "resultQuality": "unvalidated" if (val is not None or text_val) else "missing",
                "lat": lat, "lon": lon, "spatial_binding": "station coordinates approximate (RHMZ description), not from an official list",
                "dedupe_key": f"{src['sid']}|{c[0]}|{name}|{iso(pt)}",
            })
    if not rows:
        raise ValueError("RHMZ automatic table has no recognized Belgrade station rows")
    return rows


METAR_FIELDS = (("temperature", "Cel", "temp"), ("dew_point", "Cel", "dewp"), ("wind_direction", "deg", "wdir"),
                ("wind_speed", "kt", "wspd"), ("pressure_qnh", "hPa", "altim"))


def parse_metar(body: bytes, received: datetime, src: dict) -> list[dict]:
    """NOAA Aviation Weather METAR for LYBE (Belgrade / Nikola Tesla airport). The observation carries its
    own instant - obsTime, a UNIX epoch, which the airport's own site never publishes - so this is a
    measurement with a stated measurement time, not a reception. US federal data, no key. The station is
    at the airport, not in the city: the row says so through its own coordinates, and nothing here is a
    citywide temperature."""
    rows_in = json.loads(body.decode("utf-8", "replace"))
    if not isinstance(rows_in, list):
        raise ValueError("METAR: expected a list")
    out = []
    for ob in rows_in:
        icao = ob.get("icaoId")
        ts = ob.get("obsTime")
        if not icao or not isinstance(ts, (int, float)):
            continue
        pt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        lat, lon = ob.get("lat"), ob.get("lon")
        for name, unit, key in METAR_FIELDS:
            v = ob.get(key)
            val = float(v) if isinstance(v, (int, float)) else None
            out.append({
                "schema": SCHEMA_ROW, "sid": src["sid"],
                "datastream": f"{icao}|{name}", "station_id": icao, "station_name": ob.get("name") or icao,
                "parameter": name, "result": val, "unit": unit,
                "phenomenonTime": iso(pt), "phenomenonTimeUnknown": False,
                "phenomenonTimeSource": "obsTime (UNIX epoch) as published by the source",
                "resultTime": ob.get("reportTime"), "receivedTime": iso(received),
                "resultQuality": "unvalidated" if val is not None else "missing",
                "lat": lat, "lon": lon,
                "spatial_binding": "airport station coordinates as published by the source; an airport observation, not a citywide value",
                "dedupe_key": f"{src['sid']}|{icao}|{name}|{int(ts)}",
            })
    return out


RHMZ_GAUGES = {   # only the two gauges inside Belgrade; Pancevo is a different city and stays out of scope
    ("SAVA", "BEOGRAD"): (44.8206, 20.4489),
    ("DUNAV", "ZEMUN"): (44.8459, 20.4123),
}
GAUGE_FIELDS = (("water_level", "cm"), ("water_level_change", "cm"), ("discharge", "m3/s"), ("water_temperature", "Cel"))


def parse_rhmz_gauges(body: bytes, received: datetime, src: dict) -> list[dict]:
    """RHMZ river gauges (stanje_voda.php): the daily hydrological table. The page states its own instant in
    UTC - 'vreme: 8:00 (06:00 UTC)' - so no timezone is guessed here. Only the two gauges inside Belgrade are
    kept: the Sava at Beograd and the Danube at Zemun. A cell of '*' or '-' is a MISSING value, never a zero;
    the level is a level, never a discharge. Coordinates are approximate and say so on every row."""
    text = body.decode("utf-8", "replace")
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})\.?(?:&nbsp;|\s)*vreme:(?:&nbsp;|\s)*\d{1,2}:\d{2}(?:&nbsp;|\s)*\((\d{1,2}):(\d{2})\s*UTC\)", text)
    if not m:
        raise ValueError("expected RHMZ timestamp/table was not found")
    dd, mm, yy, hh, mi = (int(x) for x in m.groups())
    pt = datetime(yy, mm, dd, hh, mi, tzinfo=timezone.utc)
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S | re.I):
        c = _cells(tr)
        if len(c) < 3:
            continue
        key = (c[0].strip().upper(), c[2].strip().upper())
        if key not in RHMZ_GAUGES:
            continue
        cells_html = re.findall(r"<t[dh]\b[^>]*>.*?</t[dh]>", tr, re.S | re.I)
        # RHMZ places two image-only navigation cells before the measurements. The live page may
        # insert an additional empty separator there, so find the first four consecutive data cells
        # rather than assuming the next column is the water level. Missing values keep their cell.
        if len(c) >= 9 and all(re.search(r"<img\b", x, re.I) for x in cells_html[3:5]):
            if len(c) == 9:  # compact archived form: two navigation cells, then exactly four values
                vals = c[5:9]
            else:
                starts = [i for i in range(5, len(c) - 3)
                          if all(re.search(r'class\s*=\s*["\'][^"\']*\bbela75\b', cells_html[j], re.I)
                                 and not re.search(r"<img\b", cells_html[j], re.I)
                                 for j in range(i, i + 4))]
                if not starts:
                    raise ValueError("RHMZ gauge measurement columns were not found")
                vals = c[starts[0]:starts[0] + 4]
        elif len(c) == 7:
            vals = c[3:7]
        else:
            raise ValueError("unrecognized RHMZ gauge column layout")
        lat, lon = RHMZ_GAUGES[key]
        station = f"{key[1].title()} ({key[0].title()})"
        for i, (name, unit) in enumerate(GAUGE_FIELDS):
            raw = vals[i] if i < len(vals) else ""
            try:
                val = float(raw.replace(",", "."))
                if not finite(val): val = None
            except (TypeError, ValueError):
                val = None                     # '*' and '-' are the source's own way of saying: no value
            rows.append({
                "schema": SCHEMA_ROW, "sid": src["sid"],
                "datastream": f"{station}|{name}", "station_id": station, "station_name": station,
                "parameter": name, "result": val, "unit": unit,
                "phenomenonTime": iso(pt), "phenomenonTimeUnknown": False,
                "phenomenonTimeSource": "the page states its own reading time in UTC",
                "resultTime": None, "receivedTime": iso(received),
                "resultQuality": "unvalidated" if val is not None else "missing",
                "lat": lat, "lon": lon, "river": key[0].title(),
                "spatial_binding": "gauge coordinates approximate, not from an official list",
                "dedupe_key": f"{src['sid']}|{station}|{name}|{iso(pt)}",
            })
    if not rows:
        raise ValueError("RHMZ gauge table has no recognized Belgrade station rows")
    return rows


PARSERS = {"sepa_hvd": parse_sepa_hvd, "sensor_community": parse_sensor_community, "parking": parse_parking, "rss": parse_rss,
           "city_listing": parse_city_listing, "eds_outages": parse_eds_outages, "rhmz_auto": parse_rhmz_auto,
           "metar": parse_metar, "rhmz_gauges": parse_rhmz_gauges}


# ------------------------------------------------------------------ storage
def publish(path: pathlib.Path, value: dict) -> None:
    """Write JSON without ever replacing an existing file (hard-link publish)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=1).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=".live-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.link(tmp, path)
    finally:
        os.unlink(tmp)


def _row_key(r: dict) -> str:
    """A source row is the same row if datastream, phenomenon time, result time and result agree."""
    if r.get("dedupe_key"):
        return str(r["dedupe_key"]) + "|" + content_id(r)
    return json.dumps([r.get("datastream"), r.get("phenomenonTime"), r.get("resultTime"),
                       r.get("result"), None if r.get("phenomenonTimeUnknown") is False else r.get("receivedTime")],
                      ensure_ascii=False, sort_keys=True)


def append_rows(sid: str, rows: list[dict], received: datetime, dedupe_hours: int = 72) -> tuple[pathlib.Path, int]:
    with exclusive(LIVE / ".write.lock", timeout=120):
        return _append_rows_locked(sid, rows, received, dedupe_hours)


def _append_rows_locked(sid: str, rows: list[dict], received: datetime, dedupe_hours: int = 72) -> tuple[pathlib.Path, int]:
    """Append rows; skip rows already seen in the last `dedupe_hours` (sources with a window re-send).

    The seen-set is a small sidecar, not a re-read of the month file. Rows whose measurement time is
    unknown are keyed on receivedTime as well, so a repeated parking value is still a new reception."""
    p = LIVE / "rows" / sid / (received.strftime("%Y-%m") + ".jsonl")
    p.parent.mkdir(parents=True, exist_ok=True)
    seen_path = LIVE / "rows" / sid / "_seen.json"
    seen: dict = {}
    if seen_path.exists():
        try:
            seen = json.loads(seen_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise ValueError(f'Invalid deduplication cache {seen_path}: {exc}') from exc
    cutoff = iso(received - timedelta(hours=dedupe_hours))
    seen = {k: v for k, v in seen.items() if v >= cutoff}
    written = 0
    with open(p, "a", encoding="utf-8") as fh:
        for r in rows:
            k = _row_key(r)
            if k in seen:
                continue
            seen[k] = r.get("receivedTime") or iso(received)
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            written += 1
    tmp = seen_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(seen, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, seen_path)
    return p, written


def store_raw(sid: str, ts: str, body: bytes, ext: str) -> tuple[pathlib.Path, str]:
    p = LIVE / "raw" / sid / f"{ts}.{ext}.gz"
    p.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(body).hexdigest()
    if not p.exists():
        with gzip.open(p, "wb") as gz:
            gz.write(body)
    return p, digest


def _rel(p: pathlib.Path) -> str:
    """Path relative to the repo when inside it, else absolute (tests point LIVE elsewhere)."""
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def receipts(sid: str, since: datetime | None = None) -> list[dict]:
    out = []
    d = LIVE / "receipts" / sid
    if not d.exists():
        return out
    for p in sorted(d.glob("*.json")):
        if since and p.stem < stamp(since):
            continue
        try:
            out.append(json_object(p))
        except (OSError, ValueError):
            out.append({"schema": SCHEMA_RECEIPT, "sid": sid, "state": "unreadable", "file": p.name})
    return out


# -------------------------------------------------------------------- config
def load_config() -> dict:
    with open(CONFIG, encoding="utf-8") as fh:
        cfg = json.load(fh)
    for s in cfg["sources"]:
        for k in ("sid", "name", "url", "parser", "cadence_seconds", "max_bytes", "timeout_seconds"):
            if k not in s:
                raise ValueError(f"{s.get('sid', '?')}: missing config field {k}")
        if s["parser"] not in PARSERS:
            raise ValueError(f"{s['sid']}: unknown parser {s['parser']}")
    return cfg


def render_url(src: dict, now: datetime) -> str:
    return source_policy.render_url(src, now)


def is_due(src: dict, now: datetime) -> tuple[bool, str]:
    """Due when the newest receipt is older than cadence minus a small tolerance.

    Ticks fire every 5 min, so a 600 s cadence is served every second tick;
    tolerance keeps a 599.2 s gap from becoming a 900 s one."""
    rec = receipts(src["sid"])
    if not rec:
        return True, "no receipt yet"
    last = max(r.get("attempted_at", "") for r in rec)
    try:
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
    except ValueError:
        return True, "unreadable last receipt time"
    gap = (now - last_dt).total_seconds()
    if gap >= src["cadence_seconds"] - 45:
        return True, f"{int(gap)}s since last attempt"
    return False, f"not due ({int(gap)}s < {src['cadence_seconds']}s)"


def paused(sid: str) -> str | None:
    return source_policy.pause_reason(LIVE, sid)


# ---------------------------------------------------------------------- tick
def collect_one(src: dict, now: datetime, latest_gate: dict, fetcher=fetch) -> dict:
    sid = src["sid"]
    ok, why = may_collect(sid, latest_gate, render_url(src, now), now)
    if not ok:
        return {"sid": sid, "state": "not_permitted", "reason": why, "network_requests": 0}
    pz = paused(sid)
    if pz:
        return {"sid": sid, "state": "source_paused", "reason": pz, "network_requests": 0}
    ts = stamp(now)
    claim = LIVE / "receipts" / sid / f"{ts}.claim"
    target = LIVE / "receipts" / sid / f"{ts}.json"
    if target.exists():
        return {"sid": sid, "state": "already_recorded", "file": target.name, "network_requests": 0}
    try:
        publish(claim, {"sid": sid, "claimed_at": iso(now), "pid": os.getpid()})
    except FileExistsError:
        return {"sid": sid, "state": "claimed_unfinished", "network_requests": 0}
    url = render_url(src, now)
    item = {"schema": SCHEMA_RECEIPT, "sid": sid, "name": src["name"], "url": url,
            "attempted_at": iso(now), "permission_capture": why, "state": "failed",
            "http_status": None, "rows": 0, "rows_missing": 0, "network_requests": 1}
    res = fetcher(url, int(src["timeout_seconds"]), int(src["max_bytes"]))
    item["transport"] = res["transport"]
    item["http_status"] = res["status"]
    item["headers_of_interest"] = {k: v for k, v in res["headers"].items()
                                  if k in ("date", "last-modified", "etag", "cache-control", "age", "content-type", "content-length")}
    received = utcnow()
    if res["error"] or res["status"] != 200 or res["body"] is None:
        item["error"] = res["error"] or f"HTTP {res['status']}"
        if res["status"] in (403, 429):
            (LIVE / "receipts" / sid / "PAUSED").write_text(
                f"paused {iso(received)} after HTTP {res['status']}; a person removes this file after reading the source's terms again\n",
                encoding="utf-8")
            item["paused_source"] = True
    else:
        digest = hashlib.sha256(res["body"]).hexdigest()
        if src.get("store_raw", True):
            raw_path, digest = store_raw(sid, ts, res["body"], src.get("ext", "bin"))
            item["raw_file"] = _rel(raw_path)
        else:
            item["raw_file"] = None
            item["raw_not_stored"] = "by rule: this source's body is not retained, only its hash (07-legal)"
        item["raw_sha256"] = digest
        item["raw_bytes"] = len(res["body"])
        phase = 'parsing'
        try:
            rows = PARSERS[src["parser"]](res["body"], received, src)
            for r in rows:
                if isinstance(r.get('result'), (int,float)) and not finite(r['result']):
                    r['result'], r['resultQuality'] = None, 'missing'
                r["permission_capture"] = why
                r["raw_sha256"] = digest
                r["row_id"] = content_id(r)
            item['rows_parsed'] = len(rows)
            phase = 'storage'
            rows_path, written = append_rows(sid, rows, received)
            item["rows"] = len(rows)
            item["rows_new"] = written
            item["rows_missing"] = sum(1 for r in rows if r["result"] is None)
            item["rows_file"] = _rel(rows_path)
            item["state"] = "captured"
            item['payload_outcome'] = 'empty' if not rows else ('unchanged' if not written else 'rows')
        except Exception as exc:  # noqa: BLE001
            item["state"] = "unparsed" if phase == 'parsing' else 'failed'
            item['payload_outcome'] = 'parse_failed' if phase == 'parsing' else 'storage_failed'
            item["error"] = {"type": type(exc).__name__, "message": str(exc)[:240]}
    item["completed_at"] = iso(utcnow())
    publish(target, item)
    try:
        claim.unlink()
    except OSError:
        pass
    return {"sid": sid, "state": item["state"], "file": target.name, "http_status": item["http_status"],
            "rows": item["rows"], "rows_missing": item["rows_missing"], "network_requests": 1}


def tick(now: datetime | None = None, only: str = "") -> dict:
    now = now or utcnow()
    cfg = load_config()
    latest = gate()
    results = []
    for src in cfg["sources"]:
        if only and src["sid"] != only:
            continue
        if not src.get("enabled", True):
            results.append({"sid": src["sid"], "state": "disabled", "network_requests": 0})
            continue
        due, why = is_due(src, now)
        if not due:
            results.append({"sid": src["sid"], "state": "not_due", "reason": why, "network_requests": 0})
            continue
        results.append(collect_one(src, now, latest))
    return {"schema": "beops-live-tick/v1", "at": iso(now), "results": results,
            "network_requests": sum(r.get("network_requests", 0) for r in results)}


# -------------------------------------------------------------------- status
def status(now: datetime | None = None, hours: int = 24) -> dict:
    now = now or utcnow()
    cfg = load_config()
    since = now - timedelta(hours=hours)
    out = []
    for src in cfg["sources"]:
        if src.get("enabled") is False:
            continue   # a source switched off by the editor is not silent - it was never asked (the public page showed three tabloids as "silent all day")
        rec = receipts(src["sid"], since)
        expected = int(hours * 3600 // src["cadence_seconds"])
        captured = sum(1 for r in rec if r.get("state") == "captured")
        failed = sum(1 for r in rec if r.get("state") in ("failed", "unparsed"))
        last_ok = max((r["attempted_at"] for r in rec if r.get("state") == "captured"), default=None)
        age = None
        if last_ok:
            age = int((now - datetime.fromisoformat(last_ok.replace("Z", "+00:00"))).total_seconds())
        cells = _quorum_cells(src, rec, now, hours)
        out.append({"sid": src["sid"], "name": src["name"], "cadence_seconds": src["cadence_seconds"],
                    "expected_slots": expected, "captured": captured, "failed": failed,
                    "missing": max(0, expected - captured - failed), "last_captured_at": last_ok,
                    "age_seconds": age, "paused": paused(src["sid"]), "quorum": cells,
                    "rows_last": next((r.get("rows") for r in reversed(rec) if r.get("state") == "captured"), None),
                    "phenomenon_time_published": src.get("phenomenon_time_published")})
    return {"schema": "beops-live-status/v1", "as_of": iso(now), "window_hours": hours, "sources": out,
            "limit": "counts are receipts on disk; a captured receipt is a successful reception, not a verified measurement"}


def _quorum_cells(src: dict, rec: list[dict], now: datetime, hours: int) -> str:
    """One character per cadence slot: # captured  . missing  x failed  (oldest -> newest)."""
    cad = src["cadence_seconds"]
    n = int(hours * 3600 // cad)
    start = now - timedelta(seconds=n * cad)
    cells = ["."] * n
    for r in rec:
        try:
            t = datetime.fromisoformat(r["attempted_at"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        i = int((t - start).total_seconds() // cad)
        if 0 <= i < n:
            cells[i] = "#" if r.get("state") == "captured" else ("x" if cells[i] != "#" else cells[i])
    return "".join(cells)


def report(now: datetime | None = None) -> pathlib.Path:
    now = now or utcnow()
    st = status(now)
    day = now.strftime("%Y-%m-%d")
    out = RESEARCH / "observations" / "live" / f"REPORT_{day}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    L = [f"Status: current", f"Date: {day}", "Author: tools/collect_daemon.py (generated)", "",
         f"# Live collection - {day}", "",
         f"Generated {st['as_of']} from receipts on disk. A filled cell is a successful reception in that cadence slot; "
         "a dot is a slot with no receipt; an x is a failed or unparsed attempt. Received is not measured; "
         "the last column says whether the source publishes a measurement time at all.", "",
         "| source | cadence | captured / expected (24 h) | failed | last captured (UTC) | age | rows in last | measurement time |",
         "|---|---|---|---|---|---|---|---|"]
    for s in st["sources"]:
        L.append(f"| {s['sid']} {s['name']} | {s['cadence_seconds']}s | {s['captured']} / {s['expected_slots']} | {s['failed']} | "
                 f"{s['last_captured_at'] or '-'} | {_age(s['age_seconds'])} | {s['rows_last'] if s['rows_last'] is not None else '-'} | "
                 f"{s['phenomenon_time_published'] or '-'} |")
    L += ["", "## Quorum (oldest -> newest, one cell per cadence slot)", ""]
    for s in st["sources"]:
        L.append(f"`{s['sid']}` `{s['quorum']}`" + (f"  PAUSED: {s['paused']}" if s["paused"] else ""))
        L.append("")
    L += ["No value in this report is a measurement. Gaps are not filled. Corrections are appended, never edited.", ""]
    out.write_text("\n".join(L), encoding="utf-8")
    return out


def export(now: datetime | None = None, hours: int = 24) -> pathlib.Path:
    # Mutable rows share one cut. Immutable receipt/status reads and rendering
    # happen afterwards, so thousands of receipts cannot block live writers.
    from live_view import observation_view
    with observation_view(LIVE) as inputs:
        return _export_captured(now, hours, inputs)


def _export_captured(now, hours, inputs) -> pathlib.Path:
    """Snapshot of the last `hours` of rows per datastream for the UI studies (public/live-snapshot.json).

    Everything in it is a copy of rows on disk: no aggregation, no filling, no rounding. Datastreams
    with no row in the window are still listed (from the seen-set) with an empty series, so absence
    is visible rather than dropped."""
    now = now or utcnow()
    cfg = load_config()
    since = iso(now - timedelta(hours=hours))
    out = {"schema": "beops-live-snapshot/v1", "as_of": iso(now), "window_hours": hours, "sources": [], "status": status(now, hours)}
    for src in cfg["sources"]:
        streams: dict = {}
        events: list = []
        keep_ids = set(map(str, src.get("station_ids") or []))
        d = inputs / "rows" / src["sid"]
        if d.exists():
            for mf in sorted(d.glob("*.jsonl")):
                for r in observation_rows(mf):
                    if (r.get("receivedTime") or "") < since:
                        continue
                    if r.get("kind") == "text":
                        events.append({"t": r.get("resultTime"), "rx": r.get("receivedTime"), "title": r.get("result"), "link": r.get("link")})
                        continue
                    if keep_ids and r.get("station_id") is not None and str(r.get("station_id")) not in keep_ids:
                        continue   # rows captured before the Belgrade filter existed stay on disk, but are not the observatory's scope
                    ds = streams.setdefault(r["datastream"], {"datastream": r["datastream"], "station": r.get("station_name") or r.get("station_id"),
                                                                "parameter": r.get("parameter"), "unit": r.get("unit"),
                                                                "lat": r.get("lat"), "lon": r.get("lon"), "points": []})
                    # The month file is append-only and older rows predate station_coords / station_names in
                    # COLLECTORS.json; a datastream created from such a row kept lat/lon/name null for ever and the
                    # 32 SEPA stations never appeared on the map. Later rows carry the values - take them.
                    if ds.get("lat") is None and r.get("lat") is not None:
                        ds["lat"], ds["lon"] = r.get("lat"), r.get("lon")
                    if r.get("station_name") and ds.get("station") == r.get("station_id"):
                        ds["station"] = r.get("station_name")
                    pt = r.get("phenomenonTime")
                    pc = r.get("phenomenonTimeCorrected")
                    point = {"t": (pt.get("end") if isinstance(pt, dict) else pt), "tu": bool(r.get("phenomenonTimeUnknown")),
                             "rt": r.get("resultTime"), "rx": r.get("receivedTime"), "v": r.get("result"), "q": r.get("resultQuality")}
                    if r.get("sourceClockUnresolved"):
                        point["source_label"] = point["t"]
                        point["t"], point["tu"] = None, True
                        point["clock_note"] = "source clock correction requires renewed evidence"
                    if isinstance(pc, dict) and pc.get("end"):
                        point["tc"] = pc["end"]      # corrected placement (estimated); the received label stays in "t"
                    ds["points"].append(point)
        out["sources"].append({"sid": src["sid"], "name": src["name"], "cadence_seconds": src["cadence_seconds"],
                               "phenomenon_time_published": src.get("phenomenon_time_published"),
                               "datastreams": sorted(streams.values(), key=lambda x: (str(x["station"]), str(x["parameter"]))),
                               "events": sorted(events, key=lambda e: e["t"] or "")})
    # Organ output travels in its own list, never among observations: state "estimated", with the
    # model, the prompt hash and the input row it was derived from, so the interface can draw it
    # structurally and label it as model-derived (AI Act Art. 50 marking).
    derived = []
    dd = inputs / "derived" / "news"
    if dd.exists():
        for mf in sorted(dd.glob("*.jsonl")):
            for r in json_rows(mf):
                if (r.get("derivedTime") or "") < since:
                    continue
                derived.append({"t": r.get("derivedTime"), "organ": r.get("organ"), "organ_version": r.get("organ_version"),
                                "model": r.get("model"), "ai_generated": True, "bound_by": r.get("bound_by"),
                                "sid": r.get("input_sid"), "headline": r.get("input_headline"),
                                "published": r.get("input_resultTime"), "category": r.get("category"),
                                "belgrade": r.get("belgrade"), "zones": r.get("zones") or [],
                                "event_time_text": r.get("event_time_text"), "note": r.get("note")})
    out["derived"] = sorted(derived, key=lambda e: e["t"] or "")
    orx = sorted((LIVE / "derived" / "news" / "receipts").glob("*.json")) if (LIVE / "derived" / "news" / "receipts").exists() else []
    out["organ_runs"] = []
    for rp in orx[-40:]:
        rec = json_object(rp)
        if (rec.get("at") or "") >= since:
            out["organ_runs"].append({"t": rec.get("at"), "organ": rec.get("organ"), "state": rec.get("state"),
                                      "derived": rec.get("derived"), "model": rec.get("model"),
                                      "waiting": rec.get("waiting"), "reason": rec.get("reason")})
    # The mind: validated utterances of the three entities (state "thought" only - a refused utterance
    # never reaches the public), the last conversations' receipts, and the public scoreboard.
    md = inputs / "derived" / "mind"
    thoughts = []
    try:   # the ekavica guard of the organ (tools/organ_mind.py); rows voiced before it existed are re-checked at export
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        from organ_mind import ijekavian_hits  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        ijekavian_hits = None
    if md.exists():
        retracted = set()
        for mf in sorted(md.glob("????-??.jsonl")):
            if mf.name == "claims.jsonl":
                continue
            for r in json_rows(mf):
                if r.get("state") == "retracted":
                    retracted.add((r.get("conversation"), r.get("entity"), r.get("round")))
        for mf in sorted(md.glob("????-??.jsonl")):
            if mf.name == "claims.jsonl":
                continue
            for r in json_rows(mf):
                if r.get("state") not in ("thought", "organelle") or (r.get("derivedTime") or "") < since:
                    continue
                if (r.get("conversation"), r.get("entity"), r.get("round")) in retracted:
                    continue   # a retraction was appended later: the row stays on disk, never on the page
                sr_state, sr, h_sr, q_sr = r.get("sr_state"), r.get("sr"), r.get("hypotheses_sr") or [], r.get("questions_sr") or []
                # C-033: what a refusal produced is carried too, plainly labelled, so the page can show
                # the Serbian that did not pass instead of only the reason it did not. `sr` stays the
                # validated text and nothing else, so no reader can be shown a refusal as if it passed.
                sr_refused = r.get("sr_refused") or ""
                if ijekavian_hits and sr_state == "voiced":
                    hits = ijekavian_hits(sr or "") + [h for x in h_sr + q_sr for h in ijekavian_hits(x)]
                    if hits:   # voiced under an older guard: the row stays on disk, the Serbian page does not show it
                        sr_refused = sr or sr_refused
                        sr_state, sr, h_sr, q_sr = "refused at export: ijekavian, not ekavica: " + ", ".join(hits[:3]), "", [], []
                thoughts.append({"t": r.get("derivedTime"), "conversation": r.get("conversation"), "round": r.get("round"),
                                 "orchestration": r.get("orchestration"), "state": r.get("state"), "organelle": r.get("organelle"),
                                 "entity": r.get("entity"), "entity_sr": r.get("entity_sr"), "entity_en": r.get("entity_en"),
                                 "model": r.get("model"), "voice_model": r.get("voice_model"), "sr_state": sr_state,
                                 "ai_generated": True, "replies_to": r.get("replies_to") or [],
                                 "sr": sr, "sr_refused": sr_refused, "en": r.get("en"), "cites": r.get("cites") or [],
                                 "hypotheses": r.get("hypotheses") or [], "questions": r.get("questions") or [],
                                 "hypotheses_sr": h_sr, "questions_sr": q_sr,
                                 "next_check": r.get("next_check"), "claim": r.get("claim"), "similarity": r.get("similarity")})
        claims = list(json_rows(md / "claims.jsonl"))
        allrows = [r for mf in sorted(md.glob("????-??.jsonl")) for r in json_rows(mf)]
        board = {}
        for ent in ("observer", "skeptic", "connector", "organelle"):
            u = [r for r in allrows if r.get("entity") == ent and (r.get("state") != "thought" or (r.get("conversation"), r.get("entity"), r.get("round")) not in retracted)]
            c = [r for r in claims if r.get("entity") == ent]
            board[ent] = {"utterances": len(u), "accepted": sum(1 for r in u if r.get("state") in ("thought", "organelle")),
                          "voiced": sum(1 for r in u if r.get("sr_state") == "voiced"),
                          "rejected": sum(1 for r in u if r.get("state") == "rejected"),
                          "retracted": sum(1 for r in u if r.get("state") == "retracted"), "claims": len(c),
                          "true": sum(1 for r in c if r.get("outcome") == "true"), "false": sum(1 for r in c if r.get("outcome") == "false"),
                          "open": sum(1 for r in c if r.get("outcome") is None), "unverifiable": sum(1 for r in c if r.get("outcome") == "unverifiable")}
        out["mind_scores"] = board
        mrx = sorted((LIVE / "derived/mind/receipts").glob("*.json"))
        for rp in mrx[-40:]:
            rec = json_object(rp)
            if (rec.get("at") or "") >= since:
                out["organ_runs"].append({"t": rec.get("at"), "organ": "mind", "state": rec.get("state"),
                                          "derived": rec.get("utterances"), "rejected": rec.get("rejected"),
                                          "model": ", ".join(v for v in (rec.get("models") or {}).values() if v) or None,
                                          "reason": rec.get("reason")})
        out["organ_runs"].sort(key=lambda e: e.get("t") or "")
    out["thoughts"] = sorted(thoughts, key=lambda e: (e["t"] or "", e.get("round") or 0))
    target = ROOT / "public" / "live-snapshot.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(target, out)
    return target


def _age(sec):
    if sec is None:
        return "-"
    if sec < 3600:
        return f"{sec // 60} min"
    if sec < 86400:
        return f"{sec // 3600} h {sec % 3600 // 60} min"
    return f"{sec // 86400} d"


def check() -> dict:
    cfg = load_config()
    latest = gate()
    out = []
    for s in cfg["sources"]:
        ok, why = may_collect(s["sid"], latest, render_url(s, utcnow()))
        out.append({"sid": s["sid"], "permitted": ok, "why": why, "enabled": s.get("enabled", True)})
    return {"config": str(CONFIG.relative_to(ROOT)), "live_dir": str(LIVE.relative_to(ROOT)),
            "curl": shutil.which("curl.exe") or shutil.which("curl"), "sources": out}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["tick", "status", "report", "check", "export"])
    ap.add_argument("--only", default="", help="tick one source id")
    a = ap.parse_args()
    if a.command == "tick":
        print(json.dumps(tick(only=a.only), ensure_ascii=False, indent=1))
    elif a.command == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
    elif a.command == "report":
        print(str(report()))
    elif a.command == "export":
        print(str(export()))
    else:
        print(json.dumps(check(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
