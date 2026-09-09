'use strict';
// Bounded istrazivacka proba novih cula za Beops (read-only, jedan zahtev po izvoru).
// Nije produkcijski kolektor; ne pokrece se iz schedulera.
const https = require('https');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, '..', 'research', 'evidence');
const UA = 'Beops-research/1.0 (Svemir; bounded probe; contact via svemir)';
const results = [];

function get(url, timeoutMs = 25000) {
  return new Promise((resolve) => {
    const t0 = Date.now();
    const req = https.get(url, { headers: { 'User-Agent': UA, Accept: 'application/json,*/*' }, timeout: timeoutMs }, (res) => {
      let body = '';
      res.on('data', (d) => { body += d; if (body.length > 3_000_000) req.destroy(); });
      res.on('end', () => resolve({ status: res.statusCode, ms: Date.now() - t0, body }));
    });
    req.on('timeout', () => { req.destroy(); resolve({ status: 'timeout', ms: Date.now() - t0, body: '' }); });
    req.on('error', (e) => resolve({ status: 'error:' + e.code, ms: Date.now() - t0, body: '' }));
  });
}

function record(id, name, url, res, extract) {
  const r = { id, name, url, http_status: res.status, elapsed_ms: res.ms, received_at: new Date().toISOString(), bytes: res.body.length };
  try { r.extract = extract(res.body, r); } catch (e) { r.extract = { error: e.message }; }
  results.push(r);
  console.log(id, res.status, res.ms + 'ms', res.body.length + 'B', JSON.stringify(r.extract).slice(0, 200));
}

(async () => {
  // S34 openSenseMap: registar gradjanskih kutija u Beogradu (bbox)
  const osm = await get('https://api.opensensemap.org/boxes?bbox=20.2,44.6,20.7,45.0&format=json');
  record('S34', 'openSenseMap Beograd', 'https://api.opensensemap.org/boxes?bbox=20.2,44.6,20.7,45.0&format=json', osm, (b) => {
    const j = JSON.parse(b);
    return { boxes: j.length, names: j.slice(0, 8).map((x) => x.name), sensor_types: [...new Set(j.flatMap((x) => (x.sensors || []).map((s) => s.title)))] };
  });

  // S35 OSM changesets: signal izmena mape Beograda (promene grada kroz zajednicu)
  const cs = await get('https://api.openstreetmap.org/api/0.6/changesets?bbox=20.2,44.6,20.7,45.0');
  record('S35', 'OSM changesets Beograd', 'https://api.openstreetmap.org/api/0.6/changesets?bbox=20.2,44.6,20.7,45.0', cs, (b) => {
    const n = (b.match(/<changeset /g) || []).length;
    const comments = [...b.matchAll(/<tag k="comment" v="([^"]{0,90})/g)].map((m) => m[1]).slice(0, 5);
    return { changesets: n, sample_comments: comments };
  });

  // S36 OpenSky: avioni u nadletu Beograda (ADS-B, pokretljivost visokog sloja)
  const sky = await get('https://opensky-network.org/api/states/all?lamin=44.5&lomin=20.0&lamax=45.1&lomax=20.8');
  record('S36', 'OpenSky ADS-B Beograd', 'https://opensky-network.org/api/states/all?lamin=44.5&lomin=20.0&lamax=45.1&lomax=20.8', sky, (b) => {
    const j = JSON.parse(b);
    const st = (j.states || []).filter(Boolean);
    return { server_time: j.time, aircraft: st.length, callsigns: st.slice(0, 5).map((s) => (s[1] || '').trim()) };
  });

  // S37 RIPE Atlas: mrezne probe u Srbiji/Beogradu (dostupnost mreze)
  const ripe = await get('https://atlas.ripe.net/api/v2/probes/?country_code=RS&format=json');
  record('S37', 'RIPE Atlas probe RS', 'https://atlas.ripe.net/api/v2/probes/?country_code=RS&format=json', ripe, (b) => {
    const j = JSON.parse(b);
    const bg = (j.results || []).filter((p) => { const c = (p.geometry || {}).coordinates || []; return c[0] > 20.1 && c[0] < 20.9 && c[1] > 44.4 && c[1] < 45.1; });
    return { probes_rs: j.count, probes_beograd_bbox: bg.length };
  });

  // S38 GDELT: geolocirani clanci o Beogradu (jedan zahtev, uz postovanje 5s ritma iz prosle probe)
  await new Promise((r) => setTimeout(r, 6000));
  const gd = await get('https://api.gdeltproject.org/api/v2/doc/doc?query=location:Belgrade&mode=artlist&maxrecords=5&format=json');
  record('S38', 'GDELT doc Belgrade', 'https://api.gdeltproject.org/api/v2/doc/doc?query=location:Belgrade&mode=artlist&maxrecords=5&format=json', gd, (b) => {
    if (b.startsWith('Please')) return { rate_limited: true, note: b.slice(0, 60) };
    const j = JSON.parse(b);
    return { articles: (j.articles || []).length, titles: (j.articles || []).slice(0, 3).map((a) => (a.title || '').slice(0, 60)) };
  });

  const stamp = new Date().toISOString().replace(/[:.]/g, '');
  const file = path.join(OUT, 'newsenses-' + stamp + '.json');
  fs.writeFileSync(file, JSON.stringify({ probe: 'beops nova cula runda 1', at: new Date().toISOString(), user_agent: UA, results }, null, 2));
  console.log('SPREMNO:', file);
})().catch((e) => { console.error('PROBE FAIL:', e.message); process.exitCode = 1; });