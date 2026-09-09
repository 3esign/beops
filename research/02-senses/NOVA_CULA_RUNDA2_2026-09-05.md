# BEOPS — New senses, round 2: discovery, typology, and dormant municipal technology

Date: 2026-09-05, afternoon. Continues `NOVA_CULA_I_USPAVANA_TEHNOLOGIJA_2026-09-05.md` (round 1,
which took the registry from 33 to 38 sources).

Every source below was opened at its own endpoint or documentation page during this pass. Where a
fetch was blocked, rate-limited or failed DNS, that is stated instead of being filled in from
memory. Nothing here is a collector, a subscription or a request sent to anybody: this is
discovery, and discovery is not installation.

---

## 0. What this round actually adds, in six lines

- **Three domestic Serbian registries** — public procurement, business register, cadastre — live,
  searchable without login, and entirely absent from the 38-source base. The city's own
  administrative tempo is a sense we had not counted.
- **One new confirmed-live radiological sense**: EURDEP, with Serbia's own SRBATOM contributing
  32 airborne stations plus one Danube water point, near-real-time, no licence.
- **Two clean negative findings** that correct a natural but wrong assumption — EEA noise data and
  the Copernicus Urban Atlas both stop at the EEA38 line, and Serbia is outside it. Belgrade is not
  covered by "European open data" by default.
- **One sense that needs no hardware in Belgrade at all**: continental grid frequency. Serbia's grid
  is synchronously tied to the same AC phase from Portugal to Poland to Turkey, so a frequency
  reading taken anywhere in that area *is* Belgrade's grid frequency at that instant.
- **The richest single dataset found in either round**: GBIF returned 440,904 occurrence records for
  a Belgrade bounding box, almost all of it other people's phones flowing in through iNaturalist.
- **A precedent table** for the sleeping-technology categories, honest about the three where the
  world has genuinely solved this (bus AVL, traffic loops, pedestrian counting) and the several
  where it plainly has not.

---

## PART A — New candidate senses

**Legend:** ① confirmed working, Belgrade/Serbia coverage confirmed · ② confirmed working, no
Belgrade/Serbia coverage (negative finding) · ③ exists, registration/token/approval required ·
④ could not confirm (fetch blocked or coverage unresolved)

