# The closed layer — what Belgrade has, that Belgrade cannot read

*An inventory of what this project found and cannot have, and what the city
would look like if it could. 2026-09-06, from `SOURCE_REGISTRY.json` at 173
sources.*

This document exists because the absences are a finding. A survey that reports
only what it obtained describes its own luck; a survey that also reports what it
was refused, and by whom, and on what terms, describes the thing it was
surveying. **What a city keeps closed is a fact about that city.**

---

## First, the honest arithmetic, because the headline is not what it looks like

| | sources | |
|---|---:|---|
| genuinely unavailable, for a stated reason | **23** | the subject of this document |
| collected, or permitted and being collected | **32** | permission captured and clear |
| captured but not usable — refused, undecided, incomplete | **7** | |
| **not yet documented** | **122** | **no obstacle at all — our own backlog** |

The largest category is not a wall. It is a queue. Nothing about those 122 is
refused; each simply awaits a twenty-second permission capture, and this
project's own rule forbids collecting before that capture exists. That rule is
right and the backlog is ours to clear.

So the closed layer is **23 sources**, and they divide into five kinds that
must never be spoken of as one. Conflating them would let us call a technical
limit a refusal, or a refusal a technicality.

---

## 1 · Refused by name, in a file, to us specifically — 9 sources

These wrote the refusal down. Several wrote it down against *this kind of
agent* by name.

| id | source | what it says |
|---|---|---|
| S143 | **Pleiades**, gazetteer of the ancient world | `robots.txt` disallows `anthropic-ai`, `ClaudeBot` and `Claude-Web`, each `Disallow: /`, while `User-agent: *` permits everything. It also serves an Anubis anti-AI proof-of-work challenge. |
| S103 | Beobuild | named opt-out |
| S104 | Zoomer, Insajder, eKapija | named opt-out |
| S105 | Politika, Vreme, Nedeljnik | `robots.txt` refusal of the feed itself |
| S106 | AMSS / Naxi Belgrade cameras | explicit refusal in terms |
| S107 | Windy webcams | explicit refusal |
| S108 | SkylineWebcams | explicit refusal |
| S144 | transit.land | `Allow: /feeds` then `Disallow: /feeds/`; RFC 9309 longest-match refuses, and the refusal stands |
| S165 | CORDIS | its own `/data/` bulk path is disallowed |

**What this costs the city.** Pleiades holds Singidunum — the Roman layer, the
oldest thing Belgrade has. Three camera networks and three news publishers mean
the project has **no eye and no voice**: it cannot see a street, and it cannot
read what the city says about itself. For an observatory whose subject is a
living city, that is not a gap in coverage; it is the removal of two senses.

**And the shape of the refusal matters.** Pleiades did not refuse researchers.
It refused *AI agents*, by name, three times. That is a scholarly infrastructure
funded to be open, closing specifically against the kind of reader this project
is. Whether that is right is not ours to decide — but it is worth recording
that the openness of open data now has an addressee.

---

## 2 · Open content behind a closed door — 3 sources

Here the *data* is public and the *access* is not, which is the most
frustrating category because nobody intended the exclusion.

- **S135 · `gisportal.rs`** — the ArcGIS server of the national road authority.
  The root listing answers anonymously and names ten folders including
  `ITS_Putevi_Srbije` and `ITS_katastar`. Every folder returns
  `499 Token Required`.
  **This is the single most consequential closure in the registry.** S57 — the
  traffic-count series, seven years deep, that labels its own provenance row by
  row — identifies its sections by node-code pairs. The geometry that would
  turn those codes into lines on a map is inside that server.
  **The numbers are open and their geometry is not, so the best series in the
  country cannot be drawn.**
- **S139 · Sava Commission** — viewing is free; downloading needs registration;
  and the data policy forbids redistribution to third parties without consent.
  A project that publishes its evidence cannot use it. The Sava at Belgrade
  must come from RHMZ instead.
- **S140 · ICPDR TNMN** — 79 Danube monitoring stations behind a Danubis
  account, and whether any of them sits at Belgrade is *not established*,
  because establishing it requires the account.

**What this costs.** Belgrade sits where the Sava meets the Danube. Both
transnational bodies that monitor those rivers are, for this project, closed.
The city's defining geography is watched by institutions we cannot read.

---

## 3 · Refused by letter, permitted by evident intent — 2 sources

- **S141 · Wikidata Query Service** — content is CC0; `robots.txt` carries
  `Disallow: /sparql`.
- **S142 · Overpass API** — ODbL; `robots.txt` carries `Disallow: /api/`, while
  publishing a sitemap *under that same path*.

