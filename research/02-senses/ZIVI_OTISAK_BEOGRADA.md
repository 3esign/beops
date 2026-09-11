# BEOPS: dati Beogradu oblik kroz njegov zivi otisak

Istrazivacki dosije, 05.09.2026. Revidira prethodni, previse opsti pristup.
Predmet je Beograd. Pazarac je zaseban projekat i izvor iskustva. Interfejs se ne gradi u ovoj fazi.

## Sta je zapravo zadatak

Ne pravimo samo agregator vesti, spisak modela ili dashboard sa temperaturom. Istrazujemo koliko grad moze da postane opazljiv kroz postojece javne digitalne tragove: merne stanice, senzorske mreze, kamere, zvuk, seizmologiju, saobracaj, infrastrukturu, ekonomiju i objave. Zatim proveravamo koliko mali modeli mogu da povezu te tragove u razumljiv, ziv i proverljiv otisak.

"Dati gradu oblik" je stvaralacki cilj. Naucni cilj je da taj oblik ima poznat odnos prema stvarnosti: da znamo sta ga je promenilo, koji deo grada predstavlja, koliko kasni i gde nema dovoljno podataka. Konacan oblik moze biti prostoran, zvucan, tekstualan ili promenljiva struktura. Nije unapred odluceno da je lice, lik, mapa ili aplikacija.

Glavna istrazivacka tvrdnja koju TEK proveravamo: kombinacija vise heterogenih, jeftinih cula i malih specijalizovanih modela moze da napravi korisniji otisak grada od pojedinacnog izvora ili jednog velikog modela, unutar ogranicenog racunarskog budzeta.

## Mapa dosijea

Najnoviji smer korisnika: [vise domena od pocetka](VISE_DOMENA_2026-09-05.md), priblizne centralne zone i spoljno povezivanje (private working record), bez internog geokodera. Atmosferski pilot ispod ostaje jedna grana istrazivanja, ne jedini prvi proizvod. [OBS-001 trka 10K](../observations/10k-2026-09-05/PROTOKOL.md) je odvojena observacija.

- [Registar 33 izvora i pristupnih puteva](../SOURCE_REGISTRY.json): teme, linkovi, status, ritam, pristup i sledeca konkretna provera.
- [Modeli i literatura](../03-models/MODELI_I_LITERATURA.md): provereni identiteti modela, zadaci, ogranicenja i naucni izvori sa dubinom citanja.
- 65 zadataka po prioritetima (private working record): zavisnosti i dokaz zavrsetka; bez automatskog pokretanja drugih agenata.
- [Drugi gradovi, cula, organi i organizam](DRUGI_GRADOVI_CULA_I_ORGANI.md): uporedni projekti, 12 dodatnih cula, precizan recnik i kontrolisano poredjenje O0/O1/O2.
- Sta preuzeti iz Pazarca (private working record): konkretne lekcije iz koda, bez prenosa lokalnih pretpostavki ili menjanja tog projekta.
- Protokol kontrolisanih eksperimenata (private working record): osnovna evaluacija, dopunjena zivim otiskom u ovom dokumentu.
- [Direktne probe](../evidence/): odgovori i metapodaci, vreme preuzimanja, SHA-256, obim i ogranicenja. Nisu produkcijski kolektori.

## 1. Sta je vec stvarno pronadjeno

Probe su izvrsene sa PC-a 05.09.2026, oko 02:36 UTC, odnosno 04:36 po lokalnom letnjem vremenu. Ovo su nalazi u tom trenutku, ne trajna garancija dostupnosti.

