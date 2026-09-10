# Corrections

*Every time this system produced a false statement, what it said, and why.*

This file is append-only. Nothing is removed from it, including the entries
that are embarrassing. A provenance system that hides its own failures is
worth nothing, because the one thing it is supposed to prove is that it does
not quietly say things that are untrue.

---

## C-001 — `legal_capture.py` reported a total failure as a permission

**When** 2026-09-06, 00:21 UTC — the very first run of the tool.

**What it said.** Seven captures (`S134`–`S140`) each wrote:

```json
"allowed_for_us": true
```

**What was actually true.** Every single HTTP request in all seven captures had
failed. The Python interpreter in use had no usable CA bundle, so every
`https://` fetch raised:

```
URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED]
certificate verify failed: unable to get local issuer certificate>
```

Zero bytes were retrieved. Every `status_by_url` value was `null`. Every
`robots.txt` was unreadable. The captures contained no evidence whatsoever.

**The defect.** The verdict was computed as:

```python
"allowed_for_us": all(
    (p["allowed_for_us"] is not False)
    for v in verdicts.values() for p in v["paths"].values()
)
```

When `robots.txt` cannot be read, `robotparser` yields `None`, not `False`.
`None is not False` evaluates to `True`. So the boolean collapsed two very
different states — *permitted* and *unknown* — into one, and chose the
flattering one. An empty set of paths would also have returned `True`, since
`all([])` is `True`: a source with no paths checked at all would have been
reported as permitted.

**Why it matters more than an ordinary bug.** This tool exists for exactly one
purpose: to make it impossible for the project to claim a permission it does
not have. On its first run it manufactured seven such claims. Had this gone
unnoticed for a week, seven sources would have been collected, published, and
cited — with a stored "proof" file that contained nothing but failures.

**The fix**, in `tools/legal_capture.py`:

1. The verdict is now three-state — `True` / `False` / `None` — computed as:
   `False` if any path is explicitly disallowed; `None` if any `robots.txt` was
   unreadable, any URL unreachable, any path verdict unknown, or no paths were
   checked at all; `True` only otherwise.
2. Each capture now records `capture_ok`, `fetch_failed_urls`,
   `robots_unreadable_origins`, and `tls_trust` — the provenance of the
   *capture's own* trust decision.
3. TLS is built from `truststore` (OS store) or `certifi`, and there is no
   unverified mode. A capture that cannot verify who it is talking to fails.
4. `tools/build_provenance_index.py` renders `None` under **Evidence
   incomplete**, a section that did not exist before, and which states plainly
   that an unknown is not a permission.

**The seven bad captures are not deleted.** They remain at
`research/evidence/legal/S13*/20260906T0021*Z/`, and their ledger lines remain
in `LEDGER.jsonl`. They are honest records of a failed capture; only the
verdict was wrong, and the verdict is now overridden by the later, successful
capture of the same source. The generator uses the newest capture per source,
so the index shows the truth — but the wrong line stays visible in the ledger,
which is the point.

**Generalisation, now a rule in `README.md` and `CONTRIBUTING.md`.** In this
project, *unknown* and *permitted* are never the same value. Wherever a check
can fail to run, its failure must be representable, and the representation must
not be the permissive one. Any boolean that answers a question of the form
"may we?" is suspect: if it cannot also say "I could not tell", it will
eventually say yes when it means nothing at all.


---

## C-002 — Ids allocated to sources that were already registered

**When** 2026-09-06, within the hour of writing the rule that ids are permanent
and one source has exactly one id.

**What happened.** `S134`, `S136` and `S137` were allocated to JP Putevi
Srbije, Overture Maps and Sensor.Community, which were already registered as
`S57`, `S95` and `S04`. The registry was not consulted before the numbers were
handed out. Left standing, the project would have carried two records of the
same source, each with its own permission evidence, and no way to tell which
was current.

**The fix.** Not a note in a document — a check in the tool.
`tools/legal_capture.py` now loads `SOURCE_REGISTRY.json` before doing
anything, refuses an id that is not registered unless `--new-source` is passed,
and refuses a URL whose host already belongs to another source, printing that
source's id and name. Both refusals were verified against the real registry.

The three wrong captures remain on disk and in the ledger. The correct captures
were made under `S57`, `S95` and `S04`.

---

## C-003 — Data taken before the permission was captured

**When** 2026-09-06.

**What happened.** Queries were run against `query.wikidata.org/sparql` and
`overpass-api.de/api/interpreter` and their results reported — 219 Belgrade
monuments with coordinates, 1 409 bridge ways, 9 named bridges, 9 stadiums with
capacities, 137 venues, the Singidunum record — **before** `legal_capture.py`
was run on either. When it was run, both were found to disallow the queried
path for `User-agent: *`.

**Why it matters.** Rule 1 of `README.md` in this folder is *evidence before
collector*, written earlier the same day. It was inverted within hours by its
author. Had the capture come first, the `Disallow` would have been seen before
a single query was sent, and the decision in `EDGE_CASES.md` E-009 would have
been taken in advance instead of after the fact.

**What was done.** Both sources moved to **Decision required** in `INDEX.md`;
no collector was built on either; the figures are marked in
`SOURCE_REGISTRY.json` and in E-009 as obtained before permission was checked.
They are not deleted — deleting them would hide the failure, and the numbers
themselves are true. They are simply not clean, and they say so.

**Generalisation.** The order of operations is not a preference. Running the
capture takes twenty seconds and answers a question that cannot be answered
afterwards.

---

## C-004 — The verdict engine over-permitted, by standard

**When** 2026-09-06, found while capturing transit.land.

**What it said.** `allowed_for_us: true` for
`https://www.transit.land/feeds/f-sry-cityofbelgradesecretariatforpublictransport`.

**What is true.** That path is disallowed. transit.land publishes:

```
User-agent: *
Allow: /feeds
Disallow: /feeds/
```

**The defect.** `urllib.robotparser` returns the **first** matching rule.
RFC 9309 §2.2.2 requires the **most specific** — the longest — match to win,
with `Allow` winning only a tie. `Allow: /feeds` is shorter than
`Disallow: /feeds/` and comes first, so the standard library answered
"allowed" where the standard says "disallowed".

This affects every site that writes an `Allow` before a longer `Disallow`, and
it fails in the one direction this tool must never fail in: it clears us when
we are not clear.

**The fix.** `tools/legal_capture.py` now implements RFC 9309 matching itself —
longest match, `*` and `$` wildcards, `Allow` wins ties, most specific
user-agent group selected — runs **both** engines, and takes **the stricter of
the two, always**. Each path records `urllib_robotparser`,
`rfc9309_longest_match`, the `matched_rule`, and an `engines_disagree` flag, so
a disagreement is visible rather than resolved silently. Re-capturing
transit.land now returns `allowed_for_us: false` with the disagreement flagged
on exactly that URL.

**Also found in the same pass.** `Content-Signal` was being read only from HTTP
response headers. It is published **inside `robots.txt`**, which is where
Cloudflare puts it and where UNESCO and transit.land both carry it. The parser
now reads it from the robots body, per user-agent group, and the index applies
it by purpose rather than as a blanket yes or no — see `EDGE_CASES.md` E-010.

**Generalisation.** A dependency that answers a safety question is not
therefore correct. Where the standard is short enough to implement, implement
it, run both, and take the stricter. Where it is not, at least know which
reading your library implements.

---

## C-005 — "Take the stricter" turned one tool's bug into a refusal

**When** 2026-09-06, found while clearing the capture backlog.

**What it said.** `S42`, the Serbian Public Procurement Portal
(`jnportal.ujn.gov.rs`), was recorded as **refused**.

**What is true.** That site's `robots.txt` contains

```
Allow: /$
```

RFC 9309 reads `$` as an end-of-path anchor, so `Allow: /$` matches exactly the
root and, at two characters, beats a bare `Disallow: /` at one. The correct
verdict is **permitted**. Our own RFC 9309 engine got it right and reported
`matched_rule: allow: /$`.

**The defect.** `urllib.robotparser` does not implement the `$` anchor, so it
answered *disallowed*. The verdict then ran through the rule introduced in
C-004 — *take the stricter of the two engines, always* — which took urllib's
error and published it as a refusal.

**Why the earlier rule was wrong.** C-004 found urllib **over-permitting**
(transit.land, where it ignores longest-match) and concluded "always be
stricter". That was the wrong generalisation of a right observation. The
correct lesson was **urllib is unreliable**, and it is unreliable in *both*
directions: it over-permits where it ignores longest-match, and under-permits
where it ignores `$`. A rule that always leans one way converts one class of
its errors into silent refusals — losing sources that are open, and doing it
invisibly, which is the same failure mode as C-001 pointed the other way.

**The fix.** When the two engines disagree, **neither is trusted and the
verdict is `unknown`** — in both directions. Unknown never renders as a
permission, and it surfaces for a human decision instead of being resolved
silently by a heuristic. A disagreement between two implementations of the same
standard is not a fact about the site; it is a fact about the tools, and it
belongs in front of a person.

**Generalisation.** A safety rule that always resolves ambiguity the same way
is not conservative, it is just biased. Where two independent checks disagree,
the honest output is *we do not know*, and the disagreement itself must be
visible.

---

## C-006 — A valid certificate reported as unverifiable, and the pilot it touched

**When** 2026-09-06, found when the backlog capture returned `unknown` for
`S10`, `parking-servis.co.rs` — **the source of the OBS-001 parking pilot that
this project ran the day before.**

**What it said.** `robots.txt unavailable ... CERTIFICATE_VERIFY_FAILED:
unable to get local issuer certificate`, so the verdict was `unknown`, and the
collector's gate would have refused it.

**What is true.** The site's certificate is fine. Read directly:

```
SUBJECT   CN=*.parking-servis.co.rs, O=JKP Parking servis Beograd, C=RS
ISSUER    CN=Sectigo Public Server Authentication CA OV R36
VALID     2026-02-26 .. 2027-02-27
CHAIN     builds, 3 elements, to Sectigo Public Server Authentication Root R46
```

The machine's own trust store accepts it. The **`certifi` bundle shipped with
the Python this project runs on does not carry that Sectigo root**, so
verification failed for a chain that is valid.

**Why it matters beyond one source.** The failure was in the safe direction —
under-trusting, never over-trusting — but it silently excludes open sources on
a criterion that has nothing to do with permission, and it did so for the very
source of the project's flagship observation. Three further hosts were
affected: `registar.ratel.rs`, `www.putevi-srbije.rs`, `opendata.stat.gov.rs`.

**And the honest part about OBS-001.** The pilot collected thirteen hours of
parking occupancy from this source on 2026-09-05, **before** the rule "evidence
before collector" existed, and the source's permission capture has only now
been made. It came back clean once the trust problem was fixed. But the order
was wrong, as in C-003, and it is recorded rather than tidied away: the
observation stands, the sequence does not.

**The fix.** `tools/export_ca_bundle.ps1` exports this machine's own trusted
roots to `data/ca-bundle-windows.pem` (121 certificates), and
`legal_capture.py` prefers that bundle over `certifi`. Verified: all four
previously failing hosts now verify, at TLS 1.2 and 1.3.

**Why a file and not a library.** The trust decision is now something we can
hash, commit, diff and point at. "Whatever certifi happened to ship" is not an
auditable statement about what the project trusts; a PEM in the repository is.

**Generalisation.** A verification failure is not evidence about the thing
being verified until the verifier itself has been checked. Every "unknown" in
this system should be read twice: once as a statement about the source, and
once as a possible statement about our own instruments.

## C-007 — An EMF file was associated with a NetTest capture

Date: 2026-09-06. Discovered during the device/data wave.

The immutable file `research/evidence/S155/20260906T025246Z/9314c9_open-data-2-2.json`
contains the Belgrade EMF drive campaign (7,780 measurement rows). Its original
manifest says S155 and cites a NetTest-host capture. The actual resource is
`https://emf.ratel.rs/drive-test-open-data/open-data-2-2.json`, belonging to S158.
An ID-level gate did not establish that every collected URL was covered by the
capture's exact hosts/paths. The original evidence and manifest remain unchanged.

Today's exact-route captures under S158 record access evidence prospectively;
they do not retroactively validate the old sequence. The canonical association
and independent hash/count check are in
`research/evidence/device-discovery-20260906/DRIVE_BG_QA.json`.
Also, S155's NetTest files named JSON/CSV/XML were HTML responses, so their
extensions do not establish measured speed data. No failed payload is promoted.

Open engineering follow-up: make collection eligibility bind the exact URL and
validate expected media/schema, not only a source ID. No collector behavior was
changed in this wave. Every new batch was checked against its exact capture.

## C-008 — Access-check wording overstated legal clearance

Date: 2026-09-06. User steering: preserve sorting under the existing legal frame.

The generated index called successful robot/header checks "permitted" and the
captured signals "the permission". Those checks do not resolve retention,
cumulative extraction, database rights or redistribution, as E-002 through E-004
already state. The generator now labels them **access checks passed**, links the
existing frame and renders source-specific legal-review categories separately.
The access-decision algorithm and historical captures were not rewritten.

The fixed EMF endpoint returned its whole 225,410,096-byte archive in one request;
the existing collector's 250 MiB cap was technically bounded but much larger than
a discovery sample. Its receipt, source labels, duplicate rows and unexplained
values are preserved. Future discovery needs a predeclared byte budget and a
documented narrower route; do not poll this archive as a current sample. The exact
resource's licence and public-release conditions are reviewed in
`research/07-legal/DEVICE_DATA_LEGAL_SORT_2026-09-06.md`.


## C-009 — A captured 403 is not successful access or licence text

Date:2026-09-06. S190 identified article and robots requests returned403. Existing capture logic treated the robots4xx as no stated restrictions and returned an allowed access-check result. Stored terms_1.html is a401-byte error response, not the article or its licence. An offline supplemental manual review at research/evidence/legal/S190/20260906T113853Z holds collection, references the original capture and makes zero new network requests. Original bytes and earlier ledger entry remain unchanged. General HTTP/schema eligibility needs a separate engineering change; it was not silently fixed in this research wave.

Also, the page168 request planned as device metadata included actual chart literals. Its1681 timestamped field values are now recorded as received data, with exact-page reuse scope unresolved. The dataset516 metadata response exceeded2MiB and was not saved or retried. For S191, CC BY4.0 and no active embargo coexist with restricted file access; download-stat volume is not file size. See the follow-up legal review.


## C-010 — The index called three permitted sources refusals, on the strength of a search-engine header

**When** 2026-09-06 (first generation of `INDEX.md`), found 2026-09-08 during an external review.

**What it said.** `INDEX.md` listed under *Do not collect — these said no*:

| id | source | "what said no" |
|---|---|---|
| S120 | Kontur Population Dataset (H3) | `x-robots-tag: index, follow` |
| S169 | keep.eu Interreg projects | `x-robots-tag: noindex` |
| S74 | Gradnja.rs RSS | `x-robots-tag: noindex, follow` |

**What was actually true.** All three captures record `allowed_for_us: true`
in `LEDGER.jsonl`: `robots.txt` was served and permitted our agent on every
path, every URL answered 200, and no `Content-Signal` was present. Kontur's
dataset is CC BY 4.0 and its own page says commercial use is allowed
(`02-senses/HISTORY_AND_SPATIAL_BASE_2026-09-05.md`). `index, follow` is the
most permissive value the header can carry. `noindex` tells a search engine not
to list a page; it says nothing about whether the page may be read, and it is
not a machine-readable reservation under Article 4 of Directive 2019/790 (the
machine-readable forms in use are TDMRep `TDM-Reservation: 1`, the IETF
`Content-Usage` / AI-preferences vocabulary, and `X-Robots-Tag: noai`).

**The defect.** `legal_capture.py` stores *every* value of the five signal
headers under `opt_out_signals_seen`, which is right — the record must be
complete. `build_provenance_index.py` then tested only whether that dict was
non-empty:

```python
elif (last.get("allowed_for_us") is False) or last.get("opt_out_signals_seen") or signal_no:
    forbidden.append((sid, caps))
```

Presence of a header was treated as the content of a refusal. The tool that
exists so the project never claims a permission it does not have also claimed
three refusals that were never made — and `CLOSED_LAYER_2026-09-06.md` counted
them in its "10 refused".

**Why it matters.** Conservative is not the same as true. A false refusal is a
false statement about a publisher — Kontur was recorded as having "said no" to a
project it explicitly welcomes — and it silently removes the only open
population layer in H3 from v1. A provenance record is worth exactly as much as
its false positives and false negatives together.

