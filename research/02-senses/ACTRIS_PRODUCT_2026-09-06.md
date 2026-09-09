Status: historical
Date: 2026-09-06
Author: Codex hydromet agent
Source: S186
Scope: one bounded BGD optical-product investigation; no scientific data downloaded by this agent

# ACTRIS BGD product route investigation

The coordinator's bounded May 2020 query returned 39 BGD optical metadata objects: 34 Level-2 and 5 Level-1 products. Product **101626** is a concrete Level-2 355 nm backscatter profile from BARLI, with UTC interval, version, PID and checksum. Its metadata omits an explicit licence. The scientific-data permission remains unresolved because the current ACTRIS policy treats legacy Level-2 data separately. No raw profile was downloaded by this agent.

## Selected product

Evidence: `D:/Svemir/!Projekti/Beops/research/evidence/S186/20260906T112754Z/bgd_optical_may2020.json`, read without further remote requests. SHA-256: `D272F8846603552E0C2688C8A24C914673877F3BE9C88C8CFE7324608D3A429A`.

| Field | Verified value |
| --- | --- |
| Product ID | `101626` |
| Station / instrument | BGD, Institute of Physics Belgrade / `BARLI` |
| Variable / wavelength | Backscatter, 355 nm (`b0355`) |
| Observation interval | 2020-05-07 18:27:22–20:26:47 UTC; 1 h 59 min 25 s |
| Provider time encoding | `2020-05-07T18:27:22.000+0000` to `2020-05-07T20:26:47.000+0000` |
| Level / version / QC | Level 2.0 / version 3 / EARLINET QC v4; all 11 reported physical and 3 technical checks marked executed and passed |
| Filename | `EARLINET_AerRemSen_bgd_Lev02_b0355_202005071827_202005072026_v03_qc04.nc` |
| Advertised size | 41,374 bytes |
| Advertised checksum | `9af1cd69ba624ae63ec8e030ed7f6d9d` (32 hexadecimal characters; API key `Checksum` does not itself name the algorithm; compare MD5 only when authorized bytes exist) |
| Persistent ID | https://hdl.handle.net/20.500.12911/1.1H17K0JOYT7MPZ32 |
| Measurement ID | `20200507bgd1828` |
| Format convention | CF-1.7; route advertises NetCDF |
| Current-version creation | 2025-02-25 16:46 UTC; history also records versions/uploads in 2020 and 2021 |
| Processing | SCC 5.1.8; CNR-IMAA |
| Attribution names | Zoran Mijic (PI); Maja Kuzmanoski (originator, stored as `maja.kuzmanoski`); Institute of Physics Belgrade, University of Belgrade |

Selection is operational: a Level-2 backscatter profile spanning almost two hours, small enough for a single bounded check, with complete reported QC passes. It is not a comparative scientific claim that this is the best observation. All 39 objects are BGD; their returned intervals range from 2020-05-04 08:56:47 UTC to 2020-05-24 21:12:09 UTC. These bounds describe this response, not total station history or a continuous time series.

The WADL-grounded single-file route is **https://api.actris-ares.eu/api/services/restapi/opticalproducts/id/101626/downloads**. Single-product JSON is **https://api.actris-ares.eu/api/services/restapi/opticalproducts/id/101626**. These exact routes were sent to the coordinator for its capture/reuse decision; this agent did not request them. The PID was not dereferenced because it could resolve directly to scientific data.

## Documented minimal metadata routes

Read-only source: `D:/Svemir/!Projekti/Beops/research/evidence/S186/20260906T104316Z/ares_api.wadl`. The captured WADL gives the base with HTTP; the currently advertised API and DIVA client documentation use HTTPS.

| Purpose | Exact candidate URL | Why grounded / limit |
| --- | --- | --- |
| Historical campaign metadata | https://api.actris-ares.eu/api/services/restapi/datasets/id/516 | WADL JSON route `datasets/id/{id}`; primary campaign page supplies ID 516. Coordinator reports the response exceeded its 2 MiB cap and was not saved. Do not refetch. This is a dataset ID, not an optical-product ID. |
| BGD optical metadata in evidenced month | https://api.actris-ares.eu/api/services/restapi/products/metadata/optical_products?stations=BGD&fromDate=2020-05-01&toDate=2020-05-31 | WADL enumerates `optical_products` as the exact `kind`; listed query names are `stations`, `fromDate`, `toDate`. |
| Direct optical-list alternative | https://api.actris-ares.eu/api/services/restapi/opticalproducts/?stations=BGD&fromDate=2020-05-01&toDate=2020-05-31 | WADL route ends in `/`. It returns JSON and accepts these parameters. Capture this exact route separately before a data probe. |

The direct optical-list route also lists `fromDayTime`, `toDayTime`, `ewls`, `fileTypes`, `levels`, `qualityControlVersion`, and repeated `tag`. It does not document `limit` or `offset`; those belong to the separate `datasets/accesses` route. Do not add invented pagination. A returned product ID would ground the next single JSON lookup at `opticalproducts/id/{id}` or `products/metadata/optical_products/{id}`. Download paths return NetCDF/ZIP and remain outside this agent's scope.

The captured station response `research/evidence/S186/20260906T104707Z/ares_stations_RS.json` identifies canonical station `BGD`, two-character code `bg`, ACTRIS facility `q8yq`, Institute of Physics Belgrade, coordinates 44.8557 N / 20.3913 E and altitude 89 m. Generic catalogue membership does not establish a measurement product or current operation.

