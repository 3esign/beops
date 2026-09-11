# Prvi otisak nije samo atmosfera

Novi prioritet korisnika: povezivanje vise oblasti od pocetka; prostorni fokus je opisan u ZONE_I_POVEZIVANJE.md (private working record). Poslednja odluka: ceo Beograd -> vece celine -> sire zone, bez mikronivoa. Primeri centralnih zona ispod su jedan filter, ne iskljucenje Novog Beograda. Bez nove interne geografske infrastrukture ili UI-ja.

## Nova direktna proba, 05.09.2026 oko 03:23 UTC

Dokaz (private working record) sadrzi deset HTTP odgovora i ogranicene ekstrakcije. Deset uspesnih prijema nije deset produkcijskih konektora.

| Oblast | Izmereno/pronadjeno | Sta jos ne znamo |
|---|---|---|
| Kretanje | Parking servis: 27 lokacija sa prikazanim slobodnim mestima i koordinatama | Tacan cas instrumenta, ukupan kapacitet i ugovor za javni izlaz |
| Voda | Zemun: 166 procitanih casovnih vrednosti; poslednja 173 cm u 02:00 UTC | Provisional kvalitet, voda se ne meri u svakoj zoni; nivo nije dubina niti protok |
| Prevoz | Zvanicna vest o izmenama za trku 10K, vise intervala i konkretne linije | Najava ne dokazuje realizovanu putanju ili stvarno kasnjenje autobusa |
| Komunalne usluge | BVK i EDS stranice odgovaraju | Ova proba nije strukturirala svaku ulicu i interval; nije dokaz stvarnog prekida |
| Ekonomija | Kengur BG01 javni CSV: 37.209 redova, 37.207 razlicitih ID-jeva, jedan red bez ID-ja | Nema opsteg datuma cenovnika u procitanim kolonama; ne izmisljati azurnost |
| Ekonomija | Delhaize CSV: 56.150 redova; 28.061 oznacen kao VAZECI_CENOVNIK sa datumom 05.09, 28.089 kao MESECNI_PRESEK od 01.09 | Format prodavnice nije precizna lokacija; ne racunati dva preseka kao duplu ponudu ili promet |
| Kultura | TOB stranica sa najavljenim dogadjajima odgovara | Najava nije potvrda odrzavanja ili posecenosti; TOB nije jedini niti kompletan kulturni izvor |
| Tlo | GFZ vraca sest kanalnih metapodataka za AVAS/BEO, 100/20 Hz navedene frekvencije | Nije preuzet waveform; otvoren epoch metapodataka nije dokaz poslednjeg zivog uzorka |

Primarni putevi: [Parking servis](https://www.parking-servis.co.rs/lat/garaze-i-parkiralista), [RHMZ Zemun](https://www.hidmet.gov.rs/latin/osmotreni/nrt_tabela_grafik.php?hm_id=42045&period=7), [BG prevoz](https://www.bgprevoz.rs/vesti), [Kengur katalog](https://data.gov.rs/sr/datasets/cenovnici/), [Delhaize katalog](https://data.gov.rs/sl/datasets/cenovnici-proizvoda-prema-pravilniku-o-uslovima-sadrzaju-i-nacinu-objavljivanja-cenovnika-delhaize-serbia-doo-beograd/), [GFZ servisi](https://geofon.gfz.de/waveform/webservices/).

## Prva zajednicka celina

Cetiri ravnopravna toka: parking/kretanje; javne izmene i dogadjaji; dokumentovane cene; atmosfera/voda. Za centar grada biramo izvore koji se mogu pripisati zoni; Zemun i sire meteo stanice su posebno oznacen kontekst, ne lokalno merenje Dorcola. Kamere, zvuk i kontinuirano tlo ostaju aktivni istrazivacki pravci sa otvorenim pristupnim pitanjima, ne blokiraju ostale oblasti.

Za ekonomiju vec proveren BG01 nije automatski unutar novog centralnog fokusa. On ostaje dokaz da format radi; sledeci izvor biramo po centralnoj lokaciji. Delhaize format bez prodavnice ostaje siri kontekst dok se ne resi teritorijalna primena cena.

Prva pitanja: sta se u zoni upravo promenilo; sta je najavljeno; sta je nedavno opazeno; koliko je svaki signal star; koji domen nedostaje. Ne trazimo da sve ima isti ritam. Dnevni cenovnik i polucasovni parking mogu zajedno opisivati grad bez pretvaranja da oba mere svaku sekundu.

## Verifikacija i granice

18/18 offline testova istrazivackih parsera prolazi, ukljucujuci nula/nedostaje, pogresnu CSV semu, mesecni cenovnik i fiksni UTC+1 vodostaja. Windows adapter za parking zadrzava proveru sertifikata; ranija Python TLS greska nije zaobidjena iskljucivanjem zastite.

Novi fajlovi `probe_multidomain.py`, `fetch_parking_windows.ps1` i `test_multidomain.py` su ogranicene istrazivacke probe. Nisu server, interni indeks ili zamena za spoljne izvore. Nisu ukljuceni u Svemir core. Nema model inferencije, javne publikacije ili automatskog snimanja ljudi.
