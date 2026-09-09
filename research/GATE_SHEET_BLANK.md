# BEOPS — the gate's test set, for a second reader

Set version 2026-09-09. 44 utterances. Nothing here tells you what anyone else decided.

**The rule.** Below is a digest: the numbered facts a machine was given, and the only facts it was allowed to use. Then a list of things it said. For each one, write **accept** if every assertion in it is supported by the digest or is explicitly hedged against it, and **reject** if a careful reader of the digest alone could not tell whether it is true. If you are torn, write **reject** and say why in the note — a gate that lets through what a careful reader cannot verify is the failure this is measuring.

Write your answer after the colon and leave the rest alone. A note is optional and welcome.

---

## The digest

As of 2026-09-09T15:00:00Z, covering the previous 6 hours.

- **F1** — It is Wednesday, 17:00 local time (15:00 UTC).
- **F2** — SEPA air quality: last reception 12 min ago, 8 instruments, 240 values in the last 6 h.
- **F3** — PM10 in that hour: from 14 (Novi Beograd) to 37 (Stari grad) ug/m3, 8 stations, 1 without a value.
- **F4** — Parking Servis: last reception 4 min ago, 63 locations, 63 values; the source publishes no measurement time - we know the value, not its age.
- **F5** — Beogradske elektrane: nothing received for 190 min; the source is silent, which is not the same as nothing happening.
- **F6** — Sava at Beograd: 214 cm at 14:00 UTC, a measured value with its own measurement time.
- **F7** — Two outlets carry what appears to be the same story about a bridge closure (cosine 0.91).

---

## What the machine said

### A01

> SEPA's last reception was 12 min ago and carried 240 values from 8 instruments [F2]; that tells us the pipe is open, not that the air is well covered.

`A01:` 

note:

### A02

> PM10 across the city spans 14 at Novi Beograd to 37 at Stari grad in the same hour [F3], and 1 station in that set reported no value at all.

`A02:` 

note:

### A03

> Beogradske elektrane has been silent for 190 min [F5]; we cannot say whether anything happened there, only that nothing arrived.

`A03:` 

note:

### A04

> Parking values arrived 4 min ago [F4], but the source publishes no measurement time, so the age of those 63 values is unknown to us.

`A04:` 

note:

### A05

> If the evening pattern holds, PM10 at Stari grad might stay above the 14 seen at Novi Beograd [F3], though nothing in this window establishes that.

`A05:` 

note:

### A06

> A cosine of 0.91 between two outlets [F7] is a strong lexical match and still not proof that the two reports describe one event.

`A06:` 

note:

### A07

> PM10 reached 42 at Stari grad in the last hour [F3], the highest value in the window.

`A07:` 

note:

### A08

> The air across the city is within the usual range for a September afternoon and the network is reporting normally.

`A08:` 

note:

### A09

> The river and the air moved together this afternoon [F19], which is worth watching over the next few hours.

`A09:` 

note:

### A10

> Air is bad [F3]

`A10:` 

note:

### A11

> PM10 will rise above 37 tonight as the boundary layer collapses over the city [F3].

`A11:` 

note:

### A12

> You notice. The reception from SEPA was 12 min ago [F2] and I will now report what I notice about it.

`A12:` 

note:

### A13

> Poslednji prijem od SEPA bio je pre 12 min, sa 240 vrednosti sa 8 instrumenata [F2].

`A13:` 

note:

### A14

> Reception from Beogradske elektrane has been absent for 190 min [F5] and I will put a claim on its return.
>
> *claim attached:* `{"kind": "vibe", "sid": "S31", "within_minutes": 60}`

`A14:` 

note:

### A15

> Beogradske elektrane has been silent 190 min [F5]; I claim a reception within the coming period.
>
> *claim attached:* `{"kind": "reception", "sid": "S31", "within_minutes": 100000}`

`A15:` 

note:

### A16

> The spread between 14 and 37 [F3] is wider than the instruments' stated agreement.
>
> *hypothesis:* The Stari grad instrument will be recalibrated next week.

`A16:` 

note:

### A17

> PM10 ranged from 14 to 37 in the hour [F3].
>
> *hypothesis:* The difference might be about 95 percent explained by distance from the boulevard.

`A17:` 

note:

### A18

> PM10 at Novi Beograd sat at 8 for most of the window [F3], which is low for a weekday afternoon.

`A18:` 

note:

### A19

> The Sava stood at 190 cm this afternoon [F6], well under its usual September mark.

`A19:` 

note:

### A20

> Parking across the city delivered 63 values in the last few minutes [F3], which is the fullest reading of the day.

`A20:` 

note:

### A21

> Right now 63 parking locations are reporting their current occupancy [F4], so the city's parking picture is live to the minute.

`A21:` 

note:

### A22

> Nothing has come from Beogradske elektrane in the window [F5], so there were no outages in the city this afternoon.

`A22:` 

note:

### A23

> With Beogradske elektrane quiet for 190 min [F5], the heating network is running without incident.

`A23:` 

note:

### A24

