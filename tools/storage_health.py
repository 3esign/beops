"""Bounded operational storage report; never scans or deletes the evidence archive."""
import json
import os
import pathlib
import shutil
from datetime import datetime, timezone

GIB = 1024 ** 3
RESERVE_BYTES = 2 * GIB
CAPACITY_SCHEMA = 'beops-release-capacity/v1'
CAPACITY_FORMULA = '4*input_bytes+3*source_bytes+reserve_bytes'
CAPACITY_PARTITION_SCHEMA = 'beops-release-capacity/v2'
CAPACITY_PARTITION_FORMULA = '4*(input_bytes-evidence_bytes)+evidence_bytes+3*source_bytes+reserve_bytes'
CAPACITY_EVIDENCE_ORIGIN = 'live_stat_scan:research/evidence'
CAPACITY_MAX_BYTES = (1 << 63) - 1
CAPACITY_MAX_AGE_SECONDS = 90 * 60
CAPACITY_MAX_RECEIPT_BYTES = 16 * 1024


class ReleaseCapacityError(RuntimeError):
    """The measured free space cannot satisfy the release allocation and reserve."""

    def __init__(self, message, capacity=None):
        super().__init__(message)
        self.capacity = capacity


def nearest_existing(path):
    path = pathlib.Path(path).resolve()
    while not path.exists():
        path = path.parent
    return path


def release_required_bytes(input_bytes, source_bytes=0, evidence_bytes=0):
    """Budget a full evidence copy, even when immutable hardlinks are unavailable.

    Only research/evidence is capture-only: it is excluded from both Git source
    extraction and public export. Other inputs retain the four-copy allowance.
    Existing mirror bytes are already charged against measured free space.
    """
    for value in (input_bytes, source_bytes, evidence_bytes):
        if type(value) is not int or not 0 <= value <= CAPACITY_MAX_BYTES:
            raise ValueError('invalid release allocation byte count')
    if evidence_bytes > input_bytes:
        raise ValueError('evidence allocation exceeds total inputs')
    required = 4 * (input_bytes - evidence_bytes) + evidence_bytes + 3 * source_bytes + RESERVE_BYTES
    if required > CAPACITY_MAX_BYTES:
        raise ValueError('release allocation exceeds supported byte count')
    return required


def release_capacity_check(root, releases, disk_usage, now):
    """Reuse a recent allocation measurement; never walk the input archive.

    Input sizes describe this source, independent of the previous workspace's
    parent. Read current free space on the configured release volume, including
    when an operator's previous retained workspace used another parent.
    """
    check = {'name': 'release-capacity', 'path': str(releases), 'state': 'WARN'}
    receipt = root/'runtime/release-capacity.json'
    try:
        with receipt.open('rb') as stream:
            raw = stream.read(CAPACITY_MAX_RECEIPT_BYTES + 1)
    except FileNotFoundError:
        return dict(check, why='release allocation not measured; free-space floor only')
    except OSError as exc:
        return dict(check, state='UNKNOWN', why='release capacity receipt unreadable: '+type(exc).__name__)
    try:
        if len(raw) > CAPACITY_MAX_RECEIPT_BYTES:
            raise ValueError('oversized receipt')
        measured = json.loads(raw)
        if not isinstance(measured, dict) or measured.get('schema') not in (CAPACITY_SCHEMA, CAPACITY_PARTITION_SCHEMA):
            raise ValueError('unexpected schema')
        if pathlib.Path(measured['source']).resolve() != root:
            raise ValueError('source mismatch')
        if not pathlib.Path(measured['release_parent']).is_absolute():
            raise ValueError('relative release parent')
        for name in ('input_bytes', 'source_bytes', 'free_bytes', 'required_bytes', 'reserve_bytes'):
            if type(measured[name]) is not int or measured[name] < 0:
                raise ValueError('invalid byte count')
        partitioned = measured['schema'] == CAPACITY_PARTITION_SCHEMA
        evidence_bytes = measured['evidence_bytes'] if partitioned else 0
        if partitioned and (measured.get('input_bytes_from') != 'live_stat_scan'
                            or measured.get('evidence_bytes_from') != CAPACITY_EVIDENCE_ORIGIN):
            raise ValueError('evidence allocation requires a fresh classified inventory')
        if not partitioned and measured.get('evidence_bytes', 0) != 0:
            raise ValueError('legacy allocation cannot discount evidence')
        formula = CAPACITY_PARTITION_FORMULA if partitioned else CAPACITY_FORMULA
        if (measured['formula'] != formula or measured['reserve_bytes'] != RESERVE_BYTES
                or measured['required_bytes'] != release_required_bytes(
                    measured['input_bytes'], measured['source_bytes'], evidence_bytes)):
            raise ValueError('allocation formula mismatch')
        if (type(measured['admitted']) is not bool
                or measured['admitted'] != (measured['free_bytes'] >= measured['required_bytes'])):
            raise ValueError('admission outcome mismatch')
        at = datetime.fromisoformat(measured['at'])
        if at.tzinfo is None:
            raise ValueError('timestamp has no timezone')
        age = (now - at).total_seconds()
        if age < -60:
            raise ValueError('future measurement')
        check.update(measured_at=measured['at'], measurement_age_seconds=max(0, round(age)),
                     measured_release_parent=measured['release_parent'],
                     measured_admitted=measured['admitted'], required_bytes=measured['required_bytes'],
                     reserve_bytes=RESERVE_BYTES)
    except (ValueError, TypeError, KeyError, OverflowError, OSError) as exc:
        return dict(check, state='UNKNOWN', why='invalid release capacity receipt: '+type(exc).__name__)
    if age > CAPACITY_MAX_AGE_SECONDS:
        return dict(check, why='release allocation measurement older than 90 minutes; readiness unknown')
    try:
        available = disk_usage(nearest_existing(releases)).free
    except OSError as exc:
        return dict(check, state='UNKNOWN', why='release volume unreadable: '+type(exc).__name__)
    fits = available >= measured['required_bytes']
    return dict(check, state='OK' if fits else 'WARN', free_bytes=available,
                why=('current free space fits' if fits else 'current free space below')
                + ' the recent measured release allocation including 2 GiB reserve')


