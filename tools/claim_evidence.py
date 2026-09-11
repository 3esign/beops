"""Score a closed claim window from durable observations; no evidence means unknown."""
from collections import defaultdict
from contracts import content_id, finite, observation_rows, row_clock, utc


def evaluate(claim_row, live, snapshot=None):
    c = claim_row["claim"]
    made, due = utc(claim_row.get("at")), utc(claim_row.get("due"))
    if not made or not due or due <= made:
        return {"outcome": "unverifiable", "evidence": [], "reason": "invalid evaluation window"}
    records = []
    if snapshot is None:
        directory = live / "rows" / c.get("sid", "")
        for f in sorted(directory.glob("*.jsonl")):
            for r in observation_rows(f):
                rx = utc(r.get("receivedTime"))
                if rx and made < rx <= due:
                    t, frame = row_clock(r)
                    records.append({"id": r.get("row_id") or content_id(r), "rx": rx, "t": t,
                        "v": r.get("result"), "unit": r.get("unit"), "parameter": r.get("parameter"),
                        "measured": frame in ("corrected", "measured"), "raw_sha256": r.get("raw_sha256")})
    else:
        # Used for replay fixtures. The caller persists the exact supplied snapshot before scoring.
        for source in snapshot.get("sources", []):
            if source.get("sid") != c.get("sid"):
                continue
            for stream in source.get("datastreams", []):
                for p in stream.get("points", []):
                    records.append({"id": content_id(p), "rx": utc(p.get("rx")), "t": utc(p.get("tc") or p.get("t")),
                        "v": p.get("v"), "unit": stream.get("unit"), "parameter": stream.get("parameter"), "measured": not p.get("tu")})
            for event in source.get("events", []):
                records.append({"id": content_id(event), "rx": utc(event.get("rx")), "t": None, "measured": False})
    records = [r for r in records if r["rx"] and made < r["rx"] <= due]
    if c["kind"] == "reception" and records:
        r = min(records, key=lambda x: x["rx"])
        return {"outcome": "true", "evidence": [r["id"]], "observed_reception": r["rx"].isoformat()}
    if c["kind"] == "spread":
        groups = defaultdict(list)
        for r in records:
            if r.get("parameter") == c.get("parameter") and r["measured"] and r["t"] and made < r["t"] <= due and finite(r.get("v")):
                groups[r["t"]].append(r)
        if groups:
            at = min(groups)
            rows = groups[at]
            if len({r.get("unit") for r in rows}) == 1:
                value = max(r["v"] for r in rows)
                return {"outcome": "true" if c["lo"] <= value <= c["hi"] else "false",
                        "evidence": [r["id"] for r in rows], "observed_max": value, "observed_hour": at.isoformat()}
    return {"outcome": "unverifiable", "evidence": [], "reason": "no qualifying evidence in the closed window"}
