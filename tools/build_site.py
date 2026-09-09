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
html{scroll-behavior:smooth}
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
.hbar{display:flex;align-items:center;gap:calc(var(--u)*4);padding:calc(var(--u)*3) 0;flex-wrap:wrap}
.brand{font-weight:700;letter-spacing:-.01em;font-size:17px;border:0;white-space:nowrap;flex:none}
.brand span{font-weight:400;color:var(--ink55)}
nav{display:flex;gap:calc(var(--u)*4);margin-left:auto;flex-wrap:wrap;font-size:14px;color:var(--ink70)}
nav a{border:0;padding:2px 0;border-bottom:1px solid transparent}
nav a:hover{border-bottom-color:var(--signal)}
button{font:inherit;font-size:13px;color:var(--ink);background:transparent;border:1px solid var(--ink30);
  padding:3px 10px;border-radius:3px;cursor:pointer;transition:background .15s}
button:hover{background:var(--ink06)}
button[aria-pressed="true"]{background:var(--ink);color:var(--field);border-color:var(--ink)}

.hero{padding:calc(var(--u)*8) 0 calc(var(--u)*6)}
.herohead{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:calc(var(--u)*8);align-items:end;margin-bottom:calc(var(--u)*6)}
.stage{position:relative;width:100%;margin:0 auto;height:min(92vh,1040px);border:1px solid var(--ink12);border-radius:6px;overflow:hidden;background:var(--field);box-shadow:0 30px 60px -40px rgba(17,19,17,.5)}
.stage iframe{width:100%;height:100%;border:0;display:block;background:var(--field)}
.stagelink{position:absolute;right:12px;top:10px;font-size:12px;padding:4px 10px;border:1px solid var(--ink30);border-radius:3px;background:color-mix(in srgb,var(--field) 85%,transparent);backdrop-filter:blur(8px)}
.hero .authors{margin-top:calc(var(--u)*3);margin-bottom:0}
@media (max-width:900px){
  .herohead{grid-template-columns:1fr;gap:calc(var(--u)*3)}
  .hero{padding:calc(var(--u)*5) 0 calc(var(--u)*4)}
  .stage{height:min(92vh,860px);width:100%}
  .hbar{gap:calc(var(--u)*2);padding:calc(var(--u)*2) 0;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}
  .hbar::-webkit-scrollbar{display:none}
  nav{flex-wrap:nowrap;gap:calc(var(--u)*3);font-size:13px;margin-left:auto}
  nav a{white-space:nowrap}
  button#lang{flex:none}
  .brand span{display:none}
  .stagelink{top:auto;bottom:10px}
}
/* the header on a phone: two tidy rows - the name and the language on the first, every section on the
   second. Everything fits at 360 px: nothing scrolls sideways and nothing has to be zoomed to be tapped. */
@media (max-width:760px){
  .hbar{flex-wrap:wrap;overflow:visible;row-gap:calc(var(--u)*1.5);column-gap:calc(var(--u)*3);padding:calc(var(--u)*1.5) 0}
  .brand{font-size:16px;flex:0 0 auto}
  button#lang{margin-left:auto;flex:none;padding:3px 8px}
  nav{order:3;flex:1 0 100%;margin-left:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
      column-gap:calc(var(--u)*2);row-gap:calc(var(--u)*1.5);font-size:12.5px;text-align:center}
  nav a{white-space:nowrap;padding:3px 0;min-height:26px;display:flex;align-items:center;justify-content:center}
  [id]{scroll-margin-top:104px}
}
@media (max-width:390px){ nav{font-size:11.5px;column-gap:calc(var(--u)*1)} .brand{font-size:15px} }
.hero .kicker{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--signal);font-weight:600;margin-bottom:calc(var(--u)*4)}
.hero h1{font-size:clamp(26px,3.6vw,44px);line-height:1.06;margin:0 0 calc(var(--u)*5);font-weight:600;letter-spacing:-.02em;max-width:20ch;text-wrap:balance}
.hero h1 em{font-style:normal;color:var(--signal)}
.hero .sub{font-size:clamp(16px,1.5vw,19px);color:var(--ink70);max-width:62ch;margin:0 0 calc(var(--u)*6)}
.authors{font-size:14px;color:var(--ink55);max-width:70ch}
.authors b{color:var(--ink);font-weight:600}

