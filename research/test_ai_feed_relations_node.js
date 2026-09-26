'use strict';
// C-074: the AI panel may connect facts only through a named relation, may not invent terrain,
// norms or patterns, and may not call readings hours apart simultaneous.
const assert = require('node:assert/strict');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const root = path.resolve(__dirname, '..');
const C = require('../tools/ai_feed_context');
const Rel = require('../tools/ai_feed_relations');
const { revalidate } = require('../tools/ai_feed_revalidate');

const obs = (id, metric, value, time, place, location, extra = {}) => ({ kind: 'observation', id, metric, value, time, place, location, unit: '', ...extra });
const SAVA = [20.45, 44.82], DUNAV = [20.41, 44.85], VRACAR = [20.47, 44.80], BANOVO = [20.41, 44.78], KALEMEGDAN = [20.45, 44.82];

// Facts shaped like the two entries published on 16 September 2026 (05:06 and 08:28).
const night = {
  facts: [
    obs('F1', 'free_spaces', 105, '2026-09-16T03:03:00Z', 'Parkiralište „Kalemegdan“', KALEMEGDAN, { comparison: { from_value: 89, from_time: '2026-09-15T21:03:00Z', delta: 16 } }),
    obs('F2', 'Sava|water_temperature', 24.8, '2026-09-15T06:00:00Z', 'Beograd (Sava)', SAVA),
    obs('F4', 'free_spaces', 89, '2026-09-15T21:03:00Z', 'Parkiralište „Kalemegdan“', KALEMEGDAN),
    obs('F11', 'Dunav|water_temperature', 21.9, '2026-09-15T06:00:00Z', 'Zemun (Dunav)', DUNAV),
  ],
};
const nightText = {
  title: 'Noćni predah nad ušćem',
  paragraphs: [
    { text: 'U noćnim satima, dok saobraćaj u gradu uglavnom miruje, parkiralište Kalemegdan beleži 105 slobodnih mesta, iako se u ovom periodu noći obično očekuje popunjenost parking prostora.', cites: ['F1', 'F4'] },
    { text: 'Istovremeno, tik ispod kalemegdanskog grebena, reke pokazuju primetnu razliku u temperaturi vode zabeleženoj u 06:00 UTC prethodnog dana: Sava 24,8, Dunav 21,9.', cites: ['F2', 'F11'] },
  ],
  question: 'Zbog čega se slobodna mesta na obodu tvrđave oslobađaju usred noćnog zatišja dok reke podno nje zadržavaju tako različitu toplotu?',
  limitations: 'Dva očitavanja nisu uzrok.',
};
const morning = {
  facts: [
    obs('F3', 'wind_speed', 0, '2026-09-16T06:00:00Z', 'Beograd', VRACAR),
    obs('F6', 'NO2', 24.83, '2026-09-16T05:00:00Z', 'Beograd Banovo brdo', BANOVO),
    obs('F11', 'free_spaces', 80, '2026-09-16T08:10:00Z', 'Parkiralište „Opština Novi Beograd“', [20.40, 44.81]),
  ],
};
const morningText = {
  title: 'Jutarnje mirovanje između padine i ravnice',
  paragraphs: [
    { text: 'U ranim jutarnjim satima vazduh deluje mirno, jer je u 06:00 UTC zabeležena brzina vetra 0. Na padini Banovog brda nivo azot-dioksida u 05:00 UTC iznosio je 24.83.', cites: ['F3', 'F6'] },
    { text: 'Sa druge strane reke, na parkiralištu kod zgrade opštine očitano je 80 slobodnih mesta. Neobično mi je da posmatram početak jutarnjih aktivnosti na tlu bez vazdušnih strujanja.', cites: ['F11'] },
  ],
  question: 'Kako se mirovanje vetra i slobodna mesta na parkingu prepliću u prostoru?',
  limitations: 'Pojedinačna očitavanja.',
};

