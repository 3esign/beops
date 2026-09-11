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
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from contracts import atomic_json, exclusive


def git(root, *args):
    env = os.environ.copy()
    for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
        env.pop(name, None)
    result = subprocess.run(['git', '-C', str(root), *args], env=env,
        capture_output=True, text=True, encoding='utf-8', timeout=120)
    if result.returncode:
        raise RuntimeError(f'git {args[0]} failed ({result.returncode}): {result.stderr.strip()}')
    return result.stdout.strip()


def capture_inputs(source, dest):
    """Bound RAM with one temporary spool, then write destination files unlocked."""
    with tempfile.TemporaryFile(dir=dest.parent) as spool:
        return _capture_inputs(source, dest, spool)


def archive_paths(source, oid):
    """Evidence is captured once as input; scratch is never a release input.

    Explicit Git tree paths avoid unsupported archive exclude pathspecs and keep
    code selection tied to the fixed OID, even if the working tree changes.
    """
    paths = git(source, 'ls-tree', '--name-only', oid).splitlines()
    if 'research' in paths:
        paths.remove('research')
        paths.extend('research/'+p for p in git(source, 'ls-tree', '--name-only', oid+':research').splitlines()
                     if p not in ('evidence','_scratch'))
    return paths


def _capture_inputs(source, dest, spool):
    """Hold writer locks while spooling mutable bytes, not while writing many copies.

    Immutable evidence and receipts use a frozen path/stat inventory. Their bytes
    are copied after release and any intervening modification refuses the release.
    Mutable streams/caches enter one temporary container in 1 MiB chunks under
    the shared locks. Extraction and immutable copying happen after unlocking.
    """
    source, dest = pathlib.Path(source).resolve(), pathlib.Path(dest).resolve()
    immutable, inputs = [], []
    captured = set()
    cap = int(os.environ.get('BEOPS_CAPTURE_LIMIT_MB', '2048')) * 1024 * 1024
    total = 0

    def identity(path):
        rel = path.relative_to(source)
        if (path.is_symlink() or not path.resolve().is_relative_to(source)
                or any(x.lower().startswith(('.env', 'secrets.', 'kaggle.')) for x in rel.parts)):
            raise ValueError('unsafe release input path')
        st = path.stat()
        return rel, (st.st_size, st.st_mtime_ns)

    def verify(path, expected):
        rel, before = identity(path)
        if before != expected:
            raise RuntimeError('input changed after capture: ' + rel.as_posix())

    def collect(path, frozen_bytes):
        nonlocal total
        if path.suffix in ('.lock', '.tmp') or path in captured:
            return
        captured.add(path)
        rel, stat = identity(path)
        if frozen_bytes:
            total += stat[0]
            if total > cap:
                raise RuntimeError('mutable release input exceeds capture size limit; no release produced')
            with path.open('rb') as src, archive.open(rel.as_posix(), 'w') as member:
                shutil.copyfileobj(src, member, 1024 * 1024)
            verify(path, stat)
        else:
            immutable.append((path, rel, stat))

    with zipfile.ZipFile(spool, 'w', compression=zipfile.ZIP_STORED) as archive, exclusive(source/'research/08-provenance/LEDGER.lock'):
        for folder in ('research/evidence', 'data/live/receipts'):
            directory = source / folder
            for path in sorted(directory.rglob('*')) if directory.exists() else []:
                if path.is_file():
                    collect(path, False)
        # Timestamped model receipts and digests are immutable inputs too.
        # Reading thousands of them under the live lock exceeded other writers'
        # deadline. Inventory before locking; changed bytes still refuse release.
        for path in sorted((source/'data/live/derived').rglob('*.json')):
            if path.parent.name in ('receipts', 'digests') and path.is_file():
                collect(path, False)
        with exclusive(source/'data/live/.write.lock', timeout=120):
            started = time.monotonic()
            # Refresh only new immutable receipts after the writer boundary.
            for path in sorted((source/'data/live/receipts').glob('*/*.json')):
                if path not in captured:
                    collect(path, False)
            for folder in ('research/observations', 'data/live/rows', 'data/live/derived'):
                directory = source / folder
                for path in sorted(directory.rglob('*')) if directory.exists() else []:
                    if path.is_file():
                        collect(path, True)
            for rel in ('research/08-provenance/LEDGER.jsonl', 'data/ca-bundle-windows.pem',
                        'data/live/corrections.jsonl', 'data/live/retention-ledger.jsonl',
                        'data/live/guard-ledger.jsonl', 'data/live/publish-receipt.json'):
                if (source/rel).is_file():
                    collect(source/rel, True)
            shape = dest/'research/RECORD_SHAPE.json'
            if shape.exists():
                names = json.loads(shape.read_text(encoding='utf-8')).get('files_directly_in_data_live', {}).get('files', {})
                for name in names:
                    if pathlib.Path(name).name == name and (source/'data/live'/name).is_file():
                        collect(source/'data/live'/name, True)
            captured_at = datetime.now(timezone.utc).isoformat()
            lock_seconds = round(time.monotonic() - started, 3)

    def write(rel, stream):
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        digest, size = hashlib.sha256(), 0
        with target.open('wb') as out:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                out.write(block)
                digest.update(block)
                size += len(block)
        return {'path': rel.as_posix(), 'bytes': size, 'sha256': digest.hexdigest()}

    spool.seek(0)
    with zipfile.ZipFile(spool) as archive:
        for name in archive.namelist():
            with archive.open(name) as stream:
                inputs.append(write(pathlib.PurePosixPath(name), stream))
    def copy_immutable(entry):
        path, rel, stat = entry
        verify(path, stat)
        with path.open('rb') as stream:
            result = write(rel, stream)
        verify(path, stat)
        return result
    # These files share no output path. Bounded parallel I/O avoids spending an
    # entire publish cadence waiting for thousands of individual file operations.
    with ThreadPoolExecutor(max_workers=4) as pool:
        inputs.extend(pool.map(copy_immutable, immutable))
    inputs.sort(key=lambda r: r['path'])
    return inputs, captured_at, lock_seconds


