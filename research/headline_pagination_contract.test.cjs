'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const directory = path.join(__dirname, '05-design/studies');
const source = fs.readFileSync(path.join(directory, 'headlines.js'), 'utf8');
const html = fs.readFileSync(path.join(directory, 'naslovi.html'), 'utf8');
const ROW_HEIGHT = 160;

// Only DOM operations used by the actual page are implemented. Geometry models
// fixed-height rows so a refresh can be checked for reader-position movement.
function browser(rows) {
  const nodes = new Map();
  const document = {hidden: false, documentElement: {lang: 'sr'}};
  const window = {scrollY: 0, scrollBy(_x, y) { this.scrollY += y; }};
  class Element {
    constructor(tag, text = '') {
      this.tagName = tag.toUpperCase();
      this.children = [];
      this.parentElement = null;
      this.dataset = {};
      this.attributes = {};
      this.listeners = new Map();
      this.value = '';
      this._text = text;
      this.hidden = false;
      this.disabled = false;
      this.open = false;
    }
    set textContent(value) { this._text = String(value); this.children = []; }
    get textContent() { return this._text + this.children.map(e => e.textContent).join(''); }
    get firstElementChild() { return this.children[0] || null; }
    get options() { return this.children.filter(e => e.tagName === 'OPTION'); }
    append(...children) {
      for (const child of children) {
        if (child.tagName === '#FRAGMENT') {
          for (const nested of [...child.children]) this.append(nested);
          child.children = [];
          continue;
        }
        if (child.parentElement) {
          const siblings = child.parentElement.children;
          siblings.splice(siblings.indexOf(child), 1);
        }
        child.parentElement = this;
        this.children.push(child);
      }
    }
    replaceChildren(...children) {
      if (this.contains(document.activeElement)) document.activeElement = document.body;
      for (const child of this.children) child.parentElement = null;
      this.children = [];
      this._text = '';
      this.append(...children);
    }
    remove(index) {
      const [child] = this.children.splice(index, 1);
      if (child) child.parentElement = null;
    }
    contains(other) {
      for (let cursor = other; cursor; cursor = cursor.parentElement) {
        if (cursor === this) return true;
      }
      return false;
    }
    setAttribute(name, value) { this.attributes[name] = String(value); }
    addEventListener(name, callback) {
      if (!this.listeners.has(name)) this.listeners.set(name, []);
      this.listeners.get(name).push(callback);
    }
    querySelectorAll(selector) {
      const matches = element => selector === 'details[open]'
        ? element.tagName === 'DETAILS' && element.open
        : element.tagName === selector.toUpperCase();
      const found = [];
      const walk = element => {
        for (const child of element.children) {
          if (matches(child)) found.push(child);
          walk(child);
        }
      };
      walk(this);
      return found;
    }
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
    closest(selector) {
      assert.equal(selector, '#items article', 'unmodelled closest selector');
      for (let cursor = this; cursor; cursor = cursor.parentElement) {
        if (cursor.tagName === 'ARTICLE' && nodes.get('items').contains(cursor)) return cursor;
      }
      return null;
    }
    focus() { document.activeElement = this; }
    getBoundingClientRect() {
      let row = this;
      while (row && row.tagName !== 'ARTICLE') row = row.parentElement;
      const index = row ? nodes.get('items').children.indexOf(row) : 0;
      const top = index * ROW_HEIGHT - window.scrollY;
      return {top, bottom: top + ROW_HEIGHT};
    }
    scrollIntoView() {
      window.scrollY += this.getBoundingClientRect().top;
    }
  }
  document.body = new Element('body');
  document.activeElement = document.body;
  document.getElementById = id => {
    assert.ok(nodes.has(id), `The actual HTML must contain #${id}`);
    return nodes.get(id);
  };
  document.createElement = tag => new Element(tag);
  document.createTextNode = text => new Element('#text', text);
  document.createDocumentFragment = () => new Element('#fragment');
  for (const match of html.matchAll(/<([a-z][\w-]*)\b([^>]*)>/gi)) {
    const id = /\bid="([^"]+)"/.exec(match[2]);
    if (!id) continue;
    const element = new Element(match[1]);
    nodes.set(id[1], element);
    document.body.append(element);
  }
  assert.match(html, /<script\b[^>]*src="headlines\.js"/);
  nodes.get('source').append(new Element('option'));
  let archive = {rows, count: rows.length, as_of: '2026-09-27T00:00:00Z'};
  let interval;
  let requests = 0;
  const sandbox = {
    document, window, URL,
    fetch: async (url, options) => {
      assert.equal(url, 'headlines.json');
      assert.equal(options.cache, 'no-store');
      requests++;
      return {ok: true, json: async () => archive};
    },
    requestAnimationFrame: callback => queueMicrotask(() => callback(0)),
    setInterval: (callback, delay) => { assert.equal(delay, 60000); interval = callback; },
  };
  vm.runInNewContext(source, sandbox, {filename: 'headlines.js', timeout: 2000});
  const settle = async () => { await new Promise(setImmediate); };
  const click = async id => {
    const element = nodes.get(id);
    assert.ok(!element.disabled, `Cannot click disabled #${id}`);
    element.focus();
    await element.onclick();
    await settle();
  };
  const input = async (id, value) => {
    const element = nodes.get(id);
    element.value = value;
    element.focus();
    for (const listener of element.listeners.get('input') || []) listener({target: element});
    await settle();
  };
  return {
    nodes, document, window, click, input, settle,
    visible: () => nodes.get('items').children.map(e => e.dataset.id),
    async refresh(nextRows) {
      archive = {...archive, rows: nextRows, count: nextRows.length};
      interval();
      await settle();
    },
    requests: () => requests,
  };
}

