'use strict';
// Join the existing Svemir mutex; never invent a second GPU coordination protocol.
const path = require('node:path');
const crypto = require('node:crypto');
const root = process.env.BEOPS_SVEMIR_ROOT || 'C:/Svemir';
const { withLock } = require(path.join(root, 'lib', 'mind_lock.js'));
const owner = `beops-${process.pid}-${crypto.randomUUID()}`;
const waitMs = Math.max(0, Math.min(30000, Number(process.argv[2] || 0)));
let release;
const released = new Promise(resolve => { release = resolve; });
let closed = false;
function close() { closed = true; release(); }
process.stdin.on('data', close);
process.stdin.on('end', close); // parent crash closes the inherited pipe
process.stdin.on('error', close);
process.on('SIGTERM', close);
process.on('SIGINT', close);
process.stdin.resume();
withLock('ollama', async () => {
  if (closed) return;
  process.stdout.write(JSON.stringify({state:'acquired',owner}) + '\n');
  await released;
}, {mind:owner,waitMs,pollMs:100,ttlSec:1800}).catch(error => {
  process.stdout.write(JSON.stringify({state:error.code==='EMINDLOCK'?'busy':'unavailable',reason:error.code || error.name}) + '\n');
  process.exitCode = 2;
}).finally(() => { process.stdin.destroy(); });
