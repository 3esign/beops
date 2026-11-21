/* BEOPS v2 · pogledi #organizam i #o — poseban modul van 64 KB budžeta shella (rasterećenje app.js,
   21.11.2026). Registruje rute `organizam` i `o` u VIEWS; učitava se posle app.js (defer redosled u
   index.html) i koristi njegove zajedničke gradivne funkcije (el, mkTable, sectionHead, stampEl…). */
'use strict';
/* ── Pogled: #organizam ─────────────────────────────────── */
function viewOrganizam(root) {
  root.textContent = '';
  root.appendChild(sectionHead(null, T().orgTitle, T().orgSub));
  root.appendChild(mkTable(
    [T().organCol, T().ulogaCol, T().kadensaCol, T().poslednjiCol, T().statusCol],
    ((STATE.organizam && STATE.organizam.organs) || []).map(o => {
      const stamp = document.createDocumentFragment();
      if (o.last_run) { stamp.appendChild(stampEl(o.last_run, o.cadence_minutes || 30)); stamp.appendChild(el('div', 'sub', absTime(o.last_run))); }
      else stamp.appendChild(el('span', null, T().statusUnknown));
      return [o.name, o.role || '', (o.cadence_minutes || '?') + ' min', stamp,
        T()[o.status === 'ok' ? 'statusOk' : o.status === 'late' ? 'statusLate' : 'statusUnknown']];
    })));

  root.appendChild(el('h2', null, T().izvoriTitle));
  root.appendChild(el('p', 'sub', T().izvoriSub));
  root.appendChild(mkTable([T().izvorCol, T().oblastCol, T().starostCol],
    ((STATE.organizam && STATE.organizam.sources) || []).slice(0, 40).map(s =>
      [s.name, s.domain || '', s.reception_age_minutes == null ? '—' : s.reception_age_minutes + ' min'])));
}

/* ── Pogled: #o ─────────────────────────────────────────── */
function viewO(root) {
  renderO(root);
  /* K7 i B6 stižu lenjo — strana se odmah nacrta, dopuni kad moduli stignu */
  loadBelaznica().then(() => { if (currentRoute() === 'o') renderO(root); });
  loadMeto().then(() => { if (currentRoute() === 'o') renderO(root); });
}
function belaznicaRed(naziv, g) {
  const tr = el('tr');
  tr.appendChild(el('td', null, naziv));
  for (const v of [g.misli, g.korisno, g.nekorisno, g.deo_korisnih === null ? '—' : fmtNum(g.deo_korisnih, 2)])
    tr.appendChild(el('td', 'v', String(v)));
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
    const tw = el('div', 'table-wrap'); tw.appendChild(bt); body.appendChild(tw);
    let mt = bel.prihvacenih_glasova + ' ' + T().belaGlasova + ' ' + T().belaNad + ' ' + bel.ocenjenih_misli + ' ' + T().belaMisli;
    if (bel.glasova_na_nepoznatoj_misli) mt += ' · ' + bel.glasova_na_nepoznatoj_misli + ' ' + T().belaNepoznate;
    body.appendChild(el('p', 'meta', mt));
  }
  /* B6: metodološki list crta lenji modul (naslov+brojevi su u modulu) */
  if (STATE.meto) renderMeto(body);
  body.appendChild(el('h2', null, T().autorstvo));
  body.appendChild(el('p', null, 'prof. dr Darinka Golubović Matić · doc. dr Semir Poturak'));
  if (STATE.puls) {
    body.appendChild(el('p', 'sub', T().verzija + ': ' + absTime(STATE.puls.generated_at)));
  }
  root.appendChild(body);
}

VIEWS.organizam = viewOrganizam;
VIEWS.o = viewO;
