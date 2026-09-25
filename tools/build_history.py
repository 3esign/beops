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
  * A scalar mean uses the current logical observations assigned to an hour. Revisions of one
    source-labelled observation replace it; receptions are not extra measurements. Source-declared
    interval means are labelled separately. Circular directions retain unit-vector sums and counts,
    including undefined resultants. Counts, text and unknown types get no automatic arithmetic mean.

The output is small by construction (buckets, not rows), so it can grow to months without the
site growing with it.
"""
from __future__ import annotations
from contracts import observation_rows

import json
import math
from contracts import row_clock, finite, observation_identity, utc, parameter_semantics, direction_summary, PARAMETER_SEMANTICS
import pathlib
import sys
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROWS = ROOT / "data" / "live" / "rows"
OUT = ROOT / "public" / "history.json"
CONFIG = ROOT / "research" / "COLLECTORS.json"

MAX_DAYS = 92            # a quarter of hourly buckets is plenty for a page; older rows stay on disk
SCHEMA = "beops-history/v3"
WINDOW_POLICY = ROOT / "research" / "HISTORY_QUALIFICATION_POLICY.json"


def window_days() -> list:
    """The windows the project already declares. HISTORY_QUALIFICATION_POLICY.json
    names 7/14/30 and history_qualification.py refuses anything else, but the builder
    never read them, so a page was handed all MAX_DAYS at once. A declared rule that
    nothing enforces at the output is the failure this closes."""
    try:
        policy = json.loads(WINDOW_POLICY.read_text(encoding="utf-8"))
    except Exception:
        return []
    days = policy.get("windows_days")
    if not isinstance(days, list):
        return []
    return sorted({d for d in days if isinstance(d, int) and 0 < d < MAX_DAYS})


def compact(row: dict) -> dict:
    """The same record written once instead of three times.

    Measured on 70978 hourly buckets of a 7-day window (2026-09-18): `last_received` was
    never once different from `last_by_measurement` - 65657 identical, 0 differing, 4428
    received rows with no measurement time of their own - and `last` was never once
    different from `last_by_measurement["v"]`. Repeating them costs 41% of every byte the
    browser downloads, and a repetition is not a reading. So the repetition is dropped and
    the reader restores it: `last_received` where `last_same` is set, `last` from
    `last_by_measurement["v"]`. Nothing is rounded, nothing is inferred and nothing is
    defaulted - a value that ever DOES differ is written out in full, because then it is a
    reading and not a repeat. `value_sum` also stays out, but not because the window carries it: it is the only
    unrounded float in a bucket, and `mean` is rounded, so `mean * valid` returns the sum
    only to the mean's own precision. Measured over 87028 buckets of the full record, 66122
    do not return the sum exactly, and on very small values the gap reaches 3% - worst case
    S146 CO 2026-09-09T10, value_sum -0.001067825 against mean*valid -0.0011. The window is
    what a browser downloads and a browser draws a line; anything that needs the exact sum
    reads history.json, which keeps it.
    """
    out = {k: v for k, v in row.items() if k != "value_sum"}
    measured = out.get("last_by_measurement")
    if measured is not None and out.get("last_received") == measured:
        del out["last_received"]
        out["last_same"] = True
    if measured is not None and "last" in out and out["last"] == measured.get("v"):
        del out["last"]
    return out


def narrow(data: dict, days: int, now: datetime) -> dict:
    """A window is the same record over a shorter span, never a different record.
    An hour outside the window is absent exactly as an unreceived hour is absent:
    no interpolation, no zero, no line drawn across the gap."""
    floor = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H")
    series = []
    for s in data["series"]:
        buckets = {hk: row for hk, row in s["buckets"].items() if hk >= floor}
        if not buckets:
            continue
        hours = sorted(buckets)
        first = datetime.strptime(hours[0], "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
        last = datetime.strptime(hours[-1], "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
        narrowed = dict(s)
        narrowed["buckets"] = {hk: compact(row) for hk, row in buckets.items()}
        narrowed["first_hour"] = hours[0]
        narrowed["last_hour"] = hours[-1]
        narrowed["hours_present"] = len(buckets)
        narrowed["hours_expected"] = int((last - first).total_seconds() // 3600) + 1
        series.append(narrowed)
    covered = [s for s in series if s["hours_present"]]
    earliest = min((s["first_hour"] for s in covered), default=None)
    latest = max((s["last_hour"] for s in covered), default=None)
    out = {k: v for k, v in data.items() if k != "series"}
    out["window_days"] = days
    out["history_starts"] = earliest
    out["history_ends"] = latest
    out["hours_of_history"] = ((int((datetime.strptime(latest, "%Y-%m-%dT%H") -
                                     datetime.strptime(earliest, "%Y-%m-%dT%H")).total_seconds() // 3600) + 1)
                               if earliest and latest else 0)
    out["window_note"] = ("A %d-day window over the same buckets as history.json. Absent hours stay "
                          "absent. Two repetitions are written once: last_same means last_received equalled "
                          "last_by_measurement, and an absent last means it equalled "
                          "last_by_measurement's value; a value that differs is always written out. "
                          "value_sum is omitted, and it is recoverable from mean only to the mean's "
                          "own rounding, so the exact sum lives in history.json." % days)
    out["series"] = series
    return out


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
    return utc(s)


def hour_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H")


def load_config() -> dict:
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {s["sid"]: s for s in cfg.get("sources", [])}


def fold(now: datetime | None = None, rows=None) -> dict:
    """One pass; choose revisions in the bounded reception window before grouping.

    A newer unusable clock invalidates that observation's older version. It is
    retained as a compact tombstone until revision selection finishes, never as
    a fallback measurement. Both reception and plotted time must fit the cut.
    """
    now = now or datetime.now(timezone.utc)
    rows = pathlib.Path(rows) if rows is not None else ROWS
    floor = now - timedelta(days=MAX_DAYS)
    cfg = load_config()
    series: dict[str, dict] = {}
    unparsed: dict[str, int] = {}
    lower, upper = floor.timestamp(), now.timestamp()

    for sid_dir in sorted(p for p in rows.iterdir() if p.is_dir()) if rows.exists() else []:
        sid = sid_dir.name
        # Every event_key and every series key begins with sid, so a revision and a
        # series belong to exactly one source. Holding all sources' revisions at once
        # made the peak the whole record (814 MB of rows on 2026-09-24, two sources
        # 92% of it); drained per source the peak is the largest single source.
        revisions = {}
        for f in sorted(sid_dir.glob("*.jsonl")):
          for r in observation_rows(f):
                ds = r.get("datastream")
                if not ds:
                    continue

                received = utc(r.get('receivedTime'))
                if received is None:
                    unparsed[sid] = unparsed.get(sid, 0) + 1
                    continue
                if received < floor or received > now:
                    continue

                t, basis = row_clock(r)
                if basis == 'arrival':
                    basis = 'received'
                if t is None:
                    # Keep the revision identity so the previous number cannot reappear.
                    # The unusable clock is omitted only after latest revision selection.
                    unparsed[sid] = unparsed.get(sid, 0) + 1

                value_type, interval_seconds = parameter_semantics(r)
                key = json.dumps([sid, ds, basis, r.get('unit'), value_type, interval_seconds])
                s = series.get(key)
                if s is None:
                    s = series[key] = {
                        "sid": sid, "datastream": ds,
                        "station": r.get("station_name") or r.get("station_id"),
                        "parameter": r.get("parameter"), "unit": r.get("unit"),
                        "time_basis": basis,
                        "value_type": value_type, "interval_seconds": interval_seconds,
                        "cadence_seconds": (cfg.get(sid) or {}).get("cadence_seconds"),
                        "events": [],
                    }
                event_key = (sid, ds, observation_identity(r))
                event = (t.timestamp() if t is not None else None, received.timestamp(), r.get('result'))
                prior = revisions.get(event_key)
                # Clock basis, interval type and the plotting boundary cannot
                # split two versions of one source observation into two facts.
                if prior is None or event[1] >= prior[1][1]:
                    revisions[event_key] = (s, event)

        for s, event in revisions.values():
            if event[0] is not None and lower <= event[0] <= upper:
                s['events'].append(event)
        revisions = None

    out_series = []
    for key, s in sorted(series.items()):
        buckets = {}
        grouped = {}
        for event in s.pop('events'):
            grouped.setdefault(hour_key(datetime.fromtimestamp(event[0], timezone.utc)), []).append(event)
        kind = s['value_type']
        def public_point(event):
            if event is None: return None
            def stamp(value):
                return datetime.fromtimestamp(value, timezone.utc).isoformat().replace('+00:00','Z') if value is not None else None
            return {'v': event[2] if finite(event[2]) else None,
                    't': stamp(event[0]) if s['time_basis'] != 'received' else None,
                    'rx': stamp(event[1]), 'time_basis': s['time_basis']}
        for hk, events in sorted(grouped.items()):
            numeric = [float(event[2]) for event in events if finite(event[2])]
            vals = [value for value in numeric if (0 <= value <= 360 if kind == 'circular_degrees'
                    else value >= 0 and value.is_integer() if kind == 'count' else True)]
            row = {'n':len(events), 'missing':len(events)-len(numeric), 'invalid':len(numeric)-len(vals)}
            if kind in ('scalar','interval_average','count') and vals:
                row["min"] = round(min(vals), 4)
                row["max"] = round(max(vals), 4)
                if kind != 'count':
                    row['value_sum'] = math.fsum(vals)
                    row['mean'] = round(row['value_sum'] / len(vals), 4)
            if kind == 'circular_degrees':
                row.update(direction_count=len(vals),
                           direction_sum_cos=math.fsum(math.cos(math.radians(v)) for v in vals),
                           direction_sum_sin=math.fsum(math.sin(math.radians(v)) for v in vals))
                row.update(direction_summary(row['direction_sum_cos'],row['direction_sum_sin'],len(vals)))
            if kind != 'text':
                # Null is retained. A later older observation cannot become the
                # latest measurement merely because its reception happened later.
                rx_key=lambda event: event[1] if event[1] is not None else float('-inf')
                last_measured=max(events,key=lambda event:(event[0],rx_key(event))) if s['time_basis'] != 'received' else None
                received_events=[event for event in events if event[1] is not None]
                last_received=max(received_events,key=lambda event:(event[1],event[0])) if received_events else None
                row['last_by_measurement']=public_point(last_measured)
                row['last_received']=public_point(last_received)
                selected=row['last_by_measurement'] if s['time_basis'] != 'received' else row['last_received']
                row['last']=selected['v'] if selected else None
            buckets[hk] = row
        if not buckets:
            continue
        hours = sorted(buckets)
        first = datetime.strptime(hours[0], "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
        last = datetime.strptime(hours[-1], "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
        expected = int((last - first).total_seconds() // 3600) + 1
        numeric = kind in ('scalar','interval_average','count','circular_degrees')
        out_series.append({
            **{k: s[k] for k in ("sid", "datastream", "station", "parameter", "unit",
                                 "time_basis", "cadence_seconds", "value_type", "interval_seconds")},
            "kind": "numeric" if numeric else "count" if kind == 'text' else 'unclassified',
            "first_hour": hours[0], "last_hour": hours[-1],
            "hours_present": len(buckets), "hours_expected": expected,
            "buckets": buckets,
        })

    covered = [s for s in out_series if s["hours_present"]]
    earliest = min((s["first_hour"] for s in covered), default=None)
    latest = max((s["last_hour"] for s in covered), default=None)
    return {
        "schema": SCHEMA,
        "parameter_semantics": PARAMETER_SEMANTICS,
        "built": iso(now),
        "history_starts": earliest,
        "history_ends": latest,
        "hours_of_history": (int((datetime.strptime(latest, "%Y-%m-%dT%H") -
                                  datetime.strptime(earliest, "%Y-%m-%dT%H")).total_seconds() // 3600) + 1)
                            if earliest and latest else 0,
        "note": ("Hourly buckets folded from the stored rows. An absent hour is absent, never a zero and "
                 "never a line drawn across the gap; hours_present against hours_expected says how much of "
                 "the span exists. A series whose source publishes no measurement time is bucketed by "
                 "reception and says so in time_basis. n counts retained logical observations assigned to "
                 "the bucket after revisions, not physical receptions or instrument uptime. Scalar means "
                 "use retained sample sums; directions use unit-vector component sums and valid counts."),
        "unreadable_measurement_times": unparsed,   # rows dropped rather than moved to another clock
        "series": out_series,
    }


def main() -> int:
    from release_observation import input_generation, generation_time
    from live_view import observation_view
    generation = input_generation(ROWS.parent)
    with observation_view(ROWS.parent) as inputs:
        data = fold(generation_time(generation) if generation else None, inputs/'rows')
    if generation:
        data['input_generation'] = generation
        data['as_of'] = iso(generation_time(generation))
        data['built'] = iso(datetime.now(timezone.utc))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Streamed: json.dumps held the whole output as one str and write_text its utf-8
    # bytes beside it, both alive while data still was. The file is byte-identical.
    with OUT.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes; {len(data['series'])} series, "
          f"{data['hours_of_history']} h of history from {data['history_starts']})")
    basis = generation_time(generation) if generation else datetime.now(timezone.utc)
    for days in window_days():
        window = narrow(data, days, basis)
        path = OUT.parent / f"history-{days}d.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(window, handle, ensure_ascii=False, separators=(",", ":"))
        print(f"wrote {path} ({path.stat().st_size} bytes; {len(window['series'])} series, "
              f"{days}-day window, {window['hours_of_history']} h)")
        window = None
    return 0


if __name__ == "__main__":
    sys.exit(main())
