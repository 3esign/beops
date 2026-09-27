"""Disk-backed history preserves bytes while releasing completed source buckets."""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
import weakref
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import build_history as bh

NOW = datetime(2026, 9, 27, 12, tzinfo=timezone.utc)
TEMP_ROOT = pathlib.Path(os.environ.get('BEOPS_TEST_TEMP_ROOT', ROOT / 'runtime' / 'test-history'))


def row(sid='S1', **changes):
    value = {'sid': sid, 'datastream': 'station|temperature',
             'station_name': '\u010cukarica', 'station_id': 'station',
             'parameter': 'temperature', 'unit': 'Cel', 'result': 1.234567,
             'phenomenonTime': '2026-09-27T10:00:00Z',
             'phenomenonTimeUnknown': False, 'receivedTime': '2026-09-27T10:05:00Z'}
    value.update(changes)
    return value


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


class TrackedSeries(dict):
    pass


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW


class HistorySpoolCase(unittest.TestCase):
    def setUp(self):
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.rows = self.root / 'rows'
        self.rows.mkdir()
        self.spools = self.root / 'spools'
        self.spools.mkdir()
        self.config = patch.object(bh, 'load_config', return_value={})
        self.config.start()
        self.addCleanup(self.config.stop)

    def store(self, rows_by_sid, filename='a.jsonl'):
        for sid, rows in rows_by_sid.items():
            target = self.rows / sid / filename
            target.parent.mkdir(exist_ok=True)
            target.write_text('\n'.join(json.dumps(value, ensure_ascii=False) for value in rows),
                              encoding='utf-8')

    def fixture(self):
        self.store({
            'S1': [row(), row(dedupe_key='tie', result=2),
                   row(dedupe_key='invalidated', result=90),
                   row(result=None, phenomenonTime=None, phenomenonTimeUnknown=True),
                   row(phenomenonTime='2026-09-10T10:00:00Z'),
                   row(phenomenonTime='2026-08-15T10:00:00Z')],
            'S10': [row('S10', result=-0.0)],
            'S_': [row('S_', datastream='direction', parameter='wind_direction', unit='deg', result=359),
                   row('S_', datastream='direction', parameter='wind_direction', unit='deg', result=1,
                       phenomenonTime='2026-09-27T10:01:00Z')],
            'S\u00e9': [row('S\u00e9', datastream='news', parameter='headline', unit=None,
                          result=None, result_text='\u017divi grad')],
        })
        self.store({'S1': [row(dedupe_key='tie', result=7),
                           row(dedupe_key='invalidated', result=99, phenomenonTime='unknown',
                               receivedTime='2026-09-27T10:06:00Z')]}, filename='b.jsonl')

    def test_full_and_windows_are_byte_identical_including_metadata_order(self):
        self.fixture()
        expected = bh.fold(NOW, self.rows)
        with bh.spooled_fold(NOW, self.rows, self.spools) as actual:
            for value in (expected, actual):
                value['input_generation'] = {'id': 'fixture', 'captured_at': bh.iso(NOW)}
                value['as_of'] = bh.iso(NOW)
                value['built'] = bh.iso(NOW + timedelta(hours=1))
            target = io.StringIO()
            summary = bh.write_full(actual, target)
            self.assertEqual(target.getvalue().encode('utf-8'), encode(expected))
            self.assertEqual(summary['series_count'], len(expected['series']))
            for days, clock in [(7, NOW), (14, NOW), (30, NOW), (7, NOW + timedelta(days=200))]:
                with self.subTest(days=days, clock=clock):
                    target = io.StringIO()
                    bh.write_window(actual, days, clock, target)
                    self.assertEqual(target.getvalue().encode('utf-8'), encode(bh.narrow(expected, days, clock)))
            self.assertEqual([item['sid'] for item in actual['series']],
                             [item['sid'] for item in expected['series']])
        self.assertEqual(list(self.spools.iterdir()), [])

    @unittest.skipUnless(os.environ.get('BEOPS_HISTORY_REFERENCE'), 'optional pre-change byte comparison')
    def test_matches_prechange_implementation(self):
        self.fixture()
        spec = importlib.util.spec_from_file_location('history_spool_reference', os.environ['BEOPS_HISTORY_REFERENCE'])
        reference = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reference)
        with patch.object(reference, 'load_config', return_value={}):
            expected = reference.fold(NOW, self.rows)
        with bh.spooled_fold(NOW, self.rows, self.spools) as actual:
            target = io.StringIO()
            bh.write_full(actual, target)
            self.assertEqual(target.getvalue().encode('utf-8'), encode(expected))

    def test_empty_input_keeps_empty_metadata_and_windows(self):
        expected = bh.fold(NOW, self.rows)
        with bh.spooled_fold(NOW, self.rows, self.spools) as actual:
            target = io.StringIO()
            bh.write_full(actual, target)
            self.assertEqual(target.getvalue().encode('utf-8'), encode(expected))
            target = io.StringIO()
            self.assertEqual(bh.write_window(actual, 7, NOW, target),
                             {'series_count': 0, 'hours_of_history': 0})
            self.assertEqual(target.getvalue().encode('utf-8'), encode(bh.narrow(expected, 7, NOW)))

    def test_finished_source_objects_are_gone_before_reading_next_source(self):
        self.store({sid: [row(sid, datastream=str(i)) for i in range(12)]
                    for sid in ['S1', 'S2', 'S3', 'S4']})
        references, boundaries = [], []
        fold_source, reader = bh._iter_fold_source_series, bh.observation_rows

        def tracked(series):
            for key, value in fold_source(series):
                tracked_value = TrackedSeries(value)
                references.append(weakref.ref(tracked_value))
                yield key, tracked_value
                del tracked_value, value

        def read(path):
            self.assertTrue(all(reference() is None for reference in references),
                            'a completed source remained resident')
            boundaries.append(len(references))
            yield from reader(path)

        with patch.object(bh, '_iter_fold_source_series', side_effect=tracked), \
             patch.object(bh, 'observation_rows', side_effect=read), \
             bh.spooled_fold(NOW, self.rows, self.spools) as data:
            self.assertEqual(len(data['series']), 48)
            self.assertEqual(boundaries, [0, 12, 24, 36])
            self.assertTrue(all(reference() is None for reference in references))

    def test_full_writer_releases_each_decoded_series_before_loading_next(self):
        self.fixture()
        loads = json.loads
        references = []

        def tracked(payload):
            self.assertTrue(all(reference() is None for reference in references))
            value = TrackedSeries(loads(payload))
            references.append(weakref.ref(value))
            return value

        with bh.spooled_fold(NOW, self.rows, self.spools) as data:
            with patch.object(bh.json, 'loads', side_effect=tracked):
                bh.write_full(data, io.StringIO())
            self.assertEqual(len(references), len(data['series']))
            self.assertTrue(all(reference() is None for reference in references))

    def test_bad_input_and_consumer_failure_remove_only_owned_spool(self):
        sentinel = self.spools / 'unrelated.txt'
        sentinel.write_text('preserve', encoding='utf-8')
        source = self.rows / 'S1'
        source.mkdir()
        (source / 'a.jsonl').write_text('{"bad":', encoding='utf-8')
        with self.assertRaises(ValueError), bh.spooled_fold(NOW, self.rows, self.spools):
            self.fail('invalid rows reached the consumer')
        self.assertEqual(list(self.spools.iterdir()), [sentinel])
        self.store({'S1': [row()]})
        with self.assertRaisesRegex(RuntimeError, 'consumer'), \
             bh.spooled_fold(NOW, self.rows, self.spools):
            raise RuntimeError('consumer')
        self.assertEqual(list(self.spools.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'preserve')

    def test_windows_release_decoded_series_between_both_passes(self):
        self.fixture()
        loads = json.loads
        references = []

        def tracked(payload):
            self.assertTrue(all(reference() is None for reference in references),
                            'previous decoded series is still resident')
            value = TrackedSeries(loads(payload))
            references.append(weakref.ref(value))
            return value

        with bh.spooled_fold(NOW, self.rows, self.spools) as data:
            for clock in [NOW, NOW + timedelta(days=200)]:
                with self.subTest(clock=clock), patch.object(bh.json, 'loads', side_effect=tracked):
                    bh.write_window(data, 7, clock, io.StringIO())
                self.assertTrue(all(reference() is None for reference in references))

    def test_corrupt_spool_fails_visibly_and_cleans_up(self):
        self.fixture()
        with self.assertRaises(json.JSONDecodeError):
            with bh.spooled_fold(NOW, self.rows, self.spools) as data:
                data['series']._db.execute('PRAGMA query_only = OFF')
                data['series']._db.execute("UPDATE series SET payload = '{broken'")
                bh.write_full(data, io.StringIO())
        self.assertEqual(list(self.spools.iterdir()), [])

    def test_spool_contexts_are_isolated_and_unreadable_after_close(self):
        self.fixture()
        with bh.spooled_fold(NOW, self.rows, self.spools) as first:
            with bh.spooled_fold(NOW, self.rows, self.spools) as second:
                self.assertEqual(len(list(self.spools.iterdir())), 2)
                self.assertEqual(encode(list(first['series'])), encode(list(second['series'])))
            self.assertEqual(len(list(self.spools.iterdir())), 1)
            self.assertEqual(len(list(first['series'])), len(first['series']))
            with self.assertRaisesRegex(ValueError, 'not readable'):
                list(second['series'])
        self.assertEqual(list(self.spools.iterdir()), [])

    def test_main_uses_spool_and_stages_all_outputs_before_replacement(self):
        self.fixture()
        output = self.root / 'public' / 'history.json'
        output.parent.mkdir()
        paths = [output, *(output.with_name(f'history-{days}d.json') for days in [7, 14, 30])]
        for path in paths:
            path.write_bytes(b'previous')
        generation = {'id': 'fixture', 'captured_at': bh.iso(NOW)}
        expected = bh.fold(NOW, self.rows)
        expected.update(input_generation=generation, as_of=bh.iso(NOW), built=bh.iso(NOW))

        @contextlib.contextmanager
        def view(_):
            yield self.root

        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(bh, 'ROOT', self.root))
            stack.enter_context(patch.object(bh, 'ROWS', self.rows))
            stack.enter_context(patch.object(bh, 'OUT', output))
            stack.enter_context(patch.object(bh, 'datetime', FrozenDateTime))
            stack.enter_context(patch.object(bh, 'window_days', return_value=[7, 14, 30]))
            stack.enter_context(patch('release_observation.input_generation', return_value=generation))
            stack.enter_context(patch('live_view.observation_view', side_effect=view))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            with patch.object(bh, 'write_window', side_effect=OSError('disk full')):
                with self.assertRaisesRegex(OSError, 'disk full'):
                    bh.main()
            self.assertTrue(all(path.read_bytes() == b'previous' for path in paths))
            self.assertEqual(list((self.root / 'runtime').iterdir()), [])
            self.assertEqual(sorted(path.name for path in output.parent.iterdir()), sorted(path.name for path in paths))
            with patch.object(bh, '_fold_source_series', side_effect=AssertionError('materialized path')):
                self.assertEqual(bh.main(), 0)
        self.assertEqual(output.read_bytes(), encode(expected))
        for days in [7, 14, 30]:
            self.assertEqual(output.with_name(f'history-{days}d.json').read_bytes(), encode(bh.narrow(expected, days, NOW)))
        self.assertEqual(list((self.root / 'runtime').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
