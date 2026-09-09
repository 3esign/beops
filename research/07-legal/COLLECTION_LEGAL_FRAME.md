# BEOPS — the legal frame for continuous collection

Status: current
Date: 2026-09-05
Author: claude-cowork

**This is not legal advice.** It is a collection of primary texts, quoted, with the open questions
named rather than resolved. Section 6 lists what a real lawyer should be asked, phrased precisely
enough to be worth an hour of their time.

The activity being examined: continuously collecting, storing, indexing and analysing publicly
published text, images and measurements about Belgrade, for non-commercial scientific research at a
university, publishing only findings and short attributed quotations.

---

## 1. The TDM question, and the honest answer

**EU Directive 2019/790, Article 3(1)**, verbatim:

> "Member States shall provide for an exception to the rights provided for in Article 5(a) and
> Article 7(1) of Directive 96/9/EC, Article 2 of Directive 2001/29/EC and Article 15(1) of this
> Directive for reproductions and extractions made by **research organisations** and cultural
> heritage institutions in order to carry out, **for the purposes of scientific research, text and
> data mining** of works or other subject matter to which they have **lawful access**."

**Article 7(1)**: *"Any contractual provision contrary to the exceptions provided for in Articles 3,
5 and 6 shall be unenforceable."* — that is, for a research organisation, terms of service cannot
override the mining exception.

**Article 4** provides a general TDM exception for everyone, but only where rights have "not been
expressly reserved by their rightholders in an appropriate manner, such as **machine-readable
means** in the case of content made publicly available online" — this is the legal basis for
Cloudflare's `Content-Signal` header and for AI-bot entries in `robots.txt`.

**Article 15(1)** creates a press publishers' right, but explicitly *"shall not apply to acts of
hyperlinking"* nor *"in respect of the use of individual words or very short extracts"*, and expires
two years after publication.

### Does Serbia have any of this? No.

A full-text search of the consolidated **Zakon o autorskom i srodnim pravima** ("Sl. glasnik RS"
104/2009, 99/2011, 119/2012, 29/2016, 66/2019) for *rudarenje*, *tekstualno i podatkovno rudarenje*,
and for any description of automated computational analysis for research found **nothing**. No
amendment after 66/2019 was located despite specific searching, unlike the media law and the
freedom-of-information law, where recent amendments did surface.

There is also **no press publishers' right** in Serbian law — searched, absent.

**What follows, stated plainly.** Serbia's Stabilisation and Association Agreement obliges gradual
approximation of intellectual-property law, and Serbia does harmonise continuously — but obligation
to harmonise is not harmonisation, and on this point it has not happened. A Serbian research
organisation has **no mandatory TDM exception, no opt-outable general one, and nothing for Article
7(1) to protect**, because there is no underlying Serbian exception for a contract to override.

**So BEOPS does not rely on it.** The project is designed to be lawful under the *narrow* reading —
which is also the better engineering: process, derive the measure, **discard the source text**,
publish short attributed quotations, and request through statute anything that matters.

## 2. What we may collect, with the article that permits it

| What | Basis |
|---|---|
| **Laws, regulations, official materials of state bodies and bodies exercising public function, their official translations, and submissions in administrative or judicial proceedings** | **Copyright Act Art. 6(2)**: *"Ne smatraju se autorskim delom: 1) zakoni, podzakonski akti i drugi propisi; 2) službeni materijali državnih organa i organa koji obavljaju javnu funkciju; 3) službeni prevodi propisa i službenih materijala…; 4) podnesci i drugi akti u upravnom ili sudskom postupku."* **None of this is protected in the first place.** Full storage and full republication are clean. |
| Short excerpts in our own published findings, unmodified, attributed | **Art. 49**, the quotation right: *"Dozvoljeno je bez dozvole autora i bez plaćanja autorske naknade umnožavanje, kao i drugi oblici javnog saopštavanja kratkih odlomaka autorskog dela (pravo citiranja)…"* |
| Reporting on current events, within the purpose | **Art. 43** — written for media reporting; whether a research observatory's outputs qualify is not self-evident (§4). |
| Anything a public body holds and has not published | **Freedom-of-information law** — §5. A statutory right beats a scrape. |
| Copernicus Sentinel imagery | *"users shall have a free, full and open access to Copernicus Sentinel Data"* for *"reproduction, distribution, communication, adaptation, modification"*; attribution only. |
| EUMETSAT Meteosat Core Data, hourly | **CC-BY-4.0**: *"Access to Core Data and Products is granted to all users world-wide on a Free and Unrestricted basis"*; *"Users may redistribute all Core Data and Products."* The 5-minute Rapid Scan tier is paid (€4 000–8 000/yr) and Serbia cannot claim the national-met-service exemption. |
| Seismic waveforms of network SJ | FDSN metadata declares `restrictedStatus="open"` on the network and on stations AVAS and BEO; DOI 10.7914/SN/SJ. **But see §7 — declared open is not the same as available.** |

