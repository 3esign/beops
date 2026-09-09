# BEOPS — the city's past and the city's ground

Status: current
Date: 2026-09-05
Author: claude-cowork

Two questions answered together, both under the v1 rule that **the project depends on nobody**.

1. Where are the sources that update *periodically* — semi-live — so that a **pattern of change** can be read and compared?
2. What free **spatial data** exists for Belgrade: the static base everything live gets layered onto?

---

## PART ONE — reconstructing a past from sources that keep none

### The finding

Belgrade's public pages publish the present and forget it. The parking service shows free spaces now
and no history. RHMZ shows today's water level. `beoeko.com` shows this hour's air. **The Internet
Archive has been quietly keeping what they threw away.**

Queried directly against the Wayback CDX API, collapsed to distinct capture-days:

| Page | Capture-days | First | Last |
|---|---:|---|---|
| **parking-servis.co.rs/lat/garaze-i-parkiralista** | **101** | 2014-12-24 | 2026-04-18 |
| **beoeko.com** (city air network) | **257** | **2005-03-06** | 2026-05-13 |
| **hidmet.gov.rs** water levels | **180** | **2008-12-22** | 2026-08-21 |
| elektrodistribucija.rs | 192 | 2021-03-02 | 2026-08-03 |
| vazduh.sepa.gov.rs | 2 | 2026-05-16 | 2026-06-12 |

**Twenty-one years of Belgrade air and eighteen years of Sava and Danube water levels**, in snapshots
of pages that store nothing themselves.

### And the snapshots contain the numbers — checked, not assumed

101 empty pages would be worthless. They are not empty. The capture of **2025-04-01** parses cleanly
into a full table: Baba Višnjina 182 · Botanička bašta 64 · Dr Aleksandra Kostića 34 · Masarikova 390
· Obilićev venac 409 · Pinki 121 · Pionirski park 324 · Vukov spomenik 72 · Zeleni venac 181 · Ada
1160 · Belvil 412 · Bežanijska kosa 67 · Blok 43 155 · Čukarica 59 · Cvetkova pijaca 38 · Donji grad
198 · **Kalemegdan 101** · **Kamenička 57** · **Kapetanija 54** · Ljermontova 66 · Međunarodni
carinski terminal 214 · Milan Gale Muškatirović 262 · Opština NBGD …

### What the archive immediately resolved

**Kalemegdan and Kamenička report 0 in all ten of tonight's samples**, and the interim analysis logged
this as unresolved: genuinely full, or a stuck field? **In April 2025 they were 101 and 57.** The
field is not dead-since-forever. The zeros are either real or a recent breakage — and that is a
question the live source could never answer and the archive answered in one request.

**And the set of locations changes.** *Kapetanija* is in the 2025 capture and absent from tonight's
27. That is not noise; it is a measurement in its own right — **which of the city's car parks have
disappeared**.

### Three limits, stated before anyone builds on this

1. **101 capture-days across eleven years is not a time series.** It is a scatter of moments, uneven
   and uncontrolled, chosen by a crawler's schedule and by whoever happened to request a capture. Any
   analysis must treat sampling as non-random and say so.
2. **There are now three timestamps, not two.** When the source measured (unknown), when the page
   displayed, and when the Archive captured. The project's own five-state alphabet needs a fourth
   time field for archival capture, or the provenance is wrong on screen.
3. **The 2014 capture contains no numbers at all** — only a directory: *Garaža „Aerodrom"*,
   *Parkiralište „Ada Ciganlija"*, *Blok 42*, *Sava centar*, *Simpo*. The old site listed the estate;
   it did not count it. So the occupancy series **starts somewhere after 2014**, and every vintage
   must be checked for what its numbers mean before being joined to the next. Obilićev venac at
   **409** in 2025 does not read like free spaces for that garage; it may be capacity in that
   vintage. **Do not concatenate vintages without checking the semantics of each.**

The 2014 capture is still valuable — it is a dated inventory of Belgrade's parking estate, and
comparing it to tonight's 27 locations is a real finding about what the city lost.

### The rest of the periodic layer