.databar{border-bottom:1px solid var(--ink12);padding:calc(var(--u)*8) 0}
.layersbar{border-bottom:1px solid var(--ink12);padding:calc(var(--u)*8) 0}
.layers{max-width:820px;margin:0 auto}
.layers svg{width:100%;height:auto;display:block}
.layerlink{display:block;text-align:center;font-size:12px;color:var(--ink55);margin-top:calc(var(--u)*3)}
.folded .secbody{display:none}
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
@media (prefers-reduced-motion: reduce){html{scroll-behavior:auto}*{transition:none!important}}
</style>
</head>
<body class="lang-sr">
<header>
  <div class="wrap hbar">
    <a class="brand" href="#top">BEOPS <span>· Beograd</span></a>
    <nav>
      <a href="#sta"><span class="sr-only">Šta je ovo</span><span class="en-only">What this is</span></a>
      <a href="#zivo"><span class="sr-only">Uživo</span><span class="en-only">Live</span></a>
      <a href="#podaci"><span class="sr-only">Podaci</span><span class="en-only">Data</span></a>
      <a href="#slojevi"><span class="sr-only">Slojevi</span><span class="en-only">Layers</span></a>
      <a href="#kako"><span class="sr-only">Kako radi</span><span class="en-only">How it works</span></a>
      <a href="#izvori"><span class="sr-only">Izvori</span><span class="en-only">Sources</span></a>
      <a href="#srodno"><span class="sr-only">Srodno</span><span class="en-only">Related</span></a>
      <a href="#dozvole"><span class="sr-only">Dozvole</span><span class="en-only">Permissions</span></a>
      <a href="#greske"><span class="sr-only">Greške</span><span class="en-only">Corrections</span></a>
    </nav>
    <button id="lang" aria-pressed="false" title="Jezik / Language">SR / EN</button>
  </div>
</header>

<div id="top" class="hero">
  <div class="wrap herohead">
    <div>
      <div class="kicker"><span class="sr-only">Naučni rad za konferenciju „Creating sustainable commUNiTy“ · Univerzitet Union – Nikola Tesla, 2026</span><span class="en-only">A scientific paper for the conference “Creating sustainable commUNiTy” · University Union – Nikola Tesla, 2026</span></div>
      <h1><span class="sr-only">Ovo je ono što nam je Beograd rekao, kad nam je rekao, i <em>gde je zaćutao</em>.</span><span class="en-only">This is what Belgrade told us, when it told us, and <em>where it went quiet</em>.</span></h1>
      <p class="authors"><b>prof. dr Darinka Golubović Matić</b> · <b>doc. dr Semir Poturak</b> — autori rada; nastavnici Univerziteta Union – Nikola Tesla u Beogradu, ali rad ne nastupa u ime ustanove · <span class="sr-only">sa <b>Svemirom</b>, lokalnom AI infrastrukturom autora (Claude, Anthropic) — proveren saradnik, ne autor</span><span class="en-only">with <b>Svemir</b>, the authors' local AI infrastructure (Claude, Anthropic) — a verified contributor, not an author</span></p>
    </div>
    <p class="sub"><span class="sr-only">Grad govori u prijemima; mapa kruži samo kad je instrument stvarno pročitan; um od malih lokalnih modela razmišlja naglas i svaka njegova rečenica se proverava pre nego što je vidiš. Ono čega nema je zapis — nikada nula.</span><span class="en-only">The city speaks in receptions; the map pulses only when an instrument was actually read; a mind of small local models thinks aloud and every sentence is checked before you see it. What is missing is a record — never a zero.</span></p>
  </div>
  <div class="wrap">
    <div class="stage">
      <iframe id="stage" src="monolog.html?v={stamp}" title="BEOPS · Monolog + Puls" loading="eager"></iframe>
    </div>
  </div>
</div>

