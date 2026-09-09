Status: current
Date: 2026-09-06
Author: Codex coordinator, with ground/EMF, environment and infrastructure research agents

# Belgrade sensing: literature, devices and data

This additive supplement connects **32 distinct works** to the question of how we can observe Belgrade: **24 local studies or method applications, plus eight international theoretical/methodological works**. The four lane reports contain33 entries because the 2018 Gazela/Ada-approach paper was independently found twice; it is counted once here. Follow-up candidates are outside these totals. The24 local works include historical measurement campaigns, operating-system observations, a model validation and a laboratory/simulated traffic scenario; they are not24 live deployments.

The existing[93-entry wide bibliography](BIBLIOGRAPHY_2026-09-05.md) remains the foundation for urban theory, observation ontology, provenance, critical urban informatics and comparative observatories. This supplement does not replace it or the separate[experiment bibliography](BIBLIOGRAFIJA_2026-09-05.md). Exact DOI/title comparisons avoid recounting those earlier entries. Thirty-two works do not constitute a complete literature census.

## Read through the questions, not only the references

| Question | Strong local evidence | What it changes in the research |
|---|---|---|
| How does the ground move? | BEOG daily GNSS coordinates; Umka permanent GNSS, repeat geodesy, Sentinel-1 and UAV work | A point receiver, radar line-of-sight displacement and surveyed surface have different spatial support. Relocation and vegetation affect what can be inferred. |
| How does a structure respond? | Gazela and Ada north-approach load tests | Temporary instrumentation can yield valuable data without being a permanent city sensor network. |
| What surrounds us electromagnetically? | Seven-site RF study; Science Park selective monitoring; RATEL drive tests; school50Hz magnetic-field mitigation; foreign vehicle campaign through Belgrade | RF electric field and low-frequency magnetic induction are different properties. Cabin/roof/fixed-probe placement and time of passage matter. |
| What is in the air, above the air station and around a street? | Local low-cost sensor calibration, BARLI QA, eclipse multi-instrument experiment, Kestrel microclimates, historical thermal indices | Aerosol height profiles, street-level conditions and modeled thermal comfort cannot be merged as one interchangeable air reading. |
| What biological and chemical traces exist? | Bee genetic accessions, historical river RNA sampling and ICP-MS across five water plants | The sensing system includes sample collection and laboratory processing. A retained sample can expose properties absent from its original monitoring purpose. |
| What does infrastructure already know about its operation? | Pupin PV/SCADA, Voždovac CHP operational aggregates, rain/traffic observations, park-and-ride fieldwork | Papers reveal observation systems hidden behind utility operations and field campaigns. Public data access must be checked separately. |
| What can become a sense without a conventional sensor portal? | Foreign microwave-link rainfall, fibre DAS, air-filter eDNA; Gabrys and Offenhuber; soundscape ecology | Expand the device search to physical traces, repurposed infrastructure and maintained sensing practices. These are proposed Belgrade search directions, not local deployment claims. |

## Annotated source dossiers

Each dossier records the primary citation, reading depth, place, device/procedure, observation interval, dataset pointer, article/data rights and limits. Full-text sections were read selectively where available; “full text” never means the results were reproduced. Indexed primary excerpts, author copies and abstract-only evidence are explicitly identified.

- **[Ground and electromagnetic fields](LITERATURE_GROUND_EMF_2026-09-06.md)** — nine entries; BEOG, Umka, bridges and five RF/magnetic-field studies. The bridge entry is a duplicate of infrastructure6 and is counted only there in the combined tally.
- **[Atmosphere, sound, biology and water](LITERATURE_ENVIRONMENT_2026-09-06.md)** — nine entries; seven with inspected methods/full-text sections, including indexed primary sections, and two with abstract/introduction limits. Three further leads remain uncounted.
- **[Energy, mobility and structures](LITERATURE_INFRASTRUCTURE_2026-09-06.md)** — seven entries; six with inspected full-text evidence and one abstract/excerpt record. One conference paper has no verified DOI. Local simulations and human fieldwork remain distinct from electronic deployments.
- **[International theory and new sensing methods](LITERATURE_THEORY_METHODS_2026-09-06.md)** — eight works, comprising three books and five articles. Primarily bibliographic/abstract-level review, with no full-book reading claimed.
- **[What can become a sense?](../02-senses/SENSES_CONTEXT_MAP_2026-09-06.md)** — the observation-chain map and the difference between a current signal, a recent dated window, a historical campaign and an instrument whose output is unavailable.

## Concrete data trails worth following