**The fix**, in `tools/build_provenance_index.py`: a function
`header_refusals()` keeps only signals that refuse *reading or mining*
(`X-Robots-Tag` containing `noai`/`noimageai`; `TDM-Reservation: 1`;
`Content-Usage` denying `ai` or `tdm`). Everything else stays in the capture
and in the ledger untouched. Regenerated index: 153 access checks passed,
7 refused, 4 awaiting decision, 3 incomplete, 25 undocumented — exactly the
three rows moved and nothing else. The captures and ledger lines are unchanged.

**Generalisation.** A stored signal and a verdict on that signal are two
different things. Storing everything is correct; deciding on "anything stored"
is not. Every classifier over evidence needs a test with a permissive header in
it, not only tests with refusals.


## C-011 — The pilot's scheduled task did not delete itself, and ran hourly for three days after the pilot closed

**When** 2026-09-05 22:55 UTC (the intended self-delete moment) to 2026-09-08 19:30 UTC; found 2026-09-08 during an external review.

**What it said.** `tools/obs001_tick.bat` was described in OPAZANJA/LOG and in
project memory as "self-deleting after the last permitted slot". OBS-001 was
closed at 10 of 13 on 2026-09-05 and the log recorded "Windows task disable
denied; no privilege bypass".

**What was actually true.** `schtasks /query /tn Beops_OBS001` on 2026-09-08
showed the task *Enabled*, *Ready*, repeating every hour, last run 21:30 local
the same day. `runtime/obs001-tick.log` holds 79 ticks; the 69 after the pilot
each report `"state": "closed", "network_requests": 0`. The recorder's own
cutoff held — not one request left the machine — but the schedule did not.

**The defect.** The self-delete line is
`if %NOWUTC% GTR 202609052255 schtasks /delete ...`. `cmd.exe` compares `IF`
operands as 32-bit signed integers when both parse as numbers; a twelve-digit
UTC stamp overflows and saturates on both sides, so the two values compare as
equal and `GTR` is never true. The line never executed, which is why the log
never showed either SUCCESS or an error.

**The fix.** The task was deleted on 2026-09-08 (`schtasks /delete /tn
Beops_OBS001 /f` → SUCCESS, query afterwards → no such task). The batch file is
kept unchanged as evidence. Rule: a schedule that is meant to end has its end
verified by `schtasks /query`, not by the script that was meant to end it — the
same rule as 2026-09-05, from the other side: *configuration is not execution,
and a self-delete is not a deletion until the scheduler says the task is gone.*


## C-012 — The first organ run used a cloud-hosted model, against the register it had just been given

**When** 2026-09-08 21:17 UTC.

**What happened.** `tools/organ_news.py run` picked `qwen3.5:cloud` from the local daemon's model
list and made ten calls (all answered HTTP 429, nothing derived). The register entry written minutes
earlier said `allow_cloud: false` — "no headline leaves the machine" — and the code that enforces it
(`pick_model` skipping names ending in `:cloud`) was written in the same hour. The file on the body was
still the previous version: the cloud copy and the body copy differed (md5 `04f9b225` vs `49cdde04`)
although the transfer had reported success.

**What left the machine.** Ten prompts containing up to 200 public news headlines (title, no body),
rejected with 429 by the hosted endpoint. No observation row, no personal record. Public headlines
are the least sensitive text the project holds; the rule still says they must not leave, and it was
broken.

**The defect.** Two: (1) a model whose name marks it as hosted was eligible at all — a rule that lived
in the register but not yet in the code on the body; (2) the deployment path (cloud → body over a
mounted transfer) could report "written" for a file whose content did not change, and nothing
compared hashes before running. The organ's own test suite failed on the body for exactly this
reason (`test_cloud_models_are_skipped_unless_allowed`) — and the run was started anyway, in the same
command, after the failing test. **A failing test that does not stop the next command is decoration.**

**The fix.** Code and register redeployed under fresh paths and verified by hash on the body before
any further run; the run command now stops when `npm test` fails (`&&` instead of `&`);
`tests/test_organ_news.py` covers the cloud skip. Rule for every deployment from the cloud to a body:
**compare the hash on the body with the hash you meant to send, before the first command that
depends on it** — the same rule as C-011 from the other side: a transfer report is not a transfer.


## C-013 — The first local organ run bound answers to the wrong headlines

**When** 2026-09-08 21:35 UTC, the first run of `news-sorter` on a local model (qwen2.5:3b, batch of 5).

**What it said.** "Direktorka OŠ Isidora Sekulić: Ovo je najmodernija škola u Srbiji" was filed as
`saobracaj`, zone Vračar (score 1.0), event time "sutra" — the answer that belongs to the next
headline, "Deo Vračara sutra bez vode od 8.30 do 18.00". Every item in the batch was shifted by one;
the first headline got "no item".

**What was true.** The model numbered items from 1 while the prompt numbered from 0, and the binding
used the index alone. A 3-billion-parameter model cannot be trusted to keep an index; it can be
trusted to copy a string.

**The fix** (organ 0.1.1): the schema requires the model to echo the headline; binding is by the echo
first and by the index only as a fallback, and each derived row says which (`bound_by`). The ten
wrong rows stay in `data/live/derived/news/2026-09.jsonl` as organ 0.1.0 output — derived rows are
append-only like everything else — and the organ's version in every row is what tells them apart.
Rule: **a model's answer is bound to its input by content, never by position.**

## C-014 — The publish task never published: a batch that ran another batch and never came back

**When** 2026-09-08 20:05 UTC (the task was registered) to 2026-09-09 12:53 UTC (found), so
roughly seventeen hours and about a hundred scheduled runs.

**What it said.** `tools/publish_tick.bat`, the scheduled task `Beops_Publish`, is documented in the
repository and on the public page as the thing that keeps the site current: export, report, push.
The task's own status was `Ready`, its last result `0`, and `runtime/publish-tick.log` had a line for
every run. Everything a check would look at said the site was being published on a schedule.

**What was actually true.** The batch's last three lines were:

    C:\Svemir\python.cmd ... collect_daemon.py export >> runtime\publish-tick.log 2>&1
    C:\Svemir\python.cmd ... collect_daemon.py report  >> runtime\publish-tick.log 2>&1
    powershell ... tools\publish_github.ps1            >> runtime\publish-tick.log 2>&1

`python.cmd` is itself a batch file. In `cmd.exe`, a batch file that runs another batch file **without
`call`** transfers control and never returns: the first line ran, and the second and third were
skipped on every single run. The log proves it — each tick wrote the export's one line of output and
nothing else. The exit code was 0 because the export succeeded; the public site was published only
when a person (or this session) ran `publish_github.ps1` by hand. The task ran a hundred times and
published nothing, and its receipts said it was fine.

**The fix.** `call` before every `python.cmd` in all five tick batches — including the four where it
is currently the last line and therefore harmless, because the trap is sprung by the next person who
appends a line. The comment naming this correction sits in each file.

**Rule: an exit code of 0 is evidence that something finished, never evidence that it happened.** A
scheduled job that produces an artefact must be checked by the artefact — here, the timestamp of the
published commit — and not by its own status, its own log line, or its own return code. The same test
the project applies to the city applies to the project: a reception is not a measurement.

## C-015 — The gate was reported by its refusal count, which never answered the question

**When** From the first published monologue until 2026-09-09 16:34 UTC, when the same set was run
against a hardened validator.

**What it said.** The mind's honesty was reported everywhere — on the site, in the pre-paper, in the
README — as a refusal count: 49 of 176 drops refused, later 102 of 222 utterances, 45.9 %. The number
was true and was published in good faith as evidence that the gate works.

**What was actually true.** A refusal count says how often a gate fired. It says nothing about whether
it fired at the right things, and nobody had asked. `research/GATE_ADVERSARIAL_SET.json` — 44
hand-labelled utterances over one fixed digest, 36 of them unsupportable by a careful reader of that
digest — was run against `tools/organ_mind.validate` and `.validate_voice` at organ version 0.3.5.
**Seventeen of the thirty-six passed.** A false-accept rate of 0.472: the arithmetic checks caught
every attack made of tokens and missed almost every attack made of meaning. Among the seventeen the
gate would have published: a value with no measurement time presented as the present state; silence
read as nothing having happened; a similarity turned into a confirmed event; a cause the record does
not carry; a unit off by a factor of a thousand; guidance to residents; and a sentence attributed to
a state agency that the agency never said.

**The fix.** Organ version 0.4.0 adds semantic guards, each aimed at a failure the set caught: a
number must come from a fact the sentence actually cites rather than from anywhere in the digest; a
fact flagged as having no measurement time may not be spoken of in the present tense; a silence fact
may not be followed by an assertion that nothing happened; the units of the cited facts bound the
units the sentence may use; causes, advice, totality claims, out-of-window superlatives and
similarity-as-confirmation are refused; and a Serbian rendering may no longer introduce a number the
English it renders does not contain. Fourteen of the seventeen close. **Three do not**, and are named
in the paper rather than hidden: number rebinding inside a correctly cited fact, measurement-time
drift, and a Serbian rendering that is arithmetically identical and means the opposite. They need a
reader, not a rule. `research/test_gate_eval.py` pins all of it: a future edit that reopens one of the
fourteen fails the suite, and one that closes one of the three fails it too.

**Consequence for every number already published.** The gate changed on 9 September 2026. Refusal
counts recorded before that date and after it are measurements of two different gates and **must not
be compared**; the paper says so, and the receipts carry `organ_version` so any reader can separate
them.

**Rule: a safety mechanism reported by how often it acted has not been evaluated.** The question is
not how many utterances a validator refused but how many it should have refused and did not. Until
that has been measured against a set someone tried to break it with, the mechanism is a
demonstration, and calling it anything else is the same error as trusting a receipt instead of the
artefact (C-014) — one level up.

## C-016 — The pulse map was empty on a phone, and the frame that held it was 3 900 px tall

**When** From the day the monologue was embedded in the front page until 2026-09-09 18:00 UTC, when
it was reported from a phone with a screenshot.

**What it said.** The section is titled *Puls — kruži samo kad je instrument stvarno pročitan*, and on
a desktop it draws Belgrade with a ring around every instrument at the moment it is read. The offline
suite passed, the frame protocol worked, both languages were present, and nothing in the repository
suggested a problem.

**What was actually true.** On a 412 px phone the map was a blank grey box about two thousand pixels
tall. One CSS declaration caused it: `body.embedded .map .cv{min-height:52vh}`. The parent sizes that
frame from the height of its own content, so a child asking for 52 % of the viewport was asking for
52 % of itself. It settles rather than diverges — H = 1873 + 0.52H — at **3 900 px**, which is exactly
what was measured. The map's box became 2 027 px.

That alone would have been ugly. What made it *empty* was a second fault, in the canvas: the resize
compared only the width against the backing store — `if(cv.width!==Math.round(w*dpr))` — so when the
box grew taller the bitmap stayed 589 px while the projection kept drawing into a 2 027 px space.
Everything below the old height fell outside the bitmap, and what remained visible was the margin
above the city. A map of Belgrade with no Belgrade in it.

Two further defects of the same family were found while measuring, in frames that had never been
looked at below 900 px: the ribbon's source header and the data page's header both kept a desktop
two-column grid, so a source title wrapped one word per line and ran underneath its own note, and a
sparkline had 162 px left to draw twenty-four hours in.

**The fix.** The map is sized from the frame's WIDTH (`clamp(220px,72vw,420px)`) — the one dimension
the parent sets by layout and never reads back, so the loop cannot close. The canvas resize compares
both dimensions. The ribbon and the data page collapse their headers and narrow their label columns
below 560 px. Measured before and after, at 412 px: frame 3 898 → 2 134 px, map box 2 027 → 261 px,
canvas bitmap 589 → 261 px, and the map draws.

**Rule: an artefact that is only ever read as text has only ever been half tested.** Two tests are
added to `research/test_render.py` — no descendant of an embedded frame may be sized in `vh`, and a
guarded canvas resize must guard both dimensions — and both were checked against the defect itself
before being committed: reinstating the old declaration makes the suite fail. But neither would have
found the two-column headers, because a text test lays nothing out. `research/measure_render.js` now
opens the built page at five widths in a real browser and fails on a runaway frame, a canvas whose
bitmap disagrees with its box, a page that scrolls sideways, or a frame that loaded no text. It needs
a browser, so it is deliberately outside `npm test`, which stays dependency-free, and is run by hand.

**And the honest part: this was found by a person looking at a screen, again.** C-014's rule was that
a scheduled job must be checked by its artefact rather than its own report. The same applies one level
out: a site must be checked by what it looks like, not only by what it contains.

## C-017 — Four polled sources carried a status the registry reserves for sources it never verified

**When** From the day each of them entered the collector's list until 2026-09-09 18:30 UTC, when a
test was written to assert the thing everyone assumed.

