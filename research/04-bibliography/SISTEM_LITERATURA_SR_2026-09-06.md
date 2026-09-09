Status: working — završena ograničena istraživačka beleška; pregledano za ovu radnu sintezu; predlozi za razgovor, bez rukopisa i bez implementacije
Date: 2026-09-06
Author: BEOPS istraživački saradnik /root/procurement
Jezik: srpska ekavica, latinica; eventualni dvojezični rad je odložen
Protokol: [ROOM_DOOR.md](D:/Svemir/docs/ROOM_DOOR.md), pročitan u ovoj smeni. Ovaj zadatak prati izričito nativno zaduženje koordinatora; završetak dosijea predaje nalaz na pregled.

# Šta treba dopuniti između opažanja grada i planske odluke

Najveća praznina je prelaz sa načela na proverljivu praksu. Postojeći okvir već pominje granice, neizvesnost, ljude, poreklo podataka i održavanje. Potrebno je odrediti kako se ti zahtevi proveravaju za konkretno pitanje, model i odluku. Sedam novih radova ispod pomaže da se taj prelaz razradi. Nijedan nije dokaz da BEOPS već ima operativni gradski blizanac ili potvrđen planski učinak.

Pregledani su [sistemski nacrt](../06-paper/URBAN_INTELLIGENCE_SYSTEM_OUTLINE_2026-09-06.md), [predmet razgovora](../06-paper/PRE_PAPER_URBAN_INTELLIGENCE_2026-09-06.md), [modeli i literatura](../03-models/MODELI_I_LITERATURA.md), [šira bibliografija](BIBLIOGRAPHY_2026-09-05.md) i relevantni delovi [teorijske dopune](LITERATURE_THEORY_METHODS_2026-09-06.md). Bibliografija je pregledana po naslovima i identifikatorima; nisu svi njeni citirani radovi ponovo čitani. Ciljana pretraga svih Markdown beležaka u 03-models, 04-bibliography i 06-paper nije našla sedam dole navedenih naslova/identifikatora. To je provera unutar tih mapa, ne tvrdnja o svim fajlovima projekta.

| Već pokriveno | Dopuna koju predlažem | Mesto u razgovoru |
|---|---|---|
| Izvor, opažanje, proizvod, model i odluka imaju različite identitete | Za svaki model zabeležiti domen važenja, pretpostavke, ulaze, izlaze, zavisnosti i odgovornu osobu/instituciju | Pre povezivanja modela |
| Razmere i vremenske oznake su važni | Odvojiti razmeru merenja, izloženosti, modela i odluke; unapred odrediti vremenski prozor uticaja | Uz izbor mesta i perioda |
| Predlog evaluacije i poređenja sa početnim metodom postoji | Razdvojiti interpolaciju od prenosa na novu oblast/sezonu; odgovarajuće odvojiti podatke za proveru | Pre računanja kvaliteta |
| Ljudsko učešće i korisnost su važni | Pratiti ko može da ospori pretpostavku i šta se promenilo nakon primedbe | Uz poređenje alternativa |
| Upravljanje i održavanje su pomenuti | Definisati ko prepoznaje zastareo ulaz, ko obustavlja rezultat i kako se povlači model | Uz životni ciklus sistema |
| Nepotpuni podaci su problem kvaliteta | Razlikovati fizičko odsustvo pojave, odsustvo merenja, odsustvo objave i naše odsustvo pristupa | U evidenciji praznina |

Ne dupliram radove Geertman/Stillwell 2020 i Pelzer 2017 iz druge istraživačke grane, niti Rittel/Webber 1973, Kennedy 2011 i IPCC 2022 koje obrađuje koordinator. Postojeći Herrenberg, Cirih, Bettencourt, Batty, Kitchin, James i Data Cascades ostaju prethodna građa, bez novog brojanja.

## Sedam strateških radova

### 1. Tip digitalnog blizanca i stvarno učešće

