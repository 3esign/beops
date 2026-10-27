/* BEOPS v2 shell — javni servis, beli interfejs po estetici originala.
   Principi (research/V2_INTERFEJS_PLAN_2026-10-25.md):
   P2 svežina se meri u čitanju (sat čitaoca vs generated_at/as_of/at),
   P3 tišina je sadržaj (prag 2× kadence → „grad ćuti“),
   P5 jedan shell, rute u klientu,
   P6 misli su glavni sadržaj, podaci su dokaz.
   Svi podaci stižu iz ./state/*.json; DOM se gradi createElement/textContent —
   nikad innerHTML sa podacima. Brendovi modela se ne prikazuju (sve je Svemir). */
'use strict';

/* (jezik živi u strings.js — učitan pre app.js) */

/* ── Stanje ─────────────────────────────────────────────── */
const STATE = { puls: null, misli: null, organizam: null, veze: null, mapa: null, serije: {}, istaknuto: null, belaznica: null, mapaNews: null };
const SERIES_IDS = ['pm25', 'pm10', 'temperature', 'humidity'];
let serijePromise = null;

function jfetch(path) {
  return fetch(path).then(r => { if (!r.ok) throw new Error(path + ' ' + r.status); return r.json(); });
}
function loadCore() {
  return Promise.all([
    jfetch('state/puls.json'),
    jfetch('state/misli-7d.json'),
    jfetch('state/organizam.json'),
  ]).then(([puls, misli, organizam]) => {
    STATE.puls = puls; STATE.misli = misli; STATE.organizam = organizam;
  });
}
function loadSerije() {
  if (!serijePromise) {
    serijePromise = Promise.all(SERIES_IDS.map(id =>
      jfetch('state/serije/' + id + '.json').then(s => { STATE.serije[id] = s; }, () => {})
    ));
  }
  return serijePromise;
}
function loadVeze() {
  if (!STATE.veze) return jfetch('state/veze.json').then(v => { STATE.veze = v; }, () => {});
  return Promise.resolve();
}
function loadMapa() {
  if (!STATE.mapa) return jfetch('state/mapa.json').then(m => { STATE.mapa = m; }, () => {});
  return Promise.resolve();
}
/* INTERFEJS-PLAN T1–T4: istaknuto (jedna istina o relevantnosti), belažnica
   (ocene građana) i javni sloj mape (isključenja). Pad mreže ih ne ruši —
   strana živi i bez njih, samo kaže da nema. */
function loadIstaknuto() {
  if (!STATE.istaknuto) return jfetch('state/istaknuto.json').then(m => { STATE.istaknuto = m; }, () => {});
  return Promise.resolve();
}
function loadBelaznica() {
  if (!STATE.belaznica) return jfetch('state/belaznica.json').then(m => { STATE.belaznica = m; }, () => {});
  return Promise.resolve();
}
function loadMapaNews() {
  if (!STATE.mapaNews) return jfetch('state/mapa_news.json').then(m => { STATE.mapaNews = m; }, () => {});
  return Promise.resolve();
}

/* ── Svežina (P2): meri je sat čitaoca ──────────────────── */
function ageMin(iso) {
  const t = Date.parse(iso);
  return Number.isFinite(t) ? (Date.now() - t) / 60000 : NaN;
}
function tier(iso, cadenceMin) {
  const a = ageMin(iso);
  if (!Number.isFinite(a)) return 'unknown';
  if (a <= 2 * cadenceMin) return 'fresh';
  if (a <= 6 * cadenceMin) return 'old';
  return 'silent';
}
function stampEl(iso, cadenceMin) {
  const el = document.createElement('span');
  const t = tier(iso, cadenceMin);
  el.className = 'stamp' + (t === 'old' || t === 'silent' ? ' ' + t : '');
  const i = document.createElement('i');
  i.setAttribute('aria-hidden', 'true');
  el.appendChild(i);
  el.appendChild(document.createTextNode(' ' + relTime(iso) + ' '));
  el.title = T()[t === 'unknown' ? 'statusUnknown' : t === 'fresh' ? 'svezina' : t === 'old' ? 'staro' : 'cuti'];
  el.setAttribute('data-tier', t);
  return el;
}
function relTime(iso) {
  const m = ageMin(iso);
  if (!Number.isFinite(m)) return '—';
  if (m < 1) return T().sada;
  const suf = LANG === 'sr' ? T().pre : T().uscanje;
  let v, u;
  if (m < 60) { v = Math.round(m); u = 'min'; }
  else if (m < 60 * 48) { v = Math.round(m / 60); u = 'h'; }
  else { v = Math.round(m / 1440); u = 'd'; }
  return LANG === 'sr' ? `${suf} ${v} ${u}` : `${v} ${u} ${suf}`;
}
function absTime(iso) {
  const t = new Date(iso);
  if (isNaN(t)) return '—';
  const p = n => String(n).padStart(2, '0');
  return `${p(t.getUTCDate())}.${p(t.getUTCMonth() + 1)}. ${p(t.getUTCHours())}:${p(t.getUTCMinutes())} UTC`;
}
function fmtNum(x, dec) {
  if (x === null || x === undefined || !Number.isFinite(x)) return '—';
  return x.toLocaleString(LANG === 'sr' ? 'sr-RS' : 'en-US', {
    minimumFractionDigits: dec === undefined ? 1 : dec, maximumFractionDigits: dec === undefined ? 1 : dec,
  });
}

/* ── Mind identitet (brendovi modela se ne prikazuju) ───── */
function mindKey(t) { return t.origin === 'ai_feed' ? 'ai' : (t.origin === 'bridge' ? 'bridge' : (t.entity || 'unknown')); }
function mindName(t) {
  const k = mindKey(t);
  if (k === 'ai') return T().aiLabel;
  /* Zakon vidnog sloja: most je Svemir; potpis modela živi samo u javnom JSON-u. */
  if (k === 'bridge') return mindDisplayName('bridge');
  return t.entity_label || t.entity_sr || k;
}
function mindVar(k) {
  return { observer: 'var(--um-observer)', skeptic: 'var(--um-skeptic)', connector: 'var(--um-connector)', ai: 'var(--um-ai)', organelle: 'var(--um-organelle)', bridge: 'var(--um-bridge)' }[k] || 'var(--muted)';
}
function mindDisplayName(k) {
  const sr = { observer: 'Posmatrač', skeptic: 'Sumnjalo', connector: 'Povezivač', ai: null, organelle: 'Organela', bridge: 'Svemir most' };
  const en = { observer: 'Observer', skeptic: 'Skeptic', connector: 'Connector', ai: null, organelle: 'Organelle', bridge: 'Svemir bridge' };
  if (k === 'ai') return T().aiLabel;
  return (LANG === 'sr' ? sr[k] : en[k]) || k;
}
function mindChip(t) {
  const k = mindKey(t);
  const chip = document.createElement('span');
  chip.className = 'mind-chip';
  const dot = document.createElement('span');
  dot.className = 'mind-dot'; dot.style.background = mindVar(k); dot.setAttribute('aria-hidden', 'true');
  chip.appendChild(dot);
  chip.appendChild(document.createTextNode(mindName(t)));
  return chip;
}

/* ── DOM pomoćnici ──────────────────────────────────────── */
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}
function banner(srText, boldText, tailText, iso, isOk) {
  const b = el('div', 'banner' + (isOk ? ' ok' : ''));
  const t = el('span');
  t.appendChild(document.createTextNode(srText.trim() + ' '));
  if (boldText) t.appendChild(el('b', null, boldText));
  if (tailText) t.appendChild(document.createTextNode(' ' + tailText));
  t.appendChild(document.createTextNode(' '));
  const when = el('span', 'when', absTime(iso) + ' (' + relTime(iso) + ')');
  t.appendChild(when);
  b.appendChild(t);
  return b;
}
function sectionHead(eyebrowText, titleText, subText) {
  const head = el('div', 'section-head');
  head.appendChild(el('p', 'eyebrow', eyebrowText));
  if (titleText) head.appendChild(el('h1', null, titleText));
  if (subText) head.appendChild(el('p', 'sub', subText));
  return head;
}
/* rejection_reason stiže iz dva izvora: niz (organ mind) i string (ai_feed) */
function rejectionReason(t) {
  const r = t.rejection_reason;
  if (Array.isArray(r)) return r.filter(Boolean).join(' · ');
  return r ? String(r) : '';
}

/* ── Tooltip ────────────────────────────────────────────── */
let ttEl = null;
function tooltip() {
  if (!ttEl) { ttEl = el('div'); ttEl.id = 'tt'; ttEl.hidden = true; document.body.appendChild(ttEl); }
  return ttEl;
}
function showTT(x, y, value, sub) {
  const tt = tooltip();
  tt.textContent = '';
  tt.appendChild(el('b', null, value));
  tt.appendChild(el('div', 'tt-sub', sub));
  tt.hidden = false;
  const w = tt.offsetWidth, h = tt.offsetHeight;
  tt.style.left = Math.min(Math.max(4, x - w / 2), window.innerWidth - w - 4) + 'px';
  tt.style.top = Math.max(4, y - h - 10) + 'px';
}
function hideTT() { if (ttEl) ttEl.hidden = true; }


