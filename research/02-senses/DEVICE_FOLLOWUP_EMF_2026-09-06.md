Status: historical
Date: 2026-09-06
Author: emf scout (Codex sub-agent)

# RATEL fixed-station dictionary: what the sources actually resolve

Scope: read-only review of existing Beops station-21 evidence plus primary operator/manufacturer documentation. Only this report was written in the current C: workspace. No D: repository changes, archive re-download, measurement request, institutional message or device access occurred.

## Outcome

There is a second public Science and Technology Park record with a different method, coordinate and current page update date. It is a useful next metadata check, but no source inspected here establishes its relationship to the historical archive. The precise meanings of `99999.99`, duplicate times, timezone and the conflicting station-21 active labels remain unresolved. A date-limited public graph interface is documented; a corresponding bounded machine-readable archive URL was not found.

## 1. Two records must remain separate

Existing immutable local evidence is [FIXED21_QA.json](../evidence/device-discovery-20260906/FIXED21_QA.json), backed by source <https://emf.ratel.rs/getOpenData/21/json>. It preserves the original header and content SHA-256 `e3ecaba71a8a860c5c490e7d12569da35d3578497c62b9a93994c9766f42a20e`. This wave did not request that URL again.

| Attribute | Existing archive parameter 21 | Public results-page record 168 |
|---|---|---|
| Site label | BG- Naučno tehnološki park - pasiv | BG- Naučno tehnološki park |
| Address | Veljka Dugoševića 54 | Veljka Dugoševića 54, Beograd |
| Coordinate representation | Header GPS: longitude 20.50890000, latitude 44.80330000 | Page URL GPS: latitude 44.80362688, longitude 20.50281154 |
| Method | Selective measurement | Broadband, 100 kHz–8 GHz |
| Activity wording | Name says pasiv; `AKTIVNO` says Da | Page says measurement is active |
| Time evidence | Last data timestamp 2026-01-24 06:00:00; no timezone | Page label Updated: 06.09.2026; not an inspected measurement timestamp |

The second column is the previous local parse. The third is from the operator's [Science Park results page](https://emf.ratel.rs/results/details/lat/168/gps:44.80362688,20.50281154/params:1100111), opened successfully in this wave. No device model or serial number was established there. Replacement, relocation and concurrent monitoring are possible explanations, **not findings**. In particular, numeric identifiers in `/results/details/` and `/getOpenData/` have not been proven to use the same namespace. Do not infer a new data endpoint by substituting 168 into `/getOpenData/21/json`.

