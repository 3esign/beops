(function(root,factory){
 'use strict';
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.BeopsImpulseCodec=Object.freeze(api);
})(typeof globalThis==='object'?globalThis:this,function(){
 'use strict';
 // Exact column dictionaries reduce repeated source, clock, location-policy and
 // provenance fields. This is a transport encoding, not a weaker data model.
 const own=(object,key)=>Object.prototype.hasOwnProperty.call(object,key);
 function packItems(items){
  if(!Array.isArray(items))throw Error('invalid_impulse_items');
  const keys=[...new Set(items.flatMap(item=>Object.keys(item)))],columns=[],vectors=[];
  for(const key of keys){
   const values=[],byJSON=new Map(),refs=[],raw=[];let rawLength=0,missing=false;
   for(const item of items){
    if(!own(item,key)){missing=true;refs.push(-1);raw.push(null);continue;}
    const value=item[key],json=JSON.stringify(value);
    if(json===undefined)throw Error('non_json_impulse_value');
    if(!byJSON.has(json)){byJSON.set(json,values.length);values.push(value);}
    refs.push(byJSON.get(json));raw.push(value);rawLength+=json.length+1;
   }
   // Compare actual serialized column sizes. Unique titles/URLs stay raw;
   // repeated geo policy, evidence receipts and times become references.
   const dictionary=missing||JSON.stringify(values).length+JSON.stringify(refs).length+12<rawLength;
   columns.push(dictionary?{key,values}:{key});vectors.push(dictionary?refs:raw);
  }
  return {columns,records:items.map((_,index)=>vectors.map(column=>column[index]))};
 }
 function unpackItems(columns,records){
  if(!Array.isArray(columns)||!Array.isArray(records))throw Error('invalid_impulse_encoding');
  const keys=new Set();
  for(const column of columns){
   if(!column||typeof column.key!=='string'||!/^[a-z][a-z0-9_]*$/.test(column.key)||['constructor','prototype','__proto__'].includes(column.key)||keys.has(column.key))throw Error('invalid_impulse_column');
   if(own(column,'values')&&!Array.isArray(column.values))throw Error('invalid_impulse_dictionary');
   keys.add(column.key);
  }
  return records.map(row=>{
   if(!Array.isArray(row)||row.length!==columns.length)throw Error('invalid_impulse_record');
   const item={};
   for(let index=0;index<columns.length;index++){
    const column=columns[index],cell=row[index];
    if(own(column,'values')){
     if(!Number.isInteger(cell)||cell< -1||cell>=column.values.length)throw Error('invalid_impulse_reference');
     if(cell!==-1)item[column.key]=column.values[cell];
    }else item[column.key]=cell;
   }
   return item;
  });
 }
 function decodeImpulses(document){
  if(document?.schema!=='beops-public-impulses/v2'||document.encoding!=='column-dictionaries/v1')throw Error('unsupported_impulse_encoding');
  const {columns,records,...metadata}=document;
  return {...metadata,items:unpackItems(columns,records)};
 }
 return {packItems,unpackItems,decodeImpulses};
});
