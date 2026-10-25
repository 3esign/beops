/* BEOPS v2 shell — klijentska aplikacija.
   Principi (research/V2_INTERFEJS_PLAN_2026-10-25.md):
   P2 svežina se meri u čitanju (sat čitaoca vs generated_at/as_of/at),
   P3 tišina je sadržaj (prag 2× kadence → „grad ćuti“),
   P5 jedan shell, rute u klientu,
   P6 misli su glavni sadržaj, podaci su dokaz.
   Svi podaci stižu iz ./state/*.json; DOM se gradi createElement/textContent —
   nikad innerHTML sa podacima. Brendovi modela se ne prikazuju (sve je Svemir). */
'use strict';

/* ── Jezik ──────────────────────────────────────────────── */
const STR = {
  sr: {
    tagline: 'grad misli',
    footNote: 'Merenja potiču sa javnih i građanskih senzorskih mreža. Misli su AI interpretacija pod strogim epistemičkim kapijama — i prihvaćene i odbijene su javne. Svežina se meri tvojim satom, ne satom servera.',
    danasTitle: 'Beograd danas misli',
    danasSub: 'Poslednji uvidi gradske superinteligencije i živi puls grada. Svaki pečat starosti meri tvoj pregledač.',
    gradUBrojkama: 'Grad u brojkama',
    uvidiDana: 'Uvidi dana',
    otkucaji: 'Otkucaji organizma',
    uvidiEmpty: 'Još nema prihvaćenih uvida sa dovoljno dokaza u posmatranom prozoru.',
    misliTitle: 'Tok misli',
    misliSub: 'Sve misli umova grada u poslednjih 7 dana — prihvaćene i odbijene, sa razlozima.',
    filterUm: 'Um', filterStanje: 'Stanje', filterNivo: 'Nivo',
    umSve: 'svi umovi', stanjeSve: 'sve', stanjeAcc: 'prihvaćene', stanjeRej: 'odbijene',
    nivoSve: 'svi nivoi',
    aiLabel: 'AI umovi',
    hipotezePitanja: 'Hipoteze i pitanja',
    razlogOdbijanja: 'Razlog odbijanja',
    odbijenoTitle: 'Odbijeno — javna epistemika',
    odbijenoSub: 'Ništa nije tiho odbaceno: svako odbijanje ima razlog, i razlozi su javni. Ovo je deo metoda, ne kvar.',
    odbijenoNone: 'U posmatranom prozoru nema odbijenih misli za izabrane filtere.',
    reasonCol: 'Razlog (mašinski, kako je zapisan)', nCol: 'broj',
    odbijenoShow: 'Prikaži misli po ovom razlogu',
    citatHint: 'Dokaz — povezivanje sa serijom stiže u fazi F4',
    nemaPodataka: 'Stanje grada se ne učitava. Proveri da su /v2/state/*.json dostupni.',
    gradCuti: 'Grad se čuje tiše',
    gradCutiText: 'poslednji prijem podataka bilo je',
    umCuti: 'Um grada misli tiše',
    umCutiText: 'poslednja misao u toku bila je',
    sada: 'upravo sada',
    svezina: 'sveže', staro: 'staro', cuti: 'ćuti',
    pre: 'pre', uscanje: 'ago',
    nemaTrenda: 'nema 7-dnevnog trenda',
    orgTitle: 'Kako organizam diše',
    orgSub: 'Stvarni poslednji otkucaj svakog organa, čitan iz njegovog sopstvenog zapisa — ne vreme gradnje stranice.',
    organCol: 'Organ', ulogaCol: 'Uloga', kadensaCol: 'Kadensa', poslednjiCol: 'Poslednji otkucaj', statusCol: 'Status',
    izvoriTitle: 'Izvori podataka',
    izvoriSub: 'Šta sistem čita i koliko je sveže ono što je pročitao.',
    izvorCol: 'Izvor', oblastCol: 'Oblast', starostCol: 'Starost prijema',
    statusOk: 'radi', statusLate: 'kasni', statusUnknown: 'nepoznato',
    podaciTitle: 'Podaci — istraživanje',
    podaciSub: 'Serije od kojih misli citiraju dokaze. Puni prikaz (pojas običnog, anomalije, mapa) stiže u fazi F4.',
    serijaCol: 'Serija', jedinicaCol: 'Jedinica', tacakaCol: 'Tačaka (7 dana)', prozorCol: 'Prozor',
    vezeTitle: 'Stabilne veze (L5 graf)',
    vezeSub: 'Prostorno-vremenske veze koje su se održale dovoljno dugo da postanu znanje o gradu.',
    vezaCol: 'Veza', tezinaCol: 'Težina', stabilnaOdCol: 'Stabilna od',
    mapaTitle: 'Mapa',
    mapaText: 'Geo-prikaz stanica i serija je u fazi F4 — sloj nad istim state fajlovima, bez novih graditelja.',
    oTitle: 'O projektu',
    oSub: 'Šta je BEOPS, kako misli i ko stoji iza toga.',
    staJe: 'Šta je BEOPS',
    staJeText: 'BEOPS je pokušaj da grad ima digitalni kontekst koji je stvaran, proverljiv i živ: senzori i javni izvori ulaze kroz kapije koje odbijaju ono što ne može da se dokaže, umovi (Posmatrač, Sumnjalo, Povezivač i AI umovi) čitaju taj kontekst i javno misle o njemu, a građani dobijaju misli pre podataka — i mogu da provere svaku.',
    metod: 'Metod',
    metodLi1: 'Pet epistemičkih stanja; ništa nije procena bez označenog porekla.',
    metodLi2: 'Kapije odbijaju — i odbijanje je javno, sa razlogom.',
    metodLi3: 'Svežina se meri u čitanju; kad sistem ćuti, sajt to kaže.',
    metodLi4: 'Sirovi ugovori stanja su javni JSON fajlovi koje možeš preuzeti.',
    autorstvo: 'Autorstvo',
    izjava: 'Izjava (AI Act, član 50)',
    verzija: 'Stanje izgrađeno',
    tangierUcitavanje: 'Učitavam stanje grada…',
  },
  en: {
    tagline: 'the city thinks',
    footNote: 'Measurements come from public and citizen sensor networks. Thoughts are AI interpretation under strict epistemic gates — accepted and rejected alike are public. Freshness is measured by your clock, not the server’s.',
    danasTitle: 'Belgrade thinks today',
    danasSub: 'The city superintelligence’s latest insights and the live pulse. Every age stamp is measured by your browser.',
    gradUBrojkama: 'The city in numbers',
    uvidiDana: 'Insights of the day',
    otkucaji: 'Organism heartbeats',
    uvidiEmpty: 'No accepted insights with sufficient evidence in the observed window yet.',
    misliTitle: 'Stream of thoughts',
    misliSub: 'Every mind’s thoughts from the last 7 days — accepted and rejected, with reasons.',
    filterUm: 'Mind', filterStanje: 'State', filterNivo: 'Level',
    umSve: 'all minds', stanjeSve: 'all', stanjeAcc: 'accepted', stanjeRej: 'rejected',
    nivoSve: 'all levels',
    aiLabel: 'AI minds',
    hipotezePitanja: 'Hypotheses & questions',
    razlogOdbijanja: 'Rejection reason',
    odbijenoTitle: 'Rejected — public epistemics',
    odbijenoSub: 'Nothing is silently discarded: every rejection has a reason, and reasons are public. This is part of the method, not a failure.',
    odbijenoNone: 'No rejected thoughts in the observed window for the selected filters.',
    reasonCol: 'Reason (machine, as recorded)', nCol: 'count',
    odbijenoShow: 'Show thoughts for this reason',
    citatHint: 'Evidence — wiring citations to series arrives in phase F4',
    nemaPodataka: 'The city state failed to load. Check that /v2/state/*.json are reachable.',
    gradCuti: 'The city is quiet',
    gradCutiText: 'last data reception was',
    umCuti: 'The city mind thinks quietly',
    umCutiText: 'the last thought in the stream was',
    sada: 'just now',
    svezina: 'fresh', staro: 'stale', cuti: 'silent',
    pre: 'ago', uscanje: 'ago',
    nemaTrenda: 'no 7-day trend',
    orgTitle: 'How the organism breathes',
    orgSub: 'Each organ’s real last heartbeat, read from its own record — not the page build time.',
    organCol: 'Organ', ulogaCol: 'Role', kadensaCol: 'Cadence', poslednjiCol: 'Last beat', statusCol: 'Status',
    izvoriTitle: 'Data sources',
    izvoriSub: 'What the system reads, and how fresh what it read is.',
    izvorCol: 'Source', oblastCol: 'Domain', starostCol: 'Reception age',
    statusOk: 'ok', statusLate: 'late', statusUnknown: 'unknown',
    podaciTitle: 'Data — explore',
    podaciSub: 'The series thoughts cite as evidence. Full view (usual band, anomalies, map) arrives in phase F4.',
    serijaCol: 'Series', jedinicaCol: 'Unit', tacakaCol: 'Points (7 d)', prozorCol: 'Window',
    vezeTitle: 'Stable connections (L5 graph)',
    vezeSub: 'Spatio-temporal links that held long enough to become knowledge about the city.',
    vezaCol: 'Link', tezinaCol: 'Weight', stabilnaOdCol: 'Stable since',
    mapaTitle: 'Map',
    mapaText: 'The geo layer over the same state files arrives in phase F4 — no new builders.',
    oTitle: 'About',
    oSub: 'What BEOPS is, how it thinks, and who stands behind it.',
    staJe: 'What BEOPS is',
    staJeText: 'BEOPS is an attempt to give a city a digital context that is real, checkable and alive: sensors and public sources enter through gates that reject what cannot be evidenced, minds (Observer, Skeptic, Connector and AI minds) read that context and think about it in public, and citizens get thoughts before data — yet can verify every one.',
    metod: 'Method',
    metodLi1: 'Five epistemic states; nothing is an estimate without a marked origin.',
    metodLi2: 'Gates reject — and rejection is public, with a reason.',
    metodLi3: 'Freshness is measured at reading time; when the system is silent, the site says so.',
    metodLi4: 'The raw state contracts are public JSON files you can download.',
    autorstvo: 'Authorship',
    izjava: 'Statement (AI Act, article 50)',
    verzija: 'State built',
    tangierUcitavanje: 'Loading the city state…',
  },
};
let LANG = localStorage.getItem('beops-lang') === 'en' ? 'en' : 'sr';
const T = () => STR[LANG];

