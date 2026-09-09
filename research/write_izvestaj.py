"""Write the OBS-001 report from real receipts only. Never invent a sample.

Runs after 22:50 UTC, or after the final slot is terminal and every earlier
slot is terminal or expired. It never captures or backdates a sample.

The report is a research record: it states what was received, what is missing,
and what the displayed numbers cannot tell us. It never attributes change to
the race, never fills gaps, and never turns a scheduled time into a source time.

Usage:
  python -B research/write_izvestaj.py [--folder <dir>] [--now <iso>] [--dry-run]

Without --folder it writes IZVESTAJ.md next to the receipts, but only if no
report exists there yet (append-only discipline, same spirit as observe_10k.py).
With --dry-run it prints the report to stdout instead of writing it.
"""
import argparse
import json
import hashlib
import os
import pathlib
import sys
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from observe_10k import FOLDER, GRACE, LAST, name, receipts, slots  # noqa: E402

REPORT = 'IZVESTAJ.md'

# Groups are descriptive, not control groups (protocol section "Sta pratimo").
# Names must match receipt bytes exactly (diacritics included).
GROUPS = {
    'Novobeogradsko/zemunsko okruzenje trke': [
        'Parkiralište "Opština NBGD"', 'Parkiralište "Belvil"', 'Garaža "Pinki "',
    ],
    'Centralno/obalno okruzenje': [
        'Parkiralište "Donji grad"', 'Parkiralište "Kalemegdan"',
        'Garaža "Zeleni venac"',
    ],
    'Prostorno udaljeniji opisni kontekst': [
        'Parkiralište "VMA"', 'Parkiralište "Cvetkova pijaca"',
        'Parkiralište "Bežanijska kosa"',
    ],
}


def utc(value):
    if value.tzinfo is None:
        raise ValueError('timezone required')
    return value.astimezone(timezone.utc)


def local(slot):
    """Europe/Belgrade is UTC+2 during this observation (protocol)."""
    return utc(slot) + timedelta(hours=2)


def cell(value):
    if value is None:
        return '—'
    return str(value)


def slot_state(folder, slot, now):
    """Same logic as observe_10k.inventory, read directly from disk."""
    target = folder / ('sample-' + name(slot) + '.json')
    claim = folder / ('claim-' + name(slot) + '.json')
    if target.exists():
        try:
            return json.loads(target.read_text(encoding='utf-8'))['state']
        except (ValueError, KeyError):
            return 'unreadable_receipt'
    if claim.exists():
        return 'claimed_unfinished'
    if now < slot:
        return 'pending'
    if now <= slot + GRACE:
        return 'due'
    return 'missing'


def coverage_rows(folder, now):
    rows = []
    for slot in slots():
        state = slot_state(folder, slot, now)
        rows.append((slot, state))
    return rows


def location_tables(samples):
    """One table per sample: every one of the 27 locations, displayed value."""
    tables = []
    for s in samples:
        if s['state'] != 'captured':
            continue
        rows = []
        for loc in s['summary']['locations']:
            rows.append((loc['name'], loc['free_spaces'], loc['observed_at']))
        tables.append((s, rows))
    return tables


def change_rows(base_sample, last_sample):
    """Displayed-value path between two received samples. No causal language."""
    before = {loc['name']: loc['free_spaces'] for loc in base_sample['summary']['locations']}
    after = {loc['name']: loc['free_spaces'] for loc in last_sample['summary']['locations']}
    rows = []
    for name_ in sorted(set(before) | set(after)):
        delta = None
        if before.get(name_) is not None and after.get(name_) is not None:
            delta = after[name_] - before[name_]
        rows.append((name_, before.get(name_), after.get(name_), delta))
    return rows


def group_changes(rows):
    """Split all-location rows into protocol groups + the rest (appendix)."""
    grouped = {g: [] for g in GROUPS}
    grouped['Ostale lokacije (prilog, ne centar price)'] = []
    member = {n for g in GROUPS.values() for n in g}
    for name_, before, after, delta in rows:
        placed = False
        for g, members in GROUPS.items():
            if name_ in members:
                grouped[g].append((name_, before, after, delta))
                placed = True
                break
        if not placed:
            grouped['Ostale lokacije (prilog, ne centar price)'].append((name_, before, after, delta))
    return grouped


