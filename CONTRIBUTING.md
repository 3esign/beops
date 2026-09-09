# Contributing to BEOPS

BEOPS is an evidence-first urban observatory for Belgrade. Many minds — human and model — will work
in this repository. This file is the system of order that lets them do it without stepping on each
other or on the truth.

It is short on purpose. A rule that cannot be obeyed is not a rule.

---

## The one screen

1. **Claim before you write.** Add a line to `CLAIMS.md` naming the file and yourself. Never edit a
   file someone else has claimed.
2. **Put it where it belongs.** `research/0N-*/` for documents, `research/` root for code and
   registries, `observations/` and `evidence/` for things that must never change.
3. **Index it in the same commit.** A document that is not in `research/README.md` does not exist to
   the next mind.
4. **Say what state it is in.** Every document opens with a status line. No status, no trust.
5. **Never write a number you did not verify.** Received is not measured. Forecast is not
   measurement. Missing is not zero. Scheduled is not executed.
6. **Close with an honest verdict.** What you did, and what you did not do and are not claiming.
7. **English for anything public.** Working notes may be in Serbian; the paper, the README, the
   registries and this file are English.

Everything below is detail on those seven.

---

## 1. Claim before you write

Two minds edited `rad_draft.md` on 2026-09-05 with no lock. It happened to work — one pass absorbed
the other's findings, and the second caught an artefact the first had promoted to a headline result.
That was timing, not design, and it is exactly the failure the swarm methodology exists to prevent.

**The protocol, borrowed from `docs/ROJ.md` and reduced to what this repository needs:**

| Verb | Meaning |
|---|---|
| `CLAIM <path>` | I am about to write this file. Nobody else writes it until I release. |
| `DONE <path>` | I am finished, with a one-line proof (a commit hash, a test result, a file that now exists). |
| `RELEASE <path>` | I am finished and claim nothing. |
| `BLOCK <path> — reason` | I cannot proceed and I am saying why, rather than going quiet. |
| `HOLD` | Something is wrong; everyone stops writing until it is resolved. |

Claims live in `CLAIMS.md` at the repository root, append-only, one line each:

```
2026-09-05T18:20Z · claude-cowork · CLAIM research/06-paper/rad_draft.md · rewriting Results §3
2026-09-05T18:40Z · claude-cowork · DONE  research/06-paper/rad_draft.md · commit bb8e7e1, npm test 36/36
```

A claim older than **two hours** with no `DONE` or `RELEASE` is stale: take it, and write a line
saying you took it. Nothing is ever silently overwritten.

**Evidence files can never be claimed, because they can never be edited.** See §5.

## 2. Where things go

```
README.md                 what BEOPS is, and the current state
UPUTSTVO.md               the operating rules (Serbian; the working manual)
CONTRIBUTING.md           this file
CLAIMS.md                 who is writing what, right now
KNOWLEDGE.md              errors, experiences, sources, skills, decisions
LOG.md                    append-only trail of actions
RECNIK.jsonl              the vocabulary: terms this project coined or narrowed

research/
  README.md               the index — every document, what it is, what it supersedes
  SOURCE_REGISTRY.json    the sources. The register, not prose about it.
  MODEL_CANDIDATES.json   the model candidates
  *.py  *.ps1  *.js       code and tests, flat, because the test runner and the
                          recorder resolve paths from here — do not move them

  01-programme/           what we intend to do: the work programme, the plans, the protocols
  02-senses/              what the city offers: reconnaissance, discovery rounds, requests
  03-models/              model catalogue and model literature
  04-bibliography/        the two bibliographies (see below)
  05-design/              the interface direction, and studies/ that test it
  06-paper/               the manuscript, and conference/ with the call and instructions
  07-legal/               what may lawfully be collected, in quoted primary texts
  _trail/                 how the work went: intake, plans, audits, merges, reviews,
                          verification records. Read these to understand a decision.
                          Never cite them as findings about the city.
  _scratch/               throwaway. Nothing here is referenced by anything.

  observations/           THE PILOT. Immutable.
  evidence/               PROBE SNAPSHOTS. Immutable.
```

**The two bibliographies are deliberate.** `04-bibliography/BIBLIOGRAPHY_*.md` is the wide,
verified foundation — theory, ontology, observation standards, critical literature, comparative
practice. `04-bibliography/BIBLIOGRAFIJA_*.md` is the narrow layer — models and benchmarks tied to
a named experiment. New theory and standards go in the first; new models and benchmarks in the
second. Do not merge them.

