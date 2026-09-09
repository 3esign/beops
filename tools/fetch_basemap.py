#!/usr/bin/env python3
"""
fetch_basemap.py - a lawful base map for Belgrade from the national spatial data infrastructure.

    python -B tools/fetch_basemap.py capabilities            list WFS layers of the GeoSrbija services (no data)
    python -B tools/fetch_basemap.py fetch <layer> [<layer>…]   GetFeature for the Belgrade bbox, stored as evidence
    python -B tools/fetch_basemap.py derive                  simplified GeoJSON for the studies -> public/basemap-belgrade.json

Rules: the source (S193, ogc4u.geosrbija.rs) must have a permission capture in LEDGER.jsonl before
`fetch` runs (same gate as the collector); raw responses go under research/evidence/S193/<UTC>/ with a
MANIFEST and are never edited; the derived file is a simplification (Douglas-Peucker, stdlib) and says
so in its own metadata. Reuse: GeoSrbija states no open licence on its OGC page; the registry entry
carries the exact wording, and the derived base map is used for orientation on the studies and in the
document, attributed "GeoSrbija / Republički geodetski zavod", not redistributed as data.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from collect_daemon import fetch, gate, may_collect, iso, utcnow, stamp  # noqa: E402

SID = "S193"
BASE = "http://ogc4u.geosrbija.rs"
SERVICES = ["rpj", "ar", "tk250k", "ozp", "nstj", "aglomeracija"]
BBOX = (20.15, 44.55, 20.85, 45.00)  # lon/lat Belgrade administrative area, generous
EVID = ROOT / "research" / "evidence" / SID
OUT = ROOT / "public" / "basemap-belgrade.json"


def capabilities() -> dict:
    out = {}
    for svc in SERVICES:
        url = f"{BASE}/{svc}/wfs?service=WFS&request=GetCapabilities"
        res = fetch(url, 60, 5_000_000)
        layers = []
        if res["body"]:
            try:
                root = ET.fromstring(res["body"])
                for ft in root.iter():
                    if ft.tag.endswith("FeatureType"):
                        name = next((c.text for c in ft if c.tag.endswith("Name")), None)
                        title = next((c.text for c in ft if c.tag.endswith("Title")), None)
                        layers.append({"name": name, "title": title})
            except ET.ParseError as e:
                layers = [{"error": f"parse: {e}"}]
        out[svc] = {"status": res["status"], "error": res["error"], "layers": layers}
        print(svc, res["status"], res["error"] or f"{len(layers)} layers")
        for l in layers[:60]:
            print("   ", l.get("name"), "·", l.get("title"))
    return out


def fetch_layers(layers: list[str]) -> dict:
    ok, why = may_collect(SID, gate())
    if not ok:
        raise SystemExit(f"{SID} not permitted: {why}")
    ts = stamp(utcnow())
    d = EVID / ts
    d.mkdir(parents=True, exist_ok=True)
    manifest = {"sid": SID, "captured_at_utc": ts, "permission_capture": why, "bbox_wsen": BBOX, "files": []}
    for layer in layers:
        svc = layer.split(":")[0] if ":" in layer else "rpj"
        lname = layer if ":" in layer else f"{svc}:{layer}"
        for fmt in ("application/json", "json", "GEOJSON"):
            url = (f"{BASE}/{svc}/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName={quote(lname)}"
                   f"&outputFormat={quote(fmt)}&srsName=EPSG:4326&bbox={BBOX[1]},{BBOX[0]},{BBOX[3]},{BBOX[2]},EPSG:4326")
            res = fetch(url, 180, 80_000_000)
            body = res["body"]
            if res["status"] == 200 and body and body.lstrip()[:1] == b"{":
                break
            body = None
        fname = re.sub(r"[^A-Za-z0-9_.-]", "_", lname) + (".geojson" if body else ".failed.txt")
        p = d / fname
        if body:
            p.write_bytes(body)
        else:
            p.write_text(json.dumps({"url": url, "status": res["status"], "error": res["error"],
                                     "head": (res["body"] or b"")[:400].decode("utf-8", "replace")}, ensure_ascii=False, indent=1), encoding="utf-8")
        manifest["files"].append({"layer": lname, "file": fname, "url": url, "status": res["status"],
                                  "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                                  "fetched_at": iso(utcnow()), "transport": res["transport"]})
        print(lname, res["status"], p.name, p.stat().st_size, "bytes")
    (d / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


# ------------------------------------------------------------ simplification
def _dp(points: list, eps: float) -> list:
    if len(points) < 3:
        return points
    ax, ay = points[0]
    bx, by = points[-1]
    dx, dy = bx - ax, by - ay
    n = (dx * dx + dy * dy) ** 0.5 or 1e-12
    best, idx = -1.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        dist = abs(dy * px - dx * py + bx * ay - by * ax) / n
        if dist > best:
            best, idx = dist, i
    if best > eps:
        return _dp(points[:idx + 1], eps)[:-1] + _dp(points[idx:], eps)
    return [points[0], points[-1]]


def _dp_ring(points: list, eps: float) -> list:
    """Douglas-Peucker for a CLOSED ring. Running _dp directly on a ring whose first and last point
    are the same collapses it to two points - the base line has zero length, so every vertex measures
    zero distance from it. Split the ring at the vertex farthest from its start, simplify the two
    open halves, and close it again."""
    pts = [tuple(c[:2]) for c in points]
    if len(pts) < 5:
        return pts
    closed = pts[0] == pts[-1]
    body = pts[:-1] if closed else pts
    ax, ay = body[0]
    far = max(range(1, len(body)), key=lambda i: (body[i][0] - ax) ** 2 + (body[i][1] - ay) ** 2)
    first = _dp(body[:far + 1], eps)
    second = _dp(body[far:] + [body[0]], eps)
    ring = first[:-1] + second
    if len(ring) < 4:
        return pts
    return ring


def _simplify_geom(g: dict, eps: float) -> dict:
    t = g.get("type")
    if t == "Polygon":
        return {"type": t, "coordinates": [_dp_ring(ring, eps) for ring in g["coordinates"]]}
    if t == "MultiPolygon":
        return {"type": t, "coordinates": [[_dp_ring(ring, eps) for ring in poly] for poly in g["coordinates"]]}
    if t == "LineString":
        return {"type": t, "coordinates": _dp([tuple(c[:2]) for c in g["coordinates"]], eps)}
    if t == "MultiLineString":
        return {"type": t, "coordinates": [_dp([tuple(c[:2]) for c in ln], eps) for ln in g["coordinates"]]}
    return g


def derive(eps: float = 0.0006) -> pathlib.Path:
    caps = sorted(EVID.glob("*/MANIFEST.json"))
    if not caps:
        raise SystemExit("no capture under research/evidence/S193 - run fetch first")
    man = json.loads(caps[-1].read_text(encoding="utf-8"))
    out = {"type": "FeatureCollection", "name": "basemap-belgrade",
           "note": "Simplified (Douglas-Peucker, eps %.4f deg) from GeoSrbija WFS responses stored as evidence; orientation only, not a data product. Attribution: GeoSrbija / Republički geodetski zavod." % eps,
           "source": {"sid": SID, "capture": man["captured_at_utc"], "layers": [f["layer"] for f in man["files"] if f["status"] == 200]},
           "features": []}
    for f in man["files"]:
        if f["status"] != 200 or not f["file"].endswith(".geojson"):
            continue
        fc = json.loads((caps[-1].parent / f["file"]).read_text(encoding="utf-8"))
        for feat in fc.get("features", []):
            props = feat.get("properties") or {}
            keep = {k: v for k, v in props.items() if isinstance(v, (str, int, float)) and len(str(v)) < 80}
            out["features"].append({"type": "Feature", "layer": f["layer"], "properties": keep,
                                    "geometry": _simplify_geom(feat["geometry"], eps)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(OUT, OUT.stat().st_size, "bytes,", len(out["features"]), "features")
    return OUT


# ---------------------------------------------------------------- nominatim
NOMINATIM_SID = "S194"
MUNICIPALITIES = ["Stari grad", "Vračar", "Savski venac", "Novi Beograd", "Zemun", "Palilula", "Zvezdara", "Voždovac",
                  "Čukarica", "Rakovica", "Surčin", "Grocka", "Obrenovac", "Lazarevac", "Mladenovac", "Sopot", "Barajevo"]


def nominatim() -> dict:
    """Municipality outlines from OpenStreetMap via Nominatim (ODbL; © OpenStreetMap contributors).

    Why: the national SDI's OGC endpoints answered HTTP 401 on 2026-09-08 (S193 - an account is
    required). Nominatim's usage policy allows at most one request per second with an identifying
    User-Agent; this makes 17 requests, one per municipality, once, and stores every response as
    evidence. The result is orientation geometry, attributed, never redistributed as a data product."""
    import time
    ok, why = may_collect(NOMINATIM_SID, gate())
    if not ok:
        raise SystemExit(f"{NOMINATIM_SID} not permitted: {why}")
    ts = stamp(utcnow())
    d = ROOT / "research" / "evidence" / NOMINATIM_SID / ts
    d.mkdir(parents=True, exist_ok=True)
    manifest = {"sid": NOMINATIM_SID, "captured_at_utc": ts, "permission_capture": why, "files": [],
                "attribution": "© OpenStreetMap contributors, ODbL 1.0", "policy": "1 request/s, identifying User-Agent"}
    for m in MUNICIPALITIES:
        q = quote(f"Gradska opština {m}, Beograd, Srbija")
        url = f"https://nominatim.openstreetmap.org/search?q={q}&format=jsonv2&polygon_geojson=1&limit=3&countrycodes=rs"
        res = fetch(url, 60, 20_000_000)
        fname = re.sub(r"[^A-Za-z0-9_.-]", "_", m) + (".json" if res["status"] == 200 and res["body"] else ".failed.txt")
        p = d / fname
        p.write_bytes(res["body"] if res["status"] == 200 and res["body"] else json.dumps({"url": url, "status": res["status"], "error": res["error"]}).encode())
        manifest["files"].append({"municipality": m, "file": fname, "url": url, "status": res["status"], "bytes": p.stat().st_size,
                                  "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "fetched_at": iso(utcnow())})
        print(m, res["status"], p.stat().st_size, "bytes")
        time.sleep(1.2)
    (d / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


def derive_nominatim(eps: float = 0.0008) -> pathlib.Path:
    caps = sorted((ROOT / "research" / "evidence" / NOMINATIM_SID).glob("*/MANIFEST.json"))
    if not caps:
        raise SystemExit("no Nominatim capture - run nominatim first")
    man = json.loads(caps[-1].read_text(encoding="utf-8"))
    out = {"type": "FeatureCollection", "name": "basemap-belgrade",
           "note": "Municipality outlines simplified (Douglas-Peucker, eps %.4f deg) from OpenStreetMap via Nominatim, stored as evidence under research/evidence/%s; orientation only. © OpenStreetMap contributors (ODbL)." % (eps, NOMINATIM_SID),
           "source": {"sid": NOMINATIM_SID, "capture": man["captured_at_utc"]}, "features": []}
    for f in man["files"]:
        if f["status"] != 200 or not f["file"].endswith(".json"):
            continue
        cands = json.loads((caps[-1].parent / f["file"]).read_text(encoding="utf-8"))
        best = next((c for c in cands if c.get("osm_type") == "relation" and c.get("geojson", {}).get("type") in ("Polygon", "MultiPolygon")), None)
        if not best:
            out.setdefault("missing", []).append(f["municipality"])
            continue
        out["features"].append({"type": "Feature", "properties": {"name": f["municipality"], "osm_id": best.get("osm_id"), "display_name": best.get("display_name")},
                                "geometry": _simplify_geom(best["geojson"], eps)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(OUT, OUT.stat().st_size, "bytes,", len(out["features"]), "features; missing:", out.get("missing", []))
    return OUT


# ------------------------------------------------------------------ ohsome
OHSOME_SID = "S126"
OHSOME_BBOX = "20.15,44.35,20.85,45.00"


def ohsome() -> dict:
    """Municipality boundaries and the two rivers from OpenStreetMap through the ohsome API (HeiGIT),
    which is permitted (S126, capture 2026-09-06) and built for extraction, unlike Nominatim whose
    robots.txt refuses /search (S194, refused and recorded). Two requests, stored as evidence.
    Attribution: © OpenStreetMap contributors (ODbL); ohsome API, HeiGIT."""
    from urllib.parse import urlencode
    ok, why = may_collect(OHSOME_SID, gate())
    if not ok:
        raise SystemExit(f"{OHSOME_SID} not permitted: {why}")
    ts = stamp(utcnow())
    d = ROOT / "research" / "evidence" / OHSOME_SID / ts
    d.mkdir(parents=True, exist_ok=True)
    manifest = {"sid": OHSOME_SID, "captured_at_utc": ts, "permission_capture": why, "files": [],
                "attribution": "© OpenStreetMap contributors (ODbL 1.0); ohsome API, HeiGIT"}
    jobs = [("municipalities", {"bboxes": OHSOME_BBOX, "filter": "boundary=administrative and admin_level in (8,9) and type:relation",
                                "time": "2026-09-01", "properties": "tags", "clipGeometry": "false"}),
            ("rivers", {"bboxes": OHSOME_BBOX, "filter": "waterway=river and type:way", "time": "2026-09-01",
                        "properties": "tags", "clipGeometry": "true"})]
    for name, params in jobs:
        url = "https://api.ohsome.org/v1/elements/geometry?" + urlencode(params)
        res = fetch(url, 240, 60_000_000)
        okb = res["status"] == 200 and res["body"] and res["body"].lstrip()[:1] == b"{"
        p = d / (name + (".geojson" if okb else ".failed.txt"))
        p.write_bytes(res["body"] if okb else json.dumps({"url": url, "status": res["status"], "error": res["error"],
                                                           "head": (res["body"] or b"")[:300].decode("utf-8", "replace")}).encode())
        manifest["files"].append({"job": name, "file": p.name, "url": url, "status": res["status"], "bytes": p.stat().st_size,
                                  "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "fetched_at": iso(utcnow()), "transport": res["transport"]})
        print(name, res["status"], p.name, p.stat().st_size, "bytes", res["error"] or "")
    (d / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


def derive_ohsome(eps: float = 0.0008) -> pathlib.Path:
    caps = sorted((ROOT / "research" / "evidence" / OHSOME_SID).glob("*/MANIFEST.json"))
    caps = [c for c in caps if any(f.get("job") for f in json.loads(c.read_text(encoding="utf-8"))["files"])]
    if not caps:
        raise SystemExit("no ohsome base-map capture - run ohsome first")
    man = json.loads(caps[-1].read_text(encoding="utf-8"))
    out = {"type": "FeatureCollection", "name": "basemap-belgrade",
           "note": "Municipality boundaries (admin_level 8/9) and river centrelines from OpenStreetMap via the ohsome API, simplified (Douglas-Peucker, eps %.4f deg), stored as evidence under research/evidence/%s; orientation only. © OpenStreetMap contributors (ODbL); ohsome API, HeiGIT." % (eps, OHSOME_SID),
           "source": {"sid": OHSOME_SID, "capture": man["captured_at_utc"]}, "features": []}
    wanted = {m.lower() for m in MUNICIPALITIES}
    for f in man["files"]:
        if f["status"] != 200 or not f["file"].endswith(".geojson"):
            continue
        fc = json.loads((caps[-1].parent / f["file"]).read_text(encoding="utf-8"))
        for feat in fc.get("features", []):
            props = feat.get("properties") or {}
            nm = props.get("name") or ""
            if f["job"] == "municipalities":
                base = nm.replace("Gradska opština ", "").replace("Општина ", "").replace("Opština ", "").strip()
                if base.lower() not in wanted or feat["geometry"]["type"] not in ("Polygon", "MultiPolygon"):
                    continue
                out["features"].append({"type": "Feature", "layer": "municipality", "properties": {"name": base, "admin_level": props.get("admin_level"), "osm_id": props.get("@osmId")},
                                        "geometry": _simplify_geom(feat["geometry"], eps)})
            else:
                if nm.lower() not in ("sava", "dunav", "danube", "сава", "дунав") and not nm.lower().startswith(("sava", "dunav")):
                    continue
                if feat["geometry"]["type"] not in ("LineString", "MultiLineString"):
                    continue
                out["features"].append({"type": "Feature", "layer": "river", "properties": {"name": nm, "osm_id": props.get("@osmId")},
                                        "geometry": _simplify_geom(feat["geometry"], eps / 2)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    names = sorted({f["properties"]["name"] for f in out["features"] if f["layer"] == "municipality"})
    print(OUT, OUT.stat().st_size, "bytes;", len(names), "municipalities:", names, "; river segments:", sum(1 for f in out["features"] if f["layer"] == "river"))
    return OUT


# ----------------------------------------------------------- Natural Earth
# Why this route exists: every richer route to a Belgrade base map was closed, and each refusal is
# recorded rather than worked around - GeoSrbija WFS answered 401 (S193, an account is required),
# Nominatim's robots.txt disallows /search (S194), the ohsome API answered 403 to our agent (S126),
# overpass-api.de's robots.txt disallows /api/ (S142) and download.geofabrik.de's robots.txt
# disallows *.shp.zip and *.osm.pbf (S127). Natural Earth is public domain, served without a
# robots.txt restriction, and offered explicitly for reuse. It is coarse - 1:10 million - so what it
# can honestly give is the two rivers and the built-up footprint, not municipality boundaries. The
# derived file says its own scale, so no reader mistakes a generalised line for a surveyed one.
NE_SID = "S98"
NE_BASE = "https://naturalearth.s3.amazonaws.com"
NE_LAYERS = {
    "rivers_main": ("10m_physical", "ne_10m_rivers_lake_centerlines", "river"),
    "rivers": ("10m_physical", "ne_10m_rivers_europe", "river"),
    "lakes": ("10m_physical", "ne_10m_lakes_europe", "lake"),
    "urban": ("10m_cultural", "ne_10m_urban_areas", "urban"),
}
NE_BBOX = (20.15, 44.55, 20.85, 45.00)  # W, S, E, N


def naturalearth() -> dict:
    """Download the three public-domain Natural Earth layers, unchanged, as evidence."""
    ok, why = may_collect(NE_SID, gate())
    if not ok:
        raise SystemExit(f"{NE_SID} not permitted: {why}")
    ts = stamp(utcnow())
    d = ROOT / "research" / "evidence" / NE_SID / ts
    d.mkdir(parents=True, exist_ok=True)
    manifest = {"sid": NE_SID, "captured_at_utc": ts, "permission_capture": why, "files": [],
                "attribution": "Made with Natural Earth. Free vector and raster map data @ naturalearthdata.com (public domain).",
                "scale": "1:10 000 000 - generalised; suitable for orientation, not for measurement"}
    for job, (folder, name, _kind) in NE_LAYERS.items():
        url = f"{NE_BASE}/{folder}/{name}.zip"
        res = fetch(url, 240, 60_000_000)
        okb = res["status"] == 200 and res["body"] and res["body"][:2] == b"PK"
        p = d / (name + (".zip" if okb else ".failed.txt"))
        p.write_bytes(res["body"] if okb else json.dumps(
            {"url": url, "status": res["status"], "error": res["error"],
             "head": (res["body"] or b"")[:300].decode("utf-8", "replace")}).encode())
        manifest["files"].append({"job": job, "file": p.name, "url": url, "status": res["status"],
                                  "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                                  "fetched_at": iso(utcnow()), "transport": res["transport"]})
        print(job, res["status"], p.name, p.stat().st_size, "bytes", res["error"] or "")
    (d / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


# --- minimal ESRI shapefile reader (stdlib only: struct + zipfile) -----------
def _dbf_records(data: bytes) -> list:
    import struct
    if len(data) < 32:
        return []
    n_rec, hdr_len, rec_len = struct.unpack_from("<IHH", data, 4)
    fields, off = [], 32
    while off < hdr_len - 1 and data[off] != 0x0D:
        raw = data[off:off + 32]
        fname = raw[:11].split(b"\x00")[0].decode("latin-1").strip()
        flen = raw[16]
        fields.append((fname, flen))
        off += 32
    out = []
    for i in range(n_rec):
        base = hdr_len + i * rec_len
        if base + rec_len > len(data):
            break
        pos, row = base + 1, {}
        for fname, flen in fields:
            raw = data[pos:pos + flen]
            pos += flen
            try:
                val = raw.decode("utf-8")
            except UnicodeDecodeError:
                val = raw.decode("latin-1")
            val = val.replace("\x00", "").strip()
            row[fname] = val
        out.append(row)
    return out


def _shp_shapes(data: bytes) -> list:
    """Return [{'type': 'LineString'|'Polygon'|None, 'parts': [[(lon,lat),…],…], 'bbox': (w,s,e,n)}]."""
    import struct
    shapes, off, end = [], 100, len(data)
    while off + 8 <= end:
        _num, clen = struct.unpack_from(">II", data, off)
        off += 8
        body = off
        stype = struct.unpack_from("<i", data, body)[0]
        if stype in (3, 5, 13, 15, 23, 25):          # PolyLine / Polygon (and Z/M variants)
            w, s, e, n = struct.unpack_from("<4d", data, body + 4)
            nparts, npoints = struct.unpack_from("<ii", data, body + 36)
            parts = list(struct.unpack_from("<%di" % nparts, data, body + 44))
            pbase = body + 44 + 4 * nparts
            pts = struct.unpack_from("<%dd" % (2 * npoints), data, pbase)
            rings = []
            for k, start in enumerate(parts):
                stop = parts[k + 1] if k + 1 < nparts else npoints
                rings.append([(pts[2 * i], pts[2 * i + 1]) for i in range(start, stop)])
            shapes.append({"type": "Polygon" if stype in (5, 15, 25) else "LineString",
                           "parts": rings, "bbox": (w, s, e, n)})
        else:
            shapes.append({"type": None, "parts": [], "bbox": None})
        off += clen * 2
    return shapes


def _read_layer(zip_path: pathlib.Path, name: str) -> list:
    import zipfile
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        shp = next(n for n in names if n.endswith(name + ".shp") or n.endswith(".shp"))
        dbf = next(n for n in names if n.endswith(shp[:-4] + ".dbf"))
        shapes = _shp_shapes(z.read(shp))
        rows = _dbf_records(z.read(dbf))
    return [(s, rows[i] if i < len(rows) else {}) for i, s in enumerate(shapes)]


def _bbox_hits(bb, box=NE_BBOX) -> bool:
    if not bb:
        return False
    w, s, e, n = bb
    return not (e < box[0] or w > box[2] or n < box[1] or s > box[3])


def _clip_runs(pts: list, box=NE_BBOX, pad: float = 0.08) -> list:
    """Split a line into the runs of points that lie inside the padded window (no invented vertices)."""
    W, S, E, N = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    runs, cur = [], []
    for x, y in pts:
        if W <= x <= E and S <= y <= N:
            cur.append((round(x, 5), round(y, 5)))
        else:
            if len(cur) > 1:
                runs.append(cur)
            cur = []
    if len(cur) > 1:
        runs.append(cur)
    return runs


def derive_naturalearth(eps: float = 0.0004) -> pathlib.Path:
    caps = sorted((ROOT / "research" / "evidence" / NE_SID).glob("*/MANIFEST.json"))
    if not caps:
        raise SystemExit("no Natural Earth capture - run naturalearth first")
    man = json.loads(caps[-1].read_text(encoding="utf-8"))
    d = caps[-1].parent
    out = {"type": "FeatureCollection", "name": "basemap-belgrade",
           "note": ("Rivers, lakes and the built-up footprint from Natural Earth 1:10m (public domain), "
                    "clipped to the Belgrade window and simplified (Douglas-Peucker, eps %.4f deg). "
                    "Generalised at 1:10 million: this is orientation, not survey. No municipality "
                    "boundaries - every route to them was refused and the refusals are recorded "
                    "(S193 401, S194 robots, S126 403, S142 robots, S127 robots). "
                    "Made with Natural Earth." % eps),
           "scale": "1:10000000", "source": {"sid": NE_SID, "capture": man["captured_at_utc"]},
           "attribution": man.get("attribution"), "features": []}
    counts = {}
    for f in man["files"]:
        if f["status"] != 200 or not f["file"].endswith(".zip"):
            continue
        job = f["job"]
        kind = NE_LAYERS[job][2]
        for shape, row in _read_layer(d / f["file"], NE_LAYERS[job][1]):
            if not shape["type"] or not _bbox_hits(shape["bbox"]):
                continue
            nm = (row.get("name") or row.get("NAME") or row.get("name_en") or "").strip()
            if kind == "river":
                geoms = [g for part in shape["parts"] for g in _clip_runs(part)]
                for g in geoms:
                    out["features"].append({"type": "Feature", "layer": "river",
                                            "properties": {"name": nm},
                                            "geometry": _simplify_geom({"type": "LineString", "coordinates": g}, eps)})
                counts[kind] = counts.get(kind, 0) + len(geoms)
            else:
                rings = [[(round(x, 5), round(y, 5)) for x, y in part] for part in shape["parts"] if len(part) > 3]
                if not rings:
                    continue
                out["features"].append({"type": "Feature", "layer": kind, "properties": {"name": nm},
                                        "geometry": _simplify_geom({"type": "Polygon", "coordinates": rings}, eps)})
                counts[kind] = counts.get(kind, 0) + 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    rivers = sorted({f["properties"]["name"] for f in out["features"] if f["layer"] == "river" and f["properties"]["name"]})
    print(OUT, OUT.stat().st_size, "bytes;", counts, "; named rivers:", rivers)
    return OUT


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "capabilities"
    if cmd == "capabilities":
        capabilities()
    elif cmd == "fetch":
        fetch_layers(sys.argv[2:])
    elif cmd == "derive":
        derive()
    elif cmd == "nominatim":
        nominatim()
    elif cmd == "derive-nominatim":
        derive_nominatim()
    elif cmd == "ohsome":
        ohsome()
    elif cmd == "derive-ohsome":
        derive_ohsome()
    elif cmd == "naturalearth":
        naturalearth()
    elif cmd == "derive-naturalearth":
        derive_naturalearth()
    else:
        raise SystemExit(__doc__)
