"""A late CDN route gets bounded retries; a wrong or stale release never passes."""
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class RoutePropagation(unittest.TestCase):
    def test_parallel_checks_keep_limit_order_and_every_result(self):
        script = r'''
const assert = require('node:assert/strict');
const {mapBounded} = require(process.argv[2]);
let active = 0, peak = 0;
(async () => {
  const result = await mapBounded(Array.from({length: 17}, (_,i) => i), 6, async i => {
    active++; peak=Math.max(peak, active);
    await new Promise(resolve => setTimeout(resolve, i === 0 ? 30 : 2));
    active--; return i * 2;
  });
  assert.equal(peak, 6); assert.equal(active, 0);
  assert.deepEqual(result, Array.from({length: 17}, (_,i) => i * 2));
})().catch(e => {console.error(e);process.exitCode=1;});
'''
        with tempfile.TemporaryDirectory() as folder:
            runner = pathlib.Path(folder)/'bounded.cjs'
            runner.write_text(script, encoding='utf8')
            subprocess.run(['node', str(runner), str(ROOT/'tools/verify_public_site.js')],
                capture_output=True, text=True, timeout=10, check=True)

    def check_mode(self, mode):
        script = r'''
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
global.fetch = async () => {throw Error('network forbidden in offline regression');};
const {fetchMatchingRoute} = require(process.argv[2]);
const mode = process.argv[3];
let clock = 0, calls = 0;
const bytes = Buffer.from('verified release');
const expected = crypto.createHash('sha256').update(bytes).digest('hex');
(async () => {
  const item = await fetchMatchingRoute('https://example.invalid/watch.json', expected, 25, {
    now: () => clock, pollMs: 10, pause: async ms => {clock += ms;},
    get: async () => {
      calls++;
      const ready = mode === 'current' || (mode === 'late' && calls >= 2);
      return {ok: mode !== 'missing', status: mode === 'missing' ? 404 : 200,
              bytes: ready ? bytes : Buffer.from('older release')};
    }
  });
  assert.ok(clock <= 25);
  console.log(JSON.stringify({calls, clock, attempts:item.verification_attempts,
    matches:item.ok && crypto.createHash('sha256').update(item.bytes).digest('hex') === expected}));
})().catch(e => {console.error(e);process.exitCode=1;});
'''
        with tempfile.TemporaryDirectory() as folder:
            runner = pathlib.Path(folder) / 'retry.cjs'
            runner.write_text(script, encoding='utf8')
            result = subprocess.run(['node', str(runner), str(ROOT/'tools/verify_public_site.js'), mode],
                capture_output=True, text=True, timeout=10, check=True)
        return json.loads(result.stdout)

    def test_late_route_must_reach_the_exact_release_hash(self):
        result = self.check_mode('late')
        self.assertTrue(result['matches'])
        self.assertEqual(result['calls'], 2)
        self.assertEqual([a['match'] for a in result['attempts']], [False, True])

    def test_current_route_is_fetched_once(self):
        self.assertEqual(self.check_mode('current')['calls'], 1)

    def test_wrong_hash_never_passes_at_deadline(self):
        result = self.check_mode('wrong')
        self.assertFalse(result['matches'])
        self.assertEqual(result['clock'], 25)
        self.assertEqual(result['calls'], 3)

    def test_missing_route_stays_a_failure(self):
        result = self.check_mode('missing')
        self.assertFalse(result['matches'])
        self.assertEqual(result['attempts'][-1]['status'], 404)


if __name__ == '__main__':
    unittest.main()
