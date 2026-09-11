# CLAIMS — who is writing what, right now

Append-only. One line per event. Claim before you write; release when you stop.
The protocol is in [CONTRIBUTING.md](CONTRIBUTING.md) §1.

```
<ISO8601 UTC> · <mind> · CLAIM|DONE|RELEASE|BLOCK|HOLD <path> · <one line: what, or the proof>
```

A claim older than **two hours** with no `DONE` or `RELEASE` is stale. Take it — and write a line
saying you took it. Nothing is ever silently overwritten.

Evidence under `research/observations/` and `research/evidence/` is never claimed, because it is
never edited.

---

2026-09-05T18:25Z · claude-cowork · RELEASE research/ · restructure applied with tools/migrate_structure.py; 28 moves, 51 links rewritten, 0 broken, npm test 36/36
2026-09-05T18:25Z · claude-cowork · DONE CONTRIBUTING.md · created; the system of order this file belongs to
2026-09-05T18:25Z · claude-cowork · DONE CLAIMS.md · created

2026-09-05T19:05Z · claude-cowork · DONE research/02-senses/NOVA_CULA_RUNDA3_2026-09-05.md · round 3 written; 27 institutional products opened at source
2026-09-05T19:05Z · claude-cowork · DONE research/SOURCE_REGISTRY.json · 38 to 67 records, S39-S67, JSON.parse verified before write
2026-09-05T19:05Z · claude-cowork · RELEASE research/ · nothing held

2026-09-05T22:05Z · claude-cowork · DONE research/02-senses/CULA_RUNDA4_2026-09-05.md · feeds, cameras, sound
2026-09-05T22:05Z · claude-cowork · DONE research/02-senses/OPEN_LAYER_V1_2026-09-05.md · the layer that depends on nobody
2026-09-05T22:05Z · claude-cowork · DONE research/07-legal/COLLECTION_LEGAL_FRAME.md · primary texts, quoted
2026-09-05T22:05Z · claude-cowork · DONE research/SOURCE_REGISTRY.json · 67 to 111 records; opted_out added as a status
2026-09-05T22:05Z · claude-cowork · RELEASE research/ · nothing held

2026-09-05T23:05Z · claude-cowork · DONE research/02-senses/HISTORY_AND_SPATIAL_BASE_2026-09-05.md · Wayback CDX queried directly; spatial base inventoried
2026-09-05T23:05Z · claude-cowork · DONE research/SOURCE_REGISTRY.json · 111 to 132 records
2026-09-05T23:05Z · claude-cowork · RELEASE research/ · nothing held

2026-09-05T23:35Z · claude-cowork · DONE research/02-senses/HISTORY_AND_SPATIAL_BASE_2026-09-05.md · addendum: ohsome open and measured, CLMS imperviousness covers Serbia, EGMS still unresolved with the reason

*Why this file exists:* on 2026-09-05 two minds wrote into `research/06-paper/rad_draft.md` within
hours of each other with no lock. It worked, but by timing rather than by design — one pass absorbed
the other's findings, and the second caught an artefact the first had promoted to a headline result.
The next collision will not be as lucky.

2026-09-05T19:34Z · Astra · CLAIM research/engine_*.js, research/test_engine.test.js, research/EXPERIMENTS.json, research/01-programme/EXECUTION_SYSTEM.md, research/README.md, tools/test-research.js, package.json · implement offline evidence-first research execution; no core, pilot or manuscript edits

2026-09-05T22:37Z · Astra · CLAIM research/write_izvestaj.py, research/test_write_izvestaj.py, research/README.md · final OBS-001 report; fix protocol group, failed-receipt handling and immutable publication; preserve all samples

2026-09-05T22:40Z · Astra · DONE research/write_izvestaj.py, research/test_write_izvestaj.py, research/README.md · 44 tests pass; final IZVESTAJ.md read back, 270 values and ten receipt hashes checked; no sample edits

## 2026-09-06 — provenance folder, and S57 collected

