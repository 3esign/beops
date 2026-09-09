Status: current
Date: 2026-09-06
Author: Codex research lane, reviewed by coordinator

# Belgrade sensing literature: energy, mobility and structures

Integration: accepted by coordinator with the reading limits below.

Date: 2026-09-06. Author: Codex `/root/procurement`. Scope: seven additional papers; no registry IDs allocated, no raw data downloaded, no institutional contact or login, no central writes by the scout; this copy was integrated by the coordinator.

Seven papers connect Belgrade to measured infrastructure or to experimentally evaluated sensing methods. Five describe actual local observation or operation; one validates an optimisation model against local building data; one tests a simulated Belgrade traffic scenario with separate video input. Six have verified DOIs; the 2015 solar conference paper has no DOI established in the inspected record. None verifies a currently accessible live Belgrade feed.

Evidence read: three publisher-hosted full texts, two author-uploaded full texts, one publisher-provided full text on ResearchGate, and one publisher abstract with indexed section excerpts. The review checked methods and data/rights passages rather than independently reproducing results. ResearchGate is used only where it exposes the paper itself with author or publisher provenance; its recommendation snippets and unrelated citation metadata are not deployment evidence.

Before searching, I read the existing wide bibliography, experiment bibliography and model notes: `research/04-bibliography/BIBLIOGRAPHY_2026-09-05.md`, `BIBLIOGRAFIJA_2026-09-05.md`, and `research/03-models/MODELI_I_LITERATURA.md`. These additions avoid their general urban-sensing, standards and comparative-city references. River chemistry, wastewater/biosurveillance, atmosphere and noise were left to the parallel hydromet lane.

## 1. Operational heat and electricity: Voždovac CHP

