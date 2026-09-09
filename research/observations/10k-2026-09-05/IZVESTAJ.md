# OBS-001 izveštaj — 10K trka kroz prikaz parking mesta (05.09.2026)

Status: completed descriptive pilot; local research report, not publication clearance.
Author: Astra. Date: 2026-09-05 UTC.
Nastao 2026-09-05T22:38:18+00:00 UTC iz `observe_10k.py` receipt-a na disku. 
Ovo je opisna observacija prikazanih brojeva, ne dokaz o uzročnosti.

## Šta ovaj izveštaj ne tvrdi

- Raspoređeno vreme nije vreme merenja: izvor ne izlaže `observed_at`, pa svaka vrednost ostaje „prikazano u trenutku prijema".
- U sacuvanim dokazima nema potvrdenog ukupnog kapaciteta lokacija, pa nema procenta popunjenosti; neto promena ne meri dolaske, odlaske ni broj učesnika.
- Rupe u pokrivenosti se ne popunjavaju, ne interpoliraju i ne prebijaju nulama; stanje svakog termina dolazi sa diska (vidi tabelu pokrivenosti).
- Promene su moguće i zbog redovne subote, drugih događaja, kvara ili promene prikaza na izvoru; bez uporedivih subota se ne razdvajaju (vidi OPAZANJA.md).

## Vremenska linija najava (izvori, ne merenja)

- Organizator (bgdmarathon.org): program 15:00–21:00, najavljen start 18:00 lokalno.
- Sekretarijat za javni prevoz: segmentirane izmene linija tokom dana, ne jedan trenutak.
- Parking servis: javni prikaz slobodnih mesta po garazi/parkiralištu, jedan odgovor za svih 27 lokacija.
- Rani parking uzorak (05:23:21 lokalno) iz multidomain dokaza, izvan ritma slotova.

