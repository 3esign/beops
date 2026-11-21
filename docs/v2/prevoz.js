/* BEOPS v2 prevoz.js — čitalac deklarisanih GTFS linija uz merna mesta (S13).
   Jedna rečenica: Koje linije javnog prevoza opslužuju najbliže stajalište uz
   referentnu mernu stanicu i kolika je deklarisana mreža Beograda — bez lažnih
   polazaka u realnom vremenu.
   Zaseban lenji modul (obrazac: reke.js, veceras.js) van budžeta app.js/beops.css.
   Bez innerHTML; rAF gard; svetla i tamna tema preko CSS promenljivih; sr/en. */
'use strict';
/* global el, mkTable, jfetch, dlRow, fmtNum, currentRoute, krajIzbor, krajNorm, krajNajblizaRef, KRAJ_OPSTINE, LANG */
(function () {
  let mreza = null;
  let mesta = null;
  let loading = false;
  let raf = 0;
  let stil = false;
  let filterTxt = '';

  const TXT = {
    sr: {
      krajNaslov: 'Javni prevoz kod ove stanice (GTFS)',
      stajaliste: 'Najbliže stajalište',
      uRadijusu: 'unutar šetnog radijusa',
      vanRadijusa: 'van radijusa',
      linije: 'Linije',
      nemaSpoja: 'Za ovu mernu stanicu nema zabeleženog GTFS spoja.',
      podaciNaslov: 'Javni prevoz uz merna mesta (GTFS)',
      podaciSub: 'Deklarisana mreža (S13, data.gov.rs) spojena sa referentnim stanicama (S146). Bez polazaka u realnom vremenu.',
      pretragaPh: 'Filtriraj po stanici, stajalištu ili broju linije (npr. 26, Zemun)…',
      pretragaLbl: 'Filter GTFS stanica i linija',
      colStanica: 'Merno mesto',
      colStajaliste: 'Najbliže stajalište',
      colRazd: 'Udaljenost',
      colLinije: 'Linije',
      mrezaSazetak: '{ukupno} linija ({bus} autobus, {tram} tramvaj, {trol} trolejbus) · {stanica} stajališta u prozoru · GTFS izdanje v{ver}',
      prikazano: 'Prikazano {n} od {tot} stanica u radijusu {r} m.',
      nemaPogodaka: 'Nema stanica koje odgovaraju filteru.',
      napomena: 'Deklarisani spoj po koordinatama izdavača (Grad Beograd / GSP Beograd, data.gov.rs), ne merenje polazaka u realnom vremenu.',
      dlMesta: 'prevoz uz mesta (.json)',
      dlMreza: 'mreža prevoza (.json)',
    },
    en: {
      krajNaslov: 'Public transit near this station (GTFS)',
      stajaliste: 'Nearest stop',
      uRadijusu: 'within walking radius',
      vanRadijusa: 'outside radius',
      linije: 'Routes',
      nemaSpoja: 'No recorded GTFS match for this monitoring station.',
      podaciNaslov: 'Public transit near monitoring stations (GTFS)',
      podaciSub: 'Declared network (S13, data.gov.rs) matched to reference stations (S146). No real-time departures.',
      pretragaPh: 'Filter by station, stop or route number (e.g. 26, Zemun)…',
      pretragaLbl: 'Filter GTFS stations and routes',
      colStanica: 'Station',
      colStajaliste: 'Nearest stop',
      colRazd: 'Distance',
      colLinije: 'Routes',
      mrezaSazetak: '{ukupno} routes ({bus} bus, {tram} tram, {trol} trolleybus) · {stanica} stops in window · GTFS feed v{ver}',
      prikazano: 'Showing {n} of {tot} stations within {r} m radius.',
      nemaPogodaka: 'No stations match the filter.',
      napomena: 'Declared match from publisher coordinates (City of Belgrade / GSP Beograd, data.gov.rs), not real-time departures.',
      dlMesta: 'transit by station (.json)',
      dlMreza: 'transit network (.json)',
    },
  };
  function L() { return TXT[typeof LANG === 'string' && LANG === 'en' ? 'en' : 'sr']; }

  function normIme(s) {
    return String(s || '')
      .toLowerCase()
      .replace(/[čć]/g, 'c').replace(/š/g, 's').replace(/ž/g, 'z').replace(/đ/g, 'dj')
      .replace(/^beograd\s+/, '')
      .replace(/[^a-z0-9]+/g, ' ')
      .trim();
  }

  function stilovi() {
    if (stil) return;
    stil = true;
    const s = document.createElement('style');
    s.setAttribute('data-beops', 'prevoz');
    s.textContent = [
      '#prevoz-block{margin:24px 0 18px;padding-top:14px;border-top:1px solid var(--line,#e2e6e4)}',
      '.prv-kraj{margin:14px 0;padding:12px 14px;border:1px solid var(--line,#e2e6e4);border-radius:10px;background:var(--paper,#fff)}',
      '.prv-kraj h3{margin:0 0 6px;font-size:1rem}',
      '.prv-pills{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}',
      '.prv-pill{display:inline-block;padding:2px 8px;border:1px solid var(--line,#e2e6e4);border-radius:999px;font-size:.78rem;font-weight:600;font-variant-numeric:tabular-nums;background:var(--bg,#f6f7f6)}',
      '.prv-summary{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0 10px;font-size:.86rem;color:var(--ink-2,#444)}',
      '.prv-filter{width:100%;max-width:420px;padding:7px 10px;border:1px solid var(--line,#e2e6e4);border-radius:8px;background:var(--paper,#fff);color:inherit;font:inherit;margin:6px 0 10px}',
      '.prv-filter:focus-visible{outline:2px solid var(--blue,#1d6fa5);outline-offset:1px}',
    ].join('\n');
    document.head.appendChild(s);
  }

  function loadAll() {
    if ((mreza && mesta) || loading || typeof jfetch !== 'function') return;
    loading = true;
    Promise.all([
      jfetch('state/kontekst-prevoz.json').catch(() => null),
      jfetch('state/kontekst-prevoz-mesta.json').catch(() => null),
    ]).then(([a, b]) => {
      mreza = a || {};
      mesta = b || { mesta: [] };
      loading = false;
      zakazi();
    });
  }

  function mrezaLine() {
    const m = mreza && mreza.mreza;
    if (!m) return '';
    const t = m.linije_po_tipu || {};
    return L().mrezaSazetak
      .replace('{ukupno}', fmtNum(m.linije_ukupno || 0, 0))
      .replace('{bus}', fmtNum(t.autobus || 0, 0))
      .replace('{tram}', fmtNum(t.tramvaj || 0, 0))
      .replace('{trol}', fmtNum(t.trolejbus || 0, 0))
      .replace('{stanica}', fmtNum(m.stanice_u_prozoru || m.stanice_ukupno || 0, 0))
      .replace('{ver}', mreza.feed_version || '—');
  }

  function nadjiSpoj(stanicaIme) {
    const list = (mesta && Array.isArray(mesta.mesta)) ? mesta.mesta : [];
    const target = normIme(stanicaIme);
    if (!target) return null;
    let hit = list.find(x => normIme(x.stanica) === target);
    if (!hit) hit = list.find(x => normIme(x.stanica).includes(target) || target.includes(normIme(x.stanica)));
    return hit || null;
  }

  function renderKraj() {
    const refBox = document.querySelector('#view .kraj-ref');
    if (!refBox || document.getElementById('prevoz-kraj')) return;
    if (typeof krajIzbor !== 'function' || typeof krajNajblizaRef !== 'function' || !Array.isArray(KRAJ_OPSTINE)) return;
    const izbor = krajIzbor();
    const opEntry = KRAJ_OPSTINE.find(x => krajNorm(x[0]) === krajNorm(izbor) || krajNorm(x[1]) === krajNorm(izbor));
    const found = krajNajblizaRef(opEntry);
    if (!found || !found.st) return;

    const box = el('div', 'prv-kraj');
    box.id = 'prevoz-kraj';
    box.appendChild(el('h3', null, L().krajNaslov));

    const hit = nadjiSpoj(found.st.n);
    const rad = (mesta && mesta.radius_m) || 250;
    if (hit) {
      const statusTxt = hit.u_radijusu ? `${L().uRadijusu} (${rad} m)` : `${L().vanRadijusa} (${rad} m)`;
      box.appendChild(el('p', 'meta', `${L().stajaliste}: ${hit.stajaliste} (${fmtNum(hit.razdaljina_m, 0)} m · ${statusTxt})`));
      const pills = el('div', 'prv-pills');
      for (const ln of (hit.linije || [])) pills.appendChild(el('span', 'prv-pill', String(ln)));
      if (pills.childNodes.length) box.appendChild(pills);
    } else {
      box.appendChild(el('p', 'sub', L().nemaSpoja));
    }
    const ms = mrezaLine();
    if (ms) box.appendChild(el('p', 'meta', ms));
    box.appendChild(el('p', 'hint', L().napomena));
    refBox.after(box);
  }

  function renderPodaci(root) {
    const old = document.getElementById('prevoz-block');
    if (old) old.remove();
    const anchor = document.getElementById('proslost-block') || document.getElementById('reke-block') || document.getElementById('chart-box');
    if (!anchor || !root.contains(anchor)) return;

    const list = (mesta && Array.isArray(mesta.mesta)) ? mesta.mesta.filter(x => x.u_radijusu) : [];
    const rad = (mesta && mesta.radius_m) || 250;

    const block = el('section');
    block.id = 'prevoz-block';
    block.appendChild(el('h2', null, L().podaciNaslov));
    block.appendChild(el('p', 'sub', L().podaciSub));

    const ms = mrezaLine();
    if (ms) block.appendChild(el('div', 'prv-summary', ms));

    const inp = document.createElement('input');
    inp.type = 'search';
    inp.className = 'prv-filter';
    inp.placeholder = L().pretragaPh;
    inp.setAttribute('aria-label', L().pretragaLbl);
    inp.value = filterTxt;

    const countP = el('p', 'meta');
    const tblWrap = el('div');

    function drawTable() {
      tblWrap.textContent = '';
      const q = normIme(filterTxt);
      const rowsData = list.filter(x => {
        if (!q) return true;
        const hay = normIme(x.stanica + ' ' + x.stajaliste + ' ' + (x.linije || []).join(' '));
        return hay.includes(q);
      });
      countP.textContent = L().prikazano
        .replace('{n}', fmtNum(rowsData.length, 0))
        .replace('{tot}', fmtNum(list.length, 0))
        .replace('{r}', fmtNum(rad, 0));
      if (!rowsData.length) {
        tblWrap.appendChild(el('p', 'sub', L().nemaPogodaka));
        return;
      }
      const rows = rowsData.map(x => {
        const pills = el('div', 'prv-pills');
        for (const ln of (x.linije || [])) pills.appendChild(el('span', 'prv-pill', String(ln)));
        return [
          x.stanica,
          x.stajaliste,
          fmtNum(x.razdaljina_m, 0) + ' m',
          pills,
        ];
      });
      tblWrap.appendChild(mkTable([L().colStanica, L().colStajaliste, L().colRazd, L().colLinije], rows));
    }

    inp.addEventListener('input', () => { filterTxt = inp.value; drawTable(); });
    block.appendChild(inp);
    block.appendChild(countP);
    drawTable();
    block.appendChild(tblWrap);
    block.appendChild(el('p', 'sub', L().napomena));
    block.appendChild(dlRow([
      ['state/kontekst-prevoz-mesta.json', L().dlMesta],
      ['state/kontekst-prevoz.json', L().dlMreza],
    ]));
    anchor.after(block);
  }

  function napravi() {
    if (typeof currentRoute !== 'function') return;
    const r = currentRoute();
    const view = document.getElementById('view');
    if (!view) return;
    if (r === 'kraj') renderKraj();
    else if (r === 'podaci' && !document.getElementById('prevoz-block')) renderPodaci(view);
  }

  function zakazi() {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      stilovi();
      if (typeof currentRoute !== 'function') return;
      const r = currentRoute();
      if (r !== 'kraj' && r !== 'podaci') return;
      if (!mreza || !mesta) { loadAll(); return; }
      napravi();
    });
  }

  function start() {
    const view = document.getElementById('view');
    if (!view) return;
    const mu = new MutationObserver(() => zakazi());
    mu.observe(view, { childList: true, subtree: true });
    zakazi();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();

  window.BEOPS_PREVOZ = { osvezi: () => { mreza = null; mesta = null; zakazi(); } };
})();
