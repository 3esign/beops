#!/usr/bin/env python3
"""agreement.py - where two independent observers describe the same hour, do they say the same thing.

Why this exists. The instrument owns no sensor, so it can never state accuracy: every value inherits
somebody else's calibration and somebody else's clock, and no amount of provenance discipline changes
that. This is the paper's own concession and it is correct.

But accuracy is not the only measurable property of a reading. Where two sources that answer to
nobody in common describe the same parameter in the same hour, the DIFFERENCE between them is a fact
this record can compute and neither publisher states. An observatory with no instruments of its own
cannot say what the temperature was. It can say that three independent bodies disagreed about it by
1.8 degrees, and that today they disagree by six.

WHAT THE NUMBER IS. For each parameter and each hour, the spread between the per-source medians of
every source that reported that parameter in that hour: the widest gap, and each pair's own gap.

WHAT IT IS NOT, and the whole layer is worthless without this sentence. **It is not an error bar and
it is not a check of instruments.** The sources stand in different places - an airport runway, a
hillside station, a citizen's balcony - so their difference contains genuine spatial variation across
a city as well as any instrumental disagreement, and THIS RECORD CANNOT SEPARATE THE TWO. A wide
spread is not evidence that somebody is wrong. It is evidence that "the temperature in Belgrade" is
not a single number, which is itself worth publishing and is routinely hidden by dashboards that
print one.

Nothing here is used to correct, adjust, reconcile or prefer any source's value. The record keeps
what each source said, exactly as each said it.

THE CLOCK. Hours are read off the corrected clock where the collector wrote one (C-040). Comparing
two sources bucketed on two different clocks is the defect this layer would otherwise create at
industrial scale.

    python tools/agreement.py build
    python tools/agreement.py show
"""
from __future__ import annotations

import json
import pathlib
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROWS = ROOT / "data" / "live" / "rows"
OUT = ROOT / "data" / "live" / "derived" / "agreement"
SCHEMA = "beops-agreement/v1"

MIN_HOURS = 6          # fewer shared hours than this is not a comparison
MAX_DAYS = 30
NOT_A_MEASURE = {"headline", "planned_outage", "notice"}

# A bearing is not a line. 350 deg and 10 deg are 20 apart, not 340, and subtracting them like
# numbers produces a gap that is not merely imprecise but categorically wrong - the first run of this
# layer reported a 90th percentile of 186 degrees, which is the signature of exactly that error.
CIRCULAR_DEGREES = {"wind_direction", "wave_direction", "bearing", "wind_from_direction"}


def _gap(par: str, a: float, b: float) -> float:
    """The distance between two values of this parameter, on the parameter's own geometry."""
    if par in CIRCULAR_DEGREES:
        d = abs(a - b) % 360.0
        return 360.0 - d if d > 180.0 else d
    return abs(a - b)


def _circular_median(vals: list[float]) -> float:
    """The middle of a set of bearings, computed as a direction rather than as an average of numbers.
    Without this an hour containing 350 and 10 would be summarised as 180 - due south for a north
    wind."""
    import math
    if not vals:
        return 0.0
    x = sum(math.cos(math.radians(v)) for v in vals) / len(vals)
    y = sum(math.sin(math.radians(v)) for v in vals) / len(vals)
    return math.degrees(math.atan2(y, x)) % 360.0

WHAT_THIS_IS = ("the difference between what two independent sources said about the same parameter in "
                "the same hour. It contains instrumental disagreement AND real difference between the "
                "places they stand in, and this record cannot separate them. It is not an error bar, "
                "not a check of any source, and it is never used to adjust a value.")


