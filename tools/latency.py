#!/usr/bin/env python3
"""latency.py - how long after a thing is true does the city say it.

Why this exists. The observatory's central finding is about what a city publishes, and coverage
(1 of 19 ISO themes) measures only WHETHER a signal exists. It says nothing about the other half of
usefulness, which is WHEN. A river level that is four hours old is a different instrument from one
that is four minutes old, and no publisher states which theirs is.

This layer states it, out of receipts we already hold and permissions we already have. It adds no
source, asks nobody for anything, and takes nothing new.

WHAT THE NUMBER IS, EXACTLY. For every row that carries a measurement time, the age of the value at
the moment it reached us:

    age = receivedTime - (end of the measurement window)

WHAT IT IS NOT. This is not the publisher's own delay. The measurement interval's end is not the
moment its result became available. Pauses, failed cycles, transport and processing can add more
than the planned polling interval. The configured cadence is not an upper bound. Actual gaps
between completed successful cycles are disclosed separately and do not establish availability.
The unmeasured split stays unknown. An interval's duration is not added to age measured from its end.
This is not a quality score.

THE CLOCK. Where a source labels its times wrongly and the collector wrote a corrected estimate
beside them (C-040), the age is computed from the CORRECTION and the output says so. Reading the
label when a correction exists is exactly the defect this project has already written down once.

THE SILENT MAJORITY. A source that publishes no measurement time at all gets no age - it gets a
count and a sentence. That absence is the finding, not a gap in the table.

    python tools/latency.py build      # rebuild every source
    python tools/latency.py show       # print it for a person
"""
from __future__ import annotations
from contracts import observation_rows, json_object, row_clock, utc, observation_point

import json
import pathlib
import statistics
import sys
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROWS = ROOT / "data" / "live" / "rows"
RECEIPTS = None  # default follows ROWS; isolated callers never read another tree's receipts
OUT = ROOT / "data" / "live" / "derived" / "latency"
COLLECTORS = ROOT / "research" / "COLLECTORS.json"
SCHEMA = "beops-latency/v2"

MIN_N = 20            # fewer ages than this is an anecdote, not a distribution
MAX_DAYS = 30         # how far back to read
NOT_A_MEASURE = {"headline", "planned_outage", "notice"}

WHAT_THIS_IS = ("the age of a value at reception, measured from the end of the stated measurement "
                "interval. Its end is not the time the result became available. This record cannot separate "
                "publisher, transport and our waiting time without availability evidence. A planned polling "
                "interval is not an upper bound: failed or missed cycles can add several intervals. "
                "It is not a measurement of the publisher alone, and it is not a quality score.")


def _p(s):
    return utc(s)


def _end_of(row: dict) -> tuple[datetime | None, str]:
    """(end of the measurement window, which clock it was read off). The correction wins where one
    exists - the label is what was served, the correction is what we believe it meant."""
    end, basis = row_clock(row)
    return (end, basis) if basis in ('measured', 'corrected') else (None, 'none')


def successful_reception_gaps(sid, now, cadence_seconds):
    """Observed completion gaps, not a bound on data availability or our delay."""
    directory = (RECEIPTS if RECEIPTS is not None else ROWS.parent/'receipts')/sid
    lower = now-timedelta(days=MAX_DAYS)
    times = set()
    missing_clocks = 0
    for file in sorted(directory.glob('*.json')):
        # Canonical names allow a cheap date bound; unknown names are still checked.
        if len(file.stem) >= 8 and file.stem[:8].isdigit() and file.stem[:8] < lower.strftime('%Y%m%d'):
            continue
        receipt = json_object(file)
        if receipt.get('state') != 'captured':
            continue
        end = utc(receipt.get('completed_at'))
        if end is None:
            missing_clocks += 1
        elif lower <= end <= now:
            times.add(end)
    times = sorted(times)
    gaps = [(b-a).total_seconds() for a,b in zip(times,times[1:])]
    return {'time_basis':'successful_cycle_completed_at', 'successful_cycles':len(times),
            'missing_completion_clocks':missing_clocks, 'intervals':len(gaps),
            'max_minutes':round(max(gaps)/60,3) if gaps else None,
            'gaps_over_cadence':sum(g > cadence_seconds for g in gaps) if cadence_seconds else None,
            'last_success_at':times[-1].isoformat().replace('+00:00','Z') if times else None,
            'availability_observed':False}


