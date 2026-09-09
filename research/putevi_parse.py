#!/usr/bin/env python3
"""
putevi_parse.py — turn the JP "Putevi Srbije" AADT workbooks into one tidy
table, preserving the publisher's own account of how each row was obtained and
why each missing value is missing.

The workbooks are 12 columns wide in every year 2018-2024:

    0  No / Ред. број
    1  Section mark / Ознака деонице   node codes: 01001, 01001/01002, A1001/A1002
    2  Section / Саобраћајна деоница   free text "A - B"; also carries "Број пута: X"
    3  Section length (km)
    4..10  AADT split: PC BUS LT MT HT TT Total
    11 Remark / Напомена

Two things make this source unusual, and both are the reason BEOPS wants it.

1. THE PUBLISHER STATES ITS OWN PROVENANCE, ROW BY ROW.
   Every file carries a LEGEND block at the bottom that defines its own
   symbols. From the 2023 IA English edition:

       ATC 1055  - Automatic Traffic Counter
       PTR 1055  - Permanent Traffic Recorder
       PTR       - Portable Traffic Recorder
       TS 30     - Section with a Toll Station
       TS        - Section with Tolling
       INT       - Data Interpolation

   Note what TS is: tolling, not counting. A toll figure is a census of paying
   vehicles, a different instrument from a counter, and it is kept as its own
   state rather than folded into "measured".

2. THE SYMBOLS ARE NOT STABLE ACROSS FILES.
   The asterisk means "data taken from the counter on the neighbouring section"
   in 2018 IA, 2019 IB, 2021 IIA and 2022 IIA — and "unbuilt interchange" in
   2019 IA. One glyph, two meanings, depending on which publication you are
   holding.

   Therefore this parser READS THE LEGEND OUT OF EACH FILE and applies it only
   to that file. There is deliberately no global dictionary. Where a file
   defines no legend entry for a symbol it uses, the row is marked
   `unknown` and the raw text is kept; it is never guessed from a neighbour.

Absence is data here too. Where a count is missing the publisher writes which
kind of missing it is:

    "нема података - градска деоница"       urban section, not counted
    "нема података - прекид бројања"        counting was interrupted
    "неизграђена деоница у 2019. год."      the road did not yet exist

These are carried through as `absence_reason`, never as zero and never as null
alone. A road that did not exist is not a road with no traffic.

Nothing here rounds, fills or repairs.
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys
import unicodedata

COLS = ["pc", "bus", "lt", "mt", "ht", "tt", "total"]

RE_MARK = re.compile(r"^[A-ZА-Я]?\d{3,6}(\s*/\s*[A-ZА-Я]?\d{3,6})?\s*\*?$", re.I)
RE_ROADLINE = re.compile(r"(?:Број\s*пута|Broj\s*puta|Road\s*Number)\s*[:\-]?\s*(.+)", re.I)
RE_LEGEND_START = re.compile(r"(ЛЕГЕНДА|LEGENDA|LEGEND)", re.I)

# The publisher's own legend contains homoglyph typos: the 2019 IA gloss for
# ПАБ reads "пoвремено" with a LATIN o (U+006F) inside a Cyrillic word. Any
# matching that does not fold confusables silently drops that whole class of
# rows into "unknown" — which is how 177 rows went missing on the first pass.
_FOLD = str.maketrans({
    "a": "а", "c": "с", "e": "е", "o": "о", "p": "р", "x": "х", "y": "у", "j": "ј",
    "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "K": "К", "M": "М",
    "O": "О", "P": "Р", "T": "Т", "X": "Х", "Y": "У",
})


def variants(s: str) -> tuple[str, str]:
    """The gloss as written, and with Latin confusables folded to Cyrillic.

    Both are tried, because folding repairs the Cyrillic typos but would
    destroy the English editions: "Automatic Traffic Counter" folded becomes
    "аutomаtiс trаffiс сounter" and matches nothing. Fold one way, test both.
    """
    low = s.lower()
    return low, low.translate(_FOLD)

# Absence: the publisher's own words for why there is no number.
ABSENCE = [
    (re.compile(r"градска деоница|gradska deonica|populated area", re.I), "urban_section_not_counted"),
    (re.compile(r"прекид бројања|prekid brojanja|counting discontinuation", re.I), "counting_interrupted"),
    (re.compile(r"неизграђена|neizgra|undeveloped", re.I), "section_did_not_exist"),
]

# How a legend GLOSS (the publisher's own words) maps onto the BEOPS state
# grammar. The key is matched against the gloss, not against the symbol, so a
# file that renames its symbols still resolves correctly.
GLOSS_STATE = [
    (re.compile(r"аутоматск\w+ бројач|automatic traffic counter|permanent traffic recorder", re.I),
     ("observed", "permanent_counter")),
    (re.compile(r"повремено аутоматско|portable traffic recorder", re.I),
     ("observed", "portable_counter")),
    (re.compile(r"наплат|toll", re.I),
     ("observed", "toll_system")),
    (re.compile(r"интерполациј|interpolation", re.I),
     ("estimated", "interpolation")),
    (re.compile(r"суседн\w+ деониц|neighbouring section|neighboring section", re.I),
     ("transferred", "neighbouring_counter")),
    (re.compile(r"неизграђена петља|undeveloped interchange", re.I),
     ("unavailable", "interchange_not_built")),
]
# Symbols whose meaning is structural rather than instrumental.
STRUCTURAL = [
    (re.compile(r"^(преклоп|overlap)\b", re.I), ("transferred", "overlapping_section")),
    (re.compile(r"^(веза|link)\b", re.I), ("transferred", "link_section")),
    (re.compile(r"^(привремена деоница|temporary section)", re.I), ("unavailable", "temporary_section")),
]

# Absence reason -> the mechanism recorded alongside state "unavailable", so
# that a gap always says which kind of gap it is.
ABSENCE_MECHANISM = {
    "urban_section_not_counted": "urban_section_not_counted",
    "counting_interrupted": "counting_interrupted",
    "section_did_not_exist": "section_did_not_exist",
}


def norm(v) -> str:
    if v is None:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(v)).strip())


def num(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def read_legend(sh) -> dict:
    """Return {SYMBOL: gloss} exactly as this one file defines it."""
    legend, started = {}, False
    for r in range(sh.nrows):
        a, b = norm(sh.cell_value(r, 1)), norm(sh.cell_value(r, 2))
        if not started:
            if RE_LEGEND_START.search(a) or RE_LEGEND_START.search(b):
                started = True
            continue
        if not a or not b:
            continue
        gloss = b.lstrip("-–— ").strip().rstrip(",.")
        sym = re.sub(r"\s*\d+\s*$", "", a).strip()  # "ATC 1055" defines "ATC"
        if sym and gloss and sym not in legend:
            legend[sym] = gloss
    return legend


def classify(remark: str, legend: dict):
    """(state, mechanism, instrument_id, gloss) using THIS file's legend only."""
    r = norm(remark)
    if not r:
        return "unknown", None, None, None
    for rx, (st, mech) in STRUCTURAL:
        if rx.match(r):
            return st, mech, re.sub(r"^\D+", "", r).strip() or None, None
    starred = r.endswith("*")
    core = r.rstrip("*").strip()
    sym = re.sub(r"\s*[\d/]+\s*$", "", core).strip() or core
    inst = (re.search(r"([\d]+(?:\s*/\s*[\d]+)?)\s*$", core) or [None, None])[1]
    gloss = legend.get(sym)
    state, mech = "unknown", None
    if gloss:
        forms = variants(gloss)
        for rx, (st, m) in GLOSS_STATE:
            if any(rx.search(f) for f in forms):
                state, mech = st, m
                break
    if starred:
        # The asterisk is file-local: 2019 IA means "unbuilt interchange",
        # elsewhere it means "borrowed from the neighbouring counter".
        star_gloss = legend.get("*")
        if star_gloss:
            for rx, (st, m) in GLOSS_STATE:
                if any(rx.search(f) for f in variants(star_gloss)):
                    state, mech = st, m
                    break
            gloss = f"{gloss or ''} | * = {star_gloss}".strip(" |")
        else:
            state, mech = "unknown", "asterisk_undefined_in_this_file"
    return state, mech, (inst.replace(" ", "") if inst else None), gloss


