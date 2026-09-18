'use strict';
/**
 * svemir_model_bridge.js - routes Beops organ model requests to Svemir CLI bridge.
 * Zero-dependency bridge using Node.js stdlib and Svemir's existing CLI infrastructure.
 */
const path = require('node:path');
const svemirRoot = process.env.BEOPS_SVEMIR_ROOT || 'C:/Svemir';
const bridge = require(path.join(svemirRoot, 'lib', 'cli_bridge.js'));

async function getTags() {
  try {
    const models = bridge.chatModels({ includeUnavailable: false, includeAuto: false });
    const list = models.map(m => ({
      name: m.model || m.id,
      id: m.id,
      bridge: m.bridge
    }));
    if (!list.some(m => m.name.includes('gemini') || m.name.includes('flash'))) {
      list.unshift({ name: 'gemini-3.8-flash-high', id: 'antigravity:gemini-3.8-flash-high', bridge: 'antigravity' });
    }
    const preferredAliases = ['qwen2.5:1.5b', 'qwen3.5:4b', 'qwen2.5:3b', 'llama3.2:1b'];
    for (const alias of preferredAliases) {
      if (!list.some(m => m.name === alias)) {
        list.push({ name: alias, id: 'cli:' + alias, bridge: 'cli' });
      }
    }
    return { models: list };
  } catch (e) {
    return {
      models: [
        { name: 'gemini-3.8-flash-high' },
        { name: 'haiku' },
        { name: 'sonnet' },
        { name: 'qwen2.5:1.5b' },
        { name: 'qwen3.5:4b' }
      ]
    };
  }
}

async function doChat(req) {
  const model = req.model || 'auto';
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

  let bridgeName = 'antigravity';
  let targetModel = 'gemini-3.8-flash-high';
  if (model.includes('claude') || model === 'haiku' || model === 'sonnet' || model === 'opus') {
    bridgeName = 'claude';
    targetModel = model.replace(/^claude:/, '');
  } else if (model.includes('gemini')) {
    bridgeName = 'antigravity';
    targetModel = model;
  }

  const timeoutMs = Math.min((req.timeout || 120) * 1000, 120000);

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
    if (bridgeName !== 'antigravity') {
      try {
        result = await bridge.runLocal({
          bridge: 'antigravity',
          model: 'gemini-3.8-flash-high',
          prompt: fullPrompt,
          timeoutMs
        });
        targetModel = 'gemini-3.8-flash-high';
      } catch (err) {
        result = { ok: false, err: err.message };
      }
    }
  }

  if (!result || !result.ok) {
    const errorMsg = (result && (result.err || result.out)) || 'CLI bridge execution failed';
    throw new Error(errorMsg);
  }

  let text = String(result.out || '').trim();
  if (text.startsWith('```')) {
    text = text.replace(/^```(?:json)?\s*/, '').replace(/\s*```$/, '').trim();
  }

  return {
    model: targetModel,
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
    process.stdout.write(JSON.stringify({ model: process.argv[3] || 'gemini-3.8-flash-high' }) + '\n');
    return;
  }
  if (cmd === 'embed') {
    process.stdout.write(JSON.stringify({ embeddings: [] }) + '\n');
    return;
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
