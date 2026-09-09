# BEOPS — New senses, round 3: Serbia's own instruments, and senses obtained by reasoning

Status: current
Date: 2026-09-05
Author: claude-cowork

Continues round 1 (`NOVA_CULA_I_USPAVANA_TEHNOLOGIJA_2026-09-05.md`, 19 dormant categories) and
round 2 (`NOVA_CULA_RUNDA2_2026-09-05.md`, 28 global candidates and a twelve-medium typology).

**The brief changed for this round.** The ask was no longer "find more feeds" but *find senses,
instruments and devices in the city that increase the city's intelligence.* So the test applied to
every candidate here was not "is there a feed" but:

> **What question would the city be able to answer, that it cannot answer today?**

Candidates that failed that test were cut before reaching this document, however open their data.

Every entry was opened at its own source. Where a fetch failed or a page was JavaScript-only, that is
stated rather than filled in from reputation.

---

## 0. What this round changes, in seven lines

1. **The richest vein was the direction we had not looked: Serbia's own institutions.** Rounds 1 and
   2 searched global networks and kept finding that famous ones stop at the EEA38 border. The
   instruments are here, run by RHMZ, SEPA, the seismological institute, the city, and the utilities.
2. **SEPA's official air network publishes a measurement hour.** Unlike parking, it does not have our
   fifth-state problem — and it gives us the regulatory-grade reference layer against which the
   citizen networks can finally be checked.
3. **Two independent networks cover the same city** — SEPA's 17 stations and the city health
   institute's 31 at `beoeko.com`. That is not duplication; it is the only way to catch a bad sensor.
4. **The city already counts traffic on ten named streets**, per lane, with speed and vehicle class,
   into one named office. This is the most requestable finding in three rounds.
5. **A live transit feed exists and is private.** Belgrade's own GTFS dataset states real-time is not
   included, yet Google has published live Belgrade arrivals since February 2024.
6. **Belgrade has had no upper-air measurement since 1 April 2016**, when soundings moved to Niš.
7. **Two fashionable techniques were killed with numbers**, which is worth more than two more feeds.

---

## PART A — Serbian institutions: what actually exists

Legend: `probe_ok` a data path was opened and returned data · `primary_page` the page exists but the
data path does not or is not machine-readable · `lead` worth a direct request · `dead` published once,
abandoned, with the date · `no_coverage` confirmed absent.

