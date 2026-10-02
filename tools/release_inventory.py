"""Incremental input inventory: one stat per file, a Merkle root over captured hashes.

Measured 2026-09-30: under a congested disk the 'input inventory' phase grew from 11 s
to 25+ minutes, because rglob enumeration and a second per-file stat both pay the disk
for ~49,000 immutable inputs. os.scandir returns each entry's stat together with the
enumeration on Windows and Linux, so the walk below touches every directory once and
every file zero extra times.

The Merkle root turns "these inputs" into one comparable value: the root over all
captured (path, sha256) pairs names the release input set, and per-store subroots let a
later cycle prove "this store did not change" from cached hashes instead of re-reading
bytes. The root is computed over the sorted pairs directly, so it does not depend on
the grouping rule. Standard library only.
"""
import argparse
import hashlib
import json
import os
import pathlib
import stat as statmod
import time

CACHE_SCHEMA = 'beops-inventory-cache/v1'
INVENTORY_SCHEMA = 'beops-inventory-merkle/v1'
EMPTY_ROOT_LABEL = b'beops-empty-inventory'

# The stores captured as immutable release inputs, in the same scope and with the same
# filters the capture applies:
# (folder, suffix or None, top_level_only, allowed parent directory names, skip_hidden).
IMMUTABLE_SCOPES = (
    ('research/evidence', None, False, None, False),
    ('data/live/receipts', None, False, None, False),
    ('data/live/raw', None, False, None, False),
    ('runtime/ai-feed/entries', None, False, None, False),
    ('runtime/ai-feed/contexts', None, False, None, False),
    ('runtime/ai-feed/prompts', None, False, None, False),
    ('runtime/resources/receipts', '.json', True, None, True),
    ('runtime/ai-feed/receipts', '.json', True, None, True),
    ('runtime/ai-feed/responses', '.json', True, None, True),
    ('data/live/derived', '.json', False, ('receipts', 'digests'), False),
)

# Subroots are named per store so an unchanged store can be skipped with a proof, not
# with trust. Longest matching prefix wins; anything else groups by its first two
# directory components.
GROUP_PREFIXES = tuple(sorted((scope[0] for scope in IMMUTABLE_SCOPES), key=len, reverse=True)) + (
    'research/observations', 'data/live/rows')


def _entry_is_reparse(entry, observed):
    """A symlink or any Windows reparse point (junction) can escape the source tree.

    ``observed`` is the one stat result taken for this directory entry.  Keeping the
    result here matters on the congested HDD: calling ``entry.stat`` once for the
    safety check and again for the cache key turns the cheap walk back into two
    metadata passes.
    """
    if entry.is_symlink():
        return True
    attributes = getattr(observed, 'st_file_attributes', 0)
    return bool(attributes & getattr(statmod, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))


def unsafe_relative_path(rel):
    """Names that the release contract never admits, even when nested."""
    return any(part.lower().startswith(('.env', 'secrets.', 'kaggle.'))
               for part in pathlib.PurePosixPath(rel).parts)


def scan_scope(directory, suffix=None, top_level_only=False, parent_names=None,
               skip_hidden=False):
    """Yield (path, stat_result) for regular files, one metadata read per entry.

    Results are sorted per directory level; the capture sorts its manifest globally, so
    per-level order only needs to be deterministic. A reparse point anywhere in the
    scope refuses the walk: an input that is not a plain file is not a release input.
    """
    directory = pathlib.Path(directory)
    if not directory.is_dir():
        return
    stack = [directory]
    while stack:
        folder = stack.pop()
        with os.scandir(folder) as entries:
            for entry in sorted(entries, key=lambda e: e.name):
                observed = entry.stat(follow_symlinks=False)
                if _entry_is_reparse(entry, observed):
                    raise ValueError('unsafe release input path: ' + str(entry.path))
                if statmod.S_ISDIR(observed.st_mode):
                    if not top_level_only:
                        stack.append(pathlib.Path(entry.path))
                    continue
                if not statmod.S_ISREG(observed.st_mode):
                    continue
                if skip_hidden and entry.name.startswith('.'):
                    continue
                if suffix is not None and not entry.name.endswith(suffix):
                    continue
                if parent_names is not None and folder.name not in parent_names:
                    continue
                yield pathlib.Path(entry.path), observed


def iter_immutable(source):
    """Walk every immutable input scope of a source tree."""
    source = pathlib.Path(source)
    for folder, suffix, top_only, parents, skip_hidden in IMMUTABLE_SCOPES:
        yield from scan_scope(source / folder, suffix, top_only, parents, skip_hidden)


def merkle_root(pairs):
    """Root over (path, sha256) pairs; sorted here, so caller order cannot matter."""
    leaves = [hashlib.sha256(('leaf\x00%s\x00%s' % pair).encode('utf-8')).digest()
              for pair in sorted(pairs)]
    if not leaves:
        return hashlib.sha256(EMPTY_ROOT_LABEL).hexdigest()
    while len(leaves) > 1:
        paired = [hashlib.sha256(b'node\x00' + leaves[i] + leaves[i + 1]).digest()
                  for i in range(0, len(leaves) - 1, 2)]
        if len(leaves) % 2:
            paired.append(leaves[-1])
        leaves = paired
    return leaves[0].hex()


def group_of(posix):
    for prefix in GROUP_PREFIXES:
        if posix.startswith(prefix + '/'):
            return prefix
    parts = posix.split('/')
    return '/'.join(parts[:2]) if len(parts) > 2 else (parts[0] if len(parts) == 2 else '(root)')


