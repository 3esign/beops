Status: current
Date: 2026-09-06
Author: Codex coordinator, with EMF, hydromet and procurement scouts

# Devices and data: recent EMF, actual lidar products and Ada Marina datasets

This bounded continuation adds S190–S191 and deepens S158, S186 and S187: **188 source records**, not a count of devices or open feeds. The [previous discovery](DEVICE_DATA_DISCOVERY_2026-09-06.md) remains the record of the first wave. The [follow-up legal review](../07-legal/DEVICE_FOLLOWUP_LEGAL_2026-09-06.md) keeps access, licence, product scope and publication separate.

| Source | New verified finding | Exact limit |
|---|---|---|
| **S158, RATEL Science Park** | The saved operator page for record 168 embeds **1,681 electric-field values**, from **2026-08-30 00:00 to 2026-09-06 00:00**, with 1,680 six-minute intervals. Latest published value **2.12 V/m**; range 1.89–5.51 V/m. | No timezone is supplied. These are published chart values, not an independent instrument inspection or a health assessment. The historical selective archive parameter 21 and this broadband page record 168 must remain distinct. |
| **S186, ACTRIS BGD lidar** | The correct documented route returned **39 optical-product metadata records: 34 Level 2 and 5 Level 1**. Selected product **101626** is BARLI 355 nm backscatter, **2020-05-07 18:27:22–20:26:47 UTC**, version 3/QC4. | Metadata, not downloaded NetCDF profiles. Product metadata falls in an explicit CC BY 4.0 policy category; the raw legacy-product grant remains unresolved. |
| **S190, Ada Marina instrument study** | A June 2026 author preprint reports a supersite operating since June 2023, with TSI 3082/3775/3330 particle instrumentation and a Magee AE33 aethalometer. | Unreviewed author-reported deployment, not current uptime. The identified direct preprint request returned 403; no article download or bypass. Article licence does not establish access to underlying measurements. |
| **S191, WeBaSOOP catalogue** | The stored original catalogue maps **nine Ada Marina dataset families** to DOIs, with six Bor links kept separate. One exact Ada Marina DTT record declares **CC BY 4.0**, public metadata and **restricted files**. | A licence and a public DOI do not make the files anonymously downloadable. Captured metadata reports no active embargo, but files remain restricted. No raw dataset or login was attempted. |
| **S187, Plovput bulletin** | The operator's terms explicitly reserve rights in content and databases while permitting free portal service use. The bulletin homepage responds successfully. | Terms name a legacy portal domain; exact scope remains a question. Automated bulletin-record collection is held. No bridge-clearance, bathymetry or vessel records were collected. |

Primary references: [RATEL record 168](https://emf.ratel.rs/results/details/lat/168/gps:44.80362688,20.50281154/params:1100111), [ACTRIS product metadata](https://api.actris-ares.eu/api/services/restapi/products/metadata/optical_products?stations=BGD&fromDate=2020-05-01&toDate=2020-05-31), [Ada Marina preprint](https://www.preprints.org/manuscript/202606.0263), [WeBaSOOP original catalogue](https://webasoop.org/index.php/open-data/), [Ada Marina DTT record](https://zenodo.org/records/18255335), [Plovput terms](https://plovput.gov.rs/pravila-koriscenja).

## What the recent EMF page changes

The original page response is 1,194,691 bytes. Its inline Chart.js literals contain the recent series, so the request planned as metadata also received measurement data. Static parsing executed no JavaScript or additional request. All main field values align with unique timestamps; no nulls or zeros were found. GER curves and reference/uncertainty curves are separately published quantities, not additional independent measurements. `Limit polja` has no data property; absence is preserved.

The same address appears in archive 21 and page 168, but coordinates and methods differ. No replacement, relocation, common identifier namespace or continuous join is established. Manufacturer documentation helps identify internal auxiliary sensors and configurable cadence; it does not decode RATEL's `99999.99`, duplicate precedence or timestamp timezone. Those remain unresolved in the original archive.

The actual page button documents a date-range HTML route with `dd.mm.yyyy.` inputs and a maximum displayed range of 240 days. A one-day candidate is recorded in the [EMF follow-up](DEVICE_FOLLOWUP_EMF_2026-09-06.md). It was not requested. Two export-handler strings lack matching controls in the captured page and are only code leads. No new JSON export or continuous collector is claimed.

## Lidar products now have individual identities

The previous optical query failed because its route did not match the stored WADL. The successful route is `products/metadata/optical_products` with explicit station and month filters. The 39 objects span 4–24 May 2020 within this response; they do not establish the full archive's bounds.

Product 101626 has a [persistent identifier](https://hdl.handle.net/20.500.12911/1.1H17K0JOYT7MPZ32), an advertised size of 41,374 bytes and all 14 reported checks marked executed/passed. These are publisher metadata, not independently verified file contents. Its checksum algorithm is not named in the response. The general campaign metadata route for dataset 516 exceeded the declared **2 MiB cap**; its body was not saved or retried. Dataset IDs and optical-product IDs remain distinct. See the [product review](ACTRIS_PRODUCT_2026-09-06.md).

## Ada Marina: instrument and data provenance stay separate

The preprint was posted 3 June 2026 and labels itself unreviewed. It reports a modelling subset covering October 2023–August 2024 and says relevant project links become active after an embargo. That statement is not a current access verdict for every dataset in the project's catalogue.

The original WeBaSOOP catalogue now supplies Ada Marina links for OC/EC, DTT and AA oxidative potential, water-soluble ions, metals/elements, organic tracers, particle number size distribution, equivalent black carbon and total carbonaceous aerosol. The linked DTT concept DOI **10.5281/zenodo.18255335** resolves to a captured record identifying version DOI **10.5281/zenodo.18255336**, v1, published 15 January 2026. Its metadata describes Leckel LVS3 sampling and PerkinElmer Lambda35 analysis. No current device operation or numerical values are inferred from that description.

The record has restricted files despite a CC BY 4.0 licence and `embargo.active=false`. Exact file size remains unknown: the displayed 36.6 kB is cumulative download statistics, not a file-size declaration. The [catalogue and dataset review](WEBASOOP_DATA_2026-09-06.md) preserves all nine local DOI mappings. Neither Bor data nor a separately discovered software DOI substitutes for Ada Marina measurements.

## Evidence, checks and remaining work

The follow-up board (private working record) records the request budget, integration checks and worker release. Original receipts and failed responses remain immutable. The recent-chart QA (private working record), lidar metadata QA (private working record) and DOI map (private working record) retain exact inputs and distinctions. The [Plovput review](PLOVPUT_BULLETIN_2026-09-06.md) explains its collection hold.

Next work can use the retained EMF series and open product metadata. Further raw access depends on the exact RATEL chart-use scope, a linked licence for the legacy lidar product, or authorized access to restricted aerosol files. No authentication was attempted, institution contacted, scheduler created or public dataset released. This wave does not resolve every legal or scientific question in the earlier framework. Final checks and unavailable project-kit gate are recorded in the board/log.
