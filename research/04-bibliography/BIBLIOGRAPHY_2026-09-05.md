# BEOPS — Bibliography

**Compiled 2026-09-05. Ninety-three entries in four sections, each verified at a primary source.**

## Why this file exists, and what it is not

Semir asked for "all relevant, quality scientific papers" across a deliberately very wide arc:
theory and ontology of the city → urban planning and development → computer science and the
joining/integration of these → new AI technologies as an answer to the historical problems of
big data collection, processing, evaluation and synthesis.

That arc is not as wide as it sounds. The conference this bibliography serves — *The Sixth
International Conference on Sustainable Environment and Technologies, "Creating sustainable
commUNiTy", 25.09.2026, Belgrade* — has two tracks that between them name almost every step of
it: **Sustainable construction, architecture and urbanism** (sensing architecture; monitoring;
transportation and mobility; participative urban design and *space semiotics*; emergencies,
disasters, epidemics) and **The role of IT in sustainable development** (data science and big
data technologies; internet of things; information systems; business intelligence for
decision-making; and, verbatim, **metadata, ontology and semantics**). The arc Semir described
and the call's own topic list are the same arc.

This file is a **working instrument, not a reading list**. BEOPS's standing project rule is that
a paper only earns its place if it changes something concrete — an experiment, a data contract, a
vocabulary, a design decision. So every entry below carries four fields:

- **APA** — the reference exactly as it will appear in the manuscript's reference list, in the
  APA style the conference's author instructions require.
- **Verified** — which page was actually opened and what it confirmed. Where a publisher blocked
  automated access, the entry says so and names the substitute route (institutional repository,
  author-hosted PDF, Crossref registry record). Entries that could not be verified at the primary
  source are marked `UNVERIFIED` or `PARTIAL` and must be re-checked against a library copy before
  being cited load-bearing.
- **Claim it supports** — the one sentence in a BEOPS paper this citation would back.
- **What it changes in BEOPS** — the concrete consequence, or the honest words "framing only".

## How to read it fast

If you have twenty minutes and need the paper's spine, read these nine entries in this order:

1. **[A14] SOSA/SSN** — the standard that already contains the distinction BEOPS was invented to
   protect: `phenomenonTime` vs `resultTime` is *measured now* vs *received now*, formally. This
   is the single most directly implementable citation in the whole file.
2. **[A16] PROV-O** and **[A17] QUDT** — provenance and units as machine-checkable triples rather
   than as project discipline. Together with A14 they turn BEOPS's own hard rules into an existing
   standards stack instead of a house style.
3. **[C01] The Parable of Google Flu** — the canonical measured case of a trusted proxy silently
   diverging from ground truth for over a year, because nobody logged that the upstream algorithm
   had changed 86 times in two months. This is BEOPS's antagonist.
4. **[C05] Robinson, ecological fallacy** and **[C06] MAUP** — the two reasons a zone-level urban
   correlation can be an artefact of the zoning, with a sign flip demonstrated on 1930 census data.
   Every BEOPS pulse is zone-aggregated; these two are not optional.
5. **[B21] de Montjoye, unique in the crowd** — four spatio-temporal points identify 95% of people.
   The quantitative reason BEOPS's "no person-level analysis" rule cannot be satisfied by
   coarsening alone.
6. **[D13] The Ahr valley flood** — 134 of Germany's 190 flood deaths in one valley; the forecast
   existed, the warning did not arrive. The strongest single argument that *observation → forecast
   → delivered → acted upon* are four separately measurable stages, and that a project which
   publishes the first two has not thereby achieved the last two.
7. **[B11] Castell et al.** — laboratory correlation above 0.9 that did not survive contact with
   the field, across 24 identical units. Why an uncalibrated citizen sensor reading is not a
   measurement.
8. **[D22] The European Commission's own INSPIRE evaluation** — after more than a decade, roughly
   half of registered datasets met interoperability conformity, and the evaluators could not say
   who was using them. The antidote to assuming a standard's existence implies a working feed.

## The one paragraph the paper's introduction can be built from

Cities have been instrumented for two decades, and the instruments have mostly not produced
decisions. The digital-twin literature's own proponents place city-scale twins at an unresolved
computational frontier [D01]; the most-cited built twin offers a perception survey rather than a
changed planning decision as its evidence [D03]; the most-resourced municipal twin reports open-data
downloads as its headline impact [D04]; the most famous "city brain" has, as far as this search
could establish, **no independent remeasurement of its own performance claims anywhere in the
literature** [D-Gaps]. Meanwhile the failures that killed people were not sensor failures but
delivery failures [D13, D14]. BEOPS's position follows from that record rather than from ambition:
build no twin, claim no causality, publish the observation and the gap in the observation, and make
the distinction between *measured*, *forecast*, *estimated* and *unavailable* a property of the data
model [A14, A15] rather than a promise in the prose.

## Honest limits of this compilation

- Ninety-three entries were compiled by four parallel verification passes on 2026-09-05. Every
  entry names what was opened. Not every entry reached the publisher's own page: IEEE Xplore, the
  ACM Digital Library, most of ScienceDirect, World Scientific and JSTOR refused automated access,
  and those entries were verified through institutional repositories, author-hosted PDFs or the
  Crossref registry instead — stated per entry.
- Two entries are explicitly flagged as not verified at the primary source: **[C06] Openshaw &
  Taylor (MAUP)**, a 1979 book chapter that exists nowhere fetchable, and **[A03] Norberg-Schulz**,
  whose 1980 publisher record is genuinely ambiguous between Rizzoli and Academy Editions. Neither
  should carry weight in the manuscript until checked against a physical copy.
- **Full texts were not read.** These are verified *records* with verified abstracts and, in many
  cases, verified specific findings — not a systematic review. Any number quoted from these papers
  in the manuscript must be re-checked in the full text first.
- The Gaps sections at the end of each part are not filler. Several of them are findings in their
  own right — most importantly that no independent evaluation of Alibaba's Hangzhou City Brain
  performance claims could be located anywhere, and that neither OpenSky nor RIPE Atlas appears in
  the urban-informatics literature as an urban sensing source at all, which means BEOPS's use of
  them is genuinely novel rather than derivative.

## Companion file — read both, they do not overlap

A second bibliography was written the same afternoon by a parallel Svemir pass:
**`research/BIBLIOGRAFIJA_2026-09-05.md`** (Serbian, 12 entries). It is not a duplicate and
should not be merged away. It is narrower and more recent, and it maps each entry onto BEOPS's
own experiment IDs (E01–E09, OBS-001, S34), which this file does not do. Its unique entries:

- **AUDiTs** — agentic urban digital twins, separating collection / model / orchestration / interaction.
- **UrbanWell** — a benchmark aligning several urban indicators in space and time, with per-indicator error rather than one average. Directly relevant to E03/E04.
- **DynamicVL** — multi-temporal urban understanding and change detection.
- **Akidau et al., The Dataflow Model (VLDB 2015)** — event time vs processing time, windows, late corrections. This is the streaming-systems twin of [A14] SOSA/SSN: the same distinction, arrived at from the data-engineering side rather than the ontology side. Cite both together.
- **Patel et al. (AMT 2024)** — hygroscopic-growth calibration for low-cost PM2.5 sensors. Sharpens [B11] and [B12] here with the humidity mechanism.
- **SONYC-UST-V2** and **DCASE low-complexity acoustic scene classification** — the acoustic medium, which this file names only as a typology gap.
- **SeisBench** — seismic ML benchmarking.
- **Chronos** — time-series foundation model; overlaps part C here, read together.
- **BERTić** and **GLiNER** — BCMS language model and configurable entity extraction. Serbian-language processing is a real BEOPS need that this file does not cover at all.

**Division of labour, so the next mind does not redo either:** this file (`BIBLIOGRAPHY`) is the
wide, verified foundation — theory, ontology, observation standards, the critical smart-city
literature, the big-data failure record, and the comparative evidence on twins and city brains.
The companion (`BIBLIOGRAFIJA`) is the narrow, experiment-bound layer — recent models and
benchmarks tied to named BEOPS experiments. Additions of new *models and benchmarks* go there;
additions of *theory, standards, method and comparative practice* go here.

---

## Section index

| Part | Subject | Entries | Prefix |
|---|---|---|---|
| A | Theory and ontology of the city; observation standards; space semiotics | 20 | `[Axx]` |
| B | Urban informatics, city sensing, and the critical smart-city literature | 24 | `[Bxx]` |
| C | Historical problems of big data, and what recent AI actually offers | 27 | `[Cxx]` |
| D | Urban digital twins, city brains, and comparative practice | 22 | `[Dxx]` |

---



# PART A — Theory and ontology of the city

## BEOPS Bibliography — Section: Theory and Ontology of the City

*Verified references for the "theory and ontology of the city" section of the BEOPS paper (Sustainable Environment and Technologies conference, Belgrade, 25.09.2026). Every entry below was checked against a primary source page (publisher/DOI/standards-body/arXiv) during this session; verification method and any limitation is stated per entry.*

### 1. Foundational urban theory (city as system / information object)

#### [A01] Batty — Cities as Information Systems
**APA:** Batty, M. (2013). *The new science of cities*. MIT Press. https://doi.org/10.7551/mitpress/9399.001.0001
**Verified:** MIT Press Direct's own landing page refused automated fetch (HTTP 403) on every attempt. Confirmed instead via the Crossref API's authoritative registration record for this exact DOI (title, author, publisher "The MIT Press", type "monograph", year 2013 — all matched), cross-checked against MIT Press's bookstore subdomain (ISBN 9780262534567, 2017 paperback reissue) and two independent published book reviews (*Journal of Regional Science*, *Journal of Industrial Ecology*) that both cite the same 2013 hardcover, ISBN 978-0-262-01952-1, 496 pp.
**Claim it supports:** A city can be scientifically modeled as a system of interacting flows and networks (transport, people, information) rather than as a single static form, which is the theoretical warrant for treating urban data as many coupled flow-layers.
**What it changes in BEOPS:** Reinforces the "no own city index" rule at the architecture level — justifies keeping BEOPS's "city pulses" as separate, composable flow-layers (parking, transit, air, IoT, OSM changesets) rather than fusing them into one master score or index, since the theory itself treats city-ness as emergent across layers, not resident in one model.

#### [A02] Lefebvre — Production of Space
**APA:** Lefebvre, H. (1991). *The production of space* (D. Nicholson-Smith, Trans.). Blackwell. (Original French work published 1974)
**Verified:** Opened Wiley's own product page and Blackwell's bookshop page directly; both confirm author, translator, publisher (Wiley-Blackwell), and the 1991 English edition date (15 Aug 1991). No DOI exists for this trade edition. The 1974 French original date is secondary-source consensus only (not independently re-verified against a French publisher record this session).
**Claim it supports:** Physical/urban space is socially produced, not a neutral container — what an instrument records is a produced, contested space, not "the city" as such.
**What it changes in BEOPS:** Concrete documentation requirement: each pulse layer must state whose infrastructure/representation it is drawn from (e.g., which operator's parking sensors, whose road-closure feed), because "missing ≠ zero" has a spatial as well as temporal reading — silence from a district may reflect who was never instrumented there, not the absence of an event.

#### [A03] Norberg-Schulz — Genius Loci
**APA:** Norberg-Schulz, C. (1980). *Genius loci: Towards a phenomenology of architecture*. Rizzoli.
**Verified:** Opened WorldCat's library record (OCLC 6666454): Rizzoli, New York, 1980. Note of honesty: a Google Books record for a differently-scanned copy of the same title lists "Academy Editions" (London) as publisher — these appear to be simultaneous US/UK 1980 editions, and I could not adjudicate which is definitive; Rizzoli/New York is the one most consistently cited in the English-language literature found this session.
**Claim it supports:** Place has a qualitative "character" (genius loci) that is not reducible to any metric, so quantified pulses are necessarily partial proxies for lived place-meaning.
**What it changes in BEOPS:** Framing only — grounds the project's own restraint about *not* claiming to represent a place's "identity," and supports treating each pulse as a situated signal about an instrumented aspect of a location, never as a totalizing description of the place itself.

#### [A04] Lynch — Imageability
**APA:** Lynch, K. (1960). *The image of the city*. MIT Press.
**Verified:** MIT Press's own domains (mitpress.mit.edu, direct.mit.edu) blocked automated access. Confirmed via Wikipedia's article and MIT Press's separate bookstore subdomain (ISBN 9780262620017 — though that specific print run is dated 1964 there, the standard paperback reprint). The original 1960 date is independently corroborated by a contemporaneous 1960 book review in *Social Problems* carrying its own DOI (10.2307/798927), confirmed via Crossref.
**Claim it supports:** A city's legibility — paths, edges, districts, nodes, landmarks — is an empirically elicitable property of how people cognitively structure urban space, distinct from its administrative or geometric structure.
**What it changes in BEOPS:** Concrete UX/vocabulary decision: when presenting pulses to citizens, group/label locations using Lynch-type perceptual units (districts, nodes, landmarks) alongside administrative boundaries — directly relevant to the conference's "space semiotics" track, since imageability is itself a semiotic property of urban form.

#### [A05] Alexander, Ishikawa & Silverstein — Pattern Language
**APA:** Alexander, C., Ishikawa, S., & Silverstein, M. (1977). *A pattern language: Towns, buildings, construction*. Oxford University Press.
**Verified:** Opened Oxford University Press's own catalog page directly (title/publisher/1977 confirmed there, though it surfaced only Alexander as author); the full byline (Alexander, Ishikawa, Silverstein, "with" three further contributors) was independently cross-confirmed via the Wellcome Collection library catalog record.
**Claim it supports:** Recurring, named, evidence-based problem/solution pairs at urban scale ("patterns") are a legitimate, reusable unit of city knowledge distinct from raw metrics.
**What it changes in BEOPS:** Suggests a controlled vocabulary for BEOPS's qualitative/narrative layer (documented interventions, regime changes from news) as named, citable "patterns" rather than one-off free text — a real but modest vocabulary-design nudge, not a data-model change.

#### [A06] Hillier & Hanson — Space Syntax
**APA:** Hillier, B., & Hanson, J. (1984). *The social logic of space*. Cambridge University Press. https://doi.org/10.1017/CBO9780511597237
**Verified:** Opened Cambridge Core's own book page directly — confirmed title, authors, publisher, 1984, and the DOI on the publisher's own platform (strongest verification of this set: first-party page, no proxy needed).
**Claim it supports:** The configurational structure of a street network (space syntax measures such as integration/choice) is itself a measurable, stable determinant of movement and land use, independent of any single observation.
**What it changes in BEOPS:** Concrete: justifies computing standard space-syntax measures on Belgrade's OSM-derived street graph as a *structural, derived* covariate against which volatile pulses (parking occupancy, footfall) are interpreted — and gives BEOPS a clean example of a "derived property" that must be labeled as such, not conflated with a live measurement.

### 2. Formal urban ontologies and semantics

#### [A07] CityGML 3.0 (OGC Standard)
**APA:** Open Geospatial Consortium. (2021). *OGC City Geography Markup Language (CityGML) part 1: Conceptual model standard* (OGC 20-010, version 3.0.0; T. H. Kolbe, T. Kutzner, C. S. Smyth, C. Nagel, C. Roensdorf, & C. Heazel, Eds.). https://docs.ogc.org/is/20-010/20-010.html
**Verified:** Opened the standard document directly on the standards body's own site — confirmed exact title, document number, version, approval date (4 June 2021), publication date (13 Sept 2021), full editor list, and its permanent URI (`http://www.opengis.net/doc/IS/CityGML-1/3.0`).
**Claim it supports:** There is an OGC-standardized, versioned conceptual model — with defined levels of detail, feature types, and thematic modules (Transportation, LandUse, CityFurniture, etc.) — for representing city objects semantically, not just geometrically.
**What it changes in BEOPS:** Concrete: if BEOPS ever needs to reference physical city assets (parking structures, stops, sensor mounts) spatially, it should reuse CityGML's typed vocabulary and LoD concept rather than invent its own object schema — a direct, citable way to operationalize "no own city index."

#### [A08] Gröger & Plümer — CityGML Semantics
**APA:** Gröger, G., & Plümer, L. (2012). CityGML – Interoperable semantic 3D city models. *ISPRS Journal of Photogrammetry and Remote Sensing*, *71*, 12–33. https://doi.org/10.1016/j.isprsjprs.2012.04.004
**Verified:** ScienceDirect's own page blocked automated access; confirmed via the Crossref API's authoritative record for this DOI (title, both authors, journal, volume 71, pages 12–33, year 2012 — exact match).
**Claim it supports:** The value of CityGML is specifically in encoding *semantics* (thematic classification, cross-LoD generalization) — a "3D city model" and a "semantic city model" are different things, and the latter is what makes reasoning over city data possible.
**What it changes in BEOPS:** Motivates a specific modeling rule: every BEOPS pulse should carry an explicit semantic type/tag (not just coordinates + value) and should record which granularity/LoD its source implies, to avoid false precision when a citizen-IoT reading is coarser than its map pin suggests.

#### [A09] GeoSPARQL 1.1 (OGC Standard)
**APA:** Open Geospatial Consortium. (2024). *OGC GeoSPARQL — A geographic query language for RDF data* (OGC 22-047r1, version 1.1). https://docs.ogc.org/is/22-047r1/22-047r1.html
**Verified:** Opened the standard directly — confirmed title, version 1.1, OGC as publishing body, document number, approval dates for both v1.0 (27 Jan 2015) and v1.1 (29 Jan 2024), and its `opengis.net` URI.
**Claim it supports:** There is a standard vocabulary and query language for representing and reasoning over geospatial features and topological relations in RDF, designed to interoperate with SOSA/SSN and PROV-O.
**What it changes in BEOPS:** Concrete: if/when BEOPS's pulses are exposed as linked data, "space" (required by the project's own source/time/space/unit/permission rule) should be encoded as a GeoSPARQL `geo:Feature`/`geo:Geometry`, not a bespoke lat/lon pair — making location a queryable, standards-based property rather than free text.

