"""One-shot, metadata-only HF audit. Never downloads or executes model weights.

README files are untrusted source material stored as text, not instructions.
No credentials, auto-installs, inference, external links or paid requests.
"""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import quote, urlencode

from probe_sources import ROOT, get


def summarize(info, expected):
    if not isinstance(info, dict) or info.get('id') != expected:
        raise ValueError('model identity mismatch')
    sha = info.get('sha')
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('missing pinned revision')
    card = info.get('cardData') or {}
    tensors = info.get('safetensors') or {}
    files = [{'name': x['rfilename'], 'bytes': x.get('size'),
              'lfs_sha256': (x.get('lfs') or {}).get('sha256')}
             for x in info.get('siblings', []) if isinstance(x.get('rfilename'), str)]
    return {'id': expected, 'sha': sha, 'last_modified': info.get('lastModified'),
            'pipeline_tag': info.get('pipeline_tag'), 'library': info.get('library_name'),
            'license_declared': card.get('license'), 'languages_declared': card.get('language'),
            'gated': info.get('gated'), 'disabled': info.get('disabled'),
            'parameter_count_api': tensors.get('total'), 'files': files,
            'inference_verified': False, 'weights_downloaded': False,
            'publication_approved': False,
            'limit': 'metadata and owner declarations only; branch/config, rights and runtime require review'}


def store(path, data):
    with path.open('xb') as f:
        f.write(data)
    if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(data).digest():
        raise OSError('readback mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', action='append', help='audit only named candidates from the local shortlist')
    args = parser.parse_args()
    candidates = json.loads((ROOT / 'MODEL_CANDIDATES.json').read_text(encoding='utf-8'))['models']
    if args.model:
        if set(args.model) - {x['id'] for x in candidates}:
            raise ValueError('requested model is not in the reviewed shortlist')
        candidates = [x for x in candidates if x['id'] in args.model]
    ids = [x['id'] for x in candidates]
    if len(ids) > 30 or len(set(ids)) != len(ids):
        raise ValueError('at most 30 distinct explicit candidates')
    for model in ids:
        if not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+', model):
            raise ValueError('invalid repository id')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT / 'evidence' / ('model-audit-' + stamp)
    folder.mkdir()
    report = {'schema': 'beops-model-audit/v1', 'created_at': stamp, 'results': [],
              'network_requests': 0, 'downloaded_bytes': 0, 'weights_downloaded': False,
              'byte_accounting': 'successful bounded responses only; failed oversized transfers excluded'}
    blocked = False
    started = time.monotonic()
    for candidate in candidates:
        model = candidate['id']
        row = {'candidate': candidate, 'state': 'not_checked', 'requests': []}
        report['results'].append(row)
        if blocked or time.monotonic() - started > 180:
            row['state'] = 'skipped_access_or_time_budget'
            continue
        base = 'https://huggingface.co/api/models/' + quote(model, safe='/')
        try:
            report['network_requests'] += 1
            fields = ['sha', 'lastModified', 'pipeline_tag', 'library_name', 'cardData',
                      'safetensors', 'siblings', 'gated', 'disabled']
            query = urlencode([('expand', key) for key in fields])
            data, meta, _ = get(base + '?' + query, 1_000_000)
            report['downloaded_bytes'] += len(data)
            row['requests'].append(meta)
            info = json.loads(data)
            stem = model.replace('/', '--')
            store(folder / (stem + '.metadata.json'), data)
            row['metadata'] = summarize(info, model)
            row['state'] = 'metadata_verified'
            time.sleep(0.25)
            report['network_requests'] += 1
            data, meta, _ = get(base + '?expand=inferenceProviderMapping', 200_000)
            report['downloaded_bytes'] += len(data)
            row['requests'].append(meta)
            providers = json.loads(data)
            if not isinstance(providers, dict):
                raise ValueError('provider mapping schema mismatch')
            row['provider_mapping'] = providers.get('inferenceProviderMapping')
            row['provider_mapping_observed_at'] = meta['retrieved_at']
            store(folder / (stem + '.providers.json'), data)
            time.sleep(0.25)
            if 'README.md' in [x['name'] for x in row['metadata']['files']]:
                url = 'https://huggingface.co/' + quote(model, safe='/') + '/raw/' + info['sha'] + '/README.md'
                report['network_requests'] += 1
                data, meta, _ = get(url, 200_000)
                report['downloaded_bytes'] += len(data)
                row['requests'].append(meta)
                store(folder / (stem + '.card.txt'), data)
                row['card_file'] = stem + '.card.txt'
            time.sleep(0.25)
        except Exception as exc:
            row['error'] = {'type': type(exc).__name__, 'message': str(exc)[:240]}
            if row['state'] == 'not_checked':
                row['state'] = 'failed'
            if isinstance(exc, HTTPError) and exc.code in (401, 403, 429):
                blocked = True
        store(folder / (model.replace('/', '--') + '.receipt.json'),
              json.dumps(row, ensure_ascii=True, indent=2).encode('utf-8'))
        print(json.dumps({'id': model, 'state': row['state'], 'error': row.get('error')}), flush=True)
    report['completed_at'] = datetime.now(timezone.utc).isoformat()
    store(folder / 'REPORT.json', json.dumps(report, ensure_ascii=True, indent=2).encode('utf-8'))
    print('REPORT ' + str(folder / 'REPORT.json'), flush=True)


if __name__ == '__main__':
    main()
