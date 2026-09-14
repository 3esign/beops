# Beops — Uputstvo za izradu

Operativno uputstvo, uskladjeno 11.09.2026. Pocetna tacka za sledeci rad; istorijski izvestaji ne nadjacavaju kasnije odluke korisnika.

## Pravila izrade
- Beops je samo Beograd. Pazarac ostaje zaseban projekat i izvor lekcija.
- Ceo Beograd -> vece celine -> sire zone. Ostajemo na pulsu; nema mikronivoa, pojedinaca ili zgrada kao javnog nivoa analize.
- Jedan prostorni filter kroz sve domene. Dedup na roditeljskom nivou; nepokrivenost se ne popunjava izmisljenim prosekom.
- Povezujemo postojece izvore i usluge; nema sopstvenog indeksa grada, geokodera ili nove infrastrukturne platforme.
- Parking/prevoz, javne i kulturne promene, dokumentovane cene i atmosfera/voda napreduju zajedno. Zvuk, kamere i tlo su istrazivacki pravci sa otvorenim pristupnim pitanjima.
- Javni sajt `https://3esign.github.io/beops/` je glavni izlaz. `docs/` je generisana GitHub Pages povrsina; `public/` nosi interfejs/assets i generisane javne podatke; privatni git nosi izvor i dokaz, ne svaki zivi snapshot.
- Struktura se cita iz `research/STRUCTURE_CONTRACT_2026-09-11.md`: izvor, dokaz, generisano javno stanje, privatni audit, ziva memorija i ostatak moraju biti razdvojeni.
- Malo racunanja: jedan javni odgovor gde sadrzi vise lokacija, bez ponovnog geokodiranja i bez ucitavanja svih modela. Nema novih zavisnosti.
- Izvorna vremena i jedinice ostaju tacni. Primljeno sada nije izmereno sada; najavljeno nije ostvareno; nema podataka nije nula.
- Analiticke beleske su vidljivo tumacenje dokaza. Ne glume dodatni instrument i ne dokazuju uzrocnost.
- Bez novih agenata. Jezgro Svemira, tudji projekti i tajne ne diraju se kroz ovaj projekat.

## Faze
1. Istrazivacka osnova i povezivanje: izvori, uslovi, trag, recnik, zonska granularnost i testirane male probe.
2. Zivi opservatorijum: zakazani Collect, Mind, Organ, Publish, Watch, Legal, Guard i Baseline zadaci hrane privatni dokaz i javni sajt.
3. Javni oblik: filtrirani mirror `github.com/3esign/beops` i GitHub Pages sajt su aktivni; izdvojeni su od privatnih dokaza i radnih papira.
4. Rad: trenutni paper smer je `research/06-paper/PRE_PAPER_v5_2026-09-10.md`; konferencijsko slanje i prihvatanje nisu pretpostavljeni.

## Provera bez mreze

`npm test` izvrsava Python stdlib testove kroz mali Node pokretac, bez instalacije. `BEOPS_PYTHON` moze zadati drugi Python 3.9+, a publish gate za testove preferira bundled runtime sa potrebnim bibliotekama. Testovi nisu provera punog Svemira.

Lokalni `runtime/test-python.json` cuva provereni interpreter i postojecu Python podrsku; publisher koristi isti izbor za izgradnju i kompletnu kapiju. Na ovom PC-u 14.09.2026. proveren je Python 3.12.14 iz `C:/Users/treed/AppData/Roaming/uv/python/cpython-3.12-windows-x86_64-none/python.exe`, sa ReportLab podrskom u `D:/Svemir/!Projekti/_runtime/beops-test-support`. To su lokalne putanje, ne obaveza drugih uredjaja. Ne pretpostavljati da `python` na PATH-u ili stari bundled runtime postoji: publish prvo izvrsava proveru preduslova.

`python -B research/observe_10k.py status` cita 13 planiranih termina i postojece receipte; ne pristupa internetu i ne pise stanje.

## Provera javnog sajta

`npm run test:site` je read-only provera glavnog interfejsa. Ona salje spoljne GET zahteve ka `https://3esign.github.io/beops/`, sa cache-busterom, uporedjuje zivi `index.html` sa `Beops-public/docs/index.html`, kratko ceka GitHub Pages propagaciju, proverava osnovne ugradjene stranice (`podaci`, `monolog`, `sada`, `traka`, `svedoci`) i pada ako se vrati stara javna atribucija ili drugi poznat stale marker. To je posle-publish provera zivog sajta; ne zamenjuje `npm test`, koji ostaje offline gate pre objave.

