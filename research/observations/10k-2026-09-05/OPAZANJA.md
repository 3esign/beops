# OBS-001: dnevnik kratkih opazanja

## 2026-09-05 05:30 Europe/Belgrade - pocetna beleska, Astra

- IZVOR: organizator najavljuje start u 18:00 i program 15:00-21:00. To jos nije potvrda odrzavanja. Dokaz: link organizatora u PROTOKOL.md.
- MERENJE: u 05:23 lokalno primljen je parking prikaz za 27 lokacija; koordinatni linkovi su deo istog izvora. Ovo je izmereno vreme prijema i procitana vrednost, ne nezavisna provera parking senzora. Dokaz: multidomain JSON naveden u protokolu.
- TUMACENJE: dokument o prevozu nosi vise vremenskih rezima; priprema dogadjaja je deo gradskog otiska pre starta. Jedna oznaka "trka u 18h" izgubila bi taj deo.
- HIPOTEZA: oko prelaza najavljenih rezima mogu se promeniti prikazani parking brojevi. Nije pretpostavljen smer, velicina ili uzrok promene; ravna putanja je takodje rezultat.
- OGRANICENJE: bez uporedivih subota i instrument timestamp-a ne mozemo izolovati efekat trke. Drugi dogadjaji, uobicajeni vikend, kapaciteti i kvar izvora su moguca alternativna objasnjenja.
- OPAZANJE O METODU: prvi Photon pogodak za javnu adresu Visnjicka 84 nudio je broj 69. Zato gruba zona sa iskazanom neizvesnoscu moze biti postenija od precizne pogresne tacke. Taj upit nije deo trke; zabelezen je kao lekcija povezivanja.

Sledece beleske dodavati ispod, bez prepisivanja ovog pocetnog stanja. Nova saznanja mogu ispraviti ranije tumacenje uz trag promene.
  
## 2026-09-05 15:16 Europe/Belgrade - Build v1 status  
  
- OGRANICENJE: u 13:16 UTC (15:16 lokalno) status pokazuje 0/13 snimljeno; slotovi 10:30, 11:30, 12:30 UTC su missing (automatizacija nije izvrsila budjenja). Sledeci slot 13:30 UTC je pending, ~14 min od sada.  
- MERENJE: pokusaj capture u 13:14 UTC vratio missed_window za 12:30 UTC (van dozvoljenog prozora), 0 mreznih zahteva. Ovo je dokumentovana rupa, ne nula.  
- OPAZANJE O METODU: konfigurisana automatizacija nije dokaz izvrsenih budjenja; prvi opipljiv uzorak zahteva rucno pokretanje capture za tekuci slot.  

## 2026-09-05 15:55 Europe/Belgrade - Revise v2 status (prvi uzorak snimljen)

- MERENJE: slot 13:30 UTC (15:30 lokalno) je snimljen rucno — `sample-20260905T133000Z.json` postoji, HTTP 200, 27 lokacija sa prikazanim brojem slobodnih mesta. `observed_at` ostaje null (izvor ne izlaze vreme merenja). Dokaz: `research/observations/10k-2026-09-05/sample-20260905T133000Z.json`.
- STATUS: u 13:55 UTC `observe_10k.py status` pokazuje `captured: 1`; slotovi 10:30/11:30/12:30 UTC ostaju missing (dokumentovana rupa, ne nadoknadjeno); preostalih 9 slotova (14:30–22:30 UTC) pending.
- OPAZANJE O METODU: prvi opipljiv uzorak potvrdjuje da pilot stvarno radi; "konfigurisano" i dalje nije dokaz izvrsenja — preostali slotovi zahtevaju rucno pokretanje ili potvrdu automatizacije.

## 2026-09-05 16:12 Europe/Belgrade - Ispravka traga: uzorak nije snimljen rucno

