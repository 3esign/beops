"""Small current view and descriptive temporal analysis, tied to exact public inputs.

No imputation, advice, causal claims or city-wide extrapolation. Hour coverage
describes the observed instrument and clock basis, never the whole city.
"""
import argparse
import hashlib
import json
import math
import pathlib
import re
from datetime import datetime, timedelta, timezone
from contracts import direction_summary, select_observation_points


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def summarize(snapshot):
    result = {k: snapshot[k] for k in ('as_of', 'window_hours') if k in snapshot}
    result.update(schema='beops-latest-observations/v1', summary_only=True, sources=[])
    for source in snapshot.get('sources', []):
        item = {k: source.get(k) for k in ('sid', 'name', 'cadence_seconds')}
        item['datastreams'] = []
        clock_rules = {}
        for stream in source.get('datastreams', []):
            small = {k: stream[k] for k in ('datastream', 'station', 'parameter', 'unit', 'lat', 'lon') if k in stream and stream[k] is not None}
            # A later null is evidence of missingness. Never replace it with an older number.
            points = stream.get('points', [])
            selected = select_observation_points(points)
            point = selected['last_by_measurement'] or selected['last_received']
            if point is not None:
                point = dict(point)
                rule = {key:point.pop(key) for key in ('clock_note','clock_rule','clock_valid_until') if key in point}
                if rule:
                    ref = hashlib.sha256(encode(rule)).hexdigest()[:16]
                    if ref in clock_rules and clock_rules[ref] != rule:
                        raise ValueError('clock disclosure hash collision')
                    clock_rules[ref] = rule
                    point['clock_ref'] = ref
            small['points'] = [point] if point is not None else []
            item['datastreams'].append(small)
        item['event_count'] = len(source.get('events', []))
        if clock_rules:
            item['clock_rules'] = clock_rules
        result['sources'].append(item)
    return result


def pack_summary(snapshot):
    """Lossless wire encoding: identical explicit point fields appear once per source.

    Missing properties never acquire a default. In particular null and false remain
    explicit evidence. Browser consumers restore these fields before selecting rows.
    """
    packed = json.loads(encode(snapshot))
    packed['schema'] = 'beops-latest-observations/v2'
    fields = ('t0', 't', 'tc0', 'tc', 'rt', 'rtc', 'rx', 'q', 'tu',
              'source_label', 'clock_unresolved', 'clock_ref')
    for source in packed.get('sources', []):
        points = [point for stream in source.get('datastreams', []) for point in stream.get('points', [])]
        if len(points) < 2:
            continue
        shared = {key: points[0][key] for key in fields if key in points[0]
                  and all(key in point and point[key] == points[0][key] for point in points)}
        if shared:
            source['point_defaults'] = shared
            for point in points:
                for key in shared:
                    del point[key]
    return packed


def windows(series, as_of):
    end = datetime.fromisoformat(as_of.replace('Z', '+00:00')).astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    result = {}
    kind = series.get('value_type', 'scalar')
    circular = kind == 'circular_degrees'
    arithmetic = kind in ('scalar', 'interval_average')
    for hours in (24, 168, 720):
        # Complete UTC hours only; the current partial hour cannot count as complete.
        start = end - timedelta(hours=hours)
        first_key, last_key = start.isoformat()[:13], end.isoformat()[:13]
        selected = [(key, row) for key, row in sorted(series.get('buckets', {}).items())
                    if first_key <= key < last_key and isinstance(row, dict)]
        for _, row in selected:
            n, missing, invalid = row.get('n'), row.get('missing', 0), row.get('invalid', 0)
            if (not isinstance(n, int) or isinstance(n, bool) or n < 0
                    or not isinstance(missing, int) or isinstance(missing, bool) or not 0 <= missing <= n):
                raise ValueError('invalid hourly sample counts')
            if not isinstance(invalid,int) or isinstance(invalid,bool) or not 0 <= invalid <= n-missing:
                raise ValueError('invalid hourly rejected sample counts')
            if arithmetic and (n > missing+invalid) != finite(row.get('mean')):
                raise ValueError('hourly mean and numeric sample count disagree')
            if circular:
                if row.get('direction_count') != n-missing-invalid or not all(finite(row.get(k)) for k in ('direction_sum_cos','direction_sum_sin')):
                    raise ValueError('invalid circular components/count')
                if math.hypot(row['direction_sum_cos'],row['direction_sum_sin']) > row['direction_count']+1e-9:
                    raise ValueError('circular resultant exceeds sample count')
        buckets = [(key,row) for key,row in selected if row['n'] > row.get('missing',0)+row.get('invalid',0)]
        samples = sum(row['n']-row.get('missing',0)-row.get('invalid',0) for _,row in buckets)
        means = [row.get('mean') for _, row in buckets]
        circular_result = direction_summary(math.fsum(row['direction_sum_cos'] for _,row in buckets),
                                            math.fsum(row['direction_sum_sin'] for _,row in buckets),samples) if circular else None
        average = (math.fsum(row.get('value_sum',row['mean']*(row['n']-row.get('missing',0)-row.get('invalid',0))) for _,row in buckets)/samples
                   if samples and arithmetic else circular_result['mean'] if circular else None)
        result[str(hours)] = {
            'from': start.isoformat().replace('+00:00', 'Z'), 'until': end.isoformat().replace('+00:00', 'Z'),
            'hours_with_values': len(buckets), 'window_hours': hours, 'samples': samples,
            'received_samples': sum(row['n'] for _, row in selected),
            'missing_samples': sum(row.get('missing', 0) for _, row in selected),
            'invalid_samples': sum(row.get('invalid',0) for _,row in selected),
            'coverage': round(len(buckets)/hours, 4),
            'sample_mean': average,
            'min': min((row['min'] for _, row in buckets if finite(row.get('min'))), default=None) if not circular else None,
            'max': max((row['max'] for _, row in buckets if finite(row.get('max'))), default=None) if not circular else None,
            'first_hour': buckets[0][0] if buckets else None,
            'last_hour': buckets[-1][0] if buckets else None,
            'first_hour_mean': means[0] if means else None,
            'last_hour_mean': means[-1] if means else None,
            'endpoint_difference': means[-1]-means[0] if arithmetic and len(means)>1 and finite(means[-1]) and finite(means[0]) else None,
            'state': 'observed_range' if len(buckets) > 1 else 'insufficient_observations',
        }
        if circular:
            result[str(hours)].update(resultant_length=circular_result['resultant_length'],direction_state=circular_result['direction_state'])
    return result