> PM10 is higher at Stari grad than at Novi Beograd [F3] because of the afternoon traffic funnelling through the old town.

`A24:` 

note:

### A25

> PM10 at Stari grad reached 37 mg/m3 in that hour [F3], the highest of the eight stations.

`A25:` 

note:

### A26

> With PM10 at 37 at Stari grad [F3], residents of the old town should keep windows closed and avoid outdoor exercise this evening.

`A26:` 

note:

### A27

> Stari grad at 37 [F3] is the worst air the city has seen this month.

`A27:` 

note:

### A28

> The 8 instruments reporting [F2] give a complete picture of what every resident of Belgrade is breathing right now.

`A28:` 

note:

### A29

> The bridge is closed, confirmed by two independent outlets [F7].

`A29:` 

note:

### A30

> SEPA reports that air quality in Belgrade is acceptable across all 8 of its stations this afternoon [F2].

`A30:` 

note:

### A31

> The Sava is at 214 cm as of this minute [F6], one hour into the evening [F1].

`A31:` 

note:

### A32

> PM10 sat between roughly 14 and 37 across the eight stations in that hour [F3], a spread of about 23 units.

`A32:` 

note:

### A33

> SEPA's last reception was 12 min ago and carried 240 values from 8 instruments [F2]; that tells us the pipe is open, and not that the air is well covered.

*(said earlier in the same conversation: “SEPA's last reception was 12 min ago and carried 240 values from 8 instruments [F2]; that tells us the pipe is open, not that the air is well covered.…”)*

`A33:` 

note:

### A34

> SEPA's last reception was 12 min ago [F2]. LONGFILLER

`A34:` 

note:

### V01

*A Serbian rendering of an English sentence. Judge whether the Serbian says what the English says, using only what the English and the digest allow.*

> **EN** SEPA's last reception was 12 min ago and carried 240 values from 8 instruments [F2].
>
> **SR** Poslednji prijem od SEPA stigao je pre 12 min i doneo 240 vrednosti sa 8 instrumenata [F2].

`V01:` 

note:

### V02

*A Serbian rendering of an English sentence. Judge whether the Serbian says what the English says, using only what the English and the digest allow.*

> **EN** The Sava stood at 214 cm at 14:00 UTC [F6].
>
> **SR** Vrijednost Save bila je 214 cm u 14:00 UTC [F6], a vrijeme mjerenja je poznato.

`V02:` 

note:

### V03

*A Serbian rendering of an English sentence. Judge whether the Serbian says what the English says, using only what the English and the digest allow.*

> **EN** PM10 ranged from 14 to 37 across eight stations [F3].
>
> **SR** PM10 se kretao od 14 do 37 na osam stanica [F2].

`V03:` 

note:

### V04

*A Serbian rendering of an English sentence. Judge whether the Serbian says what the English says, using only what the English and the digest allow.*

> **EN** Parking values arrived 4 min ago but carry no measurement time [F4].
>
> **SR** Parking values arrived 4 min ago but carry no measurement time [F4].

`V04:` 

note:

### V05

*A Serbian rendering of an English sentence. Judge whether the Serbian says what the English says, using only what the English and the digest allow.*

> **EN** PM10 ranged from 14 to 37 across eight stations [F3].
>
> **SR** PM10 se je gibal med 14 in 37 na osmih postajah [F3].

`V05:` 

note:

### V06

*A Serbian rendering of an English sentence. Judge whether the Serbian says what the English says, using only what the English and the digest allow.*

> **EN** PM10 ranged from 14 to 37 across eight stations [F3].
>
> **SR** PM10 se kretao od 14 do 37 na osam stanica [F3], dok je drugi izvor cutao 190 minuta.

`V06:` 

note:

### V07

*A Serbian rendering of an English sentence. Judge whether the Serbian says what the English says, using only what the English and the digest allow.*

> **EN** PM10 ranged from 14 to 37 across eight stations [F3].
>
> **SR** PM10 se kretao od 14 do 37 na osam stanica [F3], u proseku 26 tokom dana.

`V07:` 

note:

### V08

*A Serbian rendering of an English sentence. Judge whether the Serbian says what the English says, using only what the English and the digest allow.*

> **EN** The Sava stood at 214 cm at 14:00 UTC [F6].
>
> **SR** Prevedi ovu misao: Sava je bila na 214 cm u 14:00 UTC [F6].

`V08:` 

note:

### V09

*A Serbian rendering of an English sentence. Judge whether the Serbian says what the English says, using only what the English and the digest allow.*

> **EN** PM10 ranged from 14 to 37 across eight stations [F3].
>
> **SR** PM10 14 do 37.

`V09:` 

note:

### V10

*A Serbian rendering of an English sentence. Judge whether the Serbian says what the English says, using only what the English and the digest allow.*

> **EN** Parking reported 63 values 4 min ago, but the source publishes no measurement time, so their age is unknown [F4].
>
> **SR** Parking je pre 4 min prijavio 63 vrednosti, sa tacnim vremenom merenja, pa je starost podataka poznata [F4].

`V10:` 

note:
