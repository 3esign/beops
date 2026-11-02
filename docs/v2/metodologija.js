/* BEOPS v2 · Metodološki list (B6) — poseban lenji modul van 64 KB budžeta shella.
   Registruje se u #o: renderMeto(body) crta tabelu izvora iz
   state/metodologija.json (COLLECTORS.json ⊗ LEDGER.jsonl). Naučni sloj #o:
   izvor, saglasnost (+ dokaz putanja), kada (cadence), izdavačev sat (offset),
   vremenska etiketa. Bez saglasnosti se pokazuje kao stanje, ne skriva. */
'use strict';
/* global el, STATE, T, absTime */

function metoSaglasnostCap(i) {
  const s = i.saglasnost || {};
  if (!s.uzeto) return T().metoBezSaglasnosti;
  if (!s.dozvoljeno) return T().metoSaglasnostNe;
  return T().metoSaglasnostDa + ' · ' + i.sid + '@' + s.uzeto.replace(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2}).*$/, '$1-$2-$3 $4:$5Z');
}
function metoSat(i) {
  if (!i.sat) return '\u2014';
  const off = i.sat.offset_s | 0;
  const sign = off < 0 ? '\u2212' : '+';
  const a = Math.abs(off);
  return sign + Math.floor(a / 3600) + 'h' + (a % 3600 ? (a % 3600) / 60 + 'm' : '') + ' (' + i.sat.id + ')';
}
function metoCadence(s) {
  const sec = s.kada_s | 0;
  return sec % 86400 === 0 ? (sec / 86400) + ' d' : sec % 3600 === 0 ? (sec / 3600) + ' h' : sec % 60 === 0 ? (sec / 60) + ' min' : sec + ' s';
}
function viewMeto(body) {
  body.appendChild(el('h2', null, T().metoTitle));
  const d = STATE.meto || STATE.metodologija;
  if (!d || !Array.isArray(d.izvori) || !d.izvori.length) {
    body.appendChild(el('p', 'sub', T().tangierUcitavanje));
    return;
  }
  body.appendChild(el('p', 'sub', T().metoSub + ' (' + d.akt + '/' + d.uk + ' · ' + T().verzija + ': ' + absTime(d.generated_at) + ')'));
  const tbl = el('table', 'kv');
  const th = el('thead'); const trh = el('tr');
  for (const h of [T().metoIzvor, T().metoSaglasnost, T().metoKada, T().metoSat, T().metoVreme]) trh.appendChild(el('th', null, h));
  th.appendChild(trh); tbl.appendChild(th);
  const tb = el('tbody');
  for (const i of d.izvori) {
    const tr = el('tr');
    const tdIz = el('td');
    tdIz.textContent = i.ime + ' ';
    tdIz.appendChild(el('span', 'meta', i.sid + (i.aktivan ? '' : ' · ' + T().metoIskljucen)));
    tr.appendChild(tdIz);
    const s = i.saglasnost || {};
    const capTd = el('td');
    const capSpan = el('span', null, metoSaglasnostCap(i));
    if (s.dokaz) capSpan.title = T().metoDokaz + ': ' + s.dokaz;
    capTd.appendChild(capSpan);
    tr.appendChild(capTd);
    tr.appendChild(el('td', null, metoCadence(i)));
    tr.appendChild(el('td', null, metoSat(i)));
    tr.appendChild(el('td', null, i.vreme ? i.vreme : '\u2014'));
    tb.appendChild(tr);
  }
  tbl.appendChild(tb);
  body.appendChild(tbl);
  if ((d.bez_saglasnosti || []).length)
    body.appendChild(el('p', 'razlog', T().metoBezSaglasnosti + ': ' + d.bez_saglasnosti.join(', ')));
  body.appendChild(dlRow([
    ['state/metodologija.json', 'metodologija (.json)'],
    ['state/observations-hourly.csv', T().preuzmiCsv],
    ['state/datapackage.json', 'datapackage.json'],
    ['CITATION.cff', T().preuzmiCff],
  ]));
}
renderMeto = viewMeto;
window.BEOPS_METO = viewMeto;

/* B4 + B5: pojas nesigurnosti (IQR p25–p75 + ±U 95 %) i citirani paket podataka */
function b4Attach(s, pts) {
  const uMap = {};
  for (const u of (s.uncertainty && s.uncertainty.points) || []) uMap[Date.parse(u[0] + ':00:00Z')] = u;
  const lcMap = {};
  for (const l of (s.low_cost && s.low_cost.points) || []) lcMap[Date.parse(l[0] + ':00:00Z')] = l;
  for (const p of pts) {
    const u = uMap[p.x];
    if (u) { p.p25 = u[1]; p.p75 = u[2]; p.u = u[3]; }
    const lc = lcMap[p.x];
    if (lc) p.lc = lc[1];
  }
  return pts;
}
function b4Bounds(id, pts, y0, y1) {
  const s = STATE.serije[id] || {};
  for (const l of (s.low_cost && s.low_cost.points) || []) {
    if (Number.isFinite(l[1])) { y0 = Math.min(y0, l[1]); y1 = Math.max(y1, l[1]); }
  }
  return [y0, y1];
}
function drawB4(svg, id, pts, sx, sy) {
  const s = STATE.serije[id] || {};
  let iqrBand = '', run = [];
  const lo = p => Math.max(id === 'pm25' || id === 'pm10' ? 0 : -Infinity, Math.min(p.p25 ?? p.mean, p.mean - (p.u || 0)));
  const hi = p => Math.max(p.p75 ?? p.mean, p.mean + (p.u || 0));
  const flush = () => {
    if (run.length > 1) iqrBand += run.map((p, i) => (i ? 'L' : 'M') + sx(p.x).toFixed(1) + ' ' + sy(hi(p)).toFixed(1)).join(' ') +
      run.slice().reverse().map(p => 'L' + sx(p.x).toFixed(1) + ' ' + sy(lo(p)).toFixed(1)).join(' ') + 'Z';
    run = [];
  };
  pts.forEach((p, i) => {
    if (i && p.x - pts[i - 1].x > 54e5) flush();
    if (p.p25 !== undefined || p.u !== undefined) run.push(p);
  });
  flush();
  if (iqrBand) svg.appendChild(mk('path', { d: iqrBand, 'class': 'band-iqr' }));
  const lcPts = ((s.low_cost && s.low_cost.points) || []).map(l => ({ x: Date.parse(l[0] + ':00:00Z'), v: l[1] }))
    .filter(l => Number.isFinite(l.x) && Number.isFinite(l.v) && l.x >= pts[0].x && l.x <= pts[pts.length - 1].x);
  if (lcPts.length > 1) {
    let dLc = '';
    lcPts.forEach((l, i) => {
      const gap = i && l.x - lcPts[i - 1].x > 54e5;
      dLc += (i && !gap ? 'L' : 'M') + sx(l.x).toFixed(1) + ' ' + sy(l.v).toFixed(1) + ' ';
    });
    svg.appendChild(mk('path', { d: dLc, 'class': 'lc-line' }));
  }
}
function ttB4(id, p) {
  const unit = id === 'temperature' ? '°C' : id === 'humidity' ? '%' : 'µg/m³';
  const head = fmtNum(p.mean) + (p.u ? ' ± ' + fmtNum(p.u) : '') + ' ' + unit;
  const parts = [absTime(new Date(p.x).toISOString())];
  if (p.p25 !== undefined && p.p75 !== undefined) parts.push('p25–p75 ' + fmtNum(p.p25) + '–' + fmtNum(p.p75));
  if (p.min !== null && p.min !== undefined) parts.push('min ' + fmtNum(p.min) + ' / max ' + fmtNum(p.max));
  parts.push(p.n + ' ' + T().mapaStations);
  if (p.lc !== undefined) parts.push('S04 ' + fmtNum(p.lc) + ' ' + unit);
  return [head, parts.join(' · ')];
}
function podaciNote(id) {
  const s = STATE.serije[id] || {};
  return T().minMax + ' · ' + T().iqrBand + (s.low_cost ? ' · ' + T().lcLine : '') + ' · ' + T().q7;
}
function podaciLinks(id) {
  return [
    ['state/serije/' + id + '.json', T().preuzmiSerija],
    ['state/observations-hourly.csv', T().preuzmiCsv],
    ['state/datapackage.json', 'datapackage.json'],
    ['state/kolokacija.json', T().preuzmiKolok],
    ['CITATION.cff', T().preuzmiCff],
  ];
}