<div class="airbar" id="vazduhbar">
  <div class="wrap">
    <h2 class="barhead"><span class="sr-only">Vazduh — državna mreža, poslednji sat</span><span class="en-only">Air — the state network, the last hour</span></h2>
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
    <p class="wnote"><span class="w-sr">Ova četiri odgovora postoje na srpskom, engleskom, kineskom i nemačkom. Ostatak stranice je dvojezičan, srpski i engleski, jer se generiše iz registara koji se menjaju svakih nekoliko minuta.</span><span class="w-en">These four answers exist in Serbian, English, Chinese and German. The rest of the page is bilingual, Serbian and English, because it is generated from registers that change every few minutes.</span><span class="w-zh">以上四个回答提供塞尔维亚语、英语、中文和德语版本。本页其余部分为塞尔维亚语和英语双语，因为它由每隔几分钟变动一次的登记册生成。</span><span class="w-de">Diese vier Antworten gibt es auf Serbisch, Englisch, Chinesisch und Deutsch. Der übrige Teil der Seite ist zweisprachig, Serbisch und Englisch, weil er aus Registern erzeugt wird, die sich alle paar Minuten ändern.</span></p>
  </div>
</div>

<div class="databar" id="podaci">
  <div class="wrap">
    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:12px">
      <h2 style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink55);margin:0;font-weight:600"><span class="sr-only">Podaci — šta smo izmerili, po stanici i na mapi</span><span class="en-only">Data — what was measured, per station and on the map</span></h2>
      <a class="stagelink" style="position:static" href="podaci.html?v={stamp}"><span class="sr-only">Otvori sve podatke ↗</span><span class="en-only">Open all the data ↗</span></a>
    </div>
    <div class="datastage"><iframe id="datastage" src="podaci.html?v={stamp}" title="BEOPS · Podaci" loading="lazy"></iframe></div>
    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap;margin:28px 0 12px">
      <h2 style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink55);margin:0;font-weight:600"><span class="sr-only">Traka — vreme kao glavni predmet, jedna traka po čulu</span><span class="en-only">The ribbon — time as the primary object, one lane per sense</span></h2>
      
    </div>
    <div class="datastage trakastage"><iframe id="trakastage" src="traka.html?v={stamp}" title="BEOPS · Traka" loading="lazy"></iframe></div>
    <p class="mono" style="font-size:11.5px;color:var(--ink55);margin:12px 0 0"><span class="sr-only">Oznaka postoji samo tamo gde red postoji; prazno mesto je tišina, ne nula.</span><span class="en-only">A mark exists only where a row exists; an empty place is silence, not a zero.</span></p>
  </div>
</div>

<div class="layersbar" id="slojevi">
  <div class="wrap">
    <h2 style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink55);margin:0 0 6px;font-weight:600"><span class="sr-only">Slojevi — od čega je opservatorija napravljena</span><span class="en-only">Layers — what the observatory is made of</span></h2>
    <p class="sub" style="margin:0 0 16px;max-width:80ch"><span class="sr-only">Na dnu je zakon — srpski i evropski — i on nosi sve ostalo: sloj postoji samo ako je propušten kroz kapiju dozvole. Iznad njega: podloga grada, statični slojevi, periodični izvori, živa čula, sistem koji organizuje, sistem koji misli i govori, i izraz; znanje stoji pored njih i takođe stoji na zakonu. Brojevi u crtežu se čitaju iz registara pri svakoj objavi.</span><span class="en-only">At the bottom is the law — Serbian and European — and it carries everything else: a layer exists only if it passed the permission gate. Above it: the city's ground, static layers, periodic sources, live senses, the system that organizes, the system that thinks and speaks, and expression; the knowledge stands beside them and on the same slab. The numbers in the drawing are read from the registers at every publish.</span></p>
    <div class="layers">__LAYERS_SVG__</div>
    
  </div>
</div>