**What it said.** `research/SOURCE_REGISTRY.json` gives every source a status, and the public page
renders those statuses as the audit of what this project reads and on what footing. Four of the
twenty-eight polled sources carried a status whose own legend says the opposite of being read:
**S15** (City transport service notices) as `primary_page` — "publisher page or documentation
inspected; actual local feed not validated" — and **S175** (Beogradske elektrane), **S207** (Blic
RSS) and **S208** (Beoinfo, the City's own news listing) as `lead` — "discovery lead; not
independently verified in this pass".

**What was actually true.** All four were being read every tick and all four have rows on disk. The
permission was never in question: each has a line in `research/08-provenance/LEDGER.jsonl` with its
robots.txt, headers and terms captured as bytes before the first read, and the collector re-checks
that gate on every tick. Nothing was collected without evidence. What had gone stale was the
registry's own description of these four: they were promoted into collection and their status stayed
where the discovery pass had left it.

Small, and not cosmetic. The registry IS the audit; §3 of the paper reports 211 records each with a
status and asks a reader to take that table as the state of openness in Belgrade. A reviewer who lays
the collector list beside the registry finds four sources being read whose own record says they were
never verified, and is right to ask what else the table is behind on.

**The fix, and the wrong fix that came first.** They were set to `collected` — and that was an
over-claim made without understanding the file: twenty of the twenty-eight polled sources sit at
`probe_ok`, so `collected` carries a distinction in this registry that had not been established, and
assigning it to four records would have invented a fact to cover a stale one. Caught by the test
itself, which failed on sixteen `probe_ok` sources and made the wrong assumption visible within the
hour. The four now read **`probe_ok`** — "bounded direct response and reconnaissance parsing
succeeded; not a production or accuracy verdict" — which is precisely what a source parsed
successfully every ten minutes satisfies, and is the smallest correct statement available. Each keeps
a dated `status_change_2026_09_09` note holding the old value beside the new one rather than
overwriting it out of existence. The permission evidence is untouched.

`research/test_permission_gate.py` now holds the whole claim as an invariant: every polled source has
a line in the permission ledger, no publisher who said no is polled, no polled source sits in an
unsettled state, no polled source carries a status the legend reserves for something never verified,
every polled source exists in the registry, every disabled collector says why, and nothing in the
undocumented queue is being read. If a source is ever added to the polling list without evidence
behind it, the suite fails before anything is collected.

**Rule: a status is a claim about a thing, and it has to stay true of the thing — and a correction
must not be an invention.** An audit allowed to drift from what the system does is not an audit but a
document; a correction that assigns a status nobody can define is the same failure with a newer
timestamp. The same test settles a wording problem in the other direction: the index's "26
undocumented" reads as twenty-six sources being read without paperwork and is the opposite — they are
the queue of sources *not* being read, which is now enforced rather than explained.

## C-018 — A copy rule meant to stop a document going missing published two internal ones instead

**When** 2026-09-09, from roughly 19:00 UTC (commit 879b6ad) until 20:20 UTC.

**What it said.** `tools/publish_github.ps1` states in the public repository's own notice that the
working documents, pre-papers, research trails and programme notes are internal and stay off the
public site. That was true of the site until I changed how documents reach it.

**What was actually true.** Earlier the same day a PDF was written, committed, and then absent from
`docs/` because a hand-maintained copy list had not been extended — twice. The fix made every PDF in
`research/06-paper` and `research/07-legal` reach `docs/` "by existing rather than by being listed".
It worked, and it also published **`BEOPS_WORKING_DOCUMENT_v1_2026-09-09.pdf`** and
**`BEOPS_WORKING_DOCUMENT_v1.1_2026-09-09.pdf`**, which are internal by that policy and which discuss,
among other things, commercialisation paths involving the university. A rule written to stop things
disappearing published things that were meant to stay put, and no test noticed because no test knew
what was supposed to be public.

**The fix.** Both files removed from `docs/` and from the published export. The copy rule keeps its
shape — a document reaches the site by existing — with an explicit deny for the kinds that are
internal by policy (working documents, letters, drafts, programme notes), and
`research/test_public_docs.py` now holds all three halves of the claim: no internal document is
published, the builder still carries the exclusion, and the paper itself is still published, so the
fence cannot quietly swallow what it was built to protect.

**And the wording it exposed.** Looking for what else the public surfaces claimed on the university's
behalf turned up four places saying this runs on "one university computer" / "the university machine"
— in the monologue page, the README, the September pre-paper and the publish notice — while
`research/07-legal/BEOPS_EVIDENCIJA_OBRADE` states plainly that the processing runs on the authors'
own equipment. All four now say the authors' own machine. `research/ORGANS.json` named the editor of
record as "Semir Poturak (Union Nikola Tesla University)" in five places, which reads as an
institution taking on editorial responsibility for what a machine says; the editor of record is a
person, and now says so.

**Rule: automation decides what happens, so it has to be told what must not.** "Everything of this
kind, automatically" is the right shape for a rule about publishing — a document that must not go out
is not an exception to be remembered, it is a property to be stated. The university is named on this
site as the authors' affiliation and as where the conference is held, and nowhere else: not as owner,
not as operator, not as sender, and not as the machine this runs on.

---

## C-019 — I put a name on a co-author that is not her name

**When** 2026-09-09, roughly 19:15–19:35 UTC. Caught before either document left the machine.

**What it said.** `research/06-paper/PRE_PAPER_v3_2026-09-09.md` and
`research/07-legal/BEOPS_PISMA_v3_2026-09-09.md`, as first written, named the authors as "Semir
Poturak; Dara Bakoč". Every letter in the second file carried that name in its signature block, on
letters addressed to ministries, public utilities and news publishers.

**What was actually true.** The co-author is **prof. dr Darinka Golubović Matić**. The surname
"Bakoč" appears nowhere in this project, in any file, at any date. It came from a working summary of
an earlier part of the same conversation and I carried it forward without checking it against a single
file, in the one kind of document where a wrong name is not a typo — a signed letter to an institution.

**How it was found.** Not by re-reading what I wrote. By a search for author names across the whole
tree, run for a different reason: `findstr` for "Golubovi" returned eight files, `findstr` for "Bako"
returned exactly the two files I had written minutes earlier, and nothing else.

**The fix.** Both documents corrected before they were used. The affiliation sentence was corrected at
the same time and in the same direction as C-018: the authors teach at Univerzitet Union — Nikola
Tesla, the conference is held there, and the work does not act in the institution's name — the letters
carry only the venue sentence, because in a letter an affiliation reads as backing.

**Rule: a name is a measurement.** Everything in this record that comes from a source is checked
against the source. A person's name arrived from my own memory of a conversation, which is the one
class of input this project has no gate for, and it went straight into a signature block. A fact about
a person is not more reliable than a reading of the air because it feels familiar. The check that
caught it — search the tree for it — costs one command and should have run before the first draft, not
after.

---

## C-020 — The site was still publishing three internal documents, and the deny-list named instances rather than the category

**When** From 2026-09-09 13:19 UTC (`PRE_PAPER_CONFERENCE_v2`) and 16:07 UTC
(`BEOPS_ANALYSIS_instruments_and_knowledge`) and 19:15 UTC (`BEOPS_PRE_PAPER_CONFERENCE`), until this
entry.

**What it said.** C-018, written the same evening, says in its own text that "working documents,
letters, drafts, programme notes" are internal, and that the fix gives the copy rule "an explicit deny
for the kinds that are internal by policy". `tools/publish_github.ps1` says the same and adds
**pre-papers** to that list by name.

**What was actually true.** `NOT_PUBLIC` contained `WORKING_DOCUMENT, PISMA, LETTER, INTERNAL, DRAFT,
PRESEK` — the two filenames that had just leaked, plus four guesses. It did not contain `PRE_PAPER`,
which the notice names explicitly, so three documents were live on the public site:
`BEOPS_PRE_PAPER_CONFERENCE_2026-09-09.pdf`, `PRE_PAPER_CONFERENCE_v2_2026-09-09.pdf` and
`BEOPS_ANALYSIS_instruments_and_knowledge_2026-09-09.pdf`. The first of them carries the older
affiliation line — "prof. dr Darinka Golubović Matić, doc. dr Semir Poturak (University Union — Nikola
Tesla, Belgrade)" — with no statement that the work does not act in the institution's name, which is
precisely the wording C-018 went looking for and fixed everywhere it could see.

**And the second half, which is worse.** Two of the three had no source PDF left in `research/` at
all. The build only ever copies; nothing in it can take a file back. A document therefore stays public
after it stops being eligible — after its source is deleted, after it is renamed, after the deny-list
is corrected. The deny-list would have kept the third file off the site from the next build; the other
two would have stayed up forever.

**The fix.** `NOT_PUBLIC` now names categories, not instances, and includes `PRE_PAPER`, `PREPAPER`,
`ANALYSIS`, `AUDIT`, `ATLAS`, `STRUKTURA`, `METODOLOGIJA`, `SCRATCH`, `NOTES`. The build now computes
the set of PDFs that *should* be public and withdraws every other PDF in `docs/`, printing what it
withdrew, so that publication is a property recomputed on every build rather than a state that
accumulates. `research/test_public_docs.py` gains the two assertions that would have failed here: no
PDF whose name matches a deny category is in `docs/`, and no PDF is in `docs/` without an eligible
source in `research/`.

**Rule: a fix written from the instances in front of you is not a fix.** C-018 named a rule —
"a document that must not go out is not an exception to be remembered, it is a property to be stated"
— and then implemented it by listing the two documents that had just gone out. The category was
already written down, in the project's own publish notice, one file away. And a rule about what is
public has to run in both directions: a build that can only add is a build whose mistakes are
permanent.

---

## C-021 — A test said the page carried a placeholder; the page carried the word „metodologija"

**When** 2026-09-09, ~19:47 UTC. Found by the suite, before anything was committed.

**What it said.** `research/test_render.py` failed with *"the built page carries 'TODO'"* — an
assertion that an unfinished placeholder had reached the public artefact.

**What was actually true.** Nothing on the page was unfinished. The test searched for its markers as
bare substrings, and `TODO` is inside **ME-TODO-LOGIJA**. The word arrived on the page through the
correction entry immediately above this one, which quotes the deny-list categories by name; the
correction that fixed one leak tripped a test on a different one's Serbian spelling.

**The fix.** Word-shaped markers (`TODO`, `FIXME`, `undefined`, `NaN`) are matched with word
boundaries; bracket-shaped ones (`{{`, `>None<`, `[object Object]`) stay literal, since they cannot
occur inside a word.

**Rule: a test that cries wolf is a defect, not a nuisance.** This project's whole argument is that a
check is worth more than an intention — which only holds while a failure means something. A test that
fails on correct content in the site's own second language teaches its operators to read failures as
noise, and the next real one goes past. English-only pattern matching on a bilingual artefact is the
same category of error as reading a reception time as a measurement time: the check was written for a
narrower world than the one it runs in.

---

## C-022 — The same policy answered differently depending on which door a document walked through

**When** Found 2026-09-09 ~20:15 UTC, during the publish that fixed C-020. The letters file
`BEOPS_PISMA_OBAVESTENJA_v2_2026-09-09.md` had been in the public export since it was written.

**What it said.** `tools/build_site.py` treats letters as internal by name — `PISMA` and `LETTER` are
both in `NOT_PUBLIC`, and have been since C-018. The publish notice in `tools/publish_github.ps1`
says the same about working documents, pre-papers, trails and programme notes.

**What was actually true.** The export excludes `research/06-paper` as a **folder**, which is why no
pre-paper ever reached the public repository. `research/07-legal` is exported whole, and the letters
live in it. So the site build refused to publish a letter while the repository export published it,
from the same tree, on the same run. The v3 letters — which carry the send order, the reasoning for
holding one group back, and the honest note that two of the sets have not been read by a lawyer —
went out in the export that was fixing the previous version of exactly this mistake.

**The fix.** The export now filters by filename category as well as by folder, using the same list of
kinds. A document of an internal kind is excluded by being that kind, in both places, whichever door
it walks through.

**Rule: a policy that is implemented twice is two policies.** Both implementations were written from
their own local view — one saw filenames, the other saw folders — and neither was wrong on its own
terms. The failure is that "internal" had no single definition either could be checked against, so
they could drift apart silently and did. This is the third entry in one evening about the same shape,
and the shape is now clear enough to state plainly: **what must not happen has to be written down once,
as a property, in a place every mechanism that could cause it reads.**

**Second occurrence, one hour later.** The entry above contains the literal `{{` as an example of a
marker, and the page renders this ledger. So the very correction that fixed the substring test tripped
the same test on a different marker. The pattern now asks for `{{` followed by a word character — a
template placeholder is `{{name}}`; two braces followed by a backtick are prose about braces. Twice in
one hour, a check written against a narrower world than the one it runs in, and both times the world
that broke it was this project's own writing about itself.

**Third occurrence, and the actual fix.** Tightening the pattern was still the instance-shaped answer:
the next correction entry quoted `>None<` and the test failed again. The structural fact is that the
page carries its own registers inside `<script id="data">` — the source registry, the provenance index
and this ledger — and that block QUOTES what publishers wrote and what this system said when it was
wrong. By design it may contain any string, including every marker a placeholder check looks for. A
placeholder is a defect of the *template*, so the check now scans the page with the data block removed.
Three passes to stop patching the symptom: the first two asked "which marker tripped?", the third asked
"what is this check actually about?"

---

## C-023 — A phone layout that was written, correct, and dead: CSS has no memory of intent

**When** Seen on a phone 2026-09-09 ~22:29 local, in a screenshot. The `main` rule it depends on was
written earlier the same evening, when the map moved out of `<main>`.

**What it said.** `research/05-design/studies/monolog-puls.html` carries
`@media (max-width:900px){ main{grid-template-columns:1fr} ... }` near the top of its stylesheet, with
a comment explaining that on a phone the two columns must stack. The site's own render tests assert
several other phone-layout properties. Everything said the narrow layout existed.

**What was actually true.** Further down the same sheet, added later, sat
`main{grid-template-columns:minmax(300px,4fr) minmax(0,8fr)}` — unconditional, equal specificity, and
*after*. The last rule that matches wins, so on a 412 px phone the two columns never stacked: the
three entity panels took the first column's 300 px minimum and the feed was squeezed to roughly one
character wide and clipped off the right edge of the frame. A media query that sits before the rule it
is meant to narrow is not a media query, it is a comment.

**And it was not one rule.** Written as a check and run across the three frames and the built page, the
same shape appeared **seven** times: `.line{grid-template-columns}`, `.lines{max-height}`,
`.how{padding}` and `header h1{font-size}` in the monologue; `.reading{position}`,
`.reading{border-left}` and `.gh h2{font-size}` in the ribbon; and — an hour old —
`.hlangs button{font-size}`, `.hlangs button{padding}` and `.hlangs{flex}` in the built page, which is
the phone sizing of the four language buttons I had just added. One of the seven was not worth
resurrecting at all: `.map .cv{min-height:56vh}` is the C-016 runaway, a viewport height inside a frame
the parent sizes from its content, and it was deleted rather than moved.

**The fix.** Every narrowing block now sits at the END of its stylesheet, after every rule it is meant
to override, and the phone layout of a page is in one place instead of two. `research/test_render.py`
gains a small CSS parser and the assertion that no `max-width` declaration is undone by a later
unconditional one of equal specificity — across the built page and every frame it embeds.

Separately, the phone header: nine navigation links in a three-column grid is three rows, and with the
new language row that made a sticky header about 300 px tall on a 412 px screen — a third of the phone,
permanently, on every page. Five columns fit the nine links in two rows at a size that is still a
26 px tap target, and nothing is hidden behind a sideways scroll.

**Rule: source order is part of the meaning, and only a tool can see it.** Every other rule in this
project is checked by reading a file and asking whether a claim holds. This one could not be found that
way: each rule was correct on its own, the comment above the dead one described the intent accurately,
and the defect existed only in the *relationship* between two rules a hundred lines apart. It was found
by a person looking at a phone, like C-016 before it — and the fix is not care, it is the fifteen-line
parser that now reads the whole sheet in order and answers the question nobody can hold in their head.

---

## C-024 — Fixing the phone layout broke the map on every screen, and it was published that way

**When** 2026-09-09, published 20:34 UTC in commit `8f9ac75`, found 20:41 UTC by measuring the live
page at 412 px. Live for roughly seven minutes.

**What it said.** The commit message for C-023 said the narrowing blocks had been moved to the end of
each stylesheet and that 190 tests passed. Both true.

**What was actually true.** The move was done by a script that cut from the block's opening comment to
the first `}` after its last declaration — which is the brace closing that declaration, not the one
closing the media block. So the block arrived at the end of the sheet **one brace short**, and an
orphan `}` was left behind where it had been. A stray `}` at top level makes a CSS parser discard
until it recovers, and what it discarded was the very next rule:
`canvas{position:absolute;inset:0;width:100%;height:100%;display:block}`. The pulse map's canvas
therefore fell back to its intrinsic 600×300, static and inline, hanging 238 px out of a 362 px frame —
**on every screen, not only on a phone.** The 190 tests were all green: not one of them looked at
whether the stylesheet was syntactically whole.

**How it was found.** By measuring the live page at a phone viewport and asking which elements are
wider than their container. One was: `canvas`, 600 px in a 362 px box.

**The fix.** Braces repaired, and two assertions added: every stylesheet closes every brace it opens —
the cheapest check in the suite — and every canvas inside a frame is given a CSS width. Unbalanced
braces are not a style problem; they mean everything after the break is arbitrary.

**Rule: a repair is a change, and a change is not verified by the tests that passed before it.** The
suite had thirteen checks about how this page lays out and none about whether its stylesheet parses.
Worse, the defect was introduced *by the script that implemented the previous correction* — the fix for
C-023 was correct in what it moved and wrong in how it cut, and it shipped because "190 tests OK" was
read as "the change is good" rather than as "nothing I already knew to check has broken". Three
corrections this evening now share one shape: C-018, C-020 and C-022 were fixes written from the
instances in front of me; this one is a fix that broke something no test was watching. Both are the
same failure to ask what the change could break that the record does not yet check.

---

## C-025 — The page prints UTC and the reader's clock does not, and nobody told the reader

**When** Noticed 2026-09-09 23:32 local (21:32 UTC), by the person who built it.

**What it said.** The mind cards on the front page stamp each utterance `09.09 21:18 UTC`. The wall
clock beside the screen said 23:32. Read together, that is a page whose newest thought is more than
two hours old — a stalled instrument.

**What was actually true.** Nothing was stale. Belgrade is UTC+2, so 21:18 UTC is 23:18 local:
fourteen minutes. Checked at the same moment: the newest collected row was **12 seconds** old, the
published snapshot 9 minutes, the watchman reading 2.4 minutes, and all five scheduled tasks had run
within the last minute. The offset was the reader's timezone, and the reader was the author.

**Why this is a defect and not a misunderstanding.** A page that requires its reader to perform a
timezone conversion before it can be believed has failed at the one thing this project claims to be
good at. The whole record exists to keep *when* unambiguous — measured, published, received, never
collapsed — and then the surface that shows it collapsed the last and most obvious one: the difference
between the clock on the page and the clock on the wall. If the author misreads it in the first week,
every reader will.

**The fix.** Every UTC stamp on the pulse frame now carries the age beside it — `21:18 UTC · pre 14
min` — recomputed every thirty seconds, and the section heading says *all times are UTC* in both
languages. The replay clock deliberately gets no age: during a replay the clock is not now.

**And what is deliberately NOT done.** An age is printed only for an utterance or a reception — two
instants the record knows exactly. It is never printed for a measurement whose time the source did not
publish. 49 of 843 series are `untimed`: for those the value is exact and its age is unknown, and
attaching a number to that unknown would be precisely the invention this whole instrument exists to
refuse. The absent age is a statement.

