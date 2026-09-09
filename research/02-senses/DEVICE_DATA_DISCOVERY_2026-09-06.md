Status: current
Date: 2026-09-06
Author: Codex coordinator, with procurement, hydromet and EMF scouts

# Devices behind Belgrade's data — continued discovery

This wave follows the user's request to keep finding devices and data. It adds six source records (S184–S189) to the 180-record baseline and deepens S59, S155, S158 and S175. A record can describe an archive, catalogue, operator statement or a confirmed coverage gap; **186 records does not mean 186 sensors or live feeds**.

The user's subsequent steering preserves the project's existing legal sorting. [The legal matrix for this wave](../07-legal/DEVICE_DATA_LEGAL_SORT_2026-09-06.md) applies that frame; a successful request or a crawl-signal check does not grant storage, repeated extraction or republication rights. Raw material whose reuse remains unresolved is retained as local review evidence and is not approved for public redistribution.

## What is now concrete

| Device or dataset | Evidence obtained | Availability and limits |
|---|---|---|
| RATEL Science and Technology Park fixed EMF monitor, S158 | A complete single response contains **457,698 measurement rows**, spanning **2018-02-27 to 2026-01-24**. Historic instrument evidence identifies Narda AMS 8061. | Real historical data, not current conditions. Header says both passive in the location name and active in another field. Timezone, contradictory state and unusually large repeated values need resolution. |
| RATEL Belgrade mobile EMF campaign, S158 | Independently recounted **7,780 measurement rows** on **2024-11-08**, with coordinates and timestamps. Already saved under the wrong S155 association. | Historical route coverage. No timezone in the payload. Four reported zeros retained. Source association corrected by an append-only record, not by changing old evidence. |
| Vinča stack CEMS, S184 | Operator's page downloaded and parsed: **nine daily parameters for 2026-09-05**, plus weekly tables and historical example-report links. | Current dated public results on this retrieval. Stack emissions are distinct from ambient air. Reuse licence is not established; this is not an independent compliance assessment. |
| Institute of Physics Belgrade Raman lidar, S186 | Official catalogue plus primary instrument paper; the credential-free ACTRIS API returned **BGD / RS** in both a 54-station list and a one-station Serbia-filtered response. | Local device and metadata route confirmed. Actual optical profile retrieval remains unresolved: the attempted August 2026 metadata query returned HTTP 404. |
| Plovput survey boat sonar and ADCP, S187 | Operator reports delivered SV25 equipment in May 2025 and **34 surveyed profiles at Boljevci and Ostruznica** in December 2025. Both pages stored and the local-profile statement checked. | Operator-held survey data. Public raw profiles not found. The two notices do not establish that this particular boat made those profiles. |
| Košutnjak radiosondes, S188 | RHMZ describes local balloon profiles, at least twice daily, distinct from S02 surface observations. Operator page stored. | Public description/diagram route; no numerical sounding obtained or current hardware model verified. |
| Adaptive intersection detectors, S189 | Traffic Secretariat's 2013 notice documents an implemented adaptive intersection; source page stored. | Historical deployment evidence. Current operation and a public detector feed not established. |
| Heat and water instruments, S175 | Ultrasonic building heat-meter description on the correct utility host, plus BVK's historical flow/pressure/level instrumentation account. | No public utility telemetry obtained. Purchase plans stay separate from installation evidence; building/account-level consumption is outside this wave. |