function deltaEl(d, neutral, unit) {
  const s = el('span', 'delta');
  if (d === null || d === undefined || !Number.isFinite(d)) { s.textContent = '—'; return s; }
  const dir = Math.abs(d) < 0.15 ? 'flat' : (d > 0 ? 'up' : 'down');
  const cls = neutral ? 'flat' : dir;
  const arrow = dir === 'flat' ? '→' : (d > 0 ? '▲' : '▼');
  s.appendChild(el('span', cls, arrow + ' ' + (d > 0 ? '+' : '') + fmtNum(d, 1) + (unit ? ' ' + unit : '')));
  s.appendChild(document.createTextNode(' ' + T().promena24h));
  return s;
}

function sparkTile(id) {
  const box = el('span', 'spark');
  const pts = seriesPoints(id);
  if (pts.length < 2) return box;
  const W = 116, H = 32, P = 3;
  const x0 = pts[0].x, x1 = pts[pts.length - 1].x || (x0 + 1);
  let y0 = Infinity, y1 = -Infinity;
  for (const p of pts) { if (p.mean < y0) y0 = p.mean; if (p.mean > y1) y1 = p.mean; }
  if (y1 - y0 < 1e-6) { y0 -= 1; y1 += 1; }
  const sx = t => P + (t - x0) / (x1 - x0) * (W - 2 * P);
  const sy = v => H - P - (v - y0) / (y1 - y0) * (H - 2 * P);
  const svg = mk('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img' });
  const meta = SERIES_META[id] || {};
  svg.setAttribute('aria-label', (meta[LANG] || id) + ' 7d');
  let dLine = '';
  pts.forEach((p, i) => { dLine += (i ? 'L' : 'M') + sx(p.x).toFixed(1) + ' ' + sy(p.mean).toFixed(1) + ' '; });
  const dArea = dLine + `L${sx(pts[pts.length - 1].x).toFixed(1)} ${H - P} L${sx(pts[0].x).toFixed(1)} ${H - P} Z`;
  svg.appendChild(mk('path', { d: dArea, fill: 'var(--green)', 'fill-opacity': '0.12' }));
  svg.appendChild(mk('path', { d: dLine, fill: 'none', stroke: 'var(--green)', 'stroke-width': '1.7', 'stroke-linecap': 'round' }));
  const last = pts[pts.length - 1];
  svg.appendChild(mk('circle', { cx: sx(last.x).toFixed(1), cy: sy(last.mean).toFixed(1), r: '2.6', fill: 'var(--green)' }));
  svg.addEventListener('pointermove', ev => {
    const r = svg.getBoundingClientRect();
    const fx = (ev.clientX - r.left) / r.width * W;
    let best = 0, bd = Infinity;
    for (let i = 0; i < pts.length; i++) { const dd = Math.abs(sx(pts[i].x) - fx); if (dd < bd) { bd = dd; best = i; } }
    const [hv, hs] = ttB4(id, pts[best]);
    showTT(ev.clientX, ev.clientY, hv, hs);
  });
  svg.addEventListener('pointerleave', hideTT);
  box.appendChild(svg);
  return box;
}