| # | Source | Cat. | Belgrade/Serbia coverage | Access terms (as the source states them) | Update rhythm / measurement time vs retrieval time |
|---|---|---|---|---|---|
| 1 | Danube/Sava River Information Services (Plovput) | ④ | Infrastructure exists — 18 RIS base stations on Danube + Sava | Site states RIS is "an open system, available to all users of the waterways"; no public map or API URL found | Unresolved. AIS messages carry vessel-reported timestamps, but there is no discoverable endpoint |
| 2 | WSPR propagation database (wspr.live) | ① | **Confirmed** — live YU-callsign spots pulled during the pass | Fully open, no registration; ClickHouse SQL over HTTP; 20 req/min | Each spot stamped to the actual 2-minute transmit window at 1-second precision; history to 2008 |
| 3 | Blitzortung / lightningmaps (lightning) | ④ | Unofficial MQTT/websocket feed is open and keyless; no Serbian contributing station found in a partial list check | De facto open, officially "work in progress" | Strikes multilaterated in near-real-time from surrounding stations — Belgrade may be covered by Hungarian/Romanian/Croatian stations with zero stations inside Serbia. Not verified either way |
| 4 | aprs.fi (APRS amateur radio) | ③ | Not confirmed (site returns 403 to automated fetch) | Free API key via self-service login | Position reports are radio-live, not batched |
| 5 | **EURDEP** (European Radiological Data Exchange Platform, JRC) | ① | **Confirmed, strong** — SRBATOM's 32 airborne stations + 1 Danube water point visible on the public map | Public map "neither requires a licence nor subscription"; SRBATOM: data available "to all members of this platform and the public" | Shared "in almost real time"; routine at least daily, many networks hourly, ≤2 h during emergencies |
| 6 | uRADMonitor | ④ | No Serbian device found | Local device access open; the worldwide map/API needs a forum account | 60 s default per device |
| 7 | Safecast | ④ | Not established — API query blocked by robots.txt | Generally open/CC-licensed | Not established |
| 8 | EEA NOISE / Environmental Noise Directive | ② | **Confirmed negative** — Serbia has no fact sheet; END covers EEA members plus Norway, Iceland, Switzerland, explicitly excluding candidate countries | Public EEA ArcGIS REST services | Annual/multi-year *modelled* exposure, not measurement |
| 9 | KiwiSDR / WebSDR receiver directories | ④ (leaning ②) | No Serbian receiver in the two directories checked; not exhaustive | Directories open to browse | Continuous live audio when tuned; no archive as a rule |
| 10 | WiGLE (Wi-Fi/BT/cell census) | ③ | Not quantified for Belgrade | Free account required for the query engine | Each observation carries its own first-seen/last-seen timestamp |
| 11 | **IODA** (Internet Outage Detection & Analysis, CAIDA/Georgia Tech) | ① | **Confirmed** — dedicated country dashboard for RS | Public dashboards, no registration; ~500 BGP monitors + UCSD darknet + Ark active probing | Near-real-time, 24/7; AS/country level, not city |
| 12 | Cloudflare Radar | ①/③ | **Confirmed** — live Serbia page: HTTP volume, device split, bot/human ratio, outage annotations, CSV export | Dashboard open, no login; API uses a developer token | Rolling aggregation windows; bucketed, not event-level |
| 13 | **RIPEstat / RIPE RIS** | ① | **Confirmed — best-verified item in this set.** Live query against AS8400 (Telekom Srbija) succeeded without auth | Fully open, no registration | Returned `query_time` alongside `first_seen`/`last_seen` — an explicit machine-readable measurement-vs-retrieval distinction, 327/327 RIS peers reporting |
| 14 | ENTSO-E Transparency Platform | ③ | Serbia (EMS) has a recognised country page | Free REST API, registration token required | Published per Market Time Unit (15/60 min), distinct from call time |
| 15 | Continental grid frequency (mainsfrequency.com) | ① | **Confirmed, and covers Belgrade by physics** | No registration, free | 10 s updates. Serbia's grid is synchronous with the continental AC area, so this single reading *is* Belgrade's grid frequency — a sense with no local hardware |
| 16 | M-Lab (internet speed-test archive) | ① mechanism / ④ Belgrade volume | Global, user-driven | Fully open, CC0, public BigQuery | States explicitly: "typically at least a 24-hour delay between data collection and data publication" — the cleanest measurement-vs-retrieval statement of any source checked |
| 17 | NASA Black Marble / VIIRS nightlights | ③ | Global grid, Belgrade in every scene | LAADS DAAC implies free Earthdata Login | Hourly/daily/monthly/yearly composites; overpass time fixed and distinct from download |
| 18 | Sentinel-5P / TROPOMI (S5P-PAL portal) | ③ (ambiguous) | Daily global coverage includes Belgrade | Portal says "freely accessible… anyone can retrieve and view"; wider Copernicus ecosystem expects a free account for bulk/API | New products daily; NRTI/OFFL/reprocessed streams differ in latency |
| 19 | Copernicus Urban Atlas | ② | **Confirmed negative, twice** — both the 2012 and 2018/2021 vintages state EEA38 + United Kingdom. Serbia is in neither | Free download for covered areas | 3–6-yearly vintages |
| 20 | **GBIF** (biodiversity occurrences) | ① | **Confirmed, richest dataset found** — 440,904 occurrence records for a Belgrade bounding box, largely iNaturalist-sourced bird observations | Search/API fully open, no key; only formal DOI downloads need an account | Each record carries `eventDate`, distinct from query time |
| 21 | Wikimedia Pageviews / Wikidata SPARQL | ④ | Not established this pass — the fetch tool refused both domains | Both documented elsewhere as fully open, keyless | Hourly/daily buckets |
| 22 | Google COVID-19 Community Mobility archive | ①/④ | Archive real and free; **discontinued 2022-10-15**; Belgrade-level granularity unconfirmed | Click-through terms | Frozen historical ranges against a Jan 2020 baseline |
| 23 | **Public Procurement Portal (UJN)** | ① | **Confirmed live** — 471 notices that day, 102,490 year-to-date, 172 procedures that day, 3,716 procurement plans for 2026 | Search without login; no bulk API found | Administrative dates — documentary time, not sensor time |
| 24 | **Business Registers Agency (APR)** | ① | **Confirmed live** — 143,109 companies, 242,267 entrepreneurs | Public search; no bulk export found | Registration events dated at filing |
| 25 | **Cadastre — eKatastar + GeoSerbia (RGZ)** | ① | **Confirmed** — both public viewers exist, plus property-price, address, investment-location and spatial-unit registries | Public web viewers; WMS/WFS bulk not confirmed | Viewer, not a stream |
| 26 | PEP725 phenology network | ④ | Serbian station presence unconfirmed | "Open, unrestricted data access for science, research and education" | Not established |
| 27 | EUREF Permanent GNSS Network | ④ | Serbian station unconfirmed | Open scientific infrastructure | Not established |
| 28 | Raspberry Shake citizen seismic network | ④ | Station finder 404'd, FDSN hostname failed DNS | Documented elsewhere as open FDSN | Not established |

