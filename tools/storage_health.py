"""Bounded operational storage report; never scans or deletes the evidence archive."""
import json
import os
import pathlib
import shutil
from datetime import datetime, timezone

GIB = 1024 ** 3
RESERVE_BYTES = 2 * GIB


def nearest_existing(path):
    path = pathlib.Path(path).resolve()
    while not path.exists():
        path = path.parent
    return path


def inspect(root, disk_usage=None):
    disk_usage = disk_usage or shutil.disk_usage
    root = pathlib.Path(root).resolve()
    mirror = pathlib.Path(os.environ.get('BEOPS_PUBLIC_ROOT') or root.parent/'Beops-public').resolve()
    releases = pathlib.Path(os.environ.get('BEOPS_RELEASE_ROOT') or root.parent/'_runtime/beops-releases').resolve()
    checks = []
    for name, target in [('source', root), ('mirror', mirror), ('releases', releases)]:
        try:
            usage = disk_usage(nearest_existing(target))
            checks.append({'name': name, 'path': str(target), 'free_bytes': usage.free,
                           'state': 'WARN' if usage.free < 5 * GIB else 'OK',
                           'why': 'less than 5 GiB free; publication must retain 2 GiB' if usage.free < 5 * GIB else 'capacity available'})
        except OSError as exc:
            checks.append({'name': name, 'path': str(target), 'state': 'UNKNOWN', 'why': type(exc).__name__})
    for name in ('MAINTENANCE', 'PUBLISH_PAUSED'):
        marker = root/'runtime'/name
        if marker.exists():
            checks.append({'name': name, 'path': str(marker), 'state': 'WARN',
                           'why': 'explicit operator pause remains; preserved until deliberately ended'})
    return {'schema': 'beops-storage/v1', 'at': datetime.now(timezone.utc).isoformat(),
            'source': str(root), 'temporary': str(root/'runtime/tmp'), 'reserve_bytes': RESERVE_BYTES,
            'checks': checks, 'state': 'UNKNOWN' if any(c['state']=='UNKNOWN' for c in checks)
            else 'WARN' if any(c['state']=='WARN' for c in checks) else 'OK'}


def require_release_capacity(parent, input_bytes, source_bytes=0, disk_usage=None):
    disk_usage = disk_usage or shutil.disk_usage
    # Mutable spool, captured inputs, export stage and mirror transaction can coexist.
    # Reserve remains free after this conservative working allocation.
    required = 4 * input_bytes + 3 * source_bytes + RESERVE_BYTES
    available = disk_usage(nearest_existing(parent)).free
    if available < required:
        raise RuntimeError(f'release disk space insufficient: {available} free bytes, {required} required including 2 GiB reserve')
    return {'free_bytes': available, 'required_bytes': required, 'reserve_bytes': RESERVE_BYTES}


if __name__ == '__main__':
    print(json.dumps(inspect(pathlib.Path(__file__).resolve().parents[1]), indent=2))
