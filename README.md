# BEOPS

Belgrade evidence observatory — a scientific work, not a product and not a service. A new implementation in the Living City Brain / Urban Intelligence collection.

Status: active research instrument, 2026-09-11. The previous application is archival material, not the runtime. The current runtime is the scheduled observatory in `tools/`: collectors, local model organs, guard, watchman, baseline builder and the publisher. A filtered public mirror is published at https://github.com/3esign/beops and the public site is served from GitHub Pages. The public site is the main interface and health surface; after publish, `npm run test:site` checks that the live GitHub Pages HTML matches the public export and that the embedded pages answer. Operational entry point: [research/OPERATIONAL_ORDER_2026-09-11.md](research/OPERATIONAL_ORDER_2026-09-11.md).

The current version connects parking, public events/service changes, environmental observations, static context and permission evidence through existing sources. Forecasts and archival context are separate channels. It must distinguish observations, forecasts, model estimates, and unavailable data. No fabricated camera readings, river levels, city vitality score, face recognition, individual tracking, or unsupported causal claims.

Scope: Beograd only. Urban Intelligence / Living City Brain is the collection, not an expansion to other cities. Pazarac and Novi Pazar are not part of Beops.


## Authors · Autori

prof. dr Darinka Golubović Matić · doc. dr Semir Poturak — authors of a scientific paper prepared for the conference “Creating sustainable commUNiTy” at University Union – Nikola Tesla, Belgrade. They teach at that university; this work is theirs, runs on their own equipment, is non-commercial, and does not speak for the institution or bind it. With **Svemir** (the authors' local AI infrastructure) as a verified contributor at the authors' request — contributor, not author; project-local AI work is recorded in `LOG.md`, `KNOWLEDGE.md` and git history. Licence: [MIT for code, CC BY 4.0 for documents](LICENSE.md). Public mirror: https://github.com/3esign/beops (export of the local repository without the captured evidence; see `tools/publish_github.ps1`).

## How it works · Kako radi

**EN.** Every five minutes a scheduled task on the authors' own PC runs `tools/collect_daemon.py tick`. It reads `research/COLLECTORS.json`, and for every source that is due it first checks the permission ledger (`research/08-provenance/LEDGER.jsonl` — the source's own robots.txt, headers and licence page, stored with hashes). Only a permitted source is fetched, through the operating system's verified TLS, identifying honestly as `Beops-Research-Collect/1.0`. Every value is stored with three times — measured (if the source says), published, received — a missing value is `null`, never zero; nothing is filled or forecast. Receipts are never overwritten. Other scheduled tasks run the local model organs, watch liveness, rebuild baseline/context layers, guard permission invariants and publish the filtered mirror. The rows feed studies (`research/05-design/studies/traka-live.html`, `monolog-puls.html`) and organs — small local models registered in `research/ORGANS.json` whose every sentence is marked as model-derived. Rules: [CONTRIBUTING.md](CONTRIBUTING.md). Proof of permission: [research/08-provenance/INDEX.md](research/08-provenance/INDEX.md). Situation: [research/OPERATIONAL_ORDER_2026-09-11.md](research/OPERATIONAL_ORDER_2026-09-11.md).

**SR.** Svakih pet minuta zakazani zadatak na jednom računaru autora pokreće `tools/collect_daemon.py tick`. On čita `research/COLLECTORS.json` i za svaki izvor koji je na redu prvo proveri knjigu dozvola (`research/08-provenance/LEDGER.jsonl` — robots.txt, zaglavlja i stranica licence samog izvora, sačuvani sa hešovima). Samo dozvoljen izvor se čita, kroz proveren TLS operativnog sistema, uz pošteno predstavljanje kao `Beops-Research-Collect/1.0`. Svaka vrednost se čuva sa tri vremena — izmereno (ako izvor kaže), objavljeno, primljeno — nedostajuća vrednost je `null`, nikad nula; ništa se ne popunjava niti prognozira. Priznanice se nikad ne prepisuju. Drugi zakazani zadaci pokreću lokalne modele, čuvaju ritam, grade osnovne slojeve, proveravaju dozvole i objavljuju filtrirani javni mirror. Redovi hrane studije (`research/05-design/studies/traka-live.html`, `monolog-puls.html`) i organe — male lokalne modele upisane u `research/ORGANS.json`, čija je svaka rečenica označena kao izvedena modelom. Pravila: [CONTRIBUTING.md](CONTRIBUTING.md). Dokaz dozvole: [research/08-provenance/INDEX.md](research/08-provenance/INDEX.md).

