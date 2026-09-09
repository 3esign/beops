# Beops — Uputstvo za izradu

Operativno uputstvo, uskladjeno 05.09.2026. Pocetna tacka za sledeci rad; istorijski izvestaji ne nadjacavaju kasnije odluke korisnika.

## Pravila izrade
- Beops je samo Beograd. Pazarac ostaje zaseban projekat i izvor lekcija.
- Ceo Beograd -> vece celine -> sire zone. Ostajemo na pulsu; nema mikronivoa, pojedinaca ili zgrada kao javnog nivoa analize.
- Jedan prostorni filter kroz sve domene. Dedup na roditeljskom nivou; nepokrivenost se ne popunjava izmisljenim prosekom.
- Povezujemo postojece izvore i usluge; nema sopstvenog indeksa grada, geokodera ili nove infrastrukturne platforme.
- Parking/prevoz, javne i kulturne promene, dokumentovane cene i atmosfera/voda napreduju zajedno. Zvuk, kamere i tlo su istrazivacki pravci sa otvorenim pristupnim pitanjima.
- UI je odlozen, mozda nepotreban. `server.js`, `src/`, `public/` i stari `tools/collect.js` su neaktivni i neverifikovani nacrti; `npm start` i `npm run collect` nisu put do istrazivackog rezultata.
- Malo racunanja: jedan javni odgovor gde sadrzi vise lokacija, bez ponovnog geokodiranja i bez ucitavanja svih modela. Nema novih zavisnosti.
- Izvorna vremena i jedinice ostaju tacni. Primljeno sada nije izmereno sada; najavljeno nije ostvareno; nema podataka nije nula.
- Analiticke beleske su vidljivo tumacenje dokaza. Ne glume dodatni instrument i ne dokazuju uzrocnost.
- Bez novih agenata. Jezgro Svemira, tudji projekti i tajne ne diraju se kroz ovaj projekat.

## Faze
1. Istrazivacka osnova i povezivanje: izvori, uslovi, trag, recnik, zonska granularnost i testirane male probe.
2. OBS-001: posebno odobrena opisna observacija trke, protokol i pocetni uzorak vec postoje; zakazani uzorci tek slede.
3. Uporedivi domenski uzorci i model benchmark: planirano, bez automatskog pokretanja.
4. Rad i eventualni javni oblik: tek iz rezultata; rok/prihvatanje konferencije i pravo objave posebno proveriti.

## Provera bez mreze

`npm test` izvrsava Python stdlib testove kroz mali Node pokretac, bez instalacije. `BEOPS_PYTHON` moze zadati drugi Python 3.9+. Testovi nisu provera frontend-a ili punog Svemira.

Na ovom PC-u proveren Python je `C:/Users/treed/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`. Kada `python` nije na PATH-u, pozvati taj izvrsni fajl; u PowerShell-u koristi se `&` ispred putanje u navodnicima. Putanja je lokalna pogodnost, ne obaveza drugih uredjaja.

`python -B research/observe_10k.py status` cita 13 planiranih termina i postojece receipte; ne pristupa internetu i ne pise stanje.

## OBS-001 upis

`python -B research/observe_10k.py capture` se poziva samo iz vec podesene automatizacije u ovoj sesiji. Alat je ogranicen na datume observacije. Ne podizati drugi scheduler ili novi servis.

Jedan slot dobija trajan `claim-*.json` pre GET-a i potpun `sample-*.json` posle. Upis koristi privremeni fajl, fsync i hard-link objavu bez prepisivanja na istom disku. Ako to fajl-sistem ne podrzi, staje pre mreze; ne menjati u prepisivanje starih dokaza. Svi testovi koriste privremene foldere, nikad pravi folder observacije.

Na ponovljen termin ne ide drugi zahtev. Ako proces nestane posle claim-a, ostaje nedovrsen trag i rupa; ne uklanjati claim automatski. 403/429 u receipt-u pauzira izvor i za naredne termine. Posle pada pre upisa odgovora HTTP ishod nije poznat; to ne predstavljati kao uspesno merenje.

Kasnjenje do 20 minuta belezi stvarno vreme prijema, ne vreme izvornog merenja. Veca kasnjenja preskacu slot. Na kraju `status` daje pokrivenost; izvestaj koristi samo stvarne uzorke i jasno prikazuje propuste. Granice i grupisanje lokacija su u [protokolu](research/observations/10k-2026-09-05/PROTOKOL.md).

## Gde je sta

- [Detaljan program cula i modela](research/01-programme/PLAN_CULA_MODELI_2026-09-05.md): istrazivacki ciklus, 25 cula, 12 eksperimenata i 48 razrada postojecih zadataka.
- [Banka pretrage](research/01-programme/PRETRAGA_KEYWORDS_2026-09-05.md): 64 pocetna upita, pravila izdvajanja i prosirivanja pojmova; nije automatski izvrsena pretraga.
- [Katalog modela/provajdera](research/03-models/KATALOG_MODELA_I_PROVAJDERA_2026-09-05.md): konkretni izbori, statusi proba i razlike izmedju distributera i inference servisa.
- [README](README.md): ulazi u dosije i status projekta.
- [Radni program](research/01-programme/RADNI_PROGRAM.md): 65 zadataka, zavisnosti i dokaz zavrsetka; nije automatsko ovlascenje da se sve pokrene.
- [Prostorni koncept](research/01-programme/ZONE_I_POVEZIVANJE.md): zajednicki filter, spoljne reference i bez mikronivoa.
- [Provere](research/_trail/VERIFICATION_2026-09-05.md): istorija stvarno izvrsenih provera.
- `RECNIK.jsonl`, `KNOWLEDGE.md`, `LOG.md`: definicije, odluke/lekcije i trag rada kroz postojeci projektni kit.
