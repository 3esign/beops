'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

function stable(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return '[' + value.map(stable).join(',') + ']';
  return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + stable(value[k])).join(',') + '}';
}
const digest = value => crypto.createHash('sha256').update(typeof value === 'string' || Buffer.isBuffer(value) ? value : stable(value)).digest('hex');
function check(condition, reason) { if (!condition) throw new Error(reason); }
function timestamp(value, nullable = true) {
  check((nullable && value === null) || (typeof value === 'string' &&
    /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(value) &&
    Number.isFinite(Date.parse(value))), 'timezone-qualified timestamp required');
}
function safeFile(root, relative) {
  check(typeof relative === 'string' && relative.length > 0 && !path.isAbsolute(relative), 'relative path required');
  check(!relative.split(/[\\/]/).some(p => p.startsWith('.env') || /^secrets(?:\.|$)/i.test(p)), 'secret path denied');
  const base = fs.realpathSync(root), target = path.resolve(base, relative);
  const inside = p => { const r = path.relative(base, p); return r !== '..' && !r.startsWith('..' + path.sep) && !path.isAbsolute(r); };
  check(inside(target), 'path escapes project');
  // Resolve existing ancestors as well: a junction cannot redirect a future write outside root.
  let parent = target;
  while (!fs.existsSync(parent)) { const next = path.dirname(parent); check(next !== parent, 'missing root'); parent = next; }
  check(inside(fs.realpathSync(parent)), 'link escapes project');
  return target;
}
function readBounded(root, relative, maxBytes = 8 * 1024 * 1024) {
  const file = safeFile(root, relative), fd = fs.openSync(file, 'r');
  try {
    const stat = fs.fstatSync(fd);
    check(stat.isFile() && stat.size <= maxBytes, 'input byte budget exceeded: ' + relative);
    const buffer = Buffer.alloc(stat.size + 1);
    let count = 0, n;
    while ((n = fs.readSync(fd, buffer, count, buffer.length - count, null)) > 0) { count += n; if (count === buffer.length) break; }
    check(count === stat.size, 'input changed during read: ' + relative);
    return buffer.subarray(0, count);
  } finally { fs.closeSync(fd); }
}
const readJSON = (root, ref) => JSON.parse(readBounded(root, ref).toString('utf8'));
function immutableJSON(root, relative, value) {
  const file = safeFile(root, relative), bytes = JSON.stringify(value, null, 2) + '\n';
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temp = file + '.' + crypto.randomUUID() + '.tmp';
  const fd = fs.openSync(temp, 'wx');
  try { fs.writeFileSync(fd, bytes); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
  try { fs.linkSync(temp, file); } finally { fs.unlinkSync(temp); }
  check(fs.readFileSync(file, 'utf8') === bytes, 'write verification failed');
  return { ref: relative.replaceAll('\\', '/'), sha256: digest(bytes), bytes: Buffer.byteLength(bytes) };
}
function validateEvent(e) {
  check(e.schema === 'beops-event/v1', 'invalid event schema');
  check(['observation','notice','forecast','estimate','failure','correction','document'].includes(e.kind), 'invalid kind');
  for (const k of ['source_id','source_revision','entity_id','domain','evidence_ref','evidence_sha256','shared_origin_group']) check(typeof e[k] === 'string' && e[k].length > 0, 'missing ' + k);
  check(/^[a-f0-9]{64}$/.test(e.evidence_sha256), 'invalid evidence hash');
  timestamp(e.ingested_at, false); timestamp(e.observed_at); timestamp(e.published_at);
  timestamp(e.valid_interval.from); timestamp(e.valid_interval.to);
  if (e.valid_interval.from && e.valid_interval.to) check(Date.parse(e.valid_interval.from) <= Date.parse(e.valid_interval.to), 'reversed interval');
  check(Array.isArray(e.spatial.zones) && e.spatial.zones.every(x => typeof x === 'string'), 'invalid zones');
  check(['unresolved','source','reviewed_external'].includes(e.spatial.method), 'invalid spatial method');
  check(e.spatial.zones.length === 0 || (e.spatial.method !== 'unresolved' && typeof e.spatial.evidence_ref === 'string'), 'zone needs evidence');
  check(e.measurement.value === null || (typeof e.measurement.value === 'number' && Number.isFinite(e.measurement.value)), 'numeric value or null required');
  check(e.quality.source_time_known === (e.observed_at !== null), 'source time flag mismatch');
  if (e.kind === 'observation') {
    check(typeof e.measurement.unit === 'string' && typeof e.measurement.property === 'string', 'observation unit/property missing');
    check(e.quality.missing === (e.measurement.value === null), 'missing is not zero');
  }
  if (e.kind === 'forecast') check(e.published_at !== null && e.valid_interval.from !== null, 'forecast issue and horizon required');
  check(Array.isArray(e.derived_from), 'provenance list required');
  if (['estimate','correction'].includes(e.kind)) check(e.derived_from.length > 0, 'derived event needs cause');
  check(['UNKNOWN','RESEARCH-ONLY','PUBLIC-FACTS','EXCLUDED'].includes(e.publication_status), 'publication decision invalid');
  const { event_id, ...payload } = e;
  check(event_id === digest(payload), 'event identity does not match content');
  return e;
}
function event(fields) {
  const payload = { schema: 'beops-event/v1', observed_at: null, published_at: null,
    valid_interval: { from: null, to: null }, spatial: { external_ref: null, zones: [], method: 'unresolved', evidence_ref: null },
    measurement: { property: null, value: null, unit: null }, quality: { missing: false, source_time_known: false, stale: null },
    derived_from: [], model: null, publication_status: 'UNKNOWN', ...fields };
  return validateEvent({ ...payload, event_id: digest(payload) });
}
function dedup(events) {
  const unique = new Map();
  for (const e of events) { validateEvent(e); unique.set(e.event_id, e); }
  return [...unique.values()].sort((a,b) => a.ingested_at.localeCompare(b.ingested_at) || a.event_id.localeCompare(b.event_id));
}
function freshness(e, now, maxAgeMs) {
  timestamp(now, false); check(Number.isFinite(maxAgeMs) && maxAgeMs >= 0, 'invalid freshness budget');
  if (!e.observed_at) return 'unknown';
  const age = Date.parse(now) - Date.parse(e.observed_at);
  return age < 0 ? 'clock_error' : age > maxAgeMs ? 'stale' : 'fresh';
}
function publicationDecision(e, rights) {
  const reasons = [];
  if (e.publication_status !== 'PUBLIC-FACTS') reasons.push('event_not_approved');
  if (!rights || rights.source_id !== e.source_id || rights.source_revision !== e.source_revision) reasons.push('rights_scope_mismatch');
  for (const key of ['automated_access','storage','processing','derived_publication','research_reproduction']) {
    if (rights?.permissions?.[key] !== 'allowed') reasons.push(key + '_not_allowed');
  }
  if (!rights?.reviewer || !rights?.evidence_ref || !rights?.checked_at || !rights?.attribution) reasons.push('review_incomplete');
  if (rights?.personal_data_review !== 'passed') reasons.push('privacy_not_reviewed');
  if (!rights?.event_ids?.includes(e.event_id)) reasons.push('output_not_reviewed');
  return { allowed: reasons.length === 0, reasons };
}
module.exports = { check, stable, digest, timestamp, safeFile, readBounded, readJSON, immutableJSON, validateEvent, event, dedup, freshness, publicationDecision };