**Rule: the reader's context is part of the display.** Every time in this record is stored, compared
and reasoned about in UTC, which is right. But a stored time and a shown time are different objects
with different jobs, and the shown one has to survive being looked at by a person standing next to a
clock. This is the same mistake as reading a reception time as a measurement time, made one layer
further out: correct data, rendered in a frame of reference the reader does not share.

## C-029 — the note row wrapped, so the panel had two heights

**2026-09-09.** C-028 fixed every tile in the NOW panel to one height and recorded that the panel no
longer changes height with the range. Measured afterwards, it did: 345 px in `sada`, 345 px in `24 h`,
**373 px in `7 dana`**. The tiles were fixed; the note row under them was not. Its 7-day sentence is
longer than the row is wide, so it wrapped to a second line, and it appears only while the record is
shorter than seven days — a note that is sometimes one line, sometimes two, and sometimes absent.

**Correction.** The row is one line by construction: `height:26px`, `white-space:nowrap`,
`text-overflow:ellipsis`. Every note that can appear there has a short form written for one line in all
four languages; the full sentence is carried in the row's `title`, so nothing is removed from the page.
Tiles 82 → 72 px and the sparkline 24 → 20 px, and the hero widget is now a fixed 316 px with one extra
sentence in each text beside it, so the three columns of the hero end within a line of each other.

**What was wrong with the method, not the code.** C-028 asserted an invariant — one height in every
range — after fixing the part it had been looking at, without measuring the other two states. The
measurement that would have caught it took one command. Nothing about the panel is verified by fixing
the tiles; it is verified by measuring `sada`, `24 h` and `7 dana` and finding one number three times.

**Nothing observed was changed.** This correction touches presentation only: no stored value, no
provenance state, no permission record.

## C-030 — the scrollbar belonged to the operating system

**2026-09-09.** With the dark theme selected, the monologue feed and the page's own window drew the
default platform scrollbar: a light grey track and thumb on a `#111311` ground. Every other colour in
the frame is one of two tokens; this one was neither, and it was the brightest thing on the screen.

**Correction.** `html{scrollbar-width:thin;scrollbar-color:var(--ink30) transparent}` in all four
frames and in the built page. Both properties are inherited, so the feed, the three mind columns and
the reading column are covered by the root declaration and none of them declares its own. A
`::-webkit-scrollbar` block carries the same tokens for engines without the standard properties;
engines that have them ignore it.

**Asserted, not assumed.** `test_every_scrollbar_takes_its_colour_from_the_page` requires the
declaration on the `html` rule of every frame and of `docs/index.html`. Asserting it on the root rather
than on each scroller is deliberate: the next scrollable panel added to a frame inherits the theme
without anyone having to remember it.

**Why it survived.** The theme was verified after C-027 by measuring the page and all five frames in
light and in dark — but by measuring the *background* colour each resolved to, which was correct in
both. A defect present in only one theme is not caught by checking that both themes load.

**Nothing observed was changed.** Presentation only.

## C-031 — the one-line note did not fit on one line

**2026-09-09.** C-029 fixed the note row under the NOW panel's tiles at 26 px, one line, clipped with an
ellipsis, and wrote a short form of each note for that line. Measured live in the 7-day range: the row
is 439 px wide and the text it was given is 549 px, because two notes are joined with a separator and
each short form was written as if it were alone. The height is stable — that part held — but the
ellipsis was permanent rather than exceptional.

**Correction.** Both short forms are shorter. The worst case in Serbian is now
`zapis: 30 h; pun prozor 7 dana 2026-09-15 · isprekidano = vreme merenja nepoznato` — 81 characters,
about 400 px, inside 439. The second one is reworded to the phrase the page already uses for this state
in its legend, `vreme nepoznato`, rather than a second phrase for the same thing. The full sentences
remain in the row's `title`.

**What this pair of corrections is really about.** A fixed row plus an ellipsis makes a layout stable
whatever the text; it does not make the text readable. Both were needed, and the second was only
visible by measuring `scrollWidth` against `clientWidth` on the live page — the state the record cares
about is not "did it fit in the design" but "did it fit in the browser".

**Nothing observed was changed.** Presentation and wording of a legend only.

## C-032 — the three entity columns had a scrollbar and one card each

**2026-09-09.** The mind section rendered the newest checked utterance per entity and nothing else,
inside a container with `overflow:auto`. The 24-hour window held 74 utterances — observer 29, skeptic
15, connector 30 — so the reader could see three of seventy-four, with a scrollbar suggesting
otherwise. Asked directly why the columns cannot be scrolled back, the answer was that there was
nothing behind them to scroll to.

**Correction.** Each column is that entity's whole window, newest first, scrolling in its own stack
whose height is the feed's height (so the existing drag handle sizes all four columns together). The
column header states the count.

**What the single-card view was hiding.** In Serbian only 29 of the 74 utterances are voiced. The other
45 were refused by the export validator: 15 because the citations differ from the original, 26 because
the local model produced ijekavica where the export requires ekavica (`zraka`, `utjecaj`, `provjeriti`,
`vrijednosti`), 5 failed with an error. Showing only the newest *voiced* utterance made the skeptic
appear silent for nine hours. It was not silent — its Serbian was refused. Each refused utterance is
now its own row carrying the validator's own reason verbatim, because a column that renders only what
passed reports silence where the record actually holds a refusal.

**Not a layout defect.** A panel showing the freshest state of an accumulating process is a reporting
choice, and it was the wrong one. The scrollbar was the tell and it sat there unexamined.

**Nothing observed was changed.** The utterances, their states and the validator's reasons are read as
stored; none was edited, and none is newly excluded.

## C-033, C-034, C-035 — the mind was being refused for the wrong reasons

**2026-09-10.** Read out of the organ's own 300 rows, not out of its design.

### C-034 — a clock was read as a quantity

`number not in digest: 08` is the commonest reason an utterance was ever thrown away: 17 occurrences,
followed by `09` (9), `02` (8), `23` (5), `03` (4). Every one of those is an hour. The entity wrote
"between 08:00 and 09:00 UTC"; `_nums()` extracted `08` and `09` as numbers, the digest's number set
did not contain them, and a correct sentence was refused.

**Correction.** `_clocks()` reads times of day as `HH:MM`; `_nums()` strips them before extracting
quantities; the digest carries `clock` — every time its facts name, plus every whole hour of the window
it covers, because the window is precisely what the entity was given. A time outside the window is
refused as `time outside the window: HH:MM`. The check is now about the right kind of thing.

### C-035 — a claim that named its source could not be settled

Every claim that was ever settled named `S146`. Every claim returned `unverifiable` named `SEPA`,
`RHMZ automatic stations` or `Sensor.Community` — 10 of 19. The scorer resolves a source by id
(`by_sid.get(claim["sid"])`), so a name never matched and the claim was written off as unverifiable,
which read as "the mind predicts unfalsifiable things" when what happened is that it spelled the
source in words.

**Correction.** `resolve_sid()` maps a name to its id against every name the source carries in this
window (registry label, snapshot name, Serbian label); `validate()` normalises `claim["sid"]` in place
so the row that is stored is the row the scorer can settle; a name that resolves to nothing is refused
with the reason, which the entity reads back from its notebook next round. The prompt lists the
available ids and says a name cannot be scored.

### C-033 — the refused Serbian was deleted

27 renderings were refused and 0 of them kept their text: `voice()` set `row["sr"] = ""`. The utterance
had exactly one Serbian sentence and the program erased it. This contradicts the record's own rule —
evidence is immutable, corrections are appended.

**Correction.** The refused text is kept as `sr_refused` (with its hypotheses and questions), carried
through the export, and shown on the page as a refused card with the validator's reason. `sr` still
holds validated text only, so nothing downstream can present a refusal as a voiced sentence.

### What this trio is actually about

The failure rate was being read as a fact about the models. It was largely a fact about the checks: one
refused sentences for citing the clock, another made half of all predictions unscoreable, and the third
threw away the evidence of the failure. No model changed and nothing was retrained. Before any
comparison of models means anything, the measurement has to be measuring the model.

**Nothing observed was changed.** The stored utterances, their states and reasons are read as written;
`sr_refused` only stops a future deletion.

## C-036 — the organ was alive and saying nothing

**2026-09-10.** Between 00:38 and 01:22 the mind produced no utterance. The scheduler ticked every four
minutes throughout, so nothing looked broken: eleven receipts, of which three `organ_silent` ("model
daemon not answering") and three `organ_failed` (`TimeoutError`).

**Cause.** The body has 8 GB of RAM (2.7 GB free at the time) and the preferred thinking model is
3.4 GB. When free memory dips below what the load needs, the daemon thrashes and stops answering — at
the worst moments not even `/api/tags`. Diagnosed live: the process was up, the port listening,
`/api/tags` answered 200 in 8 s, and `/api/ps` reported **no model resident**. It had been evicted and
could not be reloaded.

**What the code did with that.** It picked the first available model from the register's ordered list
and, when the call failed, recorded silence. The order had been in the register since the organ was
built — `observer: qwen3.5:4b, qwen2.5:3b, qwen2.5:1.5b` — and was never walked. A 1 GB model that was
already pulled sat unused while the organ said nothing.

**Correction.** `_chain()` returns every listed model that is present, in the register's order;
`chat_chain()` asks each in turn and returns the answer together with the model that produced it. The
stored row credits the model that actually spoke, never the one asked first, and the receipt carries
`fell_back_from` so a stretch of degraded thinking is legible as degraded. Both the drip and the
on-demand conversation take this path.

**The principle.** A smaller model is a worse thought; no thought is not a thought at all. An
observatory whose claim is that it keeps listening cannot go quiet because its preferred model is too
large for the machine it runs on.

**Not fixed here.** The daemon should be told to hold one model rather than juggle several. That is a
setting on the daemon, not code in this repository.

**How it was found, honestly.** Not by monitoring. A measurement of an earlier correction came back
empty, and only then was the receipt read — where the reason had been sitting in plain words for
three-quarters of an hour.

**Nothing observed was changed.** No stored utterance, state or receipt was edited.

## C-037 — the notebook fed the refusal back into the utterance

**2026-09-10, 01:45 UTC.** The skeptic (qwen2.5:1.5b) produced, as a thought about the city:

> "The city's maximum values of PM10 and NO2 have significantly increased between 08:00 and 09:00 UTC,
> as indicated by the ' -> REFUSED (number not in digest: 08; number not in digest (hypothesis): 08).
> The city's maximum values of PM2.5 have also increased, moving from 27 to 21 µg/m³ ..."

A line of its own notebook, copied into an observation with the refusal text attached.

**The loop.** No weights change in this organ; learning is verbal — each entity's notebook (what it
said, whether it was refused and why) is read back at the next conversation. The reason was handed back
as the validator wrote it, and a reason contains the numbers that caused the refusal — numbers that are
by construction absent from the digest. A model that copies that line therefore uses a number that
cannot pass, is refused again, and gets a longer string to copy. The smallest model was circulating its
own error messages, and every utterance it produced looked like nonsense from outside.

**Correction, two parts.**

`reason_category()` renders a refusal as a sentence with no digits — "you used a number that is not in
the facts", "you named an hour outside the window you were given", "you cited a fact id that does not
exist". The entity's own sentence is still quoted back verbatim, because those are its words and that
is the feedback; only the validator's arithmetic is withheld.

`NOTEBOOK_VOCAB` refuses any utterance that speaks the validator's language — `-> REFUSED`, `number not
in digest`, `time outside the window`, `cites nothing`, `restates the conversation`, `claim malformed`
— as *echoed its own notebook*. An utterance that talks about the checks is not an observation of a
city, and the loop cannot re-form quietly.

**Why it stayed invisible.** The output was refused, and refused output is not read. The record kept
every one of these rows on disk from the first night, in plain text, and nobody — including this
system's own weekly review — had cause to open them, because a refusal reads as a fact about the model.

**Nothing observed was changed.** Stored rows are read as written; the change is to what the next
prompt contains and to what the validator accepts.

## C-033…C-037 measured, and one of them made the numbers worse

**2026-09-10, 06:50 UTC**, 4½ hours after the corrections went live, read out of the organ's own 381
rows and 428 receipts by `research/eval_mind_effect.py`.

| | before | after |
|---|---|---|
| model steps that ended in silence | 16.3 % of 300 | **0.0 % of 56** |
| a clock refused as a quantity | 62 reasons | **5** |
| `time outside the window` (the precise reason) | 4 | **12** |
| stored utterances quoting a refusal | 2 | **0** |
| refused as an echo of its own notebook | — | **8 caught** |
| voiced in Serbian | 62.3 % | **90.9 %** (n=11) |
| claims naming a source in words rather than by id | 10 of 19 | **0 of 2** |
| claims settled | 6 true, 3 false, **10 unverifiable** | **2 true, 0 unverifiable** |
| **utterances accepted** | **47.8 %** | **32.4 %** |

**The fallback fired once in the wild.** 05:09:56, the skeptic: `qwen2.5:1.5b` returned a
`JSONDecodeError`, the chain moved to `qwen3.5:4b`, and the step produced a sentence that was then
judged on its merits. Before C-036 that step was silence.

**The notebook loop had been running for seven hours.** The same corrupted sentence — "…as indicated by
the ' -> REFUSED (number not in digest: 08…" — appears at 18:17 on 09-09 and again at 01:45 on 09-10.
Both were refused, so neither reached the page, but the line was circulating through the notebook
between those two points.

**The acceptance rate fell, and that is the honest headline.** 20 of the 23 refusals since the fix come
from two reasons that did not exist before it: `time outside the window` (12) and `echoed its own
notebook` (8). The corrections did not make the entities produce more; they made the refusals correct.
The rate should be read together with the reasons, which is why `eval_mind_effect.py` prints them
side by side and says so.

**What is a prediction and not a result.** Until 2026-09-10 the feedback an entity received was the raw
refusal string, whose digits are by construction absent from the digest — so adaptation was
structurally impossible, not merely absent. It is now possible. Whether the acceptance rate recovers is
therefore a claim about the next days, and it will be settled by running this same tool again, not by
asserting it here.

**Why this file now contains a measurement at all.** The pattern this record keeps repeating is a fix
asserted rather than measured — C-028 declared the panel stable without measuring the range that was
actually broken. `research/eval_mind_effect.py` exists so that a correction to the mind is not finished
until the two halves of the record have been counted across it.

**Nothing observed was changed.** The tool reads and prints; it writes nothing.

## C-038 — the frame asked for the theme before anything was listening, three times

**2026-09-10, 07:40–08:35 UTC.** Four attempts at one race, each of which looked correct when it was
written and each of which was refuted by the page.

**The symptom.** The public page carries five embedded studies — the now-panel, the data panel, the
live ribbon and the two monologue panels. The page owns the theme and the language; a frame is a
separate document and owns neither, so both are pushed to it by `postMessage`. On a dark page, a frame
came up light for as long as it took the message to arrive — and often it never arrived at all.

**Attempt 1 — the parent announces on `load`.** Refuted: the parent's `load` fires before the frame's
own script has registered a `message` handler. A message delivered before its handler exists is not a
late message; it is a lost one, and nothing in the browser reports it.

**Attempt 2 — the frame asks, once, as soon as it parses.** `postMessage({beopsAsk:true})` to the
parent. Refuted: at that instant the parent had not yet installed the answerer, so the question was
lost in the other direction. Two components each scheduled against their own readiness, and neither
schedule was a fact about the other.

**Attempt 3 — the frame keeps asking until an answer arrives.** A retry loop with a `got` flag, and a
small listener registered at parse time to set that flag. Refuted, and worse than refuted: **that early
listener consumed the parent's answer, set `got`, and cancelled every retry — while the real handler,
the one that actually applies the theme, did not yet exist.** The answer arrived, was counted as
received, was applied by nobody, and the retry that would have asked again was switched off by its own
arrival. The bug went quiet without going away.

**Attempt 4 — correct.** The ask is issued on the line immediately after the real handler is
registered, so the only listener that can consume the answer is the one that uses it. The parent
answers `beopsAsk` with the theme and both language values. Verified live in both directions — dark
page → frame arrives dark, light page → frame arrives light — on all five frames.

**The principle this leaves behind.** *Every schedule is a guess about when the handler exists.*
Readiness is not a time; it is the presence of the thing that will act. And a flag that records "an
answer arrived" is not the same object as "the answer was applied" — attempt 3 is the general shape of
a monitor that says OK because a message was received, which is the same error this record writes about
its sources under the name **received ≠ measured**.

**How it was found.** Not by reading the code — three readings of the code produced three wrong fixes.
By four live experiments on the running page, each of which was allowed to refute the previous one.

**Two notes on this file itself, recorded rather than tidied away.** The sequence has no **C-026**; the
ledger does not say why, and this note records the gap rather than closing it. The measurement entry
immediately above — *"C-033…C-037 measured, and one of them made the numbers worse"* — carries no id of
its own; it is left as written, because renumbering an append-only file is the kind of quiet edit this
file exists to make impossible.

**Nothing observed was changed.** No stored row, state or receipt was touched; the change is to the
order of two lines of page script.

## C-039 — the correction about the ledger's gaps was itself wrong, and there is no definition of "a correction"

**2026-09-10, 09:00 UTC**, twenty minutes after C-038 was appended. C-038 closed with a note saying
the sequence "has no **C-026**", recorded as a gap rather than closed. That note was written from a
list of the ids that appear anywhere in this file. It is wrong in the direction that flatters us.

**What the file actually contains,** counted three ways on the file itself:

| Counting rule | Answer |
|---|---|
| Headings that begin with an id (`## C-0NN — …`) | **34** |
| Ids that head an entry (one heading covers C-033, C-034 and C-035) | **35** |
| Ids that appear anywhere in the file | **38** |
| **Ids referenced by other entries and heading none of their own** | **C-026, C-027, C-028** |
| The number the public site prints | **32** |

