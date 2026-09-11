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

WHAT IT IS NOT, and this is load-bearing. It is NOT the publisher's own latency. We ask on a fixed
cadence, so a value published one second after we asked waits a whole interval before we see it. The
age therefore contains the publisher's delay PLUS up to one polling interval of ours, and this record
cannot separate them. Every output carries the cadence next to the age so the reader can subtract our
share themselves; nothing here subtracts it for them, because the split is not measured.

It is also not a quality score. A source that publishes hourly means cannot be fresher than half an
hour on average and is not worse for it.

THE CLOCK. Where a source labels its times wrongly and the collector wrote a corrected estimate
beside them (C-040), the age is computed from the CORRECTION and the output says so. Reading the
label when a correction exists is exactly the defect this project has already written down once.

THE SILENT MAJORITY. A source that publishes no measurement time at all gets no age - it gets a
count and a sentence. That absence is the finding, not a gap in the table.

    python tools/latency.py build      # rebuild every source
    python tools/latency.py show       # print it for a person
"""
from __future__ import annotations
from contracts import observation_rows

import json
import pathlib
import statistics
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROWS = ROOT / "data" / "live" / "rows"
OUT = ROOT / "data" / "live" / "derived" / "latency"
COLLECTORS = ROOT / "research" / "COLLECTORS.json"
SCHEMA = "beops-latency/v1"

MIN_N = 20            # fewer ages than this is an anecdote, not a distribution
MAX_DAYS = 30         # how far back to read
NOT_A_MEASURE = {"headline", "planned_outage", "notice"}

WHAT_THIS_IS = ("the age of a value at the moment it reached this record: the time between the end of "
                "the measurement window the source stated and our reception of it. It contains the "
                "publisher's own delay AND up to one of our polling intervals, and this record cannot "
                "separate the two. It is not a measurement of the publisher alone, and it is not a "
                "quality score.")


def _p(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def _end_of(row: dict) -> tuple[datetime | None, str]:
    """(end of the measurement window, which clock it was read off). The correction wins where one
    exists - the label is what was served, the correction is what we believe it meant."""
    if row.get('sourceClockUnresolved'):
        return None, 'none'
    pc = row.get("phenomenonTimeCorrected")
    if isinstance(pc, dict) and pc.get("end") and not row.get("phenomenonTimeUnknown"):
        d = _p(pc["end"])
        if d:
            return d, "corrected"
    pt = row.get("phenomenonTime")
    end = pt.get("end") if isinstance(pt, dict) else pt
    if end and not row.get("phenomenonTimeUnknown"):
        d = _p(end)
        if d:
            return d, "measured"
    return None, "none"


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
    negative = 0
    total = 0
    note = None
    for f in sorted(d.glob("*.jsonl")):
        for r in observation_rows(f):
            if r.get("parameter") in NOT_A_MEASURE:
                continue
            rx = _p(r.get("receivedTime"))
            if not rx or (now - rx).days > MAX_DAYS:
                continue
            total += 1
            if r.get("sourceClockNote"):
                note = str(r["sourceClockNote"])
            end, clock = _end_of(r)
            if end is None:
                untimed += 1
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
        "our_polling_interval_minutes": round((src.get("cadence_seconds") or 0) / 60.0) or None,
        "clocks": sorted(clocks),
        "source_clock_note": note,
        "what_this_is": WHAT_THIS_IS,
        "age_minutes": None,
        "arrived_before_the_window_closed": negative,
    }
    if untimed and not ages:
        out["what_this_source_publishes"] = ("no measurement time at all: we know the value and when it "
                                             "reached us, never when it was true. No age can be computed "
                                             "and none is shown.")
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
        "sources_publishing_a_measurement_time": sum(1 for b in res.values() if b.get("age_minutes")),
        "sources_publishing_no_measurement_time": sum(1 for b in res.values()
                                                      if not b.get("age_minutes") and b["rows_without_a_measurement_time"]),
        "what_this_is": WHAT_THIS_IS,
        "sources_on_more_than_one_clock": sum(1 for b in res.values() if b.get("mixed_clocks")),
        "names": {s: names.get(s, "") for s in sorted(res)},
        "by_source": {s: {"median_age_minutes": (b.get("age_minutes") or {}).get("median"),
                          "age_by_clock": b.get("age_by_clock") or {},
                          "mixed_clocks": b.get("mixed_clocks"),
                          "polling_interval_minutes": b.get("our_polling_interval_minutes"),
                          "clocks": b.get("clocks"),
                          "rows_read": b.get("rows_read"),
                          "rows_with_a_measurement_time": b.get("rows_with_a_measurement_time"),
                          "rows_without_a_measurement_time": b["rows_without_a_measurement_time"],
                          "source_clock_note": b.get("source_clock_note"),
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
