#!/usr/bin/env python3
"""baseline.py - what is USUAL here, at this hour, in our own record.

Why this exists. The entities see a six-hour window, so they cannot notice anything that takes longer
than six hours to show itself - and almost everything a city does is daily. "PM10 is 41" is a number;
"41, where this station usually shows 28 at this hour" is an observation. Nothing about the models
changes; the program simply computes what it already has and hands it over as a fact like any other.

What this is NOT. It is not a norm, a limit, a standard or a health threshold, and nothing here may be
worded as one. It is the median of what THIS record received from THIS station at THIS hour, over the
days it has been listening - a fact about the observatory, carrying its own sample size, and useless
for saying whether the air is safe.

The rules it keeps:
  - a bucket is published only with enough behind it (BUCKET_MIN_DAYS days, BUCKET_MIN_N values);
    a thin bucket is ABSENT, never filled in, because missing is not zero
  - a source that publishes no measurement time is bucketed by the hour it ARRIVED, and says so
  - only numbers are counted; a missing value contributes nothing and does not pull a median down
  - stations and parameters never mix

    python tools/baseline.py build      # rebuild every source it can
    python tools/baseline.py show S146  # print what it knows, for a person
"""
from __future__ import annotations
from contracts import observation_rows

import json
from contracts import row_clock, finite, atomic_json
import pathlib
import statistics
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROWS = ROOT / "data" / "live" / "rows"
OUT = ROOT / "data" / "live" / "derived" / "baseline"
SCHEMA = "beops-baseline/v2"

BUCKET_MIN_DAYS = 3       # fewer days than this is an anecdote, not a usual
BUCKET_MIN_N = 5          # and fewer values than this is one bad afternoon
MAX_DAYS = 30             # how far back a bucket may reach
NOT_A_MEASURE = {"headline", "planned_outage", "notice"}


