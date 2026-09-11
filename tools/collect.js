'use strict';
// The package entry point uses the same permission gate and records as the scheduler.
const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  console.log('Usage: npm run collect -- [tick|status|report|check|export] [--only SOURCE_ID]\nDefault: tick. Help performs no collection or network requests.');
  process.exit(0);
}
const commands = new Set(['tick', 'status', 'report', 'check', 'export']);
if (!args.length) args.push('tick');
if (!commands.has(args[0]) || (args.length !== 1 && !(args.length === 3 && args[1] === '--only' && /^S\d+$/.test(args[2])))) {
  console.error('Invalid arguments. Use --help.'); process.exit(2);
}
const fs = require('node:fs'), path = require('node:path'), {spawnSync} = require('node:child_process');
const bundled = path.join(process.env.USERPROFILE || '', '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe');
const candidates = process.env.BEOPS_PYTHON ? [process.env.BEOPS_PYTHON] : [fs.existsSync(bundled) && bundled, 'python', 'python3'].filter(Boolean);
const python = candidates.find(exe => spawnSync(exe, ['-B', '-c', 'import sys; assert sys.version_info >= (3,12)'], {timeout:5000, windowsHide:true, stdio:'ignore'}).status === 0);
if (!python) { console.error('Python 3.12+ required; set BEOPS_PYTHON.'); process.exit(1); }
const result = spawnSync(python, ['-X', 'utf8', '-B', path.join(__dirname, 'collect_daemon.py'), ...args], {
  cwd:path.resolve(__dirname, '..'), windowsHide:true, stdio:'inherit', timeout:540000,
});
if (result.error) console.error(result.error.message);
process.exit(result.status === 0 ? 0 : 1);
