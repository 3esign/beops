# What can fail here without anyone finding out

**BEOPS — Belgrade Evidence Observatory · stability review, 2026-09-10**

Not a health check. A check of the checks: for every moving part, what watches it, how we would learn
that it stopped, and how long it would be wrong before we did. Measured from the machine, not assumed.

---

## The one that had already happened

**2026-09-10, 00:38 → 01:22.** The mind ticked every four minutes, every tick failed to reach its
model, and it produced nothing for forty-four minutes. During that window:

| watcher | what it said | why |
|---|---|---|
| the scheduled task | `Ready`, last result `0` | the task ran and exited cleanly — it did |
| the watchman | `OK — 34 current, 0 late, 0 stalled` | it watches SOURCES, and sources kept arriving |
| the guard | `ok` | it watches TASKS and PERMISSIONS, and both were fine |

Nothing was broken by any measure anyone was taking. **"Is the task running" and "is the organ
producing" had never been different questions here**, so no instrument could tell them apart. The
reason was sitting in the organ's own receipts in plain words — `model daemon not answering` — for
three quarters of an hour, and no check ever read it.

It was found because a measurement of something else came back empty. That is not monitoring; that is
luck, and luck is not a property you can keep.

**Fixed the same day** (commit `12d3414`): `guard.py` gains a third question beside the tasks and the
permission invariants, three-way on purpose —

- **ok** — a row inside the organ's window;
- **warn** — no row, still ticking, *and the receipt's own reason is carried* into the ledger and onto
  stdout;
- **unknown** — no row and no receipt: not merely quiet, not running.

The guard does not repair this class. It repairs exactly one thing — a task that exists and is not
running — and an organ may be quiet lawfully. Restarting one because it is quiet is how a record
starts inventing. A test asserts the organ check contains no repair call at all.

---

## What is watched, and by what

| part | watcher | cadence | how a failure shows |
|---|---|---|---|
| scheduled tasks | guard | 15 min | re-enabled and started; the one class it repairs |
| permission invariants | guard | 15 min | **STOP** in the ledger and on stdout; never repaired |
| sources current | watchman | 10 min | late / stalled / unknown counts in the watch ledger |
| **organs producing** | **guard (new)** | **15 min** | **warn with the organ's own reason, or unknown** |
| retention window | guard | 15 min | first erasure falls due 2026-12-07 |
| the built page's invariants | the test suite | **only when a person ships** | see below |

Measured at the review: 8 Beops tasks present, guard verdict `ok` across 12 checks, watchman
`34 current · 0 late · 0 stalled` — 79 watch-ledger rows, 48 guard-ledger rows.

---

## What is still not watched

**1. The publish path runs no tests.** `Beops_Publish` rebuilds the site and pushes it every ten
minutes. It calls `build_site.py` and `make_maps.py` — and nothing else. The 224 tests that guard the
page's invariants run only when a person ships. A page that violated one of them would go live and
stay live.

*Judgement, not a fix:* the exposure is small, because those invariants break when CODE changes, and
code changes only through a ship, where the tests do run and the gate does hold. Putting a test gate on
the automatic publish would be a stabilising change, but it puts a new way to fail into the one path
that must not stop. It is worth doing carefully and on purpose, not today and not quickly.

**2. Static layers have no staleness rule.** `context-population.json` was 31 h old at the review and
`basemap-belgrade.json` 33 h. Both are supposed to be static, so age is not itself wrong — but nothing
anywhere states how old either is allowed to become, which means nobody would notice a build that
silently stopped refreshing them.

**3. One machine, and the models sit in 4 GB of VRAM.** At the review, `llama3.2:1b` (1.6 GB) and
`paraphrase-multilingual` (0.17 GB) were resident, leaving ~2.2 GB — while the thinking model needs
3.4 GB. It does not fit, which is exactly the shape of the `TimeoutError` and `model daemon not
answering` receipts from last night. `OLLAMA_MAX_LOADED_MODELS=1` is set in both user and machine scope
and **is not being honoured** — two models are resident. `OLLAMA_KEEP_ALIVE` was moved 0 → 20m at 08:47
and back to 6m at 10:00 after this review; it will not be touched again before an hour of measurement,
because tuning on one sample is how the 20m was chosen.

**4. The publish token and the GitHub remote** are a single point of failure with no check: nothing
would tell us that a push had been failing except the absence of new commits, which nothing watches.

**5. Disk.** C: 49.8 GB free of 237.4; D: 46.0 GB free of 1 862.5. Not close to anything, and not
watched either.

---

## The pattern under all of it

Every watchman here was built to answer *is the record current*, and every one of them answers it
correctly. Not one was built to answer *is the thing that thinks about the record still thinking*, or
*is what we publish still what we tested*, or *is the machine still able to load the model it needs*.

The failures this project has actually had — the forty-four minutes, the clock read as a number, the
notebook loop, the panel that changed height in one range out of three — share a shape. In each case
every check that existed passed, and the thing that was wrong was a question nobody had asked. That is
not an argument for more checks. It is an argument for asking, of each new part, the question this
review is named after, before it has had a chance to fail quietly.

*Verified against the machine on 2026-09-10 between 09:50 and 10:05 local. Nothing in this document is
inferred from what the code says it does.*
