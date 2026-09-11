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
import shutil
from contracts import json_rows
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
VERSION = "1.2"

# The sentence the dataset turns on. It is written once and quoted into both the dictionary and the
# README, because when it lived in two places the two copies had already drifted: the README said
# "not a compliance score, and not a ranking" and the dictionary said only "not a score".
NOT_A_SCORE = ("not a legal characterisation of any organisation, not a compliance score, "
               "and not a ranking")

# Every version that was ever generated, and why it is not the previous one. A published dataset
# whose text changes while its version does not is a quiet edit, which is the thing this project
# exists to refuse.
# Exactly what this dataset is. The manifest is built from this list and not from whatever happens
# to be lying in the directory: v1.0 published a working note that had been left there, because the
# manifest was a directory listing. A file in the folder that is not named here stops the build.
PUBLISHED = ("sources.csv", "refusals.csv", "captures.csv", "data_dictionary.md",
             "README.md", "CHANGES.md", "zenodo.json")

CHANGES = [
    ("1.2", "2026-09-11", "Capture manifest hashes are read and verified from stored evidence; outcomes are explicit allowed/refused/unknown. Each content edition is preserved under releases/<edition_id>."),
    ("1.1", "2026-09-10",
     "Three corrections, none of them to a row. (a) The data dictionary's caveat on `status` was "
     "shorter than the README's and had lost \"compliance score\" and \"ranking\"; both now quote "
     "one sentence held in one place. (b) `zenodo.json` was written by hand while stating that it "
     "had been generated from the record; it is now generated from the record, and carries the "
     "version it describes, which it did not before. (c) v1.0's manifest was a listing of the "
     "directory, so a working note left in that folder was published as part of the dataset; the "
     "manifest is now built from a declared list and a file that is not on it stops the build. "
     "The CSVs of 1.1 are byte-identical to those of 1.0, verified by hash."),
    ("1.0", "2026-09-10", "First publication: 215 sources reviewed, the refusals named, the "
     "permission captures listed by hash."),
]

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
    ledger = list(json_rows(LEDGER))
    for entry in ledger:
        path = ROOT / entry["evidence_dir"] / "MANIFEST.json"
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if entry.get("manifest_sha256") and entry["manifest_sha256"] != sha:
            raise ValueError("capture manifest mismatch: " + entry["sid"])
        manifest = json.loads(raw)
        if manifest.get("sid") != entry["sid"]:
            raise ValueError("capture identity mismatch: " + entry["sid"])
        entry["manifest_sha256"] = sha
        entry["export_outcome"] = ("refused" if entry.get("manual_verdict") == "refused" or entry.get("allowed_for_us") is False else
            "allowed" if entry.get("allowed_for_us") is True and entry.get("capture_ok") is True else "unknown")
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
                        e["export_outcome"],
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
| `status` | **this project's reading of what the publisher's site said on the day it was read.** It is {NOT_A_SCORE}. `probe_ok` the endpoint answered and nothing forbade us; `primary_page` the site was read but the specific local feed was not validated; `lead` recorded but not independently verified in this pass; `opted_out` the publisher declined; `no_coverage` the source exists but holds nothing for Belgrade; `needs_decision` an unresolved conflict, and therefore not collected; `collected` in the record |
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

{' · '.join('`' + n + '`' for n in PUBLISHED)} — and `MANIFEST.json`, which holds the sha256 and
byte length of each. **Read the data dictionary before the CSVs.** It says what a status is and, more
importantly, what it is not. `CHANGES.md` says what each version is not, relative to the one before it.

## How to cite

> {CITE}

## What this is honest about

