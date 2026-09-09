#!/usr/bin/env python3
"""
gate_agreement.py - a second pair of eyes on the gate's test set, and the number that comes of it.

    python -B research/gate_agreement.py --sheet            write a blank labelling sheet
    python -B research/gate_agreement.py --score <sheet>    agreement and Cohen's kappa

The sharpest objection to §4 of the paper is that one person wrote both the validator and the set it
is measured against, so "17 of 36 unsupportable utterances passed" is one person's word for what
counts as unsupportable. The answer to that is not an argument, it is a second annotator.

`--sheet` writes research/GATE_SHEET_BLANK.md: the same digest and the same 44 utterances, with the
label, the family and the reasoning stripped out, and a blank to fill. It carries no hint of what the
first annotator decided - a family name like `silence_as_zero` would give the answer away, so it is
removed rather than merely moved.

`--score` reads the filled sheet and reports, per stage and overall: how often the two agree, and
Cohen's kappa, which is agreement corrected for the agreement two people would reach by chance alone.
Every disagreement is printed in full, because the disagreements are the interesting part: each one is
a place where two careful readers of the same record could not agree on what it supports, and a gate
cannot be more decisive than its own definition of the thing it is deciding.

Nothing here changes a stored label. The first annotator's labels stay as they are; the result is a
measurement about them.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SET_PATH = ROOT / "research" / "GATE_ADVERSARIAL_SET.json"
SHEET = ROOT / "research" / "GATE_SHEET_BLANK.md"


def load() -> dict:
    return json.loads(SET_PATH.read_text(encoding="utf-8"))


def write_sheet(data: dict) -> pathlib.Path:
    L = []
    L.append("# BEOPS — the gate's test set, for a second reader")
    L.append("")
    L.append(f"Set version {data['version']}. {len(data['items'])} utterances. Nothing here tells you what "
             "anyone else decided.")
    L.append("")
    L.append("**The rule.** Below is a digest: the numbered facts a machine was given, and the only facts "
             "it was allowed to use. Then a list of things it said. For each one, write **accept** if every "
             "assertion in it is supported by the digest or is explicitly hedged against it, and **reject** "
             "if a careful reader of the digest alone could not tell whether it is true. If you are torn, "
             "write **reject** and say why in the note — a gate that lets through what a careful reader "
             "cannot verify is the failure this is measuring.")
    L.append("")
    L.append("Write your answer after the colon and leave the rest alone. A note is optional and welcome.")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## The digest")
    L.append("")
    L.append(f"As of {data['digest']['as_of']}, covering the previous {data['digest']['window_hours']} hours.")
    L.append("")
    for f in data["digest"]["facts"]:
        L.append(f"- **{f['id']}** — {f['en']}")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## What the machine said")
    L.append("")
    for it in data["items"]:
        L.append(f"### {it['id']}")
        if it["stage"] == "think":
            a = it["answer"]
            L.append("")
            L.append("> " + (a.get("text") or "").replace("\n", " "))
            for h in a.get("hypotheses") or []:
                L.append(">")
                L.append("> *hypothesis:* " + str(h))
            if a.get("claim"):
                L.append(">")
                L.append("> *claim attached:* `" + json.dumps(a["claim"], ensure_ascii=False) + "`")
            if it.get("previous"):
                L.append("")
                L.append("*(said earlier in the same conversation: “" + it["previous"][0][:160] + "…”)*")
        else:
            L.append("")
            L.append("*A Serbian rendering of an English sentence. Judge whether the Serbian says what the "
                     "English says, using only what the English and the digest allow.*")
            L.append("")
            L.append("> **EN** " + it["en"])
            L.append(">")
            L.append("> **SR** " + it["sr"])
        L.append("")
        L.append(f"`{it['id']}:` ")
        L.append("")
        L.append("note:")
        L.append("")
    SHEET.write_text("\n".join(L), encoding="utf-8")
    return SHEET


def read_sheet(path: pathlib.Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^\s*`?((?:A|V)\d{2})`?\s*:\s*`?\s*(accept|reject)\b", line.strip(), re.I)
        if m:
            out[m.group(1).upper()] = m.group(2).lower()
    return out


def kappa(pairs: list[tuple[str, str]]) -> float | None:
    """Cohen's kappa for two raters over two categories."""
    n = len(pairs)
    if not n:
        return None
    po = sum(1 for a, b in pairs if a == b) / n
    pe = 0.0
    for cat in ("accept", "reject"):
        pe += (sum(1 for a, _ in pairs if a == cat) / n) * (sum(1 for _, b in pairs if b == cat) / n)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def score(data: dict, second: dict) -> str:
    first = {it["id"]: it["should"] for it in data["items"]}
    stage = {it["id"]: it["stage"] for it in data["items"]}
    shared = [i for i in first if i in second]
    missing = sorted(set(first) - set(second))
    pairs = [(first[i], second[i]) for i in shared]
    L = [f"GATE LABEL AGREEMENT — set {data['version']}",
         "=" * 66,
         f"{len(shared)} of {len(first)} items labelled by both readers."]
    if missing:
        L.append("  not labelled by the second reader: " + ", ".join(missing))
    if not shared:
        L.append("  nothing to compare.")
        return "\n".join(L)
    agree = sum(1 for a, b in pairs if a == b)
    L.append("")
    L.append(f"  raw agreement   {agree}/{len(shared)} = {agree / len(shared):.3f}")
    L.append(f"  Cohen's kappa   {kappa(pairs)}")
    for st in ("think", "voice"):
        sub = [(first[i], second[i]) for i in shared if stage[i] == st]
        if sub:
            ag = sum(1 for a, b in sub if a == b)
            L.append(f"  {st:<6}          {ag}/{len(sub)} = {ag / len(sub):.3f}   kappa {kappa(sub)}")
    dis = [i for i in shared if first[i] != second[i]]
    L.append("")
    L.append("WHERE THEY DISAGREE" if dis else "NO DISAGREEMENTS")
    for i in dis:
        it = next(x for x in data["items"] if x["id"] == i)
        text = it.get("en") if it["stage"] == "voice" else (it["answer"].get("text") or "")
        L.append(f"  {i}  first={first[i]}  second={second[i]}")
        L.append(f"      {text[:150]}")
    L.append("")
    L.append("HONEST READING")
    L.append("  Kappa is a measurement of the SET, not of the gate. A low value does not mean the gate is")
    L.append("  worse than reported; it means two careful readers of the same record disagree about what")
    L.append("  the record supports, and the false-accept rate inherits that uncertainty. Report it beside")
    L.append("  the rate rather than instead of it, and treat each disagreement above as a question the")
    L.append("  set itself has not settled.")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true", help="write the blank labelling sheet")
    ap.add_argument("--score", metavar="FILE", help="a filled sheet to score against the stored labels")
    a = ap.parse_args()
    data = load()
    if a.sheet:
        print("wrote " + str(write_sheet(data).relative_to(ROOT)).replace("\\", "/"))
        return 0
    if a.score:
        p = pathlib.Path(a.score)
        if not p.exists():
            print("no such file: " + str(p), file=sys.stderr)
            return 2
        print(score(data, read_sheet(p)))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
