"""Read-only calendar publication gate using the collector's canonical policy.

No capture/refresh or network request is made. Run with Python -B; only relevant
source entries and evidence participate in the returned policy revision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime

import permission_policy


def check(root, as_of, sources, byte_budget=64 * 1024 * 1024):
    root = pathlib.Path(root).resolve()
    now = datetime.fromisoformat(as_of.replace('Z', '+00:00'))
    if now.tzinfo is None:
        raise ValueError('explicit timezone required')
    reads = []
    bytes_read = 0
    per_file_limit = 16 * 1024 * 1024
    original_bytes, original_text = pathlib.Path.read_bytes, pathlib.Path.read_text

    def record(file, data):
        nonlocal bytes_read
        if len(data) > per_file_limit or bytes_read + len(data) > byte_budget:
            raise ValueError('calendar_policy_input_byte_limit')
        bytes_read += len(data)
        reads.append({'path': str(pathlib.Path(file).resolve().relative_to(root)).replace('\\', '/'),
                      'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        return data

    def tracked_bytes(file):
        size = pathlib.Path(file).stat().st_size
        if size > per_file_limit or bytes_read + size > byte_budget:
            raise ValueError('calendar_policy_input_byte_limit')
        # An opened file may grow after stat; bounded read protects that race.
        with pathlib.Path(file).open('rb') as stream:
            data = stream.read(min(per_file_limit, byte_budget - bytes_read) + 1)
        return record(file, data)

    def tracked_text(file, *args, **kwargs):
        # Exact source bytes, including CRLF, count once for this actual read.
        raw = tracked_bytes(file)
        encoding = kwargs.get('encoding') or (args[0] if args else None) or 'utf-8'
        errors = kwargs.get('errors') or (args[1] if len(args) > 1 else None) or 'strict'
        return raw.decode(encoding, errors)

    ledger = root / 'research/08-provenance/LEDGER.jsonl'
    rows = []
    if ledger.exists():
        # Incomplete policy input must not accidentally erase a sticky veto.
        raw = tracked_bytes(ledger)
        for line in raw.decode('utf-8-sig').splitlines():
            if line.strip():
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError('invalid permission ledger entry')
                rows.append(row)
    original_rows = permission_policy.json_rows
    permission_policy.json_rows = lambda _: iter(rows)
    try:
        entries = permission_policy.latest(ledger)
    finally:
        permission_policy.json_rows = original_rows
    relevant = {s['source_id']: entries.get(s['source_id']) for s in sources}
    decisions = []
    pathlib.Path.read_bytes, pathlib.Path.read_text = tracked_bytes, tracked_text
    try:
        for source in sources:
            allowed, reason = permission_policy.authorize(
                source['source_id'], entries, root, source.get('url'), now)
            decisions.append({'source_id': source['source_id'], 'allowed': allowed,
                              'capture': reason if allowed else None})
    finally:
        pathlib.Path.read_bytes, pathlib.Path.read_text = original_bytes, original_text
    evidence = [{k: r[k] for k in ('path', 'bytes', 'sha256')} for r in reads
                if r['path'] != 'research/08-provenance/LEDGER.jsonl']
    revision_input = {'entries': relevant, 'evidence': evidence, 'decisions': decisions}
    revision = hashlib.sha256(json.dumps(revision_input, sort_keys=True,
                                         separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    return {'schema': 'beops-calendar-policy/v1', 'revision': revision,
            'decisions': decisions, 'inputReadBytes': sum(r['bytes'] for r in reads),
            'inputFiles': sorted({r['path'] for r in reads})}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--as-of', required=True)
    parser.add_argument('--byte-budget', type=int, default=64 * 1024 * 1024)
    args = parser.parse_args()
    sources = json.load(sys.stdin)
    if not isinstance(sources, list) or len(sources) > 100:
        raise ValueError('invalid calendar source list')
    if not 0 <= args.byte_budget <= 64 * 1024 * 1024:
        raise ValueError('invalid policy byte budget')
    print(json.dumps(check(args.root, args.as_of, sources, args.byte_budget)))


if __name__ == '__main__':
    main()
