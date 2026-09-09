# Cula trazimo; organe, organizam i oblik projektujemo

Beops / Beograd. Istrazivacka dopuna 05.09.2026. Drugi gradovi su uporedni slucajevi, ne zamena za beogradska merenja. Nijedan novi senzor, agent ili model ovim dokumentom nije pokrenut.

## 1. Precizan recnik

| Pojam | Operativno znacenje | Primer i granica |
|---|---|---|
| Izvor | Izdavac i pristupni put podacima | Dva API-ja mogu prenositi isti instrument; nisu dva nezavisna dokaza |
| Culo | Merna sposobnost sa lokacijom, vremenom, jedinicom i ogranicenjima | Termometar meri temperaturu; vremenska prognoza je model, ne dodatni termometar |
| Organ | Proverljiva obrada jednog ili vise cula | Organ atmosfere proverava stanice, izdvaja promene i daje interval neizvesnosti |
| Organizam | Povezana celina organa, memorije, raspodele resursa i oporavka | Radi i bez jednog izvora; ne izmisli zamensko merenje kada izvor nestane |
| Otisak | Verziona projekcija onoga sto je opazeno u vremensko-prostornom prozoru | Vektor signala sa pokrivenoscu i poreklom, ne proizvoljan jedinstveni skor grada |
| Puls | Promena otiska u vremenu, pri poznatoj ucestalosti i kasnjenju | Satni PM i minutni vetar imaju razlicite satove |
| Memorija | Izvorni dokaz i aditivna istorija njegovih tumacenja | Naknadna ispravka ostavlja prethodnu verziju; indeks se moze ponovo izgraditi |
| Oblik | Nacin na koji otisak postaje opazljiv coveku | Parametar oblika ima trag do signala; nepoznato mora biti vidljivo |

Ovo je inzenjerski recnik i stvaralacka metafora, ne tvrdnja da softver ili grad imaju biolosku svest. Model je komponenta organa, ne obavezna zamena za parser, sat, bazu ili kontrolu pristupa.

## 2. Sta ucimo od drugih gradova

### Melburn: kretanje bez identiteta

