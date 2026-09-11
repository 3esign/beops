"""Create a physical, private release workspace at one full Git OID and one input capture.

Code comes only from the OID. Evidence/data come from a hashed capture under writer locks.
No build command runs in the live repository. A failed preparation never touches the mirror.
"""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from contracts import atomic_json, exclusive


def git(root, *args):
    env = os.environ.copy()
    for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
        env.pop(name, None)
    return subprocess.run(['git', '-C', str(root), *args], env=env, check=True,
        capture_output=True, text=True, encoding='utf-8', timeout=120).stdout.strip()


def prepare(source, destination, oid=None):
    source = pathlib.Path(source).resolve()
    dest = pathlib.Path(destination).resolve()
    if dest == source or source in dest.parents:
        raise ValueError('release workspace must be outside the live source')
    if dest.exists():
        raise FileExistsError('release workspace already exists')
    oid = git(source, 'rev-parse', '--verify', (oid or 'HEAD') + '^{commit}')
    tree = git(source, 'rev-parse', oid + '^{tree}')
    dest.mkdir(parents=True)
    # A physical .git prevents tests that initialize temporary repositories from sharing source metadata.
    git(source, 'clone', '--bare', '--no-hardlinks', '--quiet', str(source), str(dest/'.git'))
    git(dest, 'config', 'core.bare', 'false')
    git(dest, 'update-ref', 'refs/heads/release', oid)
    git(dest, 'symbolic-ref', 'HEAD', 'refs/heads/release')
    git(dest, 'read-tree', oid)
    archive = dest / 'release-source.tar'
    git(source, 'archive', '--format=tar', '-o', str(archive), oid)
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            path = (dest / member.name).resolve()
            path.relative_to(dest)
            if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise ValueError('release archive contains a link or device')
        tar.extractall(dest, filter='data')
    archive.unlink()  # our own temporary archive
    inputs = []
    def copy_input(path):
        rel = path.relative_to(source)
        if path.is_symlink() or any(x.lower() in ('.env', 'secrets.json', 'kaggle.json') for x in rel.parts):
            raise ValueError('unsafe release input path')
        before = path.stat()
        data = path.read_bytes()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError('input changed during capture: ' + rel.as_posix())
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        inputs.append({'path':rel.as_posix(), 'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest()})
    with exclusive(source/'research/08-provenance/LEDGER.lock'), exclusive(source/'data/live/.write.lock'):
        for folder in ('research/evidence', 'research/observations', 'data/live/rows', 'data/live/derived', 'data/live/receipts'):
            directory = source / folder
            for path in sorted(directory.rglob('*')) if directory.exists() else []:
                if path.is_file() and path.suffix not in ('.lock', '.tmp'):
                    copy_input(path)
        for rel in ('research/08-provenance/LEDGER.jsonl', 'data/ca-bundle-windows.pem',
                    'data/live/corrections.jsonl', 'data/live/retention-ledger.jsonl', 'data/live/guard-ledger.jsonl', 'data/live/publish-receipt.json'):
            if (source/rel).is_file(): copy_input(source/rel)
        shape = dest/'research/RECORD_SHAPE.json'
        if shape.exists():
            names=json.loads(shape.read_text(encoding='utf-8')).get('files_directly_in_data_live',{}).get('files',{})
            copied={item['path'] for item in inputs}
            for name in names:
                if pathlib.Path(name).name!=name or name.endswith(('.lock','.tmp')):
                    continue
                path=source/'data/live'/name
                if path.is_file() and path.relative_to(source).as_posix() not in copied:copy_input(path)
    manifest = {'schema':'beops-release-inputs/v1','source_oid':oid,'source_tree':tree,
        'captured_at':datetime.now(timezone.utc).isoformat(), 'files':inputs}
    atomic_json(dest/'runtime/release-inputs.json',manifest)
    return {'workspace':str(dest),'source_oid':oid,'source_tree':tree,'input_files':len(inputs)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--destination',required=True);p.add_argument('--oid')
    args=p.parse_args();print(json.dumps(prepare(args.source,args.destination,args.oid)))