/* ── Kartica misli ──────────────────────────────────────── */
function oslonciEl(t) {
  const box = el('div', 'reading-proof');
  if (t.status_odgovora === 'nedovoljno_podataka')
    box.appendChild(el('p', 'reading-note', LANG === 'sr' ? 'Nema dovoljno podataka za zaključak' : 'Insufficient evidence for a conclusion'));
  if (t.oblik !== 'esej' && t.pouzdanost)
    box.appendChild(el('p', 'sub', (LANG === 'sr' ? 'Procena modela: ' : 'Model assessment: ') + t.pouzdanost));
  if (t.ekspertize) {
    const exp = el('details');
    exp.appendChild(el('summary', null, LANG === 'sr' ? 'Šta treba stručno proveriti' : 'Expert checks needed'));
    exp.appendChild(el('p', 'tekst', t.ekspertize)); box.appendChild(exp);
  }
  const items = (t.oslonci || []).length ? t.oslonci : (t.cites || []).map(id => ({ naslov: id }));
  if (items.length) {
    const det = el('details');
    det.appendChild(el('summary', null, (LANG === 'sr' ? 'Izvori i ograničenja' : 'Sources and limitations') + ' · ' + items.length));
    for (const e of items) {
      det.appendChild(el('h4', null, e.naslov));
      if (e.at || e.izvor) det.appendChild(el('p', 'meta', [e.at && absTime(e.at), e.izvor].filter(Boolean).join(' · ')));
      if (e.tekst) det.appendChild(el('p', 'source-record', e.tekst));
    }
    if (t.kontekst_sha256) det.appendChild(el('p', 'meta source-record', 'SHA-256: ' + t.kontekst_sha256));
    box.appendChild(det);
  }
  return box;
}
function thoughtCard(t) {
  const card = el('article', 'misao' + (t.state === 'rejected' ? ' rejected' : ''));
  const head = el('div', 'misao-head');
  head.appendChild(mindChip(t));
  head.appendChild(el('span', null, T().filterNivo + ': ' + (t.level || '—')));
  const sp = el('span'); sp.style.marginLeft = 'auto'; head.appendChild(sp);
  head.appendChild(stampEl(t.at, 4));
  const tim = el('span', 'time', absTime(t.at));
  head.appendChild(tim);
  card.appendChild(head);
  if (t.urednicka_napomena) card.appendChild(el('p', 'reading-note', t.urednicka_napomena));
  if (t.odgovor_na_pitanje) card.appendChild(el('p', 'direct-answer', t.odgovor_na_pitanje));

  const txt = LANG === 'sr' ? (t.text_sr || t.text_en) : (t.text_en || t.text_sr);
  card.appendChild(el('p', 'tekst' + (t.state === 'rejected' ? ' rej' : ''), txt || '—'));

  if (t.state === 'rejected') {
    const reasons = rejectionReason(t);
    if (reasons) {
      const r = el('p', 'razlog');
      r.appendChild(el('b', null, T().razlogOdbijanja + ': '));
      r.appendChild(document.createTextNode(reasons));
      card.appendChild(r);
    }
  }
  const hyp = (t.hypotheses_sr || []).filter(Boolean);
  const q = (t.questions_sr || []).filter(Boolean);
  if (hyp.length || q.length) {
    const det = el('details');
    const sum = el('summary', null, T().hipotezePitanja + ' (' + (hyp.length + q.length) + ')');
    det.appendChild(sum);
    const ul = el('ul');
    for (const h of hyp) ul.appendChild(el('li', null, h));
    for (const s of q) ul.appendChild(el('li', null, s));
    det.appendChild(ul);
    card.appendChild(det);
  }
  card.appendChild(oslonciEl(t));
  return card;
}

/* ── Pogled: #danas (K4 — misli pre podataka, P6) ─────── */

/* ── K4: rok kartice odbrojava javno, nikad ne nagađa ────── */
function rokEl(iso) {
  const s = el('span', 'rok');
  if (!iso || !Number.isFinite(Date.parse(iso))) { s.appendChild(el('span', 'nema', T().rokBez)); return s; }
  const d = Date.parse(iso) - Date.now();
  if (d <= 0) { s.appendChild(el('span', 'nema', T().rokIstekao)); return s; }
  const h = Math.floor(d / 3600000), m = Math.round((d % 3600000) / 60000);
  s.appendChild(el('b', null, T().rokJos + ' ' + (h ? h + ' h ' + m + ' min' : m + ' min')));
  s.title = absTime(iso);
  return s;
}
function esejCard(t) {
  const art = el('article', 'esej');
  const head = el('div', 'esej-head');
  head.appendChild(mindChip(t));
  const reci = ((LANG === 'sr' ? t.text_sr : t.text_en) || '').trim();
  head.appendChild(el('span', 'meta', reci.split(/\s+/).filter(Boolean).length + ' ' + T().esejReci));
  /* v3: pouzdanost je ordinalna reč, nikad sirovi skor (WMO lekcija) */
  const pz = t.pouzdanost && (t.pouzdanost.match(/^(nisko|srednje|visoko)/i) || [])[0];
  if (pz) { const b = el('span', 'pouzd ' + pz.toLowerCase(), pz.toLowerCase()); b.title = t.pouzdanost; head.appendChild(b); }
  const sp = el('span'); sp.style.marginLeft = 'auto'; head.appendChild(sp);
  head.appendChild(stampEl(t.at, 4));
  art.appendChild(head);
  if (t.naslov) art.appendChild(el('h3', 'esej-naslov', t.naslov));
  if (t.urednicka_napomena) art.appendChild(el('p', 'reading-note', t.urednicka_napomena));
  /* starost nosioca na glas: razmatranje starije od 12 h to i kaže */
  if (Date.now() - Date.parse(t.at) > 12 * 3600e3) art.appendChild(el('p', 'sub', T().esejStaro));
  const body = el('div', 'esej-telo');
  for (const p of reci.split(/\n+/)) if (p.trim()) body.appendChild(el('p', null, p.trim()));
  art.appendChild(body);
  /* dokazi van proze: oslonci eseja kao čipovi, ne zagrade u rečenici */
  art.appendChild(oslonciEl(t));
  return art;
}
function karticaCard(t) {
  const z = t.za_gradjanina || {};
  const art = el('article', 'kartica');
  art.appendChild(el('p', 'akcija', z.akcija || '—'));
  const meta = el('div', 'kartica-meta');
  if (z.lokacija) meta.appendChild(el('span', 'lok', z.lokacija));
  meta.appendChild(rokEl(z.vazi_do));
  art.appendChild(meta);
  if (z.dokaz) {
    const det = el('details');
    det.appendChild(el('summary', null, LANG === 'sr' ? 'dokaz' : 'evidence'));
    det.appendChild(el('p', 'sub', z.dokaz));
    art.appendChild(det);
  }
  return art;
}
/* traka merenja: čista od uma — nula AI reči (AI Act 50 u layoutu, P6) */
function trakaMerenja() {
  const strip = el('div', 'traka');
  const cm = (STATE.puls && STATE.puls.current_metrics) || {};
  const cs = STATE.puls && STATE.puls.city_status;
  const red = (label, v, unit) => {
    const c = el('span', 'tr-c');
    c.appendChild(el('span', 'tr-l', label));
    c.appendChild(el('b', null, v === null || v === undefined || !Number.isFinite(v) ? '—' : fmtNum(v)));
    if (unit) c.appendChild(el('span', 'tr-u', unit));
    return c;
  };
  strip.appendChild(red('AQI', cs ? cs.aqi_us : null, null));
  strip.appendChild(red('PM2.5', cm.pm25 && cm.pm25.mean, 'µg/m³'));
  strip.appendChild(red('PM10', cm.pm10 && cm.pm10.mean, 'µg/m³'));
  strip.appendChild(red('NO₂', cm.no2 && cm.no2.mean, 'µg/m³'));
  strip.appendChild(red('O₃', cm.o3 && cm.o3.mean, 'µg/m³'));
  const met = cm.meteo || {};
  strip.appendChild(red(LANG === 'sr' ? 'temp' : 'temp', met.temperature, '°C'));
  strip.appendChild(red(LANG === 'sr' ? 'vlag' : 'rh', met.humidity, '%'));
  const foot = el('span', 'tr-st');
  if (STATE.puls && STATE.puls.as_of) foot.appendChild(stampEl(STATE.puls.as_of, 5));
  strip.appendChild(foot);
  return strip;
}

