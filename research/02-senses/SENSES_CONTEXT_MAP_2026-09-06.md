Status: current
Date: 2026-09-06
Author: Codex coordinator

# What can become a sense of Belgrade?

This is a working research map, extending the existing twelve-medium typology in[NOVA_CULA_RUNDA2_2026-09-05.md](NOVA_CULA_RUNDA2_2026-09-05.md). It is not a new sensor standard or a declaration that all listed capabilities operate locally. Semir's question is broader than finding another API: through what physical, technical and interpretive arrangements can we notice a part of reality, including its present state?

Our useful unit is an **observation chain**: phenomenon → physical interaction/sample → instrument or procedure → published result → interpretation → human experience. A device may expose several properties. Several devices may contribute to one derived indicator. A public page may publish an old result. A missing stream may describe inaccessible infrastructure rather than a missing instrument.

The existing wide bibliography already supplies SOSA/SSN, O&M and PROV-O for observations, samples, procedure and provenance. The chain below is our organizing convention; it does not replace those standards. New international precedents and conceptual works are linked in the[sensing bibliography supplement](../04-bibliography/BIBLIOGRAPHY_SENSING_CONTEXT_2026-09-06.md).

## Different routes into reality

| Route | What interacts with reality | What reaches us | Current Belgrade evidence and limit |
|---|---|---|---|
| A dedicated physical instrument | Electric field, pressure, radiation, temperature or displacement changes a sensor response | Numeric series with units and calibration context | [RATEL Science Park chart record 168](DEVICE_FOLLOWUP_2026-09-06.md) has a recent dated chart window; actual current latency/timezone unresolved. BEO1 is an instrument lead, not proof of a public signal. |
| A remote instrument | Light/radar is emitted or received from a place or volume | Image, spectrum, backscatter or derived product | BARLI/BGD has39 dated May2020 product metadata records. A lidar profile observes a volume above a site; it is not a street-level pollutant concentration. |
| A sample plus a laboratory | Air filter, water or biological sample is analyzed later | Chemical concentration, particles, genetic detections | Ada Marina aerosol dataset records and local water/bee studies reveal extra properties; catalogue access and restricted files remain distinct. Sampling time and analysis/report time differ. |
| Infrastructure with telemetry | A power plant, pump, meter or traffic system records its own operation | Power, flow, runtime, counts, fault state | Pupin solar SCADA, Voždovac CHP, TENT and smart meters appear in dated sources. Current public readout is a separate unresolved question. |
| Repurposed infrastructure | Telecom link attenuates in rain; fibre strains under ground motion | Derived rainfall or vibration/traffic indicators | Verified foreign methods; local implementation and lawful telemetry access unverified. |
| A retained material trace | A filter, deposit, surface or archive preserves an interaction | A later observation of past conditions | Air-filter eDNA is an international precedent. Whether suitable Belgrade filters are retained is an open research question. |
| A network of distributed observations | Several places are sampled under a protocol | Spatial pattern and changing coverage | Local fixed/mobile field campaigns exist; selection of sites and instruments limits citywide generalization. |
| An institutional operational record | A public service records an event or an administrative action | Notice, aggregate counter or dated report | Existing BEOPS notice and public-service sources belong here. An announcement or planned outage is not a physical measurement that the event happened. |
| An explicit model or synthesis | A procedure combines measured fields and assumptions | Estimate, forecast, classification or index | Thermal comfort indices, rainfall retrieval, InSAR displacement and virtual black-carbon sensing need the inputs, method and uncertainty retained. They are not independent raw senses. |

Humans also notice, describe and interpret environments. Published aggregate soundscape/perception research can supply context, but collecting people's records is outside this pass. The device inventory must not become a reason to track individuals.

## Live is a property of the evidence chain

Use separate fields for: existence/deployment date; phenomenon/sample time; analysis time; publication/update time; receipt time; timezone; sampling interval; publication interval; aggregation window; and observed delivery lag. Unknown fields remain unknown.

