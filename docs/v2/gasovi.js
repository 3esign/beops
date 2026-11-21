/* BEOPS v2 gasovi.js — četiri gasa iz referentne mreže (NO₂, O₃, SO₂, CO)
   kao ravnopravne 7-dnevne serije u #podaci i #danas.
   Jedna rečenica: Četiri gasa iz referentne mreže (NO₂, O₃, SO₂, CO) postaju
   ravnopravne 7-dnevne serije sa stvarnim jedinicama i iskricama na naslovnoj.
   Zaseban modul jer je app.js na ugovornoj granici od 64 KB.
   Izvori: state/serije/no2.json, state/serije/o3.json, state/serije/so2.json,
   state/serije/co.json (Talas 3 / S146 SEPA, CO ostaje u mg/m³ bez konverzije). */
'use strict';
/* global SERIES_IDS, SERIES_META */
(function () {
  if (typeof SERIES_IDS === 'undefined' || typeof SERIES_META === 'undefined') return;
  const GASES = {
    no2: { sr: 'NO₂ (µg/m³)', en: 'NO₂ (µg/m³)' },
    o3:  { sr: 'O₃ (µg/m³)',  en: 'O₃ (µg/m³)' },
    so2: { sr: 'SO₂ (µg/m³)', en: 'SO₂ (µg/m³)' },
    co:  { sr: 'CO (mg/m³)',  en: 'CO (mg/m³)' },
  };
  for (const id of Object.keys(GASES)) {
    if (!SERIES_META[id]) SERIES_META[id] = GASES[id];
    if (!SERIES_IDS.includes(id)) SERIES_IDS.push(id);
  }
})();