| Culo | Konkretan nalaz | Znacenje za Beops |
|---|---|---|
| RHMZ automatske stanice | HTTP 200, procitani redovi Beograd, Kosutnjak i Barosevac; izvor prikazuje termine 04:30/04:35 | Postoje stvarna javna meteo ocitavanja; vremensku zonu, identifikatore i geografski obuhvat jos treba formalizovati |
| NOAA Aviation Weather / LYBE | JSON, jedno ocitavanje sa `reportTime=2026-09-05T02:30:00Z`; temperatura 22 C | Nezavisan pristupni put za aerodromske podatke, ne nuzno nezavisan fizicki instrument od drugih agregatora |
| Sensor.Community | 84 zapisa / 37 jedinstvenih senzorskih ID-jeva u probnom pravougaoniku; najnovije oznake do 02:36 | Postoji lokalna mreza finijeg ritma. ID nije isto sto i nezavisna lokacija; geometrija i kvalitet nisu auditovani |
| Beoeko | Procitan 31 red stanica; satni termin od 03:00; postoje prazna polja | Zvanična gradska mreza ima javni digitalni izlaz. Podaci su oznaceni kao neverifikovani, satni |
| RHMZ Zemun | Dostupna tabela sa 179 HTML redova, ukljucujuci hidro podatke | Kandidat za ritam reke, ali broj HTML redova nije broj validnih merenja; treba normalizovati |
| BVK i EDS | Obe stranice dostupne; EDS dnevna tabela nosi datum 05.09.2026 | Ziv administrativni tok planiranih prekida, ne neposredno merenje vode ili struje |
| Parking servis | Javno prikazuje slobodne kapacitete, ali lokalna Python proba odbijena zbog TLS lanca | Jak kandidat za agregatni mobilni puls; ne iskljucivati proveru sertifikata da bi proba prosla |
| EMSC i USGS | Oba API-ja odgovorila; EMSC regionalni pravougaonik vratio 11 dogadjaja, USGS krug 300 km vratio 0 za zadatih 30 dana | Dokaz pristupa katalogu, ne dokaz istovetne pokrivenosti ili gradskog podrhtavanja; upiti NISU prostorno jednaki |
| GTFS Beograd | ZIP 17.576.567 bajtova; 3.266 stop redova, 241 route red | Upotrebljiva strukturna osnova saobracaja. Feed nosi pocetak 02.09.2025. i kraj 31.12.2026, sto nije dokaz stvarne aktuelnosti svake linije |

Dokazi: `live-20260905T023625849552Z.json`, `global-20260905T024115643191Z.json`, `gtfs-20260905T023808172742Z.json` u `evidence/`. Deset HF identiteta provereno je zasebno, bez skidanja tezina ili ucitavanja modela.

Praktican zakljucak: moze da se zapocne stvarni meteo/atmosferski otisak BEZ kupovine senzora i BEZ kamera. Kamere, zvuk i zemljiste imaju smisla kao sledeca cula, ne kao uslov da prvi otisak postoji.

## 2. Prioritetna tema: vreme i javne stanice

