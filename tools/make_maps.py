#!/usr/bin/env python3
"""
make_maps.py - the three maps of the working document, generated from the same files the site uses.

    python -B tools/make_maps.py            -> research/06-paper/maps/map-instruments.svg
    python -B tools/make_maps.py --out docs -> the same three maps into docs/ (what the site serves)
                                               research/06-paper/maps/map-coverage.svg
                                               research/06-paper/maps/map-last24h.svg
                                               research/06-paper/maps/MAPS.json   (what each map was made from)

Inputs: public/basemap-belgrade.json (Natural Earth 1:10m, public domain, S98) and
public/live-snapshot.json (the last 24 h of receptions). Nothing is drawn that the two files do not
contain: an instrument is a point at the coordinate its operator publishes; a filled mark means a
reception exists in the window; a hollow mark means none does. The coverage field is computed from
our own instrument coordinates only. Rivers and the built-up footprint are generalised at
1:10 million and every map says so on its face. No persons, no cameras, no streets.

Stdlib only: json, math, pathlib, datetime. The SVGs are plain XML and render in any browser and in
the PDF pipeline without a library.
"""
from __future__ import annotations

import json
import math
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASEMAP = ROOT / "public" / "basemap-belgrade.json"
SNAPSHOT = ROOT / "public" / "live-snapshot.json"
OUT = ROOT / "research" / "06-paper" / "maps"

# Belgrade window, WGS84 (same as the studies)
BB = {"lo0": 20.17, "lo1": 20.80, "la0": 44.55, "la1": 44.98}
W, H = 1200, 820                       # px; the PDF scales it to the column
INK, INK60, INK30, INK12, INK06 = "#111311", "#5c5e5c", "#a5a7a5", "#dcdcd9", "#ececea"
WATER, SIGNAL, UNTIMED, PAPER = "#b9c4cc", "#D93A16", "#e08a75", "#fbfaf7"
FONT = "font-family='Carlito, DejaVu Sans, Arial, sans-serif'"
MONO = "font-family='DejaVu Sans Mono, Menlo, monospace'"

MUNI = [("Stari grad", 44.8186, 20.4573), ("Vračar", 44.7969, 20.4739), ("Savski venac", 44.7936, 20.4528),
        ("Novi Beograd", 44.815, 20.412), ("Zemun", 44.8458, 20.4016), ("Palilula", 44.83, 20.5),
        ("Zvezdara", 44.795, 20.505), ("Voždovac", 44.76, 20.49), ("Čukarica", 44.76, 20.41),
        ("Rakovica", 44.74, 20.44), ("Surčin", 44.79, 20.28), ("Grocka", 44.67, 20.72),
        ("Obrenovac", 44.655, 20.20), ("Barajevo", 44.63, 20.42), ("Sopot", 44.52, 20.58)]


def proj(lat: float, lon: float) -> tuple[float, float]:
    kx = math.cos(44.8 * math.pi / 180)
    sx = W / ((BB["lo1"] - BB["lo0"]) * kx)
    sy = H / (BB["la1"] - BB["la0"])
    s = min(sx, sy)
    cx = (W - (BB["lo1"] - BB["lo0"]) * kx * s) / 2
    cy = (H - (BB["la1"] - BB["la0"]) * s) / 2
    return cx + (lon - BB["lo0"]) * kx * s, cy + (BB["la1"] - lat) * s


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def path_of(coords, close=False) -> str:
    pts = [proj(c[1], c[0]) for c in coords]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return d + (" Z" if close else "")


