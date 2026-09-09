# Beops: mali modeli, mesta preuzimanja i izvrsni putevi

05.09.2026. Katalog za odabir eksperimenata, ne spisak spremnih organa. Masinski izbor je u [MODEL_CANDIDATES.json](../MODEL_CANDIDATES.json).

## 1. Sta je stvarno provereno i skinuto

- Prvi [audit](../evidence/model-audit-20260905T035841827817Z/REPORT.json): 24 trazena repozitorijuma, 22 potvrđena identiteta/revizije i 22 lokalno sacuvane kartice. Dve greske su sacuvane, nisu izbrisane.
- Drugi [ciljani audit](../evidence/model-audit-20260905T040035741530Z/REPORT.json): E5 identitet/provider metadata i kanonski Moonshine identitet potvrđeni; sacuvana jos jedna kartica.
- Ukupno 24 kanonska HF identiteta/revizije, provider metapodaci za svih 24 i 23 kartice. Nisu skinute tezine, nisu instalirani runtimes i nije izvrsen inference.
- Prvi prolaz: 68 pokusaja HTTP zahteva. Brojac bajtova u izvestaju obuhvata samo uspesne odgovore; ne obuhvata prekoračeni odgovor, HTTP/TLS overhead ili ostalo istrazivanje. Ne koristiti ga kao merenje ukupnog mrežnog saobracaja.
- E5 potpuni metadata odgovor presao je pocetnu granicu 1 MB. Selektivna polja su uspela; README i dalje prelazi granicu 200 kB i nije lokalno skinut. Nema razloga da zbog jednog velikog README-a uklonimo granice svih fetch poziva.
- `UsefulSensors/moonshine` preusmerava na `moonshine-ai/moonshine`. Prvi audit ispravno nije prihvatio promenjeni identitet. Naknadno potvrđena kanonska revizija: `48b4e427b587bcf67797a5be706d6ddc4a298149`. Stari dokaz ostaje istorija, shortlist pokazuje alias.

API parametri su broj tenzora koje je servis prijavio za datu reviziju, ne nasa izmerena memorija. `null` znaci da nema podatka, ne da je model mali ili besplatan. Kartice su nepoverljiv preuzeti tekst, ne instrukcije za shell.

## 2. Prvi izbor prema zadatku