<div class="livebar" id="zivo">
  <div class="wrap">
    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:16px">
      <h2 style="font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink55);margin:0;font-weight:600"><span class="sr-only">Poslednji prijem po izvoru</span><span class="en-only">Last reception per source</span></h2>
      <span class="mono" style="font-size:12px;color:var(--ink55)" id="asof"></span>
    </div>
    <div class="lgrid" id="lgrid"></div>
    <p class="mono" style="font-size:11.5px;color:var(--ink55);margin:16px 0 0"><span class="sr-only">Popunjena ćelija = prijem u tom taktu; prazna = tišina. Prijem nije merenje.</span><span class="en-only">A filled cell is a reception in that slot; an empty one is silence. A reception is not a measurement.</span></p>
  </div>
</div>

<section id="kako">
  <div class="wrap">
    <h2><span class="sr-only">Kako ovo radi</span><span class="en-only">How this works</span></h2>
    <p class="lede"><span class="sr-only">Jedan računar autora, jedan zakazani zadatak na svakih pet minuta, i pravila koja se ne pregovaraju.</span><span class="en-only">One computer belonging to the authors, one scheduled task every five minutes, and rules that are not negotiable.</span></p>
    <div class="cols">
      <div>
        <h3><span class="sr-only">Dozvola pre kolektora</span><span class="en-only">Permission before collector</span></h3>
        <p><span class="sr-only">Nijedan izvor se ne čita dok njegov <code>robots.txt</code>, zaglavlja i stranica licence ne budu sačuvani kao bajtovi sa hešom. Nepoznato nikada nije dozvola. Predstavljamo se pošteno kao <span class="mono">Beops-Research-Collect/1.0</span> i kad izvor kaže ne — odgovor je ne, i to se zapisuje da niko ne pokuša ponovo.</span><span class="en-only">No source is read until its <code>robots.txt</code>, headers and licence page are stored as bytes with a hash. An unknown is never a permission. We identify honestly as <span class="mono">Beops-Research-Collect/1.0</span>, and when a source says no the answer is no — recorded, so nobody tries again next year.</span></p>
        <h3><span class="sr-only">Tri vremena</span><span class="en-only">Three times</span></h3>
        <p><span class="sr-only">Izmereno, objavljeno, primljeno — nikad se ne stapaju. Neki izvori ne objavljuju vreme merenja uopšte: tada je vrednost tačna, a njena starost nepoznata, i tako se i crta.</span><span class="en-only">Measured, published, received — never collapsed into one. Some sources publish no measurement time at all: then the value is exact and its age is unknown, and it is drawn that way.</span></p>
      </div>
      <div>
        <div class="rule"><b><span class="sr-only">Nema izmišljenog merenja</span><span class="en-only">No invented measurement</span></b><span><span class="sr-only">Broj koji nijedan izvor nije rekao ne postoji. Bez interpolacije, bez popunjavanja.</span><span class="en-only">A number no source reported does not exist. No interpolation, no back-filling.</span></span></div>
        <div class="rule"><b><span class="sr-only">Primljeno nije izmereno</span><span class="en-only">Received is not measured</span></b><span><span class="sr-only">Vreme prijema je naše, ne gradsko.</span><span class="en-only">The reception time is ours, not the city's.</span></span></div>
        <div class="rule"><b><span class="sr-only">Prognoza nije merenje</span><span class="en-only">Forecast is not measurement</span></b><span><span class="sr-only">Procena i prognoza imaju drugi potez i drugu boju — nikad boju merenja.</span><span class="en-only">Estimates and forecasts get a different stroke and never the colour of measurement.</span></span></div>
        <div class="rule"><b><span class="sr-only">Nedostaje nije nula</span><span class="en-only">Missing is not zero</span></b><span><span class="sr-only">Mrtav senzor, izdavač koji je odbio i nikad prikupljen izvor su tri različita zapisa.</span><span class="en-only">A dead sensor, a publisher that refused and a never-collected source are three different records.</span></span></div>
        <div class="rule"><b><span class="sr-only">Svaka tvrdnja nosi izvor, vreme, prostor, jedinicu i dozvolu</span><span class="en-only">Every claim carries source, time, space, unit and permission</span></b><span><span class="sr-only">Dozvola je bajt na disku, ne rečenica.</span><span class="en-only">Permission is bytes on disk, not a sentence.</span></span></div>
      </div>
      <div>
        <h3><span class="sr-only">Šta se sada sakuplja</span><span class="en-only">What is collected now</span></h3>
        <div id="collectors"></div>
        <h3 style="margin-top:20px"><span class="sr-only">Organi — mali lokalni modeli</span><span class="en-only">Organs — small local models</span></h3>
        <div id="organs"></div>
      </div>
    </div>
  </div>
