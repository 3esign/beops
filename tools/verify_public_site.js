'use strict';
/*
 * verify_public_site.js - read-only check that the public interface is the export.
 *
 * This is deliberately outside `npm test`: the full suite is an offline pre-publish gate, while this
 * tool asks GitHub Pages after a publish whether the live page is the same artefact the public mirror
 * contains. It does not touch project data.
 */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const http = require('node:http');
const https = require('node:https');

const ROOT = path.resolve(__dirname, '..');
const SITE_URL = process.env.BEOPS_SITE_URL || 'https://3esign.github.io/beops/';
const RAW_INDEX_URL = process.env.BEOPS_RAW_INDEX_URL ||
  'https://raw.githubusercontent.com/3esign/beops/main/docs/index.html';
const PUBLIC_ROOT = process.env.BEOPS_PUBLIC_ROOT
  ? path.resolve(process.env.BEOPS_PUBLIC_ROOT)
  : path.resolve(ROOT, '..', 'Beops-public');
const WAIT_SECONDS = Number(process.env.BEOPS_SITE_WAIT_SECONDS || '120');
const POLL_MS = Number(process.env.BEOPS_SITE_POLL_MS || '10000');
const RUN_DEADLINE = Math.min(Date.now() + Math.max(10, WAIT_SECONDS + 30) * 1000,
  process.env.BEOPS_CYCLE_DEADLINE ? Date.parse(process.env.BEOPS_CYCLE_DEADLINE) : Infinity);
const CHECK_RAW = process.env.BEOPS_CHECK_RAW === '1';
const MAX_AGE_MINUTES = Number(process.env.BEOPS_SITE_MAX_AGE_MINUTES || '60');
const MAX_MARKUP_BYTES = 2 * 1024 * 1024;
const GENERATION_ROUTES = new Set(['live-snapshot.json', 'history.json', 'city-overview.json', 'city-analysis.json']);

const CORE_ROUTES = [
  'instrument.html', 'events.json',
  'mapa.html', 'mapa.js', 'MAP_LAYERS.json', 'materija.json',
  'ai-feed.html', 'ai-feed/latest.json', 'kontekst.html', 'context-catalog.json',
  'podaci.html',
  'monolog.html',
  'sada.html',
  'traka.html',
  'svedoci.html',
  'obrasci.html', 'city-overview.json', 'city-analysis.json', 'beops-view.js',
  'live-snapshot.json', 'history.json', 'watch.json', 'latency.json', 'agreement.json',
  'basemap-belgrade.json',
  'export-manifest.json'
];

const CITIZEN_REQUIRED_MARKERS = [
  'Beograd danas',
  'BEOPS',
  'local AI infrastructure'
];

const REQUIRED_MARKERS = [
  'Ovo je ono sto nam je Beograd rekao',
  'local AI infrastructure',
  'href="#izvori"',
  'href="#greske"'
];

const FORBIDDEN_MARKERS = [
  'Claude, Anthropic',
  'Claude Fable',
  'Svemir (Claude',
  'UI je odlo',
  'no public release has happened'
];

function normalizeText(s) {
  return String(s || '').replace(/^\uFEFF/, '').replace(/\r\n/g, '\n');
}

function validateGeneration(rel, value, expectedId, expectedAsOf) {
  const generation=rel==='city-overview.json'?value.edition?.input_generation:value.input_generation;
  if(!/^[a-f0-9]{64}$/.test(expectedId||'')||generation?.id!==expectedId||generation?.schema!=='beops-input-generation/v1'||generation.observation_prefix!=='complete-lf-lines/v1')throw Error('input generation differs from export manifest');
  const captured=Date.parse(generation.captured_at),asOf=Date.parse(value.as_of);
  if(!Number.isFinite(captured)||!Number.isFinite(asOf)||Math.floor(captured/1000)!==Math.floor(asOf/1000))throw Error('projection clock differs from declared capture');
  if(expectedAsOf!==undefined&&Date.parse(expectedAsOf)!==Math.floor(captured/1000)*1000)throw Error('projection clock differs from export manifest');
  return generation.id;
}

