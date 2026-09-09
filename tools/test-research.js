'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const bundled = path.join(process.env.USERPROFILE || '', '.cache', 'codex-runtimes',
  'codex-primary-runtime', 'dependencies', 'python', 'python.exe');
const candidates = process.env.BEOPS_PYTHON
  ? [[process.env.BEOPS_PYTHON, []]]
  : [...(fs.existsSync(bundled) ? [[bundled, []]] : []), ['python', []], ['python3', []]];
let selected;
for (const [exe, prefix] of candidates) {
  const check = spawnSync(exe, [...prefix, '-c', 'import sys; assert sys.version_info >= (3, 9)'],
    { windowsHide: true, timeout: 5000, stdio: 'ignore' });
  if (check.status === 0) { selected = [exe, prefix]; break; }
}
if (!selected) {
  console.error('Python 3.9+ required for stdlib research tests; set BEOPS_PYTHON. No install attempted.');
  process.exit(1);
}
const result = spawnSync(selected[0], [...selected[1], '-B', '-m', 'unittest', 'discover',
  '-s', 'research', '-p', 'test_*.py', '-v'], {
  cwd: path.resolve(__dirname, '..'), stdio: 'inherit', windowsHide: true, timeout: 60000,
});
if (result.error) console.error(result.error.message);
process.exit(result.status === 0 ? 0 : 1);
