# OBS-001 — interim analysis at five of thirteen slots

Written 2026-09-05, 20:05 local (18:05 UTC), with the observation still running. This is an interim
reading, not the report the protocol requires at the end. Five slots are captured, three are
permanently missing, five remain. Nothing here is a conclusion about the race.

---

## 1. What is actually on disk

| Slot (UTC) | Local | HTTP | Bytes | ms | sha256 (12) | Locations |
|---|---|---|---|---|---|---|
| 13:30 | 15:30 | 200 | 47 313 | 754 | `e6e8d451b1dc` | 27 |
| 14:30 | 16:30 | 200 | 47 314 | 219 | `4fd153cd0c1c` | 27 |
| 15:30 | 17:30 | 200 | 47 316 | 275 | `5fd0b0efa028` | 27 |
| 16:30 | 18:30 | 200 | 47 323 | 226 | `328c6e96dd7f` | 27 |
| 17:30 | 19:30 | 200 | 47 322 | 251 | `76a1a2cdbcb4` | 27 |

Missing and not recoverable: 10:30, 11:30, 12:30 UTC. Pending: 18:30 → 22:30 UTC.

**Every hash differs.** The source is not serving a cached or frozen response; the page really
changes between requests. Byte count drifts by single digits as the numbers change width, which is
consistent with the same template rendering different values — no schema change occurred during the
window. First response was 754 ms cold, the rest 219–275 ms.

`observed_at` is null in all five. See §5: that is now a verified property of the source, not a gap
in our reading of it.

---

## 2. The trajectory, all 27 locations

Displayed free spaces. Sorted by the final value.

| Location | 15:30 | 16:30 | 17:30 | 18:30 | 19:30 | Δ |
|---|---:|---:|---:|---:|---:|---:|
| Ada | 440 | 443 | 430 | 484 | 568 | **+128** |
| VMA | 518 | 338 | 505 | 558 | 560 | +42 |
| Belvil | 397 | 398 | 400 | 398 | 392 | −5 |
| Masarikova | 346 | 361 | 371 | 372 | 375 | +29 |
| Pionirski park | 275 | 315 | 328 | 332 | 336 | +61 |
| Baba Višnjina | 233 | 245 | 246 | 250 | 242 | +9 |
| Međunarodni carinski terminal | 222 | 220 | 222 | 224 | 223 | +1 |
| Milan Gale Muškatirović | 60 | 73 | 102 | 146 | 164 | **+104** |
| Donji grad | 254 | 254 | 210 | 173 | 154 | **−100** |
| Blok 43 | 144 | 146 | 146 | 145 | 148 | +4 |
| Opština NBGD | 114 | 117 | 115 | 115 | 115 | +1 |
| Pinki | 93 | 95 | 102 | 105 | 101 | +8 |
| Zeleni venac | 89 | 104 | 119 | 110 | 91 | +2 |
| Slavija | 82 | 80 | 76 | 70 | 74 | −8 |
| Bežanijska kosa | 70 | 70 | 69 | 67 | 65 | −5 |
| Ljermontova | 62 | 63 | 63 | 66 | 67 | +5 |
| Čukarica | 58 | 57 | 60 | 62 | 59 | +1 |
| Cvetkova pijaca | 35 | 35 | 34 | 38 | 48 | +13 |
| Vukov spomenik | 26 | 47 | 51 | 48 | 47 | +21 |
| Dr Aleksandra Kostića | 37 | 39 | 38 | 36 | 34 | −3 |
| Viška | 16 | 29 | 38 | 35 | 34 | +18 |
| Botanička bašta | 74 | 73 | 63 | 52 | 29 | **−45** |
| Vidin kapija | 3 | 8 | 1 | 0 | 4 | +1 |
| Politika | 2 | 2 | 0 | 1 | 1 | −1 |
| Obilićev venac | 29 | 41 | 31 | 6 | 0 | **−29 → 0** |
| Kalemegdan | 0 | 0 | 1 | 0 | 0 | 0 |
| Kamenička | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **3 679** | **3 653** | **3 821** | **3 893** | **3 931** | **+252** |

---

## 3. Four findings, in order of how much they change the project

### 3.1 A single-sample excursion that fully reverts is a source artefact, not a city event

VMA: 518 → **338** → 505 → 558 → 560.

At 16:30 this was the largest single change in the sample, −180 in one hour. It was flagged then,
in writing, as not to be folded into any claim about the race, with an instruction to check whether
it repeated before drawing any conclusion. **It did not repeat, and it reverted by +167 in the very
next hour.** A car park does not lose 180 vehicles in an hour and regain 167 in the next.

Had the observation stopped at two samples — which is exactly what it looked like it would do this
morning, when the pilot had captured nothing at all — the honest-looking move would have been to
report the largest observed change. It would have been a fabrication produced entirely by good
faith and a short series.

**The rule this yields, and it belongs in the paper:** a single-sample excursion that fully reverts
in the adjacent sample is a candidate source artefact and must be excluded from any claim until it
recurs. Formally: for a series with no measurement time, an excursion is only admissible as evidence
if it persists across at least two consecutive samples, because a one-sample spike is
indistinguishable from a rendering, counting or transient-sensor fault in the publisher's own system.
This is not a statistical test; it is a minimum-persistence rule, and it is cheap.

### 3.2 The pre-registered spatial grouping did not hold — and that is the better result

The protocol, written before any samples existed, separated three groups. The first was
**Opština NBGD, Belvil and Pinki** as the New Belgrade/Zemun environment of the race, on the side
the race is actually run.

Those three are the flattest lines in the entire dataset: **Belvil −5, Opština NBGD +1, Pinki +8**,
across four hours spanning the announced start. Nothing happened where the protocol expected
something.