| Institution | Product | Machine-readable | Belgrade granularity | States a measurement time? | Status |
|---|---|---|---|---|---|
| **SEPA** | `vazduh.sepa.gov.rs` real-time air quality | HTML table, no export found | **17 named Belgrade stations**, 5 pollutants | **Yes** — explicit hour, and explicitly "неверификоване сатне вредности" | `probe_ok` |
| **SEPA** | Weekly PDF bulletin, `sepa.gov.rs/koncentracije/` | PDF, archived 2021→2026, published Wednesdays | City-wide | Yes, week-dated | `probe_ok` |
| **Gradski zavod za javno zdravlje** | `beoeko.com` live table | HTML table | **31 stations**, including Lazarevac, Mladenovac, Vinča, Borča | Yes, explicit hour | `probe_ok` |
| **Gradski zavod za javno zdravlje** | Daily PDF archive on `zdravlje.org.rs` | PDF | City-wide | Yes | **`dead` — last report 25.08.2021** |
| **RHMZ** | Radar imagery, `osmotreni/radarska.php` | Static composite GIF | City — **MRL-5 at Košutnjak + LAWR in Belgrade** | **Yes** — UTC per image | `probe_ok` |
| **RHMZ** | Water levels, `osmotreni/stanje_voda.php` | HTML table | Per gauge — **Sava at Beograd 133 cm, Danube at Zemun 176 cm** on 05.09 | Yes, "на дан" | `probe_ok` |
| **RHMZ** | Hydrology bulletin + RSS/ATOM | RSS and ATOM exist | Per gauge | Yes — **but content observed was 12 days and ~8 weeks stale, reproduced twice** | `lead` — verify in a browser before building on it |
| **RHMZ** | Warnings, `upozorenja/` | HTML only, no CAP/RSS found | National, rivers named | **Yes** — explicit validity window | `primary_page` |
| **Seizmološki zavod** | Automatic event table, `Alerts/tableCyr.php` | Plain HTML, trivially parsed | National; **station BEO in central Belgrade, AVAS on Avala** | **Yes** — GMT origin time to 0.1 s | `probe_ok` |
| **Elektrodistribucija Srbije** | Planned outages, rolling 4 days | HTML | **Per municipality**, Belgrade named | Yes — future window per outage | `probe_ok` |
| **JP Putevi Srbije** | Traffic counting, PGDS 2013–2025 | **XLS and PDF** | Road class, not per station | Annual only | `probe_ok` (aggregate) |
| **SMATSA** | eAIP and NOTAM | HTML/PDF, no login | Belgrade FIR | Inherently timed | `probe_ok` |
| **Aerodrom Nikola Tesla** | Live flights, `beg.aero/eng/flights` | Rendered table | Airport | **Yes** — "Landed at 09:49" | `probe_ok` |
| **data.gov.rs** | National portal + REST API | **Real JSON API**, reads open | Scattered; thin for Belgrade | Per dataset | `probe_ok` (platform) |
| **RZS** | `opendata.stat.gov.rs` catalogue | HTML catalogue, 731 datasets, CSV/JSON claimed per set | Includes municipal indicators | Varies | `primary_page` |
| **RATEL** | Spectrum licence register, `registar.ratel.rs/sr/reg203` | Public search form: frequency, location, licensee, station type | **Potentially every licensed transmitter in Belgrade** | Unknown — no query could be submitted | `lead` |
| **RGZ / AGROS** | 29-station national GNSS network | **Nothing public** — login-gated brochure | 29 nationally; none confirmed in Belgrade | N/A | `lead` |
| **EMS** | Real-time measurements, Energy Flux, NERA, Transparency | JS-only, invisible to fetch | National | Undetermined | `lead` — try ENTSO-E Transparency first |
| **JKP BVK** | Outage and works notices | Dated HTML posts | Per street | Yes, dated | `primary_page` |
| **JKP BVK** | `bvk.rs/kvalitet-vode/` | **No data whatsoever** — assurance copy citing 1998/99 gazette | — | No | **`no_coverage`** |
| **JKP Beogradske elektrane** | System status, planned works | Dated HTML posts | Per plant / substation | Yes, dated | `primary_page` |
| **AMSS** | Road conditions map, border cameras | Rendered map/JS | City and national | No timestamp seen | `primary_page` |
| **Železnice / Srbija Voz** | Timetable at `w3.srbvoz.rs` | Route-gated web app; base path 404 | Station level implied | No live data found | `lead` |
| **Plovput** | Notices to skippers, `nts.risserbia.rs` | HTML notices | Retrieved notice was Prahovo, **not Belgrade**, dated 12.02.2021 | Yes, dated | `lead` — possibly stale |
| **Plovput** | Public AIS vessel tracking | Described in prose only | — | — | **`no_coverage`** |
| **Grad Beograd** | Unified open-data / GIS portal | **Does not exist** — geodata permanently split across Urbel, Beoland, RGZ | — | — | **`no_coverage`** |
| **Direktorat za civilno vazduhoplovstvo** | — | — | — | — | **`no_coverage`** — function sits with SMATSA |

### The five worth taking first, and why

**1. SEPA's official network.** It answers a question BEOPS cannot answer today: *is Belgrade's air
actually clean right now, by the government's own regulatory-grade instruments* — and, because it
publishes an hour, it is the reference against which every citizen sensor we already hold can be
validated. Lowest effort, highest value found this round.

**2. RHMZ radar.** A forecast API cannot answer *is it raining over Voždovac right now.* Reflectivity
imagery from radar sited inside the city can, and it is a static file with a UTC stamp.

**3. The seismic event table.** An entirely new observational domain — the solid earth — with a
station in central Belgrade operating since 1918, a GMT origin time cleanly separated from retrieval
time, and a table simple enough to parse in ten lines.

