/* BEOPS v2 · Metodološki list (B6) — poseban lenji modul van 64 KB budžeta shella.
   Registruje se u #o: renderMeto(body) crta tabelu izvora iz
   state/metodologija.json (COLLECTORS.json ⊗ LEDGER.jsonl). Naučni sloj #o:
   izvor, saglasnost (+ dokaz putanja), kada (cadence), izdavačev sat (offset),
   vremenska etiketa. Bez saglasnosti se pokazuje kao stanje, ne skriva. */
'use strict';
/* global el, STATE, T, absTime */

function metoSaglasnostCap(i) {
  const s = i.saglasnost || {};
  if (!s.uzeto) return T().metoBezSaglasnosti;
  if (!s.dozvoljeno) return T().metoSaglasnostNe;
  return T().metoSaglasnostDa + ' · ' + i.sid + '@' + s.uzeto.replace(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2}).*$/, '$1-$2-$3 $4:$5Z');
}
function metoSat(i) {
  if (!i.sat) return '\u2014';
  const off = i.sat.offset_s | 0;
  const sign = off < 0 ? '\u2212' : '+';
  const a = Math.abs(off);
  return sign + Math.floor(a / 3600) + 'h' + (a % 3600 ? (a % 3600) / 60 + 'm' : '') + ' (' + i.sat.id + ')';
}
function metoCadence(s) {
  const sec = s.kada_s | 0;
  return sec % 86400 === 0 ? (sec / 86400) + ' d' : sec % 3600 === 0 ? (sec / 3600) + ' h' : sec % 60 === 0 ? (sec / 60) + ' min' : sec + ' s';
}
function viewMeto(body) {
  body.appendChild(el('h2', null, T().metoTitle));
  const d = STATE.meto || STATE.metodologija;
  if (!d || !Array.isArray(d.izvori) || !d.izvori.length) {
    body.appendChild(el('p', 'sub', T().tangierUcitavanje));
    return;
  }
  body.appendChild(el('p', 'sub', T().metoSub + ' (' + d.akt + '/' + d.uk + ' · ' + T().verzija + ': ' + absTime(d.generated_at) + ')'));
  const tbl = el('table', 'kv');
  const th = el('thead'); const trh = el('tr');
  for (const h of [T().metoIzvor, T().metoSaglasnost, T().metoKada, T().metoSat, T().metoVreme]) trh.appendChild(el('th', null, h));
  th.appendChild(trh); tbl.appendChild(th);
  const tb = el('tbody');
  for (const i of d.izvori) {
    const tr = el('tr');
    const tdIz = el('td');
    tdIz.textContent = i.ime + ' ';
    tdIz.appendChild(el('span', 'meta', i.sid + (i.aktivan ? '' : ' · ' + T().metoIskljucen)));
    tr.appendChild(tdIz);
    const s = i.saglasnost || {};
    const capTd = el('td');
    const capSpan = el('span', null, metoSaglasnostCap(i));
    if (s.dokaz) capSpan.title = T().metoDokaz + ': ' + s.dokaz;
    capTd.appendChild(capSpan);
    tr.appendChild(capTd);
    tr.appendChild(el('td', null, metoCadence(i)));
    tr.appendChild(el('td', null, metoSat(i)));
    tr.appendChild(el('td', null, i.vreme ? i.vreme : '\u2014'));
    tb.appendChild(tr);
  }
  tbl.appendChild(tb);
  body.appendChild(tbl);
  if ((d.bez_saglasnosti || []).length)
    body.appendChild(el('p', 'razlog', T().metoBezSaglasnosti + ': ' + d.bez_saglasnosti.join(', ')));
}
renderMeto = viewMeto;
window.BEOPS_METO = viewMeto;