function asciiFold(s) {
  return normalizeText(s).normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

function sha256(s) {
  return crypto.createHash('sha256').update(normalizeText(s)).digest('hex');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function firstExisting(paths) {
  return paths.find(p => fs.existsSync(p)) || '';
}

function localRouteFile(rel) {
  return firstExisting([
    path.join(PUBLIC_ROOT, 'docs', rel),
    path.join(ROOT, 'docs', rel)
  ]);
}

function cacheBusted(url) {
  const u = new URL(url);
  u.searchParams.set('beops_site_check', new Date().toISOString().replace(/[^0-9TZ]/g, ''));
  return u.toString();
}

function tryIncognitoHeaders(url) {
  const roots = [
    process.env.SVEMIR_ROOT,
    path.resolve(ROOT, '..', '..'),
    'C:\\Svemir'
  ].filter(Boolean);
  for (const base of roots) {
    try {
      const incognito = require(path.join(base, 'lib', 'incognito.js'));
      const headers = incognito.headers(url, { vrsta: 'html' });
      delete headers['Accept-Encoding'];
      return headers;
    } catch {
      // The public mirror can be cloned without Svemir. Fall back to a generic browser shape below.
    }
  }
  throw new Error('incognito header provider unavailable');
}

async function fetchText(url, options = {}) {
  const asked = cacheBusted(url);
  const deadline = Math.min(options.deadline ?? RUN_DEADLINE, RUN_DEADLINE);
  const maxBytes = options.maxBytes ?? 64 * 1024 * 1024;
  const keepBody = options.keepBody !== false;
  async function requestText(currentUrl, redirectsLeft) {
    if (Date.now() >= deadline) throw new Error('Public verification total deadline reached');
    const timeoutMs = Math.max(1, Math.min(10000, deadline - Date.now()));
    const parsed = new URL(currentUrl);
    const headers = tryIncognitoHeaders(parsed.toString());
    const client = parsed.protocol === 'http:' ? http : https;
    return await new Promise((resolve, reject) => {
      let timer;
      const fail = error => { clearTimeout(timer); reject(error); };
      let responseStream;
      const abort = error => {
        fail(error);
        // Destroy without forwarding the error onto a keep-alive socket whose
        // request listeners may already have detached after the final chunk.
        responseStream?.destroy();
        req.destroy();
      };
      const req = client.request(parsed, {method: 'GET', headers}, response => {
        responseStream = response;
        const status = response.statusCode || 0;
        const location = response.headers.location || '';
        if (status >= 300 && status < 400 && location) {
          clearTimeout(timer);
          response.resume();
          if (redirectsLeft <= 0) {
            reject(new Error(`Public response redirected too many times from ${currentUrl}`));
            return;
          }
          let nextUrl;
          try { nextUrl = new URL(location, currentUrl).toString(); }
          catch (error) { reject(new Error(`Public redirect is invalid: ${location}`)); return; }
          if (!/^https?:$/.test(new URL(nextUrl).protocol)) {
            reject(new Error(`Public redirect uses unsupported protocol: ${nextUrl}`));
            return;
          }
          resolve(requestText(nextUrl, redirectsLeft - 1));
          return;
        }
        const chunks = [];
        const digest = crypto.createHash('sha256');
        let size = 0;
        response.on('data', chunk => {
          size += chunk.length;
          if (size > maxBytes) {
            abort(new Error('Public response exceeds byte limit'));
            return;
          }
          digest.update(chunk);
          if (keepBody) chunks.push(chunk);
        });
        response.on('error', fail);
        response.on('aborted', () => fail(new Error('Public response ended before completion')));
        response.on('end', () => {
          clearTimeout(timer);
          const body = keepBody ? Buffer.concat(chunks) : null;
          resolve({
            url,
            asked: currentUrl,
            status,
            ok: status >= 200 && status < 300,
            etag: response.headers.etag || '',
            lastModified: response.headers['last-modified'] || '',
            cacheControl: response.headers['cache-control'] || '',
            hash: digest.digest('hex'),
            byteLength: size,
            ...(keepBody ? {text: body.toString('utf8'), bytes: body} : {})
          });
        });
      });
      timer = setTimeout(() => abort(new Error('Public verification total deadline reached')),
        Math.max(1, deadline - Date.now()));
      req.setTimeout(timeoutMs, () => abort(new Error(`Public fetch timed out after ${timeoutMs}ms`)));
      req.on('error', fail);
      req.end();
    });
  }
  return await requestText(asked, 5);
}

function fetchDigest(url, maxBytes, deadline = RUN_DEADLINE) {
  return fetchText(url, {keepBody: false, maxBytes, deadline});
}

/* Select only root metadata while hashing the complete local file. This is not
 * a replacement for the offline JSON validity gate: skipped payloads are never
 * reconstructed. Root keys, quoted strings, escapes and container boundaries
 * are tracked so a nested or quoted "as_of" cannot become publication metadata.
 */
function metadataReader() {
  const wanted = new Set(['as_of', 'input_generation', 'edition']);
  const result = Object.create(null), seen = new Set();
  let phase = 'start', token = '', key = '', quoted = false, escaped = false;
  let depth = 0, primitive = false, capture = false;
  const append = ch => {
    if (!capture && phase !== 'key') return;
    token += ch;
    if (token.length > 256 * 1024) throw new Error('Publication metadata exceeds bounded size');
  };
  const finishValue = () => {
    if (capture) result[key] = JSON.parse(token);
    token = ''; phase = 'separator'; primitive = false;
  };
  function write(text) {
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (phase === 'start') {
        if (/\s|\uFEFF/.test(ch)) continue;
        if (ch !== '{') throw new Error('Publication metadata requires a JSON object');
        phase = 'keyStart'; continue;
      }
      if (phase === 'done') {
        if (!/\s/.test(ch)) throw new Error('Unexpected bytes after publication JSON');
        continue;
      }
      if (phase === 'keyStart' || phase === 'nextKey') {
        if (/\s/.test(ch)) continue;
        if (ch === '}' && phase === 'keyStart') { phase = 'done'; continue; }
        if (ch !== '"') throw new Error('Invalid publication metadata key');
        phase = 'key'; token = '"'; quoted = true; escaped = false; continue;
      }
      if (phase === 'key') {
        append(ch);
        if (escaped) { escaped = false; continue; }
        if (ch === '\\') { escaped = true; continue; }
        if (ch !== '"') continue;
        key = JSON.parse(token); token = ''; quoted = false;
        if (wanted.has(key) && seen.has(key)) throw new Error('Duplicate publication metadata key: ' + key);
        if (wanted.has(key)) seen.add(key);
        phase = 'colon'; continue;
      }
      if (phase === 'colon') {
        if (/\s/.test(ch)) continue;
        if (ch !== ':') throw new Error('Invalid publication metadata separator');
        phase = 'valueStart'; continue;
      }
      if (phase === 'separator') {
        if (/\s/.test(ch)) continue;
        if (ch === ',') { phase = 'nextKey'; continue; }
        if (ch === '}') { phase = 'done'; continue; }
        throw new Error('Invalid publication metadata boundary');
      }
      if (phase === 'valueStart') {
        if (/\s/.test(ch)) continue;
        if (ch === '}' || ch === ',' || ch === ']') throw new Error('Missing publication metadata value');
        capture = wanted.has(key); token = ''; depth = 0; quoted = false; escaped = false;
        primitive = ch !== '{' && ch !== '[' && ch !== '"'; phase = 'value';
      }
      if (primitive && !quoted && depth === 0 && /[\s,}]/.test(ch)) {
        finishValue(); i--; continue;
      }
      append(ch);
      if (quoted) {
        if (escaped) { escaped = false; continue; }
        if (ch === '\\') { escaped = true; continue; }
        if (ch === '"') { quoted = false; if (!depth) finishValue(); }
      } else if (ch === '"') quoted = true;
      else if (ch === '{' || ch === '[') depth++;
      else if (ch === '}' || ch === ']') { if (--depth === 0) finishValue(); }
    }
  }
  return {write, finish() {
    if (phase !== 'done') throw new Error('Incomplete publication metadata JSON');
    return result;
  }};
}

