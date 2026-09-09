# The open state layer — what Serbia already publishes, and had published all along

*2026-09-06. Sources S146–S156. Permission for each is captured in
`research/08-provenance/`; nothing here was collected before that capture
except where E-009 and CORRECTIONS C-003 say otherwise.*

---

## What was searched, and the correction it forced

The project had been hunting sources one site at a time. It had never opened
the front door: **`data.gov.rs`, the national open data portal, has an API,
3 530 datasets, 232 organisations and 7 064 resources — and no `robots.txt`.**
BEOPS had taken exactly one dataset from it.

All 3 530 were harvested on 2026-09-06 (36 pages, stored at
`research/_scratch/datagovrs/`). The portal is not what its size suggests, and
that has to be said before anything else:

| | |
|---|---:|
| datasets from **one** publisher (Zavod za javno zdravlje Šabac) | **1 633 (46 %)** |
| retail price lists mandated by the consumer-protection act | 113 |
| RZS, the statistical office | 728 (+306 SDG) |
| everything else | ≈ 750 |

Its own `frequency` field is the useful part, because the portal states each
dataset's cadence: 1 695 punctual · 747 annual · 296 irregular · 107 monthly ·
90 continuous · 36 daily · 5 weekly. Licence is `sodl` — the Serbian Open Data
Licence — on 3 528 of 3 530.

Only 40 datasets mention Belgrade by name. That number is misleading: the
municipality-level series from RZS cover the city without ever saying so.

---

## S146 — the model source, and it is Serbian

`opendata.kosava.cloud` — the Environmental Protection Agency's air quality
API. `GET /api/v1/metadata` answers:

```json
"snapshot_id":            "20260906020624",
"generated_at_utc":       "2026-09-06T03:00:15Z",
"data_status":            "preliminary",
"aggregation_type":       "hourly_mean",
"averaging_period":       "1h",
"retention_days":         30,
"counts": { "networks": 8, "stations": 87,
            "components": 15, "measurement_rows": 16055 },
"applicable_legislation": "http://data.europa.eu/eli/reg_impl/2023/138/oj",
"license": { "name": "Otvoreni podaci po Zakonu o e-upravi (CC BY-equivalent)" }
```

Read that against everything else in this project. This source states, as
fields, in every response: **when the snapshot was made**, that the data are
**preliminary**, **how they were aggregated and over what period**, **how long
it remembers**, and **its own legal basis as an ELI URI** — Regulation (EU)
2023/138 on high-value datasets, which is what obliges it to be free,
machine-readable and API-served under an open licence.

It is the first source in the registry that hands us the legal basis instead of
making us reconstruct it, and the first that publishes its epistemic status as
data rather than as a footnote. Everything the five-state grammar has been
arguing for, a Serbian agency shipped in May 2026.

Components: `/stations` `/parameters` `/observations` `/bulk` `/dcat`
`/data-dictionary` `/metadata`, with OpenAPI, Swagger, ReDoc and a DCAT-AP HVD
JSON-LD catalogue for harvesters.

**Belgrade: 32 active stations** inside the bbox (44.60–44.95, 20.20–20.65) —
28 named *Beograd*, plus Obrenovac Centar and three in Pančevo. Codes are EEA
AirBase format (`RS3030A`), so they join to European datasets.

```
RS1018A Stari grad          RS3020A Bulevar despota Stefana   RS3030A Ada Ciganlija
RS1023A Novi Beograd        RS3021A Dragiša Mišović           RS3034A Jajinci
RS1025A Mostar              RS3026A Bežanijska kosa           RS3036A Rakovica
RS1026A Vračar              RS3027A Banovo brdo               RS3037A Mirijevo
RS1027A Zeleno brdo         RS3029A Ada petlja                RS3039A Beograd na vodi
RS3010A Zemun Ugrinovačka   RS3011A Borča                     RS3019A Vinča
RS3013A Surčin              RS3012A Krnjača                   RS3041A Danijelova
RS3016A Zemun TB            RS3014A Franše d'Epere            RS3017A Stojčino brdo
RS3022A Omladinskih brigada RS3023A Topčiderska zvezda        RS3025A Vračar Dom zdravlja
RS3015A Leštane             RS1033A Obrenovac Centar          RS1014A/RS4013A/RS4015A Pančevo
```

Fifteen components: `SO2 PM10 PM2.5 O3 NO2 NOX NO CO NH3 Benzen Toluene
Ethyl benzene mp-Xylene o-Xylene TNx` — BTEX as well as particulates.