The current [operator legend](https://emf.ratel.rs/cyr/rezultati-merenja/) explains that active locations are where monitoring occurs, while passive locations are where it previously occurred. This establishes the general UI meaning of passive, but does not explain why the old JSON says `AKTIVNO: Da`, nor which label takes precedence. Keep both raw labels and mark current operational state unknown for the archive record.

## 2. Sentinel-like values and duplicate times remain unresolved

The existing QA counted 14 rows with `99999.99` in six bands, 84 cells, including the latest row. No inspected operator dictionary or manufacturer source assigns a meaning to **that exact value** in RATEL's public JSON. Do not convert it to missing, overload or failure, and do not publish it as a physical maximum.

The manufacturer's current [AMS-8061 datasheet, AMS8061-BEN-11205, pp. 2 and 4](https://www.narda-sts.com/index.php?dl=1&eID=dumpFile&f=1178&t=f&token=b9acd01fad935cf4c928f0be893ea2784a7e291c) lists a probe-dependent electric-field measuring range up to 200 V/m and overload at 435 V/m. This is a specification for that model family, not an export-error dictionary or proof of which exact probe generated every historical row. It does not decode `99999.99`.

The RATEL-coauthored [Wideband Approach of 5G EMF Monitoring, p. 7](https://emf.ratel.rs/download/02_AFRICOMM_2020_NDJ.pdf) describes native `.D61` binary files processed by a dedicated parser into a database before public publication. Thus the JSON is a transformed output. The paper supplies no deduplication key, correction precedence or rule that maps repeated times to retransmission. The existing 7,796 extra repeated-time rows, including 727 whose payload differs from the first same-time row after excluding RBR, must remain intact. A parser, device, clock or database cause has not been established.

## 3. Manufacturer documentation resolves instrument context, not export timezone

The same AMS-8061 datasheet explicitly describes **internal** temperature and humidity sensors, an internal real-time clock, and configurable storing rates of 1, 2, 6 or 15 minutes. This is useful support for avoiding an ambient-weather interpretation of the historical auxiliary columns. It does not independently establish the units or exact meaning of RATEL's `TEMPERATURA` and `VLAZNOST` columns. Configurable cadence also does not prove why the archive changes cadence.

No inspected operator source declares UTC, CET/CEST, an IANA timezone, daylight-saving policy or timestamp-offset convention for `DATUM_VREME`. Retain timezone as null. Do not use the sensor clock's existence, Serbia's location or server receipt time as a timezone dictionary.

The [manufacturer product page](https://www.narda-sts.com/en/products/emf-monitors/ams-8061/) links a current operating manual and FAQ. The [manual download](https://www.narda-sts.com/index.php?dl=1&eID=dumpFile&f=1180&t=f&token=ef15f49722ce3e0ed36432f9b808043d660377b4) is 10,927,785 bytes according to the web-tool size-limit error. It was **not downloaded or fully inspected** here. Search excerpts identify document AMS8061EN-60221-1.40, © Narda 2026; this is newer than much of the archive and would require careful version matching. Absence of a search hit is not proof the full manual lacks relevant information.

The [Narda Area Monitoring FAQ, December 2021, p. 2](https://www.narda-sts.com/index.php?dl=1&eID=dumpFile&f=1179&t=f&token=653ff3d3562730358c9545aa79c29521c9e2efed) explains that AMS-8061 integrates user-defined bands and does not expose a full spectrum view. It does not supply a RATEL JSON dictionary. Bands and their original names must remain distinguishable; do not fabricate a full RF spectrum from these columns.

## 4. Narrower historical review is supported in the public interface

The [Science Park results page](https://emf.ratel.rs/results/details/lat/168/gps:44.80362688,20.50281154/params:1100111) exposes From/Until date controls and a maximum selected range of **240 days**. This is a documented UI capability, not a verified JSON query contract. No date selection was submitted in this wave.

A [2020 paper authored by RATEL, Continuous monitoring of the electromagnetic field level, pp. 3–4](https://emf.ratel.rs/download/01_YUINFO_2020_NR.pdf), explicitly says the public graph supports choosing a past period or a part of a day. It separately identifies administrative settings as restricted to authorized personnel. The public date-selection page is the appropriate next place to inspect a bounded request. Internal FTP, direct instrument commands and administrative configuration are outside this task.

No primary documentation inspected here specifies date parameters, pagination, row limits or a smaller archive route for `/getOpenData/21/json`. Do not append guessed `from`, `to`, `limit` or replacement station IDs. First inspect the documented public control and its exact request, then have the coordinator capture and approve that precise route within a byte budget.

## 5. Legal scope and smallest useful capture targets

The accepted [Beops legal matrix](../07-legal/DEVICE_DATA_LEGAL_SORT_2026-09-06.md) covers identified S158 dataset resources and attribution requirements; it explicitly does not license all RATEL content. The [operator's open-data explanation](https://emf.ratel.rs/eng/otvoreni-podaci/) points to the national portal's CSV/XML/JSON datasets. This wave does not enlarge that grant to every detail page or a guessed endpoint. Manufacturer documentation remains copyrighted reference material, not open-licensed measurement data. Access checks, content licence and repeated collection remain separate.

Prioritized exact targets for coordinator review/capture:

1. **Small operator metadata/UI page:** <https://emf.ratel.rs/results/details/lat/168/gps:44.80362688,20.50281154/params:1100111>. Capture the labels and date-control contract before any bounded selection. Do not equate page update with observation time.
2. **Operator method paper, four pages:** <https://emf.ratel.rs/download/01_YUINFO_2020_NR.pdf>. Supports public historical selection and separates public results from administration.
3. **Manufacturer datasheet, five pages:** <https://www.narda-sts.com/index.php?dl=1&eID=dumpFile&f=1178&t=f&token=b9acd01fad935cf4c928f0be893ea2784a7e291c>. Supports internal auxiliary sensors, model-family range and configurable cadence. Its query token is the publisher's public document-link parameter.
4. **Manual only if the larger documentation read is budgeted:** the 10.9 MB manual URL above. Check historical/manual version and search exact sentinel, native time representation and parser-export semantics. This is an unresolved documentation lead, not a reason to touch a device or full archive.

Existing `/getOpenData/21/json` must remain a local analytical input, not a recurring sample URL. No newly verified machine-readable bounded route is delivered by this report.

## Search log and honest verdict

Read the previous EMF report, QA references, closed wave board and legal matrix. Primary searches used RATEL site restrictions with exact `99999.99`, `99999`, `AKTIVNO`, `pasiv`, `getOpenData`, `UTC`, `GMT`, `timezone`, `duplikat`, `duplicate` and `.D61`; manufacturer searches used AMS-8061 with the sentinel, clock and timezone terms. Exact sentinel/timezone/duplicate queries produced no relevant primary dictionary. Searches discovered and opened the current Science Park record 168, manufacturer product page, datasheet and FAQ, and the RATEL operator method paper. The old manually inferred details/21 page could not be opened, so no claim is based on it. The obsolete 2015 manual link failed; the current manual exceeded the web-tool limit. No bypass or alternate collector was used.

**Confirmed:** a distinct current public Science Park record; documented public date selection; manufacturer internal auxiliary sensors and programmable cadence; an operator-side binary/parser/database publication pipeline. **Still unresolved:** archive activity contradiction, relation between the two records and ID namespaces, exact sentinel meaning, duplicate origin/precedence, timezone, and a bounded machine export route. The useful outcome is a smaller next investigation and stronger separation of the records, not an invented completed dictionary.

## Follow-up: the captured record-168 HTML already contains a measured series

After the review above, the coordinator captured the exact page route and saved [science_park_record168.html](../evidence/S158/20260906T112754Z/science_park_record168.html). This follow-up only read that local file. It is **1,194,691 bytes**, SHA-256 **95868186ee46992c8f7be3cc197aea6d5df6736d1b33818f6310c9376adde677**. Thus the earlier metadata-only characterization is superseded for this saved response: it includes literal Chart.js data arrays. No JavaScript was executed and no additional request was made by the scout.

The derived [RECORD168_STATIC_QA.json](../evidence/device-followup-20260906/RECORD168_STATIC_QA.json) records the static parser method and results. A balanced-delimiter/string scanner isolated the two chart objects and their literal arrays; JSON decoding processed dates, labels and numeric values only. Script API keys, contact fields and other unrelated content were neither copied to QA nor used.

| Published chart content | Verified result |
|---|---|
| Main electric-field series, label Nivo polja | **1,681 numeric values** |
| Axis unit | **E [V/m]** |
| First/last chart labels | **30.08.2026. 00:00 – 06.09.2026. 00:00** |
| Unique labels | **1,681**; no duplicates |
| Adjacent label intervals | **1,680 intervals of six minutes** |
| Main-series nulls / zeros / nonnumeric values | **0 / 0 / 0** |
| Main-series min/max | **1.89 / 5.51 V/m**, as published |
| Latest published value | **2.12 V/m** at **06.09.2026. 00:00** |

These timestamps are embedded series labels, independently read from the payload, rather than a substitution of the page's update date. They still declare **no timezone**. The saved page proves a recent published series, not uninterrupted reporting after that last timestamp. There was no rendered-chart or live-instrument verification.

Two other field-chart arrays are labelled upper/lower uncertainty. The second chart uses axis **GER** and contains upper/lower exposure bounds and an allowed-limit curve equal to 1. These are separate published derived/reference curves, **not additional independent sensor measurements**. All populated arrays align with the same 1,681 labels. The field chart also defines a `Limit polja` object with **no `data` property**; absence remains absence, not zero or a fabricated threshold. No health/exposure-limit conclusion is derived here.

### Exact date-selection contract found without executing it

The actual `getResults` button and the two inputs `dateFrom`, `dateUntil` exist in the HTML. Both date pickers specify **`dd.mm.yyyy.`**, with an end date of today; their saved values are `30.08.2026.` and `06.09.2026.`. Source code for the button constructs this navigation path:

```text
/results/details/lat/168/from:{dateFrom}/until:{dateUntil}/params:{graphChbs}/gps:44.80362688,20.50281154
```

`graphChbs` has seven checkbox bits in this order: field level, field limit, upper uncertainty, lower uncertainty, upper exposure border, lower exposure border, allowed exposure limit. The captured source route supplied `1100111`. The page displays a maximum range of 240 days and its client code adjusts ranges exceeding that value. Server-side enforcement was not tested.

A concrete **one-day candidate for the coordinator's exact-route capture**, derived from this inspected button contract, is:

<https://emf.ratel.rs/results/details/lat/168/from:05.09.2026./until:06.09.2026./params:1100111/gps:44.80362688,20.50281154>

The scout did not request it. This is a substantiated HTML selection route; its response size, server behavior, resampling and reuse scope still require the coordinator's review. It does not change the fact that no bounded contract for `/getOpenData/21/json` has been found.

Inline code additionally contains `/results/saveResults1/168/from:{dateFrom}/until:{dateUntil}` and the analogous `saveResults2` handler. **Neither handler's target DOM control (`save-results-1`, `save-results-2`) exists in this saved HTML.** Consequently these are code leads, not verified active export controls. Do not claim CSV/JSON availability or send those requests on this evidence alone.

Legal handling remains separate from the technical discovery: the coordinator's supposedly metadata request already received public chart data. Retain that fact in the capture/provenance record and review reuse for this exact product; do not assume the archived S158 open-data resource grant automatically establishes rights for every chart detail/export route. Original D: evidence was untouched; only this C: addendum and its derived QA were written.