function viewDanas(root) {
  loadSerije().then(() => { if (currentRoute() === 'danas') renderDanas(root); });
  loadIstaknuto().then(() => { if (currentRoute() === 'danas') renderDanas(root); });
  renderDanas(root);
}
function renderDanas(root) {
  root.textContent = '';
  const d = new Date();
  root.appendChild(sectionHead(
    LANG === 'sr' ? 'Danas · ' + d.toLocaleDateString('sr-RS') : 'Today · ' + d.toLocaleDateString('en-GB'),
    T().danasTitle, T().danasSub));

  const cs = STATE.puls && STATE.puls.city_status;
  if (cs) {
    root.appendChild(banner(
      LANG === 'sr' ? 'Vazduh:' : 'Air:',
      'AQI ' + cs.aqi_us + ' · ' + (LANG === 'sr' ? cs.summary_sr : cs.summary_en), null,
      STATE.puls.as_of, (cs.aqi_us || 0) <= 100
    ));
  }
  /* P3 — tišina grada: puls (kadenca 5 min) i um (4 min) */
  if (STATE.puls && tier(STATE.puls.as_of, 5) === 'silent') {
    root.appendChild(banner(T().gradCuti + ' —', T().gradCutiText, null, STATE.puls.as_of, false));
  }
  const newest = newestThoughtAt();
  if (newest && tier(newest, 4) === 'silent') {
    root.appendChild(banner(T().umCuti + ' —', T().umCutiText, null, newest, false));
  }

  /* 1 — razmatranje dana: esej je nosilac strane (K4) */
  root.appendChild(el('h2', null, T().razmatranjeTitle));
  root.appendChild(el('hr', 'rule'));
  const eseji = ((STATE.misli && STATE.misli.thoughts) || [])
    .filter(t => t.oblik === 'esej' && t.state === 'accepted')
    .sort((a, b) => Date.parse(b.at) - Date.parse(a.at));
  if (eseji.length) root.appendChild(esejCard(eseji[0]));
  else root.appendChild(el('p', 'sub', T().razmatranjeEmpty));

  /* 2 — koraci za građanina: akcija, lokacija, rok na glas */
  root.appendChild(el('h2', null, T().karticeTitle));
  root.appendChild(el('hr', 'rule'));
  const kartice = ((STATE.misli && STATE.misli.thoughts) || [])
    .filter(t => t.state === 'accepted' && t.za_gradjanina && typeof t.za_gradjanina === 'object' && t.za_gradjanina.akcija)
    .sort((a, b) => Date.parse(b.at) - Date.parse(a.at))
    .slice(0, 6);
  if (!kartice.length) root.appendChild(el('p', 'sub', T().karticeEmpty));
  else {
    const g = el('div', 'kartice');
    for (const t of kartice) g.appendChild(karticaCard(t));
    root.appendChild(g);
  }

  /* 3 — traka merenja: mono, fizički odvojena od misli */
  root.appendChild(el('h2', null, T().trakaTitle));
  root.appendChild(el('hr', 'rule'));
  root.appendChild(trakaMerenja());

  /* 4 — istaknuto po relevantnosti (T1: jedna istina, šel ne boduje sam) */
  if (STATE.istaknuto && (STATE.istaknuto.top || []).length) {
    root.appendChild(el('h2', null, T().istaknutoTitle));
    root.appendChild(el('hr', 'rule'));
    const list = el('div', 'istaknuto');
    for (const st of STATE.istaknuto.top.slice(0, 5)) {
      const row = el('article', 'ist-red');
      row.appendChild(el('span', 'score', fmtNum(st.score, 2)));
      const mid = el('div', 'ist-mid');
      mid.appendChild(el('p', 'naslov', st.naslov));
      mid.appendChild(el('p', 'meta', (st.tema_ime || st.tema || '') + ' · ' + (st.vrsta || '') + (st.t ? ' · ' + absTime(st.t) : '')));
      row.appendChild(mid);
      const det = el('details');
      det.appendChild(el('summary', null, T().istaknutoZasto));
      det.appendChild(el('p', 'sub', st.zasto));
      if (st.izvor) det.appendChild(el('p', 'meta', st.izvor));
      row.appendChild(det);
      list.appendChild(row);
    }
    root.appendChild(list);
  }

  root.appendChild(el('h2', null, T().otkucaji));
  root.appendChild(el('hr', 'rule'));
  const organs = el('div', 'organs');
  for (const o of (STATE.organizam && STATE.organizam.organs) || []) {
    const chip = el('span', 'organ');
    chip.appendChild(el('b', null, o.name));
    if (o.last_run) chip.appendChild(stampEl(o.last_run, o.cadence_minutes || 30));
    else chip.appendChild(el('span', null, T().statusUnknown));
    organs.appendChild(chip);
  }
  root.appendChild(organs);
}

/* ── Pogled: #misli ─────────────────────────────────────── */
const MISLI_F = { um: 'all', stanje: 'acc', nivo: 'all' };
function newestThoughtAt() {
  const ts = ((STATE.misli && STATE.misli.thoughts) || []).map(t => Date.parse(t.at)).filter(Number.isFinite);
  if (!ts.length) return null;
  return new Date(Math.max(...ts)).toISOString();
}
function filteredThoughts() {
  let ts = (STATE.misli && STATE.misli.thoughts) || [];
  if (MISLI_F.um !== 'all') ts = ts.filter(t => mindKey(t) === MISLI_F.um);
  if (MISLI_F.stanje !== 'all') ts = ts.filter(t => t.state === (MISLI_F.stanje === 'acc' ? 'accepted' : 'rejected'));
  if (MISLI_F.nivo !== 'all') ts = ts.filter(t => t.level === MISLI_F.nivo);
  return ts.slice().sort((a, b) => Date.parse(b.at) - Date.parse(a.at));
}
function selectFilter(labelText, options, value, onch) {
  const lab = el('label');
  lab.appendChild(document.createTextNode(labelText + ' '));
  const s = el('select');
  for (const [val, name] of options) {
    const o = el('option', null, name); o.value = val;
    if (val === value) o.selected = true;
    s.appendChild(o);
  }
  s.addEventListener('change', () => onch(s.value));
  lab.appendChild(s);
  return lab;
}
function viewMisli(root) {
  root.textContent = '';
  root.appendChild(sectionHead(null, T().misliTitle, T().misliSub));

  const newest = newestThoughtAt();
  if (newest && tier(newest, 4) === 'silent') {
    root.appendChild(banner(T().umCuti + ' —', T().umCutiText, null, newest, false));
  }

  const f = el('div', 'filters');
  const mindOpts = [['all', T().umSve], ['observer', mindDisplayName('observer')], ['skeptic', mindDisplayName('skeptic')], ['connector', mindDisplayName('connector')], ['organelle', mindDisplayName('organelle')], ['ai', mindDisplayName('ai')], ['bridge', mindDisplayName('bridge')]];
  f.appendChild(selectFilter(T().filterUm + ':', mindOpts, MISLI_F.um, v => { MISLI_F.um = v; route(); }));
  f.appendChild(selectFilter(T().filterStanje + ':', [
    ['acc', T().stanjeAcc], ['rej', T().stanjeRej], ['all', T().stanjeSve],
  ], MISLI_F.stanje, v => { MISLI_F.stanje = v; route(); }));
  const levels = [...new Set(((STATE.misli && STATE.misli.thoughts) || []).map(t => t.level).filter(Boolean))];
  f.appendChild(selectFilter(T().filterNivo + ':', [['all', T().nivoSve], ...levels.map(l => [l, l])], MISLI_F.nivo, v => { MISLI_F.nivo = v; route(); }));
  /* legenda identiteta: tačke u filteru su legenda umova */
  const legend = el('span', 'legend');
  for (const k of ['observer', 'skeptic', 'connector', 'organelle', 'ai', 'bridge']) {
    const lab = el('label');
    const dot = el('span', 'mind-dot'); dot.style.background = mindVar(k); dot.setAttribute('aria-hidden', 'true');
    lab.appendChild(dot);
    lab.appendChild(document.createTextNode(mindDisplayName(k)));
    legend.appendChild(lab);
  }
  f.appendChild(legend);
  root.appendChild(f);

  const feed = el('div');
  root.appendChild(feed);
  drawMisliFeed(feed);

  root.appendChild(el('h2', null, T().odbijenoTitle));
  root.appendChild(el('p', 'sub', T().odbijenoSub));
  root.appendChild(rejectedBox());
}
function drawMisliFeed(feed) {
  feed.textContent = '';
  const ts = filteredThoughts();
  const count = el('div', 'filters');
  count.appendChild(el('span', 'count', ts.length + ' / ' + ((STATE.misli && STATE.misli.total_thoughts) || 0)));
  feed.appendChild(count);
  if (!ts.length) {
    feed.appendChild(el('p', 'sub', T().odbijenoNone));
    return;
  }
  for (const t of ts.slice(0, 60)) feed.appendChild(thoughtCard(t));
  if (ts.length > 60) {
    const more = el('p', 'sub', '+ ' + (ts.length - 60) + ' …');
    feed.appendChild(more);
  }
}
function rejectedBox() {
  const box = el('div', 'odbijeno-box');
  const all = (STATE.misli && STATE.misli.thoughts) || [];
  let rej = all.filter(t => t.state === 'rejected');
  if (MISLI_F.um !== 'all') rej = rej.filter(t => mindKey(t) === MISLI_F.um);
  if (MISLI_F.nivo !== 'all') rej = rej.filter(t => t.level === MISLI_F.nivo);
  box.appendChild(el('p', null, rej.length + ' × ' + T().stanjeRej));
  if (!rej.length) { box.appendChild(el('p', 'sub', T().odbijenoNone)); return box; }
  const groups = new Map();
  for (const t of rej) {
    const key = rejectionReason(t) || '—';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(t);
  }
  const rows = [...groups.entries()].sort((a, b) => b[1].length - a[1].length);
  const table = el('table');
  const thead = el('thead'); const trh = el('tr');
  trh.appendChild(el('th', null, T().nCol)); trh.appendChild(el('th', null, T().reasonCol));
  thead.appendChild(trh); table.appendChild(thead);
  const tb = el('tbody');
  for (const [reason, list] of rows.slice(0, 12)) {
    const tr = el('tr');
    tr.appendChild(el('td', 'n', String(list.length)));
    const td = el('td');
    const det = el('details');
    det.appendChild(el('summary', null, reason.length > 110 ? reason.slice(0, 110) + '…' : reason));
    for (const t of list) {
      const line = el('div', null, absTime(t.at) + ' · ' + mindName(t));
      line.style.margin = '4px 0';
      const txt = el('div', 'sub', (LANG === 'sr' ? (t.text_sr || t.text_en) : (t.text_en || t.text_sr)) || '');
      txt.style.fontSize = '12px';
      det.appendChild(line); det.appendChild(txt);
    }
    td.appendChild(det);
    tr.appendChild(td);
    tb.appendChild(tr);
  }
  table.appendChild(tb);
  box.appendChild(table);
  return box;
}