| Model / autorski izvor | API parametri, zaokruzeno | Organ i predlog | Glavna provera pre upotrebe |
|---|---|---|---|
| [Chronos-Bolt Tiny](https://huggingface.co/amazon/chronos-bolt-tiny) | 8,65M | P0 kratki brojcani ritam | Rolling-origin, persistence, kvantili i stvarna istorija |
| [Chronos-Bolt Mini](https://huggingface.co/amazon/chronos-bolt-mini) | 21,24M | P1 kontrola koristi vece varijante | Isti ulaz i budzet kao Tiny |
| [IBM TTM R2](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2) | 0,805M za default reviziju | P0 multivarijantna prognoza | Birati tacnu context/horizon granu; broj ne vazi za celu porodicu |
| [IBM TSPulse R1](https://huggingface.co/ibm-granite/granite-timeseries-tspulse-r1) | 1,084M | P0 anomalije/slicnost | Task head, scale, false alerts/day; imputacija nije sirovo merenje |
| [E5-small multilingual](https://huggingface.co/intfloat/multilingual-e5-small) | 117,65M | P0 povezivanje dokaza i upita | Srpski, query/passage preprocessing, BM25 komparator |
| [Multilingual MiniLM L12](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) | 117,65M | P1 retrieval/dedup konkurent | MiniLM u imenu ne znaci da je ceo model 20M; truncation i pooling |
| [BERTic NER](https://huggingface.co/classla/bcms-bertic-ner) | 110,03M | P0 lokalne objave | NER klase ne pokrivaju automatski datume, negaciju i revizije |
| [GLiNER Small v2.1](https://huggingface.co/urchade/gliner_small-v2.1) | nije prijavljeno | P1 kontrola | Deklarisano en; nije podrazumevani izbor za srpski |
| [GLiNER Multi v2.1](https://huggingface.co/urchade/gliner_multi-v2.1) | 288,95M | P0 fleksibilne klase entiteta | Lokalna tacnost oba pisma; veci od BERTic-a |
| [PP-OCRv6 Tiny detector](https://huggingface.co/PaddlePaddle/PP-OCRv6_tiny_det_safetensors) | 0,438M | P1 pozicije teksta | Detektor nije prepoznavac slova; pregled ulaza i konverzije |
| [PP-OCRv6 Tiny recognizer](https://huggingface.co/PaddlePaddle/PP-OCRv6_tiny_rec_safetensors) | 1,113M | P1 tekst iz crop-a | API navodi en/zh; tvrdnje porodice o mnogo jezika nisu test srpskog checkpoint-a |
| [PP-OCRv5 Latin recognizer](https://huggingface.co/PaddlePaddle/latin_PP-OCRv5_mobile_rec_safetensors) | 5,629M | P1 latinicni dokumenti | Test č/ć/š/ž/đ i tacnih brojeva; jezik nije naveden u API kartici |
| [PP-OCRv5 Cyrillic recognizer](https://huggingface.co/PaddlePaddle/cyrillic_PP-OCRv5_mobile_rec_safetensors) | 5,631M | P1 cirilicni dokumenti | Test srpskih slova i recnika, ne samo naziva modela |
| [Granite Docling 258M](https://huggingface.co/ibm-granite/granite-docling-258M) | 257,52M | P1 struktura dokumenata, kontrola | API en; fidelity tabela/cena/datuma naspram obicnog parsera |
| [MobileNetV3 Small](https://huggingface.co/timm/mobilenetv3_small_100.lamb_in1k) | 2,555M | P2 jeftin vizuelni backbone | ImageNet klase nisu gotova detekcija kvara kamere; potreban task head |
| [DINOv2 Small](https://huggingface.co/facebook/dinov2-small) | 22,06M | P2 promene/retrieval kadrova | Embedding promena moze biti svetlost ili pokret kamere |
| [SegFormer B0 ADE](https://huggingface.co/nvidia/segformer-b0-finetuned-ade-512-512) | 3,753M | P2 segmentacija dozvoljene scene | License metadata `other`; RGB/ADE nije satelitski multispektralni ugovor |
| [SmolVLM 256M](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct) | 256,48M | P2 kvalitativni opis | Nije precizan brojac, kalibrisani senzor ili potvrda dogadjaja |
| [SigLIP2 Base](https://huggingface.co/google/siglip2-base-patch16-224) | 375,19M ukupno | P2 veci vizuelno-tekstualni komparator | 86M za vision tower nije ukupna velicina modela |
| [Prithvi EO 2.0 100M TL](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-100M-TL) | API nije prijavio; ime/kartica 100M | P2 orbitalni trag | Odgovarajuci spektralni kanali, scaling, metadata i downstream head |
| [Whisper Tiny](https://huggingface.co/openai/whisper-tiny) | 37,76M | P2 dozvoljeni govorni dokumenti | Ne koristi se za preslusavanje prolaznika ili kao audio-tagging zamena |
| [Moonshine](https://huggingface.co/moonshine-ai/moonshine) | vise artefakata, nije jedan broj | P2 opcioni ASR konkurent | Izabrati tacan jezik/varijantu; ne skidati repozitorijum u celini |
| [Silero VAD ONNX konverzija](https://huggingface.co/onnx-community/silero-vad) | API nije prijavio | P1 tehnicki detektor govorne aktivnosti | Uporediti sa izvornim Silero; ne garantuje anonimnost |
| [LFM2.5 1.2B GGUF](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF) | API nije prijavio | P2 veca sinteza dokaza, kontrola | License `other`, sr nije deklarisan; ne menja parser ni izvorne brojke |

Brojevi nisu rang-lista kvaliteta. Za OCR meriti zbir detektora, recognizer-a i preprocessinga; za embedding punu arhitekturu i tokenizer; za generativni model ukljuciti kontekst i KV cache. Deklaracija Apache/MIT u metadata nije zavrsen pregled svih ulaza, artefakata i izlaza.

## 3. Van HF-a: konkretni putevi koje ne treba propustiti

| Put | Sta uzimamo | Sta je stvarno pregledano / ostaje |
|---|---|---|
| [Google YAMNet na Kaggle-u](https://www.kaggle.com/models/google/yamnet/tfLite/tflite) | Mali akusticki klasifikator, 521 klasa; LiteRT varijanta | Primarna indeksirana kartica daje Apache 2.0 i mono 16kHz; direktni web prikaz nije izlozio tekst; download/hash/runtime jos nisu provereni |
| [EfficientAT autor](https://github.com/fschmid56/EfficientAT) | AudioSet MobileNet/Dynamic MobileNet tezine iz GitHub releases | README i nacin preuzimanja pregledani; izabrati tacan mn/dymn model i release; nema lokalnog benchmarka |
| [Silero autor](https://github.com/snakers4/silero-vad) | Izvorna VAD putanja i ONNX | README navodi MIT, 8/16kHz i primere; conversion parity i lokalni zvuk nisu provereni |
| [SeisBench](https://seisbench.readthedocs.io/en/stable/pages/models/pretrained_models.html) | PhaseNet/EQTransformer i vise treniranih checkpoint-a | Dokumentovani list/get pretrained; nije jedan model niti blanket licenca svakog dataseta |
| [DCASE 2024 rezultati](https://dcase.community/challenge2024/task-data-efficient-low-complexity-acoustic-scene-classification-results) | CP-Mobile/TF-SepNet/MobileNet pravci i technical reports | Pronadjene male arhitekture; svaki checkpoint/licencu proveriti posebno; papir nije gotov artefakt |
| [DCASE 2026](https://dcase.community/challenge2026/index) | Noviji taskovi, benchmarki i rezultatne strane | Pregledani zadaci; ne poistovecivati sa ranijim low-complexity Task 1 |

Silero original i HF konverzija nisu dva nezavisna modela. Isto vazi za isti checkpoint objavljen na GitHub-u, HF-u i u ONNX katalogu.

## 4. Provajder nije jedna stvar

Razlikujemo **autora**, **distributera tezina**, **runtime**, **hostovani inference** i **katalog za otkrivanje**. Jedna organizacija moze imati vise uloga. Cena, dostupnost i kvalitet hostovanog puta proveravaju se posebno; ova proba nije koristila placeni inference.

| Ekosistem | Uloga za Beops | Pravilo izbora |
|---|---|---|
| [Hugging Face Hub](https://huggingface.co/docs/hub/api) | Identiteti, revizije, kartice, tezine i veze sa providerima | Prvo author -> commit -> ugovor; popularnost samo discovery signal |
| [HF Inference Providers](https://huggingface.co/docs/inference-providers/en/hub-api) | Trenutna mapa servisa za tacan model | Mapa se menja; `live` nije test poziva, besplatnost niti SLA |
| Autorski GitHub releases | Originalne tezine/kod iz naucnih projekata | Pinovati tag i hash; ne izvrsavati instalacione skripte iz README-a |
| Kaggle / Google modeli | Autorske audio i edge varijante | Proveriti konkretnu varijantu/version, ne opstu licencu sajta |
| [Qualcomm AI Hub](https://app.aihub.qualcomm.com/docs/index.html) | Konverzija i provera na podrzanim uredjajima | Nije dokaz da je Semirov telefon podrzan; prvo inventar SoC/runtime-a |
| [OpenVINO ekosistem](https://github.com/openvinotoolkit/open_model_zoo) | CPU/Intel deployment kandidati | Open Model Zoo je u maintenance modu; istrazivati odrzavane notebooks/model tutorials, ne predstavljati stari zoo kao dnevni izvor novih modela |
| [PaddleOCR autor](https://github.com/PaddlePaddle/PaddleOCR) | OCR verzije, jezicki recnici, det/rec pipeline | Footprint celog pipeline-a; srpski test oba pisma obavezan |
| [SeisBench autor](https://github.com/seisbench/seisbench) | Domen, datasetovi i seizmicki preprocessing | Provera konkretnih pretrained weights, ne samo Python klase |
| [IBM/NASA Prithvi](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-100M-TL) | Multispektralni backbone i TerraTorch put | Ne tretirati kao gotov model za RGB kameru ili minute-live puls |
| [Docling katalog](https://github.com/docling-project/docling/blob/main/docs/usage/model_catalog.md) | Obrada dokumenta kroz vise uskih koraka | Proveriti sta je model a sta orchestrator; ne instalirati ceo stack radi jednog PDF-a |
| Drugi hostovani servisi | Buduci kontrolni put ako tacan mali model imaju | Lead, bez utvrdjene liste/cene/ugovora; nijedan nalog ili placeni resurs nije otvoren |

### Trenutno zatecen hostovani put

U sacuvanim HF API odgovorima `hf-inference` ima `status=live` za **E5-small**, **multilingual MiniLM** i **SegFormer B0**. Za ostalih 21 model mapa je prazna u trenutku upita. To znaci da u tom HF polju nije naveden servis; ne dokazuje da ga nijedan provajder na svetu nema. Nije izvrsen nijedan inference poziv i ne tvrdimo cenu, dostupnost pod nasim nalogom ili kvalitet.

## 5. Veze cula i organa koje prvo vredi proveriti

| Culo | Deterministicka obrada | Model kandidat | Koristan rezultat | Kada ga odbacujemo |
|---|---|---|---|---|
| Parking/vodostaj/vazduh | Clock, jedinice, validni istorijski prozori | Chronos Tiny / TTM | Ocekivana putanja i odstupanje | Nema dovoljno istorije ili gubi od persistence |
| Isti brojcani tok | Missing/stale/flatline provera | TSPulse | Kandidat anomalije/slicnog perioda | Kvar instrumenta se predstavlja kao gradski dogadjaj |
| Gradska objava | HTML/PDF text, izvor, datum, revizija | BERTic / GLiNER Multi | Entitet, tip promene, vremenski interval i sira zona | Pogresan interval/negacija ili nema izvornog spana |
| Upiti i vest | Lexical retrieval i canonical dedup | E5 / MiniLM | Relevantan raniji dokaz | Pogresno spaja razlicite dogadjaje ili pakovanja |
| Dozvoljen skenirani PDF | Native text prvo, raster samo kad treba | OCR det+rec, Docling kontrola | Tacan tekst/tabela sa poreklom | Izmisljen broj ili neproverena slova |
| Dozvoljen zvuk | Sampling/quality/privacy | YAMNet / EfficientAT | Siroke akusticke kategorije po vremenu | Nema prava, device shift ili curenje govora |
| Ovlasten kadar | Izvorni sat i kvalitet slike | Mali encoder/segmentator | Ogranicene scene i promene | Lica/tablice/trag pojedinca ili nedozvoljena obrada |
| Dozvoljeni waveform | Kanali, response, sample rate | SeisBench picker | Kandidat dolaska za strucnu proveru | Nedostatak metadata ili lazni javni alarm |

## 6. Najvaznije nove lekcije

1. Naziv porodice i stvarni footprint mogu biti veoma razliciti: SigLIP2 ceo model ima oko 375M, iako se cesto pominje 86M vision tower; multilingual MiniLM ima oko 118M ukupno.
2. Najnoviji OCR nije automatski najbolji za Beograd: detektor moze biti veoma mali, ali alphabets i tacnost na srpskom treba dokazati.
3. Model hostovan na HF-u nije automatski model koji HF izvrsava.
4. Kanonski model ID moze se promeniti; alias/preusmerenje treba evidentirati, ne tiho prihvatiti pri nabavci.
5. Kartice i metadata mogu postati veliki. Selektivna polja i bounded download su deo higijene i istrazivackih alata.
6. Najvredniji prvi dobitak moze biti mali kvalitetan parser ili prag. Model zadrzavamo kada doda merenu vrednost.

## Honest verdict

Potvrđeni su identiteti, revizije i prijavljeni metapodaci, ne kvalitet inferencije, potpuna bezbednost ili prava celog javnog proizvoda. Preuzete kartice nisu u celini strucno auditovane; odabrane primarne strane i apstrakti jesu procitani. Nije izvrseno sistematsko automatsko keyword izdvajanje ni kompletna pretraga drugih provajdera. Sledeci rad je opisan u [glavnom planu](../01-programme/PLAN_CULA_MODELI_2026-09-05.md).
