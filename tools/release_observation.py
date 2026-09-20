"""Verify a publisher's frozen observation view without making another copy.

The publisher binds the exact manifest bytes and physical root in the environment.
Each use verifies every relevant payload; this is not a stat/mtime cache.
"""
import hashlib
import json
import os
import pathlib
import stat as statmod
from datetime import datetime, timezone


def is_observation_path(name):
    rel = pathlib.PurePosixPath(name)
    parts = rel.parts
    return bool(
        len(parts) == 5 and parts[:3] == ('data', 'live', 'rows') and rel.suffix == '.jsonl' or
        len(parts) == 5 and parts[:3] == ('data', 'live', 'derived') and
        (rel.match('*/????-??.jsonl') or name.endswith('/mind/claims.jsonl')) or
        name == 'data/live/corrections.jsonl')


def input_generation(live):
    manifest = frozen_manifest(pathlib.Path(live).resolve())
    if manifest is None:
        return None
    if manifest.get('observation_prefix') != 'complete-lf-lines/v1':
        raise ValueError('release lacks a complete observation prefix')
    captured = datetime.fromisoformat(manifest['captured_at'].replace('Z', '+00:00'))
    if captured.tzinfo is None:
        raise ValueError('capture clock needs an explicit timezone')
    root = pathlib.Path(live).resolve().parent.parent
    for entry in manifest['configuration']:
        name = entry['path']
        if name not in ('research/COLLECTORS.json', 'research/SOURCE_REGISTRY.json', 'research/ORGANS.json'):
            raise ValueError('unexpected release configuration path')
        raw = (root/name).read_bytes()
        if len(raw) != entry['bytes'] or hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('release configuration changed: '+name)
    return {'schema': 'beops-input-generation/v1',
            'id': os.environ['BEOPS_FROZEN_MANIFEST_SHA256'],
            'source_oid': manifest['source_oid'], 'source_tree': manifest['source_tree'],
            'captured_at': captured.astimezone(timezone.utc).isoformat(),
            'observation_prefix': manifest['observation_prefix'],
            'omitted_partial_files': sum(bool(f.get('excluded_tail_bytes')) for f in manifest['files']),
            'configuration': manifest['configuration']}


def generation_time(generation):
    # Public as_of fields have second precision. Preserve the exact boundary in
    # captured_at while every projection uses the same canonical UTC second.
    return datetime.fromisoformat(generation['captured_at'].replace('Z', '+00:00')).astimezone(timezone.utc).replace(microsecond=0)


def observation_paths(live):
    paths = list((live/'rows').glob('*/*.jsonl'))
    paths += list((live/'derived').glob('*/????-??.jsonl'))
    paths += [live/'derived/mind/claims.jsonl', live/'corrections.jsonl']
    return sorted(set(p for p in paths if p.exists()))


def frozen_manifest(live):
    root_text = os.environ.get('BEOPS_FROZEN_ROOT')
    if not root_text or pathlib.Path(root_text).resolve()/'data/live' != live:
        return None
    root = pathlib.Path(root_text).resolve()
    raw = (root/'runtime/release-inputs.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != os.environ.get('BEOPS_FROZEN_MANIFEST_SHA256'):
        raise ValueError('frozen observation manifest hash changed')
    manifest = json.loads(raw)
    marker = json.loads((root/'.beops-generated-workspace.json').read_text(encoding='utf-8'))
    if (manifest.get('schema') != 'beops-release-inputs/v1' or
            marker.get('source_oid') != manifest.get('source_oid') or
            marker.get('source_oid') != os.environ.get('BEOPS_FROZEN_SOURCE_OID')):
        raise ValueError('frozen observation source identity differs')
    return manifest


def verify(live, manifest):
    root = live.parent.parent
    expected = {}
    for entry in manifest['files']:
        rel = pathlib.PurePosixPath(entry['path'])
        if rel.is_absolute() or '..' in rel.parts or '\\' in entry['path']:
            raise ValueError('unsafe release input path')
        if entry['path'] in expected:
            raise ValueError('duplicate release input path')
        expected[entry['path']] = entry
    total = 0
    selected = {}
    for name, entry in expected.items():
        if is_observation_path(name):
            selected[name] = entry
    paths = observation_paths(live)
    actual = {p.relative_to(root).as_posix() for p in paths}
    if actual != set(selected):
        raise ValueError('frozen observation inventory changed')
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(live):
            raise ValueError('unsafe frozen observation path')
        entry = selected[path.relative_to(root).as_posix()]
        if entry.get('state_index_sealed') is True:
            observed = path.stat()
            if (observed.st_size != entry.get('bytes') or
                    observed.st_mtime_ns != entry.get('state_index_mtime_ns') or
                    observed.st_ino != entry.get('state_index_file_id') or
                    observed.st_dev != entry.get('state_index_device') or
                    observed.st_mode & (statmod.S_IWUSR | statmod.S_IWGRP | statmod.S_IWOTH)):
                raise ValueError('frozen observation identity changed: ' + entry['path'])
            total += entry['bytes']
            continue
        digest, size = hashlib.sha256(), 0
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''):
                digest.update(block)
                size += len(block)
        if size != entry['bytes'] or digest.hexdigest() != entry['sha256']:
            raise ValueError('frozen observation payload changed: ' + entry['path'])
        total += size
    return total
