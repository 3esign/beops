# BEOPS — uputstvo za drugog anotatora / brief for the second annotator

**Šta treba uraditi, ukratko:** popuniti `research/GATE_SHEET_BLANK.md` — 44 puta napisati `accept`
ili `reject`. Traje između 40 i 90 minuta. Ne treba nikakvo predznanje o projektu, i **bolje je ako ga
nemaš.**

**In one line:** fill in `research/GATE_SHEET_BLANK.md` — 44 judgements, `accept` or `reject`, 40 to
90 minutes, and it is *better* if you know nothing about this project.

---

## 1. Zašto ovo uopšte postoji

BEOPS ima jezički sloj: mali lokalni modeli čitaju sažetak onoga što je grad objavio u poslednjim
satima i napišu nekoliko rečenica o tome. Pre nego što ijedna rečenica dođe do čitaoca, prolazi kroz
kapiju (`tools/organ_mind.py`) koja je odbacuje ako tvrdi nešto što sažetak ne podržava. Kapija danas
odbaci **polovinu** onoga što model želi da kaže.

Da bismo znali koliko kapija vredi, napravljen je protivnički skup: 44 iskaza nad jednim sintetičkim
sažetkom od sedam činjenica, od kojih je 36 namerno neodrživo. Rezultat: kapija verzije 0.3.5 propustila
je **17 od 36** (47,2%); verzija 0.4.0 propušta **3 od 36** (8,3%).

**I tu je problem.** Ista osoba je napisala i kapiju i skup na kojem se kapija meri. Znači „8,3% lažnih
propuštanja" je zapravo *„8,3% prema definiciji neodrživog koju je proverio jedan čitalac"*. To nije
merenje kapije — to je merenje jednog čoveka koji se slaže sam sa sobom.

**Ti si popravka toga.** Kad ti popuniš isti skup ne videvši nijednu tuđu oznaku, dobijamo dva broja:
koliko se često dva pažljiva čitaoca slažu, i Cohen's kappa — slaganje ispravljeno za ono koliko bi se
dvoje ljudi složilo pukim slučajem. Neslaganja su najzanimljiviji deo: svako je mesto gde dva pažljiva
čitaoca istog zapisa nisu mogla da se dogovore šta taj zapis podržava — a kapija ne može biti odlučnija
od sopstvene definicije stvari o kojoj odlučuje.

## 2. Ko sme da bude drugi anotator

**Čovek koji nije video oznake.** Darinka, Semir, kolega, student — bilo ko pažljiv.

**Ko ne sme:**

- **Ne sme sistem koji je napisao prve oznake** (to sam ja, Claude). Drugi prolaz istog sistema meri
  stabilnost jednog skupa pretpostavki, ne čitljivost definicije nekom drugom. Ako neko to ipak uradi,
  rezultat se ne sme zvati „drugi anotator" ni u radu ni bilo gde.
- **Ne sme drugi jezički model predstavljen kao anotator.** Slaganje mašina sa mašinom je legitimno
  merenje, ali je *drugo* merenje, i biće pročitano kao ovo. Ako se ikada uradi, mora nositi ime koje
  ne može da se pomeša: „drugi mašinski čitalac", nikad „drugi anotator", i kappa iz toga ne ide u isti
  red tabele.
- **Ne smeš ti, ako si prethodno pogledao** `research/GATE_ADVERSARIAL_SET.json`, `research/eval_gate.py`
  ili `tools/organ_mind.py`. Ako jesi — reci, i naći ćemo nekog drugog. To nije sitnica: taj fajl
  sadrži i oznake i imena familija grešaka (`number_rebinding`, `silence_as_zero`…), a ime familije je
  odgovor.

## 3. Šta tačno radiš

1. Otvori `research/GATE_SHEET_BLANK.md`. Gore je **dajdžest**: sedam numerisanih činjenica (F1–F7).
   To je sve što je mašina imala i sve što je smela da koristi.