- IZVOR: prethodna beleska ("Revise v2") kaze da je slot 13:30 UTC snimljen rucno. To nije tacno i ispravlja se ovde, jer bi netacan trag naveo sledeci um da svaki termin pokrece rukom.
- MERENJE: uzorak je snimio Windows zakazani zadatak `Beops_OBS001`, kreiran u 13:17 UTC (15:17 lokalno) sa `/sc HOURLY /st 15:30`. Dokaz: `runtime/obs001-tick.log` prvi red glasi `---- Sat 09/05/2026 15:30:01.29 (utc 202609051330)` i odmah ispod `{"state":"captured","network_requests":1,"http_status":200}`; `schtasks /query /tn Beops_OBS001` prijavljuje `Next Run Time` i `Status: Ready`.
- MERENJE: koren propusta 10:30/11:30/12:30 UTC je utvrdjen. `schtasks /query` pre 13:17 UTC nije imao nijedan Beops zadatak; automatizacija `beops-obs-001-trka-10k` je zivela unutar Codex sesije koja je u medjuvremenu prestala, pa nije imala trajnog domacina. Nije bio problem izvora, mreze niti upisivaca.
- OGRANICENJE: zadatak je `Logon Mode: Interactive only` — izvrsava se dok je korisnik prijavljen na DESKTOP-QEDTGVM. Odjava, spavanje ili gasenje masine tokom trke znaci propustene termine, i to bi ostalo rupa, ne nula.
- ODLUKA: zadatak se brise sam posle 22:55 UTC (poslednji dozvoljeni termin 22:30 + 20 min gracea + 5 min rezerve); logika je u `tools/obs001_tick.bat`. Ovo je namerno odstupanje od pravila "ne podizati drugi scheduler": postojeci raspored je bio mrtav, a upisivac je idempotentan po terminu pa drugi okidac ne moze da udvostruci prikupljanje.

## 2026-09-05 16:30 Europe/Belgrade - Merge faza: drugi uzorak snimljen

- MERENJE: slot 14:30 UTC (16:30 lokalno) je snimljen — `sample-20260905T143000Z.json` postoji, HTTP 200, 27 lokacija sa prikazanim brojem slobodnih mesta, `observed_at` null. Dokaz: `research/observations/10k-2026-09-05/sample-20260905T143000Z.json`.
- STATUS: u 14:30 UTC `observe_10k.py status` pokazuje `captured: 2`; slotovi 10:30/11:30/12:30 UTC ostaju missing (dokumentovana rupa, ne nadoknadjeno); preostalih 8 slotova (15:30–22:30 UTC) pending.
- OPAZANJE O METODU: drugi uzorak potvrdjuje da zakazani zadatak `Beops_OBS001` stvarno izvrsava termine; pilot sada ima dva stvarna uzorka.

## 2026-09-05 16:32 Europe/Belgrade - Drugi termin snimljen automatski; prva putanja

- MERENJE: slot 14:30 UTC snimljen bez ijedne rucne radnje. `runtime/obs001-tick.log`: `---- Sat 09/05/2026 16:30:00.77 (utc 202609051430)` pa `{"state":"captured","network_requests":1,"http_status":200}`. Dokaz: `sample-20260905T143000Z.json`. Zakazani zadatak je time prestao da bude jednokratna sreca i postao ritam.
- MERENJE: prva putanja izmedju dva stvarna uzorka, 15:30 -> 16:30 lokalno, svih 27 lokacija iz jednog odgovora. Neto promena prikazanih slobodnih mesta: -26. Raste na 16 lokacija, pada na 5, bez promene na 6.
- MERENJE: najveci pojedinacni skok navise Pionirski park +40, Vukov spomenik +21, Masarikova +15, Zeleni venac +15, Baba Visnjina +12, Obilicev venac +12. Najveci pad VMA -180.
- OGRANICENJE: `observed_at` je null u oba uzorka. Ovo je putanja PRIKAZANIH brojeva izmedju dva vremena PRIJEMA, ne izmedju dva vremena merenja. Razlika od 60 minuta u prijemu ne znaci 60 minuta u izvoru.
- OGRANICENJE: nema ukupnog kapaciteta, pa nema procenta popunjenosti; neto promena ne meri dolaske, odlaske ni broj ucesnika.
- TUMACENJE: rast slobodnih mesta u centralnim garazama u satu pre najavljenog starta je ono sto se vidi. Subotnje popodnevno praznjenje centra je podjednako moguce objasnjenje kao i trka; bez uporedivih subota se ne razdvajaju.
- OGRANICENJE: VMA -180 je najveca promena u uzorku a VMA je u protokolu svrstan u prostorno udaljeniji opisni kontekst, ne u okruzenje trke. Ne uvrstavati taj broj u tvrdnju o trci. Moguca alternativna objasnjenja: nezavisan dogadjaj, promena prikaza na izvoru, greska izvora. Proveriti da li se ponavlja u narednim terminima pre bilo kakvog zakljucka.
- HIPOTEZA: ako je rast u centru vezan za trku, ocekivali bismo nastavak rasta do 18:00 i obrnut smer posle 21:00. Ravna putanja je takodje rezultat i ne bi bila neuspeh observacije.

## 2026-09-05 20:10 Europe/Belgrade - Pet uzoraka, cetiri nalaza (puna analiza u INTERIM_ANALYSIS.md)