// Relations: mechanism, comparison, and the absence of any link.
const rels = Rel.relations(morning.facts);
assert.ok(rels.some(r => r.rule === 'wind_dispersion' && r.facts.includes('F3') && r.facts.includes('F6')), 'wind and NO2 within 90 min and 30 km are related');
assert.ok(!rels.some(r => r.facts.includes('F11')), 'parking has no relation to wind or NO2');
const nrels = Rel.relations(night.facts);
assert.ok(nrels.some(r => r.kind === 'comparison' && r.facts.includes('F2') && r.facts.includes('F11')), 'Sava and Dunav temperature at the same hour are a comparison');
assert.ok(!nrels.some(r => (r.facts.includes('F1') || r.facts.includes('F4')) && (r.facts.includes('F2') || r.facts.includes('F11'))), 'parking and river temperature are never related');
// C-077: two gauges' water levels have different zeros and are never compared; their changes are.
const levels = [obs('L1', 'Sava|water_level', 123, '2026-09-16T06:00:00Z', 'Beograd (Sava)', SAVA), obs('L2', 'Dunav|water_level', 166, '2026-09-16T06:00:00Z', 'Zemun (Dunav)', DUNAV)];
assert.deepEqual(Rel.relations(levels), [], 'gauge levels are not comparable numbers');
const changes = [obs('C1', 'Sava|water_level_change', 4, '2026-09-16T06:00:00Z', 'Beograd (Sava)', SAVA), obs('C2', 'Dunav|water_level_change', 2, '2026-09-16T06:00:00Z', 'Zemun (Dunav)', DUNAV)];
assert.ok(Rel.relations(changes).length === 1);
const gauges = { title: 'Vodostaji', paragraphs: [{ text: 'Dunav kod Zemuna je na 166 cm, a Sava kod Beograda na 123 cm.', cites: ['L1', 'L2'] }], question: 'Kakav će biti sledeći podatak?', limitations: 'x' };
assert.ok(C.reasoningReasons(gauges, { facts: levels }).includes('incomparable_gauges'));
assert.equal(Rel.domain({ kind: 'historical_context' }), 'statistics');
assert.equal(Rel.domain(obs('X', 'S146|PM2.5', 1, '2026-09-16T05:00:00Z')), 'air');

// The published night entry is refused for every reason it deserved.
const n = C.reasoningReasons(nightText, night);
for (const r of ['unsupported_norm', 'invented_terrain', 'false_simultaneity', 'unrelated_question']) assert.ok(n.includes(r), r + ' ' + n);
// The published morning entry: invented slope and plain, a norm, and a question linking wind to parking.
const m = C.reasoningReasons(morningText, morning);
for (const r of ['invented_terrain', 'unsupported_norm', 'unrelated_question']) assert.ok(m.includes(r), r + ' ' + m);
assert.ok(!m.includes('unrelated_domains'), 'wind and NO2 in one paragraph are allowed');
// "brdo" is allowed where the place itself carries it.
assert.ok(!C.reasoningReasons({ title: 'Banovo brdo u zoru', paragraphs: [{ text: 'Na stanici Banovo brdo azot-dioksid je 24.83.', cites: ['F6'] }], question: 'Šta pokazuje sledeće očitavanje?', limitations: 'x' }, morning).includes('invented_terrain'));

// Two unrelated domains in one paragraph are refused; separately they are fine.
const mixed = { title: 'Dva odvojena očitavanja', paragraphs: [{ text: 'Parking ima 80 slobodnih mesta, a vetar je 0.', cites: ['F11', 'F3'] }], question: 'Šta pokazuje sledeće očitavanje?', limitations: 'x' };
assert.ok(C.reasoningReasons(mixed, morning).includes('unrelated_domains'));
const clean = {
  title: 'Tih vetar i azot-dioksid',
  paragraphs: [
    { text: 'U 06:00 UTC brzina vetra je 0, a na stanici Banovo brdo azot-dioksid je u 05:00 UTC 24.83. Slab vetar u načelu slabije raznosi zagađenje, ali ovi podaci ne pokazuju da se to baš sada desilo.', cites: ['F3', 'F6'] },
    { text: 'Odvojeno od toga, na parkiralištu kod opštine Novi Beograd u 08:10 UTC ima 80 slobodnih mesta; ovaj podatak ne povezujem sa vazduhom.', cites: ['F11'] },
  ],
  question: 'Da li će azot-dioksid ostati sličan kada vetar ojača?',
  limitations: 'Dva očitavanja nisu trend niti uzrok.',
};
assert.deepEqual(C.reasoningReasons(clean, morning), [], 'a careful text passes');
// Negated norms and patterns are honest, not claims.
assert.deepEqual(C.reasoningReasons({ ...clean, paragraphs: [{ text: 'Ne znam šta je ovde uobičajeno, a dva očitavanja nisu trend; vetar je 0.', cites: ['F3'] }] }, morning), []);
assert.ok(C.reasoningReasons({ ...clean, paragraphs: [{ text: 'Vidi se jasan dnevni ritam vetra koji je sada 0.', cites: ['F3'] }] }, morning).includes('premature_pattern'));
// Statistics never share a paragraph with live readings.
const stat = { facts: [...morning.facts, { kind: 'historical_context', id: 'F4', value: 715614, period: '2026-K2', place: 'Beogradska oblast' }] };
assert.ok(C.reasoningReasons({ ...clean, paragraphs: [{ text: 'U garaži je 80 mesta, a zaposlenih je 715614.', cites: ['F11', 'F4'] }] }, stat).includes('context_mixed_with_live'));
// validateOutput carries the new rules and version.
const v = C.validateOutput(nightText, { facts: night.facts });
assert.equal(v.version, 'citizen-v3');
assert.ok(!v.ok);

