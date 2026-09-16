'use strict';
// Re-reads every accepted AI observation against the citizen-v3 reasoning rules and records a
// public quality flag for each one that would now be refused. Entries are never edited or removed:
// the flag sits beside the original in research/AI_FEED_REVIEWS.json (C-074).
//   node tools/ai_feed_revalidate.js            dry run: counts and reasons
//   node tools/ai_feed_revalidate.js --write    append the missing flags
const fs = require('node:fs');
const path = require('node:path');
const { reasoningReasons, readJSON, hash } = require('./ai_feed_context');

const WORDS = {
  unrelated_domains: ['povezuje činjenice iz različitih oblasti bez poznate veze', 'connects facts from different domains that have no known link'],
  unrelated_question: ['pitanje nagoveštava vezu koju podaci ne podržavaju', 'the question implies a link the data do not support'],
  context_mixed_with_live: ['meša statistiku ili broj stanovnika sa živim očitavanjima', 'mixes statistics or population with live readings'],
  false_simultaneity: ['naziva istovremenim očitavanja udaljena više od sat vremena', 'calls readings more than an hour apart simultaneous'],
  invented_terrain: ['opisuje teren koji nije u podacima', 'describes terrain that is not in the data'],
  unsupported_norm: ['tvrdi šta je uobičajeno bez osnovne linije', 'claims what is usual without a baseline'],
  premature_pattern: ['tvrdi obrazac ili trend pre dovoljno duge istorije', 'claims a pattern or trend before the history is long enough'],
};

function revalidate(root, { write = false, now = new Date() } = {}) {
  const dir = path.join(root, 'runtime/ai-feed');
  const entriesDir = path.join(dir, 'entries');
  const ledgerPath = path.join(root, 'research/AI_FEED_REVIEWS.json');
  const ledger = fs.existsSync(ledgerPath) ? readJSON(ledgerPath, 4 * 1024 * 1024) : { schema: 'beops-ai-reviews/v1', records: [] };
  const flagged = new Set(ledger.records.map(r => r.entry_id));
  const report = { written: write, checked: 0, would_refuse: 0, already_flagged: 0, added: 0, reasons: {}, entries: [] };
  const names = fs.existsSync(entriesDir) ? fs.readdirSync(entriesDir).filter(n => /^[a-f0-9]{32}\.json$/.test(n)).sort() : [];
  for (const name of names) {
    const entry = readJSON(path.join(entriesDir, name), 65536);
    const packet = readJSON(path.join(dir, 'contexts', entry.context_hash + '.json'), 65536);
    report.checked++;
    const reasons = reasoningReasons(entry.content || {}, packet);
    if (!reasons.length) continue;
    report.would_refuse++;
    for (const r of reasons) report.reasons[r] = (report.reasons[r] || 0) + 1;
    report.entries.push({ id: entry.id, at: entry.at, title: entry.content && entry.content.title, reasons });
    if (flagged.has(entry.id)) { report.already_flagged++; continue; }
    ledger.records.push({
      entry_id: entry.id,
      entry_sha256: hash(entry),
      reviewed_at: now.toISOString(),
      status: 'quality_flag',
      reviewer: 'BEOPS validator citizen-v3 (automatic re-review)',
      reason_sr: 'Naknadna provera pravilima citizen-v3: tekst ' + reasons.map(r => WORDS[r][0]).join('; ') + '. Original je sačuvan radi istraživačkog traga.',
      reason_en: 'Later check against the citizen-v3 rules: the text ' + reasons.map(r => WORDS[r][1]).join('; ') + '. The original is retained as part of the research record.',
      reference: 'C-074',
      codes: reasons,
    });
    flagged.add(entry.id);
    report.added++;
  }
  if (write && report.added) {
    const tmp = ledgerPath + '.' + process.pid + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(ledger, null, 2) + '\n');
    fs.renameSync(tmp, ledgerPath);
  }
  return report;
}

module.exports = { revalidate, WORDS };
if (require.main === module) {
  const report = revalidate(path.resolve(__dirname, '..'), { write: process.argv.includes('--write') });
  console.log(JSON.stringify(report, null, 1));
}
