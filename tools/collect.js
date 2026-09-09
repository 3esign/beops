'use strict';
const path=require('node:path');const {Store}=require('../src/store');
new Store(process.env.BEOPS_DATA||path.join(__dirname,'../runtime')).init().then(async store=>{
  const state=await store.refresh();console.log(JSON.stringify({updated:state.updated,sources:state.sources.map(s=>({id:s.id,status:s.status,error:s.error})),records:state.observations.length}));
  if(!state.sources.some(s=>s.status==='ok'))process.exitCode=1;
}).catch(error=>{console.error(error);process.exitCode=1;});
