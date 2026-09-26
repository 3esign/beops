#!/usr/bin/env python3
"""
build_public_page.py - generates the citizen-facing front door: docs/index.html (Beograd danas).

Design principles:
- Zero external dependencies (raw HTML5 + inline CSS tokens).
- Five clear blocks for citizens:
  1. Puls sada (rečenica stanja, vreme, vazduh, kiša, starost podatka)
  2. Šta znamo danas... (deca, trčanje, provetravanje, bicikl, veš: DA / OPREZ / NE)
  3. Ritam grada (kultura, sport, saobraćajni radovi iz events.json)
  4. Rečeno / Izmereno (poređenje medijskih naslova i fizičkih senzora)
  5. Zašto verovati (3 ključne metrike i veliko dugme ka instrument.html)
- Every claim links directly to the underlying measurement in instrument.html.
- If data is missing, it explicitly states "ne znam / još ne merimo", never zero.
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import sys
from html import escape
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PUBLIC = ROOT / "public"
RESEARCH = ROOT / "research"

HTML_TEMPLATE = """<!doctype html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Beograd danas — BEOPS</title>
<meta name="description" content="Puls Beograda za građane: vazduh, mikroklima, dešavanja, radovi i provera medijskih tvrdnji na osnovu objektivnih merenja.">
<style>
:root {
  --u: 4px;
  --field: #FBFAF7;
  --panel: #F4F2ED;
  --ink: #111311;
  --ink70: rgba(17,19,17,.72);
  --ink55: #626760;
  --ink30: rgba(17,19,17,.30);
  --ink12: rgba(17,19,17,.12);
  --ink06: rgba(17,19,17,.06);
  --signal: #B93720;
  --signal-faint: rgba(217,58,22,.12);
  --ok: #2E7D32;
  --ok-bg: rgba(46,125,50,.10);
  --warn: #87500C;
  --warn-bg: rgba(201,122,20,.10);
  --bad: #D93A16;
  --bad-bg: rgba(217,58,22,.10);
  --sans: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --mono: "Source Code Pro", Consolas, monospace;
  --maxw: 960px;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --field: #0F110F;
    --panel: #171A17;
    --ink: #F2F1EC;
    --ink70: rgba(242,241,236,.72);
    --ink55: rgba(242,241,236,.55);
    --ink30: rgba(242,241,236,.30);
    --ink12: rgba(242,241,236,.12);
    --ink06: rgba(242,241,236,.06);
    --signal: #F0532B;
    --signal-faint: rgba(240,83,43,.15);
    --ok: #4CAF50;
    --ok-bg: rgba(76,175,80,.14);
    --warn: #E08A1E;
    --warn-bg: rgba(224,138,30,.14);
    --bad: #F0532B;
    --bad-bg: rgba(240,83,43,.14);
  }
}
:root[data-theme="dark"] {
  --field: #0F110F;
  --panel: #171A17;
  --ink: #F2F1EC;
  --ink70: rgba(242,241,236,.72);
  --ink55: rgba(242,241,236,.55);
  --ink30: rgba(242,241,236,.30);
  --ink12: rgba(242,241,236,.12);
  --ink06: rgba(242,241,236,.06);
  --signal: #F0532B;
  --signal-faint: rgba(240,83,43,.15);
  --ok: #4CAF50;
  --ok-bg: rgba(76,175,80,.14);
  --warn: #E08A1E;
  --warn-bg: rgba(224,138,30,.14);
  --bad: #F0532B;
  --bad-bg: rgba(240,83,43,.14);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--field);
  color: var(--ink);
  font: 16px/1.55 var(--sans);
  -webkit-font-smoothing: antialiased;
}
.mono { font-family: var(--mono); font-variant-numeric: tabular-nums; }
a { color: inherit; text-decoration: none; border-bottom: 1px solid var(--signal-faint); transition: border-color .15s; }
a:hover { border-bottom-color: var(--signal); }

header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: color-mix(in srgb, var(--field) 80%, transparent);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--ink12);
}
.hbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: calc(var(--u)*4);
  max-width: var(--maxw);
  margin: 0 auto;
  padding: calc(var(--u)*3) calc(var(--u)*5);
}
.brand { font-weight: 700; font-size: 17px; letter-spacing: -.01em; border: 0; }
.brand span { font-weight: 400; color: var(--ink55); margin-left: 6px; font-size: 14px; }
.nav-link { font-size: 13px; font-weight: 600; padding: 4px 10px; border-radius: 3px; border: 1px solid var(--ink12); }
.nav-link:hover { background: var(--ink06); }