def inspect(root, disk_usage=None, now=None):
    disk_usage = disk_usage or shutil.disk_usage
    now = now or datetime.now(timezone.utc)
    root = pathlib.Path(root).resolve()
    mirror = pathlib.Path(os.environ.get('BEOPS_PUBLIC_ROOT') or root.parent/'Beops-public').resolve()
    releases = pathlib.Path(os.environ.get('BEOPS_RELEASE_ROOT') or root.parent/'_runtime/beops-releases').resolve()
    checks = []
    for name, target in [('source', root), ('mirror', mirror), ('releases', releases)]:
        try:
            usage = disk_usage(nearest_existing(target))
            checks.append({'name': name, 'path': str(target), 'free_bytes': usage.free,
                           'state': 'WARN' if usage.free < 5 * GIB else 'OK',
                           'why': 'less than 5 GiB free; publication must retain 2 GiB' if usage.free < 5 * GIB else 'basic free-space floor available'})
        except OSError as exc:
            checks.append({'name': name, 'path': str(target), 'state': 'UNKNOWN', 'why': type(exc).__name__})
    checks.append(release_capacity_check(root, releases, disk_usage, now))
    for name in ('MAINTENANCE', 'PUBLISH_PAUSED'):
        marker = root/'runtime'/name
        if marker.exists():
            checks.append({'name': name, 'path': str(marker), 'state': 'WARN',
                           'why': 'explicit operator pause remains; preserved until deliberately ended'})
    return {'schema': 'beops-storage/v1', 'at': datetime.now(timezone.utc).isoformat(),
            'source': str(root), 'temporary': str(root/'runtime/tmp'), 'reserve_bytes': RESERVE_BYTES,
            'checks': checks, 'state': 'UNKNOWN' if any(c['state']=='UNKNOWN' for c in checks)
            else 'WARN' if any(c['state']=='WARN' for c in checks) else 'OK'}


def require_release_capacity(parent, input_bytes, source_bytes=0, disk_usage=None, *, evidence_bytes=0):
    disk_usage = disk_usage or shutil.disk_usage
    required = release_required_bytes(input_bytes, source_bytes, evidence_bytes)
    available = disk_usage(nearest_existing(parent)).free
    capacity = {'free_bytes': available, 'required_bytes': required, 'reserve_bytes': RESERVE_BYTES}
    if available < required:
        raise ReleaseCapacityError(f'release disk space insufficient: {available} free bytes, {required} required including 2 GiB reserve', capacity)
    return capacity


if __name__ == '__main__':
    print(json.dumps(inspect(pathlib.Path(__file__).resolve().parents[1]), indent=2))
