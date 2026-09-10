# A refusal is a refusal to be our source, not a censorship of the world

**BEOPS — standing rule, written 2026-09-10.** This one is not pending counsel: it does not read a
statute and it does not widen what the record takes. It narrows what the record may *say*, and it is
enforced by `tools/guard.py` on every pass and by `research/test_refusal_route.py` on every ship.

---

## 1. The hole this closes

Fourteen organisations have told this project no, and the guard has asserted from the beginning that
none of them is polled. That invariant is true and it was never the whole question.

Three of the fourteen — **MUP**, **JKP Beograd-put** and **JKP Gradska čistoća** — publish exactly the
kind of notice this observatory exists to record, and those notices are republished by city
municipalities, by the City portal and by the newspapers. So their material arrives anyway, through
doors they do not control.

Measured on 2026-09-10, before this rule was written: **23 headlines naming Gradska čistoća** (via
Novosti, Tanjug and Dan u Beogradu) and **4 naming MUP** (via Euronews, Tanjug and Danas) are in the
record; six and two of them respectively were live in the published snapshot at that moment. Nothing
was wrong with any of them — every one carried the outlet that wrote it and a link to the outlet. But
nothing asserted that, either. The practice was correct by habit, which is the same condition Article
41 attribution was in until it became `test_attribution.py`.

## 2. The rule

> Where a named refuser's material reaches this record through a third party, **it is kept as the
> third party's utterance**, attributed to the third party, and:
>
> - the refuser is **never named as a source of ours**;
> - the refuser is **never counted among our sources**, in any total, anywhere;
> - the refuser is **never presented as having supplied us with anything**;
> - the third party's own attribution — who published it, and the link to where — **travels with it
>   always**, because that attribution is the only thing that makes the route honest.

And its second half, which matters just as much:

> **Nothing is filtered, suppressed or removed because a refuser is named in it.** A newspaper's
> report about JKP Gradska čistoća is the newspaper's publication and the newspaper's right. A refusal
> withdraws an organisation from being *our source*. It does not withdraw them from the news, from the
> city, or from the record other people keep of them, and this project has no business acting as
> though it could.

## 3. Why both halves are needed

Drop the first half and the refusal becomes decorative: the record could take everything a refuser
withheld, one republication at a time, and still print *no named refusal is polled* with a clear
conscience. That is the failure this file exists to prevent, and it is the exact shape of defect this
record keeps writing corrections about — an invariant true in the letter and hollow in the substance.

Drop the second half and something worse happens: a research project starts deciding which of a city's
publications may be seen, on the strength of an organisation having declined to answer its emails.
Nobody asked for that and nobody should have it. **A refusal is not a right to be unmentioned.**

## 4. What is not a violation

- **A refuser's name inside somebody else's headline**, carrying that outlet's sid and link. This is
  the permitted case and the common one. It is counted and printed by the guard rather than merely
  allowed, because a number that is never printed is not an invariant.
- **A refuser's name as a place.** "Aerodrom Nikola Tesla" is a location in Belgrade before it is an
  organisation that refused us, and a zone named after it is geography, not attribution.
- **A refuser named in this project's own documents** — the registry, the corrections ledger, the
  permission dataset, this file. Naming who declined is the opposite of presenting them as a supplier,
  and it is the paper's central finding.

## 5. How it is enforced

`tools/guard.py`, every pass, two checks beside the existing one:

| check | fails when |
|---|---|
| *a named refusal is never our source* | a refuser's id appears among the published sources, or as the `sid` / `input_sid` of any derived row we publish |
| *a refusal reached by another route stays the third party's utterance* | a headline naming a refuser is published without the outlet that wrote it and a link to it |

`research/REFUSER_NAMES.json` holds the names to watch for, with diacritics folded so a rule written
as `gradska cistoca` still sees `Gradska čistoća`. That file also records, in the open, the names
deliberately **not** watched and why: *Politika* and *Vreme* are ordinary Serbian words — "policy" and
"weather"/"time" — and a record full of weather cannot match on them without lying about what it found.

`research/test_refusal_route.py` asserts the same properties on every ship, plus the one the guard
cannot see: that the watch list is only ever used to observe and count, and never to drop a row.

## 6. Honest verdict

This rule costs the project nothing today, because the practice already complied. That is precisely
why it was worth writing: an invariant adopted while it is free is an invariant, and one adopted after
it starts costing something is a negotiation.

The part that could still be got wrong is the second half. If a future reader takes this file as
licence to strip a refuser's name out of a newspaper's headline, they will have inverted it. The
headline is the newspaper's. We are keeping a record of what the city's publishers said, and a
publisher saying something about an organisation that declined to talk to us is not our business to
edit.
