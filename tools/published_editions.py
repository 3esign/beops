"""Verify immutable dataset editions from a fixed Git object, before release work.

The mirror working tree is never an authority for previously published bytes.
Recovery preserves every replaced byte in an explicit evidence archive first.
"""
import argparse
import hashlib
import io
import json
import pathlib
import re
import subprocess
import zipfile
from datetime import datetime, timezone

PREFIX = 'public/dataset/permission-landscape/releases'


def git(root, *args, **kw):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                            timeout=120, **kw)
    if result.returncode:
        raise ValueError('published editions: Git read failed: ' + result.stderr.decode('utf-8', 'replace')[:240])
    return result.stdout


def validate(files, edition):
    try:
        manifest = json.loads(files['MANIFEST.json'])
        if manifest.get('edition_id') != edition:
            raise ValueError('edition identity mismatch')
        names = set()
        for row in manifest['files']:
            name = row['name']
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or name in ('.', '..', 'MANIFEST.json') or name in names:
                raise ValueError('unsafe or duplicate payload name')
            names.add(name)
            payload = files[name]
            if len(payload) != row['bytes'] or hashlib.sha256(payload).hexdigest() != row['sha256']:
                raise ValueError('payload hash mismatch: ' + name)
        if not names or set(files) != names | {'MANIFEST.json'}:
            raise ValueError('edition membership mismatch')
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('invalid published edition ' + edition + ': ' + str(exc)) from exc


def committed(root, oid=None):
    root = pathlib.Path(root).resolve()
    if not (root/'.git').exists():
        if root.exists() and any(root.iterdir()):
            raise ValueError('published editions require a Git mirror')
        return None, {}
    # An initialized, unborn mirror has no prior editions.
    if oid is None:
        probe = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', 'HEAD'], capture_output=True, timeout=30)
        if probe.returncode:
            if (root/PREFIX).exists():
                raise ValueError('dataset files exist without a committed public HEAD')
            git(root, 'rev-parse', '--git-dir')
            return None, {}
        oid = probe.stdout.decode().strip()
    oid = git(root, 'rev-parse', '--verify', oid+'^{commit}').decode().strip()
    tree = git(root, 'ls-tree', '-r', '-z', oid, '--', PREFIX)
    if not tree:
        return oid, {}
    entries, editions = [], {}
    for line in tree.split(b'\0'):
        if not line: continue
        meta, path = line.split(b'\t', 1)
        mode, kind, blob = meta.split()
        rel = pathlib.PurePosixPath(path.decode('utf-8')).relative_to(PREFIX)
        if (mode not in (b'100644', b'100755') or kind != b'blob' or len(rel.parts) != 2
                or not re.fullmatch(r'[0-9a-f]{64}', rel.parts[0])):
            raise ValueError('unsafe published edition member')
        entries.append((rel, blob))
    # cat-file returns literal object bytes. git archive may apply line-ending
    # conversion on Windows, even when the object itself has the correct hash.
    data = io.BytesIO(git(root, 'cat-file', '--batch', input=b''.join(blob+b'\n' for _, blob in entries)))
    for rel, blob in entries:
        header = data.readline().split()
        if len(header) != 3 or header[0] != blob or header[1] != b'blob':
            raise ValueError('invalid Git blob response')
        size = int(header[2])
        if size > 64 * 1024 * 1024: raise ValueError('oversized edition member')
        payload = data.read(size)
        if len(payload) != size or data.read(1) != b'\n':
            raise ValueError('truncated Git blob')
        editions.setdefault(rel.parts[0], {})[rel.name] = payload
    for edition, files in editions.items():
        validate(files, edition)
    return oid, editions


def export(root, destination, oid=None):
    oid, editions = committed(root, oid)
    destination = pathlib.Path(destination).resolve()
    # Validate ALL committed bytes before writing the first output.
    for edition, files in editions.items():
        folder = destination/edition
        if folder.exists() and (folder.is_symlink() or not folder.resolve().is_relative_to(destination)):
            raise ValueError('linked edition destination')
        folder.mkdir(parents=True, exist_ok=True)
        for name, payload in files.items():
            target = folder/name
            if target.is_symlink():
                raise ValueError('linked edition output')
            target.write_bytes(payload)
    return {'source_oid': oid, 'editions': len(editions), 'files': sum(map(len, editions.values()))}


def recover(root, evidence):
    root, evidence = pathlib.Path(root).resolve(), pathlib.Path(evidence).resolve()
    if evidence.exists():
        raise ValueError('recovery evidence must be a new directory')
    oid, editions = committed(root)
    replace, unknown = [], []
    base = root/PREFIX
    for edition, files in editions.items():
        for name, payload in files.items():
            path = base/edition/name
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError('linked mirror input')
            old = path.read_bytes() if path.exists() else None
            if old != payload:
                # Recover the diagnosed corruption; never overwrite unrelated edits.
                if old and any(old):
                    raise ValueError('nonzero local edit requires review: ' + str(path.relative_to(root)))
                replace.append((path, payload, old))
    for directory in sorted(base.iterdir()) if base.exists() else []:
        if directory.name in editions:
            continue
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError('unexpected mirror edition path')
        for path in directory.rglob('*'):
            if path.is_symlink():
                raise ValueError('linked unknown edition')
            if path.is_file() and any(path.read_bytes()):
                raise ValueError('uncommitted nonzero edition requires review')
        unknown.append(directory)
    evidence.mkdir(parents=True)
    archive = evidence/'before-recovery.zip'
    records = []
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as saved:
        paths = [(p, old) for p, _, old in replace if old is not None]
        paths += [(p, p.read_bytes()) for d in unknown for p in d.rglob('*') if p.is_file()]
        for path, payload in paths:
            rel = path.relative_to(root).as_posix()
            saved.writestr(rel, payload)
            records.append({'path': rel, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()})
    with zipfile.ZipFile(archive) as saved:
        for row in records:
            if hashlib.sha256(saved.read(row['path'])).hexdigest() != row['sha256']:
                raise ValueError('recovery evidence verification failed')
    report = {'schema': 'beops-edition-recovery/v1', 'at': datetime.now(timezone.utc).isoformat(),
              'source_oid': oid, 'restored_files': len(replace), 'committed_editions': len(editions),
              'unresolved_local_editions': [p.name for p in unknown], 'preserved': records,
              'unknown_publication_history': 'not established; no replacement bytes invented'}
    (evidence/'recovery.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    for path, payload, _ in replace:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        if path.read_bytes() != payload:
            raise ValueError('restored bytes did not read back')
    # Keep unresolved originals in the mirror's own quarantine (same volume).
    quarantine = root.parent/'_to_delete'/('beops-unresolved-editions-'+evidence.name)
    if not quarantine.resolve().is_relative_to(root.parent):
        raise ValueError('quarantine escaped project parent')
    if unknown:
        quarantine.mkdir(parents=True, exist_ok=False)
        for path in unknown:
            path.rename(quarantine/path.name)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['check', 'export', 'recover'])
    parser.add_argument('mirror')
    parser.add_argument('--oid')
    parser.add_argument('--destination')
    args = parser.parse_args()
    if args.command == 'check':
        oid, editions = committed(args.mirror, args.oid)
        result = {'source_oid': oid, 'editions': len(editions), 'files': sum(map(len, editions.values()))}
    elif args.command == 'export':
        result = export(args.mirror, args.destination, args.oid)
    else:
        result = recover(args.mirror, args.destination)
        result = {k: v for k, v in result.items() if k != 'preserved'}
    print(json.dumps(result))
