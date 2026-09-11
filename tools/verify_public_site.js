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

const ROOT = path.resolve(__dirname, '..');
const SITE_URL = process.env.BEOPS_SITE_URL || 'https://3esign.github.io/beops/';
const RAW_INDEX_URL = process.env.BEOPS_RAW_INDEX_URL ||
  'https://raw.githubusercontent.com/3esign/beops/main/docs/index.html';
const PUBLIC_ROOT = process.env.BEOPS_PUBLIC_ROOT
  ? path.resolve(process.env.BEOPS_PUBLIC_ROOT)
  : path.resolve(ROOT, '..', 'Beops-public');
const WAIT_SECONDS = Number(process.env.BEOPS_SITE_WAIT_SECONDS || '120');
const POLL_MS = Number(process.env.BEOPS_SITE_POLL_MS || '10000');
const CHECK_RAW = process.env.BEOPS_CHECK_RAW === '1';

const CORE_ROUTES = [
  'podaci.html',
  'monolog.html',
  'sada.html',
  'traka.html',
  'svedoci.html',
  'live-snapshot.json',
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
  return {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'DNT': '1'
  };
}

async function fetchText(url) {
  const asked = cacheBusted(url);
  const response = await fetch(asked, {
    cache: 'no-store',
    redirect: 'follow',
    headers: tryIncognitoHeaders(url)
  });
  const text = await response.text();
  return {
    url,
    asked,
    status: response.status,
    ok: response.ok,
    etag: response.headers.get('etag') || '',
    lastModified: response.headers.get('last-modified') || '',
    cacheControl: response.headers.get('cache-control') || '',
    text
  };
}

async function main() {
  const errors = [];
  const warnings = [];
  const routes = [];
  const attempts = [];
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

  for (const rel of CORE_ROUTES) {
    const url = new URL(rel, SITE_URL).toString();
    const item = await fetchText(url);
    const route = { route: rel, status: item.status, ok: item.ok };
    if (!item.ok) {
      errors.push(`${rel} returned HTTP ${item.status}`);
    }
    const localRoute = localRouteFile(rel);
    if (localRoute) {
      const liveRouteHash = sha256(item.text);
      const localRouteHash = sha256(fs.readFileSync(localRoute, 'utf8'));
      route.live_hash = liveRouteHash;
      route.local_hash = localRouteHash;
      route.match = liveRouteHash === localRouteHash;
      if (item.ok && !route.match) {
        errors.push(`${rel} hash ${liveRouteHash} does not match ${localRoute} hash ${localRouteHash}`);
      }
    } else {
      warnings.push(`no local public mirror file for ${rel}`);
    }
    routes.push(route);
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

main().catch(err => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
