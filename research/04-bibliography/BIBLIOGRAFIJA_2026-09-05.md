# BEOPS — Bibliografija 2026-09-05 (faza Build v1)

Datum: 05.09.2026, ~15:15 lokalno (13:15 UTC). Faza: Build v1 (Svemir).
Svrha: sistematski pregled relevantnih radova (teorija, ontologija, urbano planiranje, CS, AI, big data) sa **mapom rad → konkretna izmena eksperimenta/ugovora**. Pravilo: svaki rad mora promeniti konkretan eksperiment, podatkovni ugovor ili izbor modela; ne gomilamo PDF-ove. Ovo je ciljani pregled, ne iscrpan sistematski review; "apstrakt" znači da su identitet i opis provereni, metodologija/rezultati nisu reprodukovani.

## Mapa rad → konkretna izmena (≥5 radova)

### B01. Towards Agentic Urban Digital Twins (AUDiTs), 2026 — Springer
- **Izvor:** https://link.springer.com/article/10.1007/s44212-025-00099-3
- **Kontekst:** agentic urban digital twins; razdvaja prikupljanje, modele, orkestraciju, interakciju.
- **Konkretna izmena:** u `rad_draft.md` dodati poređenje arhitektonskih odgovornosti (prikupljanje vs. model vs. orkestracija) kao okvir za opis Beops organizma; ne tvrditi da je agent potreban u svakom kolektoru.

### B02. UrbanWell, 2026 — arXiv 2606.15890, DOI 10.1145/3770855.3817584
- **Izvor:** https://arxiv.org/html/2606.15890v1
- **Kontekst:** benchmark poravnava više urbanih pokazatelja u prostoru i vremenu; greške po indikatoru, ne jednim prosekom.
- **Konkretna izmena:** u eksperimentima E03/E04 (brojčani ritam, anomalije) uvesti **odvojene metrike po indikatoru** (MAE/MASE po seriji, ne jedan zbirni prosek) i test vremenskog rezonovanja; ne koristiti procene iz slika kao termometar.

### B03. DynamicVL, 2025 — arXiv 2505.21076
- **Izvor:** https://arxiv.org/abs/2505.21076
- **Kontekst:** viševremensko urbano razumevanje, detekcija promena i kvantitativni zadaci.
- **Konkretna izmena:** u E08 (slika) koristiti njihov dizajn benchmarka za kasniji satelitski sloj; ne prepisivati njihove performanse na Sentinel piksele Beograda (američki snimci visoke rezolucije ≠ dostupni Sentinel pikseli).

### B04. Akidau et al., The Dataflow Model, VLDB 2015
- **Izvor:** https://research.google/pubs/pub43864/
- **Kontekst:** korektnost, latencija, trošak u neuređenim tokovima; vreme događaja vs. obrade, vremenski prozori, kasne korekcije.
- **Konkretna izmena:** u OBS-001 protokolu i `observe_10k.py` eksplicitno razdvojiti `observed_at` (null) od `attempted_at`/`completed_at`; dokumentovati da zakazano vreme nije vreme izvora. Ovo je već delom ugrađeno; rad daje teorijsku potporu za taj ugovor.

### B05. Patel et al., Towards a hygroscopic growth calibration for low-cost PM2.5 sensors, AMT 2024 — DOI 10.5194/amt-17-1051-2024
- **Izvor:** https://amt.copernicus.org/articles/17/1051/2024/
- **Kontekst:** vlaga, aerosol i sezona menjaju odnos jeftinog senzora i reference.
- **Konkretna izmena:** u S34 (openSenseMap) i Sensor.Community ugovoru uvesti **ko-lokaciju, vremenske prozore i proveru prenosa**; ne preslikavati kalifornijske koeficijente na Beograd. Ovo direktno menja kako tumačimo S34 merenja (vidi `ZAHTEVI_JP_AGREGATI.md` i S34 freshness nalaz).

### B06. Cartwright et al., SONYC-UST-V2, 2020 — arXiv 2009.05188
- **Izvor:** https://arxiv.org/abs/2009.05188
- **Kontekst:** urbano zvučno okruženje sa prostorno-vremenskim kontekstom i ljudskom proverom oznaka.
- **Konkretna izmena:** u E07 (zvuk) koristiti multi-label evaluaciju i podelu po lokaciji/vremenu/uređaju; ne predstavljati arhivu kao živi mikrofon; javna verzija bez transkripata prolaznika.

