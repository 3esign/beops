# Edge cases — where we are at the edge, and the questions we would ask

*A separate section, deliberately. The rest of this folder records what we are
clearly permitted to do. This file records what is **not settled**, states the
position we have taken anyway, and names the question we would put to someone
with the authority to answer it.*

The purpose is not to look careful. It is that a project which collects a city
for years will eventually meet one of these, and the honest thing is to have
written down, in advance and in the open, where we knew the ground was soft.

Nothing in this file is legal advice, and none of us is a lawyer. Each entry
names the instrument it reads, quotes what that instrument actually says, and
separates that from our own choice.

---

## E-001 — Text and data mining has no clear Serbian rule

**The soft ground.** EU Directive 2019/790 (DSM) Art. 3 creates a mandatory
exception for text and data mining by research organisations for scientific
research, and Art. 4 a general exception subject to a machine-readable
reservation by the rightholder. Serbia is harmonising its acquis
continuously, but we have not verified a transposition of Art. 3 or Art. 4 into
the Serbian Copyright and Related Rights Act. Until we can point to the
transposed article, we cannot claim the research exception by name.

**What we stand on instead.** The Serbian Act, Art. 6(2), excludes from
protection *ideas, principles, discoveries, and official materials* — and
facts. A water level, a vehicle count, a station identifier, a timestamp: these
are not authored expression. What BEOPS stores is overwhelmingly facts and
their provenance, not the pages that carried them.

**Our choice.** We apply the **stricter of the two regimes**. We behave as if
Art. 4 were already Serbian law: we honour every machine-readable reservation —
`robots.txt`, `Content-Signal`, `TDM-Reservation`, terms — even where no
Serbian rule presently requires it, and even where the reservation targets AI
specifically rather than research. Where a publisher has reserved, we record
the refusal and do not collect. We have already done this and lost sources by
it.

**The question we would put.** *Does the Serbian Copyright Act, as it now
stands, permit text and data mining for non-commercial scientific research by a
university-affiliated project; and if the DSM exceptions are not yet
transposed, does Art. 6(2) alone suffice for the extraction of unprotected
facts from lawfully accessible public web pages?*

---

## E-002 — `robots.txt` binds us, but probably not by law

**The soft ground.** RFC 9309 standardises the *format* of `robots.txt`. It
creates no obligation. Whether ignoring it is a breach of contract, an
unauthorised access, or nothing at all, is unsettled in Serbia and thinly
settled anywhere. A `404` — which is what most Serbian public sites return — is
under RFC 9309 the statement *no restrictions stated*, not permission granted.

**Our choice.** We treat a disallow as binding on us regardless of its legal
force, and we treat an absence as an absence, not as a grant: for a source with
no `robots.txt` we look further — to terms, to the nature of the publisher, to
whether the document was published *in order to be read*.

**The question we would put.** *Where a public body publishes a document
without any stated reuse licence and without a `robots.txt`, is systematic
automated retrieval of that document permitted, and does the absence of a
stated licence mean "no rights granted" or "published for public use"?*

---

## E-003 — Absence of a licence is not a grant

**The soft ground.** Our strongest sources are official documents of public
enterprises — annual traffic counts, hydrological bulletins, air-quality
tables. Almost none carries an explicit reuse licence. Serbia's transposition
of the Open Data Directive (EU) 2019/1024 is partial, and the Law on Free
Access to Information of Public Importance (105/2021) governs *access*, which
is not the same as *reuse*.

**Our choice.** For a document published by a public body or public enterprise
for a public purpose, containing facts, we: reuse the **facts**, not the
document's layout or text; attribute the publisher by name and URL in every
derived figure; store the original bytes as evidence rather than
redistributing them as a product; and remove anything on request from the
publisher, without argument. We do not relicense anything as ours.

**Where this is genuinely thin.** A public enterprise is not the state. Its
published reports may carry rights the state's official materials do not.

**The question we would put.** *Are the annual traffic-count reports of a
public enterprise "official materials" within the meaning of Art. 6(2), and if
not, what reuse of the tabulated figures — as distinct from the report — is
permitted absent a licence?*

---

## E-004 — Repeated small extractions may add up to a substantial one

**The soft ground.** The sui generis database right (Serbian Act, Art. 138 and
following; EU Directive 96/9 Art. 7) prohibits extraction of a *substantial
part* of a protected database — and Art. 7(5) also prohibits **repeated and
systematic extraction of insubstantial parts** where this conflicts with normal
exploitation. A collector that samples thirteen parking garages every hour for
a year takes nothing substantial on any single call, and something quite
substantial by the end.

