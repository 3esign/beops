/* BEOPS v2 ulice.js — „Moj kraj“ po ulici i naselju (D-005 + rok važenja najave). Bez innerHTML; sr/en. */
'use strict';
/* global el, jfetch, dlRow, fmtNum, currentRoute, STATE, PARAM_LABEL, UNIT_LABEL, KRAJ_KEY, krajIzbor, krajNorm, krajKm, LANG */
(function () {
  const KEY = 'beops-kraj-mesto';
  let data = null, loading = false, raf = 0, stil = false, query = '', showExp = false, sel = null;
  try { sel = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch { sel = null; }

  const CM = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','ђ':'dj','е':'e','ж':'z','з':'z','и':'i','ј':'j',
    'к':'k','л':'l','љ':'lj','м':'m','н':'n','њ':'nj','о':'o','п':'p','р':'r','с':'s','т':'t',
    'ћ':'c','у':'u','ф':'f','х':'h','ц':'c','ч':'c','џ':'dz','ш':'s','č':'c','ć':'c','š':'s','ž':'z','đ':'dj'
  };
  function fold(s) {
    let o = ''; const low = String(s || '').toLowerCase();
    for (let i = 0; i < low.length; i++) o += CM[low[i]] || low[i];
    return o.replace(/[^a-z0-9]+/g, ' ').trim();
  }

  const TXT = {
    sr: {
      title: 'Ulica ili naselje (D-005)',
      sub: 'Registar naselja (OSM ODbL / Wikidata CC0) i komunalne najave sa rokom važenja po tvom satu.',
      ph: 'Ulica ili naselje (npr. Mirijevo, Cvijićeva, Ripanj)…',
      lbl: 'Pretraga ulice ili naselja', clear: 'Očisti', naselje: 'naselje', ulica: 'ulica',
      act: 'U TOKU', up: 'NAJAVLJENO', exp: 'ISTEKLO',
      vJos: 'važi još', pZa: 'počinje za', iPre: 'isteklo pre',
      geoOk: 'D-005', geoNo: 'bez koordinata',
      staVazi: 'Šta važi', struja: 'Struja (EPS)', voda: 'Voda (BVK)', grejanje: 'Grejanje',
      vazduh: 'Najbliža ref. stanica',
      nemaM: 'Nema aktivnih ni najavljenih isključenja za ovo mesto.',
      nemaA: 'Nema aktivnih ni najavljenih obustava za opštinu.',
      ostale: 'Ostale ulice u opštini',
      pExp: 'Istekle najave (24 h)', sExp: 'Sakrij istekle',
      najNas: 'Najave po ulici sa rokom važenja', van: 'Van Beograda',
      zadnji: 'poslednji', nemaP: 'Nema u prozoru',
      bezR: 'Nema poklapanja.',
      dl: 'kraj (.json)',
    },
    en: {
      title: 'Street or neighborhood (D-005)',
      sub: 'Settlement register (OSM ODbL / Wikidata CC0) and utility notices checked against your clock.',
      ph: 'Street or neighborhood (e.g. Mirijevo, Cvijićeva, Ripanj)…',
      lbl: 'Search street or neighborhood', clear: 'Clear', naselje: 'neighborhood', ulica: 'street',
      act: 'ACTIVE', up: 'UPCOMING', exp: 'EXPIRED',
      vJos: 'ends in', pZa: 'starts in', iPre: 'ended ago',
      geoOk: 'D-005', geoNo: 'no coordinates',
      staVazi: 'What applies', struja: 'Power (EPS)', voda: 'Water (BVK)', grejanje: 'Heating',
      vazduh: 'Nearest ref. station',
      nemaM: 'No active or upcoming outages for this place.',
      nemaA: 'No active or upcoming notices for this municipality.',
      ostale: 'Other streets in municipality',
      pExp: 'Expired notices (24 h)', sExp: 'Hide expired',
      najNas: 'Street notices with validity', van: 'Outside Belgrade',
      zadnji: 'last', nemaP: 'None in window',
      bezR: 'No matches.',
      dl: 'kraj (.json)',
    },
  };
  const L = () => TXT[typeof LANG === 'string' && LANG === 'en' ? 'en' : 'sr'];

  function stilovi() {
    if (stil) return;
    stil = true;
    const s = document.createElement('style');
    s.setAttribute('data-beops', 'ulice');
    s.textContent =
      '#ulice-block{margin:14px 0;padding:12px 14px;border:1px solid var(--line,#e2e6e4);border-radius:10px;background:var(--paper,#fff)}' +
      '#ulice-block h3{margin:0 0 4px;font-size:1.05rem}.ul-row,.ul-kv{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:6px 0}' +
      '.ul-in{flex:1;min-width:200px;max-width:460px;padding:7px 9px;border:1px solid var(--line,#e2e6e4);border-radius:8px;background:var(--bg,#f6f7f6);color:inherit;font:inherit}' +
      '.ul-in:focus-visible,.ul-hit:focus-visible{outline:2px solid var(--blue,#1d6fa5)}' +
      '.ul-btn,.ul-hit{padding:5px 9px;border:1px solid var(--line,#e2e6e4);border-radius:8px;color:inherit;font:inherit;cursor:pointer}' +
      '.ul-btn{background:var(--bg,#f6f7f6);font-size:.82rem}.ul-hits{display:flex;flex-direction:column;gap:4px;margin:6px 0;max-width:560px}' +
      '.ul-hit{display:flex;justify-content:space-between;align-items:center;gap:8px;background:var(--paper,#fff);font-size:.86rem;text-align:left}' +
      '.ul-card{margin:8px 0;padding:10px 12px;border:1px solid var(--line,#e2e6e4);border-radius:8px;background:var(--bg,#f6f7f6)}' +
      '.ul-card h4{margin:0 0 6px;font-size:.96rem}.ul-pill{display:inline-block;padding:2px 7px;border-radius:999px;font-size:.75rem;font-weight:700;border:1px solid var(--line,#e2e6e4)}' +
      '.ul-pill.act{background:#fee2e2;color:#991b1b}.ul-pill.up{background:#fef3c7;color:#92400e}.ul-pill.exp{background:var(--bg,#f6f7f6);color:var(--ink-2,#555)}' +
      '.ul-n{padding:7px 9px;margin:5px 0;border-left:3px solid var(--blue,#1d6fa5);background:var(--paper,#fff);border-radius:4px;font-size:.86rem}' +
      '.ul-n.act{border-left-color:#dc2626}.ul-n.up{border-left-color:#d97706}.ul-n.exp{border-left-color:var(--line,#cbd5e1);opacity:.78}' +
      '.ul-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px;margin:6px 0}' +
      '.ul-mini{padding:7px 9px;border:1px solid var(--line,#e2e6e4);border-radius:8px;background:var(--paper,#fff);font-size:.84rem}';
    document.head.appendChild(s);
  }

  function dur(ms) {
    const m = Math.max(1, Math.round(Math.abs(ms) / 60000));
    if (m < 60) return m + ' min';
    const h = Math.floor(m / 60), rm = m % 60;
    return h < 48 ? h + ' h' + (rm ? ' ' + rm + ' min' : '') : Math.round(h / 24) + ' d';
  }

  function val(naj) {
    const now = Date.now(), od = Date.parse(naj.vazi_od), d0 = Date.parse(naj.vazi_do);
    if (!Number.isFinite(od) || !Number.isFinite(d0)) return { cls: 'up', lbl: L().up, rel: '' };
    if (now >= od && now < d0) return { cls: 'act', lbl: L().act, rel: L().vJos + ' ' + dur(d0 - now) };
    if (now < od) return { cls: 'up', lbl: L().up, rel: L().pZa + ' ' + dur(od - now) };
    return { cls: 'exp', lbl: L().exp, rel: L().iPre + ' ' + dur(now - d0) };
  }

  const opLbl = (i, fb) => (data && data.opstine && i != null && data.opstine[i]) ? data.opstine[i][0] : (fb || '');

  function renderNotice(naj, filterName) {
    const v = val(naj), box = el('div', 'ul-n ' + v.cls), head = el('div', 'ul-kv');
    head.appendChild(el('span', 'ul-pill ' + v.cls, v.lbl));
    head.appendChild(el('b', null, opLbl(naj.op, naj.op_ime) + ' · ' + naj.d + ' ' + naj.od + '–' + naj.do));
    if (v.rel) head.appendChild(el('span', 'meta', v.rel));
    if (naj.van_beograda) head.appendChild(el('span', 'ul-pill exp', L().van + ': ' + (naj.stvarna_opstina || '')));
    box.appendChild(head);
    const ms = naj.mesta || [];
    if (ms.length) {
      const fk = filterName ? fold(filterName) : '';
      const pts = ms.map(m => m.n + (m.br ? ': ' + m.br : ''));
      const hi = fk ? ms.findIndex(m => fold(m.n).includes(fk)) : -1;
      const sh = hi >= 0 ? [pts[hi]].concat(pts.filter((_, i) => i !== hi).slice(0, 4)) : pts.slice(0, 6);
      box.appendChild(el('p', null, sh.join('; ') + (pts.length > sh.length ? ' (+' + (pts.length - sh.length) + ')' : '')));
    } else if (naj.txt) box.appendChild(el('p', null, naj.txt));
    box.appendChild(el('p', 'meta', naj.izvor + (naj.rok_procena ? ' · procena kraja dana' : '')));
    return box;
  }

  function buildIndex() {
    const out = [], seen = new Set();
    for (const naj of (data.najave || [])) {
      const st = val(naj), oi = opLbl(naj.op, naj.op_ime);
      for (const m of (naj.mesta || [])) {
        const k = fold(m.n) + '|' + (naj.op != null ? naj.op : naj.op_ime);
        if (seen.has(k)) continue;
        seen.add(k);
        out.push({ n: m.n, t: m.t || 'ulica', op: naj.op, op_ime: oi, la: m.la ?? null, lo: m.lo ?? null, badge: st.cls !== 'exp' ? st : null, fk: fold(m.n + ' ' + oi) });
      }
    }
    for (const [n, op, la, lo] of (data.naselja || [])) {
      const k = fold(n) + '|' + op;
      if (seen.has(k)) continue;
      seen.add(k);
      const oi = opLbl(op, '');
      out.push({ n, t: 'naselje', op, op_ime: oi, la, lo, badge: null, fk: fold(n + ' ' + oi) });
    }
    return out;
  }

  function nearRef(la, lo) {
    const M = typeof STATE === 'object' && STATE && STATE.mapa;
    if (!M || !Array.isArray(M.stations) || !Number.isFinite(la) || !Number.isFinite(lo)) return null;
    let best = null, bd = Infinity, nr = 0;
    for (const st of M.stations) {
      if (!Number.isFinite(st.la) || !Number.isFinite(st.lo)) continue;
      const d = krajKm(la, lo, st.la, st.lo);
      if (d <= 1.5) nr++;
      if (st.cls === 'reference' && d < bd) { bd = d; best = st; }
    }
    return best ? { st: best, d: bd, nr } : null;
  }

  function renderCard(wrap, s) {
    const card = el('div', 'ul-card');
    card.appendChild(el('h4', null, L().staVazi + ': ' + s.n + ' (' + (s.t === 'naselje' ? L().naselje : L().ulica) + ', ' + s.op_ime + ')'));
    card.appendChild(el('p', 'meta', Number.isFinite(s.la) && Number.isFinite(s.lo)
      ? L().geoOk + ': ' + fmtNum(s.la, 4) + ', ' + fmtNum(s.lo, 4) + ' · OSM ODbL / Wikidata CC0' : L().geoNo));
    const sk = fold(s.n), dir = [], same = [];
    for (const n of (data.najave || [])) {
      const v = val(n);
      if (!showExp && v.cls === 'exp') continue;
      const hm = (n.mesta || []).some(m => { const fm = fold(m.n); return fm === sk || fm.includes(sk) || sk.includes(fm); });
      if (hm && (s.op == null || n.op === s.op)) dir.push(n);
      else if (s.op != null && n.op === s.op && v.cls !== 'exp') same.push(n);
    }
    const g = el('div', 'ul-grid');
    const b1 = el('div', 'ul-mini');
    b1.appendChild(el('b', null, L().struja));
    if (dir.length) dir.forEach(n => b1.appendChild(renderNotice(n, s.n)));
    else b1.appendChild(el('p', 'meta', L().nemaM));
    g.appendChild(b1);

    const pok = data.pokrivenost || {}, pv = pok.voda || {}, pg = pok.grejanje || {};
    const b2 = el('div', 'ul-mini');
    b2.appendChild(el('b', null, L().voda + ' · ' + L().grejanje));
    b2.appendChild(el('p', 'meta', L().voda + ': ' + (pv.najava ? pv.najava : L().nemaP + (pv.poslednji_zapis ? ' (' + L().zadnji + ': ' + pv.poslednji_zapis + ')' : ''))));
    b2.appendChild(el('p', 'meta', L().grejanje + ': ' + (pg.najava ? pg.najava : (pg.napomena || L().nemaP))));
    g.appendChild(b2);

    const ref = nearRef(s.la, s.lo);
    if (ref) {
      const b3 = el('div', 'ul-mini');
      b3.appendChild(el('b', null, L().vazduh));
      b3.appendChild(el('p', 'meta', ref.st.n + ' (' + fmtNum(ref.d, 1) + ' km) · ' + ref.nr + ' senz. ≤1,5 km'));
      const kv = el('div', 'ul-kv');
      for (const r of (ref.st.r || []).slice(0, 4)) {
        if (r.v === undefined) continue;
        const pl = typeof PARAM_LABEL === 'object' && PARAM_LABEL[r.p];
        const un = (typeof UNIT_LABEL === 'object' && UNIT_LABEL[r.u]) || r.u || '';
        kv.appendChild(el('span', 'ul-pill exp', (pl ? pl[LANG] : r.p) + ': ' + fmtNum(r.v, 1) + ' ' + un));
      }
      b3.appendChild(kv);
      g.appendChild(b3);
    }
    card.appendChild(g);
    if (same.length) {
      card.appendChild(el('p', 'meta', L().ostale + ' (' + same.length + '):'));
      same.slice(0, 3).forEach(n => card.appendChild(renderNotice(n, null)));
    }
    wrap.appendChild(card);
  }

  function renderBlock(koren) {
    if (!data) return;
    stilovi();
    let wrap = document.getElementById('ulice-block');
    if (!wrap) {
      wrap = el('section', 'ulice-block');
      wrap.id = 'ulice-block';
      const iz = koren.querySelector('.kraj-izbor');
      if (iz && iz.nextSibling) koren.insertBefore(wrap, iz.nextSibling);
      else koren.appendChild(wrap);
    }
    wrap.textContent = '';
    wrap.appendChild(el('h3', null, L().title));
    wrap.appendChild(el('p', 'meta', L().sub));

    const row = el('div', 'ul-row'), inp = el('input', 'ul-in');
    inp.type = 'search'; inp.value = query; inp.placeholder = L().ph; inp.setAttribute('aria-label', L().lbl);
    row.appendChild(inp);
    if (sel) {
      const clr = el('button', 'ul-btn', L().clear);
      clr.type = 'button';
      clr.addEventListener('click', () => { sel = null; localStorage.removeItem(KEY); renderBlock(koren); });
      row.appendChild(clr);
    }
    wrap.appendChild(row);

    const hits = el('div', 'ul-hits');
    hits.setAttribute('role', 'listbox');
    wrap.appendChild(hits);

    const idx = buildIndex();
    const rank = (it, qf) => {
      const fn = fold(it.n);
      if (fn === qf) return 0;
      if (fn.startsWith(qf)) return 1;
      return it.fk.includes(qf) ? 2 : 9;
    };
    const fill = q => {
      hits.textContent = '';
      const qf = fold(q);
      if (qf.length < 2) return;
      const ms = idx.map(it => [rank(it, qf), it]).filter(x => x[0] < 9)
        .sort((a, b) => a[0] - b[0] || (b[1].badge ? 1 : 0) - (a[1].badge ? 1 : 0)).slice(0, 10).map(x => x[1]);
      if (!ms.length) { hits.appendChild(el('p', 'meta', L().bezR)); return; }
      for (const it of ms) {
        const b = el('button', 'ul-hit');
        b.type = 'button';
        b.appendChild(el('span', null, it.n + ' · ' + it.op_ime + ' (' + (it.t === 'naselje' ? L().naselje : L().ulica) + ')'));
        if (it.badge) b.appendChild(el('span', 'ul-pill ' + it.badge.cls, it.badge.lbl));
        b.addEventListener('click', () => {
          sel = { n: it.n, t: it.t, op: it.op, op_ime: it.op_ime, la: it.la, lo: it.lo };
          localStorage.setItem(KEY, JSON.stringify(sel));
          query = '';
          if (it.op_ime && typeof KRAJ_KEY === 'string') {
            localStorage.setItem(KRAJ_KEY, it.op_ime);
            const se = document.getElementById('kraj-opstina');
            if (se && se.value !== it.op_ime) { se.value = it.op_ime; se.dispatchEvent(new Event('change')); }
          }
          renderBlock(koren);
        });
        hits.appendChild(b);
      }
    };
    inp.addEventListener('input', () => { query = inp.value; fill(query); });
    if (query.length >= 2) fill(query);
    if (sel) renderCard(wrap, sel);

    const opName = typeof krajIzbor === 'function' ? krajIzbor() : '';
    const opIdx = opName && Array.isArray(data.opstine)
      ? data.opstine.findIndex(p => krajNorm(p[0]) === krajNorm(opName) || krajNorm(p[1]) === krajNorm(opName)) : -1;
    const scoped = (data.najave || []).filter(n => opIdx < 0 || n.op === opIdx);
    const active = scoped.filter(n => val(n).cls !== 'exp');
    const expired = scoped.filter(n => val(n).cls === 'exp');

    wrap.appendChild(el('h4', null, L().najNas + (opIdx >= 0 ? ' — ' + data.opstine[opIdx][0] : '') + ' (' + active.length + ')'));
    if (active.length) active.slice(0, 12).forEach(n => wrap.appendChild(renderNotice(n, null)));
    else wrap.appendChild(el('p', 'meta', L().nemaA));

    if (expired.length) {
      const tog = el('button', 'ul-btn', (showExp ? L().sExp : L().pExp) + ' (' + expired.length + ')');
      tog.type = 'button'; tog.setAttribute('aria-expanded', String(showExp));
      tog.addEventListener('click', () => { showExp = !showExp; renderBlock(koren); });
      wrap.appendChild(tog);
      if (showExp) expired.slice(0, 10).forEach(n => wrap.appendChild(renderNotice(n, null)));
    }
    if (typeof dlRow === 'function') wrap.appendChild(dlRow([['state/kraj.json', L().dl]]));
  }

  function ensure() {
    if (typeof currentRoute !== 'function' || currentRoute() !== 'kraj') return;
    const koren = document.getElementById('view');
    if (!koren) return;
    if (data) { renderBlock(koren); return; }
    if (loading) return;
    loading = true;
    jfetch('state/kraj.json').then(d => {
      data = d; loading = false;
      if (currentRoute() === 'kraj') renderBlock(document.getElementById('view'));
    }).catch(() => { loading = false; });
  }

  function sched() { if (!raf) raf = requestAnimationFrame(() => { raf = 0; ensure(); }); }
  window.addEventListener('hashchange', sched);
  document.addEventListener('DOMContentLoaded', () => {
    const v = document.getElementById('view');
    if (v) new MutationObserver(sched).observe(v, { childList: true });
    sched();
  });
})();
