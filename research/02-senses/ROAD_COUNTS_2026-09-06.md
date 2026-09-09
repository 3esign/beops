# Road counts, and the share of them that is a measurement

**Source** S57 · JP "Putevi Srbije", annual AADT (PGDS) per road section
**Permission** documented at `research/08-provenance/` (S57), captured 2026-09-06
**Data** `research/evidence/putevi-aadt/20260906T002726Z/` (30 workbooks, raw)
**Derived** `research/observations/putevi-aadt/putevi_aadt_2018_2024.csv` (7 448 rows)
**Code** `research/collect_putevi_aadt.py`, `research/putevi_parse.py`

---

## What this source is

Serbia's road authority publishes, once a year, for each of the four
state-road categories (IA motorways, IB, IIA, IIB), a table of Average Annual
Daily Traffic per road section: passenger cars, buses, and five goods classes,
with the section's length in kilometres. Files exist for **2018 to 2024**,
in `.xls` and `.pdf`, with English editions for 2019, 2020, 2021 and 2023.
Eighty-six files were probed and found present; forty-four `.xls` files were
retrieved.

No account. No robots.txt (HTTP 404 — under RFC 9309, no restrictions
stated). No opt-out signal on any probed URL. See `08-provenance/EDGE_CASES.md`
E-003 for why the absence of a stated reuse licence is not a grant, and what we
therefore do and do not do with these figures.

## Why it matters more than a traffic table

**The publisher states, row by row, how the number was obtained.** Every file
carries a legend defining its own symbols. From the 2023 IA English edition:

```
ATC 1055  - Automatic Traffic Counter
PTR 1055  - Permanent Traffic Recorder
PTR       - Portable Traffic Recorder
TS  30    - Section with a Toll Station
TS        - Section with Tolling
INT       - Data Interpolation
```

and in the Serbian editions:

```
АБС 1055  - аутоматски бројач саобраћаја са класификацијом (10+1 категорија)
ПАБ       - повремено аутоматско бројање саобраћаја
НП        - деоница у затвореном систему наплате путарине
НП 30     - деоница са рампом за наплату путарине
ИНТ       - интерполација података
*         - подаци преузети са бројача на суседној деоници
```

Note what `TS` / `НП` actually is: **tolling, not counting**. A toll figure is
a census of vehicles that paid, produced by a different instrument from a
counter, and it is kept as its own mechanism rather than folded into
"measured".

**And absence has three named kinds.** Where there is no number, the publisher
writes which kind of nothing it is:

| the publisher's words | rows | what it means |
|---|---:|---|
| `нема података - градска деоница` / `no data - section passing through populated area` | 1 026 | urban section, not counted |
| `нема података - прекид бројања` / `no data - counting discontinuation` | 541 | the counting stopped |
| `неизграђена деоница у 2019. год.` / `undeveloped section in 2019` | 136 | the road did not yet exist |

A road that did not exist is not a road with no traffic. This distinction —
the whole premise of BEOPS's five-state grammar — is already present in a
Serbian public enterprise's open spreadsheets, seven years deep, and is
discarded by every reader who takes only the Total column.

## The symbols are not stable, so the parser reads each file's own legend

The asterisk means **"data taken from the counter on the neighbouring
section"** in 2018 IA, 2019 IB, 2021 IIA and 2022 IIA — and **"unbuilt
interchange"** in 2019 IA. One glyph, two meanings, depending on which
publication you are holding.

`research/putevi_parse.py` therefore extracts the legend from each workbook and
applies it **only to that workbook**. There is deliberately no global
dictionary. Two consequences worth stating:

- **2024 IIA and 2024 IIB publish no legend at all.** Rather than mark 411 rows
  unknown, or silently assume the usual meanings, the parser borrows the legend
  from another file of the same year and writes the donor's filename into a
  `legend_source` column on every affected row. A borrow that is recorded per
  row is not a guess.
- **`ПАБ` is used in 174 rows across four publications that never define it.**
  Its definition appears only in the 2019 IA Serbian edition. Those rows stay
  `unknown`. We do not import a definition across publications without saying
  so, and here there was nowhere to say it.

One further detail, small and instructive: the 2019 IA Serbian legend spells
`пoвремено` with a **Latin `o` (U+006F)** inside a Cyrillic word. Matching that
did not fold confusable characters dropped all 177 `ПАБ` rows into `unknown` on
the first pass. The fix folds Latin confusables to Cyrillic **and** tests the
unfolded form, because folding an English gloss destroys it.

## What the labels say when you count them