/* ── Pogled: #podaci — veliki graf sa pojasom ───────────── */
let PODACI_SERIJA = 'pm25';
const SERIES_META = {
  pm25: { sr: 'PM2.5 (µg/m³)', en: 'PM2.5 (µg/m³)' },
  pm10: { sr: 'PM10 (µg/m³)', en: 'PM10 (µg/m³)' },
  temperature: { sr: 'Temperatura (°C)', en: 'Temperature (°C)' },
  humidity: { sr: 'Vlažnost (%)', en: 'Humidity (%)' },
};
function seriesPoints(id) {
  const s = STATE.serije[id];
  if (!s || !Array.isArray(s.points)) return [];
  return s.points.map(p => ({
    x: Date.parse(p[0] + ':00:00Z'),
    mean: p[1], min: p[2], max: p[3], n: p[4],
  })).filter(p => Number.isFinite(p.x) && p.mean !== null && Number.isFinite(p.mean));
}
function bigChart(id, wpx) {
  const wrap = el('div');
  const pts = seriesPoints(id);
  const meta = SERIES_META[id] || {};
  const title = el('div', 'chart-title');
  const h3 = el('h3', null, LANG === 'sr' ? meta.sr : meta.en);
  h3.style.fontSize = '15px'; h3.style.margin = '14px 0 6px';
  title.appendChild(h3);
  if (pts.length) {
    title.appendChild(el('span', 'muted', pts.length + ' ' + T().tacaka + ' · ' +
      absTime(new Date(pts[0].x).toISOString()) + ' – ' + absTime(new Date(pts[pts.length - 1].x).toISOString())));
  }
  wrap.appendChild(title);
  if (pts.length < 2) {
    wrap.appendChild(el('p', 'sub', T().nemaTrenda));
    return wrap;
  }
  const W = Math.max(340, Math.floor(wpx || 1000)), H = 320, L = 52, R = 14, TP = 14, B = 28;
  const x0 = pts[0].x, x1 = pts[pts.length - 1].x;
  let y0 = Infinity, y1 = -Infinity;
  for (const p of pts) {
    if (p.min !== null && Number.isFinite(p.min)) y0 = Math.min(y0, p.min);
    if (p.max !== null && Number.isFinite(p.max)) y1 = Math.max(y1, p.max);
    y0 = Math.min(y0, p.mean); y1 = Math.max(y1, p.mean);
  }
  if (!Number.isFinite(y0) || !Number.isFinite(y1)) { y0 = Math.min(...pts.map(p => p.mean)); y1 = Math.max(...pts.map(p => p.mean)); }
  if (id === 'pm25' || id === 'pm10') y0 = Math.max(0, y0); /* koncentracije ne mogu biti negativne */
  if (y1 - y0 < 1e-9) y1 = y0 + 1;
  const pad = (y1 - y0) * 0.06;
  y0 -= pad; y1 += pad;
  const sx = t => L + (t - x0) / (x1 - x0) * (W - L - R);
  const sy = v => H - B - (v - y0) / (y1 - y0) * (H - TP - B);

  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('width', W);
  svg.setAttribute('height', H);
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('role', 'img');
  svg.id = 'bigchart';
  svg.tabIndex = 0;
  const mk = (tag, at, text) => {
    const n = document.createElementNS(NS, tag);
    for (const k in at) n.setAttribute(k, at[k]);
    if (text !== undefined) n.textContent = text;
    return n;
  };
  /* horizontalne mrežne linije + y labele (recesivne) */
  for (let i = 0; i <= 4; i++) {
    const v = y0 + (y1 - y0) * i / 4;
    const y = sy(v);
    svg.appendChild(mk('line', { x1: L, x2: W - R, y1: y.toFixed(1), y2: y.toFixed(1), 'class': 'axisline', opacity: i === 0 ? 1 : 0.55 }));
    svg.appendChild(mk('text', { x: L - 8, y: (y + 3).toFixed(1), 'text-anchor': 'end' }, fmtNum(v, Math.abs(v) < 10 ? 1 : 0)));
  }
  /* dnevne x labele */
  const dayMs = 24 * 3600e3;
  for (let t = Math.ceil(x0 / dayMs) * dayMs; t <= x1; t += dayMs) {
    const x = sx(t);
    svg.appendChild(mk('line', { x1: x.toFixed(1), x2: x.toFixed(1), y1: TP, y2: H - B, 'class': 'axisline', opacity: 0.3 }));
    const d = new Date(t);
    const lab = String(d.getUTCDate()).padStart(2, '0') + '.' + String(d.getUTCMonth() + 1).padStart(2, '0') + '.';
    svg.appendChild(mk('text', { x: x.toFixed(1), y: H - 8, 'text-anchor': 'middle' }, lab));
  }
  /* pojas min–max */
  let band = '';
  const ups = pts.filter(p => p.max !== null && Number.isFinite(p.max));
  const downs = pts.filter(p => p.min !== null && Number.isFinite(p.min));
  if (ups.length > 1 && downs.length > 1) {
    band = ups.map((p, i) => (i ? 'L' : 'M') + sx(p.x).toFixed(1) + ' ' + sy(p.max).toFixed(1)).join(' ');
    band += downs.slice().reverse().map(p => 'L' + sx(p.x).toFixed(1) + ' ' + sy(p.min).toFixed(1)).join(' ');
    band += 'Z';
    svg.appendChild(mk('path', { d: band, 'class': 'band' }));
  }
  /* prosek — 2px linija */
  const dLine = pts.map((p, i) => (i ? 'L' : 'M') + sx(p.x).toFixed(1) + ' ' + sy(p.mean).toFixed(1)).join(' ');
  svg.appendChild(mk('path', { d: dLine, 'class': 'meanline' }));
  /* crosshair + točka interakcija */
  const cross = mk('line', { x1: 0, x2: 0, y1: TP, y2: H - B, 'class': 'crosshair', visibility: 'hidden' });
  const dot = mk('circle', { r: 4, 'class': 'hoverdot', visibility: 'hidden' });
  svg.appendChild(cross); svg.appendChild(dot);

  let active = -1;
  const setIdx = (i, clientX, clientY) => {
    i = Math.max(0, Math.min(pts.length - 1, i));
    active = i;
    const p = pts[i], px = sx(p.x);
    cross.setAttribute('x1', px); cross.setAttribute('x2', px);
    cross.setAttribute('visibility', 'visible');
    dot.setAttribute('cx', px); dot.setAttribute('cy', sy(p.mean));
    dot.setAttribute('visibility', 'visible');
    const r = svg.getBoundingClientRect();
    const ax = clientX !== undefined ? clientX : r.left + px / W * r.width;
    const ay = clientY !== undefined ? clientY : r.top + sy(p.mean) / H * r.height;
    const sub = absTime(new Date(p.x).toISOString()) + ' · ' +
      (p.min !== null && p.min !== undefined ? 'min ' + fmtNum(p.min) + ' / max ' + fmtNum(p.max) + ' · ' : '') +
      p.n + ' ' + (LANG === 'sr' ? 'izvora' : 'sources');
    showTT(ax, ay, fmtNum(p.mean) + ' ' + (id === 'temperature' ? '°C' : id === 'humidity' ? '%' : 'µg/m³'), sub);
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
  const firstT = absTime(new Date(x0).toISOString());
  const lastT = absTime(new Date(x1).toISOString());
  const lastP = pts[pts.length - 1];
  svg.setAttribute('aria-label', `${meta[LANG] || id}: ${pts.length} ${T().tacaka}, ${firstT} – ${lastT}, ${LANG === 'sr' ? 'poslednja' : 'last'} ${fmtNum(lastP.mean)}`);
  wrap.appendChild(svg);
  return wrap;
}
let podaciRoot = null;
function viewPodaci(root) {
  podaciRoot = root;
  root.textContent = '';
  root.appendChild(sectionHead(null, T().podaciTitle, T().podaciSub));
  loadVeze().then(() => { if (currentRoute() === 'podaci') renderVeze(root); });
  loadSerije().then(() => { if (currentRoute() === 'podaci') renderPodaci(root); });

  const tabs = el('div', 'chart-tabs');
  tabs.id = 'chart-tabs';
  root.appendChild(tabs);
  const chartBox = el('div');
  chartBox.id = 'chart-box';
  root.appendChild(chartBox);
  if (STATE.serije[PODACI_SERIJA]) renderPodaci(root);
}
function renderPodaci(root) {
  const tabs = document.getElementById('chart-tabs');
  const box = document.getElementById('chart-box');
  if (!tabs || !box) return;
  tabs.textContent = '';
  for (const id of SERIES_IDS) {
    const b = el('button', id === PODACI_SERIJA ? 'active' : null, (LANG === 'sr' ? SERIES_META[id].sr : SERIES_META[id].en));
    b.type = 'button';
    b.addEventListener('click', () => { PODACI_SERIJA = id; renderPodaci(root); });
    tabs.appendChild(b);
  }
  box.textContent = '';
  box.appendChild(bigChart(PODACI_SERIJA, box.clientWidth || root.clientWidth || 1000));
  box.appendChild(el('p', 'sub', T().minMax + ' · ' + T().q7));
}
window.addEventListener('resize', () => {
  if (currentRoute() === 'podaci' && podaciRoot) renderPodaci(podaciRoot);
});
function renderVeze(root) {
  const old = document.getElementById('veze-block');
  if (old) old.remove();
  if (!STATE.veze) return;
  const block = el('div');
  block.id = 'veze-block';
  block.appendChild(el('h2', null, T().vezeTitle));
  block.appendChild(el('p', 'sub', T().vezeSub + ' — ' + (STATE.veze.stable_edges_count || 0) + ' / ' + (STATE.veze.total_edges || 0)));
  const vt = el('table', 'kv');
  const vh = el('thead'); const vrh = el('tr');
  for (const h of [T().vezaCol, T().tezinaCol, T().stabilnaOdCol]) vrh.appendChild(el('th', null, h));
  vh.appendChild(vrh); vt.appendChild(vh);
  const vb = el('tbody');
  for (const c of (STATE.veze.connections || []).slice(0, 20)) {
    const tr = el('tr');
    tr.appendChild(el('td', null, (c.pair || []).join(' ↔ ')));
    tr.appendChild(el('td', null, fmtNum(c.weight, 2)));
    tr.appendChild(el('td', null, c.stable_since || ''));
    vb.appendChild(tr);
  }
  vt.appendChild(vb);
  block.appendChild(vt);
  root.appendChild(block);
}

/* ── Mapa: stanja, oblici, boje ─────────────────────────── */
const MAP_STATE_VAR = {
  observed: 'var(--st-observed)', untimed: 'var(--st-untimed)',
  estimated: 'var(--st-estimated)', forecast: 'var(--st-forecast)',
  unavailable: 'var(--st-unavailable)',
};
function mapStateWord(s) {
  return { observed: T().stObserved, untimed: T().stUntimed, estimated: T().stEstimated, forecast: T().stForecast, unavailable: T().stUnavailable }[s] || s;
}
function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '#888';
}
const PARAM_LABEL = {
  pm25: { sr: 'PM2.5', en: 'PM2.5' }, pm10: { sr: 'PM10', en: 'PM10' },
  no2: { sr: 'NO₂', en: 'NO₂' }, o3: { sr: 'O₃', en: 'O₃' },
  co: { sr: 'CO', en: 'CO' }, so2: { sr: 'SO₂', en: 'SO₂' },
  temp: { sr: 'Temperatura', en: 'Temperature' }, rh: { sr: 'Vlažnost', en: 'Humidity' },
  hpa: { sr: 'Pritisak', en: 'Pressure' }, wind: { sr: 'Vetar', en: 'Wind' },
  dir: { sr: 'Pravac vetra', en: 'Wind dir.' }, noise: { sr: 'Buka', en: 'Noise' },
};
const UNIT_LABEL = { u: 'µg/m³', m: 'mg/m³', C: '°C', p: '%', h: 'hPa', w: 'm/s', d: 'dB' };