Both are endpoints built to be queried programmatically, whose disallow is
plainly aimed at crawlers following expensive generated links. Both are held
under **Decision required** in the provenance index, and nothing is collected
from either. See `08-provenance/EDGE_CASES.md` E-009.

**What this costs.** 219 Belgrade monuments with coordinates, 1 409 bridge
segments, the whole OSM query surface — all obtained once, before the capture,
and now frozen pending a decision that has not been taken. This is the honest
cost of taking one's own rule seriously.

---

## 4 · Simply absent for Belgrade — 7 sources

Not refused. Measured, and not there.

| id | source | the absence |
|---|---|---|
| S62 | **Copernicus Urban Atlas** | stops at EEA38; Belgrade is outside |
| S61 | **EEA NOISE / Environmental Noise Directive** | same boundary |
| S64 | **City of Belgrade unified open data / GIS portal** | **does not exist** |
| S63 | JKP BVK water quality page | nothing published |
| S125 | Military Geographical Institute archive | commercial |
| S67 | e-Callisto solar radio network | no Serbian node |
| S65 | GZZJZ daily air quality PDF archive | published once, abandoned |

**S64 deserves its own section, and a correction.** The first draft of this
document said Belgrade publishes nothing on the national portal. That was
wrong, and checking it before publishing is the only reason it is not standing
here as a finding. **Belgrade's city administration publishes seven datasets**
(`Градска управа града Београда`), plus one from a city veterinary utility.

The true statement is more precise and, if anything, sharper. Counting every
publisher on `data.gov.rs` whose name begins with *Grad* or *Opština*:

| publisher | datasets |
|---|---:|
| Novi Pazar | **67** |
| Niš | 49 |
| Kraljevo | 45 |
| Subotica | 28 |
| Kragujevac | 27 |
| Šabac | 25 |
| Zrenjanin | 22 |
| Vranje | 21 |
| Sombor · Topola | 17 |
| Kikinda | 15 |
| … 47 further towns and municipalities … | |
| **Belgrade (city administration)** | **7** |

Fifty-seven Serbian towns and municipalities publish open data. **The capital
ranks below Topola, Priboj, Raška and Despotovac.** Novi Pazar — a city of
about a tenth Belgrade's population — publishes **nearly ten times as many
datasets**.

There is also no unified city open data or GIS portal (S64), and
`beograd.rs/robots.txt` disallows `/data`.

The consequence stands as originally written, and counting only made it exact:
almost everything this project knows about Belgrade, it knows from **national
agencies, European programmes, foreign financiers and volunteers** — not from
the city.

That is the central finding of this document, and it was not obtained by asking
anyone. It fell out of counting, and it survived being checked.

---

## 5 · Published once, then abandoned — 2 sources

S65, the city public-health institute's daily air-quality archive, and S66, the
US embassy PM2.5 monitor. Both were real instruments. Both stopped. They are
kept in the registry with their last-update dates because **a dead sensor is
evidence too** — the state's five states include `unavailable`, and this is what
that looks like at the level of a whole source.

---

## What the city would look like if the closed layer opened

Taking only the twenty-two, and only what is already known to exist inside them:

- **S135 alone** would place seven years of provenance-labelled traffic counts
  on the actual road network — the observed sections drawn as measurements, the
  interpolated ones drawn as estimates, the 1 522 stated absences drawn as
  holes. That single unlock converts the project's best table into its best map.
- **The three camera networks and three publishers** would restore sight and
  speech: a city that can be looked at and that says things about itself, both
  dated.
- **The two river commissions** would close the Danube–Sava axis with
  transnational, comparable, quality-assured measurement instead of national
  bulletins.
- **Pleiades** would give the Roman layer a gazetteer, and with it the temporal
  depth the place register is built to hold.
- **Urban Atlas and EEA NOISE** would put Belgrade in the same frame as every
  EU capital — which is precisely what their boundary at EEA38 currently
  prevents, and precisely why comparison keeps having to be argued rather than
  shown.

## What this document is for

Three things, and only these:

1. **So the absences cannot be quietly forgotten.** Every entry above stays in
   `SOURCE_REGISTRY.json` with its reason, so nobody rediscovers a refused
   source next year and starts collecting it.
2. **So the reasons stay distinguished.** A named opt-out, a token wall, a
   coverage boundary and an abandoned feed are four different facts about a
   city, and flattening them into "no data" destroys the information.
3. **So the picture is honest.** This project's claim is that it shows what is
   known and what is not. That claim is empty unless the not-known is
   inventoried as carefully as the known.

*Nothing in this document proposes obtaining any of it by other means. Where a
publisher has refused, the answer is no, and stays no.*