def base_layers(bm: dict) -> str:
    """Built-up footprint, then rivers, then municipality names. Structure colour only."""
    parts = [f"<rect x='0' y='0' width='{W}' height='{H}' fill='{PAPER}'/>"]
    areas = [f for f in bm.get("features", []) if f.get("layer") in ("urban", "lake")]
    for f in areas:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            d = " ".join(path_of(ring, close=True) for ring in poly)
            parts.append(f"<path d='{d}' fill='{INK06}' stroke='{INK30}' stroke-width='1' fill-rule='evenodd'/>")
    rivers = [f for f in bm.get("features", []) if f.get("layer") == "river"]
    for width, alpha in ((16, .35), (7, 1)):
        for f in rivers:
            parts.append(f"<path d='{path_of(f['geometry']['coordinates'])}' fill='none' stroke='{WATER}' "
                         f"stroke-width='{width}' stroke-opacity='{alpha}' stroke-linejoin='round' stroke-linecap='round'/>")
    for name, lat, lon in MUNI:
        x, y = proj(lat, lon)
        parts.append(f"<rect x='{x-1:.1f}' y='{y-1:.1f}' width='2' height='2' fill='{INK30}'/>")
        parts.append(f"<text x='{x+7:.1f}' y='{y+4:.1f}' {FONT} font-size='11' font-weight='600' letter-spacing='1.5' fill='{INK30}'>{esc(name.upper())}</text>")
    return "\n".join(parts)


def caption(lines: list[str]) -> str:
    out = [f"<rect x='0' y='{H - 14 * len(lines) - 14}' width='{W}' height='{14 * len(lines) + 14}' fill='{PAPER}' fill-opacity='.94'/>"]
    y = H - 10 - 14 * (len(lines) - 1)
    for ln in lines:
        out.append(f"<text x='10' y='{y}' {MONO} font-size='11' fill='{INK60}'>{esc(ln)}</text>")
        y += 14
    return "\n".join(out)


def svg(body: str, title: str) -> str:
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' width='{W}' height='{H}' role='img' aria-label='{esc(title)}'>\n"
            f"<title>{esc(title)}</title>\n{body}\n</svg>\n")


def instruments(snap: dict) -> list[dict]:
    """One point per instrument with a published coordinate: SEPA station, citizen sensor, parking lot."""
    by_key: dict = {}
    for src in snap["sources"]:
        for ds in src["datastreams"]:
            if ds.get("lat") is None or ds.get("lon") is None:
                continue
            key = (src["sid"], ds.get("station"))
            n_rx = sum(1 for p in ds["points"] if p.get("rx"))
            untimed = any(p.get("tu") for p in ds["points"])
            q = by_key.get(key)
            if q is None:
                by_key[key] = {"key": key, "sid": src["sid"], "station": ds.get("station"), "lat": ds["lat"], "lon": ds["lon"],
                               "rows": len(ds["points"]), "rx": n_rx, "streams": 1, "untimed": untimed}
            else:
                q["rows"] += len(ds["points"])
                q["rx"] += n_rx
                q["streams"] += 1
                q["untimed"] = q["untimed"] or untimed
    return list(by_key.values())


