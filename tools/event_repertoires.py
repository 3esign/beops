"""Narrow, source-specific extraction of explicitly timed official schedule facts.

No article descriptions, images, inferred dates, date ranges or inferred venues.
The small HTML tree is standard-library only and does not execute page content.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit

from contracts import belgrade_local

SOURCES = (
    {'source_id': 'S225', 'name': 'Kolarac — zvanični repertoar',
     'url': 'https://www.kolarac.rs/koncerti/', 'parser': 'kolarac-entry-title/v2'},
    {'source_id': 'S226', 'name': 'Dom omladine Beograda — zvanični program',
     'url': 'https://domomladine.org/', 'parser': 'dom-omladine-schedule-card/v1'},
    {'source_id': 'S227', 'name': 'Kulturni centar Beograda — zvanični program',
     'url': 'https://www.kcb.org.rs/', 'parser': 'kcb-schedule-card/v1'},
)


class Element:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def has(self, cls):
        return cls in self.attrs.get('class', '').split()

    def text(self):
        return ' '.join(' '.join(c.text() if isinstance(c, Element) else c
                                 for c in self.children).split())

    def find(self, predicate):
        for child in self.children:
            if isinstance(child, Element):
                if predicate(child):
                    yield child
                yield from child.find(predicate)


class ScheduleHTML(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element()
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        child = Element(tag, attrs, self.current)
        self.current.children.append(child)
        if tag not in self.VOID:
            self.current = child

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        node = self.current
        while node.parent:
            if node.tag == tag:
                self.current = node.parent
                break
            node = node.parent

    def handle_data(self, value):
        if self.current.tag not in {'script', 'style'}:
            self.current.children.append(value)


def first(node, predicate):
    return next(node.find(predicate), None)


MONTHS = {name: number for number, names in enumerate((
    'januar januara', 'februar februara', 'mart marta', 'april aprila', 'maj maja', 'jun juna',
    'jul jula', 'avgust avgusta', 'septembar septembra', 'oktobar oktobra',
    'novembar novembra', 'decembar decembra'), 1) for name in names.split()}
WEEKDAYS = {name: n for n, name in enumerate(('ponedeljak', 'utorak', 'sreda', 'četvrtak', 'petak', 'subota', 'nedelja'))}
DOM_CLOCK = re.compile(r'(?:(ponedeljak|utorak|sreda|četvrtak|petak|subota|nedelja),\s*)?(\d{1,2})\.\s*([a-zčćžšđ]+)\s+(20\d{2})\.\s*(?:u|od)\s+(\d{1,2})[:.](\d{2})\.?', re.I)
KCB_CLOCK = re.compile(r'(\d{1,2})\.(\d{1,2})\.(20\d{2}),\s*(\d{1,2}):(\d{2})\.?')


def explicit_clock(label, sid):
    match = (DOM_CLOCK if sid == 'S226' else KCB_CLOCK).fullmatch(label.strip())
    if not match:
        return None, 'missing_or_non_single_explicit_clock'
    try:
        if sid == 'S226':
            weekday, day, month, year, hour, minute = match.groups()
            local = datetime(int(year), MONTHS[month.casefold()], int(day), int(hour), int(minute))
            if weekday and WEEKDAYS[weekday.casefold()] != local.weekday():
                return None, 'source_weekday_date_conflict'
        else:
            day, month, year, hour, minute = match.groups()
            local = datetime(int(year), int(month), int(day), int(hour), int(minute))
        start, offset = belgrade_local(local)
        if start is None:
            return None, 'ambiguous_or_nonexistent_local_time'
        return (local, start, offset), None
    except (KeyError, ValueError):
        return None, 'invalid_source_clock'


def safe_event_url(value, sid):
    try:
        route = urlsplit(value)
        if route.scheme != 'https' or route.username or route.password or route.port or route.query or route.fragment:
            return False
        if sid == 'S226':
            return route.netloc == 'domomladine.org' and bool(re.fullmatch(r'/(?:koncerti|filmovi|debate|izlozbe|predstave|radionice|vesti)/[^/]+/', route.path))
        return route.netloc == 'www.kcb.org.rs' and bool(re.fullmatch(r'/20\d{2}/\d{2}/[^/]+/', route.path))
    except (TypeError, ValueError):
        return False


def schedule_cards(root, sid):
    if sid == 'S226':
        for heading in root.find(lambda n: n.tag == 'h3' and n.has('ev-title')):
            card = heading.parent
            link = first(heading, lambda n: n.tag == 'a')
            title = first(heading, lambda n: n.has('main-title')) or heading
            clock = first(card, lambda n: n.tag == 'p' and n.has('ev-date'))
            venue = first(card, lambda n: n.tag == 'p' and n.has('ev-loc'))
            if link and clock:
                yield link.attrs.get('href', ''), title.text(), clock.text(), venue.text() if venue else None
    else:
        for section in root.find(lambda n: n.tag == 'div' and n.has('events')):
            for card in section.find(lambda n: n.tag == 'div' and n.has('text-content')):
                title = first(card, lambda n: n.tag == 'h4')
                clock = first(card, lambda n: n.tag == 'div' and n.has('date'))
                venue = first(card, lambda n: n.tag == 'div' and n.has('location'))
                link = title.parent if title and title.parent.tag == 'a' else None
                if link and clock:
                    yield link.attrs.get('href', ''), title.text(), clock.text(), venue.text() if venue else None


def parse_official_programme(body, source, received_at, raw_sha256):
    sid = source['source_id']
    if sid not in {'S226', 'S227'}:
        raise ValueError('unknown official programme parser')
    tree = ScheduleHTML()
    tree.feed(body.decode('utf-8'))
    events, rejected, seen = [], [], set()
    for url, title, label, venue in schedule_cards(tree.root, sid):
        clock, error = explicit_clock(label, sid)
        if not safe_event_url(url, sid) or not title or not venue:
            error = 'missing_title_venue_or_disallowed_event_url'
        if error:
            rejected.append({'url': url if safe_event_url(url, sid) else None, 'source_clock': label, 'reason': error})
            continue
        local, start, offset = clock
        key = url, start.isoformat()
        if key in seen:
            continue
        seen.add(key)
        events.append({
            'id': 'EV-' + hashlib.sha256((url + start.isoformat()).encode()).hexdigest()[:16],
            'title': title, 'category': 'kultura', 'zone': None, 'location': venue,
            'venue_id': ('dom-omladine' if sid == 'S226' and venue in (
                'DOB//Amerikana', 'DOB//Tribinska sala', 'DOB//Klub', 'DOB//Velika sala',
                'DOB//Galerija', 'Dom omladine Beograda') else
                'kcb-artget' if sid == 'S227' and venue == 'Galerija ARTGET' else None),
            'source': source['name'], 'source_id': sid, 'url': url,
            'is_official': True, 'verified': True,
            'verification_scope': 'explicit schedule facts in one official source; not independent corroboration or occurrence verification',
            'classification': 'official-repertoire', 'state': 'forecast', 'event_status': 'scheduled',
            'event_start': start.isoformat().replace('+00:00', 'Z'),
            'event_start_local': local.isoformat(timespec='minutes') + f'{offset:+03d}:00',
            'event_timezone': 'Europe/Belgrade', 'event_end': None, 'published': None,
            'provenance': {'url': source['url'], 'received_at': received_at, 'raw_sha256': raw_sha256,
                           'source_label': ' | '.join((title, label, venue)), 'parser': source['parser']},
            'limitation': 'One official schedule; end time, availability, cancellation and actual occurrence are unknown.'
        })
    return {'events': sorted(events, key=lambda e: e['event_start']), 'rejected': rejected}