**4. Elektrodistribucija's outage schedule.** A new category for the project: infrastructure stress
and maintenance, per municipality, rolling four days, dated in the future rather than the past.

**5. `beoeko.com`.** Not a duplicate of SEPA. Thirty-one stations reaching outer municipalities that
the national network may not, run by a different institution over the same city. Whether the two
networks share physical cabinets is unresolved and must be reconciled station by station before
either is treated as independent confirmation of the other.

### Confirmed dead or absent, with dates

- The city health institute's **daily PDF archive stopped 25.08.2021** — five years. Do not let it
  stand in for the institute's real output; `beoeko.com`, from the same institute, is alive.
- **`bvk.rs/kvalitet-vode/` has never carried a measurement.** Not a decayed feed — an empty one,
  whose only dates are legal citations from 1998 and 1999.
- **Grad Beograd has no unified open-data or GIS portal**, and never has.
- **`cad.gov.rs` has no data function at all.**
- Flagged, not concluded: **RHMZ's hydrology RSS/ATOM** returned content 12 days and ~8 weeks old on
  05.09, reproduced across two fetches; and **Plovput's notice-to-skippers** returned a 2021 notice
  for a location 300 km from Belgrade. Both need one manual browser check before anyone builds on
  them or writes them off.

### Where a request beats more searching

**RGZ's AGROS network** — 29 physical GNSS stations running commercially since 2005, and a brochure
page in front of all of it. **RATEL's register** — the search form is real and detailed; only an
interactive session or a formal request under the freedom-of-information law will reveal whether
bulk export exists. **JKP BVK's lab results** — the utility performs legally mandated testing and
publishes none of it. **EMS** — try the ENTSO-E Transparency Platform before fighting the JavaScript.

---

## PART B — Instruments that physically stand in Belgrade

An instrument whose existence is documented is a candidate for a request. An instrument nobody knows
about cannot even be asked for. This is the map for asking.

| Instrument | What it measures | Where | Owner | Documented? |
|---|---|---|---|---|
| **Seismograph BEO** | Ground motion, long-period 3-component; network processing hub | 44.809297 N, 20.471419 E, 129 m — central Belgrade, **operating since 1918** | Republički seizmološki zavod | Yes, with coordinates |
| **Seismograph AVAS** | Ground motion | Avala, 44.69595 N, 20.513157 E, 444 m | same | Yes |
| **Meteorološki radarski centar Beograd** | Precipitation reflectivity | 44°46′ N, 20°25′ E, 230 m, with a legally defined protective zone | RHMZ | Yes, named in a government decree |
| **LAWR radar** | Local precipitation | Belgrade | RHMZ | Yes |
| **Upper-air sounding, Košutnjak** | Vertical profile of the atmosphere | Košutnjak | RHMZ | **Retired.** Launched April 1987 → **1 April 2016**, then moved to Niš |
| **River gauges** | Water level | Sava at Beograd; Danube at Zemun | RHMZ | Yes, live |
| **Air-quality cabins** | PM10, PM2.5, NO₂, SO₂, O₃ | 17 SEPA + 31 city-institute sites | SEPA / GZZJZ | Yes, named per station |
| **Inductive-loop traffic counters** | Count, speed, vehicle class, **per lane** | **Mirijevski bulevar · Borska · Kirovljeva · Cara Dušana (Zemun) · Bulevar kralja Aleksandra** (2026 procurement) and **Bulevar Nikole Tesle · Marka Čelebonovića · Omladinskih brigada · Južni bulevar · Višnjička** (existing) | **Centar za upravljanje saobraćajem, Sekretarijat za saobraćaj** | Yes — ten named streets, one named office |
| **Airport noise monitoring** | Aircraft noise; WebTrak tracking tool; 2024 strategic noise maps | Around Nikola Tesla | Aerodrom Nikola Tesla | Program documented; monitor coordinates not published |
| **Broadcast transmitters** | Radio and television emission | Avala Tower and others | Various, licensed | **RATEL public register** |
| **AGROS GNSS stations** | Position, and in principle tropospheric delay | 29 nationally; Belgrade station unconfirmed | RGZ | Existence yes, locations no |
| **PurpleAir citizen cluster** | PM | Across the City of Belgrade | Private citizens | Yes, mapped — **distinct from openSenseMap and Sensor.Community** |
| **Vinča — Dosimetry and Radiation Protection** | Radiological | Vinča | Institute of Nuclear Sciences | Likely the domestic node feeding EURDEP |
| **Belgrade Astronomical Observatory** | Astronomical | Volgina 7, Zvezdara | University | Real and historical; no public machine-readable feed found |
| **AIS base stations** | Vessel position on Danube and Sava | Waterway | Plovput | Stations documented; no free public feed |

