Status: historical
Date: 2026-09-06
Author: Codex /root/emf, ground and structures lane

# Belgrade ground, structures and geodesy

The strongest new public signal is a **groundwater reporting page for Borča-dubok**, with daily dated levels. Its currentness still needs a small direct capture: web-search and web-open caches disagree, and neither supplies a year or timezone. Three further instrument families are supported by primary evidence, but their public live series were not established. These are four ranked lead families, not four verified live feeds or four proposed new registry IDs.

Scope: checked the 188-record proposed registry at `wave2/integration/research/SOURCE_REGISTRY.json` and existing `research/02-senses` reports before searching. Existing S16/S19/S53/S111 seismic sources, S88 Sentinel-1, S91 Grocka magnetic data and S102 EGMS are not new sources. Historical BEOG GNSS and national AGROS were already mentioned in research. No raw data was downloaded, authentication attempted, institution contacted, D: file changed, or source ID allocated. Search evidence is not a saved permission capture.

## 1. Groundwater: Borča-dubok reporting page and local piezometer pairs

**New signal family; public numerical observations, live status unresolved.** The operator's [reporting groundwater page](https://www.hidmet.gov.rs/latin/osmotreni/podzemne_automatske.php?parametar=nivo&stanica=beograd) identifies `Borča-dubok`, `9NP163`, Pančevački rit, Danube basin. It offers Level and Temperature controls and a last-ten-values table. Web open showed ten daily entries from `22.04.` to `01.05.`, latest `401 cm`; search indexing showed `04.08. — 432 cm`. These are conflicting cached views, not evidence of September observations. Year, observation time, timezone and delivery latency are absent. Station zero elevation is 73.79 m; ground elevation 73.39 m. The observed page leaves depth blank. Do not substitute the nearby shallow station's specifications or infer a pressure-probe model from the URL's word “automatske”.

The phenomenon is change in groundwater level beneath the city; the station and reporting system are confirmed, but the transducer model and calibration are not. Daily dates demonstrate a displayed daily series, not the instrument sampling interval. This route is the first priority for the coordinator's exact-route access/legal capture and bounded HTML inspection. The same station selector visibly includes Obrenovac, but its exact route and readings were not followed in this lane.

Useful deployed-device context is independent of the live-page question:

