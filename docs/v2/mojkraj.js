/* BEOPS v2 · Moj kraj (C2) — poseban modul van 64 KB budžeta shella (dosije E4).
   Registruje rutu `kraj` u VIEWS; učitava se posle app.js (defer redosled u index.html).
   Izbor opštine pamti se u localStorage — bez naloga, bez servera.
   Podaci: state/mapa.json + state/mapa_news.json (lenjo). Iskren prazan sloj:
   „nema najava u prozoru" je odgovor, ne kvar (F2: etiketa prati tekst izvora). */
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

function krajNorm(s) { return (s || '').toLowerCase().replace(/\s+/g, ' ').trim(); }
function krajIzbor() { return localStorage.getItem(KRAJ_KEY) || ''; }
function krajKm(la1, lo1, la2, lo2) {
  const r = Math.PI / 180, dLa = (la2 - la1) * r, dLo = (lo2 - lo1) * r;
  const a = Math.sin(dLa / 2) ** 2 + Math.cos(la1 * r) * Math.cos(la2 * r) * Math.sin(dLo / 2) ** 2;
  return 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function krajStaniceBlok(telo, opEntry) {
  const M = STATE.mapa;
  if (!M || !Array.isArray(M.stations) || !opEntry) return;
  const [, , la, lo] = opEntry;
  let bestRef = null, bestRefD = Infinity, uKrugu = 0;
  for (const st of M.stations) {
    if (!Number.isFinite(st.la) || !Number.isFinite(st.lo)) continue;
    const d = krajKm(la, lo, st.la, st.lo);
    if (d <= 1.5) uKrugu++;
    if (st.cls === 'reference' && d < bestRefD) { bestRefD = d; bestRef = st; }
  }
  if (!bestRef) return;
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
