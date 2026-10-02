"""2026-10-01: a closed month of rows is sealed once and linked, not re-frozen every cycle.

What must stay true: the release names exactly the bytes and facts the ordinary capture would
(sha256, rows, newest reception, state key), a closed month is the very captured file and is
read-only, an open month is still copied under the write lock, a file with a partial last line
is never sealed, a second release reads no closed month again, the grace keeps the first hours
of a new month open, the switch restores the old capture, and retention can still redact a
sealed month."""
import datetime as dt
import hashlib
import json
import os
import pathlib
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_release as P  # noqa: E402
import apply_retention as R  # noqa: E402

NOW = dt.datetime.now(dt.timezone.utc)
OPEN = NOW.strftime('%Y-%m')
CLOSED = (NOW.replace(day=1) - dt.timedelta(days=40)).strftime('%Y-%m')


def rows(n, month, state=False):
    out = []
    for i in range(n):
        row = {'sid': 'S01', 'parameter': 'pm25', 'result': i,
               'receivedTime': f'{month}-0{1 + i % 9}T10:00:0{i % 10}Z'}
        if state:
            row['state'] = 'observed'
        out.append(json.dumps(row) + '\n')
    return ''.join(out).encode()


class SealedMonths(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = pathlib.Path(self.tmp.name)
        self.source, self.releases = base / 'source', base / 'releases'
        self.closed = self.source / f'data/live/rows/S01/{CLOSED}.jsonl'
        self.open = self.source / f'data/live/rows/S01/{OPEN}.jsonl'
        self.closed.parent.mkdir(parents=True)
        self.closed.write_bytes(rows(40, CLOSED, state=True))
        self.open.write_bytes(rows(3, OPEN))
        (self.source / 'data/live/.write.lock').touch()
        self.releases.mkdir()
        self.n = 0
        env = patch.dict(os.environ, {'BEOPS_RELEASE_LINK_EVIDENCE': '1', 'BEOPS_RELEASE_SEAL_MONTHS': '1'})
        env.start()
        self.addCleanup(env.stop)

    def tearDown(self):
        # Lift the seal so the temporary tree can be removed on Windows.
        for f in self.source.rglob('*.jsonl'):
            f.chmod(stat.S_IREAD | stat.S_IWRITE)
        for f in self.releases.rglob('*'):
            if f.is_file():
                f.chmod(stat.S_IREAD | stat.S_IWRITE)

    def capture(self):
        self.n += 1
        dest = self.releases / f'beops-release-{self.n:032x}'
        dest.mkdir()
        metrics = {}
        inputs, _, _ = P.capture_inputs(self.source, dest, metrics)
        return dest, {r['path']: r for r in inputs}, metrics

    def rel(self, f):
        return f.relative_to(self.source).as_posix()

    def test_closed_month_is_linked_sealed_and_described_like_a_copy(self):
        dest, sealed, m = self.capture()
        closed = self.rel(self.closed)
        self.assertTrue(os.path.samefile(self.closed, dest / closed))
        self.assertFalse(os.stat(dest / closed).st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        self.assertEqual(m['sealed_month_files'], 1)
        self.assertEqual(sealed[closed]['sha256'], hashlib.sha256(self.closed.read_bytes()).hexdigest())
        # The ordinary capture of the same bytes produces the same facts.
        with patch.dict(os.environ, {'BEOPS_RELEASE_SEAL_MONTHS': '0'}):
            copy_dest, copied, m2 = self.capture()
        self.assertEqual(m2['sealed_month_files'], 0)
        self.assertFalse(os.path.samefile(self.closed, copy_dest / closed))
        identity = ('state_index_mtime_ns', 'state_index_file_id', 'state_index_device')
        strip = lambda r: {k: v for k, v in r.items() if k not in identity}
        self.assertEqual(strip(sealed[closed]), strip(copied[closed]))

    def test_open_month_is_still_copied(self):
        dest, got, _ = self.capture()
        self.assertFalse(os.path.samefile(self.open, dest / self.rel(self.open)))
        self.assertEqual(got[self.rel(self.open)]['nonblank_lines'], 3)

    def test_second_release_reads_no_closed_month_again(self):
        self.capture()
        _, got, m = self.capture()
        self.assertEqual(m['sealed_month_bytes_read'], 0)
        self.assertEqual(got[self.rel(self.closed)]['nonblank_lines'], 40)

    def test_partial_last_line_is_never_sealed(self):
        self.closed.write_bytes(rows(5, CLOSED) + b'{"sid":"S01","res')
        dest, got, m = self.capture()
        self.assertEqual(m['sealed_month_files'], 0)
        entry = got[self.rel(self.closed)]
        self.assertEqual(entry['excluded_tail_bytes'], len(b'{"sid":"S01","res'))
        self.assertFalse(os.path.samefile(self.closed, dest / self.rel(self.closed)))

    def test_grace_keeps_the_first_hours_of_a_month_open(self):
        name = 'data/live/rows/S01/2026-09.jsonl'
        self.assertFalse(P.sealed_month(name, dt.datetime(2026, 10, 1, 3, tzinfo=dt.timezone.utc)))
        self.assertTrue(P.sealed_month(name, dt.datetime(2026, 10, 1, 7, tzinfo=dt.timezone.utc)))
        self.assertFalse(P.sealed_month(name, dt.datetime(2026, 9, 30, 23, tzinfo=dt.timezone.utc)))
        self.assertTrue(P.sealed_month('data/live/rows/S01/2026-12.jsonl', dt.datetime(2027, 1, 2, tzinfo=dt.timezone.utc)))
        self.assertFalse(P.sealed_month('data/live/derived/mind/2026-08.jsonl', NOW))
        self.assertFalse(P.sealed_month('data/live/rows/S01/_seen.json', NOW))

    def test_retention_can_redact_a_sealed_month(self):
        self.capture()  # seals the closed month read-only
        old = (NOW - dt.timedelta(days=400)).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.closed.chmod(stat.S_IREAD | stat.S_IWRITE)
        self.closed.write_text(json.dumps({'sid': 'S01', 'parameter': 'headline', 'result': 'x',
                                           'receivedTime': old}) + '\n', encoding='utf-8')
        self.closed.chmod(stat.S_IREAD)
        n = R.redact_file(self.closed, NOW - dt.timedelta(days=90), 'R1', NOW)
        self.assertEqual(n, 1)
        self.assertIsNone(json.loads(self.closed.read_text(encoding='utf-8'))['result'])


if __name__ == '__main__':
    unittest.main()
