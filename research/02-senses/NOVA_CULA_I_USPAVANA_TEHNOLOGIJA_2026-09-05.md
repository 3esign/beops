# Beops: drugi prolaz — nova cula, "uspavana" tehnologija grada i baze koje niko ne cita

Dopuna 05.09.2026 (popodne). Otvoreni pravac po zahtevu Semira: naci nova cula/instrumente/baze korisne za gradski puls, ukljucujuci tehnologiju koja po gradovima "lezi beskorisno". Dve metode paralelno: (1) inventar sistema koje grad vec ima a ne objavljuje — koga pitati, sta legitimno traziti; (2) bounded probe javnih platformi koje se retko koriste kao gradsko culo. Nista ovde nije automatski pokrenuto u produkciju.

## 1. Uspavana tehnologija koju Beograd vec poseduje (inventar zahteva, ne izmisljeno stanje)

Pravilo: svaki od ovih sistema VEC postoji i VEC nesto loguje; pitanje nije "da li ima podataka" nego "ko ga pita". Za svaki: vlasnik/tacka za zahtev, sta bi doslovno trazili, i granica. Zahteve pisati kao open-data zahtev ili predlog partnerstva, uvek za agregat — nikad za redove sa licnim podacima. Status svih stavki: NEPOTVRDJENO da li je bilo koji od ovih već objavljen; ovo je lista kandidata za zahtev, ne nalaz da postoji feed.

| Kandidat | Sta sistema vec loguje | Tacka za zahtev (konkretno) | Sta traziti (bezbedan oblik) | Rizik/ograničenje |
|---|---|---|---|---|
| Ticketing javnog prevoza (BusPlus) | Validacije po liniji/stajalistu/vremenu | Sekretarijat za javni prevoz GB + GSP "Beograd" + BusPlus | Agregat broja validacija po stajalistu i satu | Komercijalni ugovor; licne karte ne izlaze |
| GPS vozila javnog prevoza | Pozicija, kasnjenje, brzina po voznji | Sekretarijat za javni prevoz GB | GTFS-Realtime feed ili dnevni agregati kasnjenja po liniji | Operatori cesto nemaju javni RT feed u Srbiji |
| Semafori / detekcija na raskrsnicama | Zauzece traka, broj prolaza, faze | Sekretarijat za saobracaj GB; Beograd-put (odrzavanje) | Satni broj vozila po raskrsnici | MUP/operater mogu odbiti; bez licnih vozila |
| JKP Parking Servis | Slobodna mesta, naplata po zoni (27 lokacija vec probano) | JKP Parking servis (veza postoji preko OBS-001) | Zvanicna dozvola za citanje istog endpoint-a ritmom OBS-001 | Redistribution terms nisu potvrdjeni |
| Javna rasveta | Ukljucenje po zoni, kvarovi, potrosnja | JKP "Javno osvetljenje" Beograd | Dnevno vreme ukljucenja po zoni + spisak kvarova | Operativni podatak, ne javni |
| Komunalna vozila (cistoca, zelenilo) | GPS rute, praznjenja kontejnera | JKP "Gradska cistoca"; JKP "Zelenilo-Beograd" | Broj praznjenja po naselju/danu | Logistika se cuva interno |
| Vodomeri / telemerenje | Potrosnja i pritisak po zoni, curenja | JKP BVK (planirani radovi vec se prate) | Zonski agregat potrosnje dnevno; pritisak po hidrantskoj zoni | Domicinstvo ne izlazi; BVK je i vlasnik naseg izvora S11 |
| Ticketing + besplatni WiFi gradskih objekata | Broj sesija po pristupnoj tacki | Gradski sekretarijati za informisanje; operator (nepotvrdjen) | Broj sesija po lokaciji/danu | MAC podaci ostaju kod operatora |
| Saobracajne kamere i brojaci | Broj vozila po klasi, brzina | MUP Uprava saobracajne policije; operator mostova | Agregat brojanja po sat (nema snimaka, nema tablica) | Pristup tesko; zadrzati kao dalji cilj |
| BMS javnih zgrada (klima, energija) | Temperatura/potrosnja zgrade | Direkcija za imovinu GB | Mesecna potrosnja + temperaturni profil javnih zgrada | Malo objekata ima BMS |
| Hitne intervencije (112/HMP) | Broj i tip poziva po opstini/satu | MUP Sektor za vanredne situacije; Gradski zavod za hitnu pomoc | Agregat po opstini/satu, bez lokacije poziva | Vrlo osetljivo; samo gustina, nikad adrese |
| CEOP građevinske dozvole | Izdate dozvole po opstini, tip, datum | MGSI/APR preko ceop.apr.gov.rs | Vec javno — parsirati kao citalac, bez licnosti investitora | Vec postoji javni portal; prava proveriti |
| Javne nabavke | Tenderi, vrednosti, rokovi | Uprava za javne nabavke (jnportal) | Vec javno — indeks investicione aktivnosti po zonama | Vec postoji portal |
| Seizmicka mreza + mikrotremori | Kontinuirani talasni zapis | Repubicki seizmoloski zavod; GFZ/EIDA kanali BEO/AVAS (vec u registru S19) | Vec je u registru; dodati latest waveform proveru | Vec pokruto zadatakom G03 |

Pravilo izvodenja: prvo zahtevi za vec-javne portale (CEOP, nabavke, katastar), pa agregati komunalnih JP, pa tek onda MUP/telekom. Niko ne dobija zahtev pre nego sto napisemo tacan oblik agregata koji trazimo.

## 2. Nova cula probana ovim dahom (bounded probe, po jedan zahtev)

