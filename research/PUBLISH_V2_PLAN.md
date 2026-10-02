Status: in progress (steps 1-2 implemented 2026-10-01)
Date: 2026-10-01

# Publishing in parts — a simpler release path for BEOPS

## Why this exists

The public site has not updated since 2026-09-27 16:06 UTC. Each failure had a different trigger:
a cycle budget, a disk admission, the durable-root check after the move to the project disk
(fixed in 3ff2bdc), and tests that assumed September (fixed in 0d89f57). All of them failed
inside one monolithic cycle. A failure at minute 90 throws away the 89 minutes before it, and
the next cycle starts that work again.

Measured from `runtime/publish-phases-*.jsonl` over the last 7 days (70 cycles):

| phase | median | worst | total over 7 days |
|---|---|---|---|
| prepare isolated release (freeze inputs) | 648 s | 6 595 s | 26.5 h |
| ├ input inventory (stat walk, ~64 000 files) | — | 5 810 s | 12.1 h |
| ├ immutable copy/link (~63 000 files, 0.94 GB) | — | 3 642 s | 7.5 h |
| └ mutable capture (1.06 GB copied **under the collectors' write lock**) | — | 629 s | 2.1 h |
| rebuild frozen latency | 205 s | 2 555 s | 3.4 h |
| complete research gate (full suite) | 178 s | 474 s | 1.4 h |
| build_site.py | 17 s | 55 s | 0.2 h |
| git push public export | 17 s | 22 s | 0.1 h |

What the public receives is about 130 MB (`docs/`). What every cycle freezes is about 2 GB in
64 000 files. On a quiet disk the whole cycle took 7–26 min (measured 2026-09-25 and 2026-09-27).
On a busy disk the same phases take up to 70× longer (KNOWLEDGE, 2026-09-30). Almost all of the
lost time is spent re-freezing the same history again, not building or publishing.

| input scope | size | files |
|---|---|---|
| data/live/rows | 1 031 MB | 100 |
| research/evidence (local only, never published) | ~600 MB | ~2 600 |
| data/live/derived | 174 MB | 9 651 |
| data/live/raw | 91 MB | 10 061 |
| data/live/receipts | 35 MB | 33 392 |

## The principle

**What is closed never has to be frozen again.** Rows are append-only per month, and receipts
and raw files are written once. A closed period can therefore be sealed once: hashed, recorded
in a manifest and made read-only. After that, a release refers to the seal by its root hash
and does not copy or re-hash it. Only the open period (the current month's tail, today's receipts)
is captured per release. That capture is a few MB and holds the write lock for seconds.

Every guarantee stays where it is. Inputs are still frozen and the build is still isolated and
deterministic. Success is still verified on the artefact, and the chain of confirmations still
links every publication. The only change is that work which was proven once is not proven again
every hour.

## The stages

Each stage writes its own receipt (`runtime/stages/<stage>.json`: input root, output root,
seconds, verdict). A stage reruns alone when it fails. The cycle is the chain of these receipts,
not one 110-minute process.

| stage | cadence | budget | does | proves |
|---|---|---|---|---|
| S1 seal | daily 00:30 + month end | 30 min | closed day/month → read-only + manifest (sha256 per member, Merkle root) | manifest root; spot re-hash 1 % per run |
| S2 capture | per release | 2 min | open period only, under the write lock | open-part root; seal roots referenced, not copied |
| S3 build | per release | 15 min | derived products incrementally: closed-period aggregates cached by seal root, only the open period recomputed | output root; determinism (same inputs → same bytes) |
| S4 gate | code: per source commit · data: per release | 10 min / 1 min | full suite runs once per source commit, as its own job; a release runs only the data-integrity gate if that commit already has a passing full-gate receipt | gate receipt bound to the commit + data root |
| S5 publish | per release | 5 min | export + one commit + push, skipped if `docs/` root is unchanged | remote HEAD equals the pushed commit |
| S6 verify | after S5 | 5 min | public site serves the new `as_of` | public artefact SHA = local artefact SHA |

## Order of work (each step is useful on its own)

1. **Code gate as its own job (S4).** It already exists in part: the "fast data gate" applies when
   the last *successful publication* had the same source commit and its full gate is less than
   24 h old. Missing piece: a commit runs the full suite once, outside any release, and the release
   only reads that receipt. Today a new commit, a failed publication, or a 24-hour rollover each
   put the 3–8 min suite back inside the 110-minute release budget. Two of those three happened today.
2. **Closed months move out of the mutable path (S1 for rows).** `data/live/rows/*/<YYYY-MM>.jsonl`
   whose month is before the current UTC month is classified like immutable evidence. Those files
   are inventoried with the cached hash and linked, never copied under the write lock. On 2026-10-01
   this alone moves ~1 GB out of every cycle and out of the collectors' lock. Guard: a closed-month
   file whose size or mtime changes refuses the release (the existing post-copy verify).
3. **Receipts and raw sealed per closed day (S1).** One manifest per day replaces ~1 000
   per-file inventory entries per day. The stat walk stops scaling with the age of the observatory.
4. **Incremental derived products (S3).** History, latency, agreement and baseline keep their
   closed-period results keyed by the seal root and recompute only the open period.
5. **Stage receipts and per-stage budgets (S2–S6)**, replacing the single cycle budget.

## Done (2026-10-01)

- **Step 1.** `tools/code_gate.ps1` runs as scheduled task `Beops_CodeGate`, every 30 min. It
  writes `runtime/code-gate/<commit>.json`. `tools/publish_github.ps1` accepts a passing receipt
  for its own commit that is younger than 24 h and then runs only the data-integrity gate. The code
  gate yields while a release preparation holds its lock, and it writes no receipt for uncommitted
  code. Guard: `research/test_code_gate.py`.
- **Step 2.** `tools/prepare_release.py` seals a rows month file that closed more than 6 h ago. The
  file is linked instead of copied under the write lock. Its facts (sha256, rows, newest reception,
  state key) are read once per day and cached in `.beops-sealed-months.json`, and the shared file
  is made read-only. Retention lifts the seal before it redacts. The switch is
  `BEOPS_RELEASE_SEAL_MONTHS=0`. Guard: `research/test_release_sealed_months.py`, which also shows
  that the sealed facts equal the facts of an ordinary copy of the same bytes.
- **Cleanup off the critical path.** A finished or abandoned workspace (about 64 000 files) used to
  be deleted with Remove-Item before the next capture. That took tens of minutes on a loaded body
  and left no phase trace: the "stall after resolve release OID". Now it is renamed to
  `beops-trash-<hex>` at once, under the same ownership checks, and deleted with `rd` at the end of
  the cycle, while the cycle still holds the lock. Guard: `research/test_release_trash.py`.
- **Priority.** Every release phase runs above normal priority (`tools/publish_safety.ps1`;
  `BEOPS_PUBLISH_PRIORITY=normal` turns this off). Publication has priority on a shared body.

## Toward an invisible observatory

The goal is a publication cost that follows what is *new*, not how long the observatory has
existed. Then adding a source, a database or a year of history does not make the hourly cycle
heavier, and BEOPS runs unnoticed on a working machine.

- **Per source, per period.** Every source keeps its own month files, so a new database is a new
  directory with its own seals. A cycle touches only open periods: today's receipts and this month's
  rows of the sources that received something.
- **Seals instead of copies** (steps 2–3). Closed periods are referenced by root hash. Releases
  share them and never move them.
- **Incremental derived products** (step 4). Each product keeps one result per closed period, keyed
  by that period's seal, and combines them with a fresh result for the open period.
- **Stages that can move.** Stage receipts make a stage a unit of work with declared inputs and
  outputs. Once more workstations join, building (S3) and the code gate (S4) can run on another
  machine against the same sealed inputs. Collection and the permission evidence stay on the
  authors' machine, by rule.
- **Measured, not assumed.** Each stage receipt carries its seconds and bytes, so "invisible" is a
  number in the guard: the share of a cycle spent on unchanged history should trend to zero.

## Questions that came out of the simulation

- Answered 2026-10-01 (Semir): closed months may be sealed; publication has priority over chats.
- Open: the paper's methods section may need one line saying that a closed month is captured by
  its sealed hash (verified daily) rather than copied on every cycle.