### The five things in that table that matter

**The waterway gap is organisational, not physical.** Serbia has real River Information Services
infrastructure — 18 base stations across the Danube and the Sava, meeting at Belgrade — and
Plovput's own text calls it an open system. Two passes found no map, no API, no data terms. This
is the sharpest case in the whole round of infrastructure that is *legally* open with no
discoverable *technical* door, and it is worth one direct question to Plovput rather than more
searching. Vessel traffic at the confluence is, for a city built on two rivers, an obvious sense
that nobody is reading.

**EURDEP closes a gap that three citizen networks left open.** uRADMonitor, Safecast and the EEA's
noise layer all came back empty or blocked for Serbia. EURDEP came back with Serbia's own national
authority publishing, in near-real-time, without a licence. The pattern is worth stating in the
paper: in this region, official inter-governmental networks have closed coverage gaps that
citizen-hardware networks have not.

**Two negative findings are load-bearing.** EEA noise and the Copernicus Urban Atlas both stop at
the EEA38 boundary. Anyone starting a Belgrade observatory will assume both cover a European
capital; both explicitly do not. Writing that down is worth more than another source that does work.

**One sense is free because of physics.** Continental grid frequency needs no sensor in Belgrade,
because Belgrade's grid is the same synchronous AC area. This is the cheapest new sense either
round has produced and it belongs in the paper as an example of the category "senses obtained by
reasoning about coupling rather than by installing hardware."

**The city's paperwork is a sense.** Procurement, business registration and cadastre are not
sensors, and they are not exotic — but they measure the administrative tempo of the city, they are
live, they are open without login, and BEOPS did not have them. `documentary` deserves its own
medium in the taxonomy below, on equal footing with `chemical` or `acoustic`.

---

## PART B — A typology of urban senses

Twelve media. For each: what it uniquely reveals, one real anchor, and — the most valuable column —
one sense in that medium that is technically possible and for which **no public feed was found
anywhere in the world**.

