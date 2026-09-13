"""The bounded publisher gate must cover every test and never swallow a failed group."""
import fnmatch
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ResearchRunner(unittest.TestCase):
    def simulate(self, mode):
        script = r'''
const fs = require('node:fs'), vm = require('node:vm');
const calls = [], probes = [], mode = process.argv[3];
let exitCode;
const mockedProcess = {env: {BEOPS_PYTHON: 'fixture-python'}, argv: mode === 'check' ? ['node', 'runner', '--check'] : [], exit(code) { exitCode = code; throw new Error('EXIT'); }};
if (mode === 'support') mockedProcess.env.BEOPS_TEST_PYTHONPATH = 'fixture-support';
const context = {__dirname: require('node:path').dirname(process.argv[2]),
  process: mockedProcess, console: {error() {}}, require(name) {
    if (name === 'node:child_process') return {spawnSync(exe, args, options) {
      if (args.includes('-c')) {
        probes.push(args);
        return {status: mode === 'missing_dependency' && args.join(' ').includes('reportlab') ? 1 : 0};
      }
      calls.push({args, timeout: options.timeout, pythonpath: options.env?.PYTHONPATH});
      if (calls.length === 2 && mode === 'fail') return {status: 1};
      if (calls.length === 2 && mode === 'timeout') return {status: null, error: {message: 'ETIMEDOUT'}};
      if (calls.length === 5 && mode === 'empty') return {status: 5};
      if (mode === 'all-empty') return {status: 5};
      return {status: 0};
    }};
    return require(name);
  }};
try { vm.runInNewContext(fs.readFileSync(process.argv[2], 'utf8'), context); }
catch (error) { if (error.message !== 'EXIT') throw error; }
process.stdout.write(JSON.stringify({exitCode, calls, probes}));
'''
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp) / 'runner-check.js'
            fixture.write_text(script, encoding='utf-8')
            result = subprocess.run(['node', str(fixture), str(ROOT/'tools/test-research.js'), mode],
                                    capture_output=True, text=True, timeout=20, check=True)
            return json.loads(result.stdout)

    def test_every_test_file_is_run_exactly_once_with_bounded_groups(self):
        result = self.simulate('ok')
        self.assertEqual(result['exitCode'], 0)
        patterns = [c['args'][c['args'].index('-p') + 1] for c in result['calls']]
        names = [p.name for p in (ROOT/'research').glob('test_*.py')]
        names += ['test_A.py', 'test_9.py', 'test_é.py', 'test_.py', 'test__new.py']
        for name in names:
            self.assertEqual(sum(fnmatch.fnmatchcase(name, p) for p in patterns), 1, name)
        self.assertIn('test_p*.py', patterns)
        self.assertIn('test_[q-r]*.py', patterns)
        self.assertNotIn('test_[p-r]*.py', patterns)
        self.assertTrue(all(c['timeout'] == 120000 for c in result['calls']))

    def test_failure_refuses_success_and_stops_later_groups(self):
        for mode in ('fail', 'timeout'):
            with self.subTest(mode=mode):
                result = self.simulate(mode)
                self.assertEqual(result['exitCode'], 1)
                self.assertEqual(len(result['calls']), 2)

    def test_an_empty_disjoint_bucket_does_not_fail_the_full_gate(self):
        result = self.simulate('empty')
        self.assertEqual(result['exitCode'], 0)
        self.assertEqual(len(result['calls']), 8)

    def test_incomplete_python_override_is_refused_before_any_discovery(self):
        result = self.simulate('missing_dependency')
        self.assertEqual(result['exitCode'], 1)
        self.assertEqual(result['calls'], [])

    def test_preflight_checks_pdf_support_without_writing_external_bytecode(self):
        result = self.simulate('ok')
        self.assertIn('-B', result['probes'][0])
        self.assertIn('reportlab', result['probes'][0][-1])
        self.assertIn('import TTFont', result['probes'][0][-1])

    def test_test_support_reaches_every_discovery_group(self):
        result = self.simulate('support')
        self.assertTrue(all(c['pythonpath'] == 'fixture-support' for c in result['calls']))

    def test_prerequisites_only_mode_does_not_run_or_claim_the_suite(self):
        result = self.simulate('check')
        self.assertEqual(result['exitCode'], 0)
        self.assertEqual(result['calls'], [])

    def test_zero_discovered_tests_refuses_success(self):
        result = self.simulate('all-empty')
        self.assertEqual(result['exitCode'], 1)
        self.assertEqual(len(result['calls']), 8)


if __name__ == '__main__':
    unittest.main()
