# BEOPS v1 — the layer that depends on nobody

Status: current
Date: 2026-09-05
Author: claude-cowork

**The rule this document obeys:** version 1 asks no one for anything. No letters, no purchases, no
approval workflows, no waiting. Only what is openly licensed and reachable today. A free,
instant, self-service key — type an email, receive a token — is acceptable and is listed separately
so the distinction stays honest. A key that a human must approve is disqualifying and is named as
such.

The finding this document exists to record: **that space is much larger than it looked**, because
Belgrade sits inside European and global scientific systems that publish openly whether or not
Serbia's own institutions do.

Legal basis for each item is in [`../07-legal/COLLECTION_LEGAL_FRAME.md`](../07-legal/COLLECTION_LEGAL_FRAME.md).

---

## 1. Needs nothing at all — no key, no account, no email

| Source | What it tells us about Belgrade | Cadence / resolution | Licence |
|---|---|---|---|
| **ECMWF Open Data** | A second, independent global forecast model over the city — not Open-Meteo's stack | 4 runs/day (00/06/12/18 UTC), 0.25°, out to 15 days; reference time and valid time are separate fields | **CC-BY-4.0**, zero authentication. Rolling ~2–3 day archive only |
| **EMSC-CSEM** | Independent pan-Euro-Mediterranean earthquake catalogue including Serbia — a cross-check on the national table we already hold | Real-time; origin time and `lastupdate` are distinct fields — a direct match to our own time rule | FDSN-WS + GeoJSON/RSS at seismicportal.eu, **no key** |
| **NASA POWER** | Independent global solar and meteorological record over Belgrade back to the 1980s | ~0.5° grid, daily/hourly | Public-domain-style, direct REST, no key |
| **FDSN network SJ metadata + availability** (GEOFON) | The Serbian seismic network's own station inventory and what is actually archived | Queryable now | `restrictedStatus="open"`, DOI 10.7914/SN/SJ. **See §4 — declared open, archive stale** |
| **CORINE Land Cover, CLMS Imperviousness, Tree Cover Density** | Belgrade's land cover, sealed surface and tree canopy, measured the same way as the rest of Europe | 100 m / 25 ha MMU; imperviousness and canopy at 10 m and 100 m; epochs 1990–2018 | Copernicus free and open, direct download |
| **JRC Global Surface Water** | Historical water extent of the Danube and Sava at Belgrade — the floodplain baseline. The FAQ names them explicitly | 30 m, 1984 onward | *"full and open access conforming to the Copernicus Regulation"* |
| **JRC GHSL** — built-up surface, population grid, urban centre database | How Belgrade's built footprint and population grid changed across decades, globally comparable | 10 m built-up from Sentinel-2; 100 m / 1 km population; epochs 1975 → 2030 | CC-BY-4.0, direct download or Earth Engine |
| **Overture Maps** | Belgrade buildings, places, transport, divisions — OSM-first, so quality tracks the OSM changeset feed we already hold | Monthly releases (latest seen `2026-08-19.0`) | **ODbL**, direct S3/Azure parquet, zero login |
| **Microsoft Global ML Building Footprints** | ML-derived building polygons with height estimates, as a cross-check against OSM | Static releases | **CDLA Permissive 2.0**. Serbia's presence in the index not yet confirmed |
| **OpenInfraMap** | Belgrade's power grid and substations, exactly as complete as OSM's power tagging | Live, OSM cadence | ODbL, viewer + Overpass |
| **Natural Earth** | Reference boundaries and the Belgrade point for basemaps | Static | **Public domain** — the cleanest licence on this list |
| **GADM** | Administrative boundaries down to municipality | Static | *"freely available for academic use and other non-commercial use"* — **redistribution and commercial use need permission**, softer than the rest; keep it out of anything republished |
| **Global Power Plant Database** | Serbian and Belgrade-area generating capacity by fuel — TENT, Kolubara | Static compilation, 2013–2017 generation vintage. **Not a live feed** | CC-BY-4.0 |
| **Eurostat / World Bank / OECD / UNECE REST APIs** | Serbia-level series; Belgrade-level only via Urban Audit, still unresolved | Annual | Open, keyless |

## 2. Needs one instant, self-service key