**Do not move code or registries out of `research/` root.** `tools/test-research.js` discovers tests
with `unittest discover -s research -p test_*.py`; `audit_model_cards.py` reads
`MODEL_CANDIDATES.json` from its own directory; `observe_10k.py` writes into `research/observations`.
Moving them breaks the test chain and the live recorder for no navigational gain.

**If you move documents, use `tools/migrate_structure.py`.** It rewrites every local link and then
moves, in that order — the reverse order silently leaves every moved file's links pointing at
nothing, because after a move a file's old and new directory look identical. Run the link check
afterwards and report the number.

## 3. Naming

- Documents: `SCREAMING_SNAKE.md`, plus `_YYYY-MM-DD` when the document is a dated pass rather than a
  living reference. `RADNI_PROGRAM.md` lives; `AUDIT_V1_2026-09-05.md` is a moment.
- Code: `snake_case.py`, tests as `test_<subject>.py` so the discoverer finds them.
- Evidence: `<kind>-<ISO8601 compact>.json`, never overwritten, never renamed.
- Sources in the register: `S<nn>`, allocated in order, **never reused** — a retired source keeps its
  id with a `retired` status, because a number that changes meaning is worse than a gap.
- Experiments `E<nn>`, research questions `RQ<nn>`, work items `R<nn>`, tasks `T<nn>`. Same rule: ids
  are permanent.

## 4. Status, at the top of every document

The first lines of every document, before anything else:

```
Status: draft | working | current | superseded by <path> | historical
Date:   YYYY-MM-DD
Author: <mind or person>
```

`current` means: if this contradicts another document, this one wins. There is at most one `current`
document per subject, and `research/README.md` says which.

## 5. What may never be edited

Anything under `observations/` and `evidence/`. These are the record.

- A `claim-*.json` is written before the request; a `sample-*.json` after it. Neither is ever
  rewritten, and a repeated slot never re-requests.
- An interrupted claim with no sample stays as uncertainty. It is not cleaned up, and it is not
  retried.
- `OPAZANJA.md` is append-only. If an earlier note was wrong, **append the correction with its
  evidence** — do not edit the note. The chain of what we believed and when is itself data.
- A missing slot stays missing. It is never backfilled, interpolated or replaced with zero.

If you need to reclassify past evidence — for example, an "observed zero" that later proves to be a
dead field — write the reclassification as a new note naming what changed and why, and leave the
original readings untouched.

## 6. How to add things

**A source.** Probe it once, bounded. Open the endpoint yourself; do not trust a description. Record
in `SOURCE_REGISTRY.json` with: id, name, URL, status (`probe_ok` / `primary_page` / `lead` /
`no_coverage` / `retired`), access terms **as the source itself states them**, update rhythm, and —
the field that matters most — whether it publishes a measurement time distinct from the retrieval
time. Save the probe output under `evidence/`. **A confirmed absence is a source record too**: a
global network with nothing over Serbia gets `no_coverage`, not silence, so the next mind does not
spend the same afternoon.

**A document.** Write it, give it a status line, add its row to `research/README.md` in the same
commit, and put it in the right folder. If you cannot say which folder, the document is doing two
jobs and should be two documents.

**A finding.** It goes in `KNOWLEDGE.md` through `node tools/project_kit.js kb <dir> add
error|lesson|source|skill|decision "<text>" --source <path>`, so the counters stay honest. An error
is something that went wrong; a lesson is something the next mind would otherwise have to discover
alone.

**A term.** If you coin or narrow a word, add it to `RECNIK.jsonl` the same day. The vocabulary is
how minds that never meet still mean the same thing.

**An experiment.** It needs a question, a pre-registered method, and a stated way it could fail,
written **before** any data. If it fails, report the failure — a falsified pre-registration is worth
more than a pattern found afterwards, because a pattern found afterwards in many series is nearly
free and therefore nearly worthless.

## 7. What a number is allowed to claim

These are not style preferences. They are the project.

- **Received is not measured.** If the source publishes no measurement time, say so and keep the
  field null. Do not substitute the retrieval time.
- **Forecast is not measurement.** Different word, different mark, different colour.
- **Missing is not zero**, and a reported zero is not missing. These must never look or read alike.
- **Scheduled is not executed.** A configured job is not evidence that it ran. Show the receipt.
- **An excursion is not evidence until it persists.** In a series with no measurement time, a
  single-sample spike that reverts in the adjacent sample is a candidate source artefact and stays
  out of every claim until it recurs. This rule cost us one nearly-published fabrication; it is
  cheap to obey.
