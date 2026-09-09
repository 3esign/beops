# BEOPS — UI concepts and composition

Version 1, 2026-09-05 evening. Written under `skills/svemir-lepota` (the law and the gate) and
`skills/svemir-design` (the method). The seven gate questions are answered at the end; without
them this document is not delivered.

---

## 0. The sentence

Article 2 of the law says every artefact exists to say one sentence, and if the sentence cannot be
written the thing is not built. Here it is:

> **This is what Belgrade told us, when it told us, and where it went quiet.**

Three clauses, and the third is the one that makes this different from every city dashboard in the
precedent survey. Most of them are built to show the first clause. A few honest ones show the
second. Almost none of them are *composed around* the third.

Everything below follows from that sentence. If an element does not serve one of its three clauses,
it comes off the screen.

---

## 1. What this document is, and what it is not

It is a design direction: the state grammar, three genuinely different compositions, the chosen one
with its contradiction named, the proportional/colour/type/motion systems, and one cheap test that
can falsify the whole thing before anything expensive is built.

It is **not** permission to start building an application. `UPUTSTVO.md` still stands: the existing
`server.js`, `src/` and `public/` are inactive unvalidated sketches, and the research product may
end with no interface at all. What has changed is that the mechanism is now real — two genuine
observations exist on disk with hashes and receipts — and Article 7's corollary applies: *UI made
before the mechanism is real is one of the named ugly patterns; UI designed after it is real is the
work.*

Everything here is drawn from two verified research passes done today
(`research/BIBLIOGRAPHY_2026-09-05.md` and the encoding/precedent briefs summarised in §3–§4) plus
BEOPS's own two real samples. Where a claim rests on nothing but convention, it says so.

---

## 2. The design problem, stated exactly

BEOPS must make five things impossible to confuse:

| | State | What it is | The lie if we get it wrong |
|---|---|---|---|
| 1 | **Observed** | A source actually reported this value | — |
| 2 | **Forecast** | A statement about the future | A prediction read as a reading |
| 3 | **Estimated** | A model produced it from other values | A derivation read as a measurement |
| 4 | **Unavailable** | Nothing came | **Absence read as zero** |
| 5 | **Untimed** | The value is exact; its *age* is not | A stale number read as current |

State 5 is not an edge case, it is our daily condition: every parking sample carries
`observed_at: null` while `attempted_at` and `completed_at` are exact to the millisecond. We know
the number precisely and its age not at all. The value is sharp; the time is a smear.

Two further facts sharpen the problem, and both were established today:

**There is no published research on how to draw state 5.** OGC SensorThings gives the data model —
`phenomenonTime` vs `resultTime` — and GTFS-Realtime arrived at the same split independently from
transit engineering. But no one has published a comprehension study of how to *render* a value whose
time is unknown. Whatever BEOPS ships here is an original design, not an implementation of somebody
else's tested pattern. That is a contribution worth naming in the paper, and a risk worth stating in
the interface.

**The dot-map's free lunch does not reach us.** The best precedent for absence — the EEA Air Quality
Index viewer — greys out a dead station *at its own pixel*, and can afford two different greys for
two different failure modes because each failure has a location. BEOPS refused micro-level detail on
purpose: we work at whole city → larger units → broad zones. A zone of forty sensors with three dead
ones **has no pixel to grey**. The pattern that works everywhere else in the survey dies exactly at
the resolution we chose. We have to invent the zone-level equivalent ourselves.

---

## 3. What the evidence actually supports

Ten rules, each traceable. Where the evidence is thin the rule says "convention".

1. **Magnitude by position or length; state by shape and pattern; colour last.** Cleveland & McGill's
   ranked perceptual tasks put position along a common scale first and colour saturation last, and
   that ranking has held since 1984. Colour carries the state as a *redundant* channel, never as the
   only one.
2. **"Unavailable" gets a positive glyph, not an absence.** Song & Szafir measured it: zero-filling
   dropped reading accuracy to 72.9% against 80.7% for interpolation, and in bar charts made missing
   values visually identical to real zeros — but *removing* the mark entirely also lowered confidence
   and accuracy. So neither fill nor erase: mark the gap with something that is unmistakably a mark
   about nothing.