def analyze(history, as_of):
    rows = []
    for series in history.get('series', []):
        if series.get('kind') != 'numeric': continue
        item = {k: series.get(k) for k in ('sid', 'datastream', 'station', 'parameter', 'unit', 'time_basis','value_type','interval_seconds')}
        item['windows'] = windows(series, as_of)
        # Descriptive differences are not evidence of recurrence or a long-term trend.
        item['recurrence'] = {'state': 'not_tested', 'reason': 'descriptive windows do not establish a recurring pattern'}
        rows.append(item)
    return {'schema': 'beops-city-analysis/v2', 'as_of': as_of, 'series': rows,
            'method': 'UTC complete hours; registered scalar sample sums or unweighted direction components; counts have no automatic mean; missing hours remain absent; no spatial aggregation',
            'scope': 'Descriptive instrument observations, not city-wide conditions, causation, predictions or recommendations.'}


def build(docs):
    docs = pathlib.Path(docs)
    resources, values = {}, {}
    for name in ('live-snapshot.json', 'history.json', 'watch.json'):
        path = docs/name
        if not path.exists():
            values[name] = {}
            continue
        raw = path.read_bytes()
        values[name] = json.loads(raw)
        resources[name] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    snapshot = values['live-snapshot.json']
    if not snapshot.get('as_of'):
        raise ValueError('current overview requires a dated observation snapshot')
    history = values['history.json']
    generation = snapshot.get('input_generation')
    history_generation = history.get('input_generation')
    if generation or history_generation:
        if not generation or generation != history_generation:
            raise ValueError('snapshot and history input generations differ')
        if (generation.get('schema') != 'beops-input-generation/v1' or generation.get('observation_prefix') != 'complete-lf-lines/v1'
                or not re.fullmatch('[a-f0-9]{64}', str(generation.get('id', '')))):
            raise ValueError('unverified observation generation')
        captured = datetime.fromisoformat(generation['captured_at'].replace('Z', '+00:00'))
        if captured.tzinfo is None:
            raise ValueError('unqualified capture clock')
        if captured > datetime.now(timezone.utc)+timedelta(minutes=5):
            raise ValueError('capture clock is in the future')
        expected_as_of = captured.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        if snapshot['as_of'] != expected_as_of or history.get('as_of') != expected_as_of:
            raise ValueError('projection does not cover the declared capture')
    analysis = analyze(values['history.json'], snapshot['as_of'])
    analysis['input_generation'] = generation
    analysis['generation_state'] = 'verified_capture' if generation else 'unverified_legacy'
    raw_analysis = encode(analysis)
    resources['city-analysis.json'] = {'sha256': hashlib.sha256(raw_analysis).hexdigest(), 'bytes': len(raw_analysis)}
    view = {'schema': 'beops-city-view/v1', 'as_of': snapshot['as_of'],
            'edition': {'built_at': datetime.now(timezone.utc).isoformat(),
                        'input_generation': generation,
                        'state': 'verified_capture' if generation else 'unverified_legacy'},
            'generation': hashlib.sha256(encode(resources)).hexdigest(), 'resources': resources,
            'snapshot': pack_summary(summarize(snapshot)),
            'collector': {'assessed_at': (snapshot.get('status') or {}).get('as_of'),
                          'sources': [{k:s.get(k) for k in ('sid','last_captured_at','last_attempt_at','last_attempt_state','cadence_seconds','paused','captured','failed','missing')}
                                      for s in (snapshot.get('status') or {}).get('sources', [])]},
            'watch': {k: values['watch.json'].get(k) for k in ('at', 'counts')},
            'history': {k: values['history.json'].get(k) for k in ('built', 'as_of', 'history_starts', 'history_ends', 'hours_of_history')},
            'scope': 'Latest retained observation per instrument; detailed series and descriptive analysis are loaded on request.'}
    payload = encode(view)
    # Refuse silent truncation if the live network outgrows the first-frame budget.
    if len(payload) > 150 * 1024:
        raise ValueError(f'overview exceeds 150 KiB budget: {len(payload)} bytes')
    (docs/'city-analysis.json').write_bytes(raw_analysis)
    (docs/'city-overview.json').write_bytes(payload)
    return {'generation': view['generation'], 'overview_bytes': len(payload), 'analysis_bytes': len(raw_analysis), 'streams': len(analysis['series'])}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('docs'); args = parser.parse_args()
    print(json.dumps(build(args.docs)))
