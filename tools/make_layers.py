#!/usr/bin/env python3
"""
make_layers.py - the axonometric scheme of BEOPS: the law as the foundation slab, seven strata on it,
knowledge standing beside them. Every plate is drawn in its OWN idiom, and every idiom is a small true
statement read from the registers and the public layers - never a texture chosen for looks.

    python -B tools/make_layers.py                 writes research/05-design/studies/slojevi.svg
    python -B tools/make_layers.py --out docs      writes docs/slojevi.svg
    (build_site.py imports build()/counts() and inlines the same drawing on the landing page)

The order is the editor's rule of 9 September 2026: THE LAW IS GROUND ZERO. Permission is captured
before anything is read - the collector refuses without a ledger line - and even the ground of the map
is a legal fact (five richer routes were refused; Natural Earth is public domain). So the law is not a
stage a datum passes through; it is the slab everything stands on, drawn wider than every plate above
it: nothing overhangs the law.

  0  law and permission   one slab, two halves (Serbian law | the EU horizon), a dotted gate along its
                          front edge, wider than every plate above
  1  ground               the real Natural Earth outline the pulse map draws (public domain)
  2  static layers        the Kontur H3 hexagons, opacity by people (CC BY) - the census on the map
  3  periodic sources     one clock face per polled source slower than 15 min, hand at its cadence
  4  live senses          one ring per live source, radius by cadence - the pulse itself
  5  organizing           the five states in the site's stroke grammar
  6  mind                 three entities in a triangle, arrows between them, the validator's gate
  7  expression           a miniature of the stage: lines on the left, the map on the right
  +  knowledge            a stack of spines beside the strata, standing on the same slab

Bilingual in one SVG (class sr-only / en-only on every label, so the page's language toggle applies),
themed by the page's tokens (currentColor, var(--field), var(--signal)). Two label sets: the full
drawing carries the lists, the small figure (root class "small") carries three words per plate.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "research" / "05-design" / "studies" / "slojevi.svg"

W_PLATE, D_PLATE, H_PLATE, STEP = 340, 150, 15, 118
# A point (u,v) of a plate is hidden by the plate above it when u >= STEP/W and v >= STEP/D.
# Every idiom therefore draws inside the visible band; only the far edge of the two maps is allowed
# to slide under the plate above, which is what makes the stack read as depth.
BAND = (0.07, STEP / D_PLATE - 0.09)
BB = {"lo0": 20.17, "lo1": 20.80, "la0": 44.55, "la1": 44.98}   # the pulse map's own window


# --------------------------------------------------------------------- the registers


def _load(p: pathlib.Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def counts() -> dict:
    """Everything the drawing is allowed to say, read from the registers and the public layers."""
    reg = (_load(ROOT / "research" / "SOURCE_REGISTRY.json") or {}).get("sources", [])
    col = (_load(ROOT / "research" / "COLLECTORS.json") or {}).get("sources", [])
    st = _load(ROOT / "research" / "STATIC_LAYERS.json") or {}
    stat = st.get("layers", []) if isinstance(st, dict) else []
    polled = [s for s in col if s.get("enabled", True)]
    docs = 0
    readme = ROOT / "research" / "README.md"
    if readme.exists():
        docs = sum(1 for ln in readme.read_text(encoding="utf-8").splitlines() if ln.lstrip().startswith("- **["))
    return {
        "records": len(reg),
        "refused": sum(1 for s in reg if s.get("status") == "opted_out"),
        "polled": len(polled),
        "live": [s for s in polled if s.get("cadence_seconds", 0) <= 900],
        "periodic": [s for s in polled if s.get("cadence_seconds", 0) > 900],
        "static": len(stat) if isinstance(stat, list) else 0,
        "docs": docs,
        "basemap": _load(ROOT / "public" / "basemap-belgrade.json"),
        "people": _load(ROOT / "public" / "context-population.json"),
    }


# --------------------------------------------------------------------- geometry


def iso(u: float, v: float, x0: float, y0: float, w: float = W_PLATE, d: float = D_PLATE):
    """Plate coordinates (u to the right, v to the back, both 0..1) -> page coordinates, 2:1 axonometry."""
    return x0 + u * w - v * d, y0 - u * w * 0.5 - v * d * 0.5


def band(t: float) -> float:
    """0..1 across the visible band of a plate."""
    return BAND[0] + t * (BAND[1] - BAND[0])


def plate_faces(x0, y0, w=W_PLATE, d=D_PLATE, h=H_PLATE):
    p0 = (x0, y0)
    p1 = (x0 + w, y0 - w * 0.5)
    p2 = (x0 + w - d, y0 - w * 0.5 - d * 0.5)
    p3 = (x0 - d, y0 - d * 0.5)
    return (p0, p1, p2, p3), (p3, p0, (p0[0], p0[1] + h), (p3[0], p3[1] + h)), (p0, p1, (p1[0], p1[1] + h), (p0[0], p0[1] + h))


def poly(points) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, sr, en, cls="", size=12, anchor="start", weight=""):
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text class="sr-only {cls}" x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}"{w}>{esc(sr)}</text>'
            f'<text class="en-only {cls}" x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}"{w}>{esc(en)}</text>')


def wrap(s: str, n: int) -> list[str]:
    words, lines, cur = s.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > n and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    if cur:
        lines.append(cur)
    return lines


MAP_V0, MAP_V1 = 0.05, 0.86          # the far edge slides under the plate above - that is the depth
_ASPECT = ((BB["lo1"] - BB["lo0"]) * math.cos(math.radians(44.8))) / (BB["la1"] - BB["la0"])
MAP_U0 = 0.42          # far enough right that the far edge never reaches the label column
MAP_U1 = MAP_U0 + (MAP_V1 - MAP_V0) * D_PLATE * _ASPECT / W_PLATE


def _on_plate(lon, lat, x0, y0):
    u = (lon - BB["lo0"]) / (BB["lo1"] - BB["lo0"])
    v = (lat - BB["la0"]) / (BB["la1"] - BB["la0"])
    return iso(MAP_U0 + (MAP_U1 - MAP_U0) * u, MAP_V0 + (MAP_V1 - MAP_V0) * v, x0, y0), (0 <= u <= 1 and 0 <= v <= 1)


# --------------------------------------------------------------------- one idiom per stratum


def idiom_ground(x0, y0, c) -> str:
    """The real Natural Earth geometry the pulse map draws - the map is made only of what is public domain."""
    bm = c.get("basemap")
    if not bm:
        return ""
    out = []
    for f in bm.get("features", []):
        g = f.get("geometry") or {}
        if f.get("layer") == "river" and g.get("type") == "LineString":
            pts = [_on_plate(a, b, x0, y0)[0] for a, b in g["coordinates"]]
            out.append(f'<polyline class="river" points="{poly(pts)}"/>')
        elif g.get("type") in ("Polygon", "MultiPolygon"):
            rings = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            for pg in rings:
                for ring in pg[:1]:
                    pts = [_on_plate(a, b, x0, y0)[0] for a, b in ring]
                    out.append(f'<polygon class="urban" points="{poly(pts)}"/>')
    return "".join(out)


def idiom_static(x0, y0, c) -> str:
    """The Kontur H3 cells at the plate's scale, opacity by people - the census as it sits on the map."""
    pe = c.get("people")
    if not pe:
        return ""
    hexes = [h for h in pe.get("hexes", []) if len(h) >= 3 and h[2] >= 300]
    if not hexes:
        return ""
    vals = sorted(h[2] for h in hexes)
    p95 = vals[min(len(vals) - 1, int(len(vals) * 0.95))] or 1
    r, out = 2.4, []
    for h in hexes:
        (x, y), inside = _on_plate(h[0], h[1], x0, y0)
        if not inside:
            continue
        a = 0.10 + 0.55 * min(1.0, math.sqrt(h[2] / p95))
        pts = [(x + r * math.cos(k * math.pi / 3), y + r * 0.5 * math.sin(k * math.pi / 3)) for k in range(6)]
        out.append(f'<polygon class="hex" fill-opacity="{a:.2f}" points="{poly(pts)}"/>')
    return "".join(out)


