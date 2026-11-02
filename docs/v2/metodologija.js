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