For organizing the search, use these descriptive states rather than a single live/not-live boolean:

| State | Evidence required | Example from this wave |
|---|---|---|
| Time-verified recent observation | An explicit observation timestamp and known clock, checked against receipt; any claimed lag calculated from those fields | No new continuously fresh public feed was established by the breadth/literature pass. |
| Recent dated publication, clock incomplete | A recent source date/window, but missing year/timezone/time semantics or untested lag | Record168 ends06September2026 at 00:00 with timezone unknown. Borča groundwater's last displayed day is06.09., year and clock omitted. |
| Historical empirical series | A real past sampling interval and method | ACTRIS May2020 products; local2019 noise campaign; solar2014/CHP2021–2022 operational studies. |
| Instrument existence, output unavailable | A credible deployment/instrument source without a verified current readout | Pupin public-browser claim; airport noise network; installed meter inventory. |
| Proposed capability or transferable method | A design/model or a foreign example | Dutch microwave rainfall and Palo Alto fibre DAS; local deployment must be separately established. |

A source describing a continuous instrument, a daily series and a real-time laboratory technique says three different things. None by itself establishes that a usable measurement of Belgrade reaches us now. A slow process can still be a useful sense: seasonal groundwater movement, retained contaminants and structural displacement reveal parts of reality on different timescales.

## Newly useful search directions

1. **Groundwater as a current-looking daily window.** The[exact RHMZ page](https://www.hidmet.gov.rs/latin/osmotreni/podzemne_automatske.php?parametar=nivo&stanica=beograd) opened through the web tool on 2026-09-06 displayed Borča-dubok9NP163 and last label06.09.,488 cm. The page omits the year/timezone and its datum/sign convention has not been reconciled. Do not relabel this as488 cm depth, infer an absolute elevation, or assign the current year to the observation. Earlier scout cached readings differed; preserve the date of each review.
2. **Local InSAR despite a service coverage gap.** The[EGMS operator product page](https://land.copernicus.eu/en/products/european-ground-motion-service/egms-calibrated) lists EU27, Iceland, Norway and UK, with annual archive updates. Serbia is outside that stated product footprint. This does not exclude local Sentinel-1 research, demonstrated by Umka papers in the ground literature lane.
3. **Follow the data statement.** A paper may name a DOI, institutional deposit, device model, historical API or archived campaign absent from general portal search. Check the exact record and its rights before any download. Restricted files and request-only data remain useful discovery outcomes.
4. **Look for operating systems that happen to measure.** Energy/flow/temperature telemetry may exist because a plant must operate, not because somebody built an observatory. Papers provide dates and device clues; they do not establish present public access.
5. **Search beyond citywide summaries.** A named park, bridge, filter, school, pumping station or river reach may be a stronger discovery key than “Belgrade smart city”. Locality variants and Serbian scripts matter.
6. **Find the missing disciplines.** Bioacoustics, phenology, eDNA, material indicators, hydrological samples, microclimates and maintenance records deserve explicit search lanes alongside weather, traffic and pollution portals.

## Access and reuse remain distinct

Keep a source's access state, article licence, dataset licence, restrictions on automated collection, and redistribution scope in separate fields. The[current legal frame](../07-legal/COLLECTION_LEGAL_FRAME.md) and[follow-up legal decisions](../07-legal/DEVICE_FOLLOWUP_LEGAL_2026-09-06.md) remain in force. “Public paper”, “downloadable metadata” and “open raw data” are not interchangeable. This literature map grants no collection permission.

## Honest verdict

This map integrates dated device reconnaissance, selected scientific literature and explicitly labeled methodological inferences. It expands the search space without turning archives, simulations or foreign precedents into local live feeds. It does not constitute an exhaustive instrument census, complete literature review or independently calibrated measurement system. Current raw data were not collected in the breadth/literature pass. Earlier exact-route evidence and legal captures remain immutable and separately linked.
