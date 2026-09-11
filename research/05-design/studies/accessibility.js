'use strict';
// Enhance native structure after each data render. No observer changes text data.
(() => {
  function start() {
    const main = document.querySelector('main,[role="main"]');
    if(main){if(!main.id)main.id='beops-main';main.tabIndex=-1;const a=document.createElement('a');a.className='skip-link';a.href='#'+main.id;a.textContent='Pređi na sadržaj / Skip to content';document.body.prepend(a);}
    let scheduled=false;
    function semantics(){scheduled=false;for(const table of document.querySelectorAll('table')){
      if(!table.caption){const h=table.closest('section')?.querySelector('h2');const c=table.createCaption();c.className='a11y-only';c.textContent=h?.textContent.trim()||'Podaci / Data';}
      for(const th of table.querySelectorAll('thead th'))if(!th.hasAttribute('scope'))th.scope='col';
    }}
    semantics();new MutationObserver(()=>{if(!scheduled){scheduled=true;requestAnimationFrame(semantics);}}).observe(document.body,{childList:true,subtree:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
