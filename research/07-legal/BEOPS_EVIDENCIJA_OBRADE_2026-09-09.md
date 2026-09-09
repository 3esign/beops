# BEOPS — Evidencija radnji obrade i javno obaveštenje
# BEOPS — Record of processing activities and public notice

**Verzija / Version:** 1 · **Datum / Date:** 2026-09-09 · **Status:** važeći dokument / in force

Ovaj dokument zatvara E-013 zajedno sa `research/RETENTION.json`. Do danas je zapis sadržao naslove
vesti bez pisanog pravila o roku čuvanja i bez zapisane evidencije obrade. Oba sada postoje.
*This document closes E-013 together with `research/RETENTION.json`. Until today the record held news
headlines with no written retention rule and no written record of processing. Both now exist.*

> **Nije pravni savet.** Ovo je pravno čitanje autora, ne mišljenje advokata. Pisma A i D (u
> `research/07-legal/`) treba da prođu kroz advokata pre slanja.
> *Not legal advice. This is the authors' own legal reading, not a lawyer's opinion.*

---

## SRPSKI

### 1 · Rukovalac

Doc. dr Semir Poturak i prof. dr Darinka Golubović Matić, kao autori naučnog rada pripremljenog za
konferenciju *Creating sustainable commUNiTy* (Univerzitet Union — Nikola Tesla, 25. septembar 2026).
Obrada se vrši na sopstvenoj opremi autora, nije komercijalna, i **ne vrši se u ime univerziteta niti
ga obavezuje**. Kontakt za sva pitanja i prigovore: **poturaksemir@gmail.com**.

### 2 · Svrha obrade

Naučno istraživanje: izgradnja i provera zapisa gradskih podataka u kojem svaka vrednost nosi svoj
izvor, tri vremena, jedinicu, jedno od pet evidencijskih stanja i uhvaćenu dozvolu koja je čitanje
dopustila. Sloj vesti postoji da bi se ono što je objavljeno moglo postaviti pored onoga što je
izmereno istog dana. Nema druge svrhe, nema profilisanja, nema ciljanja, nema donošenja odluka o
pojedincima.

### 3 · Pravni osnov

- **Član 12** ZZPL — zakonitost obrade. Osnov je obrada neophodna u svrhe naučnog istraživanja, uz
  zaštitne mere iz **člana 92**; podredno, legitimni interes objavljivanja proverljivog zapisa o
  javnim izvorima jednog grada, pri čemu su podaci već objavljeni od strane samih medija.
- **Član 92** ZZPL — obrada u svrhe naučnog istraživanja, uz zaštitne mere iz odeljka 5 ovog
  dokumenta.
- Naslov, link i vreme objave koriste se u obimu kratkog citata (**član 49** Zakona o autorskom i
  srodnim pravima); službeni materijali su van autorskopravne zaštite (**član 6 stav 2**). Srbija
  **nema izuzetak za rudarenje teksta i podataka** i ovaj rad se ni u jednom delu na njega ne
  oslanja.

### 4 · Kategorije lica i podataka

| Kategorija lica | Podaci koji se obrađuju | Šta se **ne** obrađuje |
|---|---|---|
| Lica imenovana u objavljenom naslovu beogradskog medija — pretežno nosioci javnih funkcija | ime i funkcija onako kako stoje u naslovu; link na objavu; vreme objave; vreme prijema | telo teksta, fotografije, kontakt podaci, adrese, identifikacioni brojevi, lokacija, bilo koji posebno osetljiv podatak |

Nema kamera. Nema podataka o zdravlju, veroispovesti, političkom opredeljenju, seksualnoj
orijentaciji, članstvu u sindikatu ni bilo koje druge posebne kategorije. Nema podataka o deci.
Nema podataka o pojedincima izvan onoga što je medij sam objavio kao naslov.

### 5 · Zaštitne mere (član 92)

1. **Minimizacija na izvoru.** Uzima se isključivo naslov, link i vreme objave. Telo teksta se ne
   preuzima nikada, ni privremeno.
2. **Dozvola kao uhvaćeni bajtovi.** Pre svakog prvog čitanja izvora sačuvan je bajt-po-bajt zapis
   njegovih pravila (robots.txt, uslovi korišćenja), sa nedeljnom ponovnom proverom. Četrnaest
   izdavača je reklo ne i njihova odluka se poštuje po imenu, nikada se ne zaobilazi.
3. **Rok čuvanja.** `research/RETENTION.json`, pravilo R1: tekst naslova se briše posle **90 dana**;
   red ostaje sa izvorom, linkom i vremenima, kao dokaz da je nešto objavljeno u tom minutu na toj
   adresi — što je činjenica o izdavaču, ne o imenovanom licu. Pravilo R2 briše i sirove zapise
   izvora. Brisanje sprovodi `tools/apply_retention.py`, a šta je obrisano beleži se u
   `data/live/retention-ledger.jsonl`, koji se nikada ne prepisuje.
