# The legal ground under the news layer, re-read

**BEOPS — Belgrade Evidence Observatory · v1, 2026-09-10**
A re-reading of what this record may lawfully take as news, of the sources it already takes, and of
what it is not taking and could. It supersedes nothing: the news audit of 2026-09-09 stands as
written, and this document says where it was right, where it under-claimed, and where it missed.

*Not legal advice. I am not a lawyer. This is the analysis to hand a lawyer, and the letter sets
awaiting counsel's read are unaffected by it.*

---

## 1. What the Act actually says

The operative statute is the **Zakon o autorskom i srodnim pravima** (Law on Copyright and Related
Rights). Four provisions matter here, quoted verbatim.

**Article 6 — what is not a work at all.**

> „Ne smatraju se autorskim delom: 1) zakoni, podzakonski akti i drugi propisi; 2) službeni materijali
> državnih organa i organa koji obavljaju javnu funkciju; 3) službeni prevodi propisa i službenih
> materijala državnih organa i organa koji obavljaju javnu funkciju; 4) podnesci i drugi akti u
> upravnom ili sudskom postupku."

Note the breadth of 6(2): not only state organs but **bodies exercising a public function** — which
reaches city administrations, city municipalities and public utility enterprises.

**Article 43 — reporting on current events.**

> „Dozvoljeno je, u okviru izveštavanja javnosti putem štampe, radija, televizije i drugih medija o
> tekućim događajima, u obimu koji odgovara svrsi i načinu izveštavanja o tekućem događaju, bez dozvole
> autora i bez plaćanja autorske naknade:
> 1) umnožavanje primeraka objavljenih dela koja se pojavljuju kao sastavni deo tekućeg događaja o kome
> se javnost izveštava;
> **2) pripremanje i umnožavanje kratkih izvoda ili sažetaka iz novinskih i drugih sličnih članaka u
> pregledima štampe;**
> 3) umnožavanje političkih, verskih i drugih govora održanih na javnim skupovima, u državnim organima,
> verskim ustanovama ili prilikom državnih ili verskih svečanosti;
> **4) slobodno korišćenje dnevnih informacija i vesti koje imaju prirodu novinskog izveštaja."**

**Article 49 — quotation.**

> „Dozvoljeno je bez dozvole autora i bez plaćanja autorske naknade umnožavanje, kao i drugi oblici
> javnog saopštavanja kratkih odlomaka autorskog dela (pravo citiranja), odnosno pojedinačnih kratkih
> autorskih dela"

**Article 41 — the price of every one of those.**

> „U slučajevima iskorišćavanja autorskog dela na osnovu odredaba ovog zakona o ograničenju autorskog
> prava, moraju se navesti ime autora dela i izvor iz koga je delo preuzeto"

and the three-step test:

> „U svakom konkretnom slučaju, obim ograničenja isključivih prava ne sme biti u suprotnosti sa
> normalnim iskorišćavanjem dela niti sme nerazumno vređati legitimne interese autora"

**What the Act does not contain.** No related right for press publishers — the EU DSM Directive's
Article 15 is **not transposed**. No text-and-data-mining provision of any kind: neither the Directive's
Articles 3–4 exception nor any restriction. Both absences were checked against the text on 2026-09-10.

---

## 2. Finding 1 — the record has been standing on the weakest ground available

Every news source in the registry is justified the same way: *"no reuse statement found"*, *"clean
robots.txt"*, *"allowed, 200, no opt-out signal"*. That is an argument from **absence of objection**.
It is true, it is carefully evidenced, and it is the weakest thing that could be said.

