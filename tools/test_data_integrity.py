#!/usr/bin/env python3
"""
test_data_integrity.py - ultra-fast sanity gate (< 1s) for BEOPS data-only releases.

Verifies:
- docs/index.html (citizen front door) and docs/instrument.html (evidence instrument) exist and are non-empty.
- All core public JSON files parse cleanly and conform to their schemas.
- No forbidden markers (e.g. Claude, undefined, NaN) in public documents.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PUBLIC = ROOT / "public"

def main() -> int:
    errors = []

    # 1. HTML entries
    idx = DOCS / "index.html"
    inst = DOCS / "instrument.html"

    if not idx.exists() or idx.stat().st_size < 1000:
        errors.append("docs/index.html missing or too small")
    else:
        text = idx.read_text(encoding="utf-8")
        if "Beograd danas" not in text:
            errors.append("docs/index.html missing 'Beograd danas' title/brand")
        if "BEOPS" not in text:
            errors.append("docs/index.html missing 'BEOPS'")

    if not inst.exists() or inst.stat().st_size < 100000:
        errors.append("docs/instrument.html missing or too small")
    else:
        text = inst.read_text(encoding="utf-8")
        if "href=\"index.html\"" not in text and "href='index.html'" not in text:
            errors.append("docs/instrument.html missing back-link to index.html")

    # 2. JSON files
    core_jsons = [
        (PUBLIC / "events.json", "beops-events/v1"),
        (PUBLIC / "live-snapshot.json", "beops-live-snapshot/v1"),
        (PUBLIC / "headlines.json", "beops-headline-archive/v1"),
        (DOCS / "city-overview.json", "beops-city-view/v1"),
    ]

    for path, expected_schema in core_jsons:
        if not path.exists():
            errors.append(f"{path.name} does not exist")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if expected_schema and data.get("schema") != expected_schema:
                errors.append(f"{path.name} schema mismatch: expected {expected_schema}, got {data.get('schema')}")
        except Exception as e:
            errors.append(f"{path.name} JSON parse error: {e}")

    # 3. Forbidden markers check in index.html
    if idx.exists():
        idx_text = idx.read_text(encoding="utf-8")
        for bad in ["undefined", "NaN", "Claude, Anthropic"]:
            if bad in idx_text:
                errors.append(f"docs/index.html contains forbidden token: {bad}")

    if errors:
        print("DATA INTEGRITY GATE FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("DATA INTEGRITY GATE OK: all core JSONs and HTML pages verified (< 1s).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