**The official-materials point is the most under-used finding in this whole file.** The Službeni list
grada Beograda, official announcements, decisions and acts are not copyright works at all. That is
the cleanest corpus available to this project and nobody is using it.

## 3. Personal data in collected text

**Zakon o zaštiti podataka o ličnosti** ("Sl. glasnik RS" 87/2018), Art. 4, verbatim:

> *"svaki podatak koji se odnosi na fizičko lice čiji je identitet određen ili odrediv, neposredno
> ili posredno"*

**A correction to this project's earlier notes.** Two documents written today placed the
journalistic/academic exemption at Article 92. It is the reverse:

- **Art. 88 is the exemption**: the provisions of Chapters II–VI and Articles 89–94 do not apply to
  processing carried out for the purposes of journalistic reporting and publication of information
  in media, **as well as for the purposes of scientific, artistic or literary expression**, if in the
  concrete case such restriction is necessary to protect freedom of expression and information.
- **Art. 92 is the safeguards article** — Serbia's equivalent of GDPR Art. 89: processing for
  archiving in the public interest, scientific or historical research, or statistical purposes is
  subject to appropriate safeguards.

**GDPR for comparison**, verbatim: Art. 85(1) requires Member States to reconcile data protection
with *"the right to freedom of expression and information, including processing for journalistic
purposes and the purposes of academic, artistic or literary expression"*; Art. 89(1) requires
*"appropriate safeguards"*, data minimisation and pseudonymisation *"if those purposes can be
fulfilled in that manner"*; Recital 159 says scientific research purposes *"should be interpreted in
a broad manner"*.

## 4. What is genuinely unclear

- **Continuous full-text ingestion has no clearly applicable Serbian exception.** Art. 49 covers
  short excerpts inside another work. Art. 43 is written for media reporting. **Art. 48** requires
  the copy be *"prolazno ili slučajno"* (transient or incidental) — whether a durable, queryable
  index is "transient" is precisely what nothing found resolves. **Art. 46** (private use) is scoped
  to *a natural person for personal needs* and is **not available to an institutional pipeline**,
  however non-commercial.
- **Database right, cumulative extraction.** Art. 5a defines the database right and says it *"не
  односи се на садржину базе података"*; Art. 138 gives the maker the right to prohibit extraction
  of a *"ukupnog ili značajnog dela"*. Whether Serbian law mirrors **EU Database Directive Art.
  7(5)** — which prohibits *"the repeated and systematic extraction and/or re-utilization of
  insubstantial parts"* where this conflicts with normal exploitation — could not be confirmed;
  every fetch of the consolidated text truncated mid-Article-138.
- **Whether ZZPL Art. 88 reaches the collection pipeline or only the published output.** A published
  finding quoting a name looks like expression. A standing database retaining every name that ever
  appeared in Belgrade news looks like ordinary processing under Art. 12 with Art. 92 safeguards.
  Nothing found draws that line.

## 5. The lever we are not using

**Zakon o slobodnom pristupu informacijama od javnog značaja** ("Sl. glasnik RS" 105/2021):

- **Art. 6**: *"Prava iz ovog zakona pripadaju svima pod jednakim uslovima"* — everyone, no
  citizenship or residency test.
- **Art. 15**: a written request; an oral request is permitted and logged.
- **Art. 16**: **15 days**, extendable to 40 with written justification given within 7; **48 hours**
  where life, freedom, health or the environment are at stake; a refusal must be written, reasoned,
  and carry appeal instructions.
- **Art. 17**: *"Uvid… je besplatan"* — inspection is free; copies are charged only at *"nužnih
  troškova izrade te kopije"*. Fees are waived entirely for journalists, human-rights organisations
  and health/environment requesters — **whether a university research observatory counts as any of
  those three is not addressed by anything found.**
- **Art. 9**: refusal grounds include national security, economic interests, trade secrets and
  intellectual property. A body could try to withhold on "economic interest" grounds. That refusal
  is appealable.
- **Art. 22**: appeal to the Poverenik on refusal, missed deadline or obstruction.

**Every named target of this project is reachable this way**: the ten traffic counters and the office
that owns them, the utility's lab results, RATEL's spectrum register, the transit AVL feed, the
seismic archive, AGROS station data. A request that must be answered within fifteen days beats a
feed whose terms call automated access a material breach.

## 6. What to ask a real lawyer

1. Does continuous full-text ingestion, storage and indexing — as distinct from the published,
   quotation-based outputs — infringe Serbian copyright absent permission, given that Articles 43,
   46, 48 and 49 were each written narrower than that? Does a "process, derive, discard the source
   quickly" architecture change the answer?
