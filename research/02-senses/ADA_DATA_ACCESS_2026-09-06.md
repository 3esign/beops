Status: bounded metadata review complete; no public raw file candidate verified
Reviewed: 2026-09-06
Scope: eight Ada Marina records from the captured WeBaSOOP catalogue; no raw data requested

# Ada Marina: exact data availability

This review separates dataset declarations, repository file access and evidence from research papers. The original catalogue establishes nine local DOI links. The DTT record was already reviewed and remains excluded from new requests; its declared CC BY 4.0 licence coexists with restricted files. Bor is a different site and is excluded.

All eight exact DataCite singleton responses were received with HTTP 200 and declare **CC BY 4.0 for their referenced datasets**. Seven NILU file-access states remain unknown. The captured AA Zenodo landing shows **public metadata and restricted files**. Consequently, this wave identifies no demonstrably accessible small raw file. This is not a finding that no public files exist. Machine-readable details and individual receipt hashes are in [ADA_DATA_ACCESS.json](../_trail/ADA_DATA_ACCESS_2026-09-06.json).

DataCite's separate [CC0 metadata declaration](https://support.datacite.org/docs/harvesting-datacite-doi-metadata) applies to DOI metadata, not to the underlying observations. It is distinct from each record's dataset-specific [CC BY 4.0 declaration](https://creativecommons.org/licenses/by/4.0/legalcode). These declarations resolve the earlier unknown licence field for the eight exact records; they do not clear generic provider websites, recurring extraction or inaccessible files.

## Exact registered products and dates

Titles below are the registered DataCite titles. NILU links are exact `attributes.url` destinations, obtained from metadata; their landing pages were not retrieved in this wave. A `Collected` range is a registered coverage statement, not verification of individual samples or gap-free observations. The seven NILU ranges have date precision and do not establish a timezone. The creation/availability dates describe these dataset versions, not live measurement freshness.

| Catalogue label | Exact title and registered destination | Version | Collected range | Created / Available |
| --- | --- | --- | --- | --- |
| OC / EC | [Measurement of OC/EC at Beograd Ada Marina](https://doi.nilu.no/doi/J32C-ZYJW) | 3 | 2023-05-30 / 2024-12-12 | 2026-01-12 |
| OP (AA) | [WeBaSOOP_Oxidative_Potential_Ascorbic_acid_assay_Ada_Marina_station_Belgrade](https://zenodo.org/records/18254835) | Landing displays v2; index 2 | Description starts 2023-05-31 22:00 UTC; period code 1 year; exact end unknown | Issued 2026-01-15 |
| Water-Soluble Ions | [Measurement of Inorganics in air and particle phase at Beograd Ada Marina](https://doi.nilu.no/doi/5JNE-638V) | 4 | 2023-05-30 / 2024-05-31 | 2026-01-12 |
| Metals & Elements | [Measurement of Heavy metals and inorganics in air and particle phase at Beograd Ada Marina](https://doi.nilu.no/doi/8TQV-HXDA) | 4 | 2023-05-30 / 2024-05-31 | 2026-01-12 |
| Organic Tracers | [Measurement of Organic tracers at Beograd Ada Marina](https://doi.nilu.no/doi/AJ4A-EZ64) | 3 | 2023-06-05 / 2024-05-28 | 2026-01-14 |
| PNSD | [Measurement of Particle_number_size_distribution at Beograd Ada Marina](https://doi.nilu.no/doi/CQF2-YGGJ) | 3 | 2024-02-14 / 2024-07-28 | 2026-01-12 |
| eBC | [Measurement of Aerosol_absorption_coefficient at Beograd Ada Marina](https://doi.nilu.no/doi/DKPQ-W9KT) | 4 | 2023-10-20 / 2025-02-11 | 2026-01-19 |
| TCA | [Measurement of Total_carbon at Beograd Ada Marina](https://doi.nilu.no/doi/3YA2-Z4PX) | 3 | 2023-10-24 / 2024-07-25 **and** 2024-09-20 / 2025-06-19 | 2026-02-09 |

All seven NILU records locate the resource at **Beograd Ada Marina, 44.790286 N, 20.417187 E**. The AA public description gives the same point and 71 m altitude. Preserve the slightly different coordinates printed in the chemical paper as separate evidence rather than silently replacing either value.

The registered eBC destination describes **aerosol absorption coefficient**. Equivalent black-carbon mass, its units and conversion parameters are not verified file variables. Likewise, catalogue shorthand such as Water-Soluble Ions is narrower than the registered title. Seven NILU abstracts repeat only their measurement group: they provide no exact analyte/channel inventory, instrument model, acquisition cadence or file size. All seven advertise `application/x-netcdf`; this is a metadata format declaration, not a received or inspected NetCDF file. Record-linked instrument identification for those seven remains unknown; the paper crosswalk below supplies explicitly qualified campaign context.

## AA version, measurement chain and restricted files

Catalogue concept DOI **10.5281/zenodo.18232817** lists two versions in DataCite: `18232818` and `18254835`. The captured concept landing resolves to **10.5281/zenodo.18254835**, displayed **v2**, index 2, marked latest at retrieval. Do not report the first listed version as the observed latest version.

The public version description reports **PM10 oxidative potential by ascorbic acid assay**, in **nmol/min/m3**. It specifies **Leckel LVS3** sampling, **BioTek/Agilent Synergy H1 Microplate reader** analysis by UV absorption, and the Vinča laboratory. Its resolution code is **4 days**, with **24-hour samples**. The description reports an EBAS-template `.txt` upload but the file itself was not inspected. An exact final timestamp cannot be calculated safely from the period code alone. Its acknowledgement asks for the DOI and WeBaSOOP project credit; no contact details are reproduced here.

The captured `access` object says record `public`, files `restricted`, overall `restricted`, embargo active `false`. The metadata has no exposed file inventory or verified size. Neither download-statistics volume nor `files.enabled: true` establishes a small accessible file. The version's CC BY 4.0 declaration remains recorded while file collection stays on hold. [Observed AA version](https://zenodo.org/records/18254835).

## Paper-to-data crosswalk, kept separate from repository metadata

The [EGUsphere preprint](https://egusphere.copernicus.org/preprints/2026/egusphere-2026-2112/) links the OC/EC, ions, metals and organic-tracer DOIs. Its [methods PDF](https://egusphere.copernicus.org/preprints/2026/egusphere-2026-2112/egusphere-2026-2112.pdf), pp. 3–4, describes Ada Marina at 44.790166 N, 20.4169 E, 71 m and a study subset spanning 6 June 2023–28 May 2024. PM10 sampling used co-located Leckel LVS3 units. Analyses used Sunset OC/EC with EUSAAR-2, Dionex ICS-1600 ion chromatography, Agilent 7700 ICP-MS, and Vanquish UHPLC/Q Exactive Plus Orbitrap. These methods identify physical measurement chains; the study interval does not establish every exported DOI's interval. Its April 2026 receipt and May 2026 discussion publication concern the preprint, not observation freshness. The article's CC BY declaration is not transferred to the external datasets.

The [Environments paper](https://www.mdpi.com/2076-3298/13/1/47), published 12 January 2026, links PNSD DOI CQF2-YGGJ and describes a February–August 2024 study. Methods identify MPSS 3938 at 90-second intervals, AE-33 eBC at five minutes, and TCA08 total carbon at 30 minutes; analysed PNSD spans 10–400 nm. These acquisition cadences do not establish repository update cadence. The paper asserts open PNSD availability; current file access remains unverified. It does not explicitly link the eBC or TCA catalogue DOIs, so those devices remain study context. PMF source estimates are model outputs. The DOI's narrower registered interval is preserved separately; the difference is unresolved. Neither source proves a current stream.

## Operational legal sorting

Resource-specific rights declarations must be preserved with their exact DOI/version. Operational categories are **explicit resource-linked licence declaration, file access unresolved** for the seven NILU datasets, and **explicit resource-linked licence declaration, files restricted** for the observed AA version. DataCite metadata has its own CC0 basis. A CC BY declaration does not supply credentials or establish public files. Missing metadata fields are unknown, not evidence of absent rights or absent files. Retain attribution, DOI/version, retrieval date and transformations when relying on the dataset grant.

E-003 remains the project's bounded local evidence practice, not a publisher grant or a conclusion about Serbian law. E-004 still requires an exact question, minimal fields, cadence, horizon and shared request/byte budget before repeated extraction. This review provides no authority for recurring collection or raw redistribution. S190's 403 hold and S175's opt-out remain in force. No login, access request, raw data request or institutional message was attempted.

## Search and reading log

1. Read the committed WeBaSOOP DOI map, dataset note and existing legal follow-up locally. Reused the captured catalogue instead of requesting it again.
2. Attempted the eight exact DOI URLs and the AA Zenodo landing with the web tool. No usable record content or HTTP status was returned.
3. Read the documented [DataCite single-DOI route](https://support.datacite.org/docs/api-get-doi). A web-tool attempt for the exact OC/EC route also failed. Prepared the eight singleton URLs for the coordinator's bounded metadata capture; no independent collector was run.
4. Read primary EGUsphere landing/PDF and indexed primary Environments methods/data-availability text. Distinct paper publication dates, historical measurements and repository assertions are retained.
5. The held S190 preprint surfaced incidentally in a broad search. It was not opened or used for new claims. Subsequent instrument searches were restricted to MDPI domains.
6. Independently inspected the coordinator's eight saved HTTP-200 DataCite bodies and captured AA embedded record JSON. No further requests followed their delivery. Checked titles, version relations, dates, points, rights, access flags and format/size-field limits.

## Evidence receipts and remaining boundary

The corresponding exact request plan is [ADA_DATACITE_PLAN.json](../_trail/CURRENT_PRODUCTS_DATACITE_PLAN_2026-09-06.json). Initial direct DOI and AA web opens failed without usable server status; the coordinator's later responses establish successful metadata access through the documented routes. Tool errors are not recast as server denials.

- Eight singleton bodies: `research/evidence/S191/20260906T123813Z/`; individual HTTP status, byte count, SHA-256 and URL are preserved in its `MANIFEST.json` and the companion review JSON. Each is below the authorized 128 KiB cap. Batch timestamp: 2026-09-06 12:38:13 UTC.
- DataCite metadata policy: `research/evidence/legal/S191/20260906T123714Z/terms_1.html`; captured 12:37:20 UTC; SHA-256 `3066a3388cf5c9e3512b421d1a82a2fcc80c8389cf1f349cfe4325b01b1b295a`.
- AA concept landing / resolved version: `research/evidence/legal/S191/20260906T123714Z/terms_2.html`; captured 12:37:22 UTC; 95,843 bytes; SHA-256 `4f75c8db3a4a06d0cc85ac35891d3c3d78486e9f7f5b4740c97232d3f75d9e61`.
- Existing catalogue and DTT evidence are reused from the committed `WEBASOOP_DOI_MAP.json`; neither resource was re-collected by this lane.

The strongest next access question concerns an exact NILU landing and its exposed file inventory, rather than another paper or a guessed download route. This bounded wave stops before that step. **No small raw candidate, file checksum, live update cadence, delivery latency or latest individual sample has been verified.**