def map_instruments(bm: dict, snap: dict, pts: list[dict]) -> str:
    body = [base_layers(bm)]
    # citizen sensors first (small), then parking (square), then SEPA (large, named)
    for p in pts:
        x, y = proj(p["lat"], p["lon"])
        if p["sid"] == "S04":
            body.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='2.6' fill='{INK60}'/>")
    for p in pts:
        x, y = proj(p["lat"], p["lon"])
        if p["sid"] == "S10":
            body.append(f"<rect x='{x-3:.1f}' y='{y-3:.1f}' width='6' height='6' fill='none' stroke='{INK}' stroke-width='1.2'/>")
    sepa = [p for p in pts if p["sid"] == "S146"]
    for p in sepa:
        x, y = proj(p["lat"], p["lon"])
        body.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='5' fill='{PAPER}' stroke='{INK}' stroke-width='1.6'/>")
        body.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='1.6' fill='{INK}'/>")
    # SEPA names: to the right of the dot, with a paper halo so they cut through the ground; when a
    # label has to move down to avoid another, a hairline leader keeps it tied to its dot.
    placed: list[tuple[float, float, float]] = []      # x0, x1, y of labels already set
    for p in sorted(sepa, key=lambda q: (proj(q["lat"], q["lon"])[1], proj(q["lat"], q["lon"])[0])):
        x, y = proj(p["lat"], p["lon"])
        wpx = 6.0 * len(p["station"]) + 4
        lx, ty = x + 8, y + 4
        for _ in range(16):
            if all(ty + 4 < py - 8 or ty - 8 > py + 4 or lx > px1 + 4 or lx + wpx < px0 - 4 for px0, px1, py in placed):
                break
            ty += 11
        placed.append((lx, lx + wpx, ty))
        if ty - (y + 4) > 8:
            body.append(f"<line x1='{x:.1f}' y1='{y:.1f}' x2='{lx - 2:.1f}' y2='{ty - 3:.1f}' stroke='{INK30}' stroke-width='.8'/>")
        body.append(f"<text x='{lx:.1f}' y='{ty:.1f}' {FONT} font-size='10.5' fill='{INK}' paint-order='stroke' stroke='{PAPER}' stroke-width='3' stroke-linejoin='round'>{esc(p['station'])}</text>")
    n = {k: sum(1 for p in pts if p["sid"] == k) for k in ("S146", "S04", "S10")}
    legend = [
        f"<circle cx='22' cy='24' r='5' fill='{PAPER}' stroke='{INK}' stroke-width='1.6'/><circle cx='22' cy='24' r='1.6' fill='{INK}'/>",
        f"<text x='34' y='28' {FONT} font-size='12' fill='{INK}'>SEPA air-quality station ({n['S146']}) - hourly means, measurement interval published</text>",
        f"<circle cx='22' cy='46' r='2.6' fill='{INK60}'/>",
        f"<text x='34' y='50' {FONT} font-size='12' fill='{INK}'>Sensor.Community citizen sensor ({n['S04']}) - one reading every few minutes, timestamp published</text>",
        f"<rect x='19' y='63' width='6' height='6' fill='none' stroke='{INK}' stroke-width='1.2'/>",
        f"<text x='34' y='71' {FONT} font-size='12' fill='{INK}'>Parking Servis lot ({n['S10']}) - displayed free spaces, NO measurement time published</text>",
    ]
    body.append(f"<g transform='translate(0 {H - 74 - 44 - 8})'><rect x='8' y='8' width='640' height='74' fill='{PAPER}' fill-opacity='.94' stroke='{INK12}'/>" + "".join(legend) + "</g>")
    body.append(caption([f"Instruments the observatory listens to, at the coordinates their operators publish  ·  snapshot {snap['as_of'][:16]}Z  ·  WGS84",
                         "Ground: Natural Earth 1:10m (public domain) - generalised, orientation not measurement  ·  no municipality boundaries: every route to them was refused and recorded"]))
    return svg("\n".join(body), "Map 1 - Instruments")


def map_coverage(bm: dict, snap: dict, pts: list[dict]) -> str:
    """Stipple density rises with distance to the nearest instrument: dense = far from every instrument."""
    body = [base_layers(bm)]
    P = [proj(p["lat"], p["lon"]) for p in pts]
    step, near, far = 10, 26, 140
    buckets: dict = {}          # 8 opacity buckets -> one <g> each, so the file stays small
    y = step / 2
    while y < H:
        x = step / 2
        while x < W:
            d2 = min(((px - x) ** 2 + (py - y) ** 2) for px, py in P) if P else 1e9
            d = math.sqrt(d2)
            if d >= near:
                t = min(1.0, (d - near) / (far - near))
                b = min(7, int(t * 8))
                buckets.setdefault(b, []).append(f"<circle cx='{x:.0f}' cy='{y:.0f}' r='{0.7 + (b + .5) / 8 * 1.1:.1f}'/>")
            x += step
        y += step
    for b, dots in sorted(buckets.items()):
        body.append(f"<g fill='{INK}' fill-opacity='{(b + .5) / 8 * 0.22:.3f}'>" + "".join(dots) + "</g>")
    for px, py in P:
        body.append(f"<circle cx='{px:.1f}' cy='{py:.1f}' r='1.8' fill='{INK30}'/>")
    # scale bar: 5 km at this latitude
    km5 = (5 / (111.32 * math.cos(44.8 * math.pi / 180))) * (proj(44.8, 20.5)[0] - proj(44.8, 20.4)[0]) / 0.1
    x0, y0 = W - 30 - km5, 30
    body.append(f"<line x1='{x0:.1f}' y1='{y0}' x2='{x0+km5:.1f}' y2='{y0}' stroke='{INK}' stroke-width='2'/>")
    body.append(f"<text x='{x0:.1f}' y='{y0+16}' {FONT} font-size='11' fill='{INK}'>5 km</text>")
    body.append(f"<rect x='8' y='8' width='560' height='52' fill='{PAPER}' fill-opacity='.92' stroke='{INK12}'/>")
    body.append(f"<text x='18' y='28' {FONT} font-size='12' font-weight='700' fill='{INK}'>Where the observatory can and cannot hear the city</text>")
    body.append(f"<text x='18' y='46' {FONT} font-size='11.5' fill='{INK60}'>Stipple density rises with distance to the nearest instrument ({len(pts)} instruments). Computed from our own coordinates only - no borrowed cartography.</text>")
    body.append(caption([f"Coverage field  ·  {len(pts)} instruments with a published coordinate  ·  snapshot {snap['as_of'][:16]}Z  ·  WGS84",
                         "Ground: Natural Earth 1:10m (public domain) - generalised, orientation not measurement"]))
    return svg("\n".join(body), "Map 2 - Coverage")


