"""Source-boundary history regressions; all temporary files remain in Svemir.

Set BEOPS_HISTORY_MODULE to a candidate or use tools/build_history.py in a repo.
BEOPS_HISTORY_REFERENCE optionally adds an exact JSON-byte comparison with the
previous implementation; ordinary invariant tests do not depend on that copy.
"""
import copy
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

SOURCE_ROOT = pathlib.Path(os.environ.get(
    'BEOPS_SOURCE_ROOT',
    str(pathlib.Path(__file__).resolve().parent.parent)))
sys.path.insert(0, str(SOURCE_ROOT / 'tools'))
DEFAULT_MODULE = pathlib.Path(__file__).with_name('build_history.py')
if not DEFAULT_MODULE.is_file():
    DEFAULT_MODULE = SOURCE_ROOT / 'tools/build_history.py'
MODULE = pathlib.Path(os.environ.get('BEOPS_HISTORY_MODULE', str(DEFAULT_MODULE)))
TEMP_ROOT = pathlib.Path(os.environ.get(
    'BEOPS_TEST_TEMP_ROOT', tempfile.gettempdir()))
NOW = datetime(2026, 9, 27, 12, tzinfo=timezone.utc)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bh = load_module('history_source_candidate', MODULE)


def row(sid, **changes):
    result = {'sid': sid, 'datastream': 'station|temperature',
              'station_name': 'Čukarica', 'station_id': 'one',
              'parameter': 'temperature', 'unit': 'Cel', 'result': 20.0,
              'phenomenonTime': '2026-09-27T10:00:00Z',
              'phenomenonTimeUnknown': False,
              'receivedTime': '2026-09-27T10:05:00Z'}
    result.update(changes)
    return result


class SourceFoldingCase(unittest.TestCase):
    def setUp(self):
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.addCleanup(self.temp.cleanup)
        self.rows = pathlib.Path(self.temp.name) / 'rows'
        self.rows.mkdir()

    def fold(self, rows_by_sid, module=bh, reader=None):
        for sid in rows_by_sid:
            directory = self.rows / sid
            directory.mkdir(exist_ok=True)
            (directory / '2026-09.jsonl').touch()
        if reader is None:
            reader = lambda path: iter(rows_by_sid[path.parent.name])
        config = {sid: {'cadence_seconds': 300} for sid in rows_by_sid}
        with patch.object(module, 'load_config', return_value=config), \
             patch.object(module, 'observation_rows', side_effect=reader):
            return module.fold(now=NOW, rows=self.rows)

    def test_original_global_json_key_order_survives_source_partitioning(self):
        # Escaped Unicode sorts before underscore in the original JSON key,
        # although directory order puts underscore before the accented letter.
        inputs = {sid: [row(sid)] for sid in ['S_', 'Sé', 'S2', 'S10', 'S1']}
        data = self.fold(inputs)
        self.assertEqual([s['sid'] for s in data['series']],
                         ['S1', 'S10', 'S2', 'Sé', 'S_'])
        self.assertEqual(data['history_starts'], '2026-09-27T10')
        self.assertEqual(data['history_ends'], '2026-09-27T10')

    def test_malformed_later_revision_does_not_restore_earlier_value(self):
        inputs = {
            'S1': [row('S1', dedupe_key='revised'),
                   row('S1', dedupe_key='revised', phenomenonTime='unknown',
                       receivedTime='2026-09-27T10:06:00Z', result=99.0)],
            'S2': [row('S2', result=7.0)],
        }
        data = self.fold(inputs)
        self.assertEqual([s['sid'] for s in data['series']], ['S2'])
        self.assertEqual(data['unreadable_measurement_times'], {'S1': 1})
        self.assertEqual(data['series'][0]['buckets']['2026-09-27T10']['mean'], 7.0)

    def test_source_rows_remain_unchanged_and_clocks_stay_separate(self):
        inputs = {
            'S1': [row('S1'), row('S1', phenomenonTime=None,
                                phenomenonTimeUnknown=True, result=None,
                                receivedTime='2026-09-27T11:05:00Z')],
            'S2': [row('S2', parameter='headline', datastream='news',
                       unit=None, result=None, result_text='Događaj')],
        }
        original = copy.deepcopy(inputs)
        data = self.fold(inputs)
        self.assertEqual(inputs, original)
        first = [s for s in data['series'] if s['sid'] == 'S1']
        self.assertEqual([s['time_basis'] for s in first], ['measured', 'received'])
        self.assertEqual(first[1]['buckets']['2026-09-27T11']['missing'], 1)
        self.assertNotIn('mean', data['series'][-1]['buckets']['2026-09-27T10'])

    def test_source_is_bucketed_before_the_next_source_is_read(self):
        inputs = {sid: [row(sid)] for sid in ['S1', 'S2', 'S3']}
        completed = []
        original_fold = bh._fold_source_series

        def finish(series):
            result = original_fold(series)
            self.assertTrue(all('events' not in value for value in series.values()))
            completed.append(next(iter(result.values()))['sid'])
            return result

        def read(path):
            sid = path.parent.name
            self.assertEqual(completed, ['S1', 'S2', 'S3'][:int(sid[1:]) - 1])
            return iter(inputs[sid])

        with patch.object(bh, '_fold_source_series', side_effect=finish):
            self.fold(inputs, reader=read)
        self.assertEqual(completed, ['S1', 'S2', 'S3'])

    @unittest.skipUnless(os.environ.get('BEOPS_HISTORY_REFERENCE'),
                         'optional pre-change implementation comparison')
    def test_exact_json_bytes_match_previous_implementation(self):
        reference = load_module('history_source_reference',
                                pathlib.Path(os.environ['BEOPS_HISTORY_REFERENCE']))
        inputs = {
            'S1': [row('S1', result=1.234567),
                   row('S1', dedupe_key='bad-revision'),
                   row('S1', dedupe_key='bad-revision', phenomenonTime='unknown',
                       receivedTime='2026-09-27T10:06:00Z'),
                   row('S1', result=None, phenomenonTime=None,
                       phenomenonTimeUnknown=True)],
            'S_': [row('S_', datastream='direction', parameter='wind_direction',
                       unit='deg', result=359),
                   row('S_', datastream='direction', parameter='wind_direction',
                       unit='deg', result=1, phenomenonTime='2026-09-27T10:01:00Z')],
            'Sé': [row('Sé', datastream='news', parameter='headline', unit=None,
                       result=None, result_text='Vest')],
        }
        encode = lambda value: json.dumps(value, ensure_ascii=False,
                                          separators=(',', ':')).encode('utf-8')
        self.assertEqual(encode(self.fold(inputs)),
                         encode(self.fold(inputs, module=reference)))


if __name__ == '__main__':
    unittest.main()