3. **Never draw a forecast as a filled shape with a crisp outer edge.** The hurricane-cone work is
   the controlled proof: with a bounded cone, 95% of viewers agreed the storm "gets larger over
   time" — reading widening *positional uncertainty* as growing physical size. With an ensemble of
   sampled paths and no salient boundary, the same false statement fell to 81% (χ²=10.66, p<.001).
   A hard edge reads as a physical limit.
4. **For a decision, show discrete outcomes, not a summary interval.** Quantile dotplots produced
   decisions worth 97% of optimal, five points above a no-uncertainty control — and, importantly,
   the *text* framing ("85% chance") failed to help at all. If BEOPS ever answers "will there be a
   space", it answers in dots, not in a sentence with a percentage in it.
5. **Replace whiskers with density.** Error bars carry a measured directional bias — values inside
   the bar are judged more likely than statistically identical values just outside it — and even
   trained researchers misread them (N=473). Gradient and violin encodings scored 88.5% and 89.2%
   against 83.2% for bar-plus-whisker.
6. **Uncertainty stated *specifically* does not cost trust; stated *vaguely*, it does.** Across
   5,780 participants, giving a numeric range lowered confidence in the number and produced **no
   significant change in trust of the source** — while verbal hedging cost more. The opposite-signed
   study agrees on the mechanism: it was *low-quality and ambiguous* cues that damaged trust
   (d=0.22–0.36). So: "value is 41–70 minutes old, source X" is safe; "data quality: unclear" is not.
   This single finding kills the entire idea of a vague confidence badge.
7. **Two timestamps, never collapsed into one.** SensorThings and GTFS-Realtime both keep phenomenon
   time separate from generation time and expect one of them to be null. Our `observed_at: null` is
   a named, modelled case, and the interface must show both fields, not substitute one for the other.
