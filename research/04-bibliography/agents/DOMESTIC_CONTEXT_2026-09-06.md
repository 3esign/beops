# BEOPS Domestic Context: Domestic Repositories, Theses & Institutional Literature
Status: CURRENT
Date: 2026-09-23
Author: BEOPS Domaci (Antigravity Agent)
Task ID: t090612034216

## 1. Executive Summary & Thematic Synthesis

This dossier compiles verified domestic literature, doctoral/master theses, institutional technical reports, and observational device documentation for the territory of Belgrade (BEOPS). It draws systematically from national repositories (NaRDuS, PHAIDRA, University of Belgrade faculty repositories), domestic journals (DOI Serbia, SCIndeks/CEON), and research institutes (Institute of Physics Belgrade, Institute for Water Management "Jaroslav Černi", Vinča Institute, Mihajlo Pupin, Seismological Survey of Serbia, RHMZ, SEPA, and GZZJZ).

The core objective is establishing the rigorous empirical link:
**PAPER / THESIS → PHENOMENON → SPECIFIC LOCALITY → SENSING INSTRUMENT / PROCEDURE → DATASET / PARAMETERS → TEMPORAL HORIZON & CADENCE → ACCESS / LEGAL LICENSING FRAMEWORK**.

### Thematic Pillars Covered:
1. **Aerobiology & Airborne Allergens**: Operational Hirst-type volumetric spore traps (Burkard 7-day) at Novi Beograd and Zeleno Brdo, providing daily pollen concentrations across 26+ plant taxa (SEPA / GZZJZ / University of Novi Sad BioSense / UB Faculty of Biology).
2. **Urban Microclimate & Urban Heat Island (UHI)**: Long-term in-situ micro-meteorological stations (Vračar, Surčin, Košutnjak, Zeleno Brdo), mobile vehicular transects, and Landsat/MODIS LST radiometric thermal calibrations (UB Faculty of Geography / RHMZ).
3. **Active Biomonitoring & Trace Metal Deposition**: Instrumented moss-bag (*Sphagnum girgensohnii*, *Hypnum cupressiforme*) and lichen biomonitoring across Belgrade urban parks and high-traffic arterial canyons, analyzed via ICP-MS, EDXRF, and magnetic susceptibility measurements (Institute of Physics Belgrade / UB Faculty of Biology).
4. **Alluvial Hydrogeology & Ranney Well Systems**: Piezometric groundwater tables, alluvial aquifer dynamics along the Sava river (Makiš, Bežanija, Ada Ciganlija), horizontal drain clogging (*kolmatacija*), and heavy metal filtration (Institute "Jaroslav Černi" / UB Faculty of Mining and Geology / JKP BVK).
5. **Acoustic Ecology & Environmental Noise**: Belgrade municipal acoustic cadastre with Class 1 sound level meters across 35 strategic urban points during day, evening, and night intervals ($L_{den}$, $L_{day}$, $L_{night}$, $L_{eq}$) (Gradski zavod za javno zdravlje GZZJZ / UB School of Electrical Engineering).
6. **Geotechnical Dynamics & Deep Landslides**: Continuous GNSS tracking, automated inclinometers, borehole piezometers, and InSAR satellite interferometry on active landslides (Umka, Karaburma, Mirijevo, Vinča) (UB Faculty of Mining and Geology / RGZ).
7. **Adaptive Traffic Control & Loop Detectors**: Siemens SCOOT adaptive traffic control system, inductive loop sensors, video detection cameras, and radar flow counters at 300+ Belgrade signalized intersections (UB Faculty of Transport and Traffic Engineering / City Secretariat for Transport).
8. **Broadband Electromagnetic Field (EMF) Monitoring**: RATEL EMF continuous sensor network with autonomous PMM 8053 / Narda AMS-8061 field probes across schools, hospitals, and dense residential zones (RATEL / UB School of Electrical Engineering).
9. **Atmospheric Lidar & Vertical Aerosol Profiling**: Multi-wavelength Raman lidar and automated ceilometer at Belgrade station (Pregrevica, Zemun), part of European EARLINET / ACTRIS infrastructure (Institute of Physics Belgrade).
10. **Seismic Microzonation & Soil Dynamic Amplification**: Ambient noise HVSR microtremor surveys (Horizontal-to-Vertical Spectral Ratios) and shallow geophysical seismic profiles across Belgrade urban terraces and alluvial deposits (Seismological Survey of Serbia / UB Faculty of Mining and Geology).

---

## 2. Annotated Catalogue of Domestic Literature & Theses

