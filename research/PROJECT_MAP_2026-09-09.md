# BEOPS — the map of the project, 9 September 2026

Status: current (written after the day's last commit `f8a3ea7`; supersedes nothing — `research/README.md`
stays the index of documents, this is the map of *where things live and how they move*)
Date: 2026-09-09
Author: claude-cowork, for the editor of record

Read this when you want to know **which folder holds what, which task writes where, and what is
public**. Paths are relative to the project root (the `Beops` folder). Nothing here needs to be
memorised: every line points at a file that explains itself.

## 1. The whole thing on one screen

```
Beops/
├── README.md                public front page (English)
├── CONTRIBUTING.md          the contract: claims, status lines, immutable evidence
├── CLAIMS.md · KNOWLEDGE.md · TEAMWORK.md · UPUTSTVO.md · RECNIK.jsonl
├── LOG.md                   one line per working session (Serbian, internal)
├── package.json · server.js · src/   the local server, zero dependencies
├── tools/       THE MACHINES  — everything scheduled runs from here     (§3)
├── research/    THE KNOWLEDGE — registries, law, provenance, papers, code (§4)
├── data/live/   THE MEMORY    — receipts, rows, thoughts; never in git    (§5)
├── public/      THE EXPORT    — snapshot, base map, context layers        (§6)
├── docs/        THE SITE      — generated for GitHub Pages, never edited  (§6)
├── runtime/     logs and scratch of the scheduled tasks; ignored by git   (§7)
└── archive/ · qa/            older material and test fixtures
```

Two other places outside the folder matter:

- `C:\Svemir\data\brain\hands\` — the **hands** channel: a `.cmd` file dropped here is executed on
  the PC and answered in `.out`. This is how work from the cloud reaches the machine.
- **github.com/3esign/beops** and **3esign.github.io/beops** — the public export and the site.

## 2. The five clocks (scheduled tasks)

Registered by `tools/register_tasks.ps1`; each runs a `.bat` in `tools/`, logs to `runtime/`,
and can be checked with `schtasks /query /tn Beops_<name> /v /fo list`.

| task | every | runs | writes | log |
|---|---|---|---|---|
| **Beops_Collect** | 5 min | `collect_tick.bat` → `collect_daemon.py tick` + `export` | `data/live/receipts/`, `data/live/rows/`, `public/live-snapshot.json` | `runtime/collect-tick.log` |
| **Beops_Organ** | 10 min | `organ_tick.bat` → `organ_news.py run` (the news-sorter) | `data/live/derived/news/` | `runtime/organ-tick.log` |
| **Beops_Mind** | 4 min | `mind_tick.bat` → `organ_mind.py step` (one drop of the conversation) | `data/live/derived/mind/` | `runtime/mind-tick.log` |
| **Beops_Publish** | 30 min | `publish_tick.bat` → `publish_github.ps1` (export → `build_site.py` → `make_maps.py` → push) | `docs/`, the public repo | `runtime/publish-tick.log` |
| **Beops_Legal** | weekly | `legal_tick.bat` → `legal_capture.py --recheck-collectors` | `research/evidence/legal/`, `research/08-provenance/LEDGER.jsonl` | `runtime/legal-tick.log` |

A person stops the mind by creating the file `data/live/derived/mind/PAUSED`; a source is paused by
`data/live/receipts/<SID>/PAUSED` (the collector writes one itself after a 429).

## 3. `tools/` — the machines

| file | what it is | its tests |
|---|---|---|
| `collect_daemon.py` | the collector: gate (newest ledger line per source), fetch, parse (`sepa_hvd`, `sensor_community`, `parking`, `rss`, **`city_listing`** new today), dedupe, receipts, export to `public/live-snapshot.json` (with the mind's thoughts re-checked for ekavica at export) | `research/test_collect_daemon.py` |
| `organ_news.py` | the news-sorter (0.1.1): category, Belgrade yes/no, zones from the gazetteer; binds answers to headlines by echo (C-013) | `research/test_organ_news.py` |
| `organ_mind.py` | the mind (0.3.5): digest → organelles → three thinkers → Serbian voice → validator; `step` (drip), `run`, `score`, `status`, `check`, `retract`, `voice-bench` | `research/test_organ_mind.py` |
| `legal_capture.py` | permission evidence before any collection; `--recheck-collectors` weekly | — (its output is the ledger) |
| `build_site.py` | generates `docs/index.html` from the registry, the provenance index, the corrections and the last snapshot; the landing page is the live stage (`monolog.html` in a frame) | — |
| `make_maps.py` | Maps 1–4 (coverage, instruments, last 24 h, people) as SVG into `docs/` | — |
| `fetch_basemap.py` · `fetch_static.py` | the base map (Natural Earth, S98) and the static context layers (`research/STATIC_LAYERS.json`; Kontur population first) | `research/test_basemap.py` |
| `publish_github.ps1` | the export: copies what is public (see §6), commits, pushes | — |
| `register_tasks.ps1` + `*_tick.bat` | the five clocks of §2 | — |
| `build_provenance_index.py` | regenerates `research/08-provenance/INDEX.md` from the ledger | — |

Run all tests with `npm test` (104 today). A change to any of these files goes with its test
in the same commit — that rule caught a real regression today (§9).

## 4. `research/` — the knowledge

```
research/
├── SOURCE_REGISTRY.json   205 records S01–S208, every source with status and verdict
├── COLLECTORS.json        the 26 sources the collector polls (each has a capture)
├── ORGANS.json            the organs' register: models, licences, cadences, measurements
├── STATIC_LAYERS.json     static/semi-static context layers (Kontur first)
├── MODEL_CANDIDATES.json  local models researched for organelles and voices
├── COLLECTION_PLAN.json   the earlier collection plan (history)
├── README.md              THE INDEX of documents — unlisted = does not exist
├── 01-programme/          intent: programme, hypotheses, place register, zones (internal)
├── 02-senses/             what the city offers: senses rounds, layers, device discovery
├── 03-models/             MIND_ARCHITECTURES, MIND_0.3.5 (today), GEOPARSING, model catalogue
├── 04-bibliography/       the two bibliographies
├── 05-design/             UI concepts; studies/monolog-puls.html is THE stage
├── 06-paper/              working document v1.1, pre-paper, methods audit (internal)
├── 07-legal/              COLLECTION_LEGAL_FRAME, NEWS_AUDIT_2026-09-09 (today), legal sorts
├── 08-provenance/         LEDGER.jsonl, INDEX.md, EDGE_CASES (E-001–013), CORRECTIONS (C-001–013)
├── evidence/              IMMUTABLE: legal/<SID>/<stamp>/ captures, probe snapshots
├── observations/          IMMUTABLE: the OBS-001 pilot
├── _trail/ · _scratch/    how the work went (internal) · throwaway
└── test_*.py · probe_*.py · collect_permitted.py · write_izvestaj.py
```

Where to look for a question:

- *Is source X allowed?* → `08-provenance/LEDGER.jsonl` (newest line for its SID wins), the bytes in
  `evidence/legal/<SID>/`, the rule in `07-legal/COLLECTION_LEGAL_FRAME.md`, the doubt in
  `08-provenance/EDGE_CASES.md`.
- *What do we know about source X?* → its record in `SOURCE_REGISTRY.json` (dated fields such as
  `news_audit_2026_09_09`, `measured_2026_09_09` hold the history).
- *What did the system get wrong?* → `08-provenance/CORRECTIONS.md`, and the honest-verdict
  paragraph of every commit message (`git log`).
- *How does the mind work / which model / under what licence?* → `ORGANS.json` (`mind`, `news-sorter`),
  `03-models/MIND_ARCHITECTURES_2026-09-09.md`, `03-models/MIND_0.3.5_EKAVICA_AND_THE_BODY_2026-09-09.md`.
- *What is the paper?* → `06-paper/PRE_PAPER_CONFERENCE_2026-09-09.md` (+PDF) and the working
  document v1.1 (PDF) beside it.

## 5. `data/live/` — the memory (never in git)

```
data/live/
├── receipts/<SID>/<slot>.json   one receipt per fetch slot, failures included
├── rows/<SID>/<YYYY-MM>.jsonl   the rows, append-only; _seen.json = dedupe set
├── raw/<SID>/<slot>.<ext>.gz    raw bodies only where store_raw=true (never news)
└── derived/
    ├── news/<YYYY-MM>.jsonl     the sorter's estimates + receipts/
    └── mind/
        ├── <YYYY-MM>.jsonl      every utterance: thought / rejected / organelle / retracted
        ├── notebook/<entity>.jsonl   what each entity is told about its past
        ├── claims.jsonl         claims and how they settled (scoreboard: `organ_mind.py status`)
        ├── digests/ · receipts/ the facts each step saw; one receipt per step
        ├── context.json         the drip's working context
        ├── voice_bench/         renderings of candidate voice models, for reading
        └── PAUSED               create it to stop the mind