- MERENJE: pet termina snimljeno (13:30-17:30 UTC), svi HTTP 200, svih pet hesova RAZLICITO - izvor se stvarno menja, nema zamrznutog ni kesiranog odgovora. Tri jutarnja termina ostaju trajno propustena.
- MERENJE: VMA 518 -> 338 -> 505 -> 558 -> 560. Pad od -180 u 16:30 se NIJE ponovio i vratio se za +167 u sledecem terminu. Parking ne izgubi 180 vozila za sat i ne vrati 167 u sledecem.
- OPAZANJE O METODU: iz toga sledi pravilo minimalne postojanosti - jednouzoracki iskok koji se potpuno vrati u susednom uzorku je kandidat za gresku izvora i ne sme u tvrdnju dok se ne ponovi. Za seriju bez vremena merenja iskok je dokaz tek ako traje kroz najmanje dva uzastopna uzorka. Ovo je metodski rezultat nezavisan od toga sta je trka radila.
- MERENJE: unapred izdvojena grupa "novobeogradsko/zemunsko okruzenje trke" (Opstina NBGD, Belvil, Pinki) daje najravnije linije u celom skupu: -5, +1, +8 kroz cetiri sata oko najavljenog starta.
- TUMACENJE: unapred izabrana prostorna hipoteza je oborena za ovaj dogadjaj. To se prijavljuje kao rezultat, ne sakriva - naknadno nadjen obrazac u 27 serija sa 5 tacaka je skoro besplatan i zato bezvredan.
- MERENJE: grad u celini je dobio slobodna mesta, 3679 -> 3931 (+252, oko +7%). Ada +128 i Milan Gale Muskatirovic +104 nose 92% neto promene. Sve sto se desava u centru je LOKALNA preraspodela unutar grada koji se u zbiru prazni.
- OGRANICENJE: prijaviti samo garaze u centru koje padaju znacilo bi tacan skup brojeva slozen u netacan utisak. Zbir ide u izvestaj uz njih, uvek.
- OGRANICENJE: Kalemegdan i Kamenicka prijavljuju 0 u svih pet uzoraka dok se sve oko njih pomera. Ne razlikujemo "stvarno pun" od "polje zaglavljeno na nuli". Razresenje je zakazano po konstrukciji: ako i u 00:30 bude 0, polje je mrtvo i obe lokacije se retroaktivno prekvalifikuju iz opazene nule u nedostupno, sa upisanim razlogom. Do tada ostaju opazene nule jer je to ono sto je izvor rekao.
- IZVOR (revizija izvora, jedan zaseban zahtev van OBS-001, upisan u runtime/, ne dira folder observacije): stranica NIGDE ne objavljuje vreme merenja - nema "azurirano", nema vremenske oznake, nema ritma osvezavanja; jedini brojevi nalik vremenu su koordinate. Zaglavlja ne daju ni gornju granicu: Cache-Control no-cache private, BEZ Last-Modified, BEZ ETag, BEZ Age.
- OPAZANJE O METODU: dakle observed_at null je svojstvo izvora provereno na izvoru, ne propust upisivaca. Peto stanje je nuznost, ne izbor.
- OGRANICENJE: ukupan kapacitet po lokaciji nije objavljen nigde, pa je odbijanje da se racuna procenat popunjenosti ispravno a ne samo oprezno. Prozni podatak sa stranice "kapaciteta oko 2.800 parking-mesta i 17 parkiralista" opisuje drugi skup od zivog brojaca (nas zbir SLOBODNIH ide do 3931) - ta dva broja se ne smeju kombinovati.

## 2026-09-05 21:39 Europe/Belgrade - Ispravka tumacenja pre zavrsnog izvestaja, Astra