async function inspectLocalRoute(file, rel) {
  const before = await fs.promises.stat(file);
  const markup = rel.endsWith('.html') && !rel.includes('/');
  if (markup && before.size > MAX_MARKUP_BYTES) throw new Error('Public markup exceeds byte limit');
  const metadata = GENERATION_ROUTES.has(rel) ? metadataReader() : null;
  const decoder = metadata ? new (require('node:string_decoder').StringDecoder)('utf8') : null;
  const digest = crypto.createHash('sha256'), chunks = [];
  let bytes = 0;
  for await (const chunk of fs.createReadStream(file)) {
    bytes += chunk.length; digest.update(chunk);
    if (metadata) metadata.write(decoder.write(chunk));
    if (markup) chunks.push(chunk);
  }
  const after = await fs.promises.stat(file);
  if (bytes !== before.size || before.size !== after.size || before.mtimeMs !== after.mtimeMs ||
      before.ino !== after.ino || before.dev !== after.dev) throw new Error('Local publication changed during verification');
  if (metadata) metadata.write(decoder.end());
  return {hash: digest.digest('hex'), bytes, metadata: metadata?.finish(),
    text: markup ? Buffer.concat(chunks).toString('utf8') : undefined};
}

async function fetchMatchingRoute(url, expectedHash, deadline, options = {}) {
  const get = options.get || fetchText;
  const now = options.now || Date.now;
  const pause = options.pause || sleep;
  const pollMs = options.pollMs ?? POLL_MS;
  const verification_attempts = [];
  let item;
  do {
    item = await get(url);
    const hash = item.hash || crypto.createHash('sha256').update(item.bytes).digest('hex');
    const match = item.ok && (!expectedHash || hash === expectedHash);
    verification_attempts.push({status: item.status, hash, match});
    if (match || now() >= deadline) break;
    await pause(Math.min(Math.max(1, pollMs), Math.max(0, deadline - now())));
  } while (now() < deadline);
  return {...item, verification_attempts};
}

