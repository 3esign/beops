#!/usr/bin/env python3
"""
build_provenance_index.py - render research/08-provenance/INDEX.md from the
stored captures. The index is GENERATED, never hand-written, so it cannot
claim a permission that no captured bytes support.

Inputs
  research/08-provenance/LEDGER.jsonl   one line per capture (append-only)
  research/SOURCE_REGISTRY.json         the sources themselves

Output
  research/08-provenance/INDEX.md

Rules encoded here:
  * A source with no capture is listed under "NOT YET DOCUMENTED" - visible,
    not hidden. That list is the work queue.
  * A capture whose robots verdict is False, or that carries an opt-out signal
    header, is listed under "DO NOT COLLECT" no matter what any note says.
    An opt-out signal is one that reserves rights against READING or text and
    data mining: `X-Robots-Tag` containing `noai` or `noimageai`,
    `TDM-Reservation: 1`, or `Content-Usage` denying `ai`/`tdm`. A plain
    `noindex`/`nofollow`/`index, follow` is an instruction to search engines
    about indexing, not a refusal to be read, and is recorded in the row but
    does not refuse. See CORRECTIONS.md C-010 - the first version of this rule
    treated the mere presence of any such header as a refusal and so listed a
    CC BY dataset that explicitly permits commercial reuse under "said no".
  * A capture that did not complete - TLS failed, robots.txt unreadable, a URL
    unreachable - is listed under "EVIDENCE INCOMPLETE". An unknown is never
    rendered as a permission. This section exists because the first run of
    legal_capture.py did exactly that; see CORRECTIONS.md.
  * The newest capture per source wins for the verdict; every capture is kept.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "research", "08-provenance", "LEDGER.jsonl")
REGISTRY = os.path.join(ROOT, "research", "SOURCE_REGISTRY.json")
OUT = os.path.join(ROOT, "research", "08-provenance", "INDEX.md")


def rel(evidence_dir: str) -> str:
    """Evidence paths are stored relative to the repo root; INDEX.md lives two
    levels down, so links must be rewritten or every one of them is broken."""
    return os.path.relpath(os.path.join(ROOT, evidence_dir),
                           os.path.dirname(OUT)).replace("\\", "/")


def load_ledger():
    rows = []
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def load_registry():
    if not os.path.exists(REGISTRY):
        return {}
    with open(REGISTRY, encoding="utf-8") as fh:
        data = json.load(fh)
    recs = data.get("sources", data if isinstance(data, list) else [])
    out = {}
    for r in recs:
        sid = r.get("id") or r.get("sid")
        if sid:
            out[sid] = r
    return out


from permission_policy import header_refusals


def name_of(sid: str, entry: dict, registry: dict) -> str:
    """The source's name for a row of the index, from the capture, then the registry, then said to be
    absent.

    It used to be `entry['name']`, so a single ledger line written without that key took down the
    generation of the whole provenance index - the file the paper's permission figures are read out
    of. One malformed line is not a reason for a record to become unreadable, and an index that shows
    a row with its name missing is more use than an index that does not exist.
    """
    return (entry.get("name") or (registry.get(sid) or {}).get("name")
            or (registry.get(sid) or {}).get("title") or "(name not recorded in the capture)")


def main() -> int:
    ledger = load_ledger()
    from permission_policy import latest
    effective = latest(LEDGER)
    registry = load_registry()

    by_sid = defaultdict(list)
    for e in ledger:
        by_sid[e["sid"]].append(e)
    for sid in by_sid:
        by_sid[sid].sort(key=lambda e: e["captured_at_utc"])

    forbidden, permitted, incomplete, undecided = [], [], [], []
    for sid, caps in by_sid.items():
        last = effective.get(sid, caps[-1])
        # Content-Signal is per purpose, not yes/no. BEOPS reads; it does not
        # train. So ai-input=no or search=no forbids what we actually do, while
        # ai-train=no is a real restriction we honour and record but which does
        # not by itself stop us reading. Treating them the same would either
        # lose sources we may use, or let us use ones we may not.
        sigs = {k: v for sig in (last.get("content_signal") or {}).values() for k, v in sig.items()}
        signal_no = sigs.get("ai-input") == "no" or sigs.get("search") == "no"
        signal_note = ", ".join(f"{k}={v}" for k, v in sorted(sigs.items())) if sigs else ""
        if last.get("manual_verdict") == "needs_decision":
            undecided.append((sid, caps))
        elif last.get("manual_verdict") == "refused" or (last.get("allowed_for_us") is False) or header_refusals(last) or signal_no:
            forbidden.append((sid, caps))
        elif last.get("allowed_for_us") is True and last.get("capture_ok", False):
            permitted.append((sid, caps))
        else:
            incomplete.append((sid, caps))

    undocumented = sorted(set(registry) - set(by_sid))

    L = []
    A = L.append
    A("# Provenance index — stored access evidence and legal review")
    A("")
    A("<!-- GENERATED by tools/build_provenance_index.py. Do not edit by hand;")
    A("     capture again or update registry legal reviews, then re-run. Never edit old evidence. -->")
    A("")
    A(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · "
      f"{len(by_sid)} sources with stored evidence · {len(ledger)} captures · "
      f"{len(permitted)} access checks passed · {len(forbidden)} refused · "
      f"{len(undecided)} awaiting decision · "
      f"{len(incomplete)} incomplete · {len(undocumented)} undocumented")
    A("")
    A("Every row below is backed by bytes on disk under `research/evidence/legal/`:")
    A("the site's own `robots.txt` as it was served, the response headers of the")
    A("exact URLs we intend to read (including any `X-Robots-Tag` or")
    A("`Content-Signal` opt-out), the licence or terms page as it was served, and")
    A("a SHA-256 of each. These are stored access signals, not blanket licences")
    A("for retention, repeated extraction, model training or republication.")
    A("Apply the existing [legal frame](../07-legal/COLLECTION_LEGAL_FRAME.md) and")
    A("[edge cases](EDGE_CASES.md); unknown reuse rights remain unknown.")
    A("")
    A("Outbound requests use the workspace transport identity. Each capture records")
    A("the actual request agent and evaluates that agent against the stored robots rules.")
    A("")

    if forbidden:
        A("## Do not collect")
        A("")
        A("These said no. The answer is no. They stay listed so that nobody")
        A("re-discovers them next year and quietly starts collecting.")
        A("")
        A("| id | source | what said no | captured |")
        A("|---|---|---|---|")
        for sid, caps in sorted(forbidden):
            last = effective.get(sid, caps[-1])
            why = []
            if last.get("allowed_for_us") is False:
                why.append("robots.txt disallows our agent")
            csig = {k: v for sg in (last.get("content_signal") or {}).values() for k, v in sg.items()}
            if csig.get("ai-input") == "no" or csig.get("search") == "no":
                why.append("`Content-Signal: " + ", ".join(f"{k}={v}" for k, v in sorted(csig.items())) + "`")
            for u, sig in header_refusals(last).items():
                why.append("; ".join(f"`{k}: {v}`" for k, v in sig.items()))
            if last.get("manual_verdict") == "refused":
                why.append(last.get("manual_reason") or "refused by decision")
            A(f"| {sid} | {name_of(sid, last, registry)} | {' · '.join(why) or 'see capture'} | "
              f"[{last['captured_at_utc']}]({rel(last['evidence_dir'])}/) |")
        A("")

    A("## Access checks passed — reuse remains source-specific")
    A("")
    A("Where a row carries a `Content-Signal`, it is an express reservation of")
    A("rights under Article 4 of Directive (EU) 2019/790. We read; we do not")
    A("train. `ai-train=no` is honoured as written and recorded here, and any")
    A("source carrying it must never be used to train anything.")
    A("")
    A("| id | source | robots.txt | HTTP | Content-Signal | evidence | last checked |")
    A("|---|---|---|---|---|---|---|")
    for sid, caps in sorted(permitted):
        last = effective.get(sid, caps[-1])
        rb = "; ".join(v["regime"] for v in last.get("robots", {}).values()) or "—"
        codes = sorted({str(c) for c in last.get("status_by_url", {}).values()})
        cs = {k: v for sg in (last.get("content_signal") or {}).values() for k, v in sg.items()}
        cst = ", ".join(f"{k}={v}" for k, v in sorted(cs.items())) if cs else "—"
        A(f"| {sid} | {name_of(sid, last, registry)} | {rb} | {', '.join(codes) or '—'} | {cst} | "
          f"[{len(caps)} capture{'s' if len(caps) > 1 else ''}]({rel(last['evidence_dir'])}/) | "
          f"{last['captured_at_utc']} |")
    A("")

    if undecided:
        A("## Decision required — do not collect until it is made")
        A("")
        A("The capture completed and the verdict is deliberately held open,")
        A("because the letter and the evident intent of the rule point different")
        A("ways. Each is written up in `EDGE_CASES.md`. Until a decision is")
        A("recorded there, nothing may be collected from these.")
        A("")
        A("| id | source | why it is open | captured |")
        A("|---|---|---|---|")
        for sid, caps in sorted(undecided):
            last = effective.get(sid, caps[-1])
            A(f"| {sid} | {name_of(sid, last, registry)} | {(last.get('manual_reason') or '')[:150]} | "
              f"[{last['captured_at_utc']}]({rel(last['evidence_dir'])}/) |")
        A("")

    if incomplete:
        A("## Evidence incomplete — not usable yet")
        A("")
        A("The capture did not finish: TLS could not be verified, `robots.txt`")
        A("could not be read, or a URL was unreachable. **An unknown is not a")
        A("permission.** Nothing from these sources may be collected until a")
        A("capture completes. Re-run `tools/legal_capture.py` for each.")
        A("")
        A("| id | source | what failed | captured |")
        A("|---|---|---|---|")
        for sid, caps in sorted(incomplete):
            last = effective.get(sid, caps[-1])
            why = []
            for o in last.get("robots_unreadable_origins") or []:
                why.append(f"robots.txt unreadable at {o}")
            for u in last.get("fetch_failed_urls") or []:
                why.append(f"unreachable: {u}")
            if not why:
                why.append("verdict unknown")
            A(f"| {sid} | {name_of(sid, last, registry)} | {'; '.join(why)[:160]} | "
              f"[{last['captured_at_utc']}]({rel(last['evidence_dir'])}/) |")
        A("")

    if undocumented:
        A("## Not yet documented — this is the work queue")
        A("")
        A("These are in `SOURCE_REGISTRY.json` but have no stored permission")
        A("evidence. Until a capture exists, no number from them may be")
        A("published. Run:")
        A("")
        A("```")
        A("python -B tools/legal_capture.py --sid <ID> --name \"<name>\" \\")
        A("    --url <the exact URL we read> --terms <licence page>")
        A("```")
        A("")
        for sid in undocumented:
            r = registry.get(sid, {})
            nm = r.get("name") or r.get("title") or ""
            st = r.get("status", "")
            A(f"- `{sid}` — {nm} ({st})")
        A("")

    reviewed = defaultdict(list)
    for sid, record in registry.items():
        review = record.get("legal_review")
        if isinstance(review, dict):
            reviewed[review.get("category", "Unresolved")].append((sid, record, review))
    if reviewed:
        A("## Legal sorting — reviewed records")
        A("")
        A("This review is separate from the automated access verdict above. It does")
        A("not change that verdict or grant rights. Unreviewed records are not cleared")
        A("by omission. See the [initial matrix](../07-legal/DEVICE_DATA_LEGAL_SORT_2026-09-06.md) and [follow-up scope review](../07-legal/DEVICE_FOLLOWUP_LEGAL_2026-09-06.md).")
        A("")
        for category, records in sorted(reviewed.items()):
            A("### " + category)
            A("")
            A("| id | source | basis/evidence | scope and remaining gate |")
            A("|---|---|---|---|")
            for sid, record, review in sorted(records):
                cells = [sid, record.get("name", ""), review.get("basis", "Unknown"), review.get("scope", "Unresolved")]
                A("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in cells) + " |")
            A("")

    A("## How to add a source, in full")
    A("")
    A("1. Run `tools/legal_capture.py` **before** writing the collector. If the")
    A("   capture comes back disallowed, stop there and record it as such.")
    A("2. Add the source to `research/SOURCE_REGISTRY.json` with the same id.")
    A("3. Re-run `python -B tools/build_provenance_index.py` and commit the")
    A("   regenerated index together with the capture, in one commit.")
    A("4. Re-capture whenever the terms could have changed, and at least once")
    A("   before anything is published. Old captures are never deleted — a")
    A("   permission that was true in 2026 is part of the record even if the")
    A("   site changes its mind in 2027.")
    A("")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))
    print(f"wrote {os.path.relpath(OUT, ROOT)}  ({len(L)} lines, "
          f"{len(permitted)} access checks passed, {len(forbidden)} forbidden, {len(undocumented)} undocumented)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
