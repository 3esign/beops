/* BEOPS v2 komentar.js — „Komentar grada" na vrhu #danas.
   Čita jedan mali ugovor (state/komentar.json, organ tools/hronika.py):
   najjači dostupni um pročita ceo dan grada (vazduh, vreme, reke, upozorenja,
   isključenja, servisne informacije Grada, vesti, istorija meseca) i napiše
   opažanja, veze i projekcije. Program proverava svaki broj prema paketu
   dokaza; projekcije se posle presuđuju merenjem i skor je javan.
   Bez innerHTML; rAF gard; idempotentno (obrazac veceras.js). */
'use strict';
(function () {
  let data = null, raf = 0, stil = false;

  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function jf(p) { return (typeof jfetch === 'function') ? jfetch(p) : fetch(p).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }); }
  function ruta() { const h = (location.hash || '').replace('#', ''); return h === '' || h === 'danas'; }

  function kad(iso) {
    const d = new Date(iso); if (isNaN(d)) return iso || '';
    return d.toLocaleString('sr-Latn-RS', { weekday: 'short', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  }
  function staro(iso) {
    const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (!isFinite(m)) return '';
    return m < 90 ? 'pre ' + m + ' min' : 'pre ' + Math.round(m / 60) + ' h';
  }

  function stilovi() {
    if (stil) return; stil = true;
    const s = el('style'); s.setAttribute('data-beops', 'komentar');
    s.textContent = [
      '.kg{max-width:760px;margin:0 auto 18px;padding:12px}',
      '.kg .kg-nad{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted,#68766e)}',
      '.kg h2{font-size:1.35rem;line-height:1.25;margin:4px 0 6px}',
      '.kg .kg-meta{font-size:.75rem;color:var(--muted,#68766e);margin-bottom:10px}',
      '.kg .kg-meta b{color:var(--ink,#1f2925);font-weight:600}',
      '.kg .kg-tekst{font-size:1rem;line-height:1.6;white-space:pre-line}',
      '.kg .kg-gr{margin:12px 0;padding:10px 12px;border-left:4px solid var(--accent,#13644d);background:var(--wash,#f6f8f7);font-size:.95rem}',
      '.kg h3{font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;margin:16px 0 6px;color:var(--muted,#68766e)}',
      '.kg ul{margin:0;padding-left:18px}.kg li{margin:4px 0;line-height:1.45;font-size:.92rem}',
      '.kg .kg-c{font-size:.7rem;color:var(--blue,#326d98);cursor:help;margin-left:4px;white-space:nowrap}',
      '.kg .kg-tag{display:inline-block;font-size:.66rem;border:1px solid var(--line,#d5ded9);border-radius:8px;padding:0 6px;margin-right:6px;color:var(--muted,#68766e)}',
      '.kg .kg-p{display:grid;grid-template-columns:52px 1fr;gap:8px;align-items:start;margin:6px 0}',
      '.kg .kg-pct{font-weight:700;font-variant-numeric:tabular-nums;font-size:1.05rem}',
      '.kg .kg-sm{font-size:.74rem;color:var(--muted,#68766e)}',
      '.kg .kg-dg{margin-top:12px;padding:10px 12px;border:1px dashed var(--line,#d5ded9);border-radius:8px;font-size:.88rem}',
      '.kg details{margin-top:12px;font-size:.85rem}.kg summary{cursor:pointer;color:var(--blue,#326d98)}',
      '.kg .ok{color:var(--green,#13644d)}.kg .ne{color:var(--red,#b74732)}',
      '.kg .kg-ai{font-size:.7rem;color:var(--muted,#68766e);margin-top:12px}'
    ].join('');
    document.head.appendChild(s);
  }

  function cites(li, ids, dokazi) {
    (ids || []).forEach(id => {
      const c = el('span', 'kg-c', id);
      if (dokazi && dokazi[id]) c.title = dokazi[id];
      li.appendChild(c);
    });
  }

  function lista(sec, naslov, items, dokazi, tagKey) {
    if (!items || !items.length) return;
    sec.appendChild(el('h3', null, naslov));
    const ul = el('ul');
    items.forEach(o => {
      const li = el('li');
      if (tagKey && o[tagKey]) li.appendChild(el('span', 'kg-tag', o[tagKey]));
      li.appendChild(document.createTextNode(typeof o === 'string' ? o : o.tekst));
      if (typeof o !== 'string') cites(li, o.cites, dokazi);
      ul.appendChild(li);
    });
    sec.appendChild(ul);
  }

  function projekcije(sec, ps, dokazi) {
    if (!ps || !ps.length) return;
    sec.appendChild(el('h3', null, 'Projekcije — proveriće ih merenje'));
    ps.forEach(p => {
      const row = el('div', 'kg-p');
      row.appendChild(el('div', 'kg-pct', Math.round(100 * p.verovatnoca) + '%'));
      const t = el('div');
      t.appendChild(document.createTextNode(p.tekst));
      cites(t, p.cites, dokazi);
      t.appendChild(el('div', 'kg-sm', 'rok ' + kad(p.rok_utc) + ' · ' + p.metrika + ' · ' + p.mesto));
      row.appendChild(t);
      sec.appendChild(row);
    });
  }

  function skor(sec, pr) {
    if (!pr) return;
    const s = pr.skor || {};
    sec.appendChild(el('h3', null, 'Kako su umovi do sada pogađali'));
    if (!s.n) {
      sec.appendChild(el('p', 'kg-sm', 'Još nijedna projekcija nije presuđena — prve presude stižu kad im istekne rok. Otvoreno: ' + ((pr.otvorene || []).length) + '.'));
      return;
    }
    sec.appendChild(el('p', 'kg-sm', s.n + ' presuđeno, ' + s.tacno + ' tačno · Brier ' + s.brier + ' (0 je savršeno, 0,25 je bacanje novčića) · otvoreno ' + ((pr.otvorene || []).length)));
    const ul = el('ul');
    (pr.presudjene || []).slice(0, 6).forEach(p => {
      const li = el('li');
      li.appendChild(el('span', p.presuda === 'tačno' ? 'kg-tag ok' : (p.presuda === 'netačno' ? 'kg-tag ne' : 'kg-tag'), p.presuda));
      li.appendChild(document.createTextNode(p.tekst + ' — izmereno ' + p.izmereno + ' (' + Math.round(100 * p.verovatnoca) + '%, ' + (p.model || '') + ')'));
      ul.appendChild(li);
    });
    sec.appendChild(ul);
  }

  function napravi(view) {
    if (!data || !data.poslednji || view.querySelector('section.kg')) return;
    const k = data.poslednji;
    const sec = el('section', 'kg');
    sec.setAttribute('aria-label', 'Komentar grada');
    sec.appendChild(el('div', 'kg-nad', 'Komentar grada · Beops um'));
    sec.appendChild(el('h2', null, k.naslov));
    const meta = el('div', 'kg-meta');
    meta.appendChild(document.createTextNode(kad(k.at) + ' (' + staro(k.at) + ') · napisao '));
    meta.appendChild(el('b', null, k.model || 'um'));
    meta.appendChild(document.createTextNode(' · ' + (k.dokaza || 0) + ' dokaza iz paketa · svaki broj proveren programom'));
    sec.appendChild(meta);
    sec.appendChild(el('div', 'kg-tekst', k.komentar));
    if (k.za_gradjanina) sec.appendChild(el('div', 'kg-gr', k.za_gradjanina));
    lista(sec, 'Opažanja', k.opazanja, k.dokazi);
    lista(sec, 'Veze', k.veze, k.dokazi, 'vrsta');
    projekcije(sec, k.projekcije, k.dokazi);
    lista(sec, 'Šta ne znamo', k.ne_znamo);
    const dg = k.druga_glava;
    if (dg && dg.state === 'accepted' && dg.tekst) {
      const b = el('div', 'kg-dg');
      b.appendChild(el('div', 'kg-sm', 'Druga glava (' + dg.model + ') sumnja:'));
      b.appendChild(el('div', null, dg.tekst));
      sec.appendChild(b);
    }
    skor(sec, data.projekcije);
    if (data.znanje && data.znanje.length) {
      const d = el('details');
      d.appendChild(el('summary', null, 'Šta Beops uči o Beogradu (' + data.znanje.length + ' kandidata za pravilnost)'));
      const ul = el('ul');
      data.znanje.slice(0, 10).forEach(z => ul.appendChild(el('li', null, z.tekst + ' — ' + z.status + ', predloženo ' + z.puta + '×')));
      d.appendChild(ul); sec.appendChild(d);
    }
    if (k.dokazi) {
      const d = el('details');
      d.appendChild(el('summary', null, 'Paket dokaza koji je um čitao (' + Object.keys(k.dokazi).length + ')'));
      const ul = el('ul');
      Object.keys(k.dokazi).forEach(id => ul.appendChild(el('li', null, id + ' · ' + k.dokazi[id])));
      d.appendChild(ul); sec.appendChild(d);
    }
    if (data.istorija && data.istorija.length > 1) {
      const d = el('details');
      d.appendChild(el('summary', null, 'Raniji komentari'));
      const ul = el('ul');
      data.istorija.slice(1).forEach(h => ul.appendChild(el('li', null, kad(h.at) + ' — ' + h.naslov + ' (' + h.model + ')')));
      d.appendChild(ul); sec.appendChild(d);
    }
    const odb = (data.odbijeno_24h || []).length;
    sec.appendChild(el('p', 'kg-ai', 'Tekst je generisala veštačka inteligencija (AI Act čl. 50). Merenja ispod su dokaz, komentar je tumačenje.' +
      (odb ? ' Kapija je u poslednja 24 h odbila ' + odb + ' komentar(a) sa brojem ili uzrokom bez dokaza.' : '')));
    view.insertBefore(sec, view.firstChild);
  }

  function zakazi(view) {
    if (raf || !ruta()) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      if (!ruta()) return;
      stilovi();
      if (data) { napravi(view); return; }
      jf('state/komentar.json').then(d => { data = d; napravi(view); }, () => { });
    });
  }

  function start() {
    const view = document.getElementById('view');
    if (!view) return;
    new MutationObserver(() => zakazi(view)).observe(view, { childList: true });
    zakazi(view);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