**This is the sharpest edge we have**, because it applies to exactly the thing
BEOPS is: a long, patient, repeated observation.

**Our choice.**

- We sample at the lowest rate that still answers the question, and we write
  the rate down as a pre-registered decision, not a convenience.
- We store the **minimum field set** — the value, the time, the source, the
  claim — never a mirror of the source database.
- We publish **derived series and aggregates with provenance**, not
  reconstructions of anyone's database.
- One source, one budget: no parallel collectors, no retry storms.
- We stop on request, immediately, and record the stop.

**What would change our mind.** If a publisher's terms say the series itself is
the product they sell, we do not collect it at all, however open the endpoint.

**The question we would put.** *At what cadence and horizon does repeated
retrieval of individual current values from a continuously updated public page
become "repeated and systematic extraction of insubstantial parts" conflicting
with normal exploitation, where the publisher is a public utility and the
values are facts about public infrastructure?*

---

## E-005 — We stopped at a door that was ajar

**What happened.** `https://gisportal.rs/server/rest/services?f=pjson` returns,
without authentication, the list of folders on a public ArcGIS Server:
`ITS_Putevi_Srbije`, `ITS_katastar`, `PMIS`, `InfoCentar`, `UBS`, `UDBRS`,
`AMR`, `REPORTS`, `Hosted`. Every one of those folders returns
`{"code":499,"message":"Token Required"}`.

**Our choice.** We issued one GET to a documented public endpoint, read the
answer, recorded it, and stopped. We did not seek, guess, borrow or derive a
token; we did not look for a service published without one; we did not read the
portal's JavaScript for credentials. The names are recorded in
`SOURCE_REGISTRY.json` as *closed, name known* so that the project does not
spend another evening rediscovering them.

**Why it is here at all.** A listing that a server offers anonymously is
information the operator chose to expose, and reading it is not circumvention.
But the distance between "read the index the server offered" and "went looking
for the way in" is a distance of intent, not of technique, and it deserves to
be written down by the party that could have crossed it.

**The question we would put.** *Is enumeration of a publicly served service
index, where the services themselves require a token, within the scope of
authorised access?* Our practice does not depend on the answer: we stop at the
door either way.

---

## E-006 — Archived copies of a page whose publisher has since refused

**The soft ground.** Several publishers we would otherwise read have opted out
of AI collection — in `robots.txt`, or by `Content-Signal`. Copies of their
pages from before that decision sit in public web archives, retrievable
lawfully by anyone.

**Our choice, which no law requires.** We do not use an archive to obtain what
a live opt-out refuses. The refusal attaches to the **source**, not to the
retrieval path. Where an archive is the only way to reconstruct a history, we
use it **only** for publishers who have not refused — and we record, in the
source's registry entry, that the reconstruction came from an archive and not
from the publisher.

**The question we would put.** *Does a rightholder's machine-readable
reservation, made today, extend to lawfully archived copies of their pages made
before it?* We think the honest reading is that intent should be honoured
regardless, and that is what we do.

---

## E-007 — Sound, and the word "measurement"

**The soft ground.** The Serbian law on protection from environmental noise
(96/2021), Art. 21–25, reserves noise *measurement* to accredited bodies using
prescribed methods. Any acoustic figure BEOPS derives — from a citizen sensor,
from an open stream, from anything — is not that.

**Our choice.** No acoustic value BEOPS produces may ever be presented as a
noise measurement, may ever be expressed in the units and averaging periods the
law reserves (L_den, L_night as compliance figures), or may ever be compared to
a legal limit. We publish it as an **indicator with a stated instrument and a
stated method**, under a name that cannot be mistaken for the legal term, and
every such figure carries that statement in the same view as the number, not in
a footnote.

**Still unresolved: what to call it.** "Sound level" is already close enough to
mislead. The naming decision belongs with the design work in `05-design`, and
until it is made, no acoustic figure is published at all.

---

## E-008 — Nothing regulates the combination

**The soft ground.** Every source in this project is individually open and
individually harmless. Nothing in Serbian or EU law addresses what happens when
twenty of them are joined: traffic counts, parking occupancy, water level, air
quality, event calendars, construction permits, mapping activity. A combination
can reveal a pattern that no component reveals, and that is the entire purpose
of the project — it is also its only real risk.

**Our choice.**

