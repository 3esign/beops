#!/usr/bin/env python3
"""
build_site.py - generate the public front door, docs/index.html, from files on disk.

    python -B tools/build_site.py            write docs/index.html (and copy the studies + snapshot)

It is GENERATED, never hand-edited, for the same reason INDEX.md is: a page that states how many
sources are permitted must not be able to say a number the files do not support. Everything on it
comes from:

    research/SOURCE_REGISTRY.json        the sources and their status
    research/08-provenance/INDEX.md      the permission verdicts (itself generated from captures)
    research/08-provenance/CORRECTIONS.md every time this system said something untrue
    research/COLLECTORS.json             what is collected continuously, and at what cadence
    research/ORGANS.json                 the model organs and their editor of record
    public/live-snapshot.json            the last export of real rows

The page is bilingual by construction (Serbian first, English beside it) and works with no network:
the data is embedded at build time. tools/publish_github.ps1 runs this before pushing, so the public
site is a snapshot of the same files a reviewer can clone.
"""
from __future__ import annotations

import json
import sys
import pathlib
import re
import shutil
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "research"
DOCS = ROOT / "docs"

def read_json(p: pathlib.Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default

def registry() -> dict:
    d = read_json(RES / "SOURCE_REGISTRY.json", {}) or {}
    src = d.get("sources", [])
    rows = []
    for s in src:
        rows.append({
            "id": s.get("id"), "name": s.get("name", ""), "theme": s.get("theme", ""),
            "status": s.get("status", ""), "url": s.get("url", ""),
            "time": (s.get("measurement_time") or "")[:180],
            "reuse": (s.get("reuse") or "")[:220],
            "rhythm": (s.get("rhythm") or "")[:140],
        })
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"reviewed_at": d.get("reviewed_at"), "rows": rows, "counts": counts, "legend": d.get("status_legend", {})}

def provenance() -> dict:
    txt = ""
    try:
        txt = (RES / "08-provenance" / "INDEX.md").read_text(encoding="utf-8")
    except OSError:
        pass
    head = re.search(r"Generated ([^\n]+)", txt)
    nums = {}
    if head:
        for key, pat in [("sources", r"(\d+) sources with stored evidence"), ("captures", r"(\d+) captures"),
                         ("passed", r"(\d+) access checks passed"), ("refused", r"(\d+) refused"),
                         ("undecided", r"(\d+) awaiting decision"), ("incomplete", r"(\d+) incomplete"),
                         ("undocumented", r"(\d+) undocumented")]:
            m = re.search(pat, head.group(1))
            if m:
                nums[key] = int(m.group(1))
        nums["generated"] = head.group(1).split("·")[0].strip()
    refused = []
    block = re.search(r"## Do not collect(.+?)\n## ", txt, re.S)
    if block:
        for line in block.group(1).splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
            if len(cells) >= 3 and cells[0] not in ("id", "---") and not set(cells[0]) <= set("-"):
                refused.append({"id": cells[0], "source": cells[1], "said": re.sub(r"\[|\]\([^)]*\)", "", cells[2])[:300]})
    return {"nums": nums, "refused": refused}

def corrections() -> list:
    try:
        txt = (RES / "08-provenance" / "CORRECTIONS.md").read_text(encoding="utf-8")
    except OSError:
        return []
    out = []
    for m in re.finditer(r"^## (C-\d+) — (.+?)$(.*?)(?=^## C-|\Z)", txt, re.M | re.S):
        body = m.group(3)
        said = re.search(r"\*\*What it said[.:]?\*\*\s*(.+?)(?:\n\n|\*\*)", body, re.S)
        what = re.search(r"\*\*What (?:was actually true|happened)[.:]?\*\*\s*(.+?)(?:\n\n|\*\*)", body, re.S)
        rule = re.search(r"\*\*(?:Generalisation|Rule|The fix)[^*]*\*\*[.:]?\s*(.+?)(?:\n\n|\*\*)", body, re.S)
        def clean(x):
            return re.sub(r"\s+", " ", re.sub(r"`|\*\*|\[|\]\([^)]*\)", "", x.group(1))).strip()[:400] if x else ""
        out.append({"id": m.group(1), "title": re.sub(r"`", "", m.group(2)).strip(),
                    "said": clean(said), "true": clean(what), "rule": clean(rule)})
    return out

def collectors() -> list:
    d = read_json(RES / "COLLECTORS.json", {}) or {}
    return [{"sid": s.get("sid"), "name": s.get("name"), "cadence": s.get("cadence_seconds"),
             "time": s.get("phenomenon_time_published", ""), "enabled": s.get("enabled", True)}
            for s in d.get("sources", [])]

def related() -> dict:
    d = read_json(RES / "RELATED_WORK.json", {}) or {}
    return {"claim": d.get("claim_boundary", {}), "entries": d.get("entries", [])}

def organs() -> list:
    d = read_json(RES / "ORGANS.json", {}) or {}
    return [{"id": o.get("id"), "purpose": o.get("purpose", ""), "status": o.get("status", ""),
             "models": o.get("models_preferred", []), "editor": o.get("editor_of_record", ""),
             "runs_where": o.get("runs_where", "")} for o in d.get("organs", [])]

def live() -> dict:
    d = read_json(ROOT / "public" / "live-snapshot.json", {}) or {}
    out = {"as_of": d.get("as_of"), "sources": []}
    st = {s["sid"]: s for s in (d.get("status", {}) or {}).get("sources", [])}
    for s in d.get("sources", []):
        rows = sum(len(x["points"]) for x in s.get("datastreams", []))
        ev = len(s.get("events", []))
        q = st.get(s["sid"], {})
        out["sources"].append({"sid": s["sid"], "name": s["name"], "rows": rows, "events": ev,
                               "streams": len(s.get("datastreams", [])), "cadence": s.get("cadence_seconds"),
                               "time": s.get("phenomenon_time_published", ""), "quorum": q.get("quorum", ""),
                               "captured": q.get("captured", 0), "expected": q.get("expected_slots", 0),
                               "age": q.get("age_seconds"), "paused": q.get("paused")})
    return out

