Status: current
Date: 2026-09-26
Autori: doc. dr Semir Poturak (ideja, smer) · Svemir (razrada, plan) — contributor, not author

# Interaktivna mapa Beops-a — plan pre ijedne linije koda

Teoretski i računski plan. Ništa ovde nije izgrađeno; svaka tvrdnja o postojećem pokazuje na fajl.

## 1. Rečenica artefakta

**Interaktivna mapa Beograda koja crta isključivo ono što fajlovi sa provenijencijom sadrže —
sloj po sloj, sa izvorom, licencom i stanjem na licu — i na klik otvara dosije entiteta,
uključujući retro-pasoš materijala tamo gde postoji.**

Šta NEĆE biti na ekranu:
- tuđi tile serveri, Leaflet/MapLibre, bilo koja zavisnost (pravilo: plain browser JS);
- ulice, osobe, kamere (isto pravilo koje već važi za statične mape, `tools/make_maps.py`);
- opštinske granice — svi putevi do njih odbijeni i zabeleženi (S193 401, S194 robots, S126 403,
  S142 robots, S127 robots); mapa to kaže na licu umesto da krije;
- izmišljena geometrija, ocena "kružnosti", bilo koji broj bez izvora;
- šesto stanje. Pet stanja (observed / untimed / estimated / forecast / unavailable) važi i na mapi:
  `unavailable` se renderuje kao samo sebe.

## 2. Pozicioniranje — odgovor na pitanje "niša projekat, nadogradnja ili filter lejer"

**Ni jedno ni drugo ni treće: mapa je ČETVRTI OKVIR Beops-a.** Beops već ima tri okvira
(`research/05-design/studies/`: monolog-puls, podaci, traka-live) — vremenski, tabelarni i tok.
Mapa je prostorni okvir: ista disciplina, isti izvori, nova osa (prostor umesto vremena).
Uz okvir ide jedna nadogradnja infrastrukture: **registar mapovih slojeva** (proširenje ideje
`research/STATIC_LAYERS.json` na sve što mapa sme da crta).

Podela rada sa MaterialPassport-om je čista i ostaje:
- **MaterialPassport** (`!Projekti/MaterialPassport`) proizvodi podatke — retro-pasoš zapise po šemi
  iz `research/RETRO_FORENZIKA_okvir.md` §5 (JSONL, probabilistički, ocene A–D, `podigao_bi`).
- **Beops** prikazuje i čuva disciplinu — sloj "materija" je za mapu samo još jedan registrovan
  sloj sa sid-om, capture-om i licencom, kao Kontur populacija danas.
Beops ne postaje pasoš-projekat; MaterialPassport ne gradi svoj viewer.

## 3. Šta već postoji (inventar, provereno u fajlovima 2026-09-26)

| deo | fajl | stanje |
|---|---|---|
| Basemap sa provenijencijom | `public/basemap-belgrade.json` (Natural Earth 1:10m, S98, public domain, sha256 u registru) | živ |
| Projekcija WGS84→px | `proj()` u `tools/make_maps.py` (cos-korigovana ekvirektangularna, prozor 20.17–20.80 / 44.55–44.98) | živa, treba port u JS |
| Registar slojeva | `research/STATIC_LAYERS.json` (2 sloja: basemap, kontur-populacija S120 H3 r8) | živ, uzor za registar mape |
| 4 statične mape | `docs/map-{instruments,coverage,last24h,people}.svg` + `MAPS.json` ("Nothing drawn that the two files do not contain") | žive — mapa nasleđuje ovo pravilo doslovno |
| Instrumenti | `public/live-snapshot.json` (116 tačaka sa koordinatama operatera) | živ |
| Događaji | `public/events.json` | živ; **ima li koordinate — neprovereno** |
| AI zapažanja | `research/ORGANS.json`, `research/AI_FEED.json` | živi; bez prostornog sidra danas |
| Sadržaj za sloj materije | elaborat Centralne zone NBG — 102 objekta sa izvođačima i sistemima (javan; GRANA13) | pročitan u istraživanju, još nije registrovan kao S-izvor |

Zaključak inventara: **interaktivnost je jedino što fali.** Podaci, disciplina i projekcija već stoje.

## 4. Arhitektura

- `public/mapa.html` + `public/mapa.js` — vanilla JS, Canvas 2D, nula zavisnosti, radi sa GitHub
  Pages jer čita samo sopstvene JSON fajlove (nema mrežnih poziva ka trećima u runtime-u).
- Projekcija: `proj()` portovana 1:1 iz `make_maps.py`; pan/zoom = jedna afina transformacija
  preko nje (scale + translate), ništa više.
- **`research/MAP_LAYERS.json`** — registar: za svaki sloj `id`, `file`, `sid`, `licence`,
  `must_be_named`, `states_it_may_carry`, `geometry` (point | line | polygon | h3-point),
  `dossier_fields`. Contract test: mapa ne sme da crta fajl koga nema u registru
  (isti duh kao `city_view_contract.test.cjs`).