- **No persons, at any resolution, ever.** No faces, no plates, no devices, no
  trajectories, no household-level inference. This is not a resolution setting;
  it is a category we do not hold.
- **No spatial resolution finer than the question needs.** Where a series could
  in principle single out one household or one business, it is aggregated
  before it is stored, not before it is published.
- **Absence is shown, not filled.** The project's whole grammar exists so that
  a gap reads as a gap. A combination that quietly interpolates is a
  combination that invents a city.
- **Every published figure carries its provenance.** Anyone must be able to
  walk back from a picture to the sources and to this folder.

**The question we would put, and we think it is the real one.** *At what point
does the lawful aggregation of individually open public data acquire
obligations of its own — of accuracy, of correction, of notification — that
none of the component sources carried?*

We do not know the answer. We have built the system so that if the answer turns
out to be "sooner than you thought", every figure can be traced, dated,
corrected and withdrawn.

---

---

## E-009 — `robots.txt` on an endpoint that exists to be queried

**The soft ground.** Two of the best keyless sources available to the project
disallow the very path that is their API:

```
query.wikidata.org/robots.txt        overpass-api.de/robots.txt
User-agent: *                        User-agent: *
Disallow: /sparql                    Disallow: /api/
Disallow: /bigdata                   Sitemap: https://z.overpass-api.de/api/sitemap
```

The evident target is a search engine following links into expensive
generated queries — Overpass even publishes a sitemap *under the path it
disallows*, which only makes sense if the directive is aimed at crawlers and
not at clients. Both endpoints exist to be called programmatically; both
publish client documentation and rate limits; Wikidata's content is CC0 and
Wikimedia's own policy asks API clients to identify themselves and behave,
which is a policy for clients, not for crawlers.

And yet the letter covers us. `User-agent: *` includes us, and we do fetch
those paths.

**What we have NOT done.** We have not decided this in the permissive
direction on our own reasoning. Both sources sit in `INDEX.md` under
**Decision required**, and no collector is built on either until the decision
is recorded here, with a date and a name.

**What the decision needs.** Whether `robots.txt` — a crawler-exclusion
standard whose own RFC 9309 abstract speaks of *crawlers* — governs a
deliberate API call at all; and, if the project decides it does not, whether
that reasoning is written down in a form that would survive being read by
someone unsympathetic. A rule that only holds when it is convenient is not a
rule.

**Disclosure, because it belongs here and not in a footnote.** Belgrade
figures were taken from both endpoints on 2026-09-06 **before** their
permission was captured — 219 monuments, 1 409 bridge ways, 9 named bridges,
9 stadiums, 137 venues, and the Singidunum record. That inverted this folder's
first rule, which is *evidence before collector*. It is recorded in
`CORRECTIONS.md` C-003, and every figure derived from those queries carries the
note until the decision above is made.

**The question we would put.** *Does a `Disallow` in `robots.txt` bind a client
making documented API calls to a service whose published purpose is to answer
them, or is its scope limited to crawling?*

---

## E-010 — Permission is per purpose, not yes or no

**What we found.** `Content-Signal`, which Cloudflare and others now publish
inside `robots.txt`, does not say yes or no. It says what for:

```
whc.unesco.org      Content-Signal: search=yes, ai-train=no, use=reference
www.transit.land    Content-Signal: ai-train=no, search=yes, ai-input=yes
```

and transit.land states plainly what that is in law:

> ANY RESTRICTIONS EXPRESSED VIA CONTENT-SIGNALS ARE EXPRESS RESERVATIONS OF
> RIGHTS UNDER ARTICLE 4 OF THE EUROPEAN UNION DIRECTIVE 2019/790 ON COPYRIGHT
> AND RELATED RIGHTS IN THE DIGITAL SINGLE MARKET.

This is the Art. 4 reservation named in E-001, made machine-readable — the
thing we said we would honour even though we cannot yet point to its Serbian
transposition.

**Our choice.** BEOPS **reads**; it does not train. So the signals are applied
by purpose:

- `ai-input=no` or `search=no` forbids what we actually do → the source moves
  to *Do not collect*.
- `ai-train=no` is honoured as written and recorded on the source's row in
  `INDEX.md`. It does not stop us reading, and it means **no data from that
  source may ever be used to train anything**, by us or by anyone we hand the
  archive to.
- A signal absent means neither granted nor restricted, which is what the
  policy text itself says, and we treat it as the licence and the law leave it.

