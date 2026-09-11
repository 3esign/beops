Status: historical
Date: 2026-09-06
Author: emf scout (Codex sub-agent; coordinator review accepted)

# Belgrade EMF devices and data: verified local coverage

Accepted discovery snapshot. The [integrated report](DEVICE_DATA_DISCOVERY_2026-09-06.md) incorporates later captures and is current for this wave.

## 1. Belgrade drive campaign already exists in the local evidence

The November 2024 Belgrade campaign is already saved, under S155 rather than its correct subject S158. No new dataset request was needed to resolve the coverage gap.

- Immutable file: 9314c9_open-data-2-2.json (private working record).
- Source URL, as recorded by its manifest (private working record): <https://emf.ratel.rs/drive-test-open-data/open-data-2-2.json>.
- SHA-256, recomputed and matching manifest: `e350841f6584272ea0609ea2b5bee37fe15930cf30d9e866df526ce802c0a960`.
- Total objects: **7,781 = one campaign metadata header + 7,780 measurement rows**. Header identifies Beograd / Belgrade, BG, November 2024.
- Measurement dates: all rows are **2024-11-08**, minimum `09:02:08`, maximum `15:03:33`. All 7,780 `Date_time` values are unique. **No timezone or UTC offset is supplied** in these values or the header.
- Per-row fields: `Date_time`, `E_rms_avg`, `Longitude`, `Latitude`, `Height`. Numeric values are JSON strings. Unit/height reference and coordinate reference system are not declared in this JSON header.
- Coordinate extent: longitude **20.35953662 to 20.43062492**, latitude **44.79069237 to 44.86030167**. Zero longitude/latitude rows: **0**. Outside the explicit broad QA box longitude 20.0–20.8, latitude 44.4–45.1: **0**. This box check is not an administrative-boundary spatial join.
- **Four rows report `E_rms_avg = 0.00`**. Preserve them as reported zeros. Do not silently discard or relabel as missing.
- File retrieval in manifest: `20260906T025402Z`; HTTP Last-Modified: `2026-03-16 11:03:58 GMT`. Neither is measurement time.

