# Decisions

Append-only, like the corrections ledger and for the same reason. A correction records something
that was wrong. This records something that was **chosen** — where the record could have gone one way
and went another, with the reason, on the day. A decision that is not written down becomes, a month
later, an omission nobody can account for.

Format: an id, the decision in one sentence, what it costs, what it does not change, and who made it.

---

## D-001 — no counsel is engaged, and no letters are sent

**Decided 2026-09-10 by Semir Poturak, on the analysis in pre-paper v5 §5.**

Two items sat at the top of the open list from pre-paper v3 through v5: engage a lawyer, and send the
35 letters. Both are dropped.

**The reasoning.** The question the lawyer was for is *are we breaking the law*, and the answer on the
analysis is no. The record already behaves as though the favourable reading of the Copyright Act does
not exist: all 33 legal readings are marked *pending counsel*, nothing was enabled on the strength of
them, and the four sources that reading found were entered as leads marked NOT TO BE ENABLED. **The
instrument's behaviour does not change by dropping this item, because the instrument was never using
the thing counsel was going to check.**

**What it costs, stated plainly and against the decision.**

1. **The paper loses its control condition.** The central claim is that permission, not capability, is
   the binding constraint. That claim currently rests on 14 refusals *collected passively* — from
   terms pages and robots files, from organisations that were never asked. The letters would have
   turned an assertion into a distribution: who answers, who refuses, who ignores, how long each
   takes. A reviewer is entitled to say the 1-of-19 measures not having asked. Pre-paper v5 §6 called
   the letters "§2.9 with a control condition", and that section is now describing an experiment that
   will not be run.
2. **Group C is given up too, and it was the one with nothing in it to check.** Nine organisations
   that already refused would have been told, in writing, that their refusal is honoured. It contains
   no legal assertion, no request, and nothing a lawyer would need to read. It is dropped with the
   rest because the decision is to stop with letters, not to triage them.
3. **§5.4 stays a question forever.** The reading that Articles 43(1)(4) and 43(1)(2) positively
   permit the practice is careful, evidenced, and now permanently unreviewed. The record therefore
   stands on the weakest available ground — the absence of objection — **by choice rather than by
   circumstance**, and the paper has to say so in those words.

**What it does not change.** Not one line of what is collected, polled, published or refused. Every
named refusal is still honoured and asserted by the guard on every run. The čl. 24 public notice
stands. The right to object stands, with the 30-day retention rule behind it. If an organisation
writes to complain, it is honoured the same day, and that path was never dependent on a letter having
been sent first.

**How this must be reported.** Not as "the legal questions are settled". They are not settled; they
are **not being asked**, which is a different sentence and the one that goes in the paper. §8 of the
next pre-paper drops items 1 and 4 and states this decision and its cost in their place.

## D-003 — every model that touches BEOPS is named in public

**Decided 2026-09-15 by Semir Poturak** ("we will record it publicly, for all models"), after the
independent review found that the page said the processing stays on the authors' computer while the
experimental AI panel was written by a model in the cloud.

**Runs on the authors' computer; its input does not leave it.**

| Model | Licence | Role |
|---|---|---|
| qwen3.5:4b | Apache-2.0 | the mind's Observer and Connector; the Serbian voice |
| qwen2.5:1.5b | Apache-2.0 | the mind's Skeptic; the news-sorter (on CPU) |
| llama3.2:1b | Llama 3.2 Community Licence | the surprise ranker |
| paraphrase-multilingual | Apache-2.0 | headline similarity (embeddings) |
| qwen2.5:3b | Qwen Research Licence (non-commercial) | fallback only, when the models above do not answer |

**Runs outside Serbia.** The experimental "AI observations" panel is written by **Google Gemini 3.8
Flash** (low and medium effort) through the Antigravity CLI, on the authors' account. Each request
carries up to eight recent values from permitted measurement sources (air quality, citizen sensors,
parking, weather, rivers), the modelled population total of the observation window (Kontur, CC BY 4.0),
and statistical tables whose published licence allows external AI use. It never carries headlines,
article text, permission evidence or anything about a person. Its text is checked for structure,
citations and numbers only - not for whether its interpretation is right - and it is marked as AI
output on the page.

**Wrote code and documents.** Claude (Anthropic), Codex (OpenAI) and Gemini through Antigravity
(Google) worked in this repository for the authors. Every commit is authored by Semir Poturak; the
models that took part are named in commit trailers and in `LOG.md`.

**What it costs.** The sentence "nothing leaves the machine" is true for the local organs only, and the
page now says where the exception is. A reviewer can object that measurement values from Serbian
public sources are processed by a US provider; the answer is that those values are already public and
openly licensed or permitted, and that the panel is labelled experimental.

**What it does not change.** No source is added and none is removed. The local organs keep
`allow_cloud: false`. The panel can be switched off with `public_enabled: false` in
`research/AI_FEED.json` without touching anything else.
