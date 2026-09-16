import json
import pathlib
import sys
import tempfile
import unittest
import io
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import collect_daemon as cd


class Cadence(unittest.TestCase):
    def test_regular_tick_refreshes_local_snapshot_for_ai_without_publication(self):
        # C-076: with no snapshot (or one older than ten minutes) the tick refreshes it.
        with tempfile.TemporaryDirectory() as tmp, patch.object(cd,'ROOT',pathlib.Path(tmp)), patch.object(sys,'argv',['collect_daemon.py','tick']), patch.object(cd,'tick',return_value={'results':[]}), patch.object(cd,'export',return_value=pathlib.Path('snapshot.json')) as refresh, patch.object(sys,'stdout',io.StringIO()):
            self.assertEqual(cd.main(),0)
            refresh.assert_called_once_with()

    def test_snapshot_failure_is_visible_after_receipts_were_recorded(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(cd,'ROOT',pathlib.Path(tmp)), patch.object(sys,'argv',['collect_daemon.py','tick']), patch.object(cd,'tick',return_value={'results':[{'state':'captured'}]}), patch.object(cd,'export',side_effect=OSError('disk full')), patch.object(sys,'stdout',io.StringIO()) as output:
            self.assertEqual(cd.main(),1)
            result=json.loads(output.getvalue())
            self.assertEqual(result['results'][0]['state'],'captured')
            self.assertEqual(result['snapshot_error']['type'],'OSError')

    def test_due_reads_only_newest_receipt_and_respects_last_failed_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            live=pathlib.Path(tmp);folder=live/'receipts/S10';folder.mkdir(parents=True)
            at=datetime(2026,9,14,tzinfo=timezone.utc)
            for i in range(100):
                t=at-timedelta(minutes=i*5)
                (folder/(cd.stamp(t)+'.json')).write_text(json.dumps({'attempted_at':cd.iso(t),'state':'failed'}))
            with patch.object(cd,'LIVE',live), patch.object(cd,'json_object',wraps=cd.json_object) as reads:
                self.assertFalse(cd.is_due({'sid':'S10','cadence_seconds':600},at+timedelta(minutes=5))[0])
                self.assertEqual(reads.call_count,1)
                self.assertTrue(cd.is_due({'sid':'S10','cadence_seconds':600},at+timedelta(minutes=10))[0])
                self.assertEqual(reads.call_count,2)

    def test_corrupt_latest_is_explicit_and_does_not_reopen_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            live=pathlib.Path(tmp);folder=live/'receipts/S10';folder.mkdir(parents=True)
            (folder/'20260914T000000Z.json').write_text('{broken')
            with patch.object(cd,'LIVE',live):
                self.assertEqual(cd.is_due({'sid':'S10','cadence_seconds':600},datetime(2026,9,14,tzinfo=timezone.utc)),(True,'unreadable last receipt time'))
