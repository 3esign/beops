"""Offline bounded-memory audit of S158 station 21 JSON or JSON.gz.

Usage: python -B research/audit_fixed21_20260906.py INPUT [--output NEW_JSON]
No network. Existing output paths are refused. Input evidence is never changed.
input_bytes and input_sha256 always describe decompressed JSON content.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import gzip
import json
from pathlib import Path
import re
import sys


def open_content(path, mode, **kwargs):
    """Read the same JSON bytes from a plain file or a .gz representation."""
    if path.suffix.lower() == ".gz":
        return gzip.open(path, mode, **kwargs)
    return path.open(mode, **kwargs)


def array_objects(path):
    """Parse one top-level array using JSONDecoder and bounded text chunks."""
    decoder = json.JSONDecoder()
    with open_content(path, "rt", encoding="utf-8") as handle:
        buf = ""
        eof = False

        def fill():
            nonlocal buf, eof
            chunk = handle.read(1024 * 1024)
            if not chunk:
                eof = True
            buf += chunk

        def whitespace():
            nonlocal buf
            buf = buf.lstrip()
            while not buf and not eof:
                fill()
                buf = buf.lstrip()

        whitespace()
        if not buf.startswith("["):
            raise ValueError("Top-level JSON array required")
        buf = buf[1:]
        first = True
        while True:
            whitespace()
            if buf.startswith("]"):
                buf = buf[1:]
                whitespace()
                if buf:
                    raise ValueError("Unexpected trailing data")
                return
            if not first:
                if not buf.startswith(","):
                    raise ValueError("Expected array comma")
                buf = buf[1:]
                whitespace()
                if buf.startswith("]"):
                    raise ValueError("Trailing comma")
            while True:
                try:
                    value, end = decoder.raw_decode(buf)
                    break
                except json.JSONDecodeError:
                    if eof:
                        raise
                    fill()
            if not isinstance(value, dict):
                raise ValueError("Every array member must be an object")
            buf = buf[end:]
            first = False
            yield value


def audit(path):
    raw_hash = hashlib.sha256()
    size = 0
    with open_content(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            raw_hash.update(chunk)
            size += len(chunk)
    timestamps = {}
    schemas = Counter()
    yearly = Counter()
    numeric = {}
    sentinel_bands = {}
    total = rows = duplicate_rows = conflicting_rows = backwards = 0
    rbr_errors = invalid_times = timezone_times = all_zero = 0
    sentinel_rows = sentinel_cells = 0
    header = None
    previous = None
    extra_headers = 0
    for obj in array_objects(path):
        total += 1
        if "DATUM_VREME" not in obj:
            if header is None:
                header = obj
            else:
                extra_headers += 1
            continue
        rows += 1
        rbr_errors += obj.get("RBR") != rows
        stamp = obj["DATUM_VREME"]
        shape_ok = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", stamp))
        try:
            datetime.fromisoformat(stamp)
            valid = shape_ok
        except ValueError:
            valid = False
        invalid_times += not valid
        timezone_times += bool(re.search(r"Z$|[+-]\d{2}:?\d{2}$", stamp))
        backwards += previous is not None and stamp < previous
        previous = stamp
        payload = {key: val for key, val in obj.items() if key != "RBR"}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True,
                                            separators=(",", ":")).encode("ascii")).digest()
        if stamp in timestamps:
            duplicate_rows += 1
            conflicting_rows += timestamps[stamp] != digest
        else:
            timestamps[stamp] = digest
        schemas[tuple(obj)] += 1
        yearly[stamp[:4]] += 1
        row_sentinel = False
        row_zero = True
        for key, value in obj.items():
            if key in ("RBR", "DATUM_VREME"):
                continue
            info = numeric.setdefault(key, {"count": 0, "null_or_empty": 0,
                                           "nonnumeric": 0, "zero": 0})
            info["count"] += 1
            if value is None or value == "":
                info["null_or_empty"] += 1
            else:
                try:
                    number = float(value)
                    info["zero"] += number == 0
                except (ValueError, TypeError):
                    info["nonnumeric"] += 1
            if re.fullmatch(r"\d+M_\d+M", key):
                row_zero = row_zero and float(value) == 0
                if value == "99999.99":
                    row_sentinel = True
                    sentinel_cells += 1
                    band = sentinel_bands.setdefault(key, {"cells": 0, "first": stamp, "last": stamp})
                    band["cells"] += 1
                    band["first"] = min(band["first"], stamp)
                    band["last"] = max(band["last"], stamp)
        all_zero += row_zero
        sentinel_rows += row_sentinel
    times = sorted(timestamps)
    intervals = Counter()
    greater = {"six_minutes": 0, "one_hour": 0, "one_day": 0}
    largest = {"nominal_seconds": 0}
    for before, after in zip(times, times[1:]):
        seconds = int((datetime.fromisoformat(after) - datetime.fromisoformat(before)).total_seconds())
        intervals[seconds] += 1
        greater["six_minutes"] += seconds > 360
        greater["one_hour"] += seconds > 3600
        greater["one_day"] += seconds > 86400
        if seconds > largest["nominal_seconds"]:
            largest = {"nominal_seconds": seconds, "from": before, "to": after}
    return {
        "status": "verified_local_parse_with_unresolved_source_semantics",
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_path": str(path.resolve()), "input_bytes": size,
        "input_sha256": raw_hash.hexdigest(),
        "input_representation": "gzip" if path.suffix.lower() == ".gz" else "json",
        "input_file_bytes": path.stat().st_size,
        "input_hash_semantics": "input_sha256 and input_bytes describe decompressed JSON content",
        "source_id": "S158", "source_url": "https://emf.ratel.rs/getOpenData/21/json",
        "method": {
            "network_requests": 0,
            "parser": "Python standard-library JSONDecoder, streaming top-level array; each object validated",
            "timestamp_comparison": "Naive source wall-clock strings; no timezone inferred; sorted unique timestamps for gaps",
            "duplicate_comparison": "Compare every extra same-time row to first row at that timestamp; exclude RBR; sorted-key JSON serialization before SHA256",
            "source_modifications": "None; no rows dropped or values recoded",
        },
        "header": header,
        "counts": {"total_objects": total, "header_objects": total - rows,
                   "extra_nonmeasurement_objects": extra_headers, "measurement_rows": rows,
                   "unique_timestamps": len(times), "extra_duplicate_time_rows": duplicate_rows,
                   "extra_duplicate_time_rows_conflicting_with_first": conflicting_rows,
                   "backwards_file_order_transitions": backwards, "nonsequential_rbr": rbr_errors,
                   "invalid_datetime_values": invalid_times, "explicit_timezone_strings": timezone_times},
        "time_range": {"earliest": times[0], "latest": times[-1], "timezone": None},
        "schemas": [{"fields": list(keys), "rows": value} for keys, value in schemas.items()],
        "rows_by_timestamp_year_duplicates_retained": dict(sorted(yearly.items())),
        "gaps": {"common_nominal_seconds_and_counts": intervals.most_common(10),
                 "strictly_greater_than": greater, "largest": largest},
        "numeric_field_checks": numeric,
        "values_needing_source_interpretation": {
            "exact_string": "99999.99", "rows": sentinel_rows, "cells": sentinel_cells,
            "by_band": sentinel_bands, "all_twenty_bands_zero_rows": all_zero,
            "meaning": "Unknown. Sentinel-like pattern; not accepted as physical maximum, not silently converted to missing.",
        },
        "limitations": [
            "Header location says pasiv while AKTIVNO says Da; current operational status unresolved.",
            "Latest timestamp is historical relative to retrieval; current feed not proven.",
            "Timezone and daylight-saving policy absent; nominal gap calculations are not uptime.",
            "Header declares E-field effective value V/m; no separate temperature/humidity units or ambient-weather meaning.",
            "Model and serial number not declared in this response.",
            "Bands overlap; summing them as total exposure is not valid without a source method.",
            "Conflicting duplicates, zero values, gaps and sentinel-like values retained exactly in original.",
        ],
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.input)
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as out:
            out.write(encoded)
        print(json.dumps({"output": str(args.output), "input_sha256": result["input_sha256"],
                          "counts": result["counts"], "time_range": result["time_range"]},
                         ensure_ascii=True))
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
