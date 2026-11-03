/* BEOPS v2 dizajn.js — vizuelni sloj „za građanina" (lenji CSS modul, bez logike).
   beops.css i app.js su puni do ugovornog plafona, pa svaka nadgradnja ide
   kroz mali modul (obrazac: veceras.js, glas.js). Jedan <style> koji podiže
   tipografiju, dubinu ploča i toplinu redova IZNAD postojećeg beops.css:
   ni podatak, ni tekst, ni logika se ne menja — samo izgled.
   Sve boje naslanjaju se na postojeće varijable (--paper/--line/--green), pa
   tamna tema ostaje ispravna; badge boje su proverene na AA kontrast sa belim
   tekstom (#13644d ≈ 7.9:1, #a06b00 ≈ 4.6:1). Identitet i dalje nosi tekst,
   ne samo boja. */
'use strict';
(function () {
  if (document.getElementById('beops-dizajn')) return;
  const s = document.createElement('style');
  s.id = 'beops-dizajn';
  s.textContent = [
    'body{font-family:"Segoe UI Variable Text","Segoe UI",system-ui,-apple-system,Roboto,"Helvetica Neue",Arial,sans-serif;font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}',
    'body::before{content:"";display:block;height:3px;background:linear-gradient(90deg,var(--green),var(--blue),var(--um-ai,#eda100),var(--um-bridge,#7a6bd6))}',
    'h1,h2,h3,.brand strong{font-family:Georgia,"Times New Roman",serif}',
    '.section-head .sub{font-size:.92em;color:var(--ink-2);margin-top:2px}',
    '.metric,.kartica,.misao,.esej,.vodic-card,.banner,.danas-trend-box,.hero-advice{border-radius:10px}',
    '.metric,.kartica,.misao,.esej,.vodic-card,.veceras .ist-red{transition:transform .18s ease,box-shadow .18s ease}',
    '.metric,.kartica,.misao,.esej,.vodic-card,.veceras .ist-red{box-shadow:0 1px 2px rgba(20,45,35,.05),0 3px 12px rgba(20,45,35,.07)}',
    '@media (hover:hover) and (prefers-reduced-motion:no-preference){.kartica:hover,.misao:hover,.vodic-card:hover,.veceras .ist-red:hover{transform:translateY(-2px);box-shadow:0 2px 4px rgba(20,45,35,.06),0 8px 20px rgba(20,45,35,.11)}}',
    '.traka,.map-wrap{border-radius:10px;overflow:hidden}',
    '.table-wrap{border-radius:8px}',
    '.cite,.tag,.pill,.eaqi-tag,.chart-tabs button{border-radius:999px}',
    '.rail a[data-nav]{border-radius:999px;padding:3px 12px;transition:background .15s ease,color .15s ease}',
    '.rail a[data-nav][aria-current="page"]{background:var(--green);border-color:var(--green);color:#fff}',
    '.veceras .ist-red{border:1px solid var(--line);border-left:3px solid var(--green);background:var(--paper);padding:10px 14px}',
    '.veceras .tag.vc-vreme{background:var(--green);border-color:var(--green);color:#fff;font-weight:700;letter-spacing:.06em}',
    '.veceras .tag.vc-tok{background:#a06b00;border-color:#a06b00;color:#fff;font-weight:700;letter-spacing:.06em}',
    '.veceras .napomena{margin-top:8px}',
    '.delta,.tr-c b{font-variant-numeric:tabular-nums}',
    '@media (prefers-reduced-motion:reduce){.metric,.kartica,.misao,.esej,.vodic-card,.veceras .ist-red{transition:none}}'
  ].join('\n');
  document.head.appendChild(s);
})();