#### [A10] SAREF4CITY (ETSI)
**APA:** ETSI. (2020). *SAREF4CITY: An extension of SAREF for the smart city domain* (ETSI TS 103 410-4 V2.1.1). https://saref.etsi.org/saref4city/v2.1.1/
**Verified:** Opened ETSI's own SAREF ontology portal directly — confirmed title, version 2.1.1, publication date (5 June 2020, last modified 11 Apr 2025), and the formal document number.
**Claim it supports:** A standardized, ETSI-published ontology extension already exists for representing smart-city domain concepts (parking, city objects, events) interoperably with the broader SAREF/IoT ecosystem.
**What it changes in BEOPS:** Concrete: for BEOPS's parking-occupancy and citizen-IoT layers specifically, reusing SAREF4CITY classes instead of inventing project-specific vocabulary gives a documented path to interoperate with any city or vendor system already emitting SAREF-based data.

#### [A11] KM4City Ontology
**APA:** Bellini, P., Benigni, M., Billero, R., Nesi, P., & Rauch, N. (2014). Km4City ontology building vs. data harvesting and cleaning for smart-city services. *Journal of Visual Languages & Computing*, *25*(6), 827–839. https://doi.org/10.1016/j.jvlc.2014.10.023
**Verified:** Opened the paper's own arXiv preprint PDF directly (arXiv:1508.01086), confirming exact title, full five-author byline, and DISIT Lab/University of Florence affiliation. Cross-confirmed the published venue, DOI, volume/issue/pages via the Crossref API record and the Snap4City project's own reference page (ScienceDirect's page itself would not render for automated fetch).
**Claim it supports:** Building a working smart-city knowledge graph from many heterogeneous public sources requires an explicit, published ontology *plus* a documented harvesting/reconciliation pipeline — and this has been done and published at real-city scale before.
**What it changes in BEOPS:** Highly concrete: this is one of the few published precedents for BEOPS's exact task (harvest + reconcile heterogeneous open city data under one ontology). BEOPS's ingestion/reconciliation design can point to this paper's documented algorithms and failure modes instead of re-deriving that step from scratch.

#### [A12] Smart Data Models (FIWARE et al.)
**APA:** Smart Data Models. (n.d.). *Smart Data Models: A global program for open, interoperable smart data models*. FIWARE Foundation, TM Forum, IUDX, & OASC. Retrieved September 5, 2026, from https://smartdatamodels.org/
**Verified:** Opened fiware.org/smart-data-models/ and smartdatamodels.org directly — confirmed the initiative is jointly run by FIWARE Foundation, TM Forum, IUDX, and OASC, and that it publishes JSON Schema/NGSI-LD data models across sectors including smart cities. This is a live, versioned web resource, not a peer-reviewed paper; no DOI applies, and I could not locate (in the time available) a single canonical academic paper describing the initiative as a whole — see Gaps.
**Claim it supports:** A live, multi-organization catalogue of standardized, freely reusable data models for smart-city domains (parking, air quality, etc.) already exists and is in production use by cities.
**What it changes in BEOPS:** Concrete: BEOPS's data contracts for domains it already covers (parking occupancy, air quality) should be checked against the matching Smart Data Models schema *before* inventing field names/units — giving an external, versioned reference for what a claim in that domain is expected to carry.

#### [A13] Agarwal — GIScience Ontology (Place Ontology)
**APA:** Agarwal, P. (2005). Ontological considerations in GIScience. *International Journal of Geographical Information Science*, *19*(5), 501–536. https://doi.org/10.1080/13658810500032321
**Verified:** Taylor & Francis's own page would not render for automated fetch; confirmed via the Crossref API's authoritative record for this DOI (title, author "P. Agarwal", journal, volume 19, issue 5, pages 501–536, year 2005, publisher Informa/Taylor & Francis).
**Claim it supports:** "Ontology" in GIScience covers several distinct senses (philosophical, domain, formal/computational), and geographic categories — including "place" — are theory- and task-dependent constructions, not natural kinds waiting to be measured.
**What it changes in BEOPS:** Concrete caution with a real design consequence: it is a rigorous argument against BEOPS quietly building an implicit, undocumented "ontology of Belgrade" (what counts as a neighborhood or "place") through its own data choices — reinforces documenting, per layer, which external gazetteer/ontology's place-categories are deferred to, consistent with "no own geocoder."

### 3. Ontology of observation itself (measurement vs. forecast vs. estimate)

#### [A14] SOSA/SSN (W3C/OGC)
**APA:** Janowicz, K., Haller, A., Cox, S. J. D., Le Phuoc, D., & Lefrançois, M. (2019). SOSA: A lightweight ontology for sensors, observations, samples, and actuators. *Journal of Web Semantics*, *56*, 1–10. https://doi.org/10.1016/j.websem.2018.06.003
**Verified:** Confirmed via the Crossref API record for this DOI (title, all five authors, journal, volume 56, pages 1–10, year 2019). Separately opened the companion W3C Recommendation "Semantic Sensor Network Ontology" directly at w3.org/TR/vocab-ssn/ (Recommendation, 19 Oct 2017, corrected 8 Dec 2017; joint OGC document 16-079; editors Haller, Janowicz, Cox, Le Phuoc, Taylor, Lefrançois) — both sources agree on SOSA's core classes and its `phenomenonTime`/`resultTime` distinction.
**Claim it supports:** SOSA/SSN formally distinguishes an *Observation* (a Sensor/Procedure applied to a FeatureOfInterest, with both a phenomenon time and a result time) from a *Sample* and an *Actuation* — the standard already contains the primitives needed to formally separate "measured" from "received."
**What it changes in BEOPS:** The single most directly implementable citation in this section: BEOPS's data model should adopt `sosa:Observation`/`sosa:phenomenonTime`/`sosa:resultTime` literally — phenomenonTime vs. an ingestion timestamp *is* "measured now" vs. "received now" — and should model forecasts as a distinct class, never as a `sosa:Observation`.

#### [A15] O&M / OGC Abstract Specification Topic 20
**APA:** Open Geospatial Consortium. (2023). *OGC abstract specification topic 20: Observations, measurements and samples* (OGC 20-082r4, version 3.0.0; K. Schleidt & I. Rinne, Eds.). https://docs.ogc.org/as/20-082r4/20-082r4.html
**Verified:** Opened the document directly — confirmed title, document number, version 3.0.0, editors, publication date (26 May 2023), and its stated alignment with ISO 19156:2023(E). (Historical note, not independently re-verified this session: the O&M lineage traces to Simon Cox's original ISO 19156:2011/OGC work; the edition opened and cited here is the current 2023 revision.)
**Claim it supports:** A valid observation formally requires a stated observed property, feature of interest, procedure, phenomenon time, and result — an observation without a stated method and target is not a conformant observation.
**What it changes in BEOPS:** Concrete ingestion rule: BEOPS should reject or flag any source value that cannot be mapped to an explicit (what, where, when, how-measured) tuple — this operationalizes the project's own "path to source, time, space, unit" rule against a pre-existing conformance model instead of an ad hoc internal checklist.

#### [A16] PROV-O (W3C)
**APA:** Lebo, T., Sahoo, S., & McGuinness, D. (Eds.). (2013). *PROV-O: The PROV ontology* (W3C Recommendation). World Wide Web Consortium. https://www.w3.org/TR/prov-o/
**Verified:** Opened the W3C Recommendation directly — confirmed exact title, "W3C Recommendation 30 April 2013" status line, and the three editors listed.
**Claim it supports:** Provenance — which entity was generated or used by which activity, attributed to which agent, and when — is formally representable and machine-checkable, independent of domain content.
**What it changes in BEOPS:** Concrete: BEOPS's "permission" and "path to source" requirements should be implemented as PROV-O triples (`prov:wasDerivedFrom`, `prov:wasAttributedTo`, `prov:used`) on every published pulse value — an audit-trail data model for free, instead of a bespoke provenance log.

#### [A17] QUDT
**APA:** QUDT.org. (n.d.). *QUDT: Quantities, units, dimensions and types* [Ontology]. https://doi.org/10.25504/FAIRsharing.d3pqw7
**Verified:** Opened qudt.org directly — confirmed the organization's self-description (a 501(c)(3) nonprofit originating from NASA Ames' Exploration Initiatives Ontology Models project) and the DOI it names as "the official DOI citation" for itself (a FAIRsharing registry record).
**Claim it supports:** Units, quantity kinds, and dimensions can be attached to any numeric value formally and machine-checkably, with defined conversion factors between them.
**What it changes in BEOPS:** Concrete: every numeric field in BEOPS should carry a QUDT quantity-kind/unit URI rather than a free-text "unit" string — directly operationalizes the "unit" leg of the project's own source/time/space/unit/permission rule and prevents silent unit mismatches when merging heterogeneous public feeds (e.g., mixed µg/m³ vs. mg/m³ air-quality sources).

### 4. Space semiotics

#### [A18] Gottdiener & Lagopoulos — The City and the Sign
**APA:** Gottdiener, M., & Lagopoulos, A. Ph. (Eds.). (1986). *The city and the sign: An introduction to urban semiotics*. Columbia University Press.
**Verified:** Confirmed via WorldCat's library record (Columbia University Press, New York, 1986) and independently via the Crossref API record for the book's own DOI (10.7312/gott93206, ISBN 9780231892544), which lists the same editors, publisher, and year.
**Claim it supports:** Urban form and urban space can be read as a signifying system — a "text" whose meaning is socially produced — distinct in kind from an engineering or measurement account of the same space.
**What it changes in BEOPS:** Framing, directly relevant to the conference's "space semiotics" track: supports keeping any interpretive/semiotic annotation (place names, how a location is framed in news or OSM tags) in a clearly separate, labeled layer from measured pulses — never blended into one "importance" or "activity" score.

#### [A19] Barthes — Semiology and the Urban
**APA:** Barthes, R. (1986). Semiology and the urban. In M. Gottdiener & A. Ph. Lagopoulos (Eds.), *The city and the sign: An introduction to urban semiotics* (pp. 87–98). Columbia University Press. https://doi.org/10.7312/gott93206-005
**Verified:** Confirmed via the Crossref API record for this exact chapter DOI (chapter title, author, pages 87–98, book, publisher, year — all matched). Honesty note: I initially assumed this essay appears in Neil Leach's widely-cited reader *Rethinking Architecture*; opening that reader's actual table of contents showed its Barthes chapter is instead "The Eiffel Tower," so I did not cite that reader for this text and used the Gottdiener & Lagopoulos printing instead, which I could directly verify.
**Claim it supports:** The city itself functions like a discourse — its elements (a "centre," "empty" vs. "full" zones) are read and signified by inhabitants prior to, and apart from, any functional or measured account of them.
**What it changes in BEOPS:** Framing, with one concrete implication: any "centrality" or place-name claim BEOPS surfaces from toponymy/OSM tags should be flagged as a semiotic/discursive fact (what people call or treat as central) rather than a geometric or functional one, so the two are never silently merged into a single score.

#### [A20] Krampen — Meaning in the Urban Environment
**APA:** Krampen, M. (1979). *Meaning in the urban environment*. Pion.
**Verified:** Confirmed via a Taylor & Francis eBook page for the 2013 Routledge reissue (DOI 10.4324/9780203717226), which states the book was first published in 1979; the original 1979 Pion (London) edition, "Research in Planning and Design" series no. 5, ISBN 9780850860672, was corroborated via multiple bookseller/library records but its own original page was not directly opened this session.
**Claim it supports:** Meaning in the urban environment (how residents read facades, signage, wayfinding) can be studied empirically via semiotic methods, rather than asserted a priori by designers or planners.
**What it changes in BEOPS:** Framing only for now — but it is a real precedent should BEOPS ever incorporate citizen-facing wayfinding/signage data (e.g., from OSM tags or citizen reports): "legibility/meaning" would be its own measurable-but-qualitative layer, not reducible to sensor pulses.

### Gaps

Genuine dead ends from this session, scoped to "theory and ontology of the city":

- **Urban knowledge graphs as a distinct citation.** KM4City [A11] and Smart Data Models [A12] are concrete instances of urban knowledge-graph work, but I did not pursue verifying a dedicated survey/paper on "urban knowledge graphs" as a concept in its own right, within the time budget for this pass.
- **A semiotics-of-the-datafied-city bridge paper.** I looked for recent (2015–2026), verifiable work specifically bridging space semiotics with sensor/IoT/dashboard infrastructure — i.e., semiotics of the *instrumented* city, which is exactly BEOPS's own novel territory — and did not find anything I could verify solidly enough to include. Everything verifiable in Section 4 is pre-digital (1967–1986).
- **A canonical academic paper for the Smart Data Models initiative as a whole.** [A12] is necessarily a web-resource citation; I did not locate a single peer-reviewed paper describing the initiative comprehensively.
- **Genius Loci's publisher record has an unresolved wrinkle** (Rizzoli New York vs. Academy Editions London, both 1980) — noted honestly in [A03] rather than silently picking one.
- I did not attempt verification of a Belgrade- or Balkans-specific semantic/3D city-model dataset — none is implied to exist, and none was searched for here since it falls outside "theory and ontology" into "data availability," which is presumably another section's territory.

---


# PART B — Urban informatics, city sensing and the critical literature

## Bibliography Section — Urban Informatics, City Sensing, and the Critical Literature on Smart Cities and Urban Data
### (BEOPS: Belgrade Evidence-first Observatory of Pulses in the City)

All 24 entries below were opened directly at a DOI landing page, publisher page, official institutional repository, or an author-hosted full-text PDF — not cited from a search-result title alone. Where a field could not be independently confirmed (e.g., an exact page range), this is stated explicitly in the "Verified" line rather than invented.

---

### 1. Urban informatics / smart-urbanism scholarship (including the critical/sceptical literature)

#### [B01] Kitchin — The Real-Time City?
**APA:** Kitchin, R. (2014). The real-time city? Big data and smart urbanism. *GeoJournal, 79*(1), 1–14. https://doi.org/10.1007/s10708-013-9516-8
**Verified:** Opened the SpringerLink article landing page (link.springer.com/article/10.1007/s10708-013-9516-8). Confirmed sole authorship, journal, volume/issue/pages, and DOI. Confirmed the article identifies five risk clusters in real-time/smart urbanism: politics of urban data, technocratic governance, corporate/vendor control, system vulnerability, and panopticon-style surveillance.
**Claim it supports:** Real-time, sensor-instrumented urban dashboards are not neutral instrumentation — they carry specific governance, vendor-dependency, and surveillance risks that any "real-time city" project must address explicitly.
**What it changes in BEOPS:** Justifies BEOPS's refusal of a single unified "city score" in favor of layered, provenance-tagged pulses (whole city → larger units → broad zones); each layer's source/permission metadata is a direct structural answer to Kitchin's "technocratic governance" and "corporate control" risks rather than decorative citation.

#### [B02] Townsend — Smart Cities
**APA:** Townsend, A. M. (2013). *Smart cities: Big data, civic hackers, and the quest for a new utopia*. W. W. Norton & Company.
**Verified:** Opened the publisher's own book page (wwnorton.com/books/smart-cities), which confirmed title, author, and publisher; cross-checked publication year (2013), page count (xiv + 384 pp.), and ISBN (9780393082876) on the Internet Archive catalog record (archive.org/details/smartcitiesbigda0000town).
**Claim it supports:** The dominant vendor-led "smart city" narrative has historically over-promised centralized control while under-delivering, with civic/citizen data and bottom-up hacking emerging as the more durable alternative.
**What it changes in BEOPS:** Reinforces BEOPS's foundational design choice to build exclusively on EXISTING public/citizen sources rather than commissioning new proprietary sensor networks, positioning that choice against the documented vendor-lock-in failure mode this book catalogs.

#### [B03] Greenfield — Against the Smart City
**APA:** Greenfield, A. (2013). *Against the smart city* (The city is here for you to use, Book 1). Do Projects.
**Verified:** Opened the Urban Omnibus excerpt/review page (urbanomnibus.net/2013/10/against-the-smart-city), which confirmed the argument and quoted passages directly. Publisher ("Do Projects", New York), year (2013), and ISBN (978-0-9824383-1-2) cross-confirmed via a university library catalog record and a ResearchGate citation record (this is a Kindle-only pamphlet with no DOI).
**Claim it supports:** Algorithmic city-management proposals assume an impossible "perfect knowledge" and a false universal optimum; historically, such assumptions (e.g., RAND's 1970s NYC fire-house closure model) have produced measurable harm when treated as ground truth.
**What it changes in BEOPS:** This is the direct historical precedent behind BEOPS's "missing ≠ zero" hard rule — Greenfield's RAND fire-station example is the canonical case of an absent signal being misread as "no risk," which BEOPS's rule is explicitly designed to prevent from recurring.

#### [B04] Mattern — A City Is Not a Computer
**APA:** Mattern, S. (2017, February 7). A city is not a computer. *Places Journal*. https://doi.org/10.22269/170207
**Verified:** Opened the Places Journal article landing page (placesjournal.org/article/a-city-is-not-a-computer), which displayed the DOI (10.22269/170207), author, and publication date, and confirmed the essay's argument (later expanded into Mattern's 2021 Princeton UP book of the same title, which I did not verify separately).
**Claim it supports:** Treating a city as a computational, information-processing system erases the plural, non-quantifiable ways cities actually produce and hold knowledge, and risks delegating properly political/ethical decisions to algorithmic optimization.
**What it changes in BEOPS:** Framing only, but load-bearing: motivates avoiding "city brain" / "urban operating system" language in BEOPS's own documentation, keeping instead to "layered evidence pulses" — vocabulary consistent with Mattern's critique of computational city-metaphors.

#### [B05] Luque-Ayala & Marvin — Developing a Critical Understanding of Smart Urbanism?
**APA:** Luque-Ayala, A., & Marvin, S. (2015). Developing a critical understanding of smart urbanism? *Urban Studies, 52*(12), 2105–2116. https://doi.org/10.1177/0042098015577319
**Verified:** Opened the SAGE Journals DOI landing page (journals.sagepub.com/doi/10.1177/0042098015577319). Confirmed authors, year (published online March 2015, in print September 2015), volume/issue/pages, and DOI, and confirmed the article's argument that smart-urbanism research is fragmented and under-theorized.
**Claim it supports:** "Smart urbanism" logics are typically implicit, technology-driven, and normatively loaded rather than neutral or self-evidently beneficial, and each case needs its underlying logic made explicit.
**What it changes in BEOPS:** Motivates a documentation requirement that each BEOPS pulse layer carry an explicit statement of its governing assumption/logic (not just source/time/space/unit), addressing the "fragmented, single-case, under-theorized" gap this paper identifies.

#### [B06] Sadowski & Bendor — Selling Smartness
**APA:** Sadowski, J., & Bendor, R. (2019). Selling smartness: Corporate narratives and the smart city as a sociotechnical imaginary. *Science, Technology, & Human Values, 44*(3), 540–563. https://doi.org/10.1177/0162243918806061
**Verified:** Opened the SAGE Journals DOI landing page (journals.sagepub.com/doi/abs/10.1177/0162243918806061). Confirmed authors, year (online October 2018, in print May 2019), volume/issue/pages, and DOI. Confirmed the argument that IBM and Cisco marketing constructed "smartness" as a unifying, marginalizing corporate narrative.
**Claim it supports:** "Smart city" branding functions as a specific corporate sociotechnical imaginary that marginalizes non-proprietary, alternative visions of urban technology — a project that is not a vendor product should say so explicitly.
**What it changes in BEOPS:** Justifies a naming/positioning decision — BEOPS avoids "smart city" branding in its own materials and frames itself explicitly against the vendor "smartness" imaginary, reinforcing non-proprietary, non-commercial data contracts (no vendor lock-in clauses).

---

### 2. Urban sensing and participatory / citizen sensing

#### [B07] Burke et al. — Participatory Sensing
**APA:** Burke, J., Estrin, D., Hansen, M., Parker, A., Ramanathan, N., Reddy, S., & Srivastava, M. B. (2006). *Participatory sensing*. Center for Embedded Networked Sensing, UCLA. https://escholarship.org/uc/item/19h777qd
**Verified:** Opened the UC eScholarship repository landing page, which confirmed the full author list, year, and the CENS/UCLA (World Sensor Web workshop, SenSys 2006) venue, and summarized the "campaign" model spanning personal/social/urban participation tiers.
**Claim it supports:** Ordinary mobile devices can form legitimate, structured "participatory" sensor networks with an explicit privacy/credibility model, distinct from ad hoc crowdsourcing.
**What it changes in BEOPS:** Motivates adopting Burke et al.'s personal/social/public participation-tier vocabulary as the basis for BEOPS's "permission" metadata field, classifying citizen data sources by consent/aggregation tier rather than a flat public/private binary.

#### [B08] Campbell et al. — The Rise of People-Centric Sensing
**APA:** Campbell, A. T., Eisenman, S. B., Lane, N. D., Miluzzo, E., Peterson, R. A., Lu, H., Zheng, X., Musolesi, M., Fodor, K., & Ahn, G.-S. (2008). The rise of people-centric sensing. *IEEE Internet Computing, 12*(4), 12–21. https://doi.org/10.1109/MIC.2008.90
**Verified:** Fetched the full text from a co-author's own hosted copy (mircomusolesi.org/papers/ic08.pdf), which confirmed the title, complete author list, and content (the MetroSense "Sense–Learn–Share" opportunistic-sensing framework). The journal/volume/issue/DOI were cross-confirmed via IEEE Computer Society CSDL's own index entry ("mic2008040012" = *IEEE Internet Computing*, vol. 12, issue 4) and an ACM Digital Library index record found in search results; direct IEEE Xplore/ACM DL page fetches were blocked (403).
**Claim it supports:** "Opportunistic" sensing — where ordinary carried devices are recruited as sensors without dedicated instrumentation — is a distinct, well-established mode of urban sensing alongside deliberate participatory campaigns.
**What it changes in BEOPS:** Motivates explicitly tagging each BEOPS source along an "opportunistic vs. participatory vs. dedicated-instrument" axis (relevant to using OpenSky/RIPE Atlas-style "found" infrastructure signals as opportunistic city sensors) in its data-source taxonomy.

#### [B09] Goodchild — Citizens as Sensors
**APA:** Goodchild, M. F. (2007). Citizens as sensors: The world of volunteered geography. *GeoJournal, 69*(4), 211–221. https://doi.org/10.1007/s10708-007-9111-y
**Verified:** Opened the SpringerLink article landing page. Confirmed sole authorship, year, volume/issue/pages, DOI, and the article's argument that VGI platforms (OpenStreetMap, Wikimapia, etc.) constitute a distinct, motivation-driven mode of geographic knowledge production.
**Claim it supports:** Volunteered geographic information is a legitimate but epistemically distinct evidentiary category — driven by contributor motivation and coverage bias, not equivalent to authoritative survey data.
**What it changes in BEOPS:** Motivates a dedicated "volunteered/VGI" provenance tag (distinct from "instrument reading") in BEOPS's source schema, carrying its own confidence weighting rather than being silently merged with authoritative geodata.

#### [B10] Haklay — How Good Is Volunteered Geographical Information?
**APA:** Haklay, M. (2010). How good is volunteered geographical information? A comparative study of OpenStreetMap and Ordnance Survey datasets. *Environment and Planning B: Planning and Design, 37*(4), 682–703. https://doi.org/10.1068/b35097
**Verified:** Opened the SAGE Journals DOI landing page (journals.sagepub.com/doi/10.1068/b35097). Confirmed author, year, volume/issue/pages, and DOI, and confirmed the specific quantitative findings (~6 m average positional offset from Ordnance Survey; ~29% of England's area covered by OSM after four years; ~24% of features lacking complete attribute sets).
**Claim it supports:** OSM data quality is usable but bounded and quantifiable — positional accuracy on the order of several metres, with highly uneven completeness — not survey-grade by default.
**What it changes in BEOPS:** Sets a concrete numeric expectation for any BEOPS claim derived from OSM changesets: do not imply spatial precision finer than roughly the ~6–10 m range documented here, consistent with BEOPS's "no own geocoder" rule and its requirement that every claim carry an explicit unit/uncertainty.

#### [B11] Castell et al. — Can Commercial Low-Cost Sensor Platforms Contribute to Air Quality Monitoring?
**APA:** Castell, N., Dauge, F. R., Schneider, P., Vogt, M., Lerner, U., Fishbain, B., Broday, D., & Bartonova, A. (2017). Can commercial low-cost sensor platforms contribute to air quality monitoring and exposure estimates? *Environment International, 99*, 293–302. https://doi.org/10.1016/j.envint.2016.12.007
**Verified:** Fetched the full-text PDF hosted on co-author Barak Fishbain's institutional page (fishbain.net.technion.ac.il), which prints the exact title, full author list, journal, volume, pages, and DOI. Confirmed findings: laboratory correlations >0.9 did not transfer to field conditions; 24 identical units varied node-to-node; most pollutants exceeded EU Air Quality Directive uncertainty thresholds for regulatory use.
**Claim it supports:** Raw low-cost air-quality sensor output cannot be treated as a calibrated measurement — laboratory performance does not predict field performance, and each unit needs individual field validation.
**What it changes in BEOPS:** Concrete data-contract rule: every openSenseMap/Sensor.Community-style air-quality reading in BEOPS must carry a calibration-status/uncertainty flag; absolute pollutant concentrations should not be reported without either documented field calibration or an explicit "indicative/uncalibrated" label.

#### [B12] Benabbas et al. — Measure Particulate Matter by Yourself
**APA:** Benabbas, A., Geißelbrecht, M., Nikol, G. M., Mahr, L., Nähr, D., Steuer, S., Wiesemann, G., Müller, T., Nicklas, D., & Wieland, T. (2019). Measure particulate matter by yourself: Data-quality monitoring in a citizen science project. *Journal of Sensors and Sensor Systems, 8*(2), 317–328. https://doi.org/10.5194/jsss-8-317-2019
**Verified:** Opened the Copernicus Publications open-access article landing page (jsss.copernicus.org/articles/8/317/2019). Confirmed full author list, journal, volume/issue/pages, and DOI, and the finding that only 30–88% of hourly citizen-sensor readings (across test sites) fell within ±5 µg/m³ of reference stations, with humidity-dependent degradation above 70% RH.
**Claim it supports:** A citizen low-cost PM sensor network's data quality can be continuously scored by comparing each reading to its nearest reference station, rather than relying on a single one-time factory/lab calibration.
**What it changes in BEOPS:** Concrete pipeline design: adopt a "nearest reference-station delta" as an automated, continuous QA/QC step for BEOPS's air-quality layer, producing a live per-reading quality flag rather than a static calibrated/uncalibrated label.

---

### 3. Urban observatories, city dashboards, and urban living labs as a research genre

#### [B13] Kitchin & McArdle — Urban Data and City Dashboards: Six Key Issues
**APA:** Kitchin, R., & McArdle, G. (2018). Urban data and city dashboards: Six key issues. In R. Kitchin, T. P. Lauriault, & G. McArdle (Eds.), *Data and the city* (Chapter 9). Routledge.
**Verified:** Opened Maynooth University's institutional repository copy of the chapter (mural.maynoothuniversity.ie/id/eprint/7422), confirming title, authors, and that it is Chapter 9 ("Part III: Urban Data Technologies") of *Data and the City*. Confirmed the book's publisher (Routledge), editors, and its own DOI (10.4324/9781315407388) via the Routledge and Taylor & Francis publisher pages; the publication year shows as 2017 on the editors' own research-group announcement but as 2018 on both the Routledge product page and Aston University's research portal — cited here as 2018 per the two independent publisher-side records. Exact chapter page range could not be independently confirmed and is not invented.
**Claim it supports:** Dashboards embed six recurring, documentable failure modes — epistemology (realist framing masking design choices), scope/access gaps, veracity/validity issues (including the Modifiable Areal Unit Problem), usability/literacy barriers, technocratic uses/utility, and ethical risks (place-based stigmatization).
**What it changes in BEOPS:** Concrete: adopt this six-issue list as an internal pre-publication checklist for every new BEOPS pulse layer or dashboard view, directly operationalizing the "false precision"/"indicator selection" concerns named in the BEOPS brief.

#### [B14] McArdle & Kitchin — The Dublin Dashboard
**APA:** McArdle, G., & Kitchin, R. (2016). The Dublin Dashboard: Design and development of a real-time analytical urban dashboard. *ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences, IV*-4/W1, 19–25. https://doi.org/10.5194/isprs-annals-IV-4-W1-19-2016
**Verified:** Fetched the full-text PDF directly from the Copernicus/ISPRS Annals open-access site, which prints the exact title, both authors, venue, volume, page range, and DOI. Confirmed the architecture description (MVC pattern; 12 modules; two-tier ingestion of live API feeds vs. manually ingested periodic government datasets; "overview first, details on demand").
**Claim it supports:** A real-time, multi-source municipal dashboard mixing live-API and periodically-ingested official data, organized around "overview first, details on demand," is a proven, documented implementation pattern.
**What it changes in BEOPS:** Concrete architectural template: adopt the same two-tier ingestion pattern (automated real-time pull vs. scheduled manual ingestion for slow-changing official datasets) and the overview-then-detail principle for BEOPS's whole-city → larger-unit → broad-zone drill-down.

#### [B15] James et al. — Realizing Smart City Infrastructure at Scale (Newcastle Urban Observatory)
**APA:** James, P., Jonczyk, J., Smith, L., Harris, N., Komar, T., Bell, D., & Ranjan, R. (2022). Realizing smart city infrastructure at scale, in the wild: A case study. *Frontiers in Sustainable Cities, 4*, Article 767942. https://doi.org/10.3389/frsc.2022.767942
**Verified:** Opened the Frontiers journal article landing page. Confirmed full author list, journal, article number, and DOI. Confirmed the paper documents the Newcastle Urban Observatory and identifies five recurring obstacles to at-scale operation (multi-stakeholder governance complexity, privacy/governance tension, data-quality/standardization gaps, sensor-maintenance burden, analytical-skills shortages), with two case studies (pedestrian-flow monitoring during pedestrianization debates; COVID-19 mobility-change tracking).
**Claim it supports:** Long-running, multi-year urban observatories surface a specific, recurring set of operational obstacles that any comparable city-pulse project should plan for from the outset, not discover after deployment.
**What it changes in BEOPS:** Concrete: adds an operational risk register to BEOPS's project plan mirroring these five categories, and validates non-camera pedestrian-flow and lockdown-mobility-change tracking as a template for BEOPS's own event/mobility pulse experiments.

#### [B16] Voytenko, McCormick, Evans & Schliwa — Urban Living Labs
**APA:** Voytenko, Y., McCormick, K., Evans, J., & Schliwa, G. (2016). Urban living labs for sustainability and low carbon cities in Europe: Towards a research agenda. *Journal of Cleaner Production, 123*, 45–54. https://doi.org/10.1016/j.jclepro.2015.08.053
**Verified:** Fetched the full-text open-access PDF (mirrored at An-Najah National University, portals-assets.najah.edu), which prints the exact title, full and correctly spelled author list, journal, volume, pages, and DOI; cross-checked against the Lund University research-portal record. Confirmed the five defining ULL characteristics: geographical embeddedness, experimentation/learning, participation, leadership/ownership, evaluation/refinement.
**Claim it supports:** "Urban living lab" is a defined research genre with specific, checkable design characteristics for iterative, stakeholder-embedded urban experimentation — relevant if BEOPS runs a Belgrade pilot with city stakeholders.
**What it changes in BEOPS:** Framing only at this stage; if/when BEOPS runs a pilot deployment, adopt the five ULL characteristics as explicit success criteria rather than an informal pilot design.

---

### 4. Mobility and parking as urban signal

#### [B17] Millard-Ball, Weinberger & Hampshire — Is the Curb 80% Full or 20% Empty?
**APA:** Millard-Ball, A., Weinberger, R. R., & Hampshire, R. C. (2014). Is the curb 80% full or 20% empty? Assessing the impacts of San Francisco's parking pricing experiment. *Transportation Research Part A: Policy and Practice, 63*, 76–92. https://doi.org/10.1016/j.tra.2014.02.016
**Verified:** Opened the UC eScholarship open-access repository copy (escholarship.org/uc/item/7wc126pq), which confirmed authors, year, journal, volume, pages, and DOI; independently confirmed the DOI resolves (via doi.org) to the matching Elsevier ScienceDirect record. Confirmed the finding that SFpark's demand-responsive pricing moved occupancy toward its 60–80% target and was associated with a documented reduction in cruising for parking.
**Claim it supports:** Parking occupancy data is a validated, policy-actionable urban signal, but its meaning depends on relating occupancy levels to driver-relevant outcomes (cruising, space-finding probability) rather than reporting a bare percentage.
**What it changes in BEOPS:** Concrete: BEOPS should pair raw parking-occupancy percentages with a derived cruising/arrival-rate proxy where the underlying data permits, and should avoid presenting a single occupancy snapshot as a stand-alone "demand" claim without temporal context.

#### [B18] Herrera et al. — The Mobile Century Field Experiment
**APA:** Herrera, J. C., Work, D. B., Herring, R., Ban, X. J., Jacobson, Q., & Bayen, A. M. (2010). Evaluation of traffic data obtained via GPS-enabled mobile phones: The Mobile Century field experiment. *Transportation Research Part C: Emerging Technologies, 18*(4), 568–583. https://doi.org/10.1016/j.trc.2009.10.006
**Verified:** Fetched the full-text PDF directly from the project's own site (bayen.berkeley.edu), which prints the exact title, full author list, journal, volume/issue/pages, and DOI. Confirmed the central finding: 2–3% penetration of GPS-enabled phones in the driver population was sufficient to reconstruct traffic velocity accurately against video-verified ground truth.
**Claim it supports:** Sparse floating-car/probe-vehicle data, even at low penetration rates, can yield accurate aggregate flow estimates — providing a quantified basis for treating probe-style signals as a legitimate mobility pulse.
**What it changes in BEOPS:** Concrete: gives BEOPS an evidence-based penetration-rate threshold to cite when judging whether a sparse mobility feed is sufficient for a zone-level flow claim, and supports reporting flow/velocity pulses with an explicit penetration-rate caveat rather than an unqualified number.

#### [B19] Wessel & Farber — On the Accuracy of Schedule-Based GTFS
**APA:** Wessel, N., & Farber, S. (2019). On the accuracy of schedule-based GTFS for measuring accessibility. *Journal of Transport and Land Use, 12*(1). https://doi.org/10.5198/jtlu.2019.1502
**Verified:** Opened the *Journal of Transport and Land Use* article page (jtlu.org/index.php/jtlu/article/view/1502), which confirmed title, both authors, journal, volume/issue, and DOI, and confirmed the method (comparing AVL-derived actual vehicle movement to GTFS-schedule predictions across four North American agencies) and findings (5–15% systematic over-prediction in higher-access zones; strong, non-random spatial bias). The article's exact page range could not be independently confirmed within the sources opened and is not invented here.
**Claim it supports:** Scheduled GTFS data systematically diverges from actually-operated transit service, with a directional, spatially patterned bias — it is a schedule, not a measurement of delivered service.
**What it changes in BEOPS:** Concrete: any BEOPS claim derived from GTFS schedules alone (absent a real-time/AVL feed) must be explicitly labeled "scheduled," never "operated" — a direct, transit-specific operationalization of the "forecast ≠ measurement" hard rule.

#### [B20] Lemaire et al. — Early Detection of Critical Urban Events Using Mobile Phone Network Data
**APA:** Lemaire, P., Furno, A., Rubrichi, S., Bondu, A., Smoreda, Z., Ziemlicki, C., El Faouzi, N.-E., & Gaume, E. (2024). Early detection of critical urban events using mobile phone network data. *PLOS ONE, 19*(8), Article e0309093. https://doi.org/10.1371/journal.pone.0309093
**Verified:** Opened the PLOS ONE article landing page, which displayed the exact citation line ("PLoS ONE 19(8): e0309093"), publication date (22 August 2024), full author list, and DOI. Confirmed the method (minute-level antenna-level call/SMS volume anomaly detection against 86 documented Paris events: concerts, fires, protests) and the reported precision (up to 28.63%).
**Claim it supports:** Aggregate, antenna-level (non-camera, non-individual) telecom signalling data can detect crowd-scale urban events with useful but modest precision, without any per-person tracking.
**What it changes in BEOPS:** Concrete: offers a validated method template and a realistic precision benchmark (~29%, not near-100%) for a future BEOPS "crowd/event pulse" built only from aggregate, antenna-level signals — consistent with the "no person-level analysis... no tracking" hard rule, and a caution against overclaiming detection reliability.

---

### 5. Privacy, ethics, and legality of urban data reuse

#### [B21] de Montjoye et al. — Unique in the Crowd
**APA:** de Montjoye, Y.-A., Hidalgo, C. A., Verleysen, M., & Blondel, V. D. (2013). Unique in the crowd: The privacy bounds of human mobility. *Scientific Reports, 3*, Article 1376. https://doi.org/10.1038/srep01376
**Verified:** Opened the *Scientific Reports* (Nature Portfolio) article landing page. Confirmed all four authors, year, journal, article number, and DOI. Confirmed the central "unicity" result: four spatio-temporal points identify 95% of individuals in a 1.5-million-person, 15-month mobile-phone dataset, and coarsening resolution reduces uniqueness only slowly (roughly as the 1/10 power).
**Claim it supports:** Even substantially coarsened mobility traces remain re-identifying for the large majority of individuals from very few data points — simple spatial/temporal coarsening is not, by itself, adequate anonymization.
**What it changes in BEOPS:** Concrete lower bound: any BEOPS aggregation of mobility-adjacent signals must not rely on coarsening alone; this motivates a minimum-count-per-cell (k-anonymity-style) publication rule instead of a resolution-only rule, directly reinforcing the "no person-level analysis" hard rule with a quantitative justification.

#### [B22] Sweeney — Achieving k-Anonymity
**APA:** Sweeney, L. (2002). Achieving k-anonymity privacy protection using generalization and suppression. *International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems, 10*(5), 571–588. https://doi.org/10.1142/S021848850200165X
**Verified:** Fetched the full-text PDF from the author's own Data Privacy Lab site (dataprivacylab.org), which confirmed the title, sole authorship, and content (the MinGen generalization/suppression algorithm for achieving a k-anonymity threshold). Volume/issue/pages (10(5), 571–588) and the DOI were cross-confirmed via an ACM Digital Library index entry and a Scientific Research Publishing reference-database record; the WorldScientific publisher landing page itself returned a 403 error and was not directly opened.
**Claim it supports:** k-Anonymity — ensuring every released record is indistinguishable from at least k−1 others on quasi-identifying fields — is a formal, implementable standard for aggregation thresholds, achievable via generalization and suppression.
**What it changes in BEOPS:** Concrete: BEOPS's data contracts should specify an explicit minimum k (no published cell/bucket built from fewer than k underlying source records) as an auditable gate before publishing any zone-level aggregate derived from potentially re-identifiable inputs.

#### [B23] Article 29 Data Protection Working Party — Opinion 05/2014 on Anonymisation Techniques
**APA:** Article 29 Data Protection Working Party. (2014). *Opinion 05/2014 on anonymisation techniques* (WP216). European Commission. https://ec.europa.eu/justice/article-29/documentation/opinion-recommendation/files/2014/wp216_en.pdf
**Verified:** Opened the official EU document PDF directly. Confirmed it is Opinion 05/2014, adopted 10 April 2014, and confirmed its core conclusions: no single anonymization technique is sufficient on its own; a "release and forget" approach is explicitly warned against; k-anonymity alone does not prevent inference/attribute-disclosure attacks and needs complementary techniques (e.g., l-diversity).
**Claim it supports:** Anonymization/aggregation for open-data reuse is a continuous, context-specific risk-management process under EU data-protection doctrine, not a one-off technical checkbox, and residual re-identification risk must be actively monitored as external data grows.
**What it changes in BEOPS:** Concrete: BEOPS should adopt a periodic re-review process for published aggregate layers (not a one-time aggregation check at first publication) and document which specific technique each layer uses — feeding directly into the "permission" field of BEOPS's per-claim metadata contract.

#### [B24] van Zoonen — Privacy Concerns in Smart Cities
**APA:** van Zoonen, L. (2016). Privacy concerns in smart cities. *Government Information Quarterly, 33*(3), 472–480. https://doi.org/10.1016/j.giq.2016.06.004
**Verified:** Opened the Erasmus University Rotterdam institutional repository landing page (pure.eur.nl), which confirmed sole authorship, journal, volume/issue/pages, and DOI, and confirmed the article's focus on how privacy acceptability in smart-city data collection varies systematically by data type and by which actor (government vs. commercial) collects it.
**Claim it supports:** Public acceptability of urban sensing is not uniform — it varies by data type (environmental/infrastructure vs. behavioral/movement) and by which actor holds the data — so a single blanket privacy posture is empirically the wrong model.
**What it changes in BEOPS:** Concrete: motivates a per-layer "sensitivity tier" in BEOPS's data catalog (e.g., environmental/infrastructure pulses as lower sensitivity; anything mobility- or behavior-adjacent as higher sensitivity requiring stronger aggregation/permission review), rather than one uniform privacy rule across all layers.

---

### Gaps

The following were searched for specifically and could not be confirmed to the same verification standard, or could not be found at all, within the time available:

1. **A peer-reviewed paper studying the Sensor.Community/luftdaten network specifically by name.** I found and verified a closely analogous citizen-science low-cost PM sensor network data-quality paper (Benabbas et al., S12), but did not find a comparably citable, DOI-bearing academic paper that names "Sensor.Community" or "luftdaten" explicitly as its studied platform (most such discussion lives in project reports, blog posts, and grey literature rather than indexed journals).
2. **A dedicated academic paper on openSenseMap** as a platform, even though it is named in the BEOPS project context. Nothing citable at the required verification standard turned up in the time available.
3. **Rob Kitchin's *The Data Revolution* (Sage, 2014)** as a stand-alone entry. I located the book (ISBN 978-1-4462-8748-4) but the SAGE Research Methods page was blocked by robots.txt and I could not open a verifiable landing page within scope; I chose not to cite it without direct verification, and used "The real-time city?" (S01) as the representative Kitchin entry instead.
4. **A single integrated peer-reviewed treatment of "GDPR and open-data reuse"** (as opposed to general anonymization doctrine). Several law-review candidates appeared in search results (e.g., in *International Data Privacy Law*), but none was opened and verified in scope; the Article 29 Working Party Opinion 05/2014 (S23) was used instead as the verified, canonical authority on anonymization standards that GDPR-era practice still cites.
5. **Academic urban-informatics literature treating OpenSky Network or RIPE Atlas explicitly as urban-sensing data sources** (both named in BEOPS's own project context). These platforms are extensively studied in aviation-security and network-measurement literatures respectively, but I found no dedicated treatment of either as a general-purpose *urban* sensing signal — this reads as a genuine gap in the literature itself, not only a search limitation, and is worth flagging to BEOPS as an area where the project may be doing literally novel repurposing rather than following an established research thread.
6. **Direct publisher-page verification was blocked (403/robots.txt) for several venues** — IEEE Xplore, ACM Digital Library, ScienceDirect (in most cases), WorldScientific, and JSTOR all refused automated fetches in this environment. Where this occurred (S08 Campbell et al.; S17 Millard-Ball et al., partially; S19 Wessel & Farber, page range only; S22 Sweeney, DOI only; S24 van Zoonen, publisher copy only), I verified via the journal's own institutional repository copy, an author-hosted PDF, or cross-referenced independent secondary indexes (ACM DL/IEEE CSDL listings, university repositories) rather than treating a blocked fetch as a substitute for verification — each such case is flagged individually in its "Verified" line above rather than left ambiguous.

---


# PART C — The historical problems of big data, and what AI actually offers

## The Historical Problems of Big Data and What Recent AI Actually Offers — A Verified Bibliography for BEOPS

### 1. The historical problems: collection, processing, evaluation, synthesis

#### [C01] Google Flu Trends and "Big Data Hubris"
**APA:** Lazer, D., Kennedy, R., King, G., & Vespignani, A. (2014). The parable of Google Flu: Traps in big data analysis. *Science, 343*(6176), 1203–1205. https://doi.org/10.1126/science.1248506
**Verified:** Opened a full-text mirror of the article directly (dhi.ac.uk PDF; publisher page at science.org returned 403 to automated fetch, so this mirror was used to read the actual text). Confirmed title, all four authors, journal, volume/issue/pages, and date (14 March 2014). Confirmed the article uses "Big Data Hubris" as an explicit section heading, defined verbatim as "the often implicit assumption that big data are a substitute for, rather than a supplement to, traditional data collection and analysis." Confirmed the measured failure: Google Flu Trends (GFT) over-estimated CDC-measured flu prevalence in 100 of the 108 weeks from August 2011–September 2013, overshooting the 2012–2013 peak by more than 50%, while fitting ~50 million candidate search terms to only 1,152 CDC data points (severe overfitting) — compounded by undocumented changes to Google's own search algorithm (86 changes in a single two-month window).
**Claim it supports:** A widely-trusted, algorithmically-mediated proxy signal can silently and severely diverge from ground truth for well over a year without the pipeline itself flagging anything, because the model substitutes correlation-mining over an undocumented, drifting data-generating process for domain-grounded measurement.
**What it changes in BEOPS:** No fused "city pulse" ships as a standalone number — every derived indicator must retain and expose its supporting raw sources, and be periodically back-checked against whatever slower official ground truth exists (city statistics office, even if lagged/coarse). Concretely: add a data contract field for "upstream platform/algorithm version" per source, and log version changes as first-class provenance events — this is exactly the undetected failure mode Lazer et al. document.

#### [C02] Data quality is multi-dimensional, not a single accuracy number
**APA:** Wang, R. Y., & Strong, D. M. (1996). Beyond accuracy: What data quality means to data consumers. *Journal of Management Information Systems, 12*(4), 5–33. https://doi.org/10.1080/07421222.1996.11518099
**Verified:** Direct fetch of the Taylor & Francis abstract page returned a 403; confirmed the identical bibliographic record (title, both authors, journal, volume 12 issue 4, pages 5–33, 1996, DOI) via ScienceOpen's independently-indexed record instead.
**Claim it supports:** Empirically-derived (consumer-survey-based) data quality is a multi-dimensional construct — intrinsic, contextual, representational, and accessibility dimensions — so a record can be accurate and still be low-quality (stale, not believable, poorly documented, wrong granularity for the use case).
**What it changes in BEOPS: ** Replace any single scalar "confidence score" per source/pulse with an explicit quality vector — at minimum timeliness/staleness, completeness, believability/source reputation, and cross-source consistency — and make this vector, not a scalar, the thing the fusion and evaluation layers consume. This is the direct academic anchor for "veracity," older and more rigorous than the popular but non-peer-reviewed "4 Vs of big data" industry framing, which I deliberately did not cite here since I could not find a peer-reviewed original for it.

#### [C03] Schema matching and drift
**APA:** Rahm, E., & Bernstein, P. A. (2001). A survey of approaches to automatic schema matching. *The VLDB Journal, 10*(4), 334–350. https://doi.org/10.1007/s007780100057
**Verified:** Opened the Springer/VLDB Journal landing page directly. Confirmed title, both authors, journal, volume 10 issue 4, pages 334–350, publication date (online 21 Nov 2001), and the DOI as displayed on the page.
**Claim it supports:** Matching the schemas of independently-produced public datasets (differing field names, units, granularities, encodings for the same real-world concept) is a long-studied, only partially automatable problem with a documented taxonomy of matcher types (name-, structure-, instance/content-based, hybrid) — not a solved one.
**What it changes in BEOPS:** Adopt this taxonomy as BEOPS's internal ingestion vocabulary: every source connector declares which matcher strategy resolved each field to BEOPS's canonical schema, and at what confidence. A field silently renamed, re-typed, or re-scaled upstream then produces a visible re-matching event in the data contract instead of a silent join failure — directly serving the PROCESSING problem's "schema drift" concern.

#### [C04] Deep-learning entity matching actually measured against classical ML matching
**APA:** Mudgal, S., Li, H., Rekatsinas, T., Doan, A., Park, Y., Krishnan, G., Deep, R., Arcaute, E., & Raghavendra, V. (2018). Deep learning for entity matching: A design space exploration. In *Proceedings of the 2018 International Conference on Management of Data* (pp. 19–34). Association for Computing Machinery. https://pages.cs.wisc.edu/~anhai/papers1/deepmatcher-sigmod18.pdf
**Verified:** Opened the authors' self-archived PDF directly (this is the DeepMatcher paper). Confirmed title, all 9 authors, and venue (SIGMOD'18) from the document header. I could not independently confirm the ACM DOI on an ACM page (dl.acm.org returned 403 to every automated fetch attempted this session), so I cite the verified author-hosted copy instead of asserting an unconfirmed DOI string. Confirmed the actual measured, non-uniform result: DeepMatcher beats the classical/ML pipeline Magellan (Konda, P., Das, S., Suganthan G. C., P., Doan, A., Ardalan, A., Ballard, J. R., Li, H., Panahi, F., Zhang, H., Naughton, J., Prasad, S., Krishnan, G., Deep, R., & Raghavendra, V. (2016). Magellan: Toward building entity matching management systems over data science stacks. *Proceedings of the VLDB Endowment, 9*(13), 1581–1584. https://doi.org/10.14778/3007263.3007314 — this companion citation confirmed directly via its dblp bibliographic record) by 3.0–22.0 F1 points on textual/long-text matching and by 6.2–32.6 F1 points on "dirty" data with misaligned attributes, but is merely competitive — not better — on clean structured data with atomic values, while requiring far longer training time; the paper explicitly recommends against reaching for deep learning on the clean-structured case. The classical framing both papers work within is set out in Doan, A., Halevy, A., & Ives, Z. (2012). *Principles of Data Integration.* Morgan Kaufmann/Elsevier (ISBN 978-0-12-416044-6, confirmed directly via the publisher's page: 1st edition, 25 June 2012), with Elmagarmid, A. K., Ipeirotis, P. G., & Verykios, V. S. (2007). Duplicate record detection: A survey. *IEEE Transactions on Knowledge and Data Engineering, 19*(1) (confirmed directly via the authors' Purdue-hosted PDF) as the pre-ML antecedent survey.
**Claim it supports:** Whether learned entity matching beats classical/rule-based matching is conditional on data shape (dirty vs. clean, textual vs. atomic) — not a blanket win for deep-learning- or LLM-era methods, and must be benchmarked per source-pair rather than assumed.
**What it changes in BEOPS:** Formalize cross-source deduplication ("sources that secretly share one physical origin") as a per-source-pair experiment: profile each incoming pair's dirtiness/structuredness first, and route only textual/dirty pairs to a learned matcher, keeping clean structured pairs on cheaper rule/blocking-based matching — with the learned path's training cost budgeted explicitly, since BEOPS runs CPU-first.

#### [C05] The ecological fallacy
**APA:** Robinson, W. S. (1950). Ecological correlations and the behavior of individuals. *American Sociological Review, 15*(3), 351–357. https://doi.org/10.2307/2087176
**Verified:** Opened a full-text scan of the original article directly (stats.uwo.ca mirror). Confirmed the worked example on 1930 U.S. census data: the individual-level correlation between being Black and being illiterate is 0.203, while the state-level ("ecological") correlation on the same underlying phenomenon is 0.773–0.946 — roughly a 4× inflation. More strikingly, for nativity and illiteracy the individual correlation is positive (+0.118) while the ecological correlation is negative (−0.526 to −0.619): the relationship's *sign* flips under aggregation. The DOI is the standard, widely-repeated JSTOR identifier for this article (I did not see it printed on the scanned PDF itself, which predates DOIs; it is corroborated across every independent bibliographic index checked).
**Claim it supports:** A correlation computed on data aggregated to a zone (state, municipality, census tract) can differ arbitrarily from — and even reverse the sign of — the same relationship computed on finer-grained or individual-level data, independent of any error in the underlying data.
**What it changes in BEOPS:** Any pulse that correlates two indicators at the level of Belgrade's administrative units (opština/mesna zajednica) needs an explicit caveat that the correlation is a property of that aggregation, not a demonstrated individual-level or point-level effect — this should be a standing disclaimer template in BEOPS's synthesis layer whenever two zone-aggregated series are compared.

#### [C06] The Modifiable Areal Unit Problem (MAUP)
**APA:** Openshaw, S., & Taylor, P. J. (1979). A million or so correlation coefficients: Three experiments on the modifiable areal unit problem. In N. Wrigley & R. J. Bennett (Eds.), *Statistical applications in the spatial sciences* (pp. 127–144). Pion.
**Verified — PARTIAL:** I could **not** open or read this 1979 book chapter itself (pre-digital, no DOI, not hosted anywhere fetchable). I confirmed author, year, publisher (Pion), and page range (127–144) via a secondary bibliometric aggregator (scispace's indexed record), and confirmed by cross-referencing that this is the standard, universally-cited source for the specific claim that recomputing the same correlation coefficient under thousands of alternative zoning schemes on the same underlying data produces a wide, non-random spread of results (i.e., MAUP demonstrated empirically, not just asserted). I am marking this entry **UNVERIFIED at the primary-source level** — everything past bibliographic metadata is inference from secondary citing literature, not something I read myself. If the paper needs this fact load-bearing, it should be re-verified against a library copy of Wrigley & Bennett's edited volume before citing.
**Claim it supports:** The same point/areal data, aggregated to different zone boundaries or resolutions, yields different — sometimes wildly different — statistical results, independent of measurement error.
**What it changes in BEOPS:** Before treating any zone-level urban pattern as a real effect, BEOPS should test the same indicator's correlation/behavior under at least one alternative spatial aggregation (a different zoning or resolution) — a concrete, cheap experiment this specific paper's method licenses, distinct from and complementary to the ecological-fallacy caveat above (S05 is about aggregation level; MAUP is about aggregation *shape*, for a fixed level).

---

### 2. Provenance, documentation and reproducibility as the engineered answer

#### [C07] FAIR data principles
**APA:** Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., Appleton, G., Axton, M., Baak, A., Blomberg, N., Boiten, J.-W., da Silva Santos, L. B., Bourne, P. E., ... Mons, B. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data, 3*, Article 160018. https://doi.org/10.1038/sdata.2016.18
**Verified:** Opened the Nature/Scientific Data article page directly (following a redirect from the DOI). Confirmed title, journal, volume 3 article 160018, date (15 March 2016), the 50+-author list with Barend Mons as corresponding author, and that FAIR stands for Findable, Accessible, Interoperable, Reusable, described in the abstract as "a concise and measurable set of principles."
**Claim it supports:** Data reuse and machine-actionable discovery require deliberately engineered metadata, identifiers, and access/licensing practices — reproducibility is not a byproduct of good intentions but a set of concrete, checkable requirements.
**What it changes in BEOPS:** Score every ingested source and every derived pulse against the FAIR checklist explicitly (does it have a persistent identifier? machine-readable license? documented vocabulary mapping to BEOPS's schema?) as part of the ingestion data contract, not as an afterthought. The "Interoperable" pillar in particular is best operationalized with a machine-readable provenance vocabulary — W3C's PROV-O (Lebo, T., Sahoo, S., & McGuinness, D. (Eds.). (2013). *PROV-O: The PROV ontology* [W3C Recommendation]. https://www.w3.org/TR/prov-o/ — confirmed directly via the W3C page itself: Recommendation status, 30 April 2013, editors Timothy Lebo, Satya Sahoo, Deborah McGuinness, providing OWL2 classes/properties for representing and interchanging provenance across systems) is the natural implementation choice for exactly the lineage graph a fusion pipeline like BEOPS needs (which raw records, transformed how, by which pipeline version, contributed to which pulse) — this can substitute for an ad hoc, hand-rolled "data version control" scheme, since a generic lineage ontology already exists and is machine-checkable.

#### [C08] Datasheets for Datasets
**APA:** Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H., Daumé III, H., & Crawford, K. (2021). Datasheets for datasets. *Communications of the ACM, 64*(12), 86–92. https://arxiv.org/abs/1803.09010
**Verified:** Opened the arXiv abstract page directly. Confirmed title, all 7 authors, and the core proposal ("every dataset be accompanied with a datasheet that documents its motivation, composition, collection process, recommended uses"). Confirmed 8 versions spanning March 2018–December 2021, with an author comment on the page stating publication in *Communications of the ACM*, December 2021; I did not independently confirm the CACM DOI on a page I opened, so I cite via the arXiv URL, which the task brief explicitly allows.
**Claim it supports:** Datasets, like hardware components, should ship with standardized documentation of provenance, collection method, and known limitations — the same discipline BEOPS demands of its own sources should be demanded of every public source it ingests, most of which currently ship with none.
**What it changes in BEOPS:** Require a datasheet-style record (motivation, collection process, known gaps, recommended/inappropriate uses) for every external Belgrade data source BEOPS ingests, stored alongside the schema mapping from S03 — this is the concrete artifact that operationalizes "evidence-first." A closely related NLP-specific analogue, confirmed directly via the ACL Anthology (Bender, E. M., & Friedman, B. (2018). Data statements for natural language processing: Toward mitigating system bias and enabling better science. *Transactions of the Association for Computational Linguistics, 6*, 587–604. https://doi.org/10.1162/tacl_a_00041), should be used instead wherever a BEOPS source is free text (news, social posts) rather than structured records.

#### [C09] Model Cards
**APA:** Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I. D., & Gebru, T. (2019). Model cards for model reporting. In *Proceedings of the Conference on Fairness, Accountability, and Transparency* (pp. 220–229). Association for Computing Machinery. https://doi.org/10.1145/3287560.3287596
**Verified:** Opened the arXiv abstract page directly, which carries the confirmed DOI (10.1145/3287560.3287596) and venue metadata (FAT* '19, Atlanta, GA, 29–31 January 2019). Confirmed all 9 authors and the proposal for short documents disclosing benchmarked evaluation "across different cultural, demographic, or phenotypic groups" plus intended-use statements.
**Claim it supports:** A released model needs standardized documentation of what it was evaluated on, under what conditions, and where it is known to fail — the model-side complement to a datasheet.
**What it changes in BEOPS:** Ship a model card for every small specialist model BEOPS runs locally (ONNX/GGUF) — stating training data, evaluation conditions, and known failure modes on Belgrade-specific inputs (e.g., Serbian-language text, Cyrillic/Latin mixed input) rather than only citing the upstream model's original card, since local fine-tuning or quantization changes behavior the original card cannot speak to.

#### [C10] Data work is systematically undervalued and under-resourced relative to model work
**APA:** Sambasivan, N., Kapania, S., Highfill, H., Akrong, D., Paritosh, P., & Aroyo, L. M. (2021). "Everyone wants to do the model work, not the data work": Data cascades in high-stakes AI. In *Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems* (Article 39, pp. 1–15). Association for Computing Machinery. https://doi.org/10.1145/3411764.3445518
**Verified:** Opened the ACM full-text HTML at this exact DOI directly and confirmed it is the "data cascades" paper (compounding downstream effects of upstream data quality problems in deployed high-stakes AI systems). The complete author list beyond the first two names is drawn from cross-referenced secondary sources (a semanticscholar URL slug showing "Sambasivan-Kapania" as first authors, plus consistent listings elsewhere) rather than confirmed directly from an author-list field on the page I opened — flagging this because the full-text fetch surfaced the paper's argument and DOI but not a clean structured author-list element.
**Claim it supports:** Practitioners in AI/ML pipelines consistently report that data-related problems compound silently downstream ("cascades") into model failures, and that organizational incentives systematically reward model-building over the unglamorous data work that would prevent this. Two data points on the magnitude of "unglamorous data work": Kandel, S., Paepcke, A., Hellerstein, J. M., & Heer, J. (2012). Enterprise data analysis and visualization: An interview study. *IEEE Transactions on Visualization and Computer Graphics, 18*(12) — a peer-reviewed interview study of enterprise analysts, confirmed directly via a Stanford-hosted PDF, which contains the directly-quoted practitioner statement "I spend more than half of my time integrating, cleansing and transforming data without doing any actual analysis." The much more frequently repeated claim that data scientists spend roughly 80% of their time on data cleaning (traced to a 2016 CrowdFlower survey reported by Forbes) I could **not** verify: both the original Forbes article and an archive.org mirror of it returned access-blocked errors to automated fetch this session, so I flag that specific figure as **UNVERIFIED** and recommend citing Kandel et al.'s peer-reviewed, quoted measurement instead of the popular 80% statistic.
**What it changes in BEOPS:** Budget engineering time for BEOPS explicitly against this asymmetry — the datasheet/schema-matching/deduplication work from S03–S04, S08 is where cascades originate, so it should be resourced and reviewed with the same rigor as the fusion/synthesis model code, not treated as one-time plumbing.

---

### 3. Evaluation without ground truth

#### [C11] Weak supervision at scale (Snorkel)
**APA:** Ratner, A., Bach, S. H., Ehrenberg, H., Fries, J., Wu, S., & Ré, C. (2017). Snorkel: Rapid training data creation with weak supervision. *Proceedings of the VLDB Endowment, 11*(3), 269–282. https://arxiv.org/abs/1711.10160
**Verified:** Opened the arXiv abstract page directly, which carries the confirmed journal-ref (PVLDB, 11(3), 269–282, 2017). Confirmed all 6 authors and the measured claims: subject-matter experts using labeling-function-based weak supervision build models "2.8x faster" than hand-labeling, with "132% average improvements to predictive performance over prior heuristic approaches" across the paper's evaluated applications.
**Claim it supports:** When no labeled ground truth exists, multiple imperfect, possibly-conflicting heuristic label sources can be statistically combined (denoised) into a single probabilistic label that outperforms any one heuristic alone — this is a general-purpose answer to "how do you get a training/evaluation signal with no ground truth."
**What it changes in BEOPS:** For any pulse where "is this indicator right" has no ground-truth answer (BEOPS's stated EVALUATION problem), treat each contributing raw source as a Snorkel-style "labeling function" and fit a label/generative model over their agreements and disagreements, rather than hand-picking one source as authoritative or naively averaging — this gives BEOPS a documented, falsifiable procedure instead of an ad hoc weighting scheme.

#### [C12] Truth discovery: estimating source reliability from disagreement
**APA:** Li, Y., Gao, J., Meng, C., Li, Q., Su, L., Zhao, B., Fan, W., & Han, J. (2016). A survey on truth discovery. *ACM SIGKDD Explorations Newsletter, 17*(2), 1–16. https://arxiv.org/abs/1505.02463
**Verified:** Opened the arXiv abstract page directly, confirming title, all 8 authors, and the framing ("truth discovery, which integrates multi-source noisy information by estimating the reliability of each source"). The SIGKDD Explorations journal/volume/issue/DOI (10.1145/2897350.2897352) is corroborated across multiple independent bibliographic indexes and appeared as the exact title on an ACM Digital Library listing in search results, but I could not open the ACM page directly (403 to automated fetch), so the formal journal citation details are cross-referenced rather than self-verified.
**Claim it supports:** When multiple sources report conflicting values for the same fact (e.g., two open-data portals giving different figures for the same intersection's traffic count), the sources' reliabilities and the most likely true values can be jointly estimated iteratively, without needing any of them to be a known-trustworthy ground truth in advance.
**What it changes in BEOPS:** This is the direct algorithmic answer to BEOPS's "sources that secretly share one physical origin" problem's evaluation side: truth discovery methods explicitly model source *dependence* (two sources copying the same upstream feed should not each get independent reliability weight), which naive averaging does not — BEOPS's fusion layer should adopt a dependence-aware truth-discovery weighting rather than an unweighted or naively-weighted mean.

#### [C13] From data fusion to knowledge fusion at web scale
**APA:** Dong, X. L., Gabrilovich, E., Heitz, G., Horn, W., Murphy, K., Sun, S., & Zhang, W. (2014). From data fusion to knowledge fusion. *Proceedings of the VLDB Endowment, 7*(10), 881–892. https://doi.org/10.14778/2732951.2732962
**Verified:** Opened the official VLDB-hosted PDF directly (vldb.org/pvldb/vol7/p881-dong.pdf) — a primary-source, publisher-hosted copy. Confirmed title, all 7 authors, venue (PVLDB, Vol. 7, No. 10), pages 881–892, year 2014. Confirmed the core contribution: extending classical two-dimensional (source × claim) data fusion to a three-dimensional problem that also accounts for noisy automatic information extractors, applied at a scale (1.6 billion RDF triples from over 1 billion web pages) the paper states is "three orders of magnitude larger than the data sets used in previous data fusion papers," with the refined method producing well-calibrated confidence estimates (predicted confidence tracks actual accuracy).
**Claim it supports:** Source-reliability-weighted fusion methods that work on small, curated datasets need re-engineering (not just re-running) to remain calibrated at the scale and noise level of real, automatically-extracted or automatically-scraped city data.
**What it changes in BEOPS:** Before adopting any truth-discovery or fusion method from the smaller-scale literature (S12), BEOPS should explicitly test whether its confidence outputs stay calibrated at BEOPS's actual source count and noise level — calibration is a property to test per deployment, not something inherited automatically from a method's paper.

#### [C14] Neural network confidence is not calibrated by default
**APA:** Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of modern neural networks. In *Proceedings of the 34th International Conference on Machine Learning* (PMLR Vol. 70, pp. 1321–1330).
**Verified:** Opened the official PMLR proceedings page directly. Confirmed title, all 4 authors, proceedings volume 70, pages 1321–1330, year 2017.
**Claim it supports:** Modern (larger, deeper) neural networks are systematically *less* calibrated than older, smaller ones — a model's stated confidence should not be trusted as a probability without explicit post-hoc calibration (the paper shows a single-parameter temperature-scaling correction is "surprisingly effective").
**What it changes in BEOPS:** Any confidence score BEOPS's small local models emit (classification of a claim as supported/unsupported, an anomaly score, a source-reliability estimate) must be calibration-checked (e.g., via temperature scaling and a reliability diagram) before being used numerically in fusion — an uncalibrated 0.9 is not "90% likely true," and BEOPS's synthesis layer should not treat it as one until checked.

#### [C15] Conformal prediction: distribution-free uncertainty with finite-sample guarantees
**APA:** Angelopoulos, A. N., & Bates, S. (2021). A gentle introduction to conformal prediction and distribution-free uncertainty quantification. arXiv. https://arxiv.org/abs/2107.07511
**Verified:** Opened the arXiv abstract page directly. Confirmed both authors, the core claim (prediction sets with "explicit, non-asymptotic guarantees even without distributional assumptions or model assumptions"), and version history (6 versions, v1 July 2021 through v6 December 2022, the latest confirmed on the page).
**Claim it supports:** It is possible to wrap any model's point prediction in an uncertainty interval/set with a mathematically guaranteed coverage rate, without assuming the model is well-specified or the errors are Gaussian — which matters when there is no ground truth to check calibration against empirically in the usual way.
**What it changes in BEOPS:** Wrap BEOPS's small forecasting/anomaly models' point outputs in conformal prediction intervals rather than reporting a bare number — this gives a defensible, distribution-free "how confident is this pulse" statement that does not require BEOPS to have solved the EVALUATION problem's ground-truth gap first, since conformal guarantees hold regardless of whether the underlying model is any good, as long as a held-out calibration set exists.

#### [C16] The point-adjustment protocol inflates time-series anomaly detection scores
**APA:** Kim, S., Choi, K., Choi, H.-S., Lee, B., & Yoon, S. (2022). Towards a rigorous evaluation of time-series anomaly detection. *Proceedings of the AAAI Conference on Artificial Intelligence, 36*(7), 7194–7201. https://doi.org/10.1609/aaai.v36i7.20680
**Verified:** Opened the arXiv abstract page directly (confirming title, all 5 authors, and the core critique) and separately opened the official AAAI OJS page directly (confirming volume 36, issue 7, pages 7194–7201, 2022).
**Claim it supports:** The widely-used point-adjustment (PA) evaluation protocol for time-series anomaly detection is measurably broken: the paper shows even *random* anomaly scores achieve state-of-the-art-looking results under PA, meaning published rankings of anomaly detectors built on this protocol cannot be trusted at face value.
**What it changes in BEOPS:** If BEOPS builds or evaluates any anomaly-detection component on its city-pulse time series, it must not use point-adjusted F1 as the evaluation metric, or must report both PA and non-PA numbers explicitly and treat a large gap between them as a red flag — this is a direct, avoidable methodology bug the paper documents by name.

---

### 4. What current AI actually adds — verified, not hype

#### [C17] Chronos (time-series foundation model)
**APA:** Ansari, A. F., Stella, L., Turkmen, C., Zhang, X., Mercado, P., Shen, H., Shchur, O., Rangapuram, S. S., Pineda Arango, S., Kapoor, S., Zschiegner, J., Maddix, D. C., Wang, H., Mahoney, M. W., Torkkola, K., Wilson, A. G., Bohlke-Schneider, M., & Wang, Y. (2024). Chronos: Learning the language of time series. arXiv. https://arxiv.org/abs/2403.07815
**Verified:** Opened the arXiv abstract page directly. Confirmed title, all 17 authors, Amazon Science origin (via the linked code repository), and version history (v1 March 2024 through v3 November 2024). Confirmed the claim as stated: models "have comparable and occasionally superior zero-shot performance on new datasets, relative to methods that were trained specifically on them" — a claim about zero-shot transfer, not a claim of universal superiority. The page did not display an explicit software license; this should be checked directly against the model repository (not just the paper) before any deployment decision.
**Claim it supports:** A single transformer pretrained on tokenized time series can forecast previously-unseen series zero-shot at accuracy comparable to — not reliably better than — models trained specifically on that series.
**What it changes in BEOPS:** Candidate backbone for BEOPS's city-pulse forecasting, but "comparable... occasionally superior" is a modest, specific claim — BEOPS must benchmark Chronos zero-shot against a cheap task-specific baseline on its own Belgrade series before adopting it, not assume the paper's zero-shot results transfer to Belgrade-specific series with their own seasonal/administrative quirks.

#### [C18] TimesFM (time-series foundation model)
**APA:** Das, A., Kong, W., Sen, R., & Zhou, Y. (2024). A decoder-only foundation model for time-series forecasting. arXiv. https://arxiv.org/abs/2310.10688
**Verified:** Opened the arXiv abstract page directly. Confirmed title, all 4 authors (Google), and version history (October 2023–April 2024, v1–v4). Confirmed the claim as stated: zero-shot performance "comes close to the accuracy of state-of-the-art supervised forecasting models" — explicitly "comes close to," not "exceeds."
**Claim it supports:** Same category of claim as Chronos — competitive, not superior, zero-shot forecasting from a single pretrained decoder-only model.
**What it changes in BEOPS:** A second, independently-verified candidate for the same backbone slot as S17; the two should be benchmarked against each other and against Moirai/Lag-Llama (below) on BEOPS's own data rather than picked by paper reputation, since none of the four claims outright superiority over task-specific models.

#### [C19] Moirai (time-series foundation model)
**APA:** Woo, G., Liu, C., Kumar, A., Xiong, C., Savarese, S., & Sahoo, D. (2024). Unified training of universal time series forecasting transformers. arXiv. https://arxiv.org/abs/2402.02592
**Verified:** Opened the arXiv abstract page directly. Confirmed title, all 6 authors, Salesforce AI Research origin (via linked GitHub repo), version history (v1 Feb 2024, v2 May 2024), and the LOTSA pretraining corpus (27+ billion observations across nine domains).
**Claim it supports:** Same category as S17/S18 — strong zero-shot performance from one model trained across many domains simultaneously (a genuinely different architectural bet than Chronos/TimesFM's single-domain-agnostic tokenization).
**What it changes in BEOPS:** Third candidate; Moirai's explicit multi-domain training corpus may matter for BEOPS specifically since city pulses span genuinely different domains (traffic, air quality, social sentiment) in one system — worth testing whether Moirai's cross-domain training transfers better to a multi-domain city observatory than single-domain-trained alternatives.

#### [C20] Lag-Llama (probabilistic time-series foundation model)
**APA:** Rasul, K., Ashok, A., Williams, A. R., Ghonia, H., Bhagwatkar, R., Khorasani, A., Darvishi Bayazi, M. J., Adamopoulos, G., Riachi, R., Biloš, M., Garg, S., Schneider, A., Chapados, N., Drouin, A., Zantedeschi, V., Nevmyvaka, Y., & Rish, I. (2024). Lag-Llama: Towards foundation models for probabilistic time series forecasting. arXiv. https://arxiv.org/abs/2310.08278
**Verified:** Opened the arXiv abstract page directly. Confirmed title, all 17 authors, and version history (October 2023–February 2024, v1–v3). Confirmed it targets *probabilistic* forecasting specifically (distributions, not point forecasts) and that a comment on the page states "all data, models and code used are open-source."
**Claim it supports:** Same foundation-model-for-forecasting category, but with an explicit probabilistic (distributional) output rather than point forecasts — directly composable with the conformal-prediction approach in S15 for uncertainty-honest pulses.
**What it changes in BEOPS:** If BEOPS wants native uncertainty bands rather than bolting conformal prediction onto a point-forecaster, Lag-Llama's probabilistic framing is the more natural starting candidate of the four — this is a genuine architectural fork in the backbone decision, not just a fourth interchangeable option.

#### [C21] Small language models, not one large model, for agentic pipelines
**APA:** Belcak, P., Heinrich, G., Diao, S., Fu, Y., Dong, X., Muralidharan, S., Lin, Y. C., & Molchanov, P. (2025). Small language models are the future of agentic AI. arXiv. https://arxiv.org/abs/2506.02153
**Verified:** Opened the arXiv abstract page directly. Confirmed title, all 8 authors, NVIDIA affiliation, and — importantly — that the authors themselves explicitly frame this **as a position paper, not an empirical study**: "This is a value statement" seeking "contributions to and critique," not a benchmark result.
**Claim it supports:** Narrow, repetitive, well-specified sub-tasks inside an agentic pipeline are argued to be better served by small specialized models on both capability-fit and cost grounds, with general-purpose LLMs reserved for genuinely open-ended sub-tasks — but this is an argument, not a measured finding.
**What it changes in BEOPS:** Directly matches BEOPS's own stated architecture (small specialist CPU-first ONNX/GGUF models rather than one large model), which is valuable as external framing/validation of the design choice — but because the paper itself disclaims empirical rigor, it should be cited as **framing only** in the BEOPS paper, never as evidence that the architecture is measurably better; BEOPS's own ablations are the only thing that can actually support that claim.

#### [C22] Small, efficient models for retrieval-grounded fact-checking
**APA:** Tang, L., Laban, P., & Durrett, G. (2024). MiniCheck: Efficient fact-checking of LLMs on grounding documents. arXiv. https://arxiv.org/abs/2404.10774
**Verified:** Opened the arXiv abstract page directly. Confirmed title, all 3 authors, and version history (v1 April 2024, v2 October 2024). Confirmed the measured claim: a 770M-parameter model (MiniCheck-FT5) trained on GPT-4-synthesized examples "outperforms all systems of comparable size and reaches GPT-4 accuracy" at "400x lower cost," evaluated on a unified benchmark (LLM-AggreFact) the authors built by aggregating prior fact-checking datasets.
**Claim it supports:** A small, cheap, locally-runnable model can match a much larger proprietary model's fact-verification accuracy on the specific task of checking whether a claim is supported by a grounding document — the exact task shape BEOPS's SYNTHESIS problem needs (checking a generated city-pulse statement against its cited sources).
**What it changes in BEOPS:** Strong direct candidate for BEOPS's claim-verification step, and evidence that this does not require a large model to be run remotely — matching BEOPS's local-small-model constraint. Two related, independently-verified approaches worth comparing empirically rather than assuming interchangeable: Min, S., Krishna, K., Lyu, X., Lewis, M., Yih, W., Koh, P. W., Iyyer, M., Zettlemoyer, L., & Hajishirzi, H. (2023). FActScore: Fine-grained atomic evaluation of factual precision in long form text generation. In *Proceedings of EMNLP 2023* (confirmed directly via arXiv:2305.14251 — decomposes text into atomic facts and scores each against a knowledge source, rather than MiniCheck's single supported/unsupported judgment per claim-document pair); and Zha, Y., Yang, Y., Li, R., & Hu, Z. (2023). AlignScore: Evaluating factual consistency with a unified alignment function. In *Proceedings of ACL 2023* (confirmed directly via arXiv:2305.16739 — a 355M-parameter alignment model trained on 4.7M examples across 7 tasks). These three represent genuinely different mechanisms (atomic-fact decomposition, NLI-style alignment, and MiniCheck's own distilled-from-GPT-4 approach) and BEOPS should pick empirically, not by recency.

#### [C23] LLMs for entity matching: real gains, with a real caveat
**APA:** Peeters, R., Steiner, A., & Bizer, C. (2024). Entity matching using large language models. arXiv. https://arxiv.org/abs/2310.11244
**Verified:** Opened the arXiv abstract page directly. Confirmed title, all 3 authors, and latest version (v4, October 2024). Confirmed the measured finding: the best LLMs "require no or only a few training examples to perform comparably to" PLMs (e.g., BERT-family) fine-tuned on thousands of examples, with higher robustness to unseen entities — but also confirmed the explicit limitation: "there is no single best prompt but the prompt needs to be tuned for each model/dataset combination," i.e., not a drop-in, zero-effort solution.
**Claim it supports:** LLM-based entity matching can match fine-tuned classical approaches with far less labeled data, directly relevant to BEOPS's cross-source deduplication problem — but prompt sensitivity is a real, measured limitation, not a hypothetical one.
**What it changes in BEOPS:** Treat prompt design for entity matching as a per-source-pair tuning artifact that must be version-controlled and re-validated whenever a source's format changes, not a one-time prompt written once and trusted indefinitely. This tempers the more bullish claim in Narayan, A., Chami, I., Orr, L., & Ré, C. (2022). Can foundation models wrangle your data? (confirmed directly via arXiv:2205.09911, which claims foundation models "generalize and achieve SoTA performance on data cleaning and integration tasks" with less benchmarking of prompt sensitivity) — the two papers together are a useful positive/caveated pair for BEOPS to cite rather than either alone.

#### [C24] LLM inference is not actually deterministic, even at temperature zero
**APA:** Yuan, J., Li, H., Ding, X., Xie, W., Li, Y.-J., Zhao, W., Wan, K., Shi, J., Hu, X., & Liu, Z. (2025). Understanding and mitigating numerical sources of nondeterminism in LLM inference. arXiv. https://arxiv.org/abs/2506.09501
**Verified:** Opened the arXiv abstract page directly. Confirmed title and all 10 authors. Confirmed the measured finding: identical prompts under different batch sizes/GPU counts/GPU versions produce different outputs because floating-point arithmetic is not associative under limited precision, with one measured case showing "up to 9% variation in accuracy and 9,000 tokens difference in response length" purely from system configuration changes, not from any sampling randomness. Confirmed the authors' proposed mitigation (LayerCast: FP16 storage with FP32 compute) is presented as a working fix, not just a proposal.
**Claim it supports:** "Deterministic" LLM output (temperature = 0) is not actually deterministic in practice once batching, hardware, or serving configuration changes — a claim verification or data-cleaning result obtained once may not reproduce on a re-run with a different batch composition.
**What it changes in BEOPS:** Any BEOPS component that uses an LLM (small or large) for claim verification, entity matching, or synthesis needs its outputs treated as a distribution across runs, not a fixed answer — BEOPS should log the exact inference configuration (batch composition, precision, hardware) alongside any LLM-derived judgment it stores, and should not assume re-running the same verification step later will reproduce the same verdict without that configuration held fixed. This is the concrete, measured version of the brief's "honest limits: non-determinism under batching" concern.

---

### 5. Urban and geospatial foundation models: the honest state

#### [C25] Urban foundation models — survey and honest gaps
**APA:** Zhang, W., Han, J., Xu, Z., Ni, H., Lyu, T., Liu, H., & Xiong, H. (2024). Towards urban general intelligence: A review and outlook of urban foundation models. arXiv. https://arxiv.org/abs/2402.01749
**Verified:** Opened the arXiv abstract page directly. Confirmed title and all 7 authors. Confirmed the paper's scope: defining "Urban Foundation Models," a data-centric classification of urban research tasks, and a review of benchmarks/datasets in the space — i.e., a review/position paper, not itself a new model or a new empirical result. Note: I separately located, but did not open, a different, later paper titled "Urban Foundation Models: A Survey" (KDD 2024, DOI 10.1145/3637528.3671453) — the ACM page returned 403 to every fetch attempt, so I am citing the paper I could actually verify rather than the one I could only find via search.
**Claim it supports:** The urban-foundation-model field as of 2024 has coalesced around a shared vocabulary and taxonomy, but the survey itself frames this as an outlook/agenda rather than reporting that the promise has been delivered.
**What it changes in BEOPS:** Useful **framing only** — a shared vocabulary (which of BEOPS's "city pulses" map to which urban-FM task category) helps position the paper relative to this literature, but nothing in this survey should be cited as evidence that an urban foundation model is ready to replace BEOPS's fusion-of-existing-small-models approach.

#### [C26] Prithvi — a real, open, but narrow-domain geospatial foundation model
**APA:** Jakubik, J., Roy, S., Phillips, C. E., Fraccaro, P., Godwin, D., Zadrozny, B., Szwarcman, D., Gomes, C., Nyirjesy, G., Edwards, B., Kimura, D., Simumba, N., Chu, L., Mukkavilli, S. K., Lambhate, D., Das, K., Bangalore, R., Oliveira, D., Muszynski, M., ... Ramachandran, R. (2023). Foundation models for generalist geospatial artificial intelligence. arXiv. https://arxiv.org/abs/2310.18660
**Verified:** Opened the arXiv abstract page directly. Confirmed title and a 32-author list (NASA/IBM collaboration, released via Hugging Face). Confirmed the model (Prithvi) is "pre-trained on more than 1TB of multispectral satellite imagery" (Harmonized Landsat-Sentinel 2) and evaluated on cloud-gap imputation, flood mapping, wildfire segmentation, and crop classification — all remote-sensing/pixel-level tasks, not urban socio-economic indicator fusion.
**Claim it supports:** A genuinely open, well-documented geospatial foundation model exists and demonstrably improves specific satellite-imagery tasks — but its demonstrated scope is remote-sensing imagery, not the kind of tabular/administrative/social city data BEOPS mostly fuses. Two closely related 2024–2025 data points on the same lineage: IBM and ESA's successor model, Jakubik, J., Yang, F., Blumenstiel, B., Scheurer, E., Sedona, R., Maurogiovanni, S., Bosmans, J., Dionelis, N., Marsocci, V., Kopp, N., Ramachandran, R., Fraccaro, P., Brunschwiler, T., Cavallaro, G., Bernabe-Moreno, J., & Longépé, N. (2025). TerraMind: Large-scale generative multimodality for Earth observation. In *Proceedings of ICCV 2025* (confirmed directly via arXiv:2504.11171 — an any-to-any generative model across nine geospatial modalities, reporting state-of-the-art results on the PANGAEA benchmark below); and the Clay Foundation's "Clay" model, for which I could find **no peer-reviewed paper or technical report at all** (confirmed directly via the project's own documentation site: Apache-2.0-licensed, sponsored by the nonprofit Radiant Earth/Renaissance Philanthropy, but with no citable academic publication) — worth naming explicitly as a case where a geospatial foundation model has real community adoption and an open license but no verifiable peer-reviewed claims to cite.
**What it changes in BEOPS:** If BEOPS ever ingests satellite imagery directly (e.g., for land-use or green-space indicators), Prithvi/TerraMind are real, verifiable candidates for that specific sub-task — but this entire model family answers a different question than BEOPS's core fusion problem, and Clay specifically should not be cited as an academic reference in the paper at all, since none exists.

#### [C27] A published critique: geospatial foundation models do not consistently beat supervised baselines
**APA:** Marsocci, V., Jia, Y., Le Bellier, G., Kerekes, D., Zeng, L., Hafner, S., Gerard, S., Brune, E., Yadav, R., Shibli, A., Fang, H., Ban, Y., Vergauwen, M., Audebert, N., & Nascetti, A. (2024). PANGAEA: A global and inclusive benchmark for geospatial foundation models. arXiv. https://arxiv.org/abs/2412.04204
**Verified:** Opened the arXiv abstract page directly. Confirmed title and all 15 authors. Confirmed the paper's explicit finding: evaluating popular open geospatial foundation models against supervised baselines (U-Net, standard ViTs) across a deliberately geographically-diverse benchmark, the authors report that the foundation models "do not consistently outperform supervised models," particularly with limited labeled data.
**Claim it supports:** The specific, measured rebuttal the brief asked for — geospatial foundation models' zero/few-shot superiority claims do not hold up uniformly under an independent, diversity-aware benchmark; a plain supervised U-Net is sometimes just as good or better.
**What it changes in BEOPS:** If BEOPS ever considers adopting a geospatial FM for any imagery sub-task, this paper is the mandatory due-diligence citation before doing so — the correct baseline to beat is a cheap supervised model on BEOPS's own Belgrade imagery, not the foundation model's paper-reported numbers on its own benchmark. This is also a template BEOPS's own paper can point to methodologically: an independent, diversity-aware benchmark is what would be needed to make an equivalent claim about time-series foundation models (S17–S20), and I did not find a PANGAEA-equivalent benchmark for that family (see Gaps).

---

### Gaps

**Could not verify, despite specific attempts:**
- The specific, frequently-repeated claim that data scientists spend "80%" of their time on data cleaning (traced to a 2016 CrowdFlower/Figure Eight survey reported by Forbes journalist Gil Press). Both the original Forbes article and an archive.org mirror of it returned access-blocked errors to every automated fetch attempted. I could not confirm the survey's actual sample size, methodology, or exact percentage, and recommend the paper either drop this specific number or cite it explicitly as an unverified industry claim, using Kandel et al. (2012)'s peer-reviewed, directly-quoted interview finding instead as the credible anchor for the same point.
- The original source of the "4 Vs of Big Data" (Volume, Velocity, Variety, Veracity) framing. This is conventionally traced to a Doug Laney / META Group (now Gartner) 2001 industry research note, which is not peer-reviewed and which I did not attempt to verify since Wang & Strong (1996) already provides a stronger, peer-reviewed academic anchor for the "veracity/quality dimensions" point. Worth flagging explicitly in the paper as industry terminology, not an academic result, if BEOPS's paper uses the "4 Vs" language at all.
- The primary text of Openshaw & Taylor (1979) on the Modifiable Areal Unit Problem (see S06) — a pre-digital book chapter with no available online full text or DOI. Bibliographic metadata only, cross-confirmed via secondary aggregators.
- The full author list and interview-count methodology of Sambasivan et al. (2021) beyond what I could extract from the ACM full-text HTML I did open (see S10) — the paper's existence, DOI, venue, and core argument are solid; granular methodology details (exact number of practitioners/organizations interviewed) are not independently confirmed by me.

**Searched for but found no strong candidate at all:**
- An independent, diversity-aware benchmark for time-series foundation models (Chronos/TimesFM/Moirai/Lag-Llama) analogous to what PANGAEA (S27) does for geospatial foundation models — i.e., a paper systematically showing where simple, non-foundation baselines match or beat these four models in genuinely zero-shot settings. I found several unverified leads via search (a preprints.org zero/few/full-shot benchmark, an arXiv paper on TS-FMs as baselines in transportation forecasting) but did not open or verify any of them at the source, so none is included above. Given how directly this bears on BEOPS's own backbone choice, I'd flag this as the single most valuable follow-up search before the paper is finalized.
- A peer-reviewed academic (as opposed to grey-literature/industry) treatment of "deduplication across sources that secretly share one physical origin" as a named urban-open-data phenomenon specifically — i.e., literature addressing the case where two city open-data portals republish the same underlying municipal registry under different names/formats without disclosing the shared origin. General entity-resolution and data-fusion literature (S04, S12, S13) applies in principle, but I found nothing addressing this exact "hidden shared upstream" framing for city/government open data specifically.
- A published academic paper (rather than a benchmark leaderboard or blog post) specifically measuring LLM-based data-cleaning or entity-matching failure modes caused by evaluation-set contamination (i.e., the model having seen the benchmark's answers during pretraining) — I found general LLM-benchmark-contamination surveys (e.g., arXiv:2406.04244) but did not verify one that specifically ties contamination to the data-cleaning/entity-matching task family named in the brief, so I chose not to force a tangential citation into the bibliography.agentId: a5c7f40915de56c51 (use SendMessage with to: 'a5c7f40915de56c51', summary: '<5-10 word recap>' to continue this agent)
<usage>subagent_tokens: 214075
tool_uses: 86
duration_ms: 1215907</usage>

---


# PART D — Urban digital twins, city brains and comparative practice

## Urban Digital Twins, City Brains, and Comparative Practice — Verified Bibliography

### 1. Urban/city digital twins

#### [D01] Nature Computational Science critical review of urban digital twins
**APA:** Bettencourt, L. M. A. (2024). Recent achievements and conceptual challenges for urban digital twins. *Nature Computational Science, 4*(3). https://doi.org/10.1038/s43588-024-00604-9
**Type:** peer-reviewed evaluation
**Verified:** Opened the Nature.com landing page directly. Confirmed title, sole author (Bettencourt), journal, volume/issue (4(3)), and publication date (26 March 2024). Full text was not retrievable (abstract/metadata only), so the "twin vs. 3D-model-with-a-feed" distinction is not confirmed as explicit in-text; the abstract-level argument (cities' scale/heterogeneity create genuine computational-science-frontier obstacles, not just engineering ones) is confirmed.
**Claim it supports:** Even a Santa Fe Institute–style complexity scientist arguing *for* urban digital twins concludes that city-scale twins sit at an unresolved computational-science frontier, not a solved-engineering problem.
**What it changes in BEOPS:** Framing only — a citable, non-dismissive reason (from a proponent, not a critic) for BEOPS's explicit non-goal of building a full digital twin.

#### [D02] Digital twins for cities — the participation-gap survey
**APA:** van der Laag, C., Tan, W., Östh, J., & Benenson, I. (2026). Digital twins for cities: The rise of the socio-technical system. *Environment and Planning B: Urban Analytics and City Science, 53*(4). https://doi.org/10.1177/23998083261446012
**Type:** peer-reviewed evaluation
**Verified:** Opened the SAGE Journals DOI landing page directly. Confirmed title, four authors, journal, volume/issue (53(4)), year (2026), DOI. Content is framed as an editorial/synthesis piece introducing a special issue, built on the guest editors' own survey of digital-twin projects (not a single empirical study) — noting this hybrid status rather than presenting it as a standard empirical article.
**Claim it supports:** Surveyed digital twin deployments inform (78%) and consult (82%) communities far more often than they enable genuine participation in the underlying decisions.
**What it changes in BEOPS:** Vocabulary/data contract — every BEOPS "city pulse" should be labeled against an explicit inform/consult/decide scale rather than allowing "decision support" to be implied by default.

#### [D03] Herrenberg — the most-documented built urban digital twin
**APA:** Dembski, F., Wössner, U., Letzgus, M., Ruddat, M., & Yamu, C. (2020). Urban digital twins for smart cities and citizens: The case study of Herrenberg, Germany. *Sustainability, 12*(6), Article 2307. https://doi.org/10.3390/su12062307
**Type:** official self-report (peer-reviewed venue; authors are the team that built the system, University of Stuttgart/HLRS working with the city)
**Verified:** Opened the MDPI publisher page directly. Confirmed full author list, journal, volume/issue/article number, DOI. Confirmed the twin's five components (3D model, space-syntax street network, mobility simulation, wind-flow simulation, VGI/citizen data) and that the only outcome evidence offered is a citizen-perception survey (95–97% reporting a positive effect on "planning and participatory processes"), not a documented change to an actual planning decision.
**Claim it supports:** The most-cited concrete "urban digital twin" is, by its own creators' account, a visualization-and-simulation prototype whose evidence base is a perception survey, not a measured planning-outcome change.
**What it changes in BEOPS:** Data contract — BEOPS's observation/forecast/model-estimate/unavailable taxonomy should add an explicit "perception improved" category distinct from "decision changed," with Herrenberg as the citable example of the former claimed as if it were the latter.

#### [D04] Zurich — digital twin as open-data distribution layer
**APA:** Schrotter, G., & Hürzeler, C. (2020). The digital twin of the city of Zurich for urban planning. *PFG – Journal of Photogrammetry, Remote Sensing and Geoinformation Science, 88*(1), 99–112. https://doi.org/10.1007/s41064-020-00092-2
**Type:** official self-report (peer-reviewed venue; authors are City of Zurich geomatics/planning officials)
**Verified:** Opened the Springer full-text page directly (after a redirect). Confirmed authors, journal, volume/issue/pages, DOI. Confirmed the 3D model covers 50,000+ buildings, is used for cold-air-flow/climate simulation, citizen participation tools (including a Minecraft version), and architecture-competition review — and that the authors' own headline usage metric is that nearly a third of the city's open-data-portal downloads came from the twin's underlying 3D datasets.
**Claim it supports:** A well-resourced municipal digital twin's own authors report its clearest measured impact as open-data download volume, not a documented planning decision.
**What it changes in BEOPS:** Design decision — supports publishing BEOPS's layered "pulses" directly as open data rather than gating them behind a 3D viewer, since even Zurich's own reported success metric is downloads of the underlying data.

#### [D05] Rotterdam — independent critique of participation "limits-by-design"
**APA:** De Jaeger, A., & Swerts, T. (2026). Right to the digital Twin City? Citizen participation and limits-by-design in Rotterdam's urban digital twin. *Cities, 168*, Article 106498. https://doi.org/10.1016/j.cities.2025.106498
**Type:** peer-reviewed evaluation (independent — authors are Erasmus University Rotterdam/Centre for BOLD Cities researchers, not the twin's builders)
**Verified:** ScienceDirect blocked the full page by robots.txt and a re-fetch attempt (SSRN preprint mirror) was rate-limited (429), so full-text content is **not independently confirmed**. Bibliographic metadata (title, authors, journal *Cities*, volume 168, article 106498, DOI 10.1016/j.cities.2025.106498) was cross-checked via the Crossref API against the ScienceDirect PII and against the authors' own institutional pages and a LinkedIn post by the lead author describing the paper's topic (citizen participation constrained by the twin's technical design choices). Treat the specific argument as **plausible but not directly verified from primary text**.
**Claim it supports:** Independent (non-vendor) urban-planning scholarship finds that a digital twin can structurally limit citizen participation through its design choices ("limits-by-design"), independent of surrounding policy.
**What it changes in BEOPS:** Design decision — if BEOPS ever adds a citizen-facing query/annotation layer, "who can challenge or add to the data" should be an explicit, evaluated design decision rather than an assumed side-effect of publishing data.

#### [D06] DUET — the EU's flagship "urban twin for decision-making" project
**APA:** European Commission, CORDIS. (n.d.). *Digital Urban European Twins for smarter decision making (DUET)* [Project record, Grant Agreement No. 870697]. https://cordis.europa.eu/project/id/870697
**Type:** official self-report
**Verified:** Opened the CORDIS project page directly. Confirmed official title, project ID, coordinator (Flanders Region), 15 partner organizations, H2020 funding line, duration (Dec 2019–Nov 2022), and total/EU funding (€4.52M/€3.97M). Confirmed self-described deliverable: a "Policy-Ready-Data-as-a-Service" 3D interface for simulating traffic/pollution/noise policy across three pilot cities (Athens, Pilsen, Flanders). No independent (non-project) evaluation of decision impact was found (see Gaps).
**Claim it supports:** The EU's own named "urban digital twin for smarter decision making" project documents technical delivery across three pilots in its official record, not an independently measured decision or policy-outcome impact.
**What it changes in BEOPS:** Framing/vocabulary — DUET's own vocabulary ("Policy-Ready-Data-as-a-Service", policy simulation) is useful precisely as a contrast: BEOPS explicitly does not simulate policy decisions, only fuses and labels observations, and can cite DUET as the EU-standard alternative it is deliberately not building.

### 2. "City brain" / city operating system deployments

#### [D07] Hangzhou City Brain — independent platform-urbanism analysis
**APA:** Caprotti, F., & Liu, D. (2022). Platform urbanism and the Chinese smart city: The co-production and territorialisation of Hangzhou City Brain. *GeoJournal, 87*(3), 1559–1573. https://doi.org/10.1007/s10708-020-10320-2
**Type:** peer-reviewed evaluation
**Verified:** Opened via PubMed Central (PMC7607375) and confirmed full citation (journal, volume/issue/pages, DOI, online-first Nov 2020). Confirmed this is a conceptual/theoretical platform-urbanism analysis of governance, data control, and Alibaba–municipality co-production — **it does not independently verify or refute Alibaba's own quantitative traffic-improvement claims**; it critiques the governance arrangement, not the performance numbers.
**Claim it supports:** Independent academic scholarship on Hangzhou's City Brain analyzes it as privately co-produced urban governance infrastructure with asymmetric control, without validating the specific efficiency numbers the deployment is famous for in press coverage.
**What it changes in BEOPS:** Vocabulary/framing — BEOPS should explicitly state it is not a platform-urbanism arrangement (no single vendor holding city-wide sensor/data/decision control) and can cite this paper as the scholarly articulation of the governance risk that design choice avoids.

#### [D08] Barcelona — Sentilo platform and the "technological sovereignty" turn
**APA:** Mann, M., Mitchell, P., Foth, M., & Anastasiu, I. (2020). #BlockSidewalk to Barcelona: Technological sovereignty and the social license to operate smart cities. *Journal of the Association for Information Science and Technology, 71*(9), 1103–1115. https://doi.org/10.1002/asi.24387
**Type:** peer-reviewed evaluation
**Verified:** Bibliographic details confirmed via Crossref-indexed record (RePEc mirror) matching journal, volume/issue/pages, DOI, and abstract (Sidewalk Labs Toronto vs. Barcelona's Digital City plan as a technological-sovereignty contrast). Separately opened the official Barcelona City Council Sentilo page directly: confirmed Sentilo is open-source, city-owned middleware (any city can redeploy it), won a 2016 Open Award, and aggregates sensor feeds (bike/pedestrian flow, noise, temperature, air quality) — the council page itself does not use the phrase "technological sovereignty," which is the academic framing of the policy this platform instantiates.
**Claim it supports:** Barcelona's open-source, municipally-owned Sentilo platform is the concrete technical instantiation of a "technological sovereignty" policy that peer-reviewed literature treats as a genuine alternative to vendor-controlled platform urbanism.
**What it changes in BEOPS:** Standards/architecture decision — supports BEOPS using or mirroring a self-hostable, open-source sensor/data bus (Sentilo-like) rather than a proprietary "city brain" stack, consistent with its own local-model, non-vendor-locked design.

#### [D09] Amsterdam/Helsinki public AI/algorithm registers
**APA:** City of Amsterdam. (n.d.). *Public AI registers*. Amsterdam Open Research. https://openresearch.amsterdam/en/page/73074/public-ai-registers
**Type:** official self-report
**Verified:** Opened directly. Confirmed the registers were built by Helsinki, Amsterdam, and transparency-platform vendor Saidot; confirmed the schema (purpose, accountability, datasets, data processing, non-discrimination, human oversight, risk mitigation, explainability, including the system's eventual "dismantling"). The page contains **no published evaluation** of real-world effectiveness — it is aspirational/promotional in tone. Broader search (Open Government Partnership, academic databases) found NGO/advocacy assessments but no peer-reviewed effectiveness study (see Gaps).
**Claim it supports:** City-run public AI registers exist as a concrete, replicable governance instrument with a defined schema, but their real-world effectiveness as transparency mechanisms is, as of 2026, still unevaluated in the published literature.
**What it changes in BEOPS:** Governance artifact/vocabulary — BEOPS should publish an equivalent register (one row per model/pulse: purpose, inputs, human oversight, known limitations, retirement plan) modeled directly on this schema, while the paper should not claim registers are proven effective — only that they are an available, documented instrument.

### 3. Environmental & risk sensing at city scale

#### [D10] Low-cost air-quality sensor network calibration
**APA:** deSouza, P., Kahn, R., Stockman, T., Obermann, W., Crawford, B., Wang, A., Crooks, J., Li, J., & Kinney, P. (2022). Calibrating networks of low-cost air quality sensors. *Atmospheric Measurement Techniques, 15*(21), 6309–6328. https://doi.org/10.5194/amt-15-6309-2022
**Type:** peer-reviewed evaluation
**Verified:** Opened the Copernicus/AMT full-text article directly. Confirmed authors, journal, volume/issue/pages, DOI. Confirmed the study evaluated 89 calibration models on Denver's 24-sensor "Love My Air" school network, and found ML calibrations do not reliably transfer across space/time, and short (2-week) co-location calibrations can perform *worse than no correction at all*.
**Claim it supports:** Calibration models for low-cost air-quality sensor networks are not reliably transferable across locations or seasons, and inadequate co-location periods can actively degrade data quality relative to raw readings.
**What it changes in BEOPS:** Data contract/experiment — BEOPS's air-quality pulse should specify a minimum reference-station co-location duration and a transferability check (per this paper's C1–C4 scheme) before any calibrated sensor reading is labeled "observation" rather than "unavailable/uncertain."

#### [D11] Mobile urban heat island monitoring
**APA:** Kousis, I., Pigliautile, I., & Pisello, A. L. (2021). Intra-urban microclimate investigation in urban heat island through a novel mobile monitoring system. *Scientific Reports, 11*. https://doi.org/10.1038/s41598-021-88344-y
**Type:** peer-reviewed evaluation
**Verified:** Opened the Nature.com/Scientific Reports full-text page directly. Confirmed authors, journal, year, DOI. Confirmed the vehicle-mounted, five-directional-sensor mobile methodology (Perugia, Italy) and the ~1.5°C intra-urban temperature differential found between suburban and dense-core areas that a fixed network would likely average away.
**Claim it supports:** Mobile (vehicle-based) sensing campaigns reveal intra-urban heat-island variation that sparse fixed-station networks do not capture.
**What it changes in BEOPS:** Experiment design — if BEOPS adds a heat pulse, budget for at least one low-cost mobile-sensing validation campaign rather than relying solely on fixed stations, following this study's directional-sensor design.

#### [D12] Urban seismic networks — worldwide inventory
**APA:** Scudero, S., Costanzo, A., & D'Alessandro, A. (2023). Urban seismic networks: A worldwide review. *Applied Sciences, 13*(24), Article 13165. https://doi.org/10.3390/app132413165
**Type:** peer-reviewed evaluation
**Verified:** Opened the MDPI publisher page directly (after DOI redirect). Confirmed authors, journal, volume/issue/article number, DOI. Confirmed the review catalogs 100+ urban seismic networks across 37 countries (1994–2023), concentrated in the USA, Italy, and Turkey, and that the paper offers **design guidance, not a measured decision/outcome evaluation** of any network's real-world effectiveness.
**Claim it supports:** Urban seismic/structural monitoring networks are a mature, globally widespread instrument category, but the published literature on them is dominated by design and inventory work rather than measured decision-impact evaluation.
**What it changes in BEOPS:** Framing only — the *absence* of impact evaluation in even this mature domain supports BEOPS's cautious, evidence-first posture: publish what is observed, and do not imply that sensing alone constitutes an evaluated safety improvement.

#### [D13] Ahr Valley 2021 flood — when the decision layer, not the sensor layer, fails
**APA:** Rhein, B., & Kreibich, H. (2025). Causes of the exceptionally high number of fatalities in the Ahr valley, Germany, during the 2021 flood. *Natural Hazards and Earth System Sciences, 25*(2). https://doi.org/10.5194/nhess-25-581-2025
**Type:** peer-reviewed evaluation
**Verified:** Opened the Copernicus/NHESS full-text article directly. Confirmed authors, journal, volume/issue, DOI. Confirmed specific figures: 134 of 190 German flood deaths concentrated in the Ahr valley; 29% of affected Rhineland-Palatinate residents received no warning at all; the official evacuation order came at 23:09 on 14 July 2021, after floodwaters were already dangerously high; 75% of deaths occurred outside officially mapped hazard zones; the elderly were 80% of fatalities.
**Claim it supports:** In Europe's deadliest recent urban/regional flood, hydrological forecasting existed, but the warning-dissemination and evacuation-decision layer failed catastrophically — underestimation, late warnings, and non-receipt, not absent sensors, drove the death toll.
**What it changes in BEOPS:** Design decision — the strongest single citation for BEOPS's core observation/forecast/model-estimate/unavailable separation, and for treating "alert delivered and acknowledged" as its own measured pipeline stage rather than an assumed consequence of publishing a forecast.

#### [D14] Ahmedabad Heat Action Plan — aggregate success, distributional communication failure
**APA:** Nastar, M. (2020). Message sent, now what? A critical analysis of the heat action plan in Ahmedabad, India. *Urban Science, 4*(4), Article 53. https://doi.org/10.3390/urbansci4040053
(Companion citation, verified separately: Hess, J. J., Mavalankar, D., Azhar, G. S., et al. (2018). Building resilience to climate change: Pilot evaluation of the impact of India's first heat action plan on all-cause mortality. *Journal of Environmental and Public Health, 2018*, Article 7973519. https://doi.org/10.1155/2018/7973519)
**Type:** peer-reviewed evaluation
**Verified:** Opened the MDPI *Urban Science* article directly — confirmed sole author, journal, volume/issue/article number, DOI, and its finding that despite multi-channel warnings (SMS/WhatsApp/email), ~37% of Ahmedabad residents lack constant mobile access, field interviews found frontline workers "had seldom heard about the HAP," and 92% lack reliable water access to act on heat advice. Separately opened the Hindawi mirror of Hess et al. directly — confirmed authors, journal, article ID, and its quantitative finding of an estimated 1,190 annualized deaths avoided post-implementation (relative risk at 47°C fell from 2.34 to 1.25).
**Claim it supports:** The same early-warning programme can be both a measured population-level mortality success (Hess et al.) and, per independent qualitative fieldwork, a communication failure for its most vulnerable subpopulation (Nastar) — aggregate outcome improvement does not imply universal warning delivery.
**What it changes in BEOPS:** Experiment/vocabulary — any future BEOPS alerting feature should track "warning issued" and "warning received/actionable-by-recipient" as two separately measured states, following this paired aggregate-vs-distributional citation logic.

### 4. Urban observatories as institutions

#### [D15] UK Urban Observatories programme (Newcastle, Birmingham, Manchester)
**APA:** Newcastle University, University of Birmingham, & University of Manchester. (2021). *Urban Observatories sensor report* (data snapshot 13 December 2021). https://assets.publishing.service.gov.uk/media/62ba0adf8fa8f57214d717a1/urban-observatories-sensor-report.pdf
**Type:** official self-report
**Verified:** Opened the report PDF directly (gov.uk-hosted). Confirmed sensor counts by city (Newcastle 1,564; Manchester 492; Birmingham 193; total 2,146), open API/JSON-LD/CSV access, an explicit no-PII policy, CCTV auto-deletion after processing, and institutional DPIA governance. Separately opened the UKCRIC Newcastle Urban Observatory page directly: confirmed it publishes "the largest set of publicly available real-time urban data in the UK," refreshed second-by-second, via API/download, described as "open-data" — **no specific licence name (e.g., OGL, CC-BY) was confirmed on either page** (see Gaps).
**Claim it supports:** A real, multi-city, university-run urban-observatory programme operates thousands of low-cost sensors publishing open real-time data under documented privacy/ethics governance (DPIA, no-PII, CCTV auto-deletion) — a working precedent, not a proposal.
**What it changes in BEOPS:** Governance/data-contract template — BEOPS can cite this as direct precedent for its own "evidence-first, no person-level analysis" stance, and should adopt the observatories' own caveat language ("interpret as a set for city-wide analysis, not a single point in time/location") as boilerplate for its low-cost-sensor pulses.

#### [D16] MIT Senseable City Lab — Trash Track and LIVE Singapore
**APA:** Phithakkitnukoon, S., Wolf, M. I., Offenhuber, D., Lee, D., Biderman, A., & Ratti, C. (2013). Tracking trash. *IEEE Pervasive Computing, 12*(2), 38–48. https://doi.org/10.1109/mprv.2013.37
(Companion citation, verified separately: Kloeckl, K., Senn, O., & Ratti, C. (2012). Enabling the real-time city: LIVE Singapore! *Journal of Urban Technology, 19*(2), 89–112. https://doi.org/10.1080/10630732.2012.698068)
**Type:** peer-reviewed evaluation (project-team authored — treat as insider-reported empirical results, not independent evaluation)
**Verified:** Opened the official senseable.mit.edu Trash Track page and the linked paper PDF directly; bibliographic details (journal, volume/issue/pages, DOI) confirmed via Crossref. Confirmed key figures: 1,152 of 1,977 deployed tags returned valid traces; >95% reached a "compliant" end destination but **fewer than 10% reached the facility specified in the municipal disposal contract**; e-waste was traced to Vancouver and beyond. For LIVE Singapore, opened the official MIT project page directly (confirms real-time multi-source data aggregation for public visualization) and confirmed the Journal of Urban Technology citation via Crossref API directly, though the paper's own full text was not retrievable (paywalled).
**Claim it supports:** Tagging/tracking consumer waste at city scale can surface concrete, previously invisible logistics facts (e.g., large gaps between contracted and actual disposal routing) using only observation and visualization — no predictive model required.
**What it changes in BEOPS:** Framing/vocabulary — a citable precedent that a purely observational pulse (no model layer) can be independently valuable and can surface uncomfortable contract-compliance findings, worth anticipating if BEOPS ever adds a Belgrade waste/logistics pulse.

#### [D17] MIT Underworlds — sewage biosurveillance, critically examined
**APA:** Reis-Castro, L. (2017). The Underworlds project and the "collective microbiome": Mining biovalue from sewage. In *Bioeconomies* (pp. 105–127). Springer International Publishing / Palgrave Macmillan. https://doi.org/10.1007/978-3-319-55651-2_5
**Type:** peer-reviewed evaluation (independent critical/STS analysis, not the project team)
**Verified:** Confirmed full citation (author, book title, page range 105–127, publisher, DOI) via Crossref API directly. Confirmed via earlier fetch of the chapter's content that it critically analyzes how sewage is transformed into a "collective microbiome" proxy for population health surveillance, situating it within histories of turning waste into value and questioning what population-level legibility the technique enables.
**Claim it supports:** Aggregate, technically-anonymized wastewater/city-scale biosurveillance still renders a population "legible" in ways that raise ethical questions distinct from (and not resolved by) individual-level anonymization.
**What it changes in BEOPS:** Vocabulary/ethics framing — directly relevant if BEOPS ever considers a wastewater or other aggregate-biological pulse: supports writing an explicit population-legibility/consent paragraph even where no individual is identifiable.

#### [D18] Chicago Array of Things — design, open-data commitment, and stalled deployment
**APA:** Catlett, C. E., Beckman, P. H., Sankaran, R., & Galvin, K. K. (2017). Array of things: A scientific research instrument in the public way: Platform design and early lessons learned. In *Proceedings of the 2nd International Workshop on Science of Smart City Operations and Platforms Engineering* (pp. 26–33). ACM. https://doi.org/10.1145/3063386.3063771
**Type:** peer-reviewed evaluation (project-team authored — insider self-report of design/lessons, not independent evaluation)
**Verified:** Opened an author-hosted PDF mirror directly; bibliographic details (authors, venue, page range, DOI) confirmed via Crossref API directly. Confirmed the NSF-cooperative-agreement commitment to fully open, non-monetized data via the open-source Plenario platform and Waggle firmware, and documented manufacturing/QC failures (a 2mm heat-sink miscalculation damaged CPUs during thermal cycling). Separately confirmed via the project's own FAQ (accessed directly) that as of November 2020 only ~130 of a planned 150+ nodes were deployed, installations were COVID-halted, and the project was piloting a next-generation "SAGE" node platform from 2021 onward. **No formal decommissioning/wind-down report was located** — the shift to "SAGE" branding is the strongest available evidence that the original Array of Things network was effectively superseded rather than completed (see Gaps).
**Claim it supports:** A well-funded, technically serious city-sensing instrument can commit convincingly to open data and open-source firmware up front, and still fall well short of its planned physical deployment scale for reasons (funding cycles, pandemic disruption, hardware QC) unrelated to the data-openness commitment itself.
**What it changes in BEOPS:** Data contract/procurement lesson — supports drafting BEOPS's open-data and no-monetization commitments up front (as Chicago did), while budgeting realistically against the same deployment/QC risks this paper documents, rather than assuming a sensor network reaches its planned scale on schedule.

### 5. Standards and interoperability for city data

#### [D19] OGC SensorThings API
**APA:** Open Geospatial Consortium. (2021). *OGC SensorThings API Part 1: Sensing, Version 1.1* (OGC 18-088). https://docs.ogc.org/is/18-088/18-088.html
**Type:** standard
**Verified:** Opened the official OGC standard page directly. Confirmed version history (v1.0 → v1.1 current → Part 2 Tasking → STAplus and WebSub extensions, plus a v2.0 draft out for public comment), and that OGC runs a formal compliance/certification programme with a public "Implementations by Standard" registry. The page does not itself state adoption *rates* (see Gaps).
**Claim it supports:** SensorThings API is a mature, actively extended OGC standard purpose-built for IoT sensor observations and metadata, with a formal conformance program — not an ad hoc REST convention.
**What it changes in BEOPS:** Data contract — BEOPS should adopt SensorThings (or explicitly justify a deviation) as the wire format for its sensor-observation layer, using OGC's own certification bar as the compliance target rather than inventing a bespoke schema.

#### [D20] NGSI-LD / FIWARE / ETSI CIM
**APA:** ETSI. (2019, January). *ETSI CIM group releases full-feature specification for context information exchange in smart cities* [Press release/standard announcement, GS CIM 009 NGSI-LD API]. https://www.etsi.org/newsroom/press-releases/1519-2019-01-etsi-cim-group-releases-full-feature-specification-for-context-information-exchange-in-smart-cities
**Type:** standard
**Verified:** Opened the official ETSI press release directly. Confirmed the ETSI Industry Specification Group for Context Information Management (ISG CIM) released GS CIM 009 (NGSI-LD), built explicitly on FIWARE's NGSIv2 community experience plus JSON-LD/Linked Data conventions, with the ISG chair quoted that smart cities are the intended first beneficiary because NGSI-LD is meant to "glue together" existing siloed municipal databases (the announcement's own example: linking a vehicle record to a hospital record).
**Claim it supports:** NGSI-LD is an ETSI-ratified (not merely vendor-proprietary) standard explicitly designed to link data across otherwise-siloed city domains.
**What it changes in BEOPS:** Data contract/vocabulary — if BEOPS ever needs to link entities across its own pulses (e.g., a traffic-incident pulse to an air-quality pulse), NGSI-LD is the standard vocabulary to adopt or explicitly reject in the paper, rather than building ad hoc joins.

#### [D21] GTFS/GTFS-Realtime real-world adoption
**APA:** Voulgaris, C. T., & Begwani, C. (2023). Predictors of early adoption of the General Transit Feed Specification. *Findings*. https://doi.org/10.32866/001c.57722
**Type:** peer-reviewed evaluation
**Verified:** Opened the Findings journal article directly. Confirmed authors, journal, DOI, and its logistic-regression analysis of 471 transit agencies: higher ridership and smaller regional market share (i.e., greater need for cross-agency coordination) predicted early GTFS adoption, while agency size was a weaker predictor than expected; by June 2022 ~75% of US transit agencies had adopted GTFS — sixteen years after its 2006 introduction. Separately opened the official gtfs.org page directly, confirming MobilityData now stewards the spec, claiming 10,000+ agencies in 100+ countries, and that GTFS-Realtime (vehicle positions/arrivals/alerts) is a distinct extension layered on the static GTFS schedule format. **No dedicated peer-reviewed adoption study specific to the GTFS-Realtime extension** (as opposed to static GTFS) was located (see Gaps).
**Claim it supports:** Even a free, technically simple, widely-praised open transit-data standard took over a decade to reach ~75% adoption among the agencies it targeted, and adoption speed correlated with coordination need, not agency size.
**What it changes in BEOPS:** Expectation-setting/experiment design — BEOPS should budget years, not months, for a reliable Belgrade GTFS(-Realtime) feed to exist and stay current, and should log feed presence/freshness as an empirical, periodically-rechecked fact rather than assume it once confirmed.

#### [D22] INSPIRE directive — the European Commission's own adoption evaluation
**APA:** COWI, Milieu, & Technopolis Group. (2021). *Evaluation of the INSPIRE Directive (2007/2/EC): Draft final report* (prepared for the European Commission). EuroGeographics. https://eurogeographics.org/app/uploads/2021/09/INSPIRE-evaluation-Draft-Final-Report-August-2021.pdf
**Type:** official self-report (independent consultants, Commission-commissioned institutional evaluation — not academic peer review)
**Verified:** Opened the report PDF directly. Confirmed commissioning consultants (COWI, Milieu, Technopolis Group), August 2021 date, and quantitative findings from 2020 monitoring data: only 59% of registered spatial-dataset metadata met interoperability standards, only 50% of datasets themselves met interoperability conformity, only 42% were accessible via view/download services, and the report states explicitly that "information on use and users is too scarce to provide a clear overview" of real-world impact.
**Claim it supports:** More than a decade after adoption, the EU's own commissioned evaluation found only about half of INSPIRE-registered geospatial datasets actually met interoperability conformity, and could not even characterize who was using the data or how.
**What it changes in BEOPS:** Design decision/expectation-setting — BEOPS should not treat "INSPIRE-conformant" as a guarantee of usable data for any external Serbian/EU geospatial source; each source should be spot-checked for actual conformity and freshness rather than trusted by directive-membership alone.

---

### Gaps

**Famous deployments with no independent evaluation found (only official/vendor/press material):**
- **Virtual Singapore** — extensive official description (Singapore Land Authority, via the OECD Observatory of Public Sector Innovation page, opened directly) claims uses in "urban planning, infrastructure management, and disaster preparedness," but **no independent peer-reviewed evaluation of any actual decision made using the system was found**, despite specific search for one. The OPSI page itself is self-described as case-study material, not evaluation.
- **Helsinki/Kalasatama digital twin** — an apparently relevant peer-reviewed paper (*IET Smart Cities*, "Urban development with dynamic digital twins in Helsinki city") was identified by title/venue in search results, but **two direct-fetch attempts both failed (403)**, and no alternate open copy was found. Its content is therefore **not verified** and is excluded from the numbered list rather than cited on title alone. Only the city's own open 3D-data pages were confirmed as an official source.
- **DUET's decision impact** — the official CORDIS record (S06) documents technical delivery across three pilot cities; no independent, non-project evaluation of whether DUET's simulations actually changed a real policy decision was found.

**Alibaba City Brain's specific quantitative claims** — every quantitative traffic/efficiency figure surfaced in searching (e.g., congestion-index improvements, ambulance-response-time cuts) traced back to Alibaba's own blog/press material or to government (ehangzhou.gov.cn) and press (CNN, China Daily, The Week) restatements of those same figures. The one peer-reviewed academic source located that engages critically with City Brain (Caprotti & Liu, S07) is a governance/platform-studies analysis that does **not** independently remeasure the traffic claims. One additional paper turned up in search ("Optimizing Urban Mobility in Hangzhou," hosted on an obscure institutional repository) was not pursued for verification because the venue could not be confirmed as a serious peer-reviewed journal. **No independent, methodologically transparent remeasurement of Alibaba's own performance claims was found anywhere in the literature searched** — this absence is itself worth stating plainly in the paper, given how frequently these figures are repeated as fact.

**Herrenberg's Gemini/FAIR-principles critique** — a paper titled "Demystifying urban digital twins: Evaluating the case of Herrenberg through the lens of the Gemini and FAIR data Principles" appears repeatedly in search results (via ResearchGate) and looks like exactly the kind of independent critical re-assessment the brief asks for, but its ResearchGate page could not be loaded (rate-limited twice) and a Crossref bibliographic search could not locate a matching DOI/journal record. **Excluded from the numbered list rather than cited from a title alone.**

**"CityOS: Privacy Architecture for Urban Sensing"** (arXiv, apparently 2026) surfaced in search as a proposed privacy-preserving three-tier API architecture directly relevant to BEOPS's own design instincts, but two fetch attempts both returned empty/unparseable content, so its existence and content could not be confirmed. **Excluded as unverified** rather than risk citing a possibly-malformed or hallucinated identifier.

**Smart Citizen Kit / Making Sense EU project** — a plausible peer-reviewed reference (an open-hardware environmental-monitoring paper, ScienceDirect/HardwareX-family) was identified, but full-text access was blocked (429/robots.txt) on every attempt within the time available. **Excluded rather than cited without having opened it.**

**Chicago Array of Things' formal wind-down** — no single decommissioning report or "end of project" announcement was found. The strongest evidence of wind-down is indirect: the project's own FAQ (accessed directly) shows deployment stalled around 130–140 of a planned 150+ (originally up to ~500) nodes as of late 2020, compounded by COVID-19, with the team piloting a differently-branded "SAGE" hardware platform from 2021 — suggesting evolution/supersession rather than a clean continuation, but this is an inference, not a confirmed fact.

**Specific open-data licences** — both the Newcastle/UK Urban Observatories pages and the Array of Things FAQ assert "open data" but neither states a specific licence name (Open Government Licence, CC-BY, etc.) on the pages actually opened; BEOPS should not assume a specific reuse licence for either without checking the underlying data portal terms directly.

**GTFS-Realtime-specific adoption research** — the one adoption study verified (Voulgaris & Begwani, S21) covers static GTFS adoption; no equivalent peer-reviewed adoption study specific to the GTFS-Realtime extension was located.

**Amsterdam/Helsinki AI register effectiveness** — beyond the registers' own descriptive white paper, searches turned up only advocacy/NGO assessments (Open Government Partnership's "State of the Evidence: Algorithmic Transparency"; a Spanish civic-tech report) rather than a peer-reviewed academic evaluation of whether the registers change real governance outcomes. As of 2026, roughly six years after launch, this remains an unevaluated governance instrument in the scholarly literature.

---
