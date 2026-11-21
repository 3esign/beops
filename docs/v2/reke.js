/* BEOPS v2 reke.js — 14-dnevni trend vodostaja Save, Dunava i Tamiša na #podaci.
   Jedna rečenica: Vodostaji Save, Dunava i Tamiša kroz poslednjih 14 dana —
   stvarna visina u centimetrima, promena za 24 h i temperatura vode, bez
   izmišljenih pragova.
   Zaseban lenji modul (obrazac: veceras.js, metodologija.js) jer su app.js i
   beops.css puni do ugovornog plafona. Bez innerHTML; rAF gard; svetla i tamna
   tema preko postojećih CSS promenljivih; dvojezično (sr/en). */
'use strict';
/* global el, mk, jfetch, dlRow, showTT, hideTT, absTime, relTime, fmtNum, currentRoute, LANG */
(function () {
  let data = null;
  let activeIdx = 0;
  let raf = 0;
  let stil = false;
  let mu = null;

  const TXT = {
    sr: {
      title: 'Reke — vodostaj (14 dana)',
      sub: 'Sava, Dunav i Tamiš: satni vodostaji (S223) i dnevna temperatura vode (RHMZ S52). Bez izmišljenih pragova odbrane.',
      nema: 'Podaci o vodostajima trenutno nisu dostupni.',
      malo: 'Nedovoljno tačaka za 14-dnevni graf.',
      promena: 'za 24 h',
      raspon: '14d raspon',
      temp: 'voda',
      tacaka: 'tačaka',
      poslednja: 'poslednja',
      preuzmi: 'reke 14d (.json)',
      napomena: 'Kote su u centimetrima po vodomernim letvama stanica; izvor satnih serija je S223, a dnevne temperature vode i 24h promene RHMZ S52.',
    },
    en: {
      title: 'Rivers — water level (14 days)',
      sub: 'Sava, Danube and Tamiš: hourly water levels (S223) and daily water temperature (RHMZ S52). No invented flood thresholds.',
      nema: 'River water level data is currently unavailable.',
      malo: 'Not enough points for a 14-day chart.',
      promena: '24h',
      raspon: '14d range',
      temp: 'water',
      tacaka: 'points',
      poslednja: 'latest',
      preuzmi: 'rivers 14d (.json)',
      napomena: 'Gauge heights are in centimetres on each station staff; hourly series come from S223 and daily water temperature from RHMZ S52.',
    },
  };
  function L() { return TXT[typeof LANG === 'string' && LANG === 'en' ? 'en' : 'sr']; }

  function stilovi() {
    if (stil) return;
    stil = true;
    const s = document.createElement('style');
    s.setAttribute('data-beops', 'reke');
    s.textContent = [
      '#reke-block{margin:24px 0 18px;padding-top:14px;border-top:1px solid var(--line,#e2e6e4)}',
      '.reke-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:10px 0 12px}',
      '.reke-card{border:1px solid var(--line,#e2e6e4);border-radius:10px;padding:10px 12px;background:var(--paper,#fff);cursor:pointer;text-align:left;color:inherit;font:inherit;width:100%}',
      '.reke-card.active{border-color:var(--blue,#1d6fa5);box-shadow:inset 3px 0 0 var(--blue,#1d6fa5)}',
      '.reke-card .rk-name{font-size:.82rem;color:var(--muted,#666);display:flex;justify-content:space-between;gap:6px}',
      '.reke-card .rk-val{font-size:1.45rem;font-weight:700;line-height:1.2;margin:4px 0 2px;font-variant-numeric:tabular-nums}',
      '.reke-card .rk-val small{font-size:.75rem;font-weight:400;color:var(--muted,#666)}',
      '.reke-card .rk-meta{font-size:.78rem;color:var(--ink-2,#444);font-variant-numeric:tabular-nums}',
      '.reke-svg{display:block;max-width:100%;height:auto;outline:none}',
      '.reke-svg:focus-visible{outline:2px solid var(--blue,#1d6fa5);outline-offset:2px}',
      '.reke-line{fill:none;stroke:var(--blue,#1d6fa5);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}',
      '.reke-area{fill:var(--blue,#1d6fa5);fill-opacity:.1}',
      '.reke-dot{fill:var(--blue,#1d6fa5);stroke:var(--paper,#fff);stroke-width:1.5}',
    ].join('\n');
    document.head.appendChild(s);
  }

  function fmtDelta(d) {
    if (d === null || d === undefined || !Number.isFinite(d)) return '';
    const arrow = Math.abs(d) < 0.5 ? '→' : (d > 0 ? '▲' : '▼');
    return arrow + ' ' + (d > 0 ? '+' : '') + fmtNum(d, 0) + ' cm ' + L().promena;
  }

  function riverChart(st, wpx) {
    const wrap = el('div');
    const pts = (st.points || []).map(p => ({
      x: Date.parse(p[0] + ':00:00Z'),
      v: p[1],
    })).filter(p => Number.isFinite(p.x) && Number.isFinite(p.v));

    const title = el('div', 'chart-title');
    const h3 = el('h3', null, st.name + ' · ' + st.unit);
    h3.style.fontSize = '15px';
    h3.style.margin = '10px 0 6px';
    title.appendChild(h3);
    if (pts.length) {
      title.appendChild(el('span', 'muted', pts.length + ' ' + L().tacaka + ' · ' +
        absTime(new Date(pts[0].x).toISOString()) + ' – ' + absTime(new Date(pts[pts.length - 1].x).toISOString())));
    }
    wrap.appendChild(title);
    if (pts.length < 2) {
      wrap.appendChild(el('p', 'sub', L().malo));
      return wrap;
    }

    const W = Math.max(340, Math.floor(wpx || 1000)), H = 260, Lpad = 52, R = 14, TP = 14, B = 28;
    const x0 = pts[0].x, x1 = pts[pts.length - 1].x;
    let y0 = Infinity, y1 = -Infinity;
    for (const p of pts) { if (p.v < y0) y0 = p.v; if (p.v > y1) y1 = p.v; }
    if (y1 - y0 < 5) { y0 -= 3; y1 += 3; }
    const pad = (y1 - y0) * 0.08;
    y0 -= pad; y1 += pad;
    const sx = t => Lpad + (t - x0) / (x1 - x0) * (W - Lpad - R);
    const sy = v => H - B - (v - y0) / (y1 - y0) * (H - TP - B);

    const svg = mk('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img', 'class': 'reke-svg' });
    svg.tabIndex = 0;

    for (let i = 0; i <= 4; i++) {
      const v = y0 + (y1 - y0) * i / 4;
      const y = sy(v);
      svg.appendChild(mk('line', { x1: Lpad, x2: W - R, y1: y.toFixed(1), y2: y.toFixed(1), 'class': 'axisline', opacity: i === 0 ? 1 : 0.55 }));
      svg.appendChild(mk('text', { x: Lpad - 8, y: (y + 3).toFixed(1), 'text-anchor': 'end' }, fmtNum(v, 0)));
    }
    const dayMs = 24 * 3600e3;
    let tickIdx = 0;
    for (let t = Math.ceil(x0 / dayMs) * dayMs; t <= x1; t += dayMs) {
      const x = sx(t);
      svg.appendChild(mk('line', { x1: x.toFixed(1), x2: x.toFixed(1), y1: TP, y2: H - B, 'class': 'axisline', opacity: 0.25 }));
      if (W >= 540 || tickIdx % 2 === 0) {
        const d = new Date(t);
        const lab = String(d.getUTCDate()).padStart(2, '0') + '.' + String(d.getUTCMonth() + 1).padStart(2, '0') + '.';
        svg.appendChild(mk('text', { x: x.toFixed(1), y: H - 8, 'text-anchor': 'middle' }, lab));
      }
      tickIdx++;
    }

    let dLine = '', dArea = '', run = [];
    const flushArea = () => {
      if (run.length > 1) {
        dArea += run.map((p, i) => (i ? 'L' : 'M') + sx(p.x).toFixed(1) + ' ' + sy(p.v).toFixed(1)).join(' ') +
          ` L${sx(run[run.length - 1].x).toFixed(1)} ${(H - B).toFixed(1)} L${sx(run[0].x).toFixed(1)} ${(H - B).toFixed(1)} Z`;
      }
      run = [];
    };
    pts.forEach((p, i) => {
      const gap = i && p.x - pts[i - 1].x > 6 * 3600e3;
      dLine += (i && !gap ? 'L' : 'M') + sx(p.x).toFixed(1) + ' ' + sy(p.v).toFixed(1) + ' ';
      if (gap) flushArea();
      run.push(p);
    });
    flushArea();
    if (dArea) svg.appendChild(mk('path', { d: dArea, 'class': 'reke-area' }));
    svg.appendChild(mk('path', { d: dLine, 'class': 'reke-line' }));

    const cross = mk('line', { x1: 0, x2: 0, y1: TP, y2: H - B, 'class': 'crosshair', visibility: 'hidden' });
    const dot = mk('circle', { r: 4, 'class': 'reke-dot', visibility: 'hidden' });
    svg.appendChild(cross); svg.appendChild(dot);

    let active = -1;
    const setIdx = (i, clientX, clientY) => {
      i = Math.max(0, Math.min(pts.length - 1, i));
      active = i;
      const p = pts[i], px = sx(p.x), py = sy(p.v);
      cross.setAttribute('x1', px); cross.setAttribute('x2', px); cross.setAttribute('visibility', 'visible');
      dot.setAttribute('cx', px); dot.setAttribute('cy', py); dot.setAttribute('visibility', 'visible');
      const r = svg.getBoundingClientRect();
      const ax = clientX !== undefined ? clientX : r.left + px / W * r.width;
      const ay = clientY !== undefined ? clientY : r.top + py / H * r.height;
      showTT(ax, ay, fmtNum(p.v, 0) + ' cm', st.name + ' · ' + absTime(new Date(p.x).toISOString()) + ' · ' + st.series_sid);
    };
    const clear = () => {
      active = -1;
      cross.setAttribute('visibility', 'hidden');
      dot.setAttribute('visibility', 'hidden');
      hideTT();
    };
    svg.addEventListener('pointermove', ev => {
      const r = svg.getBoundingClientRect();
      const fx = (ev.clientX - r.left) / r.width * W;
      let best = 0, bd = Infinity;
      for (let i = 0; i < pts.length; i++) { const dd = Math.abs(sx(pts[i].x) - fx); if (dd < bd) { bd = dd; best = i; } }
      setIdx(best, ev.clientX, ev.clientY);
    });
    svg.addEventListener('pointerleave', clear);
    svg.addEventListener('keydown', ev => {
      if (ev.key === 'ArrowLeft' || ev.key === 'ArrowRight') {
        ev.preventDefault();
        setIdx(active < 0 ? pts.length - 1 : active + (ev.key === 'ArrowRight' ? 1 : -1));
      } else if (ev.key === 'Escape') clear();
    });
    svg.addEventListener('blur', clear);
    const lastP = pts[pts.length - 1];
    svg.setAttribute('aria-label', `${st.name}: ${pts.length} ${L().tacaka}, ${L().poslednja} ${fmtNum(lastP.v, 0)} cm`);
    wrap.appendChild(svg);
    return wrap;
  }

  function renderBlock(root) {
    const old = document.getElementById('reke-block');
    if (old) old.remove();
    const chartBox = document.getElementById('chart-box');
    if (!chartBox || !root.contains(chartBox)) return;

    const block = el('section');
    block.id = 'reke-block';
    block.appendChild(el('h2', null, L().title));
    block.appendChild(el('p', 'sub', L().sub));

    const stations = (data && Array.isArray(data.stations)) ? data.stations : [];
    if (!stations.length) {
      block.appendChild(el('p', 'sub', L().nema));
      chartBox.after(block);
      return;
    }
    if (activeIdx >= stations.length) activeIdx = 0;

    const grid = el('div', 'reke-grid');
    stations.forEach((st, idx) => {
      const card = el('button', 'reke-card' + (idx === activeIdx ? ' active' : ''));
      card.type = 'button';
      card.setAttribute('aria-pressed', idx === activeIdx ? 'true' : 'false');
      const top = el('div', 'rk-name');
      top.appendChild(el('span', null, st.name));
      if (st.latest && st.latest.at) top.appendChild(el('span', null, relTime(st.latest.at)));
      card.appendChild(top);

      const val = el('div', 'rk-val', st.latest && st.latest.level_cm != null ? fmtNum(st.latest.level_cm, 0) : '—');
      val.appendChild(el('small', null, ' cm'));
      card.appendChild(val);

      const bits = [];
      const dTxt = fmtDelta(st.latest && st.latest.delta_24h_cm);
      if (dTxt) bits.push(dTxt);
      if (st.rhmz && st.rhmz.temp_c != null) bits.push(L().temp + ' ' + fmtNum(st.rhmz.temp_c, 1) + ' °C');
      if (st.min_14d_cm != null && st.max_14d_cm != null) bits.push(L().raspon + ' ' + fmtNum(st.min_14d_cm, 0) + '–' + fmtNum(st.max_14d_cm, 0));
      card.appendChild(el('div', 'rk-meta', bits.join(' · ')));
      card.addEventListener('click', () => { activeIdx = idx; renderBlock(root); });
      grid.appendChild(card);
    });
    block.appendChild(grid);
    block.appendChild(riverChart(stations[activeIdx], chartBox.clientWidth || root.clientWidth || 1000));
    block.appendChild(el('p', 'sub', L().napomena));
    block.appendChild(dlRow([['state/reke.json', L().preuzmi]]));
    chartBox.after(block);
  }

  function napravi() {
    if (typeof currentRoute !== 'function' || currentRoute() !== 'podaci') return;
    const view = document.getElementById('view');
    const chartBox = document.getElementById('chart-box');
    if (!view || !chartBox) return;
    if (document.getElementById('reke-block')) return;
    renderBlock(view);
  }

  function zakazi() {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      stilovi();
      if (typeof currentRoute === 'function' && currentRoute() !== 'podaci') return;
      if (!data && typeof jfetch === 'function') {
        jfetch('state/reke.json').then(m => { data = m; napravi(); }, () => { data = { stations: [] }; napravi(); });
        return;
      }
      if (data) napravi();
    });
  }

  function start() {
    const view = document.getElementById('view');
    if (!view) return;
    mu = new MutationObserver(() => zakazi());
    mu.observe(view, { childList: true });
    window.addEventListener('resize', () => {
      if (typeof currentRoute === 'function' && currentRoute() === 'podaci' && data) {
        const v = document.getElementById('view');
        if (v) renderBlock(v);
      }
    });
    zakazi();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();

  window.BEOPS_REKE = { osvezi: () => { data = null; zakazi(); } };
})();