function row(index, extra = {}) {
  return {
    id: `row-${index}`, sid: 'S1', source: 'Source One', title: `Headline ${index}`,
    link: `https://example.invalid/headline/${index}`,
    published: '2026-09-27T00:00:00Z', received: '2026-09-27T00:01:00Z',
    ...extra,
  };
}

async function main() {
  const rows = Array.from({length: 15016}, (_, index) => row(index));
  rows[14000] = row(14000, {title: 'Distinctive needle beyond the first page'});
  rows[14001] = row(14001, {sid: 'S2', source: 'Other source', published: '2026-09-26T12:00:00Z'});
  const page = browser(rows);
  await page.settle();
  assert.equal(page.requests(), 1);
  assert.equal(page.visible().length, 100, 'large archives must not create unbounded DOM rows');
  assert.equal(page.visible()[0], 'row-0');
  assert.equal(page.visible().at(-1), 'row-99');
  assert.equal(page.nodes.get('page-count').textContent, 'Stranica 1 / 151');
  assert.equal(page.nodes.get('previous').disabled, true);
  assert.equal(page.nodes.get('next').disabled, false);
  assert.match(page.nodes.get('status').textContent, /1–100 \/ 15016/);

  await page.click('next');
  assert.equal(page.visible()[0], 'row-100');
  assert.equal(page.visible().at(-1), 'row-199');
  await page.click('previous');
  assert.equal(page.visible()[0], 'row-0');
  await page.input('query', 'DISTINCTIVE NEEDLE');
  assert.deepEqual(page.visible(), ['row-14000'], 'search must reach the full archive');
  assert.equal(page.nodes.get('pages').hidden, true);
  assert.equal(page.nodes.get('previous').disabled, true);
  assert.equal(page.nodes.get('next').disabled, true);
  await page.click('reset');
  assert.equal(page.visible()[0], 'row-0');
  assert.equal(page.visible().length, 100);

  await page.input('source', 'S2');
  assert.deepEqual(page.visible(), ['row-14001']);
  await page.input('from', '2026-09-27');
  assert.deepEqual(page.visible(), [], 'source and date constraints combine');
  assert.match(page.nodes.get('status').textContent, /0–0 \/ 0/);
  assert.equal(page.nodes.get('page-count').textContent, 'Stranica 1 / 1');
  assert.equal(page.nodes.get('pages').hidden, true);
  assert.equal(page.nodes.get('next').disabled, true);
  assert.equal(page.nodes.get('previous').disabled, true);
  await page.click('reset');
  for (const id of ['query', 'source', 'from', 'to']) assert.equal(page.nodes.get(id).value, '');
  await page.click('next');
  await page.click('reset');
  assert.equal(page.nodes.get('page-count').textContent, 'Stranica 1 / 151', 'reset returns from a later page');

  await page.click('next');
  const oldArticle = page.nodes.get('items').children[49];
  oldArticle.querySelector('details').open = true;
  oldArticle.querySelector('summary').focus();
  page.window.scrollY = 49 * ROW_HEIGHT - 37;
  const oldTop = oldArticle.getBoundingClientRect().top;
  const updated = [row('new'), ...rows];
  await page.refresh(updated);
  assert.equal(page.visible().length, 100);
  assert.equal(page.nodes.get('page-count').textContent, 'Stranica 2 / 151');
  let focusedArticle = page.document.activeElement.closest('#items article');
  assert.equal(focusedArticle.dataset.id, 'row-149');
  assert.equal(page.document.activeElement.tagName, 'SUMMARY');
  assert.equal(focusedArticle.querySelector('details').open, true);
  assert.equal(focusedArticle.getBoundingClientRect().top, oldTop, 'refresh keeps the reader at the same screen position');
  assert.notEqual(focusedArticle, oldArticle, 'focus must survive replacement, not remain on a detached node');

  // The last visible row crosses onto the next page when a new row is prepended.
  const boundary = page.nodes.get('items').children.at(-1);
  const boundaryId = boundary.dataset.id;
  boundary.querySelector('details').open = true;
  boundary.querySelector('a').focus();
  page.window.scrollY = 99 * ROW_HEIGHT - 21;
  await page.refresh([row('newer'), ...updated]);
  focusedArticle = page.document.activeElement.closest('#items article');
  assert.equal(focusedArticle.dataset.id, boundaryId);
  assert.equal(page.document.activeElement.tagName, 'A');
  assert.equal(focusedArticle.querySelector('details').open, true);
  assert.equal(focusedArticle.getBoundingClientRect().top, 21);
  assert.equal(page.nodes.get('page-count').textContent, 'Stranica 3 / 151');

  const tail = browser(rows.slice(0, 216));
  await tail.settle();
  await tail.click('next');
  await tail.click('next');
  assert.deepEqual(tail.visible(), rows.slice(200, 216).map(r => r.id));
  assert.equal(tail.nodes.get('next').disabled, true);
  assert.equal(tail.nodes.get('previous').disabled, false);
  assert.match(tail.nodes.get('status').textContent, /201–216 \/ 216/);
  await tail.input('query', 'no such headline anywhere');
  assert.deepEqual(tail.visible(), []);
  assert.equal(tail.nodes.get('page-count').textContent, 'Stranica 1 / 1');
  const empty = browser([]);
  await empty.settle();
  assert.deepEqual(empty.visible(), []);
  assert.match(empty.nodes.get('status').textContent, /0–0 \/ 0/);
  assert.equal(empty.nodes.get('items').attributes['aria-busy'], 'false');
  console.log('Headline archive: 15,016-row bound, navigation, full search, filters, reset, empty/last pages and refresh reader preservation passed.');
}
main().catch(error => {console.error(error); process.exitCode = 1;});
