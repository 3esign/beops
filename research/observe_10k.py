"""Small OBS-001 recorder over the existing public connector; no new service.

Immutable per-slot claims prevent retries after interruption. All receipts are
research records; source time remains unknown and gaps never become zeroes.
"""
import argparse
import hashlib
import json
import os
import pathlib
import tempfile
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError

from probe_multidomain import parking_get, page_summary
from probe_sources import ROOT

FIRST = datetime(2026, 9, 5, 10, 30, tzinfo=timezone.utc)
LAST = datetime(2026, 9, 5, 22, 30, tzinfo=timezone.utc)
GRACE = timedelta(minutes=20)
FOLDER = ROOT / 'observations' / '10k-2026-09-05'
URL = 'https://www.parking-servis.co.rs/lat/garaze-i-parkiralista'
BASELINE = ROOT / 'evidence' / 'multidomain-20260905T032324953657Z.json'


def utc(value):
    if value.tzinfo is None:
        raise ValueError('timezone required')
    return value.astimezone(timezone.utc)


def slots():
    return [FIRST + timedelta(hours=i) for i in range(13)]


def name(slot):
    return slot.strftime('%Y%m%dT%H%M%SZ')


def publish(path, value):
    """Publish complete JSON without ever replacing an existing receipt."""
    path = pathlib.Path(path)
    payload = json.dumps(value, ensure_ascii=True, indent=2).encode('utf-8')
    fd, tmp = tempfile.mkstemp(prefix='.obs-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.link(tmp, path)
    finally:
        os.unlink(tmp)
    if json.loads(path.read_text(encoding='utf-8')) != value:
        raise OSError('receipt readback mismatch')


def receipts(folder):
    out = []
    for path in sorted(pathlib.Path(folder).glob('sample-*.json')):
        item = json.loads(path.read_text(encoding='utf-8'))
        if item.get('schema') != 'beops-obs001-sample/v1':
            raise ValueError('unknown sample schema: ' + path.name)
        out.append(item)
    return out


def capture(folder=FOLDER, now=None, fetch=parking_get):
    now = utc(now or datetime.now(timezone.utc))
    folder = pathlib.Path(folder)
    if now < FIRST:
        return {'state': 'not_started', 'next_slot': FIRST.isoformat(), 'network_requests': 0}
    if now > LAST + GRACE:
        return {'state': 'closed', 'network_requests': 0}
    slot = FIRST + timedelta(hours=int((now - FIRST).total_seconds() // 3600))
    if now - slot > GRACE:
        return {'state': 'missed_window', 'slot': slot.isoformat(), 'network_requests': 0}
    folder.mkdir(parents=True, exist_ok=True)
    previous = receipts(folder)
    if any(x.get('http_status') in (403, 429) for x in previous):
        return {'state': 'source_paused', 'network_requests': 0}
    target = folder / ('sample-' + name(slot) + '.json')
    claim = folder / ('claim-' + name(slot) + '.json')
    if target.exists():
        return {'state': 'already_recorded', 'file': target.name, 'network_requests': 0}
    try:
        publish(claim, {'slot': slot.isoformat(), 'claimed_at': now.isoformat(), 'pid': os.getpid()})
    except FileExistsError:
        return {'state': 'claimed_unfinished', 'slot': slot.isoformat(), 'network_requests': 0}
    item = {'schema': 'beops-obs001-sample/v1', 'slot': slot.isoformat(),
            'attempted_at': now.isoformat(), 'source_url': URL, 'state': 'failed',
            'observed_at': None, 'http_status': None}
    try:
        data, meta, encoding = fetch()
        # Transport success alone cannot become a successful measurement receipt.
        item['transport'] = meta
        item['http_status'] = meta.get('status')
        if item['http_status'] != 200:
            raise HTTPError(URL, item['http_status'] or 0, 'Unexpected status', {}, None)
        item['summary'] = page_summary(data.decode(encoding), URL, 'parking')
        item['state'] = 'captured'
        item['content_sha256'] = hashlib.sha256(data).hexdigest()
    except Exception as exc:
        if isinstance(exc, HTTPError):
            item['http_status'] = exc.code
        item['error'] = {'type': type(exc).__name__, 'message': str(exc)[:240]}
    item['completed_at'] = datetime.now(timezone.utc).isoformat()
    publish(target, item)
    return {'state': item['state'], 'file': target.name, 'network_requests': 1,
            'http_status': item['http_status']}


def inventory(folder=FOLDER, now=None):
    now = utc(now or datetime.now(timezone.utc))
    folder = pathlib.Path(folder)
    rows = {x['slot']: x for x in receipts(folder)}
    coverage = []
    for slot in slots():
        sample = rows.get(slot.isoformat())
        if sample:
            state = sample['state']
        elif (folder / ('claim-' + name(slot) + '.json')).exists():
            state = 'claimed_unfinished'
        elif now < slot:
            state = 'pending'
        elif now <= slot + GRACE:
            state = 'due'
        else:
            state = 'missing'
        coverage.append({'slot': slot.isoformat(), 'state': state})
    return {'schema': 'beops-obs001-inventory/v1', 'as_of': now.isoformat(),
            'planned_slots': 13, 'coverage': coverage,
            'captured': sum(x['state'] == 'captured' for x in coverage),
            'source_paused': any(x.get('http_status') in (403, 429) for x in rows.values()),
            'baseline_reference': str(BASELINE),
            'limit': 'scheduled times are not source observation times; no causal claim'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['capture', 'status'])
    args = parser.parse_args()
    result = capture() if args.command == 'capture' else inventory()
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