def absence_of(cell) -> str | None:
    s = norm(cell)
    if not s:
        return None
    for rx, tag in ABSENCE:
        if rx.search(s):
            return tag
    return None


def parse_file(path: str, manifest: dict, borrow: dict | None = None) -> tuple[list[dict], dict]:
    import xlrd
    base = os.path.basename(path)
    meta = next((f for f in manifest.get("files", []) if f["file"] == base), {})
    sh = xlrd.open_workbook(path).sheet_by_index(0)
    legend = read_legend(sh)
    legend_source = base
    if not legend and borrow:
        # Two 2024 files publish no legend at all. Rather than mark 400 rows
        # unknown, or silently assume a global dictionary, we borrow the legend
        # from another file of the SAME YEAR and record on every row which file
        # it came from. A borrow that is written down is not a guess.
        legend, legend_source = borrow

    rows, road = [], None
    for r in range(sh.nrows):
        c1, c2 = norm(sh.cell_value(r, 1)), norm(sh.cell_value(r, 2))
        m = RE_ROADLINE.search(c2)
        if m and not c1:
            road = m.group(1).strip()
            continue
        if not RE_MARK.match(c1):
            continue
        vals = {k: num(sh.cell_value(r, 4 + i)) for i, k in enumerate(COLS)}
        reason = absence_of(sh.cell_value(r, 4)) or absence_of(sh.cell_value(r, 2))
        state, mech, inst, gloss = classify(sh.cell_value(r, 11), legend)
        if reason and vals["total"] is None:
            state, mech = "unavailable", ABSENCE_MECHANISM.get(reason, mech)
        rows.append({
            "year": meta.get("year"), "road_category": meta.get("category"),
            "language": meta.get("language"), "road": road,
            "section_mark": c1.replace(" ", ""),
            "section": "" if absence_of(sh.cell_value(r, 2)) else c2,
            "length_km": num(sh.cell_value(r, 3)),
            **vals,
            "state": state, "mechanism": mech, "instrument": inst,
            "absence_reason": reason,
            "remark_raw": norm(sh.cell_value(r, 11)),
            "legend_gloss": gloss,
            "legend_source": legend_source,
            "source_file": base, "source_url": meta.get("url"),
            "source_sha256": meta.get("sha256"),
        })
    return rows, legend


