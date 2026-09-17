Status: research, not yet acted on
Date: 2026-09-17
Author: claude-cowork (six parallel desk studies, consolidated and checked against the registry)

# BEOPS — new source candidates, 2026-09-17

> **Ids assigned in the same commit (C-086).**
> - New sources: N1 → S219, N2 → S220, N3 → S221, N5 → S222, N9 → S223, MUP (§4) → S224.
> - New routes captured under existing ids: N4 under S11, N6–N8 under S148, N10 under S04.
>
> Ids are permanent. Tier 2 and tier 3 candidates keep their N-numbers until a capture is taken.

**Question.** Which live, semi-static and static public data about Belgrade are not yet in
`research/SOURCE_REGISTRY.json` (215 entries), and would pass the collection frame
(`research/07-legal/COLLECTION_LEGAL_FRAME.md`)?

**Method.** The work was split into six domains:
- environment and hazards;
- mobility and networks;
- Serbian open government data;
- global baseline layers;
- energy, utilities, health and economy;
- science archives and citizen networks.

For each domain, the studies searched the web, fetched endpoints where they could, and quoted licences.
Every candidate was then checked against the registry and against the enabled collectors. Nothing here
has been collected, and no permission capture has been taken yet.

**What "verified" means here.** The container, and in one study the device, could not reach most hosts
directly. Most checks went through a fetching tool that summarises pages. So:
- **FETCHED** means Belgrade data were seen in the response.
- Quoted terms are as that tool returned them. They must be captured byte-for-byte by
  `legal_capture` before any collection.
- robots.txt was read only where the tables below say so. Response headers (X-Robots-Tag,
  Content-Signal, TDM-Reservation) were **not** inspected anywhere.

---

## 1. Tier 1: new senses, clean terms, Belgrade data seen

| Proposed | Source | Endpoint | Class | What it adds | Terms (as read) | Checked |
|---|---|---|---|---|---|---|
| N1 | **Meteoalarm warnings, Serbia** (EUMETNET; issued by RHMZ) | `https://feeds.meteoalarm.org/api/v1/warnings/feeds-serbia` (JSON); `https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-serbia` (CAP/Atom) | LIVE | Official hazard warnings, with Belgrade as its own region **RS003**, in sr, sr-Latn and en. A new sense: what the state warned about, and when. | "terms equivalent to CC BY 4.0, with additional requirements for redistributing" (the additional requirements are **not yet read**). robots.txt: all rules commented out. | FETCHED (RS003 entries 2026-09-15) |
| N2 | **RHMZ UV-index forecast** | `https://www.hidmet.gov.rs/latin/prognoza/uv1.php` | LIVE (daily, 3 days ahead) | UV exposure for Beograd. A dataset separate from S01/S52. | Official material, Copyright Act Art. 6(2). hidmet robots.txt: `Disallow:` empty. | FETCHED (17–19.09: 5/5/4) |
| N3 | **RHMZ heat- and cold-wave warnings** | `https://www.meteoalarm.rs/latin/talasi.php` | LIVE (daily) | Heat-health alert for the Beograd region; complements N1. | Art. 6(2). robots.txt not checked on meteoalarm.rs. | FETCHED ("Nema upozorenja") |
| N4 | **BVK unplanned network faults** (same publisher as S11, new page) | `https://www.bvk.rs/kvarovi-na-mrezi/` | LIVE | Unplanned water outages by street and municipality, with repair time and tanker locations. S11's feed carries planned works. Together with EDS (S12/S54) this gives a failure picture for power and water. | BVK robots.txt disallows only `/wp-admin/`. The S11 feed answers `X-Robots-Tag: noindex, follow` (E-011): check this page's headers. | FETCHED (16.09 entry) |
| N5 | **GZZJZ Beograd weekly respiratory surveillance** (City Institute of Public Health) | index `https://www.zdravlje.org.rs/index.php/izvestaji/epidemioloska-situacija-bgd` | SEMI-STATIC (weekly, all year) | City-level acute respiratory infections and influenza-like illness, as counts and rates per 100k, with change on the previous week. A new sense: respiratory illness in the city, week by week. | Public health institution, so Art. 6(2) is plausible. **The "Opšti uslovi korišćenja" (general terms) page was not opened.** Joomla robots.txt does not disallow `/index.php/izvestaji/`. | FETCHED (week 36: ARI 5,730; ILI 159) |
| N6 | **RZS monthly tourist nights by municipality** (table 220205IND02) | `https://opendata.stat.gov.rs/data/WcfJsonRestService.Service1.svc/dataset/220205IND02/1/json` | SEMI-STATIC (monthly) | Visitor pressure for Grad Beograd (79014) and each municipality. July 2026: 365,932 nights, of which 321,633 foreign. A new route inside S148, which so far has only the portal and context tables. | RZS rights capture already on file (`CONTEXT_DATASETS.json`, review due 2026-12-12). robots.txt allows. | FETCHED |
| N7 | **RZS registered employment by municipality of residence** (24021308IND01) | same pattern | SEMI-STATIC (quarterly) | Labour baseline per Belgrade municipality (756 rows). | as N6 | FETCHED |
| N8 | **RZS building permits and dwellings in permits** (050204IND01, 050202IND01, 05020102IND01/02) | same pattern | SEMI-STATIC (monthly) | The construction pipeline. **Heavy:** a 46 MB zip that expands to 2.1 GB, so stream it and poll rarely. The Belgrade row was not isolated. | as N6 | FETCHED (not Belgrade-confirmed) |
| N9 | **DanubeHIS latest values** (ICPDR; data from RHMZ and upstream services) | `https://www.danubehis.org/latest-results/h` | LIVE (0.5–1 h) | Beograd (Sava), Zemun and Pančevo, plus Hungarian and Croatian gauges upstream: the basin view that gives lead time. | **CC BY-NC-SA 4.0.** ShareAlike obliges any derivative to carry the same licence. robots.txt: Crawl-delay 10, `/results` disallowed, `/latest-results` not disallowed. | FETCHED (Beograd 128 cm) |
| N10 | **Sensor.Community per-sensor archive** (new route; S04 is the live area filter) | `https://archive.sensor.community/YYYY-MM-DD/…_sensor_<id>.csv` | STATIC backfill + daily | History back to 2015 for the 47 sensor ids at 24 Belgrade locations. | ODbL (archive disclaimer). No robots.txt on the archive host. A User-Agent is required. Coordinates sit near volunteers' homes, so publish aggregates only. | FETCHED (1,440 rows for sensor 54945) |

