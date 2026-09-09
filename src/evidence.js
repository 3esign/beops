'use strict';
const crypto = require('node:crypto');
const CITIES = [{id:'beograd', name:'Beograd', lat:44.8176, lon:20.4633}];
const METRICS = {
  temperature_2m:{label:'Temperatura', unit:'\u00b0C', range:[-90,65]},
  relative_humidity_2m:{label:'Relativna vlaznost', unit:'%', range:[0,100]},
  wind_speed_10m:{label:'Brzina vetra', unit:'km/h', range:[0,500]},
  precipitation:{label:'Padavine', unit:'mm', range:[0,1000]},
  pm2_5:{label:'PM2.5', unit:'\u03bcg/m\u00b3', range:[0,2000]},
  pm10:{label:'PM10', unit:'\u03bcg/m\u00b3', range:[0,4000]},
  nitrogen_dioxide:{label:'NO2', unit:'\u03bcg/m\u00b3', range:[0,5000]},
  ozone:{label:'Ozon', unit:'\u03bcg/m\u00b3', range:[0,5000]}
};
const hash = input => crypto.createHash('sha256').update(input).digest('hex');
function sources() {
  return CITIES.flatMap(city => ['weather','air'].map(type => {
    const metrics = type === 'weather' ? Object.keys(METRICS).slice(0,4) : Object.keys(METRICS).slice(4);
    const url = new URL(type === 'weather' ? 'https://api.open-meteo.com/v1/forecast' : 'https://air-quality-api.open-meteo.com/v1/air-quality');
    for (const [key,value] of Object.entries({latitude:city.lat,longitude:city.lon,current:metrics.join(','),hourly:metrics.join(','),forecast_days:2,timezone:'GMT',timeformat:'unixtime'})) url.searchParams.set(key,String(value));
    return {id:`${city.id}-${type}`, city:city.id, type, metrics, url:String(url),
      label:type === 'weather' ? 'Open-Meteo / numericka prognoza' : 'CAMS ENSEMBLE / Open-Meteo',
      method:'forecast', license:'CC BY 4.0', access:'non-commercial research API',
      docs:type === 'weather' ? 'https://open-meteo.com/en/docs' : 'https://open-meteo.com/en/docs/air-quality-api'};
  }));
}
function normalize(source, raw, retrievedAt, contentHash) {
  const observed = raw.current?.time;
  if (!Number.isFinite(observed) || observed < 0 || !raw.current_units) throw new Error('Invalid source time or units');
  const validAt = new Date(observed * 1000).toISOString();
  if (Math.abs(Date.parse(validAt)-Date.parse(retrievedAt)) > 48*3600000) throw new Error('Current source time is outside 48-hour validity window');
  const observations = source.metrics.map(metric => {
    const def = METRICS[metric], value = raw.current[metric];
    const present = typeof value === 'number' && Number.isFinite(value);
    const unitOk = raw.current_units[metric] === def.unit;
    const inRange = present && value >= def.range[0] && value <= def.range[1];
    const state = !present ? 'missing' : !unitOk || !inRange ? 'invalid' : 'available';
    return {id:hash(`${source.id}|${metric}|${validAt}|${contentHash}`).slice(0,24), city:source.city,
      metric, label:def.label, value:state === 'available' ? value : null, unit:def.unit, state,
      method:source.method, validAt, retrievedAt, source:source.id, contentHash,
      spatialSupport:'model grid at city reference point; not an in-situ station',
      reason:state === 'available' ? '' : !present ? 'missing upstream value' : !unitOk ? 'unexpected unit' : 'outside validation range'};
  });
  const timeline = [];
  for (let i=0; i<Math.min(48, raw.hourly?.time?.length || 0); i++) {
    const t=raw.hourly.time[i];
    if (!Number.isFinite(t)) continue;
    const row={validAt:new Date(t*1000).toISOString()};
    for (const metric of source.metrics) {
      const value=raw.hourly[metric]?.[i], def=METRICS[metric];
      row[metric]=typeof value==='number' && Number.isFinite(value) && value>=def.range[0] && value<=def.range[1] && raw.hourly_units?.[metric]===def.unit ? value : null;
    }
    timeline.push(row);
  }
  return {observations,timeline};
}
function viewRecord(record, source, now=Date.now()) {
  const stale = !source || source.status !== 'ok' || now-Date.parse(record.retrievedAt)>30*60000 || now-Date.parse(record.validAt)>3*3600000;
  return {...record, freshness:stale?'stale':'fresh'};
}
function validateSelection(value, records) {
  if (!value || !Array.isArray(value.evidenceIds) || value.evidenceIds.length > 6) throw new Error('Invalid model selection');
  const allowed=new Set(records.filter(r=>r.state==='available' && r.freshness==='fresh').map(r=>r.id));
  if (new Set(value.evidenceIds).size!==value.evidenceIds.length || value.evidenceIds.some(id=>!allowed.has(id))) throw new Error('Model selected unknown, stale or unavailable evidence');
  return value.evidenceIds;
}
module.exports={CITIES,METRICS,sources,hash,normalize,viewRecord,validateSelection};
