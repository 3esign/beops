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
        for attempt in range(5):
            try:
                os.replace(tmp, path)
                break
            except OSError:
                if attempt == 4:
                    raise
                time.sleep(0.05)
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


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


# R04: a number alone does not authorize arithmetic. Units are retained, never
# silently converted; an unregistered parameter/unit is explicitly unknown.
PARAMETER_SEMANTICS = 'beops-parameter-semantics/v1'
SCALAR_UNITS = {
    **{name: {'Cel', 'C'} for name in ('temperature', 'dew_point', 'water_temperature')},
    **{name: {'Pa', 'hPa'} for name in ('pressure', 'pressure_qnh', 'pressure_at_sealevel')},
    'humidity': {'%'}, 'wind_speed': {'m/s', 'kt'}, 'discharge': {'m3/s'},
    'water_level': {'cm'}, 'water_level_change': {'cm'},
    **{name: {'ug.m-3'} for name in ('PM10','PM2.5','P0','P1','P2','NO','NO2','NOX',
        'O3','SO2','NH3','Benzen','Ethyl benzene','TNx','Toluene','mp-Xylene','o-Xylene')},
    'CO': {'mg.m-3'},
}


def parameter_semantics(row):
    parameter, unit = row.get('parameter'), row.get('unit')
    kind, seconds = 'unknown', None
    if parameter in {'headline', 'notice', 'planned_outage'}:
        kind = 'text'
    elif parameter == 'wind_direction':
        kind = 'circular_degrees' if unit == 'deg' else 'text' if unit == 'compass' else 'unknown'
    elif parameter == 'free_spaces' and unit == '1':
        kind = 'count'
    elif unit in SCALAR_UNITS.get(parameter, set()):
        kind = 'scalar'
        start, end = interval(row.get('phenomenonTimeCorrected') or row.get('phenomenonTime'))
        if start is not None and end is not None and end > start:
            seconds = (end-start).total_seconds()
            # Use the source's retained aggregation declaration. Neither a
            # source ID nor an interval alone proves an averaging operation.
            if row.get('aggregation') in {'hourly_mean','daily_mean'}:
                kind = 'interval_average'
    return kind, seconds


def direction_summary(sum_cos, sum_sin, count):
    if not count:
        return {'mean': None, 'resultant_length': None, 'direction_state': 'no_valid_directions'}
    length = min(1.0, math.hypot(sum_cos, sum_sin)/count)
    if length < 1e-12:
        return {'mean': None, 'resultant_length': length, 'direction_state': 'undefined_resultant'}
    angle = math.degrees(math.atan2(sum_sin, sum_cos)) % 360.0
    if min(abs(angle), abs(angle-360.0)) < 1e-10:
        angle = 0.0
    return {'mean': angle, 'resultant_length': length, 'direction_state': 'defined'}


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


def observation_point(row):
    """Public disclosure of source labels, estimated labels and reception.

    Original labels stay verbatim. Invalid/unknown measurement clocks do not
    gain a measurement time from reception or an invalid estimate's source.
    """
    def labels(value):
        if isinstance(value, dict):
            return value.get('start') or value.get('begin'), value.get('end')
        if isinstance(value, str) and '/' in value:
            return tuple(value.split('/', 1))
        return None, value
    start, end = labels(row.get('phenomenonTime'))
    _, basis = row_clock(row)
    point = {'t':end, 'tu':basis in ('arrival', 'invalid'),
             'rt':row.get('resultTime'), 'rx':row.get('receivedTime'),
             'v':row.get('result'), 'q':row.get('resultQuality')}
    if start is not None:
        point['t0'] = start
    if basis in ('arrival', 'invalid'):
        point['t'] = None
        if end is not None:
            point['source_label'] = end
        if basis == 'invalid':
            point['clock_unresolved'] = True
    elif basis == 'corrected':
        corrected_start, corrected_end = labels(row['phenomenonTimeCorrected'])
        point['tc'] = corrected_end
        if corrected_start is not None:
            point['tc0'] = corrected_start
        if row.get('resultTimeCorrected') is not None:
            point['rtc'] = row['resultTimeCorrected']
    for original, public in [('sourceClockRule','clock_rule'),
                             ('sourceClockValidUntil','clock_valid_until'),
                             ('sourceClockNote','clock_note')]:
        if row.get(original) is not None:
            point[public] = row[original]
    return point


def select_observation_points(points):
    """Explicit selectors over public points, retaining null and known clocks."""
    def measured(point):
        return None if point.get('tu') or point.get('clock_unresolved') else interval(point.get('tc') if 'tc' in point else point.get('t'))[1]
    minimum = datetime.min.replace(tzinfo=timezone.utc)
    received = [point for point in points if utc(point.get('rx')) is not None]
    timed = [point for point in points if measured(point) is not None]
    return {
        'last_by_measurement': max(timed, key=lambda point:(measured(point),utc(point.get('rx')) or minimum)) if timed else None,
        'last_received': max(received, key=lambda point:(utc(point.get('rx')),measured(point) or minimum)) if received else None,
    }


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


def observation_identity(row):
    """One source-labelled observation, independent of its value/reception revision."""
    if row.get('dedupe_key'):
        return str(row['dedupe_key'])
    start, end = interval(row.get('phenomenonTime'))
    if not row.get('phenomenonTimeUnknown') and end is not None:
        identity = [row.get('sid'),row.get('datastream'),row.get('parameter'),row.get('unit'),
                    start.isoformat() if start else None,end.isoformat()]
        return hashlib.sha256(json.dumps(identity,ensure_ascii=False).encode('utf-8')).hexdigest()
    # An untimed reading is a reception; never invent a shared measurement time.
    return str(row.get('row_id') or content_id(row))+'|received='+str(row.get('receivedTime') or '')