**Pair it with S06**, the verified daily archive, and the same measurement
exists in two declared states — *preliminary hourly* and *verified daily* —
from the same agency. That is the cleanest demonstration of the grammar the
project will ever get, and it needs no argument: both labels are the
publisher's.

**One defect, recorded so it does not bite later.** The `municipality` field
carries both `"Beograd"` (26 stations) and `"Beograd "` with a trailing space
(4). It will silently split a group-by. Normalise on read; never edit the
capture.

---

## The rest of the layer

| id | source | rhythm | what it is |
|---|---|---|---|
| **S147** | `data.gov.rs` udata API | continuous | the catalogue itself; re-harvest quarterly and **diff** — the diff measures what the state chooses to open |
| **S148** | RZS REST, `opendata.stat.gov.rs` | monthly → annual | 1 034 datasets behind one URL pattern with a code. `robots.txt`: `User-agent: * / Allow: /`. **The JSON endpoint returns a ZIP**, not bare JSON |
| **S149** | APR company register | monthly snapshot | every registered company in Serbia with `SifraOpstine`; the payload carries `DatumPreseka` (2026-08-31). 57.8 MB — a monthly job, never a poll |
| **S150** | RGZ Address Register via `download.geosrbija.rs` | stated weekly | house numbers and streets as **GeoPackage**, keyless. The spatial base this project has been missing |
| **S151** | Ministry of Mining, CISGIR ArcGIS | portal says continuous | open ArcGIS 10.8, `/query` works: **10 exploitation fields and 4 exploration fields intersect Belgrade** |
| **S152** | SEPA airborne pollen | weekly, 2016→ | air that has a **species**, not only a concentration. 32 MB combined, plus station locations and an allergen dictionary |
| **S153** | SEPA NRIZ emissions to air | annual, 2010–2024 | emission **sources** to pair with concentrations. Fifteen consecutive years |
| **S154** | Commissioner for Information of Public Importance | **daily**, 16 series | requests, complaints, appeals, lawsuits, opinions, the personal-data register. Measures **how much the state is asked and how often it refuses** |
| **S155** | RATEL | spectrum daily, speeds continuous | transmitters and measured internet speeds — an electromagnetic and a digital layer |
| **S156** | Public Procurement Office | daily, 2013→ | **what the city is about to build, before it is built**, with the contracting authority named. Endpoint is plain `http` |

Belgrade-relevant RZS series identified by code, so they can be fetched
directly: tourist overnight stays by municipality **monthly** (`220205IND02`);
registered employment by municipality **quarterly** (`24021308IND01`) and
annual (`24021105IND01`); average price of new-build flats sold **semiannual**
(`05010107IND02`); average gross wages **monthly** (`2403040111IND02`, and
`2403040110IND02` for the public sector).

Tourist overnight stays by municipality, monthly, is a visitor pulse for the
city that nobody had proposed and that has been published all along.

---

## Two senses nobody in this project had thought of

**Pollen.** Weekly, nine years deep, by station, with an allergen dictionary.
Every other air sense the project holds measures *how much*; this one measures
*what*. A city whose air has a species — birch in April, grass in June,
ragweed in August — is a different object from a city with a PM10 number.

**Being asked.** The Commissioner publishes, daily, how many requests for
access to information were filed, how many appeals, how many lawsuits against
the Commissioner. That is a measurement of the friction between a public and
its administration, refreshed every day, in CSV, under an open licence. For an
observatory that intends to describe a city honestly, an instrument pointed at
the act of asking is not a curiosity — it is the closest thing to a control.

---

## What is not established

- **S150 carries no snapshot date.** The address register changes
  continuously; the download states no reference moment. The portal says
  weekly, the portal entry was last modified 2024-04-15, and those two
  statements disagree. Do not assume weekly.
- **S149 and S156 have incomplete captures** — the 57.8 MB response and an
  unreadable `robots.txt` on plain http. They sit under *Evidence incomplete*
  in the index and nothing may be taken from them until that clears.
- **`opendata.geosrbija.rs` is behind a login**, and probing the download
  proxy with invented layer names returns `400` with no listing. The catalogue
  of categories and layers must be found, not guessed. Only `ar` /
  `kucni_broj_ar` / `ulica_ar` are known.
- **S152, S153, S155, S156 have not been parsed.** Their structure, their
  Belgrade coverage and their row grain are unverified. Nothing about them may
  be stated as a number until they are.

## Collection manners

Everything above was one request per endpoint, sequential, honest user-agent,
counts before geometry. The catalogue harvest was 36 paged requests at 700 ms
apart. None of these is a recurring collector, and none becomes one without
`08-provenance/EDGE_CASES.md` E-004.
