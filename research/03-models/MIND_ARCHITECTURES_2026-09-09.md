# The mind of the observatory: three entities, one conversation, checked by code

Status: current · Date: 2026-09-09 · Author: Svemir (claude-cowork) for the authors · Supersedes: nothing (first document on the subject); extends `ORGANS.json` (organ `mind` 0.2.0) and §13 of the working document v1.1 · Editor of record: Semir Poturak

## 1. What the authors asked for, and what this answers

The interface of BEOPS is a monologue: the city speaking in receptions. On 9 September the authors asked for the monologue to become **real** — an entity thinking about what it sees — and then for **three** such entities in **conversation**, with **a system of learning and checking**, built on the small local models that fit under a desk, so that architectures and orchestrations can be examined now and the product can grow with better hardware later.

This document says what was built, what is being compared, how it is kept honest, how it learns without being trained, how it is scored, and what the literature warns about. It is the research frame for the second contribution of the paper: not "a model that talks about the city" but *an architecture in which small local models may talk about the city without ever being allowed to say something the evidence does not carry* — and in which their talk is measured.

## 2. The layers

| Layer | What it is | Who produces it | State on the interface |
|---|---|---|---|
| Senses | one deterministic sentence per reception, silence, organ run — built from receipts, never from a model | `monolog-puls.html` over `live-snapshot.json` | observed / untimed / silent, chromatic only where measured |
| Digest | the same evidence rendered as numbered facts F1…Fn, with the set of every number those facts contain | `organ_mind.py digest` | not shown; stored per conversation in `data/live/derived/mind/digests/` |
| Mind | three entities read the digest, think aloud in the first person, answer each other | `organ_mind.py run` on local models | **thought** — dashed mark, entity name, model id, `ai_generated=true` |
| Check | every utterance validated by code before anyone sees it; claims settled against later snapshots | `validate()` and `organ_mind.py score` | rejected utterances never shown; scoreboard public |
| Editor | a person reads a weekly sample and every settled claim; can pause the organ with one file | editor of record | corrections appended to `CORRECTIONS.md` |

The senses do not depend on the mind. If the mind is silent, paused or refused, the monologue still says what arrived and what stayed silent. That ordering is the design: the entity thinks *about* the record, it is never *the* record.

## 3. The three entities

