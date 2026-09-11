"""One bounded copy of mutable observation inputs; expensive readers run unlocked."""
import contextlib
import pathlib
import shutil
import tempfile
import time
import zipfile
from contracts import exclusive


@contextlib.contextmanager
def observation_view(live, metrics=None):
    live = pathlib.Path(live).resolve()
    metrics = metrics if metrics is not None else {}
    with tempfile.TemporaryFile() as spool, tempfile.TemporaryDirectory(prefix='beops-view-') as td:
        with zipfile.ZipFile(spool, 'w', compression=zipfile.ZIP_STORED) as archive:
            with exclusive(live / '.write.lock', timeout=120):
                started, size = time.monotonic(), 0
                paths = list((live / 'rows').glob('*/*.jsonl'))
                paths += list((live / 'derived').glob('*/????-??.jsonl'))
                paths += [live / 'derived/mind/claims.jsonl', live / 'corrections.jsonl']
                for path in sorted(set(paths)):
                    if not path.exists():
                        continue
                    if path.is_symlink() or not path.resolve().is_relative_to(live):
                        raise ValueError('unsafe observation input path')
                    size += path.stat().st_size
                    if size > 512 * 1024 * 1024:
                        raise ValueError('observation view exceeds 512 MiB; no snapshot produced')
                    with path.open('rb') as source, archive.open(path.relative_to(live).as_posix(), 'w') as target:
                        shutil.copyfileobj(source, target, 1024 * 1024)
                metrics.update(bytes=size, lock_seconds=round(time.monotonic() - started, 3))
        spool.seek(0)
        root = pathlib.Path(td)
        with zipfile.ZipFile(spool) as archive:
            for name in archive.namelist():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(name) as source, path.open('wb') as target:
                    shutil.copyfileobj(source, target, 1024 * 1024)
        yield root
