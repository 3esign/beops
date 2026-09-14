"""R04: geometry, reception order, revisions and explicit unknown arithmetic."""
import math
import pathlib
import subprocess
import unittest
import test_build_history as history_cases
import build_city_view as city
from contracts import select_observation_points
row=history_cases.row


class ParameterSemantics(unittest.TestCase):
    fold=history_cases.HistoryCase.fold
    def bucket(self, records):
        return self.fold({'S01':records})['series'][0]['buckets']['2026-09-09T10']

    def direction(self, value, minute=0, **fields):
        return row(parameter='wind_direction',unit='deg',datastream='Beograd|wind_direction',
                   result=value,phenomenonTime=f'2026-09-09T10:{minute:02d}:00Z',**fields)

    def test_direction_across_north_and_antipodal_cancellation(self):
        north=self.bucket([self.direction(350),self.direction(10,1)])
        self.assertAlmostEqual(north['mean'],0,places=6)
        self.assertEqual(north['direction_count'],2)
        self.assertNotIn('min',north)
        opposite=self.bucket([self.direction(90),self.direction(270,1)])
        self.assertIsNone(opposite['mean'])
        self.assertEqual(opposite['direction_state'],'undefined_resultant')
        self.assertEqual(opposite['missing'],0)

    def test_windows_combine_components_even_when_an_hour_cancels(self):
        records=[self.direction(90),self.direction(270,1),
                 row(parameter='wind_direction',unit='deg',datastream='Beograd|wind_direction',
                     result=350,phenomenonTime='2026-09-09T11:00:00Z'),
                 row(parameter='wind_direction',unit='deg',datastream='Beograd|wind_direction',
                     result=10,phenomenonTime='2026-09-09T11:01:00Z')]
        series=self.fold({'S01':records})['series'][0]
        result=city.windows(series,'2026-09-09T14:30:00Z')['24']
        self.assertAlmostEqual(result['sample_mean'],0,places=6)
        self.assertEqual(result['samples'],4)
        self.assertEqual(result['hours_with_values'],2)
        self.assertIsNone(result['min'])
        self.assertIsNone(result['endpoint_difference'])
        self.assertAlmostEqual(result['resultant_length'],math.cos(math.radians(10))/2)

    def test_hourly_direction_means_are_not_averaged_or_equally_weighted(self):
        records=[self.direction(0,n) for n in range(3)]
        records.append(row(parameter='wind_direction',unit='deg',datastream='Beograd|wind_direction',
                           result=90,phenomenonTime='2026-09-09T11:00:00Z'))
        series=self.fold({'S01':records})['series'][0]
        value=city.windows(series,'2026-09-09T14:30:00Z')['24']['sample_mean']
        self.assertAlmostEqual(value,math.degrees(math.atan2(1,3)),places=8)

    def test_latest_measurement_and_last_reception_have_distinct_clocks(self):
        bucket=self.bucket([
            row(result=30,phenomenonTime='2026-09-09T10:50:00Z',receivedTime='2026-09-09T11:00:00Z'),
            row(result=10,phenomenonTime='2026-09-09T10:10:00Z',receivedTime='2026-09-09T11:05:00Z')])
        self.assertEqual(bucket['last_by_measurement']['v'],30)
        self.assertEqual(bucket['last_received']['v'],10)
        self.assertEqual(bucket['last_by_measurement']['t'],'2026-09-09T10:50:00Z')
        self.assertEqual(bucket['last_received']['rx'],'2026-09-09T11:05:00Z')

    def test_latest_null_remains_null_and_latest_revision_wins_out_of_order(self):
        bucket=self.bucket([row(result=20,phenomenonTime='2026-09-09T10:10:00Z'),
                            row(result=None,phenomenonTime='2026-09-09T10:30:00Z',receivedTime='2026-09-09T10:31:00Z')])
        self.assertIsNone(bucket['last'])
        self.assertIsNone(bucket['last_by_measurement']['v'])
        bucket=self.bucket([row(result=None,dedupe_key='event',receivedTime='2026-09-09T10:30:00Z'),
                            row(result=40,dedupe_key='event',receivedTime='2026-09-09T10:10:00Z')])
        self.assertEqual(bucket['n'],1)
        self.assertIsNone(bucket['last_received']['v'])

    def test_unknown_type_does_not_inherit_arithmetic(self):
        series=self.fold({'S01':[row(parameter='unknown_quantity',unit='u',result=999)]})['series'][0]
        self.assertEqual(series['value_type'],'unknown')
        self.assertNotIn('mean',series['buckets']['2026-09-09T10'])

    def test_implicit_measurement_identity_revises_without_a_custom_dedupe_key(self):
        bucket=self.bucket([row(result=10,receivedTime='2026-09-09T10:10:00Z'),
                            row(result=None,receivedTime='2026-09-09T10:30:00Z'),
                            row(result=50,receivedTime='2026-09-09T10:20:00Z')])
        self.assertEqual(bucket['n'],1)
        self.assertEqual(bucket['missing'],1)
        self.assertIsNone(bucket['last'])

    def test_revision_moves_hours_and_counter_has_no_automatic_mean(self):
        series=self.fold({'S01':[row(dedupe_key='x',result=1),
            row(dedupe_key='x',result=2,phenomenonTime='2026-09-09T11:00:00Z',receivedTime='2026-09-09T11:01:00Z')]})['series'][0]
        self.assertEqual(list(series['buckets']),['2026-09-09T11'])
        series=self.fold({'S01':[row(parameter='free_spaces',unit='1',result=10)]})['series'][0]
        self.assertEqual(series['value_type'],'count')
        self.assertNotIn('mean',series['buckets']['2026-09-09T10'])
        window=city.windows(series,'2026-09-09T14:30:00Z')['24']
        self.assertIsNone(window['sample_mean'])
        self.assertEqual(window['samples'],1)

    def test_public_selectors_and_small_overview_keep_latest_null(self):
        first={'t':'2026-09-09T12:50:00+02:00','rx':'2026-09-09T11:00:00Z','v':None}
        late={'t':'2026-09-09T10:10:00Z','rx':'2026-09-09T11:05:00Z','v':10}
        selected=select_observation_points([first,late])
        self.assertEqual(selected['last_by_measurement'],first)
        self.assertEqual(selected['last_received'],late)
        snap={'sources':[{'sid':'S01','datastreams':[{'points':[first,late]}]}]}
        self.assertEqual(city.summarize(snap)['sources'][0]['datastreams'][0]['points'],[first])
        untimed={'tu':True,'t':None,'rx':'2026-09-09T11:10:00Z','v':0}
        self.assertIsNone(select_observation_points([untimed])['last_by_measurement'])
        self.assertEqual(select_observation_points([untimed])['last_received'],untimed)

    def test_invalid_counts_and_angles_do_not_enter_valid_sample_totals(self):
        bucket=self.bucket([self.direction(361),self.direction(None,1)])
        self.assertEqual((bucket['n'],bucket['missing'],bucket['invalid'],bucket['direction_count']),(2,1,1,0))
        self.assertIsNone(bucket['mean'])
        series=self.fold({'S01':[row(parameter='free_spaces',unit='1',result=-1),
            row(parameter='free_spaces',unit='1',result=0,phenomenonTime='2026-09-09T10:01:00Z')]})['series'][0]
        window=city.windows(series,'2026-09-09T14:30:00Z')['24']
        self.assertEqual((window['samples'],window['invalid_samples'],window['min']),(1,1,0))

    def test_neutral_map_and_actual_latest_selectors(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        result=subprocess.run(['node',str(root/'research/parameter_surface_contract.test.cjs')],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_parameter_unit_and_interval_semantics_keep_series_separate(self):
        def pm(**kw):
            return row(sid='S146',parameter='PM10',datastream='station|PM10',unit=kw.pop('unit','ug.m-3'),**kw)
        series=self.fold({'S146':[
            pm(result=1),
            pm(result=2,aggregation='hourly_mean',phenomenonTime={'start':'2026-09-09T09:00:00Z','end':'2026-09-09T10:00:00Z'}),
            pm(result=3,unit='unknown-unit'),
        ]})['series']
        self.assertEqual(sorted(s['value_type'] for s in series),['interval_average','scalar','unknown'])


if __name__=='__main__':unittest.main()
