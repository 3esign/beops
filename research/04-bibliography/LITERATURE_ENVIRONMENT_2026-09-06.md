Status: current
Date: 2026-09-06
Author: Codex research lane, reviewed by coordinator

# Belgrade environmental devices and data — empirical literature

Research date: **2026-09-06**. Prepared for the Beops coordinator; this file assigns no registry IDs and changes no collection permissions.

Nine papers below have primary publisher, institutional repository, or author-source verification. They concern measurements in Belgrade, not merely authors affiliated with Belgrade. The existing `04-bibliography/BIBLIOGRAPHY_2026-09-05.md`, its Serbian companion, and `03-models/MODELI_I_LITERATURA.md` were checked: these nine are additions to that general-methods bibliography. BARLI, Kestrel and bee references deepen earlier device notes rather than claiming rediscovery of their devices.

No raw datasets, supplementary data files, audio or personal records were downloaded. No printed API was tested, no authentication attempted, and no institutions contacted. Gradska Čistoća/S175 remains on its existing ContentSignal hold and was not revisited. All findings below are historical studies or instrument characterization; **none establishes a live September 2026 feed**.

## Read levels and legal sorting

- **F — full-text sections inspected:** methods and relevant results/data statements were read in primary HTML/PDF, including indexed primary full text where direct rendering failed. This does not mean results were reproduced.
- **A+ — publisher abstract/introduction plus bibliographic verification:** detailed methods, individual instrument models, or sample timestamps remain unverified where stated.
- **Article grant and data grant are separate.** Public reading, repository deposit, official employment, and an “open access” label alone do not establish a licence for raw measurements. Existing E-003/E-004 and collection framework still govern repeat extraction, retention and redistribution. Missing licence evidence below is an unresolved field, not a finding that no licence exists.

## 1. Low-cost air sensors against a Belgrade reference station

