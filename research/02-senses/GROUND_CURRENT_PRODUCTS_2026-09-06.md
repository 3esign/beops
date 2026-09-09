Status: current
Date: 2026-09-06
Author: Codex research lane, reviewed by coordinator

# Ground products: BEOG GNSS and Borča-dubok groundwater

Status: bounded documentation review complete; exact current BEOG product remains unconfirmed. Submitted for coordinator review.
Date: 2026-09-06. Author: Codex /root/emf. Language: English.

No raw time series were collected. No reporting-page request was made for Borča in this wave. No D: files, registry entries or earlier evidence were changed. Public metadata and documentation were inspected through primary web sources. Search-index observations are labelled separately from directly opened documents.

## 1. BEOG: a historical data citation does not yet resolve to a current product

The 2019 [BEOG/SRJV paper](https://www.geodetski-vestnik.com/63/4/gv63-4_tucikesic.pdf) establishes historical BEOG daily coordinates in IGS08, August 2014–March 2019. This wave followed the actual links from [NGL About](https://geodesy.unr.edu/about.php) and its [Plug and Play Portal](https://geodesy.unr.edu/PlugNPlayPortal.php), rather than constructing a series URL from memory.

| Official metadata route inspected | Result for BEOG | Evidence limit |
|---|---|---|
| [GlobalStationList](https://geodesy.unr.edu/NGLStationPages/GlobalStationList) | Web full-document find: no `BEOG` or `BEO` match. | Current catalogue response, not proof a receiver stopped. |
| [DataHoldings.txt — final daily solutions](https://geodesy.unr.edu/NGLStationPages/DataHoldings.txt) | No `BEOG` match. | Metadata, not coordinate samples. |
| [DataHoldingsRapid24hr.txt](https://geodesy.unr.edu/NGLStationPages/DataHoldingsRapid24hr.txt) | No `BEOG` match. | Does not establish a renamed station identity. |
| [DataHoldingsRapid5min.txt](https://geodesy.unr.edu/NGLStationPages/DataHoldingsRapid5min.txt) | No `BEOG` match. | No five-minute BEOG product established. |

As a positive control, `SRJV` was found in the global catalogue, final holdings and rapid-five-minute holdings, including a station-page link. Thus the BEOG negative finding is not based solely on a failed search of an unreadable list. Sarajevo remains outside this local Belgrade task; its data were not substituted for BEOG.

The Portal explicitly documents the station-page template `https://geodesy.unr.edu/NGLStationPages/stations/<ssss>.sta`, using an uppercase four-character station ID. One grounded request for [BEOG.sta](https://geodesy.unr.edu/NGLStationPages/stations/BEOG.sta) returned the web tool's non-retryable safe-open error. It was not retried. That tool result is **not an observed HTTP 404, denial of licence, or proof the station page does not exist**.

**Verdict:** no exact functioning current BEOG coordinate or troposphere endpoint, latest observation, receiver model, station operator or product-specific reuse licence was established. Do not mark this source live or construct a raw-series request from a filename pattern. Possible station renaming, removal, data-provider changes or publication error remain untested explanations.

## 2. NGL's current data contract, confirmed independently of BEOG availability

These facts describe NGL products generally; they do not supply missing BEOG coverage.

**Frame and freshness.** [NGL About](https://geodesy.unr.edu/about.php) states that current station-page solutions and plots use **IGS20**, while the final IGS14 products stop at **2024-08-24**. Its holdings metadata are updated daily and describe station coordinates, observation start/end, solution counts and original site names. Nominal daily-final latency is about two weeks; daily-rapid and five-minute-rapid latency is about 24 hours. These are processing classes, not guaranteed end-to-end latency for every station. The [2025 transition notice on the home page](https://geodesy.unr.edu/index.php) also explains that directories and station-page links changed during IGS20 reprocessing.

**URLs need current station links.** The [Portal](https://geodesy.unr.edu/PlugNPlayPortal.php) was last edited 22 April 2026 and says IGS20 in its prose, but several direct-access examples still contain IGS14 or older directory layouts. Therefore an example template alone is insufficient evidence for a current BEOG product. The portal permits machine-readable access using scripts and requests citation of Blewitt, Hammond and Kreemer (2018), DOI [10.1029/2018EO104623](https://doi.org/10.1029/2018EO104623); original data citations may also apply.

**Position fields and units.** The directly linked [tenv3 README](https://geodesy.unr.edu/gps_timeseries/README_tenv3.txt) describes station ID; calendar date; decimal year; modified Julian day; GPS week/day; reference-meridian longitude in degrees; east, north and vertical integer/fractional components in **metres**; assumed antenna height and component sigmas in metres; correlations; and nominal latitude/longitude/height. The fractional coordinate is not necessarily limited to 0–1. Large sigmas use the documented value `9.99999`; this is specific NGL documentation, not permission to generalize sentinel meanings to other sources.

**Time convention.** [NGL DecimalYearConvention](https://geodesy.unr.edu/NGLStationPages/DecimalYearConvention) specifies a 365.25-day year and integer decimal years at January 1, noon **GPS time**, in leap years. It links a conversion table; that table was not collected. Do not parse this as the calendar year's elapsed fraction, or silently label GPS time as UTC. No BEOG observation timestamp was recovered.

**Troposphere is an additional physical observation product.** The [official processing summary](https://geodesy.unr.edu/gps/ngl.acn.IGS20.txt) documents estimated five-minute zenith delay/gradients and integrated water vapour derived with auxiliary atmospheric modelling. The linked [troposphere README](https://geodesy.unr.edu/gps_timeseries/README_trop2.txt) describes yearly archives of daily SINEX products and warns that north/east gradient columns and corresponding errors are interchanged in affected formatting. It is dated 2020 and still contains older paths. A current file header would need to establish units, version and applicability; no archive was fetched and no BEOG troposphere availability was inferred.

## 3. NGL access and reuse: institutional grant found, exact BEOG scope unresolved

[NGL About](https://geodesy.unr.edu/about.php) identifies the lab as part of the Nevada Bureau of Mines and Geology at the University of Nevada, Reno. The [NBMG copyright page](https://nbmg.unr.edu/Copyright.html) states **CC BY 4.0**, asks for NBMG/UNR credit when using its products, and requires attention to accompanying copyright/disclaimer notices and suggested citations.

This is meaningful primary institutional reuse evidence. However, the page also refers to data “on this website”; no functioning BEOG station page or specific file notice was obtained to resolve its exact product scope or upstream data rights. The NGL citation request and public/script access should be recorded separately from the institutional CC grant. **Do not certify a particular BEOG dataset as CC BY 4.0 from this evidence alone.** EarthScope's separate data licence must not be transferred to BEOG without proving that provenance.

## 4. Borča-dubok 9NP163: separate pipe-top datum from water elevation

The current reporting capture belongs to the coordinator. Previously established 9NP163 reporting metadata identify **Borča-dubok, Pančevački rit**, zero elevation **73.79 m** and ground elevation **73.39 m**. The operator's English reporting search result labels these elevations relative to the **Adriatic Sea**. This wave did not open that reporting route again and did not assign its current observation year.

**Directly opened operator convention.** The [RHMZ Borča 9NP164 card](https://www.hidmet.gov.rs/latin/hidrologija/podzemne/stanica.php?pd_rb=5230) explicitly defines its relative levels as distances from the top of the pipe, the station zero, to groundwater. Its smallest depth corresponds to the highest water level. Thus larger positive centimetre readings indicate a deeper, lower water surface under that convention. The card has its own zero **72.52 m**, ground **72.20 m**, and depth **11.68 m**; none should be copied into station **163**.

[RHMZ hydrological definitions](https://www.hidmet.gov.rs/latin/hidrologija/pojmovi.php) separately define a piezometer as a groundwater borehole used to measure distance from a fixed construction point to water. The page's signed river-gauge `vodostaj` definition is a different convention; it should not overwrite piezometer depth semantics. Neither general definition proves the exact automatic probe make or pressure compensation method at 163.

**Additional station-specific evidence, indexed metadata only.** The operator's [2021 groundwater yearbook](https://www.hidmet.gov.rs/data/hidro_pod_godisnjaci/PODZEMNE%20VODE%202021.pdf) search-index station table explicitly lists Borča-dubok **163** with:

- coordinates **44°52′33″ N, 20°28′26″ E**;
- zero **73.79 m**, above-ground construction **0.40 m**;
- a **30.00 m** length/depth entry, foundation date **1994-01-01**, daily programme.

This supports identity and the 0.40 m zero-to-ground offset. The complete table header and explanatory pages were not opened in this wave. The 30.00 m entry appears to concern construction length, by comparison with the adjacent 164 entry, but that interpretation is provisional; do not assert screen depth, aquifer depth or current probe depth. The yearbook metadata labels the station rank differently from the reporting page; retain document year and source instead of silently harmonizing rank. The currently opened [Pančevački rit station table](https://www.hidmet.gov.rs/eng/hidrologija/podzemne/tabela.php?pd_pod_br=9np) lists only 164–166, so it does not provide an exact static card link for 163.

**Conditional conversion, not an official extra measurement.** If the coordinator confirms that reporting field `nivo` uses the documented pipe-top depth convention and that these datums still apply, then for a reported depth `d_cm`:

```text
water elevation in the published Adriatic datum = 73.79 - d_cm / 100  metres
depth below local ground                     = d_cm / 100 - 0.40 metres
```

For example, the coordinator's previously observed **488  cm** would imply **68.91 m** water elevation and **4.48 m** below ground. These are conditional derived values, not independently fetched observations. A formal vertical reference realization/EPSG identifier, current datum history and exact reporting-field contract remain unconfirmed; do not label this a WGS84 ellipsoidal altitude.

## 5. Small next requests for coordinator review

No raw BEOG series request is justified yet. The smallest useful next resource is the already documented **BEOG station metadata page**, subject to the coordinator's exact-route and access review, or a frozen capture of the official holdings metadata sufficient to resolve a renamed identifier. Do not probe alternative prefixes or historical series directories without a grounded link.

For Borča, the existing reporting-page capture plus its embedded labels may settle the `nivo` field and date context without another network request. If not, inspect only the **2021 yearbook station-table header and explanatory pages** under the coordinator's document review. Its exact URL is listed above. This would test the datum/rank/depth interpretation; it does not authorize collecting annual measurement tables. No unreviewed raw request, new collection schedule or institution contact is proposed.

## Search and verification record

Primary navigation: NGL About → station catalogue/three holdings lists/Portal → format and time-convention documentation; RHMZ 164 card → groundwater network and hydrological definitions. Searches included `site.geodesy.unr.edu BEOG station`, exact `BEOG` + NGL domain, NGL data licence, `site.hidmet.gov.rs "9NP163"`, Latin `Borča-dubok` and Cyrillic `Борча-дубок` plus datum. Search hits from secondary legal mirrors and unrelated GNSS licences were not treated as primary product grants.

The main new result is a documented negative current-product check for BEOG plus a safer groundwater measurement interpretation. It narrows the gap without presenting a historical study, generic processing promise or derived depth conversion as a verified live signal.

## Coordinator receipt update

The subsequent saved S192 response and independent static QA resolve the latest chart label to2026-09-06; the latest ten full dates match the visible table. Earlier uncertainty above describes the preceding documentation-only review. Exact measurement time,163 field contract and conditional depth conversion remain unresolved. See[current product synthesis](CURRENT_PRODUCTS_2026-09-06.md) and[static QA](../_trail/BORCA_QA_REVIEW_2026-09-06.json).