def build_report(folder, now, samples, rows):
    samples = sorted(samples, key=lambda s: datetime.fromisoformat(s['slot']))
    captured = sum(1 for _, state in rows if state == 'captured')
    lines = []
    a = lines.append
    a('# OBS-001 izveštaj — 10K trka kroz prikaz parking mesta (05.09.2026)')
    a('')
    a('Status: completed descriptive pilot; local research report, not publication clearance.')
    a('Author: Astra. Date: %s UTC.' % now.date())
    a('Nastao %s UTC iz `observe_10k.py` receipt-a na disku. ' % now.isoformat(timespec='seconds'))
    a('Ovo je opisna observacija prikazanih brojeva, ne dokaz o uzročnosti.')
    a('')
    a('## Šta ovaj izveštaj ne tvrdi')
    a('')
    a('- Raspoređeno vreme nije vreme merenja: izvor ne izlaže `observed_at`, pa svaka '
      'vrednost ostaje „prikazano u trenutku prijema".')
    a('- U sacuvanim dokazima nema potvrdenog ukupnog kapaciteta lokacija, pa nema procenta popunjenosti; neto promena '
      'ne meri dolaske, odlaske ni broj učesnika.')
    a('- Rupe u pokrivenosti se ne popunjavaju, ne interpoliraju i ne prebijaju nulama; '
      'stanje svakog termina dolazi sa diska (vidi tabelu pokrivenosti).')
    a('- Promene su moguće i zbog redovne subote, drugih događaja, kvara ili promene prikaza '
      'na izvoru; bez uporedivih subota se ne razdvajaju (vidi OPAZANJA.md).')
    a('')
    a('## Vremenska linija najava (izvori, ne merenja)')
    a('')
    a('- Organizator (bgdmarathon.org): program 15:00–21:00, najavljen start 18:00 lokalno.')
    a('- Sekretarijat za javni prevoz: segmentirane izmene linija tokom dana, ne jedan trenutak.')
    a('- Parking servis: javni prikaz slobodnih mesta po garazi/parkiralištu, jedan odgovor za svih 27 lokacija.')
    a('- Rani parking uzorak (05:23:21 lokalno) iz multidomain dokaza, izvan ritma slotova.')
    a('')
    a('Zavrsna provera najava 05.09.2026 oko 22:35 UTC (06.09.00:35 lokalno): '
      '[organizator](https://bgdmarathon.org/10k-belgrade-run-nike-2026/) i '
      '[Sekretarijat](https://www.bgprevoz.rs/vesti/informacija-o-promeni-rezima-rada-linija-javnog-prevoza-tokom-odrzavanja-manifestacije-trka-10k-beograd-2026) '
      'ponovo otvoreni kroz web alat. Organizator i dalje prikazuje datum 05.09, program 15-21h i start 18h. '
      'Na ove dve strane nije nadjena nova oznaka otkazivanja; to nije nezavisna potvrda odrzavanja.')
    a('Najava prevoza razlikuje 04.09.08h-05.09.06h, zatim 05.09.06-16h, 16-21h i 21-24h '
      'za linije 15/84/704/706/707; za 9A/60 navodi 16-21h. Rani parking prijem je vec u periodu priprema. '
      'Ovo su najavljeni rezimi, ne GPS dokaz izvrsenja. Nije sacuvana cela tudja stranica za redistribuciju. '
      'Nisu dokazani svi ranije planirani medjuterminski pregledi najava; nema tvrdnje o potpunom nadzoru promena.')
    a('')
    a('## Pokrivenost slotova (%d od 13)' % captured)
    a('')
    a('| slot UTC | slot lokalno | stanje | dokaz |')
    a('|---|---|---|---|')
    for slot, state in rows:
        a('| %s | %s | %s | %s |' % (slot.strftime('%H:%M'), local(slot).strftime('%H:%M'),
                                     state, NOTES[state]))
    a('')
    a('## Tabela promena (prikazane vrednosti po prijemu)')
    a('')
    captured_samples = [s for s in samples if s['state'] == 'captured']
    if len(captured_samples) >= 2:
        first, last = captured_samples[0], captured_samples[-1]
        a('Prvi prijem %s → poslednji prijem %s. ' % (received(first), received(last)))
        a('Razlika je razlika prikazanih vrednosti između dva trenutka prijema, ne merenja.')
        a('')
        changes = change_rows(first, last)
        if all(before is not None and after is not None for _, before, after, _ in changes):
            total_before = sum(r[1] for r in changes)
            total_after = sum(r[2] for r in changes)
            a('Isti skup od %d lokacija: zbir prikazanih slobodnih mesta %d -> %d (razlika %+d). '
              'Ovo nije promena za ceo Beograd.' % (len(changes), total_before, total_after, total_after-total_before))
            a('')
        grouped = group_changes(changes)
        for gname, grows in grouped.items():
            if not grows:
                continue
            a('### %s' % gname)
            a('')
            a('| lokacija | prvi prijem | poslednji prijem | razlika prikaza |')
            a('|---|---|---|---|')
            for name_, before, after, delta in sorted(grows, key=lambda r: -(r[3] or 0)):
                a('| %s | %s | %s | %s |' % (name_, cell(before), cell(after), cell(delta)))
            if all(r[3] is not None for r in grows):
                a('')
                a('Zbir promena ovih %d lokacija: %+d; samo opis, bez kontrolnog ili uzrocnog tumacenja.' %
                  (len(grows), sum(r[3] for r in grows)))
            a('')
    else:
        a('Manje od dva uspešno primljena uzorka — tabela promena se ne pravi (nema od čega).')
    a('')
    a('## Sve primljene vrednosti po uzorku (prilog)')
    a('')
    for s, lrows in location_tables(samples):
        a('### Prijem %s (slot %s UTC, HTTP %s)' % (received(s), s['slot'][11:16], s.get('http_status')))
        a('')
        a('| lokacija | prikazano slobodnih |')
        a('|---|---|')
        for name_, free, _ in lrows:
            a('| %s | %s |' % (name_, cell(free)))
        a('')
    a('## Putanje i integritet dokaza')
    a('')
    a(trajectory_table(captured_samples))
    a('')
    a('| termin UTC | stvarni prijem UTC | lokacija | nedostajucih vrednosti | zbir prijavljenih mesta | SHA-256 receipta |')
    a('|---|---|---|---|---|---|')
    for s in captured_samples:
        values = [r['free_spaces'] for r in s['summary']['locations']]
        total = sum(values) if all(v is not None for v in values) else None
        ref = 'sample-' + name(datetime.fromisoformat(s['slot'])) + '.json'
        file = folder / ref
        receipt_hash = hashlib.sha256(file.read_bytes()).hexdigest() if file.exists() else 'fixture'
        a('| [%s](%s) | %s | %d | %d | %s | `%s` |' % (s['slot'][11:16], ref, received(s), len(values),
          sum(v is None for v in values), cell(total), receipt_hash))
    a('')
    a('Zbir opisuje samo primljeni skup lokacija operatora. Nije ukupan kapacitet niti mera praznjenja Beograda. '
      'Nula ostaje nula; nepoznato ostaje nedostupno. Razlicit HTML hash ne dokazuje svezinu instrumentalnog merenja.')
    a('')
    a('## Neutralne analitičke beleške')
    a('')
    a('- `observed_at` je null u svim receiptima: prijem i merenje nisu isti trenuci i '
      'razlika od sat vremena u prijemu ne znači sat vremena u izvoru.')
    a('- Najveće pojedinačne promene se posmatraju bez smera i uzroka; lokacije van '
      'okruženja trke ostaju opisni kontekst, ne dokaz.')
    a('- Nema ukupnog kapaciteta, pa nema procenta popunjenosti; neto promena ne meri '
      'dolaske, odlaske ni broj učesnika.')
    a('- Ranija tvrdnja o pet nula na Kalemegdanu ispravljena je u [OPAZANJA.md](OPAZANJA.md): '
      'termin 15:30 UTC ima 1. Ponovljena nula na Kamenickoj nije dokaz mrtvog brojaca. '
      'VMA 518 -> 338 -> 505 ne dokazuje nemoguc promet ili kvar. Sve putanje ostaju u tabeli.')
    a('- Naknadno predlozen uslov dva uzastopna uzorka nije preregistrovan kriterijum iskljucivanja. '
      'Nijedan kratak iskok nije uklonjen. Grupe iz protokola nisu kontrolne; slaba promena nije opsta falsifikacija hipoteze.')
    a('')
    a('## Negativni nalazi')
    a('')
    a('- Termini bez receipt-a su rupe: dokumentovane, ne nadoknađene, ne pretvorene u nule.')
    a('- Nema kapaciteta, pa nema procenta; nema brojača prolazaka, pa nema toka učesnika.')
    a('- Nema uporedivih subota, pa se efekat trke ne izoluje — ni u jednom smeru.')
    a('')
    a('## Granice')
    a('')
    a('- Receipt, ne zakazano okidanje, jeste dokaz pokrivenosti prijema; '
      'zadatak je `Interactive only` (odjava/spavanje hosta = propušteni termini).')
    a('- Trka je izdvojena novobeogradska/zemunska epizoda unutar ukupnog Beograda; '
      'grupe u tabeli su opisne, nisu kontrolne grupe.')
    a('- Kvar izvora, parsera ili pojedinacnog brojaca moze uticati na jednu ili vise lokacija; '
      'bez nezavisne provere ne znamo uzrok ni obuhvat.')
    a('')
    a('---')
    a('')
    a('Honest verdict: izveštaj je napisan iz stvarno primljenih receipt-a (%d od 13 slotova) i '
      'ni jedan broj nije izmišljen ni interpoliran; ali pokrivenost ima rupe, izvorno vreme '
      'merenja je nepoznato, i ništa ovde ne dokazuje da je bilo koja promena uzrokovana trkom. '
      'Slanje bilo kog dela ovoga je Semirova odluka, ne deo ovog izveštaja.' % captured)
    return '\n'.join(lines) + '\n'