def map_last24h(bm: dict, snap: dict, pts: list[dict]) -> str:
    """Filled = at least one reception in the window; hollow = none. Untimed sources carry the untimed colour."""
    body = [base_layers(bm)]
    heard = [p for p in pts if p["rx"] > 0]
    silent = [p for p in pts if p["rx"] == 0]
    for p in silent:
        x, y = proj(p["lat"], p["lon"])
        body.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3.2' fill='none' stroke='{INK30}' stroke-width='1' stroke-dasharray='2 2'/>")
    for p in heard:
        x, y = proj(p["lat"], p["lon"])
        col = UNTIMED if p["untimed"] else SIGNAL
        r = 5 if p["sid"] == "S146" else 3.2
        body.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r + 5}' fill='{col}' fill-opacity='.10'/>")
        body.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r}' fill='{col}'/>")
    st = {s["sid"]: s for s in snap["status"]["sources"]}
    rows = []
    for sid, label in (("S146", "SEPA hourly means"), ("S04", "Sensor.Community"), ("S10", "Parking Servis")):
        s = st.get(sid)
        if s:
            rows.append(f"{label}: {s['captured']} of {s['expected_slots']} slots received  {s['quorum'][-24:]}")
    bh = 40 + 16 * len(rows) + 30
    L = [f"<rect x='8' y='8' width='700' height='{bh}' fill='{PAPER}' fill-opacity='.94' stroke='{INK12}'/>",
         f"<text x='18' y='28' {FONT} font-size='12' font-weight='700' fill='{INK}'>The last 24 hours: what was heard, what stayed silent</text>",
         f"<circle cx='24' cy='44' r='4' fill='{SIGNAL}'/><text x='34' y='48' {FONT} font-size='11.5' fill='{INK}'>reception in the window, measurement time published</text>",
         f"<circle cx='300' cy='44' r='4' fill='{UNTIMED}'/><text x='310' y='48' {FONT} font-size='11.5' fill='{INK}'>reception, but the source publishes no measurement time</text>",
         f"<circle cx='24' cy='62' r='3.2' fill='none' stroke='{INK30}' stroke-dasharray='2 2'/><text x='34' y='66' {FONT} font-size='11.5' fill='{INK}'>instrument known, nothing received in the window ({len(silent)})</text>"]
    y = 86
    for r in rows:
        L.append(f"<text x='18' y='{y}' {MONO} font-size='10.5' fill='{INK60}'>{esc(r)}</text>")
        y += 16
    body.append(f"<g transform='translate(0 {H - bh - 44 - 8})'>" + "".join(L) + "</g>")
    body.append(caption([f"Receptions in the 24 h to {snap['as_of'][:16]}Z  ·  {len(heard)} instruments heard, {len(silent)} silent  ·  a silence is a record, not a zero",
                         "Ground: Natural Earth 1:10m (public domain) - generalised, orientation not measurement"]))
    return svg("\n".join(body), "Map 3 - The last 24 hours")


CONTEXT_POP = ROOT / "public" / "context-population.json"