**Vajs, Ivan; Drajic, Dejan; Gligoric, Nenad; Radovanovic, Ilija; Popovic, Ivan. (2021). Developing Relative Humidity and Temperature Corrections for Low-Cost Sensors Using Machine Learning. _Sensors, 21_(10), 3338.** [DOI: 10.3390/s21103338](https://doi.org/10.3390/s21103338).

**Evidence:** F, sections 2.1 and calibration evaluation. One DunavNET ekoNET AQ10x co-located with a SEPA automatic station in Belgrade; the station's name/address was not established. Hardware includes Alphasense gas sensors, Bosch BME280 and Plantower particulate sensing. The evaluated channels are CO, NO₂ and PM10. Campaigns cover February–October 2019 and the same months in 2020; minute samples were averaged hourly to match reference data. Calibration outputs are estimates derived from measurements, with explicit seasonal and cross-year evaluation.

**Data/access:** No standalone campaign dataset URL found. Article **CC BY 4.0** is explicit; no independent raw-data licence established. Beops use: local evidence for humidity/temperature correction, co-location and temporal validation, without transferring fitted coefficients to another device.

Primary sources: [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC8151330/), [publisher PDF, indexed methods](https://mdpi-res.com/d_attachment/sensors/sensors-21-03338/article_deploy/sensors-21-03338.pdf). Checked 2026-09-06; direct MDPI HTML returned 429 and was not retried through a bypass.

## 2. BARLI hardware and quality assurance

**Mijić, Zoran; Ilić, Luka; Kuzmanoski, Maja. (2023). Data quality assurance for atmospheric probing and modeling: characterization of Belgrade Raman lidar station. _Contributions of the Astronomical Observatory Skalnaté Pleso, 53_(3), 163–175.** [DOI: 10.31577/caosp.2023.53.3.163](https://doi.org/10.31577/caosp.2023.53.3.163).

**Evidence:** F, pp.165–173. Institute of Physics Belgrade, approximately 44.860°N, 20.390°E. Nd:YAG transmitter at 355 nm; elastic 355/Raman 387 nm receivers; Hamamatsu R9880U-110 detectors and Licel acquisition. Reported raw bins are 7.5 m and typical accumulation approximately one minute. QA includes zero-bin, signal-delay, telecover and Rayleigh-fit tests. Coordinator check of the primary PDF identifies the telecover example on 27 April 2020 (p.169); dates of all other QA procedures were not established.

**Temporal caution:** Its 2023 conclusion describes regular scheduled measurements, automation and multiwavelength upgrades as future work. Capability does not prove continuous operation.

**Data/access:** [Primary paper PDF](https://www.ta3.sk/caosp/Eedition/FullTexts/vol53no3/pp163-175.pdf), checked 2026-09-06. No paper-specific dataset or article licence identified. Existing S186 ACTRIS product metadata proves historical BGD products separately; it does not prove these QA traces were deposited. Preserve the unresolved legacy raw-product licence documented in [ACTRIS product review](../02-senses/ACTRIS_PRODUCT_2026-09-06.md).

## 3. A solar eclipse observed through several different “senses”

**Ilić, L.; Kuzmanoski, M.; Kolarž, P.; Nina, A.; Srećković, V.; Mijić, Z.; Bajčetić, J.; Andrić, M. (2018). Changes of atmospheric properties over Belgrade, observed using remote sensing and in situ methods during the partial solar eclipse of 20 March 2015. _Journal of Atmospheric and Solar-Terrestrial Physics, 171_, 250–259.** [DOI: 10.1016/j.jastp.2017.10.001](https://doi.org/10.1016/j.jastp.2017.10.001).

**Evidence:** A+. Publisher abstract/introduction verifies the Belgrade event on **20 March 2015**, four experimental setups and two meteorological sites at different elevations/heights. It combines lidar, solar/UV-B radiation, weather, ozone and air ions with an **AWESOME VLF/LF receiver** and a **3 GHz line-of-sight radio link**. Radio-signal variation is measured; ionospheric interpretation and attribution to the eclipse are inferential. Exact site coordinates and channel cadences remain unverified here.

**Data/access:** No deposited campaign dataset or explicit article/data licence located. Publication volume is 2018; DOI contains 2017 and online indexing may use that earlier year. Beops use: an excellent precedent for synchronizing heterogeneous physical observations without equating every derived variable with a direct reading.

Primary verification: [publisher](https://www.sciencedirect.com/science/article/abs/pii/S136468261730202X), [IPB author bibliography](https://mail.ipb.ac.rs/~kolarz/Publications.htm), checked 2026-09-06. The complete eight-author initials/order are verified; expanded given names were not independently established for every author.

## 4. Street-scale air and globe temperature in summer 2021

**Savić, Stevan; Milovanović, Boško; Milošević, Dragan; Dunjić, Jelena; Pecelj, Milica; Lukić, Milica; Ostojić, Miloš; Fekete, Renata. (2024). Thermal assessments at local and micro scales during hot summer days: a case study of Belgrade (Serbia). _Időjárás, 128_(1), 121–141.** [DOI: 10.28974/idojaras.2024.1.7](https://doi.org/10.28974/idojaras.2024.1.7).

**Evidence:** A+, publisher abstract and primary PDF title/abstract indexed. Two hot-day campaigns in urban Belgrade in 2021, five sites representing different local climate zones. Kestrel heat-stress tracking measured air and globe temperature at one-minute resolution; analyses use ten-minute means. These are observed temperatures; globe temperature is not direct measurement of a person's thermal state. Shadow, radiation and within-zone variability are central methodological concerns.

**Data/access:** No separate numerical dataset or explicit article/data licence captured. Primary rendering did not expose the complete methods in this pass, so exact campaign days, site names and the Kestrel model suffix are deliberately not promoted from secondary reports. Beops use: require sensor exposure/shade and aggregation interval metadata for microclimate comparisons.

Primary sources: [publisher issue/abstract](https://met.hu/ismeret-tar/kiadvanyok/idojaras/index.php?id=5964), [official PDF](https://mtb.met.hu/downloads.php?fn=%2Fmetadmin%2Fnewspaper%2F2024%2F02%2F3f1f76439cb98dc9136b2a37f6fadfe5-128-1-7-savic.pdf), checked 2026-09-06.

## 5. Long meteorological archive, derived human heat indices

**Pecelj, Milica; Matzarakis, Andreas; Vujadinović, Mirjam; Radovanović, Milan; Vagić, Nemanja; Đurić, Dijana; Cvetkovic, Milena. (2021). Temporal Analysis of Urban-Suburban PET, mPET and UTCI Indices in Belgrade (Serbia). _Atmosphere, 12_(7), 916.** [DOI: 10.3390/atmos12070916](https://doi.org/10.3390/atmos12070916).

**Evidence:** F, indexed publisher methods §2.2. Urban Belgrade versus suburban Surčin airport, **1976–2018**. Temperature, daily extremes, wind, relative humidity and cloud cover underpin PET, mPET and UTCI. Analysis uses observations at **07:00 and 14:00 CET**; do not describe the analysed series as every hour of every day. Specific historical sensor models and replacements were not identified.

**Data/access:** Station observations are inputs; thermal indices are model-derived outputs. No paper-specific reusable data export located. Publisher labels the article open access, but precise article licence text and underlying station-data reuse terms were not captured in this pass. Keep both unresolved rather than inheriting a provider-wide licence.

Beops use: historical seasonal context and explicit model provenance; no contemporary heat reading follows from these archival indices. [Primary publisher page](https://www.mdpi.com/2073-4433/12/7/916), checked 2026-09-06 via indexed full text; direct open returned 429. Preserve publisher spelling “Cvetkovic” in the citation.

## 6. Belgrade phone-based noise measurements and a documented historical API

**Jezdović, Ivan; Popović, Snežana; Radenković, Miloš; Labus, Aleksandra; Bogdanović, Zorica. (2021). A crowdsensing platform for real-time monitoring and analysis of noise pollution in smart cities. _Sustainable Computing: Informatics and Systems, 31_, 100588.** [DOI: 10.1016/j.suscom.2021.100588](https://doi.org/10.1016/j.suscom.2021.100588).

**Evidence:** F, §7.1/p.7. **4,251 measurements, 8–28 May 2019**, at Bogoslovija, Bulevar Oslobođenja, Studentski grad, Vojvode Stepe and Jove Ilića. Smartphone microphone/GPS plus app-derived noise levels/spectra. Agreement within 5% against another Android app is **not calibration against a traceable certified sound-level meter**.

**Data/access:** Paper p.7 prints an API with `page`, `limit`, `from`, `to`: `https://crowdsensing.elab.fon.bg.ac.rs/api/data-protected/{redacted_access_component}?page=1&limit=10&from=2019-05-08&to=2019-05-10`. The opaque component is intentionally withheld. No API request was made; present access, raw-data licence and ongoing operation remain unknown. Author PDF carries Elsevier all-rights-reserved text.

Beops use: architecture/method evidence; only ambient aggregates are in scope, with participant/location privacy review before any future collection.

Sources checked 2026-09-06: [publisher](https://www.sciencedirect.com/science/article/abs/pii/S2210537921000779), [author's full paper](https://jezdovic.com/PDF/A%20crowdsensing%20platform%20for%20real-time%20monitoring%20and%20analysis%20of%20noise%20pollution%20in%20smart%20cities.pdf), [FON record](https://rfos.fon.bg.ac.rs/handle/123456789/2160?mode=full).

## 7. Urban bee genetics with deposited sequence accessions

**Patenković, Aleksandra; Tanasković, Marija; Erić, Pavle; Erić, Katarina; Mihajlović, Milica; Stanisavljević, Ljubiša; Davidović, Slobodan. (2022). Urban ecosystem drives genetic diversity in feral honey bee. _Scientific Reports, 12_, 17692.** [DOI: 10.1038/s41598-022-21413-y](https://doi.org/10.1038/s41598-022-21413-y).

**Evidence:** F, indexed primary methods/data statement. Belgrade **2020–2021**, 40 feral colonies and 42 managed hives from seven apiaries; one worker per colony analyzed. Garmin eTrex 22x establishes location; PCR–RFLP, 14 microsatellite loci and mitochondrial sequencing establish biological observations. Genetic diversity statistics are derived from those observations.

**Data/access:** Article/supplementary tables contain study data; deposited **GenBank ON187787–ON187868**, via the [GenBank repository](https://www.ncbi.nlm.nih.gov/genbank/). No sequences or supplements fetched. Article CC BY 4.0 was verified in the preceding device wave; raw GenBank terms remain a separate check. The Google Earth basemap does not automatically inherit article permissions. Use coarse study geography, not exact private hive locations.

Beops use: a concrete biological measurement-to-repository chain and an archive of urban biodiversity, not continuous bee sensing.

Primary sources: [publisher](https://www.nature.com/articles/s41598-022-21413-y), [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9587283/), checked 2026-09-06 through indexed primary full text after redirect/challenge responses.

## 8. River RNA as an aggregate biological observation

**Kolarević, Stoimir; Micsinai, Adrienn; Szántó-Egész, Réka; Lukács, Alena; Kračun-Kolarević, Margareta; Lundy, Lian; Kirschner, Alexander K. T.; Farnleitner, Andreas H.; Djukic, Aleksandar; Čolić, Jasna; Nenin, Tanja; Sunjog, Karolina; Paunović, Momir. (2021). Detection of SARS-CoV-2 RNA in the Danube River in Serbia associated with the discharge of untreated wastewaters. _Science of the Total Environment, 783_, 146967.** [DOI: 10.1016/j.scitotenv.2021.146967](https://doi.org/10.1016/j.scitotenv.2021.146967).

**Evidence:** F, methods §2.1–2.4. Three sites: upstream, a Belgrade wastewater-impacted stretch, and 20 km downstream. Upstream/downstream grabs: **7 December 2020**; impacted-site hourly sampling over twelve hours: **10 December 2020**. **QuantStudio 5 RT-qPCR**, N1/N2/E targets. RNA detection is not evidence of infectious virus or individual infection.

**Data/access:** Results/tables and supplementary-information pointer in paper; no independent raw-data repository or explicit reuse grant established. Publication/campaign are historical; this is not a current wastewater dashboard.

Primary verification: [research-network full paper](https://www.normandata.eu/sites/default/files/files/Publications/Kolarevic%20et%20al%20published.pdf), [TU Wien author repository record](https://repositum.tuwien.at/handle/20.500.12708/138149), checked 2026-09-06. The repository warns its migrated record was not quality-checked; author/order/method checks used the paper itself.

## 9. Serbian-language study: elemental composition across five water plants

**Antanasijević, Davor Z.; Lukić, Nataša A.; Pocajt, Viktor V.; Perić-Grujić, Aleksandra A.; Ristić, Mirjana Đ. (2011). Analiza odabranih elemenata u vodi u pogonima za pripremu vode za piće u Beogradu. _Hemijska industrija, 65_(2), 187–196.** [DOI: 10.2298/HEMIND101027001A](https://doi.org/10.2298/HEMIND101027001A). Publisher English title: _Analysis of selected elements in water in the drinking water preparation plants in Belgrade, Serbia_.

**Evidence:** F, pp.188–189. **2009**, fourteen raw/intermediate/finished-water samples across **Bele vode, Banovo brdo, Bežanija, Makiš and Vinča**. **Agilent 7500ce ICP-MS** with multielement standards measured trace elements; tables preserve detection-limit notation. Exact collection days and repeated cadence are not given in the inspected sections.

**Data/access:** Numerical results are printed in tables, not a separately licensed machine-readable dataset. No article-specific reuse grant verified; do not automatically apply current journal terms to a 2011 paper. Beops use: evidence of real laboratory instrumentation and a staged treatment/sample ontology, without projecting 2009 concentrations to today's water quality.

Primary sources: [DOISerbia record](https://doiserbia.nb.rs/Article.aspx?id=0367-598X1100001A), [full Serbian paper](https://doiserbia.nb.rs/ft.aspx?id=0367-598X1100001A), checked 2026-09-06.

## Follow-up leads, not counted among the nine

1. **Jauković, Zorica; Grujić, Svetlana; Matić Bujagić, Ivana; Petković, Anđelka; Laušević, Mila (2022). _Steroid-based tracing of sewage-sourced pollution of river water and wastewater treatment efficiency: Dissolved and suspended water phase distribution_. Science of the Total Environment 846, 157510.** [DOI 10.1016/j.scitotenv.2022.157510](https://doi.org/10.1016/j.scitotenv.2022.157510). [Primary publisher](https://www.sciencedirect.com/science/article/pii/S0048969722046083) verifies Belgrade confluence samples, LC-MS/MS and separate dissolved/suspended phases. Sampling dates, detailed dataset route and licence are unresolved; the two wastewater plants studied elsewhere must not be relabelled Belgrade plants.
2. **Kecman, Snežana; Stojanović, Nadežda; Vukmirović, Milena; Vasiljević, Nevena; Bjedov, Ivana; Vujović, Dragana (2025). _The Impact of the Small Urban Green Space on the Urban Thermal Environment: The Belgrade Case Study (Serbia)_. Forests 16(2), 321.** [Primary publisher / DOI 10.3390/f16020321](https://www.mdpi.com/1999-4907/16/2/321). Eighteen local green spaces are stated in indexed abstract; dates and hardware not verified, direct page 429. Promising deeper campaign/thesis chain, not accepted just from the title.
3. **_Integrated Targeted and Suspect Screening Workflow for Identifying PFAS of Concern in Urban-Impacted Serbian Rivers_ (2026), Toxics 14(1), 78**, [DOI 10.3390/toxics14010078](https://doi.org/10.3390/toxics14010078). Local Belgrade sampling not confirmed; author affiliations and generic Serbia coverage are insufficient. Keep outside the Belgrade core until station/sample metadata proves coverage.

## Search record and integration notes

Searches used English, Serbian Latin and Cyrillic, including `Belgrade river mass spectrometry wastewater paper`, `Belgrade wastewater SARS-CoV-2 study`, `Београд квалитет воде doi научни рад`, and exact local paper titles combined with `Data Availability Statement`, instrument names, years and primary domains. Citation details were checked against publishers, IPB/FON/TU Wien institutional records, author-hosted papers, NORMAN and DOISerbia. Secondary index/news hits served only as leads; unverified details from them were withheld.

Several PMC/PubMed opens returned browser challenges; some MDPI pages returned 429, Nature returned an unsafe identity-provider redirect, and the institutional steroid PDF could not be rendered. No challenge was solved, no endpoint spray used and no site controls bypassed. Indexed primary text was labelled as such. There was no Gradska Čistoća or CORDIS access.

Strongest data pointers: bee GenBank accessions; the redacted, untested 2019 noise API; S186's already-captured historical optical-product metadata. Strongest instrument-to-place evidence: BARLI hardware, AQ10x co-location, QuantStudio river sampling and five-plant ICP-MS. Literature can substantiate these historical chains while live accessibility and raw redistribution stay independently sorted in the legal matrix.

Coordinator: preserve these read-level and licence qualifications if moving entries into a bibliography. All nine have complete author lists (initials retained where that is the verified form), exact DOI and article-year information; no entry should be marked “dataset collected” or “live feed verified.”
