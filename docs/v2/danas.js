/* BEOPS v2 danas.js — istorijski sloj fotografija grada na #danas (lenji modul).
   Čita isključivo mali JSON ugovor ./state/foto.json (generiše tools/v2/foto_grad.py
   nad Wikimedia Commons, uz autora i licencu po stavci). Bez innerHTML; slike su
   lazy. Sama ubacuje traku posle vodiča kad renderDanas obnovi #danas (rAF gard,
   nikad mikrozadatak-petlja — pouka od glas.js). Sadržinski nizovi su tu dok
   ne budu premešteni u strings.js (dug: 1. potez). */
'use strict';
(function () {
  const ID = 'foto-traka';
  let slike = null;      // keš state/foto.json
  let raf = 0;           // rAF gard protiv observer petlje
  let stil = false;      // <style> jednom
  let mu = null;

  function T2(k, sr, en) { return (typeof LANG === 'string' && LANG === 'en') ? en : sr; }

  function stilovi() {
    if (stil) return;
    stil = true;
    const s = document.createElement('style');
    s.setAttribute('data-beops', 'danas-foto');
    s.textContent = [
      '.foto-traka{margin:26px 0 8px}',
      '.foto-traka h2{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 10px;font-weight:600}',
      '.foto-red{display:flex;gap:14px;overflow-x:auto;scroll-snap-type:x proximity;padding:2px 2px 14px}',
      '.foto-red::-webkit-scrollbar{height:8px}.foto-red::-webkit-scrollbar-thumb{background:var(--grid);border-radius:4px}',
      '.foto-k{flex:0 0 260px;scroll-snap-align:start;margin:0;background:var(--card, #fff);border:1px solid var(--grid);border-radius:12px;overflow:hidden;box-shadow:0 1px 2px rgba(16,24,40,.06)}',
      '.foto-k img{display:block;width:100%;height:170px;object-fit:cover;background:var(--grid)}',
      '.foto-k figcaption{padding:9px 12px 11px;font-size:12.5px;line-height:1.45;color:var(--ink,#111)}',
      '.foto-k .f-naslov{font-weight:600;margin:0 0 2px}',
      '.foto-k .f-opis{color:var(--muted);margin:0 0 5px}',
      '.foto-k .f-credit{font-size:11px;color:var(--muted)}',
      '.foto-k .f-credit a{color:inherit}',
      '@media (prefers-reduced-motion: no-preference){.foto-k{transition:box-shadow .15s ease}.foto-k:hover{box-shadow:0 6px 18px rgba(16,24,40,.12)}}',
      '@media (max-width:680px){.foto-k{flex-basis:210px}.foto-k img{height:140px}}'
    ].join('\n');
    document.head.appendChild(s);
  }

  function kartica(it) {
    const fig = el('figure', 'foto-k');
    const img = document.createElement('img');
    img.loading = 'lazy'; img.decoding = 'async';
    img.width = it.w || 960; img.height = it.h || 640;
    img.alt = (it.opis || it.naslov) + ' — Wikimedia Commons';
    img.src = it.img;
    fig.appendChild(img);
    const cap = el('figcaption');
    cap.appendChild(el('p', 'f-naslov', String(it.naslov || '').replace(/\.[a-z]+$/i, '')));
    cap.appendChild(el('p', 'f-opis', it.opis || ''));
    const cr = el('p', 'f-credit');
    cr.appendChild(document.createTextNode(it.autor || 'Wikimedia Commons'));
    cr.appendChild(document.createTextNode(' · '));
    const a = document.createElement('a');
    a.href = it.stranica || '#'; a.target = '_blank'; a.rel = 'noopener';
    a.textContent = it.licenca || 'Wikimedia Commons';
    cr.appendChild(a);
    cap.appendChild(cr);
    fig.appendChild(cap);
    return fig;
  }

  function traka() {
    if (!slike || !slike.length) return null;
    const sec = el('section');
    sec.id = ID;
    sec.className = 'foto-traka';
    sec.appendChild(el('h2', null, T2('x', 'Grad u fotografijama', 'The city in photographs')));
    const red = el('div', 'foto-red');
    for (const it of slike) red.appendChild(kartica(it));
    sec.appendChild(red);
    const nap = el('p', 'f-credit', T2('x',
      'Fotografije: Wikimedia Commons, autori i licence uz svaku sliku.',
      'Photos: Wikimedia Commons, author and licence on each image.'));
    sec.appendChild(nap);
    return sec;
  }

  function primeni(root) {
    if (location.hash && location.hash !== '#danas') return;
    if (!root || !root.isConnected) return;
    if (root.querySelector('#' + ID)) return;      // već stoji — kraj lanca
    const sec = traka();
    if (!sec) return;
    const misli = root.querySelector('.danas-misli-grid');
    if (misli && misli.parentNode === root) root.insertBefore(sec, misli);
    else root.appendChild(sec);
  }

  function zakazi(root) {
    if (raf) return;
    raf = requestAnimationFrame(() => { raf = 0; primeni(root); });
  }

  function start() {
    const v = document.getElementById('view');
    if (!v) return;
    stilovi();
    jfetch('state/foto.json').then(d => {
      slike = (d && Array.isArray(d.items)) ? d.items : [];
      zakazi(v);
    }, () => { slike = []; });
    mu = new MutationObserver(() => zakazi(v));
    mu.observe(v, { childList: true });
    zakazi(v);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();

  window.BEOPS_DANAS = { osvezi: () => { slike = null; const v = document.getElementById('view'); if (v) zakazi(v); } };
})();