def cadences() -> dict:
    try:
        d = json.loads(COLLECTORS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {s["sid"]: s for s in d.get("sources", [])}


def build_source(sid: str, now: datetime | None = None, src: dict | None = None) -> dict | None:
    now = now or datetime.now(timezone.utc)
    d = ROWS / sid
    if not d.exists():
        return None
    ages: list[float] = []
    by_clock: dict[str, list[float]] = {}
    clocks: set[str] = set()
    untimed = 0
    unresolved = 0
    negative = 0
    total = 0
    note = None
    example, example_at = None, None
    for f in sorted(d.glob("*.jsonl")):
        for r in observation_rows(f):
            if r.get("parameter") in NOT_A_MEASURE:
                continue
            rx = _p(r.get("receivedTime"))
            if not rx or rx > now or rx < now-timedelta(days=MAX_DAYS):
                continue
            total += 1
            if example_at is None or rx >= example_at:
                example, example_at = observation_point(r), rx
            if r.get("sourceClockNote"):
                note = str(r["sourceClockNote"])
            end, clock = _end_of(r)
            if end is None:
                if r.get('phenomenonTimeUnknown') and not r.get('sourceClockUnresolved'):
                    untimed += 1
                else:
                    unresolved += 1
                continue
            clocks.add(clock)
            a = (rx - end).total_seconds() / 60.0
            if a < 0:
                negative += 1
            ages.append(a)
            by_clock.setdefault(clock, []).append(a)
    if not total:
        return None
    src = src or {}
    out = {
        "schema": SCHEMA, "sid": sid, "made_at": now.isoformat().replace("+00:00", "Z"),
        "rows_read": total,
        "rows_with_a_measurement_time": len(ages),
        "rows_without_a_measurement_time": untimed,
        "rows_with_unresolved_clock": unresolved,
        "our_polling_interval_minutes": round((src.get("cadence_seconds") or 0) / 60.0) or None,
        "our_delay_upper_bound_minutes": None,
        "delay_bound_state": "unknown_without_availability_evidence",
        "successful_reception_gaps": successful_reception_gaps(sid, now, src.get('cadence_seconds')),
        "clocks": sorted(clocks),
        "source_clock_note": note,
        "clock_example": example,
        "what_this_is": WHAT_THIS_IS,
        "age_minutes": None,
        "arrived_before_the_window_closed": negative,
    }
    if untimed and not ages and not unresolved:
        out["what_this_source_publishes"] = ("no measurement time at all: we record the number displayed by the source "
                                             "and our reception; accuracy and measurement age are unconfirmed. No age can be computed "
                                             "and none is shown.")
        return out
    if unresolved and not ages:
        out['what_this_source_publishes'] = (f"measurement clocks are unresolved on {unresolved} rows; "
            f"{untimed} further rows publish no measurement time. No age distribution is computed; "
            "an unresolved source label is not an absent measurement time or a fast reception.")
        return out
    if len(ages) < MIN_N:
        out["what_this_source_publishes"] = ("too few timed values to describe a distribution "
                                             f"({len(ages)}, the floor is {MIN_N}); withheld on purpose.")
        return out
    def describe(v: list[float]) -> dict:
        v = sorted(v)

        def q(pr):
            return round(v[min(len(v) - 1, int(len(v) * pr))], 1)

        return {"n": len(v), "min": round(v[0], 1), "p10": q(0.10),
                "median": round(statistics.median(v), 1), "p90": q(0.90), "max": round(v[-1], 1)}

    out["age_by_clock"] = {c: describe(v) for c, v in sorted(by_clock.items()) if len(v) >= MIN_N}
    if len(by_clock) > 1:
        # The first run of this layer blended a source's corrected rows with the rows collected before
        # its clock note was written, and printed one median across both. That is the very error the
        # layer exists to avoid, committed by the layer. Two clocks do not make one distribution, so
        # there is no single number - only one per clock, each saying which clock it is.
        out["age_minutes"] = None
        out["mixed_clocks"] = sorted(by_clock)
        out["what_this_source_publishes"] = (
            "this source's rows are on more than one clock (" + ", ".join(sorted(by_clock)) + "): rows "
            "collected before its clock note was written carry only the label, later rows carry our "
            "corrected estimate beside it. Ages on two clocks are not one distribution and are not "
            "blended into one; see age_by_clock.")
        return out
    out["age_minutes"] = describe(ages)
    return out


def build(sids: list[str] | None = None) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    cad = cadences()
    names = {sid: (c.get("name") or "") for sid, c in cad.items()}
    res = {}
    for d in sorted(ROWS.iterdir()) if ROWS.exists() else []:
        if not d.is_dir() or (sids and d.name not in sids):
            continue
        b = build_source(d.name, src=cad.get(d.name))
        if not b:
            continue
        (OUT / f"{d.name}.json").write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
        res[d.name] = b
    summary = {
        "schema": SCHEMA, "made_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sources_read": len(res),
        "sources_publishing_a_measurement_time": sum(1 for b in res.values() if b['rows_with_a_measurement_time']),
        "sources_publishing_no_measurement_time": sum(1 for b in res.values()
                                                      if not b['rows_with_a_measurement_time'] and not b['rows_with_unresolved_clock'] and b["rows_without_a_measurement_time"]),
        "sources_with_unresolved_clocks": sum(1 for b in res.values() if b['rows_with_unresolved_clock']),
        "what_this_is": WHAT_THIS_IS,
        "sources_on_more_than_one_clock": sum(1 for b in res.values() if b.get("mixed_clocks")),
        "names": {s: names.get(s, "") for s in sorted(res)},
        "by_source": {s: {"median_age_minutes": (b.get("age_minutes") or {}).get("median"),
                          "age_by_clock": b.get("age_by_clock") or {},
                          "mixed_clocks": b.get("mixed_clocks"),
                          "polling_interval_minutes": b.get("our_polling_interval_minutes"),
                          "our_delay_upper_bound_minutes": b['our_delay_upper_bound_minutes'],
                          "delay_bound_state": b['delay_bound_state'],
                          "successful_reception_gaps": b['successful_reception_gaps'],
                          "clocks": b.get("clocks"),
                          "rows_read": b.get("rows_read"),
                          "rows_with_a_measurement_time": b.get("rows_with_a_measurement_time"),
                          "rows_without_a_measurement_time": b["rows_without_a_measurement_time"],
                          "rows_with_unresolved_clock": b['rows_with_unresolved_clock'],
                          "source_clock_note": b.get("source_clock_note"),
                          "clock_example": b.get("clock_example"),
                          "what_this_source_publishes": b.get("what_this_source_publishes")}
                      for s, b in sorted(res.items())},
    }
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "build"
    if cmd not in ("build", "show"):
        print(__doc__)
        return 1
    res = build(argv[2:] or None)
    print("%-7s %-11s %8s %9s %9s %9s" % ("sid", "clock", "n", "median", "p90", "poll"))
    lines = []
    for s, b in res.items():
        for c, a in (b.get("age_by_clock") or {}).items():
            lines.append((a["median"], s, c, a, b.get("our_polling_interval_minutes")))
    for _, s, c, a, poll in sorted(lines, reverse=True):
        print("%-7s %-11s %8d %8.1fm %8.1fm %8sm" % (s, c, a["n"], a["median"], a["p90"], poll))
    mixed = [s for s, b in res.items() if b.get("mixed_clocks")]
    if mixed:
        print("\non more than one clock, so no single age is shown: " + ", ".join(sorted(mixed)))
    silent = [s for s, b in res.items() if not b.get("age_by_clock") and b["rows_without_a_measurement_time"]]
    thin = [s for s, b in res.items() if not b.get("age_by_clock") and not b["rows_without_a_measurement_time"]]
    print("\npublish no measurement time at all (%d): %s" % (len(silent), ", ".join(sorted(silent)) or "none"))
    if thin:
        print("too thin to describe yet (%d): %s" % (len(thin), ", ".join(sorted(thin))))
    print("\n" + WHAT_THIS_IS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