| Medium | What it uniquely reveals | Anchor (real, existing) | Named absence |
|---|---|---|---|
| **Electromagnetic (RF)** | Ionospheric/tropospheric conditions; spectrum congestion; silence as an outage proxy | WSPR global beacon network (A2) — Belgrade-origin propagation confirmed live | A continuously updated **ambient RF noise-floor / spectrum-occupancy map** for an ordinary city. KiwiSDR lets a human listen; nobody aggregates noise-floor telemetry openly |
| **Acoustic** | Traffic tempo and composition; the rhythm of human activity; bio-acoustic phenology | SONYC (NYU/Ohio State, New York) — ML-classified acoustic mesh | A standing **open API for raw citywide noise levels**. Even SONYC publishes no live API; the EEA layer is modelled annual exposure and excludes Serbia |
| **Chemical (trace atmospheric)** | Combustion-source fingerprinting (traffic vs heating vs industry via NO₂/SO₂/CH₄ ratios); gas-leak signatures | Sentinel-5P / TROPOMI (A18) | An open city-scale **odour/VOC "smell-scape" feed**. Electronic-nose networks exist only as proprietary industrial monitors or one-off prototypes |
| **Mechanical / vibration** | Bridge and road load history; construction and demolition; separating quarry blasts and heavy trucks from real seismicity | Raspberry Shake citizen seismic network (A28) | Open continuous **structural-health vibration data for ordinary, non-iconic bridges**. Routine engineering practice, universally kept private by asset owners |
| **Thermal** | Heat-island microstructure; envelope quality via roof temperature; industrial and data-centre waste heat | Satellite land-surface temperature (MODIS/VIIRS/Landsat thermal) | A *continuous* public sense of the **subsurface heat plume from leaking district-heating pipes and sewers** — not a one-off drone survey |
| **Hydrological** | River stage and discharge; groundwater table; combined-sewer overflow events | EUREF/IGS GNSS zenith tropospheric delay — water vapour above a city inferred from GPS signal delay (A27) | An open real-time **combined-sewer-overflow or urban groundwater feed** for an ordinary city |
| **Biological** | Species presence as microclimate proxy; commensal fauna as a management signal; invasive spread along transport corridors | GBIF (A20) — 440,904 confirmed Belgrade-area records | Continuous, openly published **environmental-DNA sampling** of a city's rivers or air. A real method (used on the Danube for invasive species), never a standing feed |
| **Radiological** | Background variation by geology and building material; transboundary incidents; industrial/medical isotope activity | EURDEP (A5) — Serbia confirmed contributing, public, near-real-time | An open continuous **non-ionising RF/EMF exposure network** at city scale. Only single-point consultant surveys or closed apps exist |
| **Electrical grid** | Instantaneous supply/demand stress; load shedding; industrial rhythm in aggregate load curves | Continental grid frequency (A15) — Belgrade covered by physics | Open real-time **distribution-level (feeder/substation) voltage or load** for specific neighbourhoods. Every utility keeps SCADA/AMI private — the same institutional pattern as Part C |
| **Informational / documentary** | The state's own administrative tempo — procurement, permitting, litigation — as an economic and governance proxy | Public Procurement Portal (A23) | A machine-readable near-real-time **court docket / case-filing feed**. A global gap, not a Serbian one |
| **Economic / transactional** | Retail health at block level; informal-economy footprint; tourism seasonality; business churn | APR business register (A24) | Open **aggregate card-transaction volume** at neighbourhood granularity. Sold to funds and retailers; never open |
| **Behavioural-aggregate** | How people actually occupy public space, independent of any one mode-specific system | City of Melbourne Pedestrian Counting System (C9) — hourly since 2009, open API | Open **raw people-counting data from indoor private venues** (malls, concourses, stadiums). Google's "popular times" is a derived, opaque product, not a feed |

The absences column is the part to keep. It is the honest map of where a research project could
contribute an instrument rather than consume one — and three of the twelve absences (RF noise
floor, ordinary-bridge vibration, subsurface heat plume) are technically within reach of a
university lab on a small budget.

---

## PART C — Dormant municipal technology: precedents, or their explicit absence

The round-1 lesson still stands and is worth repeating before the table: *"sleeping technology" is
a list of candidates for a request, not a finding that a feed exists.* Every system below certainly
logs; the question this pass asked is narrower and more useful — **has any city anywhere already
published this stream as open aggregate data?** A named precedent turns "please give us data" into
"city X publishes exactly this, here is the endpoint."

| # | Category | Precedent found | Status |
|---|---|---|---|
| 1 | Ticketing / fare validators | Chicago Transit Authority — "CTA Ridership: Daily Boarding Totals" plus a per-station entries dataset | Existence, title and URL confirmed on Chicago's official portal; the data dictionary itself did not render this pass |
| 2 | Bus GPS / AVL | MTA Bus Time (New York) — free public SIRI real-time vehicle-monitoring API | **Confirmed live.** Page states verbatim "a real-time developer API that anyone can use for free"; key delivered within half an hour. Live since 2011 |
| 3 | Traffic signal controllers & inductive loops | UK National Highways — WebTRIS API (MIDAS loop data) | **Confirmed, strongest precedent in the table.** Page states verbatim: "All WebTRIS API endpoints are available without registration or API keys" |
| 4 | Street-lighting controllers | — | **No precedent confirmed.** Washington DC and Los Angeles publish "streetlights" datasets, but what could be confirmed of their content reads as static pole inventories, not live controller telemetry (dimming state, energy draw, fault codes) |
| 5 | Water meters & pressure sensors | Cary, North Carolina ("Aquastar") | **Unresolved.** The open-data portal exists and is openly licensed, but no water-meter dataset was located; Aquastar is more likely a per-account customer portal than an open aggregate feed. A lead, not a precedent |
| 6 | District heating | Denmark — Energidataservice.dk (Energinet) | **Unresolved.** A genuine open national energy platform with a documented API, but no district-heating consumption dataset located this pass |
| 7 | Waste-bin fill sensors | — | **No precedent found, and this is a checked absence.** Smart Dublin's portal — 931 datasets, a city known specifically for IoT pilots — returned footfall, cycle parking and fire-brigade datasets, and nothing on bin fill levels |
| 8 | Parking barrier counters | SFpark (San Francisco, 2011–2017) | **Unresolved.** The landmark case for block-by-block on-street occupancy from in-ground sensors, but current live status unconfirmed — San Francisco's portal was mid-migration. Note that BEOPS already has *garage* free-space; SFpark's unmatched contribution was *on-street* sensor-level occupancy |
| 9 | CCTV / video counting lines | City of Melbourne Pedestrian Counting System | **Confirmed.** Hourly counts per sensor since 2009, monthly updates, open API, no registration. Dublin's pedestrian-footfall dataset is a second real example |
| 10 | Building management systems in public buildings | New York City Local Law 84 / 95 energy and water benchmarking | **Partially confirmed.** The law and its mechanism (annual mandatory building-level reporting via EPA Portfolio Manager, public each 1 May) confirmed from NYC's own page; the resulting dataset URL was blocked by robots.txt |