Listed separately because the distinction matters: these are still v1-eligible, but they are not
zero-friction, and each should be recorded in the registry with that fact.

| Source | What it adds | Key |
|---|---|---|
| **CAMS European air-quality regional ensemble** | An independent atmospheric model over Belgrade, checkable against SEPA's own stations. **Domain confirmed as 25°W–45°E, 30°N–72°N — Serbia is well inside it, not at an edge.** 10 km, hourly steps, 4-day forecast | Free Copernicus/ECMWF account, `cdsapi`. Licence: **CC-BY** |
| **C3S ERA5** | The actual weather over Belgrade for any hour **back to 1940** — the baseline every derived sense needs. Hourly, 0.25°, *"updated daily with a latency of about 5 days"*; preliminary ERA5T versus final ERA5 is itself a textbook measured-versus-published pair | Same account |
| **Sentinel-1 and Sentinel-5P** | Radar (6–12 day repeat, 5–20 m) and atmospheric columns (daily, 5.6×3.6 km) | Copernicus Data Space Ecosystem, free instant account |
| **NASA FIRMS** | Active fire in Belgrade's peri-urban fringe, VIIRS 375 m near-real-time | MAP_KEY emailed instantly, 5 000 calls / 10 min |
| **GPM IMERG** | Independent precipitation at **~4 km, half-hourly**, with a **three-tier latency published as such**: Early 4 h, Late 12–14 h, Final ~3.5 months — a richer version of our own provisional/reviewed pattern | Free NASA Earthdata login |
| **NOAA GHCN-Daily** | A second long-run station record for Belgrade (Surčin, WMO 13274) | Token by email |
| **OpenAQ** | *Would* be SEPA's own measurements through a clean API — **but v3 returned 401 to an unauthenticated call when tested here, and whether Serbia is ingested at all is unconfirmed.** Do not assume | Key self-service at explore.openaq.org |

## 3. The instrument near the city nobody had counted

**Grocka (IAGA code GCK)**, roughly 30 km from central Belgrade, is a **geomagnetic observatory**,
and it is listed on the INTERMAGNET GIN data service at the British Geological Survey alongside LON
(Croatia), SUA (Romania) and KIV/LVV (Ukraine). **No login is needed to download.** The licence, as
quoted from the service: *"supplied on the condition that they are not used for commercial gain."*

This is a genuinely new class of sense for the project — a real physical instrument near Belgrade,
publishing openly, measuring the geomagnetic field and therefore the city's exposure to space
weather and geomagnetic storms. Which tier GCK itself delivers (real-time, quasi-definitive,
definitive) and which institute operates it were not confirmed in this pass and are the first things
to check.

## 4. The seismic picture, queried directly rather than taken on report

A radius query against GEOFON returned **eight Serbian stations within two degrees of Belgrade**:

| Station | Site | Lat / Lon | Since |
|---|---|---|---|
| **BEO** | Station Beograd | 44.8093 / 20.4714 | 2005 (instrument since 1918) |
| **AVAS** | Avala | 44.6960 / 20.5132 | 2004 |
| **FRGS** | Fruška Gora | 45.1573 / 19.8098 | 2010 |
| **TEKS** | Tekeriš | 44.5493 / 19.5281 | 2004 |
| **SVIS** | Svilajnac | 44.2655 / 21.2152 | 2004 |
| **GRUS** | Gruža | 43.8888 / 20.7151 | 2005 |
| **DJES** | Đerdap–Kladovo | 44.6672 / 22.5197 | 2005 |
| **BORS** | Borsko jezero | 44.0904 / 22.0177 | 2004 |

Plus one Hungarian station, **AMBH** (Ambrózfalva), to the north.

**The network is dense and declared open. The archive is not there.** The availability extent for
AVAS shows 100 Hz data ending **2026-01-28** in sixteen fragments, and six days at the end of
January for the short-period channels. **BEO returns no availability rows at all.** `dataselect`
answers 204 No Content even inside a declared window, and the whole-network availability query times
out.

So the honest v1 position on seismic is: **the metadata is a usable sense today** — station
inventory, network geometry, the fact of openness with a citable DOI — and **the waveforms are not**.
That is recorded as a `lead`, not a source, and v1 does not lean on it.

## 5. Confirmed absent — so nobody looks again