[DIVA's client reference](https://docs.diva-platform.com/api/pydiva/) corroborates the HTTPS API base. Its [ARES wrapper documentation](https://docs.diva-platform.com/data-gathering/sources/actris-ares/) uses lowercase examples such as `waw`; this does not prove server case sensitivity or justify replacing the captured canonical `BGD` identifier. Wrapper names such as `optical` are not substitutes for the WADL's `optical_products` route segment.

## Historical BGD campaign lead

The indexed original [ACTRIS May 2020 campaign page](https://actris.nilu.no/Content/?pageid=fbd17f7652e04deebf0d530c82cc800e) lists BGD / IPB Belgrade and supplies DOI [10.21336/gen.xmbc-tj86](https://doi.org/10.21336/gen.xmbc-tj86), dataset ID `516`, and PID `ARES/LCFUKTPCZKMII585U35Z9ZUKYFWO2AVC`. It describes an intensive May 2020 schedule around noon and after sunset, subsequent reprocessing, and mixed level-1/level-2 results. These are campaign-level facts; they are not the exact times or level of a particular Belgrade product. Its historical download instructions require EARLINET credentials; the newer [EARLINET access announcement](https://earlinet.eu/our-knowledge/access-to-data/) documents the replacement service without that requirement. Neither permits bypassing authentication on an old endpoint.

Observation quality: the original ACTRIS page remains discoverable in the search index, but direct opening now redirects to the generic NILU data portal. Treat the original indexed text as a historical primary-source lead requiring a current API metadata cross-check. [A participating institute's campaign entry](https://igf.fuw.edu.pl/en/publications/943/) independently describes the level-1/level-2 distinction; its heading links the broader collection DOI, so do not copy that identifier as the May dataset DOI.

## Product-specific legal classification

Keep the current matrix category for the raw product: **explicit licensing policy; product scope unresolved**. The [approved ACTRIS licensing policy](https://actris.eu/sites/default/files/inline-files/ACTRIS_ERIC_GA_approved_ACTRIS%20licensing.pdf), adopted 2023-06-06, assigns CC BY 4.0 to levels 0/1/2 and metadata of levels 1/2, but recommends rather than automatically assigns that licence to level 3 and legacy level 2. The [current data-policy page](https://data.actris.eu/data-policy) preserves this scope distinction. Product 101626's 2025 creation date does not by itself resolve whether its 2020 observations and earlier versions are covered by the legacy exception.

**Metadata scope has advanced:** these are now explicitly Level-1/Level-2 product metadata, so the policy's Level-1/Level-2 metadata category can be linked to this exact response. This is more specific than the earlier generic station catalogue. Keep contact attributes out of public notes. **Raw-product scope has not advanced to an explicit grant:** none of the selected object's property names identifies a licence, rights, access or policy field. The [ACTRIS-maintained data management plan](https://github.com/actris/data-management-plan/blob/master/DMP/ACTRIS-DMP.md) says legacy data may retain a different policy, which should be recorded in metadata; an omitted field is not an affirmative current licence. No resource-linked declaration for this product was found in the bounded search.

The indexed [broader COVID-19 collection page](https://actris.nilu.no/Content/?pageid=9fc8c68eda87498ba69147b4e3ec8608), DOI `10.21336/gen.682q-8163`, describes non-commercial/scientific use and attribution/coauthorship conditions. That page is not the same resource as dataset 516. Neither its restrictions nor CC BY 4.0 should be transplanted to an individual BGD file without an explicit relationship and applicable grant.

Operationally, retain this bounded metadata review under the existing evidence rules; cite attributed station/campaign facts. Before raw acquisition, coordinator should capture the exact metadata route, match station, product ID, interval, level/version and licence, then decide a single product's permitted use and size budget. E-004 still requires the minimal fields, horizon and request budget for any repeated extraction. Do not publish raw profiles merely because a route is accessible. No inference about EU text/data-mining law applying in Serbia is made.

## Outstanding evidence

| Required field | Current evidence |
| --- | --- |
| BGD individual optical product ID | Verified: 101626; dataset ID 516 remains separate. |
| Exact measurement start/end and time zone | Verified in the selected-product table, explicitly UTC. |
| Product level, version and QC | Verified: Level 2.0, v3/QC4; reported checks pass. |
| Exact licence / applicable provider declaration | Level-1/Level-2 metadata policy applies to the identified metadata class. Raw product's licence unresolved; do not label the NetCDF CC BY 4.0 yet. |
| Current cadence and latest observation | Unknown. Historical campaign scheduling is not today's cadence. |
| Download format / size | Single route advertises NetCDF; product metadata gives 41,374 bytes; bytes/in-file licence not examined. |

## Search and verification log

- Read the stored WADL, station response, current hydromet lane and legal-sorting matrix. All D: access was read-only.
- Searched primary ACTRIS/EARLINET pages, DOI strings and BGD campaign terms; identified May 2020 dataset 516 and separated its DOI from the broader collection.
- Opened DIVA's author-maintained API documentation to verify the current HTTPS base and distinguish wrapper arguments from server route vocabulary.
- Direct web opening of the legacy NILU content redirects to the generic portal. The old EARLINET published-dataset page, DOI and current Swagger JSON produced web-tool errors; these are not proof the underlying products are absent.
- A primary IPB PDF indexed a historical copy of the campaign page, but direct opening failed. Its bibliographic/archive lead does not substitute for current product metadata.
- Related pollen and GARRLiC papers link other stations or derived datasets. Their article/data licences were not applied to BGD products.
- Sent coordinator the exact minimal metadata URLs and the legacy-licence caveat. No API data probes, raw scientific downloads, institution messages, credentials, scheduling or D: writes were performed by this agent.
- Inspected the coordinator's captured 39 objects read-only and selected ID 101626. Used string-preserving JSON date parsing to avoid the shell converting UTC timestamps to the host's local offset. No contact values were printed or added to this note.
