'use strict';
/**
 * svemir_model_bridge.js - routes Beops organ model requests to Svemir CLI bridge.
 * Zero-dependency bridge using Node.js stdlib and Svemir's existing CLI infrastructure.
 */
const path = require('node:path');
const svemirRoot = process.env.BEOPS_SVEMIR_ROOT || 'C:/Svemir';
const bridge = require(path.join(svemirRoot, 'lib', 'cli_bridge.js'));

const REMOTE_MODEL_MARKERS = [
  ':cloud', '-cloud', 'cloud:',
  'claude', 'sonnet', 'opus', 'haiku',
  'gemini', 'flash', 'antigravity',
  'codex', 'openai', 'gpt-'
];

function normalizeModelName(name) {
  return String(name || '')
    .trim()
    .replace(/^cli:/i, '')
    .replace(/^pc-llama-/i, '')
    .toLowerCase();
}

function modelKey(name) {
  return normalizeModelName(name).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function isRemoteName(name) {
  const normalized = normalizeModelName(name);
  return REMOTE_MODEL_MARKERS.some(marker => normalized.includes(marker));
}

function localModels() {
  const rows = bridge.chatModels({ includeUnavailable: false, includeAuto: false }) || [];
  return rows
    .filter(m => m && m.bridge === 'llama' && m.model && m.model !== 'auto' && m.runnable !== false)
    .map(m => ({
      name: m.model,
      id: m.id,
      bridge: 'llama',
      backend: 'svemir-cli',
      capabilities: { chat: true, structured_output: true, embedding: false }
    }));
}

function findLocalModel(name) {
  if (!name || isRemoteName(name)) return null;
  const normalized = modelKey(name);
  return localModels().find(m => {
    const names = [m.name, m.id, 'pc-llama-' + m.name].map(modelKey);
    return names.includes(normalized);
  }) || null;
}

async function getTags() {
  return { models: localModels() };
}

async function doChat(req) {
  const model = req.model || 'auto';
  const found = findLocalModel(model);
  if (!found) {
    throw new Error(`local model is unavailable or not permitted: ${model}`);
  }
  const messages = req.messages || [];
  let system = '';
  let prompt = '';
  for (const m of messages) {
    if (m.role === 'system') system += (system ? '\n' : '') + m.content;
    else if (m.role === 'user') prompt += (prompt ? '\n' : '') + m.content;
  }
  if (!prompt && messages.length) {
    prompt = messages[messages.length - 1].content || '';
  }

  let fullPrompt = prompt;
  if (req.format) {
    fullPrompt += '\n\nIMPORTANT: You must respond with ONLY a single valid JSON object matching the requested schema. No markdown wrapping (do not use ```json), no conversation, no thoughts or explanations outside the JSON.';
  }
  if (system) {
    fullPrompt = `[System Instructions]\n${system}\n\n[Input]\n${fullPrompt}`;
  }

  const bridgeName = 'llama';
  const targetModel = found.name;

  if (req.options && req.options.num_predict) {
    process.env.LLAMA_PREDICT = String(req.options.num_predict);
  } else {
    process.env.LLAMA_PREDICT = '800';
  }
  if (req.options && req.options.num_ctx) {
    process.env.LLAMA_CTX = String(req.options.num_ctx);
  }

  const timeoutMs = Math.max(1, Number(req.timeout || 210)) * 1000;

  let result;
  try {
    result = await bridge.runLocal({
      bridge: bridgeName,
      model: targetModel,
      prompt: fullPrompt,
      timeoutMs
    });
  } catch (err) {
    result = { ok: false, err: err.message };
  }

  if (!result || !result.ok) {
    const errorMsg = (result && (result.err || result.out)) || 'CLI bridge execution failed';
    throw new Error(errorMsg);
  }

  let text = '';
  const lines = String(result.out || '').trim().split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try {
      const parsed = JSON.parse(trimmed);
      if (parsed.status === 'COMPLETED' && parsed.response !== undefined) {
        text = String(parsed.response);
      } else if (parsed.status && parsed.status !== 'COMPLETED') {
        const err = new Error(parsed.error || parsed.status);
        err.bridgeStatus = true;
        throw err;
      }
    } catch (err) {
      if (err && err.bridgeStatus) throw err;
    }
  }
  if (!text) {
    text = String(result.out || '').trim();
  }
  text = text.replace(/^assistant:?\s*/i, '').replace(/\[end of text\]\s*$/i, '').trim();
  if (text.startsWith('```')) {
    text = text.replace(/^```(?:json)?\s*/, '').replace(/\s*```$/, '').trim();
  }

  if (req.format || fullPrompt.includes('JSON')) {
    const firstBrace = text.indexOf('{');
    const lastBrace = text.lastIndexOf('}');
    if (firstBrace !== -1 && lastBrace > firstBrace) {
      const candidate = text.substring(firstBrace, lastBrace + 1);
      try {
        JSON.parse(candidate);
        text = candidate;
      } catch {}
    }
  }

  return {
    requested_model: model,
    model: targetModel,
    backend: 'svemir-cli',
    done: true,
    done_reason: 'stop',
    message: {
      role: 'assistant',
      content: text
    }
  };
}

async function main() {
  const cmd = process.argv[2] || 'tags';
  if (cmd === 'tags') {
    const res = await getTags();
    process.stdout.write(JSON.stringify(res) + '\n');
    return;
  }
  if (cmd === 'show') {
    const found = findLocalModel(process.argv[3]);
    if (!found) throw new Error(`local model is unavailable or not permitted: ${process.argv[3] || ''}`);
    process.stdout.write(JSON.stringify(found) + '\n');
    return;
  }
  if (cmd === 'embed') {
    throw new Error('embedding is not supported by the Svemir CLI bridge');
  }
  if (cmd === 'chat') {
    let input = '';
    for await (const chunk of process.stdin) input += chunk;
    const req = JSON.parse(input.replace(/^\uFEFF/, '').trim() || '{}');
    const res = await doChat(req);
    process.stdout.write(JSON.stringify(res) + '\n');
    return;
  }
  throw new Error('Unknown command: ' + cmd);
}

main().catch(err => {
  process.stderr.write((err.stack || err.message) + '\n');
  process.exit(1);
});