Everything that moved is elsewhere: Obilićev venac collapsing monotonically to zero, Donji grad −100,
Botanička bašta −45 — the central/riverside axis the protocol had classed as a second environment —
plus Ada +128 and Milan Gale Muškatirović +104, which the protocol had classed as distant
descriptive context.

Two things follow. First, **the a-priori grouping is falsified for this event**, and reporting a
falsified pre-registration is worth more than reporting a hit, because a hit found post-hoc in 27
series with 5 points each is nearly free. Second, the honest reading of the spatial pattern is that
we do not have one: we have a Saturday-evening city, and the burden is on anyone who wants to claim
otherwise.

### 3.3 The city as a whole emptied. Any race effect is local and runs against the citywide trend

Total displayed free spaces rose from 3 679 to 3 931 across the window: **+252, about +7%.** More
free spaces at 19:30 than at 15:30, an hour and a half after the announced start.

The two largest positive contributors are Ada (+128) and Milan Gale Muškatirović (+104) — a lake
recreation area and a Danube-quay sports centre, both of which emptying on a Saturday evening is
entirely ordinary. Together they account for 92% of the net change.

So: whatever is happening in the centre is a *local* redistribution inside a city that is, in
aggregate, emptying. Reporting only the falling central garages would produce a true set of numbers
arranged into a false impression. The total belongs in the report next to them, always.

**Alternative explanations that this observation cannot exclude, and does not try to:** ordinary
Saturday-evening behaviour; other events in the city; weather; the announced transport-regime changes
themselves redirecting traffic independently of the race; and the unknown age of every number.

### 3.4 Our own founding problem appeared in our own data, twice

**Kalemegdan and Kamenička report 0 in all five samples**, while every neighbour moves. We cannot
distinguish "genuinely full all evening" from "this field is stuck at zero" — the exact confusion
between an observed zero and a silent source that the project was built to prevent, now present in
our own dataset under two names.

The resolution is cheap and is scheduled by construction: **the last slots run at 22:30 and 23:30
local, and the final check at 00:30**, when central Belgrade car parks are not plausibly full. If
those locations still read 0 at 00:30, the field is dead and both locations must be reclassified from
*observed zero* to *unavailable* for the whole series — retroactively, with the reason recorded.

Until then they stay drawn as observed zeros, because that is what the source said, and changing them
before the evidence exists would be the same sin in the opposite direction.

---

## 4. What the interface study got right and wrong, checked against this data

The study `research/studies/state-alphabet.html` was drawn from two samples. Against five:

- **The observed-zero versus silent-source distinction is not a subtlety.** It is the live problem
  in this dataset, on two named locations, tonight. The study's decision to draw a reported zero with
  a small open ring, deliberately unlike the hollow tick of absence, is doing real work.
- **The quorum bar is under-tested.** Every one of the five samples returned all 27 locations, so the
  bar has been full every time. The mechanism has not yet met a partial response and therefore has
  not been exercised at all. If the source never returns a partial set, the quorum bar is unproven
  for parking and its real test will come from a multi-source zone.
- **The ribbon's vertical scale is wrong.** It was drawn against a fixed maximum of 3 900 chosen from
  two samples; the total has now exceeded it. A fixed scale chosen from an incomplete series is the
  same error class as a pre-registered grouping that does not hold — and it is worth keeping as a
  visible bug in the study rather than silently rescaling, because it demonstrates the failure mode.

---

## 5. The source, audited directly

One separate bounded request was made outside the observation, stored in `runtime/` and touching no
observation file, to answer the single most important open question: does the publisher state when it
measured?

**It does not, anywhere.** The full 47 328-byte page contains no "ažurirano", no timestamp, no
statement of refresh interval; the only time-shaped numbers on the page are geographic coordinates.
The response headers give no bound either: `Cache-Control: no-cache, private`, **no `Last-Modified`,
no `ETag`, no `Age`**, nginx with a per-request Laravel render.

Three consequences:

1. **`observed_at: null` is a property of the source, verified at the source** — not a shortcoming of
   the recorder. The fifth state (value exact, time unknown) is therefore not a design preference but
   a necessity, and the paper can say so with evidence rather than assumption.
2. **Total capacity per location is not published.** The protocol's refusal to compute an occupancy
   percentage is correct and necessary, not merely cautious.
3. The page's prose mentions "capacity of about 2 800 parking spaces and 17 car parks", while our
   **free**-space total reaches 3 931 across 27 locations. The prose figure and the live counter
   describe different sets and **must never be combined**. Anyone adding them would produce a
   confident nonsense.

---

## 6. What must still happen for this to become a report

1. Complete the remaining slots (18:30 → 22:30 UTC), including the 00:30 local final check.
2. Resolve Kalemegdan and Kamenička against the late-night samples, and reclassify with a recorded
   reason if the zeros persist.
3. Build the timeline of announcements — organiser, transport authority — and place the actual
   regime-change times against the sample times, since the protocol warns that some changes began the
   previous day and none of this should collapse to "the race was at 18:00".
4. Report coverage as 10 of 13 with the three missing slots named, and the reason named.
5. State the minimum-persistence rule (§3.1) as a method contribution, and state the falsified
   pre-registration (§3.2) as a result rather than burying it.

## Honest verdict on this interim reading

Five real samples, all verified HTTP 200 with distinct hashes; one source audit; four findings, of
which two (the minimum-persistence rule, the falsified pre-registration) are method results
independent of whatever the race did.

Not established, and not claimed: any causal link between the event and any number; any statement
about participants, arrivals or departures; any occupancy percentage; any claim about the two
constant zeros; and any claim that the observation is complete. Five of thirteen slots is not a
series, and three of the missing slots are missing permanently.
