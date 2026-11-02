/* BEOPS v2 · Moj kraj (C2) + obogaćeni vizuelni moduli za #danas — poseban modul van 64 KB budžeta shella.
   Registruje rutu `kraj` u VIEWS i pruža vizuelne komponente za #danas (heroPulsGrid, vodicGrid, danasTrendBlok);
   učitava se posle app.js (defer redosled u index.html). */
'use strict';
const KRAJ_OPSTINE = [
  ['Barajevo', 'Барајево', 44.583, 20.583],
  ['Voždovac', 'Вождовац', 44.768, 20.482],
  ['Vračar', 'Врачар', 44.794, 20.481],
  ['Grocka', 'Гроцка', 44.745, 20.717],
  ['Zvezdara', 'Звездара', 44.810, 20.497],
  ['Zemun', 'Земун', 44.843, 20.404],
  ['Lazarevac', 'Лазаревац', 44.388, 20.258],
  ['Mladenovac', 'Младеновац', 44.433, 20.717],
  ['Novi Beograd', 'Нови Београд', 44.806, 20.417],
  ['Obrenovac', 'Обреновац', 44.667, 20.200],
  ['Palilula', 'Палилула', 44.824, 20.492],
  ['Rakovica', 'Раковица', 44.766, 20.443],
  ['Savski venac', 'Савски венац', 44.796, 20.461],
  ['Sopot', 'Сопот', 44.478, 20.575],
  ['Stari grad', 'Стари град', 44.817, 20.456],
  ['Surčin', 'Сурчин', 44.800, 20.300],
  ['Čukarica', 'Чукарица', 44.783, 20.412],
];
const KRAJ_KEY = 'beops-kraj';
let DANAS_SERIJA = 'pm25';