def received(sample):
    return sample.get('transport', {}).get('retrieved_at') or 'unknown; attempted_at is not reception time'


def trajectory_table(samples):
    if not samples:
        return 'No captured samples; no trajectory.'
    names = sorted({r['name'] for s in samples for r in s['summary']['locations']})
    maps = [{r['name']: r['free_spaces'] for r in s['summary']['locations']} for s in samples]
    lines = ['| lokacija | ' + ' | '.join(s['slot'][11:16] + ' UTC' for s in samples) + ' |',
             '|---|' + '---|' * len(samples)]
    for n in names:
        lines.append('| ' + n + ' | ' + ' | '.join(cell(m.get(n)) for m in maps) + ' |')
    return '\n'.join(lines)


def can_close(folder, now):
    now = utc(now)
    if now > LAST + GRACE:
        return True
    return now >= LAST and all(state in ('captured', 'failed', 'missing')
                               for _, state in coverage_rows(folder, now))


def publish_report(target, report):
    """Same immutable hard-link publication discipline as the recorder."""
    fd, tmp = tempfile.mkstemp(prefix='.izvestaj-', suffix='.tmp', dir=target.parent)
    payload = report.encode('utf-8')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.link(tmp, target)
    finally:
        os.unlink(tmp)
    if target.read_bytes() != payload:
        raise OSError('report readback mismatch')