De-duplicating the Serbian and English editions of the same year, category and
section leaves **6 940 section-years** across Serbia, 2018–2024.

| state | rows | share |
|---|---:|---:|
| **observed** — a counter or a toll system | 2 544 | **36.7 %** |
| **estimated** — interpolated | 2 500 | **36.0 %** |
| **unavailable** — with a stated reason | 1 522 | 21.9 % |
| transferred — taken from a neighbouring or overlapping section | 197 | 2.8 % |
| unknown — symbol used but not defined in that file | 177 | 2.6 % |

Almost exactly **one interpolated figure for every measured one**.

### The share that is measured is falling

| year | observed | estimated | unavailable |
|---|---:|---:|---:|
| 2018 | 35.4 % | 33.3 % | 23.0 % |
| 2019 | **46.3 %** | 28.9 % | 21.3 % |
| 2020 | 38.7 % | 36.4 % | 21.2 % |
| 2021 | 38.3 % | 36.3 % | 21.8 % |
| 2022 | 37.9 % | 27.4 % | 21.7 % |
| 2023 | 33.7 % | 40.7 % | 22.5 % |
| 2024 | **27.0 %** | **48.7 %** | 22.0 % |

In five years the measured share fell from 46 % to 27 %, and interpolation rose
from 29 % to 49 %. Nearly half the state road network's 2024 figures were
produced by interpolation rather than by an instrument.

*(2018 and 2022 carry elevated `unknown` — 6.1 % and 11.3 % — from the
undefined `ПАБ` symbol. Excluding those rows does not change the direction of
the trend; it is visible in `observed` and `estimated` alike.)*

This is not our inference. It is the publisher's own per-row label, counted.
It is invisible in the published tables because a measurement and an
interpolation are printed in the same typeface in the same column.

### Belgrade

420 section-years fall in the Belgrade area (matched on settlement and
interchange names in the section text — a text match, and therefore a floor,
not an exact boundary).

| state | rows | share |
|---|---:|---:|
| estimated | 192 | **45.7 %** |
| observed | 154 | 36.7 % |
| unavailable | 62 | 14.8 % |
| unknown | 8 | 1.9 % |
| transferred | 4 | 1.0 % |

The four largest 2024 figures on the Belgrade ring:

```
55 545   Bubanj Potok – Tranšped     estimated   interpolation
52 486   Tranšped – Vrčin            estimated   interpolation
49 597   Vrčin – Mali Požarevac      observed    toll system
48 855   Dobanovci – Belgrade        unknown     (symbol undefined in file)
```

**The largest traffic figure Serbia publishes for the Belgrade ring was not
measured.** Under the project's grammar it is drawn as an estimate, and the
two sections that were measured — Orlovača–Avala at 35 922 and Avala–Bubanj
Potok at 34 408, both permanent counters — are drawn as measurements.

## What this gives BEOPS

1. **A test case with ground truth about provenance.** Most sources force us to
   infer how a number was made. This one says. Any rendering of the five-state
   grammar can be checked against a publisher's own labels.
2. **A seven-year series with structured absence**, which is what the
   `unavailable` state was invented for and has until now been demonstrated
   only on our own parking pilot.
3. **A measurable claim about the city's instruments**, in the project's own
   terms: Belgrade's road network is 37 % observed and 46 % estimated, and the
   observed share is falling nationally.

## What it does not give

- **No geometry.** Sections are identified by node-code pairs (`01001/01002`,
  `A1001/A1002`) and free text, not coordinates. Placing them on a map requires
  the road-section reference network, which is inside `gisportal.rs` and
  requires a token (S135, closed). Until then this source is a table with
  names, not a layer.
- **No sub-annual resolution.** The publisher states it holds hourly data
  across all 8 760 hours; what is published is the annual average.
- **Preliminary status.** Several editions carry
  `ПОДАЦИ СУ ПРЕЛИМИНАРНИ И ПОДЛОЖНИ СУ ПРОМЕНАМА НАКОН ДЕТАЉНЕ ОБРАДЕ` —
  the figures may change after detailed processing. Any published figure must
  carry the edition it came from.

## Note on the publisher's own consistency

`2024_DP-IIB-PGDS-2024.xls` has its worksheet named `DP IIA 2022`. Nothing
depends on the sheet name here, but it is recorded because a source's small
carelessness is information about how much weight its other fields can carry.

## Collection manners

Forty-four files, one request at a time, 1.5 s apart, honest user-agent, once.
This is **not** a recurring collector and must not become one without
revisiting `08-provenance/EDGE_CASES.md` E-004 on repeated extraction.
