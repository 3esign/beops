Status: historical
Date: 2026-09-06
Author: Codex procurement / infrastructure lane

# Belgrade infrastructure as physical senses

The strongest new lead for a local live sense is the Mihajlo Pupin campus solar plant and its weather instruments. Its operator documents commissioning and browser access, but this review did not locate a working public readout with a measurement timestamp. EPS supplies actual annual local environmental measurements; EDS supplies a substantial installed-meter census. These findings should not increase the count of verified live feeds.

Five instrument/product leads below belong to four operational settings. TENT emissions and water share the same operator and 2024 report; they are distinct products, not independent source confirmations. Airport noise was handed to the hydromet lane and is not counted here.

## Evidence table

| Lead / physical phenomenon | Transducer and place | Strongest inspected primary evidence | Measurement time versus publication time | Cadence and latency | Access / reuse |
| --- | --- | --- | --- | --- | --- |
| **Pupin campus solar and weather** — electricity production, irradiance, wind and temperature | Rooftop PV plant, energy meter, inverter telemetry, weather sensors, pAtlas acquisition units; Mihajlo Pupin Institute campus, Belgrade | Operator says connected on **2013-09-20**, approximately 50 kW and 180 panels; browser live/archive capability described. [P1] | No actual sample timestamp obtained. Announcement **2013-09-23**; a **2025-07-28** operator article discusses the existing plant and planned living-lab adaptation. [P2] | Described as real-time; numerical sampling interval, public latency and present availability unknown | Public descriptive pages. Exact public data URL unresolved. No dataset licence established; project footer reserves rights. |
| **TENT stack emissions** — emitted gases and particles | CEMS gas/particle analysers at TENT A/B, Obrenovac; acquisition/processing equipment | Installation completed November 2011; calibration work March–April 2013. [E1] The 2024 report contains annual measurement results and equipment inventory, Tables 70–72, printed pages 83–85. [E2] | Measurement year **2024**; report **March 2025**. No current reading obtained | Continuous measurement at source; published product annual. No live public endpoint established | Public operator PDF; no explicit reuse licence established. Separate from BCE/Vinča CEMS S184. |
| **TENT water volumes and treatment performance** — water flow and effluent chemistry | Flowmeters for groundwater and sanitary effluent; laboratory sampling of treatment inflow/outflow at TENT A/B, Obrenovac | Tables 77–78, printed page 98, contain treatment results and annual water quantities. Direct flowmeter readings are distinguished from quantities calculated from pump capacity and runtime. [E2] | **2024**, published **March 2025**. TENT B treatment results cover Q1 only | Annual published totals/ranges; some quarterly chemistry. No present stream/latency established | Same public report, same unresolved reuse scope as emissions. It is one shared publication, not another independent source. |
| **EDS Belgrade smart-meter deployment** — electric energy and voltage-loss/fault events | Smart meters in the Belgrade distribution area, including Beograd–Centar, Banovo brdo and Zemun branches; no household identifiers | September 2024 operator magazine reports **377,350 installed replacement meters** in the Belgrade distribution area. [D1] | This is a **September 2024 installation census**, not a measurement series. No latest energy reading obtained | Operator describes several readings daily into its internal system; no public aggregate cadence or latency established | Magazine public; operator explicitly describes restricted employee access to readings. Only deployment totals retained. No account or household readings sought. |
| **Batajnica railway condition monitoring** — dynamic condition of passing rolling stock | Historical wayside measurement station, Batajnica; exact currently installed transducer/model inventory unverified | A railway-operator-hosted CIP design dated **May 2020**, PDF page 44, explicitly says the referenced equipment had been installed and operated at Batajnica. [R1] | Historical operational statement; no observation timestamp or present operation established. The referenced **2010** project is not treated as a commissioning date | Event-related purpose; actual sampling and public latency unknown | Public design document, no open data endpoint or reuse licence established. No individual train records or infrastructure access details retained. |

## Scope-sensitive qualifications

**Pupin is a deployed physical system, with a missing public-data route.** P1 describes wind speed/direction, air and panel temperature, and insolation alongside electrical measurements. P2's proposed digital-twin living lab is not evidence that a new public platform has been commissioned. The SINERGY homepage repeats browser availability, but its relevant “Read more” links returned to that homepage. No host, API path or credential was guessed. [P1–P3]

**The EPS report mixes direct measurement, calculated aggregates and incomplete periods.** CEMS Tables 70 and 71 separate operation without and with the desulphurisation plant; do not merge them into one uninterrupted series. The water chapter records missing Q2 sampling at TENT A because no laboratory contract existed, and reconstruction affected TENT B coverage. TENT A wastewater treatment is described as operating since 2016. Do not label every published water volume a sensor reading, or missing sampling as zero. [E2]

**Installed electricity meters are not a public energy feed.** The exact Belgrade total includes 353,398 residential replacements, 10,379 installations associated with relocated metering points and 13,573 replacement metering groups. These add to 377,350. The source calls Centar, Banovo brdo and Zemun *branches*, not municipalities. Its future nationwide financing targets must not be added to this completed local count. [D1]