.wrap { max-width: var(--maxw); margin: 0 auto; padding: 0 calc(var(--u)*5); }

/* BLOK 1: Puls sada */
.hero { padding: calc(var(--u)*10) 0 calc(var(--u)*6); }
.hero-tag { font-size: 12px; letter-spacing: .08em; text-transform: uppercase; font-weight: 700; color: var(--signal); margin-bottom: calc(var(--u)*2); }
.hero-headline { font-size: clamp(26px, 4vw, 36px); font-weight: 700; line-height: 1.25; margin: 0 0 calc(var(--u)*3); letter-spacing: -.02em; }
.hero-sub { font-size: 15px; color: var(--ink70); display: flex; gap: calc(var(--u)*4); flex-wrap: wrap; align-items: center; }

/* BLOK 2: Šta znamo danas */
.section-title { font-size: 19px; font-weight: 700; margin: calc(var(--u)*8) 0 calc(var(--u)*4); border-bottom: 1px solid var(--ink12); padding-bottom: calc(var(--u)*2); display: flex; justify-content: space-between; align-items: baseline; }
.section-title span { font-size: 12px; font-weight: 400; color: var(--ink55); }
.cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: calc(var(--u)*3.5); }
.action-card { background: var(--panel); border: 1px solid var(--ink12); border-radius: 4px; padding: calc(var(--u)*4); display: flex; flex-direction: column; justify-content: space-between; min-height: 130px; }
.action-card-top { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: calc(var(--u)*2); }
.action-name { font-weight: 700; font-size: 15px; }
.badge { font-family: var(--mono); font-size: 12px; font-weight: 700; padding: 2px 7px; border-radius: 2px; }
.badge-da { background: var(--ok-bg); color: var(--ok); }
.badge-oprez { background: var(--warn-bg); color: var(--warn); }
.badge-ne { background: var(--bad-bg); color: var(--bad); }
.action-reason { font-size: 13px; color: var(--ink70); margin-bottom: calc(var(--u)*3); }
.action-proof { font-size: 11px; color: var(--ink55); margin-top: auto; font-family: var(--mono); }

/* BLOK 3: Ritam grada */
.events-list { display: flex; flex-direction: column; gap: calc(var(--u)*2); }
.event-row { display: flex; gap: calc(var(--u)*3); align-items: baseline; padding: calc(var(--u)*2.5) calc(var(--u)*3); background: var(--panel); border: 1px solid var(--ink12); border-radius: 3px; font-size: 14px; flex-wrap: wrap; }
.event-zone { font-family: var(--mono); font-size: 11px; font-weight: 600; padding: 2px 6px; background: var(--ink06); border-radius: 2px; color: var(--ink70); }
.event-cat { font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--signal); }
.event-title { flex: 1; min-width: 200px; font-weight: 500; }
.event-src { font-size: 12px; color: var(--ink55); }

/* BLOK 4: Receno vs Izmereno */
.compare-box { background: var(--panel); border: 1px solid var(--ink12); border-radius: 4px; overflow: hidden; }
.compare-header { display: grid; grid-template-columns: 1fr 1fr; padding: calc(var(--u)*2.5) calc(var(--u)*4); background: var(--ink06); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--ink70); }
.compare-row { display: grid; grid-template-columns: 1fr 1fr; padding: calc(var(--u)*3) calc(var(--u)*4); border-top: 1px solid var(--ink12); gap: calc(var(--u)*4); font-size: 13px; }
.compare-side b { display: block; font-size: 14px; margin-bottom: 2px; }
.compare-side span { color: var(--ink55); font-size: 12px; }

/* BLOK 5: Dokazi i instrument */
.evidence-hero { margin: calc(var(--u)*10) 0 calc(var(--u)*8); padding: calc(var(--u)*6); background: var(--panel); border: 1px solid var(--ink12); border-radius: 6px; text-align: center; }
.metrics-row { display: flex; justify-content: center; gap: calc(var(--u)*8); margin-bottom: calc(var(--u)*6); flex-wrap: wrap; }
.metric-box { text-align: center; }
.metric-num { font-size: 32px; font-weight: 700; font-family: var(--mono); color: var(--ink); line-height: 1; }
.metric-lbl { font-size: 12px; color: var(--ink55); margin-top: calc(var(--u)*1); }
.btn-instrument { display: inline-block; background: var(--ink); color: var(--field); font-weight: 700; font-size: 15px; padding: calc(var(--u)*3) calc(var(--u)*6); border-radius: 4px; border: 0; transition: opacity .15s; }
.btn-instrument:hover { opacity: .9; }