- Interakcije, redom vrednosti: (1) toggle slojeva, (2) klik → dosije panel (hit-test nad
  projektovanim tačkama/poligonima), (3) pan/zoom, (4) kasnije vremenski klizač nad
  `history-*.json`. Bez ijedne animacije koja sugeriše podatak koji ne postoji.
- Dosije panel: za instrument — sid, poslednja recepcija, stanje; za objekat — retro-pasoš polja
  sa ocenom i `podigao_bi`; svaka rečenica izvedena modelom nosi oznaku (pravilo 7).

## 5. Sloj "materija" — retro-forenzika na mapi

- Ulaz: `retro-pasos.jsonl` koji proizvodi MaterialPassport (pilot: Centralna zona NBG).
- Mapiranje ocena A–D na pet stanja Beops-a — ovo je teorijski šav dva projekta:
  **A** (dokument o samom objektu) → `observed` · **B/C** (dedukcija tipologija→sistem→fabrika,
  JUS godine gradnje) → `estimated` sa imenovanom metodom · **D/prazno** → `unavailable`.
  Vremena: izmereno = datum izvora o objektu; objavljeno = datum elaborata/biltena; primljeno = upis.
- Geometrija: footprint-i objekata nemaju čist izvor (katastar/geoSrbija uslovi neprovereni) —
  v0 je **tačka-centroida po objektu**, ručno očitana iz javnog elaborata, sa izvorom po tački.
  Poligon tek kad postoji dozvoljen izvor; do tada mapa pošteno crta tačke.
- Prvi vidljivi rezultat: 102 objekta Centralne zone kao tačke sa dosijeom izvođač + sistem +
  JUS-ovi godine gradnje — **prvi retro-pasoš na ekranu, sa rupama iskreno označenim.**

## 6. Digitalni kontekst za zapažanja superinteligencije

Nadogradnja u dva smera, oba mala:
1. **Zapis dobija sidro**: polje `geo` u AI_FEED zapažanju — `{lat, lon}` ili `{layer, id}`
   (npr. objekat iz sloja materije). Organ koji ne može da sidri ne sidri — polje je opciono,
   nikad izmišljeno.
2. **Organ dobija isečak**: ulaz organu može biti sloj-isečak (objekti u prozoru + njihova
   dosije polja) — mapa tako postaje kontekst iz koga model izvodi zapažanje, a zapažanje se
   vraća na mapu označeno kao model-derived. Krug je zatvoren i svaki luk je proverljiv.

## 7. Etape (svaka sa izlazom i testom na artefaktu)

- **E1 — viewer**: `mapa.html` sa 3 postojeća sloja (basemap, instrumenti, populacija). Nijedan
  nov podatak. Test golog ekrana pre predaje; contract test da su svi crtani fajlovi u registru.
- **E2 — registar + dosije**: `MAP_LAYERS.json` + klik → dosije za instrumente. Test: dosije
  prikazuje samo polja iz registra.
- **E3 — materija v0**: registracija elaborata kao S-izvora (capture, licenca — proveriti pre
  upotrebe!), `retro-pasos.jsonl` za Centralnu zonu u MaterialPassport-u, sloj na mapi. Test:
  svako polje nosi ocenu i izvor; nijedna tačka bez izvora.
- **E4 — sidro**: `geo` u AI_FEED šemi + prikaz model-derived zapažanja. Test: zapažanje bez
  sidra se ne crta; zapažanje sa sidrom nosi oznaku modela.

E1 je dah-dva posla i ne traži nijednu odluku; E3 traži proveru licence elaborata; E4 dira
AI_FEED šemu pa ide na grani sa testovima pre i posle.

## 8. Otvoreno / rizici

- `events.json` — koordinate neprovereno; ako ih nema, događaji ostaju van mape do izvora.
- Licenca/uslovi elaborata Centralne zone i geoSrbija WMS — neprovereni; E3 čeka na to.
- Performanse: 2452 H3 tačke + 116 instrumenata + 102 objekta na Canvas-u — trivijalno; nema rizika.
- Opštinske granice ostaju odsutne dok neki put ne bude dozvoljen; mapa nosi tu rečenicu vidljivo.

## 9. Honest verdict

Provereno: postojanje i sadržaj basemap-a, STATIC_LAYERS, MAPS.json, make_maps.py projekcije,
live-snapshot broja instrumenata — čitano iz fajlova danas. Zaključeno (ne provereno): da je
Canvas bez zavisnosti dovoljan za ove količine — izvesno po veličini ulaza, ali nemereno; da
mapiranje A–D→pet stanja drži vodu — teorijska tvrdnja, pada ili stoji na E3. Nije gledano:
events.json sadržaj, uslovi geoSrbija/elaborata, AI_FEED šema u detalje (E4 je zato na grani).
Ništa iz ovog plana nije izgrađeno.
