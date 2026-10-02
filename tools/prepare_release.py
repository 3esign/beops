"""Create a physical, private release workspace at one full Git OID and one input capture.

Code comes only from the OID. Evidence/data come from a hashed capture under writer locks.
No build command runs in the live repository. A failed preparation never touches the mirror.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat as statmod
import subprocess
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from contracts import atomic_json, exclusive
from storage_health import (CAPACITY_FORMULA, CAPACITY_SCHEMA, CAPACITY_PARTITION_SCHEMA,
                            CAPACITY_PARTITION_FORMULA, CAPACITY_EVIDENCE_ORIGIN,
                            ReleaseCapacityError, require_release_capacity)
from release_inventory import build_inventory, inventory_summary, save_cache
from release_observation import is_observation_path

STATE_KEY_PATTERN = re.compile(
    rb'"(?:s|\\u0073)(?:t|\\u0074)(?:a|\\u0061)(?:t|\\u0074)(?:e|\\u0065)"[ \t\r\n]*:'
)
STATE_KEY_TAIL_BYTES = 64
STATE_KEY_PREFILTER = (b'"state"', b'\\u0073', b'\\u0074', b'\\u0061', b'\\u0065')
RECEIVED_TIME_PATTERN = re.compile(rb'"receivedTime"[ \t\r\n]*:[ \t\r\n]*"([^"]+)"')


def raw_may_spell_state_key(raw):
    return any(needle in raw for needle in STATE_KEY_PREFILTER)


def _json_depth_before(raw: bytes, stop: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for ch in raw[:stop]:
        if in_string:
            if escaped:
                escaped = False
            elif ch == 92:  # backslash
                escaped = True
            elif ch == 34:  # "
                in_string = False
            continue
        if ch == 34:  # "
            in_string = True
        elif ch in (123, 91):  # { [
            depth += 1
        elif ch in (125, 93):  # } ]
            depth -= 1
    return depth


def raw_has_top_level_state_key(raw: bytes) -> bool:
    if not raw_may_spell_state_key(raw):
        return False
    for match in STATE_KEY_PATTERN.finditer(raw):
        if _json_depth_before(raw, match.start()) == 1:
            return True
    return False


def scan_state_key_block(pending: bytes, block: bytes) -> tuple[bytes, bool]:
    haystack = pending + block
    lines = haystack.split(b'\n')
    for raw_line in lines[:-1]:
        if raw_has_top_level_state_key(raw_line):
            return b'', True
    return lines[-1], False


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


def git(root, *args, timeout_sec=120):
    env = os.environ.copy()
    for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
        env.pop(name, None)
    result = subprocess.run(['git', '-C', str(root), *args], env=env,
        capture_output=True, text=True, encoding='utf-8', timeout=timeout_sec)
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
PROGRESS_NAME = '.beops-prepare-progress.json'
CAPACITY_ESTIMATE_MARGIN_BYTES = 512 * 1024 * 1024
CAPACITY_CACHED_ORIGIN = 'runtime/release-inputs-last.json+512MiB'


def link_enabled():
    return os.environ.get('BEOPS_RELEASE_LINK_EVIDENCE', '1') != '0'


# 2026-10-01: a closed month is sealed once, not re-frozen every cycle. Rows are appended by
# reception month (collect_daemon.append_rows), so a month file is final once its month is over.
# Until now every release copied all rows under the collectors' write lock: 1.06 GB, 111-629 s of
# lock and 33-195 s of re-hashing per cycle, almost all of it September. A closed month is now
# linked like evidence, its facts (sha256, rows, newest reception, state key) are read once and
# cached by (bytes, mtime_ns, file id), and the shared file is made read-only: that is the seal.
# The grace covers a collector that received in the old month and wrote just after midnight.
# Retention (tools/apply_retention.py) lifts the seal before it redacts. Switch off with
# BEOPS_RELEASE_SEAL_MONTHS=0 to capture every month under the lock as before.
SEALED_MONTHS_NAME = '.beops-sealed-months.json'
SEAL_GRACE_HOURS = 6
MONTH_FILE = re.compile(r'^data/live/rows/[^/]+/(\d{4})-(\d{2})\.jsonl$')


def sealed_month(posix, now=None):
    if os.environ.get('BEOPS_RELEASE_SEAL_MONTHS', '1') == '0':
        return False
    match = MONTH_FILE.match(posix)
    if not match:
        return False
    year, month = int(match.group(1)), int(match.group(2))
    following = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=timezone.utc)
    return (now or datetime.now(timezone.utc)) >= following + timedelta(hours=SEAL_GRACE_HOURS)


def describe_observation(path):
    """Release facts of one observation file, the same ones write() derives while copying."""
    digest, size, last = hashlib.sha256(), 0, b''
    state_tail, state_key_present = b'', False
    row_count, pending_nonblank = 0, False
    row_tail, newest_received_time = b'', None
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
            last = block[-1:]
            if not state_key_present:
                state_tail, state_key_present = scan_state_key_block(state_tail, block)
            parts = block.split(b'\n')
            if len(parts) == 1:
                pending_nonblank = pending_nonblank or bool(parts[0].strip())
            else:
                row_count += bool(pending_nonblank or parts[0].strip())
                row_count += sum(bool(part.strip()) for part in parts[1:-1])
                pending_nonblank = bool(parts[-1].strip())
            row_parts = (row_tail + block).split(b'\n')
            for raw_line in row_parts[:-1]:
                if not raw_line.strip():
                    continue
                match = RECEIVED_TIME_PATTERN.search(raw_line)
                if match:
                    try:
                        stamp = match.group(1).decode('ascii')
                    except UnicodeDecodeError:
                        stamp = None
                    if stamp and (newest_received_time is None or stamp > newest_received_time):
                        newest_received_time = stamp
            row_tail = row_parts[-1]
    if not state_key_present and state_tail:
        state_key_present = raw_has_top_level_state_key(state_tail)
    return {'bytes': size, 'sha256': digest.hexdigest(), 'complete': size == 0 or last == b'\n',
            'nonblank_lines': row_count, 'newest_received_time': newest_received_time,
            'state_key_present': state_key_present}


class SealedMonths:
    """Facts of closed month files by (bytes, mtime_ns, file id), re-read at least once a day."""

    def __init__(self, file):
        self.file = pathlib.Path(file)
        self.fresh = {}
        try:
            self.rows = json.loads(self.file.read_text(encoding='utf-8')).get('files', {})
        except (OSError, ValueError, AttributeError):
            self.rows = {}
        self.read_bytes = 0

    def facts(self, path, posix, observed):
        row = self.rows.get(posix)
        now = time.time()
        if (isinstance(row, dict) and row.get('bytes') == observed.st_size
                and row.get('mtime_ns') == observed.st_mtime_ns and row.get('file_id') == observed.st_ino
                and now - float(row.get('read_at', 0)) < HASH_CACHE_MAX_AGE_SECONDS):
            self.fresh[posix] = row
            return row
        facts = describe_observation(path)
        self.read_bytes += facts['bytes']
        row = {**facts, 'mtime_ns': observed.st_mtime_ns, 'file_id': observed.st_ino, 'read_at': now}
        self.fresh[posix] = row
        return row

    def save(self, partial=False):
        files = {**self.rows, **self.fresh} if partial else self.fresh
        try:
            atomic_json(self.file, {'schema': 'beops-sealed-months/v1', 'files': files})
        except OSError:
            pass


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

    def save(self, partial=False):
        # A partial save (mid-copy checkpoint) keeps loaded rows the walk has not
        # revisited yet; only the completed save prunes deleted inputs. Measured
        # 2026-10-01: taskkill /F ends an over-budget cycle with no finally, so a
        # cache written only at the end lost every hash a killed attempt had read.
        files = {**self.rows, **self.fresh} if partial else self.fresh
        try:
            atomic_json(self.file, {'schema': 'beops-evidence-sha-cache/v1', 'files': files})
        except OSError:
            pass


def capture_inputs(source, dest, metrics=None):
    """Freeze release inputs with bounded RAM and short live writer locks."""
    return _capture_inputs(source, dest, metrics)


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


def archive_source_bytes(source, oid, paths):
    """Measure only fixed-OID files actually extracted into the release.

    Evidence is captured separately, so asking Git for its blob sizes repeats
    work over thousands of inputs and counts those bytes in both allocations.
    """
    if not paths:
        return 0
    rows = git(source, 'ls-tree', '-r', '-l', oid, '--', *paths, timeout_sec=600)
    return sum(int(fields[3]) for line in rows.splitlines()
               if len(fields := line.split()) >= 4 and fields[3].isdigit())


def estimate_release_input_bytes(source, *, use_cached=True, inventory=None):
    """Avoid a duplicate deep stat walk, or explicitly recount current inputs."""
    if inventory is not None:
        inventory.clear()
    manifest = source / 'runtime/release-inputs-last.json'
    if use_cached and manifest.is_file():
        try:
            previous = json.loads(manifest.read_text(encoding='utf-8-sig'))
            captured = int(previous.get('timings', {}).get('captured_bytes') or 0)
            if captured > 0:
                return captured + CAPACITY_ESTIMATE_MARGIN_BYTES, CAPACITY_CACHED_ORIGIN
        except (OSError, ValueError, TypeError):
            pass
    input_bytes, evidence_bytes = 0, 0
    for folder in ('data/live', 'research/evidence', 'research/observations',
                   'runtime/ai-feed', 'runtime/resources/receipts'):
        for path in (source/folder).rglob('*'):
            if path.is_file() and path.suffix not in ('.lock', '.tmp'):
                size = path.stat().st_size
                input_bytes += size
                if folder == 'research/evidence':
                    evidence_bytes += size
    if inventory is not None:
        inventory['evidence_bytes'] = evidence_bytes
    return input_bytes, 'live_stat_scan'


def release_capacity(source, parent, input_bytes, input_bytes_from, source_bytes, *, evidence_bytes=0):
    """Recount a refused cached estimate and classify capture-only evidence.

    The cached manifest adds a growth allowance to avoid routine deep scans.
    Near the capacity boundary that allowance can reject a release which the
    current input inventory can fit. A fresh stat walk supplies a new estimate
    to the same guard. Evidence is budgeted for one physical copy, including
    hardlink fallback. Scan/storage errors and an exact refusal still fail.
    """
    if evidence_bytes and input_bytes_from != 'live_stat_scan':
        raise ValueError('evidence allocation requires a fresh input inventory')

    def require():
        options = {'evidence_bytes': evidence_bytes} if evidence_bytes else {}
        return require_release_capacity(parent, input_bytes, source_bytes, **options)

    def record(capacity, admitted):
        partition = ({'evidence_bytes': evidence_bytes,
                      'evidence_bytes_from': CAPACITY_EVIDENCE_ORIGIN} if evidence_bytes else {})
        atomic_json(source/'runtime/release-capacity.json', {
            'schema': CAPACITY_PARTITION_SCHEMA if evidence_bytes else CAPACITY_SCHEMA,
            'at': datetime.now(timezone.utc).isoformat(),
            'source': str(pathlib.Path(source).resolve()),
            'release_parent': str(pathlib.Path(parent).resolve()),
            'input_bytes': input_bytes, 'input_bytes_from': input_bytes_from,
            'source_bytes': source_bytes,
            'formula': CAPACITY_PARTITION_FORMULA if evidence_bytes else CAPACITY_FORMULA,
            'admitted': admitted, **partition, **capacity})

    try:
        try:
            capacity = require()
        except ReleaseCapacityError:
            if input_bytes_from != CAPACITY_CACHED_ORIGIN:
                raise
            started = time.monotonic()
            trace_phase('capacity recount', 'start', cached_input_bytes=input_bytes,
                        source_bytes=source_bytes)
            inventory = {}
            input_bytes, input_bytes_from = estimate_release_input_bytes(source, use_cached=False, inventory=inventory)
            evidence_bytes = inventory.get('evidence_bytes', 0)
            capacity = require()
            trace_phase('capacity recount', 'end', round(time.monotonic()-started, 3),
                        input_bytes=input_bytes, input_bytes_from=input_bytes_from,
                        source_bytes=source_bytes, evidence_bytes=evidence_bytes)
    except ReleaseCapacityError as exc:
        if exc.capacity is not None:
            record(exc.capacity, False)
        raise
    record(capacity, True)
    return capacity, input_bytes, input_bytes_from


def _capture_inputs(source, dest, metrics=None):
    """Hold writer locks only while freezing mutable bytes.

    Immutable evidence and receipts use a frozen path/stat inventory. Their bytes
    are copied after release and any intervening modification refuses the release.
    Mutable streams/caches are copied directly into the release under the shared
    lock, then hashed, prefix-trimmed and sealed after unlocking.
    """
    source, dest = pathlib.Path(source).resolve(), pathlib.Path(dest).resolve()
    immutable, mutable, inputs = [], [], []
    metrics = metrics if metrics is not None else {}
    phase_started = time.monotonic()
    trace_phase('input inventory', 'start')
    inventory_file = source / 'runtime/inventory-cache.jsonl'
    initial_inventory, inventory_cache, inventory_metrics, observed_entries = build_inventory(
        source, inventory_file)
    metrics['inventory_seconds'] = inventory_metrics['seconds']
    metrics['inventory_files'] = inventory_metrics['files']
    metrics['inventory_hashed_files'] = inventory_metrics['hashed_files']
    metrics['inventory_hashed_bytes'] = inventory_metrics['hashed_bytes']
    metrics['inventory_initial_root'] = initial_inventory['root']
    captured = set()
    cap = int(os.environ.get('BEOPS_CAPTURE_LIMIT_MB', '2048')) * 1024 * 1024
    total = 0
    prepared_parents = set()

    def prepare_parent(parent):
        if parent not in prepared_parents:
            if parent != dest:
                prepare_parent(parent.parent)
            parent.mkdir(exist_ok=True)
            prepared_parents.add(parent)

    def unsafe_name(rel):
        return any(x.lower().startswith(('.env', 'secrets.', 'kaggle.')) for x in rel.parts)

    def identity(path):
        rel = path.relative_to(source)
        if (path.is_symlink() or not path.resolve().is_relative_to(source)
                or unsafe_name(rel)):
            raise ValueError('unsafe release input path')
        return rel, path.stat()

    def verify(path, expected):
        rel, before = identity(path)
        if (before.st_size, before.st_mtime_ns) != expected:
            raise RuntimeError('input changed after capture: ' + rel.as_posix())
        return before

    def collect(path, frozen_bytes, rel=None, observed=None, inventory_sha=None):
        nonlocal total
        if path.suffix in ('.lock', '.tmp') or path in captured:
            return
        # In-flight collector claims disappear when the request finishes. They
        # are coordination markers, unlike durable JSON receipts and PAUSED.
        if path.suffix.lower() == '.claim' and path.relative_to(source).parts[:3] == ('data','live','receipts'):
            return
        captured.add(path)
        if rel is None:
            rel, observed = identity(path)
            stat = (observed.st_size, observed.st_mtime_ns)
        else:
            rel = pathlib.Path(rel)
            if unsafe_name(rel):
                raise ValueError('unsafe release input path')
            stat = observed
        if frozen_bytes:
            total += stat[0]
            if total > cap:
                raise RuntimeError('mutable release input exceeds capture size limit; no release produced')
            target = dest / rel
            prepare_parent(target.parent)
            if target.exists():
                # A resumed workspace may hold this path from the interrupted
                # attempt, possibly sealed read-only; mutable bytes are always
                # recaptured fresh.
                target.chmod(statmod.S_IREAD | statmod.S_IWRITE)
                target.unlink()
            shutil.copyfile(path, target)
            verify(path, stat)
            mutable.append(rel)
        else:
            immutable.append((path, rel, stat, inventory_sha))

    # The inventory already made the one metadata walk for every immutable scope.
    # Reuse its observed stat and cached hash instead of rglob + stat-ing the same
    # 49k entries again. Files that appear at the writer boundary are added below
    # and receive the same post-copy verification.
    for path, rel, stat, sha in observed_entries:
        collect(path, False, rel=rel, observed=stat, inventory_sha=sha)
    metrics['inventory_seconds'] = round(time.monotonic()-phase_started, 3)
    trace_phase('input inventory', 'end', metrics['inventory_seconds'], files=len(immutable),
                root=initial_inventory['root'])
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
                    # A closed month is final: it leaves the lock and is linked below.
                    collect(path, not (link_enabled() and sealed_month(path.relative_to(source).as_posix())))
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

    def write(rel, stream):
        target = dest / rel
        prepare_parent(target.parent)
        if target.exists():
            # Stale bytes from an interrupted attempt, possibly sealed read-only.
            target.chmod(statmod.S_IREAD | statmod.S_IWRITE)
            target.unlink()
        digest, size = hashlib.sha256(), 0
        complete_digest, complete_size = hashlib.sha256(), 0
        prefix_only = is_observation_path(rel.as_posix())
        count_rows = rel.as_posix().startswith('data/live/rows/') and rel.suffix == '.jsonl'
        index_state_key = (rel.suffix == '.jsonl' and
                           rel.as_posix().startswith(('data/live/rows/', 'data/live/derived/')))
        state_tail, state_key_present = b'', False
        row_count, pending_nonblank = 0, False
        row_tail, newest_received_time = b'', None
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
                if index_state_key and not state_key_present:
                    state_tail, state_key_present = scan_state_key_block(state_tail, block)
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
                    row_bytes = row_tail + block
                    row_parts = row_bytes.split(b'\n')
                    for raw_line in row_parts[:-1]:
                        if not raw_line.strip():
                            continue
                        match = RECEIVED_TIME_PATTERN.search(raw_line)
                        if match:
                            try:
                                stamp = match.group(1).decode('ascii')
                            except UnicodeDecodeError:
                                stamp = None
                            if stamp and (newest_received_time is None or stamp > newest_received_time):
                                newest_received_time = stamp
                    row_tail = row_parts[-1]
            if prefix_only:
                out.truncate(complete_size)
        if index_state_key and not state_key_present and state_tail:
            state_key_present = raw_has_top_level_state_key(state_tail)
        sealed_stat = None
        if index_state_key:
            # The state index describes these exact captured bytes. Freeze them
            # before the manifest is written so later builders cannot invalidate
            # the index with an accidental same-size rewrite.
            target.chmod(statmod.S_IREAD)
            sealed_stat = target.stat()
        result = {'path': rel.as_posix(), 'bytes': complete_size if prefix_only else size,
                  'sha256': complete_digest.hexdigest() if prefix_only else digest.hexdigest()}
        if prefix_only:
            result.update(source_bytes=size, source_sha256=digest.hexdigest(),
                          excluded_tail_bytes=size-complete_size)
        if count_rows:
            result['nonblank_lines'] = row_count
            if newest_received_time:
                result['newest_received_time'] = newest_received_time
        if index_state_key:
            # This is an acceleration claim over the exact bytes already hashed into
            # release-inputs.json, never a second source of truth. A possible match in
            # an excluded partial observation tail is a safe false positive: the state
            # test will parse that frozen file instead of skipping it.
            result['state_key_present'] = state_key_present
            result.update(state_index_sealed=True,
                          state_index_mtime_ns=sealed_stat.st_mtime_ns,
                           state_index_file_id=sealed_stat.st_ino,
                           state_index_device=sealed_stat.st_dev)
        return result

    def seal_existing(rel):
        target = dest / rel
        digest, size = hashlib.sha256(), 0
        complete_digest, complete_size = hashlib.sha256(), 0
        prefix_only = is_observation_path(rel.as_posix())
        count_rows = rel.as_posix().startswith('data/live/rows/') and rel.suffix == '.jsonl'
        index_state_key = (rel.suffix == '.jsonl' and
                           rel.as_posix().startswith(('data/live/rows/', 'data/live/derived/')))
        state_tail, state_key_present = b'', False
        row_count, pending_nonblank = 0, False
        row_tail, newest_received_time = b'', None
        with target.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                last_lf = block.rfind(b'\n') if prefix_only else -1
                if last_lf >= 0:
                    complete_digest = digest.copy()
                    complete_digest.update(block[:last_lf+1])
                    complete_size = size + last_lf + 1
                digest.update(block)
                size += len(block)
                if index_state_key and not state_key_present:
                    state_tail, state_key_present = scan_state_key_block(state_tail, block)
                if count_rows:
                    parts = block.split(b'\n')
                    if len(parts) == 1:
                        pending_nonblank = pending_nonblank or bool(parts[0].strip())
                    else:
                        row_count += bool(pending_nonblank or parts[0].strip())
                        row_count += sum(bool(part.strip()) for part in parts[1:-1])
                        pending_nonblank = bool(parts[-1].strip())
                    row_bytes = row_tail + block
                    row_parts = row_bytes.split(b'\n')
                    for raw_line in row_parts[:-1]:
                        if not raw_line.strip():
                            continue
                        match = RECEIVED_TIME_PATTERN.search(raw_line)
                        if match:
                            try:
                                stamp = match.group(1).decode('ascii')
                            except UnicodeDecodeError:
                                stamp = None
                            if stamp and (newest_received_time is None or stamp > newest_received_time):
                                newest_received_time = stamp
                    row_tail = row_parts[-1]
        if prefix_only:
            with target.open('r+b') as out:
                out.truncate(complete_size)
        if index_state_key and not state_key_present and state_tail:
            state_key_present = raw_has_top_level_state_key(state_tail)
        sealed_stat = None
        if index_state_key:
            target.chmod(statmod.S_IREAD)
            sealed_stat = target.stat()
        result = {'path': rel.as_posix(), 'bytes': complete_size if prefix_only else size,
                  'sha256': complete_digest.hexdigest() if prefix_only else digest.hexdigest()}
        if prefix_only:
            result.update(source_bytes=size, source_sha256=digest.hexdigest(),
                          excluded_tail_bytes=size-complete_size)
        if count_rows:
            result['nonblank_lines'] = row_count
            if newest_received_time:
                result['newest_received_time'] = newest_received_time
        if index_state_key:
            result['state_key_present'] = state_key_present
            result.update(state_index_sealed=True,
                          state_index_mtime_ns=sealed_stat.st_mtime_ns,
                          state_index_file_id=sealed_stat.st_ino,
                          state_index_device=sealed_stat.st_dev)
        return result

    phase_started = time.monotonic()
    trace_phase('mutable extract', 'start')
    for rel in mutable:
        inputs.append(seal_existing(rel))
    metrics['mutable_extract_seconds'] = round(time.monotonic()-phase_started, 3)
    metrics['spooled_bytes'] = total
    metrics['mutable_copied_bytes'] = total
    metrics['extracted_bytes'] = sum(item['bytes'] for item in inputs)
    trace_phase('mutable extract', 'end', metrics['mutable_extract_seconds'], bytes=metrics['extracted_bytes'])
    hashes = EvidenceHashes(dest.parent / HASH_CACHE_NAME) if link_enabled() else None
    seals = SealedMonths(dest.parent / SEALED_MONTHS_NAME) if link_enabled() else None
    linked = []
    sealed = []

    def link_sealed(path, rel, stat):
        posix = rel.as_posix()
        facts = seals.facts(path, posix, path.stat())
        if not facts['complete'] or (facts['bytes'], facts['mtime_ns']) != tuple(stat):
            return None  # a partial last line or a moved file: capture it the ordinary way
        target = dest / rel
        if target.exists() and not os.path.samestat(path.stat(), target.stat()):
            target.chmod(statmod.S_IREAD | statmod.S_IWRITE)
            target.unlink()
        if not target.exists():
            try:
                os.link(path, target)
            except OSError:
                return None  # another volume or no link support: copy as before
        target.chmod(statmod.S_IREAD)
        verified = verify(path, stat)
        sealed_stat = target.stat()
        if not os.path.samestat(verified, sealed_stat):
            raise RuntimeError('sealed month is not the captured file: ' + posix)
        linked.append(stat[0])
        sealed.append(stat[0])
        result = {'path': posix, 'bytes': facts['bytes'], 'sha256': facts['sha256'],
                  'source_bytes': facts['bytes'], 'source_sha256': facts['sha256'], 'excluded_tail_bytes': 0,
                  'nonblank_lines': facts['nonblank_lines']}
        if facts.get('newest_received_time'):
            result['newest_received_time'] = facts['newest_received_time']
        result['state_key_present'] = facts['state_key_present']
        result.update(state_index_sealed=True, state_index_mtime_ns=sealed_stat.st_mtime_ns,
                      state_index_file_id=sealed_stat.st_ino, state_index_device=sealed_stat.st_dev)
        return result

    def copy_immutable(entry):
        path, rel, stat, known_sha = entry
        verify(path, stat)
        posix = rel.as_posix()
        if seals is not None and sealed_month(posix):
            result = link_sealed(path, rel, stat)
            if result is not None:
                return result
        if hashes is not None and linkable(posix) and not is_observation_path(posix):
            target = dest / rel
            already_linked = False
            if target.exists():
                # A resumed workspace may already hold this input. Reuse it only
                # when it is the very same inode; anything else is replaced.
                if os.path.samestat(path.stat(), target.stat()):
                    already_linked = True
                else:
                    target.chmod(statmod.S_IREAD | statmod.S_IWRITE)
                    target.unlink()
            if not already_linked:
                try:
                    os.link(path, target)
                except OSError:
                    already_linked = None # another volume or no link support: copy as before
                else:
                    already_linked = True
            if already_linked:
                digest = hashes.sha(path, rel, stat)
                verified = verify(path, stat)
                # The source stat just used for the post-hash mutation check
                # already supplies the file identity. Only the target needs a
                # new stat; samefile would query the source a second time.
                if not os.path.samestat(verified, target.stat()):
                    raise RuntimeError('linked input is not the captured file: ' + posix)
                if known_sha is not None and digest != known_sha:
                    raise RuntimeError('inventory hash changed: ' + posix)
                linked.append(stat[0])
                return {'path': posix, 'bytes': stat[0], 'sha256': digest}
        with path.open('rb') as stream:
            result = write(rel, stream)
        verify(path, stat)
        if known_sha is not None and result['sha256'] != known_sha:
            raise RuntimeError('inventory hash changed: ' + posix)
        return result
    # These files share no output path. Bounded parallel I/O avoids spending an
    # entire publish cadence waiting for thousands of individual file operations.
    phase_started = time.monotonic()
    trace_phase('immutable copy', 'start', files=len(immutable),
                bytes=sum(entry[2][0] for entry in immutable))
    # Set up shared output directories once before workers start. Repeated mkdir
    # on Windows also stats each existing directory, multiplying metadata I/O.
    for parent in sorted({(dest / rel).parent for _, rel, _, _ in immutable}):
        prepare_parent(parent)
    immutable_results = []
    last_checkpoint = time.monotonic()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(copy_immutable, immutable):
            immutable_results.append(result)
            if hashes is not None and time.monotonic() - last_checkpoint >= 120:
                # Checkpoint hash work mid-copy: an over-budget kill (taskkill /F,
                # no finally) must not cost the next attempt these byte reads.
                hashes.save(partial=True)
                if seals is not None:
                    seals.save(partial=True)
                last_checkpoint = time.monotonic()
    inputs.extend(immutable_results)
    metrics['immutable_copy_seconds'] = round(time.monotonic()-phase_started, 3)
    metrics['linked_files'] = len(linked)
    metrics['linked_bytes'] = sum(linked)
    metrics['sealed_month_files'] = len(sealed)
    metrics['sealed_month_bytes'] = sum(sealed)
    if seals is not None:
        metrics['sealed_month_bytes_read'] = seals.read_bytes
        seals.save()
    if hashes is not None:
        metrics['evidence_bytes_hashed'] = hashes.read_bytes
        hashes.save()
    trace_phase('immutable copy', 'end', metrics['immutable_copy_seconds'])
    inventory_rows = []
    for entry, result in zip(immutable, immutable_results):
        path, rel, stat, _ = entry
        posix = rel.as_posix()
        inventory_rows.append({'path': posix, 'sha256': result['sha256']})
        inventory_cache[posix] = {'bytes': stat[0], 'mtime_ns': stat[1],
                                  'sha256': result['sha256']}
    final_inventory = inventory_summary(inventory_rows)
    metrics['inventory'] = final_inventory
    metrics['inventory_root'] = final_inventory['root']
    metrics['inventory_files'] = final_inventory['files']
    metrics['inventory_groups'] = final_inventory['groups']
    try:
        save_cache(inventory_file, inventory_cache)
        metrics['inventory_cache_saved'] = True
    except OSError as exc:
        # The cache is an acceleration artefact, never a release prerequisite. A
        # read-only or temporarily full runtime must not discard a verified release.
        metrics['inventory_cache_saved'] = False
        trace_phase('input inventory cache', 'error', error=str(exc))
    metrics['captured_bytes'] = sum(item['bytes'] for item in inputs)
    metrics['captured_files'] = len(inputs)
    inputs.sort(key=lambda r: r['path'])
    return inputs, captured_at, lock_seconds


def resumable_fixed_source(source, dest, oid):
    """Trust a resumed workspace only by artefact, never by its receipt alone:
    the owner marker, a completed fixed-source progress marker for this exact
    OID, and the workspace Git HEAD standing on that OID."""
    try:
        owner = json.loads((dest / '.beops-generated-workspace.json').read_text(encoding='utf-8'))
        progress = json.loads((dest / PROGRESS_NAME).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise RuntimeError('resume refused: workspace markers unreadable: ' + str(exc))
    if (owner.get('schema') != 'beops-generated-workspace/v2'
            or pathlib.Path(owner.get('source', '')) != source
            or pathlib.Path(owner.get('destination', '')) != dest):
        raise RuntimeError('resume refused: workspace owner marker mismatch')
    if progress.get('schema') != 'beops-prepare-progress/v1' or not progress.get('fixed_source_complete'):
        raise RuntimeError('resume refused: fixed source phase incomplete')
    if progress.get('source_oid') != oid:
        raise RuntimeError('resume refused: workspace holds a different source OID')
    if git(dest, 'rev-parse', '--verify', 'HEAD^{commit}') != oid:
        raise RuntimeError('resume refused: workspace HEAD is not the release OID')
    return owner


def prepare(source, destination, oid=None, owner_pid=None, retained=False, resume=False):
    timings = {}
    phase_started = time.monotonic()
    trace_phase('capacity and inventory', 'start')
    source = pathlib.Path(source).resolve()
    dest = pathlib.Path(destination).resolve()
    if dest == source or source in dest.parents:
        raise ValueError('release workspace must be outside the live source')
    if dest.exists():
        if not resume:
            raise FileExistsError('release workspace already exists')
    elif resume:
        raise FileNotFoundError('no interrupted release workspace to resume')
    oid = git(source, 'rev-parse', '--verify', (oid or 'HEAD') + '^{commit}')
    tree = git(source, 'rev-parse', oid + '^{tree}')
    owner = resumable_fixed_source(source, dest, oid) if resume else None
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Refuse before allocating anything large; a publish must never consume the
    # operating system's last free bytes. The last manifest avoids a duplicate
    # deep stat walk over immutable evidence and receipts on normal cadence.
    inventory = {}
    input_bytes, input_bytes_from = estimate_release_input_bytes(source, inventory=inventory)
    paths = archive_paths(source, oid)
    source_bytes = archive_source_bytes(source, oid, paths)
    capacity_options = {'evidence_bytes': inventory['evidence_bytes']} if inventory.get('evidence_bytes') else {}
    capacity, input_bytes, input_bytes_from = release_capacity(
        source, dest.parent, input_bytes, input_bytes_from, source_bytes, **capacity_options)
    timings['capacity_and_inventory_seconds'] = round(time.monotonic()-phase_started, 3)
    timings['capacity_input_bytes_from'] = input_bytes_from
    trace_phase('capacity and inventory', 'end', timings['capacity_and_inventory_seconds'],
                input_bytes=input_bytes, input_bytes_from=input_bytes_from, source_bytes=source_bytes)
    phase_started = time.monotonic()
    trace_phase('fixed source', 'start', resumed=owner is not None)
    if owner is not None:
        # Fixed source already stands verified at this OID; only the ownership
        # moves to the resuming process. Capture below always replays in full.
        owner['owner_pid'] = owner_pid or os.getpid()
        atomic_json(dest/'.beops-generated-workspace.json', owner)
        timings['fixed_source_resumed'] = True
    else:
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
        git(source, 'archive', '--format=tar', '-o', str(archive), oid, '--', *paths, timeout_sec=600)
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                path = (dest / member.name).resolve()
                path.relative_to(dest)
                if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                    raise ValueError('release archive contains a link or device')
            tar.extractall(dest, filter='data')
        archive.unlink()  # our own temporary archive
        # Written only after extraction finished: its presence attests the
        # fixed-source phase, so a killed capture can resume instead of
        # throwing this work away.
        atomic_json(dest/PROGRESS_NAME, {'schema': 'beops-prepare-progress/v1',
            'source_oid': oid, 'source_tree': tree, 'fixed_source_complete': True,
            'at': datetime.now(timezone.utc).isoformat()})
    timings['fixed_source_seconds'] = round(time.monotonic()-phase_started, 3)
    trace_phase('fixed source', 'end', timings['fixed_source_seconds'], resumed=owner is not None)
    inputs, captured_at, lock_seconds = capture_inputs(source, dest, timings)
    configuration = []
    for name in ('research/COLLECTORS.json', 'research/SOURCE_REGISTRY.json', 'research/ORGANS.json'):
        file = dest/name
        if file.is_file():
            raw = file.read_bytes()
            configuration.append({'path':name, 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()})
    manifest = {'schema':'beops-release-inputs/v1','source_oid':oid,'source_tree':tree,
        'state_index':'sealed-readonly-jsonl/v1',
        'observation_prefix':'complete-lf-lines/v1', 'configuration':configuration,
        'captured_at':captured_at, 'writer_lock_seconds':lock_seconds, 'capacity':capacity,
        'inventory':timings.get('inventory'),
        'timings':timings, 'files':inputs}
    atomic_json(dest/'runtime/release-inputs.json',manifest)
    return {'workspace':str(dest),'source_oid':oid,'source_tree':tree,'input_files':len(inputs), 'writer_lock_seconds':lock_seconds}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--destination',required=True);p.add_argument('--oid')
    p.add_argument('--owner-pid',type=int);p.add_argument('--retained',action='store_true');p.add_argument('--resume',action='store_true')
    args=p.parse_args();print(json.dumps(prepare(args.source,args.destination,args.oid,args.owner_pid,args.retained,args.resume)))