Primary sources: [RATEL fixed endpoint](https://emf.ratel.rs/getOpenData/21/json), [RATEL mobile endpoint](https://emf.ratel.rs/drive-test-open-data/open-data-2-2.json), [BCE monitoring](https://www.bcenergy.rs/emissions/), [EARLINET station list](https://earlinet.eu/earlinet-map/), [ACTRIS station metadata](https://api.actris-ares.eu/api/services/restapi/stations/?countryCode=RS), [Plovput delivered equipment](https://www.plovput.gov.rs/vesti/1/1537), [Plovput local profiles](https://www.plovput.gov.rs/vesti/1/1580), [RHMZ aerology](https://hidmet.gov.rs/eng/meteorologija/aero_eng.php). Historical detector and utility references are in the procurement lane below.

## The richest new response also exposes data-quality problems

The fixed EMF route returns an entire archive, **225,410,096 bytes**, rather than a small current sample. It was fetched once after an exact-route permission capture. A lossless gzip copy is **9,454,026 bytes**; decompression reproduces SHA-256 `e3ecaba71a8a860c5c490e7d12569da35d3578497c62b9a93994c9766f42a20e`. The original remains unchanged locally; the compressed copy is the portable repository artifact.

The audit finds **449,902 unique timestamps**, **7,796 additional repeated-time rows** and **496 gaps longer than six minutes**. The largest gap runs from 2024-09-30 to 2025-04-19. Of the repeated-time rows, 727 differ from the first payload at that time after excluding the row-number field. None were removed. Six bands contain the conspicuous value `99999.99`; its meaning is not declared in the inspected payload. Do not interpret it as a field-strength maximum or silently replace it with null.

These checks describe the archive and the publishing instrument. They do not establish changes in the city's exposure. The exact audit method and counts are in [FIXED21_QA.json](../evidence/device-discovery-20260906/FIXED21_QA.json), with the [offline audit script](../audit_fixed21_20260906.py).

## Corrections and negative findings that prevent wasted work

1. **Existing data had the wrong source association.** The mobile EMF JSON under S155 was gated on a NetTest-host capture. Today's S158 exact-route capture does not retroactively validate that earlier collection. The original file and manifest stay intact; [CORRECTIONS.md](../08-provenance/CORRECTIONS.md) records the mismatch and canonical alias. The S155 files labelled JSON/CSV/XML were actually HTML responses; no speed measurements were established from them.
2. **A current page is not a cached search result.** Scout web extraction of BCE showed 2026-08-18; independent web opening and the stored direct HTTP response showed 2026-09-05. The direct capture settles only this retrieval. It does not prove the reason for the different representations.
3. **Listed fixed sites are not active devices.** RATEL's inspected list mixes active/passive sites; an older portal catalogue and the current page differ in site count. No live-device total is claimed.
4. **AERONET local coverage was tested spatially.** The captured all-site catalogue has **1,672 rows** and **zero stations** in the explicit rectangle west/south/east/north **20.0, 44.4, 20.8, 45.1**. S185 records this bounded coverage gap. This is not a Serbia-boundary test or proof that no unregistered photometer exists.
5. **An API root 404 is not API absence.** ACTRIS's documented WADL and station routes work. The lower-case station lookup returned 404, whereas the catalogue declares uppercase `BGD`. The optical-product query failure is retained without turning it into a claim of no historical lidar data.
6. **Radio licences describe permissions.** S59 cannot be interpreted as a verified inventory of installed, sensing or currently operating devices. The heat utility's relevant host is `beoelektrane.co.rs`; a capture of a similar hostname would not cover it.

## Next useful investigations

- Resolve the fixed EMF header contradiction, repeated timestamps and `99999.99` from RATEL's data dictionary or publisher documentation. Then compare periods without inventing timezone or deleting reported values. Do not poll the full-history route repeatedly.
- Follow one ACTRIS BGD product through documented metadata to a NetCDF file with its measurement interval, quality level and licence. The station catalogue is now established; repeating global discovery has little value.
- Inspect Plovput's [new bulletin](https://bilten.plovput.rs/) after its own provenance capture: distinguish RHMZ inputs, calculated bridge clearance, forecasts and aggregate AIS counts. Keep individual-vessel records out of scope. Raw anchorage profiles remain a separate access question.
- Search completed awards/commissioning records behind heat and traffic procurement leads. A tender proves intent, and its device quantity must not become an installed count.

A historical [BEOG GNSS study](https://www.geodetski-vestnik.com/en/clanek/10.15292/geodetski-vestnik.2019.04.525-540) supports a further slow-ground-motion lead. A current station/data service was not established, so it was not added as a verified feed. WMO/WIS2, ICOS and SensorThings search branches remain unresolved, not coverage absences.

## Evidence and teamwork

- [EMF lane](DEVICE_EMF_2026-09-06.md): source/file identity, measured coverage, historic instrument evidence and fixed-archive audit.
- [Hydromet lane](DEVICE_HYDROMET_2026-09-06.md): lidar, sonar/ADCP, radiosondes and derived navigation products.
- [Procurement lane](DEVICE_PROCUREMENT_2026-09-06.md): CEMS, traffic, heat and water devices, with installation dates separated from procurement plans.
- [Native-agent board](../_trail/DEVICE_DISCOVERY_BOARD_2026-09-06.md), [one-shot collection plan](../_trail/DEVICE_COLLECTION_PLAN_2026-09-06.json), [compression proof](../evidence/device-discovery-20260906/COMPRESSION.json), [BCE table](../evidence/device-discovery-20260906/BCE_DAILY_QA.json), [AERONET spatial check](../evidence/device-discovery-20260906/AERONET_COVERAGE.json), [independent mobile recount](../evidence/device-discovery-20260906/DRIVE_BG_QA.json).

Agents owned disjoint reports; coordinator independently checked local counts/hashes, ACTRIS responses, BCE date/table and Plovput's local-profile statement. Primary dates, exact URLs, captured permission evidence and retrieval manifests are retained. Public readability and a permissive robots result are not blanket redistribution licences.

## Honest verdict

Verified: the stored pages and metadata, two concrete EMF archives, the BCE daily table, the source-association problem, and bounded device evidence described above. Offline suite: **44/44 passed**. The [integration receipt](../evidence/device-discovery-20260906/INTEGRATION_QA.json) verifies 186 unique records, eight legal reviews in five groups, 24 new manifests, 76 payload hashes/lengths, 11 collected routes matched to prior exact-route captures and 262 local links at that check. Independent review found no change in access-verdict logic and no missing legal-review links.

Not established: exhaustive sensor coverage, current uptime of historical instruments, a continuous collector, public raw Plovput profiles, BGD optical profile contents, or reuse permission for every public document. No institution was contacted, UI changed, scheduler created, or deployment performed. The project-kit helper named by CONTRIBUTING is absent from Svemir; that gate cannot truthfully be reported as passed.
