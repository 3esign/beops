# BEOPS — the news layer re-combed: what we have, what was wrong, what else is lawful

Status: measured — 27 permission captures from the PC on 2026-09-09 (12 re-captures, 3 extended
records, 12 new records; one manual refusal). Where a line says "pre-screen", the robots.txt and
the feed were also read from the cloud the same day; the ledger line is what counts.
Date: 2026-09-09
Author: claude-cowork, for the editor of record

**This is not legal advice.** It applies the frame in `COLLECTION_LEGAL_FRAME.md` to one layer
— news — and records what a second look found. Every verdict below is repeatable from the
stored bytes under `research/evidence/legal/<SID>/`.

## 1. What the news layer actually is

The collector keeps, per feed item, **the headline (capped at 200 characters), the link and
the publisher's own publication time**. It stores no description, no body, no image, and no
raw feed (`store_raw=false`; only the hash of the response). The mind reads the headline as a
numbered fact and links back to the publisher. This is the narrow reading of Art. 49 (short
quotation, attributed) plus metadata, chosen because Serbia has no text-and-data-mining
exception to rely on (§1 of the frame). Nothing in this audit widens that.

Twelve news records existed before today (S68–S79). Seven are polled (Tanjug, Danas, Studio B,
Beta, Danubeogradu, Gradnja; Vračar is captured but not polled), three are registered and
switched off (Kurir, Telegraf, Informer), and three named refusals stand (Beobuild; Zoomer,
Insajder, eKapija; Politika, Vreme, Nedeljnik).

## 2. What was wrong or missing — corrections appended to the registry

| Record | Finding | What changed |
|---|---|---|
| **S68 Tanjug** | Registered as "state agency, state-owned". The impressum names the publisher as **Tačno d.o.o.**, Dečanska 12/7 — a private company that has operated the Tanjug brand since the state agency was wound up. | `reuse` corrected; `news_audit_2026_09_09` records the source. Editorial alignment stays noted; the ownership claim is now true. |
| **S77 "KRIK + Cenzolovka + Mašina"** | One record, three outlets, one host, one capture. Two of the three were never captured. | Record split: S77 = KRIK; **S200 Cenzolovka**, **S201 Mašina** with their own captures. |
| **S74 Gradnja.rs** | The feed answers `X-Robots-Tag: noindex, follow`. The capture saw the signal; no decision was recorded. | Decision recorded (E-011): `noindex` addresses search indexing of the feed document; BEOPS keeps a headline, a link and a time and links back — that is `follow`. Verdict stays permitted; revisited if an AI signal appears. |
| **S73 N1 news sitemap** | A Google-News sitemap is addressed to search engines; it is not a feed the publisher offers to readers. robots.txt permits it for every agent. | Recorded as an edge case (E-011). Not polled in v1 — Danas of the same group is. |
| **S69 Danas, S73 N1, S205 Nova** | Same newsroom group under sale (Adria News → Alpac Capital). | Re-captured today; noted that three streams of one newsroom would be one voice counted thrice. Only Danas is polled. |
| **S70/71/72** | Registered, captured, disabled — without the reason written down. | Reason written: v1 does not need three government-aligned tabloids for service content when Tanjug, Studio B, Beta and Novosti-Beograd carry it. |
| **S76 Beta** | "Commercial reuse needs a paid subscription". | Recorded that BEOPS is non-commercial research and that a product would need Beta's licence. |
| **All twelve** | Captures were three days old. | All re-captured today; a **weekly re-capture** now exists (`legal_capture.py --recheck-collectors`, task `Beops_Legal`), because a permission captured once is a claim about one day. |

Nothing collected so far was collected without permission evidence; the corrections are to the
descriptions of sources, not to their verdicts — with one exception in the other direction:
the S204 refusal below is new and closes a door before anyone opened it.

## 3. What else is lawful — twelve candidates, pre-screened, captured, sorted

Three sorts, in the order the frame itself ranks them.

### 3a. Official materials — outside copyright (Copyright Act Art. 6(2)), the cleanest corpus

| SID | Source | Route | Verdict |
|---|---|---|---|
| **S15** (extended) | **beograd.rs** — Beoinfo vesti and Servisne informacije | robots.txt **disallows `/feed/`** (the RSS route is therefore refused) and permits the listing pages; terms permit downloading source documents without restriction with attribution and a link. | Listing pages, title + link + date. Needs an HTML listing parser (not RSS) — the one engineering item this audit leaves open. Political framing of Beoinfo is real; the service notices are the value. |
| **S11** (extended) | **BVK** (water utility) RSS `bvk.rs/feed/` | robots.txt clean; the feed answers `X-Robots-Tag: noindex, follow` (E-011); ~10 items; outages, works, deratisation per street. | Enable, 30 min. |
| **S175** (extended) | **Beogradske elektrane** RSS `beoelektrane.co.rs/feed/` | robots.txt clean; "Radovi na toplovodnoj mreži", a daily **"Stanje sistema"** line, outage reports. | Enable, 30 min. The daily status line is the closest thing to an instrument the heating operator publishes. |
| **S203** | **Vlada Republike Srbije** RSS (`srbija.gov.rs/rss/?change_lang=cr`) | robots.txt harmless; the feed works only with the language parameter; the feed lagged the page by three weeks when read. | Enable, 60 min; national, the sorter filters. |
| **S204** | **MUP** (police press releases) | robots.txt **names ClaudeBot** (and GPTBot, OAI-SearchBot, Bytespider…) with `Disallow: /`; no `*` group. | **Refused.** Art. 6(2) would put the texts outside copyright; the project honours a named opt-out regardless (E-012). A letter, not a workaround. |
| **S206** | **JP Putevi Srbije** — road conditions, notices | no robots.txt, no feed, HTML listings, "all rights reserved" footer. | Lead; needs a parser; not in v1. |
| S79 (already) | GO Vračar | the only municipal feed | Candidate for the same layer; not polled in v1. |