**The rail evidence is historical and narrowly worded.** R1 mainly designs future stations outside Belgrade. Only its explicit retrospective Batajnica statement supports this lead; proposed equipment quantities and technical capabilities elsewhere in the document are not a current Batajnica inventory. A present operator confirmation and a public aggregate product would be necessary to promote it beyond historical discovery.

## Primary source register

All sources below were reviewed on **2026-09-06** through normal primary-page/PDF web navigation. Dates refer to the source, not retrieval. No raw dataset was downloaded or saved by this lane. Exact-route provenance capture and product review remain the coordinator's responsibility before collection.

- **P1 — operator commissioning notice, 2013-09-23:** [Fotonaponska elektrana na krovu Instituta](https://www.pupin.rs/2013/09/fotonaponska-elektrana-na-krovu-instituta/). Commissioning event stated as 20 September; year follows the dated notice. Public article; no dataset licence or working data link established.
- **P2 — operator follow-up, 2025-07-28:** [IMP Hosts GOTOTWIN Project Meeting on Renewable Energy](https://www.pupin.rs/en/2025/07/imp-hosts-gototwin-project-meeting-on-renewable-energy/). Existing rooftop plant, proposed adaptation. The body describes a June 2025 meeting; article date is later.
- **P3 — primary funded-project site, publication date not established:** [SINERGY](https://project-sinergy.org/). Commissioned campus system and browser-access description; copyright footer states rights reserved. This is corroborating project documentation, not another plant.
- **E1 — operator environmental page, update date not established:** [EPS / TENT environmental protection](https://www.eps.rs/lat/tent/Stranice/Zastita_sredine.aspx). Historical CEMS installation and calibration facts. The mixed-date page is not a current instrument-health report.
- **E2 — operator report, March 2025, observations for 2024:** [EPS environmental report for 2024](https://www.eps.rs/lat/Documents/Izve%C5%A1taj%20o%20stanju%20%C5%BEivotne%20sredine%20u%20EPS%20AD%20za%202024.%20%20godinu.pdf). 218 PDF pages. Relevant printed pages 83–85 and 98–99. [Official report catalogue](https://www.eps.rs/cir/Pages/Sredina-izvestaji.aspx) supplies the annual publication route. No currentness beyond the report period is claimed.
- **D1 — operator magazine, September 2024, issue 12:** [Elektrodistribucija Srbije](https://elektrodistribucija.rs/aktuelnosti/list_edb/dokumenta/Elektrodistribucija_br_12.pdf). Printed pages 6–7, especially the Belgrade census on page 7. This is evidence of completed deployment and internal readings, not an open meter database.
- **R1 — primary design hosted by railway infrastructure operator, May 2020:** [CIP project 2017-728-MAŠ-6.4](https://arhiva.infrazs.rs/dokumenta_o_padu_nadstresice/6.4_CIP.pdf). Cover date verified; retrospective Batajnica statement at PDF page 44. The hosting/upload date was not established.

## Deduplication and exclusions

Read the proposed **188-record** registry at `wave2/integration/research/SOURCE_REGISTRY.json` before searching, plus existing utility, procurement, round-two/round-three and public-aggregate-request notes. These findings expand beyond S12/S54 outage notices, S175 heat/water historical devices, S184 Vinča emissions and S189 intersection detectors. They do not duplicate national EMS/ENTSO-E or mains-frequency leads already recorded in notes.

- **Airport noise:** exact operator source and 5-fixed/1-portable statement handed to hydromet; no further parallel probing or flight-track access here.
- **Public lighting:** [the actual utility host](https://bg-osvetljenje.rs/) claims remote control and fault detection, but no dated specific deployment or timestamped readout was established. Its footer reserves rights. Its display counters rendered as zero; this is not a device census. Kept below the five stronger leads.
- **Airport wastewater:** the inspected operator description still framed the 2023 plant as undergoing final adjustments; not promoted to fully commissioned sensing evidence.
- **Solar research software:** publication metadata for a local NEON/SINERGY platform explicitly describes tests using Spanish data. A system hosted in Belgrade is not automatically measuring Belgrade; that work was not promoted as a local stream.
- **Rail proposals and household examples:** proposed non-Belgrade measuring stations, private household solar monitoring and account portals were excluded.

## Next concrete step and search log

For a live-first follow-up, prioritize a publisher-grounded **public Pupin campus readout URL** and its current measurement timestamp. If none is published, retain the installation evidence without inventing access. For a useful public aggregate now, select a bounded TENT table only after the coordinator captures its exact report route and reviews reuse. No messages to institutions, repeated collector, authentication or UI control has been authorized by this lane.

Search families included operator domains for installed smart meters; TENT continuous monitoring and 2024 environmental reporting; lighting remote control; railway wayside measurement stations; Belgrade campus PV and weather monitoring; and EMS real-time measurement pages. Searches favoured commissioning/operation over procurement. The live-first steering was incorporated during the task: every candidate explicitly distinguishes physical operation from a verified fresh public readout. No new fresh public infrastructure feed was confirmed in this bounded review.


## Coordinator integration note

Accepted as a dated discovery dossier with its stated evidence limits, not an access clearance or live-feed verification. Current registry remains188 records. No source IDs were allocated from these broader leads.