Gradski sistem broji prolaske u dva smera, bez slika pojedinaca. Katalog lokacija cuva premestanje i status senzora; oznaka aktivan nije garancija trenutnog rada. [Primarni katalog](https://data.melbourne.vic.gov.au/explore/dataset/pedestrian-counting-system-sensor-locations/map/).

Poseban skup opisuje minutne vrednosti objavljivane svakih 15 minuta. Navodi da zapis nastaje pri prolasku i upozorava na duplikate pojedinih senzora u istorijskoj napomeni. To nije dokaz da je isti kvar prisutan danas. [Opis toka](https://data.melbourne.vic.gov.au/explore/dataset/pedestrian-counting-system-past-hour-counts-per-minute/information/).

**Nas transfer:** organ kretanja meri intenzitet, smer i odstupanje od istog dana/sata. Ne broji jedinstvene ljude. Minut rezolucije nije minut latencije; odsutan red nije automatski kvar niti nula bez potvrde rada. Beogradski ekvivalent nije pronadjen u ovom prolazu. Sledece traziti agregatne gradske brojace ili partnera, ne identifikaciju prolaznika.

### Barselona: vise cula u istom uredjaju

Smart Citizen razdvaja uredjaj, senzor, merenje i eksperiment; ima latest/history pristup i UTC vremenske oznake. [API dokumentacija](https://developer.smartcitizen.me/). Njihova dokumentacija obuhvata PM, gasove, svetlo/UV i zvuk uz standardne meteo velicine. [Merne sposobnosti](https://docs.smartcitizen.me/knowledge/air/). Vlaznost tla je zasebna mogucnost za posmatranje potreba za navodnjavanjem. [Tlo](https://docs.smartcitizen.me/knowledge/soil-water/moisture/).

**Nas transfer:** katalog sposobnosti mora biti odvojen od kataloga tela. Jedan uredjaj moze nositi vise cula, ali njihova medjusobna zavisnost ostaje vidljiva. Svetlo, UV i vlaznost tla prosiruju otisak, ne samo spisak temperatura. Dokumentovano postojanje hardvera ne dokazuje javnu beogradsku instalaciju ili tacnost bez kalibracije.

### Barselona / Sentilo: infrastruktura nije samo jos jedan dashboard

Sentilo nudi otvorenu platformu, API, katalog i integracije za senzore/aktuatore; izdavac povezuje dokumentaciju i barselonsku instalaciju. [Primarni projekat](https://www.sentilo.io/).

**Nas transfer:** preuzeti razdvajanje inventara, toka merenja i potrosaca. Ne uvoziti njihov ceo tehnoloski stek u Svemir bez potrebe. Otvoren kod nije dozvola za sve gradske tokove. Beops u ovoj fazi samo posmatra; automatizovano upravljanje gradskom opremom nije cilj.

### Cikago: Array of Things i zivotni vek cula

Projektna stranica izricito navodi povlacenje originalnih AoT cvorova u septembru 2021. i nasledne pravce Eclipse/Sage. Stari koncept je ukljucivao svetlo, vibracije, gasove, zvuk i lokalnu obradu slike. Ne citirati stare najave kao dokaz da svih tih zivih tokova danas ima. [Primarni status i arhitektura](https://arrayofthings.github.io/).

**Nas transfer:** senzor mora imati datum poslednjeg dokaza zivota, istoriju zamene i verziju kalibracije. Softverski obradjeno culo moze da salje samo agregat, ne sirov video. Za skalabilnost meriti i cenu odrzavanja i prestanak rada, ne samo broj cvorova.

### Sage: programski definisana cula

Sage opisuje aplikacije koje se rasporedjuju na cvorove prema naucnom zadatku. Njihov primer API upita cita izlaz obrade kretanja oblaka sa dva cikaska cvora. To je dokumentovan istorijski primer, ne proba trenutnog stanja tih cvorova. [Platforma i primer](https://sagecontinuum.org/).

**Nas transfer:** kamera okrenuta ka nebu moze hraniti organ oblacnosti, a ne nadzora ljudi. Jedno culo daje vise izvedenih signala, sa identitetom algoritma i verzijom. Mali model se pali kada donosi merljiv dobitak u okviru budzeta; primarna akvizicija i provera nastavljaju bez njega.

### Njujork / SONYC: zvucne klase i anotacije

SONYC-UST-V2 je istrazivacki skup gradskih snimaka sa vremenom/lokacijom i visestrukim zvucnim oznakama. Apstrakt opisuje ljudsko oznacavanje i verifikaciju, kao i baseline koji koristi prostorno-vremenski kontekst. [Rad, apstrakt procitan](https://arxiv.org/abs/2009.05188).

**Nas transfer:** organ zvuka mora razlikovati nivo zvuka od klase dogadjaja. Model ne daje kalibrisane decibele. Test deliti po mestu, vremenu i uredjaju da ne nauci adresu umesto zvuka. Javna verzija ne treba transkripte prolaznickih razgovora. Aktivni javni beogradski audio tok nije potvrdjen; ovaj dataset je materijal za evaluaciju, ne zivo culo Beograda.

### Helsinki: uporediti razlicite instrumente za isti fenomen

Pronadjeni su zvanicni katalozi saobracajnih brojanja i pilot masinskog vida iz proleca 2023. Jedno otvaranje pilot stranice uspelo je, ponovna otvaranja i API katalog vracali su 403. Zato tacnu aktuelnu semu, kadencu i brojeve odstupanja ostavljamo za sledecu direktnu proveru. [Pilot](https://hri.fi/data/en/dataset/datankeruukokeilu-helsingissa-liikennelaskenta-konenaon-avulla), [statisticki API katalog](https://hri.fi/data/en/dataset/helsingin-liikennemittausten-tilastorajapinta).

**Nas transfer:** poredjenje kamere i nezavisnog brojaca na istom prostoru korisnije je od lepog demo videa. Istorijski pilot nije aktivno culo. Razlicite geometrije brojanja prvo poravnati, pa tek onda racunati neslaganje.

## 3. Dodatna cula za istrazivanje u Beogradu

Sledece su kandidati izvedeni iz primera i naseg zadatka, NE tvrdnje o lokalnoj dostupnosti. Prvih nekoliko se moze povezati sa vec pronadjenim izvorima; ostala cekaju javni tok, dozvolu ili sopstveni instrument.

| Kandidat | Sta bi merio / organ | Put pristupa i trenutna granica | Merilo korisnosti |
|---|---|---|---|
| Svetlost, UV i solarno zracenje | Promenu dnevnog osvetljenja / atmosfera | Proveriti meteo kanale i Smart Citizen lokalne uredjaje; satelitska procena nije lokalni radiometar | Greska prema nezavisnom instrumentu; koliko pomaze tumacenju temperaturne promene |
| Oblacnost i kretanje oblaka | Udeo neba i kretanje / atmosfera | Odobrena sky-kamera ili sopstvena, Sage kao metod; lokalni tok nije potvrdjen | IoU oznacenih oblaka, greska kratkorocne prognoze prema persistence baseline-u |
| Vlaznost tla | Lokalni vodni deficit / zelenilo | Javni partnerski ili sopstveni senzor; ne procena iz naslova vesti | Slaganje sa referentnim uzorkom, stabilnost po tipu tla |
| Vegetaciona promena | Sporije stanje zelenila / sezonska memorija | Sentinel-2 kandidat vec u registru; oblaci i dani cekanja ostaju vidljivi | Ponovljivost indeksa i provera poznatih promena; ne dijagnoza pojedinacnog stabla |
| Temperatura povrsine | Toplotno opterecenje povrsina / mikroklima | Traziti termalne satelitske proizvode, zemaljska referenca potrebna | Razlika od temperature vazduha eksplicitna; prostorna validacija |
| Vlaznost kolovoza i stajaca voda | Lokalni odgovor na kisu / odvodnjavanje | Odobrena kamera ili senzor; razvojni pravac, ne postojeci feed | Precision/recall prema oznacenim epizodama, pogresni alarmi po danu |
| Pesacki i biciklisticki prolazi | Agregatni protok / kretanje | Traziti otvorene brojace; Melburn/Helsinki su obrazac | MAE brojanja po prozoru, nedostajuca mesta i duplikati |
| Parking popunjenost | Ritam zauzeca / kretanje | Parking servis kandidat; TLS problem nije resen za kolektor | Sveze/celovite vrednosti, promene kapaciteta i nepoklapanje ukupnih mesta |
| Ambijentalne zvucne klase | Udeo transporta, radova, kise / zvuk | SONYC/YAMNet kao evaluacija; lokalni mikrofon i uslovi tek treba | Macro-F1, kalibracija verovatnoca, nova lokacija i novi mikrofon |
| Vibracije tla | Kontinuirano podrhtavanje / tlo | SJ/BEO/AVAS metapodaci pronadjeni; poslednji waveform nije preuzet | Dostupnost kanala, instrument response, spektar; ne automatska atribucija uzroka |
| Hemija vode | pH, provodljivost, rastvoreni kiseonik / voda | Smart Citizen pokazuje tehnicki put; lokalni otvoreni tok nije nadjen | Kalibracija i stabilnost sonde; ne zakljucak da je voda bezbedna za pice |
| Punjenje i praznjenje kontejnera | Tok materijala / infrastruktura | Traziti zvanicne agregatne podatke ili partnera, nema potvrdjenog BG feeda | Tacnost vremena praznjenja i obuhvat, bez pracenja domacinstava |

Ne pretvarati ekonomiju, vesti i arhivu u fizicke senzore. Oni daju dokumentovani institucionalni ili drustveni trag. Radno vreme u registru nije dokaz da radnja sada radi; najava radova nije dokaz da je iskop zapoceo.

## 4. Organi koje mi gradimo

1. **Prijem i identitet:** jedan kolektor po izvoru, idempotentni upis, poznat izdavac/instrument, ogranicen saobracaj. Adapter ne sme sam sebi da potvrdi nezavisnost podataka.
2. **Kvalitet i vreme:** jedinice, prostor, observed_at/published_at/received_at, missing/stale/revised. Ako observed_at nije poznat, ostaje null sa razlogom; vreme preuzimanja ga ne zamenjuje.
3. **Atmosfera, voda, kretanje, zvuk i tlo:** odvojeni domeni i native cadence. Svaki organ mora dati koristan deterministicki baseline pre modela.
4. **Povezivanje:** kandidati istog dogadjaja sa tragom porekla i mogucim alternativama. Zajednicka promena kise, zvuka i saobracaja nije sama dokaz uzrocnosti.
5. **Memorija i recnik:** izvorni dokaz, revizije, verzije modela i pojmovi kao indeks. Sirovi audio/video cuva se samo u dozvoljenom i opravdanom obimu; provenance ne zahteva masovno zadrzavanje licnih podataka.
6. **Raspodela i oporavak:** task budget, zakup, backpressure, replay i replikacija. Obrada je tipicno at-least-once sa idempotentnim efektima; ne obecavati magican exactly-once preko svih uredjaja.
7. **Izraz:** jedan ili vise oblika istog otiska. Svaki pomak, boja, rec ili ton ima dokumentovano mapiranje i vidljivo stanje nepoznatog.
8. **Integritet:** izvori su nepoverljivi podaci, ne instrukcije za Svemir. HTML/PDF/vest ne pokrecu komande; parsiranje, sandbox i izlazna sema razdvajaju opazanje od izvrsavanja.

Organizam je ugovor izmedju tih organa, ne centralni LLM koji sve tumaci i drzi u svom kontekstu. Prvo trajni tok i mali proverljivi izlazi; model dobija relevantan prozor i trag, ne celu istoriju svakog grada.

## 5. Tri uporediva organizma, ne tri proizvoljna skora

- **O0: osnovni organizam.** Isti validni izvori, pravila i statistika, bez modela. Meri promene, pokrivenost i kvarove.
- **O1: specijalizovani organizam.** Isti ulazi, jedan mali model za konkretan zadatak. Meriti dodatnu korist i cenu u odnosu na O0.
- **O2: povezani organizam.** Dodati drugi domen i eksplicitno povezivanje dokaza; model i obim racunanja ograniciti istim budzetom gde je moguce.

Odvojiti dve ose eksperimenta: promena izvora i promena obrade. Inace nije jasno da li je rezultat bolji zbog modela ili zato sto je dobio vise podataka. Vise pulseva najpre ostaju vise imenovanih vektora, a ne sabiranje decibela, cena i PM u jedan broj.

Korisnost: detekcija oznacenih promena (precision/recall, latencija), prognoza (MAE i pokrivenost intervala), utemeljenost tekstualnih tvrdnji, prostorna pokrivenost, dostupnost posle kvara, CPU/RAM/mreza i trosak po validnom izlazu. Wh meriti samo uz odgovarajucu telemetriju, ne proglasavati CPU vreme za energiju.

Skalabilnost: replay 1x/5x/10x bez bombardovanja javnih izvora; vise gradskih celija; vise heterogenih izvora; spor ili nedostupan uredjaj; dodavanje novog organa; mesecna istorija. Pokazati gde dobitak prestaje da opravdava cenu.

## 6. Dodatna literatura i dubina provere

| Rad / izvor | Dokle provereno | Sledece citanje i transfer |
|---|---|---|
| [Optimizing Cloud Motion Estimation on the Edge with Phase Correlation and Optical Flow](https://doi.org/10.5194/amt-16-1195-2023), 2023 | Otvorena stranica izdavaca i procitan apstrakt; nije ceo rad | Uporediti klasicnu korelaciju/optical flow sa malim modelom, cenu i uslove snimanja; rad pokazuje vaznost razmaka izmedju snimaka, ne samo rezolucije |
| [Let's Unleash the Network Judgment](https://doi.org/10.1175/AIES-D-22-0063.1) | Bibliografija Sage; DOI pristup odbijen 403 | Self-supervised obradjivanje neba; proveriti prenos na lokalnu kameru |
| [Acoustic Fingerprints in Nature](https://doi.org/10.1016/j.ecoinf.2024.102823) | Bibliografija Sage, Ecological Informatics 83; DOI vratio 429 | Ekosistemski zvuk kao prosirenje, bez tvrdnje da je metod vec ispitan u gradu |
| Goal-driven Scheduling Model in Edge Computing for Smart City Applications | Naslov, autori i casopis u [primarnoj bibliografiji](https://sagecontinuum.org/publications) | Procitati puni rad pre odluke o rasporedjivanju modela |
| SONYC-UST-V2 | Procitan apstrakt, ne pun rad u ovoj dopuni | Anotacije, multilabel zadatak i prostorno-vremenski holdout |

Ovi primeri dopunjuju, ne zamenjuju novije radove 2025-2026 i model kartice u [MODELI_I_LITERATURA.md](../03-models/MODELI_I_LITERATURA.md). Stariji operativni sistemi su korisni upravo zato sto pokazuju odrzavanje i prestanak rada, sto novi preprint jos ne moze.

## Honest verdict

Proverene su navedene primarne stranice i razlike izmedju arhive, dokumentacije i dostupnog toka. Lokalni rezultati su u zasebnim [probama](../evidence/). Nisu preuzeti aktuelni podaci svih uporednih gradova, niti je potvrdjen lokalni izvor za svako novo culo. Nema izvrsene inferencije, nove instalacije, javnog audio/video snimanja ili zavrsenog kontrolisanog eksperimenta. Arhitektura organa i O0/O1/O2 su nasi predlozi za merenje, ne nalazi iz literature.
