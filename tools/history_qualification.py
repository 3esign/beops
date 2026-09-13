#!/usr/bin/env python3
"""Build deterministic 7/14/30-day receipt and row qualification reports.

Only complete UTC days are counted. The current report is replaceable; the daily
report is create-once and a differing rebuild fails visibly.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import sys
from datetime import datetime, timedelta, timezone

from contracts import atomic_json, json_object, observation_rows, row_clock

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "research" / "COLLECTORS.json"
POLICY = ROOT / "research" / "HISTORY_QUALIFICATION_POLICY.json"
RECEIPTS = ROOT / "data" / "live" / "receipts"
ROWS = ROOT / "data" / "live" / "rows"
OUT = ROOT / "data" / "live" / "derived" / "history-qualification"
SCHEMA = "beops-history-qualification/v1"


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(value):
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value) -> str:
    raw = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_inputs(root: pathlib.Path):
    config = json_object(root / "research" / "COLLECTORS.json")
    policy = json_object(root / "research" / "HISTORY_QUALIFICATION_POLICY.json")
    if config.get("schema") != "beops-collectors/v1":
        raise ValueError("invalid collector contract")
    if policy.get("schema") != "beops-history-qualification-policy/v1":
        raise ValueError("invalid history qualification policy")
    if policy.get("windows_days") != [7, 14, 30]:
        raise ValueError("history qualification requires 7/14/30-day windows")
    return config, policy


def source_contract_hash(source: dict) -> str:
    return digest(source)


def receipts_for(root: pathlib.Path, sid: str) -> list[dict]:
    directory = root / "data" / "live" / "receipts" / sid
    if not directory.exists():
        return []
    return [json_object(path) for path in sorted(directory.glob("*.json"))]


def receipt_metrics(receipts: list[dict], start: datetime, end: datetime, cadence: int) -> dict:
    expected = int((end - start).total_seconds() // cadence)
    selected = []
    for receipt in receipts:
        at = parse_time(receipt.get("attempted_at"))
        if at and start <= at < end:
            selected.append((at, receipt))
    selected.sort(key=lambda pair: (pair[0], canonical(pair[1])))
    slots: dict[int, list[dict]] = {}
    late = 0
    previous = None
    duplicate_rows = 0
    for at, receipt in selected:
        slot = int((at - start).total_seconds() // cadence)
        if 0 <= slot < expected:
            slots.setdefault(slot, []).append(receipt)
        if previous is not None and (at - previous).total_seconds() > cadence * 1.5:
            late += 1
        previous = at
        if receipt.get("state") == "captured":
            total = receipt.get("rows")
            new = receipt.get("rows_new")
            if isinstance(total, int) and isinstance(new, int):
                duplicate_rows += max(0, total - new)
    captured = sum(any(r.get("state") == "captured" for r in values) for values in slots.values())
    failed = sum(not any(r.get("state") == "captured" for r in values) and
                 any(r.get("state") in ("failed", "unparsed") for r in values)
                 for values in slots.values())
    receipt_duplicates = sum(max(0, len(values) - 1) for values in slots.values())
    coverage = captured / expected if expected else 0.0
    return {
        "expected_receipt_slots": expected,
        "captured_receipt_slots": captured,
        "failed_receipt_slots": failed,
        "missing_receipt_slots": max(0, expected - captured - failed),
        "duplicate_receipts_in_slot": receipt_duplicates,
        "duplicate_rows_discarded": duplicate_rows,
        "late_receipt_slots": late,
        "receipt_coverage": round(coverage, 6),
    }


def row_metrics(root: pathlib.Path, sid: str, start: datetime, end: datetime) -> dict:
    directory = root / "data" / "live" / "rows" / sid
    valid = 0
    invalid_clock = 0
    missing_unit = 0
    missing_space = 0
    signatures: dict[tuple, set] = {}
    days = set()
    if directory.exists():
        for path in sorted(directory.glob("*.jsonl")):
            for row in observation_rows(path):
                event_at, clock = row_clock(row)
                received = parse_time(row.get("receivedTime"))
                if not received or not start <= received < end:
                    continue
                if event_at is None:
                    invalid_clock += 1
                    continue
                value = row.get("result")
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    continue
                valid += 1
                days.add(event_at.date().isoformat())
                if not row.get("unit"):
                    missing_unit += 1
                if not (row.get("station_name") or row.get("station_id")):
                    missing_space += 1
                event_key = (str(row.get("datastream")), iso(event_at))
                signature = canonical([row.get("result"), row.get("unit"), row.get("resultQuality"),
                                       row.get("resultTime"), clock])
                signatures.setdefault(event_key, set()).add(signature)
    revised = sum(max(0, len(values) - 1) for values in signatures.values())
    return {
        "valid_numeric_observations": valid,
        "observation_days": len(days),
        "invalid_clock_rows": invalid_clock,
        "missing_unit_rows": missing_unit,
        "missing_spatial_label_rows": missing_space,
        "revised_events": revised,
    }


def build(root: pathlib.Path = ROOT, now: datetime | None = None) -> dict:
    root = pathlib.Path(root).resolve()
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    config, policy = load_inputs(root)
    limits = policy["serious_baseline"]
    enabled = [source for source in config.get("sources", []) if source.get("enabled", True)]
    windows = []
    receipt_cache = {source["sid"]: receipts_for(root, source["sid"]) for source in enabled}
    for days in policy["windows_days"]:
        start = end - timedelta(days=days)
        sources = []
        for source in enabled:
            sid = source["sid"]
            cadence = int(source["cadence_seconds"])
            receipt = receipt_metrics(receipt_cache[sid], start, end, cadence)
            rows = row_metrics(root, sid, start, end)
            eligible_source = bool(
                days == limits["consecutive_complete_calendar_days"]
                and receipt["receipt_coverage"] >= limits["minimum_receipt_coverage"]
                and rows["invalid_clock_rows"] == 0
                and rows["missing_unit_rows"] == 0
                and rows["missing_spatial_label_rows"] == 0
            )
            sources.append({
                "sid": sid,
                "cadence_seconds": cadence,
                "source_contract_sha256": source_contract_hash(source),
                **receipt,
                **rows,
                "eligible_source_for_serious_baseline": eligible_source,
            })
        windows.append({"days": days, "start": iso(start), "end_exclusive": iso(end),
                        "sources": sorted(sources, key=lambda row: row["sid"])})
    report = {
        "schema": SCHEMA,
        "as_of_complete_day": (end - timedelta(days=1)).date().isoformat(),
        "day_boundary": "UTC",
        "policy_sha256": digest(policy),
        "collector_contract_sha256": digest(config),
        "windows": windows,
        "limits": policy["limits"],
    }
    report["report_sha256"] = digest(report)
    return report


def persist(report: dict, root: pathlib.Path = ROOT) -> dict:
    root = pathlib.Path(root).resolve()
    out = root / "data" / "live" / "derived" / "history-qualification"
    current = out / "current.json"
    version = f"{report['policy_sha256'][:12]}-{report['collector_contract_sha256'][:12]}"
    daily = out / "daily" / f"{report['as_of_complete_day']}-{version}.json"
    atomic_json(current, report)
    if daily.exists():
        old = json_object(daily)
        if old.get("report_sha256") != report.get("report_sha256"):
            raise FileExistsError("daily history qualification differs; preserve both and investigate")
    else:
        daily.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(daily, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        try:
            payload = (json.dumps(report, ensure_ascii=False, indent=1, allow_nan=False) + "\n").encode("utf-8")
            written = 0
            while written < len(payload):
                written += os.write(fd, payload[written:])
            os.fsync(fd)
        finally:
            os.close(fd)
    return {"current": str(current), "daily": str(daily), "report_sha256": report["report_sha256"]}


def main(argv: list[str]) -> int:
    if len(argv) > 1 and argv[1] not in ("build",):
        print("usage: history_qualification.py [build]", file=sys.stderr)
        return 2
    report = build()
    result = persist(report)
    window30 = next(window for window in report["windows"] if window["days"] == 30)
    result["eligible_sources"] = sum(row["eligible_source_for_serious_baseline"] for row in window30["sources"])
    result["sources"] = len(window30["sources"])
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
