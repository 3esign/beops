"""One-shot reconnaissance outside weather. No inference or continuous polling.

Reuses bounded stdlib HTTP probes; Windows parking adapter retains TLS checks.
Only compact summaries and response hashes persist, not complete source pages.
"""
import base64
import csv
import hashlib
import io
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.error import HTTPError

from probe_sources import ROOT, Tables, get


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.headings, self.parking = [], [], []
        self.anchor = self.heading = self.item = None
        self.in_parking = False
        self.in_count = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '').split()
        if tag == 'ul' and 'parking-count' in classes:
            self.in_parking = True
        if tag == 'li' and self.in_parking:
            self.item = {'name': [], 'raw': [], 'map_url': None}
        if tag == 'a':
            self.anchor = {'href': attrs.get('href', ''), 'text': []}
            if self.item is not None:
                self.item['map_url'] = attrs.get('href')
        if tag in ('h1', 'h2', 'h3'):
            self.heading = []
        if tag == 'span' and 'count' in classes and self.item is not None:
            self.in_count = True

    def handle_data(self, data):
        if self.anchor is not None:
            self.anchor['text'].append(data)
            if self.item is not None:
                self.item['name'].append(data)
        if self.heading is not None:
            self.heading.append(data)
        if self.in_count:
            self.item['raw'].append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.anchor is not None:
            self.anchor['text'] = ' '.join(' '.join(self.anchor['text']).split())
            self.links.append(self.anchor)
            self.anchor = None
        if tag in ('h1', 'h2', 'h3') and self.heading is not None:
            self.headings.append(' '.join(' '.join(self.heading).split()))
            self.heading = None
        if tag == 'span':
            self.in_count = False
        if tag == 'li' and self.item is not None:
            raw = ''.join(self.item['raw']).strip()
            self.parking.append({'name': ' '.join(' '.join(self.item['name']).split()),
                                 'free_spaces': int(raw) if re.fullmatch(r'\d+', raw) else None,
                                 'raw_count': raw, 'map_url': self.item['map_url'],
                                 'observed_at': None})
            self.item = None
        if tag == 'ul':
            self.in_parking = False


def river_summary(html):
    table = Tables()
    table.feed(html)
    text = ' '.join(table.text)
    if 'UTC+1' not in text:
        raise ValueError('Source time convention missing; refusing guessed UTC conversion')
    rows, rejected = [], 0
    for row in table.rows:
        if len(row) != 2 or not re.fullmatch(r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}', row[0]):
            continue
        if not re.fullmatch(r'-?\d+', row[1]):
            rejected += 1
            continue
        when = datetime.strptime(row[0], '%d.%m.%Y %H:%M').replace(tzinfo=timezone(timedelta(hours=1)))
        rows.append({'observed_at': when.astimezone(timezone.utc).isoformat(), 'level_cm': int(row[1])})
    rows.sort(key=lambda x: x['observed_at'])
    return {'valid_rows': len(rows), 'rejected_values': rejected,
            'oldest': rows[0] if rows else None, 'latest': rows[-1] if rows else None,
            'unit': 'cm relative to station datum', 'source_offset': '+01:00 fixed as publisher states',
            'limit': 'provisional stage, not discharge or depth; missing/latest data may lag'}


def prices_summary(data):
    text = data.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text), delimiter=';')
    columns = reader.fieldnames or []
    if 'Redovna cena' not in columns:
        raise ValueError('Unexpected price schema')
    count, missing = 0, 0
    dates, kinds, formats = Counter(), Counter(), Counter()
    ids = set()
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError('Ragged CSV row')
        count += 1
        ident = row.get('Ident', row.get('Barkod proizvoda', '')).strip()
        if not ident:
            missing += 1
        else:
            ids.add(ident)
        for field, target in [('Datum cenovnika', dates), ('VRSTA_CENOVNIKA', kinds),
                              ('Naziv trgovca - formata', formats)]:
            if row.get(field):
                target[row[field]] += 1
    return {'rows': count, 'columns': columns, 'distinct_product_ids': len(ids),
            'missing_id_rows': missing, 'dated_rows': dict(dates), 'price_list_types': dict(kinds),
            'retail_formats': dict(formats),
            'limit': 'advertised prices, not transactions or stock; geography and units need separate validation'}