- A status is a reading of what a site said on one day, in the reviewer's words. It is
  {NOT_A_SCORE}.
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

    (OUT / "CHANGES.md").write_text(
        "# Changes\n\nEach version of this dataset says what it is not, relative to the one before "
        "it. Older versions are not rewritten.\n\n"
        + "\n".join(f"## {v} — {d}\n\n{what}\n" for v, d, what in CHANGES),
        encoding="utf-8")

    (OUT / "zenodo.json").write_text(json.dumps(
        {"metadata": {
            "upload_type": "dataset",
            "title": ("The permission landscape of a European capital: "
                      f"{len(srcs)} public data sources reviewed for a city observatory"),
            "version": VERSION,
            "publication_date": made[:10],
            "creators": [
                {"name": "Golubović Matić, Darinka",
                 "affiliation": "Univerzitet Union — Nikola Tesla, Belgrade"},
                {"name": "Poturak, Semir",
                 "affiliation": "Univerzitet Union — Nikola Tesla, Belgrade"}],
            "description": (
                "<p>A city-scale evidence instrument can be built for nothing. What cannot be bought"
                " is permission. This dataset is the measurement of that: every public source"
                " considered for the Belgrade Evidence Observatory for Public Signals (BEOPS), what"
                " was decided about it, why, and whether the bytes that justified the decision are on"
                f" file.</p><p>It contains {len(srcs)} reviewed sources with the reviewer's own"
                f" written reason for each, the {len(refusals)} that declined on their own, and one"
                f" row per stored permission capture ({len(ledger)}) with its SHA-256. It contains no"
                " captured bytes (third-party content held as evidence, not as publication), no"
                " headline text, no personal data and no measurement values.</p><p><strong>What a"
                " status is not.</strong> A status is this project's reading of what a publisher's"
                f" site said on the day it was read. It is {NOT_A_SCORE}; <em>opted_out</em> means an"
                " organisation declined to be a source for this project, and several of those are"
                " routine terms-of-use statements never addressed to us. Read"
                " <code>data_dictionary.md</code> before the CSVs.</p><p><strong>Known bias, stated"
                " against our own interest.</strong> The source list is incomplete and its gaps are"
                " not random: it was assembled by reading robots files and terms pages rather than by"
                " reading the statute, and it under-represents official publishers, whose material is"
                " least encumbered.</p>"),
            "access_right": "open",
            "license": "cc-by-4.0",
            "language": "eng",
            "keywords": ["urban observatory", "open data", "data access",
                         "web scraping permission", "robots.txt", "provenance", "Belgrade",
                         "Serbia", "research data governance", "city dashboards", "ISO 37120"],
            "related_identifiers": [{"identifier": "https://github.com/3esign/beops",
                                     "relation": "isSupplementTo", "resource_type": "software"}],
            "notes": ("Generated by tools/export_permission_dataset.py from the observatory's own"
                      " registry, provenance ledger and collector configuration. Every figure in it"
                      " is read from the files that hold it; none is typed by hand."),
        }}, ensure_ascii=False, indent=1), encoding="utf-8")

    stray = sorted(p.name for p in OUT.iterdir()
                   if p.is_file() and p.name != "MANIFEST.json" and p.name not in PUBLISHED)
    if stray:
        raise SystemExit(
            "export_permission_dataset: %s is in the dataset folder and not in PUBLISHED. "
            "v1.0 published a working note this way. Either add it to PUBLISHED deliberately or "
            "move it out of public/." % ", ".join(stray))
    missing = [n for n in PUBLISHED if not (OUT / n).exists()]
    if missing:
        raise SystemExit("export_permission_dataset: declared but not written: %s" % ", ".join(missing))

    files = [OUT / n for n in PUBLISHED]
    manifest = {"schema": "beops-dataset/v1", "name": "permission-landscape", "version": VERSION,
                "generated_at": made, "licence": LICENCE, "cite_as": CITE,
                "counts": {"sources": len(srcs), "refusals": len(refusals), "captures": len(ledger),
                           "by_status": counts},
                "files": [{"name": p.name, "bytes": p.stat().st_size,
                           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    edition = hashlib.sha256((VERSION + json.dumps([{k: f[k] for k in ("name", "sha256")} for f in manifest["files"] if f["name"].endswith(".csv")], sort_keys=True)).encode()).hexdigest()
    manifest["edition_id"] = edition
    manifest["edition_path"] = "releases/" + edition
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    version_dir = OUT / "releases" / edition
    if not version_dir.exists():
        version_dir.mkdir(parents=True)
        for name in (*PUBLISHED, "MANIFEST.json"):
            shutil.copyfile(OUT / name, version_dir / name)
    else:
        prior = json.loads((version_dir / "MANIFEST.json").read_text(encoding="utf-8"))
        for f in prior["files"]:
            if hashlib.sha256((version_dir/f["name"]).read_bytes()).hexdigest() != f["sha256"]:
                raise ValueError("immutable dataset edition changed")
    return manifest


if __name__ == "__main__":
    m = build()
    print("permission-landscape v%s -> %s" % (m["version"], OUT))
    for f in m["files"]:
        print("  %-22s %8d bytes  %s" % (f["name"], f["bytes"], f["sha256"][:16]))
    print("  sources %(sources)d | refusals %(refusals)d | captures %(captures)d" % m["counts"])
