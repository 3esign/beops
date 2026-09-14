# Matrica svrhe, pristupa i prava korišćenja (R08)

Ovaj dokument razdvaja pristupni signal od pravne osnove i svrhe obrade (BEO-046). Robots.txt ili odsustvo zabrane u HTTP zaglavljima shvataju se isključivo kao *tehnički signal pristupa*, a ne kao autorska licenca ili pravni osnov obrade. 

## 1. Pristup naspram prava korišćenja (BEO-046)
- **Tehnički pristup (Crawl/Fetch):** Potvrđuje se kroz obots.txt, TDM zaglavlja i statusne kodove. Ovo je samo dokaz da server nije tehnički zabranio pristup. 
- **Pravni osnov (Upotreba/Zadržavanje):** Tehnički pristup ne daje automatsku licencu. Pravo na zadržavanje i prikazivanje se oslanja na specifične izuzetke (citat, pravo informisanja, službeni tekst) i legitimni interes/naučno istraživanje.

## 2. Matrica po klasama podataka (BEO-023, BEO-048, BEO-047)

| Klasa / Izvor | Tehnički signal pristupa | Zadržavanje i Arhiva | Javni prikaz / Izlaz | Prekogranični model (AI) |
| --- | --- | --- | --- | --- |
| **RSS Vesti (Mediji)** | Dozvoljen pristup (RSS standard). | Kratki metapodaci (naslov, link, vreme). Nema arhiviranja punog teksta. | Obim kratkog citata (ZASP čl. 49). Nije dozvoljena trajna obrada celog teksta. | NE šalju se spoljnim LLM provajderima. Obrađuje ih lokalni model (organ_news). |
| **Službeni podaci ustanova** | Javni API / Open Data. | Puni rezultati merenja. | Objavljuju se kao sirovi podaci. | NE. Samo statistike. |
| **Sadržaj na sajtovima ustanova** | Dozvoljen crawl. | Zavisi od vrste fajla (BEO-048). | Ne tretira se automatski sve kao "službeni materijal". Razlikovati bazu podataka, sliku i zvanični akt. | NE. |

*Napomena za BEO-047: Obično citiranje naslova ne znači pravo na arhiviranje punih tekstova novinskih članaka. Beops zato čuva strogo samo naslov bez tela vesti.*
*Napomena za BEO-048: Status javne ustanove ne znači da su sve fotografije i tekstovi na njenom sajtu "službeni materijal" izuzet od zaštite.*

## 3. Prekogranični prenos i hosting (BEO-043)
- Okolnost da je neki podatak "već javno dostupan" na internetu ne suspenduje pravila prekograničnog prenosa podataka o ličnosti (ZZPL). 
- **Obrada u BEOPS-u**: Kompletan proces ekstrakcije i čuvanja odvija se lokalno na serverima u Srbiji. GitHub (javni export) hostuje se eksterno, pa se na taj deo primenjuje izuzetak ili adekvatna zaštita minimizacijom (heševi i pseudonimizacija gde je neophodno). Ne oslanjamo se na puku "javnost" kao blanketni osnov prenosa.

## 4. Primena AI Act-a (BEO-051)
- Dosadašnja tvrdnja "AI Act se ne primenjuje jer smo u Srbiji" je nepotpuna i uklonjena iz tvrdnji projekta.
- **Korekcija:** Teritorija EU nije jedini test za AI Act. Ipak, s obzirom na to da su izlazi usmereni na lokalnu analizu i da AI alati u BEOPS-u služe isključivo za klasifikaciju i agregaciju (bez donošenja automatizovanih odluka o pojedincima ili visokorizičnih modela), procena rizika pokazuje da operacije spadaju u sisteme minimalnog/nultog rizika. Uz to, striktno primenjujemo **Član 50 (Transparentnost)** označavanjem svih generisanih tekstova kao "ai_generated=true".

## Zbirni dokaz
Ovaj dokument, uz implementiranu arhitekturu, čini evidenciju za zahteve iz R08. Svaka klasa ima jasno definisan red, dokaz i neizvesnost. Nema automatske pravne potvrde pukim preuzimanjem bajta.