### The pattern under the table

The three clean precedents — bus AVL, traffic loops, pedestrian counting — share one trait: the
data always had a *pre-existing external audience*. A rider wants to know when the bus arrives; a
pedestrian count feeds planning arguments and press releases. The unresolved and absent categories
— street lighting, water meters, district heating, waste bins, on-street parking sensors — are
precisely those whose only audience was ever an internal maintenance crew or a billing system.
Nobody outside the utility ever had a reason to look, so no publication habit ever formed.

That is the real shape of the sleeping-senses problem, and it changes the ask. The technology is
not rare and the data is not secret. Publication has simply never followed, because publication
follows audiences. Where BEOPS wants one of the unresolved categories from Belgrade's utilities,
the request has to *manufacture* the external audience explicitly — name who will read it and what
decision it informs — rather than point at a peer city that already did it, because for half these
categories no peer city has.

---

## What goes into the registry

Proposed as `S39`–`S48`, in the order they should be added — confirmed-live and Belgrade-covered
first, negative findings recorded as negative rather than omitted:

| ID | Source | Status | Note |
|---|---|---|---|
| S39 | RIPEstat / RIPE RIS | `probe_ok` | Only source in either round that returns an explicit machine-readable measurement-vs-retrieval timestamp pair. Use it as the reference example when specifying BEOPS's own time contract |
| S40 | EURDEP (JRC) — SRBATOM stations | `probe_ok` | 32 airborne + 1 Danube water point; near-real-time; no licence |
| S41 | GBIF — Belgrade bounding box | `probe_ok` | 440,904 records; per-record `eventDate` |
| S42 | Public Procurement Portal (UJN) | `primary_page` | No bulk API; search only. Documentary time |
| S43 | Business Registers Agency (APR) | `primary_page` | Same caveat |
| S44 | Cadastre — eKatastar / GeoSerbia (RGZ) | `primary_page` | WMS/WFS bulk access unconfirmed |
| S45 | IODA (CAIDA) — country RS | `probe_ok` | AS/country resolution, not city |
| S46 | Cloudflare Radar — Serbia | `probe_ok` | Dashboard open; API needs a token |
| S47 | WSPR (wspr.live) | `probe_ok` | Live Belgrade-origin spots; 2-minute measurement windows |
| S48 | Continental grid frequency | `probe_ok` | Covered by grid synchrony, not by local hardware |

Recorded as **negative findings**, not as sources: EEA NOISE (`no_coverage` — END excludes
candidate countries) and Copernicus Urban Atlas (`no_coverage` — EEA38 + UK only).

Recorded as **leads requiring one question, not more searching**: Plovput River Information
Services (open by statute, no technical door) and Blitzortung (open feed, Serbian station density
unknown).

## Honest verdict on this round

Done: 28 candidate sources opened at their own endpoints; ten proposed for the registry with status
and caveats; two negative findings confirmed twice each; a twelve-medium typology with a named
absence per medium; a precedent table for ten categories of dormant municipal technology.

Not done, and not claimed: nothing was registered for, no credential was used, no organisation was
contacted, no collector was built, no weights were downloaded, and no source in the table has been
sampled more than once. Coverage for six sources (Blitzortung, Safecast, PEP725, EUREF, Raspberry
Shake, Wikimedia) remains genuinely unresolved and deserves a second, more patient pass with
correct hostnames rather than being written off. The web-search budget for the pass was exhausted
partway through, so depth is uneven — denser where the endpoint was known in advance.