## 2. Tier 2: strong baselines (static or yearly)

| Proposed | Source | Endpoint | What it adds | Terms |
|---|---|---|---|---|
| N11 | **EDGAR 2025 1 km emission grids + emissions by urban centre** (JRC) | `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/EDGAR_2025_1km/…`; `edgar_cities/EDGAR_GHG_AP_by_UCDB_2026.xlsx` | Modelled CO2, GHG, NOx and PM2.5 at 1 km, plus a per-city total. A pressure layer beside the measured air data. | CC BY 4.0 (`copyright.txt`). The IEA-EDGAR CO2 product is CC BY-NC-ND, so keep it apart. Belgrade coverage in the 1 km grid is **not yet confirmed**. |
| N12 | **RHMZ meteorological dataset 1998–2024** (Zenodo, 10.5281/zenodo.19239744) | `https://zenodo.org/records/19239744` | 27 years of daily data for the Beograd observatory, machine-readable, taken from the RHMZ yearbooks. | CC BY 4.0; underlying RHMZ reports are Art. 6(2). |
| N13 | **MeteoSerbia1km** (Sekulić et al. 2021, 10.5281/zenodo.4058167) | Zenodo record | Daily 1 km grids, 2000–2019 (Tmax, Tmin, Tmean, SLP, precipitation): a climate baseline for each municipality. | CC BY 4.0 (paper). |
| N14 | **WorldPop 2000–2020, 100 m** | `https://data.worldpop.org/GIS/Population/Global_2000_2020/{Y}/SRB/srb_ppp_{Y}.tif` | A third population grid to cross-check against GHSL (S94) and Kontur (S120), with 21 years. | CC BY 4.0 (`licence.txt`). |
| N15 | **Local Climate Zones, 100 m** (Demuzere et al., 10.5281/zenodo.6364594; take the latest version) | Zenodo record | Urban-climate classes for heat-island reasoning. The imperviousness layers do not give this. | CC BY 4.0. |
| N16 | **Global Solar Atlas point API** | `https://api.globalsolaratlas.info/data/lta?loc=44.8176,20.4569` | A second opinion to PVGIS (S116) on the long-term solar resource. | CC BY 4.0 (World Bank catalogue); API terms not read. FETCHED. |
| N17 | **E-OBS 0.1° grids** (KNMI/C3S) | `knmi-ecad-assets-prd.s3.amazonaws.com/ensembles/data/Grid_0.1deg_reg_ensemble/…` | A climate baseline built from observations, independent of ERA5 (S87). | **Non-commercial research only; no raw redistribution.** Derived numbers are allowed, with the citation. |
| N18 | **RZS vital statistics by territory** (180304IND03–10, 18030202IND01) | as N6 | Yearly denominators for any per-capita figure. | as N6. Territory level not fetched. |