### B07. Schmid et al., Low-Complexity Acoustic Scene Classification with Device Information, DCASE 2025 — arXiv 2505.01747
- **Izvor:** https://arxiv.org/abs/2505.01747
- **Kontekst:** mali akustički modeli i različiti mikrofoni; promena mikrofona je deo evaluacije.
- **Konkretna izmena:** u E07 uvesti **device holdout** (test na neviđenom uređaju/uslovima), ne samo nasumične frejmove; izabrati jedan javni checkpoint tek posle čitanja limita i licence.

### B08. SeisBench, 2021 — arXiv 2111.00786
- **Izvor:** https://arxiv.org/abs/2111.00786
- **Kontekst:** zajednički pristup seizmičkim datasetovima/modelima; reproducibilnost preprocessing-a, kanala, checkpoint-a.
- **Konkretna izmena:** u E09 (tlo) i S19 (seizmička mreža) uvesti reproducibilnost preprocessing-a i kanala; checkpoint nije potvrda seizmičkog događaja bez stručnog postupka; ne preuzimati waveform bez instrument metadata.

### B09. Chronos: Learning the Language of Time Series, 2024 — arXiv 2403.07815
- **Izvor:** https://arxiv.org/abs/2403.07815
- **Kontekst:** kvantilne prognoze vremenskih serija; prirodan test nesigurnosti.
- **Konkretna izmena:** u E03 (brojčani ritam) koristiti MAE/MASE, pinball loss i pokrivenost intervala, bez budućih podataka u istorijskom prozoru; ne automatski kalibrisati za naše senzore.

### B10. Ljubešić i Lauc, BERTic, BSNLP 2021 — aclanthology 2021.bsnlp-1.5
- **Izvor:** https://aclanthology.org/2021.bsnlp-1.5/
- **Kontekst:** regionalni jezički model za BCMS; ozbiljniji komparator od pretpostavke da mali engleski LLM razume ulice i padeže.
- **Konkretna izmena:** u E01 (objave) testirati izvorni tekst oba pisma (ćirilica/latinica); normalizovani indeks ne sme da zameni originalni dokaz.

### B11. GLiNER, 2024 — arXiv 2311.08526
- **Izvor:** https://arxiv.org/abs/2311.08526
- **Kontekst:** fleksibilno izdvajanje entiteta sa konfigurabilnim oznakama.
- **Konkretna izmena:** u E01 koristiti kao kandidat za konfigurabilne oznake iz obaveštenja; izdvojena lokacija je tek kandidat za geografsko povezivanje, ne dokaz tačne ulice.

### B12. OGC SensorThings + W3C PROV-O (standardi)
- **Izvor:** https://www.ogc.org/standards/sensorthings/ ; https://www.w3.org/TR/prov-o/
- **Kontekst:** organizacija senzora/posmatranog svojstva/merenja/lokacije; poreklo i transformacije.
- **Konkretna izmena:** u `DRUGI_GRADOVI_CULA_I_ORGANI.md` recniku usvojiti precizne pojmove (izvor, culo, organ, otisak, puls, memorija, oblik) i kasnije eksplicitno testirati mapiranje; ne proglašavati conformance jer JSON ima slična imena.

## Dodatni radovi iz uporednih gradova (kontekst, ne zamena za beogradska merenja)

- **Melburn** pedestrian counting (data.melbourne.vic.gov.au): organ kretanja meri intenzitet/smer/odstupanje, ne broji jedinstvene ljude; minut rezolucije ≠ minut latencije.
- **Barselona Smart Citizen** (developer.smartcitizen.me): katalog sposobnosti odvojen od kataloga tela; jedan uređaj može nositi više čula.
- **Chicago Array of Things** (arrayofthings.github.io): senzor mora imati datum poslednjeg dokaza života, istoriju zamene, verziju kalibracije.
- **Sage** (sagecontinuum.org): kamera okrenuta ka nebu hrani organ oblačnosti, ne nadzora ljudi; jedno čulo daje više izvedenih signala sa identitetom algoritma.

## Honest verdict

Urađeno: 12 radova/standarda mapirano na konkretne izmene eksperimenata/ugovora (E01–E09, OBS-001, S34, recnik), plus kontekst iz uporednih gradova. Nije urađeno: reprodukcija metodologije/rezultata bilo kog rada, skidanje težina, slanje bilo čega. Ovo je ciljani pregled, ne iscrpan sistematski review; svaki rad je interpretacija za Beops, ne rezultat tih autora na Beogradu.