| Entity | Temperament (the prompt's one sentence) | Model family (first present wins) | Why this one |
|---|---|---|---|
| **Posmatrač / Observer** | notices — what arrived, what is missing, what changed; does not interpret beyond the facts | qwen2.5:3b → qwen2.5:1.5b | the most capable local model on the PC, spent on the entity that must be most literal |
| **Sumnjalo / Skeptic** | doubts — what the facts do *not* carry: reception vs measurement, missing measurement time, what we do not know; says so when the others overreach | llama3.2:1b → llama3.2:3b → qwen2.5:3b | a different family, so that a shared misconception is less likely to be shared |
| **Povezivač / Connector** | connects — two facts, the hour, the weekday, one sense with another; proposes hypotheses and, when it can, one checkable claim | lfm2.5:1.2b → qwen3.5:0.8b → qwen2.5:3b | a third family; the entity most likely to be wrong, and therefore the one whose claims are worth scoring |

Heterogeneity by family is deliberate, not decorative. The one result the multi-agent literature agrees on is that agents of the same model converge on the same errors (§8).

## 4. One conversation

Every 30 minutes (`Beops_Mind`, S4U, `mind_tick.bat`):

1. `score` settles every claim whose deadline has passed, from the snapshot as it is now, and writes the outcome into the claimant's notebook.
2. `run` builds the digest over the last 6 hours and stores it with its SHA-256.
3. **Round 1** — each entity, alone, with its own notebook read back to it, writes `{sr, en, cites, hypotheses, questions, next_check, claim}` as constrained JSON.
4. Each utterance is validated (§5). Refused ones are logged and **not passed on**.
5. **Round 2** — each entity reads the other two's *validated* round-1 utterances and answers: agrees, disputes, refines — still citing facts.
6. A receipt records models, calls, accepted, refused, reasons. The snapshot carries only accepted utterances; the site shows the conversation as one block: three voices, replies indented, hypotheses and claims on their own lines, the models named.

Six local model calls per conversation. On the PC's CPU a 3B model takes minutes per call; the task's time limit is 28 minutes and a second instance is never started while one runs.

## 5. What the validator refuses (and why each rule exists)

| Rule | Refuses | Why |
|---|---|---|
| Numbers | any number in `sr` or `en` that is not in the digest's number set | the one way a small model lies fluently is a plausible number; the digest is the closed world of numbers it may use |
| Fact ids | any `[F…]` that does not exist; an utterance that cites nothing | a thought must point at evidence |
| Future as fact | "will", "biće", "sigurno će" without a hedge ("možda", "if", "might"…) | a prediction is allowed only as a *claim* with a fixed shape, so that it can be scored |
| Claim shape | anything but `reception(sid, within_minutes)` or `spread(sid, parameter, lo, hi, within_minutes)`; horizons outside 5…1440 min | only claims a program can settle are claims |
| Length | under 20 or over 900 characters per language | a thought, not an essay |

A refused utterance is kept as `state: "rejected"` with every reason, in the same append-only file as the accepted ones. It reaches the entity's notebook (so it learns), the receipt (so the run is honest), and the scoreboard (so the reader sees the refusal rate) — but never the other entities and never the public page.

## 6. Learning without training

No weight changes. Each entity has a notebook (`notebook/<entity>.jsonl`): what it said, whether it was refused and why, and how its claims scored. The last three entries are read back to it in its next prompt, in words:

> Tvoja beležnica: 01:58 „PM10 do 41 u 7777 stanica" → ODBIJENO (number not in digest: 7777); tvrdnja: false.

This is the Reflexion pattern — verbal feedback as memory — chosen because it is the only form of learning that (a) works on a CPU tonight, (b) leaves a public, readable trace of *what* was learned, and (c) can be switched off by deleting a file. Whether small models actually improve their refusal rate under this feedback is one of the measurable questions (§7). If they do not, the notebook still serves as the audit trail.

## 7. What is measured (the experiment)

Per entity, per model, per week — all computable from the files, all public in `mind_scores`:

| Metric | Meaning | First honest reading |
|---|---|---|
| Refusal rate | refused ÷ utterances | how often a family invents a number or cites nothing; expected to differ by family and to fall (or not) with the notebook |
| Citation density | facts cited per utterance | does the entity actually point at evidence |
| Claim rate | claims ÷ utterances | does the entity commit to anything checkable |
| Claim accuracy | true ÷ (true + false) | worth nothing before a week of series; after that, the only number that says whether the mind knows the city |
| Disagreement rate | round-2 utterances that dispute a round-1 one | is round 2 a conversation or an echo |
| Editor agreement | sampled utterances the editor accepts as fair readings | the human number |

Comparisons the design supports without new code: entity × model family (swap the register), notebook on/off (delete `notebook/`), round 2 on/off (one round), digest window (6 h vs 24 h). Each is one line in `ORGANS.json` and a dated note in this file. The claims file settles across configuration changes because a claim carries its model and its conversation id.

## 8. What the literature warns, and how the design answers it

- **Councils reduce hallucination, at a price.** Council Mode (arXiv 2604.02923, April 2026) reports a 35.9 % relative reduction on HaluEval with three heterogeneous frontier models, at 2–3× latency, and states that a misconception shared by all experts is reproduced, not caught. → Heterogeneous families here; latency accepted (30-minute cadence); the *validator*, not consensus, is the last line, because consensus cannot catch what the digest does not contain.
- **Debate can amplify falsehood.** The hallucination-amplification literature on multi-agent debate names echo, sycophancy, confident-but-wrong voting and context bloat as the mechanisms, and evidence grounding, independent verification, heterogeneity, provenance logging and a human interrupt as the mitigations. → Only validated utterances are exchanged; the digest is the grounding; every utterance carries digest and prompt hashes; `PAUSED` is the interrupt.
- **Small models cannot keep an index.** BEOPS's own C-013: a 3B model shifted every answer by one headline. → Binding is by content (fact ids inside the text, numbers checked against the digest), never by position.
- **Reflexion works when feedback is specific.** → The notebook carries the validator's exact reason and the claim's exact outcome, not a score.

## 9. Hardware path

Tonight: four local models on one CPU, minutes per utterance, one conversation per half hour. That is enough to examine architecture and orchestration, which is the point of this phase. When a GPU is available (the authors offered a Kaggle API; a rented GPU hour is the other route), the same files support: (a) replaying every stored digest through larger local models to compare families at equal evidence — `digests/` is the benchmark, already collected; (b) one conversation per five minutes; (c) a fourth entity with the static context of §10 read in. Nothing in the architecture changes — only the register and the cadence.

## 10. What comes next (in order)

1. **Static and semi-static context** (the authors' request of the same night): a small register of lawful layers — Kontur population (H3, CC BY), GHSL/WSF built-up, WorldCover, Copernicus DEM, JRC flood hazard, the road network on data.gov.rs, the Official Gazette (no copyright, Art. 6(2)) — each captured once with its hash, reduced to a *zone context* the digest can carry ("Zemun: dense, low, on the river"), and shown as quiet layers on the map. One layer per question the mind will actually ask; not everything that exists.
2. **Week of series**, then the first honest reading of claim accuracy.
3. **series-watch** (organ 3) as a fourth voice that speaks only in ranges from its own history — the entity that makes the Connector's claims testable against a baseline.
4. The editor's first weekly sample, and the first corrections.

## Honest verdict

**Checked:** the validator against grounded and ungrounded answers (11 offline tests, green); a two-round conversation with a fake model, including a refused round-1 utterance that must not reach round 2, the notebook read back, and claims settled true/false from a later snapshot; the conversation rendered on the monologue page from a sample snapshot. **Concluded:** the architecture is honest by construction — a wrong number cannot reach the public, and a prediction cannot be stated as a fact — and its value as intelligence is *unknown until scored*, which is the design. **Not looked at:** any real utterance of the three models on the PC (the first scheduled conversation runs after this document); how the small models behave in Serbian at temperature 0.5; whether the notebook improves refusal rates — that is the experiment.
