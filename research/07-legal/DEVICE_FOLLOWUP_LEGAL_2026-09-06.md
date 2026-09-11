Status: current
Date: 2026-09-06
Author: Codex coordinator; independent product/terms reviews

# Follow-up legal sorting: product rights and actual access

This review applies the existing [collection frame](COLLECTION_LEGAL_FRAME.md), [edge cases](../08-provenance/EDGE_CASES.md) and [initial matrix](DEVICE_DATA_LEGAL_SORT_2026-09-06.md) to five advanced/new records. Other records are not cleared by omission. It records operational project decisions and publisher declarations, without revalidating every statement of Serbian law in the earlier frame.

| Source/product | Reuse basis | Actual access and evidence retention | Publication / next gate |
|---|---|---|---|
| **S158 archive 21 and mobile JSON** | Exact previously catalogue-linked resources retain their Serbian open-data grant and attribution conditions. | Already retained; no full-archive re-download. | Preserve authority, URL, retrieval date and transformations. |
| **S158 page 168 chart** | Operator factual evidence; the earlier resource grant is not automatically transferred to another page/product. | One bounded identified page request succeeded and included 1,681 chart values. Retained as local review evidence under the existing project practice. | Attribute factual findings; raw chart redistribution and repeated collection remain unresolved. No timezone or ID linkage is invented. |
| **S186 actual Level-1/2 product metadata** | Approved ACTRIS policy explicitly assigns CC BY 4.0 to Level-1/2 metadata; this response now identifies that category. | 39 objects received and parsed. Preserve authors/institutions and source/version; omit contact details from public summaries. | Product metadata scope is established; it does not imply rights in generic catalogue fields or all raw scientific files. |
| **S186 raw legacy product 101626** | No resource-linked licence field found. Legacy Level-2 policy may differ. | No NetCDF requested. Historical observation and earlier versions prevent treating a 2025 creation date alone as proof of a new-policy grant. | Exact raw-product licence remains the gate. Advertised size/checksum/QC are not verification of bytes. |
| **S187 Plovput bulletin** | Explicit operator content/database reservation; free service use does not supply a reuse grant. Terms name the legacy `www.plovput.rs` domain. | Homepage/terms captured; automated bulletin-record collection held with `needs_decision`. Existing historical notice facts remain attributed evidence. | Resolve exact product/domain scope before raw or recurring collection. This is a deliberate project hold, not an observed robots refusal. |
| **S190 author preprint** | Web extraction displays a CC BY 4.0 article declaration; underlying project data have separate conditions. | Identified article and robots requests returned 403. Stored `terms_1.html` is an error response, not captured article/licence text. No alternate downloader or further article request. | New source is an author-reported device lead with blocked direct access. Preserve the distinction between web-observed declaration and direct evidence. |
| **S191 WeBaSOOP catalogue / DTT record** | General open-science language does not license every linked dataset. The selected DTT version record explicitly declares CC BY 4.0. | Original catalogue and public DTT metadata received. Record metadata is public; data files are **restricted**; no active embargo is reported. No login or data-file request. | CC BY 4.0 does not provide credentials or establish access. Nine local DOI links do not mean nine openly downloadable datasets. Other resource licences/access states remain unverified. |

The selected DTT concept DOI is **10.5281/zenodo.18255335**; its captured version DOI is **10.5281/zenodo.18255336**, v1. Reported absence of an active embargo is not equivalent to open file access. The version-specific declaration does not license unrelated project files. See the [dataset review](../02-senses/WEBASOOP_DATA_2026-09-06.md).

Primary policy references: [ACTRIS policy](https://data.actris.eu/data-policy), [approved licensing PDF](https://actris.eu/sites/default/files/inline-files/ACTRIS_ERIC_GA_approved_ACTRIS%20licensing.pdf), [Plovput terms](https://plovput.gov.rs/pravila-koriscenja), [selected Zenodo record](https://zenodo.org/records/18255335), [project open-data catalogue](https://webasoop.org/index.php/open-data/).

## Evidence and the access-check correction

- S158 exact-page capture (private working record) precedes its bounded HTML receipt; original archive licence evidence is unchanged.
- S186 documented metadata-route capture (private working record) retains the policy and exact URLs. One oversized metadata response was refused by the data byte cap.
- S187 terms capture and hold (private working record) records the new explicit reservation.
- S190 direct 403 capture (private working record) is preserved. An offline supplemental decision (private working record) holds collection without refetching or changing the original evidence.
- S191 catalogue access (private working record) and DTT record/licence capture (private working record) concern different scopes. The latter's initial hold remains effective for raw restricted files even though subsequent reading resolved the licence declaration.

The existing capture code treated an HTTP 403 robots response as a robots 4xx with no stated restrictions and returned `allowed_for_us=true` despite a 403 article response. That is not proof of successful access or a stored licence. The offline S190 review places the source on hold using the existing manual-verdict mechanism; [C-009](../08-provenance/CORRECTIONS.md) records the limitation. Historical evidence and the collector's global behavior were not rewritten in this research wave.

No new ongoing collection or public release is established. E-003 remains a stated project practice with an unresolved legal scope, not a publisher grant. E-004 still requires a question-specific minimal field set, cadence, horizon and shared byte/request budget before repeated extraction is considered. The original limited requests and local analyses do not establish permission to mirror a database.