function viewMapa(root) {
  root.textContent = '';
  root.appendChild(sectionHead(null, T().mapaTitle, T().mapaSub));
  const loading = el('p', 'sub', T().tangierUcitavanje);
  root.appendChild(loading);
  Promise.all([loadMapa(), loadMapaNews()]).then(() => {
    if (currentRoute() === 'mapa') renderMapa(root, loading);
  });
}
let mapCleanup = null;
function renderMapa(root, loading) {
  loading.remove();
  if (mapCleanup) { mapCleanup(); mapCleanup = null; }
  const M = STATE.mapa;
  if (!M) { root.appendChild(el('p', 'sub', T().nemaPodataka)); return; }

  const wrap = el('div', 'map-wrap');
  /* — karta — */
  const area = el('div', 'map-area');
  const canvas = el('canvas');
  canvas.id = 'map';
  canvas.tabIndex = 0;
  canvas.setAttribute('role', 'application');
  canvas.setAttribute('aria-label', T().mapaTitle);
  area.appendChild(canvas);
  const mt = el('div', 'map-title');
  mt.appendChild(el('strong', null, 'Beograd'));
  mt.appendChild(el('span', null, M.stations_count + ' ' + T().mapaStations + ' · ' + (M.population.hexes || []).length + ' ' + T().mapaCells));
  area.appendChild(mt);
  const tools = el('div', 'map-tools');
  const zoomIn = el('button', null, '+'); zoomIn.type = 'button'; zoomIn.setAttribute('aria-label', '+');
  const zoomOut = el('button', null, '−'); zoomOut.type = 'button'; zoomOut.setAttribute('aria-label', '−');
  const zoomReset = el('button', null, '⌂'); zoomReset.type = 'button'; zoomReset.setAttribute('aria-label', 'reset');
  tools.append(zoomIn, zoomOut, zoomReset);
  area.appendChild(tools);
  const mfoot = el('div', 'map-footer');
  mfoot.appendChild(el('span', null, T().mapaAsOf + ' ' + absTime(M.as_of) + ' (' + relTime(M.as_of) + ')'));
  mfoot.appendChild(el('span', null, LANG === 'sr' ? 'prijem nije potvrda merenja' : 'reception is not confirmation'));
  area.appendChild(mfoot);
  wrap.appendChild(area);

  /* — bočna traka — */
  const side = el('div', 'map-side');
  /* legenda stanja (oblik + boja + tekst + broj) */
  const legBox = el('div');
  legBox.appendChild(el('h3', null, LANG === 'sr' ? 'Stanja podatka' : 'Data states'));
  const leg = el('div', 'legend');
  const counts = M.state_counts || {};
  for (const s of M.states || ['observed', 'untimed', 'estimated', 'forecast', 'unavailable']) {
    const li = el('span', 'li');
    li.appendChild(stateGlyph(s, 14));
    li.appendChild(el('span', null, mapStateWord(s)));
    li.appendChild(el('span', 'n', String(counts[s] || 0)));
    leg.appendChild(li);
  }
  /* neznanje kao podatak (T4): deo naseljenih ćelija bez ijednog senzora */
  const zn = STATE.mapaNews && STATE.mapaNews.znanje;
  if (zn && zn.hex_naseljenih) {
    const li = el('span', 'li');
    li.appendChild(el('span', 'n', Math.round(100 * zn.hex_bez_senzora / zn.hex_naseljenih) + '%'));
    li.appendChild(el('span', null, T().znanjeNasPrazno));
    li.title = zn.hex_bez_senzora + ' / ' + zn.hex_naseljenih;
    leg.appendChild(li);
  }
  legBox.appendChild(leg);
  side.appendChild(legBox);

  /* slojevi */
  const layerBox = el('div');
  layerBox.appendChild(el('h3', null, LANG === 'sr' ? 'Slojevi' : 'Layers'));
  const LAY = [
    ['stations', T().slojStanice, M.stations_count],
    ['population', T().slojPopulacija, (M.population.hexes || []).length],
    ['basemap', T().slojBaza, (M.basemap.features || []).length],
  ];
  /* T4: sloj isključenja iz javnog ugovora mapa_news.json (agregat po opštini) */
  const isklj = STATE.mapaNews && STATE.mapaNews.slojevi && STATE.mapaNews.slojevi.iskljucenja;
  if (isklj && isklj.opstine) LAY.push(['iskljucenja', T().slojIskljucenja, isklj.opstine.length]);
  const visible = new Set(['stations', 'population', 'basemap']);
  if (isklj && isklj.opstine) visible.add('iskljucenja');
  for (const [id, label, n] of LAY) {
    const row = el('label', 'layer-row');
    const cb = el('input'); cb.type = 'checkbox'; cb.checked = true;
    cb.addEventListener('change', () => {
      if (cb.checked) visible.add(id); else visible.delete(id);
      draw();
    });
    row.appendChild(cb);
    row.appendChild(el('span', null, label));
    row.appendChild(el('span', 'n', String(n)));
    layerBox.appendChild(row);
  }
  side.appendChild(layerBox);

  /* dosije */
  const dossier = el('div', 'dossier');
  dossier.appendChild(el('p', 'hint', T().dosijeHint));
  side.appendChild(dossier);

  side.appendChild(el('p', 'map-note', T().mapNapomena));
  wrap.appendChild(side);
  root.appendChild(wrap);

  /* ── crtanje (canvas) ── */
  const ctx = canvas.getContext('2d');
  const W0 = M.window;
  let width = 1, height = 1, dpr = 1, scale = 1, tx = 0, ty = 0, frame = 0;
  let selected = null;
  const stations = (M.stations || []).map(s => ({ lat: s.la, lon: s.lo, data: s, layer: 'stations' }));
  const hexes = (M.population.hexes || []).map(h => ({ lat: h[1], lon: h[0], pop: h[2], layer: 'population' }));
  const opstine = ((isklj && isklj.opstine) || []).map(o => ({ lat: o.lat, lon: o.lon, data: o, layer: 'iskljucenja' }));
  const rIskl = o => 6 + Math.sqrt(o.broj_mesta) * 2.2;

  function project(lat, lon) {
    const kx = Math.cos(44.8 * Math.PI / 180);
    const s = Math.min((width - 36) / ((W0.lo1 - W0.lo0) * kx), (height - 36) / (W0.la1 - W0.la0));
    return [(width - (W0.lo1 - W0.lo0) * kx * s) / 2 + (lon - W0.lo0) * kx * s,
            (height - (W0.la1 - W0.la0) * s) / 2 + (W0.la1 - lat) * s];
  }
  function geomParts(f) {
    const g = f && f.geometry;
    if (!g || !Array.isArray(g.coordinates)) return [];
    if (g.type === 'LineString') return [{ coords: g.coordinates, closed: false }];
    if (g.type === 'MultiLineString') return g.coordinates.map(c => ({ coords: c, closed: false }));
    if (g.type === 'Polygon') return g.coordinates.map(c => ({ coords: c, closed: true }));
    if (g.type === 'MultiPolygon') return g.coordinates.flatMap(p => p.map(c => ({ coords: c, closed: true })));
    return [];
  }
  function drawStampShape(c2d, s, x, y, r) {
    c2d.beginPath();
    if (s === 'untimed') { c2d.moveTo(x, y - r); c2d.lineTo(x + r, y); c2d.lineTo(x, y + r); c2d.lineTo(x - r, y); c2d.closePath(); }
    else if (s === 'estimated') { c2d.rect(x - r * 0.8, y - r * 0.8, r * 1.6, r * 1.6); }
    else if (s === 'forecast') { c2d.moveTo(x, y - r); c2d.lineTo(x + r, y + r); c2d.lineTo(x - r, y + r); c2d.closePath(); }
    else { c2d.arc(x, y, r, 0, Math.PI * 2); }
  }
  function draw() {
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = cssVar('--m-paper');
    ctx.fillRect(0, 0, width, height);
    ctx.translate(tx, ty); ctx.scale(scale, scale);
    /* baza */
    if (visible.has('basemap')) {
      for (const f of (M.basemap.features || [])) {
        const water = f.layer === 'river' || f.layer === 'lake';
        const parts = geomParts(f);
        ctx.beginPath();
        for (const part of parts) {
          let started = false;
          for (const c of part.coords) {
            if (!Array.isArray(c) || !Number.isFinite(c[0]) || !Number.isFinite(c[1])) continue;
            const [x, y] = project(c[1], c[0]);
            if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
          }
          if (part.closed) ctx.closePath();
        }
        ctx.fillStyle = water ? cssVar('--m-water') : cssVar('--m-land');
        ctx.strokeStyle = water ? cssVar('--m-waterline') : cssVar('--m-landline');
        ctx.lineWidth = (f.layer === 'river' ? 3 : 0.8) / scale;
        if (parts.some(p => p.closed)) ctx.fill('evenodd');
        ctx.stroke();
      }
    }
    /* populacija */
    if (visible.has('population')) {
      for (const h of hexes) {
        const [x, y] = project(h.lat, h.lon);
        ctx.globalAlpha = 0.08 + Math.min(0.42, Math.sqrt(h.pop) / 180);
        ctx.fillStyle = cssVar('--m-waterline');
        ctx.beginPath();
        ctx.arc(x, y, Math.max(2, Math.min(6, 2 + Math.sqrt(h.pop) / 30)) / scale, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    }
    /* stanice */
    if (visible.has('stations')) {
      for (const p of stations) {
        const [x, y] = project(p.lat, p.lon);
        const sxp = x * scale + tx, syp = y * scale + ty;
        if (sxp < -20 || syp < -20 || sxp > width + 20 || syp > height + 20) continue;
        const st = p.data.st || 'unavailable';
        const col = cssVar(MAP_STATE_VAR[st] ? '--st-' + st : '--st-unavailable');
        const r = 4.2 / scale;
        drawStampShape(ctx, st, x, y, r);
        if (st === 'unavailable') {
          ctx.fillStyle = cssVar('--m-paper');
          ctx.fill();
          ctx.strokeStyle = col;
        } else {
          ctx.fillStyle = col;
          ctx.strokeStyle = col;
        }
        ctx.lineWidth = 1.3 / scale;
        ctx.fill(); ctx.stroke();
        if (selected === p) {
          ctx.beginPath();
          ctx.arc(x, y, 9 / scale, 0, Math.PI * 2);
          ctx.strokeStyle = cssVar('--ink');
          ctx.lineWidth = 1.6 / scale;
          ctx.stroke();
        }
      }
    }
    /* isključenja struje (T4): prsten po opštini, prečnik po broju mesta */
    if (isklj && visible.has('iskljucenja')) {
      for (const o of opstine) {
        const [x, y] = project(o.lat, o.lon);
        const r = rIskl(o.data) / scale;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fillStyle = cssVar('--isklj');
        ctx.globalAlpha = 0.14; ctx.fill(); ctx.globalAlpha = 1;
        ctx.strokeStyle = cssVar('--isklj');
        ctx.lineWidth = 1.6 / scale;
        ctx.setLineDash([4 / scale, 3 / scale]);
        ctx.stroke();
        ctx.setLineDash([]);
        if (selected === o) {
          ctx.beginPath();
          ctx.arc(x, y, (rIskl(o.data) + 4) / scale, 0, Math.PI * 2);
          ctx.strokeStyle = cssVar('--ink');
          ctx.lineWidth = 1.6 / scale;
          ctx.stroke();
        }
      }
    }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }
  function redraw() {
    if (!frame) frame = requestAnimationFrame(() => { frame = 0; draw(); });
  }
  function resize() {
    const r = canvas.getBoundingClientRect();
    width = Math.max(1, r.width); height = Math.max(1, r.height);
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    redraw();
  }
  function zoom(f, x = width / 2, y = height / 2) {
    const next = Math.max(0.65, Math.min(20, scale * f));
    f = next / scale;
    tx = x - (x - tx) * f; ty = y - (y - ty) * f;
    scale = next;
    redraw();
  }
  zoomIn.addEventListener('click', () => zoom(1.35));
  zoomOut.addEventListener('click', () => zoom(1 / 1.35));
  zoomReset.addEventListener('click', () => { scale = 1; tx = 0; ty = 0; redraw(); });
  canvas.addEventListener('wheel', ev => {
    ev.preventDefault();
    const r = canvas.getBoundingClientRect();
    zoom(ev.deltaY < 0 ? 1.12 : 1 / 1.12, ev.clientX - r.left, ev.clientY - r.top);
  }, { passive: false });
  let drag = null;
  canvas.addEventListener('pointerdown', ev => {
    if (ev.button !== 0) return;
    try { canvas.setPointerCapture(ev.pointerId); } catch { /* sintetički ili nestali pointer */ }
    drag = { id: ev.pointerId, x: ev.clientX, y: ev.clientY, tx, ty, moved: false };
  });
  canvas.addEventListener('pointermove', ev => {
    if (!drag || drag.id !== ev.pointerId) return;
    const dx = ev.clientX - drag.x, dy = ev.clientY - drag.y;
    if (Math.hypot(dx, dy) > 4) drag.moved = true;
    tx = drag.tx + dx; ty = drag.ty + dy;
    redraw();
  });
  canvas.addEventListener('pointerup', ev => {
    if (!drag || drag.id !== ev.pointerId) return;
    const click = !drag.moved;
    drag = null;
    if (!click) return;
    const r = canvas.getBoundingClientRect();
    const mx = ev.clientX - r.left, my = ev.clientY - r.top;
    let hit = null, best = 13;
    for (const p of stations) {
      if (!visible.has('stations')) break;
      const [x, y] = project(p.lat, p.lon);
      const dist = Math.hypot(mx - (x * scale + tx), my - (y * scale + ty));
      if (dist < best) { best = dist; hit = p; }
    }
    if (!hit && visible.has('iskljucenja')) {
      for (const o of opstine) {
        const [x, y] = project(o.lat, o.lon);
        if (Math.hypot(mx - (x * scale + tx), my - (y * scale + ty)) < rIskl(o.data) + 8) { hit = o; break; }
      }
    }
    if (hit) {
      selected = hit;
      if (hit.layer === 'iskljucenja') showIsklj(hit); else showDossier(hit);
      redraw();
    } else {
      /* klik u prazno (T4): „koliko znamo ovaj kraj" — neznanje je podatak */
      selected = null;
      showZnanje(mx, my);
      redraw();
    }
  });
  canvas.addEventListener('pointercancel', () => { drag = null; });
  canvas.addEventListener('keydown', ev => {
    if (ev.key === '+' || ev.key === '=') zoom(1.35);
    else if (ev.key === '-') zoom(1 / 1.35);
    else if (ev.key === '0') { scale = 1; tx = 0; ty = 0; redraw(); }
    else if (ev.key.startsWith('Arrow')) {
      tx += ev.key === 'ArrowLeft' ? 30 : ev.key === 'ArrowRight' ? -30 : 0;
      ty += ev.key === 'ArrowUp' ? 30 : ev.key === 'ArrowDown' ? -30 : 0;
      redraw();
    } else return;
    ev.preventDefault();
  });
  function showDossier(p) {
    const d = p.data;
    dossier.textContent = '';
    dossier.appendChild(el('h4', null, d.n));
    dossier.appendChild(el('p', 'meta', T().dosijeIzvor + ': ' + d.src + ' · ' + T().dosijeKoordinate + ': ' + d.la.toFixed(4) + ', ' + d.lo.toFixed(4)));
    const table = el('table');
    const thead = el('thead'); const trh = el('tr');
    for (const h of [T().dosijeParam, T().dosijeVrednost, T().dosijeStanje, T().dosijeVreme]) trh.appendChild(el('th', null, h));
    thead.appendChild(trh); table.appendChild(thead);
    const tb = el('tbody');
    for (const r of d.r || []) {
      const tr = el('tr');
      const pl = PARAM_LABEL[r.p];
      tr.appendChild(el('td', null, pl ? (LANG === 'sr' ? pl.sr : pl.en) : r.p));
      tr.appendChild(el('td', 'v', (r.v === undefined ? '—' : fmtNum(r.v, Math.abs(r.v) < 10 ? 2 : 1)) + ' ' + (UNIT_LABEL[r.u] || r.u || '')));
      const stTd = el('td');
      const g = stateGlyph(r.s, 11);
      stTd.appendChild(g);
      stTd.appendChild(document.createTextNode(' ' + mapStateWord(r.s)));
      tr.appendChild(stTd);
      tr.appendChild(el('td', null, r.t ? absTime(r.t) : (r.rx ? T().prijemHint + ' ' + absTime(r.rx) : '—')));
      tb.appendChild(tr);
    }
    table.appendChild(tb);
    dossier.appendChild(table);
    dossier.appendChild(el('p', 'meta', T().merenoHint + ' = vreme merenja; ' + T().prijemHint + ' = vreme prijema · ' + T().mapaAsOf + ' ' + absTime(M.as_of)));
  }
  function unproject(px, py) {
    const kx = Math.cos(44.8 * Math.PI / 180);
    const s = Math.min((width - 36) / ((W0.lo1 - W0.lo0) * kx), (height - 36) / (W0.la1 - W0.la0));
    const A = (width - (W0.lo1 - W0.lo0) * kx * s) / 2, B = (height - (W0.la1 - W0.la0) * s) / 2;
    return [W0.la1 - (py - B) / s, W0.lo0 + (px - A) / (kx * s)];
  }
  function kmHav(la1, lo1, la2, lo2) {
    const r = Math.PI / 180, dLa = (la2 - la1) * r, dLo = (lo2 - lo1) * r;
    const a = Math.sin(dLa / 2) ** 2 + Math.cos(la1 * r) * Math.cos(la2 * r) * Math.sin(dLo / 2) ** 2;
    return 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }
  function showIsklj(o) {
    const d = o.data;
    dossier.textContent = '';
    dossier.appendChild(el('h4', null, d.ime));
    dossier.appendChild(el('p', 'meta', T().mapaIskljProzor + ': ' + (isklj.prozor || []).join(', ') + ' · ' + d.broj_mesta + ' ' + T().mapaIskljMesta));
    for (const m of d.mesta || []) {
      const p = el('p', 'isklj-mesto');
      p.appendChild(el('b', null, m.ime));
      p.appendChild(document.createTextNode(' — ' + (m.prozori || []).join('; ')));
      dossier.appendChild(p);
    }
    dossier.appendChild(el('p', 'hint', T().mapaIskljHint));
  }
  function showZnanje(mx, my) {
    const [la, lo] = unproject((mx - tx) / scale, (my - ty) / scale);
    let senzora = 0, najnovije = 0, najblSt = null, najblD = Infinity;
    for (const st of M.stations || []) {
      const dkm = kmHav(la, lo, st.la, st.lo);
      if (dkm < najblD) { najblD = dkm; najblSt = st; }
      if (dkm <= 1.5) {
        senzora++;
        for (const r of st.r || []) { const tm = r.t ? Date.parse(r.t) : 0; if (tm > najnovije) najnovije = tm; }
      }
    }
    let pop = null, najblH = Infinity;
    for (const h of hexes) {
      const dkm = kmHav(la, lo, h.lat, h.lon);
      if (dkm < najblH) { najblH = dkm; pop = h.pop; }
    }
    dossier.textContent = '';
    dossier.appendChild(el('h4', null, T().znanjeTitle));
    dossier.appendChild(el('p', 'meta', la.toFixed(4) + ', ' + lo.toFixed(4) + (pop != null ? ' · ' + fmtNum(pop, 0) + ' ' + T().znanjePop : '')));
    if (senzora) {
      dossier.appendChild(el('p', null, senzora + ' ' + T().znanjeSenzora + (najnovije ? ' · ' + T().znanjeNajnovije + ' ' + relTime(new Date(najnovije).toISOString()) : '')));
      if (najblSt && najblD > 1.5) dossier.appendChild(el('p', 'sub', (LANG === 'sr' ? 'najbliža stanica ' : 'nearest station ') + najblSt.n + ' — ' + fmtNum(najblD, 1) + ' km'));
    } else {
      dossier.appendChild(el('p', null, T().znanjeNema + (najblSt ? ' (' + najblSt.n + ' — ' + fmtNum(najblD, 1) + ' km)' : '')));
    }
    dossier.appendChild(el('p', 'hint', T().znanjeHint));
  }
  const onTheme = () => redraw();
  window.addEventListener('resize', resize);
  document.documentElement.addEventListener('beops-theme', onTheme);
  resize();
  mapCleanup = () => {
    window.removeEventListener('resize', resize);
    document.documentElement.removeEventListener('beops-theme', onTheme);
  };
}
function stateGlyph(s, size) {
  /* oblik + boja + uz tekst uvek — legenda i dosije nose i reč */
  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('width', size); svg.setAttribute('height', size);
  svg.setAttribute('viewBox', '0 0 16 16');
  svg.setAttribute('aria-hidden', 'true');
  const col = MAP_STATE_VAR[s] || MAP_STATE_VAR.unavailable;
  const shape = document.createElementNS(NS, 'path');
  let d;
  if (s === 'untimed') d = 'M8 1 L15 8 L8 15 L1 8 Z';
  else if (s === 'estimated') d = 'M2.5 2.5 H13.5 V13.5 H2.5 Z';
  else if (s === 'forecast') d = 'M8 1.5 L14.8 14 H1.2 Z';
  else d = 'M8 1 A7 7 0 1 1 7.99 1 Z';
  shape.setAttribute('d', d);
  shape.setAttribute('fill', s === 'unavailable' ? 'none' : col);
  shape.setAttribute('stroke', col);
  shape.setAttribute('stroke-width', s === 'unavailable' ? '2' : '1');
  svg.appendChild(shape);
  return svg;
}

/* ── Pogled: #organizam ─────────────────────────────────── */
function viewOrganizam(root) {
  root.textContent = '';
  root.appendChild(sectionHead(null, T().orgTitle, T().orgSub));
  const table = el('table', 'kv');
  const thead = el('thead'); const trh = el('tr');
  for (const h of [T().organCol, T().ulogaCol, T().kadensaCol, T().poslednjiCol, T().statusCol]) trh.appendChild(el('th', null, h));
  thead.appendChild(trh); table.appendChild(thead);
  const tb = el('tbody');
  for (const o of (STATE.organizam && STATE.organizam.organs) || []) {
    const tr = el('tr');
    tr.appendChild(el('td', null, o.name));
    tr.appendChild(el('td', null, o.role || ''));
    tr.appendChild(el('td', null, (o.cadence_minutes || '?') + ' min'));
    const td = el('td');
    if (o.last_run) { td.appendChild(stampEl(o.last_run, o.cadence_minutes || 30)); td.appendChild(el('div', 'sub', absTime(o.last_run))); }
    else td.appendChild(el('span', null, T().statusUnknown));
    tr.appendChild(td);
    tr.appendChild(el('td', null, T()[o.status === 'ok' ? 'statusOk' : o.status === 'late' ? 'statusLate' : 'statusUnknown']));
    tb.appendChild(tr);
  }
  table.appendChild(tb);
  root.appendChild(table);

  root.appendChild(el('h2', null, T().izvoriTitle));
  root.appendChild(el('p', 'sub', T().izvoriSub));
  const st = el('table', 'kv');
  const sh = el('thead'); const srh = el('tr');
  for (const h of [T().izvorCol, T().oblastCol, T().starostCol]) srh.appendChild(el('th', null, h));
  sh.appendChild(srh); st.appendChild(sh);
  const sb = el('tbody');
  for (const s of ((STATE.organizam && STATE.organizam.sources) || []).slice(0, 40)) {
    const tr = el('tr');
    tr.appendChild(el('td', null, s.name));
    tr.appendChild(el('td', null, s.domain || ''));
    tr.appendChild(el('td', null, (s.reception_age_minutes === null || s.reception_age_minutes === undefined ? '—' : s.reception_age_minutes + ' min')));
    sb.appendChild(tr);
  }
  st.appendChild(sb);
  root.appendChild(st);
}

/* ── Pogled: #o ─────────────────────────────────────────── */
function viewO(root) {
  renderO(root);
  /* belažnica (K7) stiže posebnim ugovorom — strana se nacrta odmah, dopuni se */
  loadBelaznica().then(() => { if (currentRoute() === 'o') renderO(root); });
}
function belaznicaRed(naziv, g) {
  const tr = el('tr');
  tr.appendChild(el('td', null, naziv));
  tr.appendChild(el('td', 'v', String(g.misli)));
  tr.appendChild(el('td', 'v', String(g.korisno)));
  tr.appendChild(el('td', 'v', String(g.nekorisno)));
  tr.appendChild(el('td', 'v', g.deo_korisnih === null ? '—' : fmtNum(g.deo_korisnih, 2)));
  return tr;
}
function renderO(root) {
  root.textContent = '';
  root.appendChild(sectionHead(null, T().oTitle, T().oSub));
  const body = el('div', 'static');
  body.appendChild(el('h2', null, T().staJe));
  body.appendChild(el('p', null, T().staJeText));
  body.appendChild(el('h2', null, T().metod));
  const ul = el('ul');
  for (const k of ['metodLi1', 'metodLi2', 'metodLi3', 'metodLi4']) ul.appendChild(el('li', null, T()[k]));
  body.appendChild(ul);
  const d = STATE.organizam && STATE.organizam.epistemic_disclaimer;
  if (d) {
    body.appendChild(el('h2', null, T().izjava));
    body.appendChild(el('p', 'sub', LANG === 'sr' ? d.measurement_vs_inference_sr : d.measurement_vs_inference_en));
  }
  /* belažnica (K7, T3): glasovi građana kao javno učenje — prazna je iskrena */
  body.appendChild(el('h2', null, T().belaTitle));
  body.appendChild(el('p', 'sub', T().belaSub));
  const bel = STATE.belaznica;
  if (!bel) body.appendChild(el('p', null, '—'));
  else if (!bel.prihvacenih_glasova) body.appendChild(el('p', null, T().belaEmpty));
  else {
    const bt = el('table', 'kv');
    const th = el('thead'); const trh = el('tr');
    for (const h of ['', T().belaMisli, T().belaKorisno, T().belaNekorisno, T().belaDeo]) trh.appendChild(el('th', null, h));
    th.appendChild(trh); bt.appendChild(th);
    const tb = el('tbody');
    const sekcija = (naslov, acc) => {
      const tr = el('tr'); tr.appendChild(el('td', 'sec', naslov));
      for (let i = 0; i < 4; i++) tr.appendChild(el('td'));
      tb.appendChild(tr);
      for (const [k, g] of Object.entries(acc || {})) tb.appendChild(belaznicaRed(k, g));
    };
    sekcija(T().belaPoNaravi, bel.po_naravi);
    sekcija(T().belaPoNivou, bel.po_nivou);
    bt.appendChild(tb);
    body.appendChild(bt);
    const m = el('p', 'meta');
    m.appendChild(document.createTextNode(bel.prihvacenih_glasova + ' ' + T().belaGlasova + ' ' + T().belaNad + ' ' + bel.ocenjenih_misli + ' ' + T().belaMisli));
    if (bel.glasova_na_nepoznatoj_misli) m.appendChild(document.createTextNode(' · ' + bel.glasova_na_nepoznatoj_misli + ' ' + T().belaNepoznate));
    body.appendChild(m);
  }
  body.appendChild(el('h2', null, T().autorstvo));
  body.appendChild(el('p', null, 'prof. dr Darinka Golubović Matić · doc. dr Semir Poturak'));
  if (STATE.puls) {
    body.appendChild(el('p', 'sub', T().verzija + ': ' + absTime(STATE.puls.generated_at)));
  }
  root.appendChild(body);
}

/* ── Ruter ──────────────────────────────────────────────── */
const VIEWS = {
  danas: viewDanas, misli: viewMisli, podaci: viewPodaci,
  mapa: viewMapa, organizam: viewOrganizam, o: viewO,
};
function currentRoute() {
  const h = (location.hash || '#danas').replace(/^#/, '');
  return VIEWS[h] ? h : 'danas';
}
let routeSeq = 0;
function route() {
  const seq = ++routeSeq;
  const v = currentRoute();
  for (const a of document.querySelectorAll('[data-nav]')) {
    if (a.dataset.nav === v) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  }
  const root = document.getElementById('view');
  hideTT();
  VIEWS[v](root);
  if (seq === routeSeq) window.scrollTo(0, 0);
}

/* ── Statični tekst (jezik) ─────────────────────────────── */
function applyStatic() {
  document.documentElement.lang = LANG === 'sr' ? 'sr-Latn' : 'en';
  document.title = LANG === 'sr' ? 'BEOPS · Beograd — grad misli' : 'BEOPS · Belgrade — the city thinks';
  for (const n of document.querySelectorAll('[data-i18n]')) n.textContent = T()[n.dataset.i18n] || n.textContent;
  document.getElementById('lang').textContent = LANG === 'sr' ? 'EN' : 'SR';
}
function applyTopStamp() {
  const slot = document.getElementById('top-stamp');
  const edition = document.getElementById('edition');
  if (STATE.puls && slot) {
    slot.textContent = '';
    slot.appendChild(stampEl(STATE.puls.as_of, 5));
  }
  if (edition && STATE.puls) {
    edition.textContent = 'BEOPS v2 · ' + relTime(STATE.puls.as_of);
  }
}

/* ── Boot ───────────────────────────────────────────────── */
function initTheme() {
  /* Belo je podrazumevano (javni servis); tamno je izbor koji se pamti. */
  if (localStorage.getItem('beops-theme') === 'dark') document.documentElement.dataset.theme = 'dark';
  document.getElementById('theme').addEventListener('click', () => {
    const cur = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
    const next = cur === 'dark' ? 'light' : 'dark';
    if (next === 'light') delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = 'dark';
    localStorage.setItem('beops-theme', next);
    document.documentElement.dispatchEvent(new CustomEvent('beops-theme'));
  });
}
function boot() {
  initTheme();
  applyStatic();
  document.getElementById('lang').addEventListener('click', () => {
    LANG = LANG === 'sr' ? 'en' : 'sr';
    localStorage.setItem('beops-lang', LANG);
    applyStatic();
    applyTopStamp();
    route();
  });
  window.addEventListener('hashchange', route);
  const root = document.getElementById('view');
  root.appendChild(el('p', 'sub', T().tangierUcitavanje));
  loadCore().then(() => { applyTopStamp(); route(); }, err => {
    root.textContent = '';
    root.appendChild(el('p', 'razlog', T().nemaPodataka + ' (' + err.message + ')'));
  });
}
boot();