**Article 43(1)(4) positively permits it.** Daily information and news having the nature of a press
report may be used freely — no permission, no fee. A service headline (*"Deo Zvezdare bez vode zbog
planiranih radova 10. septembra"*) is the paradigm case: it is the news of the day in its most factual
form.

**Article 43(1)(2) permits the shape of it.** Preparing and reproducing short extracts or summaries
from newspaper and similar articles **in press reviews**. A feed of headlines with outlet, link and
publication time, presented as a survey of what the city's outlets said and when, is a press review in
the ordinary sense of the phrase. Both are conditioned on being *within reporting to the public about
current events, in a scope corresponding to the purpose* — and headline + link + time is the smallest
scope that can serve the purpose at all.

**Consequence.** The posture changes from *nobody has objected yet* to *the Act permits this, and we
meet its condition*. That is a different sentence to put in a paper, in a letter, and in front of a
publisher who writes to complain. The evidence already captured does not become less valuable — an
opt-out is still binding, and a robots refusal is still refused — but it stops being the whole case.

**What must follow.** Article 41 is not free. The name of the source and the origin must be stated.
BEOPS does show outlet, link and time — but by design habit, not as an asserted requirement. It should
be an invariant with a test behind it: **no headline is published without its outlet and its link.**
Today that is true by accident.

---

## 3. Finding 2 — one source is justified by a rule that does not exist

**S76, Beta agency.** The record reads: *"the public RSS is the free teaser of a paid wire and BEOPS is
non-commercial research — fine for v1; a product would need Beta's licence."*

There is no non-commercial research exception in the Serbian Act that covers this. Article 43 has no
commercial/non-commercial distinction, and there is no TDM provision to invoke. So the sentence claims
a legal basis that is not there, and it does it for the one source with a commercial licensing model —
the place where the claim is most likely to be tested.

The correct statement is narrower and stronger: **Beta stands on Article 43 like every other outlet.**
The subscription concerns the paid wire, not the public feed, and taking a headline from a public feed
is not taking the wire. What changes for a product is not the copyright analysis but the risk of a
commercial counterparty objecting — which is a business question, not this one.

---

## 4. Finding 3 — the municipal layer is described as absent and is not

The 2026-09-09 audit registered one municipal feed, **S79 Vračar**, and noted it as *"the only
municipal feed found"*. It is not polled.

Checked on 2026-09-10 from the cloud, unauthenticated:

| Municipality | `/feed/` | Newest item at check |
|---|---|---|
| Novi Beograd | RSS, 10 items, "Градска Општина Нови Београд" | 2026-09-09 14:01 UTC |
| Zvezdara | RSS, 10 items, "GO Zvezdara" | 2026-09-09 14:02 UTC |
| Stari grad | RSS, 10 items, "Стари град" | 2026-09-02 13:41 UTC |
| Palilula | not a feed — HTML homepage | — |

Three of the four checked serve live feeds. Belgrade has seventeen city municipalities; four were
looked at. **The claim that Vračar was the only one is an artefact of where the audit stopped**, and it
matters more than a missing source, because of what these bodies are.

A city municipality is a **body exercising a public function**. Its notices are **Article 6(2) official
materials — not copyright works at all**. The Zvezdara item quoted above is exactly the fact this
observatory exists to record, published by the body that caused it, on ground where no permission
question arises.

So the record is currently taking service news from private newspapers under Article 43, when the same
facts are published by the responsible bodies under no copyright at all. Both are lawful. One is
better.

---

## 5. Finding 4 — the City's official gazette is not in the registry

**`sllistbeograd.rs`** — *Službeni list grada Beograda*, published by the City of Belgrade's
administration (Sekretarijat za informisanje). Archive 2002–2026. Acts of the City, of its
municipalities, of the Constitutional Court and of the public utility enterprises.

Checked 2026-09-10 from the cloud: `robots.txt` is

```
User-Agent: *
Allow: /
```

and no copyright or terms statement appears on the front page.

This is Article 6(1) and 6(2) in their purest form: laws, subordinate acts, other regulations, and
official materials. **Not works.** For an observatory whose subject is what the city does and when it
said so, an official gazette with a complete archive is the most solid and most under-used source
available, and 211 registered sources contain no gazette at all.

It is HTML only — no feed — so it needs a listing parser, which is why it is a lead and not a
switch to flip.

---

## 6. Finding 5 — the refusals need a rule they do not yet have

Fourteen sources are recorded as opted out, and the guard asserts every pass that no named refusal is
polled. That invariant is formally sound and substantively incomplete.

**MUP**, **JKP Beograd-put** and **JKP Gradska čistoća** have refused. Their notices are nonetheless
republished by city municipalities, by the City portal and by the outlets. If a municipal feed carries
a Beograd-put closure, collecting it is lawful — it is the municipality's own material — but the record
must not treat that route as a way to obtain what a named refuser withheld.

**Proposed rule, to be written into the doctrine and asserted by the guard:** where a named refuser's
material reaches this record through a third party, it is kept as the third party's utterance and
attributed to the third party — and the refuser is never named as a source of ours, never counted among
our sources, and never presented as having supplied anything. A refusal is a refusal to be our source,
not a censorship of the world.

Without that rule the invariant is true in the letter and hollow in the substance, which is precisely
the failure mode this record keeps writing corrections about.

---

## 7. What this changes, concretely

**Registry wording — the case, not just the capture.** Every `news_feed` entry should record the ground
it stands on, and there are only four:

1. **Art. 43(1)(4)** — daily information and news of the nature of a press report (the default for
   every outlet headline);
2. **Art. 43(1)(2)** — short extracts and summaries in a press review (the shape of the monologue feed);
3. **Art. 6(1)–(2)** — regulations and official materials of state bodies and bodies exercising a public
   function (the gazette, the City portal, the municipalities, the public enterprises, the Government);
4. **Art. 49** — quotation, for a headline original enough to be a work in its own right.

Each carries **Art. 41**: the source is named and the origin is stated.

**Corrections to make.**
- S76 (Beta): drop the non-commercial research basis; state Art. 43.
- Every polled news source: state the ground, not only the absence of objection.
- S79 (Vračar): the note "the only municipal feed found" is wrong as of 2026-09-10.

**Additions to pre-screen and capture from the machine, strongest ground first.**
- *Službeni list grada Beograda* — Art. 6(1)–(2), robots open, needs a listing parser.
- City municipalities with live feeds — Art. 6(2). Novi Beograd, Zvezdara and Stari grad confirmed;
  the remaining thirteen unchecked.
- Skupština grada Beograda — sessions and decisions, Art. 6(2).
- Republički zavod za statistiku, Portal javnih nabavki — official, Art. 6(2), and both likely to carry
  an explicit open licence, which is better than an exception.

**Invariant to add.** No headline is published without its outlet and its link — Art. 41, asserted by a
test rather than left to habit.

---

## 8. Honest verdict

The 2026-09-09 audit was careful about *evidence* and careless about *law*. It captured robots.txt and
terms from the machine for every source, corrected itself about Tanjug's ownership, and refused what
refused it — all of that is right and none of it changes. But it never asked what the Act permits, and
so it built a news layer whose entire justification was that nobody had said no.

The Act says yes. It has said yes since before this project existed, in Article 43, and the provision
that most exactly describes what BEOPS does with headlines — *short extracts and summaries in press
reviews* — appears nowhere in 192 kilobytes of registry.

And the second half of the finding is the one that stings: while standing on the weakest available
ground for private newspapers, the record left the strongest ground almost untouched. The city's own
gazette is not registered. Sixteen of seventeen municipalities are not registered. Those bodies publish
the same service facts, first, and their publications are not copyright works at all.

This is a research finding about the observatory, not about the city, and it was available at any point
in the last week to anyone who read the statute rather than the robots files.