footer { padding: calc(var(--u)*6) 0 calc(var(--u)*10); border-top: 1px solid var(--ink12); font-size: 12px; color: var(--ink55); }
.authors { font-weight: 500; color: var(--ink70); margin-bottom: calc(var(--u)*2); }
</style>
</head>
<body>

<header>
  <div class="hbar">
    <div class="brand">BEOPS <span>Beograd danas</span></div>
    <div style="display:flex; gap:10px; align-items:center;">
      <a href="mapa.html" class="nav-link">Mapa →</a>
      <a href="instrument.html" class="nav-link">Naučni instrument →</a>
    </div>
  </div>
</header>

<main class="wrap">

  <!-- BLOK 1: PULS SADA -->
  <section class="hero">
    <div class="hero-tag">Puls Beograda · __PULSE_TIME_LABEL__</div>
    <h1 class="hero-headline">__PULSE_SENTENCE__</h1>
    <p style="max-width:680px;color:var(--ink55);font-size:14px;line-height:1.5">Po jedna poslednja vrednost po seriji u okviru tri sata pre preseka. Prosek ne opisuje svaku lokaciju u gradu.</p>
    <div class="hero-sub">
      <div><b>Vazduh:</b> __AIR_STATUS__ (PM2.5: <span class="mono">__AVG_PM25__ µg/m³</span>)</div>
      <div><b>Stanica u mreži:</b> <span class="mono">__ACTIVE_STATIONS_COUNT__</span></div>
      <div><b>Presek evidencije:</b> <span class="mono">__AS_OF_LABEL__</span></div>
    </div>
  </section>

  <!-- BLOK 2: MOGU LI DANAS -->
  <section>
    <div class="section-title">
      Šta znamo danas u Beogradu…
      <span>raspoloživi zapisi, uz vremenske i prostorne granice</span>
    </div>
    <div class="cards-grid">
      __ACTION_CARDS_HTML__
    </div>
  </section>

  <!-- BLOK 3: RITAM GRADA -->
  <section>
    <div class="section-title">
      Ritam grada: Dešavanja i radovi
      <span>zvanični termini i odvojeni signali iz naslova</span>
    </div>
    <div class="events-list">
      __EVENTS_LIST_HTML__
    </div>
  </section>

  <!-- BLOK 4: RECENO / IZMERENO -->
  <section>
    <div class="section-title">
      Rečeno naspram Izmerenog
      <span>šta mediji tvrde u odnosu na stvarne senzore</span>
    </div>
    <div class="compare-box">
      <div class="compare-header">
        <div>Objavljena tvrdnja u medijima</div>
        <div>Fizičko merenje stanica BEOPS-a</div>
      </div>
      __COMPARE_ROWS_HTML__
    </div>
  </section>

  <!-- BLOK 5: DOKAZI I INSTRUMENT -->
  <section class="evidence-hero">
    <div class="metrics-row">
      <div class="metric-box">
        <div class="metric-num">__HOURS_OF_HISTORY__</div>
        <div class="metric-lbl">Vremenski raspon arhive u satima</div>
      </div>
      <div class="metric-box">
        <div class="metric-num">__SOURCES_COUNT__</div>
        <div class="metric-lbl">Registrovanih izvora</div>
      </div>
      <div class="metric-box">
        <div class="metric-num">?</div>
        <div class="metric-lbl">Nepoznato ostaje nepoznato</div>
      </div>
    </div>
    <a href="instrument.html" class="btn-instrument">Otvori Naučni Instrument i sve dokaze →</a>
    <div style="font-size:12px; color:var(--ink55); margin-top:12px;">
      Instrument pokazuje poreklo i dostupna vremena. Nepoznato vreme, nepotpun izvor i praznina ostaju vidljivi.
    </div>
  </section>

</main>

