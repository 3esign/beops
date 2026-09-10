#!/usr/bin/env python3
"""export_permission_dataset.py - publish the permission landscape itself as a dataset.

Why this exists. Everything this observatory publishes is a measurement of Belgrade. The one thing it
holds that nobody else has measured at all is a measurement of ACCESS: what it costs, in permission,
to observe a European capital from outside its institutions. 215 sources reviewed one at a time, each
with a status and a written reason; 14 organisations that said no, named; 313 captures of the bytes
that were actually served when permission was checked.

That is the paper's central claim in the form of an artefact rather than an argument, and it is
citable in a way an argument is not.

WHAT IS IN IT
  sources.csv        one row per reviewed source: id, theme, kind, status, whether it is polled,
                     whether stored permission evidence exists, and the reason in the reviewer's words
  refusals.csv       the named refusals, on their own, because they are the finding
  captures.csv       one row per stored capture: source, timestamp, what was fetched, sha256
  data_dictionary.md every column, what it means, and what it must not be read as
  README.md          provenance, licence, the known biases, how to cite it

WHAT IS NOT IN IT, and the omissions are the point:
  - no captured bytes. The captures are third-party content held as evidence, not as publication.
    Their hashes are here; a reviewer may ask for any capture by id and sha256.
  - no headline text and no personal data of any kind. This dataset is about organisations.
  - no measurement values. Those are a different dataset with a different licence question.

WHAT IT MUST NOT BE READ AS. A status is this project's reading of what a publisher's site said on
the day it was read, in the reviewer's words - not a legal characterisation of that publisher, not a
compliance score, and not a ranking. `opted_out` means an organisation declined to be a source for
this project; it does not mean the organisation is closed, obstructive, or in breach of anything.
Several of the refusals are entirely routine terms-of-use statements.

    python tools/export_permission_dataset.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "dataset" / "permission-landscape"
REG = ROOT / "research" / "SOURCE_REGISTRY.json"
COLLECTORS = ROOT / "research" / "COLLECTORS.json"
LEDGER = ROOT / "research" / "08-provenance" / "LEDGER.jsonl"
VERSION = "1.0"

LICENCE = "CC BY 4.0"
CITE = ("Golubović Matić, D., & Poturak, S. (2026). The permission landscape of a European capital: "
        "215 public data sources reviewed for a city observatory (v%s) [Data set]. "
        "Belgrade Evidence Observatory for Public Signals (BEOPS).") % VERSION


def _reason(s: dict) -> str:
    """The reviewer's own words. Never rewritten, only trimmed and flattened to one line."""
    for k in ("reuse", "access", "next"):
        v = s.get(k)
        if isinstance(v, str) and v.strip():
            return re.sub(r"\s+", " ", v.strip())
    return ""


