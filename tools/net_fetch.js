'use strict';
// BEOPS requests identify the observatory honestly (C-069). A disguised browser persona would let a
// publisher neither recognise nor refuse us by name, and the permission record would describe a
// visitor that does not exist. The same identity is what robots.txt is evaluated against.
const fs = require('node:fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const USER_AGENT = 'Beops-Research-Collect/1.0 (+https://3esign.github.io/beops/; poturaksemir@gmail.com)';
function identityHeaders(url) {
  return {
    'User-Agent': USER_AGENT,
    'From': 'poturaksemir@gmail.com',
    'Accept': '*/*',
    'Accept-Language': 'sr-RS,sr;q=0.9,en;q=0.8'
  };
}
// C-084: a request that failed on the network was still sent under this identity, and its receipt says so.
let sentIdentity = null;
async function main() {
  const url = new URL(input.url);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) throw new Error('Unsupported URL');
  const headers = identityHeaders(url.href);
  sentIdentity = headers['User-Agent'] || headers['user-agent'];
  if (input.headers_only) { process.stdout.write(JSON.stringify({user_agent: headers['User-Agent'] || headers['user-agent']})); return; }
  const timeout = Math.max(100, Math.min(120000, input.timeout_ms || 30000));
  const limit = Math.max(1, Math.min(262144000, input.max_bytes || 2097152));
  const response = await fetch(url, {headers, redirect: 'manual', signal: AbortSignal.timeout(timeout)});
  const out = {status: response.status, headers: Object.fromEntries(response.headers), body: null,
    request_user_agent: headers['User-Agent'] || headers['user-agent'], transport: 'node/verified TLS; honest identity', error: null};
  const h=out.headers;
  const refusal=/\b(?:ai-input|search)\s*=\s*no\b/i.test(h['content-signal']||'') || /\bno(?:image)?ai\b/i.test(h['x-robots-tag']||'') || /^1$/.test((h['tdm-reservation']||'').trim()) || /\b(?:ai|tdm)\s*=\s*n(?:o)?\b/i.test(h['content-usage']||'');
  if (refusal) {
    await response.body?.cancel(); out.error='Publisher opt-out in HTTP headers; body not read';
  } else if (response.status >= 300 && response.status < 400) {
    await response.body?.cancel();
    out.error = 'Redirect requires a separate permission capture';
  } else {
    const reader = response.body?.getReader();
    const chunks = []; let bytes = 0;
    if (reader) for (;;) {
      const {done, value} = await reader.read();
      if (done) break;
      bytes += value.length;
      if (bytes > limit) { await reader.cancel(); out.error = `Response exceeds ${limit} bytes`; break; }
      chunks.push(Buffer.from(value));
    }
    if (!out.error) out.body = Buffer.concat(chunks).toString('base64');
  }
  process.stdout.write(JSON.stringify(out));
}
// C-083: undici reports every network failure as "fetch failed" and keeps the reason in error.cause.
// Without it a failing source cannot be told apart: refused, reset, DNS, TLS or a timeout.
function describe(error) {
  const parts = [String(error && error.message)];
  let cause = error && error.cause, depth = 0;
  while (cause && depth < 3) {
    const bits = [cause.code, cause.name !== 'Error' ? cause.name : null, cause.message].filter(Boolean);
    if (bits.length) parts.push(bits.join(' '));
    cause = cause.cause; depth += 1;
  }
  return parts.join(' <- ').slice(0, 240);
}
main().catch(error => { process.stdout.write(JSON.stringify({status:null, headers:{}, body:null,
  error: describe(error), request_user_agent: input.headers_only ? null : sentIdentity,
  transport:'node/verified TLS; honest identity'})); process.exitCode=1; });