## 3. Tier 3: useful, but each carries a condition

| Proposed | Source | Condition |
|---|---|---|
| N19 | **GloFAS forecasts** (CEMS, `ewds.climate.copernicus.eu`) | token_required: a free account and licence acceptance. Gives a forward flood forecast for the Sava/Danube at Belgrade. |
| N20 | **ENTSO-E Transparency, bidding zone Serbia** (load, generation by type, flows, day-ahead price) | token_required: free, granted by e-mail. Data "freely re-used", CC BY 4.0; 400 requests/min. National scale only. |
| N21 | **ENTSOG Transparency, Serbian entry points** (Horgoš ITP-10013 …) | Open API. Terms allow automated download, with a citation format. National scale only. FETCHED. |
| N22 | **IODA API, region "Grad Beograd" (id 3638)**, a new route for S45 | FETCHED: 288 five-minute values per day. **No licence or terms found**; ask IODA before collecting. |
| N23 | **Ookla open-data tiles** | CC BY-NC-SA 4.0 (ShareAlike). Quarterly; clip to Belgrade. |
| N24 | **EUROCONTROL airport traffic, LYBE** | "not used for commercial purposes … may not be modified without prior written permission": check whether derived counts are acceptable. The airport itself refused (S211). This is another publisher, but read §5 first. |
| N25 | **EDO drought indicators** (WMS) and **EFFIS fire danger** (WMS, CC BY 4.0) | Grids covering Belgrade. Reading a pixel value needs WCS or GeoTIFF, not the rendered WMS image. |
| N26 | **EEA air-quality download service** (Serbian stations RS0027A, RS0028A, RS0032A, RS0037A) | CC BY 4.0, POST-only API. Useful as an audit of SEPA (S06/S146). Whether E2a data actually arrive for RS is **unconfirmed**. |
| N27 | **Ministry of Trade maximum fuel prices** (RSS `must.gov.rs/rss/?change_lang=cr`) | Weekly. Site licence CC BY-NC-ND 3.0 RS, but the notices are official acts (Art. 6(2)) and the prices are facts. National. |
| N28 | **NSZ monthly bulletin** (Beogradska oblast, table T6) | PDF. "Preuzimanje sadržaja … dozvoljeno uz navođenje izvora" (taking content is allowed with the source cited). robots.txt not checked. |
| N29 | **RGZ real-estate market reports** (quarterly PDF) | Art. 6(2); robots.txt `Allow: /`. The record-level price register is paid and professional-only, so it is **rejected**. |
| N30 | **RGZ register of residential communities** (data.gov.rs, SODL, quarterly ODS) | 27,444 Belgrade entries: building-community names and addresses. Low personal-data risk. Quarterly differences show newly registered buildings. |
| N31 | **Infrastruktura železnice Srbije RSS** (`infrazs.rs/feed/`) | robots.txt `Allow: /`. **The site's sitemap lists unrelated retail product pages, so the site may be compromised.** Do not poll until checked. |
| N32 | **Danube FIS notices to skippers** (`danubeportal.com/noticesToSkippers`) | "Any commercial use … requires prior approval". HTML only. Belgrade reach roughly rkm 1160–1180 plus the Sava. |

## 4. A decision only Semir can make

**MUP traffic-accident open data** (data.gov.rs, dataset
`podatsi-o-saobratshajnim-nezgodama-po-politsijskim-upravama-i-opshtinama`, monthly XLSX, SODL).

- **Content.** One row per accident: police administration, municipality, time, coordinates, severity
  and type, back to 2015. FETCHED: 19,535 rows for Jan–Jul 2026, including Belgrade.
- **Value.** This is the single most valuable find of the day: a geolocated, monthly record of harm on
  the city's roads.
- **The conflict.** MUP is named refusal **S204**: its robots.txt names ClaudeBot with `Disallow: /`
  on mup.gov.rs. The third-party route rule (2026-09-10) says a refuser is "never named as a source of
  ours" and "never presented as having supplied us with anything".
- **Why the file is not a third party's utterance.** MUP itself published it, deliberately, as open
  data under a licence that permits reuse, on a different host that has no robots.txt.
- **Two honest readings:**
  1. *The refusal is of the website route.* The same body separately released this dataset for reuse
     under SODL, so taking it honours what MUP chose to publish.
  2. *The refusal is of MUP as a source.* Then this is exactly the door the rule keeps closed.
