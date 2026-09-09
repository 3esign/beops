Status: historical
Date: 2026-09-06
Author: hydro scout (native Codex sub-agent)

# Belgrade hydrometeorological devices and data: primary-source discovery

Accepted discovery snapshot. The [integrated report](DEVICE_DATA_DISCOVERY_2026-09-06.md) incorporates later captures and is current for this wave.

Scope: four findings from a bounded discovery pass, for coordinator review. Existing RHMZ, SEPA, Sava and ICPDR entries were checked for duplication. No source IDs allocated, central files edited, collectors run, institutions contacted, or dataset downloads performed. Primary web pages and publication text were inspected; these are discovery notes, not stored permission captures. Registry integration and any collection require the coordinator's provenance workflow.

Proof labels used here: **operator statement** means a responsible institution explicitly reports the device/activity; **published instrument study** means researchers describe their equipment and measurements; **catalogue** proves a listed station; **data route** proves a documented route, not local records received. None means that this pass independently observed hardware operating today.

## 1. Institute of Physics Belgrade Raman lidar: a local vertical aerosol instrument

**Disposition:** strong new device candidate; local deployment supported, current data availability unresolved. Not a duplicate of surface PM stations or the coordinator's AERONET investigation.

- **Holder/location:** Institute of Physics Belgrade, Pregrevica 118. The [official EARLINET station list](https://earlinet.eu/earlinet-map/) includes BGD, Belgrade, Serbia at 44.8557 N, 20.3913 E, altitude 89 m. The table does not expose a row-specific operational status in the extracted text. The [GALION search catalogue](https://galion.world/search/) search result labels Belgrade operational at those coordinates, but direct opening failed; treat that weaker status evidence separately.
- **Installed instrument evidence:** the [2023 instrument paper, pp. 163–175](https://www.ta3.sk/caosp/Eedition/FullTexts/vol53no3/pp163-175.pdf), accepted 2023-11-02 and successfully opened, describes a bi-axial Raman lidar at IPB, with a 355 nm Nd:YAG transmitter, elastic 355 nm and nitrogen Raman 387 nm reception, Hamamatsu R9880U-110 photomultipliers and a Licel transient recorder. Its reported raw vertical sampling is 7.5 m and profile averaging about one minute. These are paper-era characteristics, not a verified present-day service interval. The paper calls BGD a joining EARLINET station and uses rounded coordinates 44.860 N, 20.390 E; preserve both coordinate provenances instead of silently merging them.
- **What it can establish:** height-resolved aerosol optical properties and boundary-layer evolution. A vertical optical measurement should not be represented as a citywide surface PM concentration.

**Data route and important migration:** the [EARLINET access page](https://earlinet.eu/our-knowledge/access-to-data/), displaying last update **2025-10-23**, explicitly points to a credential-free [ACTRIS ARES viewer](https://data.actris-ares.eu/) and [REST API documentation](https://api.actris-ares.eu/api/swagger-ui/). The API documentation page was opened but yielded no extracted body. The access page documents CF-compliant NetCDF optical profiles, quality levels and annual station datasets. This establishes a promising route; it does **not** prove BGD files are present, their date range, licence, latest observation time or update latency. Those remain untested. Dataset times must come from the files, not this visit.

The [EARLINET homepage](https://earlinet.eu/) explains that operational measurements moved into ACTRIS while EARLINET remains a science/expertise network. Its old database link reaches a [JavaScript-only legacy login path](https://data.earlinet.org/earlinet/login.zul), and its old [quicklook site](https://quicklooks.earlinet.org/) reports maintenance. The access page supplies newer routes, including [new quicklooks](https://quicklooks.actris-ares.eu/). The legacy URL is not evidence that the new API requires registration. Do not equate EARLINET membership with ACTRIS certification.

**Next evidence:** permission capture for the new API and relevant terms; one bounded BGD catalogue query; only then inspect the existence, licence, time coverage and quality level of a local product. No data request was made in this lane.

## 2. Plovput: delivered bathymetry/discharge equipment and confirmed Belgrade-area surveys

**Disposition:** strong new device-and-data-holder candidate. The equipment and the local surveys have independent operator evidence; their exact linkage is unknown.

| Evidence | What the primary source establishes | Limits |
|---|---|---|
| [Equipment announcement, 2025-05-20](https://www.plovput.gov.rs/vesti/1/1537) | Plovput reports acquiring an SV 25 survey boat equipped with a **Teledyne IDH-T50R multibeam echo sounder** and **ADCP RiverRay** discharge instrument, under Fairway works in the R-D Corridor. The article describes the boat as equipped, not merely tendered. | Exact instrument spelling is retained as published. No serial number, accuracy validation, last use or assignment to a particular Belgrade survey was inspected. |
| [Completed 2025 survey season, 2025-12-16](https://www.plovput.gov.rs/vesti/1/1580) | Plovput reports completing **34 profiles at Boljevci and Ostruznica anchorages on the Sava**, alongside surveys elsewhere, then checking, processing and storing the measurements in its database. These named anchorages establish Belgrade-area coverage. | The article does not give survey dates, profile coordinates, file schema or instrument used. The 34 count is an operator report, not a count of records received by BEOPS. One later open encountered a challenge; no bypass was attempted. |

**Spatial/temporal scope:** riverbed cross-sections and potentially flow measurements at surveyed locations. The confirmed local product is the 2025 anchorage profile collection. Survey cadence is campaign/annual-plan based; no continuous station stream or per-profile measurement time was inspected. The new boat's national mission does not establish that it collected these 34 profiles.

**Access:** operator-held processed data, with no public raw bathymetry/discharge API demonstrated. Public navigation plans are a possible derived output, described in finding 4. Terms, redistribution rights, formats and a public route to the actual local survey profiles remain unknown. A future authorised institutional request could ask for these exact profiles and metadata; no message was sent.

## 3. RHMZ Kosutnjak radiosondes: local upper-air data beyond the surface-station entry

**Disposition:** deepen existing RHMZ source family; do not count this as an independent provider. S02 is the surface station detail, whereas this evidence describes balloon-borne vertical measurements.

The [official English aerology page](https://hidmet.gov.rs/eng/meteorologija/aero_eng.php), opened 2026-09-06 with no publication date displayed, states that radiosonde measurements have operated at Belgrade–Kosutnjak since April 1987, at least twice daily. It identifies temperature, humidity, pressure and wind profiles and typical ascent heights of 30–35 km. It links an observed Belgrade Skew-T product. The [Serbian page](https://www.hidmet.gov.rs/ciril/meteorologija/aero.php) describes measurements collected and processed every second during a sounding. This internal sampling rate is not a one-second public API.

**Historical hardware detail:** the [2009 aerological yearbook, published 2010](https://www.hidmet.gov.rs/data/meteo_godisnjaci/Aeroloski_godisnjak_2009.pdf), introduction on PDF page 3, names Vaisala DigiCORA III / MW31 and RS92 sondes at Kosutnjak; historical location is 44°46′ N, 20°25′ E, 203 m. That describes the 2009-era system. A [2015 RHMZ tender amendment](https://www.hidmet.gov.rs/data/nabavke/1437385701.pdf), found through primary-source search, instead names balloons for M10 sondes and MODEM SR10. It does not prove present hardware or installation site and is retained only as a reason not to promote RS92 into a current inventory.

**Data/time/access:** public diagrams and a historical yearbook route are documented. This pass read the yearbook's instrument/method section, not a historical series for ingestion. Current English and Serbian page extractions showed differing hour labels (06 and 00 UTC; an earlier search extract showed 18 UTC), without a verified full observation date from the diagram. Therefore latest observation time and present launch schedule are **unknown**. No diagram was downloaded, no numerical sounding API was verified, and current model/serial/cadence/permission remain open. RobotSonde on this page is explicitly in **Nis**, not Belgrade.

## 4. Plovput's April 2026 bulletin: new derived data route, with supplier distinction

**Disposition:** new operator-published product route, related to finding 2 rather than an additional independent hydro network.

The [official announcement dated 2026-04-21](https://www.plovput.gov.rs/%D0%B2%D0%B5%D1%81%D1%82%D0%B8/17/1594), opened successfully, links [bilten.plovput.rs](https://bilten.plovput.rs/) and describes water levels, water temperature and forecasts supplied in cooperation with **RHMZ**; critical-sector plans based on Plovput surveys; bridge dimensions and calculated navigable clearance with a **96-hour forecast**; and aggregate numbers of moving/anchored vessels derived from Plovput AIS base stations.

This is a useful boundary: RHMZ water observations are reused inputs, bridge clearances are derived quantities, forecasts are predictions, and Plovput's bathymetry/AIS are separate inputs. The article demonstrates a published product, but this pass did not inspect its live records, exact Belgrade rows, API, record timestamps or terms. Its national Danube/Sava/Tisza scope includes a promising Belgrade route; local product coverage still needs a bounded check. No individual vessel records were collected or proposed for collection.

## Search log, exclusions and honest verdict

All discovery occurred on 2026-09-06. Primary web search/open tools were used; no scraping scripts, authentication attempts or opt-out workarounds were run.

| Search branch | Result and decision |
|---|---|
| WMO OSCAR/WIGOS: Belgrade and 13275 | Did not obtain a current Belgrade station metadata record. A WMO training result used BEOGRAD/SURCIN WIGOS ID 0-20000-0-13272 in a **2019** monitoring example; excluded from current-device claims. No WIS2 local topic was verified. |
| EARLINET/ACTRIS: Belgrade Raman lidar | Positive local station catalogue and full primary 2023 instrument paper; followed official access page to new API documentation. Local API holdings remain untested. |
| ICOS: Serbia/Belgrade | Search returned conference affiliations and work involving Vinca, not a verified Belgrade ICOS station. **Unresolved**, not `no_coverage`; institutional affiliation is not deployment proof. |
| Plovput: hydromet, sensors, multibeam, 2025 surveys | Positive delivered equipment, exact local surveyed anchorages and 2026 product announcement. Navigation water tables credit RHMZ; no independent Plovput hydrometeorological station was established. |
| RHMZ: aerology/radiosondes | Positive operator description, Skew-T route and dated historical hardware; guarded against assigning Nis RobotSonde or 2009 hardware to current Belgrade. |
| IPB UV radiation | Institutional [laboratory page](https://mail.ipb.ac.rs/~centar3/acp.html) links an old online UV-B route. Not pursued: no current reading or installed instrument established. |
| AERONET/GNSS | Handed to coordinator; no overlapping collection. |
| Sava/ICPDR/SEPA | Existing records checked. Sava redistribution restriction and ICPDR registration boundary retained; no duplicate collection or attempted bypass. |

Verified here: responsible institutions explicitly identify local lidar/radiosonde activity, delivered survey instruments, local survey data held by Plovput, and documented data routes. Not verified: current instrument uptime, accessible BGD lidar files, a new raw hydrology API, public reuse permission, complete local network coverage, or any present observation values. No exhaustive absence claim is made. Repository-wide tests and indexing are coordinator-owned integration work; this lane only created its preclaimed document and verified its contents/hash.