**A negative worth recording precisely:** the U.S. embassy PM2.5 monitor does not exist for Belgrade
— **the entire global embassy air-quality network went offline on 4 March 2025** for funding reasons.
And **e-Callisto**, the global solar radio-spectrometer network — small, CPU-friendly, buildable by a
university lab, exactly this project's register — **has no station in Serbia or the near Balkans**;
the nearest are Graz and Lilienfeld in Austria and Trieste in Italy. That is a *build it*, not a
*find it*, and it is the cheapest way this project could contribute an instrument rather than consume
one.

---

## PART C — Senses obtained by reasoning rather than hardware

Round 2 found one perfect specimen: continental grid frequency is Belgrade's grid frequency, because
the grid is synchronously coupled — a measurement with no local instrument. These are the others.

### Usable now

**Absence as a first-class measurement.** A feed that goes quiet is an event, provided the system can
distinguish *I could not measure* from *there is nothing there*. IODA already treats missing traffic
as an outage (Dainotti et al., ACM IMC 2011); clinical informatics calls it informative missingness
(*Diagn. Progn. Res.* 4:2, 2020, doi:10.1186/s41512-020-00077-0). BEOPS already implements an
instance of this without having named the principle — the five-state alphabet draws *unavailable* as
a positive mark and the quorum bar counts how many of N expected sources spoke.
**New question:** *how much of the city is telling us anything at all right now, and which instrument
just went quiet, for how long.* **Cost: zero new data.** This is the single highest-value item in the
round.

**River gauge plus rainfall lag.** The delay between a rainfall pulse and a downstream gauge response
is a measured property of the catchment, not a model (Giani et al., *WRR* 57, 2021,
doi:10.1029/2020WR028201). Both inputs are already reachable: RHMZ gauges and Open-Meteo.
**New question:** *given the rain that has fallen, how many hours until the river responds* — a real
measured lead time. **Honest limit:** these are big-river navigational gauges. No public real-time
gauge was found on Belgrade's small urban streams, which are the ones that actually flood streets.

**Nighttime lights as an unplanned-outage sense.** NASA Black Marble (VNP46), **750 m, daily, free,
Belgrade covered, data since 2012**. Method published with its limits stated in its own abstract
(*Remote Sensing* 9(3):286, 2017): percent-of-normal against a 90-night baseline, neural network
reaching Pearson **r = 0.48–0.58** across folds, and one full night of an eight-night test lost to
cloud.
**New question:** *did an outage happen last night, roughly where, that the planned schedule cannot
show* — because a planned-outage list by definition never contains the unplanned ones. Moderate
accuracy, and it belongs on the screen as moderate, not hidden.

**ADS-B as a wind and capacity sense.** Holding patterns, go-arounds and runway-direction changes are
responses to wind, visibility and load, inferable from trajectory alone. BEOPS already holds OpenSky;
this is new reasoning over an old feed.
**New question:** *was the airport under unusual wind or capacity stress today* — a second,
independent read on local wind and the only sense BEOPS would have for that infrastructure.

**Attention as a sense.** Wikipedia pageviews and OSM changeset density track collective interest —
never ground truth. Cite the optimistic case (*PLOS Comp Biol* 10(11):e1003892) **together with** its
corrective, "Measuring Global Disease with Wikipedia: Success, Failure, and a Research Agenda" (ACM
CSCW 2017, doi:10.1145/2998181.2998183), which exists to catalogue where the proxy breaks.
**New question:** *did attention to a place in Belgrade spike today, often before any sensor or news
feed shows why.*

