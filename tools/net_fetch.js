'use strict';
// Every outbound request gets its headers from the workspace identity boundary.
const fs = require('node:fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const paths = [process.env.BEOPS_INCOGNITO, 'C:/Svemir/lib/incognito.js', 'D:/Svemir/lib/incognito.js'].filter(Boolean);
const incognitoPath = paths.find(p => fs.existsSync(p));
async function main() {
  if (!incognitoPath) throw new Error('Incognito header provider is unavailable; configure BEOPS_INCOGNITO');
  const url = new URL(input.url);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) throw new Error('Unsupported URL');
  const headers = require(incognitoPath).headers(url.href, {vrsta: 'html'});
  if (input.headers_only) { process.stdout.write(JSON.stringify({user_agent: headers['User-Agent'] || headers['user-agent']})); return; }
  const timeout = Math.max(100, Math.min(120000, input.timeout_ms || 30000));
  const limit = Math.max(1, Math.min(262144000, input.max_bytes || 2097152));
  const response = await fetch(url, {headers, redirect: 'manual', signal: AbortSignal.timeout(timeout)});
  const out = {status: response.status, headers: Object.fromEntries(response.headers), body: null,
    request_user_agent: headers['User-Agent'] || headers['user-agent'], transport: 'node/verified TLS; incognito', error: null};
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
main().catch(error => { process.stdout.write(JSON.stringify({status:null, headers:{}, body:null,
  error: String(error.message).slice(0,240), transport:'node/verified TLS; incognito'})); process.exitCode=1; });
