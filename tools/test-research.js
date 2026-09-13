'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const runtimePath = path.resolve(__dirname, '..', 'runtime', 'test-python.json');
const runtime = fs.existsSync(runtimePath) ? JSON.parse(fs.readFileSync(runtimePath, 'utf8').replace(/^\uFEFF/, '')) : {};
const explicitPython = process.env.BEOPS_PYTHON;
const testEnv = {...process.env};
const support = process.env.BEOPS_TEST_PYTHONPATH || (!explicitPython && runtime.pythonpath);
if (support) testEnv.PYTHONPATH = [support, testEnv.PYTHONPATH].filter(Boolean).join(path.delimiter);
const bundled = path.join(process.env.USERPROFILE || '', '.cache', 'codex-runtimes',
  'codex-primary-runtime', 'dependencies', 'python', 'python.exe');
const candidates = process.env.BEOPS_PYTHON
  ? [[process.env.BEOPS_PYTHON, []]]
  : runtime.python ? [[runtime.python, []]]
  : [...(fs.existsSync(bundled) ? [[bundled, []]] : []), ['python', []], ['python3', []]];
let selected;
for (const [exe, prefix] of candidates) {
  const check = spawnSync(exe, [...prefix, '-B', '-c',
    'import sys; assert sys.version_info >= (3, 12); from reportlab.pdfbase.ttfonts import TTFont'],
    { windowsHide: true, timeout: 15000, stdio: 'ignore', env: testEnv });
  if (check.error?.code === 'ETIMEDOUT') console.error('Research prerequisite import exceeded 15 s.');
  if (check.status === 0) { selected = [exe, prefix]; break; }
}
if (!selected) {
  console.error('The complete research gate requires Python 3.12+ with the existing reportlab PDF support. ' +
    'Set BEOPS_PYTHON (or BEOPS_TEST_PYTHON for publishing) to a complete installed interpreter. No install attempted.');
  process.exit(1);
}
if (process.argv?.includes('--check')) {
  console.error('Research gate prerequisites passed.');
  process.exit(0);
}
// Disjoint discovery patterns cover every test_*.py, including future names
// outside a-z. Each process retains the 120 s ceiling; the whole growing suite
// no longer loses its completed work when the shared disk is busy.
const patterns = ['test_[a-f]*.py', 'test_[g-l]*.py', 'test_[m-o]*.py', 'test_p*.py', 'test_[q-r]*.py',
  'test_[s-z]*.py', 'test_[!a-z]*.py', 'test_.py'];
let groupsWithTests = 0;
for (const pattern of patterns) {
  console.error(`Research gate: ${pattern}`);
  const result = spawnSync(selected[0], [...selected[1], '-X', 'utf8', '-B', '-m', 'unittest', 'discover',
    '-s', 'research', '-p', pattern, '-v'], {
    cwd: path.resolve(__dirname, '..'), stdio: 'inherit', windowsHide: true, timeout: 120000, env: testEnv,
  });
  if (result.error) console.error(result.error.message);
  // Python uses exit 5 when a disjoint discovery bucket contains no tests.
  // That is expected for the catch-all buckets until such a filename exists;
  // every real failure retains a different non-zero status.
  if (result.error || (result.status !== 0 && result.status !== 5)) process.exit(1);
  if (result.status === 0) groupsWithTests += 1;
}
if (groupsWithTests === 0) {
  console.error('Research gate refused success: discovery ran zero tests.');
  process.exit(1);
}
console.error('Full research gate passed: all discovery groups completed.');
process.exit(0);
