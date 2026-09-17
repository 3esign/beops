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
from storage_health import require_release_capacity
from release_observation import is_observation_path


def trace_phase(name, event, seconds=None, **details):
    """Persist phase boundaries before work so a killed capture remains diagnosable."""
    trace = os.environ.get('BEOPS_PHASE_TRACE')
    if not trace:
        return
    row = dict(schema='beops-phase/v1', at=datetime.now(timezone.utc).isoformat(),
               pid=os.getpid(), name='capture: '+name, event=event, **details)
    if seconds is not None:
        row['seconds'] = seconds
    with open(trace, 'a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, separators=(',', ':'))+'\n')


def git(root, *args):
    env = os.environ.copy()
    for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
        env.pop(name, None)
    result = subprocess.run(['git', '-C', str(root), *args], env=env,
        capture_output=True, text=True, encoding='utf-8', timeout=120)
    if result.returncode:
        raise RuntimeError(f'git {args[0]} failed ({result.returncode}): {result.stderr.strip()}')
    return result.stdout.strip()


# C-080: every publish rewrote ~585 MB of permission evidence to the same disk (about 287 s of a
# 30-minute cadence), and the collector and the guard starved behind it. Evidence captures are
# written once and never edited, so the release links them instead of copying them. Only
# research/evidence is linked: those bytes are read, never written, by every build and test step.
# A link shares bytes with the source, so the stat check before and after, and os.path.samefile,
# still refuse a release whose input moved. Set BEOPS_RELEASE_LINK_EVIDENCE=0 to copy as before.
LINKABLE_PREFIXES = ('research/evidence/',)
# C-081: the other ~20,000 immutable inputs cost the release its time as metadata, not bytes. Every
# writer of these paths creates a file once (link-publish, 'wx', create-if-absent) or replaces it
# whole (os.replace gives the source a new file and leaves the release's link on the old bytes).
# The one file rewritten in place, receipts/<sid>/PAUSED, is never linked.
LINKABLE_PATTERNS = (
    ('data/live/receipts/', '.json'),
    ('data/live/raw/', ''),
    ('runtime/ai-feed/entries/', '.json'),
    ('runtime/ai-feed/contexts/', '.json'),
    ('runtime/ai-feed/prompts/', '.txt'),
)
LINKABLE_DERIVED = ('receipts', 'digests')


def linkable(posix):
    if posix.startswith(LINKABLE_PREFIXES):
        return True
    if os.environ.get('BEOPS_RELEASE_LINK_RECORD', '1') == '0':
        return False
    for prefix, suffix in LINKABLE_PATTERNS:
        if posix.startswith(prefix) and posix.endswith(suffix) and '/.' not in posix:
            return True
    parts = posix.split('/')
    return (posix.startswith('data/live/derived/') and len(parts) >= 3
            and parts[-2] in LINKABLE_DERIVED and posix.endswith('.json') and not parts[-1].startswith('.'))
HASH_CACHE_NAME = '.beops-evidence-sha-cache.json'
HASH_CACHE_MAX_AGE_SECONDS = 24 * 3600


def link_enabled():
    return os.environ.get('BEOPS_RELEASE_LINK_EVIDENCE', '1') != '0'


class EvidenceHashes:
    """sha256 by (path, size, mtime_ns), re-read from disk at least once a day."""

    def __init__(self, file):
        self.file = pathlib.Path(file)
        self.fresh = {}
        try:
            self.rows = json.loads(self.file.read_text(encoding='utf-8')).get('files', {})
        except (OSError, ValueError, AttributeError):
            self.rows = {}
        self.read_bytes = 0

    def sha(self, path, rel, stat):
        key = rel.as_posix()
        row = self.rows.get(key)
        now = time.time()
        if (isinstance(row, dict) and row.get('bytes') == stat[0] and row.get('mtime_ns') == stat[1]
                and now - float(row.get('hashed_at', 0)) < HASH_CACHE_MAX_AGE_SECONDS):
            self.fresh[key] = row
            return row['sha256']
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        self.read_bytes += stat[0]
        self.fresh[key] = {'bytes': stat[0], 'mtime_ns': stat[1], 'sha256': digest.hexdigest(), 'hashed_at': now}
        return digest.hexdigest()

    def save(self):
        try:
            atomic_json(self.file, {'schema': 'beops-evidence-sha-cache/v1', 'files': self.fresh})
        except OSError:
            pass


def capture_inputs(source, dest, metrics=None):
    """Bound RAM with one temporary spool, then write destination files unlocked."""
    with tempfile.TemporaryFile(dir=dest.parent) as spool:
        return _capture_inputs(source, dest, spool, metrics)


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


def _capture_inputs(source, dest, spool, metrics=None):
    """Hold writer locks while spooling mutable bytes, not while writing many copies.

    Immutable evidence and receipts use a frozen path/stat inventory. Their bytes
    are copied after release and any intervening modification refuses the release.
    Mutable streams/caches enter one temporary container in 1 MiB chunks under
    the shared locks. Extraction and immutable copying happen after unlocking.
    """
    source, dest = pathlib.Path(source).resolve(), pathlib.Path(dest).resolve()
    immutable, inputs = [], []
    metrics = metrics if metrics is not None else {}
    phase_started = time.monotonic()
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
        # In-flight collector claims disappear when the request finishes. They
        # are coordination markers, unlike durable JSON receipts and PAUSED.
        if path.suffix.lower() == '.claim' and path.relative_to(source).parts[:3] == ('data','live','receipts'):
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

    trace_phase('input inventory', 'start')
    with zipfile.ZipFile(spool, 'w', compression=zipfile.ZIP_STORED) as archive, exclusive(source/'research/08-provenance/LEDGER.lock'):
        # Receipts are not self-contained evidence: replayable receipts name the
        # immutable raw payload whose hash they attest. Keep both halves of that
        # reference in the isolated release. Raw captures are small compared with
        # rows/derived state and are immutable once their timestamped path exists.
        for folder in ('research/evidence', 'data/live/receipts', 'data/live/raw',
                       'runtime/ai-feed/entries', 'runtime/ai-feed/contexts', 'runtime/ai-feed/prompts'):
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
        metrics['inventory_seconds'] = round(time.monotonic()-phase_started, 3)
        trace_phase('input inventory', 'end', metrics['inventory_seconds'], files=len(immutable))
        phase_started = time.monotonic()
        trace_phase('mutable capture', 'start')
        with exclusive(source/'data/live/.write.lock', timeout=120):
            started = time.monotonic()
            # Refresh both sides of receipt -> raw references after the writer
            # boundary. A collector may have completed between the first inventory
            # and this lock, so refreshing receipts alone would create a release
            # whose own recovery tests cannot replay its newest observation.
            for pattern in ('data/live/receipts/*/*', 'data/live/raw/**/*'):
                for path in sorted(source.glob(pattern)):
                    if path not in captured and path.is_file():
                        collect(path, False)
            for folder in ('research/observations', 'data/live/rows', 'data/live/derived'):
                directory = source / folder
                for path in sorted(directory.rglob('*')) if directory.exists() else []:
                    if path not in captured and path.is_file():
                        collect(path, True)
            for rel in ('research/08-provenance/LEDGER.jsonl', 'data/ca-bundle-windows.pem',
                        'runtime/ai-feed/status.json',
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
        metrics['mutable_capture_seconds'] = round(time.monotonic()-phase_started, 3)
        trace_phase('mutable capture', 'end', metrics['mutable_capture_seconds'], writer_lock_seconds=lock_seconds, bytes=total)

    prepared_parents = set()

    def prepare_parent(parent):
        if parent not in prepared_parents:
            if parent != dest:
                prepare_parent(parent.parent)
            parent.mkdir(exist_ok=True)
            prepared_parents.add(parent)

    def write(rel, stream):
        target = dest / rel
        prepare_parent(target.parent)
        digest, size = hashlib.sha256(), 0
        complete_digest, complete_size = hashlib.sha256(), 0
        prefix_only = is_observation_path(rel.as_posix())
        count_rows = rel.as_posix().startswith('data/live/rows/') and rel.suffix == '.jsonl'
        row_count, pending_nonblank = 0, False
        with target.open('wb') as out:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                out.write(block)
                last_lf = block.rfind(b'\n') if prefix_only else -1
                if last_lf >= 0:
                    complete_digest = digest.copy()
                    complete_digest.update(block[:last_lf+1])
                    complete_size = size + last_lf + 1
                digest.update(block)
                size += len(block)
                if count_rows:
                    # Count the same captured bytes while they are already in RAM.
                    # Independent from the paper's line iterator; no second disk pass.
                    parts = block.split(b'\n')
                    if len(parts) == 1:
                        pending_nonblank = pending_nonblank or bool(parts[0].strip())
                    else:
                        row_count += bool(pending_nonblank or parts[0].strip())
                        row_count += sum(bool(part.strip()) for part in parts[1:-1])
                        pending_nonblank = bool(parts[-1].strip())
            if prefix_only:
                out.truncate(complete_size)
        result = {'path': rel.as_posix(), 'bytes': complete_size if prefix_only else size,
                  'sha256': complete_digest.hexdigest() if prefix_only else digest.hexdigest()}
        if prefix_only:
            result.update(source_bytes=size, source_sha256=digest.hexdigest(),
                          excluded_tail_bytes=size-complete_size)
        if count_rows:
            result['nonblank_lines'] = row_count
        return result

    phase_started = time.monotonic()
    trace_phase('mutable extract', 'start')
    spool.seek(0)
    with zipfile.ZipFile(spool) as archive:
        for name in archive.namelist():
            with archive.open(name) as stream:
                inputs.append(write(pathlib.PurePosixPath(name), stream))
    metrics['mutable_extract_seconds'] = round(time.monotonic()-phase_started, 3)
    metrics['spooled_bytes'] = total
    metrics['extracted_bytes'] = sum(item['bytes'] for item in inputs)
    trace_phase('mutable extract', 'end', metrics['mutable_extract_seconds'], bytes=metrics['extracted_bytes'])
    hashes = EvidenceHashes(dest.parent / HASH_CACHE_NAME) if link_enabled() else None
    linked = []

    def copy_immutable(entry):
        path, rel, stat = entry
        verify(path, stat)
        posix = rel.as_posix()
        if hashes is not None and linkable(posix) and not is_observation_path(posix):
            target = dest / rel
            try:
                os.link(path, target)
            except OSError:
                pass                      # another volume or no link support: copy as before
            else:
                digest = hashes.sha(path, rel, stat)
                verify(path, stat)
                if not os.path.samefile(path, target):
                    raise RuntimeError('linked input is not the captured file: ' + posix)
                linked.append(stat[0])
                return {'path': posix, 'bytes': stat[0], 'sha256': digest}
        with path.open('rb') as stream:
            result = write(rel, stream)
        verify(path, stat)
        return result
    # These files share no output path. Bounded parallel I/O avoids spending an
    # entire publish cadence waiting for thousands of individual file operations.
    phase_started = time.monotonic()
    trace_phase('immutable copy', 'start', files=len(immutable), bytes=sum(entry[2][0] for entry in immutable))
    # Set up shared output directories once before workers start. Repeated mkdir
    # on Windows also stats each existing directory, multiplying metadata I/O.
    for parent in sorted({(dest / rel).parent for _, rel, _ in immutable}):
        prepare_parent(parent)
    with ThreadPoolExecutor(max_workers=4) as pool:
        inputs.extend(pool.map(copy_immutable, immutable))
    metrics['immutable_copy_seconds'] = round(time.monotonic()-phase_started, 3)
    metrics['linked_files'] = len(linked)
    metrics['linked_bytes'] = sum(linked)
    if hashes is not None:
        metrics['evidence_bytes_hashed'] = hashes.read_bytes
        hashes.save()
    trace_phase('immutable copy', 'end', metrics['immutable_copy_seconds'])
    metrics['captured_bytes'] = sum(item['bytes'] for item in inputs)
    metrics['captured_files'] = len(inputs)
    inputs.sort(key=lambda r: r['path'])
    return inputs, captured_at, lock_seconds


def prepare(source, destination, oid=None, owner_pid=None, retained=False):
    timings = {}
    phase_started = time.monotonic()
    trace_phase('capacity and inventory', 'start')
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
    input_bytes = sum(p.stat().st_size for folder in ('data/live', 'research/evidence', 'research/observations', 'runtime/ai-feed')
                      for p in (source/folder).rglob('*') if p.is_file() and p.suffix not in ('.lock', '.tmp'))
    source_bytes = sum(int(line.split()[3]) for line in git(source, 'ls-tree', '-r', '-l', oid).splitlines()
                       if len(line.split()) >= 4 and line.split()[3].isdigit())
    capacity = require_release_capacity(dest.parent, input_bytes, source_bytes)
    timings['capacity_and_inventory_seconds'] = round(time.monotonic()-phase_started, 3)
    trace_phase('capacity and inventory', 'end', timings['capacity_and_inventory_seconds'], input_bytes=input_bytes, source_bytes=source_bytes)
    phase_started = time.monotonic()
    trace_phase('fixed source', 'start')
    dest.mkdir()
    atomic_json(dest/'.beops-generated-workspace.json', {'schema':'beops-generated-workspace/v2',
        'source':str(source),'destination':str(dest),'source_oid':oid,
        'owner_pid':owner_pid or os.getpid(), 'created_at':datetime.now(timezone.utc).isoformat(),
        'retained':bool(retained)})
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
    timings['fixed_source_seconds'] = round(time.monotonic()-phase_started, 3)
    trace_phase('fixed source', 'end', timings['fixed_source_seconds'])
    inputs, captured_at, lock_seconds = capture_inputs(source, dest, timings)
    configuration = []
    for name in ('research/COLLECTORS.json', 'research/SOURCE_REGISTRY.json', 'research/ORGANS.json'):
        file = dest/name
        if file.is_file():
            raw = file.read_bytes()
            configuration.append({'path':name, 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()})
    manifest = {'schema':'beops-release-inputs/v1','source_oid':oid,'source_tree':tree,
        'observation_prefix':'complete-lf-lines/v1', 'configuration':configuration,
        'captured_at':captured_at, 'writer_lock_seconds':lock_seconds, 'capacity':capacity,
        'timings':timings, 'files':inputs}
    atomic_json(dest/'runtime/release-inputs.json',manifest)
    return {'workspace':str(dest),'source_oid':oid,'source_tree':tree,'input_files':len(inputs), 'writer_lock_seconds':lock_seconds}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--destination',required=True);p.add_argument('--oid')
    p.add_argument('--owner-pid',type=int);p.add_argument('--retained',action='store_true')
    args=p.parse_args();print(json.dumps(prepare(args.source,args.destination,args.oid,args.owner_pid,args.retained)))
