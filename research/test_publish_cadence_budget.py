"""Exercise the real PowerShell success cadence without publishing or scheduling."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DUE = Path(os.environ.get('BEOPS_PUBLISH_DUE_SCRIPT', str(ROOT / 'tools/publish_due.ps1')))


@unittest.skipUnless(sys.platform == 'win32', 'Windows PowerShell cadence gate')
class SuccessCadenceBudget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = ROOT / 'runtime/tmp'
        cls.scratch.mkdir(parents=True, exist_ok=True)

    def run_gate(self, now, completed='00:08:00', started='00:00:00', attempt=None):
        def at(value):
            return '2026-09-27T' + value + 'Z'
        with tempfile.TemporaryDirectory(prefix='cadence-test-', dir=self.scratch) as temp:
            root = Path(temp)
            success, failed, status = (root / n for n in ('success.json', 'attempt.json', 'status.json'))
            receipt = {'published': True, 'at': at(completed)}
            if started is not None:
                receipt['cycle_started_at'] = at(started) if len(started) == 8 else started
            success.write_text(json.dumps(receipt), encoding='utf-8')
            if attempt is not None:
                failed.write_text(json.dumps(attempt), encoding='utf-8')
            result = subprocess.run([
                'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-File', str(DUE), '-ReceiptPath', str(success),
                '-AttemptReceiptPath', str(failed), '-StatusPath', str(status),
                '-NowUtc', at(now), '-FailureCooldownMinutes', '30',
            ], capture_output=True, text=True, timeout=20,
               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.assertTrue(status.exists(), result.stdout + result.stderr)
            return result.returncode, json.loads(status.read_text(encoding='utf-8-sig'))

    def test_eight_minute_success_is_due_on_the_next_half_hour_tick(self):
        code, status = self.run_gate('00:30:00')
        self.assertEqual(code, 0, status)
        self.assertEqual(status['cadence_basis'], 'cycle_start_with_completion_rest')
        self.assertTrue(status['next_due_at'].startswith('2026-09-27T00:29:00'))
        self.assertEqual(self.run_gate('00:28:59')[0], 75)
        self.assertEqual(self.run_gate('00:29:00')[0], 0)

    def test_forty_minute_success_cannot_immediately_start_another_release(self):
        for now, expected in [('00:40:00', 75), ('00:44:59', 75), ('00:45:00', 0)]:
            with self.subTest(now=now):
                code, status = self.run_gate(now, completed='00:40:00')
                self.assertEqual(code, expected, status)
                self.assertTrue(status['next_due_at'].startswith('2026-09-27T00:45:00'))

    def test_twenty_six_minute_success_preserves_five_minutes_rest(self):
        self.assertEqual(self.run_gate('00:30:00', completed='00:26:00')[0], 75)
        self.assertEqual(self.run_gate('00:31:00', completed='00:26:00')[0], 0)

    def test_unusable_start_never_shortens_completion_based_fallback(self):
        for start in [None, '', 'invalid', '2026-09-27T00:00:00', '00:09:00', '01:00:00']:
            with self.subTest(start=start):
                code, status = self.run_gate('00:30:00', started=start)
                self.assertEqual(code, 75, status)
                self.assertEqual(status['cadence_basis'], 'completion_fallback')
                self.assertTrue(status['next_due_at'].startswith('2026-09-27T00:37:00'))
                self.assertEqual(self.run_gate('00:37:00', started=start)[0], 0)

    def test_start_with_timezone_offset_obeys_the_same_instant(self):
        code, status = self.run_gate('00:30:00', started='2026-09-27T02:00:00+02:00')
        self.assertEqual(code, 0, status)
        self.assertTrue(status['next_due_at'].startswith('2026-09-27T00:29:00'))

    def test_future_completion_still_fails_closed(self):
        code, status = self.run_gate('00:30:00', completed='00:31:00')
        self.assertEqual(code, 9, status)
        self.assertEqual(status['reason'], 'successful_receipt_from_future')

    def test_failure_cooldown_still_overrides_an_eligible_success(self):
        attempt = {'published': False, 'at': '2026-09-27T00:20:00Z'}
        code, status = self.run_gate('00:30:00', attempt=attempt)
        self.assertEqual(code, 75, status)
        self.assertEqual(status['reason'], 'recent_failed_attempt')
        self.assertEqual(status['failure_cooldown_minutes'], 30)
        self.assertEqual(self.run_gate('00:50:00', attempt=attempt)[0], 0)


if __name__ == '__main__':
    unittest.main()