Tri komplementarna puta: RHMZ kao lokalna zvanicna merna osnova; LYBE/METAR kao globalno dostupan aerodromski zapis; Sensor.Community za raspored dodatnih senzora. [RHMZ](https://www.hidmet.gov.rs/latin/osmotreni/automatske.php), [NOAA API](https://aviationweather.gov/data/api/), [Sensor.Community dokumentacija](https://github.com/opendata-stuttgart/meta/wiki/APIs).

Prvi otisak treba da cuva odvojene tokove temperature, relativne vlaznosti, vetra, pritiska i dostupnih padavina. Vremenska razlika izmedju dve stanice najpre je pitanje uporedivosti instrumenata, lokacije, visine i termina, pa tek onda moguca mikroklimatska informacija. Pritisak na stanici i pritisak sveden na nivo mora nisu zamenljivi. Brzinu vetra iz METAR-a ne tretirati kao m/s bez konverzije prema API semantici.

Istraživanje: koliko se dobija dodavanjem svake stanice; koliko je otisak stabilan kad najaktivnija stanica nestane; da li model prepoznaje promenu pre jednostavne statistike i po kojoj ceni? Prve rezultate meriti po stanici i vremenskom prozoru, ne izmisljati jedan prosecni Beograd.

Ritam prikupljanja: za pilot predlog 10 minuta za RHMZ/meteorolosku projekciju, pet minuta za dokumentovani Sensor.Community poslednji prozor i 15 minuta za aerodrom. To su predlozi dok se ne potvrde pravila izvora i izgubljeni zapisi; nisu vec ukljuceni rasporedi. Za kanonsku istoriju latest prozor dopunjava se dnevnom arhivom gde postoji, uz deduplikaciju i revizije.

Open-Meteo ostaje koristan paralelan prognozni kanal. Njegov `current` ne pretvaramo u fizicku stanicu. Prognoza nosi vreme izdavanja i horizont; kasnije je poredimo sa merenjem koje u vreme prognoze jos nije bilo dostupno.

## 3. Vazduh, voda i globalno opažanje

Vazduh: Beoeko + Sensor.Community mogu da daju razlicitu prostornu i vremensku gustinu. Najbliza stanica nije automatski kalibraciona referenca. Potrebni su podaci o instrumentu, ko-lokacija ili jasno ogranicen prostorni test, vlaznost i oznake kvaliteta. [Rad o sezonskoj/vlaznosnoj kalibraciji](https://amt.copernicus.org/articles/17/1051/2024/) obrazlaze zasto univerzalni korekcioni faktor nije dovoljan.

Voda: RHMZ recni nivo, njegova promena i brzina promene. Ne izvoditi protok bez odgovarajuce krive niti rizik poplave bez modela i nadlezne prognoze. Vodostaj i najava prekida vodovoda pripadaju razlicitim procesima iako su oba "voda".

Globalno: OpenAQ kao dodatni put ka merenjima i istoriji, ali zahteva API kljuc i proveru Beograd pokrivenosti. [OpenAQ upozorava](https://docs.openaq.org/resources/latest) da pracenje samo latest endpointa ne cuva sve zakasnele podatke. To direktno utice na dizajn Beopsa.

[NASA IMERG](https://gpm.nasa.gov/data/imerg) daje polusatne procene padavina, ali Early proizvod ima oko cetiri sata kasnjenja. To jeste blisko realnom vremenu za neke procese, nije pogled na pljusak ovog minuta. [FIRMS](https://firms.modaps.eosdis.nasa.gov/api/) daje termalne detekcije; tacka toplote nije automatski gradski pozar. [Sentinel-2](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2) daje besplatne multispektralne proizvode za sporije promene vegetacije/prostora; oblaci i preleti ogranicavaju zivi ritam. Nije kamera iznad grada koja radi neprekidno.

## 4. Kamere: vid grada

[AMSS javna kamera za Novi Beograd](https://www.amss.org.rs/na-putu/stanje-na-putu/strana/kamere?granica_select=&naxi_kamere=21) potvrdjuje pristupni put, ne jos preuzet i vremenski potvrden kadar. [Windy Webcams API](https://api.windy.com/webcams/docs) je globalni katalog/pristup sa kljucem; trenutni besplatni plan, konkretna Beograd pokrivenost i prava obrade nisu provereni.

Najkorisniji pocetni vizuelni zadaci: osvetljenost i vidljivost, mokra/suva povrsina, sneg, kvalitativna zauzetost unapred definisane zone. Svaki kadar mora imati poznatu lokaciju, vidno polje, vreme i uslove koriscenja. Sabiranje vozila zahteva namenski detektor i anotacije; opis malog VLM-a nije pouzdan broj. Pomeren kadar, noc, kompresija i zaklon su posebni testovi.

Javni proizvod ne zahteva prenos sirovog videa. Moguce je objavljivati agregat sa poreklom, ako prava izvora to dozvoljavaju. Ne pratimo pojedince kroz kamere, ne prepoznajemo lica ili tablice i ne izvodimo identitet/grupnu pripadnost. Ne skeniramo privatne IP kamere. Ako javni tok ne moze zakonito da se obradi, zamena je dozvoljena sopstvena/partnerska kamera ili izostavljanje sloja.

## 5. Zvuk: zvucni ritam, ne preslusavanje grada

[Locus Sonus](https://locusonus.org/soundmap/) zaista organizuje globalne zive mikrofone i umetnicki rad sa zvucnim pejzazima. U ovoj proveri NIJE potvrdjen aktivan mikrofon u Beogradu. Ta praznina ostaje vidljiva; tok iz drugog grada ne sme biti predstavljen kao Beograd.

Sopstveni ili partnerski mikrofon otvara jasne zadatke: vremenski udeo saobracajnog zvuka, kise, gradjevinskih radova i drugih dogovorenih klasa; promena spektralnog sadrzaja i odnosa tišine/aktivnosti. Obrada na uredjaju i cuvanje kratkih agregata smanjuju potrebu za slanjem razgovora. ASR nije potreban za zvucni puls. Nekalibrisan mikrofon ne daje pouzdanu apsolutnu buku u dB(A), ma koliko precizan bio neuralni klasifikator.

[YAMNet](https://www.tensorflow.org/hub/tutorials/yamnet) i [DCASE mali akusticki modeli](https://arxiv.org/abs/2505.01747) su konkretni kandidati. [SONYC](https://arxiv.org/abs/2009.05188) je vazna metodoloska referenca: zvuk + lokacija + vreme + ljudske anotacije. Njujorški benchmark pomaze da osmislimo test, ali nije dokaz kvaliteta na beogradskim mikrofonima. Nagli impuls ne proglašavati pucnjem ili eksplozijom iz jednog modelskog izlaza.

## 6. Zemljotresi i kontinuirani otisak tla

Razdvajamo tri stvari: katalog lociranih dogadjaja, kontinuirani talasni zapis sa stanice i izvedene akusticke/seizmicke karakteristike. Katalog se menja retko; tlo moze da ima kontinuirani signal i kada nema zemljotresa.

[RSZ](https://seismo.gov.rs/) objavljuje preliminarne i obradjene podatke. [EMSC](https://www.seismicportal.eu/fdsn-wsevent.html) ima dokumentovan JSON/QuakeML servis i CC BY 4.0; [USGS](https://earthquake.usgs.gov/fdsnws/event/1/) globalne kataloge i preporucene real-time feedove. Katalozi mogu deliti izvornu mrezu i revizije, pa tri sajta ne znace tri nezavisna dokaza.

[ORFEUS SJ](https://orfeus-eu.org/stationbook/networks/SJ/1980/) vodi srpsku mrezu kao otvorenu, ukljucujuci BEO i AVAS. Sledeca provera je stvarni dostupni kanal, instrument response, uzorkovanje i poslednji dostupni waveform: oznaka open ne dokazuje malu latenciju. Za preuzimanje/procesiranje koristiti postojeci FDSN/miniSEED alat iz izolovanog istrazivackog okruzenja, ne rucni parser u jezgru.

Zanimljivo buduce pitanje: moze li spektar ambijentalnih vibracija da doprinese ritmu aktivnosti oko stanice? To zahteva kontrolu instrumenta, lokacije, vremenskih uslova i nezavisan test. Nije predvidjanje zemljotresa, broj prolaznika ili dokaz konkretnog dogadjaja. [Raspberry Shake](https://raspberryshake.org/license/) je dodatni put, ali sa ogranicenjima upotrebe/redistribucije koje treba proveriti pre javnog toka.

## 7. Saobracaj, infrastruktura i ekonomski ritam

Saobracaj: staticki GTFS kao struktura + zive objave BG Prevoza/Grada + eventualno parking agregati. Odvojiti planiranu uslugu, najavljenu izmenu i stvarno opazenu aktivnost. Dug kalendar vazenja GTFS-a nije dovoljan: preuzet primer ima stare izuzetke u calendar_dates, pa treba proveriti promene prema danasnjim obavestenjima. Stop red moze predstavljati smer/peron, ne jedinstvenu fizicku lokaciju.

Komunalne usluge: BVK i EDS su koristan dnevni puls prostora sa najavljenim prekidima. Tek spajanje naziva ulica, raspona brojeva i intervala omogucava korisno pitanje "sta je najavljeno za ovaj deo grada". Najava se ne pretvara u potvrdu stvarnog prekida niti se istekom plana automatski proglasava obnova.

Ekonomija ima i brz i spor tok: [objavljeni cenovnici](https://data.gov.rs/sr/datasets/cenovnici/) mogu dati promenu ponudjenih cena; RZS/APR daju sporiju strukturnu osnovu. Cena nije prodaja, sediste firme nije radnja, vest o investiciji nije realizovan kapital. Prvo proveriti koji trgovci daju prodavnice u Beogradu, jedinice mere, iste barkodove, akcijske intervale i objavljeni datum. Mesecne plate ne menjaju se svakim osvezavanjem stranice.

Gradski oglasi i kulturni dogadjaji daju najavljeni javni ritam. Dokumenti/arhive daju poreklo mesta i odluka. Broj vesti nije mera intenziteta dogadjaja: treba spajati prepisane objave i razdvajati objavljivanje, dogadjanje, izmenu i povlacenje informacije.

## 8. Nekoliko pulseva, bez mesanja ciljeva

Predlog tri nivoa eksperimenta:

1. **Fizicki otisak:** stanice, vazduh, reka; zatim dozvoljeni zvuk/vid/tlo. Pitanje: sta opazamo i gde su rupe?
2. **Otisak funkcionisanja:** fizicki sloj + saobracaj + komunalne najave. Pitanje: sta se menja u koriscenju grada?
3. **Kontekstualni otisak:** prethodno + javne objave, cene i memorija. Pitanje: sta mozemo bolje objasniti, a sta je samo korelacija?

Za svaki nivo poredimo pravila bez modela, jedan mali specijalista i kombinaciju specijalista. Isti zamrznuti ulazi, ista vremenska granica znanja, odvojeni budzeti. Uklanjanje jednog izvora pokazuje njegov marginalni doprinos; uklanjanje modela pokazuje da li nam uopste treba.

Otisak u trenutku t nije jedan broj. Predlog ugovora je skup:

`F(place,t) = {observed_state, changes, rhythms, spatial_support, freshness, uncertainty, evidence_ids}`

Formalna projekcija `P_k = g_k(F, window, source_set_version, model_version)` cuva trag do ulaza. "Puls" moze biti vektor ili vremenska struktura; skalar je dozvoljen samo za jasno definisanu meru sa jedinicom i proverom. Stabilna temperatura uz sveza ocitavanja je zivo stanje, a ne zastoj.

## 9. Kako oblik ostaje povezan sa stvarnoscu

Oblik nije naredni ekran koji odmah crtamo. Prvo definisemo izrazajnu gramatiku: koja merljiva promena utice na koji parametar oblika, kakvo filtriranje se primenjuje, kolika je latencija i kako se razlikuju izmereno, predvidjeno i nepoznato.

Moguce kasnije probe: prostorno polje iz stanica; vise vremenskih ritmova koji se susrecu; zvucna projekcija bez kopiranja sirovih snimaka; morfologija promena i vidljivih praznina. Nista od ovoga jos nije izabrani dizajn. Materijal je otisak, a oblik je autorska interpretacija koja ne skriva pravila.

Test korisnosti oblika: moze li covek da prepozna stvarnu promenu, da razlikuje tiho od nedostupnog i da nadje dokaz brze nego iz sirove tabele? Porediti nekoliko mapiranja na istom toku. Dopadljivost, citljivost i tacnost su odvojeni rezultati. Jedan lik ne sme da proizvoljno predstavlja raspolozenje svih stanovnika.

## 10. Naucni rad i sistem koji moze da opstane

Glavni doprinos za prvi rad: **reproduktivni zivi multimodalni otisak jednog grada sa merljivim odnosom pokrivenosti, kasnjenja, kvaliteta i racunarskog troska.** Ne pokusavati da jedan kratak konferencijski rad dokaze sve o gradu, agentima, ekonomiji i umetnosti.

Vazeci prvi slucaj je OBS-001 trka 10K: povezivanje javnog plana, parking prikaza i analitickih opazanja. Istovremeno razvijamo uporedive uzorke cene/javnih dogadjaja/atmosfere/vode. Raniji 72h/14-dnevni meteo predlog ostaje moguc domenski eksperiment, ne obavezan prvi korak niti uslov za ostale oblasti. Kontrolisano poredjenje modela i baseline-a jos nije izvrseno.

Mere: pokrivenost stanica/prostora, starost informacije, propušteni i duplirani zapisi, greska prognoze/promene, preciznost korisnih obavestenja, RAM/CPU/GPU, broj poziva, vreme oporavka. Za merenje energije potreban je odgovarajuci merac. Jedna proba u septembru nije dokaz cele godine ili prenosivosti na druge gradove.

Arhitektonski zahtev je da koristimo postojece Svemir sposobnosti za raspored, granice, trag i oporavak, a ne da Beops pravi novu infrastrukturu. Dostupnost replay-a, mesh replikacije i opsteg router-a ovde nije auditovana niti garantovana. Trenutno je posebno proverena ogranicena OBS-001 putanja; ostale sposobnosti se dokazuju po potrebi. Javna projekcija ne sme iznositi tajne, privatne sesije ili neodobrene snimke.

## Presuda ovog prolaza

Uradjeno: tematska pretraga, primarni izvori, direktne ogranicene probe, provereni metapodaci 10 modela, offline testovi istrazivackog probe alata, konkretan radni program. Postoje podaci dovoljni za pocetni zivi meteo otisak.

Nije uradjeno: stalno pracenje, merenje uptime-a kroz dane, bibliografski sistematski pregled celog polja, lokalni benchmark modela, dostupna i odobrena Beograd audio/video mreza, talasni seizmicki tok, potpun pravni audit, naucni rezultati, javni deploy. Nije pokrenut nijedan novi agent, servis, mikrofon ili kamera.