## Working here

Many minds work in this repository. **[CONTRIBUTING.md](CONTRIBUTING.md)** is the system of order:
claim before you write, where each kind of file belongs, the status line every document opens with,
what may never be edited, and what a number is allowed to claim. **[CLAIMS.md](CLAIMS.md)** is who is
writing what right now. **[research/STRUCTURE_CONTRACT_2026-09-11.md](research/STRUCTURE_CONTRACT_2026-09-11.md)**
says what is source, proof, generated public state, private audit and live memory. **[research/README.md](research/README.md)** is the index of every research
document and which one wins when two disagree.

## Research Dossier

Current paper direction: [pre-paper v5](research/06-paper/PRE_PAPER_v5_2026-09-10.md), with the [statistical collaboration note](research/06-paper/STATISTICS_COLLABORATION_2026-09-10.md), [stability review](research/STABILITY_REVIEW_2026-09-10.md) and [decision ledger](research/DECISIONS.md). It supersedes the Serbian V2 discussion pack, v3/v4 drafts and their addenda as the current discussion entry. The older [Serbian pre-paper V2](research/06-paper/PRED_RAD_SR_V2_2026-09-06.md), [earlier English pack](research/06-paper/PRE_PAPER_URBAN_INTELLIGENCE_2026-09-06.md) and [all189 source atlas](research/06-paper/ATLAS_IZVORA_SR_2026-09-06.md) are preserved history, not synchronized current texts.

Latest continuation: [Groundwater, exact Ada metadata and sensory ecology](research/02-senses/CURRENT_PRODUCTS_2026-09-06.md), with [legal scope](research/07-legal/CURRENT_PRODUCTS_LEGAL_2026-09-06.md) and [eight additional literature/practice records](research/04-bibliography/SENSORY_ECOLOGY_LITERATURE_2026-09-06.md).

Latest follow-up: [Recent EMF, individual lidar products and Ada Marina datasets](research/02-senses/DEVICE_FOLLOWUP_2026-09-06.md). [Product-specific legal review](research/07-legal/DEVICE_FOLLOWUP_LEGAL_2026-09-06.md) separates licence, actual access and publication.

Previous discovery: [Devices and data, 2026-09-06](research/02-senses/DEVICE_DATA_DISCOVERY_2026-09-06.md) — six new source records, historical Belgrade EMF archives, dated Vinca CEMS results and BGD lidar metadata. [Legal sorting](research/07-legal/DEVICE_DATA_LEGAL_SORT_2026-09-06.md) distinguishes access evidence from reuse and publication rights.

Earlier situation review: [2026-09-05 afternoon](research/_trail/PRESEK_2026-09-05_POPODNE.md) — repository/pilot defects, conference dates and the work then remaining.

Latest bibliography: [93 verified entries in four parts](research/04-bibliography/BIBLIOGRAPHY_2026-09-05.md) — theory and ontology of the city (including the SOSA/SSN, O&M, PROV-O and QUDT observation standards); urban informatics, city sensing and the critical smart-city literature; the historical problems of big data and what recent AI actually offers; urban digital twins, city brains and comparative practice. Every entry carries an APA reference, what was opened to verify it, the claim it supports, and the concrete change it makes to BEOPS. Two entries are flagged as unverified at the primary source and must not carry weight until checked.