def map_people(bm: dict, snap: dict, pts: list[dict], ctx: dict) -> str:
    """People per H3 hexagon (Kontur 2022, CC BY 4.0) under the instruments: where the city lives, where the
    observatory listens. A modelled estimate, drawn as quiet structure, never as a measurement."""
    body = [base_layers(bm)]
    hexes = [h for h in ctx.get("hexes", []) if h[2] >= 20]
    vals = sorted(h[2] for h in hexes)
    pmax = vals[int(len(vals) * 0.95)] if vals else 1
    R = (proj(44.8, 20.5)[0] - proj(44.8, 20.4)[0]) * 0.067
    cells = []
    for h in hexes:
        x, y = proj(h[1], h[0])
        if x < -R or y < -R or x > W + R or y > H + R:
            continue
        a = 0.015 + 0.30 * min(1.0, math.sqrt(h[2] / pmax))
        ptsx = " ".join(f"{x + R * math.cos(k * math.pi / 3):.1f},{y + R * math.sin(k * math.pi / 3):.1f}" for k in range(6))
        cells.append(f"<polygon points='{ptsx}' fill='{INK}' fill-opacity='{a:.3f}'/>")
    body += cells
    for p in pts:
        x, y = proj(p["lat"], p["lon"])
        r = 4.2 if p["sid"] == "S146" else 2.2
        body.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r}' fill='{PAPER}' stroke='{INK}' stroke-width='1.2'/>")
    total = ctx.get("people_total", sum(h[2] for h in hexes))
    body.append(f"<g transform='translate(0 {H - 60 - 44 - 8})'><rect x='8' y='8' width='700' height='60' fill='{PAPER}' fill-opacity='.94' stroke='{INK12}'/>"
                f"<text x='18' y='28' {FONT} font-size='12' font-weight='700' fill='{INK}'>Where the city lives, where the observatory listens</text>"
                f"<text x='18' y='46' {FONT} font-size='11.5' fill='{INK60}'>Hexagons: people per H3 cell (res 8, ~0.74 km2), darker = more people; about {total/1e6:.2f} million people in the window. Rings: the {len(pts)} instruments.</text>"
                f"<text x='18' y='62' {FONT} font-size='11.5' fill='{INK60}'>Kontur Population 2022 (CC BY 4.0) - a modelled estimate (built-up area x census), not a count.</text></g>")
    body.append(caption([f"People (Kontur 2022, CC BY 4.0, modelled) under the instruments  ·  snapshot {snap['as_of'][:16]}Z  ·  WGS84",
                         "Ground: Natural Earth 1:10m (public domain) - generalised, orientation not measurement"]))
    return svg("\n".join(body), "Map 4 - People and instruments")


def main() -> int:
    import sys
    global OUT
    if len(sys.argv) > 2 and sys.argv[1] == "--out":      # e.g. --out docs : the site's copy, refreshed at every publish
        OUT = ROOT / sys.argv[2]
    bm = json.loads(BASEMAP.read_text(encoding="utf-8")) if BASEMAP.exists() else {"features": []}
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    pts = instruments(snap)
    OUT.mkdir(parents=True, exist_ok=True)
    made = {}
    for name, fn in (("map-instruments.svg", map_instruments), ("map-coverage.svg", map_coverage), ("map-last24h.svg", map_last24h)):
        p = OUT / name
        p.write_text(fn(bm, snap, pts), encoding="utf-8")
        made[name] = p.stat().st_size
        print(p, made[name], "bytes")
    if CONTEXT_POP.exists():
        ctx = json.loads(CONTEXT_POP.read_text(encoding="utf-8"))
        p = OUT / "map-people.svg"
        p.write_text(map_people(bm, snap, pts, ctx), encoding="utf-8")
        made[p.name] = p.stat().st_size
        print(p, made[p.name], "bytes")
    meta = {"made_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "snapshot_as_of": snap["as_of"], "basemap": bm.get("note"), "basemap_source": bm.get("source"),
            "instruments": len(pts), "by_source": {k: sum(1 for p in pts if p["sid"] == k) for k in sorted({p["sid"] for p in pts})},
            "heard": sum(1 for p in pts if p["rx"] > 0), "silent": sum(1 for p in pts if p["rx"] == 0), "files": made,
            "context_population": (json.loads(CONTEXT_POP.read_text(encoding="utf-8")).get("source") if CONTEXT_POP.exists() else None),
            "rule": "Nothing drawn that basemap-belgrade.json and live-snapshot.json do not contain."}
    (OUT / "MAPS.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k != "files"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