So three corrections are *cited* in this ledger — C-028 is quoted inside the C-033…C-037 measurement
as the entry that "declared the panel stable without measuring the range that was actually broken" —
and none of the three was ever written down here. They were made; they were referred to; they have no
entry. C-038 named one of them and missed two.

**The deeper defect, which is the one worth keeping.** Five counting rules were available and four
different numbers came out. Nowhere in this project is it written what *one correction* is. A record
whose whole premise is that a figure must come from the file that holds it has been publishing a count
of its own corrections without a stated definition of the thing being counted — the same class of
error it writes about its sources under *received ≠ measured*.

**The definition, stated here so that it can be tested rather than assumed.** *An entry is a heading.
An id is a claim that an entry exists.* By that rule this file holds **34 entries** carrying **35 ids**,
and **three ids are claims with no entry behind them**.

**What is not being done.** The three missing entries are not being reconstructed now from the commit
history and back-dated into an append-only file; that would be a fabrication with a helpful motive.
They are added to the open list in the pre-paper: write them from the commits that made them, dated
today and saying plainly that they are late. And the public site's counter is left alone until it can
be pointed at the stated definition rather than quietly re-tuned to agree with it.

**Nothing observed was changed.** C-038 stays exactly as written, wrong sentence included; this entry
is what a correction to a correction looks like in a file that may not be edited.

## C-040 — the layer that says what is usual was reading the one clock we know is wrong

**2026-09-10, 09:30 UTC.** Found while surveying what the permissions already held would allow that
had never been computed — that is, while looking for something else.

**What was already right, and is the reason this is small.** S146 (SEPA's HVD air-quality API) labels
Belgrade local time as `Z` in three fields whose names end in `_utc`. That was found on 2026-09-08 by
reading a row, and handled properly: `COLLECTORS.json` carries a `source_clock_note` naming the offset,
the evidence row and the date the clocks change; `parse_sepa_hvd` keeps the label exactly as served and
writes `phenomenonTimeCorrected` / `resultTimeCorrected` beside it, marked `estimated`; the snapshot
carries `tc` next to `t`; and the mind says it out loud in both languages every round — *"SEPA's last
labelled hour ends HH:MM UTC; our estimate of true UTC is HH:MM (the source labels local time as Z)."*

**What was wrong.** `tools/baseline.py` was the one consumer that never read the correction. `_hour_of()`
took `phenomenonTime` — the label — and the file it writes calls that hour UTC. For S146 it is Belgrade
local. The layer was internally consistent, because `organ_mind` looked the bucket up by the same label,
so today's comparisons were like-for-like; it breaks the moment an S146 bucket is set beside another
source's bucket, which is exactly what a "what is usual at this hour" layer invites.

**Nothing wrong reached anyone.** The baseline layer has published zero buckets — 12,726 candidates, all
withheld for having fewer than three days behind them — so the defect was found before its first
publication. That is the only comfortable sentence in this entry.

**Correction.** `_hour_of()` now returns which of three clocks the hour came from — `measured` (the
source's own label, taken as served), `corrected` (our estimate of the true UTC, where the collector
wrote one), `arrival` (no measurement time published at all) — and prefers the correction where it
exists. Every bucket carries `hour_read_from`; every source file carries the list of clocks its buckets
were built on and the source's clock note. `organ_mind` looks the bucket up by the corrected label of
the same hour rather than by the source's label, so the two ends of the comparison are read off one
clock.

**The general form, which is the part worth keeping.** The note is hand-written prose about one source.
Nothing asserted that a source delivering values which arrive *before their own measurement window has
closed* must be declared at all — so a second source with the same defect would have been silently
wrong in the same way, and would have been found by luck again or not at all.
`research/test_source_clock.py` is that assertion, written as a property of any source: a source may
have a wrong clock, it may not have one quietly; a note that names an offset must actually produce a
corrected time, so a note cannot be decorative; a corrected time must be marked as our estimate, because
it is our reading of somebody else's clock and never their statement; and if a second source ever earns
a clock note, the suite fails and asks for the pre-paper's clock paragraph to be re-read rather than
silently generalised.

**The operator's part, recorded because it is the larger error.** Before finding the real defect I
reported to the editor of record that the correction mechanism existed but had never been switched on,
and that nothing was being corrected. That was false. I had looked for `source_clock_note` in
`SOURCE_REGISTRY.json`, found nothing, and read the absence as the answer — the same shape as **C-035**,
where a claim naming its source in words resolved to nothing and was written off as unverifiable. The
note was in `COLLECTORS.json`, which is where collector behaviour belongs, and it was better written
than what I was about to add. An absence in one file is not a fact about the system.

**Nothing observed was changed.** No stored row was touched; the 20,175 S146 rows keep their labels
exactly as the source served them, as does every correction the collector had already written beside
them. The change is to which of the two the baseline layer reads.

## C-041 — three false alarms in four hours, all of them the same lookup

**2026-09-10, 09:00–11:40 UTC.** Not a defect in the instrument. A defect in the operator, recorded
because it repeated three times in one session and each repetition was reported to the editor of
record as a finding before it was checked.

**The three.**

1. **The clock note.** Looked for `source_clock_note` in `SOURCE_REGISTRY.json`, found nothing, and
   reported that the correction mechanism for S146 existed but had never been switched on and that
   nothing was being corrected. It was in `COLLECTORS.json`, where collector behaviour belongs, and it
   was more careful than what was about to be added — it named the offset, the evidence row and the
   date the clocks change.
2. **The ledger's numbering.** Counted the correction ids that appear anywhere in `CORRECTIONS.md`
   and wrote into C-038 that the sequence is missing C-026. It is missing **C-026, C-027 and C-028** —
   three corrections that were made, are cited by other entries, and were never filed. Corrected in
   C-039, which also had to state what one entry *is*, because five counting rules gave four answers.
3. **The robots parser.** Re-checked four hosts with a script built on `urllib.robotparser`, saw it
   call a wildcard-forbidden path allowed, and raised an alarm that the project's permission verdicts
   might be permissive — against the one claim this record cannot afford to be wrong about.
   `tools/legal_capture.py` has carried a correct RFC 9309 matcher from the beginning, with a comment
   saying it exists *because* `urllib.robotparser` does not do this, and it stores the **stricter** of
   the two verdicts. The blindness was in the throwaway script, not in the tool.

**The shape, which is identical in all three.** Consult one artefact. Find an absence in it. Report
the absence as a property of the system. In none of the three was a second place checked before the
report went out, and in all three the second place held the answer, already written down, usually
better than what was about to replace it.

This is **C-035** with the roles exchanged. There, a claim that named its source in words resolved to
nothing and the scorer wrote it off as unverifiable — the failure was reading "no match" as "no such
thing". Here the lookup is a human-shaped one and the conclusion is the same error: *an absence in one
file is not a fact about the system.*

**Why it is worse than the defects it was chasing.** Each of the three reports was more alarming than
anything actually wrong, and two of them named the project's central claims. A record whose value is
that it does not say more than it can support was, for a few minutes at a time, saying considerably
more. That the reports were corrected within minutes is the mechanism working; that they went out at
all is the failure.

**What changes.** Not a rule about care - there was no shortage of care. A rule about ORDER: before a
defect is reported, the claim that the thing is missing is itself checked in the place it would live
if it existed. For this repository that means the registry AND the collectors file; the ledger's
headings AND its ids; the throwaway probe AND the tool that does the job in production. The check is
cheap and it is the same check the instrument performs on every source it polls before believing it.

**What survives as work, and it is real.** The third alarm was false and the question underneath it
was not: the guard asserts "no named refusal is polled" from the **registry** - from what was written
down when the permission was checked - and nothing re-derived that verdict from the **bytes** the
publisher served. A verdict recorded on 6 September was believed on 10 September because it was
written down, which is precisely the difference between permission as memory and permission as bytes
that this project claims to have engineered away. `research/test_robots_bytes.py` closes it: every
polled source's collected path is re-tested against the newest stored `robots.txt` with the RFC 9309
matcher on every run, the matcher's behaviour is locked with the examples `urllib.robotparser` gets
wrong, and a tripwire fails the suite the day the two parsers disagree about a path we collect.

Measured while writing it: **all 28 polled sources are allowed under both parsers**, and 34 stored
robots files use wildcard rules the standard library cannot read - five of them on hosts we poll,
where the two verdicts happen to agree because the collected paths do not match those rules. Today
that is luck rather than design. From today it is a test.

**Nothing observed was changed.**

## C-042 — the acceptance rate did not recover, and the explanation for the fall got weaker too

**2026-09-10, 10:00 UTC.** The measurement entry above (C-033…C-037 measured) ended with a prediction,
written before the answer was known:

> "Until 2026-09-10 the feedback an entity received was the raw refusal string, whose digits are by
> construction absent from the digest — so adaptation was structurally impossible, not merely absent.
> It is now possible. Whether the acceptance rate recovers is therefore a claim about the next days,
> and it will be settled by running this same tool again, not by asserting it here."

It was settled by running the tool again. **It has not recovered.**

| reading | acceptance, after the cut | n |
|---|---|---|
| 06:50 UTC | 32.4 % | 37 |
| 08:49 UTC | 35.4 % | 48 |
| **10:00 UTC** | **33.9 %** | **56** |
| (before the corrections) | 47.8 % | 161 |

Three readings across three hours, moving 32.4 → 35.4 → 33.9. That is not a recovery; it is noise
around roughly a third, against 47.8 % before. **Reported as a failed prediction**, with no excuse
attached. The prediction said "the next days" and it has been eight hours, so it is not refuted
either — the clock keeps running and the next reading is scheduled — but at the checkpoint it was
given, it failed, and that is what goes in the ledger.

**The second finding is worse than the first, because it is about the story rather than the number.**
C-038 explained the fall this way: *"20 of the 23 refusals since the fix come from two reasons that did
not exist before it — `time outside the window` (12) and `echoed its own notebook` (8). The corrections
did not make the entities produce more; they made the refusals correct."* That was 87 % of refusals
accounted for by the new, stricter checks.

At 56 utterances the same two reasons account for 21 of 37 refusals — **57 %**. The remaining 16 are
old categories that existed before the corrections: `number not in the cited facts` (16 overall),
`cites nothing inside the text` (7), `too short` (6). As n grows, the share of the gap explained by
"the checks got stricter" is falling, and the share that is simply the entities producing less
supportable output is rising.

So the honest position is now weaker than C-038's in two directions at once: the rate has not
recovered, and the reassuring explanation for why it fell covers a shrinking majority of it. Both
sentences are written here rather than waited out.

**What did hold, measured in the same run.** Every other correction is still doing what it was written
to do, and none of this is offered to soften the paragraph above:

- **C-036** — 0 silent or failed steps out of 93 model steps since the cut, against 16.3 % of 300
  before. Four fallbacks fired in the wild (05:09, 07:57, 08:01, 08:53 UTC), each recorded with the
  model that actually spoke.
- **C-037** — 0 stored utterances quote the validator back at the city, against 2 before.
- **C-035** — 5 claims, 3 settled true, **0 unverifiable, 0 naming a source in words**, against 10 of
  19 unverifiable before.
- **C-033** — 2 refused Serbian renderings kept their text instead of being erased. Serbian voiced at
  84.2 % of 19 thoughts, against 62.3 % of 77.

**One thing observed and not acted on.** `OLLAMA_KEEP_ALIVE` is set to `0` in the machine environment
and is doing nothing; what keeps models resident is the `keep_alive: "30m"` this repository sends on
every request, which overrides it. Three models were resident at the verdict hour — `qwen3.5:4b`
(3.08 GB), `qwen2.5:1.5b` (1.08 GB) and `paraphrase-multilingual` (0.16 GB), 4.32 GB in total, which
is more than the 4 GB the stability review recorded as the budget. Either that figure was wrong or the
budget is larger. Recorded as an observation; nothing is changed on the strength of it, and the
`keep_alive` line is not touched before an hour of deliberate measurement, as the stability review
already says.

**Nothing observed was changed.** The tool reads and prints; it writes nothing.

## C-043 — the refusal invariant was true in the letter and asserted nothing about the route

**2026-09-10, 12:40 UTC.** Not a false statement this record published. A missing one — found by
measuring §5.6.3 of pre-paper v4 instead of leaving it on the open list.

**What the guard has always asserted.** *No named refusal is polled.* True on every pass, and it was
never the whole question.

**What was never asserted.** Three of the fourteen refusers — **MUP**, **JKP Beograd-put** and
**JKP Gradska čistoća** — publish exactly the sort of notice this observatory exists to record, and
those notices are republished by municipalities, by the City portal and by the newspapers. Their
material reaches the record anyway, through doors they do not control.

**Measured before the rule was written:** **23 headlines naming Gradska čistoća** (via Novosti, Tanjug
and Dan u Beogradu) and **4 naming MUP** (via Euronews, Tanjug and Danas) are in the record; six and
two respectively were live in the published snapshot at that moment. **Every one of them was correct**
— each carried the outlet that wrote it and a link to that outlet, and no refuser appeared as a source,
a sid or an attribution anywhere. The practice complied. Nothing asserted that it did, which is the
same condition Article 41 attribution was in until 2026-09-10 made it a test.

**The rule, now written and enforced** (`research/07-legal/THIRD_PARTY_ROUTE_RULE_2026-09-10.md`):
where a named refuser's material reaches this record through a third party it is kept as *the third
party's utterance*, attributed to the third party, and the refuser is never named as a source of ours,
never counted among our sources, and never presented as having supplied anything.

**And its second half, which is not a formality.** *Nothing is filtered, suppressed or removed because
a refuser is named in it.* Drop the first half and a refusal becomes decorative — the record could take
everything a refuser withheld, one republication at a time, and still print its clean invariant. Drop
the second and something worse follows: a research project deciding which of a city's publications may
be seen, because an organisation declined to answer its emails. **A refusal is not a right to be
unmentioned.** `test_refusal_route.py` asserts both, including that the watch list is only ever used to
observe and count and never to drop a row.

**Two things the rule explicitly does not treat as violations,** because a check that flagged them
would be reporting findings it had not found: a refuser's name as a **place** (Aerodrom Nikola Tesla is
a location in Belgrade before it is an organisation that refused us, and a zone named after it is
geography), and a refuser named in **this project's own documents** — the registry, this ledger, the
permission dataset — where naming who declined is the opposite of presenting them as a supplier and is
the paper's central finding.

**What the watch list refuses to watch, recorded in the open.** `research/REFUSER_NAMES.json` names
*Politika* and *Vreme* as deliberately unwatched: they are ordinary Serbian words — "policy", and
"weather"/"time" — and a record full of weather cannot match on them without inventing findings.
Diacritics are folded before matching, so a rule written `gradska cistoca` sees `Gradska čistoća`; a
check that reads only one spelling is not a check.

**One thing tidied while there.** The guard's own line read *"14 refusals on file, none of them
polled"* with the 14 typed by hand. It is now counted from the registry, so it cannot go stale the way
every hand-typed figure in this project eventually has.

**Nothing observed was changed.** No stored row was touched, and no headline was removed, reworded or
withheld.