async function mapBounded(items, limit, worker) {
  const results = new Array(items.length);
  let next = 0;
  await Promise.all(Array.from({length: Math.min(limit, items.length)}, async () => {
    for (;;) {
      const index = next++;
      if (index >= items.length) return;
      results[index] = await worker(items[index]);
    }
  }));
  return results;
}

async function main() {
  const errors = [];
  const warnings = [];
  const routes = [];
  const attempts = [];
  let freshness = null;
  const localIndex = firstExisting([
    path.join(PUBLIC_ROOT, 'docs', 'index.html'),
    path.join(ROOT, 'docs', 'index.html')
  ]);

  if (!localIndex) {
    errors.push('no local docs/index.html found in public mirror or private build');
  }

  let localText = '';
  if (localIndex) {
    if (fs.statSync(localIndex).size > MAX_MARKUP_BYTES) throw new Error('Public markup exceeds byte limit');
    localText = fs.readFileSync(localIndex, 'utf8');
  }

  let live = null;
  const localHash = localText ? sha256(localText) : '';
  const deadline = Date.now() + Math.max(0, WAIT_SECONDS) * 1000;
  do {
    live = await fetchText(SITE_URL, {maxBytes: MAX_MARKUP_BYTES});
    const liveHash = sha256(live.text);
    attempts.push({ status: live.status, hash: liveHash, match: localHash ? liveHash === localHash : false });
    if (live.ok && (!localHash || liveHash === localHash)) break;
    if (Date.now() >= deadline) break;
    await sleep(POLL_MS);
  } while (true);

  if (!live.ok) {
    errors.push(`public site returned HTTP ${live.status}`);
  }
  if (localHash && sha256(live.text) !== localHash) {
    errors.push(`public site hash ${sha256(live.text)} does not match ${localIndex} hash ${localHash}`);
  }

  const foldedLive = asciiFold(live.text);
  for (const marker of CITIZEN_REQUIRED_MARKERS) {
    if (!foldedLive.includes(asciiFold(marker))) {
      errors.push(`public site is missing required marker: ${marker}`);
    }
  }
  for (const marker of FORBIDDEN_MARKERS) {
    if (foldedLive.includes(asciiFold(marker))) {
      errors.push(`public site still contains stale marker: ${marker}`);
    }
  }

  const manifestFile = localRouteFile('export-manifest.json');
  if (!manifestFile) throw new Error('Missing local release manifest');
  const manifest=JSON.parse(fs.readFileSync(manifestFile,'utf8').replace(/^\uFEFF/,''));
  if(!live.text.includes('<meta name="beops-input-generation" content="'+manifest.inputs_manifest_sha256+'">'))errors.push('public HTML generation differs from export manifest');
  const required=new Set(CORE_ROUTES);
  for(const item of manifest.files||[]){if(item.path.startsWith('docs/'))required.add(item.path.slice(5));}
  const expectedRoutes = [...required].map(rel => {
    const localRoute = localRouteFile(rel);
    return {rel, localRoute};
  });
  const checked = await mapBounded(expectedRoutes, 6, async expected => {
    try {
      if(Date.now()>=RUN_DEADLINE)throw new Error('Public verification total deadline reached');
      if (!expected.localRoute) throw new Error('no local public mirror file for ' + expected.rel);
      const local = await inspectLocalRoute(expected.localRoute, expected.rel);
      const item = await fetchMatchingRoute(new URL(expected.rel, SITE_URL).toString(), local.hash, RUN_DEADLINE, {
        // The local export supplies the bound. A growing history is not limited
        // by an unrelated fixed 64 MiB cap, and no remote route body is retained.
        get: url => fetchDigest(url, local.bytes + 1024 * 1024, RUN_DEADLINE)
      });
      const htmlGeneration = local.text === undefined || local.text.includes(
        '<meta name="beops-input-generation" content="' + manifest.inputs_manifest_sha256 + '">');
      const missingMarkers = expected.rel === 'instrument.html'
        ? REQUIRED_MARKERS.filter(marker => !asciiFold(local.text).includes(asciiFold(marker))) : [];
      return {...expected, localRouteHash: local.hash, localMetadata: local.metadata,
        htmlGeneration, missingMarkers, item};
    } catch(error) {
      return {...expected, error: error.message};
    }
  });
  for (const {rel, localRoute, localRouteHash, localMetadata, htmlGeneration, missingMarkers, item, error} of checked) {
    if (error) {
      errors.push(`${rel} verification failed: ${error}`);
      routes.push({route: rel, ok: false, error});
      continue;
    }
    const route = { route: rel, status: item.status, ok: item.ok,
      verification_attempts: item.verification_attempts };
    if (!item.ok) {
      errors.push(`${rel} returned HTTP ${item.status}`);
    }
    const matchesLocal = item.ok && item.hash === localRouteHash;
    // Metadata came from the same local stream as localRouteHash. It describes
    // the public bytes only after the complete remote digest matches that hash.
    if(matchesLocal&&GENERATION_ROUTES.has(rel)){
      try{route.input_generation=validateGeneration(rel,localMetadata,manifest.inputs_manifest_sha256,manifest.generated_as_of);}
      catch(error){errors.push(`${rel} generation is invalid: ${error.message}`);}
    }
    if(matchesLocal&&!htmlGeneration)errors.push(`${rel} HTML generation differs from export manifest`);
    if (rel === 'instrument.html' && matchesLocal) {
      for (const marker of missingMarkers) errors.push(`instrument.html is missing required marker: ${marker}`);
    }
    if (rel === 'live-snapshot.json' && matchesLocal) {
      try {
        const snapshot = localMetadata;
        const asOfMs = Date.parse(snapshot.as_of);
        if (!Number.isFinite(asOfMs)) throw new Error('missing or invalid as_of');
        const ageMinutes = (Date.now() - asOfMs) / 60000;
        freshness = {as_of: snapshot.as_of, age_minutes: Math.round(ageMinutes * 10) / 10,
          max_age_minutes: MAX_AGE_MINUTES, ok: ageMinutes >= -5 && ageMinutes <= MAX_AGE_MINUTES};
        if (!freshness.ok) errors.push(`public snapshot is ${freshness.age_minutes} min old; freshness limit is ${MAX_AGE_MINUTES} min`);
      } catch (error) {
        freshness = {as_of: null, age_minutes: null, max_age_minutes: MAX_AGE_MINUTES, ok: false};
        errors.push(`public snapshot freshness is unreadable: ${error.message}`);
      }
    }
    if (localRoute) {
      const liveRouteHash = item.hash;
      route.live_hash = liveRouteHash;
      route.local_hash = localRouteHash;
      route.bytes = item.byteLength;
      route.match = liveRouteHash === localRouteHash;
      if (item.ok && !route.match) {
        errors.push(`${rel} hash ${liveRouteHash} does not match ${localRoute} hash ${localRouteHash}`);
      }
    } else {
      errors.push(`no local public mirror file for ${rel}`);
    }
    routes.push(route);
  }

  // Retries take real time; report snapshot age at the end of verification too.
  if (freshness && freshness.as_of) {
    const ageMinutes = (Date.now() - Date.parse(freshness.as_of)) / 60000;
    const wasFresh = freshness.ok;
    freshness.age_minutes = Math.round(ageMinutes * 10) / 10;
    freshness.ok = ageMinutes >= -5 && ageMinutes <= MAX_AGE_MINUTES;
    if (wasFresh && !freshness.ok) errors.push(`public snapshot is ${freshness.age_minutes} min old; freshness limit is ${MAX_AGE_MINUTES} min`);
  }

  if (CHECK_RAW) {
    const raw = await fetchText(RAW_INDEX_URL, {maxBytes: MAX_MARKUP_BYTES});
    if (!raw.ok) {
      warnings.push(`raw GitHub index returned HTTP ${raw.status}`);
    } else if (sha256(raw.text) !== sha256(live.text)) {
      warnings.push('raw GitHub index and GitHub Pages differ; this can be short-lived cache propagation');
    }
  }

  const summary = {
    ok: errors.length === 0,
    operational_verdict: errors.length === 0 ? 'CURRENT_AND_VERIFIED' : (freshness && !freshness.ok ? 'STALE_OR_FAILED' : 'FAILED'),
    freshness,
    site: SITE_URL,
    local_index: localIndex,
    live_hash: sha256(live.text),
    local_hash: localHash,
    live_status: live.status,
    live_last_modified: live.lastModified,
    live_cache_control: live.cacheControl,
    wait_seconds: WAIT_SECONDS,
    raw_check: CHECK_RAW,
    attempts,
    routes,
    warnings,
    errors
  };
  console.log(JSON.stringify(summary, null, 2));
  if (errors.length) process.exit(1);
}

module.exports = {fetchMatchingRoute, fetchDigest, inspectLocalRoute, metadataReader, mapBounded, validateGeneration};
if (require.main === module) main().catch(err => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
