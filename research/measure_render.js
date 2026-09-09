// measure_render.js - measure the built site at real widths, in a real browser.
//
//   node research/measure_render.js [baseUrl]        default http://127.0.0.1:8099
//
// The offline suite (research/test_render.py) reads the artefact as text and catches the rules that
// produce layout defects. It cannot catch a defect that only exists at a width, because it does not
// lay anything out. This does: it opens the page at five widths, measures each embedded frame and the
// pulse canvas, and fails if a frame runs away, if a canvas box and its bitmap disagree, or if the
// page scrolls sideways. It needs a browser and is therefore NOT part of `npm test`, which this
// project keeps free of dependencies - it is run by hand before a release, and its numbers are what
// C-016 records.
//
// Serve the docs folder first:  python -m http.server 8099 --directory docs
const { chromium } = require('playwright');
const BASE = process.argv[2] || 'http://127.0.0.1:8099';
const WIDTHS = [1280, 900, 760, 412, 360];
const MAX_FRAME = 20000;      // a frame taller than this is a runaway, not a long page

(async () => {
  const b = await chromium.launch();
  let bad = 0;
  for (const w of WIDTHS) {
    const p = await b.newPage({ viewport: { width: w, height: 915 }, isMobile: w < 600, hasTouch: w < 600 });
    const errs = [];
    p.on('pageerror', e => errs.push(String(e).slice(0, 160)));
    await p.goto(BASE + '/index.html', { waitUntil: 'networkidle', timeout: 60000 });
    await p.waitForTimeout(4000);
    const r = await p.evaluate(() => {
      const out = { docW: document.documentElement.scrollWidth, win: innerWidth, frames: [] };
      for (const f of document.querySelectorAll('iframe')) {
        const d = f.contentDocument, c = d && d.querySelector('canvas');
        out.frames.push({
          src: f.getAttribute('src').split('?')[0],
          h: Math.round(f.getBoundingClientRect().height),
          text: d ? (d.body.innerText || '').trim().length : 0,
          canvasBox: c ? Math.round(c.getBoundingClientRect().height) : null,
          canvasBitmap: c ? Math.round(c.height / (devicePixelRatio || 1)) : null,
        });
      }
      return out;
    });
    const say = [];
    if (r.docW > r.win + 2) { say.push('page scrolls sideways (' + r.docW + ' > ' + r.win + ')'); }
    for (const f of r.frames) {
      if (f.h > MAX_FRAME) say.push(f.src + ' frame ' + f.h + 'px - runaway');
      if (f.text < 200) say.push(f.src + ' has almost no text (' + f.text + ' chars) - did it load?');
      if (f.canvasBox !== null && Math.abs(f.canvasBox - f.canvasBitmap) > 2)
        say.push(f.src + ' canvas box ' + f.canvasBox + 'px but bitmap ' + f.canvasBitmap + 'px - the drawing is clipped');
    }
    errs.forEach(e => say.push('page error: ' + e));
    console.log(String(w).padStart(5) + '  ' + r.frames.map(f => f.src.replace('.html', '') + '=' + f.h +
      (f.canvasBox !== null ? '/cv' + f.canvasBox : '')).join('  ') + (say.length ? '\n       ! ' + say.join('\n       ! ') : ''));
    bad += say.length;
    await p.close();
  }
  await b.close();
  console.log(bad ? '\n' + bad + ' problem(s)' : '\nclean at every width');
  process.exit(bad ? 1 : 0);
})();
