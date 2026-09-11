# BEOPS OBS-001: 10K kao observacija gradskog ritma

Verzija 2: pitanje i ishodi definisani 05.09.2026 oko 05:30 Europe/Belgrade; pre prvog zakazanog uzorka dodat je proverljiv upisivac. Ovo je prospektivna opisna observacija, ne kontrolisan eksperiment niti dokaz uzrocnosti. Pripreme i prve izmene prevoza vec su pocele; rani uzorak nije "netaknuto stanje pre trke".

Korisnik je trazio zaseban mini-eksperiment koji vodimo, belezimo i kasnije predstavljamo kao jednu observaciju, ukljucujuci moja kratka analiticka opazanja. Prostorna odluka je potom prosirena na ceo Beograd -> vece celine -> sire zone, bez mikronivoa. Trka ostaje izdvojeni slucaj novobeogradske/zemunske strane unutar ukupnog Beograda.

## Pitanje

Sta mozemo pouzdano opaziti o najavljenom dogadjaju povezivanjem javnih objava i prikazanih parking kapaciteta, bez nasih senzora, sopstvenog geografskog indeksa ili identifikacije ljudi?

## Primarni izvori i sat

- [Organizator](https://bgdmarathon.org/10k-belgrade-run-nike-2026/): 05.09.2026, dogadjaj 15:00-21:00, najavljen start 18:00. Plan se moze menjati. Datum/vreme su lokalni; tokom ove observacije Europe/Belgrade = UTC+2.
- [Sekretarijat za javni prevoz](https://www.bgprevoz.rs/vesti/informacija-o-promeni-rezima-rada-linija-javnog-prevoza-tokom-odrzavanja-manifestacije-trka-10k-beograd-2026): detaljni vremenski segmenti i promene linija. Ne svoditi sva zatvaranja na 18:00; neke izmene pocinju prethodnog dana.
- [Parking servis](https://www.parking-servis.co.rs/lat/garaze-i-parkiralista): jedan javni odgovor sadrzi sve lokacije i koordinate. Nema potrebe za 27 zahteva ili ponovnim geokodiranjem.

Rani uzorak: multidomain dokaz (private working record), parking preuzet 03:23:21 UTC / 05:23:21 lokalno; 27 lokacija. Izvorni cas merenja nije poznat. Uzorak ostaje u tom fajlu, ne menja se i ne prepisuje.

## Sta pratimo

Primarni ishod: putanja prikazanih slobodnih mesta po lokaciji, promena izmedju stvarno prikupljenih uzoraka i od prvog uzorka u odabranom prozoru. Nema ukupnog kapaciteta: ne racunamo procenat popunjenosti. Nema brojaca prolazaka: ne racunamo dolaske, odlaske ili broj ucesnika iz neto promene parkinga.

Cuvati svih 27 lokacija koje stizu jednim odgovorom. Pre naknadnog gledanja putanja, izdvajamo Opstinu NBGD, Belvil i Pinki kao novobeogradsko/zemunsko okruzenje; Donji grad, Kalemegdan i Zeleni venac kao centralno/obalno okruzenje; VMA, Cvetkovu pijacu i Bezanijsku kosu kao prostorno udaljeniji opisni kontekst. Ovo NISU uparene kontrolne grupe ili dokaz izlozenosti trci. Ostatak ostaje u prilogu; ne birati samo najdramaticnije promene posle dogadjaja.

Sekundarni ishodi: promene u zvaničnoj najavi, neslaganje vremena/trase medju izvorima, broj neuspesnih prijema, promene HTML seme, udeo nerazresenih lokacija i nedostatak source timestamp-a. I neuspesno povezivanje je rezultat.

## Ritam i zavrsetak

Predlog pracenja preko postojece Codex automatizacije u ovoj sesiji: po jedan snimak na sat, u :30 od 12:30 do 23:30 lokalno, sa zavrsnom proverom u 00:30 06.09.2026. To je 13 planiranih budjenja, uz vec postojeci rani uzorak. Ovo ogranicava trosak i rezoluciju: promene krace od jednog sata mogu promaci. Nema izmisljene istorije pre 12:30. Automatizacija i budnost hosta nisu garancija izvrsenja u sekundu.

Automatizacija `beops-obs-001-trka-10k` kreirana je ACTIVE u ovoj istoj sesiji i njen zapis je procitan nazad. Konfigurisan je navedeni satni raspored sa krajem 06.09.2026 u 00:30 lokalno. Kasnjenje i propusten termin su rupa, ne nadoknadjuju se danasnjim brojem kao da je raniji. Nema periodickih geokoderskih poziva. Najave proveravati na pocetku, oko pocetka dogadjaja, oko najavljenog starta i na kraju, ne svaki put sve stranice.

Ako pristup bude zabranjen ili izvor vrati 403/429, trajno oznaciti izvor pauziranim u dnevniku; naredni termini ne pokusavaju ponovo bez resenog uzroka. Nastaviti samo izvestavanje na osnovu vec dobijenih dokaza. Rad zavisi od dostupnosti hosta i aplikacije; konfigurisan raspored nije dokaz izvrsenih budjenja.

Za snimak pokrenuti `python -B research/observe_10k.py capture` iz korena Beopsa, koristeci dostupan Python iz UPUTSTVO.md. Upisivac koristi postojeci `parking_get` i `page_summary`; ne ponavljati ceo desetostruki probe. `python -B research/observe_10k.py status` samo cita pokrivenost i ne pristupa mrezi.

Po terminu se najpre atomski objavljuje neprepisiv `claim-*.json`, zatim najvise jedan bounded TLS-verifikovan zahtev i neprepisiv `sample-*.json`. Zapis sadrzi termin, stvarno vreme pokusaja/prijema, URL, status, hash i izdvojene vrednosti ili gresku. `observed_at` ostaje null. Ponovljen poziv ne ponavlja zahtev. Nedovrsen claim posle prekida ostaje neizvesnost i ne brise se radi retry-ja. Na 403/429 naredni pozivi citaju prethodni dokaz i preskacu mrezu. Ostale greske su neuspesni uzorci, ne nule.

Dozvoljeno kasnjenje je do 20 minuta po terminu, uz cuvanje stvarnog vremena. Van tog prozora nema nadoknade; pre 12:30 nema zahteva. Zavrsni termin 06.09. u 00:30 moze se izvrsiti do 00:50 lokalno (05.09.22:50 UTC). Posle tog roka upisivac ne pristupa mrezi. Na zavrsnom budjenju prvo pokusati poslednji dozvoljeni uzorak, potom napraviti izvestaj i pauzirati automatizaciju. Propusteno zavrsno budjenje zahteva naknadni izvestaj, ne izmisljeno merenje.

Na kraju napisati `IZVESTAJ.md`: vremenska linija najava, ostvarena pokrivenost uzoraka, tabela promena po imenovanim lokacijama, neutralne analiticke beleske, negativni nalazi i granice. Grafikon je opcioni izvoz iz podataka, ne pravljenje aplikacije. Posle zavrsetka prestati sa prikupljanjem i pauzirati automatizaciju ako jos postoji.

## Dnevnik opazanja

Svaka kratka beleska u `OPAZANJA.md` ima vreme, oznaku IZVOR/MERENJE/TUMACENJE/HIPOTEZA/OGRANICENJE, dokaz i sta bi promenilo zakljucak. Beleske su javno objasnjivi rezultati analize, ne maskirano merenje ili nezavisan izvor.

Nema individualnih rezultata trkaca, pracenja ljudi, lica, tablica ili audio razgovora. Nema javne distribucije punih tudjih stranica; pre objave proveriti uslove za konkretne podatke i navesti poreklo.

## Honest verdict na pocetku

Proveren organizator i prevozni plan; postoji jedan rani parking uzorak. Trka jos nije posmatrana tokom odrzavanja, model nije inferencijski primenjen, uzrocnost nije utvrdjena. Observacija moze zavrsiti nepotpunim podacima i to ostaje legitiman nalaz.