| Operator station card | Local deployment and working programme | What remains unproved |
|---|---|---|
| [Borča 9NP164](https://www.hidmet.gov.rs/latin/hidrologija/podzemne/stanica.php?pd_rb=5230) | 44°52′33″ N, 20°28′25″ E; founded 01.01.1994; labelled active; JP Đerdap founder; 11.68 m depth; three level measurements/month. | This is **164**, not reporting-page **163**. Model, latest timestamp and telemetry not specified. |
| [Čuvarnica-dubok 9NP165](https://www.hidmet.gov.rs/latin/hidrologija/podzemne/stanica.php?pd_rb=5240) | 44°51′16″ N, 20°27′49″ E; founded 01.01.1994; labelled active; 31.58 m depth; six measurements/month. | Site status is metadata; no current numerical observation inspected. |
| [Čuvarnica 9NP166](https://www.hidmet.gov.rs/latin/hidrologija/podzemne/stanica.php?pd_rb=5250) | Same rounded coordinates; 11.63 m depth; six measurements/month; founded 01.01.1994 and labelled active. | Same rounded coordinates do not mean same well. Separate geodetic coordinates and depths are supplied. |

These cards describe relative water depths measured down from the pipe top, in cm, and acknowledge interruptions. They are not surface-river gauges. The operator's [groundwater network description](https://www.hidmet.gov.rs/data/dokumenti_latin/hidrologija_podzemne.pdf) documents piezometers as the physical monitoring infrastructure, but is historical and cannot identify a current automatic sensor model.

**Access/reuse:** public HTML was readable; RHMZ copyright is displayed. No exact numerical-product reuse grant was established here. Existing permission for a different RHMZ route or for an official method description must not be silently expanded to this time series. Next step is the small exact reporting-page capture, not a full yearbook mirror.

## 2. Umka landslide: deployed permanent GNSS and spatial survey observations

**New local deployment evidence; historical measured results, no public live route found.** A [University of Belgrade primary paper](https://dr.rgf.bg.ac.rs/files/original/3eb29255759c7998527e8ef6633bde565dc422b9.pdf), DOI `10.7251/STP2014091S`, documents an automated GNSS system installed in March 2010 on the landslide at Umka, Čukarica, right Sava bank. One monitoring receiver on a house roof was referenced to three surrounding AGROS permanent stations; Leica GNSS Spider/GeoMoS supported 30-second observations. The monitored phenomenon is three-dimensional ground displacement. Receiver model was not established from the inspected passage.

The paper was [published 10 June 2020](https://doisrpska.nub.rs/index.php/STPG/article/view/6803). Its displayed permanent-station series ends December 2018 at 12-hour plotted intervals; a separate 62-point campaign has March 2018, November 2018 and April 2019 epochs. Those passive points are survey marks, not 62 continuously transmitting sensors. The repository's 2026 modification timestamp is not a measurement date. The paper acknowledges interruptions and a December 2013 monitoring-point relocation.

**Access/reuse:** the paper and its figures/tables are public; no public RINEX/time-series endpoint or dataset licence was identified. The article documents historical real-time acquisition, not real-time public access today. Retain as deployed monitoring capability and historical data evidence. Minimal source capture is the publisher landing page plus selected paper passages; do not create an AGROS account or request raw records under this task.

## 3. Belgrade RSZ BEO1: a strong-motion accelerograph distinct from BEO metadata

**New instrument detail under existing seismic sources; no new public waveform feed.** The operator's [accelerographic station table](https://www.seismo.gov.rs/Akcelerometrijske%20stanice_eng.htm) identifies **BEO1**, Beograd RSZ, latitude 44.8093, longitude 20.4715, altitude 128 m, **ETNA accelerograph**, EC-8 ground type B. Its real-time data-transfer field says **local network**. The [Serbian explanation](https://www.seismo.gov.rs/Akcelerometrijske%20stanice_l.htm) dates formation of this network to 2009 and documents acquisition of ETNA and EpiSensor instruments.

This measures strong ground acceleration and complements the known BEO seismic station; the codes must not be equated without a station/channel crosswalk. The table supplies neither a reading timestamp nor sampling frequency, calibration, public waveform URL or explicit update date. “Real-time local network” is an operator transport fact, not public live access. Retain as a device enrichment to S16/S53/S111 as appropriate, not a duplicate new network record.

**Access/reuse:** public institutional metadata; waveform access and licence remain separate and unresolved. No SeedLink connection, station scan, fresh waveform fetch or authentication attempt was made. Minimal capture: the exact small operator station table.

## 4. Gazela and Ada north-approach structures: actual load-test instrumentation

**New historical deployment/campaign lead; no permanent live bridge system established.** The authors' [2018 conference paper landing page](https://www.gf.uns.ac.rs/~zbornik/index.php?lang=LAT&menu=6&rad_id=685&zbornik_id=45), DOI `10.14415/konferencijaGFS2018.075`, is “Organization of bridge load testing: recent experiences”. The publisher-indexed [paper](https://zbornik.gf.uns.ac.rs/doc/NS2018.75.pdf) describes Gazela and the viaduct of the Ada bridge's north approach, built 2016–2017. Gazela involved strain measurement preparation, surveying, static and dynamic load phases, conducted by IMS and the University of Belgrade laboratories. This is structural response to controlled loading: strain, deflection and dynamic response.

Evidence limits: direct web open of the publisher PDF failed with a non-retryable safety error; only indexed publisher text and the publisher landing page were available here. Exact Gazela night dates (30 June / 1 July 2012 approaches;11/12 August 2012 main structure) appear in the author-uploaded paper text, but should be verified against a coordinator-held publisher copy before strict capture-based integration. No sensor make, sampling cadence, latest public time-series point or permanent deployment was verified. The 2018 publication date is not a current observation.

**Access/reuse:** publisher landing metadata explicitly identifies **CC BY-SA 4.0** for the article. That grant concerns the publication; it does not establish a licence for undisclosed raw bridge records or permission to access a structural-control system. This lane is a historical instrument/campaign lead, ranked below the public groundwater route.

## Resolved exclusions and remaining gaps

**S102 EGMS: current product coverage excludes Serbia.** The [operator's calibrated-product metadata](https://land.copernicus.eu/en/products/european-ground-motion-service/egms-calibrated) explicitly lists EU27, Iceland, Norway and United Kingdom; annual updates and archive usability are specified. The [29 April 2026 release announcement](https://land.copernicus.eu/en/news/egms-annual-update-brings-new-data-improvements-to-egms-explorer) describes observations 2020–2024, not a live 2026 series. Thus “Europe”, a Belgrade map tile or an authentication response is not evidence of local EGMS measurements. Recommend a scope correction using the operator metadata, without more 401 probes.

The [2026 primary EGMS evolution paper](https://doi.org/10.1016/j.rse.2026.115389) discusses possible extension including Serbia from 2028; this is a roadmap, not a guarantee. Its [author-institution repository landing](https://nora.nerc.ac.uk/id/eprint/541547/) marks the publication CC BY 4.0. The [2025 SerbianGMS paper](https://isprs-archives.copernicus.org/articles/XLVIII-4-W13-2025/57/2025/) explicitly proposes a conceptual future SrbGMS. It must not be promoted to an operating national data service. Its article is CC BY 4.0.

**Bridge naming trap:** the open [Old ADA bridge vibration dataset paper](https://ascelibrary.org/doi/abs/10.1061/%28ASCE%29BE.1943-5592.0001730) concerns Japan, demolished 2012. It is not Belgrade's Ada bridge. A Leica Apollo-bridge case study concerns Bratislava. Neither is local device coverage.

**Unresolved after bounded searches:** no current public Belgrade GNSS coordinate/tropospheric-delay series beyond the already known historical BEOG study; no primary evidence of a public Belgrade fiber-DAS or infrasound observing installation/feed; no public continuous Belgrade bridge vibration stream. These are search gaps, not proof the instruments do not exist. Grocka geomagnetism is already S91 and was not relabelled as new.

## Search and handoff log

Read the room door, parent assignment/steering, 188-record proposed registry and relevant existing senses reports; historical D campaign board was complete, while parent explicitly assigned this new C-only lane. Searches covered official RSZ accelerographs; BEOG/AGROS/EPN/Nevada GNSS; Umka GNSS/InSAR/inclinometers; Gazela/Ada/Pupin bridge monitoring; RHMZ groundwater and Pančevački rit; Belgrade fiber DAS/infrasound; EGMS operator coverage and SerbianGMS. Source-hosted papers, operator station pages and manufacturer cases were preferred. Generic capability pages and nonlocal deployments were discarded. No source collection helper was run.

Coordinator priorities: (1) capture exact Borča-dubok reporting HTML and access/reuse text, then inspect freshness without assigning a missing year; (2) capture operator EGMS coverage for S102 correction; (3) retain BEO1 as device detail and Umka as historical monitored terrain; (4) pursue bridge records only if later work calls for historical structural response rather than current public signals.


## Coordinator integration note

Accepted as a dated discovery dossier with its stated evidence limits, not an access clearance or live-feed verification. Current registry remains188 records. No source IDs were allocated from these broader leads.

A later coordinator web review of the same exact RHMZ reporting URL on2026-09-06 displayed06.09.—488cm through28.08.—469cm. This differs from the earlier cached views documented above. Year/timezone and datum interpretation remain unresolved; no observation year or depth interpretation was inferred. See[SENSES_CONTEXT_MAP_2026-09-06.md](SENSES_CONTEXT_MAP_2026-09-06.md).