</section>

<section id="izvori">
  <div class="wrap">
    <h2><span class="sr-only">Popis otvorenosti: šta Beograd objavljuje, a šta ne</span><span class="en-only">An audit of openness: what Belgrade publishes, and what it does not</span></h2>
    <p class="lede"><span class="sr-only">Svaki zapis je pristupna ruta sa stanjem i sledećim korakom. Broj zapisa nije broj uređaja niti broj živih tokova — i tu razliku ovaj projekat ne zamagljuje.</span><span class="en-only">Every record is an access route with a state and a next step. The number of records is not a number of devices or of live feeds — and this project does not blur that difference.</span></p>
    <div class="stats" id="rstats"></div>
    <div class="filters">
      <input id="q" type="search" placeholder="pretraga / search" aria-label="search sources">
      <span id="chips"></span>
    </div>
    <div class="tablewrap"><table id="rtable"><thead><tr>
      <th>id</th><th><span class="sr-only">izvor</span><span class="en-only">source</span></th>
      <th><span class="sr-only">stanje</span><span class="en-only">status</span></th>
      <th><span class="sr-only">ritam</span><span class="en-only">rhythm</span></th>
      <th><span class="sr-only">vreme merenja</span><span class="en-only">measurement time</span></th>
    </tr></thead><tbody></tbody></table></div>
    <p class="count" id="rcount"></p>
  </div>
</section>

<section id="dozvole">
  <div class="wrap">
    <h2><span class="sr-only">Dokaz dozvole, i ono što je reklo ne</span><span class="en-only">The proof of permission, and what said no</span></h2>
    <p class="lede"><span class="sr-only">Za svaki izvor čuvamo njegov sopstveni <code>robots.txt</code> kako je poslužen, zaglavlja tačnih adresa koje čitamo, stranicu licence i SHA-256 svakog od njih. Odbijanja se čuvaju sa klauzulom, pa se izvor ne otkriva ponovo za godinu dana i ne počne tiho da se sakuplja.</span><span class="en-only">For every source we store its own <code>robots.txt</code> as served, the headers of the exact URLs we read, the licence page, and a SHA-256 of each. Refusals are kept with their clause, so a source is not rediscovered next year and quietly collected.</span></p>
    <div class="stats" id="pstats"></div>
    <h3 style="font-size:15px;margin:24px 0 8px"><span class="sr-only">Rekli su ne — i to ostaje zapisano</span><span class="en-only">They said no — and it stays recorded</span></h3>
    <div class="tablewrap"><table><thead><tr><th>id</th><th><span class="sr-only">izvor</span><span class="en-only">source</span></th><th><span class="sr-only">šta je reklo ne</span><span class="en-only">what said no</span></th></tr></thead><tbody id="refused"></tbody></table></div>
  </div>
</section>

<section id="greske">
  <div class="wrap">
    <h2><span class="sr-only">Svaki put kad je ovaj sistem rekao nešto neistinito</span><span class="en-only">Every time this system said something untrue</span></h2>
    <p class="lede"><span class="sr-only">Sistem koji krije sopstvene greške ne vredi ništa, jer jedino što treba da dokaže jeste da ne govori tiho neistine. Zato je ovaj spisak javan i dopisuje se, nikad se ne briše.</span><span class="en-only">A system that hides its own failures is worth nothing, because the one thing it must prove is that it does not quietly say untrue things. So this list is public, append-only, and never edited.</span></p>
    <div class="corr" id="corr"></div>
  </div>
</section>

