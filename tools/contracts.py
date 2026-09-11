"""Small shared contracts for durable files, finite values and observation clocks.

No inference is made from an invalid time. Intervals are bucketed by their end;
the original and corrected interval remain in the source row.
"""
from __future__ import annotations

import contextlib
import functools
import hashlib
import json
import math
import os
import pathlib
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone

_held = threading.local()


def organ_pause_reason(register, directory):
    marker = pathlib.Path(directory) / 'PAUSED'
    if marker.exists():
        return marker.read_text(encoding='utf-8', errors='replace')[:200] or 'PAUSED file present'
    if register.get('enabled') is False or register.get('operational_state', 'active') != 'active' or register.get('status') in ('paused', 'disabled', 'retired'):
        return 'organ register is paused or disabled'
    return None


def serialized(path_factory, timeout=1):
    """Serialize one whole job, resolving its root at call time (also in tests)."""
    def decorate(fn):
        @functools.wraps(fn)
        def run(*args, **kwargs):
            with exclusive(path_factory(), timeout=timeout):
                return fn(*args, **kwargs)
        return run
    return decorate


@contextlib.contextmanager
def exclusive(path, timeout=30):
    """OS-owned, crash-released cross-process lock; nested calls in one thread work."""
    path = pathlib.Path(path).resolve()
    key = str(path)
    held = getattr(_held, "paths", {})
    if key in held:
        yield
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    start = time.monotonic()
    try:
        if os.fstat(fd).st_size == 0:
            os.write(fd, b"0")
        while True:
            try:
                os.lseek(fd, 0, os.SEEK_SET)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() - start >= timeout:
                    raise TimeoutError(f"resource busy: {path.name}")
                time.sleep(0.05)
        held[key] = True
        _held.paths = held
        try:
            yield
        finally:
            held.pop(key, None)
    finally:
        os.close(fd)


def atomic_json(path, value):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".beops-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(value, f, ensure_ascii=False, indent=1, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class RecordFormatError(ValueError):
    """A location in immutable input; never include arbitrary source content."""
    def __init__(self, path, line, offset, kind):
        self.path, self.line, self.offset, self.kind = str(path), line, offset, kind
        super().__init__(f"invalid JSONL {pathlib.Path(path).name}:{line} at byte {offset}: {kind}")


def json_object(path):
    """A stored receipt is either an object or a visible error, never silent absence."""
    path = pathlib.Path(path)
    try:
        value = json.loads(path.read_text(encoding='utf-8-sig'),
                           parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
        if not isinstance(value, dict):
            raise ValueError('expected an object')
        return value
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError(f"invalid JSON object {path}: {type(exc).__name__}") from exc


def json_rows(path, stats=None):
    """Strict streaming reader with byte locations and optional completeness counters."""
    path = pathlib.Path(path)
    stats = stats if stats is not None else {}
    stats.update(valid=0, blank=0, corrupt=0, truncated_tail=0)
    if not path.exists():
        return
    with path.open('rb') as f:
        for number, raw in enumerate(f, 1):
            offset = f.tell() - len(raw)
            if not raw.strip() or (number == 1 and raw.strip() == b'\xef\xbb\xbf'):
                stats['blank'] += 1
                continue
            try:
                line = raw.decode('utf-8-sig' if number == 1 else 'utf-8')
                row = json.loads(line, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
                if not isinstance(row, dict):
                    raise ValueError("row is not an object")
            except (UnicodeError, ValueError, TypeError) as exc:
                # An invalid last unterminated line may be an interrupted append;
                # it is never repaired or discarded by a reader.
                kind = 'truncated_tail' if not raw.endswith(b'\n') else 'corrupt'
                stats[kind] += 1
                raise RecordFormatError(path, number, offset, kind) from exc
            stats['valid'] += 1
            yield row


def observation_rows(path):
    """Read immutable rows with explicit, hashed correction overlays; raw bytes stay intact."""
    path = pathlib.Path(path)
    ledger = path.parent.parent.parent / 'corrections.jsonl'
    corrections = {r['original_id']: r for r in json_rows(ledger)} if ledger.exists() else {}
    affected = {r['sid'] for r in corrections.values()}
    for row in json_rows(path):
        original_id = row.get('row_id') or content_id(row) if row.get('sid') in affected else None
        correction = corrections.get(original_id)
        if correction:
            revised = dict(row, **correction['fields'])
            revised['correction'] = {'id': correction['id'], 'original_id': original_id,
                                     'reason': correction['reason'], 'at': correction['at']}
            revised['row_id'] = content_id(revised)
            yield revised
        else:
            yield row


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def utc(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo is not None else None
    except ValueError:
        return None


def interval(value):
    if isinstance(value, dict):
        return utc(value.get("start") or value.get("begin")), utc(value.get("end"))
    if isinstance(value, str) and "/" in value:
        a, b = value.split("/", 1)
        return utc(a), utc(b)
    dt = utc(value)
    return dt, dt


def row_clock(row):
    """(UTC instant at interval end, measured/corrected/arrival/invalid)."""
    if row.get('sourceClockUnresolved'):
        return None, 'invalid'
    if row.get("phenomenonTimeUnknown"):
        return utc(row.get("receivedTime")), "arrival"
    corrected = row.get("phenomenonTimeCorrected")
    value = corrected if corrected is not None else row.get("phenomenonTime")
    _, end = interval(value)
    return end, ("corrected" if corrected is not None else "measured") if end else "invalid"


def belgrade_offset(dt):
    """Contemporary EU rule, explicitly versioned; never inferred from the arrival date."""
    def sunday(month):
        d = datetime(dt.year, month + 1, 1, tzinfo=timezone.utc) - timedelta(days=1)
        return (d - timedelta(days=(d.weekday() + 1) % 7)).replace(hour=1)
    return 2 if sunday(3) <= dt.astimezone(timezone.utc) < sunday(10) else 1


def belgrade_local(local):
    """Resolve an unzoned local label. A DST fold or gap is unknown, never guessed."""
    candidates = []
    for offset in (1, 2):
        candidate = (local - timedelta(hours=offset)).replace(tzinfo=timezone.utc)
        if belgrade_offset(candidate) == offset:
            candidates.append((candidate, offset))
    return candidates[0] if len(candidates) == 1 else (None, None)


def content_id(row):
    payload = {k: v for k, v in row.items() if k not in ("receivedTime", "raw_sha256", "permission_capture", "row_id")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
