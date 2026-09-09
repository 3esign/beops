"""Bounded research probes, not a continuous collector. Python stdlib only.

No credentials, inference, full-page republication or certificate bypass.
Run with live (default), global, models or gtfs. Writes timestamped evidence metadata.
"""
import csv
import hashlib
import io
import json
import pathlib
import re
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
UA = "Beops-Research/0.1 (bounded source audit; no continuous polling)"
SOURCES = [
    ("rhmz-automatic", "https://www.hidmet.gov.rs/latin/osmotreni/automatske.php", "rhmz"),
    ("lybe-metar", "https://aviationweather.gov/api/data/metar?ids=LYBE&format=json", "metar"),
    ("sensor-community-box", "https://data.sensor.community/airrohr/v1/filter/box=44.70,20.27,44.92,20.62", "sensor"),
    ("beoeko", "https://www.beoeko.com/", "air"),
    ("rhmz-zemun", "https://www.hidmet.gov.rs/latin/osmotreni/nrt_tabela_grafik.php?hm_id=42045&period=7", "river"),
    ("parking-servis", "https://www.parking-servis.co.rs/lat/garaze-i-parkiralista", "parking"),
    ("bvk-planned", "https://www.bvk.rs/planirani-radovi/", "notice"),
    ("eds-today", "https://www.elektrodistribucija.rs/planirana-iskljucenja-beograd/Dan_1_Iskljucenja.htm", "notice"),
]
MODELS = [
    "intfloat/multilingual-e5-small", "BAAI/bge-m3", "classla/bcms-bertic-ner",
    "urchade/gliner_multi-v2.1", "amazon/chronos-bolt-tiny", "amazon/chronos-bolt-mini",
    "HuggingFaceTB/SmolVLM-256M-Instruct", "nvidia/segformer-b0-finetuned-ade-512-512",
    "openai/whisper-tiny", "LiquidAI/LFM2.5-1.2B-Instruct-GGUF",
]


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.stack, self.text = [], [], []

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.stack.append({"cells": [], "cell": None})
        elif tag in ("td", "th") and self.stack:
            self.stack[-1]["cell"] = []

    def handle_data(self, data):
        self.text.append(data)
        if self.stack and self.stack[-1]["cell"] is not None:
            self.stack[-1]["cell"].append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.stack:
            row = self.stack[-1]
            if row["cell"] is not None:
                row["cells"].append(" ".join(" ".join(row["cell"]).split()))
                row["cell"] = None
        elif tag == "tr" and self.stack:
            row = self.stack.pop()
            if row["cells"]:
                self.rows.append(row["cells"])