**Where this is thin.** "Reading" and "AI input" are not obviously distinct
when the reader is an AI system, and a future BEOPS that fits a model on its
own archive would be training on material collected under `ai-train=no`. That
restriction has to travel with the data, not just with the source row.

**The question we would put.** *Does a `Content-Signal` reservation attach to
the data itself once collected — binding anyone the archive is passed to — or
only to the act of collection?* We assume the former, and record the signal on
the source so it can be carried, because assuming the latter would make the
reservation meaningless one hop downstream.

---

## E-011 — Signals that are not addressed to us

**What we found.** Two of the polled news sources carry a machine signal that
is *about something else*:

- `gradnja.rs/feed/` and `bvk.rs/feed/` answer `X-Robots-Tag: noindex, follow`,
  and `masina.rs/feed/` answers `X-Robots-Tag: noindex`. `noindex` is a
  search-engine directive: do not list this document in search results.
  `follow` says: the links in it may be followed.
- `n1info.rs/sitemap/sitemap_news_1.xml` is a Google-News sitemap — a crawl
  aid addressed to a search engine, listing title, link and publication
  date. robots.txt permits it for every agent.

**Our choice.** BEOPS neither indexes nor republishes the feed document; it
keeps a headline, the link and the publisher's time, and links back to the
article — which is what `follow` describes. So `noindex` on a feed does not
change the verdict for reading it, and a news sitemap read for title, link
and date is used for what it publishes. Both are recorded on the source rows
(`news_audit_2026_09_09`) as decisions, not as permissions, and the verdict
is revisited the day either publisher adds an AI-purpose signal
(`Content-Signal`, a named agent in robots.txt).

**Where this is thin.** A publisher who writes `noindex` on a feed may mean
"do not machine-read this" and simply not know the vocabulary for it. We
read the letter because the letter is all a machine can read; a letter is
what E-005 promises when a door is ajar.

**The question we would put.** *Does a search-engine directive on a feed
document express any reservation under Art. 4 of Directive 2019/790 — and
if a Serbian transposition ever arrives, will it read `noindex` as one?*

---

## E-012 — A named opt-out on material that is not a copyright work

**What we found.** `mup.gov.rs/robots.txt` names ClaudeBot, GPTBot,
ChatGPT-User, OAI-SearchBot, Bytespider and others with `Disallow: /`, and
has no `User-agent: *` group. Police press releases are official materials
of a state body — outside copyright under Art. 6(2) of the Copyright Act.
Copyright law would let us take them; the operator has said no to us by
name.

**Our choice.** The refusal wins (S204, `opted_out`). The project's promise
about named opt-outs (frame §7) is a promise about consent and identity —
we ask honestly and we accept the answer — not a promise about copyright.
A rule that held only where copyright also held would be no rule.

**Where this is thin.** Art. 6(2) exists so that citizens can know what
their state says; a state body fencing its releases from named readers is
exactly what the frame's §5 (freedom of information) is for. A request
under that statute is the route, and it is on the list.

**The question we would put.** *Can a body exercising public function
lawfully restrict, by robots.txt, automated reading of materials the
Copyright Act declares free — or is the statute the answer and robots.txt
merely a preference we choose to honour?*

---

## E-013 — Headlines carry names

**What we found.** Every polled headline may name a person. The news layer
is therefore personal-data processing under ZZPL Art. 4, even though it
keeps no body, no image, no profile and never searches by person. Art. 88
(journalistic and scientific expression) may cover the published findings;
the standing store of month files looks like ordinary processing under
Art. 12 with Art. 92 safeguards (frame §4).

**What we already do.** Headline, link, time — nothing else; no per-person
index; the public export carries only the window (six hours) and the
scoreboard, never the archive; the mind cites headlines by number and is
refused when it invents.

**What we do not yet do.** There is no retention rule for the month files.
Proposed, for the editor to decide: keep them locally as research evidence
under the project's immutability rule; never build a per-person index;
delete nothing automatically, because deletion of evidence is the one thing
this project has promised not to do — and write that reasoning down where a
supervisory authority would look for it.

**The question we would put.** *Is a research archive of headlines with a
six-hour public window and no per-person index within Art. 92's
"appropriate safeguards" without a retention limit, or does the safeguard
require a date?*

---

## How to add to this file

Add an entry when you notice that a rule you are relying on does not clearly
exist. Give it the next `E-` number. Say what is soft, what we do anyway, and
what you would ask. Do not remove entries when they are resolved — record the
resolution underneath, with the source, and keep the question visible. The
history of what we were unsure about is part of the evidence too.
