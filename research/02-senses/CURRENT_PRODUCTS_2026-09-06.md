Status: current
Date: 2026-09-06
Author: Codex coordinator, with three native research/review lanes

# Current products, data meaning and sensory ecology

This continuation adds one source record, S192, for **189 registry records**. The count includes catalogues, archives and coverage gaps; it is not a device or live-feed count. Eight further literature/practice records broaden the existing 32-work sensing supplement. Separate supporting aerosol papers connect instruments to exact dataset citations. The [legal addendum](../07-legal/CURRENT_PRODUCTS_LEGAL_2026-09-06.md) governs the scope of this wave.

| Route | What is now established | What remains unverified |
|---|---|---|
| RHMZ Borča-dubok, 9NP163 | A public groundwater chart includes full dates through **2026-09-06**, latest published field **488 cm**; metadata names Pančevački rit/Danube basin | Measurement hour/timezone, instrument make, present transmission latency and exact field/datum contract |
| Eight remaining Ada Marina DOI records | All eight metadata responses succeed and declare **CC BY 4.0** for their described resources; exact versions and collected intervals now known where supplied | Seven NILU file-access states and file-level contents; AA files explicitly restricted |
| [EGMS calibrated product](https://land.copernicus.eu/en/products/european-ground-motion-service/egms-calibrated) | Operator explicitly lists EU27, Iceland, Norway and UK; **Serbia is outside this documented coverage** | This does not rule out independent Sentinel-1 analysis in Serbia |
| BEOG GNSS | Historical Belgrade study remains valid context; current NGL catalogue/three holdings lists did not establish BEOG | Current public product, last observation, station identity changes and exact licence |
| Local sensory/ecological literature | Seven scholarly works plus one creator-documented field practice: phenology, birds, Block 63 sound measurement, Skadarlija/Savamala listening | Current service operation or public raw datasets are not established by those publications |

## Borča: a dated observation, with gaps and duplicates

The exact [RHMZ reporting page](https://www.hidmet.gov.rs/latin/osmotreni/podzemne_automatske.php?parametar=nivo&stanica=beograd) was retained in one 20,459-byte response at 2026-09-06T12:38:11Z. Its static `line1` array is JSON-compatible; analysis ran no JavaScript and fetched no chart assets. The visible ten-value table omits years, but all ten entries match the fully dated embedded chart. The latest observation label is therefore **2026-09-06**, independently of the receipt date.

The response contains **389 rows, 284 unique dates, 105 duplicate surplus rows and no conflicting values for a repeated date**. Its 2025-09-26–2026-09-06 span covers 346 calendar days, with 62 absent dates in 11 gaps. The largest gap is 2026-08-04→2026-08-21, leaving 16 missing calendar dates. The raw response remains intact; no missing values were filled, and repeated rows are not counted as new observations. See the independent static review (private working record).

This verifies a date-only published series reaching the day of retrieval. It does not verify continuous daily coverage, the time of measurement, an update guarantee or a streaming service. The page's inverted depth axis supports a groundwater-depth interpretation, while its zero and ground elevations are 73.79 m and 73.39 m relative to the labelled Adriatic Sea datum. The neighboring station 164 explicitly documents pipe-top depth semantics, but it has different datums. Until the exact 163 contract is confirmed, converting 488 cm into water elevation 68.91 m or depth below ground 4.48 m remains a **conditional calculation**, not an additional official measurement. The [ground-product review](GROUND_CURRENT_PRODUCTS_2026-09-06.md) preserves the station and reference-frame distinctions.

## Ada Marina: measurement, label, version and access

The [per-DOI access review](ADA_DATA_ACCESS_2026-09-06.md) and its structured metadata review (private working record) cover the eight previously unchecked local DOIs. DataCite permits metadata reuse under CC0; that does not grant rights in measurement files. Every received DOI record separately declares CC BY 4.0. The previously checked DTT record is not requested again.

Three differences matter for analysis:

- The catalogue's **eBC** label points to DOI [10.48597/DKPQ-W9KT](https://doi.org/10.48597/DKPQ-W9KT), whose registered title is **Aerosol_absorption_coefficient**, v4, with collected interval 2023-10-20–2025-02-11. Do not equate absorption coefficient with an eBC mass concentration without the file's variable/units and conversion method.
- The **PNSD v3** DOI [10.48597/CQF2-YGGJ](https://doi.org/10.48597/CQF2-YGGJ) declares 2024-02-14–2024-07-28. A related paper describes its study more broadly as February–August 2024. The exact deposit and the paper's study wording remain separate.
- **Total carbon v3**, DOI [10.48597/3YA2-Z4PX](https://doi.org/10.48597/3YA2-Z4PX), lists **two disjoint intervals**, 2023-10-24–2024-07-25 and 2024-09-20–2025-06-19. A single minimum/maximum span would hide that interruption.

The AA concept DOI resolves to version record 18254835. Its public landing explicitly restricts files despite an inactive embargo flag. The seven NILU canonical landing URLs are grounded by metadata, but anonymous file access remains unknown. No aerosol measurement files were acquired.

The separate January 2026 [Environments paper](https://doi.org/10.3390/environments13010047) describes MPSS 3938 at 90-second acquisition, AE-33 at five minutes and TCA08 at half-hour intervals in a historical Ada campaign. These instrument acquisition intervals are not the publication latency of the linked deposits. The dossier also documents a separate 2026 preprint's chemical instrument/sample chain, explicitly marked unreviewed and kept distinct from S190's held direct route.

## What the literature adds to the idea of a sense

The [eight-record annotated review](../04-bibliography/SENSORY_ECOLOGY_LITERATURE_2026-09-06.md) supplies bibliographic identities, reading depth, actual observation dates, methods, data routes and rights limits. Six scholarly full texts were inspected in relevant passages; one article was limited to indexed primary sections after 429; one record is a creator's account of artistic fieldwork. This is a targeted gap review, not a systematic-review completeness claim.

Its observation chains broaden the earlier [sense map](SENSES_CONTEXT_MAP_2026-09-06.md): repeated BBCH flowering observations during 2007–2022; weekly leaf-fall observations of 58 oaks at Ada Ciganlija/Bojčin in 2004–2006; episodic river-bird point counts; a meter and phone compared in Block 63; soundwalking, interviews and questionnaires in Skadarlija/Savamala; and a composed portrait based on recorded field material. These methods observe different properties and require different interpretations. Decibels do not encode musical meaning; an edited sound portrait is not an unaltered measurement series; a questionnaire sample is not automatically representative of Belgrade.

## Remaining concrete paths

The smallest useful next steps are the seven metadata-grounded NILU landing pages for file inventory and exact variable descriptions; the station 163-specific datum/measurement contract; and deeper domestic thesis/institutional plus international comparative searches under the two existing room assignments. Any new acquisition needs its own exact-route review and recorded size/cadence scope. No broad archive pull is implied.

The domestic room prompt (private working record) and comparative room prompt (private working record) remain ready. No external startup or acknowledgement was observed. This completed native continuation does not claim those two assignments ran. No institution was contacted, no service account was created, and no public deployment or continuous collector was added.
