"""One bounded copy of mutable observation inputs; expensive readers run unlocked."""
import contextlib
import pathlib
import shutil
import tempfile
import time
import zipfile
from contracts import exclusive
from release_observation import frozen_manifest, observation_paths, verify


@contextlib.contextmanager
def observation_view(live, metrics=None):
    live = pathlib.Path(live).resolve()
    metrics = metrics if metrics is not None else {}
    manifest = frozen_manifest(live)
    if manifest is not None:
        started = time.monotonic()
        size = verify(live, manifest)
        metrics.update(bytes=size, lock_seconds=0, copied_bytes=0,
                       verified_seconds=round(time.monotonic()-started, 3), mode='verified_release')
        yield live
        return
    with tempfile.TemporaryDirectory(prefix='beops-view-') as td:
        root = pathlib.Path(td)
        with exclusive(live / '.write.lock', timeout=120):
            started, size = time.monotonic(), 0
            paths = observation_paths(live)
            for path in sorted(set(paths)):
                if not path.exists():
                    continue
                if path.is_symlink() or not path.resolve().is_relative_to(live):
                    raise ValueError('unsafe observation input path')
                size += path.stat().st_size
                if size > 512 * 1024 * 1024:
                    raise ValueError('observation view exceeds 512 MiB; no snapshot produced')
                target = root / path.relative_to(live)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            metrics.update(bytes=size, lock_seconds=round(time.monotonic() - started, 3))
        yield root