Latest senses round: [New senses, round 2](research/02-senses/NOVA_CULA_RUNDA2_2026-09-05.md) — 28 candidate sources opened at their own endpoints, ten proposed for the registry as S39–S48, two confirmed negative findings, a twelve-medium typology of urban senses with a named absence per medium, and a precedent table for ten categories of dormant municipal technology.

Conference: [Late-submission enquiry, drafted and not sent](research/06-paper/conference/LATE_SUBMISSION_EMAIL.md). The call's own Important Dates are 01.05.2026 for abstracts and **20.08.2026 for full manuscripts**; the conference is on-line on 25.09.2026. The manuscript deadline has passed and no acceptance is assumed.


Latest detailed program: [Senses, specialist models and useful city pulses](research/01-programme/PLAN_CULA_MODELI_2026-09-05.md), with [64 search seeds](research/01-programme/PRETRAGA_KEYWORDS_2026-09-05.md) and [the expanded model/provider audit](research/03-models/KATALOG_MODELA_I_PROVAJDERA_2026-09-05.md). It elaborates the existing work program; it is not a claim that all experiments have run.

Latest scope: all Belgrade -> larger urban areas -> broad zones, stopping before micro-level. Wider krug dvojke is one selectable focus. One spatial filter applies across domains. Connect existing sources and hosted geographic services; do not build an internal city index or geocoder. Start multiple domains together, not only weather.

- [Zones and external linking](research/01-programme/ZONE_I_POVEZIVANJE.md).
- [New multidomain evidence](research/02-senses/VISE_DOMENA_2026-09-05.md).
- [OBS-001: separate 10K race observation](research/observations/10k-2026-09-05/PROTOKOL.md), on the New Belgrade/Zemun side.

- [Living footprint of Belgrade](research/02-senses/ZIVI_OTISAK_BEOGRADA.md): start here; measured reconnaissance findings and research questions.
- [Source registry](research/SOURCE_REGISTRY.json): 215 source records, including archives, catalogues, related routes and coverage gaps. This is not a count of devices or live feeds.
- [Models and literature](research/03-models/MODELI_I_LITERATURA.md): initial ten-model review; the expanded audit above covers 24 HF identities and 23 downloaded cards, no weights or inference-quality claim.
- [Other cities, senses and organs](research/02-senses/DRUGI_GRADOVI_CULA_I_ORGANI.md): comparative examples and transferable experiments.
- [Work program](research/01-programme/RADNI_PROGRAM.md): 65 tasks in 13 themes, dependencies and completion evidence.
- [Pazarac transfer audit](research/_trail/PAZARAC_TRANSFER_AUDIT.md): read-only code findings and transfer boundaries.
- [Probe evidence](research/evidence/): bounded snapshots, not continuous monitoring.

## Work Order

1. Preserve PC and 3esign legacy snapshots with file hashes; extract lessons as text.
2. Verify Creating Sustainable CommUNiTy 2026 dates, author instructions, and submission status.
3. Define layered city pulses and controlled comparisons in [Research Protocol](research/01-programme/PULSE_RESEARCH_PROTOCOL.md).
4. Audit Belgrade source coverage, update rhythms, reuse conditions and historical vintages before building collectors.
5. Catalog small specialist models with input/output contracts and evaluation gates. Discovery is not installation, and installation is not proof of accuracy.
6. Maintain the public site as the main surface while keeping source, proof, generated state and live memory separate; use `npm run test:site` after publish to verify the live interface.
7. Build an annotated benchmark and prepare the manuscript from measured results. Conference submission remains a separate decision.

Public deployment has occurred through the filtered mirror and GitHub Pages. Conference submission is still a separate decision and is not assumed here.

## Latest sensing context

[32-work literature extension](research/04-bibliography/BIBLIOGRAPHY_SENSING_CONTEXT_2026-09-06.md), [map of possible senses](research/02-senses/SENSES_CONTEXT_MAP_2026-09-06.md), and [two room handoff packets](TEAMWORK.md). Local campaigns, simulations, current-looking pages and inaccessible data remain distinct.