<section id="kontakt">
  <div class="wrap">
    <h2><span class="sr-only">Prigovor i uklanjanje</span><span class="en-only">Objection and removal</span></h2>
    <div class="claimbox">
      <p><span class="sr-only">Ako objavljujete neki od izvora sa ovog spiska i ne želite da ga čitamo, ne treba Vam ni advokat ni obrazac. Jedna poruka je dovoljna: <a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a>. Prestajemo u roku od 24 sata, bez pregovora, i izvor se više ne predlaže. U javnom registru ostaje zapisano da je zatraženo uklanjanje i kada — zapis se dopisuje, ne prepravlja, pa se vidi i šta je bilo prikupljeno pre toga.</span><span class="en-only">If you publish one of the sources on this list and would rather we did not read it, you need no lawyer and no form. One message is enough: <a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a>. We stop within 24 hours, without negotiation, and the source is never proposed again. The public register keeps a line saying that removal was requested and when — the record is appended to, never rewritten, so what was collected before that also stays visible.</span></p>
      <p><span class="sr-only">Isto vredi i za ispravku: ako je nešto ovde netačno, javite i biće ispravljeno, a ispravka će stajati u javnom spisku grešaka sa datumom. Taj spisak se ne briše.</span><span class="en-only">The same holds for a correction: if something here is wrong, tell us and it will be corrected, and the correction will stand in the public list of failures with its date. That list is never deleted.</span></p>
      <p><span class="sr-only">Za pitanja o metodu, pravnom okviru ili saradnji — ista adresa. Odgovaraju autori, ne program.</span><span class="en-only">For questions about the method, the legal frame or collaboration — the same address. The authors answer, not the program.</span></p>
    </div>
  </div>
</section>

<section id="srodno">
  <div class="wrap">
    <h2><span class="sr-only">Srodni radovi, standardi i projekti</span><span class="en-only">Related work, standards and projects</span></h2>
    <p class="sub" style="max-width:80ch"><span class="sr-only">Ovo nije prvi pokušaj da grad govori kroz svoje instrumente. Ovde stoji odakle je šta uzeto, sa linkom na izvor da čitalac ne mora da nam veruje — i, ispod, šta se ovde tvrdi kao novo, a šta ne. Beleška „uzima" govori šta je ovaj projekat uzeo iz tog rada; ne tvrdi da autori znaju za ovaj projekat niti da ga odobravaju.</span><span class="en-only">This is not the first attempt to let a city speak through its instruments. Here is where each idea came from, with a link so the reader need not take our word — and, below, what is claimed as new here and what is not. The "takes" note says what this project took from that work; it does not claim the authors know of this project or endorse it.</span></p>
    <div class="problembox">
      <p><span class="sr-only">__PROB_SR__</span><span class="en-only">__PROB_EN__</span></p>
    </div>
    <div class="claimbox">
      <p><b><span class="sr-only">Standardno, i nimalo novo</span><span class="en-only">Standard, and in no way new</span></b><br><span class="sr-only">__STD_SR__</span><span class="en-only">__STD_EN__</span></p>
      <p><b><span class="sr-only">Ono što ovde jeste drugačije</span><span class="en-only">What is different here</span></b><br><span class="sr-only">__OURS_SR__</span><span class="en-only">__OURS_EN__</span></p>
      <p><b><span class="sr-only">Šta se ne tvrdi</span><span class="en-only">What is not claimed</span></b><br><span class="sr-only">__NOT_SR__</span><span class="en-only">__NOT_EN__</span></p>
    </div>
    <div class="rwgrid" id="related"></div>
  </div>
</section>

<section id="citaj">
  <div class="wrap">
    <h2><span class="sr-only">Čitaj dalje</span><span class="en-only">Read on</span></h2>
    <div class="cards">
      <a class="card" href="https://github.com/3esign/beops" style="border:0;padding:0"><div class="card" style="height:100%"><h3>GitHub</h3><p><span class="sr-only">Kod, registri, pravila i dokaz dozvole — otvoreno. MIT za kod, CC BY 4.0 za dokumente.</span><span class="en-only">Code, registries, rules and the permission evidence — open. MIT for code, CC BY 4.0 for documents.</span></p><span class="mono">3esign/beops</span></div></a>
    </div>
  </div>
</section>