**Tanasić, Vladimir D.; Tanasić, Nikola D.; Stamenić, Mirjana S. (2024). “Operational characteristics of the combined heat and power plant in the district heating system of Belgrade.” Thermal Science, 28(1B), 589–597. DOI: [10.2298/TSCI230405158T](https://doi.org/10.2298/TSCI230405158T).**

- Evidence: publisher full text, especially pp. 592–593, Tables 1–2. The paper reports operation from 2021-01-01 at Voždovac, with three gas engines totalling 10 MW electric and 10.1 MW thermal capacity.
- Observation: monthly electricity/heat production, gas and auxiliary electricity consumption, and operating hours for January 2021–December 2022. These are operational aggregates; measurement instrument models and original sampling cadence are unspecified.
- Interpretation: strong historical evidence that the heating plant generates a useful energy balance. Economic sensitivity scenarios are model outputs, separate from recorded operation. The 2024 issue date is not a measurement date.
- Access/rights: [public publisher PDF](https://doiserbia.nb.rs/ft.aspx?id=0354-98362300158T); its final page explicitly states CC BY-NC-ND 4.0. No separate open dataset, data licence or live route was found. Article access does not establish permission for operational-system collection.

## 2. Solar generation as an environmental observation: Pupin rooftop

**Stamatović, Radomir; Car, Aleksandar (2015). “Analiza proizvodnje krovne fotonaponske elektrane” / “The Rooftop Photovoltaic Power Plant Analysis.” 32. savetovanje CIGRE Srbija, Zlatibor, May 2015. DOI: not established.**

- Evidence: [author-uploaded full text and conference metadata](https://www.researchgate.net/publication/277018319_Analiza_proizvodnje_krovne_fotonaponske_elektrane), uploaded by Stamatović on 2015-05-22; methods/results §§4–5. The 50 kW, 180-panel plant is at the Mihajlo Pupin Institute in Belgrade.
- Observation: 2014 SCADA/MySQL records connect generation with irradiance, temperatures, wind and inverter variables; hourly/daily/monthly reports are described. Sensor models and acquisition cadence are unspecified.
- Interpretation: measured performance is compared with a clear-sky calculation; this campus system cannot represent all Belgrade.
- Access/rights: public article text; no reusable dataset licence established. Its historical PowerWeb citation remains unprobed and unresolved; see below.

## 3. Local measurements informing energy optimisation

**Batić, Marko; Tomašević, Nikola; Beccuti, Giovanni; Demiray, Turhan; Vraneš, Sanja (2016). “Combined energy hub optimisation and demand side management for buildings.” Energy and Buildings, 127, 229–241. DOI: [10.1016/j.enbuild.2016.05.087](https://doi.org/10.1016/j.enbuild.2016.05.087).**

- Evidence: [publisher abstract and indexed section excerpts](https://www.sciencedirect.com/science/article/abs/pii/S0378778816304765); direct page request returned 403, so no full-text claim. Author order independently corroborated by the institute project's [publication deliverable, item 4](https://www.project-lambda.org/sites/default/files/Deliverables/D1.6.pdf).
- Place/time: actual building complex in Belgrade; the Pupin Blue-building/PV system is identified in the publication's indexed material. Inputs cover 2015-01-29, 00:00–23:45: electricity/heating loads, PV generation and energy prices. The excerpt explicitly allows acquired **or reconstructed** time series; not every input is a sensor reading.
- Interpretation: numerical validation of integrated supply/demand optimisation. Reported savings are scenario comparisons, not verified annual savings from a commissioned controller. This paper and the preceding solar paper overlap in campus infrastructure; they are not two independent solar deployments.
- Access/rights: abstract available; no explicit open data licence or dataset DOI established. No alternative access mechanism was used to obtain publisher full text.

## 4. Weather-sensitive traffic capacity from actual observations

**Ivanović, Ivan; Jović, Jadranka (2018; first online 2017-04-12). “Sensitivity of street network capacity under the rain impact: case study of Belgrade.” Transport, 33(2), 470–477. DOI: [10.3846/16484142.2017.1283532](https://doi.org/10.3846/16484142.2017.1283532).**

- Evidence: [publisher full text](https://journals.vilniustech.lt/index.php/Transport/article/download/171/138/354), §§2.1–2.4. Four signalised Belgrade intersections were selected near automatic meteorological observations and existing video monitoring; two inner-city and two at its edge. The reported location labels do not establish a current station inventory.
- Observation: rain collected at one-minute intervals in 2012–2015 and aggregated hourly; rainy peak-hour traffic in 2015, dry-condition comparisons mainly in 2016. Video-derived vehicle headways produce aggregate saturation-flow estimates. Of 1,351 recorded signal cycles, 1,063 remained after exclusions.
- Interpretation: empirical evidence for weather/traffic coupling and the importance of observation filters. Capacity coefficients are derived quantities; the selected intersections and exclusion rules limit citywide extrapolation.
- Access/rights: public PDF, which prints a publisher copyright notice; an explicit dataset licence or downloadable research dataset was not identified. No video, identifiers or trajectories were collected. Exact transducer models and current readout are unverified.

## 5. People and infrastructure as a sensing system: park-and-ride

**Molan, Vladimir D.; Simićević, Jelena S. (2019). “Karakteristike funkcionisanja sistema ‘Parkiraj i vozi se’ – primer Beograda.” Tehnika – Saobraćaj, 66(3), 425–432. DOI: [10.5937/tehnika1903425M](https://doi.org/10.5937/tehnika1903425M).**

- Evidence: [publisher-associated SCIndeks full text](https://scindeks-clanci.ceon.rs/data/pdf/0040-2176/2019/0040-21761903425M.pdf), §4 and results. Venue numbering follows the PDF's Saobraćaj series label; some catalogues use the overall Tehnika volume 74.
- Place/time: Vladimira Popovića parking in New Belgrade on 2018-06-13, 06:00–19:00; neighbouring comparison parking on 2018-06-14, 06:00–18:00.
- Observation: trained students counted arrivals/departures and interviewed users, producing occupancy, duration and use-category aggregates. This is human observation, not evidence of installed electronic parking sensors. The underlying method recorded plates; this review uses only the published aggregate results.
- Interpretation: useful evidence of social observation complementing machines. The paper's single formal park-and-ride claim belongs to its study context and cannot describe today's network.
- Access/rights: public PDF; no explicit reuse licence or open microdata link established from the inspected text. No respondent or vehicle records collected.

## 6. Temporary structural sensing on Gazela and Ada approach viaducts

**Mišković, Zoran; Mišković, Ljiljana (2018). “Organization of bridge load testing: recent experiences” / “Organizacija ispitivanja mostova: skorašnja iskustva.” 6th International Conference, Contemporary Achievements in Civil Engineering, Subotica, 20 April 2018, 113–122. DOI: [10.14415/konferencijaGFS2018.075](https://doi.org/10.14415/konferencijaGFS2018.075).**

- Evidence: [publisher metadata/licence](https://www.gf.uns.ac.rs/~zbornik/index.php?lang=LAT&menu=6&rad_id=685&zbornik_id=45), plus [author-uploaded full text](https://www.researchgate.net/publication/325407141_ORGANIZACIJA_ISPITIVANJA_MOSTOVA_SKORASNJA_ISKUSTVA), §§2–3 and references.
- Observation: Gazela approach tests on 2012-06-30/07-01 and main-structure tests on 2012-08-11/12; Ada **north approach viaducts**, linked to 2017 test reports. Strain gauges, surveying measurements and LVDT displacement instruments documented load response; acquisition systems supported simultaneous readings. This is completed temporary testing, not proof of continuous structural monitoring.
- Place limit: the paper also covers Kostova greda in Montenegro; that case is excluded from Belgrade evidence. Ada approaches must not be conflated with the main cable-stayed span.
- Access/rights: publisher marks CC BY-SA 4.0. No raw strain/displacement series, data licence or live endpoint established. Test-report citations are additional provenance leads, not inspected source documents. Instrument models and sample rates remain unspecified.

## 7. Edge sensing experiment using a Belgrade scenario

**Bogićević, Dušan; Stojanović, Dragan; Gnjatović, Milan; Tot, Ivan; Jovanović, Boriša (2026). “Real-Time Traffic Data Analysis on Resource-Constrained Edge Devices.” Electronics, 15(8), 1703. Published 2026-04-17. DOI: [10.3390/electronics15081703](https://doi.org/10.3390/electronics15081703).**

- Evidence: [publisher page](https://www.mdpi.com/2079-9292/15/8/1703) indexed metadata; [public full text supplied by MDPI on ResearchGate](https://www.researchgate.net/publication/403927837_Real-Time_Traffic_Data_Analysis_on_Resource-Constrained_Edge_Devices), §§3–4 and data-availability statement. Direct MDPI navigation returned 429 and was not repeatedly retried.
- Experiment: Raspberry Pi 3/4, eKuiper/MQTT and YOLOv8n combine SUMO-generated Belgrade traffic with EarthCam video displayed on a screen and recaptured by a camera. A 7,400-second simulation and approximately one-second traffic messages are described; physical experiment dates are unspecified.
- Interpretation: measured hardware performance in a hybrid laboratory setup. The live video is not established as Belgrade street observation. “Real-time” concerns processing latency; this paper does not demonstrate a deployed Belgrade junction sensor service.
- Access/rights: article CC BY 4.0; research data available from authors upon request. No public dataset DOI found and no request sent. Article licensing does not grant rights to third-party camera footage.

## Integration implications and follow-up boundaries

The strongest new observational anchors are the Voždovac monthly operating tables, rain/traffic methods, and completed bridge instrumentation. They broaden the device map from environmental stations to utility balances, camera-derived traffic variables, and temporary structural tests. The park-and-ride paper adds an explicitly human observation system. These are historical observations and methods, not live-data approvals.

The two Pupin papers strengthen one existing campus lead. The solar article's reference 12 is transcribed by the text extractor as `http://147.91.50.246/PowerWeb/faces/impS olarPowerPlant.xhtml`. The embedded space is unresolved OCR, so this report intentionally preserves it as text rather than asserting a clickable endpoint. No IP connection, endpoint existence check, archive export or raw solar collection was performed. Any later endpoint investigation belongs to the coordinator's exact-host provenance and access review.

For reusable material, distinguish article licences from dataset licences. Explicit article terms were inspected for CHP (CC BY-NC-ND 4.0), bridges (CC BY-SA 4.0), and the edge experiment (CC BY 4.0). None of these establishes a general licence for operator databases, traffic recordings or household readings. The remaining paper/data permissions are unresolved rather than implicitly cleared by public access.

Potential catalogue entries should carry source publication date, observation period, instrument class, physical phenomenon, local coverage, study/operational status, and data route as separate fields. Do not use the 2026 retrieval date as measurement freshness. Public scientific figures/tables can support provenance review, but this wave did not extract them into reusable datasets.

## Search and access log

Retrieval date for all web checks: 2026-09-06. Search-engine crawl ages are not publication or observation dates. The date/count conclusions above come from article text or the original publisher/author record.

- English searches: Belgrade district heating operational characteristics; Belgrade photovoltaic SCADA production; combined energy hub optimisation Belgrade; Belgrade traffic rain saturation flow; Belgrade real-time edge traffic devices; bridge load testing Gazela Ada; Belgrade digital twin traffic.
- Serbian Latin/Cyrillic searches: “Analiza proizvodnje krovne fotonaponske elektrane”; “Organizacija ispitivanja mostova”; “Организација испитивања мостова”; Beograd parkiraj i vozi se; Beograd merni senzori mostovi. Exact-title/DOI follow-ups resolved metadata and methods.
- Primary full texts successfully read via DOI Serbia, SCIndeks, Vilnius Tech, and explicitly author/publisher-provided ResearchGate records. The ordinary ResearchGate HTML exposed text without login; login links were not used.
- Publisher limitations: ScienceDirect direct page 403; MDPI direct page 429; initial Vilnius landing page timeouts/internal tool errors, followed by a search-grounded publisher PDF; official bridge PDF tool safety/open error, so publisher metadata and independently public author copy were used. No proxy, authentication or access-control workaround was used.
- Not promoted: additional Belgrade digital-twin/AI architecture papers whose local deployment or actual-data status was not established; 2025 automatic-traffic-counter PDF whose local setting could not be verified in this bound. No filler entries were counted.

Handoff count: **7 papers, 6 verified DOIs, 6 full-text evidence records, 1 abstract/excerpt record, 0 newly verified live feeds, 0 raw datasets acquired.**