- **Google Open Buildings**: a clean negative of a different shape — it was never aimed at Europe.
  Confirmed scope is Africa, South Asia, South-East Asia, Latin America and the Caribbean.
- **CLMS "Urban Heat Island"**: does not appear to exist as a product. Probably conflated with land
  surface temperature layers.
- **Urban Atlas, EEA NOISE**: already confirmed twice — EEA38 only, Serbia outside.
- **EEA Air Quality e-Reporting**: very likely the third instance of the same cutoff, since it rests
  on an EU directive transposition obligation Serbia does not carry. Not re-verified this pass.
- **IGS / EUREF-EPN / E-GVAP**: nearest EUREF station is Šabac, ~70 km out, not confirmed feeding any
  operational product, and Serbia is not named even as a future candidate in the dedicated
  South-East Europe reprocessing project.

**Still unresolved, and worth exactly one more query each:** whether **EGMS** — millimetre-accuracy
InSAR ground motion, annually updated — covers Serbia. Its own page says only *"over the Copernicus
participating countries"* and every attempt to reach the coverage viewer failed. If it does cover
Serbia, it is millimetre-scale subsidence of Belgrade for free, and it would be the single largest
addition on this page. Also unresolved: Eurostat Urban Audit for Belgrade (check city code `RS001` in
the `urb_*` family), whether OpenAQ ingests Serbia, and the exact Belgrade monitoring points of ICPDR
and the Sava Commission.

## 6. The ten to build v1 on

1. **CAMS European ensemble** — an independent model of Belgrade's air, checkable against SEPA.
2. **ERA5** — the weather baseline, hourly, back to 1940, that every other sense needs behind it.
3. **ECMWF Open Data** — a second forecast, four times a day, with no authentication whatsoever.
4. **EMSC-CSEM** — an independent seismic catalogue with separate origin and update times.
5. **INTERMAGNET / Grocka** — a real instrument 30 km away, open, and a new sense class.
6. **GPM IMERG** — precipitation at 4 km and half-hourly, with its latency tiers published.
7. **Sentinel-1 and Sentinel-5P** — radar and atmospheric columns.
8. **CORINE + Imperviousness + Tree Cover Density** — the sealed-surface and canopy baseline.
9. **JRC GHSL + Global Surface Water** — built footprint and floodplain, globally comparable.
10. **Overture + Microsoft footprints + OpenInfraMap** — the built object layer, ODbL and CDLA.

**None of these asks anyone for permission.** Seven need no key at all; the rest need a token that
arrives by return email. Together they give Belgrade weather, air, precipitation, radiation,
seismicity, geomagnetism, land cover, built form, water extent and infrastructure — before a single
Serbian institution has been contacted.

## What v1 therefore is

An observatory of Belgrade assembled entirely from open European and global scientific
infrastructure, plus the Serbian sources that are already public without conditions — SEPA's and the
city institute's air readings, RHMZ's radar and water levels, the seismic event table,
Elektrodistribucija's outage schedule, the news and notice feeds that permit it, and the official
gazette, which under Copyright Act Art. 6(2) is not a copyright work at all.

The things that need someone's permission — the ten traffic counters, the transit AVL feed, the
utility lab results, the RATEL register, AGROS, the seismic waveform archive, the cameras — are
recorded, named, and **left out of v1 entirely**. They are what v2 asks for, from a position of
having already built something.

## Honest verdict

Done: an inventory of openly licensed international infrastructure covering Belgrade, split by
whether it needs a key; a geomagnetic observatory 30 km from the city found and its licence quoted; a
seismic radius query run directly, returning eight Serbian stations with coordinates; the seismic
availability checked and found stale; five confirmed absences recorded with their shape.

Not done, and not claimed: nothing was registered for, no key obtained, no data downloaded beyond
metadata and availability queries. Coverage of Serbia by EGMS is **unresolved**, not negative.
Eurostat Urban Audit for Belgrade is unresolved. Whether OpenAQ ingests Serbia is unresolved and the
unauthenticated call returned 401. Several items in §1 carry licence text taken from documentation
rather than re-quoted from the page this pass, and are marked in the registry accordingly. The web
search budget for this session was exhausted, so the last checks ran on direct fetches only.