def _p(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def _hour_of(row: dict):
    """(hour key 'YYYY-MM-DDTHH', which clock, was it a measurement time at all)"""
    pc = row.get("phenomenonTimeCorrected")
    if isinstance(pc, dict) and pc.get("end") and not row.get("phenomenonTimeUnknown"):
        d = _p(pc["end"])
        if d:
            return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H"), "corrected", True
    pt = row.get("phenomenonTime")
    end = pt.get("end") if isinstance(pt, dict) else pt
    if end and not row.get("phenomenonTimeUnknown"):
        d = _p(end)
        if d:
            return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H"), "measured", True
    d = _p(row.get("receivedTime"))
    return (d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H"), "arrival", False) if d else (None, "arrival", False)


def read_all(now: datetime | None = None):
    """(parameter, hour, sid) -> list of values, plus the clocks and units each source used."""
    now = now or datetime.now(timezone.utc)
    vals = defaultdict(list)
    clocks = defaultdict(set)
    units = {}
    places = defaultdict(set)
    for d in sorted(ROWS.iterdir()) if ROWS.exists() else []:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.jsonl")):
            for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
                ln = ln.strip()
                if not ln.startswith("{"):
                    continue
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                par, v = r.get("parameter"), r.get("result")
                if not par or par in NOT_A_MEASURE or not isinstance(v, (int, float)) or v != v:
                    continue
                rx = _p(r.get("receivedTime"))
                if not rx or (now - rx).days > MAX_DAYS:
                    continue
                hour, clock, timed = _hour_of(r)
                if hour is None:
                    continue
                vals[(str(par), hour, d.name)].append(float(v))
                clocks[(str(par), d.name)].add(clock)
                if r.get("unit"):
                    units[(str(par), d.name)] = str(r["unit"])
                st = r.get("station_name") or r.get("station_id")
                if st:
                    places[(str(par), d.name)].add(str(st))
    return vals, clocks, units, places


def build(now: datetime | None = None) -> dict:
    vals, clocks, units, places = read_all(now)
    per_hour = defaultdict(dict)                     # (par, hour) -> {sid: median}
    for (par, hour, sid), v in vals.items():
        per_hour[(par, hour)][sid] = _circular_median(v) if par in CIRCULAR_DEGREES else statistics.median(v)

    pairs = defaultdict(list)                        # (par, a, b) -> [|a-b| per shared hour]
    widest = defaultdict(list)                       # par -> [widest gap per shared hour]
    for (par, hour), bysid in per_hour.items():
        if len(bysid) < 2:
            continue
        sids = sorted(bysid)
        widest[par].append(max(_gap(par, bysid[a], bysid[b]) for a in sids for b in sids))
        for i, a in enumerate(sids):
            for b in sids[i + 1:]:
                pairs[(par, a, b)].append(_gap(par, bysid[a], bysid[b]))

    out = {"schema": SCHEMA, "made_at": (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z"),
           "min_shared_hours": MIN_HOURS, "what_this_is": WHAT_THIS_IS,
           "parameters": {}, "withheld_too_few_shared_hours": []}

    for par in sorted(set(list(widest.keys()))):
        hours = widest[par]
        if len(hours) < MIN_HOURS:
            out["withheld_too_few_shared_hours"].append({"parameter": par, "shared_hours": len(hours)})
            continue
        hours_sorted = sorted(hours)
        entry = {"shared_hours": len(hours),
                 "widest_gap": {"median": round(statistics.median(hours_sorted), 2),
                                "min": round(hours_sorted[0], 2),
                                "max": round(hours_sorted[-1], 2)},
                 "pairs": [], "sources": {}}
        seen_sids = set()
        for (p2, a, b), gaps in sorted(pairs.items()):
            if p2 != par or len(gaps) < MIN_HOURS:
                continue
            ua, ub = units.get((par, a)), units.get((par, b))
            rec = {"a": a, "b": b, "shared_hours": len(gaps), "unit_a": ua, "unit_b": ub,
                   "units_match": ua == ub, "geometry": "circular_degrees" if par in CIRCULAR_DEGREES else "linear"}
            if ua != ub:
                # A gap between hPa and Pa is not a large disagreement, it is not a quantity at all.
                # Publishing it with a warning attached invites the reading the warning exists to
                # prevent, so the number is withheld and the reason is named in its place.
                rec["median_gap"] = rec["p90_gap"] = rec["max_gap"] = None
                rec["withheld"] = ("the two sources publish this parameter in different units "
                                   f"({ua} and {ub}); the difference between them is not a quantity and "
                                   "no gap is shown. Converting one to the other would be our arithmetic "
                                   "presented as their measurement.")
            else:
                g = sorted(gaps)
                rec["median_gap"] = round(statistics.median(g), 2)
                rec["p90_gap"] = round(g[min(len(g) - 1, int(len(g) * 0.9))], 2)
                rec["max_gap"] = round(g[-1], 2)
            entry["pairs"].append(rec)
            seen_sids.update((a, b))
        if any(p2.get("withheld") for p2 in entry["pairs"]):
            # If any two of these sources publish in different units, the widest gap across all of
            # them is the same non-quantity as the pair gap, and it goes the same way.
            entry["widest_gap"] = None
            entry["widest_gap_withheld"] = ("at least two of these sources publish this parameter in "
                                            "different units, so the spread across them is not a quantity.")
        for sid in sorted(seen_sids):
            entry["sources"][sid] = {"clocks": sorted(clocks.get((par, sid), [])),
                                     "places": sorted(places.get((par, sid), []))[:8],
                                     "unit": units.get((par, sid))}
        entry["these_are_different_places"] = ("the sources below stand in different places, so part of "
                                               "every gap is the city itself and not the instruments.")
        entry["geometry"] = "circular_degrees" if par in CIRCULAR_DEGREES else "linear"
        out["parameters"][par] = entry

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "build"
    if cmd not in ("build", "show"):
        print(__doc__)
        return 1
    d = build()
    if not d["parameters"]:
        print("nothing comparable yet.")
        for w in d["withheld_too_few_shared_hours"]:
            print("  %-20s %d shared hours (floor %d)" % (w["parameter"], w["shared_hours"], MIN_HOURS))
        print("\n" + WHAT_THIS_IS)
        return 0
    for par, e in d["parameters"].items():
        if e["widest_gap"] is None:
            print("%s  -  %d shared hours, widest gap WITHHELD (units differ)  [%s]"
                  % (par, e["shared_hours"], e["geometry"]))
        else:
            print("%s  -  %d shared hours, widest gap median %.2f (max %.2f)  [%s]"
                  % (par, e["shared_hours"], e["widest_gap"]["median"], e["widest_gap"]["max"], e["geometry"]))
        for p in e["pairs"]:
            if p["median_gap"] is None:
                print("    %-5s vs %-5s  n=%-4d WITHHELD: units differ (%s vs %s)"
                      % (p["a"], p["b"], p["shared_hours"], p["unit_a"], p["unit_b"]))
                continue
            print("    %-5s vs %-5s  n=%-4d median %6.2f  p90 %6.2f  max %6.2f  [%s]"
                  % (p["a"], p["b"], p["shared_hours"], p["median_gap"], p["p90_gap"], p["max_gap"], p["geometry"]))
        for sid, s in e["sources"].items():
            print("      %-5s %-12s %s" % (sid, ",".join(s["clocks"]), ", ".join(s["places"])[:70]))
    for w in d["withheld_too_few_shared_hours"]:
        print("withheld: %-20s %d shared hours (floor %d)" % (w["parameter"], w["shared_hours"], MIN_HOURS))
    print("\n" + WHAT_THIS_IS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
