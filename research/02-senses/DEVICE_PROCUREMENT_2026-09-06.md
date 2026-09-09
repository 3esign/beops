Status: historical
Date: 2026-09-06
Author: Procurement scout, native Codex sub-agent

# Municipal device evidence: procurement and operators

Accepted discovery snapshot. The [integrated report](DEVICE_DATA_DISCOVERY_2026-09-06.md) incorporates later captures, including the newer BCE daily date, and is current for this wave.

Four useful device/data leads were substantiated from primary pages. One has directly published environmental results; the other three establish instruments or procurement intentions without establishing an open telemetry feed. This is a bounded discovery report, pending coordinator review and permission captures.

## Evidence table

| Lead and holder | Instrument and Belgrade coverage | Evidence level and source date | Data route and time distinction |
|---|---|---|---|
| Vinča Energy-from-Waste / Beo Čista Energija (BCE) | Stack CEMS, sampling cartridges and periodic laboratory monitoring at Vinča | Operator describes monitoring during operation; publication date absent. [B1] | Public HTML concentrations and report links have measurement periods. Browser daily headings differed: scout saw 2026-08-18; coordinator saw 2026-09-05. Root capture must settle the response; this discrepancy does not prove an outage. |
| City traffic Secretariat | Vehicle detectors and pedestrian request buttons controlling an adaptive intersection at Vojvode Micka Krstića / Patrisa Lumumbe | Official commissioning-era notice, published 2013-02-21, explicitly says the adaptive system was applied at that intersection. [T1] A 2023-03-09 technical explanation confirms detector/adaptive operation as city operating modes. [T2] | Public evidence describes the device and its purpose, not detector event logs. No public count/time-series endpoint found. Publication time is not a vehicle-detection time. Continued operation at that specific site in September 2026 was not verified. |
| JKP Beogradske elektrane | Ultrasonic heat meters measuring total heat delivered to a building through its heat-transfer station; Belgrade utility network | Operator consumer procedure describes actual meter readings, but gives no publication date or installed inventory. [H1] | Operator holds building heat readings. Public page supplies no observation series or measurement timestamps. A future research route is sufficiently aggregated heat demand with explicit utility authorization; consumer accounts and individual readings are outside scope. |
| JKP Beogradski vodovod i kanalizacija (BVK) | Water level, flow and pressure instruments and remote operational monitoring within the Belgrade water utility | Utility's own journal, issue 294, June 2013, PDF page 5 / printed pages 8–9, describes these as implemented measures. [W1] | Historical installation evidence only; no public telemetry endpoint or sample times established. Useful route is a utility-held aggregate series, subject to permission and confirmation of the present inventory. No infrastructure topology or security details reproduced. |

## Procurement evidence must retain its state

Beogradske elektrane's 2023 procurement plan, version 2, adopted **2023-03-30**, identifies these instrument-related lines. The PDF's upload path is April 2023; search-engine relative publication labels are not used as its adoption date. All list the Belgrade region. [H2]

| Plan line | Planned subject | What this proves |
|---|---|---|
| 0020 | Heat meters, CPV 38418000 | Procurement intention for heat metering. |
| 0021 | Supply and installation of M-Bus modules, CPV 32441200 | Procurement intention for metering communications; no award or commissioning evidence inspected. |
| 0033 | Supply and installation of substation equipment for remote heat-energy reading, CPV 32441200 | Explicit telemetry expansion lead; no installed device count can be derived. |

These lines should be searched by buyer, plan year and subject in S42/S156 before any completion claim. H1 supports the existence of heat meters independently; it does not establish completion of H2's purchases.

## BCE collection notes

B1 has nine daily parameters. ND means below analytical detection; N/A has distinct stated causes, including sample damage and laboratory changes. Preserve those labels. Stack concentrations are source emissions, not ambient air exposure. Named Daily/Monthly CEMS and Aerolab June 2026 report links were found; their files were not downloaded. The coordinator independently captures B1 before integration.

## Sources

All pages below were opened through web research on **2026-09-06**. Retrieval date is our observation of a page, not the source's measurement or publication date. There are no verbatim source quotations in this report.

