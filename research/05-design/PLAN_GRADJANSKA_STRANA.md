# BEOPS · dve strane jednog instrumenta
Plan, 2026-09-25. Status: predlog, ruke se nisu pomerale osim ovog fajla.

## 1. Odgovor na "da li je to na GitHubu moguce"

Jeste, bez trika. GitHub Pages sluzi ceo `docs/` folder (main branch, /docs) i svaki
`.html` u njemu je vec sopstvena ruta. Danas ih ima 10 (`sada`, `podaci`, `traka`,
`naslovi`, `svedoci`, `obrasci`, `kontekst`, `monolog`, `ai-feed`, `index`) i sve rade.
Dodavanje jos jedne strane ne trazi server, build sistem ni subdomen.

Potez je preimenovanje, ne preseljenje:

| ruta | sada | posle |
|---|---|---|
| `/` (`index.html`) | instrument (379 KB, 37 izvora, registar, dokazi) | **Beograd danas** — gradjanska strana |
| `/instrument.html` | — | sadasnja glavna, nepromenjena, samo pod svojim imenom |
| ostalih 9 | dokazni podlistovi | isto, netaknuto |

Adresa ostaje ista, pa rad i PDF koji citiraju beops URL i dalje rade — samo sada
doceka gradjanin, a prvi red zaglavlja je `Instrument →`.

## 2. Sta gradjanin vidi (pet blokova, odozgo nadole)

1. **Jedna recenica.** "Sada 14 °C, vazduh umeren, kise nema." Ispod sitno: kada je
   mereno i sa koliko stanica. Ako podatak kasni — pise da kasni.
2. **Mogu li danas…** cetiri-pet kartica sa odgovorom, ne sa brojem:
   napolje sa decom · trcanje · provetravanje · bicikl · ves na terasi.
   Svaka: DA / OPREZ / NE + jedan razlog + link na merenje iz kog je odgovor izveden.
3. **Danas u Beogradu.** Ritam grada: desavanja (kultura, sport, skupovi), izmene
   linija, radovi i zatvaranja — svako sa *gde*, *kada* i uslovima na licu mesta.
4. **Receno / Izmereno.** Naslov levo, merenje desno, oznaka slaganja. Ovo je jedini
   blok koji ni jedan drugi gradski sajt nema.
5. **Zasto nam verovati.** Tri broja (izvora · sati evidencije · polja bez cula) i
   veliko dugme **Dokazi → Instrument**.

## 3. Pravilo koje razdvaja ovu stranu od portala

**Svaka recenica je link.** Klik vodi tacno na red u instrumentu iz kog je recenica
nastala. Nema tvrdnje bez putanje do dokaza, i nema broja koji je izmisljen da bi
kartica izgledala puna: ako merenja nema, kartica kaze *ne znam* — ne nulu.
Isto pravilo koje vec drzi instrument, samo prevedeno na jezik grada.

## 4. Stil: "enhanced, ali suptilno"

Isti tokeni (`--field`, `--ink`, `--signal`, mono za brojeve), ista tipografija, isti
sum u pozadini. Razlika je u ritmu, ne u paleti:
- prvi ekran krupan i prazan, jedna recenica i nista drugo;
- kartice mekse (veci radijus, tanja linija), bez senki;
- jedno jedino kretanje na strani — traka pulsa poslednja 24 h;
- nista sto se vrti, trepce ili iskace.
Paleta se ne dira. Ako se dira — dira se na oba mesta.

## 5. Tehnicki redosled

1. `git mv docs/index.html` logikom u `build_site.py`: izlaz instrumenta ide u
   `instrument.html`; nova `build_public_page.py` pise `index.html`.
2. Nova strana se hrani iskljucivo postojecim JSON-ovima:
   `live-snapshot.json`, `history-7d.json`, `headlines.json`, `watch.json`,
   `city-overview.json`. Nula novih zavisnosti, nula novih servisa.
3. `verify_public_site.js`: 178 → 180 ruta (nova `/` i `/instrument.html`).
4. Testovi za nove tvrdnje: svaka kartica mora imati izvor ili stanje *nepoznato*;
   test golog ekrana (strana bez podataka ne sme da laze).

## 6. Sta jos ne postoji

Blok 3 (desavanja) nema organ. Treba `tools/collect_events.py` — Beoinfo, zvanicni
repertoari ustanova, saobracajne najave — i `events.json`. Dok ga nema, blok stoji
prazan sa recenicom "jos ne merimo", ne sa izmisljenim kalendarom.

Zato red poslova: **(a)** preimenovanje i skelet · **(b)** blokovi 1, 2, 4, 5 iz onoga
sto vec merimo · **(c)** organ desavanja · **(d)** blok 3.
