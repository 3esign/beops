'use strict';
// Which facts may be connected in one AI observation, and why.
// A connection is allowed only when research/AI_FEED_RELATIONS.json names a physical mechanism
// (or a same-quantity comparison) AND the two facts are close enough in time and space.
// Everything else is described separately. This is the rule that stops "parking and river
// temperature" monologues: there is no mechanism, so there is no relation to cite.
const fs = require('node:fs');
const path = require('node:path');

const RULES_FILE = path.resolve(__dirname, '../research/AI_FEED_RELATIONS.json');
let cached = null;
function rules() {
  if (!cached) cached = JSON.parse(fs.readFileSync(RULES_FILE, 'utf8').replace(/^﻿/, ''));
  return cached;
}

const QUANTITY = {
  'PM10': 'pm10', 'P1': 'pm10', 'PM2.5': 'pm25', 'P2': 'pm25', 'P0': 'pm1',
  'NO2': 'no2', 'NO': 'no', 'NOX': 'nox', 'O3': 'o3', 'CO': 'co', 'SO2': 'so2', 'Benzen': 'benzene',
  'temperature': 'air_temperature', 'dew_point': 'dew_point', 'humidity': 'humidity',
  'pressure': 'pressure', 'pressure_qnh': 'pressure', 'pressure_at_sealevel': 'pressure',
  'wind_speed': 'wind_speed', 'wind_direction': 'wind_direction',
  'water_level': 'water_level', 'water_level_change': 'water_level_change',
  'water_temperature': 'water_temperature', 'discharge': 'discharge',
  'free_spaces': 'free_spaces',
};
const DOMAIN = {
  pm10: 'air', pm25: 'air', pm1: 'air', no2: 'air', no: 'air', nox: 'air', o3: 'air', co: 'air', so2: 'air', benzene: 'air',
  air_temperature: 'weather', dew_point: 'weather', humidity: 'weather', pressure: 'weather', wind_speed: 'weather', wind_direction: 'weather',
  water_level: 'river', water_level_change: 'river', water_temperature: 'river', discharge: 'river',
  free_spaces: 'parking',
};

function quantity(f) {
  if (!f || f.kind !== 'observation') return null;
  const m = String(f.metric || '');
  if (QUANTITY[m]) return QUANTITY[m];
  const tail = m.split('|').pop();
  return QUANTITY[tail] || null;
}
function domain(f) {
  if (!f) return 'unknown';
  if (f.kind === 'historical_context') return 'statistics';
  if (f.kind === 'demographic_context') return 'population';
  if (f.kind === 'temporal_context') return 'time';
  return DOMAIN[quantity(f)] || 'unknown';
}
function when(f) {
  const t = Date.parse(f && (f.time || f.received_at));
  return Number.isFinite(t) ? t : null;
}
function km(a, b) {
  if (!Array.isArray(a && a.location) || !Array.isArray(b && b.location)) return null;
  const [lon1, lat1] = a.location, [lon2, lat2] = b.location, R = 6371, r = Math.PI / 180;
  const dLat = (lat2 - lat1) * r, dLon = (lon2 - lon1) * r;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * r) * Math.cos(lat2 * r) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

// Returns the rule that allows a and b to be discussed together, or null.
function relate(a, b) {
  const qa = quantity(a), qb = quantity(b);
  if (!qa || !qb || a === b) return null;
  const ta = when(a), tb = when(b);
  if (ta === null || tb === null) return null;
  const gap = Math.abs(ta - tb) / 60000, dist = km(a, b);
  for (const rule of rules().rules) {
    const pair = rule.same_quantity ? qa === qb && (!rule.quantities || rule.quantities.includes(qa)) && !(rule.exclude || []).includes(qa)
      : (rule.a.includes(qa) && rule.b.includes(qb)) || (rule.a.includes(qb) && rule.b.includes(qa));
    if (!pair) continue;
    if (rule.different_place && String(a.place) === String(b.place)) continue;
    if (gap > rule.max_gap_minutes) continue;
    if (rule.max_distance_km != null) {
      if (dist === null) { if (!rule.distance_unknown_ok) continue; }
      else if (dist > rule.max_distance_km) continue;
    }
    return { rule: rule.id, kind: rule.kind, gap_minutes: Math.round(gap), distance_km: dist === null ? null : Math.round(dist * 10) / 10, note_sr: rule.note_sr };
  }
  return null;
}

function relations(facts) {
  const out = [];
  for (let i = 0; i < facts.length; i++) for (let j = i + 1; j < facts.length; j++) {
    const r = relate(facts[i], facts[j]);
    if (r) out.push({ id: 'R' + (out.length + 1), facts: [facts[i].id, facts[j].id], ...r });
  }
  return out;
}

// True when the cited facts form one connected group through allowed relations.
function connected(cited, rels) {
  if (cited.length < 2) return true;
  const ids = cited.map(f => f.id), seen = new Set([ids[0]]);
  let grew = true;
  while (grew) {
    grew = false;
    for (const r of rels) {
      const [x, y] = r.facts;
      if (!ids.includes(x) || !ids.includes(y)) continue;
      if (seen.has(x) !== seen.has(y)) { seen.add(x); seen.add(y); grew = true; }
    }
  }
  return ids.every(i => seen.has(i));
}

module.exports = { quantity, domain, relate, relations, connected, when, km, rules };