```

Rule: nothing here is ever edited or deleted; a wrong row is answered by an appended retraction
(`organ_mind.py retract …`) and the export skips it.

## 6. `public/` → `docs/` → the site

- `public/live-snapshot.json` — written by the collector's export every 5 min: the last window of
  every source, the silences, the sorter's rows, the mind's **thoughts (state thought only,
  Serbian re-checked for ekavica at export)**, receipts and the scoreboard. `public/basemap-belgrade.json`
  and `public/context-population.json` are the base map and the Kontur layer.
- `docs/` — generated by `build_site.py` + `make_maps.py` at every publish: `index.html` (the landing:
  the live stage in a frame, sources, permissions, errors, how it works), `monolog.html` (a copy of
  the study), `traka.html`, the four maps, the snapshot and layers. **Never edit `docs/` by hand.**
- The export (`publish_github.ps1`) copies to the public repo everything **except**:
  `research/06-paper`, `research/_trail`, `research/01-programme` (placeholder READMEs stand in their
  place), `research/evidence` (only hashes and the ledger travel), `data/`, `runtime/`, `.env*`,
  `secrets.*`. The public history was reset to one orphan commit on 9 September; PDFs are not in it.

## 7. `runtime/` — logs and scratch (ignored by git)

`collect-tick.log`, `organ-tick.log`, `mind-tick.log`, `publish-tick.log`, `legal-tick.log` — one
block per tick, newest last. `verify_all.py` prints the state of everything in one screen (tasks,
last receipt and rows per source, the organs' last receipts, the last drops of the mind, the
snapshot's age, git). `ollama_diag.py` measures the model daemon. The `rvNN.bat`, `rvNN_msg.txt`
and `npmtest_rvNN.log` files are the day's hands commands and their test logs — safe to ignore.

## 8. What changed today, and where it landed

| change | where |
|---|---|
| Ekavica as law: guard, voice with retry, no English on the Serbian page, export re-check | `tools/organ_mind.py`, `tools/collect_daemon.py`, `research/05-design/studies/monolog-puls.html`; note `research/03-models/MIND_0.3.5_…md` |
| One main model: qwen3.5:4b thinks and voices, Skeptic and sorter on qwen2.5:1.5b; the body measured | `research/ORGANS.json` (`mind`, `news-sorter`), `runtime/ollama_diag.py` |
| The mind at the top of the stage; stale numbers blanked in the conversation context | `monolog-puls.html`, `tools/build_site.py`, `tools/organ_mind.py` |
| News audit: 3 corrections, 14 new records (S195–S208), 3 official routes, MUP refused | `research/07-legal/NEWS_AUDIT_2026-09-09.md`, `SOURCE_REGISTRY.json`, `COLLECTORS.json` (26), `08-provenance/EDGE_CASES.md` E-011–E-013, `LEDGER.jsonl`, `evidence/legal/` |
| The City's own listings parsed (Beoinfo S208, transport notices S15) | `collect_daemon.py` `city_listing`, `test_collect_daemon.py` |
| Weekly re-capture of permissions | `tools/legal_capture.py --recheck-collectors`, `tools/legal_tick.bat`, task `Beops_Legal` |
| Site: internal documents out of the site and the public repo; landing page = live stage | `tools/build_site.py`, `tools/publish_github.ps1` |

Commits of the day, in order: `bfe3205` site restructure · `56a754a` mind 0.3.5 · `c7c8827` one main
model · `9977eba` news audit · `2e6acfc` recheck retry · `1eeb9b5` mind at the top (carried a stale
sorter — see §9) · `4e5bf2d` City listings · `0240f1c` sorter restored · `7382a0f` stale numbers +
lexicon · `f8a3ea7` sorter on 1.5b.

## 9. Honest verdict on the state of the folder

- **Verified today** (`runtime/verify_all.py`, 11:07 UTC): five tasks ready with Last Result 0;
  26 polled sources, every new one with receipts and rows; snapshot 1.4 min old; 104 tests green;
  the public site carries the new stage and no ijekavian or Croatian word on the Serbian page.
- **What the layout still owes you.** `research/README.md` is long (the whole history of the
  work is in it) — the map you are reading is the short way in, and the README should one day
  point to it first. `research/` still mixes documents with code by design (the test runner
  resolves paths from there); a `research/code/` move would need every `.bat` and the runner
  changed together. The public copy of `research/README.md` links into folders the export
  replaces with placeholders — not broken, just blunt.
- **The one regression of the day was mine**, caught by the tests within the hour: a file edited
  from an old folder snapshot instead of the working tree. The rule is now written down where
  the next mind reads it: stage from the PC immediately before editing, never from a snapshot.
