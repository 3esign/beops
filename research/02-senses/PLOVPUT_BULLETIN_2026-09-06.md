Status: historical
Date: 2026-09-06
Author: procurement scout, native Codex sub-agent

# Plovput bulletin: source lineage and reuse boundaries

Scope: a bounded primary-documentation review for Beops wave 2. No D: files were changed; no bulletin records, vessel records or chart files were downloaded. The coordinator owns exact-host permission captures and any subsequent data request. This document is research evidence, not legal clearance or a navigational product.

## Principal finding

The operator publishes an explicit [terms page](https://plovput.gov.rs/pravila-koriscenja), reached through its official article footer. It claims copyright in the published texts, visual/audio/video materials, databases and code, warns against unauthorized use, and permits visitors to use portal services free of charge subject to those rules. A free service is not an open-data reuse grant.

The terms text names the legacy `www.plovput.rs` portal. Its exact application to `bilten.plovput.rs` should be retained as a scope question; do not assert either that the bulletin is exempt or that every reuse is prohibited. No explicit automated-access prohibition was identified in this page. No publication/update date was displayed; retrieval was 2026-09-06. The coordinator captured the terms and bulletin-host access evidence at `20260906T112601Z`, then deliberately held automated bulletin-record collection for a separate decision.

## Captured access outcome

The S187 capture manifest (private working record) and its headers (private working record) were independently read from disk in this lane. They record homepage HTTP 200, terms HTTP 200 and HTTP 404 for both bulletin-host and operator-host robots files. The stored terms file is 15,811 bytes. The homepage record has 6,632 response bytes and a content hash; this is access evidence, not proof that current records were parsed.

The append-only ledger entry for this capture has `capture_ok: true`, `allowed_for_us: null` and `manual_verdict: needs_decision`. Its reason distinguishes free service access from unresolved database reuse and legacy-domain scope. This is a deliberate collection hold, not a robots refusal and not permission clearance. The coordinator explicitly ended this lane at documentation, without raw/UI data extraction. No user permission question is required for the completed documentation work.

## Product lineage stated by the operator

The [official announcement, 2026-04-21](https://plovput.gov.rs/vesti/1/1595), links [bilten.plovput.rs](https://bilten.plovput.rs/) directly. It identifies these product families:

| Family | Stated lineage | Beops interpretation |
|---|---|---|
| Water levels, forecasts and water temperature | Published with RHMZ for the Danube, Sava and Tisza | RHMZ-origin inputs; forecasts remain separate from observations. |
| Critical-sector plans | Plovput's latest hydrographic surveys | Derived survey products, not continuous depth sensors. |
| Bridge opening heights | Calculated from current water level, with a 96-hour forecast | Derived clearances and forecasts, not direct bridge-height measurements. |
| Traffic picture | Plovput AIS base stations; numbers moving and at anchor | Aggregated traffic product; no individual-vessel data are in this task. |
| Notices to skippers and marking plans | Harbour-authority notices and annually prepared river-marking plans | Administrative/operational products, not environmental measurements. |

The article establishes product purpose and provenance. It supplies no record schema, measurement timestamps, API contract or licence grant for the underlying data.

## Minimal grounded routes

| Exact route | Evidence and permitted next question |
|---|---|
| `https://plovput.gov.rs/pravila-koriscenja` | Official terms opened; capture its wording and legacy-domain scope. |
| `https://plovput.gov.rs/vesti/1/1595` | Official Latin-script announcement opened; publication 2026-04-21. The previously cited Cyrillic article is the same announcement family, not another dataset. |
| `https://bilten.plovput.rs/` | Direct link from that announcement. Capture confirms HTTP 200; bulletin-record/UI data extraction is held at `needs_decision`. |
| `https://bilten.plovput.rs/pdf/mostovi/sava/DrumskiBrankovBeograd.pdf` | Search-index result identifies a Brankov Bridge document and Belgrade reference gauge. Not opened or downloaded; no present clearance or publication date established. |
| `https://plovput.gov.rs/izvestaj-o-merenju-gabarita` | Operator archive index opened. It lists a 2022 report and older survey-period links; not proof of a current bulletin feed or a public raw survey database. No linked files downloaded. |

Search also exposed document renderers under `www.bilten.plovput.rs/fpdm/mostovi_hminhmax.php`, with bridge-template and numeric input parameters, for Gazela and Ostruznica. Those indexed URLs establish neither a documented API nor the currency of their numeric arguments. No renderer was requested. Distinguish the `www` hostname from the announcement's apex host when assessing access evidence.

## Current limits and legal sorting recommendation

1. Retain attributed official announcement facts under the already adopted project framework. The newly found terms strengthen the need to distinguish factual reporting from copying full documents or reusing databases.
2. Mark bulletin reuse as **operator terms found; product-specific reuse unresolved**. A permissive robots result cannot supply a missing extraction/redistribution grant. Do not silently carry S187's announcement classification over to the bulletin database.
3. Any later aggregate-record inspection needs the coordinator's exact route capture, minimal fields and request/byte budget. The product should preserve observation time, forecast issue time and valid time, and derivation/source labels separately where the publisher supplies them.
4. Belgrade bridge documents are discoverable as indexed leads. Direct local UI content, current measurement dates, current bridge rows and aggregate AIS granularity have not yet been inspected in this lane.

## Search log and honest verdict

Searches: `site:plovput.gov.rs bilten 2026 1594`; `site:bilten.plovput.rs uslovi korišćenja licenca podaci`; operator terms/copyright searches; `site:bilten.plovput.rs Beograd mostovi`; and bulletin API/Swagger/RHMZ searches. Search results did not establish public API documentation. That is an unresolved route, not proof that no API exists.

Opened: official 2026 announcement, its terms link and the survey-report index. An official river-information-services link returned a verification/challenge page; no bypass or retry was attempted. No source quotations reproduced here. Search-engine publication-age labels were not adopted as source dates.

Verified: explicit operator terms, official bulletin link, stated separation of RHMZ inputs/derived products/AIS aggregates, indexed Belgrade-document leads, and the coordinator's stored access/hold record. Not verified: present bulletin UI data, permission for automated bulletin-record collection, product-specific reuse grant, downloadable machine records, current numerical conditions or vessel-level contents. Source-page research used web tools; only this C: report was written. Repository indexing, central legal decisions and any raw-data capture remain coordinator-owned. The final report was checked for UTF-8 validity, forbidden controls and its SHA-256; no code tests were needed for this documentation-only lane.
