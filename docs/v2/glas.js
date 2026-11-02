/* T5 — Belažnica: glas građana bez naloga (K7). Tri istine o transportu, sve javne:
   1) prijemnik (self-hosted mali server, ENV BEOPS_GLAS_URL) — živi glas u glasovi.jsonl;
   2) localStorage — glas se čuva kod građanina i vide se brojači, bez servera;
   3) mailto: — predmet i telo su oblikovan glas, čovek ga pošalje sam. Nijedan put
   ne traži ime, mejl ni kolačiće; anonim_id je slučajan i živi samo u ovom brauzeru.
   Težina glasa (brze serije se odbijaju) je javna kapija na prijemniku (ocene.js). */
(() => {
  'use strict';
  const URL_PRIJEMNIKA = (window.BEOPS_GLAS_URL || '').replace(/\/$/, '');
  const KLJUC_ANON = 'beops.anonim', KLJUC_GLASOVA = 'beops.glasovi.v1';
  let anonim = null;
  try {
    anonim = localStorage.getItem(KLJUC_ANON);
    if (!anonim) {
      anonim = 'a-' + Math.random().toString(36).slice(2, 10) + Math.random().toString(36).slice(2, 6);
      localStorage.setItem(KLJUC_ANON, anonim);
    }
  } catch { anonim = 'a-anonimni-brauzer'; }
  const mojiGlasovi = () => { try { return JSON.parse(localStorage.getItem(KLJUC_GLASOVA) || '{}'); } catch { return {}; } };
  const zapamti = m => { try { localStorage.setItem(KLJUC_GLASOVA, JSON.stringify(m)); } catch {} };
  const sk = () => (document.documentElement.lang || 'sr').startsWith('en') ? 'en' : 'sr';
  const POR = {
    sr: { pitanje: 'Da li ti je ovo pomoglo?', korisno: 'Korisno', nekorisno: 'Nekorisno', hvala: 'Hvala — glas je zabeležen.', hvalaL: 'Hvala — zabeleženo kod tebe;', posalji: 'pošalji glas mejlom', poslato: 'već si glasao', min: 'najmanje 8 znakova', M: 'Glas' },
    en: { pitanje: 'Did this help you?', korisno: 'Helpful', nekorisno: 'Not helpful', hvala: 'Thanks — your vote is recorded.', hvalaL: 'Thanks — recorded on your device;', posalji: 'send the vote by mail', poslato: 'already voted', min: 'at least 8 characters', M: 'Vote' }
  };
  const el = (t, c, x) => { const n = document.createElement(t); if (c) n.className = c; if (x !== undefined) n.textContent = x; return n; };

  function oblikujMejl(glas) {
    const t = encodeURIComponent('Glas / Vote: ' + glas.misao);
    const b = encodeURIComponent(JSON.stringify({ misao: glas.misao, odluka: glas.odluka, anonim: glas.anonim, ts: glas.ts, schema: 'glas/v1' }, null, 1));
    return 'mailto:beops.povratne@gmail.com?subject=' + t + '&body=' + b;
  }
  async function posaljiNaPrijemnik(glas) {
    if (!URL_PRIJEMNIKA) return false;
    try {
      const r = await fetch(URL_PRIJEMNIKA + '/glas', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(glas) });
      return r.ok || r.status === 400; // 400 = loš glas, ne mreža; ne lažemo uspeh
    } catch { return false; }
  }
  async function glasanje(misao, odluka, red, poruka, dK, dN) {
    const glas = { misao, odluka, anonim, ts: new Date().toISOString(), schema: 'glas/v1' };
    if (anonim.length < 8) { poruka.textContent = POR[sk()].min; return; }
    for (const d of [dK, dN]) d.disabled = true;
    const stigao = await posaljiNaPrijemnik(glas);
    const g = mojiGlasovi(); g[misao] = { ...glas, ...(stigao ? { transport: 'prijemnik' } : {}) }; zapamti(g);
    poruka.textContent = stigao ? POR[sk()].hvala : POR[sk()].hvalaL;
    if (!stigao) { // treći transport: oblikovan glas ide mejlom, čovek ga šalje sam
      const a = el('a', 'glas-mailto', POR[sk()].posalji);
      a.href = oblikujMejl(glas);
      poruka.appendChild(document.createTextNode(' '));
      poruka.appendChild(a);
    }
    red.classList.add('glasano');
  }
  function redGlasa(art, id) {
    const g = mojiGlasovi();
    if (!id || g[id] || art.querySelector('.glas-red')) return; // jedan glas po misli u ovom brauzeru — bez ponavljanja
    const P = POR[sk()], red = el('div', 'glas-red');
    const p = el('span', 'glas-pitanje', P.pitanje);
    const poruka = el('span', 'glas-poruka');
    const mk = o => {
      const d = el('button', 'glas-dugme', P[o]);
      d.type = 'button';
      d.addEventListener('click', () => glasanje(id, o, red, poruka, dK, dN));
      return d;
    };
    const dK = mk('korisno'), dN = mk('nekorisno');
    red.append(p, dK, dN, poruka);
    art.appendChild(red);
  }
  function oboji() { // glasano: dugm nestaju, ostaje znak bez ponavljanja
    const g = mojiGlasovi();
    for (const art of document.querySelectorAll('article[data-misao]')) {
      const id = art.getAttribute('data-misao');
      if (!id || art.querySelector('.glas-red')) continue;
      if (!g[id]) { redGlasa(art, id); continue; }
      const red = el('div', 'glas-red glasano'), P = POR[sk()];
      red.append(el('span', 'glas-pitanje', P.M + ' · ' + (g[id].odluka === 'korisno' ? P.korisno : P.nekorisno)), el('span', 'glas-poruka', P.poslato));
      art.appendChild(red);
    }
  }
  new MutationObserver(oboji).observe(document.body, { childList: true, subtree: true });
  document.addEventListener('beops:misli', oboji);
  window.BEOPS_GLAS = { oboji };
})();
