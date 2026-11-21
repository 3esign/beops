/* BEOPS v2 proslost.js — „Ovaj mesec prethodnih godina“ (SEPA 2011–2024, S06). Bez innerHTML; sr/en. */
'use strict';
/* global el, mk, jfetch, dlRow, fmtNum, currentRoute, STATE, krajIzbor, krajNorm, krajNajblizaRef, KRAJ_OPSTINE, LANG */
(function () {
  let data = null;
  let loading = false;
  let raf = 0;
  let stil = false;
  let activePol = 'pm25';
  let activeMonth = new Date().getMonth() + 1;
  let activeStation = '';

  const MESECI = {
    sr: ['Januar', 'Februar', 'Mart', 'April', 'Maj', 'Jun', 'Jul', 'Avgust', 'Septembar', 'Oktobar', 'Novembar', 'Decembar'],
    en: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
  };
  const POLS = [
    { id: 'pm25', label: 'PM2.5', unit: 'µg/m³' },
    { id: 'pm10', label: 'PM10', unit: 'µg/m³', limit: 50 },
    { id: 'no2', label: 'NO₂', unit: 'µg/m³' },
  ];
  const IMENA = {
    'ada-petlja': 'Ada Petlja', 'banovo-brdo': 'Banovo brdo', 'bezanijska-kosa': 'Bežanijska kosa',
    'bulevar-despota-stefana': 'Bulevar despota Stefana', 'dragisa-misovic': 'Dragiša Mišović',
    'lazarevac': 'Lazarevac', 'mostar': 'Mostar', 'novi-beograd': 'Novi Beograd',
    'obrenovac-centar': 'Obrenovac Centar', 'obrenovac-deponija-pepela': 'Obrenovac dep. pepela',
    'omladinskih-brigada': 'Omladinskih brigada', 'ovca': 'Ovča', 'pancev-most': 'Pančevački most',
    'pancevo-sodara': 'Pančevo Sodara', 'stari-grad': 'Stari grad', 'vinca': 'Vinča',
    'vracar': 'Vračar', 'vracar-gradska-mreza': 'Vračar (gradska)', 'zeleno-brdo': 'Zeleno brdo',
    'zemun-gradska-mreza': 'Zemun (gradska)',
  };

  const TXT = {
    sr: {
      title: 'Ovaj mesec prethodnih godina (2011–2024)',
      sub: 'Verifikovani dnevni proseci (SEPA S06, data.gov.rs): medijana (p50) i 90. percentil (p90) za izabrani mesec. Tačka je poslednje satno merenje (S146) u tekućem mesecu.',
      mesec: 'Mesec',
      nema: 'Nema istorijskih zapisa za ovaj polutant i mesec.',
      medijana: 'medijana',
      danas: 'danas',
      dana: 'dana',
      godisnji: 'Godišnji proseci',
      prekoGranice: 'dana > granice',
      pokrivenost: 'obuhvat',
      nizakObuhvat: 'obuhvat < 90%',
      krajNaslov: 'Uobičajeno u ovom mesecu (2011–2024)',
      napomena: 'Verifikovani dnevni proseci završavaju sa 2024, dok su živa S146 merenja satna i preliminarna. Prikaz je prošlost stanice (šta je uobičajeno), ne zakonska ocena dana.',
      dl: 'istorijski vazduh 2011–2024 (.json)',
    },
    en: {
      title: 'This month in previous years (2011–2024)',
      sub: 'Verified daily means (SEPA S06, data.gov.rs): median (p50) and 90th percentile (p90) for the selected month. Dot marks the latest hourly reading (S146) in the current month.',
      mesec: 'Month',
      nema: 'No historical records for this pollutant and month.',
      medijana: 'median',
      danas: 'now',
      dana: 'days',
      godisnji: 'Annual means',
      prekoGranice: 'days > limit',
      pokrivenost: 'coverage',
      nizakObuhvat: 'coverage < 90%',
      krajNaslov: 'Usual for this month (2011–2024)',
      napomena: 'Verified daily means end in 2024, while live S146 readings are hourly and preliminary. Shows each station’s past (what is usual), not a legal check of today.',
      dl: 'historical air 2011–2024 (.json)',
    },
  };
  function L() { return TXT[typeof LANG === 'string' && LANG === 'en' ? 'en' : 'sr']; }
  function mName(m) { return (MESECI[typeof LANG === 'string' && LANG === 'en' ? 'en' : 'sr'][m - 1]) || String(m); }
  function stLabel(slug) { return IMENA[slug] || slug; }

  function toSlug(s) {
    return String(s || '')
      .toLowerCase()
      .replace(/[čć]/g, 'c').replace(/š/g, 's').replace(/ž/g, 'z').replace(/đ/g, 'dj')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }

  function stilovi() {
    if (stil) return;
    stil = true;
    const s = document.createElement('style');
    s.setAttribute('data-beops', 'proslost');
    s.textContent = [
      '#proslost-block{margin:24px 0 18px;padding-top:14px;border-top:1px solid var(--line,#e2e6e4)}',
      '.prs-ctrl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0 12px}',
      '.prs-ctrl button,.prs-ctrl select{padding:5px 10px;border:1px solid var(--line,#e2e6e4);border-radius:8px;background:var(--paper,#fff);color:inherit;font:inherit}',
      '.prs-ctrl button{cursor:pointer}.prs-ctrl button.active{border-color:var(--blue,#1d6fa5);background:var(--blue,#1d6fa5);color:#fff}',
      '.prs-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px;margin:8px 0 12px}',
      '.prs-card{border:1px solid var(--line,#e2e6e4);border-radius:10px;padding:10px 12px;background:var(--paper,#fff);text-align:left;color:inherit;font:inherit;cursor:pointer;width:100%}',
      '.prs-card.active{border-color:var(--blue,#1d6fa5);box-shadow:inset 3px 0 0 var(--blue,#1d6fa5)}',
      '.prs-head{display:flex;justify-content:space-between;gap:8px;font-size:.88rem;font-weight:600}',
      '.prs-nums{font-size:.8rem;color:var(--ink-2,#444);margin:4px 0 6px;font-variant-numeric:tabular-nums}',
      '.prs-bar{position:relative;height:8px;border-radius:999px;background:var(--line,#e2e6e4);margin:6px 0 4px}',
      '.prs-range{position:absolute;top:0;bottom:0;border-radius:999px;background:var(--blue,#1d6fa5);opacity:.45}',
      '.prs-med{position:absolute;top:-2px;bottom:-2px;width:2px;background:var(--blue,#1d6fa5)}',
      '.prs-now{position:absolute;top:-3px;width:14px;height:14px;margin-left:-7px;border-radius:50%;background:var(--ink,#111);border:2px solid var(--paper,#fff)}',
      '.prs-annual,.prs-kraj{margin:12px 0;padding:12px 14px;border:1px solid var(--line,#e2e6e4);border-radius:10px;background:var(--paper,#fff)}',
      '.prs-annual h3,.prs-kraj h3{margin:0 0 6px;font-size:.98rem}.prs-svg{display:block;max-width:100%;height:auto}',
    ].join('\n');
    document.head.appendChild(s);
  }

  function loadData() {
    if (data || loading || typeof jfetch !== 'function') return;
    loading = true;
    jfetch('state/kontekst-vazduh-dnevno.json').then(m => {
      data = m || {};
      loading = false;
      zakazi();
    }, () => {
      data = { monthly_climatology: {}, annual: [] };
      loading = false;
      zakazi();
    });
  }

  function liveValue(slug, pol) {
    const M = typeof STATE === 'object' && STATE && STATE.mapa;
    if (!M || !Array.isArray(M.stations)) return null;
    for (const st of M.stations) {
      if (st.sid !== 'S146') continue;
      if (toSlug(st.n) !== slug) continue;
      const hit = (st.r || []).find(r => r.p === pol && Number.isFinite(r.v));
      if (hit) return hit.v;
    }
    return null;
  }

  function annualPanel(slug, polObj) {
    const rows = ((data && data.annual) || [])
      .filter(r => r.station === slug && r.pollutant === polObj.id)
      .sort((a, b) => a.year - b.year);
    const box = el('div', 'prs-annual');
    box.appendChild(el('h3', null, `${L().godisnji} · ${stLabel(slug)} · ${polObj.label} (${polObj.unit})`));
    if (!rows.length) {
      box.appendChild(el('p', 'sub', L().nema));
      return box;
    }
    const W = 720, H = 175, Lp = 42, Rp = 14, Tp = 14, Bp = 28;
    const maxV = Math.max(...rows.map(r => Math.max(r.p90 || 0, r.mean || 0)), polObj.limit || 0, 10) * 1.1;
    const step = (W - Lp - Rp) / rows.length;
    const barW = Math.max(8, Math.min(28, step * 0.56));
    const sy = v => H - Bp - (v / maxV) * (H - Tp - Bp);

    const svg = mk('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img', 'class': 'prs-svg' });
    svg.setAttribute('aria-label', `${stLabel(slug)} ${polObj.label} ${rows[0].year}-${rows[rows.length - 1].year}`);
    for (let i = 0; i <= 3; i++) {
      const v = maxV * i / 3;
      const y = sy(v);
      svg.appendChild(mk('line', { x1: Lp, x2: W - Rp, y1: y.toFixed(1), y2: y.toFixed(1), 'class': 'axisline', opacity: i === 0 ? 1 : 0.45 }));
      svg.appendChild(mk('text', { x: Lp - 6, y: (y + 3).toFixed(1), 'text-anchor': 'end', 'font-size': '10' }, fmtNum(v, 0)));
    }
    rows.forEach((r, i) => {
      const cx = Lp + step * i + step / 2;
      const yMean = sy(r.mean);
      const yP90 = sy(r.p90 || r.mean);
      svg.appendChild(mk('line', { x1: cx.toFixed(1), x2: cx.toFixed(1), y1: yP90.toFixed(1), y2: yMean.toFixed(1), stroke: 'var(--blue,#1d6fa5)', 'stroke-width': 1.5, opacity: 0.6 }));
      svg.appendChild(mk('rect', {
        x: (cx - barW / 2).toFixed(1),
        y: yMean.toFixed(1),
        width: barW.toFixed(1),
        height: Math.max(2, (H - Bp - yMean)).toFixed(1),
        rx: 2,
        fill: 'var(--blue,#1d6fa5)',
        opacity: r.coverage < 0.9 ? 0.45 : 0.85,
      }));
      svg.appendChild(mk('text', { x: cx.toFixed(1), y: H - 8, 'text-anchor': 'middle', 'font-size': '10' }, String(r.year).slice(-2)));
    });
    box.appendChild(svg);

    const last = rows[rows.length - 1];
    const bits = [
      `${last.year}: ${fmtNum(last.mean, 1)} ${polObj.unit}`,
      `p90 ${fmtNum(last.p90, 1)}`,
      `${L().pokrivenost} ${fmtNum((last.coverage || 0) * 100, 0)}%`,
    ];
    if (last.days_over_limit != null) bits.push(`${last.days_over_limit} ${L().prekoGranice}`);
    if (rows.some(r => r.coverage < 0.9)) bits.push(L().nizakObuhvat);
    box.appendChild(el('p', 'meta', bits.join(' · ')));
    return box;
  }

  function renderPodaci(root) {
    const old = document.getElementById('proslost-block');
    if (old) old.remove();
    const anchor = document.getElementById('reke-block') || document.getElementById('chart-box');
    if (!anchor || !root.contains(anchor)) return;

    const polObj = POLS.find(p => p.id === activePol) || POLS[0];
    const block = el('section');
    block.id = 'proslost-block';
    block.appendChild(el('h2', null, L().title));
    block.appendChild(el('p', 'sub', L().sub));

    const ctrl = el('div', 'prs-ctrl');
    for (const p of POLS) {
      const b = el('button', p.id === activePol ? 'active' : null, p.label);
      b.type = 'button';
      b.setAttribute('aria-pressed', p.id === activePol ? 'true' : 'false');
      b.addEventListener('click', () => { activePol = p.id; renderPodaci(root); });
      ctrl.appendChild(b);
    }
    const sel = el('select');
    sel.setAttribute('aria-label', L().mesec);
    for (let m = 1; m <= 12; m++) {
      const o = el('option', null, mName(m));
      o.value = String(m);
      if (m === activeMonth) o.selected = true;
      sel.appendChild(o);
    }
    sel.addEventListener('change', () => { activeMonth = Number(sel.value) || 1; renderPodaci(root); });
    ctrl.appendChild(sel);
    block.appendChild(ctrl);

    const mc = (data && data.monthly_climatology) || {};
    const mKey = String(activeMonth);
    const curMonth = new Date().getMonth() + 1;
    const entries = [];
    for (const [slug, byPol] of Object.entries(mc)) {
      const rec = byPol && byPol[activePol] && byPol[activePol][mKey];
      if (!rec) continue;
      entries.push({
        slug,
        rec,
        now: activeMonth === curMonth ? liveValue(slug, activePol) : null,
      });
    }
    entries.sort((a, b) => (b.rec.n || 0) - (a.rec.n || 0) || a.slug.localeCompare(b.slug));

    if (!entries.length) {
      block.appendChild(el('p', 'sub', L().nema));
    } else {
      if (!entries.some(e => e.slug === activeStation)) activeStation = entries[0].slug;
      const scaleMax = Math.max(...entries.map(e => Math.max(e.rec.p90 || 0, e.now || 0)), 10) * 1.05;
      const grid = el('div', 'prs-list');
      for (const e of entries) {
        const card = el('button', 'prs-card' + (e.slug === activeStation ? ' active' : ''));
        card.type = 'button';
        card.setAttribute('aria-pressed', e.slug === activeStation ? 'true' : 'false');

        const head = el('div', 'prs-head');
        head.appendChild(el('span', null, stLabel(e.slug)));
        head.appendChild(el('span', null, `${e.rec.n} d`));
        card.appendChild(head);

        const nums = [`${L().medijana} ${fmtNum(e.rec.p50, 1)}`, `p90 ${fmtNum(e.rec.p90, 1)} ${polObj.unit}`];
        if (e.now !== null) nums.push(`${L().danas} ${fmtNum(e.now, 1)}`);
        card.appendChild(el('div', 'prs-nums', nums.join(' · ')));

        const bar = el('div', 'prs-bar');
        const rng = el('div', 'prs-range');
        rng.style.left = '0%';
        rng.style.width = Math.min(100, (e.rec.p90 / scaleMax) * 100).toFixed(1) + '%';
        bar.appendChild(rng);

        const med = el('div', 'prs-med');
        med.style.left = Math.min(100, (e.rec.p50 / scaleMax) * 100).toFixed(1) + '%';
        bar.appendChild(med);

        if (e.now !== null) {
          const dot = el('div', 'prs-now');
          dot.style.left = Math.min(100, (e.now / scaleMax) * 100).toFixed(1) + '%';
          dot.title = `${L().danas}: ${fmtNum(e.now, 1)} ${polObj.unit}`;
          bar.appendChild(dot);
        }
        card.appendChild(bar);
        card.addEventListener('click', () => { activeStation = e.slug; renderPodaci(root); });
        grid.appendChild(card);
      }
      block.appendChild(grid);
      block.appendChild(annualPanel(activeStation, polObj));
    }

    block.appendChild(el('p', 'sub', L().napomena));
    block.appendChild(dlRow([['state/kontekst-vazduh-dnevno.json', L().dl]]));
    anchor.after(block);
  }

  function renderKraj() {
    const refBox = document.querySelector('#view .kraj-ref');
    if (!refBox || document.getElementById('proslost-kraj')) return;
    if (typeof krajIzbor !== 'function' || typeof krajNajblizaRef !== 'function' || !Array.isArray(KRAJ_OPSTINE)) return;
    const izbor = krajIzbor();
    const opEntry = KRAJ_OPSTINE.find(x => krajNorm(x[0]) === krajNorm(izbor) || krajNorm(x[1]) === krajNorm(izbor));
    const found = krajNajblizaRef(opEntry);
    if (!found || !found.st) return;

    const slug = toSlug(found.st.n);
    const mc = data && data.monthly_climatology && data.monthly_climatology[slug];
    if (!mc) return;
    const m = new Date().getMonth() + 1;
    const mKey = String(m);
    const lines = [];
    for (const p of POLS) {
      const rec = mc[p.id] && mc[p.id][mKey];
      if (rec) lines.push(`${p.label}: ${L().medijana} ${fmtNum(rec.p50, 1)}, p90 ${fmtNum(rec.p90, 1)} ${p.unit} (${rec.n} ${L().dana})`);
    }
    if (!lines.length) return;

    const box = el('div', 'prs-kraj');
    box.id = 'proslost-kraj';
    box.appendChild(el('h3', null, `${L().krajNaslov} — ${mName(m)} · ${found.st.n}`));
    for (const ln of lines) box.appendChild(el('p', 'meta', ln));
    box.appendChild(el('p', 'hint', L().napomena));
    const afterEl = document.getElementById('prevoz-kraj') || refBox;
    afterEl.after(box);
  }

  function napravi() {
    if (typeof currentRoute !== 'function') return;
    const r = currentRoute();
    const view = document.getElementById('view');
    if (!view) return;
    if (r === 'kraj') renderKraj();
    else if (r === 'podaci' && !document.getElementById('proslost-block')) renderPodaci(view);
  }

  function zakazi() {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      stilovi();
      if (typeof currentRoute !== 'function') return;
      const r = currentRoute();
      if (r !== 'kraj' && r !== 'podaci') return;
      if (!data) { loadData(); return; }
      napravi();
    });
  }

  function start() {
    const view = document.getElementById('view');
    if (!view) return;
    const mu = new MutationObserver(() => zakazi());
    mu.observe(view, { childList: true, subtree: true });
    zakazi();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();

  window.BEOPS_PROSLOST = { osvezi: () => { data = null; zakazi(); } };
})();
