'use strict';
/* Which model actually answers, and how fast - asked rather than assumed.
 *
 * On 2026-09-17/18 this observatory went nine hours without a single observation while
 * every scheduled task reported success. The organs were waiting on a local model daemon
 * that was not running, and the one CLI bridge that could have taken over had an expired
 * login. Neither state was hidden: nothing asked for it. This asks, and it writes down
 * what it heard.
 *
 *   node tools/ai_feed_probe.js           availability only - no model is called
 *   node tools/ai_feed_probe.js --live    one real round trip per available provider
 *
 * Availability is the Svemir CLI menu's own answer, so a probe costs nothing and can run
 * as often as wanted. A live probe spends one small request per provider and is the only
 * way to tell a route that is listed as ready from a route that actually replies.
 *
 * Every run appends one line to runtime/ai-feed/probe.jsonl, including a run that finds
 * nothing available - a probe that stays quiet when everything is down is the failure it
 * was written to catch. The process exit code is 0 while at least one provider is
 * available, 1 when none is, so a watcher can read it without parsing anything.
 */
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const CONFIG = path.join(ROOT, 'research', 'AI_FEED.json');
const LEDGER = path.join(ROOT, 'runtime', 'ai-feed', 'probe.jsonl');
const SCHEMA = 'beops-ai-probe/v1';

// Small enough to cost almost nothing, complete enough to exercise the whole path:
// the same context shape and the same answer shape the feed itself asks for.
const SYSTEM = 'Reply with one JSON object and nothing else: {"title":string,'
  + '"paragraphs":[{"text":string,"cites":["F1"]}],"question":string,"limitations":string}. '
  + 'Write in Serbian ekavica. Use only the fact given.';

function packetFor(now) {
  return {
    schema: 'beops-ai-context/v1',
    as_of: now.toISOString(),
    facts: [{ id: 'F1', value: 1, place: 'Beograd', unit: 'C', time: now.toISOString() }],
  };
}

async function probe(config, deps = {}) {
  const providers = deps.providers || require('./ai_feed_providers');
  const now = deps.now || new Date();
  const live = Boolean(deps.live);
  const directory = deps.cwd || path.join(ROOT, 'runtime', 'ai-feed', 'probe');
  const timeout = deps.timeoutMs || (config.job_timeout_seconds || 180) * 1000;
  const rows = [];

  for (const provider of config.providers || []) {
    const row = {
      id: provider.id, adapter: provider.adapter || null,
      bridge: provider.catalogue_bridge || null,
      ready: false, reason: null, model: null, route: null, live: null,
    };
    try {
      const seen = await providers.availability(provider, { state: deps.state || {}, now });
      row.ready = Boolean(seen.ready);
      row.reason = seen.reason || null;
      row.model = seen.model || null;
      row.route = seen.route_id || null;
    } catch (e) {
      row.reason = 'availability_threw_' + ((e && e.message) || 'unknown');
    }

    // A provider that is not available is never called. Its reason is the finding.
    if (live && row.ready) {
      const started = Date.now();
      try {
        fs.mkdirSync(directory, { recursive: true });
        const answer = await providers.generate(
          provider, row.model, packetFor(now), SYSTEM, directory, timeout);
        const text = String((answer && answer.text) || '');
        // An empty answer is not an answer. A route that returns nothing has not worked,
        // however cleanly it exited.
        row.live = {
          ok: text.trim().length > 0,
          ms: Date.now() - started,
          characters: text.length,
          model_reported: (answer && answer.model) || null,
          identity: (answer && answer.identity) || null,
          transport: (answer && answer.transport) || null,
          reason: text.trim().length ? null : 'empty_output',
        };
      } catch (e) {
        row.live = {
          ok: false, ms: Date.now() - started, characters: 0,
          model_reported: null, identity: null, transport: null,
          reason: (e && e.failureKind) || (e && e.message) || 'threw',
        };
      }
    }
    rows.push(row);
  }

  return {
    schema: SCHEMA, at: now.toISOString(), live,
    providers: rows,
    available: rows.filter(r => r.ready).map(r => r.id),
    answering: live ? rows.filter(r => r.live && r.live.ok).map(r => r.id) : null,
  };
}

function render(report) {
  const lines = [];
  for (const r of report.providers) {
    const parts = ['  ' + String(r.id).padEnd(10)
      + String(r.adapter || '-').padEnd(17)
      + (r.ready ? 'available' : 'unavailable').padEnd(13)
      + String(r.model || '-').padEnd(24)];
    if (!r.ready) parts.push('reason: ' + (r.reason || 'unstated'));
    if (r.live) {
      parts.push('answered: ' + (r.live.ok ? 'yes' : 'no') + '  ' + r.live.ms + ' ms'
        + (r.live.reason ? '  (' + r.live.reason + ')' : '')
        + (r.live.model_reported && r.live.model_reported !== r.model
          ? '  reported as ' + r.live.model_reported : ''));
    }
    lines.push(parts.join('   '));
  }
  lines.push('  ' + report.available.length + ' of ' + report.providers.length + ' available'
    + (report.live ? '; ' + report.answering.length + ' answered'
      : '; no model was called'));
  return lines.join('\n');
}

function append(report, file = LEDGER) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.appendFileSync(file, JSON.stringify(report) + '\n', 'utf8');
  return file;
}

if (require.main === module) {
  const live = process.argv.includes('--live');
  probe(JSON.parse(fs.readFileSync(CONFIG, 'utf8')), { live }).then(report => {
    console.log(render(report));
    const file = append(report);
    console.log('  written to ' + path.relative(ROOT, file).split(path.sep).join('/'));
    process.exitCode = report.providers.some(r => r.ready) ? 0 : 1;
  }).catch(e => {
    console.error('probe could not run: ' + ((e && e.message) || e));
    process.exitCode = 2;
  });
}

module.exports = { probe, render, append, SCHEMA, LEDGER, CONFIG };