| Source | Repeats | Span | Comparable with itself? |
|---|---|---|---|
| **NBS exchange rates** | daily, thousands | RSD era, 23+ years | Yes. Public, no login, date-range search, **direct CSV/XML export**. (NBS's SOAP service needs a username, password and licence ID — disqualified; the plain export tool is what qualifies) |
| **JRC GHSL** | 10–12 epochs | **1975 → 2030** | Yes, by construction — the longest consistent-method span found |
| **CORINE Land Cover** | 5 epochs + dedicated Change layers | 1990–2018 | Yes; **Serbia confirmed** by a country-specific EEA page |
| **Hansen Global Forest Change** | 24 annual | 2000–2023 | Yes, one unbroken algorithm |
| **Census (RZS)** | 4 safely comparable rounds | 1991–2022 | Partial — a single table runs 1948–2022 across nine rounds, but the territorial and methodological breaks around 1991 make the older ones unsafe as one series |
| **ohsome API** (OSM history) | any interval | since **2007-10-08** | Metadata endpoint works keyless and confirms the span; **the statistics endpoints returned 403**, including the docs' own example. Whether the free signup is instant is unconfirmed |
| **Geofabrik Serbia** | daily | from now, if we archive it ourselves | Current `.osm.pbf` is open and daily. **The full-history `.osh.pbf` is restricted**: *"The history file contains personal data and is available on the internal server only."* |
| **RIK elections** | ~10 elections | polling-station level | The measurement compares; **the access method changed** — bulk XLS existed in 2016, today it is UI-only under CC BY-NC-ND |

### Series that cannot be compared with themselves — say it out loud

- **ESA WorldCover 2020 vs 2021**: ESA's own documentation warns the difference mixes real change with
  algorithm change. Two epochs, not a series.
- **JRC Global Surface Water**: the current monthly/yearly product covers only 2022–2024; earlier
  years need a deprecated release. A version boundary, not a continuity.
- **The retail price-list datasets on data.gov.rs**: not one series but **26+ independent
  single-company datasets**, formats split across XLSX/CSV/JSON, cadences ranging from *Daily* to
  literally *"Irregular"* and *"Punctual."* Unusable as a price index without rebuilding it.
- **Census 1948–2022** as one run — see above.

---

## PART TWO — the spatial base

**Total for the ten core layers: roughly 1.1–2.3 GB.** It fits on a laptop with room to spare; it is
an afternoon's download, not a storage problem. Pulling every epoch of everything across all six
themes would reach low tens of GB — a different and much larger ambition.

### Terrain

**Copernicus DEM GLO-30** is the base, and Belgrade's exact tile is
`Copernicus_DSM_COG_10_N44_00_E020_00_DEM`, reachable with `aws s3 --no-sign-request` from
`s3://copernicus-dem-30m/`. Licence, quoted: *"The use rights granted under this licence are free of
charge to the User."* **It is the only 30 m DEM in this inventory that needs no account at all** —
SRTM, ASTER, ALOS and NASADEM all want a login, and **FABDEM is CC BY-NC-SA, non-commercial only**,
which must be known before anyone builds on it. **EU-DEM no longer exists**: CLMS states *"EU-DEM is
not maintained anymore and is no longer available on our website."*

And one call with no key at all: **PVGIS** (JRC) returns real solar irradiation and PV potential for
any Belgrade coordinate, 30 requests per second per IP, no registration, no download.

### Built form, and the finest temporal grain we have

**WSF Evolution** is the standout: **30 m, annual, 1985–2015 — thirty-one consecutive years** of
settlement growth per pixel, each with its own reliability score, CC BY 4.0, no registration. Every
other built-form product jumps in five- or ten-year steps. **GHSL** complements it across
**1975 → 2030** in one consistent EU pipeline: built-up surface, **building height**, volume,
population and the settlement model, all CC BY 4.0 — *"Reuse of this data is authorised with proper
acknowledgment of the source."*

**Geofabrik's Serbia OSM extract** does triple duty — buildings, roads, boundaries — updated daily,
ODbL, 228 MB for the whole country, 20–50 MB clipped to Belgrade.

**Confirmed absent:** no open LOD1/LOD2 3D building model for Belgrade exists. GHSL and WSF3D give
gridded height, not per-footprint geometry.

### Surface, soil, geology

**ESA WorldCover** at 10 m is the finest free "what is actually on the ground" layer. **CORINE** is
confirmed for Serbia by a country-specific EEA page — unlike Urban Atlas, which is not. **SoilGrids**
(ISRIC) gives 250 m soil properties at six depths, CC-BY.

**The Digital Geological Map of Serbia** is served by Serbia's own Geological Survey through
EGDI/OneGeology as WMS, **100% coverage** — but with a non-commercial clause and the survey's own
warning that it *"cannot be used when detailed geological information is needed"* at 1:1,000,000.

### Water and risk — the strongest theme

- **JRC Global River Flood Hazard Maps** cover Serbia at **six return periods** (10, 20, 50, 100, 200,
  500 years), CC BY 4.0, and the access statement is unusually explicit: *"Anybody can directly and
  anonymously access the data, without being required to register or authenticate."* The product
  disclaims itself as *"not an official flood hazard map"* — quote that wherever it is shown.
- **ESHM20**, the European Seismic Hazard Model — Belgrade's seismic hazard, CC BY 4.0, no
  registration. The only hazard number for the city in this whole inventory.
- **ELSUS v2** landslide susceptibility **names Serbia explicitly** in its coverage, alongside the
  whole Western Balkans — proof this list is checked case by case and not assumed. It does require
  registration, and whether that is instant is unconfirmed.
- **JRC Global Surface Water** already names *"the Danube and Sava rivers at Belgrade"* in its own FAQ.

### People

**Kontur Population** in H3 hexagons is the cleanest-licensed population layer found — **CC BY, usable
for any purpose including commercial**, Serbia-clipped at 10–30 MB, 400 m hexagons. GHS-POP and
WorldPop cross-check it. **GISCO NUTS added Serbia in May 2024** as a candidate country — but the
GISCO population grid, built on an EU census-grid regulation, probably did not, which is **a coverage
split inside a single programme** worth remembering.

### Belgrade in the past — and the quiet find beats the famous one

**Дигитална НБС** — the National Library of Serbia's digital library — is live, public and needs no
login, with a *Карте* collection spanning the 16th to the 20th century. Opened directly: **"План града
Београда", 1921, Cadastral Department of the Belgrade Municipality, scale 1:10,000, marked Public
Domain**, high resolution. A century-old city plan, free, in our own national archive.

**Mapire** (Habsburg Military Surveys, 1763–1887) carries a real catch. All three surveys mapped
Habsburg territory, and Belgrade's old town was Ottoman or Serbian throughout all three — the only
Habsburg window, 1717–39, predates them. What was almost certainly surveyed in fine detail is
**Zemun**, a Habsburg frontier town until 1934. So the left bank very likely, the historic right-bank
core very likely not. *This is inference: the viewer returned 403 and was not opened.*

Also confirmed live: **Old Maps Online** (10 Belgrade maps, 1717–1939), **Wikimedia Commons** old-map
categories, **Europeana** (the National Library of Serbia is an aggregated partner), and the
**Historical Museum of Serbia**'s 600-item map collection including 1730s Belgrade plans — **not
digitised**. **CORONA** declassified satellite imagery is free where already scanned, $30 a frame
where not; Belgrade's specific frames unconfirmed.

**One confirmed refusal:** the **Vojnogeografski institut sells** its topographic archive rather than
opening it. Disqualified for v1.

### Stops at the border, or never came

Carried forward: **EEA NOISE** and **Copernicus Urban Atlas** (EEA38 only), **Google Open Buildings**
(never aimed at Europe). New: the **Copernicus SUHI** urban-heat service is a three-city pilot, none of
them Belgrade; the **GISCO population grid** is probably EU-only; **EU-Hydro** is suspected and
unconfirmed; and **the CLMS high-resolution layers**' country list could not be confirmed for Serbia,
unlike CORINE itself — check before relying on imperviousness or tree-cover density.

---

## The ten to assemble first

1. **Copernicus DEM GLO-30** — terrain, slope, drainage; the only zero-friction 30 m DEM.
2. **Geofabrik Serbia OSM** — buildings, roads, boundaries, daily, ODbL.
3. **ESA WorldCover 10 m** — the finest free ground-cover layer.
4. **JRC GHSL suite** — fifty-five years of consistent built form and population.
5. **WSF Evolution 1985–2015** — the only annual settlement-growth record.
6. **JRC Global Surface Water + Flood Hazard** — the rivers' history and the flood envelope at six
   return periods, both naming Belgrade.
7. **ESHM20** — the city's seismic hazard.
8. **Kontur Population H3** — the cleanest-licensed population layer.
9. **SoilGrids 250 m** — what is under the pavement.
10. **Census 2022 + GADM + Natural Earth** — the official units, so a finding is *about Belgrade* and
    not about an arbitrary pixel.

**Plus, at zero cost and zero download:** PVGIS for solar, and the Wayback CDX API for the past of
every page in the registry that keeps none.

## Honest verdict

Done: the Wayback CDX queried directly for five Belgrade pages with capture counts and date ranges; a
2025 capture parsed to prove the numbers are actually there; the 2014 capture opened to prove they are
not, which bounds where the series can begin; an open question from tonight's pilot resolved from the
archive; and a spatial inventory across six themes with Belgrade coverage checked per product rather
than assumed, sized at 1.1–2.3 GB.

Not done, and not claimed: nothing was downloaded beyond the probe captures; no account was created;
no dataset was clipped or ingested. The ohsome statistics endpoints return 403 and the signup flow is
unverified. Mapire's Belgrade coverage is inference, not observation. Serbia's presence in the CLMS
high-resolution layers, GISCO LAU, EU-Hydro and the GISCO population grid is unresolved. The
comparability of every archived parking vintage is unchecked beyond the two captures opened here, and
the 2025 Obilićev venac figure of 409 is a live warning that a field name can change meaning between
vintages.


---

## Addendum, same night: two of the three open questions closed

**1. ohsome is open, and Belgrade has a measured built history.** The earlier 403 was a bad example
query, not a closed door. A live count over a Belgrade bounding box, with no key and no account:

| date | buildings mapped in OSM, Belgrade bbox |
|---|---:|
| 2010-01-01 | 1 219 |
| 2014-01-01 | 3 699 |
| 2018-01-01 | **89 423** |
| 2022-01-01 | 97 411 |
| 2026-01-01 | **108 434** |

History runs from **2007-10-08** to **2026-07-27**, any interval, any bounding box.

**The caveat is the whole finding.** This measures **OSM's mapping of Belgrade, not Belgrade**. The
jump from 3 699 to 89 423 between 2014 and 2018 is a mapping campaign or an import, not eighty-six
thousand buildings going up. From 2018 onward the growth is plausible and readable. But that jump is
itself a measurement of something real — **civic attention to the place**, the sense named in round 2
and now, for the first time, quantified. One source, two series: how much city is built, and how much
city is noticed.

**2. CLMS Imperviousness covers Serbia — against expectation.** The product index carries a named
entry, `"area":"Serbia"`, with the file `IMD_2018_010m_rs_03035_v020` — sealed surface at **10 m**,
EPSG:3035. So Belgrade gets imperviousness even though Urban Atlas and EEA NOISE stop at EEA38.
**Check tree cover density and grassland the same way** rather than assuming they follow either
precedent — this product proves the coverage line is drawn per product, not per programme.

**3. EGMS is still unresolved, and the probe designed to settle it cannot.** EGMS publishes only the
phrase *"over the Copernicus participating countries"*, with no country list anywhere reachable. The
download API was probed with Belgrade's EPSG:3035 tile — **E51N24** — against a control set including
a deliberately nonsensical tile, **E99N99**. Every one returned **401**, including the nonsense tile,
which means authentication is checked before existence and a 401 carries no information about
coverage. The question is not blocked, only unanswered: EU Login is instant and self-service, so
opening the EGMS Explorer over Belgrade settles it in five minutes.