CLAIM  svemir  research/08-provenance/**, tools/legal_capture.py, tools/build_provenance_index.py
DONE   Built the permission-evidence system: captures store robots.txt, response
       headers with opt-out signals, terms pages and SHA-256 per source under
       research/evidence/legal/; INDEX.md is generated from those captures so it
       cannot claim what the bytes do not support. EDGE_CASES.md records eight
       places where the law is unsettled, what we do anyway, and the question we
       would put. CORRECTIONS.md records C-001: the tool's first run reported
       seven total failures as "allowed_for_us": true, because None is not False.
       Fixed to three states; unknown never renders as permitted; no insecure mode.
       Second failure, same day: ids S134/S136/S137 were allocated to sources
       already registered as S57/S95/S04. Fixed by putting the check in the tool -
       it now refuses an unregistered id and refuses a host that belongs to
       another source, naming it.

CLAIM  svemir  research/02-senses/ROAD_COUNTS_2026-09-06.md, research/collect_putevi_aadt.py, research/putevi_parse.py
DONE   S57 collected. 44 XLS retrieved from JP Putevi Srbije (2018-2024, four road
       categories), stored with manifest and hashes, parsed to 7448 rows. Each file
       defines its own legend and the parser reads it per file, because the asterisk
       means different things in different publications. Serbia, 6940 section-years:
       36.7% observed, 36.0% interpolated, 21.9% unavailable with a stated reason.
       The observed share fell from 46.3% (2019) to 27.0% (2024). Belgrade: 45.7%
       interpolated, 36.7% observed; the largest published figure on the ring
       (55 545, Bubanj Potok - Transped) is interpolated, not measured.
       Not a recurring collector; see EDGE_CASES.md E-004 before it becomes one.

RELEASE svemir

## 2026-09-06 (later) — the verdict engine, and four corrections

CLAIM  svemir  tools/legal_capture.py, tools/build_provenance_index.py, research/08-provenance/**
DONE   The permission tool now implements RFC 9309 matching itself - longest
       match, * and $ wildcards, Allow wins ties - runs it alongside
       urllib.robotparser and takes THE STRICTER OF THE TWO. Found because
       urllib cleared transit.land's /feeds/<id>, which RFC 9309 disallows
       (Allow: /feeds precedes Disallow: /feeds/). Content-Signal is now read
       from inside robots.txt, not only from HTTP headers, and applied BY
       PURPOSE: ai-input=no or search=no forbids; ai-train=no is honoured,
       recorded, and travels with the data. A --refused flag records a refusal
       the parser cannot see (Pleiades names ClaudeBot, Claude-Web and
       anthropic-ai while User-agent: * permits all - reading it under another
       name is circumvention). A --needs-decision flag holds a verdict open.
       There is deliberately no flag that can force a permission.
       CORRECTIONS.md now carries C-001 through C-004, including C-003: data
       was taken from Wikidata and Overpass before their permission was
       captured, inverting this folder's own first rule.
       EDGE_CASES.md gains E-009 (robots.txt on an endpoint built to be
       queried) and E-010 (permission is per purpose, not yes or no).

RELEASE svemir

## 2026-09-06 (evening) — the open state layer

CLAIM  svemir  research/02-senses/OPEN_STATE_LAYER_2026-09-06.md, SOURCE_REGISTRY S146-S156
DONE   Opened the front door the project had walked past: data.gov.rs has a
       keyless udata API and 3530 datasets; BEOPS had taken one. Harvested all
       3530 (36 pages, 700ms apart) and read the portal honestly - 46% comes
       from a single publisher and 113 are retail price lists, but underneath
       are eleven sources worth having.
       S146 is the model source and it is Serbian: SEPA's air quality HVD API
       at opendata.kosava.cloud states, as fields in every response, its
       snapshot time, that the data are preliminary, how they were aggregated
       and over what period, how long it retains, and its legal basis as an ELI
       URI (Reg (EU) 2023/138 on high-value datasets). 87 stations nationally,
       32 active in the Belgrade bbox, 15 components including BTEX, EEA
       AirBase station codes. Paired with S06 (verified daily) the same
       measurement exists in two publisher-declared states.
       Also registered: RZS REST behind one URL pattern with 1034 datasets and
       robots.txt Allow: / ; APR's full company register with DatumPreseka;
       the RGZ address register as GeoPackage; an open Ministry of Mining
       ArcGIS where ten exploitation fields intersect Belgrade; pollen weekly
       since 2016; NRIZ emissions 2010-2024; the Commissioner's sixteen daily
       series; RATEL spectrum and speeds; public procurement notices 2013 on.
       Two senses nobody had proposed: air that has a species, and the act of
       being asked.
       legal_capture.py gained a 2 MB body cap so a 57.8 MB open endpoint can
       be captured rather than failing. S149 and S156 remain under Evidence
       incomplete and nothing may be taken from them yet.

RELEASE svemir

## 2026-09-06 (night) — geoparsing as a category, and the walk continues

CLAIM  svemir  research/03-models/GEOPARSING.md, SOURCE_REGISTRY S171-S176
DONE   Wrote the design for turning content into place: geoparsing as a DERIVED
       BINDING METHOD (inferred_from_content), never a state and never a
       measurement. Carries a full derivation chain - source document and
       sha256, character span, surface form as written, the lemma rule, the
       script, EVERY candidate considered with its gazetteer version and score,
       the chosen one and its MARGIN over the runner-up, model version, and
       verification. Keeping the losers turns a wrong answer into evidence: it
       shows whether the right place was never a candidate (gazetteer gap) or
       was and lost (disambiguation failure), which need opposite fixes.
       Serbian specifics written down: two scripts, heavy inflection where both
       words of a two-word name decline, settlement names that are also common
       nouns, repeated settlement names, streets that are personal names, and
       Beograd being a city, a district and a container of seventeen
       municipalities at once. Gate: gazetteer first, rules before models, a
       hand-built held-out set, and precision, recall and resolution accuracy
       reported separately.
       Walk found: building permits open by robots (H8 confirmed reachable);
       the official gazette explicitly allowing its ELI paths, which is both the
       cleanest legal corpus and the best geoparser material; data.europa.eu
       with a keyless search API and 8154 Serbia results, which is the
       legitimate route to the CORDIS data that CORDIS itself disallows.
FIXED  legal_capture.py: a site serving HTML at /robots.txt with HTTP 200 looked
       to both parsers like a robots.txt with no rules, so both said allowed and
       the record said "robots.txt served". abs.gov.rs does exactly this with
       82 KB. The tool now detects HTML and records the path as returning HTML,
       treated as absent rather than as permissive.

RELEASE svemir

## 2026-09-06 (late) — collected what we may, cleared the backlog, scanned the instruments

CLAIM  svemir  research/collect_permitted.py, tools/capture_backlog.py, research/01-programme/DISCOVERY_PROTOCOL.md
DONE   Collection now exists and gates itself on the provenance ledger: 218 files
       stored across thirteen sources, with every skip printed and no override
       flag. Backlog cleared: 121 sources captured in one pass, index from 31
       permitted / 137 undocumented to 143 permitted / 18 undocumented.
       Four genuine refusals found, one of them a pattern: OpenStreetMap's API,
       Wikidata's SPARQL and Overpass all disallow the path that is their API.
       Evidence compressed 1.5 GB -> 332 MB; original sha256 kept in the
       manifests so integrity is still verifiable through gunzip.
       Wrote the discovery protocol: seven proven rules plus eight new methods,
       the strongest being PROCUREMENT AS A SENSOR CENSUS - a city cannot
       install an instrument without buying it, and cannot buy it without
       publishing a tender, so the procurement record is an inventory of the
       instruments that exist including every one whose data is never published.
       Registry gains the census statuses: paid, request_required,
       exists_unpublished, exists_via_literature, sought_not_found.
       Instrument scan found four new senses with Belgrade coverage: GBIF with
       512,241 dated geolocated life records over twenty years; iNaturalist with
       58,797; Panoramax street imagery with CC-BY-SA-4.0 declared in the
       response body, which matters because all three camera networks refused
       us; and adsb.lol, where every aircraft carries outside air temperature
       and wind, making the sky over the city a free atmospheric sonde.
       One more comparative absence, checkable in one file: of 1,535 GBFS
       bikeshare systems worldwide, Serbia has zero, against Croatia 22,
       Romania 11, Hungary 10 and Bosnia 3.
FIXED  C-005 and C-006 in 08-provenance/CORRECTIONS.md - the stricter-of-two
       rule turning urllib's bug into a refusal, and a valid certificate
       rejected because our own CA bundle was older than the web.

RELEASE svemir

2026-09-06T10:36:44.8863588Z · Codex coordinator · CLAIM research/02-senses/DEVICE_DATA_DISCOVERY_2026-09-06.md; research/_trail/DEVICE_DISCOVERY_BOARD_2026-09-06.md; research/SOURCE_REGISTRY.json; research/README.md; README.md; research/08-provenance/LEDGER.jsonl; research/08-provenance/INDEX.md; KNOWLEDGE.md; LOG.md; svemir_kit.json · User asks to continue finding devices and data. Own integration and unique new evidence only.
2026-09-06T10:36:44.8863588Z · procurement scout · CLAIM research/02-senses/DEVICE_PROCUREMENT_2026-09-06.md · Independent primary-source research, no central edits.
2026-09-06T10:36:44.8863588Z · hydro scout · CLAIM research/02-senses/DEVICE_HYDROMET_2026-09-06.md · Independent primary-source research, no central edits.
2026-09-06T10:36:44.8863588Z · emf scout · CLAIM research/02-senses/DEVICE_EMF_2026-09-06.md · Independent primary-source research, no central edits.
2026-09-06T10:58:22.3525317Z · Codex coordinator · CLAIM research/07-legal/DEVICE_DATA_LEGAL_SORT_2026-09-06.md; research/08-provenance/CORRECTIONS.md; tools/build_provenance_index.py · User steering: continue existing legal sorting; clarify access signals versus rights, no blanket public clearance.
2026-09-06T11:12Z · emf scout · CLAIM research/audit_fixed21_20260906.py · Gzip portability follow-up; original evidence remains unchanged.
2026-09-06T11:15:22.1159254Z · procurement scout · DONE research/02-senses/DEVICE_PROCUREMENT_2026-09-06.md · Accepted; independent summary/BCE and index/verdict review complete; released.
2026-09-06T11:15:22.1159254Z · hydro scout · DONE research/02-senses/DEVICE_HYDROMET_2026-09-06.md · Accepted; product-scoped legal review integrated; released.
2026-09-06T11:15:22.1159254Z · emf scout · DONE research/02-senses/DEVICE_EMF_2026-09-06.md; research/audit_fixed21_20260906.py · Accepted; 457698-row audit and gzip parity across11 substantive sections; released.
2026-09-06T11:15:22.1159254Z · Codex coordinator · DONE research/02-senses/DEVICE_DATA_DISCOVERY_2026-09-06.md; research/07-legal/DEVICE_DATA_LEGAL_SORT_2026-09-06.md; research/_trail/DEVICE_DISCOVERY_BOARD_2026-09-06.md; research/SOURCE_REGISTRY.json; research/README.md; README.md; research/08-provenance/LEDGER.jsonl; research/08-provenance/INDEX.md; research/08-provenance/CORRECTIONS.md; tools/build_provenance_index.py; KNOWLEDGE.md; LOG.md · 186 unique records, eight reviews/five groups,44 tests and stored INTEGRATION_QA; original evidence retained; local checkpoint follows.
2026-09-06T11:15:22.1159254Z · Codex coordinator · RELEASE svemir_kit.json · Helper absent; no kit state modified.

2026-09-06T11:25:32.762004+00:00 · Codex coordinator · CLAIM research/02-senses/DEVICE_FOLLOWUP_2026-09-06.md; research/07-legal/DEVICE_FOLLOWUP_LEGAL_2026-09-06.md; research/_trail/DEVICE_FOLLOWUP_BOARD_2026-09-06.md; research/SOURCE_REGISTRY.json; research/README.md; README.md; research/08-provenance/LEDGER.jsonl; research/08-provenance/INDEX.md; research/08-provenance/CORRECTIONS.md; KNOWLEDGE.md; LOG.md · User authorized continued device/data discovery with legal sorting; disjoint scout drafts in writable workspace.
2026-09-06T11:57:12.873356+00:00 · Codex coordinator · CLAIM research/02-senses/DEVICE_FOLLOWUP_2026-09-06.md; research/07-legal/DEVICE_FOLLOWUP_LEGAL_2026-09-06.md; research/02-senses/DEVICE_FOLLOWUP_EMF_2026-09-06.md; research/02-senses/ACTRIS_PRODUCT_2026-09-06.md; research/02-senses/PLOVPUT_BULLETIN_2026-09-06.md; research/02-senses/WEBASOOP_DATA_2026-09-06.md; research/SOURCE_REGISTRY.json; README.md; research/README.md; tools/build_provenance_index.py; research/_trail/DEVICE_FOLLOWUP_METADATA_PLAN.json; research/_trail/DEVICE_FOLLOWUP_WEBASOOP_PLAN.json; research/_trail/DEVICE_FOLLOWUP_COLLECTION_METHOD.txt · Reviewed follow-up integration; original evidence immutable.

2026-09-06T12:06:26.397522+00:00 · Codex coordinator · CLAIM TEAMWORK.md; research\_trail\RICH_CONTEXT_BOARD_2026-09-06.json; research\01-programme\ROOM_PROMPT_DOMACI_2026-09-06.md; research\01-programme\ROOM_PROMPT_KOMPARATIVNI_2026-09-06.md · User requests two room prompts and rich local/international literature research.

2026-09-06T12:20:20.715686+00:00 · Codex coordinator · CLAIM research/04-bibliography/LITERATURE_GROUND_EMF_2026-09-06.md; research/04-bibliography/LITERATURE_ENVIRONMENT_2026-09-06.md; research/04-bibliography/LITERATURE_INFRASTRUCTURE_2026-09-06.md; research/04-bibliography/LITERATURE_THEORY_METHODS_2026-09-06.md; research/04-bibliography/BIBLIOGRAPHY_SENSING_CONTEXT_2026-09-06.md; research/02-senses/SENSES_CONTEXT_MAP_2026-09-06.md; research/02-senses/GROUND_STRUCTURES_2026-09-06.md; research/02-senses/URBAN_ENVIRONMENT_2026-09-06.md; research/02-senses/INFRASTRUCTURE_2026-09-06.md; research/_trail/LITERATURE_CONTEXT_REVIEW_2026-09-06.json · Integrate reviewed native drafts, distinct citation count, sense map and primary-source corrections.

2026-09-06T12:22:10.304650+00:00 · Codex coordinator · DONE device follow-up, bibliography supplement, senses map, two room prompt packets and integration/index files · 188 unique source records,32 distinct works,29 manifest file hashes verified,44 tests passed,316 local links checked; original evidence unchanged. Native workers released. External tasks ready, startup not observed.

2026-09-06T12:30:22.818620+00:00 · Codex coordinator · CLAIM research/02-senses/CURRENT_PRODUCTS_2026-09-06.md; research/07-legal/CURRENT_PRODUCTS_LEGAL_2026-09-06.md; research/04-bibliography/SENSORY_ECOLOGY_LITERATURE_2026-09-06.md; research/_trail/CURRENT_PRODUCTS_BOARD_2026-09-06.md; research/SOURCE_REGISTRY.json; research/README.md; README.md; research/08-provenance/LEDGER.jsonl; research/08-provenance/INDEX.md; KNOWLEDGE.md; LOG.md · User requests further device/data/literature discovery. Reserve S192 for a distinct RHMZ groundwater product after exact-route capture; no external room ownership taken.

2026-09-06T12:45:44.853927+00:00 · Codex coordinator · CLAIM research/02-senses/CURRENT_PRODUCTS_2026-09-06.md; research/07-legal/CURRENT_PRODUCTS_LEGAL_2026-09-06.md; research/04-bibliography/SENSORY_ECOLOGY_LITERATURE_2026-09-06.md; research/02-senses/GROUND_CURRENT_PRODUCTS_2026-09-06.md; research/02-senses/ADA_DATA_ACCESS_2026-09-06.md; research/_trail/ADA_DATA_ACCESS_2026-09-06.json; research/_trail/BORCA_QA_REVIEW_2026-09-06.json; research/_trail/CURRENT_PRODUCTS_DATACITE_PLAN_2026-09-06.json; research/_trail/CURRENT_PRODUCTS_METADATA_RECEIPTS_PLAN_2026-09-06.json; research/_trail/CURRENT_PRODUCTS_GROUNDWATER_PLAN_2026-09-06.json; research/_trail/CURRENT_PRODUCTS_COLLECTION_METHOD_2026-09-06.txt; research/_trail/CURRENT_PRODUCTS_INTEGRATION_QA_2026-09-06.json · Review and integrate immutable receipts and bounded native reports; no external task ownership change.

2026-09-06T12:47:38.997963+00:00 · Codex coordinator · RELEASE current-products continuation claims after integrated reports and successful44-test suite; exact QA and selective local commit complete this bounded checkpoint. External room scopes remain assigned/unstarted.

2026-09-06T17:39:50.124537+00:00 · Codex coordinator · CLAIM research/06-paper/rad_draft.md; research/06-paper/BEOPS_IOT_EVIDENCE_MAP_2026-09-06.md; research/06-paper/PAPER_STRUCTURE_2026-09-06.md; research/06-paper/PAPER_METHODS_AUDIT_2026-09-06.md; research/06-paper/PAPER_VENUE_COMPARATORS_2026-09-06.md; research/06-paper/PAPER_TABLES_2026-09-06.md; research/06-paper/figures/; research/06-paper/output/; research/07-legal/PAPER_LEGAL_SCOPE_2026-09-06.md; research/_trail/PAPER_REFRAME_BOARD_2026-09-06.md; research/_trail/PAPER_REGISTRY_CODING_2026-09-06.json; research/_trail/PAPER_METHODS_EVIDENCE_2026-09-06.json; research/_trail/PAPER_QA_2026-09-06.json; research/README.md; README.md; KNOWLEDGE.md; LOG.md · Semir explicitly reframes manuscript as a state-of-IoT/public-data evidence map with verified search methods, legal discussion, comparisons, tables and figures. Previous manuscript retained in git and marked superseded only after replacement exists. Native lanes own CWD drafts; no source collection or external submission.

2026-09-06T17:52:54.675895+00:00 · Codex coordinator · SCOPE CORRECTION / RELEASE unused claims: research/06-paper/rad_draft.md; research/06-paper/BEOPS_IOT_EVIDENCE_MAP_2026-09-06.md; research/06-paper/figures/; research/06-paper/output/. Semir explicitly requests no manuscript yet. Old manuscript stays byte-identical. CLAIM research/06-paper/PRE_PAPER_URBAN_INTELLIGENCE_2026-09-06.md; research/06-paper/RESEARCH_ATLAS_2026-09-06.md; research/06-paper/URBAN_INTELLIGENCE_SYSTEM_OUTLINE_2026-09-06.md. Existing support/index/audit claims continue. Output is organization, themes and choices for discussion; urban intelligence for design/planning is the frame, IoT a secondary input dimension.

2026-09-06T18:03:05.074139+00:00 · Codex coordinator · CLAIM research/_trail/PAPER_CODING_DECISIONS_2026-09-06.psv; research/build_paper_registry_coding_20260906.ps1. Preserve explicit AI-agent decisions and reproducible count builder as support for the pre-paper atlas; no new source decisions in the original registry.

2026-09-06T18:06:32.451291+00:00 · Codex coordinator · RELEASE all pre-paper organization claims from this wave: discussion pack, atlas, structure, system outline, methods/legal/venue/tables, coding recipe/JSON, QA/board, indexes and logs. Three native tasks accepted and released. Old manuscript/registry preserved. External rich-context campaign remains open. Selective local checkpoint follows; no push.

2026-09-06T18:27:28.278456+00:00 · Codex coordinator · CLAIM research/06-paper/PRED_RAD_SR_V2_2026-09-06.md; research/06-paper/STRUKTURA_RADA_SR_V2_2026-09-06.md; research/06-paper/SISTEM_URBANE_INTELIGENCIJE_SR_2026-09-06.md; research/06-paper/ATLAS_IZVORA_SR_2026-09-06.md; research/06-paper/METODOLOGIJA_I_USLOVI_SR_2026-09-06.md; research/07-legal/PRAVNI_OKVIR_PRED_RAD_SR_2026-09-06.md; research/04-bibliography/DOPUNA_LITERATURE_SR_V2_2026-09-06.md; research/04-bibliography/PLANIRANJE_LITERATURA_SR_2026-09-06.md; research/04-bibliography/BEOGRAD_LITERATURA_SR_2026-09-06.md; research/04-bibliography/SISTEM_LITERATURA_SR_2026-09-06.md; research/_trail/PRED_RAD_SR_WAVE7_BOARD.json; research/_trail/PRED_RAD_SR_WAVE7_SEARCH.json; research/_trail/PRED_RAD_SR_WAVE7_QA.json; research/_trail/PRED_RAD_SR_WAVE7_ATLAS_TRANSLATION.json; research/README.md; README.md; KNOWLEDGE.md; LOG.md · User requests one more literature/gap-review wave and Serbian discussion material now, eventual bilingual edition later. This explicit request authorizes Serbian artifacts despite the default public-English convention. No manuscript, original registry or previous English-pack edits. Native lanes draft separately in CWD wave7; coordinator owns integration.

2026-09-06T18:41:34.827664+00:00 · Codex coordinator · CLAIM research/06-paper/UVOD_PROVERENE_PRAKSE_SR_2026-09-06.md · User explicitly adds introductory verified institutional/group practice and established-vs-experimental positioning. emf owns CWD practices draft; coordinator integrates.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/06-paper/PRED_RAD_SR_V2_2026-09-06.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/06-paper/STRUKTURA_RADA_SR_V2_2026-09-06.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/06-paper/SISTEM_URBANE_INTELIGENCIJE_SR_2026-09-06.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/06-paper/ATLAS_IZVORA_SR_2026-09-06.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/06-paper/METODOLOGIJA_I_USLOVI_SR_2026-09-06.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/07-legal/PRAVNI_OKVIR_PRED_RAD_SR_2026-09-06.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/04-bibliography/DOPUNA_LITERATURE_SR_V2_2026-09-06.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/04-bibliography/PLANIRANJE_LITERATURA_SR_2026-09-06.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/04-bibliography/BEOGRAD_LITERATURA_SR_2026-09-06.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/04-bibliography/SISTEM_LITERATURA_SR_2026-09-06.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/_trail/PRED_RAD_SR_WAVE7_BOARD.json · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/_trail/PRED_RAD_SR_WAVE7_SEARCH.json · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/_trail/PRED_RAD_SR_WAVE7_QA.json · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/_trail/PRED_RAD_SR_WAVE7_ATLAS_TRANSLATION.json · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/README.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE README.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE KNOWLEDGE.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE LOG.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-06T19:00:20.951232+00:00 · BEOPS Coordinator · DONE research/06-paper/UVOD_PROVERENE_PRAKSE_SR_2026-09-06.md · Bounded Serbian wave integrated and reviewed; QA record,189-record preservation and npm test44/44. Claim released.

2026-09-08T20:14Z · claude-cowork · CLAIM research/_trail/PRESEK_2026-09-08_SPOLJNI_PREGLED.md; research/_trail/SPOLJNI_PREGLED_2026-09-08_ISTRAZIVANJE.md; tools/build_provenance_index.py; research/08-provenance/INDEX.md; research/08-provenance/CORRECTIONS.md; KNOWLEDGE.md; LOG.md; research/README.md · external state review at Semir's request; fix of provenance index false refusals (C-010); record of zombie task (C-011)
2026-09-08T20:14Z · claude-cowork · DONE research/_trail/PRESEK_2026-09-08_SPOLJNI_PREGLED.md; research/_trail/SPOLJNI_PREGLED_2026-09-08_ISTRAZIVANJE.md; tools/build_provenance_index.py; research/08-provenance/INDEX.md; research/08-provenance/CORRECTIONS.md; KNOWLEDGE.md; LOG.md; research/README.md · index diff = 3 rows exactly, npm test 44/44, Beops_OBS001 deleted and verified by schtasks /query

2026-09-08T21:31Z · claude-cowork · CLAIM tools/collect_daemon.py; tools/collect_tick.bat; tools/register_collect_task.ps1; tools/organ_news.py; tools/publish_github.ps1; research/COLLECTORS.json; research/ORGANS.json; research/test_collect_daemon.py; research/test_organ_news.py; research/05-design/studies/traka-live.html; research/05-design/studies/monolog-puls.html; research/06-paper/BEOPS_WORKING_DOCUMENT_v1_2026-09-09.pdf; LICENSE.md; README.md; .gitignore; research/README.md · live collector, first organ, two studies, licence, bilingual README, working document v1
2026-09-08T21:31Z · claude-cowork · DONE tools/collect_daemon.py; tools/collect_tick.bat; tools/register_collect_task.ps1; tools/organ_news.py; tools/publish_github.ps1; research/COLLECTORS.json; research/ORGANS.json; research/test_collect_daemon.py; research/test_organ_news.py; research/05-design/studies/traka-live.html; research/05-design/studies/monolog-puls.html; research/06-paper/BEOPS_WORKING_DOCUMENT_v1_2026-09-09.pdf; LICENSE.md; README.md; .gitignore; research/README.md · Beops_Collect verified firing (S4U); npm test 75 suites; C-012 recorded; export script for github.com/3esign/beops
2026-09-11T04:41:37.8762812Z · Codex audit · CLAIM research/_trail/AUDIT_ORDER_2026-09-11.md; research/README.md; LOG.md; KNOWLEDGE.md · User-requested detailed audit; source and running tasks remain under inspection only.
2026-09-11T05:00:58.7519846Z · Codex audit · DONE research/_trail/AUDIT_ORDER_2026-09-11.md; research/README.md; LOG.md; KNOWLEDGE.md · 39 findings (4 P1, 24 P2, 11 P3), evidence package, 519/519 isolated tests, five browser widths; source/runtime and task settings unchanged. Kit metadata updated only by knowledge recorder; nextMove preserved as audited.
2026-09-11T05:59:51.6059624Z · Codex deep audit · CLAIM research/_trail/AUDIT_DEEP_2026-09-11.md; research/_trail/audit-deep-20260911/; research/README.md; LOG.md; KNOWLEDGE.md; svemir_kit.json · Fresh systematic source/data/runtime audit and executable remediation plan at user request. No production repairs or publication in this scope.
2026-09-11T06:51:41.979757+00:00 · Codex deep audit · DONE research/_trail/AUDIT_DEEP_2026-09-11.md; research/_trail/audit-deep-20260911/; research/README.md; LOG.md; KNOWLEDGE.md; svemir_kit.json · Report and evidence present; 63 open findings, 535/535 final isolated tests, no production fixes claimed. Audit harness incidents disclosed in honest-verdict.
2026-09-11T06:53:58.227354+00:00 · Codex deep audit · CLAIM research/_trail/AUDIT_DEEP_2026-09-11.md; research/_trail/audit-deep-20260911/MANIFEST.json; LOG.md; KNOWLEDGE.md; svemir_kit.json · Final audit artifact byte parity with Git checkout, no production changes.
2026-09-11T06:54:38.971053+00:00 · Codex deep audit · DONE research/_trail/AUDIT_DEEP_2026-09-11.md; research/_trail/audit-deep-20260911/MANIFEST.json; LOG.md; KNOWLEDGE.md; svemir_kit.json · Audit report/evidence byte hashes match Git blobs; final correction concerns only manifest line-ending parity.
2026-09-11T09:49:03.0389859Z · Svemir / Codex recovery · CLAIM tools/; research/test_*.py; research/05-design/studies/; research/README.md; research/ORGANS.json; research/COLLECTORS.json; research/RETENTION.json; research/STRUCTURE_CONTRACT.json; research/OPERATIONAL_ORDER_2026-09-11.md; research/_trail/REPAIR_2026-09-11.md; research/_trail/repair-20260911/; public/; package.json; README.md; UPUTSTVO.md; CLAUDE.md; KNOWLEDGE.md; LOG.md; svemir_kit.json · User authorizes implementing the deep-audit remediation. Work in isolated physical repository, preserve raw evidence, validate before controlled application.
2026-09-11T10:15Z · Svemir / Codex recovery · CLAIM research/collect_permitted.py; research/eval_mind_effect.py; research/eval_gate.py; research/08-provenance/INDEX.md; .gitattributes · Shared permission policy and correction tooling; immutable evidence remains untouched.
2026-09-11T10:33:40.4448371Z · Svemir / Codex recovery · CLAIM research/recovery_fixtures.py; research/RECORD_SHAPE.json; research/STATES.json; research/08-provenance/CORRECTIONS.md; .gitignore · Extend recovery scope; these helper/schema files were already edited in isolated work. Correction: the preceding claim used a manually entered 10:15Z; this line uses the system clock.
2026-09-11T10:54:13.6324789Z · Svemir / Codex recovery · CLAIM research/DOCUMENT_STATUS_2026-09-11.json; research/_trail/DOCUMENT_STATUS_2026-09-11.md; research/GATE_SHEET_BLANK.md · Explicit status inventory and current generated evaluation sheet; no old evidence rewritten.
2026-09-11T11:20:16.9697878Z · Svemir / Codex recovery · CLAIM src/store.js · Route the explicit legacy prototype through the required workspace HTTP boundary.