4. **Prigovor pre roka.** Pravilo R6: prigovor primljen na adresu iz odeljka 1 izvršava se u roku od
   **30 dana**, bez obzira na starost reda.
5. **Nema primalaca.** Podaci se ne prosleđuju nikome, ne prodaju se i ne razmenjuju.
6. **Nema praćenja posetilaca.** Sajt je statičan: bez kolačića, bez analitike, bez trekera, bez
   naloga.
7. **Integritet.** Svaki red nosi sha256 sirovog zapisa iz kog je nastao; ispravke se dopisuju i
   nikada ne brišu (`research/08-provenance/CORRECTIONS.md`).
8. **Ograničenje mašine.** Lokalni jezički modeli komentarišu zapis iza validatora koji odbija sve
   što zapis ne podržava; svaki iskaz je mašinski označen kao veštački generisan (Akt o veštačkoj
   inteligenciji EU, član 50) i nikada se ne prikazuje kao merenje. Urednik zapisa može zaustaviti
   taj organ jednim fajlom.

### 6 · Objavljivanje i iznošenje

Javni snimak (`docs/`) objavljuje se na GitHub Pages i sadrži prozor od 24 sata. Hosting znači da se
objavljeni snimak čuva i isporučuje sa servera van Republike Srbije. **Ovo je najslabija tačka ovog
dokumenta i navodi se otvoreno:** reč je o objavljivanju već objavljenih naslova u okviru naučnog
rada, a ne o prenosu zbirke podataka trećem licu radi njegove obrade. Alternativa — hosting u zemlji
— razmatra se i biće zabeležena kao izmena ovog dokumenta ako do nje dođe.

### 7 · Zašto lica nisu obaveštena pojedinačno

Član 24 ZZPL traži obaveštavanje kada podaci nisu prikupljeni od lica na koje se odnose, i predviđa
izuzetak kada je takvo obaveštavanje nemoguće ili iziskuje nesrazmeran napor, naročito kod obrade u
svrhe naučnog istraživanja, uz uslov da postoje zaštitne mere i da je **obaveštenje javno
objavljeno**. Zapis sadrži naslove više desetina hiljada objava; pojedinačno obaveštavanje svakog
imenovanog lica nije izvodljivo bez prikupljanja kontakt podataka koje inače ne držimo — dakle bez
šire obrade nego što je sama svrha. Zato:

- zaštitne mere iz odeljka 5 postoje i proverljive su u kodu i podacima,
- ovo obaveštenje je javno objavljeno na sajtu projekta i u repozitorijumu,
- adresa za prigovor stoji na svakoj javnoj stranici.

### 8 · Prava lica

Pristup, ispravka, brisanje, ograničenje i **prigovor (član 37)** ostvaruju se pisanjem na
**poturaksemir@gmail.com**. Odgovor sledi u roku od 30 dana. Ako lice nije zadovoljno, ima pravo
pritužbe Povereniku za informacije od javnog značaja i zaštitu podataka o ličnosti.

### 9 · Šta bi ovaj dokument oborilo

Ako bi se pokazalo da naslovi u zapisu sadrže posebne kategorije podataka u meri koja nije očigledna
iz samog naslova; ako bi rok od 90 dana bio ocenjen kao predug za svrhu; ili ako bi objavljivanje
snimka van zemlje bilo ocenjeno kao iznošenje koje traži poseban osnov — pravilo se menja, a izmena
se dopisuje ovde i u `CORRECTIONS.md`. Dokument je napisan da bi mogao da bude oboren, ne da bi se
branio.

---

## ENGLISH

### 1 · Controller

Doc. dr Semir Poturak and prof. dr Darinka Golubović Matić, as the authors of a scientific paper
prepared for *Creating sustainable commUNiTy* (University Union — Nikola Tesla, 25 September 2026).
The processing runs on the authors' own equipment, is non-commercial, and **is not carried out on
behalf of the university and does not bind it**. Contact for any question or objection:
**poturaksemir@gmail.com**.

### 2 · Purpose

Scientific research: building and testing a record of city data in which every value carries its
source, three times, a unit, one of five evidential states, and the captured permission that allowed
it to be read. The news layer exists so that what was published can be set beside what was measured
on the same day. There is no other purpose: no profiling, no targeting, no decisions about
individuals.

### 3 · Legal basis

- **Article 12** of the Serbian Personal Data Protection Act (ZZPL) — lawfulness. The basis is
  processing necessary for scientific research, with the safeguards of **Article 92**; in the
  alternative, the legitimate interest in publishing a checkable record of one city's public sources,
  where the data were already published by the outlets themselves.