// Prompt v4 keeps v3 relation limits and adds only an optional grounded geo field.
const config = JSON.parse(fs.readFileSync(path.join(root, 'research/AI_FEED.json'), 'utf8'));
assert.equal(config.prompt_version, 4);
const activePrompt = fs.readFileSync(path.join(root, 'research/03-models/AI_FEED_SYSTEM_PROMPT_v4.txt'), 'utf8');
assert.ok(activePrompt.includes('relations') && !activePrompt.includes('MORA biti iz domena'));
assert.ok(activePrompt.includes('PROSTORNO SIDRO'));
const src = fs.readFileSync(path.join(root, 'tools/ai_feed_context.js'), 'utf8');
assert.ok(!src.includes('nula slobodnih mesta je redovna'), 'the context no longer asserts a parking norm');

// The context packet carries domains and relations.
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'beops-rel-'));
try {
  const w = (name, value) => { const p = path.join(tmp, name); fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, JSON.stringify(value)); };
  const now = new Date('2026-09-16T06:30:00Z');
  const pt = (v, t) => ({ v, t, rx: t, tu: false });
  w('research/SOURCE_REGISTRY.json', { sources: [{ id: 'S1', status: 'collected', url: 'https://example.org' }, { id: 'S146', status: 'collected', url: 'https://example.org' }, { id: 'S10', status: 'collected', url: 'https://example.org' }] });
  w('public/live-snapshot.json', { as_of: now.toISOString(), sources: [
    { sid: 'S1', name: 'RHMZ', cadence_seconds: 900, datastreams: [{ station: 'Beograd', datastream: 'Beograd|wind_speed', parameter: 'wind_speed', unit: 'm/s', lat: 44.80, lon: 20.47, points: [pt(0, '2026-09-16T06:00:00Z')] }] },
    { sid: 'S146', name: 'SEPA', cadence_seconds: 3600, datastreams: [{ station: 'Beograd Banovo brdo', datastream: 'X|NO2', parameter: 'NO2', unit: 'ug.m-3', lat: 44.78, lon: 20.41, points: [pt(24.83, '2026-09-16T05:00:00Z')] }] },
    { sid: 'S10', name: 'Parking', cadence_seconds: 900, datastreams: [{ station: 'Opština', datastream: 'P|free_spaces', parameter: 'free_spaces', unit: '1', points: [pt(80, '2026-09-16T06:10:00Z')] }] },
  ] });
  const packet = C.buildContext(tmp, now, {}, new Set(['S1', 'S146', 'S10']));
  assert.ok(packet.facts.every(f => typeof f.domain === 'string'));
  assert.ok(Array.isArray(packet.relations) && packet.relations.some(r => r.rule === 'wind_dispersion'));
  assert.ok(!packet.relations.some(r => r.facts.some(id => packet.facts.find(f => f.id === id).domain === 'parking')));

  // Re-review flags an old entry once, never edits it, and is idempotent.
  const ctx = C.hash(night);
  w('runtime/ai-feed/contexts/' + ctx + '.json', night);
  const entry = { schema: 'beops-ai-entry/v1', id: 'a'.repeat(32), at: '2026-09-16T03:06:00Z', context_hash: ctx, content: nightText };
  w('runtime/ai-feed/entries/' + entry.id + '.json', entry);
  w('research/AI_FEED_REVIEWS.json', { schema: 'beops-ai-reviews/v1', records: [] });
  const before = fs.readFileSync(path.join(tmp, 'runtime/ai-feed/entries', entry.id + '.json'), 'utf8');
  const first = revalidate(tmp, { write: true });
  assert.equal(first.added, 1);
  const ledger = JSON.parse(fs.readFileSync(path.join(tmp, 'research/AI_FEED_REVIEWS.json'), 'utf8'));
  assert.equal(ledger.records[0].entry_sha256, C.hash(JSON.parse(before)));
  assert.equal(ledger.records[0].status, 'quality_flag');
  assert.equal(revalidate(tmp, { write: true }).added, 0, 'a second run adds nothing');
  assert.equal(fs.readFileSync(path.join(tmp, 'runtime/ai-feed/entries', entry.id + '.json'), 'utf8'), before, 'entries are never rewritten');
} finally { fs.rmSync(tmp, { recursive: true, force: true }); }
console.log('relation contracts passed: allowed links, terrain, norms, patterns, simultaneity, statistics, prompt v3, context relations, re-review');