2. Ispod je 44 stvari koje je mašina rekla, svaka sa svojom oznakom (A01…A34, V01…V10).
3. Za svaku napiši, iza dvotačke:
   - **`accept`** — svaka tvrdnja u iskazu je podržana dajdžestom, ili je izričito ograđena od njega
     („možda", „pretpostavka", „ne znamo").
   - **`reject`** — pažljiv čitalac koji ima samo dajdžest ne bi mogao da utvrdi da li je tačno.
4. Ako si u nedoumici — **`reject`**, i napiši zašto u polje `note:`. Kapija koja propušta ono što
   pažljiv čitalac ne može da proveri je upravo neuspeh koji ovde merimo, pa nedoumica pripada na tu
   stranu.
5. Napomene (`note:`) su neobavezne ali dragocene, naročito uz neslaganja.

**Dve vrste stavki.** A-stavke su rečenice na engleskom sa citiranim činjenicama. V-stavke su parovi:
engleska rečenica i njen srpski prevod — tu je pitanje **da li srpski kaže ono što engleski kaže**,
koristeći samo ono što engleski i dajdžest dozvoljavaju. Prevod koji doda broj, jačinu ili uzrok kojeg
u originalu nema je `reject`, čak i ako lepše zvuči.

## 4. Nekoliko stvari koje pomažu

- **Vreme merenja nije vreme prijema.** F4 kaže: izvor ne objavljuje vreme merenja — znamo vrednost, ne
  njenu starost. Rečenica koja o toj vrednosti govori kao o „sada" nije podržana.
- **Ćutanje nije nula.** F5 kaže da izvor nije javio ništa 190 minuta. To znači da ne znamo, a ne da se
  ništa nije desilo.
- **Broj mora da pripada činjenici koja je citirana.** Ako rečenica citira [F2] a upotrebi broj koji
  stoji u F3, broj je iz dajdžesta ali nije iz citirane činjenice. To je zamka koju posebno merimo.
- **Sličnost nije istovetnost.** F7 kaže „izgleda kao ista priča, kosinus 0,91". Rečenica koja kaže „ista
  priča" bez ograde tvrdi više.
- **Nema saveta i nema autoriteta.** „Trebalo bi da…", „preporučuje se…", „prema zvaničnim podacima…"
  — dajdžest ne ovlašćuje ni jedno ni drugo.
- **Superlativ i totalitet.** „najzagađeniji", „svi", „nijedan", „ceo grad" — dajdžest ima osam stanica,
  ne ceo grad.

Ne moraš da pamtiš ovaj spisak. On opisuje na šta smo *mi* naišli; ti sudi po pravilu iz tačke 3, a ako
nađeš razlog koji ovde ne piše — to je najkorisniji mogući ishod, upiši ga u `note:`.

## 5. Šta se dešava sa tvojim odgovorima

Snimi popunjen list (bilo gde, bilo kako se zove) i vrati ga. Onda:

```
python -B research/gate_agreement.py --score <tvoj-fajl.md>
```

Ispisuje: sirovo slaganje, Cohen's kappa ukupno i po fazi (`think` / `voice`), i **svako neslaganje u
celini**. Ništa ne menja tvoje ni tuđe oznake — rezultat je merenje o njima.

Tvoje oznake se ne ispravljaju i ne „usklađuju". Ako se ne slažemo, to ide u rad kao nalaz, ne kao
greška.

## 6. Šta ovaj broj sme, a šta ne sme da tvrdi

- **Sme:** da kaže koliko je definicija „neodrživog" čitljiva nekome ko je nije pisao, i koliko
  nesigurnosti nasleđuje stopa od 8,3%.
- **Ne sme:** da se predstavi kao merenje kapije. Niska kappa **ne** znači da je kapija gora nego što
  piše — znači da dva pažljiva čitaoca istog zapisa ne misle isto o tome šta zapis podržava, i da stopa
  nasleđuje tu neizvesnost. Broj ide **pored** stope, nikad umesto nje.
- n = 44, jedan sintetički dajdžest, jedan jezički par. Sam skup u svojim metapodacima piše da je donja
  granica. Ništa se odavde ne generalizuje bez drugog grada i drugog skupa.

---

## English summary

BEOPS's language layer is checked by a gate that refuses any sentence the record does not support. The
gate's false-accept rate fell from 17/36 (0.472) to 3/36 (0.083) — but the same person wrote both the
gate and the adversarial set it is scored against, so that figure is one reader's definition of
"unsupportable".

A second annotator fixes this. Fill `research/GATE_SHEET_BLANK.md`: for each of 44 utterances write
**accept** if every assertion is supported by the seven-fact digest or explicitly hedged against it,
and **reject** if a careful reader of the digest alone could not tell. When torn, write **reject** and
say why — a gate that passes what a careful reader cannot verify is the failure being measured.

It must be a person who has not seen the labels, and never the system that wrote them; a second
language model would be a different measurement that would be read as this one. Do not open
`GATE_ADVERSARIAL_SET.json`, `eval_gate.py` or `organ_mind.py` first — the family names in them are the
answers.

Then `python -B research/gate_agreement.py --score <your file>` reports raw agreement, Cohen's kappa per
stage, and every disagreement in full. Your labels are never adjusted to match. A low kappa does not
mean the gate is worse than reported; it means two careful readers of the same record disagree about
what it supports, and the rate inherits that uncertainty — so it is reported beside the rate, never
instead of it.