**Internet activity as a presence proxy.** Untested proposal, labelled as such: build a diurnal and
weekly baseline of Belgrade-adjacent probe reachability from data already held, and watch for
departures. Context from RIPE's own Serbia focus: 189 ASNs assigned, 149 announcing, only ~30% of
ASes announcing IPv6.
**New question:** *is the city's night-time activity this week departing from its own rhythm* — a
presence signal precisely where BEOPS's rules forbid anything more direct.

### Scoped honestly, usable only at whole-city level

**Sentinel-5P NO₂, weekday versus weekend.** The coupling is real: NO₂ has two dominant urban
sources with different weekly rhythm, so a weekend dip net of weather is attributable to traffic
without counting a car. **But the resolution forbids anything below the whole city.** TROPOMI's NO₂
ground pixel is **5.6 × 3.6 km** since August 2019 — about 20 km² — and the lockdown literature,
working with Paris, Santiago and Delhi, still aggregates each megacity into a single **15×15 to
25×25 km box**. Belgrade's entire built-up extent is the size of that box.
**New question, correctly scoped:** *is Belgrade's NO₂ provably higher on workdays than weekends, net
of weather* — one number for the whole city, never a zone, ever.

### Beautiful, and not possible yet — so the next mind stops trying

- **GNSS meteorology.** The coupling is textbook and the European infrastructure exists (E-GVAP since
  2005). Serbia's AGROS has 29 stations, three of them EUREF-accredited — **Šabac, Novi Pazar,
  Knjaževac. None in Belgrade**, the nearest 70 km away, and none feeding the operational product. A
  2014 regional reprocessing project for South-East Europe lists Sofia, Bucharest and Dubrovnik as
  present or future; Serbia is not named even as an aspiration.
- **GTFS-Realtime congestion.** The method is published and simple. Belgrade's own open dataset
  states in its metadata: **"Ажурирање у реалном времену није укључено."** Yet Google has published
  live Belgrade transit arrivals since February 2024, which is impossible without a real-time
  position feed. **The pipe exists and is private.** This is not a technique to build; it is a
  question to ask.
- **District-heating leak detection from free satellite thermal.** Landsat surface temperature is
  delivered at 30 m, resampled from a 100 m native acquisition, every 16 days; VIIRS is 750 m. A leak
  is metre-scale. Fortum piloted satellite thermal in 2020 explicitly to see whether it could replace
  their working method — **helicopter thermal survey** — and published no validated resolution or
  false-positive numbers. What remains is real but modest: a **block-scale winter heat-loss gradient**
  as a screening layer for where to send the helicopter first.
- **Commercial microwave-link rainfall sensing.** Mature published method, entirely dependent on a
  telecom operator publishing link attenuation. No evidence any Balkan operator does.
- **e-Callisto.** No station in Serbia or the near Balkans. A build, not a find.

---

## PART D — Rhythms that are real, dated and citable, but not digital

A published heating-season start is a real annual observation. A fixture list is a real event series.
These are the city's rhythms that can become *dated, citable series* rather than folklore.

| Rhythm | What is actually published | Why it is a sense |
|---|---|---|
| **Heating season** | City Assembly decision, default **15 October**; explicit rule — heating stops above **15 °C for more than two hours**, resumes at **≤ 12 °C** | A temperature threshold that switches a city-scale emission source on and off. It is the largest single confound in every winter air-quality comparison |
| **School calendar** | Ministry PDF: 2025/26 began **1 September 2025**; ends **12 June 2026** (grades 1–7), **29 May 2026** (grade 8), with named breaks | Moves hundreds of thousands of people on a published schedule |
| **Ada Ciganlija's season** | Declared open **20 June 2026** at 22 °C water; water tested **twice weekly at four points**; Blue Flag for the 15th year | A dated, official start to a mass movement, plus a real bi-weekly water measurement |
| **The pontoon bridge to Lido** | Army river units assemble a **345 m, 38-segment** bridge Zemun↔Lido each summer; **disassembled 2 September 2026**, installed late June | A physical change to the city's connectivity, with exact dates and dimensions |
| **The ezan** | Rijaset publishes an annual **vaktija** computed for the Belgrade community | A precise daily astronomical series already computed for this city |
| **Bulky-waste rounds** | JKP Gradska čistoća announces paired dates: 1–2 Nov 2025, 4–5 Apr 2026, 9–10 May 2026 | A city-wide, dated intervention in the street |
| **Football fixtures** | Superliga official fixture PDF; 2026/27 began **18 July 2026** | Dated mass gatherings at known locations — a natural experiment BEOPS can observe rather than stage |
| **Sretenje, 15 February** | Fixed Orthodox feast and civil Statehood Day, one date in two registers | A rhythm that is simultaneously religious and civil |
| **The academic year** | Real but fragmented — 30+ faculties publish independently; no university-wide series exists | A named gap: someone could assemble it once |
| **Market days** | **The folklore is wrong.** Kalenić and Zeleni venac are **daily**, not weekly; what is published is holiday-adjusted hours | Recorded as the correction, not as a confirmation |

---

## Proposed registry entries

S39–S48 were proposed in round 2 and are not yet merged. This round proposes **S49–S60**, in the
order they should be added:

| ID | Source | Status | The thing that matters about it |
|---|---|---|---|
| S49 | SEPA `vazduh.sepa.gov.rs` | `probe_ok` | **States a measurement hour.** The reference layer for every citizen sensor we hold |
| S50 | GZZJZ `beoeko.com` | `probe_ok` | 31 stations, reaches outer municipalities; independent of S49 — reconcile station by station |
| S51 | RHMZ radar composite | `probe_ok` | Nowcasting; UTC per image; radar inside the city |
| S52 | RHMZ water levels | `probe_ok` | Sava at Beograd, Danube at Zemun; pairs with rainfall for the lag sense |
| S53 | Seizmološki zavod event table | `probe_ok` | New domain; GMT origin time; station BEO since 1918 |
| S54 | Elektrodistribucija planned outages | `probe_ok` | New category: infrastructure stress, per municipality, dated forward |
| S55 | SMATSA NOTAM / eAIP | `probe_ok` | Airspace changes over the city, inherently timed |
| S56 | Aerodrom Nikola Tesla live flights | `probe_ok` | Actual landing times; pairs with the ADS-B inference |
| S57 | Putevi Srbije PGDS (XLS) | `probe_ok` | Annual traffic volumes, road class — the only counted traffic we can have today |
| S58 | NASA Black Marble VNP46 | `probe_ok` | 750 m daily nightlights; unplanned-outage sense |
| S59 | RATEL spectrum register | `lead` | Potentially every licensed transmitter in Belgrade |
| S60 | PurpleAir Belgrade cluster | `lead` | A third citizen network, distinct from the two we hold — check for shared origin first |

Recorded as **negative findings**, not omitted: `bvk.rs/kvalitet-vode` (`no_coverage`, never carried
data), Grad Beograd unified portal (`no_coverage`, never existed), `cad.gov.rs` (`no_coverage`),
GZZJZ PDF archive (`dead`, 25.08.2021), U.S. embassy PM2.5 network (`dead`, 04.03.2025 globally),
e-Callisto in Serbia (`no_coverage`).

## Honest verdict

Done: two verification passes over Serbian institutions and derived senses; 27 institutional products
opened at source; a physical instrument inventory with coordinates where published; ten derived-sense
candidates with the coupling stated and the literature verified; ten city rhythms with their actual
published dates; twelve proposed registry entries and six recorded negatives.

Not done, and not claimed: nothing was registered for, no credentials were used, no organisation was
contacted, no collector was built, and no source here has been sampled more than once. Two products
(RHMZ hydrology RSS, Plovput notices) returned stale content and are flagged rather than judged —
they need a manual browser check. The relationship between SEPA's 17 stations and the city
institute's 31 is unresolved and must not be assumed independent. RATEL's register was never queried,
only its form inspected. And every "new question" in Part C is a question the sense would *permit*,
not one this project has yet answered.