def page_summary(html, url, kind):
    page = Page()
    page.feed(html)
    if kind == 'parking':
        if not page.parking:
            raise ValueError('Parking measurement list missing')
        return {'locations': page.parking, 'count': len(page.parking),
                'limit': 'publisher-displayed free counts; instrument timestamp and total capacity unknown'}
    candidates = []
    seen = set()
    for link in page.links:
        href = urljoin(url, link['href'])
        if href in seen or not link['text'] or len(link['text']) < 12:
            continue
        if kind == 'transport' and not any(x in href for x in ['/vesti/', '/aktuelne-izmene/']):
            continue
        seen.add(href)
        candidates.append({'url': href, 'title': link['text'][:140]})
    return {'headings': page.headings[-8:], 'candidate_links': candidates[:6] if kind == 'transport' else [],
            'limit': 'documentary/announcement source, not actual attendance, vehicle position or service outage'}


def parking_get():
    proc = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-File',
                           str(ROOT / 'fetch_parking_windows.ps1')], capture_output=True,
                          timeout=35, creationflags=subprocess.CREATE_NO_WINDOW, check=True)
    meta = json.loads(proc.stdout)
    if meta.get('error'):
        if isinstance(meta.get('status'), int):
            raise HTTPError(meta['url'], meta['status'], meta['error'], {}, None)
        raise OSError(meta['error'])
    data = base64.b64decode(meta.pop('body_base64'), validate=True)
    meta.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    return data, meta, 'utf-8'


def main():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    sources = [
        ('parking-counts', 'https://www.parking-servis.co.rs/lat/garaze-i-parkiralista', 'parking'),
        ('zemun-stage', 'https://www.hidmet.gov.rs/latin/osmotreni/nrt_tabela_grafik.php?hm_id=42045&period=7', 'river'),
        ('bvk-planned', 'https://www.bvk.rs/planirani-radovi/', 'services'),
        ('eds-planned', 'https://www.elektrodistribucija.rs/planirana-iskljucenja-beograd/Dan_1_Iskljucenja.htm', 'services'),
        ('transport-changes', 'https://www.bgprevoz.rs/linije/aktuelne-izmene', 'transport'),
        ('transport-news', 'https://www.bgprevoz.rs/vesti', 'transport'),
        ('kengur-bg01', 'https://kengur.rs/wp-content/uploads/cenovnici/Kengur_BG01_cenovnik.csv', 'prices'),
        ('delhaize-prices', 'https://tsmdelhaizeserbia.delhaize.rs/PublicDoc/cene_proizvoda_Delhaize.csv', 'prices'),
        ('culture-tob', 'https://www.tob.rs/rs/events', 'culture'),
        ('sj-beo-avas-metadata', 'https://geofon.gfz.de/fdsnws/station/1/query?net=SJ&sta=BEO,AVAS&level=channel&format=text&starttime=' + today, 'station'),
    ]
    results = []
    for sid, url, kind in sources:
        item = {'id': sid, 'domain': kind, 'url': url, 'ok': False}
        try:
            data, meta, encoding = parking_get() if kind == 'parking' else get(url, 12_000_000 if kind == 'prices' else 3_000_000)
            item.update(meta)
            if kind == 'river':
                summary = river_summary(data.decode(encoding))
            elif kind == 'prices':
                summary = prices_summary(data)
            elif kind == 'station':
                lines = data.decode(encoding).splitlines()
                summary = {'channel_rows': [s for s in lines if s and not s.startswith('#')][:12],
                           'limit': 'one archive metadata query; empty is not proof no station exists; no waveform acquired'}
            else:
                summary = page_summary(data.decode(encoding), url, kind)
            item.update(ok=True, summary=summary)
        except Exception as exc:
            item['error'] = type(exc).__name__ + ': ' + str(exc)[:250]
        results.append(item)
        print(json.dumps({'id': sid, 'ok': item['ok'], 'bytes': item.get('bytes'),
                          'error': item.get('error')}, ensure_ascii=True), flush=True)
    report = {'schema': 'beops-multidomain-probe/v1', 'created_at': datetime.now(timezone.utc).isoformat(),
              'scope': 'one-shot research only; no operational monitoring or reuse approval', 'results': results}
    target = ROOT / 'evidence' / ('multidomain-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    with target.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=True, indent=2)
    assert json.loads(target.read_text(encoding='utf-8')) == report
    print('REPORT ' + str(target), flush=True)


if __name__ == '__main__':
    main()
