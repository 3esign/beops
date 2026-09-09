# BEOPS — Draft zahteva za 3 JP agregata (faza Build v1)

Datum: 05.09.2026, ~15:15 lokalno (13:15 UTC). Faza: Build v1 (Svemir).
Svrha: pripremiti tekst zahteva za 3 najlakša javna preduzeća (JP) agregata — **bez slanja**. Slanje je Semirova odluka. Zahtevi su uvek za **agregat**, nikad za redove sa ličnim podacima. Status svih: **NEPOTVRĐENO** da li bilo koji JP već objavljuje te podatke; ovo su kandidati za zahtev, ne nalazi da feed postoji.

## Pravila zahteva (zajednička)

- Tražimo **agregat** (broj, zbir, vreme), ne identifikaciju pojedinaca, vozila, domaćinstava ili adresa.
- Navodimo tačan oblik agregata koji tražimo, da organizacija zna šta tačno šaljemo.
- Ne tražimo sirove snimke, tablice, GPS pozicije pojedinačnih vozila, niti lične podatke.
- Svaki zahtev je open-data zahtev ili predlog partnerstva; odgovor se dokumentuje pre bilo kakvog daljeg koraka.

---

## Zahtev 1 — JKP Parking Servis: javna dozvola za čitanje postojećeg endpoint-a

**Organizacija:** JKP "Parking servis" Beograd.
**Šta već postoji:** javni endpoint `https://www.parking-servis.co.rs/lat/garaze-i-parkiralista` sa prikazanim brojem slobodnih mesta po lokaciji (27 lokacija; već probano u OBS-001 i multidomain probi).
**Šta tražimo:** zvaničnu dozvolu da čitamo taj isti javni endpoint ritmom OBS-001 (jedan snimak na sat, 13 slotova) i da objavimo izvedene agregate (promena slobodnih mesta po lokaciji i vremenu), bez identifikacije vozila ili korisnika.
**Tačan oblik agregata:** `{lokacija, slobodna_mesta, vreme_prijema}` po satu; bez ukupnog kapaciteta (ne računamo procenat popunjenosti), bez brojača prolazaka.
**Granica/rizik:** redistribution terms nisu potvrđeni; ne pretpostavljamo da je javni prikaz = dozvola za ponovnu objavu.

## Zahtev 2 — JKP "Javno osvetljenje" Beograd: vreme uključenja po zoni

**Organizacija:** JKP "Javno osvetljenje" Beograd.
**Šta sistem već loguje:** uključenje/isključenje po zoni, kvarovi, potrošnja.
**Šta tražimo:** dnevno vreme uključenja/isključenja po zoni + spisak kvarova (agregat, bez adresa pojedinačnih stubova ako je osetljivo).
**Tačan oblik agregata:** `{zona, datum, vreme_ukljucenja, vreme_iskljucenja, broj_kvarova}` dnevno.
**Granica/rizik:** operativni podatak, ne nužno javni; može biti odbijen kao operativni.

## Zahtev 3 — Gradski zavod za hitnu pomoć / MUP: broj poziva po opštini i satu

**Organizacija:** Gradski zavod za hitnu pomoć Beograd (ili MUP Sektor za vanredne situacije).
**Šta sistem već loguje:** broj i tip poziva po opštini/satu.
**Šta tražimo:** **samo gustinu** — agregat broja poziva po opštini i satu, **bez lokacije poziva, bez adresa, bez identifikacije pozivaoca**.
**Tačan oblik agregata:** `{opstina, sat, broj_poziva}` — nikad adresa, nikad tip pojedinačnog poziva.
**Granica/rizik:** vrlo osetljivo; samo gustina, nikad adrese; može biti odbijen — to je legitimno.

---

## Honest verdict

Urađeno: pripremljena 3 zahteva sa tačnim oblikom agregata, bez slanja. Nije urađeno: slanje bilo čega (Semirova odluka), potvrda da bilo koji JP objavljuje te podatke. Ovo su kandidati za zahtev, ne nalazi o postojanju feeda.
