Status: current
Date: 2026-09-11

# BEOPS — orientation for anyone (or anything) arriving here

**Belgrade Evidence Observatory for Public Signals.** Read this before touching anything. It is short
on purpose; every claim in it points at the file that proves it.

---

## What this is, in one paragraph

An evidence-first instrument that reads what Belgrade's public bodies already publish, records what
arrived and *when*, and refuses to say more than the record supports. It is a scientific work by two
authors — **prof. dr Darinka Golubović Matić** and **doc. dr Semir Poturak** — offered to a conference
held at Univerzitet Union — Nikola Tesla. Both authors teach there. **The university is not the owner,
operator, controller, publisher or sender of anything here**, and no sentence in the code, the site,
the paper or the letters may be written so that it could be read that way. This is not modesty: a
claim of institutional authorship attaches an institution's liability to a private research act it
never authorised. If you are about to write an affiliation line, write it the way the site footer
does.

## Where it physically is

- **Collection, the record, and the evidence run on the authors' own computer, in Serbia.** Every
  collector, receipt, row, and the ~585 MB of stored permission captures live on one private machine.
- **What leaves the country is the publication, not the processing**: the static site on GitHub Pages
  and the public repository `3esign/beops` on GitHub, servers outside Serbia.
- **The permission evidence never leaves that machine.** The public repo carries a placeholder saying
  a reviewer may request any capture by id and SHA-256.
- The export is a one-commit-per-publish snapshot, not a `git push` of local history — see
  `tools/publish_github.ps1` and the reason in its header.

## The rules that are not negotiable

These are enforced by tests, not by intention. If a change breaks one, the change is wrong.

1. **Five states, no sixth**: observed / untimed / estimated / forecast / unavailable. `unavailable`
   renders as itself.
2. **Received is not measured.** 49 of 843 series carry only a reception time and are marked
   `untimed`. An untimed value has an exact value and an unknown age — never give it an age.
3. **Missing is not zero.** A silent source produces a receipt with zero rows, which is a different
   object from a zero measurement.
4. **Permission is bytes, not memory.** 313 stored captures. `research/test_permission_gate.py` fails
   the suite before anything is collected if a polled source has no evidence.
5. **A named refusal is permanent and is never routed around.** 14 refusals; none polled; asserted by
   test.
6. **Corrections are appended, never edited.** 25 entries in `research/08-provenance/CORRECTIONS.md`.
   The wrong text stays visible beside the right one.
7. **The machine may not say what the record does not support.** Gate version in research/ORGANS.json, measured, residue named.
8. **A monitor that cannot see says UNKNOWN, never OK.**
9. **Success is verified on the artefact, not on the receipt.** An exit code of 0 is evidence that
   something finished, never that it happened. C-018 is what skipping this costs.
10. **Everything public is in English or in all four languages the page speaks** (sr / en / zh / de for
    the page's own words; generated register content stays sr/en, because it quotes a source).

## Where things are

| | |
|---|---|
| Source registry (counts are generated from the registry) | `research/SOURCE_REGISTRY.json` |
| Collectors (31 listed, 28 polled) | `research/COLLECTORS.json` |
| Permission evidence index + ledger | `research/08-provenance/INDEX.md`, `LEDGER.jsonl` |
| Corrections ledger | `research/08-provenance/CORRECTIONS.md` |
| Gate test set and evaluation | `research/GATE_ADVERSARIAL_SET.json`, `research/eval_gate.py` |
| Retention: headlines/digests kept; raw feeds 90 days, R1–R6 | `research/RETENTION.json`, `tools/apply_retention.py` |
| Record of processing activities (ZZPL čl. 47) | `research/07-legal/BEOPS_EVIDENCIJA_OBRADE_2026-09-09.md` |
| Letters, ready to send | `research/07-legal/BEOPS_PISMA_v3_2026-09-09.md` |
| Pre-paper and its addendum | `research/06-paper/PRE_PAPER_v3_*.md` |
| The site builder | `tools/build_site.py` → `docs/` |
| The three frames | `research/05-design/studies/{monolog-puls,podaci,traka-live}.html` |
| Watchman / guard | `tools/watchman.py`, `tools/guard.py` |
| Tests (discovered by npm test) | `research/test_*.py` |

## What keeps running

Seven scheduled tasks, hardened by `tools/harden_tasks.ps1`: start-when-available, run on battery,
one-hour kill for a hung run, three retries, and an **AtLogOn** trigger so everything re-arms after a
restart. No password is stored and none will be, so the honest limit is: **they run while this user is
logged on, and resume by themselves the moment that is true again.** `WakeToRun` is deliberately off —
waking the machine to collect would make the record say the city was quiet when it was the laptop that
was asleep.

`Beops_Guard` runs every 15 minutes. It is the only thing here allowed to repair: if a BEOPS task is
disabled or has badly missed its window, it re-enables and starts it. It also re-checks four permission
invariants from the files on every pass and says **STOP** — without repairing — if one fails.

## The open items, most important first

1. **The second annotator.** See `research/GATE_SECOND_ANNOTATOR.md`. This is the single thing that
   most improves the paper, and it is one careful afternoon of one person's time.
2. **Seven days of continuous history.** 28 h at the time of writing. Nothing to build; only time.
3. **The letters actually sent, with answers recorded** — converts the coverage finding into an
   experiment. Send order and reasoning in the letters file.
4. **A lawyer's read of letter sets A and D** before they go.

## If you are an assistant working here

- Verify on the artefact, never on the receipt: read the built file, fetch the live URL, measure the
  rendered page. Every defect in the corrections ledger that reached the public was one a passing test
  did not look at.
- Never delete what you did not create; move it to `_to_delete/`.
- Never open, copy or transfer `.env` or `data/secrets.json`.
- Zero runtime dependencies: Python standard library and plain browser JavaScript. Do not add a package.
- Git author is always `Semir Poturak <scumutator@gmail.com>`.
- Outputs are issued as NEW versions; an old one is never rewritten.
- Say the honest verdict in every report and every commit message, including what is weaker than it
  looks and what would falsify the claim.


Recovery entry (2026-09-11): `research/_trail/REPAIR_2026-09-11.md` records implemented changes, validation and unresolved limits. `npm run doctor` checks local build requirements; `npm start` serves generated docs on a loopback port (printed on startup), and `npm run start:legacy` explicitly starts the old prototype. Headlines are retained and the complete collected archive is at `naslovi.html`; article bodies are not published. Public Git history persists. Scheduled task definitions are in `tools/beops_tasks.ps1`, with individual execution limits; disabled tasks and operator pauses are preserved.