def build() -> dict:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    srcs = reg["sources"]
    try:
        coll = {c["sid"]: c for c in json.loads(COLLECTORS.read_text(encoding="utf-8"))["sources"]}
    except (OSError, ValueError):
        coll = {}
    ledger = []
    if LEDGER.exists():
        for ln in LEDGER.read_text(encoding="utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if ln.startswith("{"):
                try:
                    ledger.append(json.loads(ln))
                except ValueError:
                    pass
    have_evidence = {str(e.get("sid")) for e in ledger if e.get("sid")}

    OUT.mkdir(parents=True, exist_ok=True)
    made = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    with open(OUT / "sources.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source_id", "theme", "kind", "status", "is_polled", "has_stored_permission_evidence",
                    "host", "reviewer_reason"])
        for s in sorted(srcs, key=lambda x: str(x.get("id"))):
            sid = str(s.get("id"))
            host = ""
            m = re.match(r"https?://([^/]+)", str(s.get("url") or ""))
            if m:
                host = m.group(1)
            w.writerow([sid, s.get("theme"), s.get("kind"), s.get("status"),
                        "yes" if (coll.get(sid) or {}).get("enabled") else "no",
                        "yes" if sid in have_evidence else "no", host, _reason(s)])

    refusals = [s for s in srcs if s.get("status") in ("opted_out", "blocked", "restricted")]
    with open(OUT / "refusals.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source_id", "status", "theme", "kind", "reviewer_reason"])
        for s in sorted(refusals, key=lambda x: str(x.get("id"))):
            w.writerow([s.get("id"), s.get("status"), s.get("theme"), s.get("kind"), _reason(s)])

    with open(OUT / "captures.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source_id", "captured_at_utc", "outcome", "manifest_sha256", "note"])
        for e in ledger:
            w.writerow([e.get("sid"), e.get("captured_at_utc") or e.get("at"),
                        e.get("verdict") or e.get("outcome") or ("allowed" if e.get("allowed_for_us") else ""),
                        e.get("manifest_sha256") or e.get("sha256") or "",
                        re.sub(r"\s+", " ", str(e.get("note") or ""))[:300]])

    counts = {}
    for s in srcs:
        counts[str(s.get("status"))] = counts.get(str(s.get("status")), 0) + 1

    (OUT / "data_dictionary.md").write_text(f"""# Data dictionary — the permission landscape of a European capital

Version {VERSION}, generated {made}.

## sources.csv

| column | meaning |
|---|---|
| `source_id` | this project's internal identifier, stable across versions |
| `theme` | the subject the source concerns, as this project classified it |
| `kind` | what sort of thing the source is (a feed, a register, a catalogue, a refusal) |
| `status` | **this project's reading of what the publisher's site said on the day it was read.** Not a legal characterisation and not a score. `probe_ok` the endpoint answered and nothing forbade us; `primary_page` the site was read but the specific local feed was not validated; `lead` recorded but not independently verified in this pass; `opted_out` the publisher declined; `no_coverage` the source exists but holds nothing for Belgrade; `needs_decision` an unresolved conflict, and therefore not collected; `collected` in the record |
| `is_polled` | whether a collector actually asks this source on a schedule |
| `has_stored_permission_evidence` | whether the bytes served when permission was checked are held on file with a hash |
| `host` | the hostname, so rows can be grouped by publisher |
| `reviewer_reason` | **the reviewer's own words, unedited except for whitespace.** Where they are uncomfortable — "not independently verified", "the actual local feed was not validated" — that is deliberate: the vocabulary exists so an unverified thing cannot quietly become a verified one |

## refusals.csv

The subset that said no, on its own, because it is the finding rather than a footnote to it.
**A refusal is a decision not to be a source for this project.** It is not evidence that an
organisation is closed or obstructive, and several are routine terms-of-use statements that were
never addressed to us. No refusal in this file was contacted, argued with, or worked around.

## captures.csv

One row per stored permission capture. The captured bytes themselves are **not** in this dataset:
they are third-party content held as evidence, not as publication. `manifest_sha256` identifies each
capture, and a reviewer may request any of them by source id and hash.

## What this dataset cannot tell you

- **Whether the list is complete.** It is not. It was assembled by two people reading sites, and a
  later review found that the strongest-licensed sources available — the City's official gazette and
  most of its seventeen municipalities — were missing from it, because the list was built by reading
  robots files rather than by reading the statute.
- **Anything about the publishers' intentions.** A `Disallow` line is a machine instruction, not a
  refusal addressed to a person, and this dataset does not distinguish the two.
- **Anything about Belgrade.** It measures this project's access to signals about Belgrade. Those are
  different things, and conflating them is the error the whole record is built against.
""", encoding="utf-8")

    (OUT / "README.md").write_text(f"""# The permission landscape of a European capital

**{len(srcs)} public data sources reviewed for a city observatory, with the reasons.**
Version {VERSION} · generated {made} · licence **{LICENCE}**

A city-scale evidence instrument can be built for nothing. What cannot be bought is permission. This
dataset is the measurement of that: every source considered for the Belgrade Evidence Observatory,
what was decided about it, why, and whether the bytes that justified the decision are on file.

| | |
|---|---|
| sources reviewed | {len(srcs)} |
| named refusals honoured | {counts.get('opted_out', 0)} |
| unresolved and therefore not collected | {counts.get('needs_decision', 0)} |
| actually polled | {sum(1 for c in coll.values() if c.get('enabled'))} |
| permission captures on file | {len(ledger)} |

Status breakdown: {', '.join(f'{k} {v}' for k, v in sorted(counts.items(), key=lambda x: -x[1]))}

## Files

`sources.csv` · `refusals.csv` · `captures.csv` · `data_dictionary.md` — **read the data dictionary
before the CSVs.** It says what a status is and, more importantly, what it is not.

## How to cite

> {CITE}

## What this is honest about

- A status is a reading of what a site said on one day, in the reviewer's words. It is not a legal
  characterisation of any organisation, not a compliance score, and not a ranking.
- The source list is incomplete and its gaps are not random: it was assembled by reading robots files
  and terms pages rather than by reading the statute, and it under-represents official publishers,
  who are exactly the ones whose material is least encumbered.
- No refusal was contacted, argued with, or routed around, and none appears here as anything other
  than a decision this project accepted.
- The captured bytes are not included. Their hashes are.

## Licence

The dataset is offered under **{LICENCE}**. It contains this project's own descriptions and decisions.
It contains no third-party content, no measurement values, and no personal data.
""", encoding="utf-8")

    files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != "MANIFEST.json")
    manifest = {"schema": "beops-dataset/v1", "name": "permission-landscape", "version": VERSION,
                "generated_at": made, "licence": LICENCE, "cite_as": CITE,
                "counts": {"sources": len(srcs), "refusals": len(refusals), "captures": len(ledger),
                           "by_status": counts},
                "files": [{"name": p.name, "bytes": p.stat().st_size,
                           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    m = build()
    print("permission-landscape v%s -> %s" % (m["version"], OUT))
    for f in m["files"]:
        print("  %-22s %8d bytes  %s" % (f["name"], f["bytes"], f["sha256"][:16]))
    print("  sources %(sources)d | refusals %(refusals)d | captures %(captures)d" % m["counts"])
