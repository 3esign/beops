#!/usr/bin/env python3
"""
fetch_static.py - the static and semi-static context of the city, taken once, lawfully, with a hash.

    python -B tools/fetch_static.py kontur           population per H3 hexagon for Serbia (Kontur, CC BY) -> evidence under S120
    python -B tools/fetch_static.py derive-kontur    -> public/context-population.json (hexes in the Belgrade window, representative point + people)
    python -B tools/fetch_static.py status           what context files exist, from which capture

Why this exists (research/STATIC_LAYERS.json is the register): the mind needs to know the SHAPE of
the city to think about what its instruments say - where people live, where it is dense, where it
is empty - and that knowledge must come from sources that permit it, captured once with their
hash, reduced to the few numbers a digest can carry ("about 9 000 people live within 1 km of the
Stari grad station"), never invented. One layer per question the mind will actually ask.

Rules: the source must have a permission capture in LEDGER.jsonl (same gate as the collector); the
raw file is stored unmodified under research/evidence/<sid>/<UTC>/ with a MANIFEST; the derived file
says what it is, at what resolution, from which capture, and carries the attribution the licence
asks for. Stdlib only: the GeoPackage is SQLite, read with sqlite3; its geometry blobs are parsed by
hand (GeoPackage binary header + WKB) - about forty lines, no GIS library.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import pathlib
import sqlite3
import struct
import sys
import tempfile
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from collect_daemon import fetch, gate, may_collect, iso, utcnow, stamp  # noqa: E402

REGISTER = ROOT / "research" / "STATIC_LAYERS.json"
PUBLIC = ROOT / "public"
BBOX = (20.15, 44.55, 20.85, 45.00)     # W, S, E, N - the Belgrade window of the studies


def layer(lid: str) -> dict:
    """A layer from the register, by its id - or by its sid or its file name, whichever the caller has.

    This raised `KeyError: 'id'` for every lookup from the day the register was rewritten, because the
    rewrite gave each layer a `file`, a `sid` and a `what` and no `id`, and this line still asked for
    one. Both entry points of this tool call it on their first line, so **the tool that builds the
    population layer could not start at all** - and nobody found out, because the layer it had already
    built was still sitting on disk and still correct. A builder that cannot run and an output that
    looks right are indistinguishable until somebody rebuilds (C-062).
    """
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    for x in reg["layers"]:
        if lid in (x.get("id"), x.get("sid"), x.get("file"),
                   pathlib.Path(str(x.get("file") or "")).stem):
            return {**x.get("provenance_as_the_file_carries_it", {}), **x}
    raise KeyError("no layer %r in the register; it holds: %s"
                   % (lid, ", ".join(str(x.get("id") or x.get("file")) for x in reg["layers"])))


def _manifest(sid: str, ts: str, files: list[dict], extra: dict) -> dict:
    d = ROOT / "research" / "evidence" / sid / ts
    d.mkdir(parents=True, exist_ok=True)
    man = {"sid": sid, "captured_at_utc": ts, "files": files, **extra}
    (d / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return man


# ------------------------------------------------------------------ Kontur
def kontur() -> dict:
    """Kontur Population (H3 resolution 8, ~460 m hexagons), Serbia, via HDX. CC BY 4.0."""
    L = layer("kontur-population")
    sid = L["sid"]
    ok, why = may_collect(sid, gate())
    if not ok:
        raise SystemExit(f"{sid} not permitted: {why}")
    ts = stamp(utcnow())
    d = ROOT / "research" / "evidence" / sid / ts
    d.mkdir(parents=True, exist_ok=True)
    files = []
    # 1. the dataset record from the HDX API (which resource is current is decided by the publisher, not by us)
    api = fetch(L["api_url"], 60, 5_000_000)
    p = d / "hdx_package_show.json"
    p.write_bytes(api["body"] or json.dumps({"status": api["status"], "error": api["error"]}).encode())
    files.append({"file": p.name, "url": L["api_url"], "status": api["status"], "bytes": p.stat().st_size,
                  "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "fetched_at": iso(utcnow())})
    url = None
    if api["status"] == 200 and api["body"]:
        doc = json.loads(api["body"].decode("utf-8"))
        for r in (doc.get("result") or {}).get("resources", []):
            u = r.get("download_url") or r.get("url") or ""
            if u.endswith(".gpkg.gz") and "_RS_" in u:
                url = u
                break
    if not url:
        raise SystemExit(f"no .gpkg.gz resource for RS in the HDX record (status {api['status']})")
    # 2. the file itself, unmodified
    res = fetch(url, 600, 400_000_000)
    okb = res["status"] == 200 and res["body"] and res["body"][:2] == b"\x1f\x8b"
    q = d / (url.rsplit("/", 1)[-1] if okb else "population.failed.txt")
    q.write_bytes(res["body"] if okb else json.dumps({"url": url, "status": res["status"], "error": res["error"]}).encode())
    files.append({"file": q.name, "url": url, "status": res["status"], "bytes": q.stat().st_size,
                  "sha256": hashlib.sha256(q.read_bytes()).hexdigest(), "fetched_at": iso(utcnow()), "transport": res["transport"]})
    print(q.name, res["status"], q.stat().st_size, "bytes", res["error"] or "")
    return _manifest(sid, ts, files, {"permission_capture": why, "layer": L["id"], "attribution": L["attribution"], "licence": L["licence"]})


# --- GeoPackage geometry (header + WKB), stdlib -------------------------------
def _gpkg_geom(blob: bytes) -> list:
    """Return the outer ring(s) of a Polygon/MultiPolygon as lists of (lon, lat)."""
    if blob[:2] != b"GP":
        return []
    flags = blob[3]
    env_type = (flags >> 1) & 0x07
    env_len = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}.get(env_type, 0)
    off = 8 + env_len
    bo = "<" if blob[off] == 1 else ">"
    gtype = struct.unpack_from(bo + "I", blob, off + 1)[0] & 0xFF
    off += 5

    def ring(o):
        n = struct.unpack_from(bo + "I", blob, o)[0]
        pts = struct.unpack_from(bo + "%dd" % (2 * n), blob, o + 4)
        return [(pts[2 * i], pts[2 * i + 1]) for i in range(n)], o + 4 + 16 * n

    def polygon(o):
        nr = struct.unpack_from(bo + "I", blob, o)[0]
        o += 4
        rings = []
        for _ in range(nr):
            r, o = ring(o)
            rings.append(r)
        return rings, o

    if gtype == 3:
        rings, _ = polygon(off)
        return [rings[0]] if rings else []
    if gtype == 6:
        n = struct.unpack_from(bo + "I", blob, off)[0]
        o = off + 4
        outers = []
        for _ in range(n):
            o += 5   # inner byte order + type
            rings, o = polygon(o)
            if rings:
                outers.append(rings[0])
        return outers
    return []


def derive_kontur() -> pathlib.Path:
    L = layer("kontur-population")
    sid = L["sid"]
    caps = sorted((ROOT / "research" / "evidence" / sid).glob("*/MANIFEST.json"))
    caps = [c for c in caps if json.loads(c.read_text(encoding="utf-8")).get("layer") == L["id"]]
    if not caps:
        raise SystemExit("no Kontur capture - run kontur first")
    man = json.loads(caps[-1].read_text(encoding="utf-8"))
    gz = next((caps[-1].parent / f["file"] for f in man["files"] if f["file"].endswith(".gpkg.gz")), None)
    if not gz or not gz.exists():
        raise SystemExit("capture holds no .gpkg.gz")
    hexes = []
    with tempfile.TemporaryDirectory() as td:
        gp = pathlib.Path(td) / "k.gpkg"
        with gzip.open(gz, "rb") as fin, open(gp, "wb") as fout:
            while True:
                chunk = fin.read(1 << 20)
                if not chunk:
                    break
                fout.write(chunk)
        con = sqlite3.connect(str(gp))
        table = con.execute("select table_name from gpkg_contents where data_type='features'").fetchone()[0]
        srs = con.execute("select srs_id from gpkg_geometry_columns where table_name=?", (table,)).fetchone()
        srs = int(srs[0]) if srs else 4326
        import math

        def to_wgs84(x, y):
            if srs == 3857:      # Kontur ships Web Mercator metres; the studies are WGS84 degrees
                return x / 6378137.0 * 180.0 / math.pi, (2 * math.atan(math.exp(y / 6378137.0)) - math.pi / 2) * 180.0 / math.pi
            return x, y
        cols = [r[1] for r in con.execute(f"pragma table_info('{table}')")]
        gcol = next(c for c in cols if c.lower() in ("geom", "geometry", "the_geom"))
        pcol = next(c for c in cols if "population" in c.lower())
        hcol = next((c for c in cols if c.lower() in ("h3", "h3_index", "hex")), None)
        W, S, E, N = BBOX
        for row in con.execute(f"select {gcol}, {pcol}{', ' + hcol if hcol else ''} from {table}"):
            outers = _gpkg_geom(row[0])
            if not outers:
                continue
            xs = [x for r in outers for x, _ in r]
            ys = [y for r in outers for _, y in r]
            cx, cy = to_wgs84(sum(xs) / len(xs), sum(ys) / len(ys))
            if not (W <= cx <= E and S <= cy <= N):
                continue
            hexes.append([round(cx, 5), round(cy, 5), int(round(row[1] or 0))] + ([row[2]] if hcol else []))
        con.close()
    # The downloaded resource names its edition; a dataset page may also list newer resources.
    import re
    match = re.search(r"_RS_(\d{4})(\d{2})(\d{2})", gz.name)
    release = "-".join(match.groups()) if match else "unknown resource edition"
    out = {"name": "context-population", "layer": L["id"], "source": {
        "sid": sid, "capture": man["captured_at_utc"], "srs_as_shipped": srs,
        "release": release, "demographic_reference_period": "Mixed source vintages; not established as a single census date."},
        "resolution": "H3 resolution 8; representative points displayed as schematic hexagons, not exact cell boundaries.",
        "attribution": f"Kontur Population, Serbia resource release {release}, CC BY 4.0; filtered by BEOPS.",
        "licence": L["licence"],
        "note": f"Modelled population per H3 cell from the {release} resource. Points are arithmetic means of supplied outer-ring vertices; symbols are schematic. Window and radius selections use those points, not administrative boundaries or exact population exposure.",
        "people_total": sum(h[2] for h in hexes), "hexes": hexes}
    PUBLIC.mkdir(parents=True, exist_ok=True)
    p = PUBLIC / "context-population.json"
    p.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(p, p.stat().st_size, "bytes;", len(hexes), "hexes;", out["people_total"], "people in the window")
    return p


def people_near(lat: float, lon: float, km: float = 1.0, ctx: dict | None = None) -> int | None:
    """Sum of hexagon populations whose representative point lies within `km` of (lat, lon). Used by the digest."""
    ctx = ctx or (json.loads((PUBLIC / "context-population.json").read_text(encoding="utf-8")) if (PUBLIC / "context-population.json").exists() else None)
    if not ctx or not ctx.get("hexes"):
        # A layer that is present and empty is not a city with nobody in it. Returning 0 here would
        # have let the digest say "nobody lives within a kilometre of this station", which is false
        # and indistinguishable from the true version. Missing is not zero (C-062).
        return None
    import math
    kx = 111.32 * math.cos(math.radians(lat))
    tot = 0
    for h in ctx["hexes"]:
        dx, dy = (h[0] - lon) * kx, (h[1] - lat) * 111.32
        if dx * dx + dy * dy <= km * km:
            tot += h[2]
    return tot


def status() -> dict:
    out = {}
    for f in PUBLIC.glob("context-*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        out[f.name] = {"layer": d.get("layer"), "source": d.get("source"), "entries": len(d.get("hexes") or d.get("features") or d.get("datasets") or []),
                       "bytes": f.stat().st_size}
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "kontur":
        kontur()
    elif cmd == "derive-kontur":
        derive_kontur()
    elif cmd == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
    else:
        raise SystemExit(__doc__)