| Trail | Present evidence | Exact unresolved step |
|---|---|---|
| RATEL Science Park record 168 | Already captured 1,681 electric-field values with six-minute labels through 06September2026 at 00:00 | Timezone and current lag; chart reuse scope; no invented join to archive21. See[device follow-up](../02-senses/DEVICE_FOLLOWUP_2026-09-06.md). |
| BGD/BARLI optical products | Already captured 39 product metadata records for May2020; persistent identifier and a documented single-product download route | Raw legacy-product licence remains unresolved; no NetCDF downloaded. |
| Ada Marina aerosol chemistry and particle properties | Nine exact dataset DOI families mapped from the catalogue; oneDTT record hasCCBY4.0 with restricted files | Review each actual resource separately; resolve authorized access without treating the article licence as a raw-file grant. |
| BEOG/Umka deformation | Papers identifyNGL coordinates and local GNSS/InSAR campaigns | Exact currentBEOG file/terms; any public local processedUmka product; no assumption thatEGMS coversSerbia. |
| Urban bee genetics | Paper givesGenBank ON187787–ON187868 | Check exact records and repository terms; avoid private hive-location reuse. |
| Belgrade noise study | Published2019 campaign and a printed historical API | Opaque access component redacted; endpoint untested, current operation and rights unresolved. |
| Pupin solar plant |2014 SCADA data described; paper names an oldPowerWeb route with OCR ambiguity | Resolve the documented citation before a bounded exact-route access review. No rawIP endpoint probing performed. |
| Voždovac CHP | PublisherTables1–2 contain monthly2021 and 2022 operational aggregates | Separate article rights from underlying operational data and any present telemetry. |
| Borča groundwater | RHMZ page currently displays last-ten daily labels, most recent06.09.; station9NP163 | Year, clock and level convention unresolved. A web review is not an immutable raw capture or permission to poll. |

These are differently mature trails, not a list of equally open feeds. Legal sorting remains in the[existing framework](../07-legal/COLLECTION_LEGAL_FRAME.md),[source-specific follow-up](../07-legal/DEVICE_FOLLOWUP_LEGAL_2026-09-06.md) and[provenance index](../08-provenance/INDEX.md).

## Corrections and implications from reading methods

**Device capacity is not deployment cadence.** BARLI's2023 paper describes one-minute profile accumulation, but its conclusion still treats regular scheduled monitoring and automation as future work. The coordinator independently checked its PDF: the telecover example is dated27April2020, whereas dates of all QA procedures were not established. This is compatible with historicalACTRIS products and does not prove a continuous2026 feed.

**A model test can use Belgrade without observing Belgrade.** The2026 edge-computing study combines SUMO-generated local traffic with separately sourced video on a display. It supports a method/hardware evaluation, not a deployedBelgrade traffic service.

**Primary sources can contain ambiguous labels.** The2016TELFOR RF methods have an apparent frequency-band naming inconsistency. Its short quoted clause and location are preserved in the ground dossier; no silent relabeling of measurements is performed.

**Service absence does not mean the technique cannot observe the city.** EGMS's stated product footprint excludesSerbia; Umka researchers nonetheless processed localSentinel-1 scenes. A continental service and a local research product are distinct access routes.

**Laboratory terminology is not delivery latency.** RT-qPCR or “real-timePCR” names a measurement method. A sample date, assay date and publication date must remain separate. Historic molecular observations do not establish today's public-health conditions.

## Search method and remaining coverage

This was a targeted multilingual evidence-mapping pass, not a registered systematic review. Searches usedBelgrade/Beograd/Београд plus localities, instruments, phenomena and exact titles/DOIs, followed by publisher, institution, operator and author-hosted verification. The three agents worked disjoint physical domains and compared against existing bibliographies. The coordinator checked all reports, reconciled the bridge duplicate, and independently opened primaryBARLI, CHP, water-chemistry, traffic, bridge, GNSS and RF sources, plus the eight international references at their stated reading levels. Individual records retain any unavailable full text and unverified data rights.

Missing coverage remains substantial: domestic theses and grey literature; sensory anthropology and artistic practices; ecology/phenology and local bioacoustics; riverbed and soil chemistry archives; infrastructure maintenance histories; comparative Balkan/postsocialist cities; unavailable or discontinued datasets; and sustained present-day device operation. Two prepared room agents have those complementary assignments:

- [Domestic repositories, theses and institutional archives](../01-programme/ROOM_PROMPT_DOMACI_2026-09-06.md).
- [International comparative methods and sensing theory](../01-programme/ROOM_PROMPT_KOMPARATIVNI_2026-09-06.md).

Their real queue tasks and ownership appear in the[room board](../_trail/RICH_CONTEXT_BOARD_2026-09-06.json). Preparing prompts does not prove the external agents started. Startup/ACK was not observed at this checkpoint.

## Honest verdict

The delivered result is a32-work annotated extension, a map of sensing possibilities, three broader device reconnaissance reports and two executable room handoff packets. The current source registry remains 188 access/source records; bibliography entries have not been inflated into sensor IDs. No new live public feed was established by the literature pass, and no underlying dataset, audio, household reading or personal record was collected. Previous raw evidence was not modified. Offline tests passed44/44; integrity/link checks and the absent project-kit helper are recorded in the integration QA. The two external assignments remain ready for startup and later review; this checkpoint does not claim completion of their future work.