2. Does an EU Member State's transposed Article 3 protect a Serbian research organisation against an
   EU-domiciled rightholder's claim, even though Serbia has not transposed the Directive?
3. Does Copyright Act Art. 139 mirror EU Database Directive Art. 7(5) on repeated and systematic
   extraction of insubstantial parts, and at what volume does a continuous single-publisher harvest
   cross it?
4. Under ZZPL Art. 88, does this activity qualify for the scientific-expression exemption at all, or
   only its published outputs — leaving ingestion under ordinary Art. 12 with Art. 92 safeguards?
5. Is a browsewrap terms-of-service enforceable against an automated collector under Serbian
   obligations law, and does continuing after a cease-and-desist change that?
6. Does Art. 25 of the noise law, reserving official *measurement* to accredited bodies, prevent a
   university from publishing its own acoustic observations if they are labelled as research
   observations rather than as official measurements?

## 7. What we must not do

- **Do not treat "no TDM exception" as "therefore permitted."** Copyright's default is the reverse.
- **Do not circumvent a named opt-out.** Four sources name **ClaudeBot** in `robots.txt` with
  Cloudflare `Content-Signal: search=yes, ai-train=no, use=reference` — **Beobuild, Zoomer, Insajder,
  eKapija**, the last citing EU Directive 2019/790 explicitly. **Politika** disallows `*/rss` with a
  ~800-agent blocklist; **Vreme** and **Nedeljnik** disallow `/feed/`. A researcher suggested
  collecting Beobuild "with a collector not identified as Claude". **That is refused and recorded as
  refused.** Beobuild is the best source on the physical change of the city that exists — which is
  exactly why it gets a letter, not a workaround.
- **Do not assume silence is consent, and do not assume terms are toothless.** *Ryanair v PR
  Aviation*, C-30/14 (CJEU): *"the holder of a publicly accessible database is free to determine by
  contract… the conditions of use of its database"* — failing to qualify for database protection
  does not make a database free to take. *hiQ v LinkedIn* was won on the access statute and still
  ended in a permanent injunction, deletion of all scraped data, and a $500 000 payment, on a
  contract claim.
- **Do not republish whole articles** under the quotation right; Art. 49 is bounded by *"kratki
  odlomci"*.
- **Do not harvest any camera** whose terms forbid it. AMSS/Naxi: *"Strogo je zabranjeno svako
  korišćenje kamera na bilo kojoj drugoj Web lokaciji ili računarskoj mreži bez pisanog odobrenja."*
  Windy calls continuous scanning a material breach. SkylineWebcams forbids modification without
  written authorisation, and deriving a scalar is arguably modification.
- **Do not present any acoustic figure as an official noise measurement.** Zakon o zaštiti od buke
  Art. 25 reserves that to accredited bodies. Ours are research observations and must be labelled so
  on every screen.
- **Do not record speech.** Krivični zakonik Art. 143 penalises unauthorised listening to and
  recording of a *razgovor* — a conversation. A level meter that never writes an audio sample is not
  that; a recorder is.

## 8. Registered open is not available

Two findings today share one shape, and they are the reason this file ends here rather than with a
conclusion.

Serbia's seismic network is registered with the FDSN as **SJ**, carries **DOI 10.7914/SN/SJ**, and
its metadata declares `restrictedStatus="open"` on the network and on both AVAS and BEO. The EIDA
routing service names GEOFON as the data node. And the availability extent, queried directly, shows
this: **AVAS HHZ at 100 Hz covering 2024-12-05 → 2026-01-28 in sixteen fragments; AVAS EHZ and SHZ
covering six days at the end of January 2026; and BEO — the station in the centre of Belgrade,
recording since 1918 — returning no availability rows at all.** `dataselect` returns 204 No Content
even inside the declared window.

This is the same shape as AGROS (29 GNSS stations behind a brochure), RATEL (a real register with no
export), Plovput (an "open system" with no technical door), and BVK (a laboratory with a page
carrying no numbers). **The instrument exists, the law permits, and the data does not flow.**

Which means the binding constraint on this project is not copyright and not privacy. It is that
Serbian public institutions hold real instruments and publish almost nothing from them — and the
remedy for that is written in §5, not in a scraper.

## 9. Later readings of this frame

- 2026-09-09 — the news layer re-combed under §§1–4 and §7: `NEWS_AUDIT_2026-09-09.md` (three corrections to records, twelve candidates sorted into official materials / clean-robots publishers / left alone, one new named refusal, a weekly re-capture). Nothing in that audit widens the narrow reading of §1; the three edge cases it added are E-011 to E-013.
