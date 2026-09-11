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

Na ovom PC-u proveren Python je `C:/Users/treed/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`. Kada `python` nije na PATH-u, pozvati taj izvrsni fajl; u PowerShell-u koristi se `&` ispred putanje u navodnicima. Putanja je lokalna pogodnost, ne obaveza drugih uredjaja.

`python -B research/observe_10k.py status` cita 13 planiranih termina i postojece receipte; ne pristupa internetu i ne pise stanje.

## Provera javnog sajta

`npm run test:site` je read-only provera glavnog interfejsa. Ona salje spoljne GET zahteve ka `https://3esign.github.io/beops/`, sa cache-busterom, uporedjuje zivi `index.html` sa `Beops-public/docs/index.html`, kratko ceka GitHub Pages propagaciju, proverava osnovne ugradjene stranice (`podaci`, `monolog`, `sada`, `traka`, `svedoci`) i pada ako se vrati stara javna atribucija ili drugi poznat stale marker. To je posle-publish provera zivog sajta; ne zamenjuje `npm test`, koji ostaje offline gate pre objave.

## OBS-001 upis

`python -B research/observe_10k.py capture` se poziva samo iz vec podesene automatizacije u ovoj sesiji. Alat je ogranicen na datume observacije. Ne podizati drugi scheduler ili novi servis.

Jedan slot dobija trajan `claim-*.json` pre GET-a i potpun `sample-*.json` posle. Upis koristi privremeni fajl, fsync i hard-link objavu bez prepisivanja na istom disku. Ako to fajl-sistem ne podrzi, staje pre mreze; ne menjati u prepisivanje starih dokaza. Svi testovi koriste privremene foldere, nikad pravi folder observacije.

Na ponovljen termin ne ide drugi zahtev. Ako proces nestane posle claim-a, ostaje nedovrsen trag i rupa; ne uklanjati claim automatski. 403/429 u receipt-u pauzira izvor i za naredne termine. Posle pada pre upisa odgovora HTTP ishod nije poznat; to ne predstavljati kao uspesno merenje.

Kasnjenje do 20 minuta belezi stvarno vreme prijema, ne vreme izvornog merenja. Veca kasnjenja preskacu slot. Na kraju `status` daje pokrivenost; izvestaj koristi samo stvarne uzorke i jasno prikazuje propuste. Granice i grupisanje lokacija su u [protokolu](research/observations/10k-2026-09-05/PROTOKOL.md).

## Gde je sta

- [Struktura projekta](research/STRUCTURE_CONTRACT_2026-09-11.md): sta je izvor, dokaz, generisano javno stanje, privatni audit, ziva memorija i ostatak.
- [Operativni red](research/OPERATIONAL_ORDER_2026-09-11.md): privatni Beops, javni mirror, C/D pravilo, scheduler i publish safety.
- [Research indeks](research/README.md): svi istrazivacki dokumenti i vazeci paper lineage.
- [Detaljan program cula i modela](research/01-programme/PLAN_CULA_MODELI_2026-09-05.md): istrazivacki ciklus, 25 cula, 12 eksperimenata i 48 razrada postojecih zadataka.
- [Banka pretrage](research/01-programme/PRETRAGA_KEYWORDS_2026-09-05.md): 64 pocetna upita, pravila izdvajanja i prosirivanja pojmova; nije automatski izvrsena pretraga.
- [Katalog modela/provajdera](research/03-models/KATALOG_MODELA_I_PROVAJDERA_2026-09-05.md): konkretni izbori, statusi proba i razlike izmedju distributera i inference servisa.
- [README](README.md): ulazi u dosije i status projekta.
- [Radni program](research/01-programme/RADNI_PROGRAM.md): 65 zadataka, zavisnosti i dokaz zavrsetka; nije automatsko ovlascenje da se sve pokrene.
- [Prostorni koncept](research/01-programme/ZONE_I_POVEZIVANJE.md): zajednicki filter, spoljne reference i bez mikronivoa.
- [Provere](research/_trail/VERIFICATION_2026-09-05.md): istorija stvarno izvrsenih provera.
- `RECNIK.jsonl`, `KNOWLEDGE.md`, `LOG.md`: definicije, odluke/lekcije i trag rada kroz postojeci projektni kit.