TEMPLATE = r"""<!doctype html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BEOPS — Belgrade Evidence Observatory</title>
<meta name="description" content="What Belgrade told us, when it told us, and where it went quiet. An evidence-first urban observatory: every value with its source, its three times, its unit and its permission; absence recorded, never zero.">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&family=Source+Code+Pro:wght@400;600&display=swap">
<style>
:root{
  --u:4px;
  --field:#FBFAF7; --panel:#F4F2ED; --ink:#111311; --ink70:rgba(17,19,17,.7); --ink55:rgba(17,19,17,.55);
  --ink30:rgba(17,19,17,.3); --ink12:rgba(17,19,17,.12); --ink06:rgba(17,19,17,.06);
  --signal:#D93A16; --signal-untimed:#C0705A; --signal-faint:rgba(217,58,22,.14);
  --state:#8A8F8A;
  --sans:"Source Sans 3","Segoe UI",system-ui,sans-serif; --mono:"Source Code Pro",Consolas,monospace;
  --maxw:1180px;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --field:#0F110F; --panel:#171A17; --ink:#F2F1EC; --ink70:rgba(242,241,236,.72); --ink55:rgba(242,241,236,.55);
  --ink30:rgba(242,241,236,.3); --ink12:rgba(242,241,236,.12); --ink06:rgba(242,241,236,.06);
  --signal:#F0532B; --signal-untimed:#D8836A; --signal-faint:rgba(240,83,43,.16); }}
:root[data-theme="dark"]{
  --field:#0F110F; --panel:#171A17; --ink:#F2F1EC; --ink70:rgba(242,241,236,.72); --ink55:rgba(242,241,236,.55);
  --ink30:rgba(242,241,236,.3); --ink12:rgba(242,241,236,.12); --ink06:rgba(242,241,236,.06);
  --signal:#F0532B; --signal-untimed:#D8836A; --signal-faint:rgba(240,83,43,.16); }
*{box-sizing:border-box}
html{scroll-behavior:smooth;scrollbar-gutter:stable;scrollbar-width:thin;scrollbar-color:var(--ink30) transparent}
/* C-026, the last few pixels of it. Switching a parameter changes how many stations have a
   value, so the table under the map gets longer or shorter, so the frame reports a different
   height, so the page crosses the height at which the window scrollbar appears - and every
   thing on the page slides seven pixels sideways. Reserving the gutter means the page is the
   same width whether it scrolls or not, and nothing moves that the data did not move. */
/* C-030: the scrollbar was the operating system's, so on a dark page it was a light grey bar -
   the one bright element in the frame. It takes its colours from the same two tokens as
   everything else now, and it is thin, so it reads as an edge rather than as a control.
   Both properties are inherited, so the feed, the minds and the reading column get it too. */
::-webkit-scrollbar{width:9px;height:9px;background:transparent}
::-webkit-scrollbar-thumb{background:var(--ink30);border:3px solid transparent;background-clip:padding-box;border-radius:9px}
::-webkit-scrollbar-thumb:hover{background:var(--ink60)}
::-webkit-scrollbar-corner{background:transparent}

body{margin:0;background:var(--field);color:var(--ink);font:16px/1.55 var(--sans);-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.4;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .07 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.wrap{position:relative;z-index:1;max-width:var(--maxw);margin:0 auto;padding:0 calc(var(--u)*6)}
.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
a{color:inherit;text-decoration:none;border-bottom:1px solid var(--signal-faint);transition:border-color .15s}
a:hover{border-bottom-color:var(--signal)}
a:focus-visible,button:focus-visible{outline:2px solid var(--signal);outline-offset:3px}

header{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--field) 78%,transparent);
  backdrop-filter:saturate(1.25) blur(16px);-webkit-backdrop-filter:saturate(1.25) blur(16px);
  border-bottom:1px solid var(--ink12)}
[id]{scroll-margin-top:64px}   /* the header is sticky: without this, following a nav link hides the heading under it */
.hbar{display:flex;align-items:center;gap:calc(var(--u)*4);padding:calc(var(--u)*3) calc(var(--u)*6);flex-wrap:wrap}   /* the header bar IS the .wrap element, and a `padding: y 0` shorthand here zeroes the side
      padding .wrap gives every other block. On a wide screen the viewport is wider than --maxw so
      nothing shows; on a 412 px phone the name sat flush against the glass. Set both axes. */
.brand{font-weight:700;letter-spacing:-.01em;font-size:17px;border:0;white-space:nowrap;flex:none}
/* Both palettes have always existed; what was missing was a way for the reader to choose one.
   Three states, in this order: follow the machine, light, dark. The choice is remembered in this
   browser only and is passed to every frame, because a page that is light with dark windows in it
   is not a light page. */
.themebtn{flex:none;font-size:13px;line-height:1;padding:4px 8px}
.hlangs{display:flex;gap:4px;flex:none}
.hlangs button{font-size:12px;padding:3px 8px}
.hlangs button[aria-pressed="true"]{background:var(--ink);color:var(--field);border-color:var(--ink)}
.brand span{font-weight:400;color:var(--ink55)}
nav{display:flex;gap:calc(var(--u)*4);margin-left:auto;flex-wrap:wrap;font-size:14px;color:var(--ink70)}
nav a{border:0;padding:2px 0;border-bottom:1px solid transparent}
nav a:hover{border-bottom-color:var(--signal)}
button{font:inherit;font-size:13px;color:var(--ink);background:transparent;border:1px solid var(--ink30);
  padding:3px 10px;border-radius:3px;cursor:pointer;transition:background .15s}
button:hover{background:var(--ink06)}
button[aria-pressed="true"]{background:var(--ink);color:var(--field);border-color:var(--ink)}

.hero{padding:calc(var(--u)*8) 0 calc(var(--u)*6)}
/* The hero is three bands, not two columns with things hanging off them. Band one is the claim on
   the left and the thesis on the right, their baselines aligned. Band two is the signature, quiet and
   full width. Band three is the live panel, centred. Everything that spans is declared as spanning:
   a child dropped into a two-column grid lands in the next cell, which is how the panel ended up
   under the left-hand text with half the row empty beside it. */
.herohead{display:grid;grid-template-columns:minmax(0,1fr) minmax(430px,1.45fr) minmax(0,1fr);gap:0 calc(var(--u)*7);align-items:start;margin-bottom:calc(var(--u)*6)}   /* start, not center: three columns of different heights centred against each other read as
      ragged. One top edge, and the panel is the wide one because it is the thing with data in
      it. */
.stage{position:relative;width:100%;margin:0 auto;height:min(92vh,1040px);border:1px solid var(--ink12);overflow:hidden;background:var(--field)}
.stage iframe{width:100%;height:100%;border:0;display:block;background:var(--field)}
.stagelink{position:absolute;right:12px;top:10px;font-size:12px;padding:4px 10px;border:1px solid var(--ink30);border-radius:3px;background:color-mix(in srgb,var(--field) 85%,transparent);backdrop-filter:blur(8px)}
.hero .authors{grid-column:1 / -1;max-width:none;margin:calc(var(--u)*7) 0 0;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
/* The signature and the venue line are each ONE line: a signature that wraps stops reading as a
   signature and starts reading as a paragraph. Below 900 px there is no room for that, so they
   wrap there rather than being cut. */

/* The live panel sits in the hero, under the sentence that introduces it. It reports its
   own height like every other frame; the 300px is only what the box holds until it does. */
.nowpanel{width:100%;margin:0;height:316px}
.nowpanel.fit{height:auto}
.nowpanel iframe{width:100%;height:100%;border:0;display:block;background:transparent}
@media (max-width:900px){
  .herohead{grid-template-columns:1fr;gap:calc(var(--u)*4)}
  .hero{padding:calc(var(--u)*5) 0 calc(var(--u)*4)}
  .stage{height:min(92vh,860px);width:100%}
  .hbar{gap:calc(var(--u)*2);padding:calc(var(--u)*2) calc(var(--u)*6);flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}
  .hbar::-webkit-scrollbar{display:none}
  nav{flex-wrap:nowrap;gap:calc(var(--u)*3);font-size:13px;margin-left:auto}
  nav a{white-space:nowrap}
  button#lang,.hlangs,.themebtn{flex:none}
  .brand span{display:none}
  .stagelink{top:auto;bottom:10px}
}
/* The header on a phone: two tidy rows - the name and the four languages on the first, every section
   on the second. It says "two rows" because that is what it must be: this bar is sticky, so every row
   it grows is a row taken from the page for the whole visit. Nine links in a three-column grid is
   three rows, which with the language row made a header 300 px tall on a 412 px phone - a third of
   the screen, permanently. Five columns fit the nine links in two rows at a size that is still a
   tappable 26 px target, and nothing is hidden behind a sideways scroll. */
@media (max-width:760px){
  .hbar{flex-wrap:wrap;overflow:visible;row-gap:calc(var(--u)*1);column-gap:calc(var(--u)*2);padding:calc(var(--u)*1.5) calc(var(--u)*4)}
  .brand{font-size:15.5px;flex:0 0 auto}
  button#lang,.hlangs{margin-left:auto;flex:none;gap:3px}
  .hlangs button{padding:2px 6px;font-size:11px;line-height:1.5}
  nav{order:3;flex:1 0 100%;margin-left:0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));
      column-gap:calc(var(--u)*1.5);row-gap:calc(var(--u)*1);font-size:11.5px;text-align:center}
  nav a{white-space:nowrap;padding:2px 0;min-height:26px;display:flex;align-items:center;justify-content:center}
  [id]{scroll-margin-top:86px}
}
@media (max-width:390px){ nav{font-size:10.5px;column-gap:calc(var(--u)*1)} .brand{font-size:14.5px}
  .hlangs button{padding:2px 5px;font-size:10.5px} [id]{scroll-margin-top:80px} }
.hero .kicker{grid-column:1 / -1;margin:calc(var(--u)*6) 0 0;padding-top:calc(var(--u)*4);border-top:1px solid var(--ink12);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:var(--ink55);font-weight:600}   /* one rule, one place: two declarations for one element is C-023's shape at a smaller
      scale - the second wins silently and nothing shows you which one decided. Muted, not
      signal: at the foot of the hero this is a provenance line, not a headline. */
.hero h1{font-size:clamp(23px,2.65vw,35px);line-height:1.08;margin:0 0 calc(var(--u)*4);font-weight:600;letter-spacing:-.015em;max-width:15ch;text-wrap:balance}
.hero h1 em{font-style:normal;color:var(--signal)}
.hero .sub{font-size:clamp(14.5px,1.2vw,16.5px);color:var(--ink70);max-width:38ch;margin:0;line-height:1.55}
.hero .lede2{font-size:clamp(14px,1.15vw,16px);color:var(--ink70);max-width:34ch;margin:0;line-height:1.55}
.authors{font-size:14px;color:var(--ink55);max-width:70ch}
.authors b{color:var(--ink);font-weight:600}

.databar{border-bottom:1px solid var(--ink12);padding:calc(var(--u)*8) 0}
.layersbar{border-bottom:1px solid var(--ink12);padding:calc(var(--u)*8) 0}
.layers{max-width:820px;margin:0 auto}
.layers svg{width:100%;height:auto;display:block}
.layerlink{display:block;text-align:center;font-size:12px;color:var(--ink55);margin-top:calc(var(--u)*3)}
.folded .secbody{display:none}
/* folded-reads-as-folded: a control for a body that is not there is a broken-looking page */
.folded .wlangs,.folded .stagelink,.folded .layerlink{display:none}
.folded h2{opacity:.72}
button.fold{border-radius:4px}
.folded button.fold{color:var(--ink);border-color:var(--ink30)}
.whatbar{border-bottom:1px solid var(--ink12);background:var(--panel);padding:calc(var(--u)*8) 0}
.whathead{display:flex;align-items:baseline;justify-content:space-between;gap:calc(var(--u)*4);flex-wrap:wrap;margin-bottom:calc(var(--u)*5)}
.whathead h2{margin:0}
.wlangs{display:flex;gap:calc(var(--u)*1)}
.wlangs button{font-size:12px;padding:2px 9px}
.wlangs button[aria-pressed="true"]{background:var(--ink);color:var(--field);border-color:var(--ink)}
.whatgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:calc(var(--u)*6)}
.whatgrid h3{font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink55);margin:0 0 calc(var(--u)*2);font-weight:600}
.whatgrid p{margin:0;font-size:14.5px;color:var(--ink70);line-height:1.55}
.wnote{margin:calc(var(--u)*6) 0 0;font-size:12.5px;color:var(--ink55);max-width:80ch}
.w-en,.w-zh,.w-de{display:none}
.what-en .w-en,.what-zh .w-zh,.what-de .w-de{display:inline}
.what-en .w-sr,.what-zh .w-sr,.what-de .w-sr{display:none}
.problembox{max-width:80ch;margin:calc(var(--u)*6) 0 calc(var(--u)*2);font-size:15.5px;line-height:1.6;color:var(--ink)}
.problembox p{margin:0}
.claimbox{border-left:2px solid var(--signal);padding:calc(var(--u)*1) 0 calc(var(--u)*1) calc(var(--u)*5);margin:calc(var(--u)*6) 0;max-width:80ch}
.claimbox p{margin:0 0 calc(var(--u)*4);color:var(--ink70)}
.claimbox b{color:var(--ink)}
.rwgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:calc(var(--u)*5);margin-top:calc(var(--u)*6)}
.rw{border-top:1px solid var(--ink12);padding-top:calc(var(--u)*3)}
.rw .k{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink55);font-weight:600}
.rw h3{font-size:15px;margin:calc(var(--u)*1) 0 calc(var(--u)*2);font-weight:600;line-height:1.25}
.rw p{margin:0 0 calc(var(--u)*2);font-size:13.5px;color:var(--ink70)}
.rw .takes{color:var(--ink);border-left:1px solid var(--ink12);padding-left:calc(var(--u)*3)}
button.fold{margin-left:auto;font-size:12px;line-height:1;padding:2px 9px;color:var(--ink55)}
h2+button.fold{margin-left:calc(var(--u)*3)}
/* on a narrow screen the drawing keeps a readable size and scrolls inside its own box; the page itself never scrolls sideways */
@media (max-width:760px){.layers{overflow-x:auto;-webkit-overflow-scrolling:touch}.layers svg{width:760px;max-width:none}}
.datastage{height:min(90vh,1100px);border:1px solid var(--ink12);border-radius:6px;overflow:hidden;background:var(--field)}
.airbar{padding:calc(var(--u)*8) 0 0}
.airstage{height:auto}
.barhead{font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink55);margin:0 0 12px;font-weight:600}
.datastage iframe{width:100%;height:100%;border:0;display:block}
.trakastage{height:min(62vh,620px)}   /* until the frame reports its own height, a sane first size */
.datastage.fit,.stage.fit{height:auto}   /* a frame that has reported its height is exactly that tall */
.livebar{border-top:1px solid var(--ink12);border-bottom:1px solid var(--ink12);background:var(--panel);
  padding:calc(var(--u)*5) 0;margin:calc(var(--u)*4) 0 0}
.lgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:calc(var(--u)*6)}
.lcell .sid{font-family:var(--mono);font-size:11px;color:var(--ink55);letter-spacing:.04em}
.lcell .nm{font-size:14px;font-weight:600;margin:2px 0 calc(var(--u)*2);line-height:1.25}
.lcell .big{font-family:var(--mono);font-size:22px;font-variant-numeric:tabular-nums}
.lcell .big.sig{color:var(--signal)}
.lcell .big.unt{color:var(--signal-untimed)}
.lcell .meta{font-family:var(--mono);font-size:11px;color:var(--ink55);margin-top:3px}
.q{display:flex;gap:1px;margin-top:calc(var(--u)*2);height:6px}
.q i{flex:1;display:block;border:1px solid var(--ink30);background:transparent}
.q i.f{background:var(--ink);border-color:var(--ink)}
.q i.x{background:var(--state);border-color:var(--state);opacity:.5}

section{padding:calc(var(--u)*14) 0;border-bottom:1px solid var(--ink12)}
section h2{font-size:clamp(21px,2.4vw,28px);font-weight:600;letter-spacing:-.01em;margin:0 0 calc(var(--u)*3);text-wrap:balance}
section .lede{color:var(--ink70);max-width:66ch;margin:0 0 calc(var(--u)*7)}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:calc(var(--u)*8)}
.cols h3{font-size:15px;margin:0 0 calc(var(--u)*2);font-weight:600}
.cols p{margin:0 0 calc(var(--u)*3);color:var(--ink70);font-size:14.5px}
.rule{border-left:2px solid var(--signal);padding-left:calc(var(--u)*4);margin:calc(var(--u)*2) 0}
.rule b{display:block;font-size:14px;margin-bottom:2px}
.rule span{font-size:13.5px;color:var(--ink70)}

.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:calc(var(--u)*4);margin:0 0 calc(var(--u)*8)}
.stat{border-top:2px solid var(--ink);padding-top:calc(var(--u)*2)}
.stat.warn{border-top-color:var(--signal)}
.stat .n{font-family:var(--mono);font-size:26px;font-variant-numeric:tabular-nums;line-height:1}
.stat .l{font-size:12px;color:var(--ink55);margin-top:3px;line-height:1.3}

.filters{display:flex;gap:calc(var(--u)*2);flex-wrap:wrap;margin-bottom:calc(var(--u)*4);align-items:center}
.filters input{font:inherit;font-size:14px;padding:5px 10px;border:1px solid var(--ink30);background:transparent;color:var(--ink);border-radius:3px;min-width:220px}
.chip{font-family:var(--mono);font-size:11.5px;padding:3px 8px;border:1px solid var(--ink30);border-radius:99px;cursor:pointer;color:var(--ink70)}
.chip[aria-pressed="true"]{background:var(--ink);color:var(--field);border-color:var(--ink)}
.tablewrap{overflow-x:auto;border:1px solid var(--ink12);border-radius:4px}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:760px}
th,td{text-align:left;padding:7px 10px;border-top:1px solid var(--ink12);vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--ink55);font-weight:600;background:var(--panel);position:sticky;top:0;border-top:0}
td.id{font-family:var(--mono);color:var(--ink55);white-space:nowrap}
td.st{white-space:nowrap}
.badge{font-family:var(--mono);font-size:11px;padding:2px 7px;border-radius:99px;border:1px solid var(--ink30);color:var(--ink70);white-space:nowrap}
.badge.ok{border-color:var(--signal);color:var(--signal)}
.badge.no{border-color:var(--state);color:var(--state)}
tr.hide{display:none}
.count{font-family:var(--mono);font-size:12px;color:var(--ink55);margin-top:calc(var(--u)*2)}

.corr{display:grid;gap:calc(var(--u)*4)}
.corr article{border-left:2px solid var(--state);padding-left:calc(var(--u)*4)}
.corr h3{font-size:14.5px;margin:0 0 calc(var(--u)*1);font-weight:600}
.corr h3 span{font-family:var(--mono);color:var(--signal);margin-right:8px;font-size:13px}
.corr p{margin:0 0 4px;font-size:13.5px;color:var(--ink70)}
.corr p b{color:var(--ink);font-weight:600}

.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:calc(var(--u)*4)}
.card{border:1px solid var(--ink12);border-radius:4px;padding:calc(var(--u)*5);background:var(--panel)}
.card h3{margin:0 0 calc(var(--u)*2);font-size:15px}
.card p{margin:0 0 calc(var(--u)*2);font-size:13.5px;color:var(--ink70)}
.card .mono{font-size:11.5px;color:var(--ink55)}

footer{padding:calc(var(--u)*10) 0;font-size:13.5px;color:var(--ink55)}
footer .fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:calc(var(--u)*6)}
footer b{color:var(--ink70);font-weight:600;display:block;margin-bottom:4px}
.lang-en .sr-only,.lang-sr .en-only{display:none}
/* The page writes its own explanations in four languages; everything generated from a
   register stays Serbian and English, because those strings are quotations of what a
   publisher wrote and this project does not translate a source. Chinese and German
   therefore ride on top of English: a block that has no translation falls back to it
   rather than disappearing, and .i18n marks the blocks that do have one. */
.zh-only,.de-only{display:none}
.lang-zh .zh-only,.lang-de .de-only{display:inline}
.lang-zh .en-only.i18n,.lang-de .en-only.i18n{display:none}
/* C-023, enforced by its own test one commit later: merging the two .hero .kicker rules moved
   the surviving one BELOW the narrow-screen block that lets the signature and the venue line
   wrap, so on a phone they would have been clipped to one line instead. Narrowing rules live
   at the end of the sheet. */
@media (max-width:900px){ .hero .authors,.hero .kicker{white-space:normal;overflow:visible;text-overflow:clip}
  .hero h1{max-width:none;font-size:clamp(23px,6.6vw,31px)}
  .hero .sub{max-width:none}
  .nowpanel{height:520px} }
@media (prefers-reduced-motion: reduce){html{scroll-behavior:auto}*{transition:none!important}}
</style>
</head>
<body class="lang-sr">
<header>
  <div class="wrap hbar">
    <a class="brand" href="#top">BEOPS <span>· Beograd</span></a>
    <nav>
      <a href="#sta"><span class="sr-only i18n">Šta je ovo</span><span class="en-only i18n">What this is</span><span class="zh-only">这是什么</span><span class="de-only">Was das ist</span></a>
      <a href="#zivo"><span class="sr-only i18n">Uživo</span><span class="en-only i18n">Live</span><span class="zh-only">实时</span><span class="de-only">Live</span></a>
      <a href="#podaci"><span class="sr-only i18n">Podaci</span><span class="en-only i18n">Data</span><span class="zh-only">数据</span><span class="de-only">Daten</span></a>
      <a href="#slojevi"><span class="sr-only i18n">Slojevi</span><span class="en-only i18n">Layers</span><span class="zh-only">层</span><span class="de-only">Schichten</span></a>
      <a href="#kako"><span class="sr-only i18n">Kako radi</span><span class="en-only i18n">How it works</span><span class="zh-only">如何运作</span><span class="de-only">Funktionsweise</span></a>
      <a href="#izvori"><span class="sr-only i18n">Izvori</span><span class="en-only i18n">Sources</span><span class="zh-only">来源</span><span class="de-only">Quellen</span></a>
      <a href="#srodno"><span class="sr-only i18n">Srodno</span><span class="en-only i18n">Related</span><span class="zh-only">相关</span><span class="de-only">Verwandtes</span></a>
      <a href="#dozvole"><span class="sr-only i18n">Dozvole</span><span class="en-only i18n">Permissions</span><span class="zh-only">许可</span><span class="de-only">Erlaubnisse</span></a>
      <a href="#greske"><span class="sr-only i18n">Greške</span><span class="en-only i18n">Corrections</span><span class="zh-only">更正</span><span class="de-only">Korrekturen</span></a>
    </nav>
    <button type="button" id="theme" class="themebtn" title="Svetlo / tamno · Light / dark" aria-label="Svetlo / tamno · Light / dark">◐</button><div class="hlangs" id="lang" role="group" aria-label="Jezik / Language"><button type="button" data-l="sr" aria-pressed="true">SR</button><button type="button" data-l="en" aria-pressed="false">EN</button><button type="button" data-l="zh" aria-pressed="false">中文</button><button type="button" data-l="de" aria-pressed="false">DE</button></div>
  </div>
</header>

<div id="top" class="hero">
  <div class="wrap herohead">
    <div>
      <h1><span class="sr-only i18n">Ovo je ono što nam je Beograd rekao, kad nam je rekao, i <em>gde je zaćutao</em>.</span><span class="en-only i18n">This is what Belgrade told us, when it told us, and <em>where it went quiet</em>.</span><span class="zh-only">这是贝尔格莱德告诉我们的内容、告诉我们的时刻，以及<em>它沉默的地方</em>。</span><span class="de-only">Das ist, was Belgrad uns gesagt hat, wann es das gesagt hat, und <em>wo es verstummt ist</em>.</span></h1>
      <p class="lede2"><span class="sr-only i18n">Jedan računar na svakih pet minuta pročita javne stranice i fidove beogradskih instrumenata i zapiše šta je stiglo, kad je stiglo i šta je ćutalo. Ništa se ne prikuplja bez sačuvane dozvole. Dozvola je bajt na disku, ne rečenica.</span><span class="en-only i18n">One computer reads the public pages and feeds of Belgrade's instruments every five minutes and writes down what arrived, when it arrived, and what stayed silent. Nothing is collected without a stored permission. A permission is bytes on disk, not a sentence.</span><span class="zh-only">一台计算机每五分钟读取贝尔格莱德各仪器的公开页面与数据源，记录下什么到达了、何时到达，以及什么保持沉默。没有保存的许可，就不采集任何东西。许可是磁盘上的字节，不是一句话。</span><span class="de-only">Ein Rechner liest alle fünf Minuten die öffentlichen Seiten und Feeds der Belgrader Instrumente und schreibt auf, was ankam, wann es ankam und was geschwiegen hat. Ohne gespeicherte Erlaubnis wird nichts erhoben. Eine Erlaubnis sind Bytes auf der Festplatte, kein Satz.</span></p>
    </div>
      <div class="nowpanel"><iframe id="nowstage" src="sada.html?v={stamp}" title="BEOPS · Sada / Now" loading="eager"></iframe></div>
    <p class="sub"><span class="sr-only i18n">Grad govori u prijemima; mapa kruži samo kad je instrument stvarno pročitan; um od malih lokalnih modela razmišlja naglas i svaka njegova rečenica se proverava pre nego što je vidiš. Ono čega nema je zapis — nikada nula. Ništa se ne izmišlja i ništa se ne popunjava: ako izvor ne objavi vreme merenja, ovde piše da vreme nije poznato. Odbijanja se pamte: izvor koji je rekao ne ostaje zapisan kao odbijanje i program ne može da ga zaobiđe. Svaka greška ovog sistema stoji u javnom spisku, sa datumom, i ne briše se. Ovo nije nadzor: nema podataka o pojedincima i nema kamera.</span><span class="en-only i18n">The city speaks in receptions; the map pulses only when an instrument was actually read; a mind of small local models thinks aloud and every sentence is checked before you see it. What is missing is a record — never a zero. Nothing is invented and nothing is filled in: if a source publishes no measurement time, it says here that the time is unknown. Refusals are remembered: a source that said no stays recorded as a refusal, and the program cannot route around it. Every failure of this system stands in a public list, dated, and is never deleted. This is not surveillance: no person-level data and no cameras.</span><span class="zh-only">城市以“接收”说话；只有当仪器真正被读取时，地图才会脉动；一个由小型本地模型组成的思维出声思考，而它的每一句话在你看到之前都经过核验。缺失的东西是一条记录——绝不是零。不虚构，也不填补：如果来源没有发布测量时间，这里就写明时间未知。拒绝会被记住：说过“不”的来源会作为拒绝被记录下来，程序无法绕过它。本系统的每一次失误都列在公开清单中，标注日期，且从不删除。这不是监控：没有个人层面的数据，也没有摄像头。</span><span class="de-only">Die Stadt spricht in Empfängen; die Karte pulsiert nur, wenn ein Instrument tatsächlich gelesen wurde; ein Verstand aus kleinen lokalen Modellen denkt laut, und jeder seiner Sätze wird geprüft, bevor Sie ihn sehen. Was fehlt, ist ein Eintrag — niemals eine Null. Nichts wird erfunden und nichts aufgefüllt: Veröffentlicht eine Quelle keinen Messzeitpunkt, steht hier, dass die Zeit unbekannt ist. Ablehnungen werden behalten: eine Quelle, die Nein gesagt hat, bleibt als Ablehnung festgehalten, und das Programm kann sie nicht umgehen. Jeder Fehler dieses Systems steht mit Datum in einer öffentlichen Liste und wird nie gelöscht. Das ist keine Überwachung: keine personenbezogenen Daten und keine Kameras.</span></p>
      <p class="authors"><b>prof. dr Darinka Golubović Matić</b> · <b>doc. dr Semir Poturak</b> — <span class="sr-only i18n">autori; rad ne nastupa u ime ustanove · sa <b>Svemirom</b> (Claude, Anthropic), proveren saradnik — ne autor</span><span class="en-only i18n">authors; the work does not act in the institution’s name · with <b>Svemir</b> (Claude, Anthropic), a verified contributor — not an author</span><span class="zh-only">作者；本作品不以该机构的名义行事 · 与 <b>Svemir</b>（Claude，Anthropic）协作，经核验的贡献者——而非作者</span><span class="de-only">Autoren; die Arbeit tritt nicht im Namen der Institution auf · mit <b>Svemir</b> (Claude, Anthropic), geprüfter Mitwirkender — kein Autor</span></p>
      <div class="kicker"><span class="sr-only i18n">Naučni rad za konferenciju „Creating sustainable commUNiTy“ · Univerzitet Union – Nikola Tesla, 2026</span><span class="en-only i18n">A scientific paper for the conference “Creating sustainable commUNiTy” · University Union – Nikola Tesla, 2026</span><span class="zh-only">为会议“Creating sustainable commUNiTy”撰写的科学论文 · Union – Nikola Tesla 大学，2026</span><span class="de-only">Eine wissenschaftliche Arbeit für die Konferenz „Creating sustainable commUNiTy“ · Universität Union – Nikola Tesla, 2026</span></div>
  </div>
  <div class="wrap">
    <div class="stage">
      <iframe id="stage" src="monolog.html?v={stamp}" title="BEOPS · Monolog + Puls" loading="eager"></iframe>
    </div>
  </div>
</div>

<div class="airbar" id="vazduhbar">
  <div class="wrap">
    <h2 class="barhead"><span class="sr-only i18n">Vazduh — državna mreža, poslednji sat</span><span class="en-only i18n">Air — the state network, the last hour</span><span class="zh-only">空气——国家监测网，最近一小时</span><span class="de-only">Luft — das staatliche Messnetz, die letzte Stunde</span></h2>
    <div class="datastage airstage"><iframe id="airstage" src="podaci.html?only=vazduh&amp;v={stamp}" title="BEOPS · Vazduh" loading="eager"></iframe></div>
  </div>
</div>

<div class="whatbar" id="sta">
  <div class="wrap">
    <div class="whathead">
      <h2><span class="w-sr">Šta je ovo, tačno</span><span class="w-en">What this is, exactly</span><span class="w-zh">这到底是什么</span><span class="w-de">Was das genau ist</span></h2>
      <div class="wlangs" role="group" aria-label="Jezik / Language">
        <button type="button" data-w="sr" aria-pressed="true">SR</button><button type="button" data-w="en" aria-pressed="false">EN</button><button type="button" data-w="zh" aria-pressed="false">中文</button><button type="button" data-w="de" aria-pressed="false">DE</button>
      </div>
    </div>
    <div class="whatgrid">
      <div>
        <h3><span class="w-sr">Šta je</span><span class="w-en">What it is</span><span class="w-zh">它是什么</span><span class="w-de">Was es ist</span></h3>
        <p><span class="w-sr">Naučni rad koji autori pripremaju za konferenciju na Univerzitetu Union – Nikola Tesla: istraživački instrument, ne servis, ne proizvod i ne nastup u ime ustanove. Jedan računar na svakih pet minuta pročita javne stranice i fidove beogradskih instrumenata i ustanova, i zapiše šta je stiglo, kad je stiglo i šta je ćutalo. Nijedna vrednost se ne izmišlja, ne popunjava i ne izglađuje.</span><span class="w-en">A scientific paper the authors are preparing for a conference at University Union – Nikola Tesla: a research instrument, not a service, not a product, and not the institution speaking. One computer reads the public pages and feeds of Belgrade's instruments and institutions every five minutes and records what arrived, when it arrived, and what stayed silent. No value is invented, filled in or smoothed.</span><span class="w-zh">这是两位作者为联合大学—尼古拉·特斯拉大学的一次学术会议准备的科研工作：一件研究工具，不是服务，不是产品，也不代表该机构发言。一台计算机每五分钟读取贝尔格莱德各类仪器与机构的公开页面和数据源，记录收到了什么、何时收到、以及什么保持沉默。任何数值都不会被编造、填补或平滑处理。</span><span class="w-de">Eine wissenschaftliche Arbeit, die die Autoren für eine Konferenz an der Universität Union – Nikola Tesla vorbereiten: ein Forschungsinstrument, kein Dienst, kein Produkt und keine Äußerung im Namen der Einrichtung. Ein Rechner liest alle fünf Minuten die öffentlichen Seiten und Feeds der Belgrader Messgeräte und Institutionen und hält fest, was eingegangen ist, wann es eingegangen ist und was geschwiegen hat. Kein Wert wird erfunden, ergänzt oder geglättet.</span></p>
      </div>
      <div>
        <h3><span class="w-sr">Sa čim je povezan</span><span class="w-en">What it is connected to</span><span class="w-zh">它连接到什么</span><span class="w-de">Womit es verbunden ist</span></h3>
        <p><span class="w-sr">Sa javnim izvorima, i to samo onima koji su upisani u registar: državna mreža za kvalitet vazduha, meteorološke i hidrološke stanice, aerodromska osmatranja, gradska i komunalna obaveštenja, planirana isključenja struje, parking, građanski senzori i tokovi vesti. Ceo popis, sa stanjem svakog izvora, stoji niže na ovoj stranici.</span><span class="w-en">To public sources, and only those written into the register: the state air-quality network, meteorological and hydrological stations, airport observations, city and utility notices, planned power outages, parking, citizen sensors and news feeds. The full audit, with the state of every source, is further down this page.</span><span class="w-zh">只连接公开来源，且仅限已登记在册的来源：国家空气质量监测网、气象与水文站、机场观测、市政与公用事业公告、计划停电、停车场、公民传感器与新闻源。完整清单及每个来源的状态见本页下方。</span><span class="w-de">Mit öffentlichen Quellen, und nur mit jenen, die im Register eingetragen sind: das staatliche Luftqualitätsnetz, meteorologische und hydrologische Stationen, Flughafenbeobachtungen, städtische und kommunale Mitteilungen, geplante Stromabschaltungen, Parkhäuser, Bürgersensoren und Nachrichten-Feeds. Die vollständige Übersicht mit dem Status jeder Quelle steht weiter unten auf dieser Seite.</span></p>
      </div>
      <div>
        <h3><span class="w-sr">Znaju li izvori za nas</span><span class="w-en">Do the sources know about us</span><span class="w-zh">这些来源知道我们吗</span><span class="w-de">Wissen die Quellen von uns</span></h3>
        <p><span class="w-sr">Pošten odgovor je: pojedinačno nisu obavešteni. Poštuju se pravila koja su sami javno objavili — robots.txt, uslovi korišćenja, Content-Signal — i ta pravila se sačuvaju kao bajtovi pre svakog čitanja. Predstavljamo se pod svojim imenom u svakom zahtevu, imenovano odbijanje se poštuje i ne zaobilazi, a provera se ponavlja jednom nedeljno. Ništa se ne uzima iza prijave, iza plaćanja ni iza zabrane. Ako objavljujete neki od ovih izvora i ne želite da Vas čitamo, dovoljna je jedna poruka na <a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a> — prestajemo u roku od 24 sata, a u registru ostaje zapisano ko je to tražio i kada.</span><span class="w-en">The honest answer is: they have not been individually notified. What is honoured are the rules they themselves published — robots.txt, terms of use, Content-Signal — and those rules are stored as bytes before any reading. We identify ourselves by name in every request, a named refusal is honoured and never circumvented, and the check is repeated weekly. Nothing is taken from behind a login, a paywall or a prohibition. If you publish one of these sources and would rather we did not read it, one message to <a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a> is enough — we stop within 24 hours, and the register records who asked and when.</span><span class="w-zh">诚实的回答是：没有逐一通知它们。我们遵守的是它们自己公开发布的规则——robots.txt、使用条款、Content-Signal——并在每次读取之前将这些规则以字节形式存档。我们在每个请求中都以自己的名义表明身份；被明确拒绝的来源一律遵守，绝不规避；该检查每周重复一次。不从登录、付费墙或禁止访问的位置获取任何内容。如果您是其中某个来源的发布方，且不希望我们读取，只需发一封邮件至 <a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a>——我们将在 24 小时内停止，并在登记册中记录是谁提出的以及提出的时间。</span><span class="w-de">Die ehrliche Antwort lautet: einzeln benachrichtigt wurden sie nicht. Beachtet werden die Regeln, die sie selbst veröffentlicht haben — robots.txt, Nutzungsbedingungen, Content-Signal — und diese Regeln werden vor jedem Lesen als Bytes gespeichert. Wir nennen in jeder Anfrage unseren Namen, eine ausdrückliche Ablehnung wird befolgt und nie umgangen, und die Prüfung wird wöchentlich wiederholt. Nichts wird hinter einem Login, einer Bezahlschranke oder einem Verbot geholt. Wenn Sie eine dieser Quellen veröffentlichen und nicht möchten, dass wir sie lesen, genügt eine Nachricht an <a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a> — wir hören innerhalb von 24 Stunden auf, und im Register bleibt festgehalten, wer darum gebeten hat und wann.</span></p>
      </div>
      <div>
        <h3><span class="w-sr">Šta nije</span><span class="w-en">What it is not</span><span class="w-zh">它不是什么</span><span class="w-de">Was es nicht ist</span></h3>
        <p><span class="w-sr">Nije nadzor, nije „pametni grad" i nije digitalni blizanac. Nema podataka o pojedincima, nema kamera, nema praćenja ljudi. I nije merenje grada: ovo je ono što su instrumenti objavili i kad smo to primili — prijem nije merenje, a ono čega nema je zapis, nikada nula.</span><span class="w-en">Not surveillance, not a "smart city", not a digital twin. No person-level data, no cameras, no tracking of people. And not a measurement of the city: this is what the instruments published, and when we received it — a reception is not a measurement, and what is missing is a record, never a zero.</span><span class="w-zh">这不是监控，不是"智慧城市"，也不是数字孪生。没有个人层面的数据，没有摄像头，不追踪任何人。它也不是对城市的测量：这是仪器所发布的内容以及我们接收到的时间——接收不等于测量，缺失之处是一条记录，而绝非零。</span><span class="w-de">Keine Überwachung, keine „Smart City", kein digitaler Zwilling. Keine personenbezogenen Daten, keine Kameras, keine Verfolgung von Menschen. Und keine Messung der Stadt: Dies ist, was die Instrumente veröffentlicht haben und wann wir es empfangen haben — ein Empfang ist keine Messung, und was fehlt, ist ein Eintrag, niemals eine Null.</span></p>
      </div>
    </div>
    <p class="wnote"><span class="sr-only i18n">Sve što stranica sama kaže — objašnjenja, metodologija, pravila čitanja, zaglavlja i podnožje — postoji na srpskom, engleskom, kineskom i nemačkom. Ono što se generiše iz registara — imena izvora, stanja, ispravke, srodni radovi — ostaje na srpskom i engleskom, jer su to navodi onoga što je neko drugi objavio, a tuđi izvor se ovde ne prevodi. Gde prevoda nema, stoji engleski, a ne prazno.</span><span class="en-only i18n">Everything the page says in its own voice — the explanations, the method, the reading rules, the headings and the footer — exists in Serbian, English, Chinese and German. What is generated from the registers — source names, statuses, corrections, related work — stays Serbian and English, because those are quotations of what someone else published, and a source is not translated here. Where there is no translation the English stands, not a blank.</span><span class="zh-only">凡是本页以自己的声音所说的内容——说明、方法、阅读规则、标题与页脚——都有塞尔维亚语、英语、中文和德语四种。凡是由登记册生成的内容——来源名称、状态、更正、相关工作——保持塞尔维亚语与英语，因为那些是对他人已发布内容的引用，而本项目不翻译来源。没有译文之处显示英语，而不是留白。</span><span class="de-only">Alles, was die Seite mit eigener Stimme sagt — die Erläuterungen, die Methode, die Leseregeln, die Überschriften und die Fußzeile — gibt es auf Serbisch, Englisch, Chinesisch und Deutsch. Was aus den Registern erzeugt wird — Quellennamen, Zustände, Korrekturen, verwandte Arbeiten — bleibt serbisch und englisch, denn das sind Zitate dessen, was jemand anderes veröffentlicht hat, und eine Quelle wird hier nicht übersetzt. Wo keine Übersetzung steht, steht das Englische, keine Lücke.</span></p>
  </div>
</div>

<div class="databar" id="podaci">
  <div class="wrap">
    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:12px">
      <h2 style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink55);margin:0;font-weight:600"><span class="sr-only i18n">Podaci — šta smo izmerili, po stanici i na mapi</span><span class="en-only i18n">Data — what was measured, per station and on the map</span><span class="zh-only">数据——测得了什么，按站点与地图</span><span class="de-only">Daten — was gemessen wurde, je Station und auf der Karte</span></h2>
      
    </div>
    <div class="datastage"><iframe id="datastage" src="podaci.html?v={stamp}" title="BEOPS · Podaci" loading="lazy"></iframe></div>
    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap;margin:28px 0 12px">
      <h2 style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink55);margin:0;font-weight:600"><span class="sr-only i18n">Traka — vreme kao glavni predmet, jedna traka po čulu</span><span class="en-only i18n">The ribbon — time as the primary object, one lane per sense</span><span class="zh-only">时间带——以时间为主体，每种感官一条轨道</span><span class="de-only">Das Band — die Zeit als eigentlicher Gegenstand, eine Spur je Sinn</span></h2>
      
    </div>
    <div class="datastage trakastage"><iframe id="trakastage" src="traka.html?v={stamp}" title="BEOPS · Traka" loading="lazy"></iframe></div>
    <p class="mono" style="font-size:11.5px;color:var(--ink55);margin:12px 0 0"><span class="sr-only i18n">Oznaka postoji samo tamo gde red postoji; prazno mesto je tišina, ne nula.</span><span class="en-only i18n">A mark exists only where a row exists; an empty place is silence, not a zero.</span><span class="zh-only">只有存在数据行的地方才有标记；空白之处是沉默，不是零。</span><span class="de-only">Eine Markierung gibt es nur dort, wo eine Zeile existiert; eine leere Stelle ist Stille, keine Null.</span></p>
  </div>
</div>

<div class="layersbar" id="slojevi">
  <div class="wrap">
    <h2 style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink55);margin:0 0 6px;font-weight:600"><span class="sr-only i18n">Slojevi — od čega je opservatorija napravljena</span><span class="en-only i18n">Layers — what the observatory is made of</span><span class="zh-only">层——这座观测站由什么构成</span><span class="de-only">Schichten — woraus das Observatorium besteht</span></h2>
    <p class="sub" style="margin:0 0 16px;max-width:80ch"><span class="sr-only i18n">Na dnu je zakon — srpski i evropski — i on nosi sve ostalo: sloj postoji samo ako je propušten kroz kapiju dozvole. Iznad njega: podloga grada, statični slojevi, periodični izvori, živa čula, sistem koji organizuje, sistem koji misli i govori, i izraz; znanje stoji pored njih i takođe stoji na zakonu. Brojevi u crtežu se čitaju iz registara pri svakoj objavi.</span><span class="en-only i18n">At the bottom is the law — Serbian and European — and it carries everything else: a layer exists only if it passed the permission gate. Above it: the city's ground, static layers, periodic sources, live senses, the system that organizes, the system that thinks and speaks, and expression; the knowledge stands beside them and on the same slab. The numbers in the drawing are read from the registers at every publish.</span><span class="zh-only">最底层是法律——塞尔维亚的与欧洲的——它承载着其余一切：只有通过许可闸门的层才存在。其上依次是：城市的底图、静态层、周期性来源、实时感官、负责组织的系统、负责思考与言说的系统，以及表达；知识与它们并列，立在同一块基石上。图中的数字在每次发布时都从登记册中读取。</span><span class="de-only">Zuunterst liegt das Recht — das serbische und das europäische — und es trägt alles andere: eine Schicht existiert nur, wenn sie das Erlaubnistor passiert hat. Darüber: der Grund der Stadt, statische Schichten, periodische Quellen, lebendige Sinne, das System, das ordnet, das System, das denkt und spricht, und der Ausdruck; das Wissen steht daneben und auf derselben Platte. Die Zahlen in der Zeichnung werden bei jeder Veröffentlichung aus den Registern gelesen.</span></p>
    <div class="layers">__LAYERS_SVG__</div>
    
  </div>
</div>

<div class="livebar" id="zivo">
  <div class="wrap">
    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:16px">
      <h2 style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink55);margin:0;font-weight:600"><span class="sr-only i18n">Poslednji prijem po izvoru</span><span class="en-only i18n">Last reception per source</span><span class="zh-only">每个来源的最近一次接收</span><span class="de-only">Letzter Empfang je Quelle</span></h2>
      <span class="mono" style="font-size:12px;color:var(--ink55)" id="asof"></span>
    </div>
    <div class="lgrid" id="lgrid"></div>
    <p class="mono" style="font-size:11.5px;color:var(--ink55);margin:16px 0 0"><span class="sr-only i18n">Popunjena ćelija = prijem u tom taktu; prazna = tišina. Prijem nije merenje.</span><span class="en-only i18n">A filled cell is a reception in that slot; an empty one is silence. A reception is not a measurement.</span><span class="zh-only">填充的方格表示该时段有一次接收；空格表示沉默。接收不是测量。</span><span class="de-only">Eine gefüllte Zelle ist ein Empfang in diesem Takt; eine leere ist Stille. Ein Empfang ist keine Messung.</span></p>
  </div>
</div>

<section id="kako">
  <div class="wrap">
    <h2><span class="sr-only i18n">Kako ovo radi</span><span class="en-only i18n">How this works</span><span class="zh-only">它如何运作</span><span class="de-only">Wie das funktioniert</span></h2>
    <p class="lede"><span class="sr-only i18n">Jedan računar autora, jedan zakazani zadatak na svakih pet minuta, i pravila koja se ne pregovaraju.</span><span class="en-only i18n">One computer belonging to the authors, one scheduled task every five minutes, and rules that are not negotiable.</span><span class="zh-only">作者的一台计算机，每五分钟一个计划任务，以及不容商量的规则。</span><span class="de-only">Ein Rechner der Autoren, eine geplante Aufgabe alle fünf Minuten und Regeln, über die nicht verhandelt wird.</span></p>
    <div class="cols">
      <div>
        <h3><span class="sr-only i18n">Dozvola pre kolektora</span><span class="en-only i18n">Permission before collector</span><span class="zh-only">先有许可，后有采集</span><span class="de-only">Erlaubnis vor Sammler</span></h3>
        <p><span class="sr-only i18n">Nijedan izvor se ne čita dok njegov <code>robots.txt</code>, zaglavlja i stranica licence ne budu sačuvani kao bajtovi sa hešom. Nepoznato nikada nije dozvola. Predstavljamo se pošteno kao <span class="mono">Beops-Research-Collect/1.0</span> i kad izvor kaže ne — odgovor je ne, i to se zapisuje da niko ne pokuša ponovo.</span><span class="en-only i18n">No source is read until its <code>robots.txt</code>, headers and licence page are stored as bytes with a hash. An unknown is never a permission. We identify honestly as <span class="mono">Beops-Research-Collect/1.0</span><span class="zh-only">在一个来源的 <code>robots.txt</code>、响应头与许可页面被作为带哈希的字节保存下来之前，我们不会读取它。未知从来不等于许可。我们如实以 <span class="mono">Beops-Research-Collect/1.0</span> 表明身份；当一个来源说不，答案就是不——并被记录下来，以免明年有人再试一次。</span><span class="de-only">Keine Quelle wird gelesen, bevor ihre <code>robots.txt</code>, die Header und die Lizenzseite als Bytes mit Prüfsumme gespeichert sind. Ein Unbekanntes ist niemals eine Erlaubnis. Wir weisen uns ehrlich als <span class="mono">Beops-Research-Collect/1.0</span> aus, und wenn eine Quelle Nein sagt, ist die Antwort Nein — festgehalten, damit es im nächsten Jahr niemand erneut versucht.</span>, and when a source says no the answer is no — recorded, so nobody tries again next year.</span></p>
        <h3><span class="sr-only i18n">Tri vremena</span><span class="en-only i18n">Three times</span><span class="zh-only">三种时间</span><span class="de-only">Drei Zeiten</span></h3>
        <p><span class="sr-only i18n">Izmereno, objavljeno, primljeno — nikad se ne stapaju. Neki izvori ne objavljuju vreme merenja uopšte: tada je vrednost tačna, a njena starost nepoznata, i tako se i crta.</span><span class="en-only i18n">Measured, published, received — never collapsed into one. Some sources publish no measurement time at all: then the value is exact and its age is unknown, and it is drawn that way.</span><span class="zh-only">测量时刻、发布时刻、接收时刻——绝不合并为一。有些来源根本不发布测量时刻：那么数值是准确的，而它的年龄是未知的，并且就按这样绘制。</span><span class="de-only">Gemessen, veröffentlicht, empfangen — niemals zu einem verschmolzen. Manche Quellen veröffentlichen überhaupt keinen Messzeitpunkt: dann ist der Wert exakt und sein Alter unbekannt, und genau so wird er gezeichnet.</span></p>
      </div>
      <div>
        <div class="rule"><b><span class="sr-only i18n">Nema izmišljenog merenja</span><span class="en-only i18n">No invented measurement</span><span class="zh-only">不虚构测量</span><span class="de-only">Keine erfundene Messung</span></b><span><span class="sr-only i18n">Broj koji nijedan izvor nije rekao ne postoji. Bez interpolacije, bez popunjavanja.</span><span class="en-only i18n">A number no source reported does not exist. No interpolation, no back-filling.</span><span class="zh-only">没有任何来源报告过的数字并不存在。不插值，不回填。</span><span class="de-only">Eine Zahl, die keine Quelle gemeldet hat, existiert nicht. Keine Interpolation, kein Auffüllen.</span></span></div>
        <div class="rule"><b><span class="sr-only i18n">Primljeno nije izmereno</span><span class="en-only i18n">Received is not measured</span><span class="zh-only">接收不是测量</span><span class="de-only">Empfangen ist nicht gemessen</span></b><span><span class="sr-only i18n">Vreme prijema je naše, ne gradsko.</span><span class="en-only i18n">The reception time is ours, not the city's.</span><span class="zh-only">接收时刻是我们的，不是城市的。</span><span class="de-only">Der Empfangszeitpunkt ist unserer, nicht der der Stadt.</span></span></div>
        <div class="rule"><b><span class="sr-only i18n">Prognoza nije merenje</span><span class="en-only i18n">Forecast is not measurement</span><span class="zh-only">预报不是测量</span><span class="de-only">Prognose ist keine Messung</span></b><span><span class="sr-only i18n">Procena i prognoza imaju drugi potez i drugu boju — nikad boju merenja.</span><span class="en-only i18n">Estimates and forecasts get a different stroke and never the colour of measurement.</span><span class="zh-only">估计与预报使用不同的笔触，绝不使用测量的颜色。</span><span class="de-only">Schätzungen und Prognosen erhalten einen anderen Strich und nie die Farbe der Messung.</span></span></div>
        <div class="rule"><b><span class="sr-only i18n">Nedostaje nije nula</span><span class="en-only i18n">Missing is not zero</span><span class="zh-only">缺失不是零</span><span class="de-only">Fehlend ist nicht null</span></b><span><span class="sr-only i18n">Mrtav senzor, izdavač koji je odbio i nikad prikupljen izvor su tri različita zapisa.</span><span class="en-only i18n">A dead sensor, a publisher that refused and a never-collected source are three different records.</span><span class="zh-only">失效的传感器、拒绝了我们的发布者，以及从未被采集的来源，是三种不同的记录。</span><span class="de-only">Ein toter Sensor, ein Herausgeber, der abgelehnt hat, und eine nie erhobene Quelle sind drei verschiedene Einträge.</span></span></div>
        <div class="rule"><b><span class="sr-only i18n">Svaka tvrdnja nosi izvor, vreme, prostor, jedinicu i dozvolu</span><span class="en-only i18n">Every claim carries source, time, space, unit and permission</span><span class="zh-only">每一项陈述都带有来源、时间、空间、单位与许可</span><span class="de-only">Jede Aussage trägt Quelle, Zeit, Ort, Einheit und Erlaubnis</span></b><span><span class="sr-only i18n">Dozvola je bajt na disku, ne rečenica.</span><span class="en-only i18n">Permission is bytes on disk, not a sentence.</span><span class="zh-only">许可是磁盘上的字节，不是一句话。</span><span class="de-only">Die Erlaubnis sind Bytes auf der Festplatte, kein Satz.</span></span></div>
      </div>
      <div>
        <h3><span class="sr-only i18n">Šta se sada sakuplja</span><span class="en-only i18n">What is collected now</span><span class="zh-only">目前正在采集什么</span><span class="de-only">Was derzeit gesammelt wird</span></h3>
        <div id="collectors"></div>
        <h3 style="margin-top:20px"><span class="sr-only i18n">Organi — mali lokalni modeli</span><span class="en-only i18n">Organs — small local models</span><span class="zh-only">器官——小型本地模型</span><span class="de-only">Organe — kleine lokale Modelle</span></h3>
        <div id="organs"></div>
      </div>
    </div>
  </div>
</section>

<section id="izvori">
  <div class="wrap">
    <h2><span class="sr-only i18n">Popis otvorenosti: šta Beograd objavljuje, a šta ne</span><span class="en-only i18n">An audit of openness: what Belgrade publishes, and what it does not</span><span class="zh-only">开放度清点：贝尔格莱德发布了什么，又没有发布什么</span><span class="de-only">Eine Bestandsaufnahme der Offenheit: was Belgrad veröffentlicht und was nicht</span></h2>
    <p class="lede"><span class="sr-only i18n">Svaki zapis je pristupna ruta sa stanjem i sledećim korakom. Broj zapisa nije broj uređaja niti broj živih tokova — i tu razliku ovaj projekat ne zamagljuje.</span><span class="en-only i18n">Every record is an access route with a state and a next step. The number of records is not a number of devices or of live feeds — and this project does not blur that difference.</span><span class="zh-only">每一条记录都是一条带有状态和下一步的访问路径。记录的数量不等于设备的数量，也不等于实时数据流的数量——本项目不会模糊这个区别。</span><span class="de-only">Jeder Eintrag ist ein Zugangsweg mit einem Zustand und einem nächsten Schritt. Die Zahl der Einträge ist weder eine Zahl von Geräten noch von laufenden Datenströmen — und dieses Projekt verwischt diesen Unterschied nicht.</span></p>
    <div class="stats" id="rstats"></div>
    <div class="filters">
      <input id="q" type="search" placeholder="pretraga / search" aria-label="search sources">
      <span id="chips"></span>
    </div>
    <div class="tablewrap"><table id="rtable"><thead><tr>
      <th>id</th><th><span class="sr-only i18n">izvor</span><span class="en-only i18n">source</span><span class="zh-only">来源</span><span class="de-only">Quelle</span></th>
      <th><span class="sr-only i18n">stanje</span><span class="en-only i18n">status</span><span class="zh-only">状态</span><span class="de-only">Zustand</span></th>
      <th><span class="sr-only i18n">ritam</span><span class="en-only i18n">rhythm</span><span class="zh-only">节奏</span><span class="de-only">Rhythmus</span></th>
      <th><span class="sr-only i18n">vreme merenja</span><span class="en-only i18n">measurement time</span><span class="zh-only">测量时刻</span><span class="de-only">Messzeitpunkt</span></th>
    </tr></thead><tbody></tbody></table></div>
    <p class="count" id="rcount"></p>
  </div>
</section>

<section id="dozvole">
  <div class="wrap">
    <h2><span class="sr-only i18n">Dokaz dozvole, i ono što je reklo ne</span><span class="en-only i18n">The proof of permission, and what said no</span><span class="zh-only">许可的证据，以及说“不”的那些</span><span class="de-only">Der Nachweis der Erlaubnis, und was Nein gesagt hat</span></h2>
    <p class="lede"><span class="sr-only i18n">Za svaki izvor čuvamo njegov sopstveni <code>robots.txt</code> kako je poslužen, zaglavlja tačnih adresa koje čitamo, stranicu licence i SHA-256 svakog od njih. Odbijanja se čuvaju sa klauzulom, pa se izvor ne otkriva ponovo za godinu dana i ne počne tiho da se sakuplja.</span><span class="en-only i18n">For every source we store its own <code>robots.txt</code> as served, the headers of the exact URLs we read, the licence page, and a SHA-256 of each. Refusals are kept with their clause, so a source is not rediscovered next year and quietly collected.</span><span class="zh-only">对每一个来源，我们都保存它自己被实际送达的 <code>robots.txt</code>、我们所读取的确切网址的响应头、许可页面，以及每一项的 SHA-256。拒绝连同其条款一并保存，这样一个来源不会在明年被重新“发现”并被悄悄采集。</span><span class="de-only">Für jede Quelle speichern wir ihre eigene <code>robots.txt</code> so, wie sie ausgeliefert wurde, die Header genau der URLs, die wir lesen, die Lizenzseite und je einen SHA-256. Ablehnungen werden mitsamt ihrer Klausel aufbewahrt, damit eine Quelle nicht im nächsten Jahr neu entdeckt und still gesammelt wird.</span></p>
    <div class="stats" id="pstats"></div>
    <h3 style="font-size:15px;margin:24px 0 8px"><span class="sr-only i18n">Rekli su ne — i to ostaje zapisano</span><span class="en-only i18n">They said no — and it stays recorded</span><span class="zh-only">他们说了不——并且这被记录下来</span><span class="de-only">Sie haben Nein gesagt — und das bleibt festgehalten</span></h3>
    <div class="tablewrap"><table><thead><tr><th>id</th><th><span class="sr-only i18n">izvor</span><span class="en-only i18n">source</span><span class="zh-only">来源</span><span class="de-only">Quelle</span></th><th><span class="sr-only i18n">šta je reklo ne</span><span class="en-only i18n">what said no</span><span class="zh-only">是什么说了不</span><span class="de-only">was Nein gesagt hat</span></th></tr></thead><tbody id="refused"></tbody></table></div>
  </div>
</section>

<section id="greske">
  <div class="wrap">
    <h2><span class="sr-only i18n">Svaki put kad je ovaj sistem rekao nešto neistinito</span><span class="en-only i18n">Every time this system said something untrue</span><span class="zh-only">这个系统每一次说了不真实的话</span><span class="de-only">Jedes Mal, wenn dieses System etwas Unwahres gesagt hat</span></h2>
    <p class="lede"><span class="sr-only i18n">Sistem koji krije sopstvene greške ne vredi ništa, jer jedino što treba da dokaže jeste da ne govori tiho neistine. Zato je ovaj spisak javan i dopisuje se, nikad se ne briše.</span><span class="en-only i18n">A system that hides its own failures is worth nothing, because the one thing it must prove is that it does not quietly say untrue things. So this list is public, append-only, and never edited.</span><span class="zh-only">一个隐藏自身失误的系统毫无价值，因为它唯一需要证明的，就是它不会悄悄说出不真实的话。因此这份清单是公开的，只追加，从不修改。</span><span class="de-only">Ein System, das die eigenen Fehler verbirgt, ist nichts wert, denn das Einzige, was es beweisen muss, ist, dass es nicht still Unwahres sagt. Darum ist diese Liste öffentlich, wird nur ergänzt und nie überschrieben.</span></p>
    <div class="corr" id="corr"></div>
  </div>
</section>

<section id="kontakt">
  <div class="wrap">
    <h2><span class="sr-only i18n">Prigovor i uklanjanje</span><span class="en-only i18n">Objection and removal</span><span class="zh-only">异议与撤除</span><span class="de-only">Widerspruch und Entfernung</span></h2>
    <div class="claimbox">
      <p><span class="sr-only i18n">Ako objavljujete neki od izvora sa ovog spiska i ne želite da ga čitamo, ne treba Vam ni advokat ni obrazac. Jedna poruka je dovoljna: <a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a>. Prestajemo u roku od 24 sata, bez pregovora, i izvor se više ne predlaže. U javnom registru ostaje zapisano da je zatraženo uklanjanje i kada — zapis se dopisuje, ne prepravlja, pa se vidi i šta je bilo prikupljeno pre toga.</span><span class="en-only i18n">If you publish one of the sources on this list and would rather we did not read it, you need no lawyer and no form. One message is enough: <a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a>. We stop within 24 hours, without negotiation, and the source is never proposed again. The public register keeps a line saying that removal was requested and when — the record is appended to, never rewritten, so what was collected before that also stays visible.</span><span class="zh-only">如果您是本清单中某个来源的发布者，并且不希望我们读取它，您不需要律师，也不需要表格。一条消息就够了：<a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a>。我们会在 24 小时内停止，不作商量，该来源也不会再被提议。公开登记册中会保留一行，记明曾有撤除请求以及时间——记录只追加、绝不改写，因此在那之前采集到的内容也依然可见。</span><span class="de-only">Wenn Sie eine der hier aufgeführten Quellen herausgeben und lieber nicht möchten, dass wir sie lesen, brauchen Sie weder Anwalt noch Formular. Eine Nachricht genügt: <a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a>. Wir hören innerhalb von 24 Stunden auf, ohne Verhandlung, und die Quelle wird nie wieder vorgeschlagen. Im öffentlichen Register bleibt eine Zeile stehen, dass eine Entfernung verlangt wurde und wann — der Eintrag wird ergänzt, nie umgeschrieben, sodass auch sichtbar bleibt, was zuvor erhoben wurde.</span></p>
      <p><span class="sr-only i18n">Isto vredi i za ispravku: ako je nešto ovde netačno, javite i biće ispravljeno, a ispravka će stajati u javnom spisku grešaka sa datumom. Taj spisak se ne briše.</span><span class="en-only i18n">The same holds for a correction: if something here is wrong, tell us and it will be corrected, and the correction will stand in the public list of failures with its date. That list is never deleted.</span><span class="zh-only">更正同理：如果这里有任何错误，请告诉我们，它会被更正，而这条更正会带着日期留在公开的失误清单中。那份清单从不删除。</span><span class="de-only">Dasselbe gilt für eine Korrektur: Ist hier etwas falsch, sagen Sie es uns, es wird korrigiert, und die Korrektur steht mit Datum in der öffentlichen Fehlerliste. Diese Liste wird nie gelöscht.</span></p>
      <p><span class="sr-only i18n">Za pitanja o metodu, pravnom okviru ili saradnji — ista adresa. Odgovaraju autori, ne program.</span><span class="en-only i18n">For questions about the method, the legal frame or collaboration — the same address. The authors answer, not the program.</span><span class="zh-only">关于方法、法律框架或合作的问题——同一个地址。回复的是作者，不是程序。</span><span class="de-only">Für Fragen zur Methode, zum Rechtsrahmen oder zur Zusammenarbeit — dieselbe Adresse. Es antworten die Autoren, nicht das Programm.</span></p>
    </div>
  </div>
</section>

<section id="srodno">
  <div class="wrap">
    <h2><span class="sr-only i18n">Srodni radovi, standardi i projekti</span><span class="en-only i18n">Related work, standards and projects</span><span class="zh-only">相关工作、标准与项目</span><span class="de-only">Verwandte Arbeiten, Normen und Projekte</span></h2>
    <p class="sub" style="max-width:80ch"><span class="sr-only i18n">Ovo nije prvi pokušaj da grad govori kroz svoje instrumente. Ovde stoji odakle je šta uzeto, sa linkom na izvor da čitalac ne mora da nam veruje — i, ispod, šta se ovde tvrdi kao novo, a šta ne. Beleška „uzima" govori šta je ovaj projekat uzeo iz tog rada; ne tvrdi da autori znaju za ovaj projekat niti da ga odobravaju.</span><span class="en-only i18n">This is not the first attempt to let a city speak through its instruments. Here is where each idea came from, with a link so the reader need not take our word — and, below, what is claimed as new here and what is not. The "takes" note says what this project took from that work; it does not claim the authors know of this project or endorse it.</span><span class="zh-only">让城市通过自己的仪器说话，这并非第一次尝试。这里写明每个想法来自何处，并附有链接，读者不必只听我们的说法——下面则写明这里主张什么是新的、什么不是。“取自”一栏说明本项目从该工作中取用了什么；它并不主张那些作者知晓本项目或为其背书。</span><span class="de-only">Dies ist nicht der erste Versuch, eine Stadt durch ihre Instrumente sprechen zu lassen. Hier steht, woher jede Idee stammt, mit einem Link, damit die Leserin uns nicht glauben muss — und darunter, was hier als neu beansprucht wird und was nicht. Der Vermerk „übernimmt“ sagt, was dieses Projekt jener Arbeit entnommen hat; er behauptet nicht, dass deren Autoren von diesem Projekt wissen oder es befürworten.</span></p>
    <div class="problembox">
      <p><span class="sr-only">__PROB_SR__</span><span class="en-only">__PROB_EN__</span></p>
    </div>
    <div class="claimbox">
      <p><b><span class="sr-only i18n">Standardno, i nimalo novo</span><span class="en-only i18n">Standard, and in no way new</span><span class="zh-only">标准做法，毫无新意</span><span class="de-only">Standard, und in keiner Weise neu</span></b><br><span class="sr-only">__STD_SR__</span><span class="en-only">__STD_EN__</span></p>
      <p><b><span class="sr-only i18n">Ono što ovde jeste drugačije</span><span class="en-only i18n">What is different here</span><span class="zh-only">这里有什么不同</span><span class="de-only">Was hier anders ist</span></b><br><span class="sr-only">__OURS_SR__</span><span class="en-only">__OURS_EN__</span></p>
      <p><b><span class="sr-only i18n">Šta se ne tvrdi</span><span class="en-only i18n">What is not claimed</span><span class="zh-only">不主张什么</span><span class="de-only">Was nicht behauptet wird</span></b><br><span class="sr-only">__NOT_SR__</span><span class="en-only">__NOT_EN__</span></p>
    </div>
    <div class="rwgrid" id="related"></div>
  </div>
</section>

<section id="citaj">
  <div class="wrap">
    <h2><span class="sr-only i18n">Čitaj dalje</span><span class="en-only i18n">Read on</span><span class="zh-only">继续阅读</span><span class="de-only">Weiterlesen</span></h2>
    <div class="cards">
      <a class="card" href="https://github.com/3esign/beops" style="border:0;padding:0"><div class="card" style="height:100%"><h3>GitHub</h3><p><span class="sr-only i18n">Kod, registri, pravila i dokaz dozvole — otvoreno. MIT za kod, CC BY 4.0 za dokumente.</span><span class="en-only i18n">Code, registries, rules and the permission evidence — open. MIT for code, CC BY 4.0 for documents.</span><span class="zh-only">代码、登记册、规则与许可证据——全部开放。代码采用 MIT，文档采用 CC BY 4.0。</span><span class="de-only">Code, Register, Regeln und die Erlaubnisnachweise — offen. MIT für den Code, CC BY 4.0 für die Dokumente.</span></p><span class="mono">3esign/beops</span></div></a>
    </div>
  </div>
</section>

<footer>
  <div class="wrap fgrid">
    <div><b><span class="sr-only i18n">Autori i kontakt</span><span class="en-only i18n">Authors and contact</span><span class="zh-only">作者与联系方式</span><span class="de-only">Autoren und Kontakt</span></b>prof. dr Darinka Golubović Matić<br>doc. dr Semir Poturak<br><span class="sr-only i18n">Autori rada. Predaju na Univerzitetu Union – Nikola Tesla, gde se održava i konferencija kojoj se rad nudi; rad ne nastupa u ime ustanove i ustanova nije njegov nosilac ni naručilac.</span><span class="en-only i18n">Authors of the work. They teach at University Union – Nikola Tesla, where the conference the work is offered to is also held; the work does not act in the institution’s name and the institution is neither its owner nor its commissioner.</span><span class="zh-only">本作品的作者。他们任教于 Union – Nikola Tesla 大学，本作品所投的会议也在该校举行；本作品不以该机构的名义行事，该机构既非其所有者，也非其委托方。</span><span class="de-only">Die Autoren der Arbeit. Sie lehren an der Universität Union – Nikola Tesla, an der auch die Konferenz stattfindet, der die Arbeit angeboten wird; die Arbeit tritt nicht im Namen der Institution auf, und die Institution ist weder ihre Trägerin noch ihre Auftraggeberin.</span><br><a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a></div>
    <div><b><span class="sr-only i18n">Licenca</span><span class="en-only i18n">Licence</span><span class="zh-only">许可协议</span><span class="de-only">Lizenz</span></b><span class="sr-only i18n">MIT za kod, CC BY 4.0 za dokumente i registre. Vrednosti zadržavaju licencu svog izvora.</span><span class="en-only i18n">MIT for code, CC BY 4.0 for documents and registries. Values keep their source's licence.</span><span class="zh-only">代码采用 MIT，文档与登记册采用 CC BY 4.0。数值保留其来源的许可。</span><span class="de-only">MIT für den Code, CC BY 4.0 für Dokumente und Register. Die Werte behalten die Lizenz ihrer Quelle.</span></div>
    <div><b><span class="sr-only i18n">Šta ovo nije</span><span class="en-only i18n">What this is not</span><span class="zh-only">这不是什么</span><span class="de-only">Was das nicht ist</span></b><span class="sr-only i18n">Nije digitalni blizanac, nije „pametni grad", nije nadzor. Nema podataka o pojedincima, nema kamera, nema ulica kao jedinice analize.</span><span class="en-only i18n">Not a digital twin, not a smart city, not surveillance. No person-level data, no cameras, no street as a unit of analysis.</span><span class="zh-only">不是数字孪生，不是“智慧城市”，也不是监控。没有个人层面的数据，没有摄像头，不把街道作为分析单位。</span><span class="de-only">Kein digitaler Zwilling, keine „Smart City“, keine Überwachung. Keine personenbezogenen Daten, keine Kameras, keine Straße als Analyseeinheit.</span></div>
    <div><b><span class="sr-only i18n">Gde ovo stoji</span><span class="en-only i18n">Where this runs</span><span class="zh-only">它运行在哪里</span><span class="de-only">Wo das läuft</span></b><span class="sr-only i18n">Prikupljanje i ceo zapis rade na sopstvenom računaru autora, u Srbiji. Objavljena stranica i otvoreni kod stoje na GitHub-u (GitHub Pages) — dakle na serverima van Srbije. Sačuvani dokazi o dozvolama, tuđe stranice, nikada ne napuštaju taj računar.</span><span class="en-only i18n">The collection and the whole record run on the authors' own computer, in Serbia. The published page and the open code are on GitHub (GitHub Pages) — that is, on servers outside Serbia. The stored permission evidence, which is other people's pages, never leaves that computer.</span><span class="zh-only">采集与全部记录运行在作者自己的计算机上，位于塞尔维亚。已发布的页面与开源代码托管在 GitHub（GitHub Pages）上，也就是塞尔维亚境外的服务器。保存下来的许可证据——他人的页面——从不离开那台计算机。</span><span class="de-only">Die Erhebung und der gesamte Datenbestand laufen auf dem eigenen Rechner der Autoren, in Serbien. Die veröffentlichte Seite und der offene Code liegen auf GitHub (GitHub Pages) — also auf Servern außerhalb Serbiens. Die gespeicherten Erlaubnisnachweise, fremde Seiten, verlassen diesen Rechner nie.</span></div>
    <div><b><span class="sr-only i18n">Stanje</span><span class="en-only i18n">State</span><span class="zh-only">状态</span><span class="de-only">Stand</span></b><span class="mono" id="built"></span></div>
  </div>
</footer>

<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
'use strict';
var D=JSON.parse(document.getElementById('data').textContent);
var LANG='sr';
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c];});}
function T(sr,en){return LANG==='sr'?sr:en;}

// ---- live bar --------------------------------------------------------
function age(sec){ if(sec==null) return T('nema prijema','no reception');
  if(sec<90) return T('pre '+sec+' s','+'+sec+'s ago'.replace('+',''));
  if(sec<5400) return T('pre '+Math.round(sec/60)+' min',Math.round(sec/60)+' min ago');
  if(sec<172800) return T('pre '+Math.round(sec/3600)+' h',Math.round(sec/3600)+' h ago');
  return T('pre '+Math.round(sec/86400)+' d',Math.round(sec/86400)+' d ago'); }
function live(){
  var g=document.getElementById('lgrid'); g.innerHTML='';
  (D.live.sources||[]).forEach(function(s){
    var cells=(s.quorum||'').slice(-48).split('').map(function(c){return '<i class="'+(c==='#'?'f':c==='x'?'x':'')+'"></i>';}).join('');
    var n=s.rows||s.events||0, unt=(s.time||'').toUpperCase().indexOf('NO')===0;
    g.insertAdjacentHTML('beforeend','<div class="lcell"><div class="sid">'+esc(s.sid)+' · '+(s.cadence?Math.round(s.cadence/60)+' min':'')+'</div>'+
      '<div class="nm">'+esc(shortName(s.name))+'</div>'+
      '<div class="big '+(n?(unt?'unt':'sig'):'')+'">'+(n?n.toLocaleString('sr-RS'):'—')+'</div>'+
      '<div class="meta">'+esc(age(s.age))+' · '+(s.captured||0)+'/'+(s.expected||0)+' '+T('prijema','receptions')+(unt?' · '+T('vreme nepoznato','time unknown'):'')+'</div>'+
      '<div class="q">'+cells+'</div></div>');
  });
  document.getElementById('asof').textContent=(D.live.as_of||'').slice(0,19).replace('T',' ')+' UTC';
}
function shortName(n){return String(n||'').replace(/ - .*$/,'').replace(/ citizen sensors.*$/,'').replace(/\(.*?\)/,'').trim();}

// ---- collectors + organs ---------------------------------------------
function chips(){
  var c=document.getElementById('collectors'); c.innerHTML='';
  D.collectors.forEach(function(s){
    c.insertAdjacentHTML('beforeend','<p style="margin:0 0 6px;font-size:13.5px"><span class="mono" style="color:var(--ink55)">'+esc(s.sid)+'</span> '+esc(shortName(s.name))+
      ' <span class="mono" style="color:var(--ink55)">· '+(s.cadence?Math.round(s.cadence/60)+' min':'')+(s.enabled?'':' · '+T('isključen','disabled'))+'</span></p>');
  });
  var o=document.getElementById('organs'); o.innerHTML='';
  D.organs.forEach(function(x){
    o.insertAdjacentHTML('beforeend','<p style="margin:0 0 6px;font-size:13.5px"><span class="mono" style="color:var(--ink55)">'+esc(x.id)+'</span> — '+
      esc((x.status||'').split(';')[0])+'</p>');
  });
}

// ---- registry table ---------------------------------------------------
var active=null;
function stats(){
  var s=document.getElementById('rstats'); s.innerHTML='';
  var order=[['collected',T('sakupljeno','collected'),0],['probe_ok',T('sondirano','probed'),0],['lead',T('trag','lead'),0],
             ['opted_out',T('odbili','refused'),1],['no_coverage',T('nema za Beograd','no coverage'),1],['dead',T('mrtvo','dead'),1],
             ['account_required',T('traži nalog','account'),1],['blocked',T('blokirano','blocked'),1]];
  s.insertAdjacentHTML('beforeend','<div class="stat"><div class="n">'+D.registry.rows.length+'</div><div class="l">'+T('zapisa u registru','records in the registry')+'</div></div>');
  order.forEach(function(o){ var n=D.registry.counts[o[0]]||0; if(!n) return;
    s.insertAdjacentHTML('beforeend','<div class="stat'+(o[2]?' warn':'')+'"><div class="n">'+n+'</div><div class="l">'+esc(o[1])+'</div></div>'); });
  var ch=document.getElementById('chips'); ch.innerHTML='';
  Object.keys(D.registry.counts).sort(function(a,b){return D.registry.counts[b]-D.registry.counts[a];}).forEach(function(k){
    ch.insertAdjacentHTML('beforeend','<span class="chip" role="button" tabindex="0" data-st="'+esc(k)+'" aria-pressed="false">'+esc(k)+' '+D.registry.counts[k]+'</span>');
  });
  Array.prototype.forEach.call(ch.querySelectorAll('.chip'),function(el){
    function go(){ active=(active===el.dataset.st)?null:el.dataset.st;
      Array.prototype.forEach.call(ch.querySelectorAll('.chip'),function(x){x.setAttribute('aria-pressed',String(x.dataset.st===active));}); filter(); }
    el.addEventListener('click',go);
    el.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}});
  });
}
function rows(){
  var tb=document.querySelector('#rtable tbody'); tb.innerHTML='';
  D.registry.rows.forEach(function(r){
    var good=['collected','probe_ok','primary_page','lead'].indexOf(r.status)>=0;
    var unknown=/no measurement|none|unknown|not published|NO -/i.test(r.time)||!r.time;
    tb.insertAdjacentHTML('beforeend','<tr data-st="'+esc(r.status)+'" data-t="'+esc((r.id+' '+r.name+' '+r.theme+' '+r.status+' '+r.url).toLowerCase())+'">'+
      '<td class="id">'+esc(r.id)+'</td>'+
      '<td>'+(r.url?'<a href="'+esc(r.url)+'" rel="noopener">'+esc(r.name)+'</a>':esc(r.name))+
        '<div class="mono" style="font-size:11px;color:var(--ink55)">'+esc(r.theme)+'</div></td>'+
      '<td class="st"><span class="badge '+(good?'ok':'no')+'">'+esc(r.status)+'</span></td>'+
      '<td style="color:var(--ink70);font-size:12.5px">'+esc(r.rhythm)+'</td>'+
      '<td style="color:'+(unknown?'var(--state)':'var(--ink70)')+';font-size:12.5px">'+esc(r.time||T('nije objavljeno','not published'))+'</td></tr>');
  });
}
function filter(){
  var q=(document.getElementById('q').value||'').toLowerCase().trim(), n=0;
  Array.prototype.forEach.call(document.querySelectorAll('#rtable tbody tr'),function(tr){
    var ok=(!q||tr.dataset.t.indexOf(q)>=0)&&(!active||tr.dataset.st===active);
    tr.className=ok?'':'hide'; if(ok)n++;
  });
  document.getElementById('rcount').textContent=n+' / '+D.registry.rows.length+' '+T('zapisa','records');
}

// ---- permissions + corrections ----------------------------------------
function prov(){
  var p=D.provenance.nums, s=document.getElementById('pstats'); s.innerHTML='';
  [[p.sources,T('izvora sa dokazom','sources with evidence'),0],[p.captures,T('hvatanja','captures'),0],
   [p.passed,T('provera prošlo','checks passed'),0],[p.refused,T('odbijeno','refused'),1],
   [p.undecided,T('čeka odluku','awaiting decision'),1],[p.incomplete,T('nepotpun dokaz','incomplete'),1],
   [p.undocumented,T('još bez dokaza','not yet documented'),1]].forEach(function(x){
    if(x[0]==null) return;
    s.insertAdjacentHTML('beforeend','<div class="stat'+(x[2]?' warn':'')+'"><div class="n">'+x[0]+'</div><div class="l">'+esc(x[1])+'</div></div>');
  });
  var tb=document.getElementById('refused'); tb.innerHTML='';
  D.provenance.refused.forEach(function(r){
    tb.insertAdjacentHTML('beforeend','<tr><td class="id">'+esc(r.id)+'</td><td>'+esc(r.source)+'</td><td style="color:var(--ink70);font-size:12.5px">'+esc(r.said)+'</td></tr>');
  });
}
function corr(){
  var c=document.getElementById('corr'); c.innerHTML='';
  D.corrections.slice().reverse().forEach(function(x){
    c.insertAdjacentHTML('beforeend','<article><h3><span>'+esc(x.id)+'</span>'+esc(x.title)+'</h3>'+
      (x.said?'<p><b>'+T('Reklo je','It said')+':</b> '+esc(x.said)+'</p>':'')+
      (x.true?'<p><b>'+T('Istina je bila','What was true')+':</b> '+esc(x.true)+'</p>':'')+
      (x.rule?'<p><b>'+T('Pravilo','Rule')+':</b> '+esc(x.rule)+'</p>':'')+'</article>');
  });
}

function render(){ live(); chips(); stats(); rows(); filter(); prov(); corr();
  document.getElementById('built').textContent=D.built+' UTC · '+D.registry.rows.length+' '+T('izvora','sources'); }
// Four buttons, one meaning: which language the page speaks in its own voice. Serbian and English
// also switch the generated tables, because those exist in two languages. Chinese and German sit on
// top of English - the body carries lang-en as well, so anything without a translation reads as
// English instead of vanishing, which is the only honest failure mode for a partial translation.
(function theme(){
  var b=document.getElementById('theme'); if(!b) return;
  var ORDER=['','light','dark'], MARK={'':'\u25d0','light':'\u25cb','dark':'\u25cf'};
  function read(){ try{ return localStorage.getItem('beops-theme')||''; }catch(e){ return ''; } }
  function tell(){
    var t=document.documentElement.getAttribute('data-theme')||'';
    document.querySelectorAll('iframe').forEach(function(f){
      try{ if(f.contentWindow) f.contentWindow.postMessage({beopsTheme:t},'*'); }catch(e){}
    });
  }
  function apply(v){
    if(v) document.documentElement.setAttribute('data-theme',v);
    else document.documentElement.removeAttribute('data-theme');
    b.textContent=MARK[v]; b.setAttribute('aria-pressed',String(!!v));
    b.title=(v===''?'Prati mašinu \u00b7 follow the machine':(v==='light'?'Svetlo \u00b7 light':'Tamno \u00b7 dark'));
    try{ localStorage.setItem('beops-theme',v); }catch(e){}
    tell();
  }
  apply(read());
  b.addEventListener('click',function(){ apply(ORDER[(ORDER.indexOf(read())+1)%3]); });
  // a frame that loads later has to be told too
  document.querySelectorAll('iframe').forEach(function(f){ f.addEventListener('load',tell); });
  // ...and one that loads later still, or that installed its listener after the broadcast, ASKS.
  // C-039: the load event is the parent's idea of when a frame is ready; only the frame knows.
  window.addEventListener('message',function(ev){
    var d=ev&&ev.data; if(!d||!d.beopsAsk) return;
    var t=document.documentElement.getAttribute('data-theme')||'';
    var l=(document.body.className.match(/lang-([a-z]{2})(?!.*lang-)/)||[])[1]||'';
    try{ ev.source.postMessage({beopsTheme:t, beopsLang:(LANG||'sr'), beopsLang4:(l||'sr')},'*'); }catch(e){}
  });
})();
(function language(){
  var box=document.getElementById('lang'); if(!box) return;
  var btns=box.querySelectorAll('button');
  function apply(l){
    LANG=(l==='sr')?'sr':'en';                       // the generated half only knows two
    document.body.className=(l==='sr'||l==='en')?('lang-'+l):('lang-en lang-'+l);
    document.documentElement.lang=l;
    btns.forEach(function(o){ o.setAttribute('aria-pressed', String(o.getAttribute('data-l')===l)); });
    var bar=document.getElementById('sta');
    if(bar){
      bar.classList.remove('what-sr','what-en','what-zh','what-de');
      bar.classList.add('what-'+l);
      bar.querySelectorAll('.wlangs button').forEach(function(o){
        o.setAttribute('aria-pressed', String(o.getAttribute('data-w')===l)); });
    }
    render();
    // every embedded study, not a hand-kept list of two: the ribbon was added and stayed Serbian on
    // the English page. The frames speak two languages, so they are told the two-language answer.
    document.querySelectorAll('iframe').forEach(function(f){
      try{ if(f.contentWindow) f.contentWindow.postMessage({beopsLang:LANG,beopsLang4:l,beopsTheme:document.documentElement.getAttribute('data-theme')||''},'*'); }catch(err){}
    });
  }
  btns.forEach(function(b){ b.addEventListener('click',function(){ apply(b.getAttribute('data-l')); }); });
})();
// A frame that carries a document (the data view, the ribbon) reports its height and is made exactly
// that tall, so the page has one scrollbar instead of three. The monologue is a feed and keeps its own.
addEventListener('message',function(ev){
  var d=ev.data; if(!d||d.beops!=='height'||!d.h||d.h>20000) return;   // a runaway frame is ignored, not obeyed
  var fr=document.querySelectorAll('iframe');
  for(var i=0;i<fr.length;i++) if(fr[i].contentWindow===ev.source){
    var box=fr[i].parentElement; box.classList.add('fit'); box.style.height=(d.h+2)+'px';
  }
});

// The four front-door answers carry their own language switch: Serbian, English, Chinese and German.
// It is separate from the page's SR/EN switch on purpose - the generated tables below exist in two
// languages only, and pretending otherwise would be the kind of claim this page is against.
(function whatIsThis(){
  var bar=document.getElementById('sta'); if(!bar) return;
  var btns=bar.querySelectorAll('.wlangs button');
  btns.forEach(function(b){
    b.addEventListener('click',function(){
      var w=b.getAttribute('data-w');
      bar.classList.remove('what-sr','what-en','what-zh','what-de');
      bar.classList.add('what-'+w);
      btns.forEach(function(o){ o.setAttribute('aria-pressed', String(o===b)); });
    });
  });
  bar.classList.add('what-sr');
})();

// Related work: rendered from research/RELATED_WORK.json, so no citation can appear here
// that is not in the register a reader can clone.
(function relatedWork(){
  var box=document.getElementById('related'); if(!box||!D.related) return;
  var kindName={project:[ 'Srodni projekat','Related project'],standard:['Standard','Standard'],work:['Rad','Work']};
  (D.related.entries||[]).forEach(function(e){
    var k=kindName[e.kind]||['',''];
    box.insertAdjacentHTML('beforeend',
      '<div class="rw"><div class="k">'+esc(e.id)+' · '+T(k[0],k[1])+'</div>'+
      '<h3><a href="'+esc(e.url)+'" rel="noopener">'+esc(e.name)+'</a></h3>'+
      '<p>'+esc(T(e.what_sr,e.what_en))+'</p>'+
      '<p class="takes">'+T('uzima','takes')+': '+esc(T(e.takes_sr,e.takes_en))+'</p></div>');
  });
})();

// Each part can be folded away: its heading gets a button, the rest of the part hides.
(function fold(){
  var ids=['sta','zivo','podaci','slojevi','kako','izvori','srodno','dozvole','greske','kontakt','citaj'];
  var OPEN_ON_ARRIVAL=['sta','slojevi'];   // the answer to "what is this" and the drawing that
                                   // explains the rest; the live interface at the
                                   // top of the page does not fold at all
  var opener={};
  ids.forEach(function(id){
    var sec=document.getElementById(id); if(!sec) return;
    var w=sec.querySelector('.wrap'); if(!w) return;
    var kids=[].slice.call(w.children);
    var hi=-1; for(var i=0;i<kids.length;i++){ if(kids[i].tagName==='H2'||kids[i].querySelector('h2')){ hi=i; break; } }
    if(hi<0) return;
    var body=document.createElement('div'); body.className='secbody';
    kids.slice(hi+1).forEach(function(k){ body.appendChild(k); });
    w.appendChild(body);
    var b=document.createElement('button'); b.type='button'; b.className='fold'; b.textContent='\u25be';
    b.setAttribute('aria-expanded','true');
    b.setAttribute('aria-label','Skupi / razvij · Fold / unfold');
    function setFolded(folded){
      sec.classList.toggle('folded',folded);
      b.textContent=folded?'\u25b8':'\u25be';
      b.setAttribute('aria-expanded',String(!folded));
      if(!folded){
        // A frame inside a display:none section never measured itself; a resize makes it report.
        var fr=sec.querySelectorAll('iframe');
        setTimeout(function(){ for(var i=0;i<fr.length;i++){ try{ fr[i].contentWindow.dispatchEvent(new Event('resize')); }catch(e){} } },60);
      }
    }
    b.addEventListener('click',function(){ setFolded(!sec.classList.contains('folded')); });
    var head=kids[hi];
    var row=(head.tagName==='H2'?head.parentElement:head);
    row.appendChild(b);
    // The heading row is the door. Anything in it that is itself a control keeps its own click.
    row.style.cursor='pointer';
    row.addEventListener('click',function(ev){
      if(ev.target.closest && ev.target.closest('button,a,input,select')) return;
      setFolded(!sec.classList.contains('folded'));
    });
    // OPEN_ON_ARRIVAL: the page opens as a list of its parts, with the live one running.
    if(OPEN_ON_ARRIVAL.indexOf(id)<0) setFolded(true);
    opener[id]=setFolded;
  });
  function openHash(){
    var id=(location.hash||'').replace('#','');
    if(id && opener[id]) opener[id](false);
  }
  addEventListener('hashchange',openHash);
  openHash();
})();

document.getElementById('q').addEventListener('input',filter);
render();
})();
</script>
</body>
</html>
"""