/* ── Stanje ─────────────────────────────────────────────── */
const STATE = { puls: null, misli: null, organizam: null, veze: null, serije: {} };
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
function mindKey(t) { return t.origin === 'ai_feed' ? 'ai' : (t.entity || 'unknown'); }
function mindName(t) {
  const k = mindKey(t);
  if (k === 'ai') return T().aiLabel;
  return t.entity_label || t.entity_sr || k;
}
function mindVar(k) {
  return { observer: 'var(--um-observer)', skeptic: 'var(--um-skeptic)', connector: 'var(--um-connector)', ai: 'var(--um-ai)', organelle: 'var(--um-organelle)' }[k] || 'var(--muted)';
}
function mindDisplayName(k) {
  const sr = { observer: 'Posmatrač', skeptic: 'Sumnjalo', connector: 'Povezivač', ai: null, organelle: 'Organela' };
  const en = { observer: 'Observer', skeptic: 'Skeptic', connector: 'Connector', ai: null, organelle: 'Organelle' };
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
/* rejection_reason stiže iz dva izvora: niz (organ mind) i string (ai_feed) */
function rejectionReason(t) {
  const r = t.rejection_reason;
  if (Array.isArray(r)) return r.filter(Boolean).join(' · ');
  return r ? String(r) : '';
}

/* ── Sparkline (stat tile trend) ────────────────────────── */
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

function sparkTile(points, unit) {
  /* points: [isoHour, mean, ...] — prava vremenska osa, 2px linija u prigušenoj
     nijansi, poslednji segment + tačka u akcentu, crosshair + tooltip,
     tastatura: fokusiše se i strele pomeraju aktivnu tačku. */
  const wrap = el('div', 'spark tile-spark');
  const pts = (points || []).map(p => ({ x: Date.parse(p[0] + ':00:00Z'), v: p[1] }))
    .filter(p => Number.isFinite(p.x) && p.v !== null && Number.isFinite(p.v));
  if (pts.length < 2) {
    wrap.appendChild(el('span', 'tile-unit', T().nemaTrenda));
    return wrap;
  }
  const W = 120, H = 34, PAD = 4;
  const xs = pts.map(p => p.x), ys = pts.map(p => p.v);
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  let y0 = Math.min(...ys), y1 = Math.max(...ys);
  if (y1 - y0 < 1e-9) { y1 = y0 + 1; }
  const sx = t => PAD + (t - x0) / (x1 - x0) * (W - 2 * PAD);
  const sy = v => H - PAD - (v - y0) / (y1 - y0) * (H - 2 * PAD);
  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('width', W); svg.setAttribute('height', H);
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('aria-hidden', 'true');
  const mk = (tag, at) => { const n = document.createElementNS(NS, tag); for (const k in at) n.setAttribute(k, at[k]); return n; };
  const d = pts.map((p, i) => (i ? 'L' : 'M') + sx(p.x).toFixed(1) + ' ' + sy(p.v).toFixed(1)).join(' ');
  svg.appendChild(mk('path', { d, fill: 'none', stroke: 'var(--spark-dim)', 'stroke-width': '2', 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }));
  const last = pts.length - 1;
  const dLast = 'M' + sx(pts[last - 1].x).toFixed(1) + ' ' + sy(pts[last - 1].v).toFixed(1) +
    ' L' + sx(pts[last].x).toFixed(1) + ' ' + sy(pts[last].v).toFixed(1);
  svg.appendChild(mk('path', { d: dLast, fill: 'none', stroke: 'var(--accent)', 'stroke-width': '2', 'stroke-linecap': 'round' }));
  const cross = mk('line', { x1: 0, x2: 0, y1: 0, y2: H, stroke: 'var(--axis)', 'stroke-width': '1', visibility: 'hidden' });
  svg.appendChild(cross);
  const dot = mk('circle', { cx: sx(pts[last].x), cy: sy(pts[last].v), r: 4, fill: 'var(--accent)', stroke: 'var(--surface-1)', 'stroke-width': '2' });
  svg.appendChild(dot);

  let active = -1;
  const setIdx = (i, clientX, clientY) => {
    i = Math.max(0, Math.min(pts.length - 1, i));
    if (i === active && clientX === undefined) return;
    active = i;
    const px = sx(pts[i].x);
    cross.setAttribute('x1', px); cross.setAttribute('x2', px);
    cross.setAttribute('visibility', 'visible');
    dot.setAttribute('cx', px); dot.setAttribute('cy', sy(pts[i].v));
    const r = wrap.getBoundingClientRect();
    const ax = clientX !== undefined ? clientX : r.left + px / W * r.width;
    const ay = clientY !== undefined ? clientY : r.top + sy(pts[i].v) / H * r.height;
    showTT(ax, ay, fmtNum(pts[i].v) + ' ' + (unit || ''), absTime(new Date(pts[i].x).toISOString().replace('.000Z', 'Z')));
  };
  const clear = () => {
    active = -1; cross.setAttribute('visibility', 'hidden');
    dot.setAttribute('cx', sx(pts[last].x)); dot.setAttribute('cy', sy(pts[last].v));
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
  wrap.tabIndex = 0;
  wrap.setAttribute('role', 'img');
  const firstT = absTime(new Date(x0).toISOString().replace('.000Z', 'Z'));
  const lastT = absTime(new Date(x1).toISOString().replace('.000Z', 'Z'));
  wrap.setAttribute('aria-label', `${pts.length} tačaka, ${firstT} – ${lastT}, poslednja ${fmtNum(pts[last].v)} ${unit || ''}`);
  wrap.addEventListener('keydown', ev => {
    if (ev.key === 'ArrowLeft' || ev.key === 'ArrowRight') {
      ev.preventDefault();
      setIdx(active < 0 ? last : active + (ev.key === 'ArrowRight' ? 1 : -1));
    } else if (ev.key === 'Escape') clear();
  });
  wrap.addEventListener('blur', clear);
  wrap.appendChild(svg);
  return wrap;
}

/* ── Kartica misli ──────────────────────────────────────── */
function thoughtCard(t) {
  const card = el('article', 'misao' + (t.state === 'rejected' ? ' rejected' : ''));
  const head = el('div', 'misao-head');
  head.appendChild(mindChip(t));
  const lvl = el('span', null, (T().filterNivo) + ': ' + (t.level || '—'));
  head.appendChild(lvl);
  const sp = el('span'); sp.style.marginLeft = 'auto'; head.appendChild(sp);
  head.appendChild(stampEl(t.at, 4));
  const tim = el('time', null, absTime(t.at));
  tim.setAttribute('datetime', t.at);
  head.appendChild(tim);
  card.appendChild(head);

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
  if ((t.cites || []).length) {
    const c = el('div', 'cites');
    for (const cid of t.cites) {
      const ch = el('span', 'cite', '[' + cid + ']');
      ch.title = T().citatHint;
      c.appendChild(ch);
    }
    card.appendChild(c);
  }
  return card;
}

/* ── Pogled: #danas ─────────────────────────────────────── */
function tileDef(id, labelSr, labelEn, unit, metricKey, seriesId, upIsBad) {
  return { id, labelSr, labelEn, unit, metricKey, seriesId, upIsBad };
}
function tileLabel(m) { return LANG === 'sr' ? m.labelSr : m.labelEn; }
const TILES = [
  null, // hero (AQI) se gradi posebno
  tileDef('pm25', 'PM2.5 prosek', 'PM2.5 mean', 'µg/m³', 'pm25', 'pm25', true),
  tileDef('pm10', 'PM10 prosek', 'PM10 mean', 'µg/m³', 'pm10', 'pm10', true),
  tileDef('no2', 'NO₂ prosek', 'NO₂ mean', 'µg/m³', 'no2', null, true),
  tileDef('o3', 'O₃ prosek', 'O₃ mean', 'µg/m³', 'o3', null, false),
  tileDef('temp', 'Temperatura', 'Temperature', '°C', 'meteo:temperature', 'temperature', null),
  tileDef('rh', 'Vlažnost', 'Humidity', '%', 'meteo:humidity', 'humidity', null),
];

function metricValue(m) {
  const [grp, key] = m.metricKey.split(':');
  const src = STATE.puls && STATE.puls.current_metrics && STATE.puls.current_metrics[grp];
  if (!src) return null;
  if (!key) return src.mean !== undefined ? src.mean : src;
  return src[key];
}
function delta24h(series) {
  if (!series || !Array.isArray(series.points) || series.points.length < 2) return null;
  const pts = series.points.filter(p => p[1] !== null).map(p => [Date.parse(p[0] + ':00:00Z'), p[1]]);
  if (pts.length < 2) return null;
  const lastX = pts[pts.length - 1][0], lastV = pts[pts.length - 1][1];
  const target = lastX - 24 * 3600e3;
  let best = null, bd = Infinity;
  for (const [x, v] of pts) { const d = Math.abs(x - target); if (d < bd) { bd = d; best = v; } }
  return Number.isFinite(best) ? lastV - best : null;
}
function metricTile(m) {
  const tile = el('div', 'tile');
  tile.appendChild(el('div', 'tile-label', tileLabel(m)));
  const v = metricValue(m);
  tile.appendChild(el('div', 'tile-value', fmtNum(v)));
  tile.appendChild(el('div', 'tile-unit', m.unit));
  const foot = el('div', 'tile-foot');
  const ser = STATE.serije[m.seriesId];
  const d = ser ? delta24h(ser) : null;
  if (d !== null && Math.abs(d) > 0.049) {
    const dl = el('div', 'tile-delta');
    const dir = el('span', d > 0 ? 'dir-up' : 'dir-down', (d > 0 ? '▲ +' : '▼ −') + fmtNum(Math.abs(d)));
    if (m.upIsBad === null) { dir.className = ''; dir.style.color = 'var(--ink-2)'; }
    dl.appendChild(dir);
    dl.appendChild(document.createTextNode(' / 24 h'));
    foot.appendChild(dl);
  } else {
    foot.appendChild(el('div', 'tile-delta', ' '));
  }
  if (STATE.puls && STATE.puls.as_of) foot.appendChild(stampEl(STATE.puls.as_of, 5));
  tile.appendChild(foot);
  if (ser) tile.appendChild(sparkTile(ser.points, m.unit));
  return tile;
}
function heroTile() {
  const cs = (STATE.puls && STATE.puls.city_status) || {};
  const tile = el('div', 'tile hero');
  tile.appendChild(el('div', 'tile-label', LANG === 'sr' ? 'Vazduh — AQI (US)' : 'Air — AQI (US)'));
  tile.appendChild(el('div', 'tile-value', cs.aqi_us === null || cs.aqi_us === undefined ? '—' : String(cs.aqi_us)));
  tile.appendChild(el('div', 'tile-unit', (LANG === 'sr' ? cs.summary_sr : cs.summary_en) || cs.category || ''));
  const foot = el('div', 'tile-foot');
  if (cs.dominant_pollutant) foot.appendChild(el('div', 'tile-delta', (LANG === 'sr' ? 'dominira ' : 'dominant ') + cs.dominant_pollutant));
  if (STATE.puls && STATE.puls.as_of) foot.appendChild(stampEl(STATE.puls.as_of, 5));
  tile.appendChild(foot);
  return tile;
}

function viewDanas(root) {
  loadSerije().then(() => { if (currentRoute() === 'danas') renderDanas(root); });
  renderDanas(root);
}
function renderDanas(root) {
  root.textContent = '';
  root.appendChild(el('h1', null, T().danasTitle));
  root.appendChild(el('p', 'sub', T().danasSub));

  const cs = STATE.puls && STATE.puls.city_status;
  if (cs) {
    root.appendChild(banner(
      LANG === 'sr' ? 'Vazduh: ' : 'Air: ',
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

  root.appendChild(el('h2', null, T().gradUBrojkama));
  const tiles = el('div', 'tiles');
  tiles.appendChild(heroTile());
  for (const m of TILES.slice(1)) tiles.appendChild(metricTile(m));
  root.appendChild(tiles);

  root.appendChild(el('h2', null, T().uvidiDana));
  const acc = ((STATE.misli && STATE.misli.thoughts) || []).filter(t => t.state === 'accepted')
    .map(t => ({ t, score: ((t.cites || []).length >= 2 ? 1 : 0) + (t.claim ? 2 : 0) + ((t.hypotheses_sr || []).length ? 1 : 0) }))
    .sort((a, b) => b.score - a.score || Date.parse(b.t.at) - Date.parse(a.t.at))
    .slice(0, 5);
  if (!acc.length) { root.appendChild(el('p', 'sub', T().uvidiEmpty)); }
  for (const { t } of acc) root.appendChild(thoughtCard(t));

  root.appendChild(el('h2', null, T().otkucaji));
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
  root.appendChild(el('h1', null, T().misliTitle));
  root.appendChild(el('p', 'sub', T().misliSub));

  const newest = newestThoughtAt();
  if (newest && tier(newest, 4) === 'silent') {
    root.appendChild(banner(T().umCuti + ' —', T().umCutiText, null, newest, false));
  }

  const f = el('div', 'filters');
  const mindOpts = [['all', T().umSve], ['observer', mindDisplayName('observer')], ['skeptic', mindDisplayName('skeptic')], ['connector', mindDisplayName('connector')], ['organelle', mindDisplayName('organelle')], ['ai', mindDisplayName('ai')]];
  f.appendChild(selectFilter(T().filterUm + ':', mindOpts, MISLI_F.um, v => { MISLI_F.um = v; route(); }));
  f.appendChild(selectFilter(T().filterStanje + ':', [
    ['acc', T().stanjeAcc], ['rej', T().stanjeRej], ['all', T().stanjeSve],
  ], MISLI_F.stanje, v => { MISLI_F.stanje = v; route(); }));
  const levels = [...new Set(((STATE.misli && STATE.misli.thoughts) || []).map(t => t.level).filter(Boolean))];
  f.appendChild(selectFilter(T().filterNivo + ':', [['all', T().nivoSve], ...levels.map(l => [l, l])], MISLI_F.nivo, v => { MISLI_F.nivo = v; route(); }));
  /* legenda identiteta: tačke u filteru su legenda umova */
  for (const k of ['observer', 'skeptic', 'connector', 'organelle', 'ai']) {
    const lab = el('label');
    const dot = el('span', 'mind-dot'); dot.style.background = mindVar(k); dot.setAttribute('aria-hidden', 'true');
    lab.appendChild(dot);
    lab.appendChild(document.createTextNode(' ' + mindDisplayName(k)));
    f.appendChild(lab);
  }
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
      txt.style.fontSize = '12.5px';
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

/* ── Pogled: #organizam ─────────────────────────────────── */
function viewOrganizam(root) {
  root.textContent = '';
  root.appendChild(el('h1', null, T().orgTitle));
  root.appendChild(el('p', 'sub', T().orgSub));
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
  for (const s of ((STATE.organizam && STATE.organizam.sources) || []).slice(0, 30)) {
    const tr = el('tr');
    tr.appendChild(el('td', null, s.name));
    tr.appendChild(el('td', null, s.domain || ''));
    tr.appendChild(el('td', null, (s.reception_age_minutes === null || s.reception_age_minutes === undefined ? '—' : s.reception_age_minutes + ' min')));
    sb.appendChild(tr);
  }
  st.appendChild(sb);
  root.appendChild(st);
}

/* ── Pogled: #podaci ────────────────────────────────────── */
function viewPodaci(root) {
  loadVeze().then(() => { if (currentRoute() === 'podaci') renderPodaci(root); });
  renderPodaci(root);
}
function renderPodaci(root) {
  root.textContent = '';
  root.appendChild(el('h1', null, T().podaciTitle));
  root.appendChild(el('p', 'sub', T().podaciSub));

  root.appendChild(el('h2', null, T().serijaCol));
  const table = el('table', 'kv');
  const sh = el('thead'); const srh = el('tr');
  for (const h of [T().serijaCol, T().jedinicaCol, T().tacakaCol, T().prozorCol]) srh.appendChild(el('th', null, h));
  sh.appendChild(srh); table.appendChild(sh);
  const sb = el('tbody');
  for (const id of SERIES_IDS) {
    const s = STATE.serije[id];
    if (!s) continue;
    const tr = el('tr');
    tr.appendChild(el('td', null, s.metric));
    tr.appendChild(el('td', null, s.unit || ''));
    tr.appendChild(el('td', null, String(s.total_points)));
    tr.appendChild(el('td', null, s.window_days + ' d'));
    sb.appendChild(tr);
  }
  table.appendChild(sb);
  root.appendChild(table);

  if (STATE.veze) {
    root.appendChild(el('h2', null, T().vezeTitle));
    root.appendChild(el('p', 'sub', T().vezeSub + ' — ' + (STATE.veze.stable_edges_count || 0) + ' / ' + (STATE.veze.total_edges || 0)));
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
    root.appendChild(vt);
  }
}

/* ── Pogled: #mapa, #o ──────────────────────────────────── */
function viewMapa(root) {
  root.textContent = '';
  root.appendChild(el('h1', null, T().mapaTitle));
  root.appendChild(el('div', 'placeholder', T().mapaText));
}
function viewO(root) {
  root.textContent = '';
  root.appendChild(el('h1', null, T().oTitle));
  root.appendChild(el('p', 'sub', T().oSub));
  root.appendChild(el('h2', null, T().staJe));
  root.appendChild(el('p', null, T().staJeText));
  root.appendChild(el('h2', null, T().metod));
  const ul = el('ul');
  for (const k of ['metodLi1', 'metodLi2', 'metodLi3', 'metodLi4']) ul.appendChild(el('li', null, T()[k]));
  root.appendChild(ul);
  const d = STATE.organizam && STATE.organizam.epistemic_disclaimer;
  if (d) {
    root.appendChild(el('h2', null, T().izjava));
    root.appendChild(el('p', 'sub', LANG === 'sr' ? d.measurement_vs_inference_sr : d.measurement_vs_inference_en));
  }
  root.appendChild(el('h2', null, T().autorstvo));
  root.appendChild(el('p', null, 'prof. dr Darinka Golubović Matić · doc. dr Semir Poturak'));
  if (STATE.puls) {
    root.appendChild(el('p', 'sub', T().verzija + ': ' + absTime(STATE.puls.generated_at)));
  }
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

/* ── Boot ───────────────────────────────────────────────── */
function initTheme() {
  const saved = localStorage.getItem('beops-theme');
  if (saved === 'dark' || saved === 'light') document.documentElement.dataset.theme = saved;
  document.getElementById('theme').addEventListener('click', () => {
    const cur = document.documentElement.dataset.theme ||
      (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('beops-theme', next);
  });
}
function boot() {
  initTheme();
  applyStatic();
  document.getElementById('lang').addEventListener('click', () => {
    LANG = LANG === 'sr' ? 'en' : 'sr';
    localStorage.setItem('beops-lang', LANG);
    applyStatic();
    route();
  });
  window.addEventListener('hashchange', route);
  const root = document.getElementById('view');
  root.appendChild(el('p', 'sub', T().tangierUcitavanje));
  loadCore().then(route, err => {
    root.textContent = '';
    root.appendChild(el('p', 'razlog', T().nemaPodataka + ' (' + err.message + ')'));
  });
}
boot();
