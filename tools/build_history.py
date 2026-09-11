#!/usr/bin/env python3
"""
build_history.py - fold the stored rows into hourly buckets, so the site can show how values
move over a window longer than the live snapshot's 24 hours.

    python -B tools/build_history.py            write public/history.json

The rules this file exists to keep, and which a chart makes very easy to break:

  * An hour with no reception is NOT a zero and NOT a straight line between its neighbours.
    Absent hours are simply absent from the series, and `hours_expected` vs `hours_present`
    says how much of the window actually exists. A reader can then see that a "daily mean"
    over four of twenty-four hours is not a daily mean.
  * A measurement time and a reception time are different clocks. Rows whose source publishes
    no measurement time (parking is the standing example) are bucketed by RECEPTION and the
    series is marked `time_basis: "received"`. They are never mixed into a series bucketed by
    measurement time - the mixture would be a lie about when the city was in that state.
  * `result: null` is a missing value, not a zero, and never enters min/mean/max. The count of
    such rows is kept, because "the instrument answered and had nothing to say" is a fact.
  * Text rows (a headline, an outage notice) have no numeric result. They get a count per hour
    and nothing else - counting notices is honest, averaging them is not.
  * A mean here is the mean of the rows we received in that hour, not of the hour. For SEPA
    that is one published hourly mean; for citizen sensors it is however many readings arrived.
    `n` is on every bucket so the difference is visible rather than implied.

The output is small by construction (buckets, not rows), so it can grow to months without the
site growing with it.
"""
from __future__ import annotations
from contracts import observation_rows

import json
from contracts import row_clock, finite
import pathlib
import sys
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROWS = ROOT / "data" / "live" / "rows"
OUT = ROOT / "public" / "history.json"
CONFIG = ROOT / "research" / "COLLECTORS.json"

MAX_DAYS = 92            # a quarter of hourly buckets is plenty for a page; older rows stay on disk
SCHEMA = "beops-history/v2"


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(s):
    """An hourly mean's phenomenonTime is legitimately an INTERVAL, and this project stores it as
    one - either the object {"start": ..., "end": ...} that SEPA's hourly means carry, or the ISO
    "start/end" form. The bucket is the END, matching snapshots, baseline, latency and scoring.
    The original interval remains in the source row."""
    if isinstance(s, dict):
        s = s.get("end")
    if not s or not isinstance(s, str):
        return None
    if "/" in s:
        s = s.split("/", 1)[1]
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def hour_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H")


def load_config() -> dict:
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {s["sid"]: s for s in cfg.get("sources", [])}


def fold(now: datetime | None = None) -> dict:
    """One pass over every stored row; nothing is held in memory but the buckets."""
    now = now or datetime.now(timezone.utc)
    floor = now - timedelta(days=MAX_DAYS)
    cfg = load_config()
    series: dict[str, dict] = {}
    unparsed: dict[str, int] = {}

    for sid_dir in sorted(p for p in ROWS.iterdir() if p.is_dir()) if ROWS.exists() else []:
        sid = sid_dir.name
        for f in sorted(sid_dir.glob("*.jsonl")):
          for r in observation_rows(f):
                ds = r.get("datastream")
                if not ds:
                    continue

                untimed = bool(r.get("phenomenonTimeUnknown"))
                if untimed:
                    t, basis = parse_time(r.get("receivedTime")), "received"
                else:
                    t, basis = row_clock(r)
                    if t is None:
                        # The row claims a measurement time this program cannot read. Falling back to
                        # the reception clock here would quietly relabel a measurement as a reception,
                        # which is the one substitution this project does not make. Count it and drop it.
                        unparsed[sid] = unparsed.get(sid, 0) + 1
                        continue
                if t is None or t < floor or t > now + timedelta(hours=1):
                    continue

                key = f"{sid}|{ds}|{basis}"
                if key in series and series[key].get("unit") != r.get("unit"):
                    key += "|unit=" + str(r.get("unit"))
                s = series.get(key)
                if s is None:
                    s = series[key] = {
                        "sid": sid, "datastream": ds,
                        "station": r.get("station_name") or r.get("station_id"),
                        "parameter": r.get("parameter"), "unit": r.get("unit"),
                        "time_basis": basis,
                        "cadence_seconds": (cfg.get(sid) or {}).get("cadence_seconds"),
                        "buckets": {},
                    }
                b = s["buckets"].setdefault(hour_key(t), {"n": 0, "missing": 0, "vals": []})
                b["n"] += 1
                v = r.get("result")
                if finite(v):
                    b["vals"].append(float(v))
                else:
                    b["missing"] += 1             # answered, nothing to say - a fact, not a zero

    out_series = []
    for key, s in sorted(series.items()):
        buckets = {}
        for hk, b in sorted(s["buckets"].items()):
            vals = b["vals"]
            row = {"n": b["n"]}
            if b["missing"]:
                row["missing"] = b["missing"]
            if vals:
                row["min"] = round(min(vals), 4)
                row["max"] = round(max(vals), 4)
                row["mean"] = round(sum(vals) / len(vals), 4)
                row["last"] = round(vals[-1], 4)
            buckets[hk] = row
        if not buckets:
            continue
        hours = sorted(buckets)
        first = datetime.strptime(hours[0], "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
        last = datetime.strptime(hours[-1], "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
        expected = int((last - first).total_seconds() // 3600) + 1
        numeric = any("mean" in b for b in buckets.values())
        out_series.append({
            **{k: s[k] for k in ("sid", "datastream", "station", "parameter", "unit",
                                 "time_basis", "cadence_seconds")},
            "kind": "numeric" if numeric else "count",
            "first_hour": hours[0], "last_hour": hours[-1],
            "hours_present": len(buckets), "hours_expected": expected,
            "buckets": buckets,
        })

    covered = [s for s in out_series if s["hours_present"]]
    earliest = min((s["first_hour"] for s in covered), default=None)
    latest = max((s["last_hour"] for s in covered), default=None)
    return {
        "schema": SCHEMA,
        "built": iso(now),
        "history_starts": earliest,
        "history_ends": latest,
        "hours_of_history": (int((datetime.strptime(latest, "%Y-%m-%dT%H") -
                                  datetime.strptime(earliest, "%Y-%m-%dT%H")).total_seconds() // 3600) + 1)
                            if earliest and latest else 0,
        "note": ("Hourly buckets folded from the stored rows. An absent hour is absent, never a zero and "
                 "never a line drawn across the gap; hours_present against hours_expected says how much of "
                 "the span exists. A series whose source publishes no measurement time is bucketed by "
                 "reception and says so in time_basis. n is the number of rows received in that hour, not "
                 "a claim about how many measurements the instrument made."),
        "unreadable_measurement_times": unparsed,   # rows dropped rather than moved to another clock
        "series": out_series,
    }


def main() -> int:
    data = fold()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes; {len(data['series'])} series, "
          f"{data['hours_of_history']} h of history from {data['history_starts']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
