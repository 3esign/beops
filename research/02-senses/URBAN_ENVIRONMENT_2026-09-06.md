Status: historical
Date: 2026-09-06
Author: Codex hydromet / urban-environment lane
Scope: Belgrade devices and data; primary-source metadata/document review only

# Urban environment: noise, water chemistry and biological sampling

The strongest present-day routes are airport noise microphones, SEPA's dated Belgrade river chemistry reports, and mosquito catch/laboratory results. None was verified as an accessible live numerical stream in this pass. Water results have a documented publication delay; a mosquito result is a dated laboratory event; airport continuous operation is operator-reported but the latest station reading could not be inspected. Two additional historical datasets are retained separately below.

Deduplication: checked the proposed 188-record registry under `wave2/integration/research/SOURCE_REGISTRY.json`, plus the existing senses and legal notes. S61's EEA noise coverage gap, S63's empty BVK drinking-water page, river levels, Plovput bathymetry and ACTRIS/Ada Marina remain separate. Airport noise was already mentioned in `NOVA_CULA_RUNDA3_2026-09-05.md`; its entry here deepens that lead and incorporates the procurement agent's handoff. The other four named routes were not found in the checked registry/notes. No source IDs assigned.

## 1. Airport sound pressure: continuous installed system, live values not verified

**Phenomenon/device/site.** The [airport operator](https://beg.aero/eng/corporate/sustainable-development-1) reports five fixed and one portable microphone monitoring units, connected to a server, operating 24/7 under ISO 20906. The [2024 stakeholder plan](https://begv2-live.ha.rs/sites/default/files/2025-08/2024-belgrade-airport-stakeholder-engagement-plan.pdf) reports four additional installed microphones in Bežanijska Kosa, Ledine and Novi Beograd. Its count is a dated project statement, not a replacement for the current website count. Exact device models, calibration records and station coordinates were not verified.

**Data route.** The operator links **https://webtrak.emsbk.com/beg4** for noise-monitoring access. Noise-only sound-level displays or aggregate time series are the relevant product. Its aircraft tracks, individual flight records and complaint forms are outside this lane. The operator's [2022 activity report](https://beg.aero/sites/default/files/2024-02/activity-report-2022-eng.pdf), printed page 22, records the public application; the later stakeholder plan says the public promotion occurred in May 2023. These describe different milestones.

**Time.** Latest measurement: unknown. Sampling interval, screen refresh, public delay, noise-only export and archive retention: unknown. The website says real-time or historical information is available, but that is not a measured freshness check. The environmental noise action plan's approval on 2025-06-05 for 2025–2030 is a policy date, not a noise reading.

**Access/licence/proof.** Public application is documented; no explicit data-reuse licence was located. Classify **access documented / reuse unresolved**, with exact route review before extraction and E-004 before repetition. Operator installation/public-service evidence is strong; verified live-product evidence is absent. Web-tool opening of the exact app returned an error, and CUA reported no browser available. No alternative endpoint guesses, credentials, audio, flight records or complaint records were used.

**Next bounded step.** In an available browser, inspect only station noise display/help and identify measurement timestamp, dB indicator, averaging period, latency, terms and any documented noise-only export. Do not infer an API from the app name or transfer permission from another airport's WebTrak instance.

## 2. Belgrade river chemistry: recent sampled data, explicit PDF reuse restriction

**Phenomenon/device/site.** [SEPA's water-report page](https://sepa.gov.rs/kvalitet-voda/) names Ostružnica/Sava (44.731653, 20.311836), Zemun/Danube (44.84884, 20.411830), and Belgrade Vinča/Danube (44.768411, 20.620450). Smederevo is also listed and must remain outside a narrow Belgrade filter. This is field sampling plus chemical analysis, not proof of a permanent automatic multiparameter sonde. It senses temperature, turbidity, oxygen, conductivity, pH and nutrients; instrument makes/models remain unknown.

**Time/access.** The indexed primary page advertises the latest Belgrade report as **12.08.2026**, under an obsolete “2024” heading. It states that physicochemical results are published seven days after sampling. Its separate general weekly bulletin is prepared each Tuesday for the preceding seven days; the latest indexed period found was **19–25 August 2026**. Those labels were not promoted to verified newest sample timestamps. The general weekly bulletin and the Belgrade sample series have separate schedules. Direct opened page text and indexed text differed, so coordinator should capture the current page and its exact selected link.

**Concrete sample/report evidence.** The indexed [2026-04-01 Vinča report](https://sepa.gov.rs/wp-content/uploads/2026/05/BG-VODE-Izvestaj-01.04.26.pdf) identifies station/sample context `42052 Beograd_Vinča/Desna_obala`, sampling at 09:00, 50 cm depth, and separate analysis dates. Time zone is not stated. The [2026-03-04 report](https://sepa.gov.rs/wp-content/uploads/2026/04/BG-VODE-Izvestaj-04.03.26.pdf) identifies Ostružnica, right bank, one kilometre upstream of the bridge. This is direct local evidence, not inferred coverage from a national dataset.

**Legal classification: hold the PDF route.** Both indexed report pages contain a footer describing the document as the Agency's business secret and restricting copying to Agency consent. This is an explicit resource-level restriction despite public publication. Do not download, redistribute or automate these report PDFs under an assumed official-material exception or the separate XLSX licence. Coordinator should preserve the restrictive clause through its legal evidence process. No raw report was saved by this lane; no permission request was sent.

**Separate archive with an explicit licence.** The [SEPA national water-quality catalogue](https://data.gov.rs/sr/datasets/kvalitet-voda-1/) assigns the Serbian Open Data Licence to its linked resource:

- https://data.gov.rs/s/resources/kvalitet-voda-1/20260420-083354/kvalitet-voda.xlsx
- Stable resource: https://data.gov.rs/sr/datasets/r/6e2af5a1-6e3e-44c0-8dae-0de590d399cd
- Catalogue periods: surface waters 2001–2024; groundwater/reservoirs 2004–2024; annual update; resource modified 2026-04-20; advertised size 21.6 MB.
- Advertised SHA-1: `36c33bdc61e93720cb8b55037022a2c35ca9983c`.

That resource has an **explicit open-data basis**, subject to the [portal attribution terms](https://data.gov.rs/sr/terms/). The workbook was not downloaded, so specific Belgrade rows and local groundwater coverage inside it remain to be verified. Do not say the PDF licence covers the workbook, or the workbook licence covers the PDFs. The catalogue is useful for a retrospective baseline, not current water conditions or drinking-water safety.

## 3. Mosquito catch → PCR: a current biological occurrence signal

**Phenomenon/device/site.** [Gradska Čistoća's primary notice](https://www.gradskacistoca.rs/na-teritoriji-beograda-u-jednom-uzorku-komarca-detektovan-virus-zapadnog-nila/), published **2026-08-12**, reports one Culex sample with detected West Nile virus genome from the Železnik railway yard, Čukarica. The transduction chain is capture/selection of insects and laboratory real-time PCR. “Real-time PCR” names the laboratory method; it does not mean live online reporting. Exact trap and assay instrument models are not given.

**Time/data.** The notice provides a publication date, location and positive-result count. Sampling date, assay timestamp, number tested and detection threshold are not published there. Consequently this is a dated occurrence event, not a prevalence estimate, current risk map or continuous feed. The operator says mosquito-number monitoring continues daily; publication of positive findings appears event-driven, with no API or fixed reporting latency located.

**Operational support.** The [operator's 2026 programme](https://www.gradskacistoca.rs/wp-content/uploads/2026/02/%D0%9F%D1%80%D0%BE%D0%B3%D1%80%D0%B0%D0%BC-%D0%BF%D0%BE%D1%81%D0%BB%D0%BE%D0%B2%D0%B0%D1%9A%D0%B0-%D0%B7%D0%B0-2026.%D0%B3%D0%BE%D0%B4%D0%B8%D0%BD%D1%83.pdf) specifies monitoring in 16 Belgrade municipalities from March–October, extendable by weather, and includes larval stage/count, water-surface temperature, weather and PCR testing. Treat programme cadence as a planned operating scope; the August notice separately establishes actual testing. Planned spraying is an intervention notice and does not itself reveal insect abundance.

**Access/licence/proof.** Public operator factual notice; no explicit reuse licence located. **Official/public-enterprise factual-material scope review (E-003), with E-004 before repeated structured extraction.** A minimal permitted public signal would retain event date, coarse locality, organism, test method and reported result, without resident reports, contact details or individual complaint records. No health-risk conclusion is drawn from this single result. This opens an ecological sensing category beyond generic GBIF/iNaturalist occurrence discovery.

## 4. Five-site Kestrel thermal campaign: installed-device evidence, historical only

[HungaroMet's 2024 journal page](https://met.hu/ismeret-tar/kiadvanyok/idojaras/index.php?id=5964) publishes the primary study **Thermal assessments at local and micro scales during hot summer days: a case study of Belgrade**, DOI **10.28974/idojaras.2024.1.7**. Two summer-2021 campaigns covered five Belgrade sites in different local climate zones. Kestrel heat-stress trackers measured air and globe temperature every minute; analysis used ten-minute averages. Exact campaign days and site-by-site coordinates were not verified in this pass. The journal release is dated 2024-03-22; that is not the observation date.

**Access/licence.** Public article and linked paper PDF; no standalone downloadable measurements or resource-specific data licence located. **Research-device evidence / data access unresolved.** The PDF web-tool open failed, so do not invent a sensor model suffix, raw archive URL, present operation or continuing cadence. This is a useful design/validation precedent for a new thermal sense, not a live source.

## 5. AQUA landfill water-balance outputs: new local model archive, not measurements

[Zenodo record 22110720](https://zenodo.org/records/22110720), DOI **10.5281/zenodo.22110720**, is attributed to Belgrade's Secretariat for Environmental Protection. It contains 17 HELP 4.0 simulations for seven local landfill sites, including Bežanijska Kosa and Vinča, with historical 2005–2022 forcing from Beograd Observatory/WMO 13274. Other sites are Sopot, Barajevo, Baroševac/Lazarevac, Grebača/Obrenovac and Vlaška/Mladenovac. These are modelled water balance/leachate-related outputs; they do not establish installed groundwater sensors or measured landfill discharge.

**Time/cadence.** Published 2026-08-26; repository creation/modification 2026-08-29; model period 2005–2022. Daily/monthly/annual model outputs are described. No ongoing update or live latency is stated.

**Data/access/licence.** Record advertises a 15.8 MB `HELP Output files.zip`, readme and file list. Open access is displayed, but the web rendering's licence field was empty. The documented single-record metadata URL **https://zenodo.org/api/records/22110720** returned a web-tool error; no data files were requested. Classify **public catalogue / exact file licence unresolved**. Zenodo's metadata policy and a dataset's “Open” badge do not licence its files by themselves. This is an archive candidate for the water-model layer, not a current sense.

## Capture priorities and exclusions

1. Airport: enable a noise-only freshness/terms inspection when a browser is available. Continuous device operation is documented; latest accessible sound-level value is not.
2. SEPA: capture the exact current Belgrade report link and restriction without collecting the raw PDF. Consider the separately licensed XLSX only under its own size budget and local-row check.
3. Gradska Čistoća: record the dated biological finding as an attributed event, keeping publication date distinct from unknown sample/test time. A current source is not automatically a live source.

The daily SEPA Danube incident notices surfaced for Bezdan, Bogojevo and Novi Sad; they were not substituted for Belgrade measurements. NoiseCapture individual tracks/points, airport flight tracks/audio/complaints, bee-colony exact locations, generic cityless research networks, and other-city microclimate simulations were not pursued as local live products. Honey-bee genetic research and the domestic strategic noise maps remain optional archive context, not additional current feed claims.

## Search log and constraints

Searched primary operator, government and researcher/publisher sources for local noise, water chemistry/groundwater, microclimate, ecological sampling and dataset records. Examined catalogue/licence metadata and current dated notices; searched exact known paper and dataset identifiers. Followed the user steering toward current sensing during the lane, placing the early historical findings below the present-day candidates.

No raw scientific dataset, audio, flight/person/vessel record, large XLSX/ZIP, institution message, authentication action, scheduler, API endpoint spray or D: write occurred. Existing restrictions on other sources were not bypassed. A 2024 water yearbook could not be viewed because it exceeded the web tool's size limit; no alternate copy was fetched. All output is this workspace draft for coordinator integration and legal capture.


## Coordinator integration note

Accepted as a dated discovery dossier with its stated evidence limits, not an access clearance or live-feed verification. Current registry remains188 records. No source IDs were allocated from these broader leads.