Frida Thuresson, Kevin Lau i Agatino Rizzo (2026). *Using digital twins for co-designing cities: a review of digital participatory approaches*. European Planning Studies, unapred objavljen članak, 13. maj 2026. [DOI: 10.1080/09654313.2026.2668560](https://doi.org/10.1080/09654313.2026.2668560).

**Čitanje:** pun tekst iz [univerzitetskog repozitorijuma](https://ltu.diva-portal.org/smash/get/diva2:2066442/FULLTEXT01.pdf), ciljano metodologija, tabele/kategorije, rasprava i zaključak. Izdavačka stranica neposredno je vratila 403. Pravo za članak: CC BY 4.0 potvrđeno u [zapisu repozitorijuma](https://ltu.diva-portal.org/smash/record.jsf?pid=diva2:2066442).

**Nalaz:** pregled obuhvata 26 radova; autori navode ažuriranje pretrage januara 2025. Datum objavljivanja nije datum kraja pretrage. Razlikuju analitičke, vizuelizacione, interaktivno participativne i operativne blizance. Učešće često ostaje u pilotima i prototipovima; pregled ne meri objedinjeni uzročni efekat na odluke. Izostavlja sivu literaturu i neengleske radove.

**Naša dopuna:** klasifikovati ulogu i zrelost svakog predloga zasebno; za učešće zahtevati trag od primedbe do izmene/obrazloženog odbijanja. Ne preuzimati njihovu tipologiju kao već empirijski validiranu procenu uspeha.

### 2. Više modela, raspodeljeno vlasništvo i granica rada uživo

Rico H. Herzog, Till Degkwitz i Trivik Verma (2025). *The Urban Model Platform: A Public Backbone for Modeling and Simulation in Urban Digital Twins*. Preprint, arXiv:2506.10964v3, 20. jun 2025; v1: 12. jun. [DOI: 10.48550/arXiv.2506.10964](https://doi.org/10.48550/arXiv.2506.10964).

**Čitanje:** [autorski pun tekst](https://arxiv.org/html/2506.10964v3), odeljci 3–6 i zaključak; CC BY 4.0. Status recenzirane publikacije nije potvrđen.

**Nalaz:** istraživanje kroz projektovanje u Hamburgu 2022–početak 2025 oslanja se na 12 zapisnika sastanaka,6 intervjua, 2 radionička zapisnika, izveštaje i kod. Autori prijavljuju da grad upravlja platformom od početka 2025, uz tek započeto uključivanje sektorskih modela. Potvrda prihvatanja platforme nije evaluacija planskih ishoda. Odeljak 6 izričito ograničava tadašnji backend: kontinuirana simulacija bliska realnom vremenu sa živim ulazima još nije podržana.

**Naša dopuna:** odvojiti dostupnost platforme, interoperabilnost, numeričku ispravnost spajanja i rad uživo. Modeli mogu imati različite paradigme i razmere; za svaku vezu treba zaseban ugovor ulaza/izlaza i propagacije neizvesnosti. Ovaj izvor ne dokazuje da je fizičko/statističko hibridno spajanje samo po sebi tačno.

### 3. Evaluirana saradnja čoveka i AI ima određenu jedinicu dokaza

Yu Zheng, Yuming Lin, Liang Zhao, Tinghai Wu, Depeng Jin i Yong Li (2023). *Spatial planning of urban communities via deep reinforcement learning*. Nature Computational Science 3, 748–762; objavljeno 11. septembra 2023. [DOI: 10.1038/s43588-023-00503-5](https://doi.org/10.1038/s43588-023-00503-5).

**Čitanje:** [institucijski autorski PDF](https://fi.ee.tsinghua.edu.cn/public/publications/77681512-6436-11ee-84fe-0242ac120002.pdf), rezultati/Tabela 1/Slika 4, metod formulacije, rasprava i dostupnost podataka; dopunski eksperimenti i kod nisu reprodukovani.

**Nalaz:** sintetički slučaj i geometrije dva pekinška naselja, Huilongguan i Dahongmen; poređenje sa 8 projektanata i slepi izbor 100 projektanata postdiplomskog nivoa. Meri kvalitet nacrta i radni zadatak. Statičke metrike, izostavljena brojna praktična pravila i politička pitanja ograničavaju prenos. Nema potvrde da su predlozi izgrađeni ili popravili život stanovnika.

**Naša dopuna:** razdvojiti uspeh modela, uspeh zajedničkog zadatka i stvarni učinak odluke. Dokumentovati pretpostavljene ciljeve i ograničenja, ne samo ukupni skor.

**Podaci:** članak upućuje na [Zenodo DOI 8175420](https://doi.org/10.5281/zenodo.8175420) i [autorski GitHub](https://github.com/tsinghua-fib-lab/DRL-urban-planning). Zenodo otvaranje nije uspelo; konkretne licence članaka/koda/podataka ovde nisu potvrđene. Ništa nije preuzeto ili izvršeno.

### 4. Validacija mora odgovarati budućem korišćenju

David R. Roberts, Volker Bahn, Simone Ciuti, Mark S. Boyce, Jane Elith, Gurutzeta Guillera-Arroita, Severin Hauenstein, José J. Lahoz-Monfort, Boris Schröder, Wilfried Thuiller, David I. Warton, Brendan A. Wintle, Florian Hartig i Carsten F. Dormann (2017). *Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure*. Ecography 40(8), 913–929; prvi onlajn datum8. decembar 2016. [DOI: 10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881).

**Čitanje:** [izdavački pun tekst](https://nsojournals.onlinelibrary.wiley.com/doi/full/10.1111/ecog.02881), koncept, Tabela 1, odabrani simulacioni rezultati i zaključak; bez reprodukcije dodataka.

**Nalaz:** slučajna podela zavisnih opažanja može potceniti grešku. Blokiranje mora odgovarati predikcionom cilju; može namerno proveravati ekstrapolaciju, ali i preceniti grešku interpolacije. Ekološki primeri nisu empirijska validacija Beograda.

**Naša dopuna:** unapred napisati „predviđamo novu lokaciju/sezonu” ili „popunjavamo unutar poznatog domena”; tek zatim birati blokove i početni metod poređenja.

**Podaci:** [Dryad 10.5061/dryad.737gk](https://datadryad.org/dataset/doi:10.5061/dryad.737gk) potvrđuje zapis od 8. decembra 2016 i dodatak sa R kodom/podacima; pregledani su metapodaci, bez ZIP preuzimanja. Članak je besplatno dostupan; posebna licenca ovog članka i skupa nije potvrđena u pročitanom tekstu.

### 5. Granica naselja nije automatski granica relevantnog uticaja

Mei-Po Kwan (2012). *The Uncertain Geographic Context Problem*. Annals of the Association of American Geographers 102(5), 958–968. [DOI: 10.1080/00045608.2012.687349](https://doi.org/10.1080/00045608.2012.687349).

**Čitanje:** originalni članak u [kopiji na sajtu geografskog društva](https://www.kgeography.or.kr/media/11/fixture/data/bbs/file_data/20130319-1.pdf), prostorni/vremenski kontekst, Tabela 1 i ublažavanje grešaka. Naslov/autorka/godina/strane potvrđeni u članku. DOI je potvrđen bibliografskim rezultatom, ali izdavačka stranica i pokušaj Crossref razrešenja nisu bili dostupni; nije odglumljena neposredna primarna DOI provera. [Autorski PDF](https://www.meipokwan.org/Paper/Kwan_UGCoP_2012.pdf) je pronađen, ali alat nije uspeo da ga otvori.

**Nalaz:** problem relevantnog geografskog konteksta razlikuje se od MAUP. Pogrešno mesto, trajanje ili kašnjenje uticaja mogu sakriti ili prividno proizvesti povezanost; najbolje uklapanje modela ne potvrđuje izbor konteksta.

**Naša dopuna:** za svako pitanje posebno obrazložiti fizički/planski prostorni obuhvat i vremenski prozor; menjati ih u proveri osetljivosti. Ovo ne opravdava prikupljanje pojedinačnih putanja. Prava: © 2012 Association of American Geographers; otvorena licenca nije utvrđena. Nov lokalni skup nije pronađen.

### 6. Vidljivost podacima može istovremeno pomoći i naškoditi

Linnet Taylor (2017). *What is data justice? The case for connecting digital rights and freedoms globally*. Big Data & Society 4(2), 1–14; objavljeno 1. novembra 2017. [DOI: 10.1177/2053951717736335](https://doi.org/10.1177/2053951717736335).

**Čitanje:** [izdavački pun tekst](https://journals.sagepub.com/doi/10.1177/2053951717736335), argument i odeljak predloženog okvira, Slika 1, prava. CC BY-NC-ND 4.0; ova beleška je samostalna analiza, ne prevod članka.

**Nalaz:** konceptualni okvir povezuje vidljivost/nevidljivost, mogućnost angažovanja/odbijanja tehnologije i borbu protiv diskriminacije. Koristi međunarodne primere; ne predstavlja evaluaciju beogradskog sistema. Privatnost ne iscrpljuje pitanja predstavljanja, koristi i moći.

**Naša dopuna:** za plansko pitanje voditi matricu „ko je predstavljen, ko odlučuje, ko ima korist, ko može da ospori”. Manjak zapisa o nekoj grupi nije dokaz da njene potrebe ne postoje; više podataka nije automatski pravednije. Razlog nedostupnosti i pravo na nevidljivost ostaju odvojena pitanja. Ovde nije pronađen novi lokalni skup podataka.

### 7. Održavanje uključuje zavisnosti i promenu sveta

D. Sculley, Gary Holt, Daniel Golovin, Eugene Davydov, Todd Phillips, Dietmar Ebner, Vinay Chaudhary, Michael Young, Jean-François Crespo i Dan Dennison (2015). *Hidden Technical Debt in Machine Learning Systems*. Advances in Neural Information Processing Systems 28. [Primarni zapis zbornika](https://papers.neurips.cc/paper_files/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html); DOI nije naveden/proveren.

**Čitanje:** [pun tekst zbornika](https://proceedings.neurips.cc/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf), odeljci 2–4 i 7–9, Slika 1. Otvoreno čitljivo; posebna licenca nije potvrđena.

**Nalaz:** industrijska iskustvena analiza, ne gradski eksperiment. Podaci i modeli stvaraju skrivene zavisnosti, povratne sprege i trošak održavanja; poboljšanje komponente ne garantuje poboljšanje celine. Promene sveta traže posmatranje ponašanja posle objave, uz testove softvera.

**Naša dopuna:** registar potrošača svakog izlaza, verzije, plan obustave/povlačenja i beleženje promene okruženja. Za gradski sistem to je prenos metodološke pouke, ne potvrđen lokalni učinak. Ne koristiti metaforu tehničkog duga kao već izmerenu finansijsku veličinu.

## Jedna ispravka postojeće građe, bez novog brojanja

Stavka C15 šire bibliografije tvrdi da konformalna predikcija pomaže kada nema referentne istine za empirijsku kalibraciju i time rešava deo evaluacionog jaza. To treba suziti. Angelopoulos i Bates, *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*, arXiv:2107.07511v6 (7. decembar 2022; prvobitno 2021), u [punom tekstu](https://arxiv.org/html/2107.07511v6) § 1 koriste izdvojene parove ulaza i poznatih ishoda. Dodatak D navodi razmenljivost; § 4.6 pokazuje gubitak granice pokrivenosti pri promeni raspodele. Ciljano su pročitani ti delovi, ne ceo matematički dodatak.

Predlog zamene: „Konformalna predikcija je kandidat za intervale kada postoje odgovarajući kalibracioni podaci i opravdani uslovi zavisnosti/prenosa. Osnovna garancija je marginalna pokrivenost; ne potvrđuje istinitost svakog gradskog iskaza niti uzročni učinak intervencije. Prostorno-vremenski prenos zahteva posebnu proveru.” Metapodaci verzije sa [arXiv zapisa](https://arxiv.org/abs/2107.07511) imaju prednost nad automatskim datumom koji HTML prikazuje u telu. C11/C12 takođe traže dokaz uporedivosti izvora pre izbora algoritma; ovde nisu ponovo proveravani i ne donosi se konačna presuda o tim metodama.

## Praktična dopuna strukture za razgovor

Sledeće su naši predlozi, izvedeni za BEOPS; nisu tvrdnje da ih postojeća arhitektura već sprovodi.

1. **Kartica planskog pitanja.** Šta treba razumeti, za koga, na kom području i horizontu; koji rezultat bi promenio odluku, a koji ne bi.
2. **Kartica modela i njegovih veza.** Namena, neprikladne upotrebe, verzija, pretpostavke, prostorna/vremenska podrška, ulazne zavisnosti, kalibracioni period, odgovornost i datum sledeće provere. Zajednički format ne garantuje zajedničko značenje ili numeričku kompatibilnost.
3. **Četiri odvojene provere.** Da li obrada radi kako je napisana; da li rezultat odgovara nezavisnim opažanjima; da li ljudi uz njega bolje obavljaju definisan zadatak; da li sprovedena odluka daje očekivan ishod. Za poslednju proveru potrebni su poseban dizajn i period posmatranja.
4. **Evidencija praznina.** Posebne oznake za „nije opaženo”, „nije mereno”, „nije objavljeno”, „nije dostupno nama”, „zastarelo”, „odbačeno proverom” i „izvedeno/procenjeno”. Uz svaku oznaku čuvati osnov, datum i nepoznanice. Prazan portal nije nulta pojava; odsustvo dokaza nije automatski dokaz odsustva.
5. **Pravo na osporavanje.** Uz alternative prikazati pretpostavke, raspodelu koristi/tereta i objašnjenje postupanja sa primedbama. Za učešće bez digitalnih alata predvideti ravnopravan način da se doprinos uzme u obzir.
6. **Životni ciklus.** Ko održava ulaz i model, koje kašnjenje je prihvatljivo za konkretno pitanje, kada rezultat postaje zastareo, kako se privremeno obustavlja i ko odlučuje o povlačenju. Beležiti institucionalnu i kadrovsku zavisnost uz tehničku.

Za prvi razgovor dovoljno je proći kroz ove kartice na jednom već odabranom pitanju. To bi pokazalo gde zbirka već pruža oslonac, a gde je potreban novi eksperiment. Ne predlaže se sada izrada celog sistema, rukopisa ili interfejsa.

## Trag pretrage i granice

[zajednički dnevnik pretrage](../_trail/PRED_RAD_SR_WAVE7_SEARCH.json) sadrži 16 doslovno izvršenih upita, datum, odluke o uključivanju i pristupne neuspehe. Upiti su bili na engleskom i srpskom, latinicom i ćirilicom. Regionalni rezultati bili su pretežno programi/projektni pozivi ili komercijalna predstavljanja, bez odgovarajućeg dokaza evaluirane gradske primene za ovaj izbor.

Ovo je svrhovit, ograničen izbor, ne sistematski iscrpan pregled. Sedam novih zapisa ne treba sabirati sa ranijim zbirkama bez globalne deduplikacije. Dubina čitanja označava ciljano čitanje punih primarnih tekstova; ne znači reprodukciju koda, numeričku proveru svih formula ili pregled piksela svih slika. Nije preuzet sirov skup, zvuk, individualna putanja ni drugi lični zapis. Nema novih poruka institucijama, registracionih brojeva izvora ili izmena na disku D.

## Koordinatorska dopuna provere identiteta W7-05

Posle agentovog zapisa, indeksirani [originalni izdavački metapodaci](https://www.tandfonline.com/doi/abs/10.1080/00045608.2012.687349) potvrdili su DOI, naslov, autorku, 102(5), 958–968 i datum prve onlajn objave 22.06.2012. Ranije ograničenje neposrednog DOI otvaranja ostaje istorijski tačno; bibliografski identitet sada je dodatno potkrepljen primarnim izdavačkim zapisom. Ova dopuna ne menja obim pročitanog punog članka.
