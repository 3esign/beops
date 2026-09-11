# Beops: mali modeli, literatura i sta tacno preuzimamo

Naknadna razrada: plan istrazivanja (private working record), [24-modelski audit i provajderi](KATALOG_MODELA_I_PROVAJDERA_2026-09-05.md), banka keyword upita (private working record). Donji tekst ostaje pocetni deset-modelski pregled, ne poslednji kompletan status.

05.09.2026. Nema instaliranja tezina, benchmark rezultata ili automatskog ucitavanja modela u ovom prolazu.
Deset repozitorijuma provereno direktnim HF API pozivima; revizije i deklaracije su u `evidence/models-20260905T023712000220Z.json`.

## 1. Model se bira prema pitanju, ne prema popularnosti

Prvo pitanje za svaki model: koji ulaz ZAISTA imamo i kojim nezavisnim dokazom merimo izlaz? Broj parametara je orijentacija, ne garancija brzine ili radne memorije. Ne pretpostavljamo da svi checkpoint-i rade kroz Ollama: encoderi, akusticki modeli i seizmicki modeli imaju druge runtimes. Jezgro ostaje bez novih zavisnosti; eventualni strucni runtime ide izolovano, tek posle izbora i odobrene instalacije.

| Model / izvor | Proverena velicina ili status | Uloga u zivom otisku | Test i ogranicenje |
|---|---|---|---|
| [Chronos-Bolt Tiny](https://huggingface.co/amazon/chronos-bolt-tiny) | HF tenzori oko 8,65M; autor zaokruzuje na 9M | Kratkorocna kvantilna prognoza jedne vremenske serije; odstupanje od ocekivanog ritma | Rolling-origin test prema persistence i sezonskom baseline-u; nije meteoroloski fizicki model niti dokazana detekcija anomalija |
| [Chronos-Bolt Mini](https://huggingface.co/amazon/chronos-bolt-mini) | oko 21,24M | Kontrolisana veca varijanta za isti zadatak | Zadrzati samo ako napredak opravdava trosak; covariates zahtevaju konkretan podrzan pipeline, nisu proizvoljan dodatak osnovnom pozivu |
| [multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) | oko 117,65M; sr deklarisan | Povezivanje novog zapisa/objave sa relevantnim mestom, dogadjajem i istorijom | Recall@k/nDCG prema BM25; posebno cirilica/latinica, padezi i nepoznata imena |
| [BGE-M3](https://huggingface.co/BAAI/bge-m3) | identitet/revizija potvrđeni; API nije vratio parameter total | Veci retrieval komparator za istu bazu | Nije podrazumevani izbor; izmeriti radnu memoriju i kvalitet na istim upitima |
| [BERTic NER](https://huggingface.co/classla/bcms-bertic-ner) | oko 110,03M; BCMS jezici deklarisani | Izdvajanje imena mesta/organizacija iz objava | Task-specific NER checkpoint, ne samo pretrenirani backbone; njegove klase ne resavaju automatski datume, ulice i intervale |
| [GLiNER multilingual v2.1](https://huggingface.co/urchade/gliner_multi-v2.1) | API tenzori oko 288,95M; README tabela navodi 209M | Fleksibilno izdvajanje dogovorenih tipova entiteta | Neslaganje velicine sacuvano, nije izravnato; srpsku tacnost dokazati lokalno; labels ne garantuju pravilan geokod |
| [SmolVLM 256M](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct) | oko 256,48M; en deklarisan | Kratak opis dozvoljenog kadra i kvalitativno stanje | Odvojeno dan/noc/kisa/zaklon; ne koristiti kao precizan brojac ili senzor zagadjenja |
| [SegFormer B0 ADE](https://huggingface.co/nvidia/segformer-b0-finetuned-ade-512-512) | oko 3,75M; licence=other u metapodacima | Segmentacija vidljive scene: udeo klasa u fiksnom kadru | mIoU na oznacenim slikama; ADE checkpoint nije automatski prilagodjen satellitskim kanalima ili Beograd kamerama |
| [Whisper Tiny](https://huggingface.co/openai/whisper-tiny) | oko 37,76M; sr deklarisan | Samo dozvoljeni govorni dokumenti/intervjui ako zatrebaju | WER na lokalnom uzorku; NIJE osnovni model zvucnog pejzaza i nije potreban za preslusavanje prolaznika |
| [LFM2.5 1.2B GGUF](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF) | identitet potvrđen; ranije lokalno nadjen Q4 model | Strukturisani izbor vec postojecih dokaza ili kratka sinteza | Nema sr u deklarisanim jezicima; izvorne vrednosti vraca backend, ne modelova slobodna procena |

### Van Hugging Face-a, ali relevantno

- [Google YAMNet](https://www.tensorflow.org/hub/tutorials/yamnet): MobileNet-v1 akusticki model sa 521 AudioSet klasom i ulazom mono 16 kHz. Kandidat za lokalnu klasifikaciju zvuka; ne pretvara amplitudu nepoznatog mikrofona u kalibrisani dB(A). Ne preuzimati proizvoljan reupload kada postoji autorski izvor.
- [DCASE 2025](https://arxiv.org/abs/2505.01747): izvor malih akustickih arhitektura i testova otpornosti na drugi uredjaj. Potrebno izabrati konkretan javni checkpoint, izmeriti footprint i proveriti njegovu licencu.
- [SeisBench](https://arxiv.org/abs/2111.00786): zajednicki pristup seizmickim datasetovima/modelima. PhaseNet/EQTransformer porodice su kandidati TEK kad imamo poznate waveform kanale i instrument metadata; checkpoint nije potvrda seizmickog dogadjaja bez strucnog postupka.
- Tesseract sa srpskim jezikom je kandidat za skenirane dokumente. Jos nije auditovan lokalni install/checkpoint; tekstualni PDF parser ostaje prva putanja. OCR je pomocno culo arhive, ne zamena za zive stanice.

Prioritet isprobavanja: deterministicki kvalitet podataka -> Chronos Tiny za numericki ritam -> E5-small za povezivanje -> BERTic/GLiNER za objave. Audio/vid/tlo sledi raspolozivost konkretnog izvora, ne obrnuto. Veci model je kontrolni komparator, ne stalno budan proces.

## 2. Literatura po temama

Ovo je ciljani pregled, ne iscrpan sistematski review. "Apstrakt" znaci da identitet i opis rada jesu provereni, ali detaljna metodologija/rezultati jos nisu reprodukovani. Svi dole navedeni radovi vode na primarni izdavacki ili autorski izvor. Svaka preporuka za Beops je nasa interpretacija, ne rezultat tih autora na Beogradu.

### L01. Agentic urban digital twins

[Towards Agentic Urban Digital Twins (AUDiTs), 2026](https://link.springer.com/article/10.1007/s44212-025-00099-3). Procitana stranica i arhitektonski delovi. Perspektivni rad pomaze da se odvoje prikupljanje, modeli, orkestracija i interakcija. Ne dokazuje da je agent potreban u svakom kolektoru, niti da je Beops prvi takav sistem. U rad preneti poređenje arhitektonskih odgovornosti.

### L02. Vise vremenskih skala urbanog opažanja

[UrbanWell, 2026](https://arxiv.org/html/2606.15890v1), DOI 10.1145/3770855.3817584. Procitani apstrakt, konstrukcija i delovi eksperimenta. Benchmark poravnava vise urbanih pokazatelja u prostoru i vremenu; greske objavljuje po indikatoru, ne jednim neuporedivim prosekom. U Beops preneti odvojene metrike i test vremenskog rezonovanja. Njegove procene iz slika nisu zamena za termometar, a perceptivne oznake nisu direktno izmereno blagostanje stanovnika.

### L03. Promene prostora kroz slike

[DynamicVL, 2025](https://arxiv.org/abs/2505.21076). Proveren apstrakt i verzija v2. Visevremensko urbano razumevanje obuhvata detekciju promena i kvantitativne zadatke. Koristan dizajn benchmarka za kasniji satelitski sloj. Americki snimci visoke rezolucije nisu isto sto i dostupni Sentinel pikseli u Beogradu; ne prepisivati njihove performanse.

### L04. Referentni urban digital twin podaci

[TUM2TWIN, 2025](https://arxiv.org/abs/2505.07396). Proveren apstrakt. Multimodalni benchmark je pravac za geometriju i registraciju razlicitih tipova podataka. Drugi prioritet u odnosu na zivi meteoroloski tok. Ne pocinjati rekonstrukciju celog grada samo zato sto postoji detaljan demonstracioni dataset.

### L05. Obrada na vise uredjaja

[UrbanInsight, 2025](https://arxiv.org/abs/2509.00936). Proveren apstrakt. Relevantan pravac za distribuiranu obradu i filtriranje urbanih podataka na ivici mreze. Detaljne tvrdnje o performansama nisu proverene. Za Beops eksperiment je jednostavan: isti workload na jednom telu i na vise tela, ukljucujuci cenu prenosa i nestanak jednog tela.

### L06. Zakasneli i neuredjeni tokovi

[Akidau et al., The Dataflow Model, VLDB 2015](https://research.google/pubs/the-dataflow-model-a-practical-approach-to-balancing-correctness-latency-and-cost-in-massive-scale-unbounded-out-of-order-data-processing/). Procitan autorski opis/apstrakt. Vazan temelj za odnos korektnosti, latencije i troska. Preneti razliku vremena dogadjaja i obrade, vremenske prozore i kasne korekcije. Nije potrebno uvoditi Google Cloud ili veliki stream framework u Svemir da bismo primenili te principe.

### L07. Kalibracija je vremenski i lokalno zavisna

[Patel et al., Towards a hygroscopic growth calibration for low-cost PM2.5 sensors, AMT 2024](https://amt.copernicus.org/articles/17/1051/2024/), DOI 10.5194/amt-17-1051-2024. Procitani apstrakt i metode. Vlaznost, aerosol i sezona menjaju odnos jeftinog senzora i reference. Koristimo kao osnovu za ko-lokaciju, prozore i proveru prenosa; kalifornijske koeficijente ne preslikavamo na Beograd.

### L08. Zvuk sa lokacijom i vremenom

[Cartwright et al., SONYC-UST-V2, 2020](https://arxiv.org/abs/2009.05188). Proveren apstrakt. Dataset povezuje urbane zvucne zapise sa prostornovremenskim kontekstom i ljudskom proverom oznaka. Preneti multi-label evaluaciju i podelu po lokaciji/vremenu; ne predstavljati arhivu kao zivi mikrofon.

### L09. Mali modeli i razliciti mikrofoni

[Schmid et al., Low-Complexity Acoustic Scene Classification with Device Information, DCASE 2025; revidirano 2026](https://arxiv.org/abs/2505.01747). Proveren apstrakt v2. Posebno odgovara mrezi razlicitih uredjaja: promena mikrofona je deo evaluacije, ne detalj implementacije. Sledece procitati potpune limite modela, leaderboard i licencirane checkpoint-e, pa izabrati jedan.

### L10. Seizmicki modeli i prenosivost

[SeisBench: A Toolbox for Machine Learning in Seismology](https://arxiv.org/abs/2111.00786). Proveren apstrakt. Vrednost je zajednicki pristup modelima i datasetovima, ne obecanje da bilo koji model radi na bilo kojoj stanici. Preneti reproducibilnost preprocessing-a, kanala i checkpoint-a. Dopunski pravac: [Which picker fits my data?](https://arxiv.org/abs/2110.13671), za detaljno citanje pre izbora modela.

### L11. Mali modeli vremenskih serija

[Chronos: Learning the Language of Time Series, 2024](https://arxiv.org/abs/2403.07815), uz [autorsku Bolt karticu](https://huggingface.co/amazon/chronos-bolt-tiny). Apstrakt rada i kartica procitani. Kvantilne prognoze daju prirodan test nesigurnosti i odstupanja, ali nisu automatski kalibrisane za nase senzore. Prve provere: MAE/MASE, pinball loss i pokrivenost intervala, bez buducih podataka u istorijskom prozoru.

### L12. Srpski tekstualni izvori

[Ljubesic i Lauc, BERTic, BSNLP 2021](https://aclanthology.org/2021.bsnlp-1.5/). Proveren apstrakt i bibliografski podaci. Regionalni jezicki model je ozbiljniji polazni komparator nego pretpostavka da bilo koji mali engleski LLM razume ulice i padeze. Testirati izvorni tekst oba pisma; normalizovani indeks ne sme da zameni originalni dokaz.

### L13. Fleksibilno izdvajanje entiteta

[GLiNER, 2024 izdanje rada](https://arxiv.org/abs/2311.08526), prvobitni preprint 2023. Provereni apstrakt i autorska model kartica. Koristan kandidat za konfigurabilne oznake iz obavestenja. Izdvojena lokacija tek je kandidat za geografsko povezivanje, a ne dokaz da je pronadjena tacna ulica.

### L14. Standardi, ne novi model

[OGC SensorThings](https://www.ogc.org/standards/sensorthings/) organizuje senzor, posmatrano svojstvo, merenje i lokaciju; [W3C PROV-O](https://www.w3.org/TR/prov-o/) poreklo i transformacije. Proverene standardne stranice. Za prvi korak usvojiti precizne pojmove i kasnije eksplicitno testirati mapiranje; ne proglasavati conformance jer JSON ima slicna imena.

## 3. Sto jos treba istraziti, sa jasnim izlazom

| Pitanje | Gde i sta traziti | Izlaz koji nam treba |
|---|---|---|
| Koji raspored stanica najbolje opisuje grad? | Radovi o network design, kriging uncertainty, spatial cross-validation i observability | Dve metode odabira stanica + geografski holdout; bez precizne interpolacije gde nema potpore |
| Kako uporediti tokove razlicitog ritma? | Multi-rate fusion, asynchronous sensing, mixed-frequency models | Pravilo prozora, starosti i kasnih revizija; isti backtest za sve konfiguracije |
| Kako meriti novost bez senzacionalizma? | Change-point detection, event detection, value of information | Oznaceni dogadjaji i false-alerts/day; poredjenje sa prostim pragom |
| Kako mikrofon/kamera menjaju model? | DCASE device mismatch, domain adaptation, camera shift | Test na nevidjenom uredjaju i uslovima, ne samo nasumicnim frejmovima |
| Kako oblik prenosi istinu? | Information visualization, ambient displays, sonification i data physicalization | Kontrolisano poredjenje citljivosti, ne samo umetnicka ocena |
| Sta znaci slobodan javni proizvod? | Primarni uslovi svakog feeda/checkpoint-a i mogucnost objave izvedenih podataka | Access/reuse/publish odluka za tacan izvor, ne jedna genericka izjava o internetu |

Ne praviti bibliografsku gomilu: svaki sledeci rad mora da promeni konkretan eksperiment, podatkovni ugovor ili izbor modela. Proizvodjaceve brojke, tudje lokalne beleške i apstrakti ne postaju nasi mereni rezultati.
