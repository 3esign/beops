'use strict';
/* The probe exists because nothing asked whether a model could answer. These are the
 * properties that make its answer worth reading: it never calls an unavailable route, it
 * never counts an empty reply as a reply, it never drops a provider from the report, and
 * it writes a line even when everything is down. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const probeTool = require('../tools/ai_feed_probe');

const now = new Date('2026-09-18T06:00:00Z');
const config = {
  job_timeout_seconds: 5,
  providers: [
    { id: 'up', adapter: 'antigravity-cli', catalogue_bridge: 'antigravity' },
    { id: 'down', adapter: 'claude-cli', catalogue_bridge: 'claude' },
    { id: 'empty', adapter: 'claude-cli', catalogue_bridge: 'claude' },
    { id: 'broken', adapter: 'ollama' },
  ],
};

function fake(calls) {
  return {
    async availability(provider) {
      if (provider.id === 'down') return { ready: false, reason: 'degraded' };
      if (provider.id === 'broken') throw new Error('catalogue_gone');
      return { ready: true, model: provider.id + '-model', route_id: 'pc-' + provider.id };
    },
    async generate(provider, model) {
      calls.push(provider.id);
      if (provider.id === 'empty') return { text: '   \n ', model, identity: 'requested_alias' };
      return { text: '{"title":"t"}', model: 'reported-' + model, identity: 'provider_reported',
        transport: 'test' };
    },
  };
}

async function main() {
  const quiet = await probeTool.probe(config, { providers: fake([]), now });
  assert.equal(quiet.providers.length, config.providers.length,
    'every configured provider must appear, including the ones that failed');
  assert.deepEqual(quiet.providers.map(r => r.id), ['up', 'down', 'empty', 'broken']);
  assert.equal(quiet.live, false);
  assert.equal(quiet.answering, null, 'nothing answered because nothing was asked');
  assert.deepEqual(quiet.available, ['up', 'empty']);
  assert.equal(quiet.providers.every(r => r.live === null), true,
    'the default probe must not call a model');
  assert.equal(quiet.providers.find(r => r.id === 'down').reason, 'degraded',
    'an unavailable route reports the menu\'s own reason');
  assert.match(quiet.providers.find(r => r.id === 'broken').reason, /^availability_threw_/,
    'a catalogue that throws is a finding, not a silence');

  const calls = [];
  const live = await probeTool.probe(config, { providers: fake(calls), now, live: true });
  assert.deepEqual(calls, ['up', 'empty'], 'an unavailable route is never called');
  assert.equal(live.providers.find(r => r.id === 'up').live.ok, true);
  assert.equal(live.providers.find(r => r.id === 'up').live.model_reported, 'reported-up-model',
    'what the provider says it is stays beside what was requested');
  const blank = live.providers.find(r => r.id === 'empty').live;
  assert.equal(blank.ok, false, 'an empty answer is not an answer');
  assert.equal(blank.reason, 'empty_output');
  assert.deepEqual(live.answering, ['up']);
  assert.equal(typeof live.providers.find(r => r.id === 'up').live.ms, 'number');

  const nobody = await probeTool.probe({ providers: [{ id: 'down', adapter: 'claude-cli' }] },
    { providers: fake([]), now, live: true });
  assert.deepEqual(nobody.available, []);
  assert.deepEqual(nobody.answering, []);

  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'beops-probe-test-'));
  const ledger = path.join(directory, 'probe.jsonl');
  probeTool.append(nobody, ledger);
  probeTool.append(quiet, ledger);
  const written = fs.readFileSync(ledger, 'utf8').trim().split('\n');
  assert.equal(written.length, 2, 'a run that found nothing still leaves a line');
  assert.equal(JSON.parse(written[0]).schema, probeTool.SCHEMA);
  assert.deepEqual(JSON.parse(written[1]).available, ['up', 'empty']);
  fs.rmSync(directory, { recursive: true, force: true });

  const drawn = probeTool.render(live);
  assert.match(drawn, /down .*unavailable.*reason: degraded/,
    'the table says why, not only that');
  assert.match(drawn, /empty_output/);
  assert.match(drawn, /2 of 4 available; 1 answered/);

  console.log('probe contracts passed');
}

main().catch(e => { console.error(e); process.exit(1); });
