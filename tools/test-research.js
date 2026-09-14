'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const runtimePath = path.resolve(__dirname, '..', 'runtime', 'test-python.json');
const runtime = fs.existsSync(runtimePath) ? JSON.parse(fs.readFileSync(runtimePath, 'utf8').replace(/^\uFEFF/, '')) : {};
const explicitPython = process.env.BEOPS_PYTHON;
const testEnv = {...process.env};
function phase(name, started, status, error) {
  if (!process.env.BEOPS_PHASE_TRACE) return;
  fs.appendFileSync(process.env.BEOPS_PHASE_TRACE, JSON.stringify({
    schema: 'beops-phase/v1', at: new Date().toISOString(), name,
    seconds: (Date.now()-started)/1000, exit_code: status,
    error: error?.code || null, pid: process.pid
  })+'\n');
}
const support = process.env.BEOPS_TEST_PYTHONPATH || (!explicitPython && runtime.pythonpath);
// Every isolated test file gets the same explicit project import roots; imports
// must not depend on a previous test mutating sys.path in a shared interpreter.
testEnv.PYTHONPATH = [support, path.resolve(__dirname), path.resolve(__dirname, '..', 'research'),
  testEnv.PYTHONPATH].filter(Boolean).join(path.delimiter);
const bundled = path.join(process.env.USERPROFILE || '', '.cache', 'codex-runtimes',
  'codex-primary-runtime', 'dependencies', 'python', 'python.exe');
const candidates = process.env.BEOPS_PYTHON
  ? [[process.env.BEOPS_PYTHON, []]]
  : runtime.python ? [[runtime.python, []]]
  : [...(fs.existsSync(bundled) ? [[bundled, []]] : []), ['python', []], ['python3', []]];
let selected;
for (const [exe, prefix] of candidates) {
  const started = Date.now();
  const prerequisiteRemaining = process.env.BEOPS_CYCLE_DEADLINE
    ? Date.parse(process.env.BEOPS_CYCLE_DEADLINE)-Date.now() : Infinity;
  if (!(prerequisiteRemaining > 0)) {
    console.error('Publication cycle budget exhausted before prerequisites');
    process.exit(1);
  }
  const check = spawnSync(exe, [...prefix, '-B', '-c',
    'import sys; assert sys.version_info >= (3, 12); from reportlab.pdfbase.ttfonts import TTFont'],
    { windowsHide: true, timeout: Math.min(60000, prerequisiteRemaining), stdio: 'ignore', env: testEnv });
  phase('research prerequisites', started, check.status, check.error);
  if (check.error?.code === 'ETIMEDOUT') {
    console.error('Research prerequisite import exceeded 60 s; interpreter readiness is unconfirmed.');
    process.exit(1);
  }
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
// Discover the complete inventory, then bound each file independently. Growing
// alphabetic buckets must not silently inherit one shared 120 s deadline.
const researchDir = path.resolve(__dirname, '..', 'research');
const patterns = fs.readdirSync(researchDir).filter(name => /^test_.*\.py$/.test(name)).sort()
  .map(name => name.replace(/[\[*?]/g, ch => ({'[': '[[]', '*': '[*]', '?': '[?]'}[ch])));
let groupsWithTests = 0;
for (const pattern of patterns) {
  const started = Date.now();
  const remaining = process.env.BEOPS_CYCLE_DEADLINE
    ? Date.parse(process.env.BEOPS_CYCLE_DEADLINE)-Date.now() : Infinity;
  if (!(remaining > 0)) {
    console.error('Publication cycle budget exhausted before '+pattern);
    process.exit(1);
  }
  console.error(`Research gate: ${pattern}`);
  const result = spawnSync(selected[0], [...selected[1], '-X', 'utf8', '-B', '-m', 'unittest', 'discover',
    '-s', 'research', '-p', pattern, '-v'], {
    cwd: path.resolve(__dirname, '..'), stdio: 'inherit', windowsHide: true, timeout: Math.min(120000, remaining), env: testEnv,
  });
  phase('test: '+pattern, started, result.status, result.error);
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