## C-044 — C-026, C-027 and C-028 were written down, in the code they fixed, and never carried here

**2026-09-10, 13:20 UTC.** Filed late and dated today. Nothing here is back-dated, and nothing below is
reconstructed from memory: every quotation is taken verbatim from the comment that has been sitting in
the published files since the fix, and every commit is named.

**What C-039 got wrong, and it is the fourth time today the same shape has appeared.** That entry said
three ids were "referenced by other entries and heading none of their own", and the pre-paper addendum
called them "corrections that were made, and cited, and never written down". They *were* written
down — as comments in the code they fixed, which is where a reader of that code will find them and
where the fix cannot drift away from its reason. What they were never given is an entry **here**, in
the ledger, which is the record's public claim about its own failures. A comment in a built HTML file
is not that claim.

So the defect is narrower and more interesting than "three corrections went missing": **the project has
two places where a correction can be recorded, and only one of them is the record.**

### C-026 — a frame that gains a scrollbar changes its own width, and everything centred in it slides

First in `4ac26ee`, extended in `212e82d` and `8b0a40b`. The comment, still in `docs/index.html`,
`monolog.html`, `podaci.html`, `sada.html` and `traka.html`:

> *"a frame whose own document gains or loses a scrollbar changes its content width, and anything
> centred inside it slides sideways. Reserve the gutter so the picture only moves when the data
> moves."*

And in `index.html`, the last of it:

> *"Switching a parameter changes how many stations have a value, so the table under the map gets
> longer or shorter, so the frame reports a different height, so the page crosses the height at which
> the window scrollbar appears…"*

A chain of four consequences from one hidden cause, which is why it took three commits to finish.
`scrollbar-gutter: stable` on the root of every frame and of the page.

### C-027 — the map is the rectangle, and the feed was reading three lines at a time

`027f972`. Two halves, both still commented in `podaci.html` and `monolog-puls.html`:

> *"The map is the rectangle, not a square inside it. The drawing box now takes the whole width and
> gets its height from the ground it draws: the basemap's own bounds, measured once, become the box's
> aspect ratio."*

> *"The feed and the three minds were reading three lines at a time because the frame's height is
> whatever its content asks for, and they were asking for very little. They ask for a proper column
> now, and the reader can change it."*

Cited later by **C-030**, which recorded that the theme was verified after C-027 by measuring the
background colour each frame resolved to — a check that was correct in both themes and blind to the
defect C-030 then found.

### C-028 — the drawing was 1108×831 and the city used the middle third of it

`81865a3`. Still commented in `podaci.html` and `monolog-puls.html`:

> *"The drawing was 1108x831 and the city used the middle third of it: the frame's bounds run to
> 44.98 N, but nothing we hear is north of Zemun and nothing south of Obrenovac. So the box is a 1.85
> rectangle now — shorter than the ground it draws."*

### And a mis-citation inside this ledger, which is the reason to check rather than to tidy

**C-029 says:** *"C-028 fixed every tile in the NOW panel to one height and recorded that the panel no
longer changes height with the range."*

That is not what C-028 was. The tile-height fix is `275b9b7` — *"every tile has one height in every
range"* — and it carries **no id at all**, in the code or anywhere else. It also landed **before** the
string `C-028` existed in this repository: `git log -S"C-028"` puts its first appearance in `81865a3`,
eleven commits later. So C-029 reached for the id of the commit immediately before it and attached it
to a different fix.

**C-029 is left exactly as written.** This entry is the correction to it, which is what an append-only
file is for. What follows from it:

- the tile-height fix of `275b9b7` has never had an id and does not get one now — inventing one today
  to fill a gap would be the same act as back-dating;
- **C-028 means the map rectangle**, on the evidence of the code and the commit order, and any future
  reader who follows C-029's sentence will land in the wrong place unless they read this;
- the pre-paper's open item is closed, and its wording — *"write them from the commits, dated today,
  marked late"* — is what was done, except that the commits turned out to be the second-best source and
  the code comments the first.

**The rule this leaves behind.** A correction may be commented in the code it fixes — it should be, and
these three are better documented in place than most entries here are. But **the ledger is the record**,
and a correction that exists only in a comment has not been admitted to anyone who is not reading that
file. Where the two disagree, the code is the evidence and the ledger is the claim, and it is the claim
that has to be fixed.

**Nothing observed was changed.** No code, no comment and no earlier entry was touched.

## C-045 — the publish said "nothing changed" while seventeen files sat staged

**2026-09-10, 12:41 UTC.** Found by checking whether the work of the previous hour had actually
reached the public repository, rather than by trusting the line that said it had.

**What happened.** `tools/publish_github.ps1` ran, printed *"nothing changed since the last publish"*
and exited 0. The export repository at that moment held **seventeen staged files** — the new frame,
its two data files, its test and a rebuilt `index.html` — none of them committed and none pushed. The
public site stayed one commit behind for five minutes, until the publish was run again by hand and
pushed `c1ad277..87bfddb`.

**The defect, which is more interesting than the incident.** The check was:

```powershell
$changed = (git -C $pub status --porcelain) -ne $null
if (-not $changed) { Write-Output 'nothing changed since the last publish'; exit 0 }
```

It cannot tell an **empty** status from an **unreadable** one. Git returning nothing because there is
nothing to say, and git returning nothing because it failed, are the same value here — and a failure
is entirely plausible in this exact spot: the scheduled publish task runs every ten minutes and takes
an `index.lock` on the same repository, and a `git status` that loses that race writes to stderr and
gives the caller an empty stdout. **A clean tree and a locked one read identically.**

This is the watchman's second lie — *it calls blindness success* — committed by the publish path,
which is the one part of this project that had no watchman over it. `research/STABILITY_REVIEW` had
already recorded that the automatic publish runs no tests; it had not noticed that the publish also
cannot tell whether it looked.

**Correction.** The exit code is consulted. A status that could not be read is reported as
`STOP: could not read the export status (git exit N). Nothing was published, and this is NOT
'nothing changed'.` and exits 2, so a caller that greps for the word *published* sees a failure rather
than a reassurance. The emptiness test is also made explicit rather than resting on PowerShell's
array-versus-null behaviour, which is where the ambiguity got in.

**What is honestly still not fixed.** Two publish paths — the scheduled task and a ship batch — still
run against one export repository with no coordination, so they can still race. The race is now loud
instead of silent, which is the part that mattered; making it impossible needs a lock this project has
not written, and that goes on the open list rather than into this entry as a claim.

**And the thing that found it.** Not a test. A check of the public repository's own log against what
had just been committed locally, done because the publish line came back blank in a ship batch and a
blank line is not a confirmation. **An exit code of 0 is evidence that something finished, never that
it happened** — rule 9 of the method, which this record has now had to apply to its own publisher.

**Nothing observed was changed.** No row, no entry and no published artefact was edited; one commit
that should have been pushed was pushed.

## C-046 — the gate protected the rare path and not the one the public sees

**2026-09-10, 13:10 UTC.** Not a false statement. A gate in the wrong place, which is the same thing
one publish later.

**What was true.** Every ship batch in this project builds, runs all 267 tests, and refuses to commit
if any fails. That gate fired twice today and was right both times.

**What was also true and had not been noticed.** `Beops_Publish` fires **every ten minutes**. It
exports the snapshot, rebuilds the history, runs `publish_github.ps1` — which rebuilds the whole site —
and pushes it. **It ran no tests at all.** So the check protected the path taken a few times a day by
hand, and not the path that produces almost every version of the page the public actually sees. On a
day like this one, that is roughly forty unchecked publishes against six checked ones.

**What reading the file changed about the fix, twice.** The first plan put the tests in
`publish_tick.bat`, before calling the publish script. Reading the script refuted it: `build_site.py`
runs *inside* `publish_github.ps1`, so tests placed before it would have checked **yesterday's page**
and passed it while today's went out untested — a gate that reports green on the wrong artefact is
worse than none. The second plan added a `-NoBuild` switch so the tick could build, test, then publish
what it had tested. That became unnecessary the moment the gate moved **inside the publisher**: the
thing that publishes is now the thing that checks, and every caller — the scheduled tick, any ship
batch, a person running it by hand — is gated by construction rather than by remembering.

**Correction.** The gate sits after the site is built and before anything is copied, committed or
pushed. On failure nothing is published and the live site stays exactly as it was; the export working
tree may be left half-rebuilt, which is harmless because every publish clears and rebuilds it, and the
last published commit is untouched. It runs under the same interpreter the suite is verified green
with, rather than the Inkscape-bundled Python the script otherwise uses, because a gate deciding
whether the city's page updates should not introduce a second interpreter as a variable.

**And the gate does not get to be silent.** Every run writes `data/live/publish-receipt.json`, and
`tools/guard.py` reads it: a suite that has just failed is a **warn**, one that has been failing for
half an hour — three ticks — is a **STOP**, because by then the public page is being kept deliberately
stale and somebody has to be told. A gate that stops the site quietly has exchanged one failure for a
better-hidden one, which is precisely what C-036 cost.

**The lock C-045 left open is closed too.** Two publish paths, one export repository: the second one
now refuses with `another publish holds the lock` and exits 4, instead of losing the race for git's
`index.lock` and reading an unreadable status as a clean tree. A lock older than fifteen minutes is
taken over, because a publish that takes that long has died. And because PowerShell does not run a
`finally` block on `exit`, the failing-gate path releases the lock explicitly — otherwise the first
outage would have caused a second one lasting fifteen minutes.

**What is honestly still weak.** The gate makes a failing suite freeze the public site. That is the
right trade — better stale than wrong — but it means a flaky or environment-dependent test can freeze
publication, and the suite already reads every row in the record and has grown from 6 to 13 seconds in
a day. When it is slow enough to matter, the gate is what will notice first, and the answer will not be
to weaken it.

**Nothing observed was changed.**

## C-047 — the loop was not broken, it was muted; and a third of the "refusals" were the model saying nothing

**2026-09-10, 13:50 UTC.** Both found by reading the refused rows again — the method that found C-034,
C-035 and C-037 this morning, applied a second time now that the checks are correct.

### The acceptance rate was measuring two failures as one

**16 of the 47 refusals since the cut have `text: ""` and `cites: []`**, refused as *"too short; cites
nothing inside the text"*. The gate is right to refuse an empty string. But the model **produced
nothing** — that is not the same event as producing something the record cannot support, and the
acceptance rate had been counting them together. Separated, acceptance since the cut is **19 of 50
that were actually said = 38%**, not 28.8%.

C-036 gave the organ a chain so that a model failing to answer is not silence. This is the neighbouring
case it does not cover: **the model answers, and the answer is empty.** No receipt calls that anything,
and until now no measurement did either. `eval_mind_effect.py` now counts *produced nothing* on its own
line and reports acceptance over what was actually said.

### The notebook loop reformed around its own fix

C-037's correction rendered the refusal reason as a sentence with no digits, so that a model copying it
could not import numbers that are by construction absent from the digest. It stopped the echo reaching
the page. **It did not stop the loop.** The refused sentence still went into the notebook, and the
notebook still quoted it back:

> `you said "The city's maximum values of PM10 and NO2 have significantly increased between 08:00 and
> 09:00 UTC, as indicated by the ' and it was refused because you named an hour outside the window you
> were given. Do not say it again." and it was refused because …`

The bolded half of that is **the new, digit-free wording itself**, pasted into the entity's sentence and
then handed back to it again. Measured: the skeptic (`qwen2.5:1.5b`) repeated this in rounds **369,
375, 381, 387 and 393** — five rounds of one sentence, each refused, each fed back.

**Quoting a sentence back to a model is not neutral. It is the copy.** For a sentence that was refused
*for containing the validator's words*, it is the whole mechanism.

**Correction.** A sentence refused as an echo is **never handed back**. The entity is told what
happened, in the digit-free wording, and told plainly that its sentence is deliberately not repeated so
that it cannot copy it — and asked for a new one from the facts. Everything that was not an echo is
still quoted verbatim, because for those the entity's own words *are* the feedback.

**The general form, which is the part worth keeping.** In any verbal feedback loop, the critic's
message and the model's own rejected output are both material the model will read as text to continue.
C-037 sanitised the first. This sanitises the second. *A rejected output may not be shown to the thing
that produced it when the reason for rejection was the output's form.*

### And one thing that is not a defect, but changes how the rate should be read

By model since the cut, over what was actually said: `qwen3.5:4b` **18 accepted of 48 (37.5%)**;
`qwen2.5:1.5b` **1 accepted of 17 (5.9%)**. The small model is almost never accepted — and C-036's
fallback chain means the small model speaks *precisely when the larger one has failed*, which is when
the machine is short of memory. **So the acceptance rate falls when the body is under pressure**, and
C-042 read that movement as a fact about the checks. `eval_mind_effect.py` now prints the per-model
split beside the rate and says so, because a number that moves for three different reasons has to name
them.

**Nothing observed was changed.** No stored utterance, reason or receipt was edited; the change is to
what the next prompt contains and to how the measurement is reported.

## C-048 — C-047's arithmetic was half-done, and it reached the ledger before the tests that would have stopped it

**2026-09-10, 14:25 UTC.** Two things, and the second is about how this record writes itself.

### The recount

C-047 reported that separating the empty utterances from the refusals raises acceptance since the cut
from 28.8% to **38.0%**, and let that stand as though it softened C-042's failed prediction. It does
not, because **the before-half has to be recounted the same way and it rises too**:

| | utterances | produced nothing | of what was said: accepted |
|---|---|---|---|
| before the corrections | 161 | 9 (5.6%) | 77 of 152 = **50.7%** |
| after | 66 | 16 (24.2%) | 19 of 50 = **38.0%** |

So the honest comparison is **50.7% → 38.0%**, a fall of 12.7 points — against the 13.9 points of the
uncorrected reading. Separating the empties makes both halves larger and **explains essentially none of
the fall.** C-047's own sentence, that the number "meant less than it was made to carry", was too
generous by half, and the recount is what said so.

**What the split does reveal is worse than what it was reported to soften.** The organ produces nothing
**four times as often as it did** — 5.6% of utterances before, 24.2% after. That is a regression no
check in this project can see, because from the outside the model answered. C-036 gave the organ a
chain for a model that does not answer; there is nothing for a model that answers with an empty string,
and this is now the largest single category in the refusal counts.

### And the ledger was written before the check that would have stopped it

The ship batch appends the correction to `CORRECTIONS.md`, then builds, then runs the suite, then
commits. On this occasion the suite **failed** — three of my own errors — and nothing was committed,
which is the gate working. But the ledger had already been appended to, and the ledger is append-only,
so the uncorrected C-047 could not be taken back out. The corrected text was written a few minutes
later and the appender, finding the entry already there, did nothing.

**So an append-only record was mutated by a run that was otherwise refused in full.** Here it came
right, because the fix was finished and committed twenty minutes later. Had it been abandoned, this
file would now describe a correction that does not exist in the code — which is precisely the failure
mode the ledger is supposed to make impossible.

**Correction to the process, not to the code.** The ledger append moves after the suite passes and
before the commit, in every ship batch, so that the only entries that reach it are the ones whose
change is about to be committed. The gate already refuses to commit untested work; it must also refuse
to *record* it.

**Why this is not fixed by being more careful.** It is the same shape as C-018 and C-045: an action
placed before its check, where the check's failure leaves the action standing. Ordering, not diligence.

**Nothing observed was changed.** C-047 stays exactly as written, incomplete arithmetic included; this
entry is the correction to it, which is what the file is for.

## C-049 — the layers that never change had no rule, and the obvious rule was the wrong one

**2026-09-10, 14:55 UTC.** On the stability review's open list since it was written, and left there
because the rule that first suggests itself does not work.

**What was missing.** Two of this record's layers are not streams: `basemap-belgrade.json` (the ground
the maps are drawn on) and `context-population.json` (how many people live near a station). Each is a
dated **release** of somebody else's dataset. Nothing anywhere said how old either may be, what would
make it wrong, or who should look at it.

**Why a maximum age would have been worse than nothing.** The Sava does not move, and a municipality
outline changes by law rather than by the hour; the population grid is a 2022 release and is not stale
at 34 hours and would not be at 34 weeks. **An age limit on these would have reported a fault every
single day and meant nothing on the day something actually changed** — a check that cries continuously
is a check nobody reads, which is the failure mode this record has already written about monitors
under a different name.

