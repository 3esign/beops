/* BEOPS v2 — Potez 4: Prognoza vazduha „sutra“ (Open-Meteo CAMS, D-006 A2) sa 14-dnevnim merenjem greške.
 * Čita isključivo state/prognoza_vazduh.json. Dok nije izmereno 14 punih dana greške prema SEPA S146,
 * prikazuje samo tok kalibracije i tekuću grešku bez brojeva prognoze; posle 14 dana prikazuje „sutra“
 * uz izmerenu 14-dnevnu grešku (MAE, pristrasnost, poređenje sa perzistencijom). Bez innerHTML. */
(function () {
  'use strict';
  const CONTRACT = 'state/prognoza_vazduh.json';
  const METRICS = [
    ['pm25', 'PM2.5', 'µg/m³'],
    ['pm10', 'PM10', 'µg/m³'],
    ['no2', 'NO₂', 'µg/m³'],
    ['o3', 'O₃', 'µg/m³'],
    ['so2', 'SO₂', 'µg/m³'],
    ['co', 'CO', 'mg/m³'],
  ];
  let _cache = null;
  let _sel = 'pm25';

  function isEn() {
    try { return (typeof lang !== 'undefined' && lang === 'en') || document.documentElement.lang === 'en'; }
    catch { return false; }
  }
  function mk(tag, cls, txt) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt != null) e.textContent = String(txt);
    return e;
  }
  function fmt(v, dec) {
    if (v == null || Number.isNaN(Number(v))) return '—';
    const s = Number(v).toFixed(dec == null ? 1 : dec);
    return isEn() ? s : s.replace('.', ',');
  }
  function fmtSign(v, dec) {
    if (v == null || Number.isNaN(Number(v))) return '—';
    const n = Number(v);
    return (n > 0 ? '+' : '') + fmt(n, dec);
  }

  async function loadData() {
    if (_cache) return _cache;
    try {
      const r = await fetch(CONTRACT, { cache: 'no-cache' });
      if (!r.ok) return null;
      _cache = await r.json();
      return _cache;
    } catch { return null; }
  }

  function buildSvg(hours, vals, unit) {
    const ns = 'http://www.w3.org/2000/svg';
    const W = 560, H = 132, P = { l: 38, r: 12, t: 12, b: 24 };
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', isEn() ? 'Tomorrow hourly forecast' : 'Satna prognoza za sutra');
    svg.style.width = '100%';
    svg.style.height = 'auto';
    svg.style.display = 'block';
    const pts = vals.map((v, i) => (typeof v === 'number' ? [i, v] : null)).filter(Boolean);
    if (!pts.length) return svg;
    const maxV = Math.max(1, ...pts.map(p => p[1])) * 1.15;
    const pw = W - P.l - P.r, ph = H - P.t - P.b;
    const xOf = i => P.l + (hours.length > 1 ? (i / (hours.length - 1)) * pw : pw / 2);
    const yOf = v => P.t + ph - (Math.max(0, v) / maxV) * ph;

    for (const frac of [0, 0.5, 1]) {
      const y = P.t + ph * (1 - frac);
      const ln = document.createElementNS(ns, 'line');
      ln.setAttribute('x1', P.l); ln.setAttribute('x2', W - P.r);
      ln.setAttribute('y1', y); ln.setAttribute('y2', y);
      ln.setAttribute('stroke', 'var(--rule, #d8d4cc)');
      ln.setAttribute('stroke-dasharray', frac === 0 ? '' : '2,3');
      svg.appendChild(ln);
      const lb = document.createElementNS(ns, 'text');
      lb.setAttribute('x', P.l - 5); lb.setAttribute('y', y + 3);
      lb.setAttribute('text-anchor', 'end');
      lb.setAttribute('font-size', '9');
      lb.setAttribute('fill', 'var(--muted, #666)');
      lb.textContent = fmt(maxV * frac, unit === 'mg/m³' ? 2 : 0);
      svg.appendChild(lb);
    }

    const d = pts.map((p, idx) => `${idx ? 'L' : 'M'}${xOf(p[0]).toFixed(1)},${yOf(p[1]).toFixed(1)}`).join(' ');
    const path = document.createElementNS(ns, 'path');
    path.setAttribute('d', d);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', 'var(--accent, #1f5a7a)');
    path.setAttribute('stroke-width', '2');
    path.setAttribute('stroke-dasharray', '5,3');
    svg.appendChild(path);

    for (const p of pts) {
      const c = document.createElementNS(ns, 'circle');
      c.setAttribute('cx', xOf(p[0]).toFixed(1));
      c.setAttribute('cy', yOf(p[1]).toFixed(1));
      c.setAttribute('r', '2.5');
      c.setAttribute('fill', 'var(--accent, #1f5a7a)');
      svg.appendChild(c);
    }
    for (let i = 0; i < hours.length; i += 4) {
      const tx = document.createElementNS(ns, 'text');
      tx.setAttribute('x', xOf(i).toFixed(1));
      tx.setAttribute('y', H - 6);
      tx.setAttribute('text-anchor', 'middle');
      tx.setAttribute('font-size', '9');
      tx.setAttribute('fill', 'var(--muted, #666)');
      tx.textContent = hours[i];
      svg.appendChild(tx);
    }
    return svg;
  }

  function renderVerifTable(verif) {
    const en = isEn();
    const tbl = mk('table', 'beops-prog-tbl');
    tbl.style.width = '100%';
    tbl.style.borderCollapse = 'collapse';
    tbl.style.fontSize = '0.84rem';
    tbl.style.marginTop = '0.5rem';
    const thead = mk('thead');
    const hr = mk('tr');
    const cols = en
      ? ['Metric', 'Pairs (24h)', 'MAE', 'Bias', 'Persistence MAE', 'Skill']
      : ['Metrika', 'Parova (24 h)', 'MAE', 'Pristrasnost', 'Perzistencija MAE', 'Veština'];
    for (const c of cols) {
      const th = mk('th', null, c);
      th.style.textAlign = 'left';
      th.style.padding = '0.25rem 0.4rem';
      th.style.borderBottom = '1px solid var(--rule, #d8d4cc)';
      hr.appendChild(th);
    }
    thead.appendChild(hr);
    tbl.appendChild(thead);
    const tb = mk('tbody');
    for (const [key, label, unit] of METRICS) {
      const v = verif && verif[key];
      if (!v) continue;
      const dec = key === 'co' ? 2 : 1;
      const tr = mk('tr');
      const cells = [
        `${label} (${unit})`,
        `${v.n_pairs} (${v.full_days_12h} d)`,
        fmt(v.mae, dec),
        fmtSign(v.bias, dec),
        fmt(v.persistence_mae, dec),
        v.skill_vs_persistence == null ? '—' : fmtSign(v.skill_vs_persistence * 100, 0) + '%',
      ];
      for (const txt of cells) {
        const td = mk('td', null, txt);
        td.style.padding = '0.25rem 0.4rem';
        td.style.borderBottom = '1px solid var(--rule, #eee)';
        tr.appendChild(td);
      }
      tb.appendChild(tr);
    }
    tbl.appendChild(tb);
    return tbl;
  }

  function renderCard(data) {
    const en = isEn();
    const sec = mk('section', 'beops-prognoza-card');
    sec.id = 'beops-prognoza-vazduh';
    sec.style.margin = '1.25rem 0';
    sec.style.padding = '1rem 1.1rem';
    sec.style.border = '1px solid var(--rule, #d8d4cc)';
    sec.style.borderRadius = '6px';
    sec.style.background = 'var(--paper-2, var(--bg-soft, transparent))';

    const head = mk('div');
    head.style.display = 'flex';
    head.style.flexWrap = 'wrap';
    head.style.justifyContent = 'space-between';
    head.style.alignItems = 'baseline';
    head.style.gap = '0.5rem';

    const title = mk('h3', null, en ? 'Tomorrow air-quality forecast (Open-Meteo CAMS)' : 'Prognoza vazduha „sutra“ (Open-Meteo CAMS)');
    title.style.margin = '0';
    title.style.fontSize = '1.05rem';
    head.appendChild(title);

    const badgeTxt = data.status === 'active'
      ? (en ? 'MODEL FORECAST · NOT A MEASUREMENT' : 'PROGNOZA MODELA · NIJE MERENJE')
      : (en ? `CALIBRATION ${data.kalibracija.days_measured}/${data.kalibracija.days_required} DAYS` : `KALIBRACIJA ${data.kalibracija.days_measured}/${data.kalibracija.days_required} DANA`);
    const badge = mk('span', null, badgeTxt);
    badge.style.fontSize = '0.74rem';
    badge.style.fontWeight = '600';
    badge.style.letterSpacing = '0.04em';
    badge.style.padding = '0.15rem 0.45rem';
    badge.style.border = '1px solid var(--rule, #d8d4cc)';
    badge.style.borderRadius = '3px';
    head.appendChild(badge);
    sec.appendChild(head);

    const kal = data.kalibracija || {};
    if (data.status === 'active' && data.prognoza_sutra) {
      const ps = data.prognoza_sutra;
      const sub = mk('p', null, en
        ? `Belgrade (${ps.datum_sutra}) · 24h forecast from CAMS grid point, verified over 14 days against SEPA S146.`
        : `Beograd (${ps.datum_sutra}) · 24 h prognoza sa CAMS mrežne tačke, verifikovana tokom 14 dana prema SEPA S146.`);
      sub.style.margin = '0.35rem 0 0.7rem';
      sub.style.fontSize = '0.88rem';
      sub.style.color = 'var(--muted, #555)';
      sec.appendChild(sub);

      const tabs = mk('div');
      tabs.style.display = 'flex';
      tabs.style.flexWrap = 'wrap';
      tabs.style.gap = '0.35rem';
      tabs.style.marginBottom = '0.6rem';
      const bodyWrap = mk('div');

      function drawMetric() {
        bodyWrap.textContent = '';
        const meta = METRICS.find(m => m[0] === _sel) || METRICS[0];
        const sum = ps.summary && ps.summary[_sel];
        const dec = _sel === 'co' ? 2 : 1;
        if (sum) {
          const line = mk('p', null, en
            ? `${meta[1]} tomorrow: mean ${fmt(sum.mean, dec)} ${meta[2]} (min ${fmt(sum.min, dec)}, peak ${fmt(sum.max, dec)} at ${sum.peak_hour || '—'}).`
            : `${meta[1]} sutra: prosek ${fmt(sum.mean, dec)} ${meta[2]} (min ${fmt(sum.min, dec)}, vrh ${fmt(sum.max, dec)} u ${sum.peak_hour || '—'}).`);
          line.style.margin = '0 0 0.4rem';
          line.style.fontSize = '0.9rem';
          bodyWrap.appendChild(line);
        }
        bodyWrap.appendChild(buildSvg(ps.hours_local || [], (ps.hourly && ps.hourly[_sel]) || [], meta[2]));
      }

      for (const [k, lb] of METRICS) {
        const b = mk('button', null, lb);
        b.type = 'button';
        b.style.padding = '0.2rem 0.55rem';
        b.style.fontSize = '0.82rem';
        b.style.border = '1px solid var(--rule, #d8d4cc)';
        b.style.borderRadius = '3px';
        b.style.cursor = 'pointer';
        b.style.background = k === _sel ? 'var(--accent, #1f5a7a)' : 'transparent';
        b.style.color = k === _sel ? '#fff' : 'inherit';
        b.addEventListener('click', () => {
          _sel = k;
          for (const ch of tabs.children) {
            const act = ch.textContent === lb;
            ch.style.background = act ? 'var(--accent, #1f5a7a)' : 'transparent';
            ch.style.color = act ? '#fff' : 'inherit';
          }
          drawMetric();
        });
        tabs.appendChild(b);
      }
      sec.appendChild(tabs);
      drawMetric();
      sec.appendChild(bodyWrap);
      sec.appendChild(renderVerifTable(data.verifikacija));
    } else {
      const pct = Math.min(100, Math.round(((kal.days_measured || 0) / (kal.days_required || 14)) * 100));
      const msg = mk('p', null, en
        ? `Public forecast values are withheld until 14 full days of +24h forecast error are measured against SEPA S146 stations (${kal.days_measured || 0}/${kal.days_required || 14} days; ${kal.snapshots_collected || 0} hourly snapshots stored; earliest public date: ${kal.earliest_public_date || '—'}).`
        : `Brojevi prognoze se ne objavljuju dok ne skupimo 14 punih dana izmerene +24 h greške prema SEPA S146 stanicama (${kal.days_measured || 0}/${kal.kalibracija_dana || kal.days_required || 14} dana; sačuvano ${kal.snapshots_collected || 0} satnih snimaka; najraniji javni prikaz: ${kal.earliest_public_date || '—'}).`);
      msg.style.margin = '0.45rem 0 0.6rem';
      msg.style.fontSize = '0.88rem';
      sec.appendChild(msg);

      const bar = mk('div');
      bar.style.height = '6px';
      bar.style.borderRadius = '3px';
      bar.style.background = 'var(--rule, #e2ded6)';
      bar.style.overflow = 'hidden';
      const fill = mk('div');
      fill.style.height = '100%';
      fill.style.width = `${pct}%`;
      fill.style.background = 'var(--accent, #1f5a7a)';
      bar.appendChild(fill);
      sec.appendChild(bar);

      const hasAnyPairs = data.verifikacija && Object.values(data.verifikacija).some(v => v && v.n_pairs > 0);
      if (hasAnyPairs) sec.appendChild(renderVerifTable(data.verifikacija));
    }

    const foot = mk('p', null, en
      ? 'Source: Open-Meteo Air Quality (CAMS European), CC BY 4.0 · Decision D-006 A2 · Model grid forecast, never stored as an observation.'
      : 'Izvor: Open-Meteo Air Quality (CAMS European), CC BY 4.0 · Odluka D-006 A2 · Mrežna prognoza modela, nikad merenje.');
    foot.style.margin = '0.6rem 0 0';
    foot.style.fontSize = '0.78rem';
    foot.style.color = 'var(--muted, #666)';
    sec.appendChild(foot);
    return sec;
  }

  async function mountIfNeeded() {
    const h = (location.hash || '#danas').replace(/^#/, '').split('?')[0];
    if (h !== 'podaci') return;
    const view = document.getElementById('view');
    if (!view || document.getElementById('beops-prognoza-vazduh')) return;
    const data = await loadData();
    if (!data) return;
    if (document.getElementById('beops-prognoza-vazduh')) return;
    view.appendChild(renderCard(data));
  }

  function scheduleMount() {
    setTimeout(mountIfNeeded, 120);
    setTimeout(mountIfNeeded, 600);
  }
  window.addEventListener('hashchange', scheduleMount);
  document.addEventListener('DOMContentLoaded', () => {
    scheduleMount();
    const view = document.getElementById('view');
    if (view && typeof MutationObserver !== 'undefined') {
      new MutationObserver(() => {
        if ((location.hash || '').startsWith('#podaci') && !document.getElementById('beops-prognoza-vazduh')) {
          mountIfNeeded();
        }
      }).observe(view, { childList: true });
    }
  });
})();