- **No causality.** We observe and we connect. We do not conclude that one thing caused another.
- **No occupancy percentage** without a published capacity, and no combining a figure from prose with
  a figure from a live counter — they usually describe different sets.
- **Honour every named opt-out.** A `robots.txt` entry naming ClaudeBot, a Cloudflare `Content-Signal`
  reservation, or a terms clause forbidding automated access is final. Do not work around it, do not
  rename the collector, do not propose it again. Seven sources are recorded as `opted_out` in the
  registry with their exact clause. Where the source matters, the answer is a letter, not a
  workaround.
- **Never present a figure as an official measurement** where a statute reserves that term — the
  noise law reserves *merenje buke* to accredited bodies. Ours are research observations, labelled so.
- **No person.** No faces, no plates, no tracking, no individual records, ever, at any resolution.
- **Aggregates only, and never below the level where a single person could be inferred.**

## 8. Before you say "done"

Run these and put the numbers in your closing verdict:

```
npm test                                     # the offline research suite
python -B tools/migrate_structure.py . --dry # if you moved anything: link report
node tools/project_kit.js check <dir>        # the project kit's own gate
```

Then write the honest verdict: what you did, with evidence; and what you did **not** do and are not
claiming. A verdict with no second half is not a verdict.

If the work produced a visual artefact, it also passes the seven questions in
`skills/svemir-lepota` — sentence, lie, subtraction, hierarchy, motion, naked screen, who can.

## 9. Language

Anything public — this file, `README.md`, `research/README.md`, the registries, the manuscript, the
bibliographies, commit messages — is **English**. Working notes, the operating manual and the
observation diary may be Serbian, because that is where thinking happens and thinking should not be
translated while it is still warm.

---

*If a rule here ever blocks work that is obviously right, do the right thing and then change the
rule in the same commit, with the reason. A rule nobody can amend stops being a rule and becomes an
obstacle.*

## 10. Permission before collector — and two rules the machine enforces

Nothing is collected until `research/08-provenance/` holds the stored evidence
that we may. That folder has its own README; the short version is:

```
python -B tools/legal_capture.py --sid <ID> --name "<name>" \
    --url <the exact URL we will read> --terms <licence page>
python -B tools/build_provenance_index.py
```

Commit the capture and the regenerated `INDEX.md` in the same commit. Sources
in `SOURCE_REGISTRY.json` with no capture appear in the index under **Not yet
documented** — that list is the work queue, and it is visible on purpose.

Two rules below are not written here in the hope you will remember them. The
tool refuses the work if you break them, because both were broken by the person
who wrote them, within an hour, on the day they were written.

**An unknown is never a permission.** If TLS could not be verified, if
`robots.txt` could not be read, if the URL was unreachable — the verdict is
`null`, and `null` renders under *Evidence incomplete*, never under
*permitted*. There is no `--insecure` mode and there will not be one. More
generally: any value in this project that answers a question of the form "may
we?" or "is it true?" must be able to say *I could not tell*. A boolean that
cannot say it will eventually say yes when it means nothing at all.
(`08-provenance/CORRECTIONS.md`, C-001.)

**One source, one id, forever.** Before allocating an id, the tool checks
`SOURCE_REGISTRY.json`: an id that is not in the registry is refused unless you
pass `--new-source`, and a URL whose host already belongs to another source is
refused with that source's id printed. If you believe two sources genuinely
share a host, pass `--allow-shared-host` and say why in the note.

## 11. Where a source's own words outrank ours

When a source labels its own data — a provenance column, a legend, a reason for
a missing value — **that labelling is the evidence, and we preserve it rather
than replacing it with our own judgement.** Three consequences, learned from
S57:

- **Read the dictionary that ships with the data, per file.** The Putevi Srbije
  workbooks each define their own legend, and the same asterisk means "borrowed
  from the neighbouring counter" in one publication and "unbuilt interchange"
  in another. A global lookup table would have been wrong in a way that
  produces plausible numbers, which is the worst way to be wrong.
- **A borrow is allowed; an assumption is not.** Where a file publishes no
  legend, borrowing one from another file of the same year is acceptable *only*
  if the donor is written into every affected row. If you cannot record where a
  meaning came from, you may not use it.
- **Absence keeps its kind.** "Not counted because it is a city street",
  "counting was interrupted" and "the road did not exist yet" are three
  different facts. Collapsing them into null, or into zero, destroys the thing
  this project exists to show.