**What can actually go wrong, asked as four questions every guard pass.** Is it still there and
readable. Is it still the file we accepted — a change is not wrong, but it must be *noticed and
re-accepted* rather than absorbed, so a differing hash is a warn and never a silent update. Does it
still carry the source, licence and attribution under which we may show it. And has anybody looked for
a newer release lately — a date, not an expiry.

**The attribution question is the load-bearing one, and it is a legal condition.**
`context-population.json` is **CC BY 4.0**, and its attribution — *"Kontur Population: Global Population
Density for 400m H3 Hexagons (Kontur, 2023), CC BY 4.0"* — lives inside the file.
`basemap-belgrade.json` carries Natural Earth's. If a refetch drops either, or a page shows the layer
without naming it, this record is publishing somebody's dataset unattributed. **That is Article 41 for
data rather than for headlines**, and it is exactly the condition the news layer was in this morning
until attribution became `test_attribution.py`.

**Measured before the rule was written, and it holds.** Kontur and CC BY appear on the index and in the
monologue; Natural Earth on the index, the data view and all four document maps; **and on no page that
does not use them** — `sada`, `traka` and `svedoci` name neither, correctly, because neither reads
either file. So the practice was already right. Nothing asserted it, and the file carrying the
attribution is not the same thing as the page displaying it.

**Correction.** `research/STATIC_LAYERS.json` — generated from the files themselves rather than from
anybody's memory of them, so the recorded hash, source, licence and attribution are what is actually
there. Two guard checks on every pass, and `research/test_static_layers.py` on every ship, including
the one the guard states plainly: *a layer with no expiry must not be reported as fresh either, because
silence about it is indistinguishable from neglect* — which is the state these two were in for the
whole life of the project.

**And the check's own first version was wrong in a way worth recording.** It derived the phrase a page
must contain by cutting the attribution string at its first full stop — so it demanded *"Made with
Natural Earth"* from a page that says *"Natural Earth 1:10 mil. (javno vlasništvo)"*, and failed three
pages that were correctly attributed. **A licence requires the credit, not a form of words.** The
register now names the credit explicitly (`must_be_named`: Natural Earth; Kontur, CC BY) instead of
inferring it, which is the same rule this project applies everywhere else: write down what must be
true rather than deducing it from a prefix.

**Nothing observed was changed.** No layer was refetched, edited or moved; what changed is that they
are now described.

## C-050 — rule 1 was never checked, and when it was checked it turned out to be two rules

**2026-09-10, 15:40 UTC.** Found by a sweep asking, of each of the method's thirteen stated rules,
which test enforces it — and of each of the guard's fifteen checks, which test names it.

### What the sweep found

**The guard: fifteen checks, three named in any test. `guard.run` tested by nobody. The string `STOP`
in no test in the project.** Its own docstring promises that on a permission failure it *"does NOT
repair — it says STOP, loudly"*. Nothing asserted that. A refactor making STOP unreachable, or letting
an `unknown` resolve to `ok`, would have passed all 288 tests while the guard went on printing a clean
verdict — the guard being exactly the thing that is supposed to notice when nothing else does.

**Two stated rules with no test that mentions them:** *"five states, no sixth"* (rule 1) and *"a
correction is not finished until it is measured across the record"* (rule 11, written this morning).

**Eleven tools with nothing testing them**, including three that feed published figures:
`build_provenance_index.py`, which generates the index `paper_numbers.py` parses for the 313 captures
and 188 sources quoted in the pre-paper; `paper_numbers.py` itself, which produces **every figure** in a
document that says of them *"Nothing in this table is typed by hand"*; and `export_permission_dataset.py`,
the CC BY dataset published today. Also `make_maps.py` and `make_layers.py`, 47 KB that draw the
published maps including the attribution checked by hand in C-049.

### And rule 1 is kept, and is described wrongly

Measured before writing the test: **95,015 measurement rows carry no `state` field at all.** There is
no sixth state on rows because there is no state on rows — the epistemic state is computed where a
value is rendered, from `phenomenonTime`, `phenomenonTimeUnknown`, `phenomenonTimeCorrected`,
`resultQuality` and whether the result is null. That is a better design than a stored state, and it is
not what the method says.

**What the method says is that one vocabulary governs everything. There are two.** The epistemic one —
observed, untimed, estimated, forecast, unavailable — about what is known of a measurement. And a
pipeline one — thought, rejected, retracted, organelle, claim_settled, voiced, refused, organ_silent,
organ_failed — about what happened to a derived row. **They share the field name `state`, and they meet
in `public/live-snapshot.json`**, where a reader sees `"state": "estimated"` beside `"state": "thought"`
and has no way to tell that the first is a claim about knowledge and the second a note about a process.

So a reviewer checking rule 1 against the published artefact finds `organelle` and `organ_failed` under
`state` and concludes the rule is broken. It is not broken. It is undescribed, which for a record whose
value is its vocabulary is close enough to be worth fixing.

### Correction

`research/STATES.json` declares both vocabularies, every value with a sentence a stranger could act on,
and states plainly which single value — `estimated` — belongs to both and why.
`research/test_states.py` fails if either grows an undeclared value, if a measurement row ever gains a
`state` field, or if the published snapshot shows a state nobody wrote down. **A state nobody wrote
down is a state nobody decided.**

`research/test_guard_verdict.py` drives the guard's verdict logic with its checks replaced: a STOP in
any of the five groups reaches the verdict; an UNKNOWN can never report ok; STOP outranks UNKNOWN
outranks WARN outranks OK; every emitted check carries a state from the guard's own four and a reason;
the report prints the verdict it computed; and `REPAIRABLE` is still exactly `{disabled, not running}`,
so the guard cannot quietly acquire permission to repair something that should stop it.

### What is deliberately not fixed

**The shared field name.** Renaming `state` in a published artefact changes something other people may
already read, and it is worth doing on purpose rather than in the hour it was noticed. It is written
into `STATES.json` as a named defect and asserted to stay named, so it is a known hole rather than an
unnoticed one — and it goes on the open list with the other three items from this sweep.

**Nothing observed was changed.** No row, no state and no vocabulary was altered; what changed is that
both are now written down and checked.

## C-051 — the dataset about honesty published a working note, and a file that said it was machine-generated was typed by hand

**2026-09-10, 12:20 UTC.** Found while fixing a test I had written the hour before, which failed
because the data dictionary and the README stated the same caveat in two different sets of words.
Pulling that thread found two larger things behind it.

### What the dataset said about itself, and what was true

**`zenodo.json` — the deposition record prepared for a DOI — carried this sentence in its `notes`
field: "Generated by `tools/export_permission_dataset.py` from the observatory's own registry,
provenance ledger and collector configuration. Every figure in it is read from the files that hold it;
none is typed by hand."** Nothing generated it. I wrote it by hand, including that sentence, and
nothing in the repository could have produced it. Its title said "215 public data sources" as a typed
string. It had no `version` field at all, so a record about a versioned dataset did not say which
version it described.

This is the worst kind of error this project can make, and it was made in the dataset whose subject is
what a record is allowed to claim about itself. It went out because nothing tested a file that no tool
wrote.

**`DOI_TO_FINISH.md` — a working note to Semir — was inside `public/dataset/permission-landscape/` and
listed in the dataset's `MANIFEST.json` with a hash.** It named where this machine keeps a Kaggle
credential, presented local paths, and its own table said the dataset was "six files" while the
manifest listed eight. It was published under CC BY as part of a dataset that states it "contains this
project's own descriptions and decisions".

**The reason both got out is one line.** The manifest was built from `OUT.iterdir()` — a listing of a
folder. Anything left in that folder became part of a published dataset, with a hash, silently.

### And the small one that led there

The caveat the whole dataset turns on — what a status is *not* — existed in three copies, and the three
had already drifted. The README and the Zenodo record said "not a legal characterisation of any
organisation, not a compliance score, and not a ranking". The data dictionary, which the README tells
the reader to read *first*, said only "Not a legal characterisation and not a score". The two words it
had lost, "compliance score" and "ranking", are the two a reader is most likely to need.

### Correction

`tools/export_permission_dataset.py`:

- **`NOT_A_SCORE` is one sentence in one place**, quoted into the dictionary, the README and the
  deposition record. It cannot drift again because there is nothing to drift from.
- **`PUBLISHED` declares exactly what the dataset is.** The manifest is built from that list. A file
  in the folder that is not on the list stops the build with a message naming it, rather than being
  published.
- **`zenodo.json` is now generated** — version, publication date, title count, description counts and
  the caveat all read from the same registry as the CSVs. The sentence in `notes` is true for the
  first time.
- **`CHANGES.md`**: every version says what it is, relative to the one before. A published dataset
  whose text changes while its version does not is a quiet edit, which is the thing this record exists
  to refuse. Version **1.1**.
- `DOI_TO_FINISH.md` moves out of `public/` to `research/`, with the credential location removed.

`research/test_permission_dataset.py` fails if the caveat is stated in any file's own words rather
than quoted; if `zenodo.json` is not rewritten by the build that claims to write it; if it lacks the
version or carries a count that is not the count of rows; if the manifest is anything other than the
declared list; if a stray file in the folder does not stop the build; or if the current version has no
entry in `CHANGES.md`.

### And one more, found by the same batch of tests

`tools/paper_numbers.py` — the tool that produces every figure in the paper — built two of its
tallies straight from a `Counter`, so a row whose field was absent became **a category called `null`**
in the paper's own numbers: sources by status, and every derived drop by state. `null` is not a
category. It does not tell a reader whether the field was empty, absent, or never part of the
vocabulary. It is now named `(none written)`, and a test walks every figure and fails on any category
that is not a name a person could act on.

**And the figures had no time on them at all.** Writing a test that ran `paper_numbers.py` twice and
demanded the same answer produced a failure that was not the test's fault: 96,500 rows the first time,
96,510 the second, forty seconds apart. Four of the ten figures — the provenance ledger, the rows on
disk, the history and the mind — count a record the observatory is still appending to. The tool
printed all ten with no timestamp, so the paper cites a row count that was true at an instant nobody
can name, in a record whose entire subject is that a number without its time is not a measurement.
`paper_numbers.py` now stamps every run with `taken_at` in UTC and declares which four figures are
counts of a living record; the test demands stability of the six that are not, and of the four demands
only that the disk has not gone backwards.

### Measured, not assumed

`sources.csv`, `refusals.csv` and `captures.csv` are **byte-identical between v1.0 and v1.1**, verified
by SHA-256 before and after the rebuild: `7b965a84…`, `c7fe1be9…`, `137fcc1e…`. No row, value, status,
reason or hash changed. What changed is what the dataset says about itself.

### What this cost

The dataset was published at 11:53 UTC and this was found at 12:15 UTC — twenty-two minutes, on the
public record, with a false provenance claim inside it. Nobody read it in that window as far as I can
tell, and that is luck, not process.

## C-052 — the ledger of corrections was wrong about when it was written, by up to six and a half hours

**Written at the commit that carries this entry. Nobody typed a time into this line, and that is the
correction.** Found by looking up the format of a heading and noticing that the entry above it was
stamped 15:40 UTC when the clock said 12:18.

### What was measured

Thirteen entries in `CORRECTIONS.md` carried a hand-typed line of the form `**2026-09-10, 15:40 UTC.**`
Against the commit that introduced each one:

| entry | stated | written | out by |
|---|---|---|---|
| C-033 | 06:50 | 00:22 | **+6h28** |
| C-037 | 01:45 | 02:20 | −35 min |
| C-039 | 09:00 | 09:02 | −2 min |
| C-040 | 09:30 | 09:19 | +11 min |
| C-042 | 10:00 | 09:58 | +2 min |
| C-043 | 12:40 | 10:13 | +2h26 |
| C-044 | 13:20 | 10:21 | +2h58 |
| C-045 | 12:41 | 10:44 | +1h56 |
| C-046 | 13:10 | 10:58 | +2h12 |
| C-047 | 13:50 | 11:21 | +2h28 |
| C-048 | 14:25 | 11:25 | +3h00 |
| C-049 | 14:55 | 11:36 | +3h19 |
| C-050 | 15:40 | 12:01 | **+3h38** |

Ten of the thirteen are wrong. **The offsets are not constant, so this is not a timezone** — a
timezone would put every entry out by the same amount. It is a person typing a plausible-looking time
and drifting further from the clock as the hours went on. C-045 is stamped *earlier* than C-044 while
having been written twenty-three minutes *later*, so the ledger's own order contradicts the record it
sits in.

The other thirty-eight entries carry no time at all.

This is the file whose subject is that this project is honest about what it knows and when. It holds
C-025, *"the page prints UTC and the reader's clock does not, and nobody told the reader"*. It is
published, and the site counts from it.

### Correction

**A correction's time is the commit that introduced it. It is not typed.** `tools/correction_times.py`
reads that from the repository in one pass and writes `research/08-provenance/CORRECTION_TIMES.json`:
every entry, the commit that introduced it, the true UTC time, the typed time where one exists, and
the difference between them.

**The ten wrong stamps stay exactly where they are.** Corrections are appended, never edited, and that
rule does not stop applying because the error is embarrassing. They are named in
`correction_times.KNOWN_WRONG`, and `research/test_correction_times.py` fails if one of them leaves
that list — which is what would happen if a stamp were quietly tidied or the history rewritten.

The test also fails if any entry from C-052 onward types a time at all; if the entries are not in the
order they were made; if a time anywhere does not name the clock it is on; or if more than one entry
lacks a commit. **An entry may lack a time, but only the newest one, and only until it is committed:**
a correction that has not entered the record has no time, and saying so is more accurate than giving
it one.

### What this does not fix

The pre-papers carry the same kind of line — *"Figures verified 2026-09-09 19:07 UTC"* — typed by the
same hand and never checked against anything. That number has not been audited and is not asserted to
be right. It goes on the open list.

## C-053 — the open item from C-052, measured: the papers' typed times were right

**Written at the commit that carries this entry.** C-052 said of the line in the pre-papers — *Figures
verified ... UTC* — that it was the same kind of hand-typed stamp as the ten wrong ones in this ledger,
that it had not been audited, and that it was not asserted to be right. It has now been audited. It
was right, and saying so plainly matters as much as reporting a failure would.

### What was measured

Twenty-three documents in `research/06-paper/` were scanned for a time typed into the text. Two carry
one:

| document | states | committed | difference |
|---|---|---|---|
| pre-paper v3 | 19:07 | 19:30 | 24 minutes **before** |
| pre-paper v4 | 08:49 | 08:59 | 10 minutes **before** |

Both sit shortly *before* the commit that introduced the document they are in, which is exactly what
checking the figures and then writing the line looks like. Neither is out by hours, neither is out of
order, and there is no drift between them. The failure mode found in the corrections ledger is not
present in the papers.

**What was still missing is not correctness but evidence.** Nothing anywhere recorded that
`paper_numbers.py` ever ran at 19:07. The claim was true and uncheckable, which is a weaker thing than
it looked.

### Correction

`tools/paper_numbers.py` now appends one line per run to `data/live/paper-numbers-runs.jsonl`: the
instant, and a SHA-256 of the figures that run produced. A stamp in a paper written from now on can be
matched to a run that actually happened.

`tools/paper_stamps.py` audits every typed time in every paper against the commit that introduced the
document, and writes the result to `research/06-paper/PAPER_STAMPS.json` with a verdict per stamp:
*impossible*, *implausible*, *consistent but unevidenced*, *evidenced*, or *unevidenced*.

`research/test_paper_stamps.py` enforces the invariant that needs no run log — **a stamp may never be
later than the commit that introduced the document**, because figures cannot be verified after the
paper reporting them entered the record — and requires a match to a recorded run for anything written
from here on. The two audited offsets are frozen, for the opposite reason the ledger's ten wrong ones
are: a right answer is as worth protecting from a quiet edit as a wrong one is from a quiet tidy-up.

One thing was deliberately built the awkward way: the receipt log takes an explicit path so the test
can prove receipts are written **without writing test rows into the evidence**, and a second test
fails if auditing the stamps appends anything to the real log. An append-only record that anything but
a real run may append to is not a record of runs.

### Honest note

I raised this as a suspicion at the end of C-052 and it did not survive contact with the measurement.
Flagging something as unaudited is not the same as finding it wrong, and the entry that flagged it was
written in a half-hour when two other things had just turned out to be wrong. The number was fine.

## C-054 — the map counted an instrument it did not draw, and 47 KB of drawing code had no test