def prepare(source, destination, oid=None):
    source = pathlib.Path(source).resolve()
    dest = pathlib.Path(destination).resolve()
    if dest == source or source in dest.parents:
        raise ValueError('release workspace must be outside the live source')
    if dest.exists():
        raise FileExistsError('release workspace already exists')
    oid = git(source, 'rev-parse', '--verify', (oid or 'HEAD') + '^{commit}')
    tree = git(source, 'rev-parse', oid + '^{tree}')
    dest.parent.mkdir(parents=True, exist_ok=True)
    # The spool and final input copy coexist. Refuse before allocating anything
    # large; a publish must never consume the operating system's last free bytes.
    input_bytes = sum(p.stat().st_size for folder in ('data/live', 'research/evidence', 'research/observations')
                      for p in (source/folder).rglob('*') if p.is_file() and p.suffix not in ('.lock', '.tmp'))
    required = 2 * input_bytes + 512 * 1024 * 1024
    available = shutil.disk_usage(dest.parent).free
    if available < required:
        raise RuntimeError(f'release disk space insufficient: {available} free bytes, {required} required')
    dest.mkdir()
    atomic_json(dest/'.beops-generated-workspace.json', {'source':str(source),'destination':str(dest),'source_oid':oid})
    # Independent Git metadata, read-only shared object store. This is a transient
    # build, not a backup: cloning the entire private history every ten minutes
    # filled the system disk. The fixed OID remains reachable in the source.
    git(source, 'clone', '--bare', '--shared', '--quiet', str(source), str(dest/'.git'))
    git(dest, 'config', 'core.bare', 'false')
    git(dest, 'update-ref', 'refs/heads/release', oid)
    git(dest, 'symbolic-ref', 'HEAD', 'refs/heads/release')
    git(dest, 'read-tree', oid)
    archive = dest / 'release-source.tar'
    git(source, 'archive', '--format=tar', '-o', str(archive), oid, '--', *archive_paths(source, oid))
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            path = (dest / member.name).resolve()
            path.relative_to(dest)
            if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise ValueError('release archive contains a link or device')
        tar.extractall(dest, filter='data')
    archive.unlink()  # our own temporary archive
    inputs, captured_at, lock_seconds = capture_inputs(source, dest)
    manifest = {'schema':'beops-release-inputs/v1','source_oid':oid,'source_tree':tree,
        'captured_at':captured_at, 'writer_lock_seconds':lock_seconds, 'files':inputs}
    atomic_json(dest/'runtime/release-inputs.json',manifest)
    return {'workspace':str(dest),'source_oid':oid,'source_tree':tree,'input_files':len(inputs), 'writer_lock_seconds':lock_seconds}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--destination',required=True);p.add_argument('--oid')
    args=p.parse_args();print(json.dumps(prepare(args.source,args.destination,args.oid)))
