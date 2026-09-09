Status: current
Date: 2026-09-06
Author: Codex coordinator

# Current-product access and reuse scope

This addendum extends the [collection legal frame](../07-legal/COLLECTION_LEGAL_FRAME.md) and [previous product review](DEVICE_FOLLOWUP_LEGAL_2026-09-06.md). It records the basis and limits of this bounded local research, not a general legal opinion or a deployment clearance. Technical permission to request a page, its observed access state, a declared licence and permission to redistribute are separate fields.

| Resource | Observed access | Declared basis and exact scope | Decision in this wave |
|---|---|---|---|
| S192 RHMZ Borča-dubok public reporting page | Identified HTTPS request 200; robots allowed; no opt-out signals | Operator-posted hydrometeorological law Article 36 requires source citation for published hydrological/meteorological data; sale or transfer to third parties of data obtained from the state fund requires RHMZ consent | One capped local evidence receipt and attributed factual analysis. Raw redistribution and recurring collection remain unresolved; no public mirror or scheduler |
| S191 eight DataCite singleton records | All eight exact routes200 and valid JSON | DataCite declares its DOI metadata CC0. Each received DOI record separately declares CC BY 4.0 for its described resource | Retain metadata with exact DOI, version, dates and provenance. CC0 does not apply to the underlying measurement files |
| S191 AA Zenodo landing | Public record, files restricted; inactive embargo flag | Landing resolves concept 18232817 to version 18254835, with its own rights metadata | Access restrictions remain in force despite declared licence. No login, file request or contact |
| S191 seven NILU resources | Canonical landing URLs learned from DOI metadata; file access not verified | DOI rightsList declares CC BY 4.0, but file inventory and resource-specific notices were not inspected | No anonymous-download or complete archive claim; no measurement files requested |
| S102 EGMS calibrated coverage page | Identified public page200 | Operator names EU27, Iceland, Norway and United Kingdom; annual archived product | Record no Serbia coverage for this documented product. No login or tile query needed to answer that coverage question |
| BEOG historical GNSS citation | Current NGL catalogue/holdings searches did not establish a functioning BEOG product | NGL public/script access and NBMG institutional CC BY 4.0 evidence do not resolve a missing exact BEOG file and its upstream rights | Historical study retained; current source, data clock and exact grant remain unconfirmed |

## RHMZ: a sector-specific rule that the general framework must retain

The [operator-posted law](https://www.hidmet.gov.rs/data/download/zakon_o_met_i_hid_delatnosti.pdf), Article 36 on PDF page 23, distinguishes source citation for published information from consent to sell or transfer data received from the state fund. Article 35 addresses access to the internal computing/telecommunications system; it is not used here as a blanket ban on reading an ordinary public webpage. No internal system was accessed.

The precise treatment of a downstream raw mirror, supplied datasets, derived facts and recurring collection is not resolved by this one publication. The project therefore keeps the one local factual receipt and attribution, and does not mark raw redistribution as cleared. An operator-posted draft law is not substituted for the enacted text. This is a source-specific qualification to earlier general official-material reasoning, not a silent rewrite of old immutable captures.

The new [phenology review](../04-bibliography/SENSORY_ECOLOGY_LITERATURE_2026-09-06.md) supplies a practical example: an openly licensed article describes RHMZ input data with a separate republication restriction. Article rights do not transfer to all inputs. Likewise, music, interviews, soundwalk recordings and restricted ecological datasets remain distinct from public scholarly summaries.

## Stored proof and collection limits

- [S192 legal manifest](../evidence/legal/S192/20260906T123023Z/MANIFEST.json): exact reporting route, operator law PDF, verified TLS and hashes.
- [S192 page receipt](../evidence/S192/20260906T123811Z/MANIFEST.json): one 20,459-byte HTML response; no executable script evaluation or follow-up asset requests.
- [S191 legal manifest](../evidence/legal/S191/20260906T123714Z/MANIFEST.json): eight exact API routes, DataCite CC0 statement and AA access evidence.
- [S191 metadata receipts](../evidence/S191/20260906T123813Z/MANIFEST.json): eight singleton bodies capped at 128 KiB each; no dataset files.
- [S102 coverage evidence](../evidence/legal/S102/20260906T123712Z/MANIFEST.json): original operator coverage page stored as terms evidence; no data tile requested.
- [DataCite harvesting policy](https://support.datacite.org/docs/harvesting-datacite-doi-metadata) and [documented singleton route](https://support.datacite.org/docs/api-get-doi) explain the metadata access contract.

The request budget was extended in the [bounded board](../_trail/CURRENT_PRODUCTS_BOARD_2026-09-06.md) before the eight metadata requests. Stored bodies passed 200/status, JSON and byte-cap checks. A preliminary S102 identity collision was resolved with the tool's shared-host flag because distinct Copernicus products use the same host; that initial attempt stopped before network access. No access refusal was bypassed. Existing S190403 and S175 opt-out holds remain unchanged.

Attribution for local facts: Republic Hydrometeorological Service of Serbia, named station/product, exact URL, observation date where explicit, receipt time and transformation description. Dataset reuse additionally requires the creators, DOI, actual version and its resource licence. Machine access flags never override an explicit restriction.