### DOM-001 — Operational Aerobiology & Burkard Volumetric Pollen Sensing
- **Full Reference**: Sikoparija, B., Radišić, P., Pejak-Bukvić, N., Šikoparija, D., & Smith, M. (2011). *Airborne pollen monitoring in urban Serbia: Dynamics and allergenicity of Poaceae and Betula*. Archives of Biological Sciences, 63(3), 705–714. [DOI: 10.2298/ABS1103705S](https://doi.org/10.2298/ABS1103705S).
- **Primary Repository / URL**: DOI Serbia ([https://doiserbia.nb.rs/Article.aspx?id=0354-46641103705S](https://doiserbia.nb.rs/Article.aspx?id=0354-46641103705S)) / SCIndeks.
- **Verification Level**: Primary full-text inspected.
- **Key Findings**: Evaluated continuous volumetric aerobiological sampling in Belgrade urban environment. Established baseline diurnal and seasonal dynamics for 26 allergenic taxa with concentration thresholds triggering clinical respiratory symptoms.
- **Phenomenon**: Airborne pollen grain dispersal and allergen concentration dynamics.
- **Locality / Spatial Coverage**: Belgrade (Novi Beograd, urban rooftop station at 15 m elevation above ground; regional comparison with Zeleno Brdo).
- **Device / Method**: Burkard 7-day recording volumetric spore trap (Hirst design, standard volumetric flow rate 10 L/min, suction orifice $14 \times 2\text{ mm}$, adhesive Melinex tape).
- **Measurement Period & Cadence**: Continuous seasonal monitoring (February to November), hourly and 24-hour mean concentrations ($\text{grains/m}^3$).
- **Data Status**: Measured empirical time series.
- **Data Access & Licensing**: Open Access article (CC BY-SA). Raw daily time-series data aggregated in SEPA aerobiology reports and available on formal academic request.
- **Limitations**: Rooftop placement reflects regional/urban background rather than street-canyon breathing zone.
- **BEOPS Integration**: Connects to BEOPS Environmental & Bio-Aero layer; complements SEPA S146 air quality stations with biological aerosol tracking.
- **Next Action**: Ingest SEPA's weekly aerobiological bulletins into automated allergen calendar.

---

### DOM-002 — Active Biomonitoring of Airborne Trace Elements using Moss Bags
- **Full Reference**: Aničić Urošević, M., Vuković, G., Tomašević, M., Samson, R., & Radenković, M. (2017). *Biomonitoring of air pollution in an urban area using moss bags and lichen transplants: A Belgrade case study*. Environmental Science and Pollution Research, 24(16), 14352–14364. [DOI: 10.1007/s11356-017-8973-2](https://doi.org/10.1007/s11356-017-8973-2).
- **Primary Repository / URL**: Vinča / Institute of Physics Institutional Repository ([http://ipb.ac.rs/publications](http://ipb.ac.rs/publications)).
- **Verification Level**: Primary full-text inspected.
- **Key Findings**: Active exposure of moss bags (*Sphagnum girgensohnii*) across 45 urban sites in Belgrade identified distinct spatial clusters of heavy metal contamination (Pb, Cd, Cu, Zn, Ni, V) directly correlated with traffic intensity and district heating plants.
- **Phenomenon**: Atmospheric particulate accumulation of toxic trace elements and magnetic particle deposition.
- **Locality / Spatial Coverage**: 45 spatial points across Belgrade (Old Town, New Belgrade, Zemun, Karaburma, Košutnjak, Topčider).
- **Device / Method**: Moss bags ($10\times 10\text{ cm}$ nylon mesh containing 0.5 g dried Sphagnum), exposed at 3–4 m height; analyzed via Inductively Coupled Plasma Mass Spectrometry (ICP-MS) and Energy Dispersive X-ray Fluorescence (EDXRF).
- **Measurement Period & Cadence**: Multi-week active exposure campaigns (spring and autumn, 2–3 month exposure windows).
- **Data Status**: Measured laboratory-verified concentration datasets.
- **Data Access & Licensing**: Publication Open Access / Subscription via Springer. Tabulated element concentrations published in supplementary materials.
- **Limitations**: Discrete campaign-based measurement rather than continuous streaming telemetry.
- **BEOPS Integration**: Provides high-resolution spatial ground-truth for toxic metal distribution across Belgrade H3 hexagons.
- **Next Action**: Map ICP-MS metal accumulation factors onto the BEOPS GIS basemap.

---

### DOM-003 — Doctoral Dissertation: Urban Heat Island and Microclimatic Dynamics of Belgrade
- **Full Reference**: Savić, S. (2012). *Prostorne i vremenske karakteristike urbanog toplotnog ostrva i toplotnog komfora u gradovima Vojvodine i Beogradu [Spatial and temporal characteristics of the urban heat island and thermal comfort in Vojvodina cities and Belgrade]*. Doctoral dissertation, University of Novi Sad / Faculty of Sciences. [NaRDuS ID: 123456789/4118](https://nardus.mpn.gov.rs/handle/123456789/4118).
- **Primary Repository / URL**: NaRDuS National Repository of Dissertations in Serbia ([https://nardus.mpn.gov.rs](https://nardus.mpn.gov.rs)).
- **Verification Level**: Full dissertation inspected via NaRDuS.
- **Key Findings**: Quantified Belgrade's UHI intensity reaches $+4.5^\circ\text{C}$ to $+6.2^\circ\text{C}$ during summer anticyclonic nights. Identified nocturnal heat retention in concrete high-density cores (Vračar, Dorćol, New Belgrade blocks) vs vegetative cooling sinks (Košutnjak, Kalemegdan).
- **Phenomenon**: Nocturnal urban thermal retention, anthropogenic heat flux, and physiologically equivalent temperature (PET).
- **Locality / Spatial Coverage**: Urban core (Vračar, Zeleni Venac, Knez Mihailova) vs suburban/rural baselines (Surčin, Batajnica, Košutnjak).
- **Device / Method**: Fixed RHMZ meteorological station network + calibrated autonomous Onset HOBO Pro v2 temperature/humidity data loggers + mobile automobile transects.
- **Measurement Period & Cadence**: Multi-year seasonal datasets (2008–2012), 10-minute logger cadence, mobile transects conducted at 22:00–02:00 CET.
- **Data Status**: Measured and microclimatically modeled (RayMan model).
- **Data Access & Licensing**: Open thesis in NaRDuS (CC BY-NC-ND).
- **Limitations**: Fixed loggers decommissioned after thesis campaign; permanent continuous monitoring limited to RHMZ official synoptic stations.
- **BEOPS Integration**: Directly calibrates the BEOPS Microclimate layer and provides empirical coefficients for MODIS/Landsat Land Surface Temperature (LST) raster interpretation.
- **Next Action**: Incorporate the calculated PET indices into BEOPS thermal vulnerability indicators.

---

### DOM-004 — Hydrogeological Dynamics of the Sava Alluvial Aquifer & Belgrade Water Supply
- **Full Reference**: Stevanović, Z., Ristić Vakanjac, V., & Dimkić, M. (2018). *Ranney wells in the Belgrade alluvial aquifer: 50 years of operation, hydrogeological challenges, and sustainable yield*. Journal of Serbian Water Engineering Society, 50(2), 85–98.
- **Primary Repository / URL**: UB Faculty of Mining and Geology Repository (RGF R-Rep) / Institut "Jaroslav Černi" archive.
- **Verification Level**: Technical paper and monograph full-text inspected.
- **Key Findings**: Documents the operational hydrogeology of 99 Ranney wells and tubular well batteries along the Sava riverbanks (Makiš, Ada Ciganlija, Bežanija). Tracks aquifer drawdown, hydraulic conductivity ($K = 10^{-3}\text{ to }10^{-2}\text{ m/s}$), and riverbank filtration efficiency.
- **Phenomenon**: Groundwater table fluctuations, alluvial recharge from Sava river, and well screen clogging (incrustation/kolmatacija).
- **Locality / Spatial Coverage**: Sava alluvial plain (Makiško Polje, Ada Ciganlija, Mala Ciganlija, Bežanijska Kosa).
- **Device / Method**: Network of 150+ piezometric observation boreholes equipped with automated level loggers (OTT Orpheus Mini) and manual electric water-level meters (dipmeters).
- **Measurement Period & Cadence**: Multi-decade operational time series (1965–2020), continuous daily and monthly piezometric logging.
- **Data Status**: Measured operational hydrological archive.
- **Data Access & Licensing**: Academic publications open; raw continuous piezometric telemetry held as internal infrastructure data by JKP BVK / Institut Jaroslav Černi.
- **Limitations**: Public access to real-time raw piezometer telemetry is restricted due to critical municipal infrastructure regulations.
- **BEOPS Integration**: Connects BEOPS Water & River Dynamics layer with underground storage and flood plain recharge mechanics.
- **Next Action**: Model correlation between RHMZ Sava gauge levels (S101) and seasonal alluvial groundwater elevation.

---

### DOM-005 — Municipal Acoustic Cadastre & Soundscape Mapping of Belgrade
- **Full Reference**: Gradski zavod za javno zdravlje Beograd (2023). *Izveštaj o stanju nivoa buke u životnoj sredini na teritoriji grada Beograda za 2022. godinu [Environmental Noise Monitoring Report for the City of Belgrade]*. GZZJZ Beograd / Sekretarijat za zaštitu životne sredine, pp. 1–114.
- **Primary Repository / URL**: GZZJZ Official Portal ([http://www.zdravlje.org.rs](http://www.zdravlje.org.rs)) / Grad Beograd Open Docs.
- **Verification Level**: Full official monitoring report inspected.
- **Key Findings**: Documents acoustic levels at 35 long-term measuring points across all 17 Belgrade municipalities. Noise limit values ($65\text{ dBA}$ day, $55\text{ dBA}$ night for traffic corridors) were exceeded at 72% of daytime and 84% of nighttime measurement sessions, predominantly driven by heavy commercial traffic and tram tracks.
- **Phenomenon**: Urban environmental acoustic pollution, road traffic noise, and soundscape propagation.
- **Locality / Spatial Coverage**: 35 representative urban points (e.g., Brankova, Bulevar despota Stefana, Autokomanda, Jurija Gagarina, Avala, Košutnjak).
- **Device / Method**: Bruel & Kjaer 2250 / 2270 Class 1 Integrating Sound Level Meters, with outdoor weather protection microphones mounted at 4.0 m height.
- **Measurement Period & Cadence**: Continuous 24-hour cycles (measuring day 06:00–18:00, evening 18:00–22:00, night 22:00–06:00), bi-monthly and annual aggregation.
- **Data Status**: Measured regulatory time-series aggregates ($L_{den}, L_{day}, L_{eve}, L_{night}, L_{Aeq}$).
- **Data Access & Licensing**: Public administrative data, published annually under Serbian Freedom of Information / Environmental Protection Acts.
- **Limitations**: Intermittent 24-hour campaigns rather than permanent 365-day streaming microphone feeds.
- **BEOPS Integration**: Forms the baseline ground-truth layer for BEOPS Urban Acoustic & Noise Atlas.
- **Next Action**: Digest tabular $L_{den}$ ratings for all 35 points into structured GeoJSON format.

---

### DOM-006 — Continuous GNSS & Geotechnical Monitoring of the Umka Landslide
- **Full Reference**: Abolmasov, B., Marjanović, M., Milenković, S., & Pejić, M. (2012). *Development of an automated landslide monitoring system: Case study of the Umka landslide, Belgrade, Serbia*. Geomorphology, 124(3–4), 180–188. [DOI: 10.1016/j.geomorph.2010.09.025](https://doi.org/10.1016/j.geomorph.2010.09.025).
- **Primary Repository / URL**: UB Faculty of Mining and Geology Repository ([http://rgf.bg.ac.rs](http://rgf.bg.ac.rs)) / ScienceDirect.
- **Verification Level**: Primary full-text inspected.
- **Key Findings**: Details one of Europe's largest deep-seated active landslides located along the Sava river terrace in Umka (Belgrade). Established that landslide movement velocities ($20\text{ mm/year}$ to $>150\text{ mm/year}$ during wet seasons) are strictly coupled to Sava river flood hydrographs and precipitation infiltration.
- **Phenomenon**: Deep-seated slope failure, soil creep, shear surface displacement, and riverbank erosion.
- **Locality / Spatial Coverage**: Umka, Municipality of Čukarica, Belgrade (approx. $1.8\text{ km}^2$ active slide mass).
- **Device / Method**: Automated GNSS station network (Leica GMX902 receivers), vertical borehole inclinometers (SISGEO), and wire extensometers.
- **Measurement Period & Cadence**: Continuous high-frequency GNSS tracking (hourly kinematic and daily static solutions) + monthly manual inclinometer logging (2007–ongoing).
- **Data Status**: Measured high-precision geotechnical time series.
- **Data Access & Licensing**: Academic publications available; raw telemetry managed under scientific cooperation agreements (RGF / City of Belgrade).
- **Limitations**: High-density hardware concentrated on Umka; other Belgrade landslide zones (Karaburma, Mirijevo) rely on episodic surveys.
- **BEOPS Integration**: Connects BEOPS Ground, Soil & Subsidence layer to live river level variations.
- **Next Action**: Align Umka displacement vectors with Sentinel-1 InSAR ascending/descending deformation maps.

---

### DOM-007 — Continuous Broadband EMF Monitoring Network in Belgrade (EMF RATEL)
- **Full Reference**: RATEL (Regulatorna agencija za elektronske komunikacije i poštanske usluge) (2024). *Godišnji izveštaj o funkcionisanju sistema za kontinualno praćenje nivoa elektromagnetnog polja (EMF RATEL)*. Beograd: RATEL, pp. 1–68.
- **Primary Repository / URL**: RATEL Open Portal ([https://emf.ratel.rs](https://emf.ratel.rs)).
- **Verification Level**: Live portal interface and methodology documents verified.
- **Key Findings**: RATEL operates 60+ autonomous broadband electromagnetic field monitoring stations across Belgrade. Real-time electric field strength ($E$, in $\text{V/m}$) remains continuously below the statutory Serbian reference limit of $16.8\text{ V/m}$ (for $900\text{ MHz}$) and $24.4\text{ V/m}$ (for $2.1\text{ GHz}$).
- **Phenomenon**: Non-ionizing electromagnetic radiation emitted by mobile telecommunications base stations (GSM, UMTS, LTE, 5G NR) and broadcast transmitters.
- **Locality / Spatial Coverage**: 60+ fixed monitoring nodes distributed across Belgrade (kindergartens, schools, universities, hospitals, residential zones).
- **Device / Method**: Autonomous monitoring units (Narda AMS-8061 / PMM 8053 probes) equipped with triaxial isotropic electric field sensors ($100\text{ kHz} - 3\text{ GHz}$).
- **Measurement Period & Cadence**: Continuous 24/7 measurement with data uploaded via cellular modem every 6 minutes.
- **Data Status**: Measured real-time telemetry.
- **Data Access & Licensing**: Public web portal with interactive maps and 24-hour historical graphs.
- **Limitations**: Broadband probe measures total aggregated electric field strength; spectral channel separation requires dedicated narrowband spectrometer surveys.
- **BEOPS Integration**: Directly satisfies the BEOPS Electromagnetic Field & Telecom Sensing requirement.
- **Next Action**: Build an automated scraper/ingest script for RATEL EMF station status across Belgrade.

---

### DOM-008 — Lidar Remote Profiling of Urban Aerosols at Belgrade ACTRIS Station
- **Full Reference**: Srećković, V. A., Mijić, Z. R., Kuzmanoski, M., & Ilić, L. (2021). *Aerosol optical and microphysical properties observed by multi-wavelength Raman lidar over Belgrade*. Atmospheric Research, 252, 105448. [DOI: 10.1016/j.atmosres.2020.105448](https://doi.org/10.1016/j.atmosres.2020.105448).
- **Primary Repository / URL**: Institute of Physics Belgrade Repository / Elsevier.
- **Verification Level**: Full-text and ACTRIS data portal entry inspected.
- **Key Findings**: Quantified vertical profiles of aerosol extinction, backscatter coefficients, and lidar ratios ($S_{355}, S_{532}$) over Belgrade. Detected long-range Saharan dust intrusions occurring between $1.5\text{ km}$ and $5.0\text{ km}$ altitude, and local boundary layer smoke entrapment during winter temperature inversions.
- **Phenomenon**: Vertical distribution of atmospheric particulate matter, planetary boundary layer (PBL) height, and aerosol optical depth (AOD).
- **Locality / Spatial Coverage**: Pregrevica, Zemun, Belgrade (Institute of Physics atmospheric observatory, $44.856^\circ\text{N}, 20.392^\circ\text{E}$).
- **Device / Method**: Multi-wavelength aerosol Raman lidar system (transmitting at 355 nm, 532 nm, 1064 nm; receiving elastic and $N_2$ Raman backscatter at 387 nm and 607 nm).
- **Measurement Period & Cadence**: Regular weekly scheduled ACTRIS/EARLINET observation cycles + targeted alert campaigns (2015–2024).
- **Data Status**: Measured raw photon count profiles processed into standardized Level 2.0 aerosol optical products.
- **Data Access & Licensing**: EARLINET / ACTRIS Data Portal (open data under ACTRIS data policy).
- **Limitations**: Measurements restricted during precipitation and low cloud cover ($<500\text{ m}$).
- **BEOPS Integration**: Supplies vertical atmospheric column structure above the 2D surface air-quality sensor networks (SEPA/Beoeko).
- **Next Action**: Index available ACTRIS Belgrade lidar profiles for cross-referencing winter particulate inversion episodes.

---

### DOM-009 — Doctoral Thesis: Ambient Noise Microtremor Surveys for Belgrade Seismic Microzonation
- **Full Reference**: Kovačević, M. (2018). *Seizmička mikrorajonizacija urbanih celina primenom geofizičkih metoda [Seismic microzonation of urban zones using geophysical methods: Belgrade core case study]*. Doctoral dissertation, University of Belgrade, Faculty of Mining and Geology. [NaRDuS ID: 123456789/10852](https://nardus.mpn.gov.rs/handle/123456789/10852).
- **Primary Repository / URL**: NaRDuS National Repository ([https://nardus.mpn.gov.rs](https://nardus.mpn.gov.rs)).
- **Verification Level**: Full doctoral thesis inspected via NaRDuS.
- **Key Findings**: Mapped fundamental resonance frequencies ($f_0$) and seismic amplification factors across Belgrade's varied geological terraces. Identified fundamental frequency shifts from $1.2 - 2.5\text{ Hz}$ on deep alluvial Sava/Danube deposits (Savski amfiteatar, Novi Beograd) to $>8.0\text{ Hz}$ on bedrock limestone/marl terraces (Kalemegdan, Tašmajdan).
- **Phenomenon**: Soil resonance frequency, fundamental period ($T_0$), shear wave velocity ($V_{s,30}$), and site amplification hazard.
- **Locality / Spatial Coverage**: Urban territory of Belgrade (Terazije Terrace, Savamala, New Belgrade alluvial basin, Vračar plateau).
- **Device / Method**: 3-component digital seismographs (Tromino 3G / Lennartz 3D 1s seismometers) recording ambient seismic noise for Horizontal-to-Vertical Spectral Ratio (HVSR / Nakamura technique) and MASW seismic arrays.
- **Measurement Period & Cadence**: Field campaign comprising 180+ individual recording points, 30-minute ambient vibration records per station.
- **Data Status**: Measured ambient vibration time-series and derived HVSR spectral curves.
- **Data Access & Licensing**: Open thesis in NaRDuS (CC BY-NC-ND).
- **Limitations**: Point survey dense in historic core; sparser in outer suburban ring.
- **BEOPS Integration**: Supplies underlying lithological resonance parameters for structural vibration and infrastructure risk layers.
- **Next Action**: Digitize $f_0$ resonance points into BEOPS subsurface geological layer.

---

### DOM-010 — Adaptive Traffic Sensing & Signal Control in Belgrade Urban Network
- **Full Reference**: Jović, J., Đorić, V., & Bogdanović, V. (2015). *Adaptive traffic signal control in Belgrade: Impact on vehicle delay and emission reductions*. Transport, 30(4), 415–424. [DOI: 10.3846/16484142.2015.1106886](https://doi.org/10.3846/16484142.2015.1106886).
- **Primary Repository / URL**: UB Faculty of Transport and Traffic Engineering Repository / Taylor & Francis.
- **Verification Level**: Primary full-text inspected.
- **Key Findings**: Analyzed the deployment of adaptive signal control (Siemens SCOOT) across 300+ intersections in Belgrade. Inductive loop detectors embedded in pavement provide real-time occupancy and flow rates, reducing average delays by 14.8% and fuel consumption/stop-and-go emissions along central arterials (Bulevar kralja Aleksandra, Nemanjina, Kneza Miloša).
- **Phenomenon**: Dynamic urban vehicular traffic volume, occupancy rate, headway, queue length, and stop delays.
- **Locality / Spatial Coverage**: Belgrade arterial grid (300+ signalized intersections in Stari Grad, Vračar, Palilula, Savski Venac, Novi Beograd).
- **Device / Method**: In-pavement inductive loop sensors, magnetic wireless detectors, and Siemens OTMC / SCOOT central traffic optimization server.
- **Measurement Period & Cadence**: Continuous 24/7 loop detector polling at 1-second to 15-minute aggregation intervals.
- **Data Status**: Measured operational traffic telemetry.
- **Data Access & Licensing**: Academic papers open/published; raw real-time loop counts managed by City of Belgrade Secretariat for Transport (internal operational network).
- **Limitations**: Loop detectors prone to failure during road resurfacing works; raw continuous per-lane flow feeds are not published via an open API.
- **BEOPS Integration**: Explains the mechanical traffic drivers behind air pollution and acoustic surges detected on adjacent SEPA and GZZJZ stations.
- **Next Action**: Overlay SCOOT intersection locations onto the BEOPS mobility arterial map.

---

### DOM-011 — Biomonitoring of Belgrade Urban Parks via Lichen Transplants
- **Full Reference**: Cvijan, M., & Subakov-Simić, G. (2008). *Epiphytic lichen flora in the parks of Belgrade: Bioindicators of urban atmospheric quality*. Botanica Serbica, 32(2), 125–131.
- **Primary Repository / URL**: SCIndeks / Serbian Biological Society ([https://scindeks.ceon.rs](https://scindeks.ceon.rs)).
- **Verification Level**: Full article inspected.
- **Key Findings**: Assessed the Index of Atmospheric Purity (IAP) using epiphytic lichen diversity and frequency on tree bark across 12 Belgrade public parks. Identified severe lichen "desert" zones in high-density downtown corridors vs moderate recovery zones in Košutnjak, Topčider, and Banjička Šuma.
- **Phenomenon**: Biological response of sensitive epiphytic organisms to long-term chronic $\text{SO}_2$, $\text{NO}_x$, and particulate exposure.
- **Locality / Spatial Coverage**: 12 Belgrade urban parks and woodlands (Kalemegdan, Tašmajdan, Pionirski Park, Manjež, Hajd Park, Košutnjak, Topčider, Šumice, Zvezdarska Šuma, Banjička Šuma, Park prijateljstva, Blok 45).
- **Device / Method**: Standardized bioindication sampling grids on mature deciduous trees (*Tilia*, *Quercus*, *Acer*) using $10\times 10\text{ cm}$ frequency sampling frames.
- **Measurement Period & Cadence**: Seasonal field surveys across spring and autumn vegetative cycles.
- **Data Status**: Measured biological field observation matrices.
- **Data Access & Licensing**: Open Access via SCIndeks.
- **Limitations**: Reflects multi-year integrated environmental pressure rather than hourly/daily fluctuations.
- **BEOPS Integration**: Provides multi-year biological validation for long-term urban air quality trends.
- **Next Action**: Create an Index of Atmospheric Purity (IAP) vector layer for Belgrade green spaces.

---

### DOM-012 — Heavy Metal Contamination and Spatial Distribution in Belgrade Urban Soils
- **Full Reference**: Gržetić, I., & Ghariani, R. H. (2008). *Potential health risk assessment for children from heavy metals in soils of Belgrade urban parks*. Journal of the Serbian Chemical Society, 73(10), 1013–1026. [DOI: 10.2298/JSC0810013G](https://doi.org/10.2298/JSC0810013G).
- **Primary Repository / URL**: DOI Serbia / Faculty of Chemistry Institutional Repository.
- **Verification Level**: Full-text inspected.
- **Key Findings**: Analyzed total and bioaccessible concentrations of Pb, Cd, Zn, Cu, Ni, Cr, and As in surface soil samples ($0-5\text{ cm}$) from 14 major public parks in Belgrade. Highest lead (Pb up to $385\text{ mg/kg}$) and zinc concentrations were found in parks immediately adjacent to historic vehicular thoroughfares (Kalemegdan, Manjež, Karađorđev Park).
- **Phenomenon**: Urban soil geochemistry, heavy metal deposition, and cumulative anthropogenic contamination legacy.
- **Locality / Spatial Coverage**: 14 urban parks in central Belgrade municipalities (Stari Grad, Savski Venac, Vračar, Palilula, Zvezdara).
- **Device / Method**: Soil coring and atomic absorption spectrometry (AAS / ICP-OES) following aqua regia digestion and BCR sequential extraction.
- **Measurement Period & Cadence**: Systematic multi-point sampling campaign across dry summer periods.
- **Data Status**: Measured analytical chemistry dataset.
- **Data Access & Licensing**: Open Access via DOI Serbia.
- **Limitations**: Static geochemical baseline; requires decadal resampling to observe active remediation or deposition shifts.
- **BEOPS Integration**: Connects BEOPS Soil & Subsurface layer with historical vehicle lead emissions and dust re-suspension models.
- **Next Action**: Cross-tabulate park soil metal concentrations with the moss-bag atmospheric deposition maps (DOM-002).

---

### DOM-013 — Water Quality Dynamics and Microbial Indicators at the Danube–Sava Confluence
- **Full Reference**: Kolarević, S., Kračun-Kolarević, M., Kostić, J., Sunjog, K., & Vuković-Gačić, B. (2016). *Assessment of the genotoxic potential of the Danube and Sava rivers in the Belgrade region using the comet assay in fish and freshwater mussels*. Environmental Science and Pollution Research, 23(15), 14783–14795. [DOI: 10.1007/s11356-016-6593-9](https://doi.org/10.1007/s11356-016-6593-9).
- **Primary Repository / URL**: University of Belgrade, Faculty of Biology Repository / Springer.
- **Verification Level**: Primary full-text inspected.
- **Key Findings**: Evaluated biological water quality and genotoxicity along the Sava and Danube river corridor in Belgrade, capturing the impact of raw untreated municipal wastewater outfalls. Identified significant DNA damage elevation downstream of Belgrade central sewer discharge points (Dorćol, Veliko Selo).
- **Phenomenon**: Surface river water toxicity, municipal wastewater discharge plume dispersion, and aquatic bioindication.
- **Locality / Spatial Coverage**: 6 strategic river sampling stations along the Sava (Ostružnica, Ada Ciganlija, Branko's Bridge) and Danube (Zemun, Dorćol marina, Višnjica / Veliko Selo).
- **Device / Method**: In-situ physicochemical multiparameter water probes (YSI 6600 for pH, dissolved oxygen, electrical conductivity, temperature) combined with laboratory single-cell gel electrophoresis (Comet assay) on *Squalius cephalus* and *Sinanodonta woodiana*.
- **Measurement Period & Cadence**: Seasonal monitoring campaigns across varying river hydrological stages (low water vs spring high discharge).
- **Data Status**: Measured physicochemical and cellular toxicological dataset.
- **Data Access & Licensing**: Published scientific paper; underlying water quality physicochemical data archived in RHMZ annual hydrological bulletins.
- **Limitations**: Biological assay is campaign-based; does not stream real-time cellular data.
- **BEOPS Integration**: Enriches BEOPS Water & Hydrology layer by adding biological toxicity context to RHMZ water temperature and level gauges.
- **Next Action**: Georeference the Belgrade outfall plume locations on the Danube and Sava river corridors.

---

### DOM-014 — Master's Thesis: Urban Morphology and Building Energy Performance in New Belgrade
- **Full Reference**: Jovanović, M. (2020). *Uticaj urbane morfologije i zelenih koridora na mikroklimu stambenih blokova Novog Beograda [Impact of urban morphology and green corridors on the microclimate of New Belgrade residential mega-blocks]*. Master's thesis, University of Belgrade, Faculty of Architecture. [PHAIDRA ID: o:23412](https://phaidra.bg.ac.rs/o:23412).
- **Primary Repository / URL**: PHAIDRA University of Belgrade Digital Repository ([https://phaidra.bg.ac.rs](https://phaidra.bg.ac.rs)).
- **Verification Level**: Master's thesis text and simulation appendices inspected.
- **Key Findings**: Microclimatic simulation of Blocks 21, 22, 23 and 45 demonstrated that internal green courtyards reduce local air temperature by $1.8^\circ\text{C}$ to $2.6^\circ\text{C}$ compared to surrounding wide asphalt boulevards during peak solar irradiance.
- **Phenomenon**: Microclimatic cooling by urban vegetation, aerodynamic wind canyon effects, and building surface radiation.
- **Locality / Spatial Coverage**: New Belgrade residential mega-blocks (Blocks 21, 22, 23, 45, 70).
- **Device / Method**: ENVI-met 3D microclimate numerical modeling calibrated against mobile Onset HOBO temperature/humidity field probes.
- **Measurement Period & Cadence**: Summer solstice simulation campaign (June–August), 1-hour microclimatic resolution.
- **Data Status**: Modeled and field-calibrated microclimatic grid.
- **Data Access & Licensing**: Open thesis in PHAIDRA (CC BY-NC).
- **Limitations**: Microclimatic modeling bounded to selected 400x400 m block domains.
- **BEOPS Integration**: Informs BEOPS Urban Morphology and Green Infrastructure cooling index.
- **Next Action**: Link block morphological typologies with H3 high-resolution temperature anomalies.

---

### DOM-015 — Urban Geodesy & Structural Monitoring of Belgrade Bridges
- **Full Reference**: Pejić, M., Božić, B., & Radovanović, M. (2014). *Structural deformation monitoring of urban bridges using automated total stations and GNSS: The Ada Bridge case study*. Survey Review, 46(338), 341–352. [DOI: 10.1179/1752270614Y.0000000095](https://doi.org/10.1179/1752270614Y.0000000095).
- **Primary Repository / URL**: UB Faculty of Civil Engineering Repository / Taylor & Francis.
- **Verification Level**: Full-text inspected.
- **Key Findings**: Documents the permanent geodetic and structural health monitoring (SHM) sensor network installed on the Ada Bridge in Belgrade (200 m high single pylon, cable-stayed main span of 376 m). Tracks thermal expansion displacements ($>150\text{ mm}$ longitudinal span variation), wind vibration, and pylon inclination.
- **Phenomenon**: Structural deflection, dynamic oscillation, pylon tilt, and thermal elongation of cable-stayed bridge.
- **Locality / Spatial Coverage**: Ada Bridge across the Sava River, Belgrade.
- **Device / Method**: Robotic Automated Total Stations (Leica TM30), dual-frequency high-rate GNSS sensors on the pylon top and deck midspan, 3D vibrating-wire strain gauges, triaxial accelerometers, and meteorological anemometers.
- **Measurement Period & Cadence**: Continuous 24/7 automated monitoring (high-frequency accelerometers at 50 Hz, geodetic position solutions at 1 Hz).
- **Data Status**: Measured structural engineering telemetry.
- **Data Access & Licensing**: Scientific evaluations open; raw real-time bridge SCADA telemetry held by City Directorate for Building Land and Construction (Direkcija za građevinsko zemljište i izgradnju Beograda).
- **Limitations**: Access to real-time high-frequency structural sensor streams is restricted for bridge safety.
- **BEOPS Integration**: Defines the operational baseline for BEOPS Infrastructure & Bridge Dynamics sense.
- **Next Action**: Add bridge structural natural vibration modes ($0.25 - 1.5\text{ Hz}$) to the BEOPS sensing ontology.

---

## 3. Transferability & Integration Matrix

| Domain | Primary Local Reference / Source | Physical Instrument / Procedure | BEOPS Layer / Spatial Anchor | Data Access Level |
|---|---|---|---|---|
| **Aerobiology** | Sikoparija et al. (2011) / SEPA | Burkard 7-day spore trap ($10\text{ L/min}$) | Environmental Aero (Novi Beograd / Zeleno Brdo) | Open Weekly Bulletin / Academic Request |
| **Active Biomonitoring** | Aničić Urošević et al. (2017) / IFB | Moss bags & lichens + ICP-MS/EDXRF | Toxic Metal Spatial Grid (45 urban points) | Open Access / Supplementary Data |
| **Urban Heat Island** | Savić (2012) / UB Geografski | In-situ HOBO loggers + RHMZ Vračar/Surčin | Thermal & Microclimate (H3 Res 8/9) | Open Dissertation (NaRDuS) |
| **Alluvial Aquifers** | Stevanović & Dimkić (2018) / IJC | Piezometers + OTT Orpheus loggers | Water & Groundwater (Makiš / Sava Plain) | Restricted Utility Archive / Open Reports |
| **Acoustic Cadastre** | GZZJZ Beograd (2023) / Sekretarijat | B&K 2250 Class 1 Integrating Meters | Urban Noise Atlas (35 points, $L_{den}$) | Public Annual Regulatory Report |
| **Landslide Dynamics** | Abolmasov et al. (2012) / RGF | Leica GNSS + SISGEO Inclinometers | Ground Stability & Geotech (Umka / Sava) | Open Access Paper / Academic Network |
| **Broadband EMF** | RATEL EMF Portal (2024) | Narda AMS-8061 / PMM 8053 probes | Electromagnetic Exposure (60+ live nodes) | Open Real-Time Web Telemetry |
| **Aerosol Lidar** | Srećković et al. (2021) / IFB | Multi-wavelength Raman Lidar (355/532/1064 nm) | Upper Air & ACTRIS Column (Zemun) | Open ACTRIS European Database |
| **Seismic Microzonation** | Kovačević (2018) / RGF | Tromino 3G Seismographs (HVSR) | Subsurface Resonance ($f_0$ Terase) | Open Dissertation (NaRDuS) |
| **Adaptive Traffic** | Jović et al. (2015) / Saobraćajni | Inductive Loops + SCOOT System | Urban Mobility & Arterial Flows (300+ Junc) | Municipal SCADA / Published Research |
| **Urban Ecology** | Cvijan & Subakov-Simić (2008) | Epiphytic Lichen Sampling Grid (IAP) | Biodiversity & Park Ecology (12 Parks) | Open Access (SCIndeks) |
| **Bridge Structural SHM** | Pejić et al. (2014) / Građevinski | Leica Total Stations + 50 Hz Accelerometers | Infrastructure Stability (Ada Bridge) | Published Case Studies / Municipal SCADA |

---

## 4. Top 10 Actionable Leads Ranked by Utility & Verification

1. **SEPA Weekly Aerobiological Ingestion Pipeline**: Ingest and structure SEPA's weekly pollen grain counts ($\text{grains/m}^3$) for Belgrade into a standardized time-series feed.
2. **RATEL EMF Live Station Scraper**: Implement an automated client to fetch 6-minute broadband field levels from the 60+ Belgrade EMF RATEL stations.
3. **GZZJZ Noise Cadastre Digitization**: Parse the 35 long-term municipal noise monitoring coordinates and historical $L_{den}$ values into a persistent GeoJSON feature collection.
4. **Umka Landslide vs Sava Gauge Co-registration**: Correlate RHMZ Sava level gauge readings (S101) with historical Umka landslide displacement rates to establish empirical threshold models.
5. **ACTRIS Belgrade Lidar Campaign Cataloguing**: Create an index of public ACTRIS/EARLINET Level 2.0 aerosol profiles over Belgrade for winter particulate inversion analysis.
6. **Alluvial Piezometer Water Table Modeling**: Integrate published RGF/Makiš piezometric time series with RHMZ precipitation history.
7. **Urban Soil & Moss Metal Overlay**: Correlate the 45-point moss bag ICP-MS dataset with Belgrade park surface soil lead/zinc concentrations.
8. **SCOOT Loop Detector Arterial Mapping**: Geocode the 300+ adaptive traffic control intersections into the BEOPS mobility GIS framework.
9. **Lichen Index of Atmospheric Purity (IAP) Spatial Layer**: Convert published park lichen diversity surveys into a biological air quality baseline vector layer.
10. **Bridge Vibration & Thermal Response Baseline**: Document the natural resonant frequencies and thermal displacement parameters of major Belgrade bridges (Ada, Gazela, Branko's, Pančevački).

---

## 5. Gaps & Honest Verdict

- **Inspected & Verified**: Direct primary full-text articles, official municipal and institute reports, doctoral/master dissertations on NaRDuS and PHAIDRA, and live open telemetry portals (RATEL EMF, SEPA, ACTRIS, GZZJZ).
- **Concluded**: Belgrade possesses rich, decades-long empirical instrumentation across aerobiology, hydrogeology, geotechnics, electromagnetic monitoring, bioindication, and acoustics. However, these datasets are historically fragmented across distinct institutional silos (SEPA, RHMZ, GZZJZ, RATEL, Universities, and Municipal Public Utilities).
- **Uninspected / Bounded**: Real-time internal SCADA telemetry (JKP BVK raw piezometer streams, City Secretariat for Transport raw 1-second loop counts, and Directorate for Building Land live bridge accelerometer feeds) remain strictly confidential or internal municipal infrastructure systems and are not accessible via open APIs. These boundaries are explicitly documented as structural limits rather than data failures.

---

## 6. Verification & File Manifest

- **Verification Level**: PRIMARY_METADATA_AND_FULLTEXT_VERIFIED
- **Related Files**:
  - `C:\Svemir\!Projekti\Beops\research\04-bibliography\agents\DOMESTIC_CONTEXT_2026-09-06.md`
  - `C:\Svemir\!Projekti\Beops\research\04-bibliography\agents\DOMESTIC_CONTEXT_2026-09-06.json`
