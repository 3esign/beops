"""Remaining recovery contracts: source shape, visible corruption and news retries."""
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import contracts as C
import collect_daemon as D
import organ_news as N
import news_state
import watchman as W
import guard as G
import build_site as S
import prepare_release as P
import concurrent.futures
from test_collect_daemon import RHMZ_HTML, GAUGE_HTML

NOW = datetime(2026, 9, 11, 13, tzinfo=timezone.utc)


class SourceShape(unittest.TestCase):
    def test_timestamp_without_known_stations_is_not_a_valid_empty_measurement(self):
        for parser, body in [(D.parse_rhmz_auto, b'11.09.2026. termin: 13:00 <table></table>'),
                             (D.parse_rhmz_gauges, b'11.09.2026. vreme: 8:00 (06:00 UTC)<table></table>')]:
            with self.subTest(parser=parser.__name__), self.assertRaisesRegex(ValueError, 'no recognized'):
                parser(body, NOW, {'sid': 'S1'})

    def test_malformed_known_station_does_not_hide_among_valid_rows(self):
        malformed = RHMZ_HTML.replace(b'<td>Beograd</td><td>33.5</td>', b'<td>Beograd</td>')
        with self.assertRaisesRegex(ValueError, 'column layout'):
            D.parse_rhmz_auto(malformed, NOW, {'sid': 'S1'})
        self.assertEqual(len(D.parse_rhmz_auto(RHMZ_HTML, NOW, {'sid': 'S1'})), 10)
        self.assertEqual(len(D.parse_rhmz_gauges(GAUGE_HTML, NOW, {'sid': 'S1'})), 8)

    def test_receipt_distinguishes_valid_empty_feed_from_changed_page(self):
        cases = [('rss', b'<rss><channel></channel></rss>', 'captured', 'empty'),
                 ('rhmz_auto', b'<html>maintenance</html>', 'unparsed', 'parse_failed'),
                 ('rhmz_auto', b'11.09.2026. termin: 13:00 <table></table>', 'unparsed', 'parse_failed')]
        for parser, body, state, outcome in cases:
            with self.subTest(parser=parser, body=body), tempfile.TemporaryDirectory() as td:
                src = dict(sid='S1', name='fixture', url='https://example.invalid/x', parser=parser,
                           timeout_seconds=1, max_bytes=1000, store_raw=False)
                res = dict(transport={}, status=200, body=body, error=None, headers={})
                with patch.object(D, 'LIVE', pathlib.Path(td)), patch.object(D, 'may_collect', return_value=(True, 'fixture')):
                    rec = D.collect_one(src, NOW, {}, fetcher=lambda *a: res)
                self.assertEqual(rec['state'], state)
                stored = C.json_object(pathlib.Path(td) / 'receipts/S1' / rec['file'])
                self.assertEqual(stored.get('payload_outcome'), outcome)
                shape = C.json_object(ROOT/'research/RECORD_SHAPE.json')
                declaration = next(t for t in shape['trees'] if t['path'] == 'data/live/receipts')
                self.assertIn(stored['state'], declaration['state_vocabulary'])

    def test_storage_failure_is_not_reported_as_a_parser_failure(self):
        with tempfile.TemporaryDirectory() as td:
            live = pathlib.Path(td)
            src = dict(sid='S1', name='fixture', url='https://example.invalid/x', parser='rss',
                       timeout_seconds=1, max_bytes=1000, store_raw=False)
            response = dict(transport={}, status=200, body=b'<rss><channel/></rss>', error=None, headers={})
            with patch.object(D, 'LIVE', live), patch.object(D, 'may_collect', return_value=(True, 'fixture')), patch.object(D, 'append_rows', side_effect=TimeoutError('resource busy')):
                result = D.collect_one(src, NOW, {}, fetcher=lambda *a: response)
            receipt = C.json_object(live/'receipts/S1'/result['file'])
            self.assertEqual(receipt['state'], 'failed')
            self.assertEqual(receipt['payload_outcome'], 'storage_failed')
            self.assertEqual(receipt['rows_parsed'], 0)


