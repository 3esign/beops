import json
import pathlib
import tempfile
import unittest
from datetime import timedelta
from unittest.mock import Mock
from urllib.error import HTTPError

from observe_10k import FIRST, LAST, capture, inventory, name, publish

HTML = b'<ul class="parking-count"><li><a href="https://example.org">Test</a><span class="count">0</span></li></ul>'


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = pathlib.Path(self.temp.name)
        self.fetch = Mock(return_value=(HTML, {'status': 200, 'retrieved_at': FIRST.isoformat()}, 'utf-8'))

    def test_no_network_before_or_after_experiment(self):
        self.assertEqual(capture(self.folder, FIRST - timedelta(seconds=1), self.fetch)['state'], 'not_started')
        self.assertEqual(capture(self.folder, LAST + timedelta(minutes=21), self.fetch)['state'], 'closed')
        self.fetch.assert_not_called()

    def test_duplicate_slot_not_refetched(self):
        self.assertEqual(capture(self.folder, FIRST, self.fetch)['state'], 'captured')
        self.assertEqual(capture(self.folder, FIRST + timedelta(minutes=1), self.fetch)['state'], 'already_recorded')
        self.fetch.assert_called_once()
        sample = json.loads(next(self.folder.glob('sample-*')).read_text())
        self.assertIsNone(sample['observed_at'])
        self.assertEqual(sample['summary']['locations'][0]['free_spaces'], 0)

    def test_late_wakeup_is_gap_not_backdated(self):
        self.assertEqual(capture(self.folder, FIRST + timedelta(minutes=25), self.fetch)['state'], 'missed_window')
        self.fetch.assert_not_called()
        self.assertEqual(inventory(self.folder, FIRST + timedelta(minutes=25))['coverage'][0]['state'], 'missing')

    def test_both_access_denials_pause_future_requests(self):
        for code in (403, 429):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as folder:
                fetch = Mock(side_effect=HTTPError('https://example.org', code, 'Stop', {}, None))
                self.assertEqual(capture(folder, FIRST, fetch)['http_status'], code)
                self.assertEqual(capture(folder, FIRST + timedelta(hours=1), fetch)['state'], 'source_paused')
                fetch.assert_called_once()

    def test_failure_recorded_once_and_next_slot_can_continue(self):
        self.fetch.side_effect = [OSError('timeout'), (HTML, {'status': 200}, 'utf-8')]
        self.assertEqual(capture(self.folder, FIRST, self.fetch)['state'], 'failed')
        self.assertEqual(capture(self.folder, FIRST, self.fetch)['state'], 'already_recorded')
        self.assertEqual(capture(self.folder, FIRST + timedelta(hours=1), self.fetch)['state'], 'captured')
        self.assertEqual(self.fetch.call_count, 2)

    def test_interrupted_claim_does_not_retry_http(self):
        publish(self.folder / ('claim-' + name(FIRST) + '.json'), {'slot': FIRST.isoformat()})
        self.assertEqual(capture(self.folder, FIRST, self.fetch)['state'], 'claimed_unfinished')
        self.fetch.assert_not_called()

    def test_process_interruption_leaves_claim_and_no_success(self):
        self.fetch.side_effect = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            capture(self.folder, FIRST, self.fetch)
        self.assertEqual(capture(self.folder, FIRST, self.fetch)['state'], 'claimed_unfinished')
        self.assertEqual(inventory(self.folder, FIRST)['captured'], 0)

    def test_corrupt_receipt_fails_closed_before_network(self):
        (self.folder / 'sample-bad.json').write_text('{broken', encoding='utf-8')
        with self.assertRaises(ValueError):
            capture(self.folder, FIRST, self.fetch)
        self.fetch.assert_not_called()

    def test_publish_never_overwrites(self):
        target = self.folder / 'record.json'
        publish(target, {'old': True})
        with self.assertRaises(FileExistsError):
            publish(target, {'new': True})
        self.assertEqual(json.loads(target.read_text()), {'old': True})
        self.assertEqual(list(self.folder.glob('.obs-*.tmp')), [])

    def test_html_error_not_success(self):
        self.fetch.return_value = (b'<p>maintenance</p>', {'status': 200}, 'utf-8')
        self.assertEqual(capture(self.folder, FIRST, self.fetch)['state'], 'failed')

    def test_status_has_thirteen_slots_and_is_readonly(self):
        result = inventory(self.folder, FIRST - timedelta(hours=1))
        self.assertEqual(len(result['coverage']), 13)
        self.assertTrue(all(x['state'] == 'pending' for x in result['coverage']))
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_naive_clock_rejected(self):
        with self.assertRaises(ValueError):
            capture(self.folder, FIRST.replace(tzinfo=None), self.fetch)


if __name__ == '__main__':
    unittest.main()
