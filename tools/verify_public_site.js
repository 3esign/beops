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

const CORE_ROUTES = [
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

async function fetchText(url) {
  const asked = cacheBusted(url);
  const timeoutMs = Math.max(1, Math.min(10000, RUN_DEADLINE - Date.now()));
  async function requestText(currentUrl, redirectsLeft) {
    const parsed = new URL(currentUrl);
    const headers = tryIncognitoHeaders(parsed.toString());
    const client = parsed.protocol === 'http:' ? http : https;
    return await new Promise((resolve, reject) => {
      const req = client.request(parsed, {method: 'GET', headers}, response => {
        const status = response.statusCode || 0;
        const location = response.headers.location || '';
        if (status >= 300 && status < 400 && location) {
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
        let size = 0;
        response.on('data', chunk => {
          size += chunk.length;
          if (size > 64 * 1024 * 1024) {
            req.destroy(new Error('Public response exceeds byte limit'));
            return;
          }
          chunks.push(Buffer.from(chunk));
        });
        response.on('end', () => {
          const bytes = Buffer.concat(chunks);
          resolve({
            url,
            asked: currentUrl,
            status,
            ok: status >= 200 && status < 300,
            etag: response.headers.etag || '',
            lastModified: response.headers['last-modified'] || '',
            cacheControl: response.headers['cache-control'] || '',
            text: bytes.toString('utf8'),
            bytes
          });
        });
      });
      req.setTimeout(timeoutMs, () => req.destroy(new Error(`Public fetch timed out after ${timeoutMs}ms`)));
      req.on('error', reject);
      req.end();
    });
  }
  return await requestText(asked, 5);
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
    const hash = crypto.createHash('sha256').update(item.bytes).digest('hex');
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
    localText = fs.readFileSync(localIndex, 'utf8');
  }

  let live = null;
  const localHash = localText ? sha256(localText) : '';
  const deadline = Date.now() + Math.max(0, WAIT_SECONDS) * 1000;
  do {
    live = await fetchText(SITE_URL);
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
  for (const marker of REQUIRED_MARKERS) {
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
    const localRouteHash = localRoute
      ? crypto.createHash('sha256').update(fs.readFileSync(localRoute)).digest('hex') : '';
    return {rel, localRoute, localRouteHash};
  });
  const checked = await mapBounded(expectedRoutes, 6, async expected => {
    try {
      if(Date.now()>=RUN_DEADLINE)throw new Error('Public verification total deadline reached');
      const item = await fetchMatchingRoute(new URL(expected.rel, SITE_URL).toString(), expected.localRouteHash, RUN_DEADLINE);
      return {...expected, item};
    } catch(error) {
      return {...expected, error: error.message};
    }
  });
  for (const {rel, localRoute, localRouteHash, item, error} of checked) {
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
    if(item.ok&&['live-snapshot.json','history.json','city-overview.json','city-analysis.json'].includes(rel)){
      try{route.input_generation=validateGeneration(rel,JSON.parse(normalizeText(item.text)),manifest.inputs_manifest_sha256,manifest.generated_as_of);}
      catch(error){errors.push(`${rel} generation is invalid: ${error.message}`);}
    }
    if(item.ok&&rel.endsWith('.html')&&!rel.includes('/')&&!item.text.includes('<meta name="beops-input-generation" content="'+manifest.inputs_manifest_sha256+'">'))errors.push(`${rel} HTML generation differs from export manifest`);
    if (rel === 'live-snapshot.json' && item.ok) {
      try {
        const snapshot = JSON.parse(normalizeText(item.text));
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
      const liveRouteHash = crypto.createHash('sha256').update(item.bytes).digest('hex');
      route.live_hash = liveRouteHash;
      route.local_hash = localRouteHash;
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
    const raw = await fetchText(RAW_INDEX_URL);
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

module.exports = {fetchMatchingRoute, mapBounded, validateGeneration};
if (require.main === module) main().catch(err => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
