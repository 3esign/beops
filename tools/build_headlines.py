"""Publish every retained headline and revision, independently of the live window."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib

from contracts import atomic_json, content_id, exclusive, observation_rows

ROOT = pathlib.Path(__file__).resolve().parents[1]


def build(root=ROOT):
    root = pathlib.Path(root)
    cfg = json.loads((root / 'research/COLLECTORS.json').read_text(encoding='utf-8'))
    names = {s['sid']: s['name'] for s in cfg['sources']}
    grouped = {}
    with exclusive(root / 'data/live/.write.lock'):
        for path in sorted((root / 'data/live/rows').glob('*/*.jsonl')):
            for row in observation_rows(path):
                if row.get('parameter') != 'headline' or not row.get('result') or row.get('redacted'):
                    continue
                key = row.get('row_id') or content_id(row)
                rx = row.get('receivedTime')
                if key in grouped:
                    grouped[key]['last_received'] = max(rx or '', grouped[key]['last_received'] or '')
                    continue
                grouped[key] = dict(id=key, sid=row['sid'], source=names.get(row['sid'], row['sid']),
                                    title=row['result'], link=row.get('link'), published=row.get('resultTime'),
                                    received=rx, last_received=rx, revision_key=row.get('dedupe_key'),
                                    raw_sha256=row.get('raw_sha256'), permission_capture=row.get('permission_capture'), correction=row.get('correction'))
    rows = sorted(grouped.values(), key=lambda r: (r['published'] or r['received'] or '', r['id']), reverse=True)
    payload = {'schema': 'beops-headline-archive/v1', 'as_of': dt.datetime.now(dt.timezone.utc).isoformat(),
               'count': len(rows), 'scope': 'All retained collected headlines, including revisions; publication time is not event time.',
               'rows': rows}
    target = root / 'public/headlines.json'
    atomic_json(target, payload)
    return target


if __name__ == '__main__':
    print(build())