<footer class="wrap">
  <div class="authors">
    BEOPS · prof. dr Darinka Golubović Matić, Semir Poturak · Svemir (verified contributor)
  </div>
  <div>
    Sa <b>Svemirom</b>, lokalnom AI infrastrukturom autora, kao proverenim saradnikom — ne autorom ·
    with <b>Svemir</b>, the authors' local AI infrastructure, as a verified contributor — not an author.
  </div>
  <div>
    Lokalna evidencijska opservatorija Beograda. Poreklo i granice zapisa dostupni su u instrumentu.
    Uslovi korišćenja razlikuju se po izvoru; <a href="instrument.html#izvori">pogledaj registar i dozvole</a>.
  </div>
</footer>

</body>
</html>
"""

def read_json(p: pathlib.Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def recent_air(snapshot):
    """One latest timed reading per station/parameter within a declared 3h window."""
    def stamp(value):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
        except (ValueError, AttributeError, TypeError):
            return None
    at = stamp(snapshot.get('as_of'))
    selected = {}
    if at is None:
        return selected
    for src in snapshot.get('sources', []):
        for ds in src.get('datastreams', []):
            parameter = ds.get('parameter')
            unit = str(ds.get('unit', '')).replace('μ', 'µ')
            if parameter not in ('PM2.5', 'PM10', 'O3') or not any(x in unit for x in ('µg', 'ug')):
                continue
            if ds.get('state') in ('forecast', 'estimated', 'unavailable', 'untimed'):
                continue
            for point in ds.get('points', []):
                point = {**src.get('point_defaults', {}), **point}
                value = point.get('v')
                measured = stamp(point.get('tc') or point.get('t'))
                if (point.get('tu') or point.get('clock_unresolved') or measured is None
                        or any(flag in str(point.get('q', '')).lower() for flag in ('forecast', 'estimated', 'unavailable', 'invalid'))
                        or isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or value < 0
                        or not -300 <= (at - measured).total_seconds() <= 10800):
                    continue
                key = (src.get('sid'), ds.get('station') or ds.get('datastream'), parameter)
                if key not in selected or measured > selected[key][0]:
                    selected[key] = (measured, value)
    return selected


def safe_url(value):
    return escape(value, quote=True) if isinstance(value, str) and value.startswith(('https://', 'http://')) else 'instrument.html'


def render_events(events_data):
    """A single official schedule never becomes a claim of citywide corroboration."""
    events = events_data.get('events', [])
    scheduled = [ev for ev in events if ev.get('state') == 'forecast' and ev.get('event_status') == 'scheduled' and ev.get('verified') is True and ev.get('event_start')]
    signals = [ev for ev in events if ev.get('state') == 'untimed' and ev.get('verified') is False]
    rows = ['<h3>Najavljeni termini · Kolarac</h3>',
            '<p class="event-src">Jedan zvanični repertoar. Termin je preuzet iz izvora; održavanje, dostupnost mesta i kraj nisu potvrđeni. Ovo nije potpun kalendar grada.</p>']
    received = (events_data.get('repertoire') or {}).get('received_at')
    if received:
        rows.append(f'<p class="event-src">Izvor pročitan: {escape(str(received))}. <a href="events.json">Zapisi i poreklo →</a></p>')
    for ev in scheduled[:6]:
        try:
            start = datetime.fromisoformat(ev['event_start_local'])
            label = start.strftime('%d.%m.%Y. u %H:%M') + ' · Beograd'
        except (KeyError, ValueError, TypeError):
            label = str(ev['event_start'])
        rows.append(f'''<div class="event-row">
          <time class="event-zone" datetime="{escape(str(ev['event_start']), quote=True)}">{escape(label)}</time>
          <a href="{safe_url(ev.get('url'))}" target="_blank" rel="noopener" class="event-title">{escape(str(ev.get('title', '')))}</a>
          <span class="event-src">{escape(str(ev.get('location') or 'Sala nije navedena'))} · {escape(str(ev.get('source', '')))}</span>
        </div>''')
    if not scheduled:
        rows.append('<div class="event-row">Nema budućih termina iz sveže pročitanog repertoara. Izvor nije dostupan, zapis je stariji od 24 sata ili nema potpunog termina.</div>')
    rows.extend(['<h3>Signali iz naslova · dešavanja i radovi</h3>',
                 '<p class="event-src">Klasifikacija po rečima; datum objave nije datum događaja. Vreme, lokacija i trenutna prohodnost nisu potvrđeni.</p>'])
    for ev in signals[:6]:
        rows.append(f'''<div class="event-row">
          <span class="event-cat">{escape(str(ev.get('category', 'Najava')).replace('_', ' '))}</span>
          <a href="{safe_url(ev.get('url'))}" target="_blank" rel="noopener" class="event-title">{escape(str(ev.get('title', '')))}</a>
          <span class="event-src">{escape(str(ev.get('source', '')))}</span>
        </div>''')
    if not signals:
        rows.append('<div class="event-row">U evidenciji trenutno nema izdvojenih naslova.</div>')
    return '\n'.join(rows)


def format_citizen_page():
    city_overview = read_json(DOCS / "city-overview.json") or read_json(PUBLIC / "city-overview.json") or {}
    snapshot = city_overview.get("snapshot", {})
    as_of = snapshot.get("as_of") or city_overview.get("as_of")  # None ostaje None: vreme se ne izmišlja
    
    # Izračunavanje prosečnog PM2.5 i PM10
    pm25_vals = []
    pm10_vals = []
    o3_vals = []
    active_stations = set()

    for (sid, station, param), (_, value) in recent_air(snapshot).items():
        active_stations.add((sid, station))
        {'PM2.5': pm25_vals, 'PM10': pm10_vals, 'O3': o3_vals}[param].append(value)

    avg_pm25 = round(sum(pm25_vals) / len(pm25_vals), 1) if pm25_vals else None
    avg_pm10 = round(sum(pm10_vals) / len(pm10_vals), 1) if pm10_vals else None
    max_o3 = round(max(o3_vals), 1) if o3_vals else None
    station_count = len(active_stations)  # 0 se prikazuje kao "—": odsutno nije nula

    air_status = "Nema nedavnog merenja" if avg_pm25 is None else "Merenja u evidenciji"

    # Satnica — bez očitavanja nema ni vremena očitavanja
    if as_of:
        try:
            dt = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
            as_of_label = dt.strftime("%d.%m. u %H:%M UTC")
            pulse_time_label = dt.strftime("%H:%M")
        except Exception:
            as_of_label = as_of[:16]
            pulse_time_label = "—"
    else:
        as_of_label = "nema svežeg očitavanja"
        pulse_time_label = "—"

    pulse_sentence = (
        f"Poslednji PM2.5 zapisi: prosek {avg_pm25} µg/m³ iz {len(pm25_vals)} serije."
        if avg_pm25 is not None else
        "U okviru tri sata pre ovog preseka nema upotrebljivog PM2.5 merenja. Stariji zapisi ostaju u instrumentu."
    )

    # Događaji se čitaju pre kartica: kartica za bicikl izvodi se iz stvarnih najava radova
    events_data = read_json(DOCS / "events.json") or read_json(PUBLIC / "events.json") or {}
    all_events = events_data.get("events", [])
    roadwork_events = [e for e in all_events if e.get("category") == "saobracaj_radovi"]

    # Available evidence is useful; unvalidated personal-health or route advice is not.
    cards = [
        {"name": "Vazduh na mernim mestima", "badge": "PODACI" if pm25_vals else "NEMA PODATKA",
         "badge_class": "badge-oprez", "reason": f"{len(pm25_vals)} vremenski određenih PM2.5 serija u prozoru od tri sata. Ovo nije procena uslova na svakoj lokaciji.",
         "proof": "vremena, izvori i pojedinačne vrednosti"},
        {"name": "Kretanje kroz grad", "badge": "NASLOVI", "badge_class": "badge-oprez",
         "reason": f"{len(roadwork_events)} naslova označeno je kao saobraćaj/radovi. Trajanje i trenutna prohodnost nisu potvrđeni.",
         "proof": "izvorne najave — datum objave nije datum događaja"},
        {"name": "Boravak i aktivnosti napolju", "badge": "BEZ PROCENE", "badge_class": "badge-oprez",
         "reason": "Zapisi nisu dovoljni za ličnu preporuku o deci, rekreaciji ili provetravanju.",
         "proof": "obim i ograničenja merenja"}
    ]

    cards_html = []
    for c in cards:
        cards_html.append(f"""
        <div class="action-card">
          <div class="action-card-top">
            <div class="action-name">{c['name']}</div>
            <span class="badge {c['badge_class']}">{c['badge']}</span>
          </div>
          <div class="action-reason">{c['reason']}</div>
          <div class="action-proof"><a href="sada.html">Dokaz: {c['proof']} →</a></div>
        </div>
        """)
    action_cards_html = "\n".join(cards_html)

    events_list_html = render_events(events_data)

    # Blok 4: Rečeno / Izmereno — stvarni sačuvani naslovi pored stvarnog merenja.
    # Strana ne presuđuje: pokazuje obe strane i vodi na instrument. Presuda bez analize bila bi izmišljanje.
    headlines_data = read_json(PUBLIC / "headlines.json") or {}
    # "vazduh" sam po sebi hvata avijaciju ("u vazduhu"); traže se reči kvaliteta vazduha
    air_words = ("zagađ", "zagadj", "smog", "pm2", "pm10", "aerozagađ", "aerozagadj",
                 "kvalitet vazduha", "kvalitetu vazduha", "kvaliteta vazduha")
    air_rows = [r for r in headlines_data.get("rows", [])
                if any(w in (r.get("title") or "").lower() for w in air_words)]
    air_rows.sort(key=lambda r: r.get("received") or "", reverse=True)

    if avg_pm25 is not None:
        measured_txt = f"Merne stanice u zapisu beleže srednji PM2.5 od {avg_pm25} µg/m³ ({as_of_label})."
    else:
        measured_txt = "PM2.5 očitavanja trenutno nisu u zapisu."

    compare_rows = [
        {"headline": f"„{r.get('title', '')}”", "source": r.get("source", ""), "measured": measured_txt}
        for r in air_rows[:2]
    ]
    compare_html = []
    for cr in compare_rows:
        compare_html.append(f"""
        <div class="compare-row">
          <div class="compare-side">
            <b>{escape(str(cr['headline']))}</b>
            <span>Izvor: {escape(str(cr['source']))} (sačuvan naslov, vreme objave nije vreme događaja)</span>
          </div>
          <div class="compare-side">
            <b>{cr['measured']}</b>
            <span>Status: <a href="obrasci.html">bez presude — uporedi sam u instrumentu →</a></span>
          </div>
        </div>
        """)
    if not compare_html:
        compare_html.append("""
        <div class="compare-row">
          <div class="compare-side">
            <b>U evidenciji nema svežih naslova o vazduhu za poređenje.</b>
            <span>Ćutanje izvora je zapis, ne kvar.</span>
          </div>
          <div class="compare-side">
            <b>Sva sačuvana merenja i naslovi stoje u instrumentu.</b>
            <span><a href="obrasci.html">Otvori poređenje →</a></span>
          </div>
        </div>
        """)
    compare_rows_html = "\n".join(compare_html)

    # Blok 5 metrike — izmereno, ne ukucano: sati iz watch.json, izvori iz registra
    registry = read_json(RESEARCH / "SOURCE_REGISTRY.json") or {}
    sources_count = len(registry.get("sources", [])) or "—"
    watch = read_json(PUBLIC / "watch.json") or read_json(DOCS / "watch.json") or {}
    hours_of_history = watch.get("figures", {}).get("hours") or "—"

    html = HTML_TEMPLATE
    html = html.replace("__PULSE_TIME_LABEL__", str(pulse_time_label))
    html = html.replace("__PULSE_SENTENCE__", str(pulse_sentence))
    html = html.replace("__AIR_STATUS__", str(air_status))
    html = html.replace("__AVG_PM25__", str(avg_pm25 if avg_pm25 is not None else "—"))
    html = html.replace("__ACTIVE_STATIONS_COUNT__", str(station_count) if station_count else "—")
    html = html.replace("__AS_OF_LABEL__", str(as_of_label))
    html = html.replace("__ACTION_CARDS_HTML__", action_cards_html)
    html = html.replace("__EVENTS_LIST_HTML__", events_list_html)
    html = html.replace("__COMPARE_ROWS_HTML__", compare_rows_html)
    html = html.replace("__HOURS_OF_HISTORY__", f"{hours_of_history}+" if isinstance(hours_of_history, (int, float)) else "—")
    html = html.replace("__SOURCES_COUNT__", str(sources_count))
    return html

def main():
    html = format_citizen_page()
    DOCS.mkdir(parents=True, exist_ok=True)
    out_file = DOCS / "index.html"
    out_file.write_text(html, encoding="utf-8")
    print(f"wrote citizen page: {out_file} ({len(html)} bytes)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
