/* BEOPS v2 naslovna.js — „Grad u jednom pogledu" (koncept U1+U2+U10, v1).
   Eksperimentalna naslovna iza zastavice ?naslovna=2 — bez zastavice modul
   ne radi ništa, živi sajt ostaje netaknut. Sve se crta iz postojećih malih
   JSON ugovora (puls, mapa-lite, organizam.kvorum, serije/*) — nula novih
   izvora. Bez innerHTML (el + createElementNS); rAF gard umesto petlje
   (pouka iz glas.js); idempotentno (obrazac veceras.js). Tekstovi su
   lokalni STR dok se ne usvoji (F-D) — onda idu u strings.js sr+en. */
'use strict';
(function () {
  const q = new URLSearchParams(location.search);
  if (q.get('naslovna') !== '2') return; // zastavica

  const STR = {
    naslov: 'Grad u jednom pogledu',
    sada: 'Sada',
    vazduh: 'Vazduh',
    meteo: 'Vreme',
    klase: { 1: 'Vrlo dobar', 2: 'Dobar', 3: 'Umeren', 4: 'Loš', 5: 'Vrlo loš', 6: 'Ekstremno loš' },
    savet: 'Savet',
    stanica: 'stanica',
    mapa: 'Grad na mapi',
    legendaStanja: { observed: 'izmereno', estimated: 'procenjeno', untimed: 'bez sata', unavailable: 'nema podatka' },
    kvorum: 'Koliko grada javlja (prozor 60 min)',
    napomena: 'Eksperimentalni pregled (?naslovna=2). Podrazumevana naslovna ostaje kao i do sada; brojevi nose vreme merenja, ne prognozu.',
    izvor: 'izvor',
    nema: 'Podatak još ne postoji — pišemo to umesto prazne slike.',
    grRef: 'WHO-ova granica',
    grRs: 'RS/EU granica'
  };
  const EEA = { 1: '#50f0e6', 2: '#50ccaa', 3: '#f0e641', 4: '#ff5050', 5: '#960032', 6: '#7d2181' };

  let data = { puls: null, lite: null, kvorum: null, serije: {} };
  let raf = 0, mu = null, stil = false;

  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function sv(tag, attrs) { const n = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const k in attrs) n.setAttribute(k, attrs[k]); return n; }

  function stilovi() {
    if (stil) return; stil = true;
    const s = el('style'); s.setAttribute('data-beops', 'naslovna-v2');
    s.textContent =
      '.naslovna-v2{max-width:760px;margin:0 auto;padding:12px}' +
      '.naslovna-v2 h2{font-size:1.05rem;margin:2px 0 8px}' +
      '.nv-hero{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}' +
      '.nv-tile{border:1px solid #ddd;border-radius:10px;padding:10px;background:#fff}' +
      '.nv-tile .nv-num{font-size:1.7rem;font-weight:700;line-height:1.15}' +
      '.nv-tile .nv-unit{font-size:.75rem;font-weight:400;color:#555;margin-left:4px}' +
      '.nv-tile .nv-lbl{font-size:.78rem;color:#444;margin-top:2px}' +
      '.nv-tile .nv-ref{font-size:.72rem;color:#666;margin-top:6px}' +
      '.nv-tile .nv-ref i{display:inline-block;width:10px;height:2px;vertical-align:middle;margin-right:4px;background:#666}' +
      '.nv-city{margin-top:8px;padding:10px;border-radius:10px;color:#111;font-size:.9rem}' +
      '.nv-city b{font-size:1rem}' +
      '.nv-map{border:1px solid #ddd;border-radius:10px;background:#fff;padding:8px;margin-top:10px}' +
      '.nv-map svg{width:100%;height:auto;display:block}' +
      '.nv-legend{display:flex;flex-wrap:wrap;gap:10px;font-size:.72rem;color:#444;margin-top:6px}' +
      '.nv-legend .k{display:inline-flex;align-items:center;gap:4px}' +
      '.nv-legend .tocka{width:8px;height:8px;border-radius:50%;display:inline-block}' +
      '.nv-kvorum{margin-top:10px;font-size:.8rem}' +
      '.nv-kvorum .bar{height:8px;border-radius:6px;background:#e6e6e6;overflow:hidden;display:inline-block;width:90px;vertical-align:middle}' +
      '.nv-kvorum .bar i{display:block;height:100%}' +
      '.nv-kvorum .dom{display:flex;align-items:center;gap:8px;margin-top:4px}' +
      '.nv-kvorum .dom span:first-child{width:96px}' +
      '.naslovna-v2 .napomena{font-size:.72rem;color:#666;margin-top:10px}';
    document.head.appendChild(s);
  }

  function sparkline(rawPts, w, h, ref) {
    const pts = rawPts.filter(p => p && typeof p[1] === 'number');
    const xs = pts.map(p => p[1]);
    const svg = sv('svg', { viewBox: '0 0 ' + w + ' ' + h, 'aria-hidden': 'true' });
    if (xs.length < 2) return svg;
    const min = Math.min.apply(null, xs), max = Math.max.apply(null, xs);
    const span = (max - min) || 1;
    const H = h - 2, top = 2;
    const xy = p => [(w - 2) * ((p - min) / span) + 1, H - ((H - top) * ((p - min) / span))];
    let d = '';
    pts.forEach(p => { const [x, y] = xy(p[1]); d += (d ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1); });
    svg.appendChild(sv('path', { d: d, fill: 'none', stroke: '#333', 'stroke-width': 1.4 }));
    for (const r of (ref || [])) {
      if (r.v < min || r.v > max) continue;
      const [, y] = xy(r.v);
      svg.appendChild(sv('line', { x1: 0, x2: w, y1: y, y2: y, stroke: '#999', 'stroke-dasharray': '2 2', 'stroke-width': 1 }));
    }
    const [lx, ly] = xy(xs[xs.length - 1]);
    svg.appendChild(sv('circle', { cx: lx, cy: ly, r: 2, fill: '#333' }));
    return svg;
  }

  function ploca(naslov, serija, unit, ref, lvl) {
    const t = el('div', 'nv-tile');
    if (lvl) { t.style.background = EEA[lvl]; t.style.color = (lvl >= 4) ? '#fff' : '#111'; t.style.borderColor = 'rgba(0,0,0,.15)'; }
    t.appendChild(el('div', 'nv-lbl', naslov));
    const last = serija && serija.points && serija.points.length ? serija.points[serija.points.length - 1] : null;
    if (!last) { t.appendChild(el('div', 'nv-num', '—')); t.appendChild(el('div', 'nv-ref', STR.nema)); return t; }
    const num = el('div', 'nv-num', String(Math.round(last[1] * 10) / 10));
    num.appendChild(el('span', 'nv-unit', unit));
    t.appendChild(num);
    const pts = serija.points.slice(-24);
    const sp = sparkline(pts, 96, 20, ref);
    sp.style.marginTop = '6px';
    if (lvl >= 4) sp.style.filter = 'invert(1)';
    t.appendChild(sp);
    if (ref && ref.length) {
      const r = el('div', 'nv-ref');
      ref.forEach(x => r.appendChild(el('i')));
      r.appendChild(document.createTextNode(ref.map(x => x.k + ' ' + x.v).join(' · ')));
      t.appendChild(r);
    }
    return t;
  }

  function gradSada(puls) {
    const c = puls && puls.city_status; const box = el('div');
    const grid = el('div', 'nv-hero');
    const s = data.serije || {};
    const lvl = c && c.eaqi && c.eaqi.level;
    grid.appendChild(ploca('PM2.5 (µg/m³)', s.pm25, 'µg/m³', [{ k: STR.grRef, v: 15 }, { k: STR.grRs, v: 25 }], lvl));
    grid.appendChild(ploca('PM10 (µg/m³)', s.pm10, 'µg/m³', [{ k: STR.grRef, v: 45 }], null));
    grid.appendChild(ploca('Vazduh (°C)', s.temperature, '°C', [], null));
    grid.appendChild(ploca('Vlaga (%)', s.humidity, '%', [], null));
    box.appendChild(grid);
    if (c && c.eaqi) {
      const city = el('div', 'nv-city');
      city.style.background = EEA[c.eaqi.level] || '#eee';
      city.style.color = (c.eaqi.level >= 4) ? '#fff' : '#111';
      const b = el('b', null, STR.klase[c.eaqi.level] || c.eaqi.category);
      city.appendChild(b);
      if (c.eaqi.dominant_pollutant) city.appendChild(document.createTextNode(' — dominantno: ' + c.eaqi.dominant_pollutant));
      city.appendChild(el('div', null, c.eaqi.advice_general_sr || ''));
      if (c.eaqi.advice_sensitive_sr) city.appendChild(el('div', null, 'Osetljive grupe: ' + c.eaqi.advice_sensitive_sr));
      box.appendChild(city);
    }
    if (c && puls.as_of) {
      const n = (c.reference_stations_count || 0) + (c.citizen_sensors_count || 0);
      const src = el('p', 'napomena', 'Izmereno ' + n + ' ' + STR.stanica + ' · as_of ' + String(puls.as_of).replace('T', ' ').slice(0, 16) + 'Z · ' + STR.izvor + ': puls.json, serije/*.json');
      box.appendChild(src);
    }
    return box;
  }

  function mapa(lite) {
    const box = el('div', 'nv-map');
    const w = lite.window || { lo0: 20.17, lo1: 20.8, la0: 44.55, la1: 44.98 };
    const W = 320, H = 190, pad = 6;
    const px = lo => pad + (W - 2 * pad) * ((lo - w.lo0) / (w.lo1 - w.lo0));
    const py = la => H - pad - (H - 2 * pad) * ((la - w.la0) / (w.la1 - w.la0));
    const svg = sv('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img' });
    svg.appendChild(sv('rect', { x: 0, y: 0, width: W, height: H, fill: '#fafafa' }));
    const pts = lite.stations || [];
    const brStanja = {};
    for (const p of pts) {
      brStanja[p.st] = (brStanja[p.st] || 0) + 1;
      const c = sv('circle', {
        cx: px(p.lo).toFixed(1), cy: py(p.la).toFixed(1), r: 2.6,
        fill: (p.cls === 'air' && p.lvl) ? EEA[p.lvl] : '#8aa',
        'fill-opacity': p.st === 'estimated' ? .55 : (p.st === 'untimed' ? .4 : .95)
      });
      const t = sv('title');
      t.textContent = p.sid + ' · ' + p.cls + ' · ' + (STR.legendaStanja[p.st] || p.st) + (p.lvl ? ' · ' + (STR.klase[p.lvl] || p.lvl) : '');
      c.appendChild(t);
      svg.appendChild(c);
    }
    box.appendChild(el('div', 'nv-lbl', STR.mapa));
    box.appendChild(svg);
    const lg = el('div', 'nv-legend');
    for (const st of Object.keys(brStanja)) {
      const k = el('span', 'k');
      const d = el('span', 'tocka');
      d.style.background = st === 'estimated' ? 'rgba(138,170,170,.55)' : (st === 'untimed' ? 'rgba(138,170,170,.4)' : '#8aa');
      k.appendChild(d);
      k.appendChild(document.createTextNode(STR.legendaStanja[st] || st + ' ' + brStanja[st]));
      k.appendChild(document.createTextNode(' ' + brStanja[st]));
      lg.appendChild(k);
    }
    const raz = el('span', 'k'); raz.style.gap = '6px';
    for (const l of [1, 2, 3, 4, 5, 6]) {
      const d = el('span', 'tocka'); d.style.background = EEA[l]; raz.appendChild(d);
    }
    raz.appendChild(document.createTextNode('EAQI 1–6 (vazduh)'));
    lg.appendChild(raz);
    box.appendChild(lg);
    return box;
  }

  function kvorumTraka(kv) {
    const box = el('div', 'nv-kvorum');
    box.appendChild(el('div', 'nv-lbl', STR.kvorum));
    const boja = r => r >= .66 ? '#50ccaa' : (r >= .33 ? '#f0e641' : '#ff5050');
    const imena = { reference: 'referentne', 'low-cost': 'građanske', mobility: 'mobilnost', environment: 'vazduh', meteo: 'meteo', hydro: 'vode' };
    for (const d of Object.keys(kv)) {
      const v = kv[d]; if (!v || typeof v.ukupno !== 'number') continue;
      const r = v.ukupno ? v.javilo / v.ukupno : 0;
      const row = el('div', 'dom');
      row.appendChild(el('span', null, (imena[d] || d)));
      const bar = el('span', 'bar'); const i = el('i');
      i.style.width = Math.round(100 * r) + '%'; i.style.background = boja(r);
      bar.appendChild(i); row.appendChild(bar);
      row.appendChild(document.createTextNode(v.javilo + '/' + v.ukupno));
      box.appendChild(row);
    }
    return box;
  }

  function napravi(view) {
    if (view.querySelector('section.naslovna-v2')) return; // idempotentno
    if (!data.puls || !data.lite) return;
    const sec = el('section', 'naslovna-v2');
    sec.appendChild(el('h2', null, STR.naslov));
    sec.appendChild(gradSada(data.puls));
    sec.appendChild(mapa(data.lite));
    if (data.kvorum) sec.appendChild(kvorumTraka(data.kvorum));
    sec.appendChild(el('p', 'napomena', STR.napomena));
    const hero = view.querySelector('section.puls-sekcija') || view.firstElementChild;
    if (hero && hero !== sec) hero.parentNode.insertBefore(sec, hero);
    else view.insertBefore(sec, view.firstChild);
  }

  function jf(p) { return (typeof jfetch === 'function') ? jfetch(p) : fetch(p).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }); }

  function zakazi(view) {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      stilovi();
      const treba = { puls: 'state/puls.json', lite: 'state/mapa-lite.json', kvorum: 'state/organizam.json' };
      const keys = Object.keys(treba).filter(k => !data[k]);
      if (keys.length) {
        Promise.allSettled(keys.map(k => jf(treba[k]))).then(rs => {
          rs.forEach((r, i) => {
            const k = keys[i];
            if (r.status === 'fulfilled') data[k] = (k === 'kvorum') ? (r.value.kvorum || null) : r.value;
          });
          napravi(view);
          traziSerije();
        });
        return;
      }
      napravi(view);
      traziSerije();
    });
  }

  function traziSerije() {
    if (data.serije._trazio) return;
    data.serije._trazio = true;
    const ime = { pm25: 'serije/pm25.json', pm10: 'serije/pm10.json', temperature: 'serije/temperature.json', humidity: 'serije/humidity.json' };
    Object.keys(ime).forEach(k => jf(ime[k]).then(m => { data.serije[k] = m; osvezi(); }, () => { }));
  }

  function osvezi() {
    const v = document.getElementById('view');
    if (!v) return;
    const sec = v.querySelector('section.naslovna-v2');
    if (sec) sec.remove();
    napravi(v);
  }

  function start() {
    const view = document.getElementById('view');
    if (!view) return;
    mu = new MutationObserver(() => zakazi(view));
    mu.observe(view, { childList: true });
    zakazi(view);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();

  window.BEOPS_NASLOVNA = { osvezi: osvezi };
})();