def inventory_summary(rows):
    """One canonical root plus per-store subroots, from manifest rows (path, sha256)."""
    pairs = [(row['path'], row['sha256']) for row in rows]
    groups = {}
    for pair in pairs:
        groups.setdefault(group_of(pair[0]), []).append(pair)
    return {'schema': INVENTORY_SCHEMA,
            'root': merkle_root(pairs),
            'files': len(pairs),
            'groups': {name: {'root': merkle_root(members), 'files': len(members)}
                       for name, members in sorted(groups.items())}}


def load_cache(file):
    """rel -> {bytes, mtime_ns, sha256}; an unreadable cache is an empty cache."""
    rows = {}
    try:
        with open(file, encoding='utf-8') as stream:
            for line in stream:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                rel = row.get('rel')
                if rel and isinstance(row.get('mtime_ns'), int) and row.get('sha256'):
                    rows[rel] = {'bytes': row.get('bytes'), 'mtime_ns': row['mtime_ns'],
                                 'sha256': row['sha256']}
    except OSError:
        pass
    return rows


def save_cache(file, rows):
    """Whole-file publish: temporary file then os.replace, like every receipt here."""
    file = pathlib.Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)
    tmp = file.with_name(file.name + '.tmp')
    try:
        with open(tmp, 'w', encoding='utf-8') as stream:
            stream.write(json.dumps({'schema': CACHE_SCHEMA}, separators=(',', ':')) + '\n')
            for rel in sorted(rows):
                row = rows[rel]
                stream.write(json.dumps({'rel': rel, 'bytes': row['bytes'],
                                         'mtime_ns': row['mtime_ns'], 'sha256': row['sha256']},
                                        separators=(',', ':')) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, file)
    except OSError:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def build_inventory(source, cache_file=None, checkpoint_seconds=120):
    """Build one stat/hash inventory and retain its entries for the capture.

    The returned fourth value is the exact entry list observed during the walk.  The
    publisher consumes it instead of walking the same immutable stores a second time.

    Measured 2026-10-01: a publish cycle killed over budget never reached the one
    save_cache at the end of the publisher, so every retry re-hashed all ~61k inputs
    (~60 min on the congested disk) and died the same death.  The walk therefore
    checkpoints the cache while hashing: a killed attempt still pays forward, and the
    next attempt hashes only what the checkpoint missed.  A checkpoint merges over the
    loaded cache so rows not yet revisited this walk survive; the publisher's final
    save still prunes deleted inputs.
    """
    source = pathlib.Path(source)
    cache_file = pathlib.Path(cache_file or source / 'runtime/inventory-cache.jsonl')
    cache = load_cache(cache_file)
    started = time.monotonic()
    last_checkpoint = started
    rows, fresh, entries, hashed_files, hashed_bytes = [], {}, [], 0, 0
    checkpoints = 0
    for path, stat in iter_immutable(source):
        if path.suffix in ('.lock', '.tmp'):
            continue
        rel = path.relative_to(source).as_posix()
        if unsafe_relative_path(rel):
            raise ValueError('unsafe release input path: ' + rel)
        # In-flight collector claims are coordination markers the capture also skips.
        if path.suffix.lower() == '.claim' and rel.startswith('data/live/receipts/'):
            continue
        known = cache.get(rel)
        if known and known['bytes'] == stat.st_size and known['mtime_ns'] == stat.st_mtime_ns:
            sha = known['sha256']
        else:
            sha = _sha256_file(path)
            hashed_files += 1
            hashed_bytes += stat.st_size
            if checkpoint_seconds and time.monotonic() - last_checkpoint >= checkpoint_seconds:
                try:
                    save_cache(cache_file, {**cache, **fresh})
                    checkpoints += 1
                except OSError:
                    pass  # an unwritable cache slows the next run, never this one
                last_checkpoint = time.monotonic()
        fresh[rel] = {'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns, 'sha256': sha}
        rows.append({'path': rel, 'sha256': sha})
        entries.append((path, pathlib.PurePosixPath(rel),
                        (stat.st_size, stat.st_mtime_ns), sha))
    if hashed_files and checkpoint_seconds:
        # The walk finished with fresh hashes in memory only; persist them now so a
        # later kill anywhere in the publisher cannot discard this hour of reading.
        try:
            save_cache(cache_file, {**cache, **fresh})
            checkpoints += 1
        except OSError:
            pass
    summary = inventory_summary(rows)
    metrics = {'seconds': round(time.monotonic() - started, 3),
               'files': len(rows), 'hashed_files': hashed_files, 'hashed_bytes': hashed_bytes,
               'cache_checkpoints': checkpoints}
    return summary, fresh, metrics, entries


def cached_inventory(source, cache_file=None):
    """Stat-walk immutable stores; re-read bytes only where (size, mtime_ns) moved.

    Returns (summary, cache_rows, metrics).  ``build_inventory`` is the publisher
    entry point when it also needs the observed entries.
    """
    summary, fresh, metrics, _ = build_inventory(source, cache_file)
    return summary, fresh, metrics


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merkle inventory of immutable release inputs')
    parser.add_argument('--source', required=True)
    parser.add_argument('--cache')
    parser.add_argument('--update-cache', action='store_true',
                        help='persist refreshed hashes back to the cache file')
    args = parser.parse_args()
    summary, fresh, metrics = cached_inventory(args.source, args.cache)
    if args.update_cache:
        save_cache(pathlib.Path(args.cache or pathlib.Path(args.source) / 'runtime/inventory-cache.jsonl'), fresh)
    print(json.dumps({'inventory': summary, 'metrics': metrics}, indent=2))
