# Turning content into place — a derived binding class, and why it must never look like a measurement

*Design note, 2026-09-06, from the proposal that a semantic tool could turn
content into geodata from the content itself — as **its own category**, with
**verification**, carrying a **chain of origin**. Those three conditions are
what separate this from the ordinary failure, and they are written into the
design below rather than left as intentions.*

---

## What it is, and what is already known about it

The task has a name — **geoparsing**, decomposed into **toponym recognition**
(finding the place mention in the text) and **toponym resolution** (deciding
which real place it is). It is old, well-studied, and its failure modes are
catalogued, which is good news: we are not inventing a method, we are choosing
one and binding it to this project's discipline.

The literature's standing result is worth stating plainly before any code is
written: **resolution, not recognition, is where systems fail.** Finding the
string "Zemun" is easy. Deciding whether an article means the Belgrade
municipality, the settlement, the fortress, the hospital, or a company with
Zemun in its registered name is the whole problem — and it is a problem of
*evidence*, not of language.

## Why BEOPS is unusually well placed to do it, and unusually obliged to do it carefully

A geoparser is mostly a **gazetteer plus a disambiguator**. The model is the
small part. This project is about to have a very good gazetteer — the place
register in `01-programme/PLACE_REGISTER.md`, in Linked Places Format, holding
the official heritage register, every school, every air and pollen station,
municipality boundaries, the RGZ address register, and OSM. Almost nobody
building a geoparser for Serbian has that.

And the obligation: this project's entire claim is that it never draws a number
more confidently than its origin allows. A geoparser produces **the most
seductive kind of wrong answer in the whole system** — a coordinate, which the
map will render with exactly the same crisp dot as a station whose operator
published its latitude. If inferred places are allowed to look like observed
ones, everything else the project has built is decoration.

## The category, in the grammar

Inferred locations are **not a new state**; they are a **binding method**, and
they extend the table already in `PLACE_REGISTER.md`:

| method | what it means |
|---|---|
| `stated_by_source` | the publisher gave coordinates |
| `geocoded` | an address string resolved against the address register |
| `matched_by_name` | a label matched a register entry |
| `inherited_from_parent` | only the containing unit is known |
| `asserted_by_us` | a person decided, and is named |
| **`inferred_from_content`** | **a model read a text and proposed a place** |

`inferred_from_content` is the only method in that list where **nobody
asserted the location at all** — not the publisher, not a register, not a
person. It is a hypothesis wearing the shape of a fact, and it carries three
consequences, not one:

1. **It never renders as a measurement.** Whatever the eventual visual grammar
   for it is, it must be as distinct from an observed point as a hollow cell is
   from a filled one. That is a design task for `05-design`, and until it
   exists, inferred places are stored but not drawn.
2. **It is never the sole basis of a published number.** An inferred place may
   suggest where to look; it may not be counted.
3. **It expires.** A gazetteer improves, a model changes. Every inferred
   binding carries the gazetteer version and model version that produced it,
   and is re-derivable rather than permanent.

## The chain of origin, in full

The proposal's third condition is the one that makes the category usable. A
derivation chain is not a log line; it is the record that lets anyone walk
backwards from a dot on a map to the sentence that caused it:

```
inference
  id
  place_id            what we concluded, in the register
  method              inferred_from_content
  confidence          0..1, and what the number means

  source_document     source_id + the exact URL or file, and its sha256
  captured_at         when that document was read
  span                character offsets in the stored document
  surface_form        the string exactly as written: "у Земуну"
  normalised_form     "Земун", and the lemma rule that produced it
  script              cyrillic | latin, and the transliteration applied

  candidates[]        EVERY candidate considered, not only the winner
    place_id, gazetteer, gazetteer_version, score, features_that_fired
  chosen              which one, and the margin over the runner-up
  rejected_because    for the near misses, why

  model               name + version + parameters, or "rules v3"
  gazetteer_version
  derived_at
  verified_by         null | human name | held-out set id
  superseded_by       when a later run changes the answer
```

Two fields there are unusual and both are deliberate. **Keeping every
candidate** turns a wrong answer from an embarrassment into evidence: it shows
whether the right place was never a candidate (a gazetteer gap) or was a
candidate and lost (a disambiguation failure). Those need opposite fixes.
And **the margin over the runner-up** is a far better confidence signal than a
model's own score, because a near-tie between two Zemuns is exactly the case
where a human must be asked.

## What makes Serbian hard, specifically

None of this is generic, and pretending otherwise is how such tools fail here.

- **Two scripts.** Ћирилица and latinica in the same corpus, sometimes in the
  same document. Transliteration is deterministic but lossy in the reverse
  direction, and the register must hold names in both.
- **Case endings.** Serbian is heavily inflected, and place names inflect:
  *Београд → у Београду, из Београда, ка Београду*; *Врачар → на Врачару*;
  *Нови Сад → у Новом Саду* — a two-word name where **both** words decline.
  A naïve exact match against a gazetteer finds almost nothing in running text.
- **Names that are also words.** *Бор* is a town and a pine tree. *Врање*,
  *Косјерић*, *Ужице* are safe; *Липе*, *Брестовац*, *Дубока* are not.
- **Repeated settlement names.** Serbia has many settlements sharing a name.
  Without a containing region in the same sentence, the honest answer is often
  a candidate set, not a place.
- **Streets that are people.** Belgrade addresses are overwhelmingly
  personal names — *Кнез Михаилова*, *Његошева*, *Ресавска* — so a naïve
  person-name extractor and a street extractor fight over the same spans.
- **The city inside the city.** *Београд* is a city, a district, and an
  administrative unit containing seventeen municipalities. A text saying
  "Beograd" almost never means the polygon. Resolution must return **the
  level** as well as the place.

## The order this should be built in, and the test that gates it

1. **Gazetteer first.** No geoparsing until the place register holds the
   official heritage register, schools, stations, municipalities and the
   address register — with names in both scripts and known alternates. Building
   the parser before the gazetteer is the classic way to produce a tool that
   confidently resolves everything to the twenty places it happens to know.
2. **Rules before models.** Serbian inflection is regular enough that a lemma
   table plus the register gets a long way, and a rule is auditable in a way a
   model is not. The model earns its place only where rules measurably fail.
3. **A held-out gold set, built by hand, before any output is used.** A few
   hundred spans from the actual corpora — official gazette notices,
   procurement notices, permitted news sources — annotated with the correct
   place and level. Report **precision, recall and resolution accuracy
   separately**, because they fail differently and a single F-score hides which.
4. **The gate:** no inferred binding is published until the held-out set is
   built and the numbers are recorded in the source's registry entry, the same
   way every other claim in this project carries its evidence.

## What it would unlock, once it passes

The project already holds text it cannot currently place: procurement notices
naming a street, official gazette decisions naming a cadastral parcel, the
permitted news sources, the Commissioner's case descriptions, historical
captures from the archive. Each of those is a **dated event with a place named
in words**. Turning them into places is the difference between a map of sensors
and a map of what happened.

And it is the only route to the deep past. No station published its
coordinates in 1905. The city's older layers exist only as text, and a
disciplined geoparser — with its candidates kept, its margin recorded and its
verification stated — is the honest way to read them.

## The rule this adds

> An inferred place is a **hypothesis**, stored with the sentence that caused
> it, every candidate that lost, and the versions of the gazetteer and model
> that decided. It may guide the eye. It may not carry a number, and it may
> never be drawn like a measurement.