The current [RATEL campaign index](https://emf.ratel.rs/drive-campaign/results/-/cyr) lists one Belgrade campaign, BG November 2024, alongside five other cities. This is a historical driven route, not citywide continuous coverage. The index contains no newer Belgrade campaign in the inspected text. Its crawled representation is not proof that no newer campaign exists elsewhere.

RATEL's [EMF homepage](https://emf.ratel.rs/) describes the campaign device as a vehicle-roof broadband electric-field sensor covering 100 kHz–8 GHz. The official [2024 annual report](https://www.ratel.rs/storage/upload/2025/07/2024-Izvestaj-o-radu.pdf), search-indexed figure 5.3 on printed page 34, names **MonitEM** for the Belgrade 8 November campaign. The exact campaign UI is <https://emf.ratel.rs/drive-campaign/results/2-2/cyr>. Direct web open of that route failed; direct report open exceeded the web tool's content-size limit. Therefore the MonitEM model identification is **primary search-excerpt evidence**, not a rendered page independently inspected by this scout.

The same report screenshot excerpt says **7,776 measurement points**, whereas the saved JSON contains 7,780 measurement rows. The difference equals the four zero-field rows, but exclusion of zeros is only a possible explanation, **not established**. Preserve both published counts and ask a later parser/UI comparison to resolve it. No field-strength maximum or exposure conclusion is promoted here.

### Provenance correction required before integration

The file's manifest says `sid: S155` and gates collection on S155's `20260906T011111Z` legal capture of `www.nettest.ratel.rs/opendata`. The EMF host is a different source route; this association does not prove exact-route permission. S158's existing legal capture covers the Jagodina `open-data-7-1.json` example. Coordinator should capture the exact Belgrade route under S158 and append a correction connecting the existing immutable file to S158. Do not move, rename, overwrite or retrospectively rewrite its old evidence/manifest. This is a source-association error discovered today, not a new collection by this scout.

## 2. Fixed-location monitoring is real, but listed locations are not live-device counts

The [RATEL continuous-monitoring page](https://emf.ratel.rs/cyr/rezultati-merenja/) lists **33 Belgrade locations** among 117 locations nationally. Its legend distinguishes active locations from passive locations where monitoring used to occur. The extracted list alone does not label each Belgrade location's current active state. Thus **33 listed locations**, not 33 currently reporting devices.

Examples include ETF, Science and Technology Park, RATEL, schools, kindergartens and student residences. The [RATEL open-data page](https://emf.ratel.rs/cyr/otvoreni-podaci/) explicitly routes the fixed-location results to the national portal in CSV, XML and JSON. Dataset source: [continuous field measurements at locations of interest](https://data.gov.rs/sr/datasets/rezultati-kontinualnog-merenja-nivoa-elektrichnog-polja-na-lokatsijama-od-interesa/). Portal resource modification date is 25 March 2025; it is not the time of the latest field reading.

Already-saved national-portal metadata in `research/_scratch/datagovrs/page_031.json` contains this dataset, 357 resources, licence `sodl`, and **34 BG-titled JSON resources**. The older catalog additionally includes Zemun stadium, absent from the current page's 33-location list. Scratch metadata is useful discovery evidence, not an immutable capture. These counts describe different dated listings and must not be merged into a live-device total.

Exact JSON data routes from that local catalog (no requests made):

| Site | Instrument evidence | Exact catalog route | Catalog resource modification |
|---|---|---|---|
| Science and Technology Park | Narda AMS 8061 specifically documented historically | <https://emf.ratel.rs/getOpenData/21/json> | 2021-09-16 |
| University of Belgrade, ETF | Named fixed monitoring location; model not individually verified | <https://emf.ratel.rs/getOpenData/114/json> | 2025-03-20 |
| RATEL | Named fixed monitoring location; model not individually verified | <https://emf.ratel.rs/getOpenData/5/json> | 2021-09-16 |
| OŠ Svetozar Miletić | Named fixed monitoring location | <https://emf.ratel.rs/getOpenData/146/json> | 2025-03-25 |
| OŠ Mladost | Named fixed monitoring location | <https://emf.ratel.rs/getOpenData/154/json> | 2025-03-19 |
| Zemun stadium | Older catalog only; current listed state unresolved | <https://emf.ratel.rs/getOpenData/29/json> | 2021-09-16 |

Do not substitute these catalog dates for measurement time. Current station response schema, last actual reading, timezone, continuity, station coordinates and active/passive state remain unprobed. The next bounded useful collection is one exact-route permission capture followed by one fixed-site sample, preferably Science Park because independent hardware history exists.

The RATEL-coauthored primary paper [The Wideband Approach of 5G EMF Monitoring](https://emf.ratel.rs/download/02_AFRICOMM_2020_NDJ.pdf) identifies **Narda AMS 8061** at Belgrade Science and Technology Park (pp. 7–9). It describes six-minute monitoring from **1 November 2019 to 19 March 2020**, 100 kHz–6 GHz instrument range and service sub-bands. The instrument sends results through mobile communications to central storage; the public route is the portal. This is strong evidence of historical deployed hardware and timestamped measurements at this site, not proof of today's station model or network uptime. No internal transfer service is a proposed collection route.

## 3. S59 and S155 are not sensor telemetry inventories

S59's public radio-frequency licence register and S155's broadcast spectrum catalog describe regulatory permissions. The [RATEL national-portal organization description](https://data.gov.rs/sr/organizations/regulatorno-telo-za-elektronske-komunikatsije-i-poshtanske-usluge/) says the broadcast set includes issued FM/TV transmitter licences, holder, working frequencies/channels, issue/expiry dates, transmitter location and licence status. These are authorization and infrastructure attributes. A licence does not alone prove a transmitter is installed, operating, sensing or publishing observations. Replace the registry's suggestion of a potentially complete installed transmitter inventory with this narrower interpretation.

The saved S155 manifest also exposes a data-format issue: `3ac303_opendata.json`, `.csv` and `.xml` were all the same **1,656-byte HTML page**, response content type `text/html`, from NetTest's `/opendata` route. The filename extensions are not evidence of parsed speed measurements. The current web extraction returns no page text. **No verified Belgrade speed-test dataset or test timestamps emerged in this pass.** A browser/API schema investigation remains a separate bounded task, subject to the project's aggregate-only/no-person rules.

## Search and verification log

2026-09-06: read ROOM_DOOR, campaign board, root AGENTS, CONTRIBUTING, claims and S59/S155/S158 registry records. Scoped file discovery located EMF JSON under S155 and portal metadata under `_scratch/datagovrs`. Parsed the Belgrade file locally; computed total/header/sample counts, date range, distinct times, extent, zero/outside-QA-box coordinates, zero field values and SHA-256. Inspected manifest URLs and content types. No evidence file changed.

Primary web paths inspected: EMF homepage, continuous-monitoring page, campaign index, open-data explanation, national-portal dataset and organization page, and the RATEL-coauthored AMS 8061 paper. Searches included `site:emf.ratel.rs Beograd`, Narda, MonitEM, `getOpenData`, and RATEL campaign/2024/Belgrade combinations. This found the annual-report MonitEM excerpt; direct report retrieval exceeded the tool limit. Broad university-network expansion was unnecessary once concrete existing Belgrade measurements and station routes were found.

## Honest verdict

Verified locally: the 7,780-row historical Belgrade campaign and hash; source ID/permission-gate association problem; NetTest HTML mislabeled by extensions; catalog routes. Verified from primary web text: real mobile and fixed monitoring methods, listed Belgrade fixed locations, open formats, historical Science Park instrument/time interval. Unresolved: active fixed-device count, latest station readings, current instrument assignments, timezone/CRS/height semantics, point-count discrepancy and NetTest measurement schema. No raw datasets downloaded, access workaround attempted, source IDs allocated, shared registry edited or external message sent. Parent owns provenance correction, indexing, independent acceptance and required project gates; this scout did not claim to execute the full test suite.

## Addendum: fixed station 21 local validation after coordinator collection

Status: bounded local validation delivered for coordinator review, 2026-09-06. This addendum changes the earlier statement that the fixed endpoint was unprobed: the coordinator subsequently obtained exact-route permission evidence and collected the response. The scout made **no network request** during this follow-up.

Source: <https://emf.ratel.rs/getOpenData/21/json>. Exact permission capture is `S158/20260906T104256Z`. Local fixed_station_21.json (private working record) and manifest (private working record) record receipt at `20260906T104327Z`, 225,410,096 bytes, content type `application/octet-stream;`, no Last-Modified date. Recomputed SHA-256 matches the manifest: `e3ecaba71a8a860c5c490e7d12569da35d3578497c62b9a93994c9766f42a20e`.

### Site and schema

The header identifies `BG- Naučno tehnološki park - pasiv`, Veljka Dugoševića 54, GPS string `20.50890000, 44.80330000`, sensor category `Selektivno merenje`, measured quantity electric-field effective value, unit **V/m**. It also says **`AKTIVNO: Da`**. Preserve the disagreement between the location name's `pasiv` and the active flag. Neither field plus this historical export proves live reporting today. This response does not name Narda or a serial number.

There is exactly one common measurement-row schema: `RBR`, `DATUM_VREME`, twenty frequency-band fields and `TEMPERATURA`, `VLAZNOST`. Band names are `87M_108M`, `138M_174M`, `380M_400M`, `420M_430M`, `430M_470M`, `470M_790M`, `790M_821M`, `832M_862M`, `880M_915M`, `925M_960M`, `1710M_1785M`, `1805M_1880M`, `2110M_2170M`, `2400M_2500M`, `3400M_3800M`, `5200M_5800M`, `2640M_2660M`, `2520M_2540M`, `2520M_2660M`, `3600M_3700M`. Do not sum overlapping bands into total exposure. The header's V/m applies to field strength; no separate temperature or humidity units are declared. Those two fields may describe device conditions and must not be presented as validated ambient urban weather.

### Actual time coverage and integrity

| Check | Result |
|---|---:|
| Total parsed JSON objects | 457,699 |
| Header objects | 1 |
| Measurement rows | 457,698 |
| Distinct `DATUM_VREME` strings | 449,902 |
| Earliest timestamp | 2018-02-27 02:06:00 |
| Latest timestamp | 2026-01-24 06:00:00 |
| Extra rows with an already encountered timestamp | 7,796 |
| Repeated-time rows differing from the first same-time payload, after excluding RBR | 727 |
| File-order backward timestamp transitions | 273 |
| Non-sequential RBR values | 0 |
| Invalid date-string shapes | 0 |
| Explicit timezone or UTC-offset strings | 0 |

`RBR` runs from 1 to 457,698 but time is not monotonically ordered. The first file row is January 2020, while the earliest timestamp occurs at RBR 59,332. Therefore neither the first row nor sequential RBR establishes the start of coverage. Preserve conflicting duplicate-time payloads; a unique-time count is not permission to discard them.

Sorted distinct-time differences are mostly **six minutes (399,738 gaps)** or **one minute (49,620 gaps)**. There are **496 gaps greater than six minutes**, **344 greater than one hour**, and **108 greater than one day**. The largest is between **2024-09-30 21:13:00 and 2025-04-19 06:00:00**, 17,311,620 nominal seconds, approximately 200 days. These calculations compare naive wall-clock strings on an artificial common scale; they do not infer the source timezone or resolve daylight-saving transitions. They establish discontinuity and mixed cadence, not a missing-sample denominator or network uptime percentage.

Row counts by timestamp year (duplicates retained): 2018: 573; 2019: 34,297; 2020: 102,268; 2021: 87,581; 2022: 89,547; 2023: 84,343; 2024: 27,110; 2025: 31,864; 2026: 115. The latest row is months older than retrieval. This is a substantial historical series, **not a verified current feed**.

### Values requiring source interpretation

All twenty band fields and the temperature/humidity fields are present on every row and parse numerically; there are no null/empty values in those fields. This is not equivalent to complete valid measurements.

**Fourteen rows contain the exact value `99999.99` in each of six bands**, 84 cells total: `3400M_3800M`, `5200M_5800M`, `2640M_2660M`, `2520M_2540M`, `2520M_2660M`, `3600M_3700M`. These occur from **2025-04-21 06:00:00 through the latest row, 2026-01-24 06:00:00**. This looks like a sentinel or invalid-value marker, but its meaning is **not documented in the response header**. Retain the exact supplied value and flag it as unresolved; do not publish it as a physical maximum or silently convert it to null. There are also **1,303 rows with all twenty field-band values equal to zero**. Their cause is unknown; retain reported zeros.

Executed verification: two bounded Node.js standard-library streaming passes over the local file; a brace/string-aware JSON-object scanner parsed every object, verified array delimiters and no unfinished object, recomputed full SHA-256, examined schema/numeric fields and counts, then checked sentinel dates/latest row. No full dataset was dumped into tool output or copied. No tests, external calls or central-record edits were made by this scout. The original evidence remains unchanged. Integration should carry the station-name/active-flag contradiction, absent timezone, data gaps, conflicting duplicates and unresolved sentinel semantics alongside the usable historical coverage.

Reproducibility artifacts added at the coordinator's request: the independent offline [Python auditor](../audit_fixed21_20260906.py) and immutable FIXED21_QA.json (private working record). The auditor uses only the standard library, makes no network calls, reads the original without mutation, and refuses to overwrite an output. Duplicate payload comparison excludes `RBR` and canonicalizes JSON object keys; the QA output retains the exact source hash, site header, schema, timestamp counts, gaps, sentinel counts and unresolved meanings without copying raw measurement rows.