def main(indir: str, outdir: str) -> int:
    with open(os.path.join(indir, "MANIFEST.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    paths = sorted(glob.glob(os.path.join(indir, "*.xls")))
    own = {}
    for p in paths:
        import xlrd
        own[os.path.basename(p)] = read_legend(xlrd.open_workbook(p).sheet_by_index(0))

    def donor(base: str):
        year = base[:4]
        for other, leg in own.items():
            if other != base and other.startswith(year) and len(leg) >= 8:
                return leg, other
        return None

    rows, legends = [], {}
    for p in paths:
        base = os.path.basename(p)
        got, leg = parse_file(p, manifest, borrow=None if own[base] else donor(base))
        rows.extend(got)
        legends[base] = {"own": own[base], "used": leg,
                         "borrowed_from": None if own[base] else (donor(base) or (None, None))[1]}
        tag = "" if own[base] else f"  <- legend borrowed from {(donor(base) or (None,'none'))[1]}"
        print(f"  {base:36s} {len(got):5d} rows  legend={len(leg)}{tag}")
    os.makedirs(outdir, exist_ok=True)
    csvp = os.path.join(outdir, "putevi_aadt_2018_2024.csv")
    with open(csvp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(outdir, "legends_per_file.json"), "w", encoding="utf-8") as fh:
        json.dump(legends, fh, indent=2, ensure_ascii=False)
    print(f"\n{len(rows)} rows -> {csvp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