function heroPulsGrid() {
  const wrap = el('section', 'puls-sekcija');
  const P = STATE.puls || {};
  const cs = P.city_status || {};
  const cm = P.current_metrics || {};
  const d24 = P.deltas_24h || {};
  const eq = cs.eaqi || {};
  const met = cm.meteo || {};
  const grid = el('div', 'metrics');

  const hero = el('article', 'metric wide hero-card');
  const hTop = el('div', 'hero-top');
  hTop.appendChild(el('span', 'label', T().pulsSadaTitle));
  if (P.as_of) hTop.appendChild(stampEl(P.as_of, 5));
  hero.appendChild(hTop);

  const mainRow = el('div', 'hero-main');
  const bigVal = el('div', 'value');
  bigVal.appendChild(document.createTextNode(cs.aqi_us != null ? String(cs.aqi_us) : '—'));
  bigVal.appendChild(el('small', null, ' AQI · ' + (LANG === 'sr' ? (cs.category_sr || '') : (cs.category_en || ''))));
  mainRow.appendChild(bigVal);

  const badges = el('div', 'hero-badges');
  if (eq.level) badges.appendChild(el('span', 'tag eaqi-tag lvl-' + eq.level, 'EAQI ' + eq.level + '/6 · ' + (LANG === 'sr' ? eq.label_sr : eq.label_en)));
  if (cs.dominant_pollutant) {
    const domKey = cs.dominant_pollutant;
    const domLbl = (PARAM_LABEL[domKey] && PARAM_LABEL[domKey][LANG]) || domKey.toUpperCase();
    badges.appendChild(el('span', 'tag outline', T().glavniZagadjivac + ': ' + domLbl));
  }
  mainRow.appendChild(badges);
  hero.appendChild(mainRow);

  const bar = el('div', 'eaqi-bar');
  const eqSr = ['1 Dobar', '2 Prihvatljiv', '3 Umeren', '4 Loš', '5 Veoma loš', '6 Izuzetno loš'];
  const eqEn = ['1 Good', '2 Fair', '3 Moderate', '4 Poor', '5 Very poor', '6 Extremely poor'];
  for (let i = 1; i <= 6; i++) bar.appendChild(el('span', 'eaqi-seg s' + i + (eq.level === i ? ' active' : ''), (LANG === 'sr' ? eqSr : eqEn)[i - 1]));
  hero.appendChild(bar);

  const adv = LANG === 'sr'
    ? [eq.advice_general_sr || cs.summary_sr, eq.advice_sensitive_sr].filter(Boolean).join(' ')
    : [eq.advice_general_en || cs.summary_en, eq.advice_sensitive_en].filter(Boolean).join(' ');
  if (adv) hero.appendChild(el('p', 'hero-advice', adv));

  const pills = el('div', 'hero-pills');
  if (met.temperature != null) pills.appendChild(el('span', 'pill', fmtNum(met.temperature, 1) + ' °C'));
  if (met.humidity != null) pills.appendChild(el('span', 'pill', fmtNum(met.humidity, 0) + ' % RH'));
  if (met.wind_speed != null) pills.appendChild(el('span', 'pill', fmtNum(met.wind_speed, 1) + ' m/s'));
  if (met.pressure != null) pills.appendChild(el('span', 'pill', fmtNum(met.pressure, 0) + ' hPa'));
  if (cm.pm25 && cm.pm25.sensors_count) pills.appendChild(el('span', 'pill ref', cm.pm25.sensors_count + ' SEPA ' + T().stanicaKratko));
  if (cm.low_cost && cm.low_cost.sensors_count) pills.appendChild(el('span', 'pill', cm.low_cost.sensors_count + ' S04 (PM2.5 ' + fmtNum(cm.low_cost.pm25_mean, 1) + ')'));
  hero.appendChild(pills);
  grid.appendChild(hero);

  const addMetric = (label, val, unit, subTxt, footLeft, sparkId) => {
    const m = el('article', 'metric');
    m.appendChild(el('span', 'label', label));
    const v = el('div', 'value', val === null || val === undefined || !Number.isFinite(val) ? '—' : fmtNum(val, 1));
    if (unit) v.appendChild(el('small', null, ' ' + unit));
    m.appendChild(v);
    m.appendChild(el('div', 'cat', subTxt || ''));
    const f = el('div', 'foot');
    if (footLeft) f.appendChild(footLeft);
    if (sparkId) f.appendChild(sparkTile(sparkId));
    m.appendChild(f);
    grid.appendChild(m);
  };
  const stSub = obj => obj
    ? T().vrhStanica + ' ' + fmtNum(obj.max, 1) + (obj.max_station ? ' · ' + obj.max_station : '') + ' · ' + (obj.sensors_count || 0) + ' ' + T().stanicaKratko
    : '';
  addMetric('PM2.5 · referentna mreža', cm.pm25 && cm.pm25.mean, 'µg/m³', stSub(cm.pm25), deltaEl(d24.pm25_delta, false, 'µg/m³'), 'pm25');
  addMetric('PM10 · referentna mreža', cm.pm10 && cm.pm10.mean, 'µg/m³', stSub(cm.pm10), deltaEl(d24.pm10_delta, false, 'µg/m³'), 'pm10');
  addMetric('NO₂ · azot-dioksid', cm.no2 && cm.no2.mean, 'µg/m³', stSub(cm.no2),
    cm.no2 ? el('span', 'delta', T().raspon + ' ' + fmtNum(cm.no2.min, 1) + '–' + fmtNum(cm.no2.max, 1) + ' µg/m³') : null, null);
  addMetric('O₃ · prizemni ozon', cm.o3 && cm.o3.mean, 'µg/m³', stSub(cm.o3),
    cm.o3 ? el('span', 'delta', T().raspon + ' ' + fmtNum(cm.o3.min, 1) + '–' + fmtNum(cm.o3.max, 1) + ' µg/m³') : null, null);
  addMetric(LANG === 'sr' ? 'Temperatura' : 'Temperature', met.temperature, '°C',
    (met.wind_speed != null ? (LANG === 'sr' ? 'vetar ' : 'wind ') + fmtNum(met.wind_speed, 1) + ' m/s' : '') +
    (met.pressure != null ? ' · ' + fmtNum(met.pressure, 0) + ' hPa' : ''),
    deltaEl(d24.temp_delta, true, '°C'), 'temperature');
  addMetric(LANG === 'sr' ? 'Relativna vlažnost' : 'Relative humidity', met.humidity, '%',
    (cm.low_cost && cm.low_cost.high_humidity_flag) ? (LANG === 'sr' ? '≥ 75 % · oprez za optičke senzore' : '≥ 75% · optical sensor bias') : 'RHMZ / SEPA',
    el('span', 'delta', met.humidity >= 75 ? 'RH ≥ 75 %' : 'OK'), 'humidity');
  wrap.appendChild(grid);
  return wrap;
}

function danasTrendBlok() {
  const sec = el('section', 'danas-trend-box');
  const head = el('div', 'chart-title');
  const tabs = el('div', 'chart-tabs');
  const chartSlot = el('div');
  const draw = () => {
    tabs.textContent = '';
    for (const id of SERIES_IDS) {
      const b = el('button', id === DANAS_SERIJA ? 'active' : null, LANG === 'sr' ? SERIES_META[id].sr : SERIES_META[id].en);
      b.type = 'button';
      b.addEventListener('click', () => { DANAS_SERIJA = id; draw(); });
      tabs.appendChild(b);
    }
    chartSlot.textContent = '';
    chartSlot.appendChild(bigChart(DANAS_SERIJA, chartSlot.clientWidth || 1000));
    chartSlot.appendChild(el('p', 'sub', podaciNote(DANAS_SERIJA)));
  };
  head.appendChild(tabs);
  const aPod = el('a', 'vodic-link', T().vodicOtvoriPodatke);
  aPod.href = '#podaci';
  head.appendChild(aPod);
  sec.appendChild(head);
  sec.appendChild(chartSlot);
  draw();
  return sec;
}