class Corruption(unittest.TestCase):
    def test_middle_corruption_and_interrupted_tail_have_locations_and_counters(self):
        for last, kind in [(b'{broken}\n', 'corrupt'), (b'{"a":', 'truncated_tail')]:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                path = pathlib.Path(td) / 'rows.jsonl'
                original = b'{"x":1}\n\n' + last
                path.write_bytes(original)
                stats = {}
                with self.assertRaises(C.RecordFormatError) as caught:
                    list(C.json_rows(path, stats))
                self.assertEqual(caught.exception.kind, kind)
                self.assertEqual(caught.exception.line, 3)
                self.assertEqual(caught.exception.offset, 9)
                self.assertEqual(stats['valid'], 1)
                self.assertEqual(stats['blank'], 1)
                self.assertEqual(stats[kind], 1)
                self.assertEqual(path.read_bytes(), original)

    def test_corrupt_stored_objects_cannot_silently_become_absence(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / 'receipt.json'
            for body in ('{broken}', '[]', '{"value":NaN}'):
                path.write_text(body)
                with self.assertRaisesRegex(ValueError, 'invalid JSON object'):
                    C.json_object(path)
            path.write_text('{broken}')
            with self.assertRaises(ValueError):
                S.read_json(path, {})

    def test_monitor_refuses_healthy_state_when_middle_row_is_corrupt(self):
        with tempfile.TemporaryDirectory() as td:
            live = pathlib.Path(td)
            path = live / 'rows/S1/2026-09.jsonl'
            path.parent.mkdir(parents=True)
            path.write_text('{"receivedTime":"2026-09-11T12:00:00Z"}\nBAD\n{"receivedTime":"2026-09-11T13:00:00Z"}\n')
            with patch.object(W, 'LIVE', live):
                when, reason = W.newest_row('S1')
            self.assertIsNone(when)
            self.assertIn('corrupt', reason)


class NewsCompletion(unittest.TestCase):
    def test_reconcile_drops_phantom_completion_and_recovers_interrupted_cache_write(self):
        with tempfile.TemporaryDirectory() as td:
            directory = pathlib.Path(td)
            records = [{'state':'estimated', 'input_key':'missing', 'category':None, 'belgrade':None},
                       {'state':'estimated', 'input_key':'valid', 'category':'radovi', 'belgrade':True}]
            source = directory / '2026-09.jsonl'
            raw = ''.join(json.dumps(r) + '\n' for r in records).encode()
            source.write_bytes(raw)
            result = news_state.reconcile(directory, N.CATEGORIES, {'missing', 'phantom'})
            self.assertEqual(result['unsupported_keys_removed'], ['missing', 'phantom'])
            self.assertEqual(result['supported_keys_recovered'], ['valid'])
            self.assertEqual(json.loads((directory / '_done.json').read_text()), ['valid'])
            self.assertEqual(source.read_bytes(), raw)

    def test_partial_batches_retry_only_missing_items_with_backoff_and_three_attempt_bound(self):
        with tempfile.TemporaryDirectory() as td:
            live = pathlib.Path(td)
            organs = live / 'organs.json'
            organs.write_text(json.dumps({'organs':[{'id':'news-sorter', 'models_preferred':['fixture:local']}]}))
            rows = [dict(sid='S1', result='Naslov ' + k, dedupe_key=k) for k in ['a', 'b']]
            answer = {'items':[{'i':0, 'headline':'Naslov a', 'category':'radovi', 'belgrade':True, 'zones':[]}]}
            with patch.object(N, 'LIVE', live), patch.object(N, 'ORGANS', organs), patch.object(N, 'headlines', return_value=rows):
                tags = lambda: ['fixture:local']
                rec = N.run(NOW, chat=lambda *a: answer, tags=tags)
                self.assertEqual(N.done_keys(), {'a'})
                self.assertEqual(rec['calls'], 1)
                early = N.run(NOW + timedelta(minutes=1), chat=lambda *a: self.fail('backoff ignored'), tags=tags)
                self.assertEqual(early['calls'], 0)
                prompts = []
                for minutes in (6, 17):
                    N.run(NOW + timedelta(minutes=minutes), chat=lambda m,p: (prompts.append(p) or {'items':[]}), tags=tags)
                self.assertTrue(all('Naslov a' not in p and 'Naslov b' in p for p in prompts))
                exhausted = N.run(NOW + timedelta(minutes=50), chat=lambda *a: self.fail('retry bound ignored'), tags=tags)
                self.assertEqual(exhausted['calls'], 0)
                self.assertEqual(json.loads((live / 'derived/news/attempts.json').read_text()), {'a':1, 'b':3})

    def test_malformed_model_envelopes_remain_incomplete(self):
        for answer in (None, [], {'items':None}, {'items':'bad'}, {'items':[{'i':0, 'category':'radovi'}]}):
            with self.subTest(answer=answer):
                row = N.derive([dict(sid='S1', result='Naslov', dedupe_key='a')], answer, 'fixture', 'sha', NOW)[0]
                self.assertEqual(row['state'], 'incomplete')


class SchedulerObservation(unittest.TestCase):
    def test_result_running_disabled_and_unreadable_remain_distinct(self):
        fixture = {'status':3, 'enabled':True, 'last_result':0, 'last_run':NOW.isoformat()}
        with patch.object(G, 'now', return_value=NOW):
            for changes, expected in [({}, G.OK), ({'last_result':1}, G.WARN),
                                      ({'enabled':False}, G.WARN), ({'status':4}, G.OK),
                                      ({'last_result':267011}, G.UNKNOWN)]:
                with self.subTest(changes=changes), patch.object(G, 'sh', return_value=json.dumps({**fixture, **changes})):
                    observed = G.task_state('Beops_Collect')
                    self.assertEqual(observed['state'], expected)
            with patch.object(G, 'sh', return_value='ERROR Access denied'):
                self.assertEqual(G.task_state('Beops_Collect')['state'], G.UNKNOWN)

    def test_disabled_task_is_not_resumed_and_failed_start_is_not_success(self):
        with patch.object(G, 'sh', side_effect=AssertionError('must not enable a disabled task')):
            self.assertIn('explicit operator resume', G.repair('Beops_Collect', 'disabled'))
        with patch.object(G, 'sh', return_value='ERROR exit 1'), patch.object(G, 'task_state', side_effect=AssertionError('failed run')):
            self.assertIn('start failed', G.repair('Beops_Collect', 'not running'))


class ReleaseCapture(unittest.TestCase):
    def test_writing_copies_releases_live_lock_and_preserves_one_mutable_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            source, dest = pathlib.Path(td)/'source', pathlib.Path(td)/'dest'
            a, b = source/'data/live/rows/S1/a.jsonl', source/'data/live/derived/cache.json'
            a.parent.mkdir(parents=True); b.parent.mkdir(parents=True); dest.mkdir()
            a.write_bytes(b'{"value":1}\n'); b.write_bytes(b'{"version":1}')
            real_open = pathlib.Path.open
            checked = []
            def writer(path, *args, **kwargs):
                if path.is_relative_to(dest) and 'w' in str(args[0] if args else kwargs.get('mode', 'r')):
                    def live_writer():
                        with C.exclusive(source/'data/live/.write.lock', timeout=.05):
                            return True
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        checked.append(pool.submit(live_writer).result())
                    b.write_bytes(b'{"version":2}')
                return real_open(path, *args, **kwargs)
            with patch.object(pathlib.Path, 'open', writer):
                manifest, _, held = P.capture_inputs(source, dest)
            self.assertTrue(checked and all(checked))
            self.assertEqual((dest/'data/live/derived/cache.json').read_bytes(), b'{"version":1}')
            self.assertEqual(b.read_bytes(), b'{"version":2}')
            self.assertEqual(len(manifest), 2)

    def test_changed_immutable_input_refuses_release_instead_of_copying_new_version(self):
        with tempfile.TemporaryDirectory() as td:
            source, dest = pathlib.Path(td)/'source', pathlib.Path(td)/'dest'
            raw = source/'research/evidence/input.json'; raw.parent.mkdir(parents=True)
            mutable = source/'data/live/rows/S1/a.jsonl'; mutable.parent.mkdir(parents=True)
            raw.write_bytes(b'old'); mutable.write_bytes(b'{}\n'); dest.mkdir()
            real_open = pathlib.Path.open
            def writer(path, *args, **kwargs):
                if path.is_relative_to(dest) and 'w' in str(args[0] if args else kwargs.get('mode', 'r')):
                    raw.write_bytes(b'changed after capture')
                return real_open(path, *args, **kwargs)
            with patch.object(pathlib.Path, 'open', writer), self.assertRaisesRegex(RuntimeError, 'changed after capture'):
                P.capture_inputs(source, dest)


if __name__ == '__main__':
    unittest.main()