def _p(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def _hour_of(row: dict) -> tuple[int | None, bool, str]:
    dt, frame = row_clock(row)
    return (dt.hour if dt else None), frame in ("measured", "corrected"), frame


def build_source(sid: str, now: datetime | None = None) -> dict | None:
    now = now or datetime.now(timezone.utc)
    d = ROWS / sid
    if not d.exists():
        return None
    seen: dict[tuple, list] = {}
    days: dict[tuple, set] = {}
    timed: dict[tuple, bool] = {}
    frames: dict[tuple, str] = {}
    clock_note = None
    units: dict[tuple, str] = {}
    names: dict[str, str] = {}
    first = last = None
    for f in sorted(d.glob("*.jsonl")):
        for r in observation_rows(f):
            par = r.get("parameter")
            val = r.get("result")
            if par in NOT_A_MEASURE or not finite(val):
                continue
            rx = _p(r.get("receivedTime"))
            if not rx or (now - rx).days > MAX_DAYS:
                continue
            hour, own, frame = _hour_of(r)
            if hour is None:
                continue
            if r.get("sourceClockNote"):
                clock_note = str(r["sourceClockNote"])
            st = str(r.get("station_name") or r.get("station_id") or "?")
            names[str(r.get("station_id"))] = st
            k = (st, str(par), hour, str(r.get("unit") or ""), frame)
            sample_time, _ = row_clock(r)
            if not sample_time or sample_time > now or (now - sample_time).days > MAX_DAYS:
                continue
            seen.setdefault(k, []).append(float(val))
            days.setdefault(k, set()).add(sample_time.date().isoformat())
            timed[k] = own
            frames[k] = frame
            if r.get("unit"):
                units[k] = str(r["unit"])
            first = rx if first is None or rx < first else first
            last = rx if last is None or rx > last else last
    buckets = {}
    thin = 0
    for k, vals in seen.items():
        nd = len(days[k])
        if nd < BUCKET_MIN_DAYS or len(vals) < BUCKET_MIN_N:
            thin += 1
            continue                      # absent on purpose: a thin bucket is not a usual
        vals.sort()
        buckets["|".join((k[0], k[1], "%02d" % k[2], k[3], k[4]))] = {
            "n": len(vals), "days": nd,
            "median": round(statistics.median(vals), 2),
            "p25": round(vals[len(vals) // 4], 2),
            "p75": round(vals[(3 * len(vals)) // 4], 2),
            "min": round(vals[0], 2), "max": round(vals[-1], 2),
            "unit": units.get(k), "hour_is_the_measurement_s_own": bool(timed[k]),
            "hour_read_from": frames.get(k, "measured"),
        }
    return {"schema": SCHEMA, "sid": sid, "made_at": now.isoformat().replace("+00:00", "Z"),
            "record_from": first.isoformat().replace("+00:00", "Z") if first else None,
            "record_to": last.isoformat().replace("+00:00", "Z") if last else None,
            "days_of_record": len({v for s in days.values() for v in s}),
            "min_days_per_bucket": BUCKET_MIN_DAYS, "min_values_per_bucket": BUCKET_MIN_N,
            "buckets_published": len(buckets), "buckets_too_thin_to_publish": thin,
            "what_this_is": "the median of what this record received from this station at this hour of "
                            "the day. A fact about the observatory, not a norm, a limit or a health "
                            "threshold, and not usable as one.",
            "clocks": sorted({v for v in frames.values()}),
            "source_clock_note": clock_note,
            "stations": names, "buckets": buckets}


def usual(base: dict | None, station: str, parameter: str, hour: int) -> dict | None:
    """What this station usually shows at this hour, or None when the record cannot yet say.

    `hour` must be read off the same clock the buckets were built on - for a source whose labels are
    corrected, that is the corrected hour, never the label. The caller is given `hour_read_from` on
    every bucket so a mismatch is visible rather than silent."""
    if not base:
        return None
    prefix = "|".join((str(station), str(parameter), "%02d" % int(hour)))
    matches = [v for k, v in (base.get("buckets") or {}).items() if k == prefix or k.startswith(prefix + "|")]
    return matches[0] if len(matches) == 1 else None  # ambiguous unit/clock is not a baseline


def load(sid: str) -> dict | None:
    p = OUT / f"{sid}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return None


def build(sids: list[str] | None = None) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    out = {}
    candidates = {p.name for p in ROWS.iterdir() if p.is_dir()} if ROWS.exists() else set()
    candidates.update(p.stem for p in OUT.glob("S*.json"))
    for sid in sorted(candidates):
        d = ROWS / sid
        if sids and d.name not in sids:
            continue
        b = build_source(d.name)
        if b is None:
            b = {"schema": SCHEMA, "sid": d.name, "buckets": {}, "buckets_published": 0, "state": "empty"}
        atomic_json(OUT / f"{d.name}.json", b)
        out[d.name] = b["buckets_published"]
    return out


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "build"
    if cmd == "build":
        if (ROOT / 'runtime' / 'MAINTENANCE').exists():
            print('BEOPS baseline paused for project maintenance')
            return 75
        res = build(argv[2:] or None)
        for sid, n in sorted(res.items(), key=lambda x: -x[1]):
            if n:
                print("%-8s %4d buckets" % (sid, n))
        empty = [s for s, n in res.items() if not n]
        if empty:
            print("not enough record yet:", ", ".join(sorted(empty)))
        return 0
    if cmd == "show":
        b = load(argv[2]) if len(argv) > 2 else None
        if not b:
            print("nothing built for that source")
            return 2
        print(f"{b['sid']}  {b['days_of_record']} days of record  "
              f"{b['buckets_published']} buckets published, {b['buckets_too_thin_to_publish']} too thin")
        for k, v in sorted(b["buckets"].items())[:40]:
            st, par, hh = k.split("|")[:3]
            mark = "" if v["hour_is_the_measurement_s_own"] else "  (hour of ARRIVAL, not of measurement)"
            print("  %-22s %-8s %sh  usual %7.2f %-8s  n=%-4d days=%d  [%.2f..%.2f]%s"
                  % (st, par, hh, v["median"], v.get("unit") or "", v["n"], v["days"], v["min"], v["max"], mark))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