- **Article 92** — processing for scientific research purposes, with the safeguards in section 5.
- Headline, link and publication time are used within the scope of short quotation (**Article 49** of
  the Copyright and Related Rights Act); official materials fall outside copyright altogether
  (**Article 6(2)**). Serbia has **no text-and-data-mining exception**, and no part of this work
  relies on one.

### 4 · Categories of data subjects and data

| Data subjects | Data processed | What is **not** processed |
|---|---|---|
| Persons named in a published headline of a Belgrade outlet — predominantly public office holders | the name and role exactly as they appear in the headline; the link; publication time; reception time | article body, images, contact details, addresses, identification numbers, location, any special category of data |

No cameras. No health, religion, political opinion, sexual orientation, trade-union membership or any
other special category. No data about children. Nothing about any individual beyond what the outlet
itself published as a headline.

### 5 · Safeguards (Article 92)

1. **Minimisation at the source.** Only the headline, the link and the publication time are taken.
   The body of an article is never fetched, not even temporarily.
2. **Permission as captured bytes.** Before the first read of any source, its rules (robots.txt,
   terms) were stored byte for byte, and are re-checked weekly. Fourteen publishers said no; their
   decision is honoured by name and never circumvented.
3. **Retention.** `research/RETENTION.json`, rule R1: headline text is erased after **90 days**; the
   row survives with its source, link and times, as evidence that something was published at that
   minute at that address — a fact about the publisher, not about the person named. Rule R2 deletes
   the raw feed captures as well. `tools/apply_retention.py` enforces it and what it erased is
   recorded in `data/live/retention-ledger.jsonl`, which is never rewritten.
4. **Objection before the window closes.** Rule R6: an objection received at the address in section 1
   is acted on within **30 days**, whatever the age of the row.
5. **No recipients.** Nothing is passed on, sold or exchanged.
6. **No visitor tracking.** The site is static: no cookies, no analytics, no trackers, no accounts.
7. **Integrity.** Every row carries the sha256 of the raw capture it came from; corrections are
   appended and never erased (`research/08-provenance/CORRECTIONS.md`).
8. **The machine is bounded.** Local language models comment on the record behind a validator that
   refuses anything the record does not support; every utterance is machine-marked as AI-generated
   (EU AI Act, Article 50) and is never presented as a measurement. The editor of record can stop
   that organ with a single file.

### 6 · Publication and transfer abroad

The public snapshot (`docs/`) is published on GitHub Pages and carries a 24-hour window. Hosting
means the published snapshot is stored and served from servers outside Serbia. **This is the weakest
point in this document and is stated plainly:** it is the publication of already-published headlines
as part of a scientific paper, not the transfer of a dataset to a third party for that party's own
processing. Hosting inside the country is under consideration, and would be recorded here as an
amendment.

### 7 · Why individuals were not notified one by one

Article 24 ZZPL requires notice where data were not collected from the data subject, and allows an
exception where such notice is impossible or would take disproportionate effort — particularly for
scientific research — provided safeguards exist and **the notice is made public**. The record holds
the headlines of tens of thousands of publications; notifying every named person individually is not
feasible without collecting contact data we deliberately do not hold, which would mean processing
more than the purpose itself requires. Therefore: the safeguards in section 5 exist and are checkable
in the code and in the data; this notice is published on the project's site and in the repository;
and the objection address appears on every public page.

### 8 · Rights

Access, rectification, erasure, restriction and **objection (Article 37)** are exercised by writing to
**poturaksemir@gmail.com**. An answer follows within 30 days. A person who is not satisfied may
complain to the Commissioner for Information of Public Importance and Personal Data Protection.

### 9 · What would overturn this document

If headlines in the record were shown to carry special categories of data beyond what the headline
itself makes obvious; if ninety days were judged too long for the purpose; or if publishing the
snapshot outside the country were judged a transfer needing its own basis — the rule changes, and the
change is appended here and in `CORRECTIONS.md`. This document is written to be overturned, not
defended.

---

## Honest verdict

- Do danas smo bili **saobrazni u praksi, ali bez papira**. Praksa je bila dobra: minimizacija,
  poštovana odbijanja, nikakvi posebni podaci. Papir nije postojao, a inspektor čita papir.
  *Until today the practice was sound and the paperwork did not exist. An inspection reads paperwork.*
- Najslabija tačka nije rok čuvanja nego **hosting van zemlje**, i navedena je otvoreno u odeljku 6
  umesto da bude prećutana.
- Ovaj dokument ne zamenjuje mišljenje advokata i ne tvrdi da ga zamenjuje.