def get(url, limit=3_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    start = time.monotonic()
    with urllib.request.urlopen(req, timeout=15) as response:
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("response exceeds research byte limit")
        meta = {"url": url, "final_url": response.url, "status": response.status,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "http_date": response.headers.get("Date"), "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
                "content_type": response.headers.get("Content-Type"),
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "elapsed_ms": round(1000 * (time.monotonic() - start))}
        encoding = response.headers.get_content_charset() or "utf-8"
        return data, meta, encoding


def summarize(kind, data, encoding):
    if kind == "earthquake":
        obj = json.loads(data) if data else {"features": []}
        features = obj.get("features", [])
        return {"count": len(features), "metadata": obj.get("metadata"),
                "events": [{"id": f.get("id"), "coordinates": f.get("geometry", {}).get("coordinates"),
                            "properties": {k: f.get("properties", {}).get(k) for k in
                                ("time", "lastupdate", "updated", "mag", "magtype", "flynn_region", "place", "status")}}
                           for f in features[:5]],
                "limit": "regional context query, not city ground motion; empty valid response is not sensor failure"}
    if kind == "metar":
        rows = json.loads(data)
        return {"records": len(rows), "observations": [
            {k: r.get(k) for k in ("icaoId", "obsTime", "reportTime", "temp", "dewp", "wdir", "wspd", "altim")}
            for r in rows[:3]], "limit": "airport observation, not citywide temperature"}
    if kind == "sensor":
        rows = json.loads(data)
        if not isinstance(rows, list):
            raise ValueError("expected sensor list")
        nodes = {}
        for r in rows:
            sid = str(r.get("sensor", {}).get("id"))
            node = nodes.setdefault(sid, {"sensor_id": sid, "types": set(), "timestamps": []})
            node["types"].update(x.get("value_type", "") for x in r.get("sensordatavalues", []))
            if r.get("timestamp"):
                node["timestamps"].append(r["timestamp"])
        return {"record_count": len(rows), "unique_sensor_count": len(nodes),
                "bbox": [44.70, 20.27, 44.92, 20.62],
                "limit": "query rectangle is NOT Belgrade administrative boundary; sensors are not independent stations",
                "nodes": [{"sensor_id": n["sensor_id"], "types": sorted(n["types"]),
                           "first_timestamp": min(n["timestamps"], default=None),
                           "last_timestamp": max(n["timestamps"], default=None)} for n in nodes.values()]}
    parser = Tables()
    parser.feed(data.decode(encoding, errors="replace"))
    text = " ".join(" ".join(parser.text).split())
    if kind == "rhmz":
        names = {"Beograd", "Ko\u0161utnjak", "Baro\u0161evac"}
        return {"selected_rows": [r for r in parser.rows if any(c in names for c in r)],
                "date_tokens": list(dict.fromkeys(re.findall(r"\b\d{2}\.\d{2}\.\d{4}\b", text)))[:5],
                "time_tokens": list(dict.fromkeys(re.findall(r"\b\d{2}:\d{2}\b", text)))[:8],
                "limit": "source timezone and station identity require verification; no UTC conversion inferred"}
    if kind == "air":
        rows = [r for r in parser.rows if any("GZZJZ-BGD" in c for c in r)]
        return {"station_row_count": len(rows), "example_rows": rows[:3],
                "time_tokens": list(dict.fromkeys(re.findall(r"\d{2}\.\d{2}\.\d{4}.?\s+\d{2}:\d{2}", text)))[:3],
                "limit": "provisional hourly pollutant values; not a health recommendation"}
    if kind == "river":
        numeric_rows = [r for r in parser.rows if any(re.search(r"\d{2}:\d{2}", c) for c in r)
                        and len(" ".join(r)) < 140]
        return {"table_rows": len(parser.rows), "newest_table_rows": numeric_rows[:3],
                "oldest_table_rows": numeric_rows[-3:],
                "limit": "table extraction reconnaissance, units and time convention not normalized"}
    if kind == "parking":
        return {"has_live_label": "Trenutan broj slobodnih" in text or "Slobodna parking" in text,
                "table_count_rows": len(parser.rows),
                "limit": "HTML reachable is not proof of freshness; no supported measurement timestamp parsed"}
    return {"date_tokens": list(dict.fromkeys(re.findall(r"\b(?:\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})\b", text)))[:10],
            "table_rows": len(parser.rows), "limit": "planned notice, not measured service status"}


def gtfs_summary(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        files = {pathlib.PurePosixPath(i.filename).name: i for i in z.infolist() if not i.is_dir()}
        out = {"files": {k: {"bytes": v.file_size, "compressed": v.compress_size} for k, v in files.items()}}
        for name in ("calendar.txt", "calendar_dates.txt", "feed_info.txt", "stops.txt", "routes.txt"):
            info = files.get(name)
            if not info or info.file_size > 15_000_000:
                continue
            with z.open(info) as f:
                rows = list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")))
            out[name] = {"count": len(rows), "columns": list(rows[0]) if rows else []}
            for field in ("start_date", "end_date", "date", "feed_start_date", "feed_end_date"):
                values = sorted(r[field] for r in rows if r.get(field))
                if values:
                    out[name][field] = {"min": values[0], "max": values[-1]}
        return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "live"
    if mode not in ("live", "global", "models", "gtfs"):
        raise SystemExit("mode must be live, global, models or gtfs")
    sources = SOURCES if mode == "live" else [
        (m, "https://huggingface.co/api/models/" + m, "model") for m in MODELS]
    if mode == "gtfs":
        sources = [("belgrade-gtfs", "https://data.gov.rs/s/resources/gradski-javni-prevoz-u-beogradu-gtfs/20251031-111721/bgprev-belgrade-rs-2-.zip", "gtfs")]
    if mode == "global":
        start = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
        sources = [
            ("usgs-regional", "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude=44.817&longitude=20.456&maxradiuskm=300&limit=100&starttime=" + start, "earthquake"),
            ("emsc-regional", "https://www.seismicportal.eu/fdsnws/event/1/query?format=json&minlat=43&maxlat=46&minlon=18&maxlon=23&limit=100&starttime=" + start, "earthquake"),
        ]
    results = []
    for sid, url, kind in sources:
        result = {"id": sid, "url": url, "ok": False}
        try:
            data, meta, encoding = get(url, 24_000_000 if kind == "gtfs" else 3_000_000)
            result.update(meta)
            if kind == "model":
                obj = json.loads(data)
                result["summary"] = {"id": obj.get("id"), "revision": obj.get("sha"),
                    "pipeline_tag": obj.get("pipeline_tag"), "gated": obj.get("gated"),
                    "library_name": obj.get("library_name"), "safetensors": obj.get("safetensors"),
                    "license": obj.get("cardData", {}).get("license"),
                    "languages": obj.get("cardData", {}).get("language"),
                    "limit": "metadata only; no weights downloaded or inference tested"}
            elif kind == "gtfs":
                result["summary"] = gtfs_summary(data)
            else:
                result["summary"] = summarize(kind, data, encoding)
            result["ok"] = True
        except Exception as exc:
            result["error"] = type(exc).__name__ + ": " + str(exc)[:300]
        results.append(result)
        print(json.dumps(result, ensure_ascii=True), flush=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "evidence"
    folder.mkdir(exist_ok=True)
    target = folder / (mode + "-" + stamp + ".json")
    report = {"schema": "beops-research-probe/v1", "created_at": stamp, "mode": mode,
              "scope": "bounded audit; not operational monitoring or public reuse approval", "results": results}
    with target.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=True, indent=2)
    assert json.loads(target.read_text(encoding="utf-8")) == report
    print("REPORT " + str(target), flush=True)


if __name__ == "__main__":
    main()