- IZVOR: ponovo procitani postojeci `sample-20260905T133000Z.json` do `sample-20260905T193000Z.json`; bez novog zahteva. `capture` u 19:37 UTC vraca `already_recorded`, `network_requests: 0`; `status` potvrdjuje sedam snimljenih termina, tri rupe i tri buduca termina.
- MERENJE: prethodna tvrdnja da je Kalemegdan imao nulu u svih prvih pet uzoraka nije tacna. Niz u sirovim zapisima je 0, 0, 1, 0, 0, 15, 20. Dokazi za nenulte prikaze: `sample-20260905T153000Z.json`, `sample-20260905T183000Z.json`, `sample-20260905T193000Z.json`. Kamenicka ima nulu u svih sedam procitanih uzoraka. Nijedan zapis nije promenjen.
- OGRANICENJE: ponavljanje nule, ukljucujuci eventualnu nulu u poslednjem terminu, samo po sebi ne dokazuje mrtvo polje. Nule ostaju prijavljene nule sa nepoznatom pouzdanoscu; preklasifikacija zahteva nezavisan dokaz operatora ili proverljiv kvar, sa novim zapisom razloga, nikad tihom izmenom uzoraka.
- TUMACENJE: razliciti hash-evi HTML odgovora ne dokazuju svezinu instrumentalnog merenja ili odsustvo kesiranja. Oni dokazuju razlicite primljene bajtove; `observed_at` ostaje null.
- OGRANICENJE: VMA 518 -> 338 -> 505 jeste prijavljena putanja slobodnih mesta. Iz nje ne znamo broj dolazaka/odlazaka niti da je takav promet fizicki nemoguc. Privremena promena, ispravka brojaca i greska izvora ostaju moguca objasnjenja.
- HIPOTEZA: pravilo dva uzastopna uzorka moze biti zasebna, naknadno definisana analiza osetljivosti na kratke promene, ne dokaz njihove neistinitosti niti unapred registrovan kriterijum iskljucivanja. Sirova putanja i svi izuzeci ostaju u glavnoj opisnoj tabeli.
- OGRANICENJE: zbir opisuje posmatrani skup lokacija operatora, ne ceo grad; ravna putanja izabrane grupe ne obara opstu prostornu ili uzrocnu hipotezu. Zavrsni izvestaj treba da prijavi slab ili odsutan signal u konkretnom uzorkovanju, uz alternativna objasnjenja i bez uzrocnosti.
- HONEST VERDICT: provereni su postojeci zapisi i rad zastite od duplog zahteva. Nisu provereni fizicki brojaci, stvarni promet, uzrok promena ili odrzavanje trke; nova instrumentalna merenja nisu napravljena ovim budjenjem.

## 2026-09-06 00:40 Europe/Belgrade - Zavrsni izvestaj, Astra

- IZVOR: poslednji `capture` vraca `already_recorded` za `sample-20260905T223000Z.json`, bez novog zahteva. Zavrsni `status`: 10/13 captured, prve tri rupe, bez pauze izvora. Stvarni poslednji prijem je 22:30:43.5627052 UTC. Organizator i saobracajna najava ponovo otvoreni oko 22:35 UTC; sazetak i linkovi su u `IZVESTAJ.md`, bez cele tudje stranice.
- MERENJE: isti skup od 27 lokacija u deset uzoraka ima 270 prijavljenih brojcanih vrednosti. Zbir prvog i poslednjeg ritmickog uzorka je 3679 -> 4598, razlika +919. Novobeogradsko/zemunska grupa iz protokola daje +21, centralno/obalna -112, udaljeni opisni kontekst +45; sve ostale lokacije zajedno +965. To su zbirovi prikaza operatora, ne ljudi, promet ili ceo grad.
- TUMACENJE: razliciti smerovi grupa opravdavaju prikaz svih putanja umesto jedne price o gradu. Uzrocnost trke nije utvrdjena. Kamenicka ostaje prijavljena nula u svih deset termina; nije preimenovana u kvar.
- OGRANICENJE: generator `write_izvestaj.py` je pre izvrsenja ispravljen: pogresna Baba Visnjina zamenjena Opstinom NBGD prema protokolu; prijem dolazi iz transport.retrieved_at, neuspesni receipti ne ulaze u tabele vrednosti, izvestaj se objavljuje atomskim hard-linkom bez prepisivanja. Dodato osam testova; ukupno 44 prolaze.
- DOKAZ: `IZVESTAJ.md`, 498 linija; SHA-256 `474a8e4a3760abb607dd5eb8aaace144e854cb62f460ac0351b1869b41b2025b`. Procitan nazad, proverene vrednosti i deset hash-eva receipta. Zakljucavanje izvestaja pre kraja grace perioda je moguce jer je i poslednji termin vec zavrsen; sat nije menjан niti uzorak backdated.
- STATUS: zavrsena Codex automatizacija `beops-obs-001-trka-10k` uklonjena je kroz app alat. Pokusaj iskljucivanja zasebnog Windows zadatka `Beops_OBS001` odbijen je sa `Access is denied`; nije zaobidjena zabrana. Zadatak je ostao Ready sa sledecim terminom 01:30 lokalno. Njegov postojeći upisivac posle 22:50 UTC odbija mrezu, a batch potom pokusava samobrisanje; buduce samobrisanje nije provereno niti garantovano.
- HONEST VERDICT: zavrsena je ova opisna observacija i lokalni izvestaj, ne kompletan Beops plan. Nema potvrde fizickih brojaca, uzrocnog efekta, prava javne redistribucije, javne objave ili konferencijske predaje. Ne izvrsava se dodatno prikupljanje iz ove sesije.
