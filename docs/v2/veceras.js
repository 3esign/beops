/* BEOPS v2 veceras.js — „Večeras u Beogradu" na #danas (lenji modul).
   Čita isti mali JSON ugovor kao shell (state/dogadjaji.json) i izdvaja
   današnje eksplicitne termine iz zvaničnih repertoara + periode u toku,
   odmah ispod hero ploče — građanin prvo vidi šta grad nudi večeras.
   Datum je LOKALNI datum čitača — isto pravilo iskrenosti kao ostatak
   sajta („svežina se meri tvojim satom"). Bez innerHTML; rAF gard umesto
   mikrozadatak-petlje (pouka iz glas.js). Stilovi su tu jer su app.js i
   beops.css puni do ugovornog plafona. */
'use strict';
(function () {
  let data = null;   // keš state/dogadjaji.json
  let raf = 0;       // rAF gard protiv observer petlje
  let stil = false;  // <style> jednom
  let mu = null;

  function lokalniDatum() {
    const d = new Date();
    return d.getFullYear() + '-' +
      String(d.getMonth() + 1).padStart(2, '0') + '-' +
      String(d.getDate()).padStart(2, '0');
  }

  function stilovi() {
    if (stil) return;
    stil = true;
    const s = document.createElement('style');
    s.setAttribute('data-beops', 'veceras');
    s.textContent = [
      '.veceras{margin:8px 0 20px}',
      '.veceras .ist-red{border-left:3px solid var(--line,#e8e8e8)}',
      '.veceras .tag.vc-vreme{font-variant-numeric:tabular-nums}',
      '.veceras .tag.vc-tok{font-variant-numeric:tabular-nums}',
      '.veceras .meta{margin:4px 0 0}',
      '.veceras .napomena{color:var(--muted,#777);font-size:.82em;margin:6px 0 0}'
    ].join('\n');
    document.head.appendChild(s);
  }

  function kartica(e, oznaka) {
    const row = el('article', 'ist-red');
    const mid = el('div', 'ist-mid');
    row.appendChild(el('span', 'tag outline ' + oznaka.klasa, oznaka.tekst));
    const a = el('a', 'naslov', e.n);
    a.href = e.u || '#';
    a.rel = 'noopener';
    mid.appendChild(a);
    mid.appendChild(el('p', 'meta', [e.m, e.h].filter(Boolean).join(' · ')));
    row.appendChild(mid);
    return row;
  }

  function prazna(sl) {
    const row = el('article', 'ist-red');
    row.appendChild(el('span', 'tag outline vc-vreme', T().vecerasPraznoTag));
    const mid = el('div', 'ist-mid');
    mid.appendChild(el('p', 'meta', T().vecerasPrazno));
    if (sl) {
      const tl = String(sl.tl || sl.t || '');
      const a = el('a', 'naslov', T().vecerasSledeci + tl.slice(8, 10) + '.' + tl.slice(5, 7) + '. ' + tl.slice(11, 16) + ' · ' + sl.n);
      a.href = sl.u || '#';
      a.rel = 'noopener';
      mid.appendChild(a);
      mid.appendChild(el('p', 'meta', sl.m || ''));
    }
    row.appendChild(mid);
    return row;
  }

  function napravi() {
    if (!data || typeof el !== 'function' || typeof T !== 'function') return false;
    const view = document.getElementById('view');
    const hero = view && view.querySelector('section.puls-sekcija');
    if (!view || !hero) return false;
    if (view.querySelector('section.veceras')) return true; // idempotentno

    const dan = lokalniDatum();
    const evts = data.events || [];
    const veceras = evts.filter(e => String(e.tl || e.t || '').slice(0, 10) === dan);
    const tokovi = (data.runs || []).slice(0, 3);
    const sledeci = evts.filter(e => String(e.tl || e.t || '').slice(0, 10) > dan)
      .sort((a, b) => String(a.tl || a.t).localeCompare(String(b.tl || b.t)))[0] || null;
    if (!veceras.length && !tokovi.length && !sledeci) return true; // ugovor bez termina — tišina je iskren odgovor

    const sec = el('section', 'veceras');
    sec.appendChild(el('h2', null, T().vecerasTitle));
    sec.appendChild(el('hr', 'rule'));
    const list = el('div', 'istaknuto ist-grid');
    if (!veceras.length) list.appendChild(prazna(sledeci));
    for (const e of veceras.slice(0, 6)) {
      list.appendChild(kartica(e, { klasa: 'vc-vreme', tekst: (e.tl || e.t).slice(11, 16) }));
    }
    for (const e of tokovi) {
      list.appendChild(kartica(e, { klasa: 'vc-tok', tekst: T().vecerasUtoku }));
    }
    sec.appendChild(list);
    sec.appendChild(el('p', 'napomena', T().vecerasNapomena));
    hero.after(sec);
    return true;
  }

  function zakazi(view) {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      stilovi();
      if (!data && typeof jfetch === 'function') {
        jfetch('state/dogadjaji.json').then(m => { data = m; napravi(); }, () => { data = { events: [], runs: [] }; });
        return;
      }
      napravi();
    });
  }

  function start() {
    const view = document.getElementById('view');
    if (!view) return;
    mu = new MutationObserver(() => zakazi(view));
    mu.observe(view, { childList: true });
    zakazi(view);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();

  window.BEOPS_VECERAS = { osvezi: () => { data = null; const v = document.getElementById('view'); if (v) zakazi(v); } };
})();