<footer>
  <div class="wrap fgrid">
    <div><b><span class="sr-only">Autori i kontakt</span><span class="en-only">Authors and contact</span></b>prof. dr Darinka Golubović Matić<br>doc. dr Semir Poturak<br>Univerzitet Union – Nikola Tesla<br><span class="sr-only">Naučni rad za konferenciju, ne proizvod ustanove</span><span class="en-only">A scientific paper for a conference, not a product of the institution</span><br><a href="mailto:poturaksemir@gmail.com">poturaksemir@gmail.com</a></div>
    <div><b><span class="sr-only">Licenca</span><span class="en-only">Licence</span></b><span class="sr-only">MIT za kod, CC BY 4.0 za dokumente i registre. Vrednosti zadržavaju licencu svog izvora.</span><span class="en-only">MIT for code, CC BY 4.0 for documents and registries. Values keep their source's licence.</span></div>
    <div><b><span class="sr-only">Šta ovo nije</span><span class="en-only">What this is not</span></b><span class="sr-only">Nije digitalni blizanac, nije „pametni grad", nije nadzor. Nema podataka o pojedincima, nema kamera, nema ulica kao jedinice analize.</span><span class="en-only">Not a digital twin, not a smart city, not surveillance. No person-level data, no cameras, no street as a unit of analysis.</span></div>
    <div><b><span class="sr-only">Stanje</span><span class="en-only">State</span></b><span class="mono" id="built"></span></div>
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
document.getElementById('lang').addEventListener('click',function(e){
  LANG=LANG==='sr'?'en':'sr';
  document.body.className='lang-'+LANG;
  document.documentElement.lang=LANG;
  e.currentTarget.setAttribute('aria-pressed',String(LANG==='en'));
  render();
  // every embedded study, not a hand-kept list of two: the ribbon was added and stayed Serbian on the English page
  var bar=document.getElementById('sta');
  if(bar && (LANG==='sr'||LANG==='en') && !bar.classList.contains('what-zh') && !bar.classList.contains('what-de')){
    bar.classList.remove('what-sr','what-en'); bar.classList.add('what-'+LANG);
    bar.querySelectorAll('.wlangs button').forEach(function(o){ o.setAttribute('aria-pressed', String(o.getAttribute('data-w')===LANG)); });
  }
  document.querySelectorAll('iframe').forEach(function(f){
    try{ if(f.contentWindow) f.contentWindow.postMessage({beopsLang:LANG},'*'); }catch(err){}
  });
});
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
  var OPEN_ON_ARRIVAL=['slojevi'];   // the drawing that explains the rest; the live interface at the
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
    var b=document.createElement('button'); b.type='button'; b.className='fold'; b.textContent='–';
    b.setAttribute('aria-expanded','true');
    b.setAttribute('aria-label','Skupi / razvij · Fold / unfold');
    function setFolded(folded){
      sec.classList.toggle('folded',folded);
      b.textContent=folded?'+':'–';
      b.setAttribute('aria-expanded',String(!folded));
      if(!folded){
        // A frame inside a display:none section never measured itself; a resize makes it report.
        var fr=sec.querySelectorAll('iframe');
        setTimeout(function(){ for(var i=0;i<fr.length;i++){ try{ fr[i].contentWindow.dispatchEvent(new Event('resize')); }catch(e){} } },60);
      }
    }
    b.addEventListener('click',function(){ setFolded(!sec.classList.contains('folded')); });
    var head=kids[hi];
    (head.tagName==='H2'?head.parentElement:head).appendChild(b);
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
    NOT_PUBLIC = ("WORKING_DOCUMENT", "PISMA", "LETTER", "INTERNAL", "DRAFT", "PRESEK")
    for folder in ("06-paper", "07-legal"):
        for p in sorted((ROOT / "research" / folder).glob("*.pdf")):
            if any(k in p.name.upper() for k in NOT_PUBLIC):
                continue
            shutil.copy(p, DOCS / p.name)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"wrote {DOCS/'index.html'} ({len(html)} bytes; {len(data['registry']['rows'])} sources, "
          f"{len(data['corrections'])} corrections, {len(data['provenance']['refused'])} refusals)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