## OBS-001 upis

`python -B research/observe_10k.py capture` se poziva samo iz vec podesene automatizacije u ovoj sesiji. Alat je ogranicen na datume observacije. Ne podizati drugi scheduler ili novi servis.

Jedan slot dobija trajan `claim-*.json` pre GET-a i potpun `sample-*.json` posle. Upis koristi privremeni fajl, fsync i hard-link objavu bez prepisivanja na istom disku. Ako to fajl-sistem ne podrzi, staje pre mreze; ne menjati u prepisivanje starih dokaza. Svi testovi koriste privremene foldere, nikad pravi folder observacije.

Na ponovljen termin ne ide drugi zahtev. Ako proces nestane posle claim-a, ostaje nedovrsen trag i rupa; ne uklanjati claim automatski. 403/429 u receipt-u pauzira izvor i za naredne termine. Posle pada pre upisa odgovora HTTP ishod nije poznat; to ne predstavljati kao uspesno merenje.

Kasnjenje do 20 minuta belezi stvarno vreme prijema, ne vreme izvornog merenja. Veca kasnjenja preskacu slot. Na kraju `status` daje pokrivenost; izvestaj koristi samo stvarne uzorke i jasno prikazuje propuste. Granice i grupisanje lokacija su u [protokolu](research/observations/10k-2026-09-05/PROTOKOL.md).

## Gde je sta

- Jedan aktivni Beops i skladistenje (private working record): Semirovo odobrenje za postojece D putanje, C junction kao ulaz, ogranicen privremeni build, rezerva prostora i oporavak bez dupliranja arhive.

- [Struktura projekta](research/STRUCTURE_CONTRACT_2026-09-11.md): sta je izvor, dokaz, generisano javno stanje, privatni audit, ziva memorija i ostatak.
- [Operativni red](research/OPERATIONAL_ORDER_2026-09-11.md): privatni Beops, javni mirror, C/D pravilo, scheduler i publish safety.
- [Research indeks](research/README.md): svi istrazivacki dokumenti i vazeci paper lineage.
- Detaljan program cula i modela (private working record): istrazivacki ciklus, 25 cula, 12 eksperimenata i 48 razrada postojecih zadataka.
- Banka pretrage (private working record): 64 pocetna upita, pravila izdvajanja i prosirivanja pojmova; nije automatski izvrsena pretraga.
- [Katalog modela/provajdera](research/03-models/KATALOG_MODELA_I_PROVAJDERA_2026-09-05.md): konkretni izbori, statusi proba i razlike izmedju distributera i inference servisa.
- [README](README.md): ulazi u dosije i status projekta.
- Radni program (private working record): 65 zadataka, zavisnosti i dokaz zavrsetka; nije automatsko ovlascenje da se sve pokrene.
- Prostorni koncept (private working record): zajednicki filter, spoljne reference i bez mikronivoa.
- Provere (private working record): istorija stvarno izvrsenih provera.
- `RECNIK.jsonl`, `KNOWLEDGE.md`, `LOG.md`: definicije, odluke/lekcije i trag rada kroz postojeci projektni kit.


Recovery entry (2026-09-11): `research/_trail/REPAIR_2026-09-11.md` records implemented changes, validation and unresolved limits. `npm run doctor` checks local build requirements; `npm start` serves the verified public mirror when available, otherwise local generated docs, on a loopback port (printed on startup), and `npm run start:legacy` explicitly starts the old prototype. Headlines are retained and the complete collected archive is at `naslovi.html`; article bodies are not published. Public Git history persists. Scheduled task definitions are in `tools/beops_tasks.ps1`, with individual execution limits; disabled tasks and operator pauses are preserved.

Publikacija koristi Windows task Priority=4 (normalan CPU, I/O i memorijski prioritet); ostali organi zadrzavaju prethodni background prioritet 7. Read-only task audit poredi stvarno stanje sa zajednickom definicijom. Rok obrade od 25 minuta ostavlja pet minuta do sledeceg redovnog termina; zavrsetak ciscenja i oslobodjena brava moraju se potvrditi zasebno. Faze imaju trajanje i ishod, a priprema i pocetak unutrasnjih faza, tako da timeout ostavlja poslednje poznato mesto rada. R02 se ne zatvara samom promenom prioriteta ili roka. Aktuelni dokaz i otvorene granice: R02 napredak (private working record).