- **B1** — [BCE: Monitoring of Air Pollutant Emissions from the Stack](https://www.bcenergy.rs/emissions/). Publication date absent; measurement/sampling dates visible, with the snapshot discrepancy documented above. This is the strongest immediate public-data lead.
- **T1** — [Traffic Secretariat: new traffic signals at Vojvode Micka Krstića and Patrisa Lumumbe](https://www.bgsaobracaj.rs/index.php/vest/367/novi-semafor-na-raskrsnici-ulica-vojvode-micka-krstica-i-patrisa-lumumbe). Published 2013-02-21. Initial direct open timed out; one subsequent source-reference open succeeded.
- **T2** — [Traffic Secretariat: yellow-light duration and signal design in Belgrade](https://www.bgsaobracaj.rs/index.php/kampanja-manifestacija/66/tra%D1%98anje-zutog-svetla-i-nacini-pro%D1%98ektovanja-svetlosne-signalizaci%D1%98e-u-beogradu). Published 2023-03-09. Used for operating-mode context only, not as a newly measured traffic dataset.
- **H1** — [Beogradske elektrane: consumer procedures](https://beoelektrane.co.rs/procedure-za-potrosace-2-3/). Publication date absent. The page identifies an ultrasonic meter for total heat supplied to a building.
- **H2** — [Beogradske elektrane: amendments to the 2023 public procurement plan](https://beoelektrane.co.rs/wp-content/uploads/2023/04/Izmene-i-dopune-1-Plana-javni-nabavki-za-2023-godinu.pdf). Version 2; adoption date 2023-03-30. Relevant PDF pages 1–2.
- **W1** — [BVK journal, June 2013, issue 294](https://www.bvk.rs/wp-content/uploads/2019/12/casopis_jun_2013.pdf). Publication June 2013 is printed on the cover; the upload path's December 2019 is not the observation date. Relevant implementation statement on PDF page 5.

## Deduplication and permission state

Registry inspection found S42/S156 already represent procurement portals, S167 the EBRD, S175 a broad utilities survey, S11 BVK planned works, and S63 a water-quality-page assessment. Thus H1/H2/W1 add specific device evidence to existing utility leads. T1/T2 describe urban signal detectors, unlike S57's road-section annual traffic counts. B1 had no BCE-host entry at initial scout inspection; the coordinator subsequently reserved its integration as S184. The scout allocated no source IDs.

The heat utility's inspected primary host is **beoelektrane.co.rs**. S175's survey text instead names beoelektrane.rs; permissions recorded for one hostname cannot silently cover the other. No robots/terms capture or collection authorization was established here for these exact URLs. A publicly readable page is evidence of publication, not an open-data licence. Named opt-outs in the registry were not opened or bypassed. No login, account data or private control system was accessed.

## Search log and discarded paths

Primary searches used `site:bgsaobracaj.rs detektori semafor adaptibilno`, `site:beoelektrane.rs SCADA`, `site:beoelektrane.co.rs "даљинско" "очитавање"`, `site:bvk.rs "мерење протока"`, `site:ebrd.com Belgrade district heating meters monitoring`, and `site:bcenergy.rs "emissions" "monitoring"`. Queries for municipal sensor-equipped waste containers did not establish a primary installed-device inventory. No structural-monitoring lead was promoted without adequate evidence.

The EBRD search surfaced general district-energy guidance, an old evaluation, and Vinča project information. These were useful discovery routes, but generic guidance and financing statements did not prove newly installed Belgrade devices; the primary operator pages above carry the selected findings. Nationwide smart-electricity-meter totals were not converted into a Belgrade count.

## Honest verdict

Verified: primary pages opened, source dates separated from retrieval, four device/data lead groups, one separately labelled procurement plan, registry deduplication, and explicit snapshot uncertainty. Not verified: current inventory counts, award/completion of planned purchases, open utility telemetry, API availability, collection permission, or the meaning of near-zero rounded pollutant values beyond the publisher's labels.

No raw dataset was downloaded, no central file changed, and no institution contacted. Code tests and project gates belong to coordinator integration; this scout made a documentation-only change and checked the resulting file's status, URLs and SHA-256. The Markdown campaign board was read directly after the read-only room helper reported that its JSON parser could not read this board format; the coordinator confirmed native collaboration as this wave's operating route.