8. **Show the absolute instant, not only a relative phrase.** Aviation (METAR's `DDHHMMZ`), air
   quality (AirNow's hour-ending convention plus a stated publication lag) and seismology (USGS's
   separate origin time, update time, and an `automatic`/`reviewed` flag) converged on this
   independently in three unrelated regulated domains. None of them published a usability study for
   it — this is unanimous convention, not evidence, and it should be labelled as such.
9. **A value may be shown before it is reviewed, if the review status is visible and the number does
   not change when it upgrades.** USGS's `automatic` → `reviewed` flag is the reusable pattern for
   an estimate that is later confirmed by a real observation.
10. **Do not strip the state glyphs to bare minimalism on Tufte's authority.** The direct test of the
    data-ink rule (N=87) found users preferred the "chartjunk" version, and embellished charts were
    recalled significantly better after two to three weeks with no loss of immediate comprehension.
    The state alphabet is the one place in this design where a distinctive, slightly illustrative
    mark is the better-evidenced choice.

Two rules that people expect and that the evidence does **not** support: there is no study behind
any specific dashboard density limit, and there is no citable source for "grey hatching means no
data" in cartography — the one authoritative document actually opened recommends transparency
instead. Both are our decisions to make and to label as decisions.

---

## 4. What the precedent gives, and where it runs out

Seven patterns recur across the interfaces that work. Five of them transfer to us intact.

- **The independently addressable card.** Cloudflare Radar's country page is ~15 repetitions of one
  three-part unit — heading with its own permalink, one chart, one "learn more" — and the same shape
  scales from the world view down to Serbia without changing. RIPEstat arrived at the same widget
  discipline from a completely different engineering culture. *Transfers.*
- **A permanent source line fixed to the object.** Our World in Data docks the citation and the
  "download the data" action under the chart as chrome, not as a menu item. *Transfers, and matters
  doubly since researchers are a named audience.*
- **Multi-tier provenance in line style.** Flightradar24 encodes *source*, not value: solid coloured
  for live ADS-B, black dashed for dead-reckoned estimate (time-boxed at 60 minutes), orange for a
  slower delayed feed — and the aircraft icon never disappears, only its trail changes character.
  This is our four-state problem, already shipping at global scale. *Transfers almost one-to-one.*
- **Reported and instrumental data kept structurally apart.** USGS keeps "Did You Feel It" as its own
  product rather than folding a felt-count into the magnitude. The counter-example is the transit
  "ghost bus": blend GPS-confirmed and merely-scheduled vehicles under one icon and riders wait for
  buses that were never coming. *Transfers, and is the most important single discipline for us*,
  because our input mix is exactly citizen sensors alongside official registries.
- **Smoothing said out loud.** The FT's seven-day average, explained by its author in almost our own
  words — the daily data "implies a false level of precision". *Transfers.*
- **"No data" as a named rung on the same legend.** The EEA viewer is the single best precedent
  found: Good / Fair / Moderate / Poor / Very poor / Extremely poor / **No data**, in the same
  family, plus two distinct greys for two distinct failures — reported nothing at all, versus
  reported too little to compute the index. It distinguishes *why* it is missing, not only *that*.
  *Transfers as a principle, dies as a technique* — see the next point.
- **Point symbols make staleness free.** *Does not transfer.* This is the pattern we must replace.

And three anti-patterns, named so they stay named: the vanity tile wall of decontextualised gauges
with no baseline (CityDashboard, honest enough to call itself alpha, still a wall of ungrounded
numbers fourteen years on); the photorealistic 3D twin, whose entire visual register is *uniform
completeness* and which therefore cannot show you which part of itself is three years stale; and
the single composite city score, where change the theory of "smart" and the whole ranking reorders.
All three are already forbidden by our own rules. Now they are forbidden with citations.

---

## 5. The material grammar: five states, drawn

This is the alphabet. Everything in every concept below is written in it.

### 5.1 The rule that generates the marks

Form comes from rules (creator DNA), and structure must be visible (Article 3). So the marks are not
chosen for looks; they are generated by one question with two axes:

- **Did a source say it?** (observed) versus **did we work it out?** (estimated, forecast)
- **Do we know when?** (timed) versus **do we not?** (untimed, unavailable)

A stroke says *where the value came from*. A ground says *how well we know its time*. Nothing else
changes. That is the whole grammar, and it is why the five states cannot be confused: they differ in
two independent physical properties, before colour is applied at all.

| State | Stroke | Ground | Colour role | Redundant text |
|---|---|---|---|---|
| **Observed** | solid, full weight | clean | Signal | `obs` |
| **Untimed** | solid, full weight | **age band** — a horizontal smear under the mark, as wide as the uncertainty in its age | Signal, at reduced chroma | `obs · age ≤ 61 min` |
| **Estimated** | dashed | clean | Structure, not Signal | `est` |
| **Forecast** | dotted, with a **dot column** (quantile dotplot) instead of a band | clean | Structure | `fcst` |
| **Unavailable** | **no stroke, but a mark**: a short vertical tick on the baseline with a hollow centre | hatched cell | State-neutral grey | `no data` + reason |

Four things to notice, each tied to a rule above:

- The number's **magnitude is always position or length** (rule 1). Colour never carries it.
- **Unavailable is a positive mark** (rule 2) — the eye lands on something, and that something is
  visibly not a value. The hollow tick is deliberately unlike every other mark in the set: it is the
  only one that is empty at the centre.
- The **forecast never has an outer edge** (rule 3). It is a column of discrete dots, so there is no
  boundary to mistake for a limit, and it is the encoding with the only measured decision gain
  (rule 4).
- **Untimed is where the invention is.** The value keeps its full solid stroke, because the value is
  exact and pretending otherwise would be its own lie. What becomes uncertain is drawn where the
  uncertainty actually lives: under the mark, along the *time* axis, as a band whose width is the
  real interval between the last moment the source could have measured and the moment we received
  it. Today that band is `[unknown, 15:30:03]` — unbounded on the left, so it is drawn as a band
  that **fades off to the left with no left edge**, the same no-boundary logic the hurricane work
  proved (rule 3), applied to time instead of space.

### 5.2 Absence at zone level — the quorum bar

The problem §2 named: a zone has no pixel to grey. The answer is to stop trying to draw the missing
thing and start drawing **the quorum** — how much of what should have spoken did speak.

Every zone-level figure carries, directly beneath it, a thin bar divided into as many cells as there
are contributing sources. Cells are filled for sources that reported in this window, hollow for
sources that did not, and hatched for sources that reported too little to count. It is small, it is
the same width as the number it sits under, and it is never rounded to a percentage.

```
Zeleni venac            89
▮▮▮▮▮▯▯                 7 sources · 5 reported · 2 silent
```

Three reasons this is the right answer rather than a compromise:

1. It is **counting, not estimating** — the most honest operation available, and the one thing about
   a silent source we know for certain.
2. It follows the EEA's real lesson, which was never "grey" — it was *distinguish why*. Filled,
   hollow and hatched are three states of a source, exactly the distinction the EEA made with two
   greys, moved from geography to arithmetic.
3. It is **repetition that becomes identity through variation** (creator DNA): the same seven-cell
   bar under every figure across the whole system, and you learn to read a zone's health from its
   silhouette before you read a single word.

The quorum bar is the piece of this design that does not exist anywhere in the precedent survey. It
is also the piece most likely to be wrong, which is why §11's test is built to break it first.

### 5.3 What the alphabet forbids

Because these marks differ physically, several tempting shortcuts become unnecessary and are
therefore banned: no confidence percentage badge (rule 6 — a vague quality cue is the exact pattern
that measurably costs trust); no traffic-light dot standing alone (colour is redundant, never sole);
no opacity used to mean uncertainty (opacity is reserved for interaction states, and a faded real
value is indistinguishable from a screen problem); no line connected across a gap, ever (rule 2).

---

## 6. Three compositions

The method requires genuinely different propositions — varying relation, scale, material, time or
agency, not colours. These three differ in *what the primary object is*: time, the instrument, or
the city as a drawing.

### Concept A — **TRAKA** (the ribbon). The primary object is time.

The whole screen is one horizontal strip. The x-axis is the last 24 hours; each sense is a lane
stacked vertically — parking, transit regime, air, water, network, registry. A lane is a run of
marks in the alphabet: solid where observed, hollow ticks where silent, a dot column at the right
edge where a forecast exists. Zones are not on a map; they are **rows inside a lane**, collapsed by
default into the lane's quorum bar and expanded on demand.

The signature gesture is a **single vertical hairline** that follows the pointer and reads every
lane at that instant into one column of numbers on the right. Move it and the whole city's answer at
that moment assembles. Stop moving and it rests on *now*.

- **Relation it embodies:** the city is a set of simultaneous signals, and the interesting question
  is what was true *at the same moment*.
- **Why it is honest:** time is the axis, so a gap is a hole you cannot look past, and an untimed
  value's age band lies along the same axis as everything else — it is measured in the same units as
  the picture.
- **Its cost:** space disappears. A person who wants to know about their own neighbourhood has to
  learn the lane/row structure first.
- **Tension it sits in:** monochrome evidence / chromatic intervention.

### Concept B — **KARTON** (the register). The primary object is the instrument.

A vertical stack of identical cards, one per sense, in a fixed order that never changes. Each card
is the same three-part unit — a heading with its own permalink, one figure with its alphabet mark
and quorum bar, and a fixed footer line naming the source, the retrieval time, and a download link.
Below the fold, the same card repeated per zone. Nothing moves. It is the Cloudflare Radar / OWID
discipline applied without ornament.

The signature gesture is that **the card does not change shape when the data is bad**. A card whose
source is silent is the same size, in the same place, with the same footer — only the mark inside it
is a hollow tick and the quorum bar is empty. Absence occupies exactly as much space as presence.
That is the whole argument of the project, expressed as a layout constraint.

- **Relation:** the city is a set of instruments, and an instrument's health is part of its reading.
- **Why it is honest:** it is nearly impossible to hide a failure in a layout where failure has the
  same footprint as success.
- **Its cost:** it is the least beautiful of the three at first glance, and it has no single moment
  that makes someone want to look. It is a reference work, not an experience.
- **Tension:** useful instrument / exploratory world, resolved hard toward the instrument.

### Concept C — **PRESEK** (the section). The primary object is the city as a drawing.

An architectural section — a *drawing*, explicitly and visibly not a photograph, not a 3D model.
One horizontal ground line across the screen. Senses sit at their true physical altitude relative to
it: satellite columns and aircraft above, network and radio in the upper band, air quality and noise
at head height, traffic and parking at the ground line, water and district heating and seismic below
it, and beneath everything a separate hatched band for the **documentary layer** — procurement,
registry, cadastre — which has no altitude at all and is drawn as the bedrock it behaves like.

The signature gesture is that **the ground line is drawn by hand-weight, not hairline** — one thick
architect's line across the composition, and every sense hangs off it or sits under it. Values are
drawn as marks on their own altitude band; a silent sense leaves its band visibly empty, with the
hatched cell running through where readings should be.

- **Relation:** the city is a physical section, and every sense is an instrument at a height. This is
  the only one of the three that says something about *what a city is* rather than about data.
- **Why it is honest:** a section is by definition a construction, so nobody mistakes it for reality
  — which is precisely the disease of the photorealistic twin (§4). It claims exactly what it is.
- **Its cost:** it is the most likely to become decoration, and the altitude metaphor strains for
  the documentary layer (which is why that layer is drawn as bedrock rather than forced into a
  height).
- **Tension:** precise / gestural, and orthogonal grid / folded geometry.

### Cross-cutting mode — **ODSUSTVO** (the ignorance view)

Not a fourth concept but a switch available in all three: invert the figure. Draw only what we do
not know — every silent source, every unbounded age band, every zone below quorum, at full weight,
with the known values dropped to structure grey. One keystroke.

Nothing in the precedent survey does this. It is the most direct possible expression of the third
clause of the sentence, it is trivially cheap to build once the alphabet exists, and it is the
single best answer to the accusation every observatory eventually faces — *what aren't you showing
me?* Answer: here, press this.

---

## 7. The choice, and its contradiction

**Take B as the skeleton, A as the primary view, C as the front door. Build A first.**

The reasoning, plainly:

- **B is the skeleton** because the card discipline is what keeps the system honest and is the only
  one of the three proven to scale from whole city to zone without changing shape. Every value in
  A and C resolves to a B card when you ask it to.
- **A is the primary view** because our founding problem is a *time* problem, not a space problem.
  We do not have a map problem — we deliberately gave up map resolution. We have `observed_at: null`.
  A composition whose main axis is time puts our actual difficulty in the position of honour, where
  Article 3 says the mechanism belongs.
- **C is the front door** — one screen, the section, for the person arriving with no context, that
  answers "what is this" in one image and hands off to A. It earns its place by being the only one
  that is *about Belgrade* rather than about data, and it is the argument against the 3D twin made
  visually rather than in prose.

**The contradiction, named as the method requires:** this design asks a person to read *absence* as
information, and absence is the one thing human attention is built to skip. Every honest choice here
— the hollow tick, the empty quorum cell, the unbounded age band — makes the interface harder to
enjoy at a glance than any of the dashboards it is meant to replace. We are deliberately building
something that is less immediately satisfying and more true. If it fails, it will fail there, and
the ignorance view is the pressure valve: instead of pretending absence is pleasant, we give it its
own screen and make it the subject.

---

## 8. The systems

### Proportional system

Base unit `u = 4px`, tied to a 16px body size with a 1.5 line height (24px = 6u). Everything is a
multiple: card padding 6u, gap between cards 4u, quorum-bar height 1u, lane height in TRAKA 10u,
the ground line in PRESEK 2u. One exception is allowed and only one: the vertical hairline in TRAKA
is 1 physical pixel regardless of density, because it is a measuring instrument and must not blur.

Grid: 12 columns, but the composition uses only three groupings — 12 (a lane, the full ribbon), 8+4
(stage plus reading column), and 4×3 (cards). Three groupings, used consistently, read as a system;
seven read as accident.

### Colour by role

Family: **paper / ink / intervention**, from the creator's own grammar. A mostly neutral field, a
small structural range, a scarce high-chroma signal — because our signal *must* stay scarce for the
alphabet to work at all.

| Role | Value | Used for |
|---|---|---|
| **Field** | warm off-white `#FBFAF7` (light) / ink `#111311` (dark) | the ground everything sits on |
| **Structure** | near-black `#111311` at 100/60/30% | type, grid, boundaries, estimated and forecast strokes |
| **Signal** | vivid orange-red `#D93A16` | observed values only — nothing else, ever |
| **Signal (untimed)** | the same hue at ~45% chroma | untimed values and their age bands |
| **State** | one cool grey `#8A8F8A` | unavailable marks, hatching, empty quorum cells |
| **Material** | comes from content | source-specific chart series, and nothing else |

Six values. The discipline is that **only observation is allowed to be chromatic**. An estimate is
structure-coloured, a forecast is structure-coloured, absence is state-grey. So the amount of colour
on screen *is* the amount of real measurement in the picture — the palette itself becomes an honest
readout, and a bad day looks visibly grey without anyone writing "data quality: poor".

Contrast checked at 4.5:1 for all text and all state marks against both fields (Article 7). Dark
theme is a decision about light, not a personality: same roles, field and structure swapped, signal
lifted in lightness to hold its ratio.

### Type roles

Two families, no more. A humanist sans for reading (interface, prose, labels) and a **tabular
monospace for every number, timestamp, unit, hash and source id** — because these are measurements,
and the monospace is doing structural work, not signalling technicality. Numbers align in columns
across every card by construction, which makes a wrong magnitude visible as a ragged column before
anyone reads it. Display type: none. There is no headline in this product.

Labels describe consequences: not "N/A" but `no data — source silent since 12:30`; not
"low confidence" but `age unknown, ≤ 61 min since retrieval`.

### Graphic grammar

**Line / axis / trace**, with one intrusion of hatching. Everything is drawn with strokes on a
baseline: the ribbon is traces, the quorum bar is cells, the section is a line drawing. Hatching
appears in exactly one situation — insufficient data to compute — and nowhere else, so that texture
means one thing across the whole system. No fills, no gradients, no shadows, no glass, no glow. The
naked-screen test (gate question 6) is not something this design has to pass afterwards; it is
already naked.

### Motion, each with a job

- **Respond** (120ms): the hairline follows the pointer; the reading column updates. Immediate.
- **Reveal** (240ms): a lane expands into its zone rows. Explains construction.
- **Orient** (300ms): moving between C → A → a B card preserves the position of the thing you were
  looking at.
- **Choreograph** — none. There is no narrative sequence in this product.
- **Embody** — one, and only one: when a new sample lands, its mark **draws itself in** over 400ms,
  left to right, and the quorum cell fills. That is the only animation that is about the world
  rather than the interface, and it is the answer to "what changed?" in the most literal form.

`prefers-reduced-motion` replaces all four with immediate cuts plus a 1u position shift, so state
changes stay legible without movement.

### Responsive transformation

Not a scaled artboard — re-authored per range.

- **Wide:** TRAKA full width, reading column pinned right, C reachable as a first screen.
- **Medium:** ribbon keeps 12h instead of 24h; reading column becomes a drawer under the hairline.
- **Narrow:** the ribbon rotates. Time runs **vertically**, senses become the horizontal axis, and
  the hairline becomes a horizontal band you drag with a thumb. This is the one place the design
  changes its geometry rather than its density, and it is the right call: a 24-hour horizontal
  ribbon on a phone is a scroll, and a scroll through time is exactly how a phone already reads.

---

## 9. Deliberately excluded

From the registry of ugliness and from §4's anti-examples, written down so nobody has to relitigate:

- No 3D city model, no map at micro level, no photorealism of any kind.
- No composite "city score", no index, no single number standing for Belgrade.
- No gauges, no speedometers, no tile wall of decontextualised figures.
- No neon, glass, bloom, particles, or gradient text.
- No traffic-light dot as the sole carrier of state.
- No confidence percentage, no vague quality badge — measurably trust-destroying (rule 6).
- No line connected across a gap; no zero-fill; no interpolation presented as reading.
- No skeleton loaders that imply a value is coming when the source may be dead. A pending request
  shows the alphabet's own pending mark, which is honest about not knowing whether it will arrive.
- No dark theme as identity.

---

## 10. What this needs from the data layer

The interface cannot be honest if the data is not shaped for it. Three requirements, and all three
come straight from the bibliography:

1. **Two timestamps per value, never one nullable field** (`phenomenonTime`, `resultTime` — rule 7).
   Today's samples already carry `attempted_at`, `completed_at` and `observed_at`; formalise them
   under the standard's names so the contract is external, not ours.
2. **A quorum record per aggregate**: how many sources were expected, how many reported, how many
   reported insufficiently. Without this the quorum bar cannot be drawn, and without the quorum bar
   there is no zone-level absence.
3. **A review flag per value** (`automatic` / `reviewed`, USGS's pattern — rule 9), so an estimate
   can be shown immediately and upgraded later *without the number changing*.

None of these are interface work. All three are `SOURCE_REGISTRY.json` and the recorder.

---

## 11. The cheapest test that could break this

Prefer the cheapest medium that tests the idea. So: **one self-contained HTML page, no build, no
dependencies, no server, reading the two real samples already on disk.** It draws the alphabet at
real scale, the two observations at 15:30 and 16:30 with their real values and their real unbounded
age bands, three fabricated-as-such absences for the three genuinely missed slots, and a quorum bar
over the 27 locations.

It is a study, not a product: it goes in `research/`, not in `public/`, and `UPUTSTVO.md`'s rule
that the UI is paused survives intact.

What it is built to break, in order:

1. **Is the quorum bar readable at 1u height with seven cells?** If not, the zone-absence answer
   fails and §5.2 needs rethinking before anything else is drawn.
2. **Does an unbounded age band read as "we don't know when", or as "an error"?** This is the
   invented state. If people read it as a rendering bug, the invention has failed and we say so.
3. **Does the hollow tick read as absence rather than as a very small value?** Song & Szafir's
   failure mode, checked on our own marks.
4. **Does the screen with three absences look worse than the screen with none?** It must. If a bad
   day looks the same as a good one, the palette discipline in §8 is not working.

If tests 1 and 2 fail, this document is wrong in its most original part, and that finding is worth
more than a page that looks nice.

---

## 12. Honest verdict, and the gate

**Done:** the sentence; five states resolved into a two-axis physical grammar; a zone-level absence
mechanism (the quorum bar) invented where the precedent runs out; three genuinely different
compositions with a chosen direction and its contradiction named; proportional, colour, type,
graphic and motion systems specified to implementable values; the exclusions written down; three
data-layer requirements traced to standards; and one falsifiable test.

**Not done, and not claimed:** nothing has been built. No user has seen any of this. The quorum bar
and the age band are inventions with no comprehension study behind them — mine or anyone's — and
§11 is a legibility check by one designer, not a study. Concept C is described but not drawn. The
colour values are specified but only contrast-reasoned, not measured on a real screen. The claim
that state 5 has no published visualization research is as strong as one afternoon's verified search
can make it, which is strong enough to state and not strong enough to put in a paper without a
second pass.

### The seven questions

1. **Sentence.** *This is what Belgrade told us, when it told us, and where it went quiet.*
2. **Lie.** None that I can find. Every mark is wired: solid stroke ⇢ a source reported;
   dashed ⇢ we derived; dotted column ⇢ future; hollow tick ⇢ nothing came; band width ⇢ the real
   interval between last-possible-measurement and retrieval. Colour presence ⇢ observation presence.
   The one thing to watch is the age band's left edge: it must fade, never terminate, because a
   terminated edge would claim a lower bound we do not have.
3. **Subtraction.** Removed: the map as a primary object; the overview/composite figure; the
   confidence badge; opacity-as-uncertainty; skeleton loaders; the second accent colour; display
   type; all fills, gradients and shadows; and a fourth concept (an absence-first *layout*), folded
   down into a mode because it was the same idea wearing a bigger hat.
4. **Hierarchy.** First the ribbon's traces — where colour is, measurement is. Second the hairline
   and its reading column — the moment you chose. Third the quorum bars — how much of the city was
   actually speaking. That is the order of importance, and it matches the sentence's three clauses
   in order.
5. **Motion.** Every animation was checked against "what changed?". One was cut in writing: a
   pulsing highlight on fresh data, which answers "look at me", not "what changed" — the draw-in of
   the mark itself already answers it truthfully.
6. **Naked screen.** There is nothing to switch off. No bloom, blur, particles, gradients or
   shadows were ever in the design; the grammar is strokes, hatching and a baseline. This one passes
   by construction, which is the only way it should ever pass.
7. **Who can.** Keyboard: the hairline is arrow-key steppable by slot, cards are a normal document
   order, the ignorance view is one key. Contrast 4.5:1 in both themes, and no state depends on
   colour alone — every mark differs in stroke and ground before hue. Reduced motion: all four
   motions become cuts. No network: the study page is a single file with no CDN. Phone: the ribbon
   rotates rather than shrinking. **What does not work yet:** screen-reader semantics for the ribbon
   are unspecified — a time-series of five states with age bands is a genuinely hard accessibility
   problem, and the honest answer is that it needs a per-lane data table as the accessible
   equivalent, which is not yet designed. That is the one open item in this gate, and it is named
   rather than passed over.
