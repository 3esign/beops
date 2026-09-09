# The mind, 0.3.5: every public word in ekavica, and what the body can carry

Status: measured (first night of 0.3.4, the ekavica census, the voice bench and the hardware
diagnosis of 2026-09-09; the receipts of the drip under 0.3.5 are the running test)
Date: 2026-09-09
Author: claude-cowork, for the editor of record
Supplements: `MIND_ARCHITECTURES_2026-09-09.md` (the design), `../ORGANS.json` (the register)

## 1. The instruction

The editor's rule of the day: **the entities speak pure Serbian ekavica — no ijekavica, all
text.** Not only the thought: its hypotheses, its questions, every line the public page shows.

## 2. What was true before the rule was code

A census of the first night's rows (`data/live/derived/mind/2026-09.jsonl`, 90 rows):

| | count |
|---|---|
| utterances accepted by the validator | 41 |
| of these, rendered in Serbian and accepted by the old voice check | 18 |
| of these 18, carrying an ijekavian or Croatian word | **18** |
| words the old check knew | 8 stems |

The words: *vrijednost, promijenile, utjecaj, vjerojatnost, sugerira, sljedeće, posljednjoj,
mjerenja, gdje, razmjeri, provjeriti.* And beneath the ijekavica, the Serbian of qwen2.5:3b
was weak even where it was ekavian — *"Populacijska tčinjenica"*, *"znakomati"*, *"Grad ješu
stanice"* — sentences no Serbian reader would accept, which the old check accepted because
they contained Serbian function words and the right numbers.

So the first honest statement is: **the Serbian page of the first night was not Serbian.** It
was ekavian-looking word salad with an ijekavian accent, passed by a check that looked at
numbers and citations and not at the language.

## 3. What 0.3.5 does

**A list, not a rule.** `ijekavian_hits(text)` is a compiled list of about three hundred
stems: the long and short reflexes of jat (*vrijem-, vrijed-, mjest-, mjer-, gdje, sjed-,
djec-…*) allowed after the usual verbal prefixes, and Croatian-standard lexis that ekavian
Serbian never uses (*tjedan, tisuća, utjecaj, sustav, povijest, kolodvor…*). Matching is
word-initial, so the ekavian words that only look ijekavian stay clean: *Srbije, linije,
informacije* (genitives of -ija nouns), *prijem, prijava, prijatelj*, *dijeta, pijaca,
hijerarhija*, *objekat, odjednom, sjediniti* (Sjedinjene Države), *kolovoz* (the roadway),
*travnjak*, and *đ* written as *dj* (*gradjevina, medju*). The test file carries both lists —
fourteen sentences that must be caught, fourteen that must pass — and the guard is applied to
the thought, to every hypothesis and to every question.

**One call, one retry.** `voice()` renders the thought, its hypotheses and its questions in
one JSON answer, validated as a whole (numbers only from the original, citations unchanged,
Serbian function words present, no English leakage, no ijekavian word, item counts equal).
If refused, the model is asked once more with the refusal read back — *"Prethodni pokušaj je
odbijen (ijekavian: dvije). Ispravi to i piši isključivo ekavicom."* — at temperature 0.1.
If refused again, the row keeps the English on disk and the Serbian page shows the program's
own sentence: *Misao nije izgovorena na srpskom… Ćutanje je zapis kao i svako drugo.*

**No English on the Serbian page.** Before 0.3.5 a refused rendering fell back to the English
original under the Serbian entity name, and hypotheses and questions were shown in English
always. Now the Serbian page carries Serbian only; the English page is unchanged.

**The past re-checked at export.** Rows voiced under the old guard are re-validated when the
public snapshot is built; a row with an ijekavian word is exported as *refused at export* —
the row on disk is untouched (evidence is immutable), the page simply does not show it.

## 4. The voice bench, and what the body turned out to be

`organ_mind.py voice-bench <models…> --n N` renders the last N accepted thoughts with each
candidate voice model through the same validator and writes one line per rendering as it
happens. The first run, on qwen3.5:4b (Apache-2.0, 201 languages, pulled that morning):

> Maksimalne vrednosti PM10 i NO2 u gradu su se povećale sa 85 na 119 µg/m³ i sa 80 na 84
> µg/m³, odnosno između 08:00 i 09:00 UTC, kako je pokazao model rasprostranjenja. Očekuje se
> da će vrednosti za sledeću sat vremena biti proverene kako bi se potvrdila ova pretpostavka.

— the first Serbian sentence of the project that a Serbian reader would not correct (one
gender slip, *sledeću sat*). Then the bench timed out twice, and one rendering came back with
empty fields. The diagnosis, run the same hour:

| measurement | value |
|---|---|
| body | Intel i7-7700K (4 cores), **8 GB RAM**, Radeon RX 580 **4 GB** |
| qwen3.5:4b, `think=false`, warm | 28 tokens in 3.6 s — **7.8 tok/s on the GPU** |
| qwen3.5:4b, cold load | 84 s |
| qwen3.5:4b, thinking left on | 600 tokens of thinking, **empty content** |
| qwen2.5:3b + qwen3.5:4b resident together | 5.3 GB of models on a 4 GB GPU with 0.5 GB of free RAM — thrash; the 553-second call |

So the two failures had two causes, neither of them the model's Serbian: a thinking-capable
model that was allowed to think its budget away (the empty fields), and a body that cannot
hold two models (the hang). The first was already handled in code for any model whose name
begins with a thinking family (`think=false`); the second is a register decision.

## 5. The decision

One main model. **qwen3.5:4b thinks (Observer, Connector) and voices.** The Skeptic stays on
qwen2.5:1.5b for heterogeneity by family — a shared misconception is less likely to be shared
by two families. qwen2.5:3b (Qwen Research licence, non-commercial) leaves the default chain.
For the first time the model that thinks and the model that speaks are both under a licence
that permits a product, on hardware the project actually has.

The drip picked it up at the next tick without a code change: the register names the chain,
the organ picks what is present. Its first drop on the 4b was refused by the validator —
it carried yesterday's 85 and 119 from the conversation context into a digest that no longer
had them — which is the validator doing precisely its job.

## 6. What to watch this week

- **Voiced / refused per entity** in the receipts and the scoreboard: the guard will refuse
  more than the old one did; the question is whether the 4b's ekavica passes at the rate the
  bench sentence suggests.
- **Step time.** A step is one or two model calls; at 7.8 tok/s a thought and its voice are
  under a minute warm, but a cold load is 84 s and the ranker (llama3.2:1b) and the embedding
  model also want the GPU. If the receipts show steps near the 12-minute task limit, the
  `num_ctx` of 6144 is the first thing to lower.
- **The editor's weekly sample** is the second guard: a list catches only what is on it.

## Honest verdict

**Checked:** the guard on 28 sentences (offline tests, green); the retry path with a fake
model that answers ijekavian first and ekavian second, and with one that never learns; the
export re-check on rows written under the old guard; the rendering of the Serbian page with
a voiced and a refused thought at 1200 px; one real rendering by qwen3.5:4b read by a person;
the body's memory, cores, GPU and the model daemon's placement. **Concluded:** the rule is
now enforced by code on every public line, and the model that can obey it exists on the
machine and is licensed for the product. **Not looked at:** more than one real sentence of
the 4b's Serbian (the bench must be re-run with a warm model and one model at a time); the
drip's voiced rate under the new chain — the receipts of the next hours are that reading.