**Written at the commit that carries this entry.** The C-050 sweep listed `make_layers.py` (28 KB) and
`make_maps.py` (19 KB) as the largest surfaces in the project that nothing tested. They draw the
scheme on the landing page and the three maps cited in the paper. Both now have tests, and writing
them found a defect on the first run.

### What the maps were doing

**The legend said 53 citizen sensors. The map drew 52.**

One Sensor.Community sensor sits north of the window the maps use. Its coordinate projects to twelve
pixels above the top edge of the frame, so the browser clipped it and nobody saw it go. The legend
counted it, because the legend counts the register; the ground did not show it, because the ground
only shows what fits. A reader counting dots and reading the legend gets two different numbers and no
way to find out which is right.

The same mark was drawn off-frame on the coverage map. On the last-24-hours map it was counted among
the instruments heard and not drawn either.

This is the failure this project is least entitled to make: **a number in a picture that the picture
does not support.** It is C-028's family — the drawing was 1108×831 and the city used the middle third
of it — and the reason it survived is that nobody reads a picture the way they read a table.

### Correction

An instrument outside the frame is **not dropped from the counts** — it exists, it is in the record,
and a map that quietly shrinks its own subject is worse than one that admits an edge. It is said out
loud instead:

- the legend now reads `Sensor.Community citizen sensor (53) - 1 outside this frame, not drawn`
- the coverage and last-24-hours captions state how many were counted and not drawn
- `MAPS.json` records `outside_frame` and `outside_frame_by_source`
- the coverage field still uses every instrument, including the one outside: a sensor just beyond the
  edge still covers ground inside it, and pretending otherwise would put a false hole in the field

### The tests

`research/test_make_maps.py` — every point drawn is an instrument with a coordinate the snapshot
publishes; every name beside a dot is that instrument's own; the legend's counts are the marks
actually on the ground; a hollow mark means nothing was received and is counted as such; **no mark is
drawn outside the frame, and anything outside is stated on the face of the map**; every map names the
ground it is drawn on and the refusal that removed the boundaries; the same files draw the same map
twice; an empty snapshot draws nothing rather than inventing a dot.

`research/test_make_layers.py` — the polled sources are split between live and periodic without being
double-counted or dropped; one clock per periodic source and one ring per live source; the record
count written under the slab is the registry's; the static-layer count in the label is the register's;
the five states and no sixth, checked against `STATES.json`; every label exists in both languages and
no label belongs to neither; the ground and the census are named where they are drawn; the drawing is
well-formed and identical from identical registers; and **nothing overhangs the law** — the editor's
rule of 9 September, checked as geometry against the polygons actually emitted.

### Two things the tests got wrong first, worth recording

The law test looked for plates with `class="top"` and found none, because a plate is `top plain` or
`top accent`; it reported "no stratum plate is in the drawing" about a drawing full of them. And the
test for the registry count searched the SVG for a phrase that is plainly on the page — the drawing
wraps a line at 66 characters into separate elements, so the phrase exists on screen and in no single
element. **A test that reads an artefact has to read it the way it is written, not the way it looks.**

## C-055 — the gate can be killed by the size of the record it guards

**Written at the commit that carries this entry.** Found by the publish gate refusing a correct
commit: six tests died with `MemoryError`, none of them because anything was wrong.

### What was measured

`data/live/rows` is **78.5 MB across 28 files**. Two of them carry almost all of it: 41.3 MB for the
citizen sensors and 31.2 MB for the SEPA stations. The machine had **592 MB of 8.3 GB free** when the
suite ran.

Five tests read those files with `read_text(...).splitlines()` or `read_bytes().splitlines()`, which
holds the whole file *and* a list of every line in it — several hundred megabytes for one 41 MB file,
repeated for each test. One of them, in the permission-dataset test, wanted **the first 400 lines**
and read all 41 MB to get them.

### Why this matters more than the day it happened

The gate refused, nothing was committed and nothing was published, which is the right direction to
fail in. But the reason it refused had nothing to do with whether the commit was correct.

**A gate that fails for reasons unrelated to correctness is a gate whose refusals stop meaning
something.** If it cries wolf often enough, the habit becomes to re-run it until it passes — and the
run that finally passes is the one that proves nothing. This one would have started doing that on its
own: the row files grow every ten minutes, so the only question was which month.

The record outgrowing the tools that read it is not a bug in any one line. It is what happens to an
instrument that keeps running.

### Correction

`tools/record.py` — one place that knows how to read a record larger than memory: `lines`,
`count_lines`, `objects` (with an optional limit that stops reading at the limit), `files` and
`all_objects`. Nothing in it holds a whole row file, and nothing holds a list of its lines.

Converted to stream: `test_source_clock.py`, `test_states.py`, `test_refusal_route.py`,
`test_paper_numbers.py`, `test_permission_dataset.py`, and `paper_numbers.mind()`.
`paper_numbers.rows_on_disk()` was already streaming and is left alone.

### What is not fixed

**Why the machine had 592 MB free is not a code question and is not answered here.** It is on the
open list, and it is worth answering: an instrument that shares a machine with whatever else is
running on it can be stopped by that other thing at any time, and today it was.

Nor is there yet a test that the suite runs within a memory bound. The suite is now much cheaper to
run, which is not the same as being bounded.

## C-056 — the guard decides whether the collection is lawful, and almost none of its reasoning was driven by anything

**Written at the commit that carries this entry.** The C-050 sweep counted fifteen checks in
`guard.py` and found three of them named in any test. `test_guard_verdict.py` covered how the verdict
is folded from the checks — STOP outranks UNKNOWN outranks WARN outranks OK — but not what any
individual check concludes from any particular world. The thing that decides, every quarter of an
hour, whether this record is still allowed to collect what it collects was reasoning unobserved.

### What is checked now

`research/test_guard_checks.py` builds a small BEOPS on disk — registry, collectors, ledger,
snapshot, receipt, static-layer register, published pages — points the guard at it, and asks each
check what it says. Twenty-four tests:

- **polling a named refusal** stops and names the sid; **a polled source with no ledger line** stops
  and names it; **all seven unsettled statuses** (`lead`, `primary_page`, `needs_decision`,
  `restricted`, `blocked`, `account_required`, `token_required`) stop collection, each one driven
  separately, because a status that quietly stops stopping is a source nobody verified being polled
  while the guard says ok
- **a refuser appearing as our source** stops, whether as a source, a sid, or the input of a derived
  row; **a refuser named in somebody else's headline** is permitted and counted, with the outlet and
  its link; **the same headline without the outlet that wrote it** stops
- **the publish receipt**: absent is unknown, passing is ok, one failing run warns, forty minutes of
  failing runs stops, a passing receipt three hours old warns that the publisher may be stopped, and
  a receipt written by PowerShell with a BOM is still read — C-047, kept fixed
- **the static layers**: a missing file stops, a lost licence line is unattributed, a page that shows
  a layer and does not carry its credit stops, a changed file warns rather than stops because a
  change is not a fault, and a review date in the past asks somebody to look

### The failure all of it is built against

Not a check saying STOP when it should say OK. **A check saying OK when it cannot see.** Every check
here is also asked what it says when its inputs are missing, and the answer has to be UNKNOWN:
unreadable registers, no snapshot, no receipt, no static-layer register, and — the sharpest one — a
missing `REFUSER_NAMES.json`, where having no list of names to watch for means nothing is found,
which is not the same as nothing being there.

The one with teeth is the ledger. If the ledger cannot be read, the check that asks "is any polled
source missing its permission evidence" must not run at all: no ledger read means no sid missing
means everything fine. The test asserts that the evidence verdict is **absent** in that case and an
UNKNOWN stands in its place.

### Honest note: the meta-test passed on the first run, and would have passed on nothing

The last test in the file collects every check name the guard can emit and fails if one of them is
undriven. It passed immediately — and it would have passed just as happily if the regex reading
`guard.py` had matched nothing at all, because an empty set is a subset of anything. **A check that
finds no problem because it looked at nothing is the exact defect the other twenty-three tests are
about**, and I had written one into the file that names it. It now fails if it finds fewer than
twelve check names, and fails again if this file drives a check the guard no longer emits.

### What this did not find

Nothing. Every check behaved correctly on the first run against every world it was given. The guard
was right; it simply was not verified, and those are different things — which is the same result as
C-053 and worth saying as plainly.

## C-057 — the vocabulary was closed in the declaration and open in the record, and the test that enforces it was reading two files out of eight

**Written at the commit that carries this entry.** Found while collecting the figures for pre-paper
v5: the mind's tally of states included a category called `failed: HTTPError`, which is not a state.

### What was measured

`research/STATES.json` declares fourteen values across two vocabularies, and
`research/test_states.py` is supposed to fail if a row carries one that is not declared. Scanning
every derived file:

| file | states | seen by the test |
|---|---|---|
| the mind's month | rejected 139, thought 109, organelle 253, retracted 1 | yes |
| the claims register | 26 rows with no state at all | yes |
| the connector's notebook | thought 46, rejected 38, claim_settled 19, retracted 1 | **no** |
| the observer's notebook | thought 43, rejected 39, claim_settled 5 | **no** |
| the sceptic's notebook | rejected 62, thought 20, claim_settled 1 | **no** |
| voice benchmark, 10:02 | voiced 1, refused 1, **failed 1** | **no** |
| voice benchmark, 10:19 | **failed 3** | **no** |
| the news month | estimated 1814 | yes |

**Two files of eight were scanned.** The six it never opened held 278 of the 806 derived rows — and
both files carrying an undeclared value were among them.

The cause is one character of glob. The test listed `*.jsonl` at one directory level; the record
nests, one subdirectory per entity notebook and one per benchmark run. **The declaration the test
enforces said `derived/*/**.jsonl` all along** — the file being enforced described the layout
correctly and the enforcement did not read it.

Four values were in the record and not in the declaration:

- **`failed`** — written by the voice benchmark for the event `organ_failed` already names. Four rows.
- **`derived`**, **`nothing_to_do`**, **`paused`** — written on organ tick receipts rather than on
  rows. `derived` reaches the published snapshot, where it was passing the test **because the test
  allowed it by name**: `allowed = epistemic | pipeline | {"derived"}`.

That last one is the worse of the two shapes. An undeclared value slipping past a blind scan is an
accident. An undeclared value written into the test as an exception is a decision — and a decision
recorded where nobody looking for the vocabulary would ever find it.

### Correction

All four are now declared in `research/STATES.json` (schema `v2`), each with a sentence a stranger
could act on. `failed` is declared rather than corrected, and the declaration says why: **a row is
never edited, so a value the record contains is a value the vocabulary has to contain.** New code
writes `organ_failed`.

The hard-coded `{"derived"}` allowance is gone from the test: *an exception in a test is a declaration
nobody can find*, and `how_to_add_a_state` now says so.

`test_states.py` walks the tree instead of one level, and a new test fails if the scan ever counts
fewer files than the record holds — because every assertion in that file is otherwise being made
about a fraction of the record while reporting on all of it.

### What is not fixed

**The 26 rows in the claims register carry no state at all**, and the test skips a null state rather
than judging it. Whether a settled claim ought to carry one is a real question and not a typo; it
goes on the open list rather than being decided in the hour it was noticed.

And the field-name collision named in C-050 is now three-deep: the voice benchmark writes a
rendering's outcome under `state` too. Still not renamed, still named.

## C-058 — nineteen corrections in eight hours, and what the count actually measures

**Written at the commit that carries this entry.** Not a defect: a reading of the ledger itself,
recorded here because pre-paper v5 makes a claim about this record's own correction rate and that
claim needs to be in the record before it is in a paper.

### What was counted

Between pre-paper v4 and pre-paper v5 — eight hours — nineteen entries were added: C-039 to C-057.
Read together rather than one at a time, they are three kinds, and the proportions are the finding:

| kind | entries | share |
|---|---|---|
| a check that reported success while reading less than it was believed to read | C-041, C-043, C-046, C-049, C-050, C-051, C-054, C-056, C-057 | **9 of 19** |
| the record making a false statement about itself | C-051 (a hand-written file declaring itself machine-generated), C-052 (ten timestamps wrong by up to 6h28) | 2 of 19 |
| everything else — arithmetic, ordering, encoding, memory, and one audit that cleared what it was sent to find | C-039, C-040, C-042, C-044, C-045, C-047, C-048, C-053, C-055 | 9 of 19 |

C-051 is in two rows because it is both.

### What the number means, and what it does not

**The rate of corrections measures how hard anybody looked, not how much was wrong.** Nineteen in
eight hours is not a project falling apart and it is not unusual diligence. It is what one day of
reading outputs and asking what they counted produces on a record of this size. Every one of the nine
blind checks had been passing for days or weeks; none was found by a monitor, an alert, or a failing
test.

A record that publishes its correction count therefore has to publish that sentence beside it, in the
same way the acceptance rate is published beside the reasons for the refusals. A reader who takes
either number without the sentence next to it will draw the opposite conclusion, and in both
directions: a high rate reads as chaos, a low rate reads as quality, and neither reading is supported.

### Why this is a ledger entry rather than a paragraph in the paper

Because the paper cites it. §4.7 of pre-paper v5 names the blind-check family and rests on the count
above; §9 states the rate-measures-attention rule as the thing v5 must not be allowed to imply. Both
sentences are claims about this record, and a claim about this record belongs in this record first,
where it can be checked against the entries rather than against a document that summarises them.

## C-059 — the same rule fixed twice, in one file each time, and a PDF tool that had never run on this machine

**Written at the commit that carries this entry.** Found by the publish gate refusing pre-paper v5.

### The rule that existed in a file instead of in a function

Pre-paper v5's §2.6 quotes the format it abolishes — a hand-typed verification stamp — as an example
of what was wrong with the ledger. `tools/paper_stamps.py` read that quotation as **v5 stating its own
verification time**, computed it as 74 minutes *after* the commit that introduced the document, and
called it impossible. Which it would have been.

The gate refused the publish. Nothing untrue reached the site, and the commit stands with the document
in it.

**The uncomfortable part is that this was already fixed.** Four hours earlier, `correction_times.py`
had exactly this defect — C-052's own entry quotes the stamp format, and the rule that abolishes typed
stamps read the quotation as a typed stamp and refused the entry that introduced it. The fix there was
one line: strip inline code spans before looking. **It was written into that file.** `paper_stamps.py`
was written afterwards, by the same hand, on the same afternoon, without it — and with a document that
quotes in italics and quotation marks rather than in backticks, so even a copied line would not have
been enough.

*A rule that exists in one file is a rule the next tool will not have.*

`tools/prose.py` is that rule, once: `claims(line)` returns what a line asserts in its own voice, with
code spans and quoted runs blanked — blanked rather than deleted, so a caller reporting a column is
still right about where it looked. Both tools import it. `research/test_prose.py` asserts that neither
tool has grown its own copy again, by reading their source for the pattern.

### The tool that had never worked here

`tools/md2pdf.py` renders these working documents to PDF. It named exactly one font directory — the
Debian one — and this project runs on Windows. **It could never have produced a PDF on the machine
that holds the record**, and nobody found out until a document was handed to it, four pre-paper
versions after it was written. It was on the C-050 list of tools nothing tests.

The font is not cosmetic. Serbian is written with č, ć, ž, š and đ, and a font without those letters
draws boxes — reportlab substitutes silently and says nothing.

So the tool now searches an explicit override, four Unix locations, matplotlib's bundled copy, any
font directory inside the local runtimes, and both Windows font directories; and it decides what to
use by three rules in this order:

1. **A font is never trusted because of its name.** Its character map is read and it must actually
   contain the ten letters. A test proves a Python file and a symbol font both fail this.
2. **Any family that passes may be used**, not only DejaVu.
3. **Among those, the family that can draw the most of the seven faces wins.** The first version of
   this fix preferred DejaVu unconditionally and produced a document **with no bold at all**, because
   the only DejaVu on this machine is a single regular face bundled inside a PDF utility — in a set of
   documents where the load-bearing sentence of every section is bold.

What it chose is printed on every run: *Calibri/Consolas/Times (7 of 7 faces)*, with a note saying
DejaVu was not complete here. A converter that swaps a font without saying so changes a document
quietly.

`research/test_md2pdf.py` covers all of it, including that the PDF written is a PDF and large enough
to hold the document.

### Honest note

Both halves of this entry are the same mistake at different scales. A fix that lives in one file does
not reach the next file; a search that names one directory does not reach the next machine. **Neither
was found by a test, and both were found by the gate refusing something correct** — which is the third
time today the gate has been the thing that noticed.