Zavrsna provera najava 05.09.2026 oko 22:35 UTC (06.09.00:35 lokalno): [organizator](https://bgdmarathon.org/10k-belgrade-run-nike-2026/) i [Sekretarijat](https://www.bgprevoz.rs/vesti/informacija-o-promeni-rezima-rada-linija-javnog-prevoza-tokom-odrzavanja-manifestacije-trka-10k-beograd-2026) ponovo otvoreni kroz web alat. Organizator i dalje prikazuje datum 05.09, program 15-21h i start 18h. Na ove dve strane nije nadjena nova oznaka otkazivanja; to nije nezavisna potvrda odrzavanja.
Najava prevoza razlikuje 04.09.08h-05.09.06h, zatim 05.09.06-16h, 16-21h i 21-24h za linije 15/84/704/706/707; za 9A/60 navodi 16-21h. Rani parking prijem je vec u periodu priprema. Ovo su najavljeni rezimi, ne GPS dokaz izvrsenja. Nije sacuvana cela tudja stranica za redistribuciju. Nisu dokazani svi ranije planirani medjuterminski pregledi najava; nema tvrdnje o potpunom nadzoru promena.

## Pokrivenost slotova (10 od 13)

| slot UTC | slot lokalno | stanje | dokaz |
|---|---|---|---|
| 10:30 | 12:30 | missing | termin prosao bez receipta; rupa, ne nula |
| 11:30 | 13:30 | missing | termin prosao bez receipta; rupa, ne nula |
| 12:30 | 14:30 | missing | termin prosao bez receipta; rupa, ne nula |
| 13:30 | 15:30 | captured | receipt na disku (sample-*.json) |
| 14:30 | 16:30 | captured | receipt na disku (sample-*.json) |
| 15:30 | 17:30 | captured | receipt na disku (sample-*.json) |
| 16:30 | 18:30 | captured | receipt na disku (sample-*.json) |
| 17:30 | 19:30 | captured | receipt na disku (sample-*.json) |
| 18:30 | 20:30 | captured | receipt na disku (sample-*.json) |
| 19:30 | 21:30 | captured | receipt na disku (sample-*.json) |
| 20:30 | 22:30 | captured | receipt na disku (sample-*.json) |
| 21:30 | 23:30 | captured | receipt na disku (sample-*.json) |
| 22:30 | 00:30 | captured | receipt na disku (sample-*.json) |

## Tabela promena (prikazane vrednosti po prijemu)

Prvi prijem 2026-09-05T13:30:03.5813264Z → poslednji prijem 2026-09-05T22:30:43.5627052Z. 
Razlika je razlika prikazanih vrednosti između dva trenutka prijema, ne merenja.

Isti skup od 27 lokacija: zbir prikazanih slobodnih mesta 3679 -> 4598 (razlika +919). Ovo nije promena za ceo Beograd.

### Novobeogradsko/zemunsko okruzenje trke

| lokacija | prvi prijem | poslednji prijem | razlika prikaza |
|---|---|---|---|
| Garaža "Pinki " | 93 | 102 | 9 |
| Parkiralište "Belvil" | 397 | 404 | 7 |
| Parkiralište "Opština NBGD" | 114 | 119 | 5 |

Zbir promena ovih 3 lokacija: +21; samo opis, bez kontrolnog ili uzrocnog tumacenja.

### Centralno/obalno okruzenje

| lokacija | prvi prijem | poslednji prijem | razlika prikaza |
|---|---|---|---|
| Parkiralište "Kalemegdan" | 0 | 56 | 56 |
| Garaža "Zeleni venac" | 89 | 130 | 41 |
| Parkiralište "Donji grad" | 254 | 45 | -209 |

Zbir promena ovih 3 lokacija: -112; samo opis, bez kontrolnog ili uzrocnog tumacenja.

### Prostorno udaljeniji opisni kontekst

| lokacija | prvi prijem | poslednji prijem | razlika prikaza |
|---|---|---|---|
| Parkiralište "VMA" | 518 | 565 | 47 |
| Parkiralište "Cvetkova pijaca" | 35 | 41 | 6 |
| Parkiralište "Bežanijska kosa" | 70 | 62 | -8 |

Zbir promena ovih 3 lokacija: +45; samo opis, bez kontrolnog ili uzrocnog tumacenja.

### Ostale lokacije (prilog, ne centar price)

| lokacija | prvi prijem | poslednji prijem | razlika prikaza |
|---|---|---|---|
| Parkiralište "Ada" | 440 | 954 | 514 |
| Parkiralište "Milan Gale Muškatirović" | 60 | 242 | 182 |
| Garaža "Obilićev venac" | 29 | 133 | 104 |
| Garaža "Pionirski park" | 275 | 343 | 68 |
| Garaža "Masarikova" | 346 | 387 | 41 |
| Garaža "Vukov spomenik" | 26 | 48 | 22 |
| Parkiralište "Viška" | 16 | 31 | 15 |
| Parkiralište "Politika" | 2 | 9 | 7 |
| Parkiralište "Ljermontova " | 62 | 68 | 6 |
| Garaža "Baba Višnjina" | 233 | 238 | 5 |
| Parkiralište "Slavija" | 82 | 86 | 4 |
| Garaža "Botanička bašta" | 74 | 77 | 3 |
| Parkiralište "Blok 43" | 144 | 147 | 3 |
| Parkiralište "Međunarodni carinski terminal" | 222 | 225 | 3 |
| Parkiralište "Kamenička" | 0 | 0 | 0 |
| Parkiralište "Čukarica" | 58 | 58 | 0 |
| Parkiralište "Vidin kapija " | 3 | 0 | -3 |
| Garaža "Dr Aleksandra Kostića" | 37 | 28 | -9 |

Zbir promena ovih 18 lokacija: +965; samo opis, bez kontrolnog ili uzrocnog tumacenja.


## Sve primljene vrednosti po uzorku (prilog)

### Prijem 2026-09-05T13:30:03.5813264Z (slot 13:30 UTC, HTTP 200)

| lokacija | prikazano slobodnih |
|---|---|
| Garaža "Baba Višnjina" | 233 |
| Garaža "Botanička bašta" | 74 |
| Garaža "Dr Aleksandra Kostića" | 37 |
| Garaža "Masarikova" | 346 |
| Garaža "Obilićev venac" | 29 |
| Garaža "Pinki " | 93 |
| Garaža "Pionirski park" | 275 |
| Garaža "Vukov spomenik" | 26 |
| Garaža "Zeleni venac" | 89 |
| Parkiralište "Ada" | 440 |
| Parkiralište "Belvil" | 397 |
| Parkiralište "Bežanijska kosa" | 70 |
| Parkiralište "Blok 43" | 144 |
| Parkiralište "Čukarica" | 58 |
| Parkiralište "Cvetkova pijaca" | 35 |
| Parkiralište "Donji grad" | 254 |
| Parkiralište "Kalemegdan" | 0 |
| Parkiralište "Kamenička" | 0 |
| Parkiralište "Ljermontova " | 62 |
| Parkiralište "Međunarodni carinski terminal" | 222 |
| Parkiralište "Milan Gale Muškatirović" | 60 |
| Parkiralište "Opština NBGD" | 114 |
| Parkiralište "Politika" | 2 |
| Parkiralište "Slavija" | 82 |
| Parkiralište "Vidin kapija " | 3 |
| Parkiralište "Viška" | 16 |
| Parkiralište "VMA" | 518 |

### Prijem 2026-09-05T14:30:02.7606066Z (slot 14:30 UTC, HTTP 200)

| lokacija | prikazano slobodnih |
|---|---|
| Garaža "Baba Višnjina" | 245 |
| Garaža "Botanička bašta" | 73 |
| Garaža "Dr Aleksandra Kostića" | 39 |
| Garaža "Masarikova" | 361 |
| Garaža "Obilićev venac" | 41 |
| Garaža "Pinki " | 95 |
| Garaža "Pionirski park" | 315 |
| Garaža "Vukov spomenik" | 47 |
| Garaža "Zeleni venac" | 104 |
| Parkiralište "Ada" | 443 |
| Parkiralište "Belvil" | 398 |
| Parkiralište "Bežanijska kosa" | 70 |
| Parkiralište "Blok 43" | 146 |
| Parkiralište "Čukarica" | 57 |
| Parkiralište "Cvetkova pijaca" | 35 |
| Parkiralište "Donji grad" | 254 |
| Parkiralište "Kalemegdan" | 0 |
| Parkiralište "Kamenička" | 0 |
| Parkiralište "Ljermontova " | 63 |
| Parkiralište "Međunarodni carinski terminal" | 220 |
| Parkiralište "Milan Gale Muškatirović" | 73 |
| Parkiralište "Opština NBGD" | 117 |
| Parkiralište "Politika" | 2 |
| Parkiralište "Slavija" | 80 |
| Parkiralište "Vidin kapija " | 8 |
| Parkiralište "Viška" | 29 |
| Parkiralište "VMA" | 338 |

### Prijem 2026-09-05T15:30:01.4755409Z (slot 15:30 UTC, HTTP 200)

| lokacija | prikazano slobodnih |
|---|---|
| Garaža "Baba Višnjina" | 246 |
| Garaža "Botanička bašta" | 63 |
| Garaža "Dr Aleksandra Kostića" | 38 |
| Garaža "Masarikova" | 371 |
| Garaža "Obilićev venac" | 31 |
| Garaža "Pinki " | 102 |
| Garaža "Pionirski park" | 328 |
| Garaža "Vukov spomenik" | 51 |
| Garaža "Zeleni venac" | 119 |
| Parkiralište "Ada" | 430 |
| Parkiralište "Belvil" | 400 |
| Parkiralište "Bežanijska kosa" | 69 |
| Parkiralište "Blok 43" | 146 |
| Parkiralište "Čukarica" | 60 |
| Parkiralište "Cvetkova pijaca" | 34 |
| Parkiralište "Donji grad" | 210 |
| Parkiralište "Kalemegdan" | 1 |
| Parkiralište "Kamenička" | 0 |
| Parkiralište "Ljermontova " | 63 |
| Parkiralište "Međunarodni carinski terminal" | 222 |
| Parkiralište "Milan Gale Muškatirović" | 102 |
| Parkiralište "Opština NBGD" | 115 |
| Parkiralište "Politika" | 0 |
| Parkiralište "Slavija" | 76 |
| Parkiralište "Vidin kapija " | 1 |
| Parkiralište "Viška" | 38 |
| Parkiralište "VMA" | 505 |

### Prijem 2026-09-05T16:30:01.8010755Z (slot 16:30 UTC, HTTP 200)

| lokacija | prikazano slobodnih |
|---|---|
| Garaža "Baba Višnjina" | 250 |
| Garaža "Botanička bašta" | 52 |
| Garaža "Dr Aleksandra Kostića" | 36 |
| Garaža "Masarikova" | 372 |
| Garaža "Obilićev venac" | 6 |
| Garaža "Pinki " | 105 |
| Garaža "Pionirski park" | 332 |
| Garaža "Vukov spomenik" | 48 |
| Garaža "Zeleni venac" | 110 |
| Parkiralište "Ada" | 484 |
| Parkiralište "Belvil" | 398 |
| Parkiralište "Bežanijska kosa" | 67 |
| Parkiralište "Blok 43" | 145 |
| Parkiralište "Čukarica" | 62 |
| Parkiralište "Cvetkova pijaca" | 38 |
| Parkiralište "Donji grad" | 173 |
| Parkiralište "Kalemegdan" | 0 |
| Parkiralište "Kamenička" | 0 |
| Parkiralište "Ljermontova " | 66 |
| Parkiralište "Međunarodni carinski terminal" | 224 |
| Parkiralište "Milan Gale Muškatirović" | 146 |
| Parkiralište "Opština NBGD" | 115 |
| Parkiralište "Politika" | 1 |
| Parkiralište "Slavija" | 70 |
| Parkiralište "Vidin kapija " | 0 |
| Parkiralište "Viška" | 35 |
| Parkiralište "VMA" | 558 |

### Prijem 2026-09-05T17:30:03.3752424Z (slot 17:30 UTC, HTTP 200)

| lokacija | prikazano slobodnih |
|---|---|
| Garaža "Baba Višnjina" | 242 |
| Garaža "Botanička bašta" | 29 |
| Garaža "Dr Aleksandra Kostića" | 34 |
| Garaža "Masarikova" | 375 |
| Garaža "Obilićev venac" | 0 |
| Garaža "Pinki " | 101 |
| Garaža "Pionirski park" | 336 |
| Garaža "Vukov spomenik" | 47 |
| Garaža "Zeleni venac" | 91 |
| Parkiralište "Ada" | 568 |
| Parkiralište "Belvil" | 392 |
| Parkiralište "Bežanijska kosa" | 65 |
| Parkiralište "Blok 43" | 148 |
| Parkiralište "Čukarica" | 59 |
| Parkiralište "Cvetkova pijaca" | 48 |
| Parkiralište "Donji grad" | 154 |
| Parkiralište "Kalemegdan" | 0 |
| Parkiralište "Kamenička" | 0 |
| Parkiralište "Ljermontova " | 67 |
| Parkiralište "Međunarodni carinski terminal" | 223 |
| Parkiralište "Milan Gale Muškatirović" | 164 |
| Parkiralište "Opština NBGD" | 115 |
| Parkiralište "Politika" | 1 |
| Parkiralište "Slavija" | 74 |
| Parkiralište "Vidin kapija " | 4 |
| Parkiralište "Viška" | 34 |
| Parkiralište "VMA" | 560 |

### Prijem 2026-09-05T18:30:01.6539473Z (slot 18:30 UTC, HTTP 200)

| lokacija | prikazano slobodnih |
|---|---|
| Garaža "Baba Višnjina" | 235 |
| Garaža "Botanička bašta" | 22 |
| Garaža "Dr Aleksandra Kostića" | 32 |
| Garaža "Masarikova" | 380 |
| Garaža "Obilićev venac" | 0 |
| Garaža "Pinki " | 104 |
| Garaža "Pionirski park" | 328 |
| Garaža "Vukov spomenik" | 39 |
| Garaža "Zeleni venac" | 39 |
| Parkiralište "Ada" | 742 |
| Parkiralište "Belvil" | 396 |
| Parkiralište "Bežanijska kosa" | 66 |
| Parkiralište "Blok 43" | 148 |
| Parkiralište "Čukarica" | 55 |
| Parkiralište "Cvetkova pijaca" | 47 |
| Parkiralište "Donji grad" | 141 |
| Parkiralište "Kalemegdan" | 15 |
| Parkiralište "Kamenička" | 0 |
| Parkiralište "Ljermontova " | 67 |
| Parkiralište "Međunarodni carinski terminal" | 225 |
| Parkiralište "Milan Gale Muškatirović" | 186 |
| Parkiralište "Opština NBGD" | 117 |
| Parkiralište "Politika" | 2 |
| Parkiralište "Slavija" | 67 |
| Parkiralište "Vidin kapija " | 28 |
| Parkiralište "Viška" | 21 |
| Parkiralište "VMA" | 562 |

### Prijem 2026-09-05T19:30:02.7933456Z (slot 19:30 UTC, HTTP 200)

| lokacija | prikazano slobodnih |
|---|---|
| Garaža "Baba Višnjina" | 228 |
| Garaža "Botanička bašta" | 22 |
| Garaža "Dr Aleksandra Kostića" | 32 |
| Garaža "Masarikova" | 384 |
| Garaža "Obilićev venac" | 0 |
| Garaža "Pinki " | 105 |
| Garaža "Pionirski park" | 310 |
| Garaža "Vukov spomenik" | 31 |
| Garaža "Zeleni venac" | 1 |
| Parkiralište "Ada" | 813 |
| Parkiralište "Belvil" | 399 |
| Parkiralište "Bežanijska kosa" | 65 |
| Parkiralište "Blok 43" | 148 |
| Parkiralište "Čukarica" | 58 |
| Parkiralište "Cvetkova pijaca" | 41 |
| Parkiralište "Donji grad" | 82 |
| Parkiralište "Kalemegdan" | 20 |
| Parkiralište "Kamenička" | 0 |
| Parkiralište "Ljermontova " | 68 |
| Parkiralište "Međunarodni carinski terminal" | 224 |
| Parkiralište "Milan Gale Muškatirović" | 197 |
| Parkiralište "Opština NBGD" | 118 |
| Parkiralište "Politika" | 0 |
| Parkiralište "Slavija" | 71 |
| Parkiralište "Vidin kapija " | 35 |
| Parkiralište "Viška" | 15 |
| Parkiralište "VMA" | 564 |

### Prijem 2026-09-05T20:30:02.4588621Z (slot 20:30 UTC, HTTP 200)

| lokacija | prikazano slobodnih |
|---|---|
| Garaža "Baba Višnjina" | 228 |
| Garaža "Botanička bašta" | 36 |
| Garaža "Dr Aleksandra Kostića" | 31 |
| Garaža "Masarikova" | 388 |
| Garaža "Obilićev venac" | 5 |
| Garaža "Pinki " | 104 |
| Garaža "Pionirski park" | 314 |
| Garaža "Vukov spomenik" | 33 |
| Garaža "Zeleni venac" | 30 |
| Parkiralište "Ada" | 872 |
| Parkiralište "Belvil" | 400 |
| Parkiralište "Bežanijska kosa" | 65 |
| Parkiralište "Blok 43" | 148 |
| Parkiralište "Čukarica" | 57 |
| Parkiralište "Cvetkova pijaca" | 35 |
| Parkiralište "Donji grad" | 20 |
| Parkiralište "Kalemegdan" | 12 |
| Parkiralište "Kamenička" | 0 |
| Parkiralište "Ljermontova " | 68 |
| Parkiralište "Međunarodni carinski terminal" | 225 |
| Parkiralište "Milan Gale Muškatirović" | 215 |
| Parkiralište "Opština NBGD" | 119 |
| Parkiralište "Politika" | 1 |
| Parkiralište "Slavija" | 77 |
| Parkiralište "Vidin kapija " | 36 |
| Parkiralište "Viška" | 12 |
| Parkiralište "VMA" | 565 |

### Prijem 2026-09-05T21:30:07.6592793Z (slot 21:30 UTC, HTTP 200)

| lokacija | prikazano slobodnih |
|---|---|
| Garaža "Baba Višnjina" | 234 |
| Garaža "Botanička bašta" | 72 |
| Garaža "Dr Aleksandra Kostića" | 29 |
| Garaža "Masarikova" | 386 |
| Garaža "Obilićev venac" | 45 |
| Garaža "Pinki " | 103 |
| Garaža "Pionirski park" | 329 |
| Garaža "Vukov spomenik" | 38 |
| Garaža "Zeleni venac" | 83 |
| Parkiralište "Ada" | 921 |
| Parkiralište "Belvil" | 404 |
| Parkiralište "Bežanijska kosa" | 64 |
| Parkiralište "Blok 43" | 148 |
| Parkiralište "Čukarica" | 58 |
| Parkiralište "Cvetkova pijaca" | 36 |
| Parkiralište "Donji grad" | 36 |
| Parkiralište "Kalemegdan" | 42 |
| Parkiralište "Kamenička" | 0 |
| Parkiralište "Ljermontova " | 68 |
| Parkiralište "Međunarodni carinski terminal" | 225 |
| Parkiralište "Milan Gale Muškatirović" | 233 |
| Parkiralište "Opština NBGD" | 119 |
| Parkiralište "Politika" | 2 |
| Parkiralište "Slavija" | 85 |
| Parkiralište "Vidin kapija " | 15 |
| Parkiralište "Viška" | 22 |
| Parkiralište "VMA" | 565 |

### Prijem 2026-09-05T22:30:43.5627052Z (slot 22:30 UTC, HTTP 200)

| lokacija | prikazano slobodnih |
|---|---|
| Garaža "Baba Višnjina" | 238 |
| Garaža "Botanička bašta" | 77 |
| Garaža "Dr Aleksandra Kostića" | 28 |
| Garaža "Masarikova" | 387 |
| Garaža "Obilićev venac" | 133 |
| Garaža "Pinki " | 102 |
| Garaža "Pionirski park" | 343 |
| Garaža "Vukov spomenik" | 48 |
| Garaža "Zeleni venac" | 130 |
| Parkiralište "Ada" | 954 |
| Parkiralište "Belvil" | 404 |
| Parkiralište "Bežanijska kosa" | 62 |
| Parkiralište "Blok 43" | 147 |
| Parkiralište "Čukarica" | 58 |
| Parkiralište "Cvetkova pijaca" | 41 |
| Parkiralište "Donji grad" | 45 |
| Parkiralište "Kalemegdan" | 56 |
| Parkiralište "Kamenička" | 0 |
| Parkiralište "Ljermontova " | 68 |
| Parkiralište "Međunarodni carinski terminal" | 225 |
| Parkiralište "Milan Gale Muškatirović" | 242 |
| Parkiralište "Opština NBGD" | 119 |
| Parkiralište "Politika" | 9 |
| Parkiralište "Slavija" | 86 |
| Parkiralište "Vidin kapija " | 0 |
| Parkiralište "Viška" | 31 |
| Parkiralište "VMA" | 565 |

## Putanje i integritet dokaza

| lokacija | 13:30 UTC | 14:30 UTC | 15:30 UTC | 16:30 UTC | 17:30 UTC | 18:30 UTC | 19:30 UTC | 20:30 UTC | 21:30 UTC | 22:30 UTC |
|---|---|---|---|---|---|---|---|---|---|---|
| Garaža "Baba Višnjina" | 233 | 245 | 246 | 250 | 242 | 235 | 228 | 228 | 234 | 238 |
| Garaža "Botanička bašta" | 74 | 73 | 63 | 52 | 29 | 22 | 22 | 36 | 72 | 77 |
| Garaža "Dr Aleksandra Kostića" | 37 | 39 | 38 | 36 | 34 | 32 | 32 | 31 | 29 | 28 |
| Garaža "Masarikova" | 346 | 361 | 371 | 372 | 375 | 380 | 384 | 388 | 386 | 387 |
| Garaža "Obilićev venac" | 29 | 41 | 31 | 6 | 0 | 0 | 0 | 5 | 45 | 133 |
| Garaža "Pinki " | 93 | 95 | 102 | 105 | 101 | 104 | 105 | 104 | 103 | 102 |
| Garaža "Pionirski park" | 275 | 315 | 328 | 332 | 336 | 328 | 310 | 314 | 329 | 343 |
| Garaža "Vukov spomenik" | 26 | 47 | 51 | 48 | 47 | 39 | 31 | 33 | 38 | 48 |
| Garaža "Zeleni venac" | 89 | 104 | 119 | 110 | 91 | 39 | 1 | 30 | 83 | 130 |
| Parkiralište "Ada" | 440 | 443 | 430 | 484 | 568 | 742 | 813 | 872 | 921 | 954 |
| Parkiralište "Belvil" | 397 | 398 | 400 | 398 | 392 | 396 | 399 | 400 | 404 | 404 |
| Parkiralište "Bežanijska kosa" | 70 | 70 | 69 | 67 | 65 | 66 | 65 | 65 | 64 | 62 |
| Parkiralište "Blok 43" | 144 | 146 | 146 | 145 | 148 | 148 | 148 | 148 | 148 | 147 |
| Parkiralište "Cvetkova pijaca" | 35 | 35 | 34 | 38 | 48 | 47 | 41 | 35 | 36 | 41 |
| Parkiralište "Donji grad" | 254 | 254 | 210 | 173 | 154 | 141 | 82 | 20 | 36 | 45 |
| Parkiralište "Kalemegdan" | 0 | 0 | 1 | 0 | 0 | 15 | 20 | 12 | 42 | 56 |
| Parkiralište "Kamenička" | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Parkiralište "Ljermontova " | 62 | 63 | 63 | 66 | 67 | 67 | 68 | 68 | 68 | 68 |
| Parkiralište "Međunarodni carinski terminal" | 222 | 220 | 222 | 224 | 223 | 225 | 224 | 225 | 225 | 225 |
| Parkiralište "Milan Gale Muškatirović" | 60 | 73 | 102 | 146 | 164 | 186 | 197 | 215 | 233 | 242 |
| Parkiralište "Opština NBGD" | 114 | 117 | 115 | 115 | 115 | 117 | 118 | 119 | 119 | 119 |
| Parkiralište "Politika" | 2 | 2 | 0 | 1 | 1 | 2 | 0 | 1 | 2 | 9 |
| Parkiralište "Slavija" | 82 | 80 | 76 | 70 | 74 | 67 | 71 | 77 | 85 | 86 |
| Parkiralište "VMA" | 518 | 338 | 505 | 558 | 560 | 562 | 564 | 565 | 565 | 565 |
| Parkiralište "Vidin kapija " | 3 | 8 | 1 | 0 | 4 | 28 | 35 | 36 | 15 | 0 |
| Parkiralište "Viška" | 16 | 29 | 38 | 35 | 34 | 21 | 15 | 12 | 22 | 31 |
| Parkiralište "Čukarica" | 58 | 57 | 60 | 62 | 59 | 55 | 58 | 57 | 58 | 58 |

| termin UTC | stvarni prijem UTC | lokacija | nedostajucih vrednosti | zbir prijavljenih mesta | SHA-256 receipta |
|---|---|---|---|---|---|
| [13:30](sample-20260905T133000Z.json) | 2026-09-05T13:30:03.5813264Z | 27 | 0 | 3679 | `361597798a72c22ff789766ceb33a6bdab47284ce6fa1bc287f0d17f2595e961` |
| [14:30](sample-20260905T143000Z.json) | 2026-09-05T14:30:02.7606066Z | 27 | 0 | 3653 | `0ca0ae5d5f19c925b7d663c4e73b5c39301aaacc0f6597a48fb6d655c76ef4c3` |
| [15:30](sample-20260905T153000Z.json) | 2026-09-05T15:30:01.4755409Z | 27 | 0 | 3821 | `8d2626e0e4c1afe15847d1699a44b0a8b7e7b67dae274ea4a444cc726c2c230d` |
| [16:30](sample-20260905T163000Z.json) | 2026-09-05T16:30:01.8010755Z | 27 | 0 | 3893 | `daa455bb60086db13906afb16644dce8c3f51147c415ac05a2c97045a4a8ebb0` |
| [17:30](sample-20260905T173000Z.json) | 2026-09-05T17:30:03.3752424Z | 27 | 0 | 3931 | `e44fd2cda8f2b9fdecb348350c5f0128463aca6cdaec7af46a17f271e09aa643` |
| [18:30](sample-20260905T183000Z.json) | 2026-09-05T18:30:01.6539473Z | 27 | 0 | 4064 | `3a7bd2ff7110f671bf20a8b483dd88afdb0af992fd099a80bb95af7433970afe` |
| [19:30](sample-20260905T193000Z.json) | 2026-09-05T19:30:02.7933456Z | 27 | 0 | 4031 | `3e9414a0b26fe6510777bf336c33c041c774e98f0458554aa403b888609c63c0` |
| [20:30](sample-20260905T203000Z.json) | 2026-09-05T20:30:02.4588621Z | 27 | 0 | 4096 | `3c01a7ecf0eacfd57d894731d334b54cea21eca3e1c954e6233a9fe279e6d467` |
| [21:30](sample-20260905T213000Z.json) | 2026-09-05T21:30:07.6592793Z | 27 | 0 | 4362 | `f932cf899c002f2ffabeb3a41cbab532f2ff1f481e48c86b0508a3b3374c5739` |
| [22:30](sample-20260905T223000Z.json) | 2026-09-05T22:30:43.5627052Z | 27 | 0 | 4598 | `3c52464acbac9fa198a5e6e767f01de73aa212cfa7bd89a0a1abb921af98e078` |

Zbir opisuje samo primljeni skup lokacija operatora. Nije ukupan kapacitet niti mera praznjenja Beograda. Nula ostaje nula; nepoznato ostaje nedostupno. Razlicit HTML hash ne dokazuje svezinu instrumentalnog merenja.

## Neutralne analitičke beleške

- `observed_at` je null u svim receiptima: prijem i merenje nisu isti trenuci i razlika od sat vremena u prijemu ne znači sat vremena u izvoru.
- Najveće pojedinačne promene se posmatraju bez smera i uzroka; lokacije van okruženja trke ostaju opisni kontekst, ne dokaz.
- Nema ukupnog kapaciteta, pa nema procenta popunjenosti; neto promena ne meri dolaske, odlaske ni broj učesnika.
- Ranija tvrdnja o pet nula na Kalemegdanu ispravljena je u [OPAZANJA.md](OPAZANJA.md): termin 15:30 UTC ima 1. Ponovljena nula na Kamenickoj nije dokaz mrtvog brojaca. VMA 518 -> 338 -> 505 ne dokazuje nemoguc promet ili kvar. Sve putanje ostaju u tabeli.
- Naknadno predlozen uslov dva uzastopna uzorka nije preregistrovan kriterijum iskljucivanja. Nijedan kratak iskok nije uklonjen. Grupe iz protokola nisu kontrolne; slaba promena nije opsta falsifikacija hipoteze.

## Negativni nalazi

- Termini bez receipt-a su rupe: dokumentovane, ne nadoknađene, ne pretvorene u nule.
- Nema kapaciteta, pa nema procenta; nema brojača prolazaka, pa nema toka učesnika.
- Nema uporedivih subota, pa se efekat trke ne izoluje — ni u jednom smeru.

## Granice

- Receipt, ne zakazano okidanje, jeste dokaz pokrivenosti prijema; zadatak je `Interactive only` (odjava/spavanje hosta = propušteni termini).
- Trka je izdvojena novobeogradska/zemunska epizoda unutar ukupnog Beograda; grupe u tabeli su opisne, nisu kontrolne grupe.
- Kvar izvora, parsera ili pojedinacnog brojaca moze uticati na jednu ili vise lokacija; bez nezavisne provere ne znamo uzrok ni obuhvat.

---

Honest verdict: izveštaj je napisan iz stvarno primljenih receipt-a (10 od 13 slotova) i ni jedan broj nije izmišljen ni interpoliran; ali pokrivenost ima rupe, izvorno vreme merenja je nepoznato, i ništa ovde ne dokazuje da je bilo koja promena uzrokovana trkom. Slanje bilo kog dela ovoga je Semirova odluka, ne deo ovog izveštaja.