def main() -> int:
    data = {
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "registry": registry(),
        "provenance": provenance(),
        "corrections": corrections(),
        "collectors": collectors(),
        "organs": organs(),
        "live": live(),
        "related": related(),
    }
    DOCS.mkdir(parents=True, exist_ok=True)
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</script>", "<\\/script>"))
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from make_layers import build as _layers_build, counts as _layers_counts  # noqa: PLC0415
        _c = _layers_counts()
        (ROOT / "research" / "05-design" / "studies" / "slojevi.svg").write_text(_layers_build(_c, False), encoding="utf-8")
        layers_svg = _layers_build(_c, True)   # the page shows the small rendering; the link opens the full drawing
    except Exception as e:  # noqa: BLE001
        layers_svg = f"<!-- layers drawing unavailable: {type(e).__name__} -->"
    html = html.replace("__LAYERS_SVG__", layers_svg)
    cb = data["related"]["claim"]
    for key, ph in (("problem_sr", "__PROB_SR__"), ("problem_en", "__PROB_EN__"),
                    ("standard_sr", "__STD_SR__"), ("standard_en", "__STD_EN__"),
                    ("ours_sr", "__OURS_SR__"), ("ours_en", "__OURS_EN__"),
                    ("not_sr", "__NOT_SR__"), ("not_en", "__NOT_EN__")):
        html = html.replace(ph, cb.get(key, ""))   # the claim boundary is a register entry, not page copy
    html = html.replace("{stamp}", data["built"].replace(" ", "T").replace(":", "").replace("-", ""))   # the stage frame: a browser that cached yesterday's monolog.html must not show it today
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    for src, dst in [("research/05-design/studies/monolog-puls.html", "monolog.html"),
                     ("research/05-design/studies/podaci.html", "podaci.html"),
                     ("research/05-design/studies/sada.html", "sada.html"),
                     ("research/05-design/studies/slojevi.svg", "slojevi.svg"),
                     ("research/05-design/studies/traka-live.html", "traka.html"),
                     ("public/live-snapshot.json", "live-snapshot.json"),
                     ("public/history.json", "history.json"),
                     ("public/basemap-belgrade.json", "basemap-belgrade.json"),
                     ("public/context-population.json", "context-population.json"),
                     ("public/watch.json", "watch.json")]:
        p = ROOT / src
        if p.exists():
            shutil.copy(p, DOCS / dst)
    # A document reaches the site by existing rather than by being listed - except the kinds that
    # are internal by policy. Working documents, letters and programme notes are not published;
    # research/test_public_docs.py holds this, because the first version of this loop published
    # two working documents by accident (C-018).
    # C-018 named a rule and then implemented it by listing the two documents that had just leaked.
    # C-020 is what that cost: three more internal PDFs were public, one of them a pre-paper, which
    # the project's own publish notice names as internal in so many words. So the deny-list names
    # CATEGORIES now. And publication is recomputed on every build rather than accumulated: a build
    # that can only add is a build whose mistakes are permanent, which is how two of those three
    # stayed up after their source files were gone.
    NOT_PUBLIC = ("WORKING_DOCUMENT", "PISMA", "LETTER", "INTERNAL", "DRAFT", "PRESEK",
                  "PRE_PAPER", "PREPAPER", "PRED_RAD", "ANALYSIS", "AUDIT", "ATLAS",
                  "STRUKTURA", "METODOLOGIJA", "SCRATCH", "NOTES")
    published = set()
    for folder in ("06-paper", "07-legal"):
        for p in sorted((ROOT / "research" / folder).glob("*.pdf")):
            if any(k in p.name.upper() for k in NOT_PUBLIC):
                continue
            shutil.copy(p, DOCS / p.name)
            published.add(p.name)
    for p in sorted(DOCS.glob("*.pdf")):
        if p.name not in published:
            p.unlink()
            print("withdrew docs/" + p.name + " - not eligible for publication")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"wrote {DOCS/'index.html'} ({len(html)} bytes; {len(data['registry']['rows'])} sources, "
          f"{len(data['corrections'])} corrections, {len(data['provenance']['refused'])} refusals)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