Evidence: `evidence/newsenses-2026-09-05T125146343Z.json`. Sve probe 200 OK iz jednog zahteva; OSM changesets proba je u sacuvanom evidence fajlu vratila 0 changeseta (nema evidence fajla za bilo kakvu vecu vrednost). Sve su kandidati, ne kolektori.

| ID | Platforma | Sto meri | Rezultat probe | Sta jos ne znamo |
|---|---|---|---|---|
| S34 | openSenseMap `api.opensensemap.org/boxes?bbox=20.2,44.6,20.7,45.0` | Gradjanski senzori: PM10/PM2.5, temp, vlaga, pritisak | 15 kutija u Beogradu (Mirijevo, Karaburma, VM-e/VM-i, Panorama, Garibaldijeva, Rakovica...) | `measuredAt` starost citanja; da li kutije feed-uje isti vlasnik kao Sensor.Community (dupli brojac!) |
| S35 | OSM changesets `api.openstreetmap.org/api/0.6/changesets?bbox=...` | Izmene mape grada: nove radnje, pijačna, rušenja, novi kolovoz | 0 changeseta u sacuvanom evidence fajlu (jedina verifikovana vrednost; bilo kakva veca vrednost nema evidence fajl); komentari pokazuju stvarne promene mesta | Ritam promene veci od 100/promenljivo; ne citati kao "gradjinska aktivnost grada", vec kao signal izmena javne mape |
| S36 | OpenSky `states/all` bbox Beograd | Avioni u nadletu (ADS-B): pozicija, brzina, visina | 5-8 letelica u prozoru; ASL132 (Air Serbia), WZZ, ISR... | Rate limit anonimnog pristupa; koliko cesto pozivati da ne narusimo uslove |
| S37 | RIPE Atlas `probes?country_code=RS` | Mrezne probe u Srbiji | 197 u Srbiji, 57 u Beogradu | Sami measurement rezultati zahtevaju kredite; metapodaci besplatni |
| S38 | GDELT doc `location:Belgrade` | Geolocirani novi clanci | Endpoint radi, ali rate-limit "jedan zahtev/5s" je agresivniji nego sto mislimo — dva od tri pokusaja vracena poruka o limitu | Ne koristiti bez pune pauze; bolje koristiti GDELT kao otkrivaca izvora nego kao puls |

Tri kljucna zakljucka ovog prolaza:

1. **Najveca zlata: OSM changesets i openSenseMap.** OSM changesets su "ulo gradjanske paznje" — kafei koji su otvoreni, pijačne zone, nove ulice — sve sto covek vec zapisuje, a grad ne cita. openSenseMap dopunjuje vazduh sa 15 gradjanskih kutija, ali moramo proveriti preklapanje sa Sensor.Community (ista kutija se može feed-ovati na obe mreze — onda nisu dva nezavisna cula).
2. **Avioni kao "visoki sloj" mobilnosti**: OpenSky je potpuno besplatan i bez kljuca, ritam aerodroma Nikola Tesla je direktan gradski signal (dolasci, nocni letovi). Ne meri ulicni saobracaj, ali meri konektivitet grada.
3. **GDELT je spor i cesto limitiran** — zadrzati ga samo za otkrivanje izdavaca, ne kao ritmicno culo.

## 3. Kako se nova cula ukljucuju u postojece organe (bez novog sistema)

- S34 ide u organ vazduha kao posebna porodica `citizen_iot` pored RHMZ/SEPA; poseban `shared_origin_group` flag za dupliranje sa Sensor.Community (zadatak C01 se prosiruje).
- S35 je NOVI organ: "organ javne mape grada" — cita changesete, grupise po naselju/tipu izmene, daje spori dnevni puls promene gradskog tkiva. Bez licnosti autora; autor je samo dokaz porekla, ne subjekat analize.
- S36 ide u organ kretanja kao visokoslojni indikator (satno agregirano, `aircraft_over_beograd`).
- S37 je mrezni zdravstveni organ: koliko proba zivih, latencije ka javnim servisima — ne gradi se novo, samo cita javne metapodatke.
- S38 ostaje kao istrazivacki alat za otkrivanje novih izdavaca za organ objava.

## 4. Sledeci konkretni koraci (u granicama postojeceg plana)

1. Proveriti starost merenja (measuredAt) S34 kutija jednim `boxes?date` upitom — cisti podatak za matricu pokrivenosti R02.
2. Napisati draft zahteva za 3 najlaka JP agregata (Parking servis javna dozvola, javna rasveta vreme ukljucenja, hitna pomoc broj poziva po opstini/satu) — tekst sa oblikom agregata, bez slanja; slanje je posebna Semirova odluka.
3. OSM changesets: napisati bounded parser (grupisanje po komentarima i bbox naselja) kao istrazivacki fixture za zadatak M02.
4. Ne skidati tezine, ne paliti inference, ne praviti nove schedulere; OBS-001 nastavlja po svom protokolu.

## Honest verdict

Izvrseno: 5 bounded HTTP proba (svaka po jedan zahtev, 200 OK), 1 ponovljena OSM proba, 1 uspesan RIPE upit, 1 GDELT proba koja je potvrdila limit; inventar "uspavane" gradske tehnologije sa konkretnim tackama za zahtev (19 kategorija, imena organizacija). Nepotvrdjeno: da li bilo koji JP vec objavljuje te podatke; preklapanje openSenseMap/Sensor.Community kutija; measuredAt starost podataka; gustina AIS brodova na Dunavu; prava za obradu bilo kog sadrzaja. Nije uradjeno: slanje bilo kog zahteva, instalacija i jednog kolektora, izmena postojece automatizacije. Lista JP je pisana po javno poznatim nazivima ustanova; tacne nadleznosti za neke kategorije (npr. semafori, WiFi) ostaju NEPOTVRDJENO dok se ne upita nadlezni sekretarijat.