def idiom_periodic(x0, y0, c) -> str:
    """One clock face per periodic source, the hand at its own cadence (a full turn = 24 h)."""
    srcs = c["periodic"]
    if not srcs:
        return ""
    out, cols = [], min(6, len(srcs))
    rows = math.ceil(len(srcs) / cols)
    for i, s in enumerate(srcs):
        u = 0.30 + 0.64 * ((i % cols) + 0.5) / cols
        v = band(0.18 + 0.62 * ((i // cols) + 0.5) / max(1, rows))
        x, y = iso(u, v, x0, y0)
        rad = 8.5
        frac = min(1.0, s.get("cadence_seconds", 3600) / 86400.0)
        ang = -math.pi / 2 + frac * 2 * math.pi
        out.append(f'<ellipse class="clock" cx="{x:.1f}" cy="{y:.1f}" rx="{rad}" ry="{rad * 0.5}"/>')
        out.append(f'<line class="hand" x1="{x:.1f}" y1="{y:.1f}" '
                   f'x2="{x + rad * 0.8 * math.cos(ang):.1f}" y2="{y + rad * 0.4 * math.sin(ang):.1f}"/>')
    return "".join(out)


def idiom_live(x0, y0, c) -> str:
    """One ring per live source, radius by cadence - the same ring the pulse map draws when an instrument is read."""
    srcs = c["live"]
    if not srcs:
        return ""
    out, cols = [], min(8, len(srcs))
    rows = math.ceil(len(srcs) / cols)
    for i, s in enumerate(srcs):
        u = 0.30 + 0.64 * ((i % cols) + 0.5) / cols
        v = band(0.18 + 0.62 * ((i // cols) + 0.5) / max(1, rows))
        x, y = iso(u, v, x0, y0)
        rad = 3.2 + 5.5 * min(1.0, s.get("cadence_seconds", 900) / 900.0)
        out.append(f'<ellipse class="ring faint" cx="{x:.1f}" cy="{y:.1f}" rx="{rad * 1.85:.1f}" ry="{rad * 0.93:.1f}"/>')
        out.append(f'<ellipse class="ring" cx="{x:.1f}" cy="{y:.1f}" rx="{rad:.1f}" ry="{rad * 0.5:.1f}"/>')
        out.append(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="1.4"/>')
    return "".join(out)


def idiom_organize(x0, y0, c) -> str:
    """The five states in the site's own stroke grammar: observed, untimed, estimated, forecast, unavailable."""
    out = []
    names = [("izmereno", "observed"), ("bez vremena", "untimed"), ("procenjeno", "estimated"),
             ("prognoza", "forecast"), ("nedostupno", "unavailable")]
    cls = ["st-observed", "st-untimed", "st-estimated", "st-forecast", "st-unavailable"]
    for i, (sr, en) in enumerate(names):
        x, y = iso(0.24 + 0.66 * i / 4, band(0.45), x0, y0)
        s = 7.5
        out.append(f'<polygon class="state {cls[i]}" points="{poly([(x, y - s * 0.5), (x + s, y), (x, y + s * 0.5), (x - s, y)])}"/>')
        out.append(text(x, y + 15, sr, en, cls="tiny", size=6.5, anchor="middle"))
    return "".join(out)


def idiom_mind(x0, y0, c) -> str:
    """Three entities in a triangle, arrows between them, the validator's gate on the way out."""
    pts = [iso(0.34, band(0.18), x0, y0), iso(0.62, band(0.18), x0, y0), iso(0.46, band(0.82), x0, y0)]
    names = [("Posmatrač", "Observer"), ("Sumnjalo", "Skeptic"), ("Povezivač", "Connector")]
    out = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        (x1, y1), (x2, y2) = pts[a], pts[b]
        out.append(f'<line class="arrow" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" marker-end="url(#lay-arrow)"/>')
    for (x, y), (sr, en) in zip(pts, names):
        out.append(f'<circle class="entity" cx="{x:.1f}" cy="{y:.1f}" r="4.5"/>')
        out.append(text(x + 7, y + 3, sr, en, cls="tiny", size=7))
    gx, gy = iso(0.90, band(0.46), x0, y0)
    out.append(f'<line class="arrow" x1="{pts[1][0] + 6:.1f}" y1="{pts[1][1]:.1f}" x2="{gx - 10:.1f}" y2="{gy:.1f}" marker-end="url(#lay-arrow)"/>')
    out.append(f'<rect class="gate" x="{gx - 7:.1f}" y="{gy - 7:.1f}" width="14" height="14" rx="2"/>')
    out.append(f'<path class="tick" d="M{gx - 3.6:.1f},{gy - 0.4:.1f} l3,3.2 l5.6,-6.6"/>')
    return "".join(out)


def idiom_express(x0, y0, c) -> str:
    """A miniature of the stage: the monologue's lines on the left, the pulsing map on the right."""
    out = []
    for i in range(6):
        (x1, y1) = iso(0.32, band(0.12 + i * 0.15), x0, y0)
        (x2, y2) = iso(0.58 - (i % 3) * 0.045, band(0.12 + i * 0.15), x0, y0)
        out.append(f'<line class="stageline" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    frame = [iso(0.66, band(0.06), x0, y0), iso(0.97, band(0.06), x0, y0), iso(0.97, band(0.94), x0, y0), iso(0.66, band(0.94), x0, y0)]
    out.append(f'<polygon class="stageframe" points="{poly(frame)}"/>')
    for u, t, r in ((0.74, 0.30, 3.6), (0.90, 0.54, 2.4), (0.81, 0.78, 3.0)):
        x, y = iso(u, band(t), x0, y0)
        out.append(f'<ellipse class="ring" cx="{x:.1f}" cy="{y:.1f}" rx="{r}" ry="{r * 0.5}"/>')
    return "".join(out)


# --------------------------------------------------------------------- the drawing


def build(c: dict, small: bool = False) -> str:
    """One drawing, two renderings. The page shows the small one - the plates, their names and their counts;
    the standalone file shows the same geometry with every reading note. They differ only in what is said,
    never in what is drawn, and the small one ends where its own text ends, so the page carries no empty band."""
    W, H = 1280, 1345
    x0, y0 = 512, 1078         # front-left corner of stratum 1 (the ground)
    step = STEP
    ln, pn = len(c["live"]), len(c["periodic"])
    strata = [
        ("ground", "1 · Podloga", "1 · Ground", "javno vlasništvo", "public domain",
         "Natural Earth 1:10 mil., javno vlasništvo — isti obris koji puls crta: reke, jezera, tkivo grada; orijentacija, ne merenje",
         "Natural Earth 1:10m, public domain — the outline the pulse draws: rivers, lakes, city fabric; orientation, not measurement",
         idiom_ground, False),
        ("static", "2 · Statični i polustatični slojevi", "2 · Static and semi-static layers", "popis · CC BY", "census · CC BY",
         f"Kontur stanovništvo 2022 (CC BY), heksagon po heksagon · {c['static']} sloja: popis, putevi, GHSL, poplavne zone — traju mesecima i godinama",
         f"Kontur population 2022 (CC BY), hexagon by hexagon · {c['static']} layers: census, roads, GHSL, flood zones — they last months and years",
         idiom_static, False),
        ("periodic", "3 · Periodični izvori (sati – dani)", "3 · Periodic sources (hours – days)", f"{pn} izvora · takt izvora", f"{pn} sources · own beat",
         f"{pn} izvora, svaki na svom taktu (pun krug = 24 h): SEPA satne vrednosti, isključenja struje, obaveštenja grada, Vodovod",
         f"{pn} sources, each on its own beat (a full dial turn = 24 h): SEPA hourly means, power outages, City notices, water and heating",
         idiom_periodic, False),
        ("live", "4 · Živa čula (minuti)", "4 · Live senses (minutes)", f"{ln} izvora · minuti", f"{ln} sources · minutes",
         f"{ln} izvora na 5–15 min; prsten je puls koji mapa crta kad je instrument pročitan; prijem nije merenje",
         f"{ln} sources every 5–15 min; a ring is the pulse drawn when an instrument was read; reception is not measurement",
         idiom_live, True),
        ("organize", "5 · Sistem koji organizuje", "5 · The system that organizes", "pet stanja", "five states",
         "kapija → prijem → red → dedupe → izvoz na 5 min · potvrda i za neuspeh · pet stanja · ispravke se dopisuju",
         "gate → reception → row → dedupe → export every 5 min · a receipt even for a failure · five states · corrections appended",
         idiom_organize, False),
        ("mind", "6 · Sistem koji misli i govori", "6 · The system that thinks and speaks", "tri entiteta · kapija", "three entities · a gate",
         "Posmatrač, Sumnjalo i Povezivač na lokalnim modelima · kapija: brojevi samo iz digesta, citati u tekstu",
         "Observer, Skeptic and Connector on local models · the gate: numbers only from the digest, citations in the text",
         idiom_mind, True),
        ("express", "7 · Izraz", "7 · Expression", "scena · sajt", "the stage · the site",
         "monolog, puls, podaci po stanici i na mapi · objava na 10 minuta, dvojezično · ai_generated=true na svakoj misli",
         "monologue, pulse, data per station and on the map · published every 10 minutes, bilingual · ai_generated=true",
         idiom_express, False),
    ]
    parts = []

    # ---- 0 · the law: the slab, wider than everything, two halves, a dotted gate along its front edge
    sw, sd, sh = W_PLATE + 150, D_PLATE, 30   # wider than every plate, and still clear of the knowledge column
    sx, sy = x0, y0 + 122          # one clear step under the ground, so the ground's label has the same band as the others
    top, left, right = plate_faces(sx, sy, sw, sd, sh)
    p0, p1, p2, p3 = top
    ma = ((p0[0] + p3[0]) / 2, (p0[1] + p3[1]) / 2)
    mb = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    parts.append('<g class="stratum law">')
    parts.append(f'<polygon class="side slab" points="{poly(left)}"/><polygon class="side2 slab" points="{poly(right)}"/>')
    parts.append(f'<polygon class="top slab rs" points="{poly((p0, p1, mb, ma))}"/>')
    parts.append(f'<polygon class="top slab eu" points="{poly((ma, mb, p2, p3))}"/>')
    parts.append(f'<line class="seam" x1="{ma[0]:.1f}" y1="{ma[1]:.1f}" x2="{mb[0]:.1f}" y2="{mb[1]:.1f}"/>')
    parts.append(f'<line class="gateline" x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}"/>')
    parts.append('</g>')

    # ---- strata 1..7
    labels = []
    for i, (key, tsr, ten, ssr, sen, isr, ien, idiom, accent) in enumerate(strata):
        y = y0 - i * step
        top, left, right = plate_faces(x0, y)
        cls = "accent" if accent else "plain"
        parts.append(f'<g class="stratum {key}">'
                     f'<polygon class="side {cls}" points="{poly(left)}"/>'
                     f'<polygon class="side2 {cls}" points="{poly(right)}"/>'
                     f'<polygon class="top {cls}" points="{poly(top)}"/>'
                     f'<clipPath id="lay-clip-{key}"><polygon points="{poly(top)}"/></clipPath>'
                     f'<g clip-path="url(#lay-clip-{key})">{idiom(x0, y, c)}</g></g>')
        labels.append((top[0], tsr, ten, ssr, sen, isr, ien, accent))

    # ---- labels, left of each plate's back-left corner
    for p0c, tsr, ten, ssr, sen, isr, ien, accent in labels:
        lx, ly = p0c[0] - D_PLATE - 18, p0c[1] + 16
        parts.append(f'<line class="leader" x1="{lx + 5:.1f}" y1="{ly - 4:.1f}" x2="{p0c[0] - 3:.1f}" y2="{p0c[1] + 3:.1f}"/>')
        parts.append(text(lx, ly, tsr, ten, size=12.5, anchor="end", weight="600", cls=("accent-text" if accent else "")))
        parts.append(text(lx, ly + 14, ssr, sen, size=10, anchor="end", cls="dim only-small"))
        yy = ly + 14
        for a, b in zip(wrap(isr, 66)[:2], wrap(ien, 66)[:2]):   # two lines fit the band between this plate and the one below
            parts.append(text(lx, yy, a, b, size=9.5, anchor="end", cls="dim only-full"))
            yy += 11.5

    # ---- the law's own label, under the slab's back-left corner
    lx, ly = sx - D_PLATE - 18, sy + 44
    parts.append(f'<line class="leader" x1="{lx + 5:.1f}" y1="{ly - 4:.1f}" x2="{sx - 3:.1f}" y2="{sy + 3:.1f}"/>')
    parts.append(text(lx, ly, "0 · Zakon i dozvola — temelj", "0 · Law and permission — the foundation", size=12.5, anchor="end", weight="600"))
    parts.append(text(lx, ly + 14, f"{c['records']} zapisa · {c['polled']} se čita · {c['refused']} odbijanja",
                      f"{c['records']} records · {c['polled']} polled · {c['refused']} refusals", size=10, anchor="end", cls="dim only-small"))
    yy = ly + 14
    law_sr = (f"zahvat dozvole pre svakog čitanja · knjiga zahvata · {c['records']} zapisa u registru, "
              f"{c['polled']} se čita, {c['refused']} imenovanih odbijanja koja se ne zaobilaze · nedeljna ponovna provera · "
              "ivični slučajevi E-001–E-013, ispravke C-001–C-013, urednik od zapisa · "
              "prednja polovina temelja je srpsko pravo — ZASP čl. 6(2) i 49, ZZPL čl. 88 i 92, pristup informacijama, buka čl. 25, KZ čl. 143; "
              "zadnja polovina je EU horizont — 2019/790 čl. 3–4 (Content-Signal), baze 96/9, GDPR 85 i 89, AI akt čl. 50")
    law_en = (f"a permission capture before any reading · the ledger · {c['records']} registry records, "
              f"{c['polled']} polled, {c['refused']} named refusals never circumvented · a weekly re-check · "
              "edge cases E-001–E-013, corrections C-001–C-013, an editor of record · "
              "the front half of the slab is Serbian law — Copyright Act Arts. 6(2) and 49, Data Protection Act 88 and 92, Access to Information, noise Art. 25, Criminal Code 143; "
              "the back half is the EU horizon — 2019/790 Arts. 3–4 (Content-Signal), Database 96/9, GDPR 85 and 89, AI Act Art. 50")
    for a, b in zip(wrap(law_sr, 66), wrap(law_en, 66)):   # nothing stands below the foundation, so this column may run wide
        parts.append(text(lx, yy, a, b, size=9.5, anchor="end", cls="dim only-full"))
        yy += 11.5
    H = int(ly + 34) if small else max(H, int(yy + 12))       # the canvas ends where the drawing's own last words end

    # ---- knowledge: spines standing on the slab, to the right of the strata
    kx, base = x0 + W_PLATE + 66, y0 - 138
    parts.append('<g class="know">')
    for i in range(6):
        h = 118 + (i % 3) * 8
        parts.append(f'<rect class="spine" x="{kx + i * 8.5:.1f}" y="{base - h:.1f}" width="5.6" height="{h}" rx="1"/>')
    tx = kx + 62
    parts.append(text(tx, base - 92, "Znanje pored slojeva", "Knowledge beside the strata", size=11.5, weight="600"))
    know = [(f"{c['docs']} dokumenata u indeksu istraživanja", f"{c['docs']} documents in the research index"),
            ("literatura 2024–26 · radni dokument · pre-paper", "the literature 2024–26 · working document · pre-paper"),
            ("registri · ivični slučajevi · ispravke · mapa projekta", "registers · edge cases · corrections · the project map"),
            ("stoji na istom temelju i menja svaki sloj", "stands on the same foundation and shapes every stratum")]
    for j, (sr, en) in enumerate(know):
        parts.append(text(tx, base - 74 + j * 12.5, sr, en, size=9.5, cls="dim only-full"))
    parts.append(text(tx, base - 74, f"{c['docs']} dokumenata", f"{c['docs']} documents", size=9.5, cls="dim only-small"))
    parts.append('</g>')

    # ---- the reading rises through the strata, along the right edge
    fx = x0 + W_PLATE + 14
    for i in range(6):
        ya = y0 - i * step - W_PLATE * 0.5 + 12
        yb = y0 - (i + 1) * step - W_PLATE * 0.5 + 12 + H_PLATE + 4
        parts.append(f'<line class="flow" x1="{fx}" y1="{ya:.0f}" x2="{fx}" y2="{yb:.0f}" marker-end="url(#lay-arrow)"/>')

    note_sr = ("kako se čita: svaki sloj je nacrtan svojim jezikom — prsten je puls koji mapa crta kad je instrument "
               "pročitan (veći prsten, ređi takt), brojčanik je takt periodičnog izvora, heksagon je popis na mapi, "
               "romb je stanje podatka. Svaki broj u crtežu čita se iz registara pri svakoj objavi: crtež ne može reći "
               "ono što registri ne kažu.")
    note_en = ("how to read it: every stratum is drawn in its own language — a ring is the pulse the map draws when an "
               "instrument was read (a larger ring, a slower beat), a clock face is a periodic source's beat, a hexagon is "
               "the census on the map, a rhombus is a datum's state. Every number in the drawing is read from the registers "
               "at each publish: the drawing cannot say what the registers do not.")
    for k, (a, b) in enumerate(zip(wrap(note_sr, 52), wrap(note_en, 52))):
        parts.append(text(44, 168 + k * 13, a, b, size=9.5, cls="dim only-full"))
    head = [text(40, 40, "BEOPS — slojevi opservatorije", "BEOPS — the strata of the observatory", size=17, weight="600"),
            text(40, 60, "zakon je nulti sloj: sve ostalo stoji na njemu — podloga, slojevi, čula, sistemi, izraz",
                 "the law is ground zero: everything else stands on it — ground, layers, senses, systems, expression", size=11, cls="dim")]
    style = """
<style>
.layers-svg text{font-family:"Source Sans 3","Segoe UI",system-ui,sans-serif;fill:currentColor}
.layers-svg text.dim{fill-opacity:.6}
.layers-svg text.tiny{fill-opacity:.68}
.layers-svg text.accent-text{fill:var(--signal,#D93A16)}
.layers-svg:not(.small) .only-small{display:none}
.layers-svg.small .only-full{display:none}
.layers-svg .top.plain{fill:var(--field,#FBFAF7);stroke:currentColor;stroke-width:1}
.layers-svg .side.plain,.layers-svg .side2.plain{fill:currentColor;fill-opacity:.07;stroke:currentColor;stroke-opacity:.4;stroke-width:.8}
.layers-svg .top.accent{fill:var(--signal,#D93A16);fill-opacity:.06;stroke:var(--signal,#D93A16);stroke-width:1.1}
.layers-svg .side.accent,.layers-svg .side2.accent{fill:var(--signal,#D93A16);fill-opacity:.18;stroke:var(--signal,#D93A16);stroke-opacity:.55;stroke-width:.8}
.layers-svg .top.slab{stroke:currentColor;stroke-width:1.2}
.layers-svg .top.slab.rs{fill:currentColor;fill-opacity:.11}
.layers-svg .top.slab.eu{fill:currentColor;fill-opacity:.045}
.layers-svg .side.slab,.layers-svg .side2.slab{fill:currentColor;fill-opacity:.17;stroke:currentColor;stroke-width:1}
.layers-svg .seam{stroke:currentColor;stroke-opacity:.4;stroke-width:.8;stroke-dasharray:2 3}
.layers-svg .gateline{stroke:var(--signal,#D93A16);stroke-width:2;stroke-dasharray:3 4}
.layers-svg .river{fill:none;stroke:currentColor;stroke-opacity:.34;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.layers-svg .urban{fill:currentColor;fill-opacity:.06;stroke:currentColor;stroke-opacity:.36;stroke-width:.6}
.layers-svg .hex{fill:currentColor;stroke:none}
.layers-svg .clock{fill:var(--field,#FBFAF7);stroke:currentColor;stroke-opacity:.55;stroke-width:.9}
.layers-svg .hand{stroke:currentColor;stroke-opacity:.8;stroke-width:1.1}
.layers-svg .ring{fill:none;stroke:var(--signal,#D93A16);stroke-width:1.2}
.layers-svg .ring.faint{stroke-opacity:.28;stroke-width:.8}
.layers-svg .dot{fill:currentColor;fill-opacity:.55}
.layers-svg .state{stroke:currentColor;stroke-width:1}
.layers-svg .st-observed{fill:var(--signal,#D93A16);stroke:var(--signal,#D93A16)}
.layers-svg .st-untimed{fill:var(--signal,#D93A16);fill-opacity:.38;stroke:var(--signal,#D93A16)}
.layers-svg .st-estimated{fill:none;stroke-dasharray:3 2}
.layers-svg .st-forecast{fill:none;stroke-dasharray:1 2}
.layers-svg .st-unavailable{fill:none;stroke-opacity:.32}
.layers-svg .entity{fill:var(--signal,#D93A16)}
.layers-svg .arrow{stroke:currentColor;stroke-opacity:.5;stroke-width:1}
.layers-svg .gate{fill:var(--field,#FBFAF7);stroke:currentColor;stroke-width:1.1}
.layers-svg .tick{fill:none;stroke:var(--signal,#D93A16);stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.layers-svg .stageline{stroke:currentColor;stroke-opacity:.45;stroke-width:1.2}
.layers-svg .stageframe{fill:none;stroke:currentColor;stroke-opacity:.45;stroke-width:.9}
.layers-svg .spine{fill:currentColor;fill-opacity:.10;stroke:currentColor;stroke-opacity:.45;stroke-width:.7}
.layers-svg .flow{stroke:currentColor;stroke-opacity:.4;stroke-width:1}
.layers-svg .leader{stroke:currentColor;stroke-opacity:.3;stroke-width:.7}
</style>
<defs><marker id="lay-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
<path d="M0,0 L10,5 L0,10 z" fill="currentColor" fill-opacity=".5"/></marker></defs>
"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" '
            f'aria-label="BEOPS strata, axonometric: the law as the foundation" class="layers-svg{" small" if small else ""}">'
            + style + "".join(head) + "".join(parts) + "</svg>")


def main() -> int:
    out = OUT
    if "--out" in sys.argv:
        out = ROOT / sys.argv[sys.argv.index("--out") + 1] / "slojevi.svg"
    c = counts()
    out.parent.mkdir(parents=True, exist_ok=True)
    for path, small in ((out, False), (out.with_name("slojevi-mali.svg"), True)):
        svg = build(c, small)
        path.write_text(svg, encoding="utf-8")
        print(f"wrote {path} ({len(svg)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