function krajNorm(s) { return (s || '').toLowerCase().replace(/\s+/g, ' ').trim(); }
function krajIzbor() { return localStorage.getItem(KRAJ_KEY) || ''; }
function krajKm(la1, lo1, la2, lo2) {
  const r = Math.PI / 180, dLa = (la2 - la1) * r, dLo = (lo2 - lo1) * r;
  const a = Math.sin(dLa / 2) ** 2 + Math.cos(la1 * r) * Math.cos(la2 * r) * Math.sin(dLo / 2) ** 2;
  return 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function krajNajblizaRef(opEntry) {
  const M = STATE.mapa;
  if (!M || !Array.isArray(M.stations) || !opEntry) return null;
  const [, , la, lo] = opEntry;
  let bestRef = null, bestRefD = Infinity, uKrugu = 0;
  for (const st of M.stations) {
    if (!Number.isFinite(st.la) || !Number.isFinite(st.lo)) continue;
    const d = krajKm(la, lo, st.la, st.lo);
    if (d <= 1.5) uKrugu++;
    if (st.cls === 'reference' && d < bestRefD) { bestRefD = d; bestRef = st; }
  }
  return bestRef ? { st: bestRef, d: bestRefD, uKrugu } : null;
}

function krajStaniceBlok(telo, opEntry) {
  const found = krajNajblizaRef(opEntry);
  if (!found) return;
  const { st: bestRef, d: bestRefD, uKrugu } = found;
  const box = el('div', 'kraj-ref');
  box.appendChild(el('h3', null, T().krajRefStanica + ': ' + bestRef.n + ' (' + fmtNum(bestRefD, 1) + ' km)'));
  box.appendChild(el('p', 'meta', T().klasaRef + ' · ' + uKrugu + ' ' + T().znanjeSenzora));
  const rows = (bestRef.r || []).filter(r => r.v !== undefined).map(r => {
    const pl = PARAM_LABEL[r.p];
    const st = document.createDocumentFragment();
    st.appendChild(stateGlyph(r.s, 11));
    st.appendChild(document.createTextNode(' ' + mapStateWord(r.s)));
    return [
      pl ? (LANG === 'sr' ? pl.sr : pl.en) : r.p,
      fmtNum(r.v, Math.abs(r.v) < 10 ? 2 : 1) + ' ' + (UNIT_LABEL[r.u] || r.u || ''),
      st,
      r.tc ? absTime(r.tc) : (r.t ? absTime(r.t) : '—'),
    ];
  });
  if (rows.length) box.appendChild(mkTable([T().dosijeParam, T().dosijeVrednost, T().dosijeStanje, T().dosijeVreme], rows));
  telo.appendChild(box);
}

function krajBezNajava(telo, prozor) {
  const p = Array.isArray(prozor) ? prozor : [];
  telo.appendChild(el('p', 'razlog', T().krajBezNajava.replace('{od}', p[0] || '—').replace('{do}', p[1] || '—')));
  telo.appendChild(el('p', 'hint', T().krajNapomena));
  telo.appendChild(krajFeedovi());
}

function krajSadrzaj(koren) {
  const telo = el('div', 'kraj-telo');
  const izbor = krajIzbor();
  const opEntry = KRAJ_OPSTINE.find(x => krajNorm(x[0]) === krajNorm(izbor) || krajNorm(x[1]) === krajNorm(izbor));
  if (!opEntry) {
    telo.appendChild(el('p', 'hint', T().krajNemaIzbora));
    telo.appendChild(krajFeedovi());
    koren.appendChild(telo);
    return;
  }
  Promise.all([loadMapa(), loadMapaNews()]).then(() => {
    telo.textContent = '';
    krajStaniceBlok(telo, opEntry);
    const mn = STATE.mapaNews;
    const isklj = (mn && mn.slojevi && mn.slojevi.iskljucenja) || null;
    const prozor = (isklj && isklj.prozor) || [];
    const spisak = (isklj && Array.isArray(isklj.opstine)) ? isklj.opstine : [];
    telo.appendChild(el('h3', null, T().slojIskljucenja));
    if (!spisak.length) {
      krajBezNajava(telo, prozor);
      telo.appendChild(el('p', 'hint', T().krajSlojPrazan));
      koren.appendChild(telo);
      return;
    }
    const oRaw = spisak.find(x => {
      const d = (x && x.data) || x || {};
      const n = krajNorm(d.ime);
      return n === krajNorm(opEntry[0]) || n === krajNorm(opEntry[1]);
    });
    const o = oRaw && (oRaw.data || oRaw);
    if (!o) {
      krajBezNajava(telo, prozor);
      koren.appendChild(telo);
      return;
    }
    const mesta = o.mesta || [];
    const p = Array.isArray(prozor) ? prozor : [];
    telo.appendChild(el('p', 'meta', T().krajProzor + ': ' + (p[0] || '—') + '–' + (p[1] || '—') + ' · ' +
      (o.broj_mesta != null ? o.broj_mesta : mesta.length) + ' ' + T().krajMesta));
    for (const m of mesta) {
      const pm = el('p', 'isklj-mesto');
      pm.appendChild(el('b', null, m.ime));
      pm.appendChild(document.createTextNode(' — ' + (m.prozori || []).join('; ')));
      telo.appendChild(pm);
    }
    telo.appendChild(el('p', 'hint', T().krajNapomena));
    telo.appendChild(krajFeedovi());
    koren.appendChild(telo);
  });
}

function krajFeedovi() {
  const box = el('div', 'kraj-feedovi');
  box.appendChild(el('b', null, T().krajFeedovi));
  const ics = el('a', null, T().krajIcs);
  ics.href = 'state/kultura.ics'; ics.rel = 'alternate';
  const rss = el('a', null, T().krajRss);
  rss.href = 'state/iskljucenja.rss'; rss.rel = 'alternate'; rss.type = 'application/rss+xml';
  box.appendChild(ics);
  box.appendChild(rss);
  return box;
}

function viewKraj(koren) {
  koren.textContent = '';
  koren.appendChild(sectionHead(null, T().krajTitle, T().krajIntro));
  const red = el('div', 'kraj-izbor');
  const lab = el('label', null, T().krajOpstina);
  lab.htmlFor = 'kraj-opstina';
  const sel = el('select');
  sel.id = 'kraj-opstina';
  const ph = document.createElement('option');
  ph.value = '';
  ph.textContent = T().krajIzaberi;
  sel.appendChild(ph);
  for (const [ime] of KRAJ_OPSTINE) {
    const o = document.createElement('option');
    o.value = ime;
    o.textContent = ime;
    sel.appendChild(o);
  }
  sel.value = krajIzbor();
  sel.addEventListener('change', () => {
    if (sel.value) localStorage.setItem(KRAJ_KEY, sel.value);
    else localStorage.removeItem(KRAJ_KEY);
    const stara = koren.querySelector('.kraj-telo');
    if (stara) stara.remove();
    krajSadrzaj(koren);
  });
  red.appendChild(lab);
  red.appendChild(sel);
  koren.appendChild(red);
  krajSadrzaj(koren);
}
VIEWS.kraj = viewKraj;

/* ── Obogaćeni #danas moduli (Hero Puls, 7d Sparkline, Vodič 4 kartice, 7d Trend) ── */
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
  let dLine = '', dArea = '';
  pts.forEach((p, i) => {
    const cmd = i ? 'L' : 'M';
    dLine += cmd + sx(p.x).toFixed(1) + ' ' + sy(p.mean).toFixed(1) + ' ';
  });
  dArea = dLine + `L${sx(pts[pts.length - 1].x).toFixed(1)} ${H - P} L${sx(pts[0].x).toFixed(1)} ${H - P} Z`;
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

  /* 1. Široka Hero kartica: AQI + EAQI skala + zdravstveni savet + meteo pilule */
  const hero = el('article', 'metric wide hero-card');
  const hTop = el('div', 'hero-top');
  hTop.appendChild(el('span', 'label', T().pulsSadaTitle));
  if (P.as_of) hTop.appendChild(stampEl(P.as_of, 5));
  hero.appendChild(hTop);

  const mainRow = el('div', 'hero-main');
  const bigVal = el('div', 'value');
  bigVal.appendChild(document.createTextNode(cs.aqi_us != null ? String(cs.aqi_us) : '—'));
  const unitSm = el('small', null, ' AQI · ' + (LANG === 'sr' ? (cs.category_sr || '') : (cs.category_en || '')));
  bigVal.appendChild(unitSm);
  mainRow.appendChild(bigVal);

  const badges = el('div', 'hero-badges');
  if (eq.level) {
    const bEq = el('span', 'tag eaqi-tag lvl-' + eq.level, 'EAQI ' + eq.level + '/6 · ' + (LANG === 'sr' ? eq.label_sr : eq.label_en));
    badges.appendChild(bEq);
  }
  if (cs.dominant_pollutant) {
    const domKey = cs.dominant_pollutant;
    const domLbl = (PARAM_LABEL[domKey] && PARAM_LABEL[domKey][LANG]) || domKey.toUpperCase();
    badges.appendChild(el('span', 'tag outline', T().glavniZagadjivac + ': ' + domLbl));
  }
  mainRow.appendChild(badges);
  hero.appendChild(mainRow);

  /* 6-stepena EAQI traka */
  const bar = el('div', 'eaqi-bar');
  const eqLabelsSr = ['1 Dobar', '2 Prihvatljiv', '3 Umeren', '4 Loš', '5 Veoma loš', '6 Izuzetno loš'];
  const eqLabelsEn = ['1 Good', '2 Fair', '3 Moderate', '4 Poor', '5 Very poor', '6 Extremely poor'];
  for (let i = 1; i <= 6; i++) {
    const seg = el('span', 'eaqi-seg s' + i + (eq.level === i ? ' active' : ''), (LANG === 'sr' ? eqLabelsSr : eqLabelsEn)[i - 1]);
    bar.appendChild(seg);
  }
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

  /* Helper za pojedinačnu metričku karticu */
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

function vodicGrid() {
  const grid = el('div', 'vodic-grid');
  const P = STATE.puls || {};
  const cm = P.current_metrics || {};
  const cs = P.city_status || {};
  const eq = cs.eaqi || {};

  /* Kartica 1: Vazduh i preporuka za izlazak (aktivni koraci bez isteklih rokova) */
  const c1 = el('article', 'vodic-card accent-green');
  c1.appendChild(el('span', 'eyebrow', '01 · ' + (LANG === 'sr' ? 'ZDRAVLJE I IZLAZAK' : 'HEALTH & OUTDOORS')));
  c1.appendChild(el('h3', null, T().vodicVazduh));
  const svezeKartice = ((STATE.misli && STATE.misli.thoughts) || [])
    .filter(t => t.state === 'accepted' && t.za_gradjanina && typeof t.za_gradjanina === 'object' && t.za_gradjanina.akcija)
    .filter(t => {
      const vd = t.za_gradjanina.vazi_do;
      if (vd && Number.isFinite(Date.parse(vd)) && Date.parse(vd) <= Date.now()) return false;
      return Date.now() - Date.parse(t.at) < 36 * 3600e3;
    })
    .sort((a, b) => Date.parse(b.at) - Date.parse(a.at));
  if (svezeKartice.length) {
    c1.appendChild(el('p', 'vodic-lead', svezeKartice[0].za_gradjanina.akcija));
  } else {
    c1.appendChild(el('p', 'vodic-lead', (LANG === 'sr' ? eq.advice_general_sr : eq.advice_general_en) || T().karticeEmpty));
  }
  const ul1 = el('div', 'vodic-kv');
  if (cm.pm25) ul1.appendChild(el('span', 'pill', 'PM2.5: ' + fmtNum(cm.pm25.min, 1) + '–' + fmtNum(cm.pm25.max, 1) + ' µg/m³ (' + (cm.pm25.max_station || '') + ')'));
  if (cm.no2 && cm.no2.max != null) ul1.appendChild(el('span', 'pill', 'NO₂ ' + T().vrhStanica + ': ' + fmtNum(cm.no2.max, 1) + ' µg/m³ (' + (cm.no2.max_station || '') + ')'));
  c1.appendChild(ul1);
  const a1 = el('a', 'vodic-link', T().vodicOtvoriMapu);
  a1.href = '#mapa';
  c1.appendChild(a1);
  grid.appendChild(c1);

  /* Kartica 2: Slobodna mesta u garažama (iz istaknuto / mapa S10) */
  const c2 = el('article', 'vodic-card accent-blue');
  c2.appendChild(el('span', 'eyebrow', '02 · ' + (LANG === 'sr' ? 'MOBILNOST I PARKING' : 'MOBILITY & PARKING')));
  c2.appendChild(el('h3', null, T().vodicParking));
  const garaze = [];
  for (const st of (STATE.istaknuto && STATE.istaknuto.top) || []) {
    if (st.tema === 'mobilnost' && /Slobodnih parking mesta/i.test(st.naslov || '')) {
      const m = st.naslov.match(/(\d+)\s*[—–-]\s*(.+)$/);
      if (m) garaze.push({ naziv: m[2].replace(/"/g, ''), mesta: Number(m[1]) });
    }
  }
  if (STATE.mapa && Array.isArray(STATE.mapa.stations)) {
    for (const s of STATE.mapa.stations) {
      if (s.sid === 'S10' && Array.isArray(s.r)) {
        const r0 = s.r[0];
        if (r0 && Number.isFinite(r0.v) && !garaze.some(g => g.naziv === s.n)) {
          garaze.push({ naziv: s.n, mesta: r0.v });
        }
      }
    }
  }
  if (garaze.length) {
    const gList = el('div', 'garaze-list');
    for (const g of garaze.slice(0, 5)) {
      const row = el('div', 'garaza-red');
      row.appendChild(el('span', 'garaza-ime', g.naziv));
      row.appendChild(el('b', 'garaza-br' + (g.mesta > 20 ? ' ok' : ' warn'), g.mesta + ' ' + T().slobodnoMesta));
      gList.appendChild(row);
    }
    c2.appendChild(gList);
    c2.appendChild(el('p', 'meta', T().parkingNapomena));
  } else {
    c2.appendChild(el('p', 'sub', T().tangierUcitavanje));
  }
  grid.appendChild(c2);

  /* Kartica 3: Moj kraj — interaktivni izbor opštine direktno na #danas */
  const c3 = el('article', 'vodic-card accent-amber');
  c3.appendChild(el('span', 'eyebrow', '03 · ' + (LANG === 'sr' ? 'LOKALNI PRESEK' : 'LOCAL SNAPSHOT')));
  c3.appendChild(el('h3', null, T().vodicKraj));
  const selWrap = el('div', 'kraj-izbor compact');
  const sel = el('select');
  sel.setAttribute('aria-label', T().krajOpstina);
  const savedKraj = krajIzbor() || 'Stari grad';
  for (const [ime] of KRAJ_OPSTINE) {
    const o = el('option', null, ime);
    o.value = ime;
    if (krajNorm(ime) === krajNorm(savedKraj)) o.selected = true;
    sel.appendChild(o);
  }
  const krajInfo = el('div', 'vodic-kraj-info');
  const fillKrajCard = ime => {
    krajInfo.textContent = '';
    const opEntry = KRAJ_OPSTINE.find(x => krajNorm(x[0]) === krajNorm(ime) || krajNorm(x[1]) === krajNorm(ime));
    const found = krajNajblizaRef(opEntry);
    if (found) {
      krajInfo.appendChild(el('p', 'vodic-kraj-st', T().krajRefStanica + ': ' + found.st.n + ' (' + fmtNum(found.d, 1) + ' km) · ' + found.uKrugu + ' ' + T().znanjeSenzora));
      const pills = el('div', 'vodic-kv');
      for (const r of (found.st.r || []).slice(0, 4)) {
        if (r.v === undefined) continue;
        const pl = PARAM_LABEL[r.p];
        pills.appendChild(el('span', 'pill', (pl ? pl[LANG] : r.p) + ': ' + fmtNum(r.v, 1) + ' ' + (UNIT_LABEL[r.u] || '')));
      }
      krajInfo.appendChild(pills);
    } else {
      krajInfo.appendChild(el('p', 'sub', T().tangierUcitavanje));
    }
    const isklj = STATE.mapaNews && STATE.mapaNews.slojevi && STATE.mapaNews.slojevi.iskljucenja;
    const spisak = (isklj && isklj.opstine) || [];
    const hit = opEntry && spisak.find(x => {
      const d = (x && x.data) || x || {};
      return krajNorm(d.ime) === krajNorm(opEntry[0]) || krajNorm(d.ime) === krajNorm(opEntry[1]);
    });
    if (hit) {
      const d = hit.data || hit;
      krajInfo.appendChild(el('p', 'meta', T().slojIskljucenja + ': ' + (d.broj_mesta || (d.mesta || []).length) + ' ' + T().krajMesta));
    } else if (STATE.mapaNews) {
      krajInfo.appendChild(el('p', 'meta', LANG === 'sr' ? 'Isključenja struje: nema aktivnih najava za izabranu opštinu.' : 'Power cuts: no active notices for selected municipality.'));
    }
  };
  sel.addEventListener('change', () => {
    localStorage.setItem(KRAJ_KEY, sel.value);
    fillKrajCard(sel.value);
  });
  selWrap.appendChild(sel);
  c3.appendChild(selWrap);
  fillKrajCard(savedKraj);
  c3.appendChild(krajInfo);
  const a3 = el('a', 'vodic-link', T().vodicOtvoriKraj);
  a3.href = '#kraj';
  c3.appendChild(a3);
  grid.appendChild(c3);

  /* Kartica 4: Kultura — sledeći događaji u gradu */
  const c4 = el('article', 'vodic-card accent-purple');
  c4.appendChild(el('span', 'eyebrow', '04 · ' + (LANG === 'sr' ? 'REPERTOAR GRADA' : 'CITY REPERTOIRE')));
  c4.appendChild(el('h3', null, T().vodicKultura));
  const evs = (STATE.dog && STATE.dog.events) || [];
  if (evs.length) {
    const eList = el('div', 'garaze-list');
    for (const e of evs.slice(0, 4)) {
      const row = el('div', 'kultura-mini');
      const l = e.tl || e.t || '';
      const dt = l.length >= 16 ? l.slice(8, 10) + '.' + l.slice(5, 7) + '. ' + l.slice(11, 16) : '';
      row.appendChild(el('span', 'tag outline', dt));
      const a = el('a', 'kultura-link', e.n);
      a.href = e.u; a.rel = 'noopener';
      row.appendChild(a);
      if (e.m) row.appendChild(el('span', 'meta', e.m));
      eList.appendChild(row);
    }
    c4.appendChild(eList);
  } else {
    c4.appendChild(el('p', 'sub', T().tangierUcitavanje));
  }
  const a4 = el('a', 'vodic-link', T().krajIcs + ' (.ics) →');
  a4.href = 'state/kultura.ics';
  c4.appendChild(a4);
  grid.appendChild(c4);

  return grid;
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