- **Recommendation.** Do not collect it until you decide. The frame already names the route: "A
  letter, not a workaround." A short letter to MUP asking whether the SODL release covers a research
  observatory would settle it and turn the question into evidence.

## 5. Rejected, with the reason recorded

- **Opt-out or restrictive terms:**
  - SmartCitizen API and Safecast: robots.txt blocks them.
  - Mobility Database catalogue and Open Charge Map API: robots.txt disallows them.
  - NoiseCapture raw data: robots.txt blocks it, and the data are phone GPS tracks.
  - PeeringDB: no bulk redistribution.
  - Blitzortung: data only for station operators.
  - SEEPEX: 60-day trial, then paid.
  - NBS web services: membership required.
  - RGZ price-register records: paid and professional-only.
  - AGROS GNSS: fee and account.
  - EOG VIIRS monthly night lights and Dynamic World: account required.
  - Observation.org and PEP725: account required.
  - Netatmo and Weather Underground: owner-only access, and their terms forbid redistribution.
- **Not Belgrade:**
  - Google Open Buildings: Serbia not covered.
  - Eurostat Urban Audit / city statistics: no RS cities.
  - EEA bathing water: Serbia not covered.
  - AirGradient: no Belgrade sensors.
  - Sensor.Community DNMS noise sensors: none in Serbia.
  - Belgrade EPN GNSS: none; the nearest is SABA, about 60 km away.
  - Neutron monitors: none in Serbia.
- **Duplicates of the registry:**
  - GHSL, Overture, Microsoft buildings, Kontur, WorldCover, Copernicus DEM, CORINE/HRL, PVGIS,
    Black Marble, NUTS, UNESCO, WSF.
  - CAMS, ERA5, Sentinel-5P, FIRMS, pollen, EMSC/USGS.
  - EURDEP/SRBATOM (S40); no new route found.
  - OpenSky (S36), RIPE Atlas (S37), Cloudflare Radar (S46), SMATSA (S55).
  - GTFS (S13): same two data.gov.rs feeds, SODL.
  - Beogradske elektrane works: already in the collected S175 feed.
  - GBIF (S41/S177).
- **Blocked by an existing refusal:** Sektor za vanredne situacije sits under mup.gov.rs (S204), so no
  route around it was sought.
- **Not reachable or not found:**
  - Real-time transit: no officially published GTFS-realtime or API. Reverse-engineered app backends
    were deliberately not looked for.
  - City budget execution: `/data` and `/content` are disallowed on beograd.rs.
  - City statistical yearbook, city environment secretariat noise/air reports, EMS AD (TSO) site,
    Plovput NTS portal, Srbijavoz timetable: nothing found or not reachable.
  - IPB cosmic-ray and radon stations: pages only, no licence. Write to IPB.

## 6. Corrections to existing entries noticed on the way

- **S41 / S177 GBIF.** The Belgrade box holds 528,060 records: 429,125 CC-BY, **97,778 CC-BY-NC**
  and 1,157 CC0. About 79 % come from one dataset, most likely eBird. Split the counts by licence and
  keep NC records out of any reuse.
- **S193 / S160.** opendata.geosrbija.rs announced its closure on 2025-08-01. The successor,
  download.geosrbija.rs, shows a login page. S150's unauthenticated export should be re-checked
  before it is relied on.
- **Zenodo discovery.** Zenodo's robots.txt blocks `/api` and `/search`. Discover records through the
  DataCite API (`api.datacite.org/dois?query=…`), then fetch `/records/<id>`.
- **data.gov.rs search.** It matches whole words and works better in Cyrillic. Enumerating by
  organisation is reliable; free-text search is not.

## 7. What would come next (not done)

1. Take a permission capture for N1–N7 and N9–N10 with `tools/legal_capture` from the observatory's
   own machine. That capture should save:
   - terms and robots.txt as bytes;
   - response headers, including X-Robots-Tag, Content-Signal and TDM-Reservation.
2. For those that pass, add registry rows and a parser each. Priority by new sense:
   - N1 warnings;
   - N4 water faults;
   - N5 respiratory surveillance;
   - N2 UV;
   - N6–N8 monthly municipal statistics.
3. Record ShareAlike obligations (N9, N23) in `RETENTION.json` / the licence notes before any derived
   layer is published.
4. Write the MUP letter if you choose reading 2 in §4, or decide reading 1 and record it in
   `DECISIONS.md`.
5. Send the IODA terms question and the IPB data question.