NOTES = {
    'captured': 'receipt na disku (sample-*.json)',
    'failed': 'neuspesan prijem; rupa, ne nula',
    'claimed_unfinished': 'claim postoji, uzorak nije stigao; nedovršeni trag',
    'unreadable_receipt': 'receipt na disku se ne čita; rupa uz upozorenje',
    'missing': 'termin prosao bez receipta; rupa, ne nula',
    'pending': 'zakazano, jos nije doslo',
    'due': 'unutar grace prozora; jos se moze doci do receipta',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', nargs='?', choices=['write'], default='write')
    parser.add_argument('--folder', default=None)
    parser.add_argument('--now', default=None)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    folder = pathlib.Path(args.folder) if args.folder else FOLDER
    now = utc(datetime.now(timezone.utc) if args.now is None else datetime.fromisoformat(args.now))

    if not can_close(folder, now):
        print(json.dumps({
            'state': 'observation_not_closed',
            'now': now.isoformat(),
            'report_after': (LAST + GRACE).isoformat(),
            'note': 'Wait for final terminal receipt or end of grace; no backdated sample',
        }, ensure_ascii=True, indent=2))
        return

    samples = receipts(folder)
    rows = coverage_rows(folder, now)
    report = build_report(folder, now, samples, rows)

    if args.dry_run:
        print(report)
        return
    target = folder / REPORT
    if target.exists():
        print(json.dumps({'state': 'already_written', 'file': str(target)}))
        return
    try:
        publish_report(target, report)
    except FileExistsError:
        print(json.dumps({'state': 'already_written', 'file': str(target)}))
        return
    print(json.dumps({'state': 'written', 'file': str(target),
                      'captured': sum(1 for _, st in rows if st == 'captured')}))


if __name__ == '__main__':
    main()