### 3b. Publishers with a clean robots.txt and a public feed — headline, link, time only

| SID | Source | Pre-screen | Verdict |
|---|---|---|---|
| **S195** | **RTS** (public broadcaster) `rts.rs/vesti/rss.html` | robots.txt: two harmless disallows; RSS 2.0, 20 items, **Cyrillic**, sub-hourly. | Enable, 30 min. The embedding organelle is multilingual; the digest keeps the script as served. |
| **S196** | **Večernje novosti — Beograd** `novosti.rs/rss/beograd` | robots.txt: `/dopisno/` only; ~100 items, **all Belgrade**. | Enable, 30 min; government-aligned per media research → service content. The only Belgrade-only feed of a national daily besides Tanjug's branch wire. |
| **S197** | **Euronews Srbija** `euronews.rs/rss/srbija` | robots.txt `Allow: /`; ~100 items. | Enable, 30 min; licensee ownership to record. |
| **S198** | **B92** `b92.net/info/rss/` | robots.txt blocks Bytespider and `/ajax` only. | Enable, 30 min; service content. |
| **S199** | **CINS** `cins.rs/feed/` | robots.txt empty disallow; newest item 2026-07-09. | Enable, 60 min; investigative cadence, like KRIK. |
| **S200** | **Cenzolovka** `cenzolovka.rs/feed/` | robots.txt empty disallow; feed 200 from the PC. | Enable, 60 min. |
| **S201** | **Mašina** `masina.rs/feed/` | WordPress default robots; the feed answers `X-Robots-Tag: noindex` (no `follow`). | Enable, 60 min — the E-011 decision applies; recorded on the row. |
| **S202** | **Istinomer** `istinomer.rs/feed/` | robots.txt empty disallow. | Enable, 60 min; a claim-outcome source for the mind's scoring later. |
| **S205** | **Nova.rs** | robots.txt clean; from the cloud `/feed/` redirect-looped, from the PC it answers 200 — the loop was the reader's, not the site's. | Not enabled: third stream of the Danas/N1 newsroom. |

### 3c. Looked at and left

- **Blic** (Ringier): the cloud tool used for the pre-screen is not allowed to read that host, so
  nothing was concluded; a capture from the PC is the only honest route and was not run today.
- **Mondo**: robots.txt disallows `/feed/` — the same CMS as beograd.rs; no other feed route found.
- **GSP Beograd** (`gsp.rs`): answered 500 from `gsp.co.rs` when read; the S14 BG Prevoz route
  already carries the transport notices.
- **AMSS "stanje na putevima"**: the association's terms already carry a refusal for its cameras
  (S106); the text route was not pursued.
- **Politika, Vreme, Nedeljnik, Beobuild, Zoomer, Insajder, eKapija**: refusals stand.

## 4. What the captures measured

All 27 captures completed. Every polled or newly enabled source is allowed for our agent and for
`*`, answers 200, and carries no `Content-Signal`. Three carry `X-Robots-Tag: noindex` on the feed
document (Gradnja and BVK with `follow`, Mašina without) — decided under E-011. MUP is recorded as refused
by a manual verdict on top of the stored robots.txt. Two captures had to be repeated with
`--allow-shared-host` because the City portal and the water utility already had records for
other products on the same host (S31/S64, S63/S175) — the identity check doing its job.

## 5. Three edge cases added (08-provenance/EDGE_CASES.md)

- **E-011** — `X-Robots-Tag: noindex` on a feed, and a news sitemap addressed to Google: signals
  that are not about us, and how we read them.
- **E-012** — a named opt-out on material that is not a copyright work at all (MUP): the opt-out
  wins, because the project's promise is about consent, not about copyright.
- **E-013** — headlines carry names: the news layer as personal-data processing (ZZPL Art. 92
  safeguards). What the collector already does (no bodies, no images, no profiles, no search by
  person) and the one thing it does not yet do: **a retention rule**. Proposed: public exports
  carry the window only (already true); the month files stay local as research evidence;
  nobody builds a per-person index. This is a decision for the editor, written down, not taken.

## 6. Honest verdict

- The news layer was lawful before this audit and is lawful after it; what the audit found was
  **descriptions that were wrong** (Tanjug's owner), **records that hid two uncaptured sources**
  (S77), and **a signal seen and not decided** (Gradnja). None of these changed a collection
  verdict. That is the good news and it is also the limit of what "re-combing" can find: the
  evidence was there, the reading was careless in three places.
- The valuable additions are not the new commercial feeds but **the three official routes** —
  the City portal, the water utility, the heating operator — and the discipline of a **weekly
  re-capture**. Eight more headline streams make the digest louder, not wiser; the sorter and the
  embedding organelle exist to fold them.
- What is still open: the beograd.rs listing parser; the retention rule (E-013); Blic from the
  PC; and the six lawyer's questions of the frame, unchanged.
