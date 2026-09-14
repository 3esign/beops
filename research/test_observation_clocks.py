"""R05: source labels, estimates and reception must retain different meanings."""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import contracts as C
import collect_daemon as D
import latency as L
import build_history as H
import build_city_view as V

NOW = datetime(2026, 9, 14, 15, tzinfo=timezone.utc)
BODY = json.dumps({'data':[{'station_id':1, 'parameter_code':'PM10', 'value':None,
    'time_start_utc':'2026-09-14T16:00:00Z', 'time_end_utc':'2026-09-14T17:00:00Z',
    'published_at_utc':'2026-09-14T17:05:00Z', 'aggregation_type':'hourly_mean'}]}).encode()


def source(until='2026-10-25T01:00:00Z'):
    return {'sid':'S146', 'source_clock_note':{'offset_seconds':7200,
        'text':'observed summer label offset', 'rule_id':'test-summer/v1', 'valid_until':until}}


class ObservationClocks(unittest.TestCase):
    def test_compact_wire_roundtrips_clocks_null_false_and_absent_fields(self):
        point = C.observation_point(D.parse_sepa_hvd(BODY,NOW,source())[0])
        snapshot={'sources':[{'sid':'S146','datastreams':[
            {'datastream':str(i),'points':[dict(point,v=None if i==0 else i)]} for i in range(245)]},
            {'sid':'S10','datastreams':[
                {'datastream':'a','points':[{'v':0,'t':None,'tu':True,'rx':'2026-09-14T15:00:00Z'}]},
                {'datastream':'b','points':[{'v':None,'tu':True,'rx':'2026-09-14T15:00:00Z'}]},
                {'datastream':'c','points':[]}]}]}
        expected=V.summarize(snapshot);before=copy.deepcopy(expected)
        packed=V.pack_summary(expected)
        self.assertEqual(expected,before)
        self.assertGreater(len(V.encode(expected))-len(V.encode(packed)),20000)
        self.assertNotIn('t',packed['sources'][1]['point_defaults'],'absence must remain distinct from explicit null')
        result=subprocess.run(['node',str(ROOT/'research/overview_roundtrip.test.cjs')],
            input=json.dumps({'expected':expected,'packed':packed}),capture_output=True,text=True,encoding='utf-8',timeout=40,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_small_view_retains_shared_clock_provenance(self):
        point = C.observation_point(D.parse_sepa_hvd(BODY,NOW,source())[0])
        snapshot={'sources':[{'sid':'S146','datastreams':[
            {'datastream':str(i),'points':[point]} for i in range(3)]}]}
        out=V.summarize(snapshot)['sources'][0]
        self.assertEqual(len(out['clock_rules']),1)
        for stream in out['datastreams']:
            compact=stream['points'][0]
            rule=out['clock_rules'][compact['clock_ref']]
            self.assertEqual(rule['clock_rule'],point['clock_rule'])
            self.assertEqual(rule['clock_valid_until'],point['clock_valid_until'])
            self.assertEqual(rule['clock_note'],point['clock_note'])
            self.assertEqual(compact['tc'],point['tc'])
        self.assertIn('clock_note',point,'summary must not mutate the original point')

    def test_same_sepa_row_through_real_surfaces_and_ai_context(self):
        point = C.observation_point(D.parse_sepa_hvd(BODY, NOW, source())[0])
        result = subprocess.run(['node',str(ROOT/'research/observation_clock_surfaces.test.cjs')],
            input=json.dumps(point),capture_output=True,text=True,encoding='utf-8',timeout=40,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)

    def test_public_point_keeps_all_named_clocks_and_null(self):
        row = D.parse_sepa_hvd(BODY, NOW, source())[0]
        original = copy.deepcopy(row)
        point = C.observation_point(row)
        self.assertEqual(row, original, 'disclosure must not rewrite evidence')
        self.assertIsNone(point['v'])
        self.assertEqual(point['t0'], '2026-09-14T16:00:00Z')
        self.assertEqual(point['t'], '2026-09-14T17:00:00Z')
        self.assertEqual(point['tc0'], '2026-09-14T14:00:00Z')
        self.assertEqual(point['tc'], '2026-09-14T15:00:00Z')
        self.assertEqual(point['rt'], '2026-09-14T17:05:00Z')
        self.assertEqual(point['rtc'], '2026-09-14T15:05:00Z')
        self.assertEqual(point['rx'], '2026-09-14T15:00:00Z')
        self.assertEqual(point['clock_rule'], 'test-summer/v1')
        self.assertEqual(point['clock_valid_until'], '2026-10-25T01:00:00Z')

    def test_expiry_compares_instants_not_iso_text(self):
        row = D.parse_sepa_hvd(BODY, NOW, source('2026-09-14T17:00:00+02:00'))[0]
        self.assertTrue(row.get('sourceClockUnresolved'))
        self.assertNotIn('phenomenonTimeCorrected', row)
        self.assertEqual(C.row_clock(row), (None, 'invalid'))

    def test_missing_or_invalid_expiry_never_creates_an_unbounded_estimate(self):
        for until in (None, 'bad-clock', '2026-10-25T01:00:00'):
            with self.subTest(until=until):
                row = D.parse_sepa_hvd(BODY, NOW, source(until))[0]
                self.assertTrue(row.get('sourceClockUnresolved'))
                self.assertNotIn('phenomenonTimeCorrected', row)

    def test_unzoned_source_label_is_not_interpreted_as_the_host_timezone(self):
        self.assertIsNone(D._shift('2026-09-14T17:00:00',-7200))
        doc=json.loads(BODY)
        doc['data'][0]['time_end_utc']='2026-09-14T17:00:00'
        row=D.parse_sepa_hvd(json.dumps(doc).encode(),NOW,source())[0]
        self.assertTrue(row['sourceClockUnresolved'])
        self.assertEqual(C.row_clock(row),(None,'invalid'))

    def test_at_seasonal_boundary_estimate_is_withheld_without_winter_guess(self):
        before = datetime(2026, 10, 25, 0, 59, 59, tzinfo=timezone.utc)
        at = datetime(2026, 10, 25, 1, tzinfo=timezone.utc)
        self.assertIn('phenomenonTimeCorrected', D.parse_sepa_hvd(BODY, before, source())[0])
        self.assertNotIn('phenomenonTimeCorrected', D.parse_sepa_hvd(BODY, at, source())[0])
        self.assertEqual(C.belgrade_local(datetime(2026, 3, 29, 2, 30)), (None, None))
        self.assertEqual(C.belgrade_local(datetime(2026, 10, 25, 2, 30)), (None, None))

    def test_unresolved_point_retains_label_but_has_no_measurement(self):
        row = D.parse_sepa_hvd(BODY, NOW, source('2026-09-14T14:00:00Z'))[0]
        point = C.observation_point(row)
        self.assertTrue(point['tu'])
        self.assertIsNone(point['t'])
        self.assertEqual(point['source_label'], '2026-09-14T17:00:00Z')
        self.assertIsNone(C.select_observation_points([point])['last_by_measurement'])

    def test_bad_estimate_does_not_fall_back_to_source_clock_in_latency(self):
        row = {'phenomenonTime':'2026-09-14T12:00:00Z',
               'phenomenonTimeCorrected':{'end':'invalid'}}
        self.assertIsNone(L._end_of(row)[0])

    def test_unknown_parking_keeps_zero_and_reception_without_measurement(self):
        point = C.observation_point({'result':0, 'resultQuality':'unvalidated',
            'phenomenonTimeUnknown':True, 'receivedTime':'2026-09-14T15:00:00Z'})
        self.assertEqual(point['v'], 0)
        self.assertTrue(point['tu'])
        self.assertEqual(point['rx'], '2026-09-14T15:00:00Z')
        self.assertIsNone(point['t'])

    def test_three_missed_ticks_are_not_a_one_interval_upper_bound(self):
        with tempfile.TemporaryDirectory() as folder:
            base = pathlib.Path(folder)
            rows = base/'rows'/'S1'; rows.mkdir(parents=True)
            (rows/'month.jsonl').write_text(json.dumps({'parameter':'temperature',
                'phenomenonTime':'2026-09-14T14:00:00Z',
                'receivedTime':'2026-09-14T14:40:00Z', 'result':20})+'\n', encoding='utf-8')
            rec = base/'receipts'/'S1'; rec.mkdir(parents=True)
            for i, at in enumerate(('14:00', '14:10', '14:20', '14:30', '14:40')):
                (rec/f'{i}.json').write_text(json.dumps({'sid':'S1',
                    'state':'captured' if i in (0,4) else 'failed',
                    'attempted_at':f'2026-09-14T{at}:00Z',
                    'completed_at':f'2026-09-14T{at}:05Z'}), encoding='utf-8')
            with mock.patch.object(L, 'ROWS', base/'rows'), mock.patch.object(L, 'RECEIPTS', base/'receipts', create=True):
                out = L.build_source('S1', NOW, {'cadence_seconds':600})
            self.assertEqual(out['our_polling_interval_minutes'], 10)
            self.assertIsNone(out['our_delay_upper_bound_minutes'])
            self.assertEqual(out['successful_reception_gaps']['max_minutes'], 40)
            self.assertEqual(out['successful_reception_gaps']['gaps_over_cadence'], 1)
            self.assertNotIn('up to one', out['what_this_is'])

    def test_unresolved_measurement_clock_is_not_reported_as_absent_time(self):
        with tempfile.TemporaryDirectory() as folder:
            base=pathlib.Path(folder); directory=base/'S1'; directory.mkdir()
            row={'sourceClockUnresolved':True,'parameter':'temperature',
                 'phenomenonTime':'2026-09-14T14:00:00Z','receivedTime':'2026-09-14T14:20:00Z','result':20}
            (directory/'month.jsonl').write_text(json.dumps(row)+'\n',encoding='utf-8')
            with mock.patch.object(L,'ROWS',base):
                out=L.build_source('S1',NOW,{'cadence_seconds':600})
            self.assertEqual(out['rows_with_unresolved_clock'],1)
            self.assertEqual(out['rows_without_a_measurement_time'],0)
            self.assertIsNone(out['age_minutes'])
            self.assertIn('unresolved',out['what_this_source_publishes'])

    def history(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            base = pathlib.Path(folder); sid = base/'S1'; sid.mkdir()
            (sid/'month.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows),encoding='utf-8')
            with mock.patch.object(H,'load_config',return_value={}):
                return H.fold(NOW,base)

    def test_latest_revision_is_selected_before_clock_basis_or_window_filter(self):
        original = {'sid':'S1','datastream':'station|temperature','parameter':'temperature','unit':'Cel',
            'result':10,'phenomenonTime':'2026-09-14T14:00:00Z','receivedTime':'2026-09-14T14:10:00Z','dedupe_key':'same observation'}
        for revision in (
            dict(original,result=30,phenomenonTime='2026-09-14T16:30:00Z',receivedTime='2026-09-14T14:50:00Z'),
            dict(original,result=30,sourceClockUnresolved=True,receivedTime='2026-09-14T14:50:00Z'),
        ):
            for sequence in ([original,revision],[revision,original]):
                self.assertEqual(self.history(sequence)['series'],[],'latest unusable revision must not revive the old number')
        revision = dict(original,result=30,phenomenonTimeCorrected={'end':'2026-09-14T13:00:00Z'},receivedTime='2026-09-14T14:50:00Z')
        out = self.history([original,revision])['series']
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]['time_basis'],'corrected')
        self.assertEqual(out[0]['buckets']['2026-09-14T13']['n'],1)

    def test_history_does_not_use_future_or_unzoned_receptions_or_measurements(self):
        original = {'sid':'S1','datastream':'temperature','parameter':'temperature','unit':'Cel','result':10,
            'phenomenonTime':'2026-09-14T14:00:00Z','receivedTime':'2026-09-14T14:10:00Z'}
        for row in (
            dict(original,phenomenonTime='2026-09-14T15:30:00Z'),
            dict(original,receivedTime='2026-09-14T15:30:00Z'),
            dict(original,phenomenonTimeUnknown=True,phenomenonTime=None,receivedTime='2026-09-14T14:30:00'),
        ):
            self.assertEqual(self.history([row])['series'],[])


if __name__ == '__main__':
    unittest.main()
